"""Automatic derivation of the upper bound L(C) (DeltaScope P0-2).

Text supplies the intent and the numbers; structure supplies everything else:
which outputs are licensed to change (the dependency closure of the edited
element), when the licence starts (the trigger edge) and how long it lasts
(the window).

Deliberately, nothing here reads the correct patch: the compiler sees (C, P)
only.  That is what keeps the bound from inheriting the answer it is meant to
check — and it is also why the window it produces is *tighter than*, not
identical to, the hand-written one.  A human annotator calibrates W by running
the correct patch and measuring the difference tail (标注规范 §3.2); the
compiler may not do that, so it derives W from the longest structure-reachable
delay instead.  The gap is measured (report_p02.md), not hidden.

Four rules, one per intent class — the mirror image of derive_req's four:

  refactor   -> clauses = []                    zero difference licensed
  timing     -> {edge, allow, window}           G1: where + when
  threshold  -> {always, allow, guard}          G2: + under which regime
  other      -> {always, allow}                 G0: where only

Two windows are emitted for every timing clause:

  tight  b + n_restart*|b-a| + struct_delay     what the structure supports
  sound  [0, n_cycles]                          what any input sequence needs

They bracket the truth: `tight` may fire on a compliant patch whose difference
tail was pushed out by a later restart, `sound` may miss an out-of-window edit.
Reporting both is the point — an upper bound has no single "correct" tightness,
only a tightness/soundness trade-off set by the environment assumption E.
"""

import math

from stlang import parse
from derive_req import (classify, affected_outputs, timer_instances)

CYCLE_MS = 10

# ------------------------------------------------------------------ text side

# Variable-name suffix -> Chinese words that name it in a change order.
ALIASES = {
    "EStop": ("急停", "急停按钮", "e-stop", "estop"),
    "Start": ("启动", "开始运行", "开车"),
    "Stop": ("停止", "停车"),
    "Overload": ("过载", "超载"),
    "LevelLow": ("低液位", "液位低", "低水位"),
    "LevelHigh": ("高液位", "液位高"),
    "Part": ("零件", "工件", "物料"),
    "Auto": ("自动", "自动模式"),
    "Manual": ("手动", "手动模式"),
    "Door": ("门", "安全门"),
    "Reset": ("复位",),
    "Fault": ("故障", "报警"),
}

# Verb -> edge direction.  Longer hints first: "急停复位" must beat "复位".
FALLING_HINTS = ("复位", "释放", "断开", "落下", "关闭", "消失", "撤销", "恢复", "离开")
RISING_HINTS = ("启动", "上升", "触发", "按下", "到达", "开门", "置位", "给出", "进料")

GUARD_INTENT_HINTS = ("互锁", "联锁", "禁止", "保护", "闭锁", "不允许")


def _direction_near(text, pos, default="rising"):
    """Edge direction implied by the verb *next to* the trigger word.

    Scoping matters: in "急停复位后须延时 2 秒才允许启动" the nearest verb to
    "急停" is 复位 (falling), while 启动 sits at the other end of the sentence
    and belongs to a different clause.  A whole-text scan picks the wrong one.
    """
    lo, hi = max(0, pos - 6), min(len(text), pos + 12)
    near = text[lo:hi]
    for h in FALLING_HINTS:
        if h in near:
            return "falling"
    for h in RISING_HINTS:
        if h in near:
            return "rising"
    return default


def _alias_of(name):
    for suffix, words in ALIASES.items():
        if name.endswith(suffix) or name.lower().endswith(suffix.lower()):
            return words
    return ()


def trigger_from_text(text, prog):
    """(var, dir, why) if the change order names a signal, else None.

    Earliest mention wins: a change order names the *cause* before it names the
    effect, so "急停复位后…才允许启动" is triggered by 急停, not by 启动.
    """
    names = [d.name for d in prog.decls]

    # 1. an explicit identifier in the text wins outright
    hits = [(text.find(n), n) for n in names if n in text]
    if hits:
        pos, n = min(hits)
        return n, _direction_near(text, pos), f"文本直呼标识符 {n}"

    # 2. alias words ("急停" -> xEStop); inputs before outputs on a tie
    cands = []
    for rank, d in enumerate(list(prog.inputs) + list(prog.outputs)):
        for w in _alias_of(d.name):
            p = text.find(w)
            if p >= 0:
                cands.append((p, rank, -len(w), d.name, w))
    if cands:
        p, _, _, n, w = min(cands)
        return n, _direction_near(text, p), f"文本线索「{w}」→ {n}"
    return None


# ------------------------------------------------------------------ code side

def _walk_calls(body):
    for st in body:
        if st[0] == "call":
            yield st
        elif st[0] == "if":
            for _, blk in st[1]:
                yield from _walk_calls(blk)
            if st[2]:
                yield from _walk_calls(st[2])


def timer_table(prog):
    """{instance: (pt_ms, IN expression, kind)} for every TON/TOF/TP call."""
    kinds = {d.name: d.type.upper() for d in prog.decls}
    out = {}
    for st in _walk_calls(prog.body):
        inst = st[1]
        if kinds.get(inst) not in ("TON", "TOF", "TP"):
            continue
        pt, inx = 0, None
        for pname, expr in st[2]:
            if pname == "PT" and expr[0] == "const":
                pt = expr[1]
            elif pname == "IN":
                inx = expr
        out[inst] = (int(pt), inx, kinds.get(inst))
    return out


def _first_signal(expr, inputs, polarity="rising"):
    """First input variable reached in `expr`, with edge polarity."""
    if not isinstance(expr, tuple):
        return None
    if expr[0] == "var":
        return (expr[1], polarity) if expr[1] in inputs else None
    if expr[0] == "un" and expr[1] == "NOT":
        inner = _first_signal(expr[2], inputs, polarity)
        if inner:
            return (inner[0], "falling" if polarity == "rising" else "rising")
        return None
    if expr[0] == "bin":
        if expr[1] == "AND":
            # `A AND NOT B` starts on A's rising edge
            return _first_signal(expr[2], inputs, polarity)
        for x in expr[2:]:
            r = _first_signal(x, inputs, polarity)
            if r:
                return r
    if expr[0] == "member":
        return _first_signal(expr[1], inputs, polarity)
    if expr[0] == "fcall":
        for _, e in expr[2]:
            r = _first_signal(e, inputs, polarity)
            if r:
                return r
    return None


def _target_timer(timers, a_ms, text, prog):
    """Timer the change order edits: PT == a, else the only timer, else None."""
    if a_ms is not None:
        exact = [t for t, (pt, _inx, _k) in timers.items() if pt == int(a_ms)]
        if exact:
            return exact[0], "PT 与变更单旧值一致的定时器"
    return None, "变更单未给出旧值（或无可匹配的 PT）"


def _restart_sources(prog, timer, trigger_var):
    """Inputs other than the trigger that can reset this timer's phase.

    Reaching through internal variables is not optional: `tonPulse(IN := yPulse)`
    names no input at all, yet yPulse is driven by `rtTrig.Q` and by
    `IF tonPulse.Q THEN yPulse := FALSE`, so every rising edge on xTrig restarts
    the phase and pushes the difference tail out by one more period.
    """
    from derive_req import dep_table
    inputs = {d.name for d in prog.inputs}
    timers = timer_table(prog)
    table = dep_table(prog)
    seen = set()

    def collect(e, acc):
        if not isinstance(e, tuple):
            return
        if e[0] == "var":
            acc.add(e[1])
            return
        for x in e[2:] if e[0] in ("bin", "un") else ():
            collect(x, acc)
        if e[0] == "member":
            collect(e[1], acc)

    direct = set()
    pool = [timer] if timer else list(timers)
    for t in pool:
        collect(timers.get(t, (0, None))[1], direct)

    # transitive closure over the data/control dependency graph
    stack, visited = list(direct), set(direct)
    while stack:
        n = stack.pop()
        if n in inputs:
            seen.add(n)
            continue
        for dep in table.get(n, ()):
            if dep not in visited:
                visited.add(dep)
                stack.append(dep)

    seen.discard(trigger_var)
    return sorted(seen)


def _struct_delay(prog, exclude, allow):
    """Sum of other timers' PT that actually feed the licensed outputs.

    Only timers on the dependency path count.  A timer sitting in an unrelated
    branch adds delay to nothing and would only widen the window for free.
    """
    from derive_req import dep_table
    table = dep_table(prog)
    reach, frontier = set(), list(allow)
    while frontier:
        n = frontier.pop()
        for dep in table.get(n, ()):
            if dep not in reach:
                reach.add(dep)
                frontier.append(dep)

    total = 0
    for inst, (pt, _inx, _k) in timer_table(prog).items():
        if inst in exclude:
            continue
        if f"{inst}.Q" in reach or f"{inst}.ET" in reach or inst in reach:
            total += int(math.ceil(pt / CYCLE_MS))
    return total


def _iter_stmts(body):
    for st in body:
        yield st
        if st[0] == "if":
            for _, blk in st[1]:
                yield from _iter_stmts(blk)
            if st[2]:
                yield from _iter_stmts(st[2])


def _conjuncts(expr):
    """Top-level AND factors of an expression."""
    if isinstance(expr, tuple) and expr[0] == "bin" and expr[1] == "AND":
        return _conjuncts(expr[2]) + _conjuncts(expr[3])
    return [expr]


def retained_outputs(prog):
    """Outputs that some IF branch leaves unassigned: their value persists.

    A hysteresis comparator is the canonical case — `IF in < 20 THEN q := FALSE
    ELSIF in > 80 THEN q := TRUE ELSE win := TRUE` never touches q in the middle
    band, so q *remembers* how it entered that band.  Once the two versions
    disagree at the new threshold, they keep disagreeing all the way down to the
    far boundary: the licensed region is not the interval (70, 80] but "from
    crossing 70 until both are forced again".  A static interval guard is simply
    false for such outputs.
    """
    out = set()
    for st in _iter_stmts(prog.body):
        if st[0] != "if":
            continue
        branches = []
        for _, blk in st[1]:
            branches.append({b[1][0] for b in blk
                             if b[0] == "assign" and len(b[1]) == 1})
        if st[2]:
            branches.append({b[1][0] for b in st[2]
                             if b[0] == "assign" and len(b[1]) == 1})
        else:
            branches.append(set())
        if branches:
            out |= (set.union(*branches) - set.intersection(*branches))
    return out


def _if_branches(body):
    for st in body:
        if st[0] == "if":
            for cond, blk in st[1]:
                yield cond, blk
                yield from _if_branches(blk)
            if st[2]:
                yield from _if_branches(st[2])


def _trace_edge(prog, sig, depth=0):
    """Trace a conditionally-set signal back to the primary input that clocks it.

    `IF rtPart.Q THEN yGate := TRUE` — yGate rises on xPart's rising edge, but
    only when it was FALSE.  If a second part arrives while yGate is still held,
    there is *no* new rising edge, so a trigger placed on yGate misses that
    event and every difference it causes then falls outside any short window.
    The edge that is guaranteed to recur lives upstream, in the condition.

    Tracing stops at plain assignments on purpose: a continuously-assigned
    signal (yMain := xStart AND …) does track its upstream input edge by
    edge, and keeping the nearer signal keeps the window tight.
    """
    inputs = {d.name for d in prog.inputs}
    if sig in inputs:
        return (sig, "rising")
    if depth >= 3:
        return None

    if "." in sig:
        base = sig.split(".", 1)[0]
        for st in _walk_calls(prog.body):
            if st[1] == base:
                for pname, expr in st[2]:
                    if pname in ("CLK", "IN"):
                        from derive_req import _refs
                        for ref in sorted(_refs(expr)):
                            r = _trace_edge(prog, ref, depth + 1)
                            if r:
                                return r
        return None

    from derive_req import _refs
    for cond, blk in _if_branches(prog.body):
        if any(st[0] == "assign" and st[1] == [sig] for st in blk):
            for ref in sorted(_refs(cond)):
                r = _trace_edge(prog, ref, depth + 1)
                if r:
                    return r
    return None


def observation_guard(prog, allow, related):
    """A factor of an allowed output that gates whether a difference is visible.

    `yCmd := xArm AND xB` — the change moves xArm, so xB alone decides whether
    yCmd can ever be TRUE; while xB is FALSE the two versions cannot differ.
    Narrowing the licence to `xB` costs nothing in soundness and buys the
    window dimension back for transients that only show up in that regime.
    """
    inputs = {d.name for d in prog.inputs}
    guards = {}
    for st in _iter_stmts(prog.body):
        if st[0] != "assign" or len(st[1]) != 1 or st[1][0] not in allow:
            continue
        conj = _conjuncts(st[2])
        free = [c for c in conj if isinstance(c, tuple) and c[0] == "var"
                and c[1] in inputs and c[1] not in related] if len(conj) >= 2 else []
        # only a *primary input* gates observability; a derived signal (an output
        # or an intermediate) moves as a consequence of the edit, so licensing it
        # away would narrow the bound for the wrong reason
        guards[st[1][0]] = free[0][1] if len(free) == 1 else None

    # The guard is a property of the *clause*, so it may only be adopted when every
    # licensed output is gated by the same factor.  `yBusy := yPulse AND NOT xInh`
    # next to a bare `yPulse := ...` does not license dropping xInh=FALSE cycles:
    # yPulse still differs there, and gating the clause would call that a violation.
    vals = {guards.get(a) for a in allow}
    if len(vals) == 1 and None not in vals:
        return vals.pop()
    return None


# ------------------------------------------------------------------ compile

def compile_contract(text, src, cycle_ms=CYCLE_MS, n_cycles=None, allow_sound=True):
    """Compile a change order into the upper bound L(C).  Sees (C, P) only."""
    prog = parse(src)
    kind, a, b, _ = classify(text)
    notes, diag = [], {}

    if n_cycles is None:
        longest = max((pt for pt, _inx, _k in timer_table(prog).values()), default=0)
        n_cycles = max(300, int(longest / cycle_ms * 1.5))

    # ---------- refactor: nothing may change
    if kind == "refactor":
        notes.append("重构类：上界为空集，任何行为差异都不被许可")
        return _result(kind, a, b, [], [], notes,
                       {"rule": "refactor->zero-difference", "n_cycles": n_cycles})

    # ---------- threshold: an interval guard carries the licence
    if kind == "threshold":
        from derive_req import find_boundary, FLIP
        hit = find_boundary(prog, a)
        mem = set()
        if hit:
            var, op = hit
            allow = affected_outputs(prog, [var]) or [d.name for d in prog.outputs]
            mem = retained_outputs(prog) & set(allow)
            if mem:
                # a retained output carries the disagreement past the interval
                clauses = [{"always": True, "allow": allow}]
                notes.append(f"带记忆的阈值：{sorted(mem)} 在部分分支不被赋值（值被保持），"
                             f"差异会延续到新覆盖区间之外 → 静态守卫不成立，"
                             f"只能给到变量级上界（G1）")
                diag.update(rule="threshold->memory-no-guard", seed=var,
                            retained=sorted(mem))
            else:
                # 差异必然落在 (min(a,b), max(a,b)) 之内，与比较方向无关：
                # 放宽（20→30）差异是 [20,30)，收紧（20→15）差异是 [15,20)。
                # 旧写法 `FLIP[op] a AND op b` 只对放宽成立，收紧时会算出
                # `x >= 20 AND x < 15` 这种空集，把合规改动全判成越界。
                # 这里统一取闭区间 [lo, hi]：两端各多许可一个无差异点，
                # 上界宁宽勿窄——多许可无差异点不损失健全性，少许可会误报。
                lo, hi = (a, b) if a < b else (b, a)
                guard = f"{var} >= {lo:g} AND {var} <= {hi:g}"
                clauses = [{"always": True, "allow": allow, "guard": guard}]
                notes.append(f"阈值类：许可限定在新覆盖区间 `{guard}`")
                diag.update(rule="threshold->guard-region", seed=var, guard=guard,
                            allow_source="依赖闭包")
        else:
            allow = [d.name for d in prog.outputs]
            clauses = [{"always": True, "allow": allow}]
            notes.append("找不到与旧值对应的比较 → 退化为变量级上界（G0），必误报或必漏检")
            diag.update(rule="threshold->fallback-g0", guard=None)
        return _result(kind, a, b, clauses, _sound(clauses, n_cycles) if allow_sound else [],
                       notes, diag)

    # ---------- timing (and anything with a duration literal)
    if kind == "timing":
        timers = timer_table(prog)
        tgt, why = _target_timer(timers, a, text, prog)
        diag.update(timer_where=why)

        if tgt:
            seeds = [f"{tgt}.Q"]
            allow = affected_outputs(prog, seeds)
            diag.update(seed=f"{tgt}.Q", timer=tgt, allow_source="定时器依赖闭包")
        else:
            # a duration was added on a path that has no timer yet: every timer
            # Q is a legal seed, since the delay must live on one of them
            seeds = [f"{t}.Q" for t in timers]
            allow = affected_outputs(prog, seeds)
            diag.update(seed=seeds, timer=None, allow_source="全部定时器的依赖闭包")
        if not allow:
            allow = [d.name for d in prog.outputs]
            notes.append("依赖闭包为空 → 退化为全部输出")

        trg = trigger_from_text(text, prog)
        from_timer = False
        if trg:
            tvar, tdir, twhy = trg
        elif tgt:
            pool_all = {d.name for d in prog.decls}
            sig = _first_signal(timers[tgt][1], pool_all)
            if sig:
                traced = _trace_edge(prog, sig[0])
                if traced and traced[0] != sig[0]:
                    tvar, tdir = traced[0], sig[1]
                    twhy = (f"文本无线索 → 定时器的 IN 信号 {sig[0]} 是条件置位的，"
                            f"已上溯到必然复现的边沿源 {traced[0]}")
                else:
                    tvar, tdir = sig[0], sig[1]
                    twhy = "文本无线索 → 目标定时器 IN 表达式的首个信号"
                    from_timer = True
            else:
                tvar, tdir, twhy = allow[0], "rising", "回退：许可输出的上升沿"
        else:
            tvar, tdir, twhy = allow[0], "rising", "回退：许可输出的上升沿"

        # TOF 的延时在 IN 的**下降**沿之后才开始。目标定时器是 TOF 时，上升沿触发
        # 永远看不到死区变化：许可窗口挂在上升沿上，而差异全部发生在下降沿之后。
        # ext_interlock（OSCAT INTERLOCK，500ms→1s）的第一次失败正是这个原因，
        # 与轨迹模板无关——当时的诊断"轨迹撞不上"只对了一半。
        # 只在触发取自定时器 IN 信号本身时改向；文本给了动词边的，以文本为准。
        if tgt and from_timer and timers[tgt][2] == "TOF" and tdir == "rising":
            tdir = "falling"
            twhy += "；TOF 的延时在 IN 下降沿后开始，触发取下降沿"
        diag.update(trigger=tvar, trigger_dir=tdir, trigger_where=twhy)

        b_scans = int(math.ceil(b / cycle_ms))
        moved = int(math.ceil(abs((b or 0) - (a or 0)) / cycle_ms))
        restarts = _restart_sources(prog, tgt, tvar)
        delay = _struct_delay(prog, {tgt} if tgt else set(), allow)
        hi = b_scans + len(restarts) * moved + delay
        diag.update(window_terms={"b": b_scans, "n_restart": len(restarts),
                                  "moved": moved, "struct_delay": delay},
                    restart_sources=restarts)

        clause = {"edge": {"var": tvar, "dir": tdir},
                  "allow": allow, "window": [0, hi]}
        related = set(timers) | ({tgt} if tgt else set())
        og = observation_guard(prog, allow, related)
        if og:
            clause["guard"] = og
            diag["observation_guard"] = og
            notes.append(f"可观测性守卫：差异只在 `{og}` 为真时才可见，"
                         f"加 guard 收紧上界而不损失健全性")
        clauses = [clause]
        notes.append(f"时序类：许可 = 触发 {tvar} {tdir} 后 {hi} 拍内、"
                     f"输出 {allow} 的变化"
                     f"（= b {b_scans} + 重启 {len(restarts)}×{moved} + 结构延迟 {delay}）")
        out = _result(kind, a, b, clauses,
                      _sound(clauses, n_cycles) if allow_sound else [], notes, diag)
        return out

    # ---------- guard intent ("增加互锁") or unclassified
    allow = [d.name for d in prog.outputs]
    guard = None
    trg = trigger_from_text(text, prog)
    if trg and any(h in text for h in GUARD_INTENT_HINTS):
        tvar = trg[0]
        reach = affected_outputs(prog, [tvar]) or allow
        allow = reach
        guard = tvar if trg[1] == "rising" else f"NOT {tvar}"
        notes.append(f"保护类：许可 = `{guard}` 工况下 {allow} 的变化")
        diag.update(rule="guard->regime", guard=guard, allow_source="依赖闭包")
        clauses = [{"always": True, "allow": allow, "guard": guard}]
    else:
        clauses = [{"always": True, "allow": allow}]
        notes.append("无法判定意图 → 退化为变量级上界（G0，最弱）")
        diag.update(rule="other->fallback-g0")
    return _result(kind, a, b, clauses, _sound(clauses, n_cycles) if allow_sound else [],
                   notes, diag)


def _sound(clauses, n_cycles):
    """Same allow/trigger/guard, window widened to the whole trace."""
    out = []
    for c in clauses:
        c = dict(c)
        if "edge" in c:
            c["window"] = [0, int(n_cycles)]
        out.append(c)
    return out


def _result(kind, a, b, clauses, sound, notes, diag):
    return {"kind": kind, "a": a, "b": b, "clauses": clauses,
            "clauses_sound": sound, "notes": notes, "diagnostics": diag}


if __name__ == "__main__":
    cases = [
        ("急停复位后须延时 2 秒才允许启动；其余逻辑不变。", "corpus/conveyor/orig.st", 700),
        ("星三角切换延时由 5 秒改为 7 秒；其余逻辑不变。", "corpus/stardelta/orig.st", 1000),
        ("泵启动增加 2 秒软启动延时；其余逻辑不变。", "corpus/pump/orig.st", 700),
        ("开门保持时间由 500 毫秒改为 800 毫秒；其余逻辑不变。", "corpus/gate/orig.st", 900),
        ("低液位停泵阈值由 10 改为 15；其余逻辑不变。", "corpus/tank/orig.st", 300),
        ("把 R_TRIG 边沿检测改为显式上升沿判断，行为必须逐周期不变。",
         "corpus/refactor/orig.st", 900),
        ("互锁后的动作延时由 30ms 改为 50ms；其余逻辑不变。", "corpus_bmc/edge/orig.st", 20),
    ]
    for text, path, ncy in cases:
        d = compile_contract(text, open(path, encoding="utf-8").read(), n_cycles=ncy)
        print(f"\n{path.split('/')[1]:10s} {d['kind']:9s} {d['clauses']}")
        for n in d["notes"]:
            print("           -", n)
        print("           ·", d["diagnostics"])

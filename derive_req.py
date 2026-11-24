"""Automatic derivation of the lower bound R(C).

The change order supplies only two things: an intent class and the numeric literals
(a -> b, with unit).  Everything else — which outputs are affected, which variable a
threshold belongs to — is derived from the *original* program's structure.

Deliberately, nothing here reads the correct patch: derivation sees (C, P) only, so
the resulting requirement cannot inherit the answer it is supposed to check.

Four derivation rules, one per intent class:

  refactor   -> {"structural": true}                     (behaviour may be unchanged,
                                                           but the code must change)
  timing     -> {"shape": {"len": |b-a| / cycle_ms}}     (behaviour must differ for
                                                           exactly the moved span)
  threshold  -> {"always": true, "guard": region(a,b)}   (behaviour must differ inside
                                                           the newly covered region)
  other      -> {"always": true, "allow": affected}      (existence only: the weakest
                                                           form, reported as a floor)
"""

import re

from stlang import parse

# 数值对的两个自由度：**介词**（由/从/自，常省略）和**动词**（改为/调整为/改成…）。
# 原来两者都写死成「由…改为」，于是任何同义改写都匹配失败，classify 落到 other，
# 契约退化成 allow=全部输出（静默全放行）。A1 实测：threshold 类 80% 的说法因此失效。
# 这里把动词扩成同义集合，介词改为可选——不改变匹配之后的任何推导逻辑。
_PREP = r"(?:由|从|自)?\s*"
# 单字「改」只在后面紧跟数字时才算动词（「40 改 30」），否则会吃掉「修改」里的「改」。
_VERB = (r"(?:改为|改成|改到|改作|调整为|修改为|变更为|更新为|"
         r"调到|调为|降至|升至|降为|升为|改(?=\s*\d))")
_UNIT = r"(毫秒|ms|MS|秒|s|S)"

TIME_PAIR = re.compile(rf"{_PREP}(\d+(?:\.\d+)?)\s*{_UNIT}?\s*{_VERB}\s*"
                       rf"(\d+(?:\.\d+)?)\s*{_UNIT}")
TIME_ONE = re.compile(rf"(\d+(?:\.\d+)?)\s*{_UNIT}")
PLAIN_PAIR = re.compile(rf"{_PREP}(\d+(?:\.\d+)?)\s*{_VERB}\s*(\d+(?:\.\d+)?)")

UNIT_MS = {"毫秒": 1, "ms": 1, "MS": 1, "秒": 1000, "s": 1000, "S": 1000}

# 重构意图靠「要求行为不变」这类措辞识别。原来只认「逐周期不变/行为不变」两种写法，
# 于是「结果要一模一样」「每周期结果不变」「逐周期行为必须保持」全部落到 other，
# 契约退化。A1 实测 refactor 类 40% 的说法因此失效。
# 注意：不能加裸词「不变」——所有变更单都以「其余逻辑不变。」结尾，会把所有类误判成重构。
REFACTOR_HINTS = ("逐周期", "每周期", "每个周期", "行为不变", "行为保持",
                  "重构", "等价", "一模一样", "结果相同", "结果要一样", "结果不变")
THRESHOLD_HINTS = ("阈值", "设定值", "上限", "下限", "门限")

FLIP = {"<=": ">", ">=": "<", "<": ">=", ">": "<="}

# Relative tolerance of the timing magnitude bound.
#
# M6 全语料标定（2026-11-04，31 条幅度约束 / 28 条擦边）把这一档从 10% 改成 0：
#
#   tol   good 接受   擦边被拦
#   ±0    30/31      20/28 = 71%
#   ±1    30/31      17/28 = 61%
#   ±2    30/31       7/28 = 25%
#   ±10（原值） 30/31   7/28 = 25%
#
# 10% 是为了兜住一处**模型误差**（conveyor：正确改法引入的新定时器与旧定时器起点
# 相差 17 拍，实测段长 183 而导出 need=200），却顺手把 13 条本可拦下的擦边放走了。
# 模型误差是**逐条目的、静止的**，抖动是**同一程序内的**——两者不该共用一个全局旋钮。
# 现在：默认 0，模型误差由条目用 `spec["tol"]` 显式声明（可审计），而不是全局放宽。
TOL_FRAC = 0.0


# ------------------------------------------------------------------ text side

def classify(text):
    """(kind, a, b, unit_ms) — text contributes only the intent and the numbers."""
    if any(h in text for h in REFACTOR_HINTS):
        return ("refactor", None, None, None)

    m = TIME_PAIR.search(text)
    if m:
        a = float(m.group(1)) * UNIT_MS[m.group(2) or m.group(4)]
        b = float(m.group(3)) * UNIT_MS[m.group(4)]
        return ("timing", a, b, 1)

    if any(h in text for h in THRESHOLD_HINTS):
        m = PLAIN_PAIR.search(text)
        if m:
            return ("threshold", float(m.group(1)), float(m.group(2)), None)

    m = TIME_ONE.search(text)
    if m:
        # a single duration: treat the old value as absent (0)
        return ("timing", 0.0, float(m.group(1)) * UNIT_MS[m.group(2)], 1)

    m = PLAIN_PAIR.search(text)
    if m:
        return ("threshold", float(m.group(1)), float(m.group(2)), None)
    return ("other", None, None, None)


# ------------------------------------------------------------------ code side

def _refs(node):
    """Dotted names referenced by an expression node."""
    if not isinstance(node, tuple):
        return set()
    kind = node[0]
    if kind == "var":
        return {node[1]}
    if kind == "const":
        return set()
    if kind == "member":
        base = node[1]
        if isinstance(base, tuple) and base[0] == "var":
            return {f"{base[1]}.{node[2]}"}
        return _refs(base)
    if kind in ("bin", "un"):
        out = set()
        for x in node[2:]:
            out |= _refs(x)
        return out
    if kind == "fcall":
        out = _refs(node[1])
        for _, e in node[2]:
            out |= _refs(e)
        return out
    return set()


def dep_table(prog):
    """name -> names it depends on, including control dependencies."""
    table = {}

    def add(k, vs):
        table.setdefault(k, set()).update(vs)

    def walk(body, ctrl):
        for st in body:
            kind = st[0]
            if kind == "assign":
                add(".".join(st[1]), _refs(st[2]) | ctrl)
            elif kind == "call":
                inst, s = st[1], set()
                for _, e in st[2]:
                    s |= _refs(e)
                for out in ("Q", "ET", "CV"):
                    add(f"{inst}.{out}", s | ctrl)
            elif kind == "if":
                base = ctrl | _refs(st[1][0][0])
                for cond, blk in st[1]:
                    walk(blk, base | _refs(cond))
                if st[2]:
                    walk(st[2], base)

    walk(prog.body, set())
    return table


def affected_outputs(prog, seeds):
    """Outputs reachable from the seeds in the dependency graph."""
    table = dep_table(prog)
    reach, frontier = set(seeds), list(seeds)
    while frontier:
        n = frontier.pop()
        for k, vs in table.items():
            if n in vs and k not in reach:
                reach.add(k)
                frontier.append(k)
    return [d.name for d in prog.outputs if d.name in reach]


def timer_instances(prog):
    return [d.name for d in prog.decls if d.type.upper() in ("TON", "TOF")]


EXPR_KINDS = {"var", "const", "member", "bin", "un", "fcall"}


def _iter_exprs(node):
    """Yield every expression node inside a statement/expression tree."""
    if isinstance(node, tuple):
        if node and isinstance(node[0], str) and node[0] in EXPR_KINDS:
            yield node
        for x in node:
            if isinstance(x, (tuple, list)):
                yield from _iter_exprs(x)
    elif isinstance(node, list):
        for x in node:
            yield from _iter_exprs(x)


def find_boundary(prog, value):
    """Find `VAR <op> value` in the program: (var, op) or None."""
    for st in prog.body:
        for node in _iter_exprs(st):
            if node[0] == "bin" and node[1] in FLIP:
                lhs, rhs = node[2], node[3]
                if (rhs[0] == "const" and rhs[1] == value
                        and lhs[0] == "var"):
                    return (lhs[1], node[1])
                if (lhs[0] == "const" and lhs[1] == value
                        and rhs[0] == "var"):
                    return (rhs[1], FLIP[node[1]])
    return None


# ------------------------------------------------------------------ derivation

def derive(text, src, cycle_ms=10):
    """Derive the lower bound from (change order, original source)."""
    prog = parse(src)
    kind, a, b, _ = classify(text)
    out = {"kind": kind, "a": a, "b": b, "notes": []}

    if kind == "refactor":
        out["require"] = [{"structural": True}]
        out["notes"].append("重构类：结构必须变化，行为允许不变")
        return out

    if kind == "timing":
        need = int(round(abs(b - a) / cycle_ms))
        seeds = [f"{t}.Q" for t in timer_instances(prog)]
        allow = affected_outputs(prog, seeds)
        if not allow:
            allow = [d.name for d in prog.outputs]
            out["notes"].append("原程序里没有可对应的定时器实例（改动新增了定时器）"
                                "→ 变量范围退化为全部输出，仅保留幅度约束")
        # Magnitude needs a tolerance band.  A point value is not derivable: the
        # observed run length is `need` minus whatever latency the surviving path
        # already had (conveyor: the 200 ms debounce shifts 200 down to 185), and
        # the phase of the trace shifts it again.  TOL_FRAC is the one knob of the
        # magnitude dimension — the same knob P5 studies — so it is explicit here
        # rather than buried in the checker.
        tol = min(max(0, int(round(need * TOL_FRAC))), max(0, need - 1))
        out["require"] = [{"shape": {"len": need, "tol": tol}, "allow": allow}]
        out["notes"].append(f"幅度约束：差异段应长约 {need}±{tol} 个扫描周期"
                            f"（= |{b:g}-{a:g}|ms / {cycle_ms}ms，容差 ±{TOL_FRAC:.0%}）")
        out["allow"], out["need"] = allow, need
        return out

    if kind == "threshold":
        hit = find_boundary(prog, a)
        if not hit:
            out["require"] = [{"always": True,
                               "allow": [d.name for d in prog.outputs]}]
            out["notes"].append("找不到与旧值对应的比较 → 退化为存在性约束")
            return out
        var, op = hit
        # 与 derive_lic 同一处修正：收紧阈值（20→15）时旧写法算出
        # `rSoc >= 20 AND rSoc < 15` 这个空集，下界永远无法被满足。
        # 差异区间恒为 [min, max]，与比较方向无关。
        lo, hi = (a, b) if a < b else (b, a)
        guard = f"{var} >= {lo:g} AND {var} <= {hi:g}"
        allow = affected_outputs(prog, [var]) or [d.name for d in prog.outputs]
        out["require"] = [{"always": True, "allow": allow, "guard": guard}]
        out["notes"].append(f"区间约束：差异必须落在 {guard}（边界 {a:g}→{b:g}）")
        out["allow"], out["guard"] = allow, guard
        return out

    allow = [d.name for d in prog.outputs]
    out["require"] = [{"always": True, "allow": allow}]
    out["notes"].append("无法判定意图 → 退化为存在性约束（最弱下界）")
    out["allow"] = allow
    return out


if __name__ == "__main__":
    cases = [
        ("急停复位后须延时 2 秒才允许启动；其余逻辑不变。", "corpus/conveyor/orig.st"),
        ("星三角切换延时由 5 秒改为 7 秒；其余逻辑不变。", "corpus/stardelta/orig.st"),
        ("开门保持时间由 500 毫秒改为 800 毫秒；其余逻辑不变。", "corpus/gate/orig.st"),
        ("低液位停泵阈值由 10 改为 15；其余逻辑不变。", "corpus/tank/orig.st"),
        ("互锁后的动作延时由 30ms 改为 50ms；其余逻辑不变。", "corpus_bmc/edge/orig.st"),
        ("把 R_TRIG 边沿检测改为显式上升沿判断，行为必须逐周期不变。",
         "corpus/refactor/orig.st"),
    ]
    for text, path in cases:
        d = derive(text, open(path, encoding="utf-8").read())
        print(f"{path.split('/')[1]:10s} {d['kind']:9s} {d['require']}")
        for n in d["notes"]:
            print("           -", n)

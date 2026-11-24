"""DeltaScope W1 engine: scan-cycle interpreter, differential execution, contract checking."""

from stlang import Program


# ---------------------------------------------------------------- builtin FBs

class TON:
    """IEC 61131-3 TON. ET in ms, advanced once per call."""
    def __init__(self, cycle_ms):
        self.cycle_ms = cycle_ms
        self.prev = False
        self.et = 0
        self.q = False

    def state(self):
        return ("ton", self.prev, self.et, self.q)

    def load(self, st):
        _, self.prev, self.et, self.q = st

    def step(self, IN=False, PT=0):
        if not IN:
            self.et, self.q = 0, False
        else:
            self.et = 0 if not self.prev else self.et + self.cycle_ms
            self.q = self.et >= PT
        self.prev = IN
        return {"Q": self.q, "ET": self.et}


class TOF:
    def __init__(self, cycle_ms):
        self.cycle_ms = cycle_ms
        self.prev = False
        self.et = 0
        self.q = False

    def state(self):
        return ("tof", self.prev, self.et, self.q)

    def load(self, st):
        _, self.prev, self.et, self.q = st

    def step(self, IN=False, PT=0):
        if IN:
            self.et, self.q = 0, True
        else:
            if self.prev:
                self.et = 0
            else:
                self.et += self.cycle_ms
            self.q = self.et < PT
        self.prev = IN
        return {"Q": self.q, "ET": self.et}


class R_TRIG:
    def __init__(self, cycle_ms):
        self.prev = False
        self.q = False

    def state(self):
        return ("rtrig", self.prev, self.q)

    def load(self, st):
        _, self.prev, self.q = st

    def step(self, CLK=False):
        self.q = bool(CLK) and not self.prev
        self.prev = bool(CLK)
        return {"Q": self.q}


class F_TRIG:
    def __init__(self, cycle_ms):
        self.prev = False
        self.q = False

    def state(self):
        return ("ftrig", self.prev, self.q)

    def load(self, st):
        _, self.prev, self.q = st

    def step(self, CLK=False):
        self.q = (not bool(CLK)) and self.prev
        self.prev = bool(CLK)
        return {"Q": self.q}


class CTU:
    def __init__(self, cycle_ms):
        self.prev = False
        self.cv = 0
        self.q = False

    def state(self):
        return ("ctu", self.prev, self.cv, self.q)

    def load(self, st):
        _, self.prev, self.cv, self.q = st

    def step(self, CU=False, R=False, PV=0):
        if R:
            self.cv = 0
        elif CU and not self.prev:
            self.cv += 1
        self.prev = bool(CU)
        self.q = self.cv >= PV
        return {"Q": self.q, "CV": self.cv}


BUILTIN = {"TON": TON, "TOF": TOF, "R_TRIG": R_TRIG, "F_TRIG": F_TRIG, "CTU": CTU}


# ---------------------------------------------------------------- values

def default_value(type_name):
    t = type_name.upper()
    if t == "BOOL":
        return False
    if t in ("INT", "DINT", "SINT", "UINT", "UDINT", "WORD", "BYTE", "TIME"):
        return 0
    if t == "REAL":
        return 0.0
    return 0


def truthy(v):
    return bool(v)


# ---------------------------------------------------------------- runtime

class FBInstance:
    """Instance of a user-defined FUNCTION_BLOCK."""

    def __init__(self, prog, cycle_ms, registry):
        self.prog = prog
        self.cycle_ms = cycle_ms
        self.registry = registry
        self.vars = {}
        self.insts = {}
        self._declare()

    def _declare(self):
        for d in self.prog.decls:
            t = d.type.upper()
            if t in BUILTIN:
                self.insts[d.name] = BUILTIN[t](self.cycle_ms)
            elif t in self.registry:
                self.insts[d.name] = FBInstance(self.registry[t], self.cycle_ms, self.registry)
            else:
                self.vars[d.name] = default_value(d.type)

    def state(self):
        return ("fb", tuple(sorted(self.vars.items())),
                tuple(sorted((n, i.state()) for n, i in self.insts.items())))

    def load(self, st):
        _, vars_, kids = st
        self.vars = dict(vars_)
        for n, s2 in kids:
            self.insts[n].load(s2)

    def step(self, named_args):
        for k, v in named_args.items():
            self.vars[k] = v
        exec_block(self.prog, self.vars, self.insts)
        return {d.name: self.vars.get(d.name) for d in self.prog.outputs}

    def read(self, name):
        return self.vars.get(name)


class RT:
    """Top-level runtime for one program."""

    def __init__(self, prog, cycle_ms, registry):
        self.prog = prog
        self.cycle_ms = cycle_ms
        self.registry = registry
        self.vars = {}
        self.insts = {}
        for d in prog.decls:
            t = d.type.upper()
            if t in BUILTIN:
                self.insts[d.name] = BUILTIN[t](cycle_ms)
            elif t in registry:
                self.insts[d.name] = FBInstance(registry[t], cycle_ms, registry)
            else:
                self.vars[d.name] = default_value(d.type)


def ast_sig(prog):
    """Structural fingerprint: declarations + statement tree (used by structural requirements)."""
    return (tuple((d.name, d.type.upper(), d.scope) for d in prog.decls), repr(prog.body))


def snap(rt):
    """Full snapshot of a runtime (usable as a dict key)."""
    return (tuple(sorted(rt.vars.items())),
            tuple(sorted((n, i.state()) for n, i in rt.insts.items())))


def load(rt, st):
    vars_, insts_ = st
    rt.vars = dict(vars_)
    for n, s2 in insts_:
        rt.insts[n].load(s2)


def step_once(rt, inputs):
    for k, v in inputs.items():
        rt.vars[k] = v
    exec_block(rt.prog, rt.vars, rt.insts)
    return tuple(rt.vars.get(d.name) for d in rt.prog.outputs)


# ---------------------------------------------------------------- evaluator

def eval_expr(node, vars_, insts):
    kind = node[0]
    if kind == "const":
        return node[1]
    if kind == "var":
        name = node[1]
        if name in vars_:
            return vars_[name]
        raise KeyError(f"undefined variable {name}")
    if kind == "member":
        base, attr = node[1], node[2]
        if base[0] != "var":
            raise KeyError("only simple member access supported")
        inst = insts[base[1]]
        if isinstance(inst, FBInstance):
            return inst.read(attr)
        return getattr(inst, attr.lower() if attr.lower() in ("q", "et", "cv") else attr, False)
    if kind == "un":
        op, e = node[1], node[2]
        v = eval_expr(e, vars_, insts)
        if op == "NOT":
            return not truthy(v)
        if op == "-":
            return -v
        return v
    if kind == "bin":
        op = node[1]
        a = eval_expr(node[2], vars_, insts)
        b = eval_expr(node[3], vars_, insts)
        if op == "AND":
            return truthy(a) and truthy(b)
        if op == "OR":
            return truthy(a) or truthy(b)
        if op == "XOR":
            return truthy(a) != truthy(b)
        if op == "=":
            return a == b
        if op == "<>":
            return a != b
        if op == "<":
            return a < b
        if op == ">":
            return a > b
        if op == "<=":
            return a <= b
        if op == ">=":
            return a >= b
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return int(a / b) if isinstance(a, int) and isinstance(b, int) else a / b
        if op == "MOD":
            return a % b
        raise ValueError(f"bad op {op}")
    raise ValueError(f"bad node {node}")


def exec_block(prog, vars_, insts):
    for st in prog.body:
        exec_stmt(st, vars_, insts)


def exec_stmt(st, vars_, insts):
    kind = st[0]
    if kind == "nop":
        return
    if kind == "assign":
        target, expr = st[1], st[2]
        val = eval_expr(expr, vars_, insts)
        if len(target) == 1:
            vars_[target[0]] = val
        else:
            inst = insts[target[0]]
            if isinstance(inst, FBInstance):
                inst.vars[target[1]] = val
            else:
                setattr(inst, target[1].lower(), val)
        return
    if kind == "if":
        for cond, block in st[1]:
            if truthy(eval_expr(cond, vars_, insts)):
                for s in block:
                    exec_stmt(s, vars_, insts)
                return
        for s in (st[2] or []):
            exec_stmt(s, vars_, insts)
        return
    if kind == "call":
        name, args = st[1], st[2]
        named = {}
        positional = []
        for pname, expr in args:
            val = eval_expr(expr, vars_, insts)
            if pname:
                named[pname] = val
            else:
                positional.append(val)
        inst = insts[name]
        if isinstance(inst, FBInstance):
            inst.step(named)
        else:
            setattr(inst, "_last", inst.step(**named))
        return
    raise ValueError(f"bad stmt {kind}")


# ---------------------------------------------------------------- driver

def run(prog, trace, cycle_ms=10, registry=None):
    """Execute `prog` over `trace` (list of dicts). Returns (outputs, snapshots)."""
    registry = registry or {}
    rt = RT(prog, cycle_ms, registry)
    outs, snaps = [], []
    for feed in trace:
        for k, v in feed.items():
            rt.vars[k] = v
        exec_block(prog, rt.vars, rt.insts)
        snap = dict(rt.vars)
        for name, inst in rt.insts.items():
            if not isinstance(inst, FBInstance):
                snap[f"{name}.Q"] = getattr(inst, "q", None)
        snaps.append(snap)
        outs.append({d.name: rt.vars.get(d.name) for d in prog.outputs})
    return outs, snaps


def diff_outputs(a, b):
    """Per-cycle output differences."""
    out = []
    for t, (oa, ob) in enumerate(zip(a, b)):
        for k in oa:
            if oa[k] != ob.get(k):
                out.append({"cycle": t, "var": k, "a": oa[k], "b": ob.get(k)})
    return out


def diff_sampled(a, b, stride, phase=0):
    out = []
    for t, (oa, ob) in enumerate(zip(a, b)):
        if (t - phase) % stride != 0:
            continue
        for k in oa:
            if oa[k] != ob.get(k):
                out.append({"cycle": t, "var": k, "a": oa[k], "b": ob.get(k)})
    return out


def classify(diffs, n_cycles, K=3):
    """transient (reconverged and stayed equal for >= K cycles) vs steady."""
    if not diffs:
        return "none"
    last = max(d["cycle"] for d in diffs)
    if last >= n_cycles - 1:
        return "steady"
    if n_cycles - 1 - last >= K:
        return "transient"
    return "transient-unconfirmed"


def diff_runs(diffs, allow=None):
    """Longest contiguous run of differing cycles, per licensed variable.

    A change order that moves a boundary from a to b makes behaviour differ for
    exactly |b-a| scans; the run length is therefore a signature of the *magnitude*
    of the change, which the upper bound cannot see.
    """
    by_var = {}
    for d in diffs:
        if allow and d["var"] not in allow:
            continue
        by_var.setdefault(d["var"], set()).add(d["cycle"])
    best = 0
    for cs in by_var.values():
        cs = sorted(cs)
        run = 1
        for i in range(1, len(cs)):
            run = run + 1 if cs[i] == cs[i - 1] + 1 else 1
            if run > best:
                best = run
        best = max(best, 1)
    return best


def verdict_task(orig, mod, traces, contract, cycle_ms=10, registry=None, K=3):
    """Task-level verdict: upper bound per trace, lower bound existential over traces.

    A change order counts as implemented if *some* trace exhibits a difference inside
    the required region; a trace that never reaches that region cannot refute it.
    """
    clauses = _prep(contract.get("clauses", []))
    reqs = _prep(contract.get("require", []))
    all_diffs, snaps_all = [], []
    for tr in traces:
        o1, s1 = run(orig, tr, cycle_ms, registry)
        o2, _ = run(mod, tr, cycle_ms, registry)
        all_diffs.append(diff_outputs(o1, o2))
        snaps_all.append(s1)
    return verdict_from_diffs(all_diffs, snaps_all, clauses, reqs,
                              ast_sig(mod) != ast_sig(orig))


def verdict_from_diffs(all_diffs, snaps_all, clauses, reqs, structural_ok):
    """Same judgement, from cached traces (lets several contracts share one run)."""
    first_unc, n_unc = None, 0
    req_trigs = [[] for _ in reqs]
    for t_i, diffs in enumerate(all_diffs):
        s1 = snaps_all[t_i]
        trig = [trigger_times(s1, c) for c in clauses]
        for d in diffs:
            if not covered(d, clauses, trig, s1):
                n_unc += 1
                if first_unc is None:
                    first_unc = d["cycle"]
        for i, r in enumerate(reqs):
            if not r.get("structural") and "shape" not in r:
                req_trigs[i].append(trigger_times(s1, r))
            else:
                req_trigs[i].append(None)

    unmet = []
    for i, r in enumerate(reqs):
        if r.get("structural"):
            if not structural_ok:
                unmet.append(r)
            continue
        if "shape" in r:
            need = int(r["shape"]["len"])
            tol = int(r["shape"].get("tol", 2))          # absolute slack, in scans
            # a tolerance that reaches 0 makes the bound vacuous: "no difference" would
            # be within tolerance of the required magnitude.
            tol = min(tol, max(0, need - 1))
            if not any(need - tol <= diff_runs(diffs, r.get("allow")) <= need + tol
                       for diffs in all_diffs):
                unmet.append(r)
            continue
        hit = False
        for t_i, diffs in enumerate(all_diffs):
            if any(covered(d, [r], [req_trigs[i][t_i]], snaps_all[t_i]) for d in diffs):
                hit = True
                break
        if not hit:
            unmet.append(r)

    v = "VIOLATED" if n_unc else ("INCOMPLETE" if unmet else "CONTAINED")
    return {"verdict": v,
            "reason": "out-of-scope" if n_unc else
                      ("required-change-missing" if unmet else "ok"),
            "n_uncovered": n_unc, "unmet_requirements": len(unmet),
            "max_run": max((diff_runs(d) for d in all_diffs), default=0),
            "first_uncovered_cycle": first_unc}


# ---------------------------------------------------------------- contracts

def _prep(clauses):
    """Compile guard expressions once per call."""
    from stlang import parse_expr
    out = []
    for cl in clauses:
        c = dict(cl)
        if "guard" in c:
            c["_guard"] = parse_expr(c["guard"])
        out.append(c)
    return out

def trigger_times(snaps, clause):
    """Cycle indices where the clause's trigger fires."""
    if clause.get("always"):
        return None
    edge = clause["edge"]
    var, direction = edge["var"], edge.get("dir", "rising")
    times = []
    prev = False          # IEC 上电默认：输入为 FALSE
    for t, snap in enumerate(snaps):
        cur = truthy(snap.get(var, False))
        if direction == "rising" and cur and not prev:
            times.append(t)
        if direction == "falling" and (not cur) and prev:
            times.append(t)
        prev = cur
    return times


def covered(d, clauses, trig, snaps=None):
    """Is diff point d licensed by some clause? Guard (phi) is evaluated at d's cycle."""
    for idx, cl in enumerate(clauses):
        if d["var"] not in cl["allow"]:
            continue
        guard = cl.get("_guard")
        if guard is not None and snaps is not None:
            if not truthy(eval_expr(guard, snaps[d["cycle"]], {})):
                continue
        lo, hi = cl.get("window", [0, 10 ** 9])
        if trig[idx] is None:                      # always
            if lo <= 0:
                return True
        else:
            for tau in trig[idx]:
                if lo <= d["cycle"] - tau <= hi:
                    return True
    return False


def check_requirements(reqs, diffs, snaps, mod_prog, orig_prog):
    """Lower bound: the change order must actually be implemented. Returns unmet list.

    A requirement is only enforced on traces that actually reach its region
    (trigger fired, or guard held at some cycle). Operationally: if the trace never
    exercises the change order, absence of a difference proves nothing.
    """
    unmet = []
    for r in reqs:
        if r.get("structural"):
            if ast_sig(mod_prog) == ast_sig(orig_prog):
                unmet.append(r)
            continue

        guard = r.get("_guard")
        if r.get("always"):
            active = True
            if guard is not None:
                active = any(truthy(eval_expr(guard, snap, {})) for snap in snaps)
            trig = [0] if active else []
        else:
            trig = trigger_times(snaps, r)
            active = bool(trig)

        if not active:
            continue                     # region unreachable in this trace -> vacuous
        if not any(covered(d, [r], [trig], snaps) for d in diffs):
            unmet.append(r)
    return unmet


def verdict(orig, mod, trace, contract, cycle_ms=10, registry=None, K=3):
    o1, s1 = run(orig, trace, cycle_ms, registry)
    o2, _ = run(mod, trace, cycle_ms, registry)
    diffs = diff_outputs(o1, o2)
    clauses = _prep(contract.get("clauses", []))
    trig = [trigger_times(s1, c) for c in clauses]
    uncovered = [d for d in diffs if not covered(d, clauses, trig, s1)]
    return {
        "verdict": "VIOLATED" if uncovered else "CONTAINED",
        "reason": "out-of-scope" if uncovered else "ok",
        "unmet_requirements": 0,
        "n_diffs": len(diffs),
        "n_uncovered": len(uncovered),
        "first_uncovered": uncovered[0] if uncovered else None,
        "class": classify(diffs, len(trace), K),
        "diffs": diffs,
    }

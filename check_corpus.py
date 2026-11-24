"""Corpus acceptance checker for DeltaScope change-order triples.

Usage:
    python check_corpus.py corpus/conveyor
    python check_corpus.py corpus/*        (bash expands)

A triple is (orig.st, good.st, bad.st, contract.json). The checker enforces the
mechanical part of the annotation protocol; the semantic part (is this really the
behaviour the change order licenses?) still needs two human raters.

Exit code 0 = ACCEPTED, 1 = REJECTED.
"""

import glob
import json
import os
import random
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stlang import parse                                  # noqa: E402
from engine import run, diff_outputs, verdict, verdict_task              # noqa: E402

CYCLE_MS = 10
N_TRACES = 40
N_CYCLES = 300


def load(d, which):
    with open(os.path.join(d, f"{which}.st"), encoding="utf-8") as f:
        return parse(f.read())


def gen_trace(inputs, n, rng, style="normal"):
    lo, hi = (95, 130) if style == "spaced" else (4, 30)
    cols = {}
    for dec in inputs:
        if dec.type.upper() == "BOOL":
            vals, v, t = [], bool(rng.getrandbits(1)), 0
            while t < n:
                d = rng.randint(lo, hi)
                vals += [v] * d
                t += d
                v = not v
            cols[dec.name] = vals[:n]
        else:
            vals, v = [], rng.randint(0, 100)
            for _ in range(n):
                v = max(0, min(100, v + rng.randint(-8, 8)))
                vals.append(v)
            cols[dec.name] = vals
    return [{k: cols[k][i] for k in cols} for i in range(n)]


def check(d):
    name = os.path.basename(os.path.normpath(d))
    out = []

    def add(level, msg):
        out.append((level, msg))

    # ---------- 1. files
    need = ["orig.st", "good.st", "bad.st", "contract.json"]
    missing = [f for f in need if not os.path.exists(os.path.join(d, f))]
    if missing:
        add("FAIL", f"缺少文件：{', '.join(missing)}")
        return name, out
    add("PASS", "文件齐全")

    # ---------- 2. parse
    try:
        orig, good, bad = load(d, "orig"), load(d, "good"), load(d, "bad")
    except Exception as e:                                   # noqa: BLE001
        add("FAIL", f"ST 解析失败：{type(e).__name__}: {e}")
        return name, out
    add("PASS", f"ST 解析通过（{len(orig.body)}/{len(good.body)}/{len(bad.body)} 条语句）")

    # ---------- 3. interface stability
    oi = [x.name for x in orig.outputs]
    if [x.name for x in good.outputs] != oi or [x.name for x in bad.outputs] != oi:
        add("WARN", "输出接口发生变化（允许，但契约必须显式许可接口变更）")
    else:
        add("PASS", f"输出接口一致：{oi}")

    # ---------- 4. contract
    meta = json.load(open(os.path.join(d, "contract.json"), encoding="utf-8"))
    contract = meta.get("contract", {"clauses": []})
    try:
        from engine import _prep
        clauses = _prep(contract.get("clauses", []))
    except Exception as e:                                   # noqa: BLE001
        add("FAIL", f"契约不可解析：{e}")
        return name, out
    add("PASS" if clauses or meta.get("change_order") else "WARN",
        f"契约子句 {len(clauses)} 条")

    # ---------- 5. traces
    n_cycles = int(meta.get("n_cycles", N_CYCLES))
    style = meta.get("trace_style", "normal")
    kind = meta.get("change_kind", "normal")
    expected_miss = bool(meta.get("expected_miss", False))
    rng = random.Random(zlib.crc32(name.encode()))
    traces = []
    tp = os.path.join(d, "traces.json")
    if os.path.exists(tp):
        traces.extend(json.load(open(tp, encoding="utf-8")))
        add("PASS" if len(traces) >= 2 else "WARN",
            f"自带定向轨迹 {len(traces)} 条（要求 ≥2）")
    else:
        add("WARN", "缺少 traces.json 定向轨迹，仅用随机轨迹评估（长定时器/稀疏事件会漏判）")
    traces += [gen_trace(orig.inputs, n_cycles, rng, style) for _ in range(N_TRACES)]
    n_total = len(traces)

    # ---------- 6. the correct change must be licensed everywhere
    vg = verdict_task(orig, good, traces, contract, CYCLE_MS)
    if vg["verdict"] == "VIOLATED":
        add("FAIL", f"合规改动被误判越界（{vg['n_uncovered']} 个未许可差异点）"
                    "——契约太窄（查语义闭包 / 窗口）")
    elif vg["verdict"] == "INCOMPLETE":
        add("FAIL", "合规改动未满足下界要求——require 写错，或该改动确实不产生许可差异")
    else:
        add("PASS", "合规改动 0 误报")

    # ---------- 7. the correct change must actually differ somewhere
    changed = 0
    dmax = 0
    for tr in traces:
        o1, _ = run(orig, tr, CYCLE_MS)
        o2, _ = run(good, tr, CYCLE_MS)
        dif = diff_outputs(o1, o2)
        if dif:
            changed += 1
            dmax = max(dmax, len(dif))
    if kind == "refactor":
        if changed:
            add("FAIL", f"重构类变更单要求零差异，但实测 {changed}/{n_total} 条轨迹存在差异")
        else:
            add("PASS", "重构类变更单：合规改动逐周期零差异")
    elif changed == 0:
        add("FAIL", "合规改动与原版没有任何差异——变更单没有被实现")
    else:
        add("PASS", f"合规改动在 {changed}/{n_total} 条轨迹上产生差异（最多 {dmax} 个点）")

    # ---------- 8a. the over-edit must be catchable at *some* granularity.
    # Validity is separate from performance: an over-edit that no contract in the
    # L/G0/G1/G2 lattice can flag is not a hard negative, it is an *equivalent*
    # edit, and measuring recall on it would be meaningless.  Which tiers do
    # catch it is the finding; the compiled contract is only one of them.
    tiers = {}
    tp2 = os.path.join(d, "contracts.json")
    if os.path.exists(tp2):
        try:
            tiers = {k: {"clauses": v.get("clauses", [])}
                     for k, v in json.load(open(tp2, encoding="utf-8")).items()}
        except Exception:                                        # noqa: BLE001
            tiers = {}
    tiers["编译契约"] = contract

    det, first = {}, None
    for k, ct in tiers.items():
        det[k] = 0
    for tr in traces:
        for k, ct in tiers.items():
            v = verdict(orig, bad, tr, ct, CYCLE_MS)
            if v["verdict"] == "VIOLATED":
                det[k] += 1
                c = v["first_uncovered"]["cycle"]
                first = c if first is None else min(first, c)
    catching = [k for k, n in det.items() if n]

    # ---------- 8b. performance of the compiled contract, reported not enforced
    if det["编译契约"]:
        add("PASS", f"越界改动被编译契约检出 {det['编译契约']}/{n_total} 条轨迹，"
                    f"最早第 {first} 个周期（可检出的粒度：{'/'.join(catching)}）")
    elif expected_miss:
        add("WARN", f"已知漏检（expected_miss）：{meta.get('miss_reason', '上界已退化')}"
                    f"——计入未判定率，不参与召回分母")
    elif catching:
        add("WARN", f"编译契约漏检该越界（{'/'.join(catching)} 层可检出）"
                    "——这是召回数据点，不是语料缺陷")
    else:
        add("FAIL", "越界改动在全部粒度上都不可判——与许可不可区分，样本无效")

    # ---------- 9. the over-edit must be *in addition to* the licensed change
    extra = 0
    for tr in traces:
        og, _ = run(good, tr, CYCLE_MS)
        ob, _ = run(bad, tr, CYCLE_MS)
        if diff_outputs(og, ob):
            extra += 1
    if extra == 0:
        add("FAIL", "bad 与 good 之间没有差异——越界没有被注入")
    else:
        add("PASS", f"bad 相对 good 另有差异（{extra}/{n_total} 条轨迹）")

    # ---------- 11. lower bound: the empty change must be rejected
    vn = verdict_task(orig, orig, traces, contract, CYCLE_MS)
    if vn["verdict"] == "CONTAINED":
        add("FAIL", "空改动（不修改）被判合规——缺少下界要求 require")
    elif vn["verdict"] == "INCOMPLETE":
        add("PASS", "空改动被拒（下界要求生效）")
    else:
        add("WARN", f"空改动被判 {vn['verdict']}，检查 require 与 clauses 的一致性")

    # ---------- 10. metadata hygiene
    if not meta.get("change_order"):
        add("WARN", "缺少 change_order 文本")
    if meta.get("over_edit_kind"):
        add("PASS", f"元数据完整（over_edit_kind={meta['over_edit_kind']}）")
    else:
        add("WARN", "缺少 over_edit_kind（用于分层统计）")
    return name, out


def main(argv):
    dirs = []
    for a in argv[1:] or ["corpus/*"]:
        dirs.extend(sorted(glob.glob(a)))
    if not dirs:
        print("no corpus dirs found")
        return 1

    total_fail = 0
    for d in dirs:
        if not os.path.isdir(d):
            continue
        name, out = check(d)
        status = "ACCEPTED" if not any(l == "FAIL" for l, _ in out) else "REJECTED"
        if status == "REJECTED":
            total_fail += 1
        print(f"\n=== {name}: {status} ===")
        for level, msg in out:
            print(f"  [{level}] {msg}")
    print(f"\n{len(dirs)} 个三元组，{total_fail} 个被拒")
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

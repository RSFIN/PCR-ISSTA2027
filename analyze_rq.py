#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RQ1–RQ3 统计分析（实验设计_v1.md §5–§6）。

口径：
  · 主分母 = 唯一越界补丁文件数去掉 expected_miss（实验计划 B4）
  · 三值 VIOLATED / INCOMPLETE / CONTAINED + UNDETERMINED 单列，不折算
  · recall 严格口径只计 VIOLATED；另报「被拒率」(VIOLATED+INCOMPLETE)
  · FPR 只计 VIOLATED（Ctrl-0/1 的 INCOMPLETE 是下界正确拒空改动，不是误报）
  · Wilson 单比例 CI + cluster bootstrap（按 spec 重采样，10,000 次）
  · 按程序宏平均（避免单程序多补丁主导）
  · 延迟 p50/p90/p99（不报均值）
  · McNemar 配对：D1 逐周期 vs 每 5 周期抽样

用法：python analyze_rq.py
产物：eval/rq_main_table.csv、eval/rq_stats.json
"""
import csv
import glob
import json
import math
import os
import random
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "eval", "rq_runs.jsonl")
OUT_JSON = os.path.join(HERE, "eval", "rq_stats.json")
OUT_CSV = os.path.join(HERE, "eval", "rq_main_table.csv")
SEED = 42
N_BOOT = 10000
Z = 1.959963984540054


def load():
    return [json.loads(l) for l in open(RUNS, encoding="utf-8") if l.strip()]


def wilson(k, n):
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 6), round(min(1.0, c + h), 6)]


def rate(k, n):
    return round(k / n, 6) if n else 0.0


def cluster_boot(groups, fn, n_boot=N_BOOT, seed=SEED):
    """groups: {cluster_id: [row,...]}; fn(list_of_rows)-> (k, n)。按簇有放回重采样。"""
    rng = random.Random(seed)
    keys = sorted(groups)
    vals = []
    for _ in range(n_boot):
        rows = []
        for _ in keys:
            rows.extend(groups[rng.choice(keys)])
        k, n = fn(rows)
        vals.append(k / n if n else 0.0)
    vals.sort()
    return [round(vals[int(0.025 * n_boot)], 6),
            round(vals[int(0.975 * n_boot)], 6)]


def quantiles(xs):
    xs = sorted(xs)
    if not xs:
        return {}
    def q(p):
        i = min(len(xs) - 1, int(math.ceil(p * len(xs))) - 1)
        return round(xs[i], 3)
    return {"min": round(xs[0], 3), "p50": q(.50), "p90": q(.90),
            "p95": q(.95), "p99": q(.99), "max": round(xs[-1], 3),
            "mean": round(sum(xs) / len(xs), 3)}


def mcnemar(pairs):
    """pairs: [(a_hit, b_hit), ...]；返回 b=仅 a 命中, c=仅 b 命中, 精确二项 p。"""
    b = sum(1 for a, h in pairs if a and not h)
    c = sum(1 for a, h in pairs if (not a) and h)
    n = b + c
    if n == 0:
        return dict(b=0, c=0, p=1.0)
    k = min(b, c)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))
    return dict(b=b, c=c, p=round(p, 8))


def miss_reason(r, meta):
    """36 个漏检的归因（两条已人工核实的机制）。"""
    cls = meta[r["spec"]]["contract"].get("clauses", [])
    if any(c.get("always") for c in cls):
        return "B 守卫即注入面（always/guard 型契约）"
    if any("edge" in c for c in cls) and any(
            "shape" in x for x in meta[r["spec"]]["contract"].get("require", [])):
        return "A 容差内擦边（幅度漂移 < tol）"
    return "C 其他窗口内许可"


def main():
    rows = load()
    meta = {}
    for p in glob.glob(os.path.join(HERE, "corpus_auto", "*", "contract.json")):
        spec = os.path.basename(os.path.dirname(p))
        meta[spec] = json.load(open(p, encoding="utf-8"))

    pos_all = [r for r in rows if r["arm"] == "pos"]
    und = [r for r in pos_all if r["expected_miss"]]
    pos = [r for r in pos_all if not r["expected_miss"]]
    neg = [r for r in rows if r["arm"] == "neg"]
    c0 = [r for r in rows if r["arm"] == "ctrl0"]
    c1 = [r for r in rows if r["arm"] == "ctrl1"]
    ctrl = neg + c0 + c1

    hit = lambda r: r["verdict"] == "VIOLATED"                       # noqa: E731
    blocked = lambda r: r["verdict"] in ("VIOLATED", "INCOMPLETE")  # noqa: E731

    out = {}
    out["meta"] = dict(
        n_runs=len(rows), n_specs=len({r["spec"] for r in rows}),
        n_pos_files=len(pos_all), n_undetermined=len(und),
        recall_denominator=len(pos),
        n_neg=len(neg), n_ctrl0=len(c0), n_ctrl1=len(c1), n_ctrl=len(ctrl),
        n_traces_per_case=rows[0]["n_traces"],
        n_directed=rows[0]["n_directed"],
        bootstrap=N_BOOT, seed=SEED)

    # ---------------- RQ1
    k = sum(map(hit, pos))
    kb = sum(map(blocked, pos))
    g = defaultdict(list)
    for r in pos:
        g[r["spec"]].append(r)
    out["RQ1"] = dict(
        definition="主指标 recall over observable over-edits；分母 = 唯一越界补丁文件 − expected_miss",
        k=k, n=len(pos), recall=rate(k, len(pos)), wilson=wilson(k, len(pos)),
        cluster_boot_ci=cluster_boot(g, lambda rs: (sum(map(hit, rs)), len(rs))),
        blocked_k=kb, blocked_rate=rate(kb, len(pos)),
        blocked_wilson=wilson(kb, len(pos)),
        undetermined=[r["case_id"] for r in und],
        macro_by_spec=rate(sum(1 for s, rs in g.items() if any(map(hit, rs))), len(g)),
        macro_wilson=wilson(sum(1 for s, rs in g.items() if any(map(hit, rs))), len(g)),
    )
    # 分层
    def strat(keyfn, subset=pos):
        d = defaultdict(list)
        for r in subset:
            d[keyfn(r)].append(r)
        return {str(kk): dict(k=sum(map(hit, rs)), n=len(rs),
                              recall=rate(sum(map(hit, rs)), len(rs)),
                              wilson=wilson(sum(map(hit, rs)), len(rs)))
                for kk, rs in sorted(d.items())}
    out["RQ1"]["by_op"] = strat(lambda r: r["op"])
    out["RQ1"]["by_kind"] = strat(lambda r: r["kind"])
    out["RQ1"]["by_edge"] = strat(lambda r: "有 edge" if r.get("has_edge") else "always 型")

    # ---------------- RQ2
    def fpr_block(name, rs):
        kk = sum(map(hit, rs))
        return dict(k=kk, n=len(rs), fpr=rate(kk, len(rs)), wilson=wilson(kk, len(rs)),
                    verdicts=dict(Counter(r["verdict"] for r in rs)))
    out["RQ2"] = {name: fpr_block(name, rs) for name, rs in
                  [("Neg 合规改动", neg), ("Ctrl-0 空改动", c0),
                   ("Ctrl-1 无关合规改动", c1), ("合计", ctrl)]}
    gc = defaultdict(list)
    for r in ctrl:
        gc[r["spec"]].append(r)
    out["RQ2"]["合计"]["cluster_boot_ci"] = cluster_boot(
        gc, lambda rs: (sum(map(hit, rs)), len(rs)))
    out["RQ2"]["口径"] = ("误报只计 VIOLATED；Ctrl-0/1 的 INCOMPLETE 是下界正确报告"
                          "『补丁没实现工单』，不是误报（见 make_ctrl1.py 的语义澄清）")

    # ---------------- RQ3
    lat = [r["latency_ms"] for r in rows if r.get("latency_ms")]
    out["RQ3"] = dict(unit="ms / 每组 (spec, patch)，含 44 条轨迹 × 2 次 run + 4 配置判定",
                      quantiles=quantiles(lat),
                      by_arm={a: quantiles([r["latency_ms"] for r in rows
                                            if r["arm"] == a and r.get("latency_ms")])
                              for a in ["pos", "neg", "ctrl0", "ctrl1"]},
                      undetermined_rate=rate(len(und) + sum(
                          1 for r in rows if r["verdict"] == "UNDETERMINED"), len(rows)),
                      n_parse_run_error=sum(1 for r in rows
                                            if r["verdict"] == "UNDETERMINED"))
    out["RQ3"]["total_cpu_s"] = round(sum(lat) / 1000, 1)

    # ---------------- 对照配置
    cfg = {}
    for label, field in [("D1 主方法（Ê 内全轨迹，双边）", "verdict"),
                         ("分布外（仅 40 条随机轨迹）", "ood_verdict"),
                         ("每 5 周期抽样", "sample5_verdict"),
                         ("仅上界（消融锚）", "upper_verdict")]:
        kp = sum(1 for r in pos if r[field] == "VIOLATED")
        kf = sum(1 for r in ctrl if r[field] == "VIOLATED")
        cfg[label] = dict(recall_k=kp, recall=rate(kp, len(pos)),
                          wilson=wilson(kp, len(pos)),
                          fp_k=kf, fpr=rate(kf, len(ctrl)))
    out["对照配置"] = cfg
    pairs = [(hit(r), r["sample5_verdict"] == "VIOLATED") for r in pos]
    out["McNemar_D1_vs_sample5"] = mcnemar(pairs)

    # ---------------- 触发边沿级（辅助，仅 31 条有 edge 的语料可数）
    ev = [r for r in pos if r.get("has_edge")]
    ne = sum(r["n_events"] for r in ev)
    nd = sum(r["n_events_diff"] for r in ev)
    nh = sum(r["n_events_hit"] for r in ev)
    ns = sum(r["n_events_hit_s5"] for r in ev)
    out["触发边沿级"] = dict(
        caveat=("仅契约含 edge 的语料可数：96 条中 31 条，其余 65 条为 always/guard 型，"
                "无边沿可数 → 不能作为全库主指标（实验计划 B4 因此改用唯一补丁文件作分母）"),
        n_pos_cases=len(ev), n_specs=len({r["spec"] for r in ev}),
        n_events=ne, n_events_with_diff=nd,
        n_events_uncovered=nh, n_events_sample5=ns,
        sample5_event_retention=rate(ns, nh),
        coverage_specs=rate(len({r["spec"] for r in ev}), out["meta"]["n_specs"]))

    # ---------------- 漏检归因
    miss = [r for r in pos if not hit(r)]
    out["漏检归因"] = dict(
        n=len(miss),
        by_verdict=dict(Counter(r["verdict"] for r in miss)),
        by_mechanism=dict(Counter(miss_reason(r, meta) for r in miss)),
        by_op=dict(Counter(r["op"] for r in miss)),
        cases=[dict(case_id=r["case_id"], verdict=r["verdict"],
                    n_diffs=r["n_diffs"], n_unc_points=r["n_unc_points"],
                    mechanism=miss_reason(r, meta)) for r in miss])

    # ---------------- Gate 门禁（G-D，12/26）
    out["G-D 门禁"] = dict(
        criterion="事件级 recall <50% 或 FPR >25% 则触发 Kill 预案",
        recall=out["RQ1"]["recall"], fpr=out["RQ2"]["合计"]["fpr"],
        passed=out["RQ1"]["recall"] >= .50 and out["RQ2"]["合计"]["fpr"] <= .25)

    # ---------------- 落盘
    json.dump(out, open(OUT_JSON, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    with open(OUT_CSV, "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["RQ", "metric", "subset", "k", "n", "value", "ci_lo", "ci_hi"])
        w.writerow(["RQ1", "recall", "Pos(246)", k, len(pos), out["RQ1"]["recall"],
                    *out["RQ1"]["wilson"]])
        w.writerow(["RQ1", "recall_clusterCI", "Pos(246)", k, len(pos),
                    out["RQ1"]["recall"], *out["RQ1"]["cluster_boot_ci"]])
        w.writerow(["RQ1", "blocked_rate", "Pos(246)", kb, len(pos),
                    out["RQ1"]["blocked_rate"], *out["RQ1"]["blocked_wilson"]])
        w.writerow(["RQ1", "macro_by_spec", "96 specs", "", len(g),
                    out["RQ1"]["macro_by_spec"], *out["RQ1"]["macro_wilson"]])
        for key, v in out["RQ1"]["by_op"].items():
            w.writerow(["RQ1", f"recall_op_{key}", "Pos", v["k"], v["n"],
                        v["recall"], *v["wilson"]])
        for name, v in out["RQ2"].items():
            if isinstance(v, dict) and "fpr" in v:
                w.writerow(["RQ2", "fpr", name, v["k"], v["n"], v["fpr"], *v["wilson"]])
        for label, v in cfg.items():
            w.writerow(["对照", label, "recall", v["recall_k"], len(pos),
                        v["recall"], *v["wilson"]])
        for q, v in out["RQ3"]["quantiles"].items():
            w.writerow(["RQ3", f"latency_ms_{q}", "all 522", "", "", v, "", ""])

    # ---------------- 控制台摘要
    print(f"样本 {len(rows)} 组 / {out['meta']['n_specs']} 条语料，"
          f"主分母 {len(pos)}，UNDETERMINED {len(und)}")
    print(f"\n[RQ1] recall = {k}/{len(pos)} = {out['RQ1']['recall']:.1%}  "
          f"Wilson {out['RQ1']['wilson']}  cluster-boot {out['RQ1']['cluster_boot_ci']}")
    print(f"      被拒率(VIOLATED+INCOMPLETE) = {kb}/{len(pos)} = {out['RQ1']['blocked_rate']:.1%}")
    print(f"      按程序宏平均 = {out['RQ1']['macro_by_spec']:.1%}")
    print(f"      按算子: " + "  ".join(
        f"{kk}={v['k']}/{v['n']}={v['recall']:.0%}"
        for kk, v in out["RQ1"]["by_op"].items()))
    print(f"\n[RQ2] FPR = {out['RQ2']['合计']['k']}/{len(ctrl)} = "
          f"{out['RQ2']['合计']['fpr']:.1%}  Wilson {out['RQ2']['合计']['wilson']}")
    for name in ["Neg 合规改动", "Ctrl-0 空改动", "Ctrl-1 无关合规改动"]:
        v = out["RQ2"][name]
        print(f"      {name}: {v['k']}/{v['n']} VIOLATED, 判定={v['verdicts']}")
    print(f"\n[RQ3] 延迟 p50={out['RQ3']['quantiles']['p50']}ms "
          f"p90={out['RQ3']['quantiles']['p90']}ms p99={out['RQ3']['quantiles']['p99']}ms "
          f"(总 CPU {out['RQ3']['total_cpu_s']}s)")
    print("\n[对照] " + " | ".join(
        f"{lab.split('（')[0]}: recall {v['recall']:.1%}, FPR {v['fpr']:.1%}"
        for lab, v in cfg.items()))
    print(f"       McNemar D1 vs 5周期抽样: {out['McNemar_D1_vs_sample5']}")
    print(f"\n[漏检] {len(miss)} 条，机制：{out['漏检归因']['by_mechanism']}")
    print(f"\n[G-D 门禁] {'PASS' if out['G-D 门禁']['passed'] else 'FAIL'}"
          f" (recall {out['RQ1']['recall']:.1%} ≥50%, FPR {out['RQ2']['合计']['fpr']:.1%} ≤25%)")
    print(f"\n→ {OUT_JSON}\n→ {OUT_CSV}")


if __name__ == "__main__":
    main()

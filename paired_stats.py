#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""配对检验与主表统计（DeltaScope 对比实验）。

设计原则：**在看到任何一个基线的结果之前就把口径写死**，避免"照结果挑检验"。

用法
----
    python paired_stats.py                      # 用 eval/rq_runs.jsonl + baselines/*/
    python paired_stats.py --ours eval/rq_runs.jsonl --base-dir baselines
    python paired_stats.py --selftest            # 数学自检，不需要任何数据
    python paired_stats.py --allow-incomplete    # 把 INCOMPLETE 当"接受"（默认）
    python paired_stats.py --strict              # 把 INCOMPLETE 当"弃权"

产出
----
    eval/main_table.csv      配置 × (recall / FPR / UNDET / p50)
    eval/mcnemar.csv         每个基线 vs 本文方法的配对检验 + Holm 校正
    eval/paired_detail.csv   逐用例的 2×2 明细（供复核）

判定映射（唯一口径）
--------------------
    任务侧：pos 且 expected_miss=0  →  "应当拒绝"
            neg/ctrl0/ctrl1         →  "应当放行"
    工具侧：VIOLATED                →  拒绝
            CONTAINED / INCOMPLETE  →  放行（INCOMPLETE = 没做到，不是越界）
            UNDETERMINED            →  弃权，不进配对检验，单独计数
"""
import argparse
import csv
import json
import math
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.join(HERE, "eval")


# ---------------------------------------------------------------- 基础工具

def load_cases(path):
    """读用例清单 → {case_id: dict}。标签只在这里出现。"""
    out = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            out[r["case_id"]] = {
                "cid": r["case_id"],
                "arm": r["arm"],
                "spec": r["spec"],
                "expected": r["expected"],
                "expected_miss": r["expected_miss"] in ("1", "true", "True"),
            }
    return out


def load_verdicts(path):
    """读一个配置的判定 → {case_id: verdict}。jsonl，字段 cid 或 case_id 均可。"""
    out = {}
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            cid = r.get("cid") or r.get("case_id")
            if cid:
                out[cid] = (r.get("verdict") or "UNDETERMINED").upper()
    return out


def is_should_reject(case):
    return case["arm"] == "pos" and case["expected"] == "VIOLATED" and not case["expected_miss"]


def is_scored(case):
    """expected_miss 的 4 条正例不进召回分母，也不进配对检验。"""
    return not case["expected_miss"]


def tool_decision(verdict, incomplete_as):
    if verdict in ("VIOLATED",):
        return "reject"
    if verdict in ("CONTAINED",):
        return "accept"
    if verdict in ("INCOMPLETE",):
        return "abstain" if incomplete_as == "abstain" else "accept"
    return "abstain"


def case_correct(case, verdict, incomplete_as):
    d = tool_decision(verdict, incomplete_as)
    if d == "abstain":
        return None
    truth = "reject" if is_should_reject(case) else "accept"
    return d == truth


# ---------------------------------------------------------------- 统计

def exact_mcnemar_p(b, c):
    """精确二项 McNemar（双侧）。b+c 很小，必须用精确检验，不能 χ²。"""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def holm(pvals):
    """Holm-Bonferroni。返回校正后 p（保持原顺序）。"""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = (m - rank) * pvals[i]
        running = max(running, val)
        adj[i] = min(1.0, running)
    return adj


def cluster_bootstrap_ci(rows, key, correctness, n_boot=10000, seed=42):
    """按 spec 聚类 bootstrap。rows 已按 case 粒度，correctness 是 0/1 或 None。"""
    by_cluster = defaultdict(list)
    for r in rows:
        c = correctness.get(r["cid"])
        if c is not None:
            by_cluster[r["spec"]].append(c)
    clusters = [v for v in by_cluster.values() if v]
    if not clusters:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    est = []
    for _ in range(n_boot):
        pick = [clusters[rng.randrange(len(clusters))] for _ in clusters]
        flat = [x for cl in pick for x in cl]
        if flat:
            est.append(sum(flat) / len(flat))
    est.sort()
    lo = est[int(0.025 * len(est))]
    hi = est[int(0.975 * len(est)) - 1]
    return lo, hi


def summarize(cases, verdicts, incomplete_as="accept"):
    """单配置的描述统计。"""
    scored = [c for c in cases.values() if is_scored(c)]
    n_pos = sum(1 for c in scored if is_should_reject(c))
    n_neg = len(scored) - n_pos

    hit_pos = det_pos = 0
    false_pos = n_neg_det = 0
    undet = 0
    for c in scored:
        v = verdicts.get(c["cid"], "UNDETERMINED")
        d = tool_decision(v, incomplete_as)
        if d == "abstain":
            undet += 1
            continue
        if is_should_reject(c):
            det_pos += 1
            hit_pos += (d == "reject")
        else:
            n_neg_det += 1
            false_pos += (d == "reject")
    return {
        "n": len(scored),
        "recall_k": hit_pos,
        "recall_n": n_pos,
        "recall": hit_pos / n_pos if n_pos else float("nan"),
        "recall_det_n": det_pos,
        "fpr_k": false_pos,
        "fpr_n": n_neg_det,
        "fpr": false_pos / n_neg_det if n_neg_det else float("nan"),
        "undet": undet,
    }


def mcnemar_pair(cases, ours, base, incomplete_as="accept"):
    """本文方法 vs 一个基线：只算两边都给出确定判定的可评分用例。"""
    b = c = n = 0
    detail = []
    for cid, case in cases.items():
        if not is_scored(case):
            continue
        if cid not in ours or cid not in base:
            continue
        ok_o = case_correct(case, ours[cid], incomplete_as)
        ok_b = case_correct(case, base[cid], incomplete_as)
        if ok_o is None or ok_b is None:
            continue
        n += 1
        if ok_o and not ok_b:
            b += 1
        elif ok_b and not ok_o:
            c += 1
        detail.append((cid, case["spec"], ours[cid], base[cid], int(bool(ok_o)), int(bool(ok_b))))
    return {"n": n, "b": b, "c": c, "p": exact_mcnemar_p(b, c), "detail": detail}


def p50(xs):
    if not xs:
        return float("nan")
    xs = sorted(xs)
    return xs[len(xs) // 2]


# ---------------------------------------------------------------- 自检

def selftest():
    ok = True

    def chk(name, got, want, tol=1e-9):
        nonlocal ok
        good = abs(got - want) <= tol
        print(f"  {'PASS' if good else 'FAIL'}  {name}: got {got!r}, want {want!r}")
        ok = ok and good

    print("1) 精确 McNemar")
    chk("b=12,c=0 → 0.000488", exact_mcnemar_p(12, 0), 2 * (0.5 ** 12))
    chk("b=0,c=0 → 1.0", exact_mcnemar_p(0, 0), 1.0)
    chk("b=5,c=5 → 1.0（对称）", exact_mcnemar_p(5, 5), 1.0)
    # b=3,c=1: 2*(C(4,0)+C(4,1))/16 = 2*5/16
    chk("b=3,c=1 → 0.625", exact_mcnemar_p(3, 1), 2 * 5 / 16)

    print("2) Holm 校正")
    adj = holm([0.001, 0.02, 0.04])
    chk("最小 p 放大 3 倍", adj[0], 0.003)
    chk("单调不减", float(adj[1] >= adj[0]), 1.0)
    chk("上界 1.0", float(max(adj) <= 1.0), 1.0)
    adj2 = holm([0.5, 0.9])
    chk("近 1 时截断", adj2[1], 1.0)

    print("3) 判定映射")
    pos = {"cid": "p1", "arm": "pos", "spec": "s", "expected": "VIOLATED", "expected_miss": False}
    ctrl = {"cid": "c1", "arm": "ctrl0", "spec": "s", "expected": "NOT_VIOLATED", "expected_miss": False}
    chk("VIOLATED 在正例上正确", float(case_correct(pos, "VIOLATED", "accept")), 1.0)
    chk("CONTAINED 在正例上错误", float(case_correct(pos, "CONTAINED", "accept")), 0.0)
    chk("INCOMPLETE 在对照上算放行", float(case_correct(ctrl, "INCOMPLETE", "accept")), 1.0)
    chk("INCOMPLETE 严格模式下弃权", float(case_correct(ctrl, "INCOMPLETE", "abstain") is None), 1.0)
    chk("VIOLATED 在对照上是误报", float(case_correct(ctrl, "VIOLATED", "accept")), 0.0)

    print("4) 汇总分母")
    cases = {
        "p1": dict(pos, cid="p1"),
        "p2": dict(pos, cid="p2"),
        "p3": dict(pos, cid="p3", expected_miss=True),   # 不进分母
        "c1": dict(ctrl, cid="c1"),
    }
    s = summarize(cases, {"p1": "VIOLATED", "p2": "CONTAINED", "p3": "VIOLATED", "c1": "CONTAINED"})
    chk("召回分母排除 expected_miss", float(s["recall_n"]), 2.0)
    chk("召回 1/2", s["recall"], 0.5)
    chk("误报 0/1", s["fpr"], 0.0)

    print("5) 配对只算双方都确定")
    ours_v = {"p1": "VIOLATED", "p2": "CONTAINED", "p3": "VIOLATED", "c1": "CONTAINED"}
    # 基线 p2 弃权、c1 误报 → p2 整条退出配对
    base = {"p1": "VIOLATED", "p2": "UNDETERMINED", "c1": "VIOLATED"}
    m = mcnemar_pair(cases, ours_v, base)
    chk("n 只含双方确定的可评分用例", float(m["n"]), 2.0)
    chk("b=1（我们对基线错）", float(m["b"]), 1.0)
    chk("c=0（基线弃权不计入）", float(m["c"]), 0.0)
    # 基线 p2 判对、我们判错 → 应产生 c
    m2 = mcnemar_pair(cases, ours_v, {"p1": "VIOLATED", "p2": "VIOLATED", "c1": "VIOLATED"})
    chk("c=1（基线对我们错）", float(m2["c"]), 1.0)
    chk("b=c=1 时 p=1", m2["p"], 1.0)

    print("\n" + ("✅ 自检全部通过" if ok else "❌ 自检有失败项"))
    return 0 if ok else 1


# ---------------------------------------------------------------- 主流程

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=os.path.join(EVAL, "rq_cases.tsv"))
    ap.add_argument("--ours", default=os.path.join(EVAL, "rq_runs.jsonl"))
    ap.add_argument("--base-dir", default=os.path.join(HERE, "baselines"))
    ap.add_argument("--out-dir", default=EVAL)
    ap.add_argument("--ours-name", default="ours")
    ap.add_argument("--strict", action="store_true", help="INCOMPLETE 视为弃权")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    incomplete_as = "abstain" if args.strict else "accept"
    cases = load_cases(args.cases)
    configs = {}
    ours = load_verdicts(args.ours)
    if not ours:
        print(f"[FAIL] 读不到本文方法的判定：{args.ours}", file=sys.stderr)
        return 2
    configs[args.ours_name] = ours

    if os.path.isdir(args.base_dir):
        for d in sorted(os.listdir(args.base_dir)):
            p = os.path.join(args.base_dir, d, "results.jsonl")
            v = load_verdicts(p)
            if v:
                configs[d] = v

    # 1) 主表
    os.makedirs(args.out_dir, exist_ok=True)
    table_path = os.path.join(args.out_dir, "main_table.csv")
    lat = defaultdict(list)
    for line in open(args.ours, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            if "latency_ms" in r:
                lat["ours"].append(r["latency_ms"])

    rows = []
    for name, verdicts in configs.items():
        s = summarize(cases, verdicts, incomplete_as)
        s["config"] = name
        s["p50_ms"] = round(p50(lat.get(name, [])), 1) if lat.get(name) else ""
        rows.append(s)
    with open(table_path, "w", newline="", encoding="utf-8") as f:
        cols = ["config", "n", "recall_k", "recall_n", "recall", "fpr_k", "fpr_n", "fpr", "undet", "p50_ms"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"{'config':18s} {'n':>5s} {'recall':>12s} {'FPR':>10s} {'UNDET':>6s} {'p50ms':>7s}")
    print("-" * 62)
    for r in rows:
        print(f"{r['config']:18s} {r['n']:5d} "
              f"{r['recall_k']:3d}/{r['recall_n']:<3d}{r['recall']:6.1%} "
              f"{r['fpr_k']:3d}/{r['fpr_n']:<3d}{r['fpr']:5.1%} "
              f"{r['undet']:6d} {str(r['p50_ms']):>7s}")

    # 2) 配对检验 + Holm
    bases = [n for n in configs if n != args.ours_name]
    if bases:
        res = {}
        for b in bases:
            res[b] = mcnemar_pair(cases, ours, configs[b], incomplete_as)
        adj = holm([res[b]["p"] for b in bases])
        detail_path = os.path.join(args.out_dir, "paired_detail.csv")
        with open(detail_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["cid", "spec", "ours_verdict", "base_verdict", "ours_ok", "base_ok", "baseline"])
            for b in bases:
                for row in res[b]["detail"]:
                    w.writerow(list(row) + [b])
        mcn_path = os.path.join(args.out_dir, "mcnemar.csv")
        with open(mcn_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["baseline", "n", "b_ours_only", "c_base_only", "p_raw", "p_holm", "significant_0.05"])
            for b, p_adj in zip(bases, adj):
                w.writerow([b, res[b]["n"], res[b]["b"], res[b]["c"],
                            f"{res[b]['p']:.6g}", f"{p_adj:.6g}", int(p_adj < 0.05)])
        print(f"\n配对检验（family = {len(bases)} 个基线，Holm 校正）")
        print(f"{'baseline':18s} {'n':>5s} {'b':>4s} {'c':>4s} {'p_raw':>9s} {'p_holm':>9s}")
        print("-" * 56)
        for b, p_adj in zip(bases, adj):
            print(f"{b:18s} {res[b]['n']:5d} {res[b]['b']:4d} {res[b]['c']:4d} "
                  f"{res[b]['p']:9.4g} {p_adj:9.4g}")

    # 3) 召回 CI（聚类 bootstrap，只在"应当拒绝"的正例上算，不能混入对照）
    corr = {cid: int(bool(case_correct(c, ours.get(cid, "UNDETERMINED"), incomplete_as)))
            for cid, c in cases.items() if is_scored(c) and is_should_reject(c)}
    corr = {k: v for k, v in corr.items() if ours.get(k) not in ("UNDETERMINED", None)}
    lo, hi = cluster_bootstrap_ci(list(cases.values()), "spec", corr)
    print(f"\n本文方法 recall 聚类 bootstrap 95% CI：[{lo:.1%}, {hi:.1%}]")
    print(f"-> {table_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

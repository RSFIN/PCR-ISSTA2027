#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RQ1–RQ3 全量评测运行器（主方法 D1 = 差分 + 自动编译双边契约）。

铁律（B1 修复过三处缺陷后定下）：轨迹集必须与 check_corpus.py **逐条相同**，
即 traces.json 的定向轨迹 + 40 条 random.Random(crc32(spec)) 的 gen_trace。
用另一套轨迹等于换一台仪器测同一批样本。

每个 (spec, patch) 只执行一次 44×2 次 run，diffs / snaps / 输出序列全部缓存，
以下配置共用这批缓存（verdict_from_diffs 的用途）：
    main     Ê 内全轨迹（定向 + 随机），上界 + 下界         ← RQ1/RQ2 主判定
    ood      仅 40 条无约束随机轨迹（实验设计 §5.4 分布外对照）
    sample5  每 5 周期抽样比较（§5.1 聚合陷阱 / A4 的方法学演示）
    upper    仅上界（require 置空，消融锚，不进主表）

三级分析单位（§5.1）：
    point   差异点数 / 未许可差异点数          只作诊断
    event   触发边沿事件，窗口内有越界即算一个   辅助
    program 一条 (P,C,P')，主指标按唯一补丁文件

用法：
    python run_rq.py                 # 全量
    python run_rq.py --limit 12      # 冒烟
    python run_rq.py --resume        # 断点续跑
产物：eval/rq_runs.jsonl（逐组明细，可复算）
"""
import argparse
import csv
import json
import os
import random
import sys
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from stlang import parse                                              # noqa: E402
from engine import (run, diff_outputs, diff_sampled, verdict_from_diffs,   # noqa: E402
                    ast_sig, _prep, trigger_times, covered)
from check_corpus import gen_trace                                    # noqa: E402

CYCLE_MS = 10
N_TRACES = 40
N_CYCLES = 300
CASES = os.path.join(HERE, "eval", "rq_cases.tsv")
OUT = os.path.join(HERE, "eval", "rq_runs.jsonl")


def load_spec(spec):
    """复刻 check_corpus.check 的轨迹构造，逐条一致。"""
    d = os.path.join(HERE, "corpus_auto", spec)
    meta = json.load(open(os.path.join(d, "contract.json"), encoding="utf-8"))
    orig = parse(open(os.path.join(d, "orig.st"), encoding="utf-8").read())
    directed = json.load(open(os.path.join(d, "traces.json"), encoding="utf-8"))
    n_cycles = int(meta.get("n_cycles", N_CYCLES))
    style = meta.get("trace_style", "normal")
    rng = random.Random(zlib.crc32(spec.encode()))
    traces = list(directed) + [
        gen_trace(orig.inputs, n_cycles, rng, style) for _ in range(N_TRACES)
    ]
    contract = meta.get("contract", {"clauses": []})
    clauses = _prep(contract.get("clauses", []))
    reqs = _prep(contract.get("require", []))
    # 事件窗口跨度：取窗口上界最大值；always 型用 pilot 的 90 拍
    wins = [c.get("window", [0, 90])[1] for c in clauses if not c.get("always")]
    span = max(wins) if wins else 90
    return dict(meta=meta, orig=orig, traces=traces, n_directed=len(directed),
                clauses=clauses, reqs=reqs, span=span,
                change_kind=meta.get("change_kind", "normal"))


def uncovered_of(diffs, snaps, clauses):
    trig = [trigger_times(snaps, c) for c in clauses]
    return [d for d in diffs if not covered(d, clauses, trig, snaps)]


def event_counts(spec_ctx, diffs_list, snaps_list, s5_list, n_directed):
    """触发边沿级（run_w1.event_miss_rate 的推广），仅在契约含 edge 的语料上可数。

    n_events          该补丁在定向轨迹上遇到的触发边沿总数
    n_events_diff     其中窗口内确实出现相对 orig 差异点的事件（"真实工况"）
    n_events_hit      其中窗口内出现未许可差异点的事件（主方法逐周期，必 == diff 数）
    n_events_hit_s5   其中窗口内在每 5 周期抽样下仍可见未许可差异点的事件
                      → 1 - hit_s5/diff 即 pilot 报的"按事件漏检率"
    """
    clauses, span = spec_ctx["clauses"], spec_ctx["span"]
    n_ev = n_diff = n_hit = n_hit_s5 = 0
    for i in range(n_directed):
        snaps, diffs = snaps_list[i], diffs_list[i]
        if not diffs:
            continue
        trigs = [trigger_times(snaps, c) for c in clauses]
        taus = sorted({t for ts in trigs if ts is not None for t in ts})
        if not taus:                     # always 型契约：无边沿可数，单独统计覆盖率
            continue
        unc = uncovered_of(diffs, snaps, clauses)
        unc5 = uncovered_of(s5_list[i], snaps, clauses)
        for tau in taus:
            n_ev += 1
            in_win = lambda ds: any(tau <= d["cycle"] <= tau + span for d in ds)  # noqa: E731
            if not in_win(diffs):
                continue
            n_diff += 1
            if in_win(unc):
                n_hit += 1
            if in_win(unc5):
                n_hit_s5 += 1
    return n_ev, n_diff, n_hit, n_hit_s5


def eval_patch(ctx, spec, case, patch_path):
    orig, traces = ctx["orig"], ctx["traces"]
    clauses, reqs = ctx["clauses"], ctx["reqs"]
    t0 = time.perf_counter()
    mod = parse(open(patch_path, encoding="utf-8").read())
    structural = ast_sig(mod) != ast_sig(orig)

    diffs_list, snaps_list, outs_list = [], [], []
    for tr in traces:
        o1, s1 = run(orig, tr, CYCLE_MS)
        o2, _ = run(mod, tr, CYCLE_MS)
        diffs_list.append(diff_outputs(o1, o2))
        snaps_list.append(s1)
        outs_list.append((o1, o2))
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    n_dir = ctx["n_directed"]
    # ---- 主判定：Ê 内全轨迹，双边契约
    vm = verdict_from_diffs(diffs_list, snaps_list, clauses, reqs, structural)
    # ---- 分布外：仅随机 40 条
    vo = verdict_from_diffs(diffs_list[n_dir:], snaps_list[n_dir:], clauses, reqs, structural)
    # ---- 每 5 周期抽样（复用输出序列，与 pilot 的 diff_sampled 同构）
    s5 = [diff_sampled(o1, o2, 5) for o1, o2 in outs_list]
    vs = verdict_from_diffs(s5, snaps_list, clauses, reqs, structural)
    # ---- 仅上界（消融锚）
    vu = verdict_from_diffs(diffs_list, snaps_list, clauses, [], structural)

    # ---- 点级：总差异点 / 未许可差异点 / 有未许可差异的轨迹数
    n_diffs = sum(len(d) for d in diffs_list)
    unc_per = [uncovered_of(d, snaps_list[i], clauses)
               for i, d in enumerate(diffs_list)]
    n_unc = sum(len(u) for u in unc_per)
    n_tr_unc = sum(1 for u in unc_per if u)

    # ---- 触发边沿级（仅定向轨迹，Ê 内）
    n_ev, n_ev_diff, n_ev_hit, n_ev_hit_s5 = event_counts(
        ctx, diffs_list, snaps_list, s5, n_dir)

    return dict(case_id=case["case_id"], arm=case["arm"], spec=spec,
                op=case["op"], kind=case["kind"], expected=case["expected"],
                expected_miss=case["expected_miss"] == "1",
                note=case["note"],
                verdict=vm["verdict"], reason=vm["reason"],
                ood_verdict=vo["verdict"], sample5_verdict=vs["verdict"],
                upper_verdict=vu["verdict"],
                n_uncovered=vm["n_uncovered"],
                unmet_requirements=vm["unmet_requirements"],
                max_run=vm["max_run"],
                first_uncovered_cycle=vm["first_uncovered_cycle"],
                n_diffs=n_diffs, n_unc_points=n_unc, n_traces_unc=n_tr_unc,
                n_events=n_ev, n_events_diff=n_ev_diff,
                n_events_hit=n_ev_hit, n_events_hit_s5=n_ev_hit_s5,
                has_edge=any("edge" in c for c in ctx["meta"]["contract"].get("clauses", [])),
                n_traces=len(traces), n_directed=n_dir,
                latency_ms=round(elapsed_ms, 3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    cases = list(csv.DictReader(open(CASES, encoding="utf-8"), delimiter="\t"))
    done = set()
    if args.resume and os.path.exists(args.out):
        for line in open(args.out, encoding="utf-8"):
            if line.strip():
                done.add(json.loads(line)["case_id"])
        print(f"resume：跳过 {len(done)} 条已完成")
    todo = [c for c in cases if c["case_id"] not in done]
    if args.limit:
        todo = todo[:args.limit]

    # 按 spec 分组，orig / 轨迹只构造一次
    by_spec = {}
    for c in todo:
        by_spec.setdefault(c["spec"], []).append(c)

    t_start = time.perf_counter()
    n_ok = n_err = 0
    with open(args.out, "a" if args.resume else "w", encoding="utf-8") as fo:
        for si, (spec, cs) in enumerate(sorted(by_spec.items()), 1):
            try:
                ctx = load_spec(spec)
            except Exception as e:                                  # noqa: BLE001
                for c in cs:
                    fo.write(json.dumps(dict(case_id=c["case_id"], arm=c["arm"],
                                             spec=spec, op=c["op"], kind=c["kind"],
                                             expected=c["expected"],
                                             expected_miss=c["expected_miss"] == "1",
                                             note=c["note"], verdict="UNDETERMINED",
                                             reason=f"spec-load: {type(e).__name__}: {e}",
                                             latency_ms=0), ensure_ascii=False) + "\n")
                    n_err += 1
                continue
            for c in cs:
                try:
                    rec = eval_patch(ctx, spec, c, os.path.join(HERE, c["patch"]))
                    n_ok += 1
                except Exception as e:                              # noqa: BLE001
                    rec = dict(case_id=c["case_id"], arm=c["arm"], spec=spec,
                               op=c["op"], kind=c["kind"], expected=c["expected"],
                               expected_miss=c["expected_miss"] == "1",
                               note=c["note"], verdict="UNDETERMINED",
                               reason=f"{type(e).__name__}: {e}", latency_ms=0)
                    n_err += 1
                fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fo.flush()
            if si % 10 == 0 or si == len(by_spec):
                print(f"  [{si}/{len(by_spec)}] {spec}: "
                      f"累计 {n_ok} 成功 / {n_err} 异常，"
                      f"用时 {time.perf_counter() - t_start:.0f}s", flush=True)
    print(f"完成：{n_ok} 组判定 / {n_err} 异常，用时 "
          f"{time.perf_counter() - t_start:.1f}s → {args.out}")


if __name__ == "__main__":
    main()

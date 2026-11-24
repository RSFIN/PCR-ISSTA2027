#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""一条命令复现论文里的每一个数（artifact 入口）。

    python reproduce.py              # 快跑：环境 + 统计 + 配对检验 + 哈希核对（约 20 秒）
    python reproduce.py --full       # 全量：再加 96 条语料验收 + 522 组重跑（约 4 分钟）
    python reproduce.py --full --rerun   # 连 522 组判定都重算（本地纯计算，无 API）

它做四件事，任何一件失败就以非零码退出：
  1. 环境断言：版本 / 零第三方依赖 / OSCAT 原文校验和
  2. 语料验收：96 条三元组全部 ACCEPTED（--full）
  3. 统计复算：重算 RQ1–RQ3，并与已提交的 rq_stats.json 逐字段对照（容忍 1e-6）
  4. 口径自检：paired_stats 的 14 项数学自检 + 发包哈希核对

设计原则：**不产生新数字，只复算已有数字**。复算不出来就说明 artifact 坏了，
而不是"结果可能变了"。
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

PACKAGES = {
    "dispatch/package_A_static-and-verdict.zip":
        "1483a9f97545be23c5e6b141141df0aff8110c15b8c923ccf9b504d526bf1b8f",
    "dispatch/package_B_execution-and-formal.zip":
        "4230cd14c453acb8466af0c2724fd3a4f7dc58becb8657d90864f4914a19f4ae",
}

results = []


def step(name):
    def deco(fn):
        def wrapper(*a, **kw):
            print(f"\n[{name}]")
            try:
                ok, detail = fn(*a, **kw)
            except Exception as e:  # noqa: BLE001
                ok, detail = False, f"异常：{type(e).__name__}: {e}"
            print(f"  {'PASS' if ok else 'FAIL'}  {detail}")
            results.append((name, ok, detail))
            return ok
        return wrapper
    return deco


def run(cmd, timeout=600):
    p = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


@step("1/4 环境")
def check_env():
    rc, out = run([PY, "check_env.py", "-q"], timeout=120)
    return rc == 0, (out.strip().splitlines() or ["(无输出)"])[-1][:160]


@step("2/4 语料验收（96 条主库 + 5 条上游探针）")
def check_corpus():
    """逐条对照 eval/corpus_manifest.tsv：主库必须全 ACCEPT，
    ext_toggle 必须恰好被拒（§4.4 的形式化边界），其余探针 ACCEPT。"""
    mf = os.path.join(HERE, "eval", "corpus_manifest.tsv")
    rows = []
    with open(mf, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            spec, st, exp, note = (line.rstrip("\n").split("\t") + ["", "", "", ""])[:4]
            rows.append((spec, st, exp, note))

    present = {d for d in os.listdir(os.path.join(HERE, "corpus_auto"))
               if os.path.isdir(os.path.join(HERE, "corpus_auto", d))}
    missing = [r[0] for r in rows if r[0] not in present]
    stray = sorted(present - {r[0] for r in rows})
    bad = []
    for spec, st, exp, note in rows:
        if spec in missing:
            continue
        rc, _ = run([PY, "check_corpus.py", os.path.join("corpus_auto", spec)], timeout=120)
        want = (rc == 0)
        if want != (exp == "ACCEPT"):
            bad.append("%s(expect %s)" % (spec, exp))

    n_main = sum(1 for r in rows if r[1] == "main")
    detail = "%d/%d 与清单一致" % (len(rows) - len(bad) - len(missing), len(rows))
    if bad:
        detail += "；偏离：%s" % bad[:3]
    if missing:
        detail += "；缺目录：%s" % missing[:3]
    if stray:
        detail += "；清单外目录：%s" % stray[:3]
    return (not bad and not missing and not stray), detail


@step("3/4 统计复算")
def recompute():
    old_path = os.path.join(HERE, "eval", "rq_stats.json")
    old = json.load(open(old_path, encoding="utf-8"))
    rc, out = run([PY, "analyze_rq.py"], timeout=600)
    if rc != 0:
        return False, f"analyze_rq.py 失败：{out.strip().splitlines()[-1][:160]}"
    new = json.load(open(old_path, encoding="utf-8"))

    diffs = []

    def walk(a, b, path=""):
        if isinstance(a, dict) and isinstance(b, dict):
            for k in a:
                walk(a[k], b.get(k), f"{path}.{k}")
        elif isinstance(a, float) and isinstance(b, (int, float)):
            if abs(a - b) > 1e-6:
                diffs.append(f"{path}: {a} → {b}")
        elif a != b:
            diffs.append(f"{path}: {a} → {b}")

    walk(old, new)
    recall = new.get("RQ1", {}).get("recall", 0)
    return (not diffs), (f"recall {recall:.4f}，与提交值一致" if not diffs
                         else f"{len(diffs)} 处不一致：{diffs[:3]}")


@step("4/4 口径自检与哈希")
def selftest_and_hash():
    msgs = []
    ok = True
    rc, out = run([PY, "paired_stats.py", "--selftest"], timeout=180)
    ok = ok and rc == 0
    msgs.append("paired_stats 自检 " + ("通过" if rc == 0 else "失败"))

    for rel, want in PACKAGES.items():
        p = os.path.join(HERE, rel)
        if not os.path.isfile(p):
            msgs.append(f"{os.path.basename(rel)} 缺失")
            ok = False
            continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        good = h == want
        ok = ok and good
        msgs.append(f"{os.path.basename(rel)} {'✓' if good else '✗ ' + h[:16]}")
    return ok, "；".join(msgs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="加跑 96 条语料验收")
    ap.add_argument("--rerun", action="store_true", help="连同 522 组判定一起重算")
    args = ap.parse_args()

    check_env()
    if args.rerun:
        print("\n[重跑 522 组判定]")
        rc, out = run([PY, "run_rq.py"], timeout=1800)
        print(f"  {'PASS' if rc == 0 else 'FAIL'}  {out.strip().splitlines()[-1][:160]}")
        if rc != 0:
            results.append(("重跑", False, "run_rq.py 失败"))
    if args.full:
        check_corpus()
    recompute()
    selftest_and_hash()

    n_fail = sum(1 for _, ok, _ in results if not ok)
    print("\n" + "=" * 60)
    print(f"{len(results) - n_fail}/{len(results)} 通过" + ("　✅ 可交付" if n_fail == 0 else f"　❌ {n_fail} 项失败"))
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

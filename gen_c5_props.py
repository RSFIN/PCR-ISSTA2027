#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 C5 的 96 份属性文件（inputs/c5_props/<name>.yaml）。

依据：
  - 模板：B 组 `baselines/c4_bmc_manual/props/_template.yaml`（三槽固定顺序 scope → guard → window）
  - 内容：主库自动契约 `corpus_auto/<name>/contract.json`
  - 接口：`corpus_auto/<name>/orig.st` 的 VAR_OUTPUT 列表

设计约束（见《人工标注口径与判断依据》§11 与 11/12 前置材料清单 §1）：
  1. 三槽固定、顺序固定，不适用的槽保留并 active:false + reason code；
  2. 与 C4 结构逐字同形（同键、同序），差异只在数值与变量名；
  3. reason code 仅取 NO_COMPARABLE_OUT / NO_WINDOW / NO_ANCHOR。

用法：python gen_c5_props.py [--out _deliver/c5_props]
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stlang import parse  # noqa: E402

TIME_KW = ("秒", "毫秒", "ms", "MS", "延时", "保持", "去抖", "T#")


PLAIN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def q(s):
    """安全标识符裸写（与模板一致），其余用双引号。"""
    if s is None:
        return "null"
    s = str(s)
    if PLAIN.match(s):
        return s
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def qlist(items):
    if not items:
        return "[]"
    return "[" + ", ".join(items) + "]"


def outputs_of(name):
    p = os.path.join(HERE, "corpus_auto", name, "orig.st")
    prog = parse(open(p, encoding="utf-8").read())
    return [d.name for d in prog.outputs]


def intent_of(name, contract):
    """四分类：时序 / 阈值 / 重构 / 加保护。规则与口径文档 §3 一致。"""
    clauses = contract["clauses"]
    if not clauses:
        return "重构"
    c = clauses[0]
    if "window" in c:
        return "时序"
    g = c.get("guard") or ""
    if g and re.search(r"(>=|<=|>|<)\s*-?\d", g):
        return "阈值"
    if g:
        return "加保护"
    order = json.load(open(os.path.join(HERE, "specs", name + ".json"), encoding="utf-8"))["order"]
    for kw, tag in (("保护", "加保护"), ("联锁", "加保护"), ("闭锁", "加保护"), ("互锁", "加保护"),
                    ("阈值", "阈值"), ("报警", "阈值"), ("延时", "时序"), ("保持", "时序"), ("秒", "时序")):
        if kw in order:
            return tag
    return "阈值"


def build(name):
    d = json.load(open(os.path.join(HERE, "corpus_auto", name, "contract.json"), encoding="utf-8"))
    spec = json.load(open(os.path.join(HERE, "specs", name + ".json"), encoding="utf-8"))
    c = d["contract"]
    clauses = c.get("clauses", [])
    cl = clauses[0] if clauses else {}
    outs = outputs_of(name)
    allow = list(cl.get("allow", []))
    missing = [a for a in allow if a not in outs]
    if missing:
        raise SystemExit(f"{name}: allow 里的 {missing} 不在输出列表中 {outs}")

    window = cl.get("window")
    edge = cl.get("edge") or {}
    guard = cl.get("guard")
    has_time = any(k in (spec.get("order") or "") for k in TIME_KW)

    # 槽 0：scope —— 许可范围外必须逐周期相等
    scope_outs = [o for o in outs if o not in allow]
    # 重构类 allow 为空 → 全部输出都必须在 scope 里（逐周期零差异）
    scope_active = bool(scope_outs)
    scope_reason = None if scope_active else "NO_COMPARABLE_OUT"

    # 槽 1：guard —— 工况不成立时必须相等
    guard_active = bool(guard)
    guard_outs = allow if guard_active else []
    guard_reason = None if guard_active else "NO_WINDOW"

    # 槽 2：window —— 窗口外必须相等
    win_active = window is not None
    win_outs = allow if win_active else []
    if win_active:
        win_reason = None
    elif intent_of(name, c) == "重构" or not has_time:
        win_reason = "NO_ANCHOR"     # 时间量在文案里，但契约给不出锚点
        win_reason = "NO_WINDOW"
    else:
        win_reason = "NO_ANCHOR"

    lines = [
        f"name: {name}",
        f"intent: {intent_of(name, c)}",
        "source: auto",
        "reason: null",
        "reason_detail: null",
        "properties:",
    ]

    def slot(tag, kind, active, outs, g, tv, td, lo, hi, reason):
        lines.extend([
            f"  - slot: {tag}",
            f"    kind: {kind}",
            f"    active: {'true' if active else 'false'}",
            f"    outputs: {qlist(outs)}",
            f"    guard: {q(g)}",
            f"    trigger_var: {q(tv)}",
            f"    trigger_dir: {q(td)}",
            f"    window_lo: {'null' if lo is None else lo}",
            f"    window_hi: {'null' if hi is None else hi}",
            f"    reason: {q(reason)}",
        ])

    slot("scope", "equal_outside_allow", scope_active, scope_outs, None, None, None, None, None, scope_reason)
    slot("guard", "equal_when_guard_false", guard_active, guard_outs, guard, None, None, None, None, guard_reason)
    slot("window", "equal_outside_window", win_active, win_outs, None,
         edge.get("var") if win_active else None,
         edge.get("dir") if win_active else None,
         window[0] if win_active else None,
         window[1] if win_active else None,
         win_reason)

    tol = cl.get("tol", 0) or spec.get("tol") or 0
    return "\n".join(lines) + "\n", d, spec, allow, tol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "_deliver", "c5_props"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    names = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(HERE, "specs", "*.json")))
    tol_rows = ["name\ttol\tintent\twindow\ttol_reason"]
    stats = {"active_scope": 0, "active_guard": 0, "active_window": 0, "no_anchor": 0}
    intents = {}
    for n in names:
        text, d, spec, allow, tol = build(n)
        with open(os.path.join(args.out, n + ".yaml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        intent = text.splitlines()[1].split(": ", 1)[1]
        intents[intent] = intents.get(intent, 0) + 1
        if "    active: true" in text.split("  - slot: guard")[0]:
            stats["active_scope"] += 1
        if "  - slot: guard\n    kind: equal_when_guard_false\n    active: true" in text:
            stats["active_guard"] += 1
        if "  - slot: window\n    kind: equal_outside_window\n    active: true" in text:
            stats["active_window"] += 1
        if "    reason: NO_ANCHOR" in text:
            stats["no_anchor"] += 1
        w = d["contract"]["clauses"][0].get("window") if d["contract"]["clauses"] else None
        tol_rows.append(f"{n}\t{tol}\t{intent}\t{w if w else '-'}\t{spec.get('tol_reason') or ''}")

    with open(os.path.join(os.path.dirname(args.out), "c5_tol_reference.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(tol_rows) + "\n")

    print("生成", len(names), "份 →", args.out)
    print("intent 分布", intents)
    print("槽位启用", stats)


if __name__ == "__main__":
    main()

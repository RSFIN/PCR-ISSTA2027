#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""C5 属性文件自检（不依赖 pyyaml）：结构同形 + 语义可复核 + reason code 合法性。

用法：python check_c5_props.py [dir]
输出：逐项 PASS/FAIL，末行汇总；FAIL 时退出码 1。
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stlang import parse  # noqa: E402

KEYS_TOP = ["name", "intent", "source", "reason", "reason_detail", "properties"]
KEYS_SLOT = ["slot", "kind", "active", "outputs", "guard", "trigger_var",
             "trigger_dir", "window_lo", "window_hi", "reason"]
SLOTS = [("scope", "equal_outside_allow"), ("guard", "equal_when_guard_false"),
         ("window", "equal_outside_window")]
REASONS = {"NO_COMPARABLE_OUT", "NO_WINDOW", "NO_ANCHOR"}
INTENTS = {"时序", "阈值", "重构", "加保护"}


def load(path):
    """极简 YAML 读取：只认本模板的形状（块映射 + 三槽列表）。"""
    top, slots, cur = {}, [], None
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("  - "):
            cur = {}
            k, v = line[4:].split(": ", 1)
            cur[k] = v
            slots.append(cur)
        elif line.startswith("    ") and cur is not None:
            k, v = line.strip().split(": ", 1)
            cur[k] = v
        elif not line.startswith(" "):
            if line.endswith(":") and ": " not in line:
                top[line[:-1]] = None
            else:
                k, v = line.split(": ", 1)
                top[k] = v
        else:
            raise ValueError(f"{path}: 无法解析的行 {line!r}")
    return top, slots


def scalar(v):
    if v == "null":
        return None
    if v == "[]":
        return []
    if v.startswith("[") and v.endswith("]"):
        return [x.strip() for x in v[1:-1].split(",") if x.strip()]
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if v in ("true", "false"):
        return v == "true"
    try:
        return int(v)
    except ValueError:
        return v


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "_deliver", "c5_props")
    names = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(HERE, "specs", "*.json"))}
    files = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(d, "*.yaml"))}
    errs = []

    if files != names:
        errs.append(f"文件集合不符：缺 {sorted(names - files)[:5]}，多 {sorted(files - names)[:5]}")

    shape_ref = None
    for n in sorted(files & names):
        top, slots = load(os.path.join(d, n + ".yaml"))
        if list(top) != KEYS_TOP:
            errs.append(f"{n}: 顶层键序不符 {list(top)}")
            continue
        if len(slots) != 3:
            errs.append(f"{n}: 槽数 {len(slots)}")
            continue
        if [s["slot"] for s in slots] != [x[0] for x in SLOTS]:
            errs.append(f"{n}: 槽序不符 {[s['slot'] for s in slots]}")
            continue
        if [s["kind"] for s in slots] != [x[1] for x in SLOTS]:
            errs.append(f"{n}: kind 不符")
            continue
        for s in slots:
            if list(s) != KEYS_SLOT:
                errs.append(f"{n}/{s['slot']}: 键序不符 {list(s)}")
        sig = [(s["slot"], tuple(s.keys())) for s in slots]
        if shape_ref is None:
            shape_ref = sig
        elif sig != shape_ref:
            errs.append(f"{n}: 与首份不同形")

        if scalar(top["intent"]) not in INTENTS:
            errs.append(f"{n}: intent 非法 {top['intent']}")
        if scalar(top["source"]) != "auto":
            errs.append(f"{n}: source 应为 auto")

        outs = [x.name for x in parse(open(os.path.join(HERE, "corpus_auto", n, "orig.st"), encoding="utf-8").read()).outputs]
        allow = json.load(open(os.path.join(HERE, "corpus_auto", n, "contract.json"), encoding="utf-8"))
        allow = allow["contract"]["clauses"][0].get("allow", []) if allow["contract"]["clauses"] else []

        for s in slots:
            act = scalar(s["active"])
            reason = scalar(s["reason"])
            o = scalar(s["outputs"])
            if reason is not None and reason not in REASONS:
                errs.append(f"{n}/{s['slot']}: reason 非法 {reason}")
            if act and not o:
                errs.append(f"{n}/{s['slot']}: active 但 outputs 空")
            if not act and reason is None:
                errs.append(f"{n}/{s['slot']}: 未启用但无 reason")
            if any(x not in outs for x in o):
                errs.append(f"{n}/{s['slot']}: outputs 含非输出变量 {o}")

        scope_expected = [x for x in outs if x not in allow]
        if scalar(slots[0]["outputs"]) != scope_expected:
            errs.append(f"{n}/scope: outputs 应为 {scope_expected}")

        w = slots[2]
        if scalar(w["active"]):
            lo, hi = scalar(w["window_lo"]), scalar(w["window_hi"])
            if not (isinstance(lo, int) and isinstance(hi, int) and 0 <= lo <= hi):
                errs.append(f"{n}/window: 区间非法 {lo}..{hi}")
            if scalar(w["trigger_var"]) is None or scalar(w["trigger_dir"]) not in ("rising", "falling"):
                errs.append(f"{n}/window: 缺 trigger")
            if scalar(w["outputs"]) != allow:
                errs.append(f"{n}/window: outputs 应等于 allow")

    print(f"文件数 {len(files)}，spec 数 {len(names)}")
    if errs:
        print(f"FAIL {len(errs)} 项：")
        for e in errs[:25]:
            print("  -", e)
        sys.exit(1)
    print("PASS 全部检查通过：集合一致 / 同形 / reason 合法 / scope 可复核 / window 区间合法")


if __name__ == "__main__":
    main()

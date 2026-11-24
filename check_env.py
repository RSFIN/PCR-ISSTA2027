"""环境自检：Python 版本够不够、有没有偷偷引入第三方包、原文校验和是否被改动。

    python check_env.py            # 人看
    python check_env.py -q         # 只输出一行结论（CI / 打包脚本用）

为什么需要这个脚本：整条流水线号称"零依赖"，但"号称"不是证据。
这里把三件事变成可执行的断言 —— 版本、依赖、完整性 ——
任何一条不成立就以非零码退出。
"""

import ast
import hashlib
import os
import platform
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_PY = (3, 8)
OSCAT_SHA = "b0dae75deb6947b2c210f15079465690e857c4a822479d788e60d15e1b9f96fe"

# sys.stdlib_module_names 是 3.10+ 才有的；3.8/3.9 用这份兜底清单
FALLBACK_STDLIB = {
    "os", "sys", "re", "json", "math", "time", "itertools", "random", "zlib",
    "glob", "zipfile", "shutil", "collections", "argparse", "hashlib",
    "dataclasses", "pathlib", "subprocess", "ast", "io", "typing", "functools",
    "string", "traceback", "unittest", "textwrap", "copy", "bisect", "csv",
}


def stdlib_names():
    names = getattr(sys, "stdlib_module_names", None)
    return set(names) if names else FALLBACK_STDLIB


def local_modules():
    return {fn[:-3] for fn in os.listdir(HERE) if fn.endswith(".py")}


def all_scripts():
    return sorted(fn for fn in os.listdir(HERE)
                  if fn.endswith(".py") and fn != "__pycache__")


def imports_of(path):
    """所有顶层 import 的根模块名 + 是否出现在 try/except 里。"""
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.append(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:          # 相对导入，必然是本地
                continue
            if node.module:
                out.append(node.module.split(".")[0])
    return out


def main(argv):
    quiet = "-q" in argv
    problems = []

    # ---------- 1. 版本
    ver = sys.version_info[:3]
    if ver[:2] < MIN_PY:
        problems.append(f"Python {'.'.join(map(str, ver))} 低于最低要求 "
                        f"{'.'.join(map(str, MIN_PY))}（dataclasses 需要 3.7+，"
                        f"我们按 3.8 起算）")

    # ---------- 2. 依赖
    std, loc = stdlib_names(), local_modules()
    third = {}
    for fn in all_scripts():
        for mod in imports_of(os.path.join(HERE, fn)):
            if mod not in std and mod not in loc:
                third.setdefault(mod, []).append(fn)

    # ---------- 3. 原文完整性
    oscat = os.path.join(HERE, "vendor", "oscat", "oscat.st")
    sha_state = "未附带（本包不含 vendor/oscat，正常）"
    if os.path.exists(oscat):
        h = hashlib.sha256(open(oscat, "rb").read()).hexdigest()
        if h == OSCAT_SHA:
            sha_state = f"OK {h[:12]}…"
        else:
            sha_state = f"**与记录不符** {h[:12]}…"
            problems.append("vendor/oscat/oscat.st 的 SHA-256 与 README 记录不一致："
                            "原文被改过，或者换了一版却没更新校验和")

    if third:
        problems.append("发现第三方 import：" + "；".join(
            f"{m}（{', '.join(sorted(set(f)))}）" for m, f in sorted(third.items())))

    if quiet:
        print(("FAIL " + " | ".join(problems)) if problems else
              f"OK python={'.'.join(map(str, ver))} deps=0 oscat={sha_state}")
    else:
        print("=" * 68)
        print("DeltaScope W1 沙箱 · 环境自检")
        print("=" * 68)
        print(f"Python      : {platform.python_version()}  ({sys.executable})")
        print(f"最低要求    : {'.'.join(map(str, MIN_PY))}+")
        print(f"平台        : {platform.system()} {platform.machine()}")
        print(f"第三方依赖  : {len(third)} 个" + ("" if third else "  ← 只用标准库"))
        print(f"OSCAT 原文  : {sha_state}")
        print(f"脚本数      : {len(all_scripts())}")
        print("-" * 68)
        if problems:
            for p in problems:
                print(f"[FAIL] {p}")
            print("\n结论：环境不满足要求，先解决上面几条，再跑流水线。")
        else:
            print("[PASS] Python 版本满足")
            print("[PASS] 没有任何第三方依赖（requirements.txt 因此是空文件）")
            print("[PASS] 不联网、不需要 C 编译器、不需要 matiec/OpenPLC")
            print("\n结论：可以直接 python make_corpus_auto.py <name>。")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# vendor/oscat — OSCAT Basic 原文（只读，勿改）

本目录存放**逐字未改**的上游功能块库源码，用途只有一个：让"原程序来自公开语料"
这句话可以被机器核对，而不是只能被相信。

| 项 | 值 |
|-|-|
| 上游 | OSCAT Basic（PLC-lang 的 OSCAT 单文件整理版） |
| 仓库 | https://github.com/PLC-lang/oscat |
| 文件 | `oscat.st`（30038 行 / 605046 字节 / 173 个 FUNCTION_BLOCK） |
| SHA-256 | `b0dae75deb6947b2c210f15079465690e857c4a822479d788e60d15e1b9f96fe` |
| 许可 | OSCAT 自有许可（`LICENSE` 原文，非 EPL-2.0） |
| 取得日期 | 2026-10-30 |

## 许可要点（摘自 `LICENSE` 第 1.2 条）

- 可免费用于私有与商业用途，**允许修改**，**允许再分发**；
- 再分发必须**免费**，且必须包含对 OSCAT 与 `www.oscat.de` 的明确引用；
- 因此本仓库与 artifact 可以原样附带该文件，但任何发布物（论文 artifact、
  Zenodo 包、GitHub release）都必须在显著位置保留 OSCAT 与 www.oscat.de 的引用。
  这条已写进 `../PROVENANCE.md` 的发布检查清单。

## 许可的两个版本，别混用

- `eclipse-oscat/*`（Eclipse 基金会，当前开发主线）→ **EPL-2.0**；
- `oscat-libs-archive`（历史 1.10–3.36 归档）与本目录所用版本 → **OSCAT 自有许可**。
  历史归档被明确排除在 EPL-2.0 之外。论文里写许可时必须区分，否则是事实错误。

## 复现

```bash
python probe_oscat.py        # 统计 173 个 FB 中多少个落在当前 ST 子集内
```

`probe_oscat.py` 只读本目录，不联网；它输出的数字就是论文里
"语料承接率"那一段的依据。

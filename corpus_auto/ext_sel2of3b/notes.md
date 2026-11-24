# ext_sel2of3b

- 程序来源：OSCAT Basic SEL2_OF_3B（三取二冗余表决），正文逐字
- 变更单：三个传感器状态不一致时，不一致告警的确认延时由 500 毫秒改为 1 秒；其余逻辑不变。
- 自动编译：`[{"edge": {"var": "xS1", "dir": "rising"}, "allow": ["yDisagree"], "window": [0, 200]}]`
- 自动下界：`[{"shape": {"len": 50, "tol": 0}, "allow": ["yDisagree"]}]`

## 编译器给出的依据

- 时序类：许可 = 触发 xS1 rising 后 200 拍内、输出 ['yDisagree'] 的变化（= b 100 + 重启 2×50 + 结构延迟 0）
- 幅度约束：差异段应长约 50±0 个扫描周期（= |1000-500|ms / 10ms，容差 ±0%）

- 触发来源：文本无线索 → 目标定时器 IN 表达式的首个信号
- 窗口分解：{"b": 100, "n_restart": 2, "moved": 50, "struct_delay": 0}
- 重启源：['xS2', 'xS3']

## 注入的越界（O1–O8）：5 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O1 | O1 改 yVote：追加 AND NOT xS1 | cross-variable | G0 | 997 | **主 bad** | `bad_O1.st` |
| O1 | O1 改 yVote：追加 AND NOT xS2 | cross-variable | G0 | 600 | 备选 | `bad_O1_2.st` |
| O3 | O3 T#1S → T#1020MS（+2 拍） | same-variable-window | G1 | 4 | 备选 | `bad_O3.st` |
| O8 | O8 删去 AND xS2 | same-variable-guard | G2 | 797 | 备选 | `bad_O8.st` |
| O8 | O8 删去 AND xS3 | same-variable-guard | G2 | 797 | 备选 | `bad_O8_2.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（3/3/3 条语句）
- [PASS] 输出接口一致：['yVote', 'yDisagree']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 4 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 31/44 条轨迹上产生差异（最多 92 个点）
- [PASS] 越界改动被编译契约检出 43/44 条轨迹，最早第 0 个周期（可检出的粒度：L/G0/G1/G2/编译契约）
- [PASS] bad 相对 good 另有差异（43/44 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=cross-variable）

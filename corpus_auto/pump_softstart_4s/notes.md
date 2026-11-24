# pump_softstart_4s

- 程序来源：W1 沙箱自建（泵站）
- 变更单：yValve 上升沿后，泵软启动延时由 0 秒改为 4 秒；其余逻辑不变。
- 自动编译：`[{"edge": {"var": "yValve", "dir": "rising"}, "allow": ["yPump"], "window": [0, 1600]}]`
- 自动下界：`[{"shape": {"len": 400, "tol": 0}, "allow": ["yPump"]}]`

## 编译器给出的依据

- 时序类：许可 = 触发 yValve rising 后 1600 拍内、输出 ['yPump'] 的变化（= b 400 + 重启 3×400 + 结构延迟 0）
- 幅度约束：差异段应长约 400±0 个扫描周期（= |4000-0|ms / 10ms，容差 ±0%）

- 触发来源：文本直呼标识符 yValve
- 窗口分解：{"b": 400, "n_restart": 3, "moved": 400, "struct_delay": 0}
- 重启源：['xAuto', 'xLevelLow', 'xManual']

## 注入的越界（O1–O8）：5 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O1 | O1 改 yValve：追加 AND NOT xAuto | cross-variable | G0 | 1674 | **主 bad** | `bad_O1.st` |
| O1 | O1 改 yValve：追加 AND NOT xManual | cross-variable | G0 | 1434 | 备选 | `bad_O1_2.st` |
| O2 | O2 删去 AND NOT xLevelLow | same-variable-guard | G2 | 560 | 备选 | `bad_O2.st` |
| O3 | O3 T#4S → T#4020MS（+2 拍） | same-variable-window | G1 | 4 | 备选 | `bad_O3.st` |
| O6 | O6 对调 yValve / yPump 的赋值顺序 | same-variable-window | G1 | 794 | 备选 | `bad_O6.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（4/4/4 条语句）
- [PASS] 输出接口一致：['yValve', 'yPump', 'yAlarm']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 4 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 44/44 条轨迹上产生差异（最多 400 个点）
- [PASS] 越界改动被编译契约检出 43/44 条轨迹，最早第 0 个周期（可检出的粒度：L/G0/G1/G2/编译契约）
- [PASS] bad 相对 good 另有差异（43/44 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=cross-variable）

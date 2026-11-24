# standby_fault_a

- 程序来源：W1 沙箱自建（主备泵站），自建
- 变更单：故障时允许主泵继续运行，故障闭锁只约束备用泵；其余逻辑不变。
- 自动编译：`[{"always": true, "allow": ["yPumpA", "yPumpB", "ySwapAlarm"], "guard": "xFault"}]`
- 自动下界：`[{"always": true, "allow": ["yPumpA", "yPumpB", "ySwapAlarm", "yLamp"]}]`

## 编译器给出的依据

- 保护类：许可 = `xFault` 工况下 ['yPumpA', 'yPumpB', 'ySwapAlarm'] 的变化
- 无法判定意图 → 退化为存在性约束（最弱下界）

- 触发来源：—
- 窗口分解：{}
- 重启源：[]

## 注入的越界（O1–O8）：5 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O1 | O1 改 yLamp：追加 AND NOT xAuto | cross-variable | G0 | 1407 | **主 bad** | `bad_O1.st` |
| O1 | O1 改 yLamp：追加 AND NOT xManual | cross-variable | G0 | 494 | 备选 | `bad_O1_2.st` |
| O2 | O2 删去 AND NOT xManual | same-variable-guard | G2 | 494 | 备选 | `bad_O2.st` |
| O2 | O2 删去 AND NOT xManual | same-variable-guard | G2 | 484 | 备选 | `bad_O2_2.st` |
| O8 | O8 删去 AND xFault | same-variable-guard | G2 | 1127 | 备选 | `bad_O8.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（4/4/4 条语句）
- [PASS] 输出接口一致：['yPumpA', 'yPumpB', 'ySwapAlarm', 'yLamp']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 4 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 40/44 条轨迹上产生差异（最多 119 个点）
- [PASS] 越界改动被编译契约检出 43/44 条轨迹，最早第 0 个周期（可检出的粒度：L/G0/G1/G2/编译契约）
- [PASS] bad 相对 good 另有差异（43/44 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=cross-variable）

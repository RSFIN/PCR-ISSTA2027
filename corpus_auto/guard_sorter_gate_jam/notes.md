# guard_sorter_gate_jam

- 程序来源：W1 沙箱自建（分拣线主带/闸门/分流），自建
- 变更单：xJam 为 TRUE时，该联锁不再约束手动支路，手动模式下允许闸门开合；xJam 为 TRUE这一前提不变，窗口外维持原闭锁；其余逻辑不变。
- 自动编译：`[{"always": true, "allow": ["yMain", "yDiverter", "yGate", "yAlarm"], "guard": "xJam"}]`
- 自动下界：`[{"always": true, "allow": ["yMain", "yDiverter", "yGate", "yAlarm"]}, {"always": true, "guard": "xJam AND xManual", "allow": ["yGate"]}, {"always": true, "guard": "xJam AND xManual AND NOT xAuto", "allow": ["yGate"]}, {"always": true, "guard": "xJam AND xManual AND NOT xPermit", "allow": ["yGate"]}]`

## 编译器给出的依据

- 保护类：许可 = `xJam` 工况下 ['yMain', 'yDiverter', 'yGate', 'yAlarm'] 的变化
- 无法判定意图 → 退化为存在性约束（最弱下界）
- require_extra（P1 必达子区域）：必达：变更（yGate）必须在旁路条件 [xJam AND xManual] 下可见；必达：旁路与 xAuto 无关，xAuto=0 时变更仍须可见；必达：旁路与 xPermit 无关，xPermit=0 时变更仍须可见

- 触发来源：—
- 窗口分解：{}
- 重启源：[]

## 注入的越界（O1–O8）：2 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O8 | O8 删去 AND xPermit | same-variable-guard | G2 | 180 | **主 bad** | `bad_O8.st` |
| O8 | O8 删去 AND xPermit | same-variable-guard | G2 | 180 | **主 bad** | `bad_O8_2.st` |

未能产生可观测差异而被丢弃的候选：2 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（4/4/4 条语句）
- [PASS] 输出接口一致：['yMain', 'yDiverter', 'yGate', 'yAlarm']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 3 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 42/43 条轨迹上产生差异（最多 265 个点）
- [PASS] 越界改动被编译契约检出 42/43 条轨迹，最早第 0 个周期（可检出的粒度：G2/编译契约）
- [PASS] bad 相对 good 另有差异（42/43 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=same-variable-guard）

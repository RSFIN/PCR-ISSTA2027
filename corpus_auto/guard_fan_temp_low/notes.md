# guard_fan_temp_low

- 程序来源：W1 沙箱自建（烘箱风机/加热/风门），自建
- 变更单：xTemp 断开时，该联锁不再约束手动支路，允许循环风机单独运行；xTemp 断开这一前提不变，窗口外维持原闭锁；其余逻辑不变。
- 自动编译：`[{"always": true, "allow": ["yHeat", "yDamper", "yFan", "yAlarm"], "guard": "NOT xTemp"}]`
- 自动下界：`[{"always": true, "allow": ["yHeat", "yDamper", "yFan", "yAlarm"]}, {"always": true, "guard": "NOT xTemp AND xAuto AND xPermit", "allow": ["yFan"]}, {"always": true, "guard": "NOT xTemp AND xAuto AND xPermit AND NOT xManual", "allow": ["yFan"]}]`

## 编译器给出的依据

- 保护类：许可 = `NOT xTemp` 工况下 ['yHeat', 'yDamper', 'yFan', 'yAlarm'] 的变化
- 无法判定意图 → 退化为存在性约束（最弱下界）
- require_extra（P1 必达子区域）：必达：变更（yFan）必须在旁路条件 [NOT xTemp AND xAuto AND xPermit] 下可见；必达：旁路与 xManual 无关，xManual=0 时变更仍须可见

- 触发来源：—
- 窗口分解：{}
- 重启源：[]

## 注入的越界（O1–O8）：2 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O2 | O2 删去 AND NOT xManual | same-variable-guard | G2 | 175 | **主 bad** | `bad_O2.st` |
| O2 | O2 删去 AND NOT xManual | same-variable-guard | G2 | 175 | **主 bad** | `bad_O2_2.st` |

未能产生可观测差异而被丢弃的候选：2 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（4/4/4 条语句）
- [PASS] 输出接口一致：['yHeat', 'yDamper', 'yFan', 'yAlarm']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 3 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 40/43 条轨迹上产生差异（最多 134 个点）
- [PASS] 越界改动被编译契约检出 42/43 条轨迹，最早第 0 个周期（可检出的粒度：G2/编译契约）
- [PASS] bad 相对 good 另有差异（42/43 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=same-variable-guard）

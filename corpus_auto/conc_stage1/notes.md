# conc_stage1

- 程序来源：W1 沙箱自建（浓度两级报警），形态对应两级气体报警器
- 变更单：可燃气体一级报警阈值由 40 改为 30；其余逻辑不变。
- 自动编译：`[{"always": true, "allow": ["yAlarm1", "yAlarm2", "yPurge"], "guard": "rConc >= 30 AND rConc <= 40"}]`
- 自动下界：`[{"always": true, "allow": ["yAlarm1", "yAlarm2", "yPurge"], "guard": "rConc >= 30 AND rConc <= 40"}]`

## 编译器给出的依据

- 阈值类：许可限定在新覆盖区间 `rConc >= 30 AND rConc <= 40`
- 区间约束：差异必须落在 rConc >= 30 AND rConc <= 40（边界 40→30）

- 触发来源：—
- 窗口分解：{}
- 重启源：[]

## 注入的越界（O1–O8）：3 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O4 | O4 > 70 → > 65 | same-variable-guard | G2 | 158 | **主 bad** | `bad_O4.st` |
| O6 | O6 对调 yAlarm2 / yPurge 的赋值顺序 | same-variable-window | G1 | 22 | 备选 | `bad_O6.st` |
| O8 | O8 删去 AND xPurgeEn | same-variable-guard | G2 | 113 | 备选 | `bad_O8.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（3/3/3 条语句）
- [PASS] 输出接口一致：['yAlarm1', 'yAlarm2', 'yPurge']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 8 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 46/48 条轨迹上产生差异（最多 128 个点）
- [PASS] 越界改动被编译契约检出 43/48 条轨迹，最早第 0 个周期（可检出的粒度：G2/编译契约）
- [PASS] bad 相对 good 另有差异（43/48 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=same-variable-guard）

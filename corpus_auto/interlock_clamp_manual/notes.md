# interlock_clamp_manual

- 程序来源：W1 沙箱自建（三工位互锁矩阵），自建
- 变更单：手动模式下允许夹紧动作，不再受手动闭锁限制；其余逻辑不变。
- 自动编译：`[{"always": true, "allow": ["yClamp", "yPress"], "guard": "xManual"}]`
- 自动下界：`[{"always": true, "allow": ["yClamp", "yPress", "yEject", "yAlarm"]}]`

## 编译器给出的依据

- 保护类：许可 = `xManual` 工况下 ['yClamp', 'yPress'] 的变化
- 无法判定意图 → 退化为存在性约束（最弱下界）

- 触发来源：—
- 窗口分解：{}
- 重启源：[]

## 注入的越界（O1–O8）：5 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O1 | O1 改 yEject：追加 AND NOT xAuto | cross-variable | G0 | 350 | **主 bad** | `bad_O1.st` |
| O1 | O1 改 yEject：追加 AND NOT xManual | cross-variable | G0 | 350 | 备选 | `bad_O1_2.st` |
| O2 | O2 删去 AND NOT xOverload | same-variable-guard | G2 | 175 | 备选 | `bad_O2.st` |
| O8 | O8 删去 AND xReady | same-variable-guard | G2 | 360 | 备选 | `bad_O8.st` |
| O8 | O8 删去 AND xReady | same-variable-guard | G2 | 180 | 备选 | `bad_O8_2.st` |

未能产生可观测差异而被丢弃的候选：1 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（4/4/4 条语句）
- [PASS] 输出接口一致：['yClamp', 'yPress', 'yEject', 'yAlarm']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 2 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 42/42 条轨迹上产生差异（最多 90 个点）
- [PASS] 越界改动被编译契约检出 42/42 条轨迹，最早第 0 个周期（可检出的粒度：L/G0/G1/G2/编译契约）
- [PASS] bad 相对 good 另有差异（42/42 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=cross-variable）

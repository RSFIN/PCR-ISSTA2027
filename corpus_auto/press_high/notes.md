# press_high

- 程序来源：W1 沙箱自建（压力双限报警），复用 OSCAT LIMIT 的上下限语义
- 变更单：压力高压报警阈值由 75 改为 65；其余逻辑不变。
- 自动编译：`[{"always": true, "allow": ["yLoAlarm", "yHiAlarm", "yPump"], "guard": "rPress >= 65 AND rPress <= 75"}]`
- 自动下界：`[{"always": true, "allow": ["yLoAlarm", "yHiAlarm", "yPump"], "guard": "rPress >= 65 AND rPress <= 75"}]`

## 编译器给出的依据

- 阈值类：许可限定在新覆盖区间 `rPress >= 65 AND rPress <= 75`
- 区间约束：差异必须落在 rPress >= 65 AND rPress <= 75（边界 75→65）

- 触发来源：—
- 窗口分解：{}
- 重启源：[]

## 注入的越界（O1–O8）：4 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O2 | O2 删去 AND NOT yLoAlarm | same-variable-guard | G2 | 330 | **主 bad** | `bad_O2.st` |
| O2 | O2 删去 AND NOT yHiAlarm | same-variable-guard | G2 | 1131 | 备选 | `bad_O2_2.st` |
| O4 | O4 < 25 → < 20 | same-variable-guard | G2 | 154 | 备选 | `bad_O4.st` |
| O6 | O6 对调 yHiAlarm / yPump 的赋值顺序 | same-variable-window | G1 | 24 | 备选 | `bad_O6.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（3/3/3 条语句）
- [PASS] 输出接口一致：['yLoAlarm', 'yHiAlarm', 'yPump']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 8 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 46/48 条轨迹上产生差异（最多 262 个点）
- [PASS] 越界改动被编译契约检出 41/48 条轨迹，最早第 0 个周期（可检出的粒度：G2/编译契约）
- [PASS] bad 相对 good 另有差异（41/48 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=same-variable-guard）

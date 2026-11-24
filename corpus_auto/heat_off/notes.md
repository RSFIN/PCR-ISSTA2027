# heat_off

- 程序来源：W1 沙箱自建（温度回差控制），加热/停止双阈值
- 变更单：温度回差控制的停热报警阈值由 60 改为 55；其余逻辑不变。
- 自动编译：`[{"always": true, "allow": ["yHeat", "yAlarm"], "guard": "rTemp >= 55 AND rTemp <= 60"}]`
- 自动下界：`[{"always": true, "allow": ["yHeat", "yAlarm"], "guard": "rTemp >= 55 AND rTemp <= 60"}]`

## 编译器给出的依据

- 阈值类：许可限定在新覆盖区间 `rTemp >= 55 AND rTemp <= 60`
- 区间约束：差异必须落在 rTemp >= 55 AND rTemp <= 60（边界 60→55）

- 触发来源：—
- 窗口分解：{}
- 重启源：[]

## 注入的越界（O1–O8）：1 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O4 | O4 < 45 → < 40 | same-variable-guard | G2 | 71 | **主 bad** | `bad_O4.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（1/1/1 条语句）
- [PASS] 输出接口一致：['yHeat', 'yAlarm']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 7 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 41/47 条轨迹上产生差异（最多 91 个点）
- [PASS] 越界改动被编译契约检出 44/47 条轨迹，最早第 0 个周期（可检出的粒度：G2/编译契约）
- [PASS] bad 相对 good 另有差异（44/47 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=same-variable-guard）

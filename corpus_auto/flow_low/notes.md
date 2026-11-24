# flow_low

- 程序来源：W1 沙箱自建（流量低限报警 + 泵运行联锁）
- 变更单：流量低限报警阈值由 40 改为 50；其余逻辑不变。
- 自动编译：`[{"always": true, "allow": ["yLowFlow", "yTrip"], "guard": "rFlow >= 40 AND rFlow <= 50"}]`
- 自动下界：`[{"always": true, "allow": ["yLowFlow", "yTrip"], "guard": "rFlow >= 40 AND rFlow <= 50"}]`

## 编译器给出的依据

- 阈值类：许可限定在新覆盖区间 `rFlow >= 40 AND rFlow <= 50`
- 区间约束：差异必须落在 rFlow >= 40 AND rFlow <= 50（边界 40→50）

- 触发来源：—
- 窗口分解：{}
- 重启源：[]

## 注入的越界（O1–O8）：1 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O8 | O8 删去 AND yLowFlow | same-variable-guard | G2 | 815 | **主 bad** | `bad_O8.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（2/2/2 条语句）
- [PASS] 输出接口一致：['yLowFlow', 'yTrip']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 8 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 47/48 条轨迹上产生差异（最多 246 个点）
- [PASS] 越界改动被编译契约检出 46/48 条轨迹，最早第 0 个周期（可检出的粒度：G2/编译契约）
- [PASS] bad 相对 good 另有差异（46/48 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=same-variable-guard）

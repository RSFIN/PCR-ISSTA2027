# soc_low

- 程序来源：W1 沙箱自建（电池 SOC 保护），欠压/过压双阈值
- 变更单：电池组欠压保护阈值由 20 改为 30；其余逻辑不变。
- 自动编译：`[{"always": true, "allow": ["yCharge", "yDischarge", "yWarn"], "guard": "rSoc >= 20 AND rSoc <= 30"}]`
- 自动下界：`[{"always": true, "allow": ["yCharge", "yDischarge", "yWarn"], "guard": "rSoc >= 20 AND rSoc <= 30"}]`

## 编译器给出的依据

- 阈值类：许可限定在新覆盖区间 `rSoc >= 20 AND rSoc <= 30`
- 区间约束：差异必须落在 rSoc >= 20 AND rSoc <= 30（边界 20→30）

- 触发来源：—
- 窗口分解：{}
- 重启源：[]

## 注入的越界（O1–O8）：1 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O4 | O4 > 80 → > 75 | same-variable-guard | G2 | 130 | **主 bad** | `bad_O4.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（1/1/1 条语句）
- [PASS] 输出接口一致：['yCharge', 'yDischarge', 'yWarn']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 7 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 45/47 条轨迹上产生差异（最多 408 个点）
- [PASS] 越界改动被编译契约检出 37/47 条轨迹，最早第 1 个周期（可检出的粒度：G2/编译契约）
- [PASS] bad 相对 good 另有差异（37/47 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=same-variable-guard）

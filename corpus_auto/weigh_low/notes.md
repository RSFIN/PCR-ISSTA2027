# weigh_low

- 程序来源：W1 沙箱自建（称重分选），两级阈值 + 剔除
- 变更单：称重分选的下限阈值由 30 改为 40；其余逻辑不变。
- 自动编译：`[{"always": true, "allow": ["ySort", "yReject"], "guard": "iWeight >= 30 AND iWeight <= 40"}]`
- 自动下界：`[{"always": true, "allow": ["ySort", "yReject"], "guard": "iWeight >= 30 AND iWeight <= 40"}]`

## 编译器给出的依据

- 阈值类：许可限定在新覆盖区间 `iWeight >= 30 AND iWeight <= 40`
- 区间约束：差异必须落在 iWeight >= 30 AND iWeight <= 40（边界 30→40）

- 触发来源：—
- 窗口分解：{}
- 重启源：[]

## 注入的越界（O1–O8）：2 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O1 | O1 改 yReady：追加 AND NOT xFeed | cross-variable | G0 | 1790 | **主 bad** | `bad_O1.st` |
| O4 | O4 > 60 → > 55 | same-variable-guard | G2 | 168 | 备选 | `bad_O4.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（2/2/2 条语句）
- [PASS] 输出接口一致：['ySort', 'yReject', 'yReady']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 8 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 46/48 条轨迹上产生差异（最多 282 个点）
- [PASS] 越界改动被编译契约检出 47/48 条轨迹，最早第 0 个周期（可检出的粒度：L/G0/G1/G2/编译契约）
- [PASS] bad 相对 good 另有差异（47/48 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=cross-variable）

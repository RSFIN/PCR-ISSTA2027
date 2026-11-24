# ext_btrig

- 程序来源：OSCAT Basic B_TRIG（双边沿脉冲），正文逐字
- 变更单：输出脉冲改为仅在 xClk 上升沿产生一个扫描周期；其余逻辑不变。
- 自动编译：`[{"always": true, "allow": ["yPulse"]}]`
- 自动下界：`[{"always": true, "allow": ["yPulse"]}]`

## 编译器给出的依据

- 无法判定意图 → 退化为变量级上界（G0，最弱）
- 无法判定意图 → 退化为存在性约束（最弱下界）

- 触发来源：—
- 窗口分解：{}
- 重启源：[]

## 注入的越界（O1–O8）：2 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O2 | O2 删去 AND NOT edge | same-variable-guard | G2 | 1174 | **主 bad** | `bad_O2.st` |
| O6 | O6 对调 yPulse / edge 的赋值顺序 | same-variable-window | G1 | 23 | 备选 | `bad_O6.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（2/2/2 条语句）
- [PASS] 输出接口一致：['yPulse']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 4 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 42/44 条轨迹上产生差异（最多 14 个点）
- [WARN] 已知漏检（expected_miss）：上界退化为变量级（G0）：窗口与工况守卫两维全部丢失（典型诱因：带记忆的赋值——输出在部分分支不被赋值，差异会延续到静态守卫之外）——计入未判定率，不参与召回分母
- [PASS] bad 相对 good 另有差异（44/44 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=same-variable-guard）

# stardelta_ready_bypass

- 程序来源：W1 沙箱自建（星三角启动），复用 `corpus/stardelta`
- 变更单：启动信号有效时不再等待就绪信号，过载保护保持不变；其余逻辑不变。
- 自动编译：`[{"always": true, "allow": ["yMain", "yStar", "yDelta"], "guard": "xStart"}]`
- 自动下界：`[{"always": true, "allow": ["yMain", "yStar", "yDelta", "yFault"]}]`

## 编译器给出的依据

- 保护类：许可 = `xStart` 工况下 ['yMain', 'yStar', 'yDelta'] 的变化
- 无法判定意图 → 退化为存在性约束（最弱下界）

- 触发来源：—
- 窗口分解：{}
- 重启源：[]

## 注入的越界（O1–O8）：5 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O1 | O1 改 yFault：追加 AND NOT xStart | cross-variable | G0 | 377 | **主 bad** | `bad_O1.st` |
| O1 | O1 改 yFault：追加 AND NOT xStop | cross-variable | G0 | 377 | 备选 | `bad_O1_2.st` |
| O2 | O2 删去 AND NOT xStop | same-variable-guard | G2 | 748 | 备选 | `bad_O2.st` |
| O3 | O3 T#5S → T#5020MS（+2 拍） | same-variable-window | G1 | 8 | 备选 | `bad_O3.st` |
| O6 | O6 对调 yMain / yStar 的赋值顺序 | same-variable-window | G1 | 1600 | 备选 | `bad_O6.st` |

未能产生可观测差异而被丢弃的候选：1 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（5/5/5 条语句）
- [PASS] 输出接口一致：['yMain', 'yStar', 'yDelta', 'yFault']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 4 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 40/44 条轨迹上产生差异（最多 216 个点）
- [PASS] 越界改动被编译契约检出 42/44 条轨迹，最早第 0 个周期（可检出的粒度：L/G0/G1/G2/编译契约）
- [PASS] bad 相对 good 另有差异（42/44 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=cross-variable）

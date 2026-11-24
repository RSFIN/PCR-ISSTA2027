# edge_arm_40ms

- 程序来源：W1 沙箱自建（互锁动作）
- 变更单：xA 上升沿后（xB 为 TRUE 时），互锁动作延时由 30 毫秒改为 40 毫秒；其余逻辑不变。
- 自动编译：`[{"edge": {"var": "xA", "dir": "rising"}, "allow": ["yCmd"], "window": [0, 4], "guard": "xB"}]`
- 自动下界：`[{"shape": {"len": 1, "tol": 0}, "allow": ["yCmd"]}]`

## 编译器给出的依据

- 可观测性守卫：差异只在 `xB` 为真时才可见，加 guard 收紧上界而不损失健全性
- 时序类：许可 = 触发 xA rising 后 4 拍内、输出 ['yCmd'] 的变化（= b 4 + 重启 0×1 + 结构延迟 0）
- 幅度约束：差异段应长约 1±0 个扫描周期（= |40-30|ms / 10ms，容差 ±0%）

- 触发来源：文本直呼标识符 xA
- 窗口分解：{"b": 4, "n_restart": 0, "moved": 1, "struct_delay": 0}
- 重启源：[]

## 注入的越界（O1–O8）：3 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O3 | O3 T#40MS → T#60MS（+2 拍） | same-variable-window | G1 | 14 | 备选 | `bad_O3.st` |
| O6 | O6 对调 xArm / yCmd 的赋值顺序 | same-variable-window | G1 | 7 | **主 bad** | `bad_O6.st` |
| O8 | O8 删去 AND xB | same-variable-guard | G2 | 56 | 备选 | `bad_O8.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（3/3/3 条语句）
- [PASS] 输出接口一致：['yCmd']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 4 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 42/44 条轨迹上产生差异（最多 4 个点）
- [PASS] 越界改动被编译契约检出 36/44 条轨迹，最早第 3 个周期（可检出的粒度：L/G1/G2/编译契约）
- [PASS] bad 相对 good 另有差异（44/44 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=same-variable-window）

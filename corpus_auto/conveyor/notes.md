# conveyor

- 程序来源：W1 沙箱自建（皮带线）
- 变更单：急停复位后须延时 2 秒才允许启动；其余逻辑不变。
- 自动编译：`[{"edge": {"var": "xEStop", "dir": "falling"}, "allow": ["yRun"], "window": [0, 620]}]`
- 自动下界：`[{"shape": {"len": 200, "tol": 17}, "allow": ["yRun"]}]`

## 编译器给出的依据

- 时序类：许可 = 触发 xEStop falling 后 620 拍内、输出 ['yRun'] 的变化（= b 200 + 重启 2×200 + 结构延迟 20）
- 幅度约束：差异段应长约 200±0 个扫描周期（= |2000-0|ms / 10ms，容差 ±0%）
- 容差由条目显式指定 ±17：正确改法新增 tonRestart，其起点比 tonDb 晚 17 拍，实测差异段长 183 而 |b-a|/周期=200；这 17 拍是**两个定时器起点差**造成的模型误差，不是抖动

- 触发来源：文本线索「急停」→ xEStop
- 窗口分解：{"b": 200, "n_restart": 2, "moved": 200, "struct_delay": 20}
- 重启源：['xStart', 'xStop']

## 注入的越界（O1–O8）：4 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O1 | O1 改 yFault：追加 AND NOT xStart | cross-variable | G0 | 372 | **主 bad** | `bad_O1.st` |
| O1 | O1 改 yFault：追加 AND NOT xStop | cross-variable | G0 | 525 | 备选 | `bad_O1_2.st` |
| O3 | O3 T#2S → T#2020MS（+2 拍） | same-variable-window | G1 | 4 | 备选 | `bad_O3.st` |
| O6 | O6 对调 xPerm / yRun 的赋值顺序 | same-variable-window | G1 | 2 | 备选 | `bad_O6.st` |

未能产生可观测差异而被丢弃的候选：3 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（4/5/5 条语句）
- [PASS] 输出接口一致：['yRun', 'yFault']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 4 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 8/44 条轨迹上产生差异（最多 183 个点）
- [PASS] 越界改动被编译契约检出 43/44 条轨迹，最早第 0 个周期（可检出的粒度：L/G0/G1/G2/编译契约）
- [PASS] bad 相对 good 另有差异（43/44 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=cross-variable）

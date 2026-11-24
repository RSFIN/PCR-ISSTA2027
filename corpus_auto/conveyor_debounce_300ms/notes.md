# conveyor_debounce_300ms

- 程序来源：W1 沙箱自建（传送带启动确认）
- 变更单：xStart 上升沿后，传送带启动确认延时由 200 毫秒改为 300 毫秒；其余逻辑不变。
- 自动编译：`[{"edge": {"var": "xStart", "dir": "rising"}, "allow": ["yReady"], "window": [0, 30]}]`
- 自动下界：`[{"shape": {"len": 10, "tol": 0}, "allow": ["yReady"]}]`

## 编译器给出的依据

- 时序类：许可 = 触发 xStart rising 后 30 拍内、输出 ['yReady'] 的变化（= b 30 + 重启 0×10 + 结构延迟 0）
- 幅度约束：差异段应长约 10±0 个扫描周期（= |300-200|ms / 10ms，容差 ±0%）

- 触发来源：文本直呼标识符 xStart
- 窗口分解：{"b": 30, "n_restart": 0, "moved": 10, "struct_delay": 0}
- 重启源：[]

## 注入的越界（O1–O8）：1 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O3 | O3 T#300MS → T#320MS（+2 拍） | same-variable-window | G1 | 4 | **主 bad** | `bad_O3.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（2/2/2 条语句）
- [PASS] 输出接口一致：['yReady']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 4 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 44/44 条轨迹上产生差异（最多 70 个点）
- [PASS] 越界改动被编译契约检出 2/44 条轨迹，最早第 20 个周期（可检出的粒度：L/G1/G2/编译契约）
- [PASS] bad 相对 good 另有差异（2/44 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=same-variable-window）

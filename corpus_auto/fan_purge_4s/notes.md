# fan_purge_4s

- 程序来源：W1 沙箱自建（风机停机后挡板排风）
- 变更单：xFan 断开沿后，排风挡板保持延时由 3 秒改为 4 秒；其余逻辑不变。
- 自动编译：`[{"edge": {"var": "xFan", "dir": "falling"}, "allow": ["yDamper"], "window": [0, 400]}]`
- 自动下界：`[{"shape": {"len": 100, "tol": 0}, "allow": ["yDamper"]}]`

## 编译器给出的依据

- 时序类：许可 = 触发 xFan falling 后 400 拍内、输出 ['yDamper'] 的变化（= b 400 + 重启 0×100 + 结构延迟 0）
- 幅度约束：差异段应长约 100±0 个扫描周期（= |4000-3000|ms / 10ms，容差 ±0%）

- 触发来源：文本直呼标识符 xFan
- 窗口分解：{"b": 400, "n_restart": 0, "moved": 100, "struct_delay": 0}
- 重启源：[]

## 注入的越界（O1–O8）：2 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O1 | O1 改 yFan：追加 AND NOT xFan | cross-variable | G0 | 703 | **主 bad** | `bad_O1.st` |
| O3 | O3 T#4S → T#4020MS（+2 拍） | same-variable-window | G1 | 4 | 备选 | `bad_O3.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（3/3/3 条语句）
- [PASS] 输出接口一致：['yFan', 'yDamper']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 3 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 2/43 条轨迹上产生差异（最多 100 个点）
- [PASS] 越界改动被编译契约检出 43/43 条轨迹，最早第 0 个周期（可检出的粒度：L/G0/G1/G2/编译契约）
- [PASS] bad 相对 good 另有差异（43/43 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=cross-variable）

# indexer_ready_1800ms

- 程序来源：自建：分度索引机构，工件到位后翻转索引状态并延时给出就绪输出
- 变更单：xPart 上升沿后，索引就绪延时由 1 秒改为 1800 毫秒；其余逻辑不变。
- 自动编译：`[{"edge": {"var": "xPart", "dir": "rising"}, "allow": ["yReady"], "window": [0, 180]}]`
- 自动下界：`[{"shape": {"len": 80, "tol": 0}, "allow": ["yReady"]}]`

## 编译器给出的依据

- 时序类：许可 = 触发 xPart rising 后 180 拍内、输出 ['yReady'] 的变化（= b 180 + 重启 0×80 + 结构延迟 0）
- 幅度约束：差异段应长约 80±0 个扫描周期（= |1800-1000|ms / 10ms，容差 ±0%）

- 触发来源：文本直呼标识符 xPart
- 窗口分解：{"b": 180, "n_restart": 0, "moved": 80, "struct_delay": 0}
- 重启源：[]

## 注入的越界（O1–O8）：3 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O1 | O1 改 yIndex：追加 AND NOT xPart | cross-variable | G0 | 1918 | **主 bad** | `bad_O1.st` |
| O3 | O3 T#1800MS → T#1820MS（+2 拍） | same-variable-window | G1 | 8 | 备选 | `bad_O3.st` |
| O5 | O5 rtPart.Q → 直接电平 xPart | same-variable-window | G1 | 1407 | 备选 | `bad_O5.st` |

未能产生可观测差异而被丢弃的候选：0 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（4/4/4 条语句）
- [PASS] 输出接口一致：['yIndex', 'yReady']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 4 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 4/44 条轨迹上产生差异（最多 80 个点）
- [PASS] 越界改动被编译契约检出 44/44 条轨迹，最早第 0 个周期（可检出的粒度：L/G0/G1/G2/编译契约）
- [PASS] bad 相对 good 另有差异（44/44 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=cross-variable）

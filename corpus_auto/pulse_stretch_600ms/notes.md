# pulse_stretch_600ms

- 程序来源：OSCAT basic TP（脉冲展宽）+ IEC R_TRIG
- 变更单：xTrig 上升沿触发的脉冲展宽时间由 300 毫秒改为 600 毫秒；其余逻辑不变。
- 自动编译：`[{"edge": {"var": "xTrig", "dir": "rising"}, "allow": ["yPulse", "yBusy", "yFault"], "window": [0, 60]}]`
- 自动下界：`[{"shape": {"len": 30, "tol": 0}, "allow": ["yPulse", "yBusy", "yFault"]}]`

## 编译器给出的依据

- 时序类：许可 = 触发 xTrig rising 后 60 拍内、输出 ['yPulse', 'yBusy', 'yFault'] 的变化（= b 60 + 重启 0×30 + 结构延迟 0）
- 幅度约束：差异段应长约 30±0 个扫描周期（= |600-300|ms / 10ms，容差 ±0%）

- 触发来源：文本直呼标识符 xTrig
- 窗口分解：{"b": 60, "n_restart": 0, "moved": 30, "struct_delay": 0}
- 重启源：[]

## 注入的越界（O1–O8）：3 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O2 | O2 删去 AND NOT xInh | same-variable-guard | G2 | 422 | **主 bad** | `bad_O2.st` |
| O2 | O2 删去 AND NOT yPulse | same-variable-guard | G2 | 422 | 备选 | `bad_O2_2.st` |
| O3 | O3 T#600MS → T#620MS（+2 拍） | same-variable-window | G1 | 72 | 备选 | `bad_O3.st` |

未能产生可观测差异而被丢弃的候选：1 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（6/6/6 条语句）
- [PASS] 输出接口一致：['yPulse', 'yBusy', 'yFault']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 4 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 44/44 条轨迹上产生差异（最多 480 个点）
- [WARN] 编译契约漏检该越界（L 层可检出）——这是召回数据点，不是语料缺陷
- [PASS] bad 相对 good 另有差异（39/44 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=same-variable-guard）

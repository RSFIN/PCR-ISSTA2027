# stardelta

- 程序来源：W1 沙箱自建（星三角启动）
- 变更单：星三角切换延时由 5 秒改为 7 秒；其余逻辑不变。
- 自动编译：`[{"edge": {"var": "yMain", "dir": "rising"}, "allow": ["yStar", "yDelta"], "window": [0, 1300]}]`
- 自动下界：`[{"shape": {"len": 200, "tol": 0}, "allow": ["yStar", "yDelta"]}]`

## 编译器给出的依据

- 时序类：许可 = 触发 yMain rising 后 1300 拍内、输出 ['yStar', 'yDelta'] 的变化（= b 700 + 重启 3×200 + 结构延迟 0）
- 幅度约束：差异段应长约 200±0 个扫描周期（= |7000-5000|ms / 10ms，容差 ±0%）

- 触发来源：文本无线索 → 目标定时器 IN 表达式的首个信号
- 窗口分解：{"b": 700, "n_restart": 3, "moved": 200, "struct_delay": 0}
- 重启源：['xOverload', 'xStart', 'xStop']

## 注入的越界（O1–O8）：4 个可观测

| 算子 | 注入内容 | 越界类型 | 期望被 | 差异点 | 采纳 | 文件 |
|-|-|-|-|-|-|-|
| O1 | O1 改 yMain：追加 AND NOT xStart | cross-variable | G0 | 4994 | **主 bad** | `bad_O1.st` |
| O2 | O2 删去 AND NOT xStop | same-variable-guard | G2 | 750 | 备选 | `bad_O2.st` |
| O3 | O3 T#7S → T#7020MS（+2 拍） | same-variable-window | G1 | 8 | 备选 | `bad_O3.st` |
| O6 | O6 对调 yMain / yStar 的赋值顺序 | same-variable-window | G1 | 1200 | 备选 | `bad_O6.st` |

未能产生可观测差异而被丢弃的候选：2 个。

## 验收

- [PASS] 文件齐全
- [PASS] ST 解析通过（5/5/5 条语句）
- [PASS] 输出接口一致：['yMain', 'yStar', 'yDelta', 'yFault']
- [PASS] 契约子句 1 条
- [PASS] 自带定向轨迹 4 条（要求 ≥2）
- [PASS] 合规改动 0 误报
- [PASS] 合规改动在 2/44 条轨迹上产生差异（最多 400 个点）
- [PASS] 越界改动被编译契约检出 44/44 条轨迹，最早第 0 个周期（可检出的粒度：L/G0/G1/G2/编译契约）
- [PASS] bad 相对 good 另有差异（44/44 条轨迹）
- [PASS] 空改动被拒（下界要求生效）
- [PASS] 元数据完整（over_edit_kind=cross-variable）

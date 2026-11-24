# -*- coding: utf-8 -*-
"""生成两张论文图：
  eval/pi_curve.svg     precision vs 部署先验 pi（4.3% 处竖线）
  eval/cost_curve.svg   每千单成本 vs 漏检/误报代价比 cFN/cFP（交点 8.4x）

只依赖标准库；白底，适合论文。
"""
import os
import csv

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL = os.path.join(W, 'eval')
MT = {r['config']: r for r in csv.DictReader(open(os.path.join(EVAL, 'baseline_main_table.csv'), encoding='utf-8'))}
SEL = [('OURS', 'Ours', '#C0392B'), ('L5-QW-line', 'L5-Qwen', '#2E86C1'),
       ('C7-AI', 'C7-AI', '#8E44AD'), ('C-LS', 'C-LS', '#16A085'), ('C6', 'C6', '#E67E22')]
PI0 = 0.043


def f(m, k):
    return float(m[k])


def svg_open(title, xlab, ylab):
    return ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 440" font-family="Helvetica,Arial,sans-serif">',
            '<rect width="680" height="440" fill="#ffffff"/>',
            '<text x="70" y="24" font-size="15" font-weight="bold" fill="#111">%s</text>' % title]


def axes(L, R, T, B, xlab, ylab, xticks, yticks, xmap, ymap, xfmt='%g', yfmt='%g'):
    s = []
    for v in xticks:
        x = xmap(v)
        s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#e8e8e8"/>' % (x, T, x, B))
        s.append('<text x="%.1f" y="%d" font-size="10" fill="#555" text-anchor="middle">%s</text>' % (x, B + 16, xfmt(v)))
    for v in yticks:
        y = ymap(v)
        s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e8e8e8"/>' % (L, y, R, y))
        s.append('<text x="%d" y="%.1f" font-size="10" fill="#555" text-anchor="end">%s</text>' % (L - 8, y + 3, yfmt(v)))
    s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="1.2"/>' % (L, B, R, B))
    s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="1.2"/>' % (L, T, L, B))
    s.append('<text x="%.1f" y="%d" font-size="12" fill="#333" text-anchor="middle">%s</text>' % ((L + R) / 2, 420, xlab))
    s.append('<text x="18" y="%.1f" font-size="12" fill="#333" transform="rotate(-90 18 %.1f)" text-anchor="middle">%s</text>'
             % ((T + B) / 2, (T + B) / 2, ylab))
    return s


def legend(items, y=44):
    s = []
    for i, (t, c) in enumerate(items):
        x = 70 + i * 120
        s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2.4"/>' % (x, y, x + 14, y, c))
        s.append('<text x="%d" y="%d" font-size="9.5" fill="#333">%s</text>' % (x + 18, y + 3, t))
    return s


# ---------- pi 曲线
L, R, T, B = 70, 620, 64, 370
xmap = lambda pi: L + pi / 0.50 * (R - L)
ymap = lambda p: B - p * (B - T)
s = svg_open('Precision under deployment prior', 'prevalence of true over-edits (pi)', 'precision')
s += axes(L, R, T, B, 'prevalence of true over-edits (pi)', 'precision',
          [0, 0.1, 0.2, 0.3, 0.4, 0.5], [0, 0.2, 0.4, 0.6, 0.8, 1.0], xmap, ymap,
          lambda v: '%d%%' % round(v * 100), lambda v: '%d%%' % round(v * 100))
for key, lab, col in SEL:
    m = MT[key]
    Rr, Ff = f(m, 'recall'), f(m, 'fpr')
    pts = []
    for i in range(0, 101):
        pi = i / 200.0  # 0..0.5
        den = pi * Rr + (1 - pi) * Ff
        prec = (pi * Rr / den) if den > 1e-12 else 1.0
        pts.append((xmap(pi), ymap(prec)))
    s.append('<polyline fill="none" stroke="%s" stroke-width="2" points="%s"/>'
             % (col, ' '.join('%.1f,%.1f' % p for p in pts)))
# pi=4.3% 竖线 + 标注
x0 = xmap(PI0)
s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#666" stroke-dasharray="4 3"/>' % (x0, T, x0, B))
s.append('<text x="%.1f" y="%d" font-size="9.5" fill="#444">pi=4.3%% (T3)</text>' % (x0 + 4, T + 12))
s += legend([(l, c) for _, l, c in SEL])
s.append('</svg>')
# 论文用图见 eval/redraw_figs.py
open(os.path.join(EVAL, 'pi_curve_draft.svg'), 'w', encoding='utf-8').write('\n'.join(s))

# ---------- 成本曲线
L, R, T, B = 70, 620, 64, 370
import math as _m


def xr(r):
    return L + (_m.log10(r) / _m.log10(60)) * (R - L)


def yc(c):
    return B - min(c, 200) / 200.0 * (B - T)


s = svg_open('Cost per 1000 changes vs. cost ratio', 'cFN / cFP (log scale)', 'cost per 1000 (cFP = 1)')
s += axes(L, R, T, B, 'cFN / cFP (log scale)', 'cost per 1000 (cFP = 1)',
          [1, 2, 5, 10, 20, 60], [0, 50, 100, 150, 200], xr, yc,
          lambda v: '%g' % v, lambda v: '%g' % v)
COST_SEL = [x for x in SEL if x[0] != 'C6']  # C6 的 FP≈303/千单，成本曲线整条在图外
for key, lab, col in COST_SEL:
    m = MT[key]
    Rr, Ff = f(m, 'recall'), f(m, 'fpr')
    fn = 1000 * PI0 * (1 - Rr)
    fp = 1000 * (1 - PI0) * Ff
    pts, exit_x = [], None
    for i in range(201):
        r = 1 + i * 59 / 200.0
        c = fp + r * fn
        if c > 200:                      # 超出纵轴：停笔并在上边界画出口箭头，不做水平截断
            exit_x = xr(r)
            break
        pts.append((xr(r), yc(c)))
    if pts:
        s.append('<polyline fill="none" stroke="%s" stroke-width="2" points="%s"/>'
                 % (col, ' '.join('%.1f,%.1f' % p for p in pts)))
    if exit_x is not None:
        s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%d" stroke="%s" stroke-width="2"/>'
                 % (exit_x, pts[-1][1], exit_x, T + 13, col))
        s.append('<path d="M%.1f %d L%.1f %d L%.1f %d Z" fill="%s"/>'
                 % (exit_x, T + 4, exit_x - 4, T + 14, exit_x + 4, T + 14, col))
# 本文与 L5-QW 交点 8.4
x0 = xr(8.39)
s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#666" stroke-dasharray="4 3"/>' % (x0, T, x0, B))
s.append('<text x="%.1f" y="%d" font-size="9.5" fill="#444">8.4x</text>' % (x0 + 4, T + 12))
s += legend([(l, c) for _, l, c in COST_SEL])
s.append('</svg>')
open(os.path.join(EVAL, 'cost_curve_draft.svg'), 'w', encoding='utf-8').write('\n'.join(s))
print('wrote eval/{pi_curve,cost_curve}_draft.svg (paper figures: redraw_figs.py)')

# -*- coding: utf-8 -*-
"""重画三张数据图（Figure 3/4/5），统一版式与字号。

版心 acmsmall = 395.8 pt。画布 792 px 时缩放比约 0.50，
故 13 px 字 -> 6.5 pt、14 px -> 7 pt，印刷可读。
旧版 680x440 缩到 0.85 栏宽时 10 px 字只有 4.6 pt，不可用。

产出：
  eval/workpoint.svg    recall vs FPR，18 配置 + Pareto 阶梯
  eval/pi_curve.svg     precision vs 部署先验 pi，pi=4.3% 处打点
  eval/cost_curve.svg   每千单成本 vs cFN/cFP，交点 8.4x
"""
import os
import csv
import math

W1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL = os.path.join(W1, 'eval')
FIGDIR = os.path.join(os.path.dirname(EVAL), 'paper', 'figures')
if not os.path.isdir(FIGDIR):
    FIGDIR = EVAL   # 独立使用时退回 eval/


MT = {r['config']: r for r in csv.DictReader(
    open(os.path.join(EVAL, 'baseline_main_table.csv'), encoding='utf-8'))}
PARETO = sorted([r['config'] for r in csv.DictReader(
    open(os.path.join(EVAL, 'workpoint_pareto.csv'), encoding='utf-8'))
    if r['pareto'] == '1'], key=lambda c: float(MT[c]['recall']))

PI0 = 0.043
INK = '#1a1a1a'
MUTED = '#6b6b6b'
GRID = '#e6e6e6'
RED = '#B03A2E'
BLUE = '#2471A3'
GREY = '#7F8C8D'
PURPLE = '#6C3483'
TEAL = '#117A65'
ORANGE = '#CA6F1E'

FS_TICK = 13.5
FS_AXIS = 14.5
FS_LAB = 14
FS_LEG = 13.5


def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def txt(x, y, s, size=FS_LAB, fill=INK, anchor='start', bold=False, mono=False):
    ff = ' font-family="Consolas,Menlo,monospace"' if mono else ''
    fw = ' font-weight="bold"' if bold else ''
    return ('<text x="%.1f" y="%.1f" font-size="%g" fill="%s" text-anchor="%s"%s%s>%s</text>'
            % (x, y, size, fill, anchor, fw, ff, esc(s)))


def frame(W, H):
    return ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'font-family="Helvetica,Arial,sans-serif">' % (W, H),
            '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H)]


def axis(L, R, T, B, xlab, ylab):
    s = ['<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.2"/>' % (L, B, R, B, INK),
         '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.2"/>' % (L, T, L, B, INK),
         txt((L + R) / 2, B + 42, xlab, FS_AXIS, INK, 'middle')]
    ym = (T + B) / 2
    s.append('<text x="26" y="%.1f" font-size="%g" fill="%s" text-anchor="middle" '
             'transform="rotate(-90 26 %.1f)">%s</text>' % (ym, FS_AXIS, INK, ym, esc(ylab)))
    return s


def legend(items, y, W, x0=84, gap=None):
    """一行图例，返回 (svg 元素, 无需返回值)。"""
    s = []
    if gap is None:
        gap = (W - x0 - 24) / max(len(items), 1)
    for i, (lab, col, kind) in enumerate(items):
        x = x0 + i * gap
        if kind == 'dot':
            s.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="%s"/>' % (x, y - 4, col))
        else:
            s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                     'stroke-width="2.6"/>' % (x, y - 4, x + 15, y - 4, col))
        s.append(txt(x + 20, y, lab, FS_LEG, '#333333'))
    return s


# =====================================================================
# Figure: work point
# =====================================================================
W, H = 792, 336
L, R, T, B = 88, 764, 62, 268
XMAX, YMIN, YMAX = 0.35, 0.55, 1.02


def X(f):
    return L + (f / XMAX) * (R - L)


def Y(r):
    return B - ((r - YMIN) / (YMAX - YMIN)) * (B - T)


s = frame(W, H)
s += legend([('Ours (licence + diff)', RED, 'dot'),
             ('LLM judge', BLUE, 'dot'),
             ('Formal / differential', GREY, 'dot'),
             ('Reference arm', PURPLE, 'dot')], 26, W)
for f in [0, .05, .10, .15, .20, .25, .30, .35]:
    x = X(f)
    s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s"/>' % (x, T, x, B, GRID))
    s.append(txt(x, B + 19, '%d' % round(f * 100), FS_TICK, MUTED, 'middle'))
for r in [.60, .70, .80, .90, 1.00]:
    y = Y(r)
    s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s"/>' % (L, y, R, y, GRID))
    s.append(txt(L - 9, y + 4, '%d' % round(r * 100), FS_TICK, MUTED, 'end'))
s += axis(L, R, T, B, 'false-alarm rate (%)', 'recall (%)')

# Pareto 阶梯
pp = [MT[c] for c in PARETO]
for a, b in zip(pp, pp[1:]):
    s.append('<path d="M%.1f %.1f L%.1f %.1f" fill="none" stroke="%s" stroke-width="1.4" '
             'stroke-dasharray="6 4" opacity="0.6"/>'
             % (X(float(a['fpr'])), Y(float(a['recall'])),
                X(float(b['fpr'])), Y(float(b['recall'])), RED))

# 所有点
COLOR = {'本文': RED, 'A组-LLM': BLUE, 'B组': GREY, '参考臂': PURPLE, 'A组': TEAL}
for c, m in MT.items():
    if c == 'C2-same':
        continue
    f, r = float(m['fpr']), float(m['recall'])
    if r < YMIN - 0.02:
        continue
    big = (c == 'OURS')
    rad = 7.5 if big else (5.6 if c in PARETO else 4.6)
    s.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="#ffffff" stroke-width="1.2"/>'
             % (X(f), Y(r), rad, COLOR.get(m['group'], GREY)))

# 点簇上方拥挤，不逐一引线：簇内三组各给一行说明，非支配点单独一行
s.append(txt(X(0) + 11, Y(.854) + 5, 'Ours', FS_LAB, RED, 'start', True))
s.append(txt(X(.045) + 6, Y(.683), 'C4 / C5 / C7: BMC with a contract, 68% ceiling',
             FS_LAB, GREY, 'start'))
s.append(txt(X(.045) + 6, Y(.600), 'Non-dominated:  Ours 0.0 / 85.4  \u00b7  '
             'C7-AI 5.1 / 98.8  \u00b7  L5-Qwen 5.5 / 100', FS_LAB, '#333333', 'start'))
s.append(txt(X(.290), Y(.902), 'C6 / C-SD: no contract, 30% FPR', FS_LAB, GREY, 'end'))
s.append('</svg>')
open(os.path.join(FIGDIR, 'workpoint.svg'), 'w', encoding='utf-8').write('\n'.join(s))

# =====================================================================
# Figure: precision vs prevalence
# =====================================================================
W, H = 792, 314
L, R, T, B = 88, 764, 50, 240
XMAX = 0.50
SEL = [('OURS', 'Ours', RED), ('L5-QW-line', 'L5-Qwen', BLUE),
       ('C7-AI', 'C7-AI', PURPLE), ('C-LS', 'C-LS', TEAL), ('C6', 'C6', ORANGE)]


def xp(pi):
    return L + (pi / XMAX) * (R - L)


def yp(p):
    return B - p * (B - T)


s = frame(W, H)
s += legend([(lab, col, 'line') for _, lab, col in SEL], 22, W, gap=(W - 108) / 5)
for v in [0, .1, .2, .3, .4, .5]:
    x = xp(v)
    s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s"/>' % (x, T, x, B, GRID))
    s.append(txt(x, B + 19, '%d' % round(v * 100), FS_TICK, MUTED, 'middle'))
for v in [0, .2, .4, .6, .8, 1.0]:
    y = yp(v)
    s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s"/>' % (L, y, R, y, GRID))
    s.append(txt(L - 9, y + 4, '%d' % round(v * 100), FS_TICK, MUTED, 'end'))
s += axis(L, R, T, B, 'prevalence of true over-edits (%)', 'precision (%)')

for key, lab, col in SEL:
    m = MT[key]
    Rr, Ff = float(m['recall']), float(m['fpr'])
    pts = []
    for i in range(0, 141):
        pi = i / 280.0
        den = pi * Rr + (1 - pi) * Ff
        prec = (pi * Rr / den) if den > 1e-12 else 1.0
        pts.append((xp(pi), yp(prec)))
    s.append('<polyline fill="none" stroke="%s" stroke-width="2" points="%s"/>'
             % (col, ' '.join('%.1f,%.1f' % p for p in pts)))

# pi = 4.3% 竖线 + 各曲线在此处的取值
x0 = xp(PI0)
s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="1.1" '
         'stroke-dasharray="5 4"/>' % (x0, T, x0, B, '#888888'))
s.append(txt(x0 + 7, T + 16, 'deployment prior 4.3%', FS_TICK, '#444444'))

# 各曲线在 pi=4.3% 处打点；数值不逐个引线，统一放在右下空白处
for key, lab, col in [('OURS', 'Ours', RED), ('C7-AI', 'C7-AI', PURPLE),
                      ('L5-QW-line', 'L5-Qwen', BLUE), ('C-LS', 'C-LS', TEAL),
                      ('C6', 'C6', ORANGE)]:
    m = MT[key]
    Rr, Ff = float(m['recall']), float(m['fpr'])
    den = PI0 * Rr + (1 - PI0) * Ff
    prec = (PI0 * Rr / den) if den > 1e-12 else 1.0
    s.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s" stroke="#ffffff" stroke-width="1.2"/>'
             % (x0, yp(prec), col))

s.append(txt(xp(.245), yp(.170), 'precision at 4.3% prevalence', FS_LAB, '#333333', 'start', True))
s.append(txt(xp(.245), yp(.075), 'Ours 100  \u00b7  C7-AI 46  \u00b7  L5-Qwen 45  \u00b7  '
             'C-LS 35  \u00b7  C6 12', FS_LAB, '#333333', 'start'))
s.append('</svg>')
open(os.path.join(FIGDIR, 'pi_curve.svg'), 'w', encoding='utf-8').write('\n'.join(s))

# =====================================================================
# Figure: cost per 1000 vs cost ratio
# =====================================================================
W, H = 792, 322
L, R, T, B = 92, 764, 50, 248
RMAX, CMAX = 60.0, 200.0


def xr(r):
    return L + (math.log10(r) / math.log10(RMAX)) * (R - L)


def yc(c):
    return B - (c / CMAX) * (B - T)


COST = [('OURS', 'Ours', RED), ('C7-AI', 'C7-AI', PURPLE),
        ('L5-QW-line', 'L5-Qwen', BLUE), ('C-LS', 'C-LS', TEAL)]
s = frame(W, H)
s += legend([(lab, col, 'line') for _, lab, col in COST], 22, W, gap=(W - 108) / 4)
for v in [1, 2, 5, 10, 20, 60]:
    x = xr(v)
    s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s"/>' % (x, T, x, B, GRID))
    s.append(txt(x, B + 19, '%g' % v, FS_TICK, MUTED, 'middle'))
for v in [0, 50, 100, 150, 200]:
    y = yc(v)
    s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s"/>' % (L, y, R, y, GRID))
    s.append(txt(L - 9, y + 4, '%d' % v, FS_TICK, MUTED, 'end'))
s += axis(L, R, T, B, 'cost(FN) / cost(FP)  (log scale)', 'cost per 1,000 changes (FP = 1)')

for key, lab, col in COST:
    m = MT[key]
    Rr, Ff = float(m['recall']), float(m['fpr'])
    fn = 1000 * PI0 * (1 - Rr)
    fp = 1000 * (1 - PI0) * Ff
    pts, exit_x = [], None
    for i in range(241):
        r = 1 + i * (RMAX - 1) / 240.0
        c = fp + r * fn
        if c > CMAX:
            exit_x = xr(r)
            break
        pts.append((xr(r), yc(c)))

# 与 L5-Qwen 的交点 8.39x（两线在此等成本）
def cost_at(key, r):
    m = MT[key]
    return (1000 * (1 - PI0) * float(m['fpr'])
            + r * 1000 * PI0 * (1 - float(m['recall'])))


XSTAR = 8.39
x0 = xr(XSTAR)
s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="1.1" '
         'stroke-dasharray="5 4"/>' % (x0, T, x0, B, '#888888'))
s.append(txt(x0 + 8, T + 17, '8.4x', FS_LAB, '#333333', 'start', True))

for key, lab, col in COST:
    m = MT[key]
    Rr, Ff = float(m['recall']), float(m['fpr'])
    fn = 1000 * PI0 * (1 - Rr)
    fp = 1000 * (1 - PI0) * Ff
    pts, exit_x = [], None
    for i in range(241):
        r = 1 + i * (RMAX - 1) / 240.0
        c = fp + r * fn
        if c > CMAX - 6:
            exit_x = xr(r)
            break
        pts.append((xr(r), yc(c)))
    if len(pts) > 1:
        s.append('<polyline fill="none" stroke="%s" stroke-width="2.2" points="%s"/>'
                 % (col, ' '.join('%.1f,%.1f' % p for p in pts)))
    if exit_x is not None:
        s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%d" stroke="%s" stroke-width="2.2"/>'
                 % (exit_x, pts[-1][1], exit_x, T + 9, col))
        s.append('<path d="M%.1f %d L%.1f %.1f L%.1f %d Z" fill="%s"/>'
                 % (exit_x, T + 1, exit_x - 5, T + 12, exit_x + 5, T + 12, col))

# 交点圆点
cs = cost_at('OURS', XSTAR)
s.append('<circle cx="%.1f" cy="%.1f" r="5" fill="#ffffff" stroke="%s" stroke-width="2.2"/>'
         % (x0, yc(cs), INK))
s.append(txt(x0 + 13, yc(cs) + 28, 'equal cost', FS_LAB, INK))
s.append('</svg>')
open(os.path.join(FIGDIR, 'cost_curve.svg'), 'w', encoding='utf-8').write('\n'.join(s))

print('wrote eval/{workpoint,pi_curve,cost_curve}.svg')
print('pareto order:', PARETO)

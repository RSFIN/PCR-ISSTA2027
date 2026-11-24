#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Figure 2 v2：方法流程。792×256，浅色分栏 + 时序波形 + 判定印章。"""

import os

EVAL = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(os.path.dirname(EVAL), 'paper', 'figures')
if not os.path.isdir(FIGDIR):
    FIGDIR = EVAL   # 独立使用时退回 eval/

W, H = 792, 256
INK, MUTED = '#16202A', '#6F7B85'
RED, GREEN, BLUE = '#C0392B', '#1E8449', '#2E86C1'
TINT = '#F6F8F9'

s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Helvetica, Arial, sans-serif">' % (W, H, W, H)]
s.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H))


def t(x, y, txt, size=12, fill=INK, bold=False, anchor='start', mono=False, italic=False):
    fam = ' font-family="DejaVu Sans Mono, Consolas, monospace"' if mono else ''
    fw = ' font-weight="bold"' if bold else ''
    fs = ' font-style="italic"' if italic else ''
    s.append('<text x="%.1f" y="%.1f" font-size="%.1f" fill="%s"%s%s%s text-anchor="%s">%s</text>'
             % (x, y, size, fill, fw, fam, fs, anchor, txt))


COL = [19, 211, 403, 595]
CW = 178
TOP, BOT = 18, 224

for x in COL:
    s.append('<rect x="%d" y="%d" width="%d" height="%d" rx="7" fill="%s"/>' % (x, TOP, CW, BOT - TOP, TINT))

titles = ['Change order', 'Licence compiler', 'Differential engine', 'Verdict']
for i, (x, title) in enumerate(zip(COL, titles)):
    s.append('<circle cx="%d" cy="%d" r="9" fill="%s"/>' % (x + 21, TOP + 20, INK))
    t(x + 21, TOP + 24, str(i + 1), 10.5, '#ffffff', bold=True, anchor='middle')
    t(x + 37, TOP + 24, title, 13, INK, bold=True)

for x in COL[:-1]:
    cx = x + CW + 7
    s.append('<path d="M%d %d L%d %d L%d %d" fill="none" stroke="#C3CBD1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
             % (cx - 2, 116, cx + 3, 123, cx - 2, 130))

# ---------- 1 工单 ----------
x = COL[0]
s.append('<rect x="%d" y="50" width="%d" height="94" rx="4" fill="#ffffff" stroke="%s" stroke-width="1.1"/>'
         % (x + 14, CW - 28, '#E0B4AE'))
t(x + 24, 72, 'manual clamp allowed', 11.6)
t(x + 24, 88, 'under overload', 11.6)
t(x + 24, 110, 'target: yClamp', 10.6, MUTED)
t(x + 24, 126, 'program P (ST)', 10.6, MUTED)
s.append('<circle cx="%d" cy="166" r="3" fill="%s"/>' % (x + 20, RED))
t(x + 29, 170, 'two defensible', 10.8, RED)
t(x + 29, 184, 'readings', 10.8, RED)

# ---------- 2 契约 ----------
x = COL[1]
rows = [('A', 'outputs'), ('G', 'guard'), ('W', 'window'), ('T', 'tolerance')]
for i, (k, v) in enumerate(rows):
    y = 56 + i * 30
    t(x + 18, y + 12, k, 13.5, BLUE, bold=True)
    t(x + 36, y + 12, v, 11.5, INK)
    if i < 3:
        s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="0.9"/>'
                 % (x + 16, y + 19, x + CW - 16, y + 19, '#E7ECEF'))
t(x + 18, 196, 'rules, not an LLM', 10.4, MUTED)
t(x + 18, 210, '4 typed failure codes', 10.4, MUTED)

# ---------- 3 波形 ----------
x = COL[2]
x0, x1 = x + 34, x + CW - 16
yP, yPp = 88, 128


def wave(y, rises, falls, color):
    pts = ['%d,%d' % (x0, y + 16)]
    cur = y + 16
    for r, f in zip(rises, falls):
        pts.append('%d,%d' % (r, cur)); cur = y
        pts.append('%d,%d' % (r, cur))
        pts.append('%d,%d' % (f, cur)); cur = y + 16
        pts.append('%d,%d' % (f, cur))
    pts.append('%d,%d' % (x1, cur))
    s.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.7" stroke-linejoin="round"/>'
             % (' '.join(pts), color))


t(x + 14, yP + 13, 'P', 11.5, INK, italic=True)
t(x + 14, yPp + 13, "P\u2032", 11.5, INK, italic=True)

ta, tb, tc = x0 + 36, x0 + 64, x0 + 86
wave(yP, [ta], [tb], INK)
wave(yPp, [ta], [tc], INK)

s.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" opacity="0.13"/>'
         % (tb, yP - 5, tc - tb, (yPp + 16) - (yP - 5), RED))
for xx in (tb, tc):
    s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="0.9" stroke-dasharray="3,2.5"/>'
             % (xx, yP - 7, xx, yPp + 18, RED))
t((tb + tc) / 2, yP - 11, '\u0394', 11, RED, bold=True, anchor='middle')

t(x + 14, 166, 'one output, one trace', 10.4, MUTED)
t(x + 14, 184, '40 random + 8 directed', 10.4, MUTED)
t(x + 14, 202, '3 programs, 2,099 cycles:', 10.4, GREEN)
t(x + 14, 216, 'identical to matiec / OpenPLC', 10.4, GREEN)

# ---------- 4 判定 ----------
x = COL[3]
t(x + 16, 60, 'is each \u0394 inside', 11, INK)
t(x + 16, 76, 'A ∧ G ∧ W ∧ T ?', 11.6, INK)

s.append('<rect x="%d" y="88" width="%d" height="30" rx="4" fill="#FBEDEC" stroke="%s" stroke-width="1.2"/>'
         % (x + 16, CW - 32, RED))
t(x + 26, 108, 'no \u2192 VIOLATED', 11.6, RED, bold=True)

s.append('<rect x="%d" y="126" width="%d" height="30" rx="4" fill="#EDF6EF" stroke="%s" stroke-width="1.2"/>'
         % (x + 16, CW - 32, GREEN))
t(x + 26, 146, 'yes \u2192 CONTAINED', 11.6, GREEN, bold=True)

t(x + 16, 182, 'INCOMPLETE', 10, MUTED, bold=True)
t(x + 16, 195, 'change did not happen', 9.8, MUTED)
t(x + 16, 212, 'UNDETERMINED', 10, MUTED, bold=True)
t(x + 16, 225, 'cannot parse or run', 9.8, MUTED)

s.append('</svg>')
open(os.path.join(FIGDIR, 'fig2_arch.svg'), 'w', encoding='utf-8').write('\n'.join(s))
print('written')

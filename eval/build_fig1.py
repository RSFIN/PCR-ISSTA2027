#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Figure 1：同一变更、两种工单写法、两种结果。792×300，与 Figure 2 同一套视觉语言。"""

import os

EVAL = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(os.path.dirname(EVAL), 'paper', 'figures')
if not os.path.isdir(FIGDIR):
    FIGDIR = EVAL   # 独立使用时退回 eval/

W, H = 792, 300
INK, MUTED = '#16202A', '#6F7B85'
RED, GREEN = '#C0392B', '#1E8449'
T_RED, T_GREEN = '#FDF4F3', '#F3F9F5'

s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Helvetica, Arial, sans-serif">' % (W, H, W, H)]
s.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H))


def t(x, y, txt, size=12, fill=INK, bold=False, anchor='start', mono=False):
    fam = ' font-family="DejaVu Sans Mono, Consolas, monospace"' if mono else ''
    fw = ' font-weight="bold"' if bold else ''
    s.append('<text x="%.1f" y="%.1f" font-size="%.1f" fill="%s"%s%s text-anchor="%s">%s</text>'
             % (x, y, size, fill, fw, fam, anchor, txt))


# 列标题
t(54, 20, 'WORK ORDER', 9.6, MUTED, bold=True)
t(330, 20, 'WHAT THE AGENT WROTE', 9.6, MUTED, bold=True)
t(628, 20, 'VERDICT', 9.6, MUTED, bold=True)

# ---------------- 第一行 ----------------
y1 = 30
s.append('<rect x="16" y="%d" width="%d" height="118" rx="7" fill="%s"/>' % (y1, W - 32, T_RED))
s.append('<circle cx="34" cy="%d" r="9" fill="%s"/>' % (y1 + 18, RED))
t(34, y1 + 22, 'v1', 9.6, '#ffffff', bold=True, anchor='middle')

t(54, y1 + 34, 'manual clamp allowed', 12.4)
t(54, y1 + 51, 'under overload; interlock', 12.4)
t(54, y1 + 68, 'applies in auto mode only', 12.4)
t(54, y1 + 92, 'target yClamp  \u00b7  program P', 10.4, MUTED)

s.append('<rect x="320" y="%d" width="286" height="76" rx="4" fill="#ffffff" stroke="%s" stroke-width="1"/>'
         % (y1 + 12, '#EBD5D2'))
t(332, y1 + 32, 'yClamp := (xAuto AND xReady', 10.6, INK, mono=True)
t(350, y1 + 46, 'AND NOT xOverload', 10.6, INK, mono=True)
t(350, y1 + 60, 'AND NOT xManual)', 10.6, INK, mono=True)
s.append('<rect x="322" y="%d" width="282" height="17" fill="%s" opacity="0.14"/>' % (y1 + 66, RED))
t(350, y1 + 79, 'OR (xManual AND xReady);', 10.6, RED, bold=True, mono=True)

s.append('<rect x="622" y="%d" width="150" height="30" rx="15" fill="%s"/>' % (y1 + 22, RED))
t(697, y1 + 42, 'VIOLATED  6/6', 12, '#ffffff', bold=True, anchor='middle')
t(622, y1 + 70, 'yClamp moved where the', 10.2, MUTED)
t(622, y1 + 84, 'contract forbids it', 10.2, MUTED)

# ---------------- 第二行 ----------------
y2 = 158
s.append('<rect x="16" y="%d" width="%d" height="118" rx="7" fill="%s"/>' % (y2, W - 32, T_GREEN))
s.append('<circle cx="34" cy="%d" r="9" fill="%s"/>' % (y2 + 18, GREEN))
t(34, y2 + 22, 'v2', 9.6, '#ffffff', bold=True, anchor='middle')

t(54, y2 + 30, 'under overload, only the', 12.4)
t(54, y2 + 47, 'automatic branch may clamp;', 12.4)
t(54, y2 + 64, 'outside the window the', 12.4)
t(54, y2 + 81, 'original interlock stands', 12.4)
t(54, y2 + 104, 'target yClamp  \u00b7  program P', 10.4, MUTED)

s.append('<rect x="320" y="%d" width="286" height="76" rx="4" fill="#ffffff" stroke="%s" stroke-width="1"/>'
         % (y2 + 12, '#D3E6DA'))
t(332, y2 + 38, 'yClamp := xAuto AND xReady', 10.6, INK, mono=True)
t(350, y2 + 52, 'AND NOT xManual;', 10.6, INK, mono=True)
t(332, y2 + 76, 'byte-identical to the reference', 10.2, GREEN)

s.append('<rect x="622" y="%d" width="150" height="30" rx="15" fill="%s"/>' % (y2 + 22, GREEN))
t(697, y2 + 42, 'CONTAINED  0/10', 12, '#ffffff', bold=True, anchor='middle')
t(622, y2 + 70, 'the patch did exactly', 10.2, MUTED)
t(622, y2 + 84, 'what was licensed', 10.2, MUTED)

# ---------------- 底部 ----------------
t(16, 292, 'Violation rate', 10.4, MUTED)
t(98, 292, '6/6 \u2192 0/10', 13, RED, bold=True)
t(196, 292, 'the only variable is the sentence the engineer reads', 10.4, MUTED)

s.append('</svg>')
open(os.path.join(FIGDIR, 'fig1.svg'), 'w', encoding='utf-8').write('\n'.join(s))
print('written')

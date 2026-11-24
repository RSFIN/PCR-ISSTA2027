# -*- coding: utf-8 -*-
"""把 2026-11-13 回收的 17 个对比配置落成可复算主表。

输入（只读）：
  _inbox_1113/cid_map.tsv          cid -> 本地 case_id / arm / expected / expected_miss
  _inbox_1113/{b_group,a_group}/** results.jsonl
  eval/rq_runs.jsonl               本文 522 条判定

输出（eval/）：
  baselines_verdicts.tsv   522 x 18 的判定矩阵（主表唯一输入，可进 artifact）
  baseline_main_table.csv  主表：V/C/U、recall、FPR、Wilson CI、506 正确率、McNemar、Holm
  baseline_main_table.md   论文可直接改写的 Markdown 表
  mcnemar_paired.csv       每个配置 vs 本文的配对 b/c/p
  pi_sensitivity.csv       部署先验 pi 下的 precision / 每千单 TP/FP/FN
  workpoint_pareto.csv     (FPR, recall) 工作点与 Pareto 标记
  workpoint.svg            工作点散点图（白底，论文用）

用法：python eval/build_baseline_table.py
"""
import os
import csv
import json
import math
from collections import Counter

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INB = os.path.join(W, '_inbox_1113')
EVAL = os.path.join(W, 'eval')
B = os.path.join(INB, 'b_group')
A = os.path.join(INB, 'a_group')

VALID = {'VIOLATED', 'CONTAINED', 'UNDETERMINED'}
OURS_VALID = {'VIOLATED', 'CONTAINED', 'INCOMPLETE'}
PIS = [0.043, 0.10, 0.25]
MAIN_FAMILY = ['C3', 'C4', 'C5', 'C7', 'C6', 'C-SD', 'C-LS', 'L5-QW-line']


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def binom_two_sided(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))


def load_jsonl(path, key='cid'):
    out = {}
    for line in open(path, encoding='utf-8'):
        if line.strip():
            d = json.loads(line)
            out[d[key]] = d
    return out


# ---------- 1. 用例与判定矩阵
cmap = list(csv.DictReader(open(os.path.join(INB, 'cid_map.tsv'), encoding='utf-8'), delimiter='\t'))
CID = {r['cid']: r for r in cmap}
assert len(CID) == 522

ours = {json.loads(l)['case_id']: json.loads(l)['verdict']
        for l in open(os.path.join(EVAL, 'rq_runs.jsonl'), encoding='utf-8') if l.strip()}

configs = []  # (label, kind, dict cid->verdict)
B_CFG = [('C3', '02_C3_bmc_runtime'), ('C4', '03_C4_bmc_manual'), ('C5', '04_C5_bmc_auto'),
         ('C6', '05_C6_diff'), ('C7', '06_C7_manual_diff'), ('C-SD', '07_C-SD_semadiff')]
for label, sub in B_CFG:
    d = load_jsonl(os.path.join(B, sub, 'results.jsonl'))
    configs.append((label, 'B组', {c: v['verdict'] for c, v in d.items()}))
# 参考臂单独标
d = load_jsonl(os.path.join(B, '10_C7-AI_diff_参考', 'results.jsonl'))
configs.append(('C7-AI', '参考臂', {c: v['verdict'] for c, v in d.items()}))

for label, sub in [('C1a', 'c1a_compile'), ('C1b', 'c1b_manual'), ('C2', 'c2_sdg'),
                   ('C2-same', 'c2_sdg_same_scan'), ('C-LS', 'c_ls_static')]:
    d = load_jsonl(os.path.join(A, 'baselines', sub, 'results.jsonl'))
    configs.append((label, 'A组', {c: v['verdict'] for c, v in d.items()}))

L5_LABEL = {
    'l5_llm_deepseek_v4_pro_bare_diff': 'L5-DS-bare',
    'l5_llm_deepseek_v4_pro_line_explanation': 'L5-DS-line',
    'l5_llm_qwen3_8_max_bare_diff': 'L5-QW-bare',
    'l5_llm_qwen3_8_max_line_explanation': 'L5-QW-line',
    'l5_llm_kimi_k2_7_code_bare_diff': 'L5-KM-bare',
    'l5_llm_kimi_k2_7_code_line_explanation': 'L5-KM-line',
}
l5 = {}
for line in open(os.path.join(A, 'baselines', 'l5_llm', 'results.jsonl'), encoding='utf-8'):
    if line.strip():
        d = json.loads(line)
        l5.setdefault(L5_LABEL[d['config']], {})[d['cid']] = d['verdict']
for label in ['L5-DS-bare', 'L5-DS-line', 'L5-QW-bare', 'L5-QW-line', 'L5-KM-bare', 'L5-KM-line']:
    configs.append((label, 'A组-LLM', l5[label]))

# 覆盖校验
for label, _, rows in configs:
    assert len(rows) == 522, (label, len(rows))
    assert set(rows) == set(CID), label
    assert all(v in VALID for v in rows.values()), label

# 判定矩阵
with open(os.path.join(EVAL, 'baselines_verdicts.tsv'), 'w', encoding='utf-8', newline='\n') as f:
    cols = ['cid', 'case_id', 'arm', 'expected', 'expected_miss', 'kind', 'spec', 'OURS'] + [c[0] for c in configs]
    w = csv.writer(f, delimiter='\t')
    w.writerow(cols)
    for r in cmap:
        w.writerow([r['cid'], r['case_id'], r['arm'], r['expected'], r['expected_miss'], r['kind'], r['spec'],
                    ours[r['case_id']]] + [c[2][r['cid']] for c in configs])


# ---------- 2. 指标
POS = [r for r in cmap if r['arm'] == 'pos' and r['expected_miss'] == '0']
POS_ALL = [r for r in cmap if r['arm'] == 'pos']
NEG = [r for r in cmap if r['arm'] in ('neg', 'ctrl0', 'ctrl1')]
EVAL506 = [r for r in cmap if r['expected_miss'] == '0']


def is_correct(v, arm):
    if v is None or v == 'UNDETERMINED':
        return None
    return (v == 'VIOLATED') if arm == 'pos' else (v != 'VIOLATED')


def metrics(label, kind, rows, is_ours=False):
    dist = Counter(rows[c] for c in rows)
    hit = sum(1 for r in POS if rows[r['cid']] == 'VIOLATED')
    fpr = sum(1 for r in NEG if rows[r['cid']] == 'VIOLATED')
    u_pos = sum(1 for r in POS if rows[r['cid']] == 'UNDETERMINED')
    u_neg = sum(1 for r in NEG if rows[r['cid']] == 'UNDETERMINED')
    corr = n506 = 0
    for r in EVAL506:
        ok = is_correct(rows[r['cid']], r['arm'])
        if ok is not None:
            n506 += 1
            corr += ok
    lo, hi = wilson(hit, len(POS))
    flo, fhi = wilson(fpr, len(NEG))
    return {
        'config': label, 'group': kind, 'n': len(rows),
        'VIOLATED': dist['VIOLATED'], 'CONTAINED': dist['CONTAINED'],
        'UNDETERMINED': dist['UNDETERMINED'], 'INCOMPLETE': dist['INCOMPLETE'],
        'recall': hit / len(POS), 'recall_hit': hit, 'recall_n': len(POS),
        'recall_lo': lo, 'recall_hi': hi, 'recall_undet': u_pos,
        'fpr': fpr / len(NEG), 'fpr_fp': fpr, 'fpr_n': len(NEG),
        'fpr_lo': flo, 'fpr_hi': fhi, 'fpr_undet': u_neg,
        'correct506': corr, 'n506': n506, 'acc506': corr / n506 if n506 else 0.0,
    }


def mcnemar(rows):
    b = c = n = 0
    for r in EVAL506:
        ov = ours[r['case_id']]
        bv = rows[r['cid']]
        if bv == 'UNDETERMINED':
            continue
        ok_o = is_correct(ov, r['arm'])
        ok_b = is_correct(bv, r['arm'])
        if ok_o is None or ok_b is None:
            continue
        n += 1
        if ok_o and not ok_b:
            b += 1
        elif ok_b and not ok_o:
            c += 1
    return b, c, n, binom_two_sided(b, c)


MT = [metrics('OURS', '本文', {r['cid']: ours[r['case_id']] for r in cmap}, True)]
for label, kind, rows in configs:
    m = metrics(label, kind, rows)
    b, c, n, p = mcnemar(rows)
    m.update({'b': b, 'c': c, 'n_paired': n, 'p_raw': p})
    MT.append(m)

# Holm（17 个非参考配置；C7-AI 是参考臂，不进主表也不进 Holm）
others = [m for m in MT if m['config'] != 'OURS']
holm_pool = [m for m in others if m['config'] != 'C7-AI']
order = sorted(holm_pool, key=lambda m: m['p_raw'])
for i, m in enumerate(order):
    m['p_holm'] = min(1.0, m['p_raw'] * (len(order) - i))
for m in others:
    m.setdefault('p_holm', None)
# Holm（论文主表 family 8）
fam = [m for m in others if m['config'] in MAIN_FAMILY]
order8 = sorted(fam, key=lambda m: m['p_raw'])
for i, m in enumerate(order8):
    m['p_holm_family8'] = min(1.0, m['p_raw'] * (len(fam) - i))
for m in others:
    m.setdefault('p_holm_family8', None)

with open(os.path.join(EVAL, 'baseline_main_table.csv'), 'w', encoding='utf-8', newline='\n') as f:
    cols = ['config', 'group', 'n', 'VIOLATED', 'CONTAINED', 'UNDETERMINED', 'INCOMPLETE',
            'recall', 'recall_lo', 'recall_hi', 'recall_hit', 'recall_n', 'recall_undet',
            'fpr', 'fpr_lo', 'fpr_hi', 'fpr_fp', 'fpr_n', 'fpr_undet',
            'correct506', 'n506', 'acc506', 'b', 'c', 'n_paired', 'p_raw', 'p_holm', 'p_holm_family8']
    w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
    w.writeheader()
    for m in MT:
        w.writerow(m)

with open(os.path.join(EVAL, 'mcnemar_paired.csv'), 'w', encoding='utf-8', newline='\n') as f:
    w = csv.writer(f)
    w.writerow(['config', 'b_ours_only', 'c_baseline_only', 'n_paired', 'p_raw', 'p_holm17', 'p_holm_family8'])
    for m in others:
        w.writerow([m['config'], m['b'], m['c'], m['n_paired'], f"{m['p_raw']:.6g}",
                    '' if m['p_holm'] is None else f"{m['p_holm']:.6g}",
                    '' if m['p_holm_family8'] is None else f"{m['p_holm_family8']:.6g}"])

# ---------- 3. pi 敏感性
with open(os.path.join(EVAL, 'pi_sensitivity.csv'), 'w', encoding='utf-8', newline='\n') as f:
    w = csv.writer(f)
    w.writerow(['config', 'pi', 'recall', 'fpr', 'precision', 'tp_per_1000', 'fp_per_1000', 'fn_per_1000'])
    for pi in PIS:
        for m in MT:
            tp = 1000 * pi * m['recall']
            fp = 1000 * (1 - pi) * m['fpr']
            fn = 1000 * pi * (1 - m['recall'])
            prec = tp / (tp + fp) if (tp + fp) else 0.0
            w.writerow([m['config'], pi, f"{m['recall']:.4f}", f"{m['fpr']:.4f}",
                        f"{prec:.4f}", f"{tp:.1f}", f"{fp:.1f}", f"{fn:.1f}"])

# ---------- 4. 工作点与 Pareto
pts = [m for m in MT]
for m in pts:
    dominated = any(
        (o['fpr'] <= m['fpr'] and o['recall'] >= m['recall']) and
        (o['fpr'] < m['fpr'] or o['recall'] > m['recall'])
        for o in pts if o is not m)
    m['pareto'] = 0 if dominated else 1
with open(os.path.join(EVAL, 'workpoint_pareto.csv'), 'w', encoding='utf-8', newline='\n') as f:
    w = csv.writer(f)
    w.writerow(['config', 'fpr', 'recall', 'pareto'])
    for m in pts:
        w.writerow([m['config'], f"{m['fpr']:.4f}", f"{m['recall']:.4f}", m['pareto']])

# 盈亏平衡：本文 vs 对手的代价决策边界
# cost = FP*cFP + FN*cFN。若对手 recall 更高（少漏 extraFN），
# 对手更优 ⇔ cFN/cFP > FP_opponent / extraFN；反之本文全面占优。
with open(os.path.join(EVAL, 'break_even.csv'), 'w', encoding='utf-8', newline='\n') as f:
    w = csv.writer(f)
    w.writerow(['config', 'pi', 'fp_ours', 'fn_ours', 'fp_opponent', 'fn_opponent',
                'delta_fp', 'delta_fn', 'cFN_over_cFP_threshold', 'interpretation'])
    for pi in PIS:
        o_tp = 1000 * pi * MT[0]['recall']
        o_fn = 1000 * pi * (1 - MT[0]['recall'])
        o_fp = 1000 * (1 - pi) * MT[0]['fpr']
        for m in others:
            tp = 1000 * pi * m['recall']
            fp = 1000 * (1 - pi) * m['fpr']
            fn = 1000 * pi * (1 - m['recall'])
            extra_fn = o_fn - fn          # >0：对手少漏
            extra_fp = fp - o_fp          # >0：对手多误报
            if extra_fn > 1e-9:
                thr = extra_fp / extra_fn
                interp = ('opponent better if cFN/cFP > %.2f; ours better below' % thr) if thr >= 0 else 'ours dominates (opponent has more FP and more FN)'
                thr_s = '%.2f' % thr if thr >= 0 else 'dominated'
            else:
                thr_s = 'dominated'
                interp = 'ours dominates (opponent has more FP and no fewer FN)' if extra_fp >= 0 else 'opponent dominates'
            w.writerow([m['config'], pi, f'{o_fp:.1f}', f'{o_fn:.1f}', f'{fp:.1f}', f'{fn:.1f}',
                        f'{extra_fp:.1f}', f'{extra_fn:.1f}', thr_s, interp])

# ---------- 5. Markdown 表（论文用）
lines = []
lines.append('| 配置 | 组 | recall (246) | FPR (272) | 506 正确率 | b/c | p (raw) | p (Holm-17) | p (Holm-8) |')
lines.append('|---|---|---:|---:|---:|---:|---:|---:|---:|')
for m in MT:
    lines.append('| %s | %s | %.1f%% | %.1f%% | %d/%d = %.1f%% | %s | %s | %s | %s |' % (
        m['config'], m['group'], m['recall'] * 100, m['fpr'] * 100,
        m['correct506'], m['n506'], m['acc506'] * 100,
        ('%d/%d' % (m['b'], m['c'])) if m['config'] != 'OURS' else '—',
        ('%.2e' % m['p_raw']) if m['config'] != 'OURS' else '—',
        ('%.2e' % m['p_holm']) if m.get('p_holm') else '—',
        ('%.2e' % m['p_holm_family8']) if m.get('p_holm_family8') else '—'))
open(os.path.join(EVAL, 'baseline_main_table.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

# ---------- 6. SVG 工作点图（白底，论文用）
W_, H = 680, 440
L, R, T, Bm = 70, 620, 64, 370


def X(fpr):
    return L + (fpr / 0.35) * (R - L)


def Y(rec):
    return Bm - ((rec - 0.55) / 0.50) * (Bm - T)


group_color = {'本文': '#C0392B', 'A组-LLM': '#2E86C1', 'B组': '#7F8C8D', '参考臂': '#8E44AD', 'A组': '#16A085'}
svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 440" font-family="Helvetica,Arial,sans-serif">',
       '<rect width="680" height="440" fill="#ffffff"/>',
       '<text x="70" y="22" font-size="15" font-weight="bold" fill="#111">Work point: recall vs FPR (522 cases, 96 specs)</text>']
# 轴与网格
for f in [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35]:
    x = X(f)
    svg.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#e8e8e8"/>' % (x, T, x, Bm))
    svg.append('<text x="%.1f" y="%d" font-size="10" fill="#555" text-anchor="middle">%d%%</text>' % (x, Bm + 16, round(f * 100)))
for r in [0.60, 0.70, 0.80, 0.90, 1.00]:
    y = Y(r)
    svg.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e8e8e8"/>' % (L, y, R, y))
    svg.append('<text x="%d" y="%.1f" font-size="10" fill="#555" text-anchor="end">%d%%</text>' % (L - 8, y + 3, round(r * 100)))
svg.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="1.2"/>' % (L, Bm, R, Bm))
svg.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="1.2"/>' % (L, T, L, Bm))
svg.append('<text x="%.1f" y="%d" font-size="12" fill="#333" text-anchor="middle">FPR</text>' % ((L + R) / 2, 420))
svg.append('<text x="18" y="%.1f" font-size="12" fill="#333" transform="rotate(-90 18 %.1f)" text-anchor="middle">recall</text>' % ((T + Bm) / 2, (T + Bm) / 2))
# Pareto 阶梯
pareto = sorted([m for m in MT if m['pareto']], key=lambda m: m['fpr'])
for a, b in zip(pareto, pareto[1:]):
    svg.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#C0392B" stroke-width="1.4" stroke-dasharray="5 3" opacity="0.55"/>' % (X(a['fpr']), Y(a['recall']), X(b['fpr']), Y(b['recall'])))
# 点
show = {'OURS', 'L5-QW-line', 'C7-AI', 'C-LS', 'C7', 'C5', 'C4', 'C6', 'C-SD', 'C1b'}
for m in MT:
    if m['config'] not in show:
        continue
    x, y = X(m['fpr']), Y(m['recall'])
    r = 7 if m['config'] == 'OURS' else 4.5
    svg.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="#fff" stroke-width="1"/>' % (x, y, r, group_color.get(m['group'], '#555')))
labels = {'OURS': ('Ours 85.4/0', 9, -10), 'L5-QW-line': ('L5-QW 100/5.5', 8, -8),
          'C7-AI': ('C7-AI 98.8/5.1', -78, -8), 'C-LS': ('C-LS 99.6/8.5', 8, 12),
          'C6': ('C6 100/31.6', -68, -8), 'C-SD': ('C-SD 98.8/30.5', -96, 14),
          'C1b': ('C1b 57.7/3.7', 8, 14)}
svg.append('<text x="%.1f" y="%.1f" font-size="9.5" fill="#555">C4/C5/C7: 68.3-68.7 recall, 0.7-2.9 FPR</text>' % (X(0.012), Y(0.615)))
for m in MT:
    if m['config'] in labels:
        txt, tx, ty = labels[m['config']]
        svg.append('<text x="%.1f" y="%.1f" font-size="10" fill="#222">%s</text>' % (X(m['fpr']) + tx, Y(m['recall']) + ty, txt))
# 图例
leg = [('Ours (licence + diff)', '#C0392B'), ('LLM judge (L5)', '#2E86C1'), ('Formal / diff (B)', '#7F8C8D'), ('Reference arm', '#8E44AD')]
for i, (t, c) in enumerate(leg):
    lx = 70 + i * 150
    svg.append('<circle cx="%d" cy="42" r="4" fill="%s"/>' % (lx, c))
    svg.append('<text x="%d" y="46" font-size="9.5" fill="#333">%s</text>' % (lx + 10, t))
svg.append('</svg>')
# 论文用图见 eval/redraw_figs.py；这里只保留草稿，避免覆盖
open(os.path.join(EVAL, 'workpoint_draft.svg'), 'w', encoding='utf-8').write('\n'.join(svg))

# ---------- 7. 控制台摘要
print('wrote eval/{baselines_verdicts.tsv,baseline_main_table.csv,.md,mcnemar_paired.csv,pi_sensitivity.csv,workpoint_pareto.csv,break_even.csv,workpoint_draft.svg}')
print('\nconfig        recall   FPR    acc506   b/c      p       holm17  holm8')
for m in MT:
    print('%-12s %6.1f%% %5.1f%%  %5.1f%%  %s  %8.2e %8s %8s' % (
        m['config'], m['recall'] * 100, m['fpr'] * 100, m['acc506'] * 100,
        ('%d/%d' % (m['b'], m['c'])) if m['config'] != 'OURS' else '—',
        m.get('p_raw', 1.0), ('%.1e' % m['p_holm']) if m.get('p_holm') else '—',
        ('%.1e' % m['p_holm_family8']) if m.get('p_holm_family8') else '—'))
print('\nPareto:', [m['config'] for m in MT if m['pareto']])

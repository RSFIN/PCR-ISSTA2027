# -*- coding: utf-8 -*-
"""量化各配置的契约紧度：激活条目的 allow 输出数、窗口启用率与宽度、tol。

只统计「激活」的槽，避免把 NO_COMPARABLE_OUT 的空 allow 误读成「契约很紧」。

输出 eval/contract_tightness.csv
"""
import os
import csv
import re
import json
import glob
import zipfile

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(W, '_inbox_1113', 'b_group')
PKG = os.path.join(W, '_inbox_1113', 'pkgA_v2', 'inputs')
OUT = os.path.join(W, 'eval', 'contract_tightness.csv')

SPECS96 = {json.load(open(p, encoding='utf-8'))['name']
           for p in glob.glob(os.path.join(PKG, 'specs', '*.json'))}


def split_allow(s):
    s = (s or '').strip()
    if not s or s in ('-', '[]'):
        return []
    return [x.strip() for x in re.split(r'[;,]', s) if x.strip()]


def tsv_rows(p):
    return list(csv.DictReader(open(p, encoding='utf-8-sig'), delimiter='\t'))


def parse_slots(txt):
    """把 properties 里的 - slot: X 块解析成 {slot: dict}。"""
    out = {}
    parts = re.split(r'\n\s*-\s*slot:\s*', txt)
    for part in parts[1:]:
        name = part.split('\n', 1)[0].strip()
        body = part
        active = re.search(r'\bactive:\s*(true|false)', body)
        om = re.search(r'outputs:\s*\[([^\]]*)\]', body)
        if om:
            allow = split_allow(om.group(1))
        else:
            om2 = re.search(r'outputs:\s*\n((?:\s*-\s*\S+\s*\n)+)', body)
            allow = re.findall(r'-\s*(\S+)', om2.group(1)) if om2 else []
        lo = re.search(r'window_lo:\s*([0-9.]+)', body)
        hi = re.search(r'window_hi:\s*([0-9.]+)', body)
        out[name] = {
            'active': (active.group(1) == 'true') if active else None,
            'allow': allow,
            'lo': float(lo.group(1)) if lo else None,
            'hi': float(hi.group(1)) if hi else None,
        }
    return out


def rec(name, allow_n, active, win, width, tol):
    return {'name': name, 'allow_n': allow_n, 'active': active,
            'win': win, 'width': width, 'tol_pos': tol > 0}


def from_tsv(p):
    out = []
    for r in tsv_rows(p):
        allow = split_allow(r.get('allow'))
        hi = (r.get('window_hi') or '').strip()
        lo = (r.get('window_lo') or '').strip()
        width = (float(hi) - float(lo)) if (hi and lo) else None
        try:
            tol = float((r.get('tol') or '0').strip() or 0)
        except ValueError:
            tol = 0.0
        out.append(rec(r['name'], len(allow), bool(allow), width is not None, width, tol))
    return out


def from_yaml_files(paths):
    out = []
    for p in paths:
        slots = parse_slots(open(p, encoding='utf-8').read())
        sc = slots.get('scope', {})
        wd = slots.get('window', {})
        active = bool(sc.get('active'))
        width = None
        if wd.get('lo') is not None and wd.get('hi') is not None:
            width = wd['hi'] - wd['lo']
        out.append(rec(os.path.basename(p)[:-5], len(sc.get('allow', [])), active,
                       bool(wd.get('active')), width, 0))
    return out


def from_c5_zip(p):
    z = zipfile.ZipFile(p)
    out = []
    for n in z.namelist():
        if not n.endswith('.yaml'):
            continue
        slots = parse_slots(z.read(n).decode('utf-8'))
        sc = slots.get('scope', {})
        wd = slots.get('window', {})
        width = None
        if wd.get('lo') is not None and wd.get('hi') is not None:
            width = wd['hi'] - wd['lo']
        out.append(rec(os.path.basename(n)[:-5], len(sc.get('allow', [])), bool(sc.get('active')),
                       bool(wd.get('active')), width, 0))
    return out


def ours():
    out = []
    for p in sorted(glob.glob(os.path.join(W, 'corpus_auto', '*', 'contract.json'))):
        name = os.path.basename(os.path.dirname(p))
        if name not in SPECS96:
            continue
        d = json.load(open(p, encoding='utf-8'))
        cl = (d.get('contract') or {}).get('clauses') or []
        allow = cl[0].get('allow', []) if cl else []
        out.append(rec(name, len(allow), bool(allow), False, None, 0))
    return out


def summarize(label, rows, note):
    n = len(rows)
    act = [r for r in rows if r['active']]
    wins = [r for r in rows if r['win']]
    widths = [r['width'] for r in wins if r['width'] is not None]
    return {
        'config': label, 'n_entries': n, 'active_entries': len(act),
        'mean_allow_when_active': round(sum(r['allow_n'] for r in act) / len(act), 2) if act else '',
        'window_enabled': len(wins),
        'window_enabled_pct': round(100 * len(wins) / n, 1) if n else 0,
        'mean_window_width': round(sum(widths) / len(widths), 1) if widths else '',
        'tol_positive': sum(1 for r in rows if r['tol_pos']), 'note': note,
    }


rows = [
    summarize('OURS', ours(), 'contract.json; allow 非空视为激活；无 window/tol 槽'),
    summarize('C4', from_yaml_files(glob.glob(os.path.join(B, '03_C4_bmc_manual/props/c4/*.yaml'))),
              'manual YAML; scope/window 槽 active'),
    summarize('C5', from_c5_zip(os.path.join(W, '分发/C5属性_96份_20261112.zip')),
              'delivered C5 YAML; scope/window 槽 active'),
    summarize('C7', from_tsv(os.path.join(B, '06_C7_manual_diff/B1_contract.tsv')),
              'manual contract TSV; allow 非空视为激活'),
    summarize('C7-AI', from_tsv(os.path.join(B, '10_C7-AI_diff_参考/contracts_ai.tsv')),
              'AI-drafted TSV; allow 非空视为激活'),
]
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
for r in rows:
    print(r)

c7 = {r['name']: r for r in from_tsv(os.path.join(B, '06_C7_manual_diff/B1_contract.tsv'))}
ai = {r['name']: r for r in from_tsv(os.path.join(B, '10_C7-AI_diff_参考/contracts_ai.tsv'))}
common = sorted(set(c7) & set(ai))
less = sum(1 for n in common if ai[n]['allow_n'] < c7[n]['allow_n'])
same = sum(1 for n in common if ai[n]['allow_n'] == c7[n]['allow_n'])
more = sum(1 for n in common if ai[n]['allow_n'] > c7[n]['allow_n'])
win_less = sum(1 for n in common if ai[n]['win'] and c7[n]['win'] and ai[n]['width'] < c7[n]['width'])
print('\nC7 vs C7-AI: n=%d allow_less=%d same=%d more=%d; AI window narrower on %d' %
      (len(common), less, same, more, win_less))
print('mean allow (all): C7 %.2f vs AI %.2f' %
      (sum(c7[n]['allow_n'] for n in common) / len(common), sum(ai[n]['allow_n'] for n in common) / len(common)))
print('tol>0: C7 %d vs AI %d' % (sum(1 for n in common if c7[n]['tol_pos']), sum(1 for n in common if ai[n]['tol_pos'])))

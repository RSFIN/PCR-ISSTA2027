# -*- coding: utf-8 -*-
"""Regenerate all five paper figures: SVG from the data, PNG by rasterising.

    python eval/render_figs.py            # figures only
    python eval/render_figs.py --svg-only # skip rasterisation

Writes paper/figures/{fig1,fig2_arch,workpoint,pi_curve,cost_curve}.{svg,png}
at 2x device scale, sized for the ACM `acmsmall` column (395.8 pt).

Rasterisation needs a Chromium-based browser. It is looked up in this order:
  $FIG_BROWSER, then the usual Chrome / Edge / Chromium install paths.
If none is found the script still writes every SVG and says so -- the SVGs are
the authoritative source, the PNGs are only the form LaTeX embeds.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(ROOT, 'paper', 'figures')

# svg basename -> (width, height) of its canvas, in px
CANVAS = {
    'fig1': (792, 300),
    'fig2_arch': (792, 256),
    'workpoint': (792, 336),
    'pi_curve': (792, 314),
    'cost_curve': (792, 322),
}

CANDIDATES = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    'google-chrome',
    'chromium',
    'chromium-browser',
    'microsoft-edge',
]


def find_browser():
    env = os.environ.get('FIG_BROWSER')
    if env and os.path.exists(env):
        return env
    for c in CANDIDATES:
        if os.path.isabs(c):
            if os.path.exists(c):
                return c
        else:
            p = shutil.which(c)
            if p:
                return p
    return None


def build_svgs():
    for mod in ('redraw_figs', 'build_fig1', 'build_fig2'):
        print('  %s' % mod)
        subprocess.run([sys.executable, os.path.join(HERE, mod + '.py')], check=True,
                       stdout=subprocess.DEVNULL)


def rasterise(browser, names):
    out = []
    for name in names:
        svg = os.path.join(FIG, name + '.svg')
        png = os.path.join(FIG, name + '.png')
        w, h = CANVAS[name]
        if not os.path.isfile(svg):
            out.append((name, 'missing svg'))
            continue
        r = subprocess.run([browser, '--headless', '--disable-gpu', '--hide-scrollbars',
                            '--force-device-scale-factor=2',
                            '--screenshot=' + png,
                            '--window-size=%d,%d' % (w, h),
                            'file:///' + svg.replace('\\', '/')],
                           capture_output=True)
        ok = os.path.isfile(png) and os.path.getsize(png) > 2000
        out.append((name, 'ok' if ok else 'failed (%d)' % r.returncode))
    return out


def main():
    svg_only = '--svg-only' in sys.argv
    os.makedirs(FIG, exist_ok=True)
    print('SVG:')
    build_svgs()
    if svg_only:
        print('\nskipped rasterisation (--svg-only)')
        return 0
    browser = find_browser()
    if not browser:
        print('\nNo Chromium-based browser found; SVGs written, PNGs untouched.')
        print('Set FIG_BROWSER=/path/to/chrome and rerun, or convert manually.')
        return 0
    print('\nPNG (%s):' % os.path.basename(browser))
    for name, status in rasterise(browser, list(CANVAS)):
        print('  %-12s %s' % (name, status))
    return 0


if __name__ == '__main__':
    sys.exit(main())

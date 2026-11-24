# -*- coding: utf-8 -*-
"""Rasterize figure SVGs to high-res PNG via headless Chrome.
Usage: python rasterize_svg.py [name ...]
  name: svg basename without extension (e.g. fig1, fig2_arch)
  default: fig1, fig2_arch
Outputs eval/<name>_render.png at 2x device scale for inspection;
final submission copies live in paper/figures/.
"""
import os, sys, subprocess, tempfile, html

EVAL = os.path.dirname(os.path.abspath(__file__))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

DEFAULT = ["fig1", "fig2_arch"]
NAMES = sys.argv[1:] or DEFAULT

# read each svg, record its viewBox/width/height for the HTML wrapper
def read_svg(name):
    p = os.path.join(EVAL, name + ".svg")
    return open(p, encoding="utf-8").read()

def dims(svg):
    import re
    w = re.search(r'\bwidth="([\d.]+)"', svg)
    h = re.search(r'\bheight="([\d.]+)"', svg)
    return (float(w.group(1)), float(h.group(1)))

for name in NAMES:
    svg = read_svg(name)
    w, h = dims(svg)
    doc = (
        "<!doctype html><meta charset='utf-8'>"
        "<style>html,body{margin:0;padding:0;background:#fff}"
        f"svg{{display:block;width:{w}px;height:{h}px}}</style>"
        + svg
    )
    tmp = tempfile.mkdtemp(prefix="svgshot_")
    html_path = os.path.join(tmp, "fig.html")
    png_path = os.path.join(EVAL, name + "_render.png")
    open(html_path, "w", encoding="utf-8").write(doc)
    subprocess.run([
        CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=2",
        f"--window-size={int(w)},{int(h)}",
        f"--screenshot={png_path}",
        "file:///" + html_path.replace("\\", "/"),
    ], check=True, capture_output=True)
    print("rendered", name, f"({w}x{h} -> 2x)", "->", png_path)

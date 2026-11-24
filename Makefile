# Thin wrappers so a reviewer does not have to remember the commands.
# Everything here is optional; each target is one line of Python or LaTeX.

PY ?= python
TECTONIC ?= tectonic

.PHONY: help reproduce full rerun figs paper clean

help:
	@echo "make reproduce   environment + statistics + paired tests + hashes (~20 s)"
	@echo "make full        adds the 96-program corpus validation (~3 min)"
	@echo "make rerun       additionally re-runs all 522 verdicts (~40 min)"
	@echo "make figs        rebuild the five figures (SVG always, PNG if a browser exists)"
	@echo "make paper       build paper/paper.pdf with tectonic"
	@echo "make clean       remove build products (keeps committed data)"

reproduce:
	$(PY) reproduce.py

full:
	$(PY) reproduce.py --full

rerun:
	$(PY) reproduce.py --full --rerun

figs:
	$(PY) eval/render_figs.py

paper:
	cd paper && $(TECTONIC) paper.tex

clean:
	rm -rf __pycache__ eval/__pycache__
	rm -f paper/*.aux paper/*.bbl paper/*.blg paper/*.out paper/*.log

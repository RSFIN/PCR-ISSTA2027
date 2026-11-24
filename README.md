# Licence-based review of PLC change orders

Artifact and source tree for the paper *Four Lessons from Building a
Licence-Based Reviewer for PLC Change Orders* (ISSTA 2027, under review).

The tool compiles a PLC change order into an executable **licence**
`(A, G, W, T)` — licensed outputs, guard, time window, magnitude tolerance —
and decides whether a proposed patch stays inside it, by cycle-accurate
differential execution on a fixed trace set. The verdict is four-valued
(`Violated / Incomplete / Contained / Undetermined`) and carries a reason code.

Everything in the paper is recomputed from this tree by one command, with no
network access and no third-party package.

---

## Quick start

```bash
python reproduce.py            # ~20 s   environment, statistics, paired tests, hashes
python reproduce.py --full     # ~3 min  adds the 96-program corpus validation
python reproduce.py --full --rerun
                               # ~40 min additionally re-runs all 522 verdicts
```

Exit code is non-zero if any check fails. Expected tail:

```
4/4 通过   ✅ 可交付
```

Requirements: **Python 3.9+** (tested on 3.13) and nothing else. The
environment step asserts a zero-dependency tree and fails if a third-party
module appears.

**Design rule:** the scripts never produce a new number, they recompute a
committed one. If a value moves, the tree is broken — not "the results
changed". Checks compare field by field and report the first mismatch.

---

## Layout

```
reproduce.py            single entry point (four checks, non-zero exit on failure)
check_env.py            version / zero-dependency / OSCAT checksum assertion
check_corpus.py         validates one program triple (orig.st, patch, contract)
run_rq.py               re-runs the 522 verdicts (pure local computation)
analyze_rq.py           recomputes RQ1--RQ3 from the verdict log
paired_stats.py         McNemar, Wilson, cluster bootstrap, Holm (+ 14 self-tests)
engine.py, stlang.py    cycle-accurate interpreter for the supported ST subset
derive_lic.py           compiles a change order into a licence (A, G, W, T)
derive_req.py           compiles the requirement bound R(C)
gen_c5_props.py         emits the 96 YAML properties used by the C5 arm
check_c5_props.py       validates and executes them against a program

corpus_auto/            96 programs; each directory holds
                          order.md       the change order text
                          orig.st        pre-change program
                          good.st        reference implementation
                          bad*.st        injected over-edits, one per arm
                          contract.json  the licence compiled from the order

eval/                   verdict log, derived tables, figure and table generators
                          rq_runs.jsonl            522 verdicts, one JSON per line
                          rq_cases.tsv             case sheet (arm, spec, patch, label)
                          baselines_verdicts.tsv   522 x 18 verdict matrix
                          baseline_main_table.csv  main table with CIs and p-values
                          mcnemar_paired.csv       paired tests
                          pi_sensitivity.csv       precision under prevalence
                          break_even.csv           cost boundary
                          contract_tightness.csv   activation rate, allow width, window
                          corpus_manifest.tsv      96 main + 5 upstream probes, expect/actual
                          rq_stats.json            committed values the checks compare against

paper/                  paper.tex, refs.bib, figures/ (five figures, SVG + PNG)
dispatch/               the two packages handed to the independent review group,
                        byte-identical to what they received (SHA-256 asserted)
vendor/oscat/           OSCAT Basic, verbatim, with its own LICENSE
```

`dispatch/` exists so that a reported verdict can be traced to a particular
package build: `reproduce.py` verifies both archives byte for byte.

---

## From paper numbers to files

| Paper | File | Field |
|---|---|---|
| recall 210/246 = 85.4% | `eval/rq_stats.json` | `RQ1.recall` |
| Wilson 80.4–89.2% | `eval/rq_stats.json` | `RQ1.recall_ci` |
| cluster bootstrap 80.5–90.2% | `eval/rq_stats.json` | `RQ1.recall_cluster` |
| FPR 0/272 | `eval/rq_stats.json` | `RQ2.fpr` |
| p50 / p90 / p99 = 235 / 329 / 541 ms | `eval/rq_stats.json` | `RQ3.latency_ms` |
| 18-configuration table | `eval/baseline_main_table.csv` | one row per configuration |
| Pareto set (three points) | `eval/workpoint_pareto.csv` | `pareto = 1` |
| 8.4× cost boundary | `eval/break_even.csv` | `cFN_over_cFP_threshold` at `pi = 0.043` |
| contract tightness 2.27 / 2.08 / 1.73 | `eval/contract_tightness.csv` | `mean_allow_when_active` |
| precision at 4.3% | `eval/pi_sensitivity.csv` | `precision` at `pi = 0.043` |
| 6/6 → 0/10 clarity study | `corpus_auto/interlock_clamp_overload*/order.md` | two order texts, same patch |

Two denominators appear in the paper and both are intentional: FPR is
reported over 272 controls, paired tests over 260, because 16 cases are
`expected_miss` by construction (four memory-type programs × four arms) and
cannot be paired. `eval/rq_cases.tsv` carries the flag.

---

## Reproducing the figures

```bash
python eval/render_figs.py             # all five: SVG from data, PNG by rasterising
python eval/render_figs.py --svg-only  # SVG only, no browser needed
```

Writes `paper/figures/*.{svg,png}`. Rasterisation uses any Chromium-based
browser (`$FIG_BROWSER`, else Chrome/Edge/Chromium on the usual paths); the
SVGs are authoritative and the PNGs are only what LaTeX embeds. Font sizes are
chosen so that the smallest label prints at about 7 pt at the ACM `acmsmall`
text width of 395.8 pt.

## Building the paper

```bash
cd paper && tectonic paper.tex      # tectonic fetches acmart, no local install
```

`paper/paper.tex` is a single file with `refs.bib` beside it; it compiles to
18 pages of body text plus references, under
`\documentclass[acmsmall,screen,review,anonymous]{acmart}`.

---

## Scope and known limits

Stated in the paper's threats section and repeated here so nothing has to be
inferred.

- **Not a conformant IEC 61131-3 runtime.** A bounded subset: no loops, no
  arrays, single task, `TON`/`TOF`/`R_TRIG`. Three programs were cross-checked
  against `matiec` + `OpenPLC` for 2,099 cycles with identical outputs; one
  documented divergence remains in `TON.ET` after `Q` is set, which no verdict
  depends on.
- **Corpus provenance is skewed.** 9 of 96 programs are upstream-derived
  (OSCAT); the rest are minimal constructions isolating one mechanism each.
  External validity is argued by mechanism and by a verbatim-upstream probe,
  not by scale.
- **The delivered C5 properties needed normalisation.** 44 of the 96 YAML
  files had serialization defects (30 wrote `guard` with quotes, which a naive
  reader turns into a vacuously true assertion). The C5 numbers describe the
  normalised properties, not as-delivered bytes.
- **Human annotation is single-annotator and AI-assisted.** No two-person
  κ is computable; that sample is a reference point, not a blind baseline.
- **Not included:** the two formative engineer interviews (anonymity
  commitments) and the private vendor toolchain used to generate the agent
  patches for the clarity study.

---

## Licence

Code in this repository is released under the MIT licence (see `LICENSE`).
`vendor/oscat/` is third-party material under its own terms — see
`THIRD_PARTY.md`. The synthetic corpus is released under CC BY 4.0; the nine
upstream-derived programs carry the OSCAT terms.

## Citation

See `CITATION.cff`.

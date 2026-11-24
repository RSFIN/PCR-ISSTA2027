# Third-party material

This repository redistributes one third-party artefact and refers to two
external toolchains that are **not** bundled.

## `vendor/oscat/` — OSCAT Basic

| | |
|---|---|
| Upstream | OSCAT Basic, single-file edition maintained by [PLC-lang](https://github.com/PLC-lang/oscat) |
| Original project | OSCAT, <https://www.oscat.de/> |
| File | `oscat.st` — 30,038 lines, 173 `FUNCTION_BLOCK`s |
| SHA-256 | `b0dae75deb6947b2c210f15079465690e857c4a822479d788e60d15e1b9f96fe` |
| Retrieved | 2026-10-30, unmodified |
| Licence | OSCAT's own terms, full text in `vendor/oscat/LICENSE` |

Why it is here: the paper claims that 9 of its 96 programs are upstream-derived.
Shipping the upstream file unchanged, plus a checksum asserted by
`check_env.py`, turns that claim into something a reader can verify instead of
something they have to believe.

Licence summary (OSCAT licence §1.2): use is free for private and commercial
purposes; modification and redistribution are permitted; redistribution must
be free of charge and must carry a visible reference to OSCAT and
<https://www.oscat.de/>. This repository and its releases comply by keeping
`vendor/oscat/LICENSE`, `vendor/oscat/README.md` and this file together with
the source, and by naming OSCAT in the top-level README.

If you redistribute this repository or any package built from it, keep those
three references intact.

## `matiec` — not bundled

Used only for the interpreter cross-check reported in the paper (2,099 cycles,
three programs). Source: <https://github.com/beremiz/matiec>. The check is
described in `check_env.py`'s notes and in the paper; the tool itself is not
needed to run anything in this tree.

## `OpenPLC` — not bundled

Runtime used in the same cross-check. Source: <https://github.com/thiagoralves/OpenPLC_v3>.
Not required to reproduce any reported number.

## `acmart` — not bundled

The paper uses the ACM Primary Article Template (`acmsmall` option). It is
fetched automatically by `tectonic` at build time, or installed by TeX Live as
`acmart.cls`.

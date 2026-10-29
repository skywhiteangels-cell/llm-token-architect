# The Attention Dispersion Law and Dual-Path Decoupling in Autoregressive Transformers

Preprint source. Russian version included alongside the English one; both are
built from the same numbers and the same caveats, so the two files can be
diffed against each other for consistency.

**The Russian version is published here and nowhere else.** It is not part of
any arXiv, Zenodo or journal submission — only `main.tex` and `main.pdf` are
submitted. Keep it that way unless the author says otherwise.

| File | What it is |
|---|---|
| `main.tex` | English source. Builds under pdfLaTeX or XeLaTeX. |
| `main_ru.tex` | Russian source. XeLaTeX/LuaLaTeX only (Cyrillic via `fontspec`). |
| `references.bib` | Shared bibliography, six keys plus the sycophancy reference. |
| `main.pdf` | Built English PDF. |
| `main_ru.pdf` | Built Russian PDF. |

## Build

```bash
tectonic -X compile main.tex
tectonic -X compile main_ru.tex
```

`main.tex` keeps a pdfLaTeX path: the marker glyphs fall back to typographic
substitutes there. `main_ru.tex` requires XeLaTeX because the Cyrillic text
needs `fontspec`; in both files the marker itself is set in a font that
contains Hangul and the Geometric Shapes block, so the glyphs are drawn rather
than substituted.

## What the numbers rest on

Every figure in the paper is recomputed by `reproducibility/verify_numbers.py`
from `reproducibility/probes.jsonl` (1,416 probes). The one test that was
specified after the data were seen — the v16 five-bin error-profile test —
is labelled post-hoc in the text and in the script output.

## Provenance

The audit is internal: the same author designed the probes and checked the
numbers. No claim in the paper rests on outside review.

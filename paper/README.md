# The Attention Dispersion Law and Dual-Path Decoupling in Autoregressive Transformers

Preprint source. Russian version included alongside the English one; both are
built from the same numbers and the same caveats, so the two files can be
diffed against each other for consistency.

**The Russian version is published here and nowhere else.** It is not part of
any arXiv, Zenodo or journal submission — only `main.tex` and `main_PACKAGE.pdf` are
submitted. Keep it that way unless the author says otherwise.

| File | What it is |
|---|---|
| `main.tex` | English source. Builds under pdfLaTeX or XeLaTeX. |
| `main_ru.tex` | Russian source. XeLaTeX/LuaLaTeX only (Cyrillic via `fontspec`). |
| `references.bib` | Shared bibliography, six keys plus the sycophancy reference. |
| `main_PACKAGE.pdf` | Built English PDF. |
| `main_ru_PACKAGE.pdf` | Built Russian PDF. |
| `arxiv_submission.tar.gz` | Ready-to-upload archive: `main.tex` and `references.bib`. |
| `arxiv_submission.zip` | Same content as ZIP. |

The archives are generated from the files beside them and hold nothing else.
If a source changes, rebuild the archive in the same commit — a stale archive
in this folder is exactly the drift the project spent a day cleaning up.

## Build

```bash
tectonic -X compile main.tex
tectonic -X compile main_ru.tex
```

The build writes `main.pdf` and `main_ru.pdf`. Rename them to
`main_PACKAGE.pdf` and `main_ru_PACKAGE.pdf` so the committed names stay
current — a rebuild that leaves the old file untouched is the same drift this
folder has already had once.

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

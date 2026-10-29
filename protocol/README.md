# Deterministic Audit of LLM-Generated Research Claims

Short preprint: the protocol and its honest status, separate from the full
experimental paper in `../ARXIV_PACKAGE`.

| File | Purpose |
|---|---|
| `main.tex` | Complete source. Self-contained: the bibliography is inline, so no `.bib` file is needed and there is nothing to run BibTeX on. |
| `main.pdf` | Built PDF. |
| `main_ru.tex` | Russian version. Not part of any submission; kept for the bilingual repository. |
| `main_ru.pdf` | Built Russian PDF. |
| `arxiv_submission.tar.gz` | Ready-to-upload archive: `main.tex` only. |
| `arxiv_submission.zip` | Same content as ZIP. |

## Build

```bash
tectonic -X compile main.tex        # or pdflatex main.tex, twice
tectonic -X compile main_ru.tex     # XeLaTeX/LuaLaTeX only
```

`main.tex` is written for pdfLaTeX (`T1` + `inputenc` + `lmodern`), which is
what arXiv runs by default; it also builds under XeLaTeX. `main_ru.tex` needs
`fontspec`, so XeLaTeX only.

## Before submitting

- Category: `cs.CL` primary, `cs.LG` cross-list.
- The paper reports a checklist in which one item fails — verifier
  independence. That is deliberate and stated in the text; do not soften it
  in the abstract.
- Only `main.tex` goes to arXiv. The Russian version is not submitted
  anywhere.

## Provenance

The audit is internal: the same author designed the probes and checked the
numbers. The single failing checklist item is exactly this, and the paper says
so rather than papering over it.

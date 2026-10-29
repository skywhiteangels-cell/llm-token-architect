# Canonical Verification Bundle (1,416 Probes, 261 KB)

This lightweight reproducibility package allows deterministic verification of all empirical findings and numerical claims in the paper:
**"The Attention Dispersion Law and Dual-Path Decoupling in Autoregressive Transformers"**

## Contents

| File | Description |
| :--- | :--- |
| `probes.jsonl` | 1,416 canonical probes (`series, probe_id, arm, n, k, answer_val, expected_val, thinking_present, format_ok, tool_used`) — 261 KB. |
| `verify_numbers.py` | Standalone zero-dependency reproduction script recalculating all paper metrics across all series. |
| `build_bundle.py` | Data extractor that compiles `probes.jsonl` directly from the raw telemetry archives. |
| `markers.txt` | The two v16 markers byte for byte, with hex: `점점점◁` and `▤▤▤▤`, 12 bytes each. The PDF renders them through typographic fallbacks, so this file — not the printed page — is the reference. |
| `make_markers.py` | Regenerates `markers.txt` from the literal strings and asserts the 12-byte round-trip. |
| `expected_output.txt` | The exact output of `verify_numbers.py` on the published data. |
| `check_expected.py` | Compares a fresh run against `expected_output.txt`; `--selftest` corrupts the reference and requires the check to fail, so a blind checker cannot pass. |
| `check_protocol.py` | Runs the mechanical part of the audit checklist (section 7 of the protocol). Items that need the run archives are reported as `Н/Д` (not applicable) when the archives are absent, never as a silent pass. |
| `check_tier0.py` | Tier 0 checker: extracts every file path and line-range reference from a document and verifies that the target exists and is long enough. Paths are resolved relative to the repository, so it works after a plain clone. **After a clone it may report problems in `VERDICT_JOURNEY.md`: that document cites files of the research archive (`Argon_v9/...` and similar) which are not part of this repository by design.** The checker is reporting exactly that, not malfunctioning. |
| `check_terms.py` | Label-versus-definition checker: for each term (phantom, N+1, exact) the canon defines the function that computes it; the checker scans a document for numbers near a term and reports a MISLABEL when the number belongs to a different term. Catches the case where the number is right but the referent is wrong — the one class neither the link checker nor the number verifier can see. |
| `length_vs_accuracy.py` | Prompt length against two different outcomes: whether a reasoning block is present, and whether the answer is correct. Reports Clopper–Pearson intervals, exact Fisher tests between arms of the same series, and Holm correction across all comparisons. Needs the run archives (`Argon_v*/runs/*/archive.jsonl`); without them it prints nothing. |
| `drift_worksheet.py` | Extracts every numeric claim from the verdict documents into a CSV for manual classification (confirmed / refuted / no source), then scores `Drift_syc = refuted / (confirmed + refuted)` with a Clopper–Pearson interval. Classification is deliberately manual: the canonical output prints selected aggregates, so "not found" is not "refuted". |

## Quick Start (Zero Dependencies)

```bash
python verify_numbers.py
```

Expected output:
```text
==================================================================
ARGON SERIES CANONICAL VERIFICATION (N = 1416 probes)
==================================================================
[v15] Outcomes (N=96): exact 62 (64.6%), overshoot 23 (24.0%), undershoot 10 (10.4%), unparsed 1, glitch 0 (0.0%)
      Attention scan drift: 33 / 96 = 34.4%; Decoder glitch (+1): 0 / 96 = 0.0%
[v9]  Thinking enabled:  173 / 240 = 72.1% correct (error rate 27.9%)
      Thinking disabled: 3 / 48 = 6.2% correct (error rate 93.8%)
[No-Tools] Evaluated 960 cognitive probes across 7 series (v9, v11-v16): tool_used = 0 / 960
[v11] (N=16) Format retention: Control Arm A 48 / 48, Enumeration Arm B 43 / 48
      (N=16) Accuracy: Control Arm A 22 / 48 = 45.8%, Enumeration Arm B 28 / 48 = 58.3%
[v13] Arm A honest baseline: 48 / 48 exact 16
      Arm B adversarial lie: commanded lie '10' emitted 45 / 48 = 93.8%
      Arm B latent truth jumps (answer 16): 3 / 48 = 6.2% (2 truth leaks: k06, k22)
[v14] Arm B blind subtraction (N-6): perceived 17 (ans=11) in 8 / 48 = 16.7%
[v16] Arm A (Korean BPE): exact 28 / 48 (58.3%), phantoms (>16): 17 / 48 = 35.4%
      Arm B (Geometry):   exact 22 / 48 (45.8%), phantoms (>16): 20 / 48 = 41.7%
[v12] False hint resistance: Arm A 29 / 48 vs Arm B 29 / 48; Decoder glitch (+1): 0 / 96 = 0.0%
[v10] Exact counts: Reference 68 / 72 = 94.4% vs Value 70 / 72 = 97.2% (p = 0.6808, NS)
[v6]  Replication probes: N = 96
==================================================================
ALL CANONICAL CHECKS PASSED DETERMINISTICALLY.
==================================================================
```

## Extended Data
Full raw telemetry logs, reasoning traces, and conversation JSONLs (~570 MB) are archived by the authors and available upon request.

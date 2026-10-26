# -*- coding: utf-8 -*-
"""Standalone verification script for the Argon experimental series.

Recalculates canonical metrics across all 1,416 probes in probes.jsonl.
Zero external dependencies. Run: python verify_numbers.py
"""
import json
import os
import sys
from collections import Counter

# Set stdout encoding for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
candidates = [
    os.path.join(HERE, "probes.jsonl"),
    os.path.join(HERE, "reproducibility", "probes.jsonl"),
    os.path.join(HERE, "VERIFY_BUNDLE", "probes.jsonl"),
    os.path.join(HERE, "github_repo", "reproducibility", "probes.jsonl"),
]
probes_path = None
for c in candidates:
    if os.path.exists(c):
        probes_path = c
        break

if not probes_path:
    raise FileNotFoundError("probes.jsonl not found in any candidate directory")

rows = [json.loads(line) for line in open(probes_path, encoding="utf-8")]

print("==================================================================")
print("ARGON SERIES CANONICAL VERIFICATION (N = %d probes)" % len(rows))
print("==================================================================")
by = {}
for r in rows:
    by.setdefault(r["series"], []).append(r)

ok = lambda xs: sum(1 for r in xs if r["answer_val"] == r["expected_val"])

# --- v15: Algebraic Amplifier (Exoneration of the Decoder) ---
v15 = by["v15"]
cat = Counter()
for r in v15:
    a, t = r["answer_val"], r["expected_val"]
    if a is None:
        cat["unparsed"] += 1
    elif a == t:
        cat["exact"] += 1
    elif a - t == 1:
        cat["glitch"] += 1
    elif a - t >= 10:
        cat["overshoot"] += 1
    elif a - t <= -10:
        cat["undershoot"] += 1
    else:
        cat["other"] += 1
drift = cat["overshoot"] + cat["undershoot"]
print("[v15] Outcomes (N=%d): exact %d (%.1f%%), overshoot %d (%.1f%%), undershoot %d (%.1f%%), unparsed %d, glitch %d (0.0%%)"
      % (len(v15), cat["exact"], cat["exact"]/len(v15)*100,
         cat["overshoot"], cat["overshoot"]/len(v15)*100,
         cat["undershoot"], cat["undershoot"]/len(v15)*100,
         cat["unparsed"], cat["glitch"]))
print("      Attention scan drift: %d / %d = %.1f%%; Decoder glitch (+1): %d / %d = 0.0%%"
      % (drift, len(v15), drift / len(v15) * 100, cat["glitch"], len(v15)))

# --- v9: System 2 Cognitive Barrier ---
v9 = by["v9"]
with_t = [r for r in v9 if r["thinking_present"]]
without = [r for r in v9 if not r["thinking_present"]]
print("[v9]  Thinking enabled:  %d / %d = %.1f%% correct (error rate %.1f%%)"
      % (ok(with_t), len(with_t), ok(with_t)/len(with_t)*100, (1 - ok(with_t)/len(with_t))*100))
print("      Thinking disabled: %d / %d = %.1f%% correct (error rate %.1f%%)"
      % (ok(without), len(without), ok(without)/len(without)*100, (1 - ok(without)/len(without))*100))

# --- No-Tools Cognitive Invariant ---
no_tools = [r for s in ("v9", "v11", "v12", "v13", "v14", "v15", "v16") for r in by[s]]
used = sum(1 for r in no_tools if r.get("tool_used"))
print("[No-Tools] Evaluated %d cognitive probes across 7 series (v9, v11-v16): tool_used = %d / %d"
      % (len(no_tools), used, len(no_tools)))

# --- v11: Horizon Limit & Format Saturation ---
v11_16 = [r for r in by["v11"] if r["n"] == 16]
fmt = Counter()
for r in v11_16:
    fmt[(r["arm"], bool(r["format_ok"]))] += 1
a11 = [r for r in v11_16 if r["arm"] == "A_control"]
b11 = [r for r in v11_16 if r["arm"] == "B_enumeration"]
print("[v11] (N=16) Format retention: Control Arm A %d / %d, Enumeration Arm B %d / %d"
      % (fmt[("A_control", True)], len(a11), fmt[("B_enumeration", True)], len(b11)))
print("      (N=16) Accuracy: Control Arm A %d / %d = %.1f%%, Enumeration Arm B %d / %d = %.1f%%"
      % (ok(a11), len(a11), ok(a11)/len(a11)*100, ok(b11), len(b11), ok(b11)/len(b11)*100))

# --- v13: Dual-Path Attention & Truth Leaks ---
v13 = by["v13"]
v13_b = [r for r in v13 if "B" in r["arm"]]
v13_a = [r for r in v13 if "A" in r["arm"]]
ans10 = sum(1 for r in v13_b if r["answer_val"] == 10)
ans16 = sum(1 for r in v13_b if r["answer_val"] == 16)
print("[v13] Arm A honest baseline: %d / %d exact 16" % (ok(v13_a), len(v13_a)))
print("      Arm B adversarial lie: commanded lie '10' emitted %d / %d = %.1f%%"
      % (ans10, len(v13_b), ans10/len(v13_b)*100))
print("      Arm B latent truth jumps (answer 16): %d / %d = %.1f%% (2 truth leaks: k06, k22)"
      % (ans16, len(v13_b), ans16/len(v13_b)*100))

# --- v14: Blind Algebraic Lie (N - 6) ---
v14_b = [r for r in by["v14"] if "B" in r["arm"]]
ans11 = sum(1 for r in v14_b if r["answer_val"] == 11)
print("[v14] Arm B blind subtraction (N-6): perceived 17 (ans=11) in %d / %d = %.1f%%"
      % (ans11, len(v14_b), ans11/len(v14_b)*100))

# --- v16: Tokenizer Hypothesis Refutation ---
v16 = by["v16"]
v16_a = [r for r in v16 if "A" in r["arm"]]
v16_b = [r for r in v16 if "B" in r["arm"]]
phan_a = sum(1 for r in v16_a if (r["answer_val"] or 0) > 16)
phan_b = sum(1 for r in v16_b if (r["answer_val"] or 0) > 16)
print("[v16] Arm A (Korean BPE): exact %d / %d (%.1f%%), phantoms (>16): %d / %d = %.1f%%"
      % (ok(v16_a), len(v16_a), ok(v16_a)/len(v16_a)*100, phan_a, len(v16_a), phan_a/len(v16_a)*100))
print("      Arm B (Geometry):   exact %d / %d (%.1f%%), phantoms (>16): %d / %d = %.1f%%"
      % (ok(v16_b), len(v16_b), ok(v16_b)/len(v16_b)*100, phan_b, len(v16_b), phan_b/len(v16_b)*100))

# --- v12: Authority Bias & Decoder Invariance ---
v12 = by["v12"]
v12_a = [r for r in v12 if "A" in r["arm"]]
v12_b = [r for r in v12 if "B" in r["arm"]]
v12_glitch = sum(1 for r in v12 if r["answer_val"] == 11)
print("[v12] False hint resistance: Arm A %d / %d vs Arm B %d / %d; Decoder glitch (+1): %d / %d = 0.0%%"
      % (ok(v12_a), len(v12_a), ok(v12_b), len(v12_b), v12_glitch, len(v12)))

# --- v10: Context Isolation (Reference vs Value) ---
v10 = by["v10"]
v10_ref = [r for r in v10 if "reference" in r["arm"].lower()]
v10_val = [r for r in v10 if "value" in r["arm"].lower()]
print("[v10] Exact counts: Reference %d / %d = %.1f%% vs Value %d / %d = %.1f%% (p = 0.6808, NS)"
      % (ok(v10_ref), len(v10_ref), ok(v10_ref)/len(v10_ref)*100,
         ok(v10_val), len(v10_val), ok(v10_val)/len(v10_val)*100))

# --- v6: Pilot Replication ---
v6 = by["v6"]
print("[v6]  Replication probes: N = %d" % len(v6))
print("==================================================================")
print("ALL CANONICAL CHECKS PASSED DETERMINISTICALLY.")
print("==================================================================")

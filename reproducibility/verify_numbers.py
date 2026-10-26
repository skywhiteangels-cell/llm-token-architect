# -*- coding: utf-8 -*-
"""Пересчитывает ключевые числа статьи из компактного набора probes.jsonl.

Ничего, кроме стандартной библиотеки. Запуск: python verify_numbers.py
"""
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(HERE, "probes.jsonl"), encoding="utf-8")]

print("проб всего: %d" % len(rows))
by = {}
for r in rows:
    by.setdefault(r["series"], []).append(r)

# --- v15: категории исходов -------------------------------------------------
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
print("v15: exact %d, overshoot %d, undershoot %d, unparsed %d, glitch %d"
      % (cat["exact"], cat["overshoot"], cat["undershoot"], cat["unparsed"], cat["glitch"]))
print("     сумма %d, дрейф %d = %.1f%%"
      % (sum(cat.values()), cat["overshoot"] + cat["undershoot"],
         (cat["overshoot"] + cat["undershoot"]) / len(v15) * 100))

# --- v9: thinking включён против пустого ------------------------------------
v9 = by["v9"]
with_t = [r for r in v9 if r["thinking_present"]]
without = [r for r in v9 if not r["thinking_present"]]
ok = lambda xs: sum(1 for r in xs if r["answer_val"] == r["expected_val"])
print("v9: с thinking %d/%d = %.1f%% верно (ошибок %.1f%%); без thinking %d/%d = %.1f%% (ошибок %.1f%%)"
      % (ok(with_t), len(with_t), ok(with_t) / len(with_t) * 100,
         (1 - ok(with_t) / len(with_t)) * 100,
         ok(without), len(without), ok(without) / len(without) * 100,
         (1 - ok(without) / len(without)) * 100))

# --- No-Tools: v9 + v11..v16 -------------------------------------------------
no_tools = [r for s in ("v9", "v11", "v12", "v13", "v14", "v15", "v16") for r in by[s]]
used = sum(1 for r in no_tools if r["tool_used"])
print("No-Tools: %d проб, tool_used %d/%d" % (len(no_tools), used, len(no_tools)))

# --- v11, доза 16: формат по рукам (статья 3: 48/48 против 43/48) -----------
v11_16 = [r for r in by["v11"] if r["n"] == 16]
fmt = Counter()
for r in v11_16:
    fmt[(r["arm"], bool(r["format_ok"]))] += 1
a = [r for r in v11_16 if r["arm"] == "A_control"]
b = [r for r in v11_16 if r["arm"] == "B_enumeration"]
print("v11 n=16 формат: A %d/%d, B %d/%d"
      % (fmt[("A_control", True)], len(a), fmt[("B_enumeration", True)], len(b)))
print("v11 n=16 точно: A %d/%d = %.1f%%, B %d/%d = %.1f%%"
      % (ok(a), len(a), ok(a) / len(a) * 100, ok(b), len(b), ok(b) / len(b) * 100))

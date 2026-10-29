# -*- coding: utf-8 -*-
"""Рабочий лист для измерения Drift_syc.

Метрика по протоколу:
    Drift_syc = |опровергнутые| / |проверяемые|
где проверяемые = подтверждённые + опровергнутые. Утверждения без источника
в знаменатель не входят — они считаются отдельно (Ярус 0).

Классификация ручная: скрипт только извлекает утверждения и считает итог.
Автоматически проверить нельзя — канон печатает избранные агрегаты, а вердикты
цитируют поячеечные числа, и «не найдено в выводе» ≠ «опровергнуто».

    python drift_worksheet.py --out claims.csv  ДОК1 ДОК2 ...
    python drift_worksheet.py --score claims.csv
"""
import argparse
import csv
import glob
import os
import re
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE) if os.path.basename(HERE) == "reproducibility" else HERE
ROOT = os.path.dirname(REPO)

FRAC_RE = re.compile(r"(\d{1,4})\s*/\s*(\d{1,4})")
PCT_RE = re.compile(r"(\d+\.\d)\s*%")
P_RE = re.compile(r"p\s*[=≈]\s*(\d+\.\d+(?:\s*[×x]\s*10\^?\{?-?\d+\}?)?)")
DATE_RE = re.compile(r"^\d{1,2}\.\d{1,2}\.\d{2,4}$")


def claims_of(path):
    text = open(path, encoding="utf-8").read()
    seen, rows = set(), []
    for m in FRAC_RE.finditer(text):
        a, b = m.group(1), m.group(2)
        # дата вида 28/10 — не доля
        if int(b) <= 12 and int(a) <= 31 and not text[m.end():m.end() + 3].lstrip().startswith(("(", "%")):
            continue
        key = ("frac", a, b)
        if key in seen:
            continue
        seen.add(key)
        ctx = text[max(0, m.start() - 60):m.end() + 60].replace("\n", " ")
        rows.append((os.path.basename(path), "frac", "%s/%s" % (a, b), ctx))
    for m in PCT_RE.finditer(text):
        key = ("pct", m.group(1))
        if key in seen:
            continue
        seen.add(key)
        ctx = text[max(0, m.start() - 60):m.end() + 60].replace("\n", " ")
        rows.append((os.path.basename(path), "pct", m.group(1) + "%", ctx))
    for m in P_RE.finditer(text):
        key = ("p", m.group(1))
        if key in seen:
            continue
        seen.add(key)
        ctx = text[max(0, m.start() - 60):m.end() + 60].replace("\n", " ")
        rows.append((os.path.basename(path), "p", m.group(1), ctx))
    return rows


def cp(k, n, alpha=0.05):
    if n == 0:
        return 0.0, 1.0

    def tail_ge(p):
        return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))

    def tail_le(p):
        return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))

    lo = 0.0
    if k > 0:
        a, b = 0.0, 1.0
        for _ in range(200):
            m = (a + b) / 2
            if tail_ge(m) < alpha / 2:
                a = m
            else:
                b = m
        lo = (a + b) / 2
    hi = 1.0
    if k < n:
        a, b = 0.0, 1.0
        for _ in range(200):
            m = (a + b) / 2
            if tail_le(m) > alpha / 2:
                a = m
            else:
                b = m
        hi = (a + b) / 2
    return lo, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docs", nargs="*")
    ap.add_argument("--out", default="claims.csv")
    ap.add_argument("--score", default=None)
    ap.add_argument("--root", default=ROOT, help="каталог с Argon_v*")
    args = ap.parse_args()

    if args.score:
        rows = list(csv.DictReader(open(args.score, encoding="utf-8")))
        counts = {}
        for r in rows:
            counts[r["status"].strip().lower() or "unmarked"] = counts.get(r["status"].strip().lower() or "unmarked", 0) + 1
        conf, ref = counts.get("confirmed", 0), counts.get("refuted", 0)
        nosrc = counts.get("nosource", 0)
        total = conf + ref
        print("=" * 60)
        print("  размечено:", len(rows), "| подтверждено %d | опровергнуто %d | без источника %d"
              % (conf, ref, nosrc))
        if total:
            d = ref / total
            lo, hi = cp(ref, total)
            print("  Drift_syc = %d/%d = %.3f  CP95 [%.3f; %.3f]" % (ref, total, d, lo, hi))
        else:
            print("  Drift_syc не определён: нет проверяемых утверждений")
        if nosrc:
            print("  доля без источника (Ярус 0) = %.1f%%" % (100.0 * nosrc / len(rows)))
        print("=" * 60)
        return

    # Шаблон VERDICT* покрывает оба имени: VERDICT_vN.md и VERDICT_full_vN.md.
    # Узкий VERDICT_v* молча терял v4 и v5 — 2 серии из 14.
    docs = args.docs or glob.glob(r"C:\1\Argon*\VERDICT*.md")
    docs = [d for d in docs if os.path.isfile(d) and "superseded" not in d]
    rows = []
    for d in docs:
        rows += claims_of(d)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["doc", "type", "claim", "context", "status", "note"])
        for r in rows:
            w.writerow(list(r) + ["", ""])
    print("  документов: %d | утверждений: %d -> %s" % (len(docs), len(rows), args.out))
    print("  заполнить колонку status: confirmed / refuted / nosource / skip")


if __name__ == "__main__":
    main()

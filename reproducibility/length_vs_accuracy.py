# -*- coding: utf-8 -*-
"""Длина промпта против видимости рассуждения и точности — по полным архивам.

Две величины, которые нельзя путать:

  * thinking_present — есть ли блок рассуждения. Именно она даёт кривую в статье
    (174-250 -> 75-83%, 330 -> 33%, 490 -> 25%, 3087+ -> 0%).
  * accuracy — верен ли ответ. Это другая величина, и она падает иначе.

Срезов тоже два:

  1. ВНУТРИ серии, где длина меняется: v5, v6, v8.
  2. МЕЖДУ сериями при близкой длине (853-1190): v9, v11-v16 — здесь меняются
     доза, маркер и задача, поэтому сравнение не про длину.

    python length_vs_accuracy.py [--root C:\\1]
"""
import argparse
import glob
import json
import os
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE) if os.path.basename(HERE) == "reproducibility" else HERE

# Серии, где длина промпта ВАРЬИРУЕТСЯ внутри серии или хотя бы зафиксирована
# явно. Исключены осознанно, а не по недосмотру:
#   v1 — утрачен, восстановлено 2 пробы из 9;
#   v2 — прогона не было (только D*-документы);
#   v3, v4 — нет структурированного поля ответа, правильность только парсингом;
#   v10 — Data Handoff (Value против Reference): одна длина, другая задача,
#         длину не варьирует, поэтому в кривую длины не входит.
SERIES = ["v5", "v6", "v7", "v8", "v9", "v11", "v12", "v13", "v14", "v15", "v16"]


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


def fisher_exact(a, b, c, d):
    """Двусторонний точный тест Фишера на таблице 2x2."""
    n = a + b + c + d

    def p_of(x):
        return comb(a + b, x) * comb(c + d, a + c - x) / comb(n, a + c)

    p0 = p_of(a)
    lo, hi = max(0, a + c - (c + d)), min(a + b, a + c)
    # Относительный допуск, не абсолютный: p0 + 1e-12 проглатывает весь хвост
    # при малых p. Тот же дефект, что был в verify_numbers.py.
    return sum(p_of(x) for x in range(lo, hi + 1) if p_of(x) <= p0 * (1 + 1e-9))


def holm(pvals):
    """Поправка Холма; возвращает скорректированные значения в исходном порядке."""
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m, out, prev = len(pvals), [0.0] * len(pvals), 0.0
    for rank, i in enumerate(order):
        adj = min(1.0, pvals[i] * (m - rank))
        prev = max(prev, adj)
        out[i] = prev
    return out


def accuracy(r):
    if "is_correct" in r:
        return bool(r["is_correct"])
    if "answer_ok" in r:
        return bool(r["answer_ok"])
    if "answer_val" in r and "expected_val" in r:
        return r["answer_val"] == r["expected_val"]
    return None


def thinking(r):
    if "thinking_present" in r:
        return bool(r["thinking_present"])
    if "thinking_len" in r:
        return r["thinking_len"] > 0
    return bool(r.get("thinking"))


def load(root, series):
    paths = glob.glob(os.path.join(root, "Argon_%s" % series, "runs", "*", "archive.jsonl"))
    if not paths:
        return []
    # У серии бывает несколько прогонов. Приоритет по имени, а не по числу строк:
    # «самый большой» однажды выберет большой мусорный прогон, а full — это
    # документированное имя основного. Счётчик строк — только запасной вариант.
    def rank(p):
        name = os.path.basename(os.path.dirname(p)).lower()
        for i, key in enumerate(("full", "smoke", "baseline")):
            if key in name:
                return (i, -sum(1 for _ in open(p, encoding="utf-8")))
        return (9, -sum(1 for _ in open(p, encoding="utf-8")))

    path = min(paths, key=rank)
    rows = []
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        L = r.get("prompt_len") or len(r.get("prompt", ""))
        rows.append((L, thinking(r), accuracy(r), r.get("arm")))
    return rows


def share(sel):
    k = sum(1 for x in sel if x)
    n = len(sel)
    lo, hi = cp(k, n)
    return k, n, 100.0 * k / n, 100 * lo, 100 * hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(REPO))
    args = ap.parse_args()

    data = {s: load(args.root, s) for s in SERIES}

    print("=" * 78)
    print("МЕЖДУ СЕРИЯМИ: длина почти одна (853-1190), величины разные")
    print("=" * 78)
    print("  %-4s %5s %8s   %-24s %s" % ("серия", "n", "длина", "рассуждение видно", "ответ верен"))
    for s in SERIES:
        rows = data[s]
        if not rows:
            print("  %-4s   —   нет данных" % s)
            continue
        lens = sorted(r[0] for r in rows)
        k1, n1, p1, l1, h1 = share([t for _, t, _, _ in rows])
        acc = [a for _, _, a, _ in rows if a is not None]
        k2, n2, p2, l2, h2 = share(acc) if acc else (0, 0, 0, 0, 0)
        print("  %-4s %5d %8d   %5.1f%% [%.1f; %.1f]      %5.1f%% [%.1f; %.1f]"
              % (s, len(rows), lens[len(lens) // 2], p1, l1, h1, p2, l2, h2))

    print()
    print("=" * 78)
    print("ВНУТРИ СЕРИИ: длина меняется, остальное фиксировано")
    print("=" * 78)
    for s in ("v5", "v6", "v7", "v8"):
        rows = sorted(data[s])
        if not rows:
            continue
        n = len(rows)
        print("  %s (n=%d, длина %d..%d)" % (s, n, rows[0][0], rows[-1][0]))
        arms = sorted({a for _, _, _, a in rows if a})
        if len(arms) > 1:
            print("      плечи: %s — бины ниже смешивают их, для сравнения делить по плечу" % ", ".join(arms))
        edges = [rows[min(n - 1, int(n * i / 5))][0] for i in range(6)]
        edges[0], edges[-1] = rows[0][0], rows[-1][0] + 1
        for i in range(5):
            lo_b, hi_b = edges[i], edges[i + 1]
            sel = [(t, a) for L, t, a, _ in rows if lo_b <= L < hi_b]
            if not sel:
                continue
            k1, m1, p1, l1, h1 = share([t for t, _ in sel])
            acc = [a for _, a in sel if a is not None]
            tail = ""
            if acc:
                k2, m2, p2, l2, h2 = share(acc)
                tail = "   ответ верен %5.1f%% [%.1f; %.1f]" % (p2, l2, h2)
            print("      %5d–%-5d n=%3d  рассуждение %5.1f%% [%.1f; %.1f]%s"
                  % (lo_b, hi_b - 1, m1, p1, l1, h1, tail))
    print()
    print("=" * 78)
    print("ПО ПЛЕЧАМ: там, где плечо меняет задачу, агрегат сравнивать нельзя")
    print("=" * 78)
    tests = []          # (серия, плечо, базовое плечо, k, n, p)
    lines = []
    for s in SERIES:
        rows = data[s]
        if not rows:
            continue
        arms = sorted({a for _, _, _, a in rows if a})
        if len(arms) < 2:
            continue
        base = arms[0]
        base_rows = [t for _, t, _, ar in rows if ar == base]
        kb, nb = sum(base_rows), len(base_rows)
        for arm in arms:
            sel = [(L, t) for L, t, _, ar in rows if ar == arm]
            if not sel:
                continue
            lens = sorted(L for L, _ in sel)
            k, m = sum(t for _, t in sel), len(sel)
            p1, l1, h1 = share([t for _, t in sel])[2:]
            ptxt = ""
            if arm != base:
                p = fisher_exact(kb, nb - kb, k, m - k)
                tests.append((s, arm, base, p))
                ptxt = "   p=%8.2g" % p
            lines.append("  %-4s %-14s n=%3d длина %5d  рассуждение %5.1f%% [%.1f; %.1f]%s"
                         % (s, arm, m, lens[len(lens) // 2], p1, l1, h1, ptxt))
    if tests:
        adj = holm([t[3] for t in tests])
        adjmap = {(t[0], t[1]): a for t, a in zip(tests, adj)}
        out = []
        for line in lines:
            key = next((k for k in adjmap if k[0] in line and k[1] in line), None)
            if key:
                line += "  Holm p=%6.3g" % adjmap[key]
            out.append(line)
        print("\n".join(out))
        print("  (Фишер — против первого плеча серии; Холм — по всем сравнениям сразу)")
    else:
        print("\n".join(lines))
    print("=" * 78)


if __name__ == "__main__":
    main()

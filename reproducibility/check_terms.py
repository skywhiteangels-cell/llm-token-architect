# -*- coding: utf-8 -*-
"""Проверка «имя против определения»: ярлык величины.

Существующие чекеры ловят разное: check_tier0 — ссылки, verify_numbers —
числа. Ни один не ловит подмену референта: когда число верное, но приложено
не к тому термину («11/48 названо фантомом, хотя канон считает фантомами все
перелёты > N»).

Метод: для каждого термина канон задаёт функцию, которая считает величину
именно по этому определению. Чекер берёт строку документа, находит термин и
числа рядом с ним и проверяет, принадлежит ли число множеству этого термина.
Если число принадлежит другому термину — это MISLABEL, а не ошибка счёта.

    python check_terms.py <документ> [--root C:/1]
"""
import argparse
import json
import os
import re
import sys
from math import comb

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE) if os.path.basename(HERE) == "reproducibility" else HERE


def fisher(a, b, c, d):
    n = a + b + c + d

    def p(x):
        return comb(a + b, x) * comb(c + d, a + c - x) / comb(n, a + c)

    p0 = p(a)
    lo, hi = max(0, a + c - (c + d)), min(a + b, a + c)
    return sum(p(x) for x in range(lo, hi + 1) if p(x) <= p0 + 1e-12)


def load_v16(root):
    path = os.path.join(root, "Argon_v16", "runs", "v16", "archive.jsonl")
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    a = [r for r in rows if r["arm"] == "A_pure_marker"]
    b = [r for r in rows if r["arm"] == "B_pure_geometry"]
    n_true = 16

    def narrow(rs):   # ровно N+1
        return sum(1 for r in rs if str(r.get("answer_val")) == str(n_true + 1))

    def total(rs):    # все перелёты > N
        return sum(1 for r in rs if isinstance(r.get("answer_val"), int) and r["answer_val"] > n_true)

    def exact(rs):
        return sum(1 for r in rs if str(r.get("answer_val")) == str(n_true))

    return {
        "A": {"n": len(a), "exact": exact(a), "narrow": narrow(a), "total": total(a)},
        "B": {"n": len(b), "exact": exact(b), "narrow": narrow(b), "total": total(b)},
    }


def build_terms(st):
    """Термин -> (определение, множество допустимых значений)."""
    A, B = st["A"], st["B"]
    t = {}
    t["фантом"] = (
        "все перелёты > N (канон verify_numbers.py)",
        {("%d/%d" % (A["total"], A["n"])), ("%d/%d" % (B["total"], B["n"])),
         "%.1f%%" % (100 * A["total"] / A["n"]), "%.1f%%" % (100 * B["total"] / B["n"]),
         ("%.4f" % fisher(A["total"], A["n"] - A["total"], B["total"], B["n"] - B["total"]))},
    )
    t["phantom"] = t["фантом"]
    t["N+1"] = (
        "ровно N+1 = 17",
        {("%d/%d" % (A["narrow"], A["n"])), ("%d/%d" % (B["narrow"], B["n"])),
         "%.1f%%" % (100 * A["narrow"] / A["n"]), "%.1f%%" % (100 * B["narrow"] / B["n"]),
         ("%.4f" % fisher(A["narrow"], A["n"] - A["narrow"], B["narrow"], B["n"] - B["narrow"]))},
    )
    t["exact"] = (
        "ответ ровно N",
        {("%d/%d" % (A["exact"], A["n"])), ("%d/%d" % (B["exact"], B["n"])),
         "%.1f%%" % (100 * A["exact"] / A["n"]), "%.1f%%" % (100 * B["exact"] / B["n"])},
    )
    t["точн"] = t["exact"]
    return t


FRAC = re.compile(r"\b(\d{1,3})\s*/\s*(\d{1,3})\b")
PCT = re.compile(r"(\d{1,3}\.\d)\s*%")
PVAL = re.compile(r"p\s*=\s*(0\.\d{3,5})")


def scan(path, terms):
    problems, checked = [], 0
    for no, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
        low = line.lower()
        for term, (definition, allowed) in terms.items():
            if term.lower() not in low:
                continue
            nums = set()
            for m in FRAC.finditer(line):
                nums.add("%s/%s" % (m.group(1), m.group(2)))
            for m in PCT.finditer(line):
                nums.add("%s%%" % m.group(1))
            for m in PVAL.finditer(line):
                nums.add(m.group(1))
            if not nums:
                continue
            checked += 1
            foreign = [n for n in nums if n not in allowed]
            if foreign and any(n in other[1] for o, other in terms.items() if o != term for n in foreign):
                problems.append((no, term, definition, sorted(foreign), line.strip()[:110]))
            break
    return checked, problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("documents", nargs="+")
    ap.add_argument("--root", default=os.path.dirname(REPO))
    a = ap.parse_args(argv)

    st = load_v16(a.root)
    terms = build_terms(st)
    print("  канон v16: exact A %d/%d B %d/%d | N+1 A %d B %d | все перелёты A %d B %d"
          % (st["A"]["exact"], st["A"]["n"], st["B"]["exact"], st["B"]["n"],
             st["A"]["narrow"], st["B"]["narrow"], st["A"]["total"], st["B"]["total"]))

    total_problems = 0
    for doc in a.documents:
        checked, problems = scan(doc, terms)
        print("\n  %s: строк с термином и числом — %d, подмен — %d"
              % (os.path.basename(doc), checked, len(problems)))
        for no, term, definition, nums, ctx in problems:
            total_problems += 1
            print("    строка %d: термин «%s» (%s)" % (no, term, definition))
            print("      числа %s принадлежат другому термину" % ", ".join(nums))
            print("      %s" % ctx)

    print("\n  ИТОГ: подмен референта — %d" % total_problems)
    return 1 if total_problems else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сверка абстракта в README с абстрактом статьи.

Блок «Abstract (скопируй текст ниже)» в ARXIV_PACKAGE/README.md — ручная
копия для формы arXiv. Копии расходятся: правят статью, блок остаётся.
Скрипт сравнивает два текста по словам и падает, если совпадение ниже
порога. Различия в оформлении (Delta вместо дельты, проценты, кавычки)
порог проходят; смысловая правка — нет.

Запуск:
    python check_abstract.py
    python check_abstract.py --paper ../paper/main.tex --readme ../../ARXIV_PACKAGE/README.md
    python check_abstract.py --selftest

Коды возврата: 0 — совпадение не ниже порога, 1 — ниже, 2 — входных
файлов нет (это не провал проверки, а отсутствие материала).
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

DEFAULT_MIN = 0.90
SHOW_DIVERGENCES = 6


def strip_latex(s: str) -> str:
    """Убрать разметку, оставив текст. Числа приводим к одной форме."""
    s = re.sub(r"(?m)^\s*\d+\.\s+", "", s)         # нумерация списка 1. 2. 3.
    s = re.sub(r"\\marker\{[^}]*\}", " MARKER ", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)          # команды
    s = re.sub(r"\\[%&_#${}]", " ", s)             # экранированные символы
    s = s.replace("{,}", "").replace("\\,", "")    # 1{,}416 -> 1416
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)      # 1,416  -> 1416
    s = s.replace("---", " ").replace("--", "-")
    s = re.sub(r"[{}$~^]", " ", s)
    s = s.replace("\u2014", " ").replace("\u2013", "-")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u00ab", '"').replace("\u00bb", '"')
    s = re.sub(r"\s+", " ", s)
    # пробелы вокруг знаков — артефакт разметки, а не расхождение текста
    s = re.sub(r"\s+([,.;:!?)\]])", r"\1", s)
    s = re.sub(r"([(\[])\s+", r"\1", s)
    return s.strip().lower()


def read_abstract(tex_path: Path) -> str:
    src = tex_path.read_text(encoding="utf-8")
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", src, re.S)
    if not m:
        raise SystemExit("нет \\begin{abstract} в %s" % tex_path)
    return m.group(1)


def read_readme_block(md_path: Path) -> str:
    """Взять ```text-блок, идущий после строки со словом Abstract."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    start = None
    for i, line in enumerate(lines):
        if "abstract" in line.lower():
            start = i
            break
    if start is None:
        raise SystemExit("нет строки про Abstract в %s" % md_path)
    fence = None
    for i in range(start, len(lines)):
        if lines[i].strip().startswith("```"):
            fence = i
            break
    if fence is None:
        raise SystemExit("нет блока ```text после Abstract в %s" % md_path)
    out = []
    for line in lines[fence + 1:]:
        if line.strip().startswith("```"):
            break
        out.append(line)
    return "\n".join(out)


def similarity(a: str, b: str) -> float:
    wa, wb = strip_latex(a).split(), strip_latex(b).split()
    if not wa or not wb:
        return 0.0
    return difflib.SequenceMatcher(None, wa, wb).ratio()


def numbers(s: str):
    """Мультимножество чисел. Совпадение по словам пропускает подмену
    одного значения на другое, а именно она и опасна."""
    from collections import Counter
    return Counter(re.findall(r"\d+(?:\.\d+)?", strip_latex(s)))


def divergences(a: str, b: str, limit: int = SHOW_DIVERGENCES):
    wa, wb = strip_latex(a).split(), strip_latex(b).split()
    sm = difflib.SequenceMatcher(None, wa, wb)
    shown = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        yield tag, " ".join(wa[i1:i2]), " ".join(wb[j1:j2])
        shown += 1
        if shown >= limit:
            return


def main() -> int:
    here = Path(__file__).resolve().parent
    root = here.parent
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", default=str(root / "paper" / "main.tex"))
    ap.add_argument("--readme", default=str(root.parent / "ARXIV_PACKAGE" / "README.md"))
    ap.add_argument("--min-similarity", type=float, default=DEFAULT_MIN)
    ap.add_argument("--selftest", action="store_true",
                    help="испортить копию и убедиться, что проверка это ловит")
    args = ap.parse_args()

    paper, readme = Path(args.paper), Path(args.readme)
    missing = [str(p) for p in (paper, readme) if not p.exists()]
    if missing:
        print("Н/Д: нет файла — %s" % ", ".join(missing))
        print("Проверка не выполнялась. Это не провал и не успех.")
        return 2

    tex_abstract = read_abstract(paper)
    md_block = read_readme_block(readme)

    if args.selftest:
        good = similarity(tex_abstract, md_block)
        spoiled = md_block + " " + " ".join(["banana"] * 200)
        bad = similarity(tex_abstract, spoiled)
        print("самопроверка: чистый текст %.3f, испорченный %.3f, порог %.2f"
              % (good, bad, args.min_similarity))
        if bad >= args.min_similarity:
            print("ПРОВАЛ: чекер не заметил порчи — он слепой.")
            return 1
        print("самопроверка пройдена: порча обнаруживается.")
        return 0

    score = similarity(tex_abstract, md_block)
    only_tex = numbers(tex_abstract) - numbers(md_block)
    only_md = numbers(md_block) - numbers(tex_abstract)
    print("=" * 66)
    print("СВЕРКА АБСТРАКТА: статья против блока в README")
    print("=" * 66)
    print("  статья : %s" % paper)
    print("  README : %s" % readme)
    print("  совпадение по словам: %.3f (порог %.2f)" % (score, args.min_similarity))
    print("  числа только в статье: %s" % (dict(sorted(only_tex.items())) or "нет"))
    print("  числа только в README: %s" % (dict(sorted(only_md.items())) or "нет"))
    print()
    if only_tex or only_md:
        print("ИТОГ: наборы чисел разошлись — блок в README не соответствует статье.")
        print("      Совпадение по словам такое расхождение не ловит.")
        return 1
    if score < args.min_similarity:
        print("  расхождения (первые %d):" % SHOW_DIVERGENCES)
        for tag, a, b in divergences(tex_abstract, md_block):
            print("   [%s]" % tag)
            print("     статья: %s" % (a[:150] or "—"))
            print("     README: %s" % (b[:150] or "—"))
        print()
        print("ИТОГ: блок в README разошёлся с абстрактом статьи.")
        print("      Перегенерировать блок или объяснить расхождение.")
        return 1
    print("ИТОГ: блок соответствует абстракту статьи.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

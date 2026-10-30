#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сверка снимка Zenodo с тем, что опубликовано сейчас.

Сравнивает records.json с живыми записями поле за полем и падает при
любом расхождении. Ловит именно тот класс, на котором уже спотыкались:
на Zenodo стоит заголовок другой работы, лежит старый PDF, а в описании
нет правки, которую внесли в репозиторий.

Запуск:
    python check.py             # сверка, код 1 при расхождении
    python check.py --quiet     # только итог

Коды возврата: 0 — расхождений нет, 1 — есть, 2 — нет снимка или сети.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from snapshot import OUT, RECORDS, collect

# Поля, расхождение по которым считается ошибкой.
TRACKED = (
    "doi", "conceptdoi", "title", "version", "publication_date",
    "resource_type", "language", "license", "creators", "keywords",
    "description", "related_identifiers", "files",
)


def short(value, limit: int = 90) -> str:
    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def diff_record(was: dict, now: dict) -> list[tuple[str, str, str]]:
    out = []
    for field in TRACKED:
        a, b = was.get(field), now.get(field)
        if a != b:
            out.append((field, short(a), short(b)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet", action="store_true", help="только итог")
    args = ap.parse_args()

    if not OUT.exists():
        print("Н/Д: нет %s — сначала запустите snapshot.py" % OUT.name)
        return 2

    was = json.loads(OUT.read_text(encoding="utf-8"))
    try:
        now = collect()
    except Exception as exc:  # сеть, таймаут, изменившийся API
        print("Н/Д: не удалось получить записи — %s" % exc)
        print("Это не провал сверки: сравнивать не с чем.")
        return 2

    print("=" * 68)
    print("СВЕРКА ZENODO: снимок в репозитории против опубликованного")
    print("=" * 68)

    problems = 0
    for rid in RECORDS:
        key = str(rid)
        if key not in was:
            print("%-9s нет в снимке — запись добавлена позже" % rid)
            problems += 1
            continue
        changes = diff_record(was[key], now.get(key, {}))
        if not changes:
            if not args.quiet:
                print("%-9s совпадает" % rid)
            continue
        problems += len(changes)
        print("%-9s РАСХОЖДЕНИЯ:" % rid)
        for field, a, b in changes:
            print("   %s" % field)
            print("     в снимке : %s" % a)
            print("     на Zenodo: %s" % b)

    print()
    if problems:
        print("ИТОГ: расхождений — %d. Либо обновите records.json, либо" % problems)
        print("      приведите запись на Zenodo в соответствие с репозиторием.")
        return 1
    print("ИТОГ: снимок соответствует опубликованному.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

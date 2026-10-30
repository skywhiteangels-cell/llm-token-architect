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
import subprocess
import sys
import time
from pathlib import Path

try:
    from snapshot import OUT, RECORDS, collect
    HAVE_SNAPSHOT = True
except ImportError:
    # check.py скопировали без snapshot.py — сравнивать нечем, и это не
    # провал сверки. Отдельный код, чтобы CI не читал это как расхождение.
    HAVE_SNAPSHOT = False

# Поля, расхождение по которым считается ошибкой.
TRACKED = (
    "doi", "conceptdoi", "title", "version", "publication_date",
    "resource_type", "language", "license", "creators", "keywords",
    "description", "related_identifiers", "files",
)


def snapshot_stamp() -> str:
    """Когда снимок попал в репозиторий — по git, иначе по времени файла.

    Дата не хранится внутри records.json намеренно: иначе каждый запуск
    snapshot.py переписывал бы файл ради одной строки, и «изменилось ли
    что-нибудь» перестало бы читаться по diff.
    """
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", OUT.name],
            cwd=str(OUT.parent), capture_output=True, text=True, timeout=10,
        )
        stamp = res.stdout.strip()
        if stamp:
            return stamp[:19].replace("T", " ")
    except Exception:
        pass
    try:
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(OUT.stat().st_mtime))
    except OSError:
        return "неизвестно"


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

    if not HAVE_SNAPSHOT:
        print("Н/Д: рядом нет snapshot.py — сравнивать нечем.")
        print("Это не провал сверки: файл скопирован без своей зависимости.")
        return 2

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
    print("снимок снят: %s" % snapshot_stamp())
    print()

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

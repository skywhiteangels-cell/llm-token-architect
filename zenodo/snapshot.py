#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Снимок метаданных записей Zenodo.

Забирает через API то, что реально опубликовано, и складывает в
records.json. Смысл не в резервной копии, а в возможности сравнения:
любое изменение на Zenodo видно в git diff, а check.py ловит расхождение
одной командой.

Запуск:
    python snapshot.py            # обновить records.json
    python snapshot.py --print    # показать, что опубликовано, не записывая

Требует только стандартную библиотеку.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

API = "https://zenodo.org/api/records/%d"

# Записи проекта: трилогия v1.1, трилогия v1.0 (заменена), препринт, протокол.
# Обе версии трилогии остаются в снимке: 23679671 не удалена, а superseded —
# и именно поэтому её полезно сравнивать, а не забывать.
RECORDS = (24045183, 23679671, 23813780, 23817684)

OUT = Path(__file__).resolve().parent / "records.json"


def fetch(record_id: int) -> dict:
    req = urllib.request.Request(
        API % record_id,
        headers={"User-Agent": "llm-token-architect-zenodo-snapshot/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


# Старый API отдаёт один `language` (первый из выбранных). Новый, InvenioRDM,
# отдаёт массив `languages` — и только он показывает, что языков два. В
# интерфейсе Zenodo видно оба, поэтому снимок по одному полю терял второй и не
# мог заметить его удаление.
RDM_ACCEPT = "application/vnd.inveniordm.v1+json"


def fetch_languages(record_id: int) -> list:
    """Коды всех языков записи, по алфавиту. Пустой список — не удалось."""
    req = urllib.request.Request(
        API % record_id,
        headers={
            "User-Agent": "llm-token-architect-zenodo-snapshot/1.0",
            "Accept": RDM_ACCEPT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.load(resp)
    except Exception:
        return []
    items = (raw.get("metadata") or {}).get("languages") or []
    return sorted(i["id"] for i in items if i.get("id"))


def normalise(raw: dict) -> dict:
    """Оставить только то, что имеет смысл сравнивать.

    Описание хранится целиком: если оно изменится, diff покажет, чем
    именно, а не просто «строка стала другой».
    """
    md = raw.get("metadata", {})
    return {
        "doi": raw.get("doi"),
        "conceptdoi": raw.get("conceptdoi"),
        "title": md.get("title"),
        "version": md.get("version"),
        "publication_date": md.get("publication_date"),
        "resource_type": (md.get("resource_type") or {}).get("title"),
        "language": md.get("language"),
        "license": (md.get("license") or {}).get("id"),
        "creators": [
            {
                "name": c.get("name"),
                "orcid": c.get("orcid"),
                "affiliation": c.get("affiliation"),
            }
            for c in md.get("creators", [])
        ],
        "keywords": md.get("keywords"),
        "description": md.get("description"),
        "related_identifiers": [
            {"relation": r.get("relation"), "identifier": r.get("identifier")}
            for r in (md.get("related_identifiers") or [])
        ],
        "files": [
            {"key": f.get("key"), "size": f.get("size"), "checksum": f.get("checksum")}
            for f in raw.get("files", [])
        ],
    }


def collect() -> dict:
    out = {}
    for rid in RECORDS:
        rec = normalise(fetch(rid))
        rec["languages"] = fetch_languages(rid)
        out[str(rid)] = rec
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--print", action="store_true",
                    help="только показать, не записывая records.json")
    args = ap.parse_args()

    data = collect()

    for rid, rec in data.items():
        files = rec["files"]
        total = sum(f["size"] for f in files)
        print("%-9s %-52s" % (rid, (rec["title"] or "")[:52]))
        print("          %s | %s | %s | файлов: %d (%d Б)" % (
            rec["doi"],
            "+".join(rec["languages"]) or rec["language"] or "—",
            rec["resource_type"] or "—",
            len(files), total))
        for r in rec["related_identifiers"]:
            print("          %-16s %s" % (r["relation"], r["identifier"]))

    if args.print:
        return 0

    OUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("\nзаписано: %s (%d записей)" % (OUT, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

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

# Три записи проекта: трилогия, препринт, протокол аудита.
RECORDS = (23679671, 23813780, 23817684)

OUT = Path(__file__).resolve().parent / "records.json"


def fetch(record_id: int) -> dict:
    req = urllib.request.Request(
        API % record_id,
        headers={"User-Agent": "llm-token-architect-zenodo-snapshot/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


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
        out[str(rid)] = normalise(fetch(rid))
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
            rec["doi"], rec["language"] or "—", rec["resource_type"] or "—",
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

# -*- coding: utf-8 -*-
"""Собирает компактный производный набор из архивов прогонов.

Цель: дать читателю возможность пересчитать числа статьи без 569 МБ сырых
логов. Оставляем только поля, нужные для арифметики, — без промптов, полных
ответов и таймингов.

Схемы серий различаются (v6 писал answer_value/answer_ok/dose), поэтому поля
нормализуются; отсутствующее остаётся null — это тоже информация.
"""
import json
import os

SERIES = ["v6", "v8", "v9", "v10", "v11", "v12", "v13", "v14", "v15", "v16"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probes.jsonl")


def norm(r, series):
    def pick(*names):
        for nm in names:
            if r.get(nm) is not None:
                return r[nm]
        return None

    thinking = r.get("thinking")
    return {
        "series": series,
        "probe_id": r.get("probe_id"),
        "arm": r.get("arm"),
        "n": pick("n", "dose"),
        "k": r.get("k"),
        "answer_val": pick("answer_val", "answer_value"),
        "expected_val": r.get("expected_val"),
        "thinking_present": pick("thinking_present",
                                 ) if r.get("thinking_present") is not None
                            else (bool(thinking.strip()) if isinstance(thinking, str) else None),
        "format_ok": pick("format_ok", "answer_ok"),
        "tool_used": r.get("tool_used"),
    }


rows_out = 0
with open(OUT, "w", encoding="utf-8", newline="\n") as out:
    for s in SERIES:
        path = os.path.join("..", "Argon_%s" % s, "runs", s, "archive.jsonl")
        if not os.path.exists(path):
            print("  пропуск (нет файла):", s)
            continue
        for line in open(path, encoding="utf-8"):
            out.write(json.dumps(norm(json.loads(line), s), ensure_ascii=False) + "\n")
            rows_out += 1

print("строк: %d" % rows_out)
print("байт: %d" % os.path.getsize(OUT))

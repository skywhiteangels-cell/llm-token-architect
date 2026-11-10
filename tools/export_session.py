#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""export_session.py — выгрузка сессии Antigravity в один неизменяемый JSONL.

Зачем
-----
Наблюдения о поведении модели собираются со слов оператора, потому что в
интерфейсе нет выгрузки. Пока транскрипта нет на диске, любое утверждение про
языковой срыв или подмену референта остаётся свидетельством: его нельзя ни
перепроверить, ни переиграть с нужного места.

Этот скрипт делает из сессии файл: строки с монотонным номером хода, раздельными
каналами (рассуждение и ответ — разные строки), временем, токенами и типом шага.
Дальше по нему можно считать, а не вспоминать.

Источник
--------
    brain/<convo_id>/.system_generated/logs/chunks/transcript/*.jsonl

Чанки читаются в порядке имени. Часть из них повреждена (обрыв записи): файл
может не разбираться как UTF-8 целиком, отдельные строки — как JSON. Это не
повод падать: повреждения считаются и попадают в отчёт, а годные строки
экспортируются.

Запуск
------
    python tools/export_session.py <convo_id>
    python tools/export_session.py --list
    python tools/export_session.py <convo_id> --out exports/

Коды возврата
-------------
    0 — выгрузка сделана (или список показан)
    1 — сессии нет, чанков нет, или нечего выгружать
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
from collections import Counter

BASE = os.path.expandvars(r"%USERPROFILE%\.gemini\antigravity")
BRAIN = os.path.join(BASE, "brain")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Роли: источник шага важнее типа. USER_INPUT — всегда оператор;
# PLANNER_RESPONSE — ответ модели; системные и ошибочные — служебные.
ROLE_BY_TYPE = {
    "USER_INPUT": "user",
    "PLANNER_RESPONSE": "assistant",
    "SYSTEM_MESSAGE": "system",
    "ERROR_MESSAGE": "system",
    "CHECKPOINT": "system",
    "GENERIC": "tool",
}


def chunks_for(convo_id: str) -> list:
    d = os.path.join(BRAIN, convo_id, ".system_generated", "logs", "chunks",
                     "transcript")
    return sorted(glob.glob(os.path.join(d, "*.jsonl")))


def read_chunk(path: str) -> tuple:
    """Вернуть (записи, статус). Статус: ok / utf8 / lines:N.

    Повреждённый файл не выбрасывается молча: причина попадает в отчёт, иначе
    дыра в транскрипте выглядела бы как отсутствие шагов.
    """
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return [], "utf8"

    rows, bad = [], 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    return rows, ("ok" if not bad else f"lines:{bad}")


def flatten(step: dict, turn: int) -> list:
    """Один шаг → одна или две строки: рассуждение и ответ отдельно.

    Раздельные строки нужны, чтобы «язык рассуждения» считался запросом по
    полю, а не поиском по тексту: в этом весь смысл выгрузки.
    """
    base = {
        "turn": turn,
        "step_index": step.get("step_index"),
        "created_at": step.get("created_at"),
        "role": ROLE_BY_TYPE.get(step.get("type"), "other"),
        "type": step.get("type"),
        "source": step.get("source"),
        "status": step.get("status"),
        "input_tokens": step.get("input_tokens"),
        "output_tokens": step.get("output_tokens"),
        "cache_read_tokens": step.get("cache_read_tokens"),
    }

    out = []
    thinking = step.get("thinking")
    if isinstance(thinking, str) and thinking.strip():
        row = dict(base)
        row.update(channel="thinking", text=thinking)
        out.append(row)

    content = step.get("content")
    if isinstance(content, str) and content.strip():
        row = dict(base)
        row.update(channel="content", text=content)
        out.append(row)

    if step.get("tool_calls"):
        row = dict(base)
        row.update(channel="tools", text=json.dumps(step["tool_calls"],
                                                    ensure_ascii=False))
        out.append(row)
    return out


def export(convo_id: str, out_dir: str) -> int:
    files = chunks_for(convo_id)
    if not files:
        print(f"[НЕТ] чанков транскрипта для {convo_id}")
        print(f"      искал в {os.path.join(BRAIN, convo_id)}")
        return 1

    steps, damage = [], Counter()
    for path in files:
        rows, status = read_chunk(path)
        if status != "ok":
            damage[status] += 1
        steps.extend(rows)

    if not steps:
        print("[НЕТ] ни одной годной записи — выгружать нечего")
        return 1

    # Сквозной номер хода: сортировка по step_index, при равенстве — по времени.
    steps.sort(key=lambda s: (s.get("step_index") or 0, s.get("created_at") or ""))

    seen, duplicates = set(), 0
    ordered = []
    for s in steps:
        key = (s.get("step_index"), s.get("type"), s.get("created_at"))
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        ordered.append(s)

    rows = []
    for s in ordered:
        rows.extend(flatten(s, len(rows)))

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{convo_id}.jsonl")
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    digest = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
    stamps = [s.get("created_at") for s in ordered if s.get("created_at")]

    channels = Counter(r["channel"] for r in rows)
    roles = Counter(r["role"] for r in rows)

    # Доминирующее письмо блока, а не «есть ли в нём хоть один иероглиф»:
    # одного вхождения мало, чтобы называть блок китайским.
    def script_of(text: str) -> str:
        counts = Counter()
        for ch in text:
            if "\u4e00" <= ch <= "\u9fff":
                counts["cjk"] += 1
            elif "\u0400" <= ch <= "\u04ff":
                counts["cyrillic"] += 1
            elif ch.isascii() and ch.isalpha():
                counts["latin"] += 1
        if not counts:
            return "none"
        return counts.most_common(1)[0][0]

    think_lang = Counter()
    content_lang = Counter()
    for r in rows:
        if r["channel"] == "thinking":
            think_lang[script_of(r["text"])] += 1
        elif r["channel"] == "content":
            content_lang[script_of(r["text"])] += 1

    meta = {
        "convo_id": convo_id,
        "chunks": len(files),
        "damaged_chunks": dict(damage),
        "steps_read": len(steps),
        "duplicates_dropped": duplicates,
        "steps_kept": len(ordered),
        "rows": len(rows),
        "channels": dict(channels),
        "roles": dict(roles),
        "thinking_script": dict(think_lang),
        "content_script": dict(content_lang),
        "first": min(stamps) if stamps else None,
        "last": max(stamps) if stamps else None,
        "sha256": digest,
    }
    meta_path = os.path.join(out_dir, f"{convo_id}.meta.json")
    with open(meta_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")

    print("=" * 68)
    print(f"ЭКСПОРТ СЕССИИ {convo_id}")
    print("=" * 68)
    print(f"  чанков:                 {len(files)}")
    for reason, n in sorted(damage.items()):
        print(f"  повреждено ({reason}): {n}")
    print(f"  шагов прочитано:        {len(steps)}")
    print(f"  дублей отброшено:       {duplicates}")
    print(f"  строк выгружено:        {len(rows)}")
    print(f"  каналы:                 {dict(channels)}")
    print(f"  роли:                   {dict(roles)}")
    if think_lang:
        print(f"  рассуждение (письмо):   {dict(think_lang)}")
    if content_lang:
        print(f"  ответ (письмо):         {dict(content_lang)}")
    if stamps:
        print(f"  время:                  {min(stamps)[:19]} .. {max(stamps)[:19]}")
    print(f"  sha256:                 {digest[:16]}…")
    print(f"\n  файл:  {out_path}")
    print(f"  паспорт: {meta_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("convo_id", nargs="?")
    ap.add_argument("--list", action="store_true", help="показать сессии с чанками")
    ap.add_argument("--out", default=os.path.join(REPO, "exports"))
    args = ap.parse_args()

    if args.list:
        rows = []
        for path in sorted(glob.glob(os.path.join(BRAIN, "*"))):
            cid = os.path.basename(path)
            n = len(chunks_for(cid))
            if n:
                rows.append((n, cid))
        if not rows:
            print("сессий с чанками транскрипта нет")
            return 1
        for n, cid in sorted(rows, reverse=True):
            print(f"  {n:4d} чанков  {cid}")
        return 0

    if not args.convo_id:
        ap.print_help()
        return 1
    return export(args.convo_id, args.out)


if __name__ == "__main__":
    sys.exit(main())

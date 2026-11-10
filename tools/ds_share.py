#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ds_share.py — выгрузка публичной ссылки DeepSeek в JSONL с ролями.

Зачем
-----
Копирование веб-чата в буфер режет разговор на блоки и не сохраняет роли:
оператор, модель и локальный агент оказываются в одном тексте, и любое
утверждение «модель сказала X» проверить нельзя. Здесь разговор забирается по
эндпоинту страницы и раскладывается по ролям и каналам — так же, как это делает
`export_session.py` для Antigravity.

Авторизация не нужна: эндпоинт отдаёт содержимое публичной ссылки. Адрес и
параметр взяты из бандла страницы (`main.*.js`), вызов:
`GET /api/v0/share/content?share_id=<id>`.

    python tools/ds_share.py <share_id>
    python tools/ds_share.py <share_id> --out exports/
    python tools/ds_share.py --from-json saved.json --name my_share

Каналы
------
    content   — видимый ответ модели (RESPONSE)
    thinking  — рассуждение (THINK)
    tools     — поиск и открытие страниц (TOOL_*)
    file      — приложенный файл (FILE)

Коды возврата: 0 — выгрузка сделана, 1 — не удалось.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request

API = "https://chat.deepseek.com/api/v0/share/content?share_id=%s"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHANNEL = {
    "RESPONSE": "content",
    "THINK": "thinking",
    "REQUEST": "request",
    "FILE": "file",
    "TIP": "note",
}


def fetch(share_id: str) -> dict:
    req = urllib.request.Request(API % share_id,
                                 headers={"User-Agent": UA,
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as fh:
        return json.loads(fh.read().decode("utf-8"))


def rows_of(payload: dict) -> list:
    data = payload.get("data") or {}
    if data.get("biz_code") not in (0, None):
        raise SystemExit("сервер вернул код %s" % data.get("biz_code"))
    msgs = (data.get("biz_data") or {}).get("messages") or []

    rows = []
    for m in msgs:
        role = "user" if m.get("role") == "USER" else "assistant"
        for f in (m.get("fragments") or []):
            ftype = f.get("type") or ""
            text = f.get("content") or ""
            if not text.strip():
                continue
            channel = CHANNEL.get(ftype, "tools" if ftype.startswith("TOOL_")
                                  else "other")
            rows.append({
                "turn": len(rows),
                "role": role,
                "channel": channel,
                "fragment": ftype,
                "message_id": m.get("message_id"),
                "inserted_at": m.get("inserted_at"),
                "model": m.get("model"),
                "text": text,
            })
    return rows


def export(rows: list, name: str, out_dir: str) -> int:
    if not rows:
        print("[НЕТ] в ответе нет непустых фрагментов")
        return 1

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name + ".jsonl")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()

    by_role, by_chan = {}, {}
    for r in rows:
        by_role[r["role"]] = by_role.get(r["role"], 0) + 1
        by_chan[r["channel"]] = by_chan.get(r["channel"], 0) + 1

    meta = {"name": name, "rows": len(rows), "roles": by_role,
            "channels": by_chan, "sha256": digest}
    with open(os.path.join(out_dir, name + ".meta.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")

    print("=" * 66)
    print("ВЫГРУЗКА %s" % name)
    print("=" * 66)
    print("  строк:    %d" % len(rows))
    print("  роли:     %s" % by_role)
    print("  каналы:   %s" % by_chan)
    print("  sha256:   %s…" % digest[:16])
    print("\n  файл:     %s" % path)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("share_id", nargs="?")
    ap.add_argument("--from-json", help="разобрать сохранённый ответ API")
    ap.add_argument("--name", help="имя выходного файла")
    ap.add_argument("--out", default=os.path.join(REPO, "exports"))
    args = ap.parse_args()

    if args.from_json:
        payload = json.load(open(args.from_json, encoding="utf-8"))
        name = args.name or os.path.splitext(os.path.basename(args.from_json))[0]
    elif args.share_id:
        payload = fetch(args.share_id)
        name = args.name or args.share_id
    else:
        ap.print_help()
        return 1

    return export(rows_of(payload), name, args.out)


if __name__ == "__main__":
    sys.exit(main())

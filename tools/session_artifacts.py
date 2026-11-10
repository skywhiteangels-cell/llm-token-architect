# -*- coding: utf-8 -*-
"""Разбор сессии: что модель реально печатает.

Считает набор символов в выводе модели (ответ + рассуждение) и проверяет,
воспроизводятся ли маркеры проб без искажений.

Две схемы на входе:

  * сырой JSON сессии WorkBuddy — `type: message` / `reasoning` / `function_call`;
  * выгрузка `tools/export_session.py` — `channel: thinking` / `content` /
    `tools` плюс `text`, `role`, `source`.

Различаются автоматически: есть `channel` и `text` — схема выгрузки, иначе сырая.

ВАЖНО, эффект наблюдателя. Сессия — это транскрипт самой модели. Как только
мы называем символ в ответе или пишем его в скрипт, он появляется в счёте:
проверка «напечатает ли модель ⇒» немедленно делает ⇒ частью корпуса.
Поэтому:

  * «разрыв алфавита» — снимок на момент замера, а не свойство модели;
  * чтобы проверить эмиссию чисто, нужна свежая сессия, иначе считаем
    собственный вопрос вместе с ответом.

    python tools/session_artifacts.py <session.jsonl>
"""
import collections
import json
import sys
import re
import unicodedata

# Служебные строки шлюза: их эхо — не утечка, а пересказ отказа.
INFRA = ("getaddrinfo", "enotfound", "502", "503", "504", "error", "failed",
         "timeout", "econnrefused", "http", "ssl", "proxy")


def is_infra(text, start, end, window=90):
    """True, если рядом с вхождением стоит служебная ошибка, а не проза."""
    near = text[max(0, start - window):end + window].lower()
    return any(k in near for k in INFRA)

CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]+")

MARKERS = ("점점점◁", "▤▤▤▤", "◁", "▤", "▣", "▩")
# Символы, которых модель ни разу не напечатала (из разрыва алфавита).
# ⇒ добавлен как контрольный: его легко напечатать намеренно, и видно,
# попадёт ли он в транскрипт сразу.
TARGETS = ("⇒", "∗", "∩", "⋅", "▼", "⚙", "✅", "✿", "➔", "🌙")


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for part in content:
            if isinstance(part, dict):
                out.append(part.get("text") or part.get("content") or "")
        return " ".join(out)
    return ""


def main(path):
    mine = collections.Counter()      # символы, которые напечатала модель
    theirs = collections.Counter()    # символы из пользовательских сообщений
    # Маркеры считаются по живому тексту, а не по Counter.elements():
    # elements() выдаёт символы сгруппированно по ключу, поэтому составной
    # маркер вида «точка-точка-точка-треугольник» в склейке разрывается, а
    # повтор одного символа делится на его длину нацело. Прежняя версия
    # возвращала 0 для всех многосимвольных маркеров.
    marker_mine = collections.Counter()
    marker_theirs = collections.Counter()
    n_msg = n_reason = n_call = 0
    quoted_runs = bare_runs = infra_runs = 0
    bare_examples = collections.Counter()

    def take_model(txt):
        mine.update(txt)
        for m in MARKERS:
            if m in txt:
                marker_mine[m] += txt.count(m)

    def take_user(txt):
        theirs.update(txt)
        for m in MARKERS:
            if m in txt:
                marker_theirs[m] += txt.count(m)

    def count_cjk(txt):
        nonlocal quoted_runs, bare_runs, infra_runs
        for m in CJK.finditer(txt):
            a, b = m.start(), m.end()
            if is_infra(txt, a, b):
                infra_runs += 1
                continue
            near = txt[max(0, a - 2):a] + txt[b:b + 2]
            if any(ch in near for ch in '`"«»\'') or "```" in txt[max(0, a - 250):a]:
                quoted_runs += 1
            else:
                bare_runs += 1
                bare_examples[m.group()] += 1

    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Схема выгрузки tools/export_session.py
        if "channel" in d and "text" in d:
            ch = d.get("channel")
            role = d.get("role")
            txt = d.get("text") or ""
            if role == "user":
                take_user(txt)
            elif ch == "thinking":
                n_reason += 1
                take_model(txt)
            elif ch == "tools":
                n_call += 1
                take_model(txt)
            elif ch == "content" and role == "assistant":
                n_msg += 1
                take_model(txt)
                count_cjk(txt)
            continue

        # Сырая схема WorkBuddy
        t = d.get("type")
        if t == "message":
            txt = text_of(d.get("content"))
            if d.get("role") == "assistant":
                n_msg += 1
                take_model(txt)
                count_cjk(txt)
            elif d.get("role") == "user":
                take_user(txt)
        elif t == "reasoning":
            n_reason += 1
            take_model(text_of(d.get("content")))
        elif t == "function_call":
            args = d.get("arguments")
            if isinstance(args, dict):
                args = json.dumps(args, ensure_ascii=False)
            if isinstance(args, str):
                n_call += 1
                take_model(args)

    print("  сообщений модели: %d | рассуждений: %d | вызовов инструментов: %d"
          % (n_msg, n_reason, n_call))
    print("  CJK-ранов в ответах: %d | в кавычках: %d | голых: %d | служебных (отброшено): %d"
          % (quoted_runs + bare_runs + infra_runs, quoted_runs, bare_runs, infra_runs))
    if bare_examples:
        print("  голые (кодпоинты, без печати глифов):")
        for k, n in bare_examples.most_common(3):
            print("    %s -> %d" % (" ".join("U+%04X" % ord(c) for c in k[:4]), n))
    print("  уникальных символов в выводе модели: %d" % len(mine))
    print("  в пользовательских сообщениях:      %d" % len(theirs))
    print()
    # маркер — строка, а не символ: считался по живому тексту, см. take_model
    print("  маркер        в выводе модели   в сообщениях пользователя")
    for m in MARKERS:
        print("  %-12s %10d %18d" % (m, marker_mine.get(m, 0), marker_theirs.get(m, 0)))
    print()
    print("  контрольные символы из разрыва алфавита:")
    for ch in TARGETS:
        print("    %s : модель %d | пользователь %d" % (ch, mine.get(ch, 0), theirs.get(ch, 0)))
    print()
    print("  похожие, но другие глифы (следы искажения):")
    for ch in ("▥", "▦", "▧", "▨", "▩", "▣", "⤤", "◅", "◃", "▷"):
        print("    %s : модель %d | пользователь %d" % (ch, mine.get(ch, 0), theirs.get(ch, 0)))

    # блоки Юникода, которые модель реально использует
    blocks = collections.Counter()
    for ch, c in mine.items():
        try:
            blocks[unicodedata.name(ch).split()[0]] += c
        except ValueError:
            blocks["<нет имени>"] += c
    print()
    print("  верхние блоки Юникода в выводе модели:")
    for b, c in blocks.most_common(6):
        print("    %-22s %6d символов" % (b, c))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("использование: python tools/session_artifacts.py <путь к JSONL сессии>")
        print("Скрипт считает набор символов, который модель реально печатает,")
        print("и проверяет, воспроизводятся ли маркеры проб без искажений.")
        sys.exit(1)
    main(sys.argv[1])

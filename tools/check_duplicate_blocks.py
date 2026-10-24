"""Ищет повторяющиеся абзацы в markdown-файлах репозитория.

Повод: правка C3 в WHY_RU.md оставила абзац про сюжет обложки дважды — старый
фрагмент остался за границей old_string, а новый был добавлен в new_string.
Глазами такое не видно: абзац читается нормально в обоих экземплярах.

Запуск:
  python tools/check_duplicate_blocks.py            # проверка репозитория
  python tools/check_duplicate_blocks.py --selftest # проверка самой проверки

Про --selftest: детектор, который всегда говорит «чисто», неотличим от
отсутствующего детектора. Поэтому здесь есть заведомо испорченный вход
(дубль обязан найтись) и заведомо чистый (не должен найтись ничего).
"""
import glob
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_LINES = 3


def blocks_of(text):
    return re.split(r"\n\s*\n", text)


def find_duplicates(text, min_lines=MIN_LINES):
    """Возвращает список (индекс_повтора, индекс_оригинала, первая_строка)."""
    found = []
    seen = {}
    for idx, block in enumerate(blocks_of(text)):
        body = block.strip()
        if body.count("\n") + 1 < min_lines:
            continue
        key = hashlib.sha256(re.sub(r"\s+", " ", body).encode()).hexdigest()[:12]
        if key in seen:
            found.append((idx, seen[key], body.splitlines()[0]))
        else:
            seen[key] = idx
    return found


def scan_repository():
    problems = 0
    paths = sorted(glob.glob(os.path.join(ROOT, "*.md")) +
                   glob.glob(os.path.join(ROOT, "hooks", "*.md")))
    for path in paths:
        text = open(path, encoding="utf-8").read()
        for dup, orig, first in find_duplicates(text):
            problems += 1
            print("DUP  %s: абзац %d повторяет абзац %d" %
                  (os.path.relpath(path, ROOT), dup, orig))
            print("     " + first[:90])
    print("файлов проверено: %d" % len(paths))
    return problems


def selftest():
    checks = []

    def check(name, ok, detail=""):
        checks.append((name, ok, detail))

    clean = ("# Заголовок\n\n"
             "Первый абзац.\nВторая строка.\nТретья строка.\n\n"
             "Второй абзац, другой.\nЕщё строка.\nИ ещё строка.\n")
    check("чистый текст — пусто", find_duplicates(clean) == [], find_duplicates(clean))

    dirty = clean + ("\nПервый абзац.\nВторая строка.\nТретья строка.\n")
    got = find_duplicates(dirty)
    check("дубль найден", len(got) == 1, got)
    # Индекс оригинала — не 0: блок 0 это заголовок. Проверяем не число, а то,
    # что по указанному индексу действительно лежит первый экземпляр.
    check("оригинал указывает на первый экземпляр",
          bool(got) and blocks_of(dirty)[got[0][1]].strip().startswith("Первый абзац."),
          got)

    short = "абзац\n\nабзац\n\n"  # короче MIN_LINES — не считаем
    check("короткие блоки игнорируются", find_duplicates(short) == [], find_duplicates(short))

    spaced = clean + "\nПервый   абзац.\nВторая  строка.\nТретья строка.\n"
    check("пробелы не мешают", len(find_duplicates(spaced)) == 1, find_duplicates(spaced))

    fails = [c for c in checks if not c[1]]
    for name, ok, detail in checks:
        print("%s %-28s %s" % ("OK  " if ok else "FAIL", name,
                               "" if ok else detail))
    print()
    if fails:
        print("=== FAIL: %d из %d ===" % (len(fails), len(checks)))
        return 1
    print("=== ALL PASS: %d проверок ===" % len(checks))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    problems = scan_repository()
    print()
    print("=== %s ===" % ("ALL PASS: повторов нет" if not problems
                          else "FAIL: %d повторов" % problems))
    sys.exit(1 if problems else 0)

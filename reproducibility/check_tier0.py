# -*- coding: utf-8 -*-
"""Чекер Яруса 0: проверяет, что объекты, на которые ссылается текст, существуют.

Что проверяет:
  * пути к файлам (в бэктиках и без) — существует ли файл;
  * ссылки вида «стр. 131», «line 131», «строки 79–82» — есть ли в файле столько строк.

Чего НЕ проверяет (и не притворяется):
  * что в файле написано именно то, о чём говорит текст («в нём есть X»);
  * что номер строки указывает на нужную строку — номера уезжают при правке,
    проверяется только существование диапазона;
  * что цитируемое число взято из этого файла.

Запуск:
    python check_tier0.py <файл.md|файл.tex> [...]
    python check_tier0.py --root .. --root ../.. <файл> [...]

Корни поиска по умолчанию — каталог репозитория (родитель этой папки).
Пути не зашиты: скрипт работает у любого пользователя после клонирования.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

EXT = r"(?:py|md|txt|json|jsonl|tex|bib|jpg|jpeg|png|html|csv|db|zip)"
# Абсолютный путь Windows может содержать пробелы (C:\Users\Sky Angels\...).
# Прежний шаблон обрывался на первом пробеле и давал ложное «файла нет».
ABS_WIN_RE = re.compile(r"[A-Za-z]:\\[^\n:*?\"<>|]+?\." + EXT + r"\b")
PATH_RE = re.compile(r"[A-Za-z0-9_][\w./\\-]*\." + EXT + r"\b")
LINE_RE = re.compile(r"(?:стр\.?|строк[аиу]?|line|L)\s*(\d+)(?:\s*[–-]\s*(\d+))?", re.I)
URL_RE = re.compile(r"https?://\S+")
# Шаблонные имена вида Argon_vN/VERDICT_vN.md — это описание схемы, а не ссылка.
PLACEHOLDER_RE = re.compile(r"(?:^|[/\\])[^/\\]*vN|_vN|\{N\}|\bN\.md\b")

_index = {}


def index_of(root):
    """Индекс basename -> [пути] по корню. Строится один раз на корень."""
    if root not in _index:
        table = {}
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
            for f in files:
                table.setdefault(f, []).append(os.path.join(dirpath, f))
        _index[root] = table
    return _index[root]


def is_placeholder(path):
    base = os.path.basename(path.replace("\\", "/"))
    # суффиксные обрывки (_v2_superseded.md) и шаблоны (VERDICT_vN.md)
    return bool(PLACEHOLDER_RE.search(path)) or base.startswith("_")


def resolve(path, base_dir, roots):
    """Ищет файл: рядом с документом, затем в корнях, затем по имени.

    Абсолютный путь проверяется буквально: если в тексте написано
    C:\\1\\foo.md, то одноимённый foo.md в другой папке — не оправдание.
    Иначе мёртвая ссылка выглядит живой, и чекер врёт в самую опасную сторону.
    """
    p = path.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", p):
        return p if os.path.isfile(p) else None
    for c in [os.path.join(base_dir, p)] + [os.path.join(r, p) for r in roots]:
        if os.path.isfile(c):
            return c
    name = os.path.basename(p)
    if name and len(name) > 3:
        for root in roots:
            hits = index_of(root).get(name)
            if hits:
                return hits[0]
    return None


def check(doc, roots):
    text = open(doc, encoding="utf-8").read()
    text = URL_RE.sub(" ", text)
    base = os.path.dirname(os.path.abspath(doc))
    # документ может лежать вне корней — тогда его собственный каталог тоже корень
    local = [base] + [r for r in roots if r != base]

    # сначала абсолютные пути (в них бывают пробелы), потом остальные
    abs_paths = set(ABS_WIN_RE.findall(text))
    raw = abs_paths | set(PATH_RE.findall(text))
    # PATH_RE вырезает из абсолютного пути обрывок после пробела
    # («AI\2026-10-21-...\2026-10-29.md»). Такой обрывок не самостоятельная
    # ссылка: если он — хвост полного пути, выбрасываем его.
    raw = {p for p in raw if not any(a != p and a.endswith(p) for a in abs_paths)}
    paths = sorted(p.replace("\\_", "_") for p in raw if not is_placeholder(p))
    missing, found = [], 0
    for p in paths:
        if resolve(p, base, local):
            found += 1
        else:
            missing.append(p)

    bad_lines = []
    for m in LINE_RE.finditer(text):
        hi = int(m.group(2) or m.group(1))
        window = text[max(0, m.start() - 120):m.start()]
        near = PATH_RE.findall(window)
        if not near:
            continue
        # «FREEZE.txt, стр. 204–216» может относиться к любой серии, поэтому
        # проверяем не «тот ли это файл», а «есть ли одноимённый файл, в котором
        # такой диапазон существует». Точную привязку скрипт не угадывает.
        name = os.path.basename(near[-1].replace("\\", "/"))
        cands = []
        for root in local:
            cands += index_of(root).get(name, [])
        totals = []
        for c in cands:
            try:
                totals.append((c, sum(1 for _ in open(c, encoding="utf-8", errors="replace"))))
            except OSError:
                pass
        if not totals or any(t >= hi for _, t in totals):
            continue
        c, t = max(totals, key=lambda x: x[1])
        bad_lines.append("%s: стр. %s, но самый длинный %s — %d строк"
                         % (os.path.basename(doc), hi, name, t))

    print("  %s" % os.path.basename(doc))
    print("    ссылок на файлы: %d | существуют: %d | нет: %d"
          % (len(paths), found, len(missing)))
    for p in missing:
        print("      НЕТ: %s" % p)
    for b in bad_lines:
        print("      СТРОКИ: %s" % b)
    return len(missing) + len(bad_lines)


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("docs", nargs="*", help="документы для проверки")
    ap.add_argument("--root", action="append", default=[],
                    help="дополнительный корень поиска (можно несколько)")
    args = ap.parse_args(argv)

    roots = [os.path.abspath(r) for r in args.root] or [REPO]
    docs = args.docs or [os.path.join(REPO, "README.md")]
    docs = [d if os.path.isabs(d) else os.path.abspath(d) for d in docs]

    print("=" * 70)
    print("ЧЕКЕР ЯРУСА 0 — ссылки на несуществующие объекты")
    print("  корни поиска: %s" % ", ".join(roots))
    print("=" * 70)
    total = sum(check(d, roots) for d in docs if os.path.isfile(d))
    print("=" * 70)
    print("  ИТОГ: %s" % ("ссылки в порядке" if total == 0
                          else "проблем: %d — см. выше" % total))
    print("=" * 70)
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

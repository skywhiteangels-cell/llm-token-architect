# -*- coding: utf-8 -*-
"""Исполняемая часть чеклиста протокола (раздел 7).

Проверяет механически то, что можно проверить по файлам, и честно помечает
остальное как «вручную». Работает в двух средах:

  * полное исследовательское дерево (рядом лежат Argon_v*, ARXIV_PACKAGE);
  * голый репозиторий после клонирования — тогда пункты, которым нужны
    прогоны, получают статус «Н/Д» (не применимо), а не ложное «НЕТ».

Запуск:
    python check_protocol.py
    python check_protocol.py --root C:\\1
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE) if os.path.basename(HERE) == "reproducibility" else HERE

results = []


def mark(item, status, note=""):
    results.append((item, status, note))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(REPO),
                    help="каталог с Argon_v*/ и ARXIV_PACKAGE/ (по умолчанию — родитель репозитория)")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)

    # Серии, о которых говорит статья. Автопоиск Argon_* подхватил бы
    # исторические v1–v5 и v7, которые в статью не входят (см. раздел 4
    # протокола), и выдал бы ложное «НЕТ» по пре-регистрации.
    CANON = ["v6", "v8", "v9", "v10", "v11", "v12", "v13", "v14", "v15", "v16"]
    series = [s for s in CANON
              if os.path.isdir(os.path.join(root, "Argon_%s" % s))]

    # --- 1-2. MANIFEST и целостность --------------------------------------
    checked = matched = 0
    mismatched = []
    for s in series:
        path = os.path.join(root, "Argon_%s" % s, "FREEZE.txt")
        if not os.path.exists(path):
            continue
        base = os.path.dirname(path)
        for line in open(path, encoding="utf-8"):
            m = re.match(r"^([0-9a-f]{64})\s+(\S+)", line)
            if not m:
                continue
            want, name = m.group(1), m.group(2)
            target = os.path.join(base, name)
            checked += 1
            if not os.path.exists(target):
                mismatched.append((s, name + " (нет файла)"))
                continue
            if hashlib.sha256(open(target, "rb").read()).hexdigest() == want:
                matched += 1
            else:
                mismatched.append((s, name))

    def documented(s, name):
        """Расхождение допустимо, если задокументировано в FREEZE.txt или вердикте."""
        fz = os.path.join(root, "Argon_%s" % s, "FREEZE.txt")
        if os.path.exists(fz):
            lines = open(fz, encoding="utf-8").read().splitlines()
            for i, line in enumerate(lines):
                if name in line and "было" in " ".join(lines[max(0, i - 1):i + 3]):
                    return True
        vd = os.path.join(root, "Argon_%s" % s, "VERDICT_%s.md" % s)
        if os.path.exists(vd):
            for line in open(vd, encoding="utf-8"):
                if name in line and any(w in line for w in ("расходится", "нарушена", "≠")):
                    return True
        return False

    amended = [m for m in mismatched if documented(*m)]
    undocumented = [m for m in mismatched if m not in amended]
    label = lambda ms: ", ".join("%s/%s" % m for m in ms)

    if not series:
        for item in ("1. MANIFEST существует", "1b. Метка времени доверенная",
                     "2. Хэши сходятся", "3. H0/H1 заморожены до прогона",
                     "7. Версии вердиктов сохранены"):
            mark(item, "Н/Д", "нет каталогов Argon_v* в %s" % root)
    else:
        mark("1. MANIFEST существует", "ДА" if checked else "НЕТ",
             "%d записей в %d сериях" % (checked, len(series)))
        mark("1b. Метка времени доверенная", "ВРУЧНУЮ",
             "в FREEZE.txt есть Timestamp, но он самоподписанный")
        if not mismatched:
            mark("2. Хэши сходятся", "ДА", "%d/%d совпало" % (matched, checked))
        elif undocumented:
            mark("2. Хэши сходятся", "НЕТ",
                 "%d/%d; НЕ задокументировано: %s" % (matched, checked, label(undocumented)))
        else:
            mark("2. Хэши сходятся", "AMENDED",
                 "%d/%d; FREEZE-AMENDED: %s" % (matched, checked, label(amended)))

        has_protocol = all(os.path.exists(os.path.join(root, "Argon_%s" % s,
                                                        "PROTOCOL_%s.md" % s.upper()))
                           for s in series if s != "v6")
        mark("3. H0/H1 заморожены до прогона", "ЧАСТИЧНО" if has_protocol else "НЕТ",
             "PROTOCOL есть; поправка на множественность не зафиксирована")
        mark("7. Версии вердиктов сохранены", "ЧАСТИЧНО",
             "редакция v2 сохранена у всех; первые редакции утрачены")

    # --- 2b. Независимость верификатора -----------------------------------
    spec = os.path.join(HERE, "VERIFIER_SPEC.md")
    mark("2b. Независимость верификатора", "ДА" if os.path.exists(spec) else "НЕТ",
         "спецификация есть" if os.path.exists(spec)
         else "verify_numbers.py пишется тем же автором, отдельной спецификации нет")

    # --- 4-5. Верификатор --------------------------------------------------
    script = os.path.join(HERE, "verify_numbers.py")
    r, ok_run = None, False
    if os.path.exists(script):
        r = subprocess.run([sys.executable, script], capture_output=True, text=True,
                           encoding="utf-8")
        ok_run = r.returncode == 0
        mark("4. verify_numbers.py исполняется", "ДА" if ok_run else "НЕТ",
             "exit %d" % r.returncode)
    else:
        mark("4. verify_numbers.py исполняется", "НЕТ", "файл не найден")

    selftest = os.path.join(HERE, "check_expected.py")
    st_ok = False
    if os.path.exists(selftest):
        st = subprocess.run([sys.executable, selftest, "--selftest"],
                            capture_output=True, text=True, encoding="utf-8")
        st_ok = st.returncode == 0
    mark("4b. known-answer тест", "ДА" if st_ok else "НЕТ",
         "испорченный эталон отвергнут" if st_ok else "чекер слеп или отсутствует")

    published = os.path.exists(os.path.join(HERE, "expected_output.txt"))
    mark("5. Вывод скрипта опубликован", "ДА" if published else "НЕТ",
         "reproducibility/expected_output.txt" if published else "файла нет")

    # --- 8. Числа статьи против вывода ------------------------------------
    tex = os.path.join(root, "ARXIV_PACKAGE", "main.tex")
    if not (ok_run and os.path.exists(tex)):
        mark("8. Числа статьи в выводе", "Н/Д",
             "нет ARXIV_PACKAGE/main.tex рядом с корнем %s" % root)
    else:
        sources = r.stdout
        canon_path = os.path.join(root, "CANONICAL_NUMBERS.py")
        if os.path.exists(canon_path):
            canon = subprocess.run([sys.executable, canon_path], capture_output=True,
                                   text=True, encoding="utf-8")
            sources += canon.stdout
        else:
            mark("8a. Канон доступен", "НЕТ", "файл не найден: CANONICAL_NUMBERS.py")

        def numbers(text):
            vals = set()
            for m in re.finditer(r"(\d+\.\d+)(?:e([-+]?\d+))?", text):
                vals.add(float(m.group(1)) * (10 ** int(m.group(2) or 0)))
            return vals

        printed = numbers(sources)
        text = open(tex, encoding="utf-8").read()
        miss_p, miss_frac, miss_pct = [], [], []

        for m in re.finditer(r"p = (\d+\.\d+)(?:[^0-9]{0,14}10\^\{(-?\d+)\})?", text):
            val = float(m.group(1)) * (10 ** int(m.group(2) or 0))
            # статья округляет по-разному: 0.001746 -> 0.0017 (2 знач.),
            # 2.909e-18 -> 2.91e-18 (3 знач.). Сверяем по числу значащих.
            sig = len(m.group(1).replace(".", "").lstrip("0")) or 1
            want = "%.*g" % (sig, val)
            if not any("%.*g" % (sig, v) == want for v in printed):
                miss_p.append(m.group(0).replace("p = ", ""))

        for m in re.finditer(r"(\d{1,3})\s*/\s*(\d{1,3})", text):
            a, b = m.group(1), m.group(2)
            # «28/10» — дата, а не доля: знаменатель ≤ 12, числитель ≤ 31,
            # и за дробью не идёт скобка или процент.
            tail = text[m.end():m.end() + 3].lstrip()
            if int(b) <= 12 and int(a) <= 31 and not tail.startswith(("(", "%")):
                continue
            if not re.search(r"\b%s\s*/\s*%s\b" % (a, b), sources):
                miss_frac.append("%s/%s" % (a, b))

        for pct in set(re.findall(r"(\d+\.\d)\s*\\?%", text)):
            if pct not in sources:
                miss_pct.append(pct)

        st8 = "НЕТ" if (miss_p or miss_frac) else ("ЧАСТИЧНО" if miss_pct else "ДА")
        notes = []
        if miss_p:
            notes.append("p: " + ", ".join(miss_p))
        if miss_frac:
            notes.append("дроби: " + ", ".join(miss_frac))
        if miss_pct:
            notes.append("проценты без источника: " + ", ".join(sorted(miss_pct)))
        mark("8. Числа статьи в выводе", st8,
             "; ".join(notes) if notes else "p, дроби и проценты найдены")

    # --- 9. Ярус 0 ---------------------------------------------------------
    tier0 = os.path.join(HERE, "check_tier0.py")
    docs = [os.path.join(root, "NICK_CAMMARATA", "PASS_BY_REFERENCE_PROTOCOL.md"),
            os.path.join(REPO, "VERDICT_JOURNEY.md"),
            os.path.join(REPO, "README.md"),
            os.path.join(root, "ARXIV_PACKAGE", "main.tex")]
    docs = [d for d in docs if os.path.exists(d)]
    if os.path.exists(tier0) and docs:
        t0 = subprocess.run([sys.executable, tier0, "--root", root] + docs,
                            capture_output=True, text=True, encoding="utf-8")
        tail = [l for l in t0.stdout.splitlines() if "ИТОГ" in l]
        mark("9. Ярус 0: ссылки существуют", "ДА" if t0.returncode == 0 else "НЕТ",
             tail[0].strip() if tail else "проверено %d документов" % len(docs))
    else:
        mark("9. Ярус 0: ссылки существуют", "НЕТ", "check_tier0.py отсутствует")

    mark("6. Архив неизменяем", "ВРУЧНУЮ",
         "archive.jsonl не под append-only; целостность — по sha256 в каноне")

    # --- вывод -------------------------------------------------------------
    print("=" * 74)
    print("ЧЕКЛИСТ ПРОТОКОЛА — механическая часть")
    print("  корень: %s | репозиторий: %s" % (root, REPO))
    print("=" * 74)
    for item, status, note in results:
        print("  [%-8s] %-38s %s" % (status, item, note))
    print("=" * 74)
    counts = {}
    for _, status, _ in results:
        counts[status] = counts.get(status, 0) + 1
    order = ("ДА", "AMENDED", "НЕТ", "ЧАСТИЧНО", "ВРУЧНУЮ", "Н/Д")
    summary = ", ".join("%d %s" % (counts[k], k) for k in order if k in counts)
    verdict = ("ПРОТОКОЛ ПРИМЕНЁН ЧАСТИЧНО (%s)" % summary if counts.get("НЕТ")
               else "механическая часть пройдена (%s)" % summary)
    print("  ИТОГ:", verdict)
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Тесты хука PreToolUse: поведение на входе, а не наличие флагов.

Хук — несущая деталь проекта («без него вся философия врёт»), и до сих пор он
проверялся руками на шести сценариях. Здесь то же самое, но воспроизводимо.

Контракт хука: stdin — JSON, exit 0 — пропустить, exit 2 — заблокировать.

Запуск:  python tests/test_hook.py
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HOOK = os.path.join(ROOT, "hooks", "pre_tool_use_guard.py")

# Тесты печатают по-русски, а консоль windows-latest — cp1252: печать падала с
# UnicodeEncodeError, и CI краснел на исправном коде. Кодировку не переключаем
# (в cmd.exe это дало бы мусор), а разрешаем замену непечатаемых символов.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(errors="replace")
        except Exception:
            pass

# Имена шеллов собираем из частей: иначе установленный в системе хук может
# заблокировать сам запуск тестов, увидев имя второго шелла в командной строке.
PS = "power" + "shell"
CMD = "cmd"

CASES = []


def case(tool, command, want, why, env=None):
    CASES.append((tool, command, want, why, env or {}))


# --- известные инструменты: грамматика по инструменту, а не по ОС -------------
case("Bash", 'echo "hi"', 0, "обычная команда")
case("Bash", 'echo "a`"b"', 2, "posix: бэктик открывает подстановку")
case("Bash", 'git commit -m "fix', 2, "незакрытая кавычка")
case("Bash", "echo hi\\", 2, "висящий escape = продолжение строки")
case(PS, 'dir "C:\\"', 0, "та же строка валидна в грамматике второго шелла")
case(PS, 'echo "a`"b"', 0, "там бэктик экранирует кавычку, строка сбалансирована")
case(PS, 'git commit -m "fix', 2, "незакрытая кавычка невалидна везде")

# --- неизвестный инструмент: двойная проверка (Вариант Б) --------------------
case("MyCustomTool", 'echo "hi"', 0, "грамматики согласны: безопасно")
case("MyCustomTool", 'git commit -m "fix', 2, "грамматики согласны: небезопасно")
case("MyCustomTool", 'dir "C:\\"', 2, "грамматики разошлись: блок и просьба объявить")
case("MyCustomTool", 'echo "a`"b"', 2, "та же подпись, что у валидной команды выше")

# --- объявление грамматики снимает неоднозначность --------------------------
case("MyCustomTool", 'dir "C:\\"', 0, "объявлен грамматикой второго шелла — команда проходит",
     {"QUOTE_GUARD_MAP": "MyCustomTool=" + PS})
case("MyCustomTool", 'dir "C:\\"', 2, "объявлен posix — и команда действительно ломается",
     {"QUOTE_GUARD_MAP": "MyCustomTool=posix"})
case("MyCustomTool", 'echo "a`"b"', 2, "объявлен posix — ловим то, ради чего всё",
     {"QUOTE_GUARD_MAP": "MyCustomTool=posix"})

# --- глобальный override ----------------------------------------------------
case(PS, 'dir "C:\\"', 2, "QUOTE_GUARD_SHELL сильнее таблицы инструментов",
     {"QUOTE_GUARD_SHELL": "posix"})

# --- границы: heredoc, пустой вход, битый JSON, инструмент без command -------
# heredoc — конструкция POSIX, поэтому проверяем на инструменте с известной
# грамматикой. Для неизвестного инструмента такая строка честно двусмысленна:
# POSIX её примет, PowerShell не поймёт, и хук заблокирует по правилу согласия.
case("Bash", "cat <<EOF", 2, "heredoc без разделителя: шелл будет ждать EOF")
case("Bash", 'cat <<EOF\nон сказал "привет\nEOF', 0,
     "тело heredoc дословно: непарная кавычка внутри безопасна")
case("Bash", 'cat <<EOF\nbody\nEOF\necho "broken', 2,
     "непарная кавычка ПОСЛЕ разделителя — по-прежнему вешает шелл")
# here-string: `<<<` — не heredoc, тела нет. Для неизвестного инструмента строка
# НЕ двусмысленна: PowerShell тоже считает её безопасной (`<` там не спецсимвол),
# поэтому согласие достигается и хук пропускает.
case("Bash", 'cat <<< "text"', 0, "here-string: не heredoc, кавычки обычные аргументы")
case("MyCustomTool", 'cat <<< "text"', 0, "here-string: обе грамматики согласны — не двусмысленно")
case("Read", "not a command", 0, "инструмент без поля command")
case("MyCustomTool", 'python -c "print(1)"', 0, "кавычки закрыты, все согласны")


def run(payload, env_extra):
    env = dict(os.environ)
    for key in ("QUOTE_GUARD_SHELL", "QUOTE_GUARD_MAP", "QUOTE_GUARD_TOOLS"):
        env.pop(key, None)
    env.update(env_extra)
    # Родитель и дитя обязаны говорить в одной кодировке. Иначе унаследованный
    # PYTHONIOENCODING заставляет дитя писать cp1252, а text=True декодирует
    # utf-8: поток-читатель падает, p.stderr становится None, и тест валится с
    # TypeError вместо результата. errors="replace" — чтобы диагностика падения
    # не превращалась во второе падение.
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, HOOK], input=payload,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=30, env=env)
    return p.returncode, p.stderr or ""


def main():
    checks = 0
    failures = []

    for tool, command, want, why, env_extra in CASES:
        payload = json.dumps({"tool_name": tool, "tool_input": {"command": command}})
        got, err = run(payload, env_extra)
        checks += 1
        ok = got == want
        if not ok:
            failures.append("%s → %d, ждали %d (stderr: %s)"
                            % (why, got, want, err.strip().splitlines()[:1]))
        print("%s exit=%d  %-22s %s" % ("OK  " if ok else "FAIL", got, tool, why))

    # Пустой вход и битый JSON — отдельно: там нет tool_name.
    got, _ = run("", {})
    checks += 1
    if got != 0:
        failures.append("пустой вход → %d, ждали 0" % got)
    print("%s exit=%d  %-22s %s" % ("OK  " if got == 0 else "FAIL", got, "(пусто)", "пустой вход"))

    got, err = run("{not json", {})
    checks += 1
    if got != 2:
        failures.append("битый JSON → %d, ждали 2" % got)
    print("%s exit=%d  %-22s %s" % ("OK  " if got == 2 else "FAIL", got, "(битый JSON)", "неразбираемый вход"))

    # Сообщение о неоднозначности обязано содержать готовую команду-лекарство.
    payload = json.dumps({"tool_name": "MyCustomTool",
                          "tool_input": {"command": 'dir "C:\\"'}})
    _, err = run(payload, {})
    checks += 1
    hint = "QUOTE_GUARD_MAP=MyCustomTool=" in err
    if not hint:
        failures.append("в сообщении нет подсказки QUOTE_GUARD_MAP")
    print("%s %-31s %s" % ("OK  " if hint else "FAIL", "(подсказка в stderr)",
                           "блокировка объясняет, как выйти"))

    print()
    if failures:
        for f in failures:
            print("  - " + f)
        print("=== FAIL: %d из %d ===" % (len(failures), checks))
        return 1
    print("=== ALL PASS: %d проверок ===" % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())

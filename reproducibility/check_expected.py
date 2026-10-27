# -*- coding: utf-8 -*-
"""Проверка чекера: сравнение вывода verify_numbers.py с эталоном.

Два режима:
  python check_expected.py            — сверить текущий вывод с expected_output.txt
  python check_expected.py --selftest — known-answer тест: испортить эталон и
                                        убедиться, что проверка это ловит

Второй режим отвечает на вопрос «кто проверяет проверяльщика»: чекер, который
не умеет падать, бесполезен.
"""
import difflib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "verify_numbers.py")
EXPECTED = os.path.join(HERE, "expected_output.txt")


def run():
    r = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True,
                       encoding="utf-8")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def compare(actual, expected):
    if actual == expected:
        return True, ""
    diff = list(difflib.unified_diff(expected.splitlines(), actual.splitlines(),
                                     "expected", "actual", lineterm="", n=1))
    return False, "\n".join(diff[:40])


def main():
    code, actual = run()
    if code != 0:
        print("FAIL: verify_numbers.py завершился с кодом %d" % code)
        return 1
    expected = open(EXPECTED, encoding="utf-8").read()

    if "--selftest" in sys.argv:
        # Портим одно число в эталоне и требуем, чтобы сравнение это заметило.
        broken = expected.replace("p = 0.675", "p = 0.775", 1)
        if broken == expected:
            print("FAIL: нечего портить — строка 'p = 0.675' не найдена")
            return 1
        ok, _ = compare(actual, broken)
        if ok:
            print("FAIL: испорченный эталон прошёл проверку — чекер слеп")
            return 1
        print("OK: испорченный эталон отвергнут (known-answer тест пройден)")

    ok, diff = compare(actual, expected)
    if ok:
        print("OK: вывод совпадает с эталоном (%d строк)" % len(actual.splitlines()))
        return 0
    print("FAIL: вывод расходится с эталоном\n" + diff)
    return 1


if __name__ == "__main__":
    sys.exit(main())

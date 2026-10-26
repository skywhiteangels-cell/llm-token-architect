"""
Test suite for Quote Guard v3 (Python).

No dependencies: plain `python tests/test_parity.py`.
Exit code 0 = all green, 1 = failures.

The point of this file existing separately from the built-in --selftest is that
a test suite can be wired into CI. Regression on a guardrail is silent otherwise:
the tool keeps "working" and just stops catching what it used to catch.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parity_check import analyze, verify_quote_parity, SHELLS  # noqa: E402

FAILURES = []
CHECKS = 0


def check(label, got, expected):
    global CHECKS
    CHECKS += 1
    if got != expected:
        FAILURES.append("%s\n     expected: %r\n     got:      %r" % (label, expected, got))


# ---------------------------------------------------------------------------
# 1. Grammar tables per shell
#    (shell, command, expected_safe, why)
# ---------------------------------------------------------------------------
# Cases come from a shared fixture so Python and Node test the SAME table.
# Two separate tables is exactly how the implementations drift apart while both
# suites stay green: 31 cases here vs 29 there was invisible until it wasn't.
FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "cases.jsonl")
GRAMMAR_CASES = []
with open(FIXTURE, encoding="utf-8") as _f:
    for _line in _f:
        _line = _line.strip()
        if _line:
            GRAMMAR_CASES.append(json.loads(_line))

for case in GRAMMAR_CASES:
    check("[%s] %s  (%s)" % (case["shell"], case["cmd"], case["why"]),
          verify_quote_parity(case["cmd"], shell=case["shell"]), case["safe"])


# ---------------------------------------------------------------------------
# 2. The same string under different shells must be allowed to disagree.
#    This is the whole point of v3: grammar is not universal.
# ---------------------------------------------------------------------------
check('posix  dir "C:\\" is unsafe', verify_quote_parity('dir "C:\\"', "posix"), False)
check('powershell dir "C:\\" is safe', verify_quote_parity('dir "C:\\"', "powershell"), True)


# ---------------------------------------------------------------------------
# 3. analyze() contract
# ---------------------------------------------------------------------------
r = analyze('echo "hi', "posix")
check("analyze returns safe=False", r["safe"], False)
check("analyze reports the state", r["state"], "DOUBLE")
check("analyze reports the offset", r["offset"], 5)
check("analyze echoes the shell", r["shell"], "posix")
check("analyze has a reason string", isinstance(r["reason"], str) and len(r["reason"]) > 0, True)

r = analyze("echo foo\\", "posix")
check("dangling escape has its own state", r["state"], "ESCAPE")

r = analyze("echo hi", "powershell")
check("clean command is NORMAL", r["state"], "NORMAL")
check("clean command has no offset", r["offset"], None)


# ---------------------------------------------------------------------------
# 4. Defensive behaviour
# ---------------------------------------------------------------------------
check("non-string input is refused", verify_quote_parity(None), False)
check("empty string is safe", verify_quote_parity(""), True)

try:
    analyze("echo hi", "fish")
    check("unknown shell raises", "no exception", "ValueError")
except ValueError:
    check("unknown shell raises", "ValueError", "ValueError")

check("SHELLS is stable", SHELLS, ("posix", "powershell", "cmd"))


# ---------------------------------------------------------------------------
# 5. Idempotence: the same input must always give the same answer.
#    A guardrail with hidden state is not a guardrail.
# ---------------------------------------------------------------------------
sample = 'powershell -Command "Write-Output \'Hello\'"'
results = {verify_quote_parity(sample, "powershell") for _ in range(50)}
check("idempotent over 50 runs", len(results), 1)


# ---------------------------------------------------------------------------
if FAILURES:
    print("=== FAILED: %d of %d checks ===" % (len(FAILURES), CHECKS))
    for f in FAILURES:
        print("  - " + f)
    sys.exit(1)

print("=== ALL PASS: %d checks across %d grammar cases ===" % (CHECKS, len(GRAMMAR_CASES)))
sys.exit(0)

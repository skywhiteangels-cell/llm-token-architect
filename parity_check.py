"""
Quote Parity Guardrail  (v2 — context-aware state machine)
Author: SkyAngel  (rewritten for correctness)
Purpose: Pre-flight terminal command verification to prevent interactive shell
         deadlocks (the '>>' prompt) caused by UNTERMINATED quotes.

WHY v2 (and what was wrong in v1):
  v1 counted single and double quotes independently with a regex `(?<!\\)"` and
  required each count to be even. That FALSE-POSITIVES on perfectly valid commands
  like  echo "it's a test"  (odd single-quote count) and ignores backticks
  entirely. It also mis-handled a double backslash before a quote (\\").

  The correct question is not "is the count even?" but "are we still inside a
  quote/backtick at end-of-string?" — because THAT is exactly what makes the
  shell wait for more input and hang. A shell-aware state machine answers it and
  naturally accepts "it's" while still catching genuinely dangling quotes.

  Limitation: this is a guardrail, not a full POSIX/bash parser. It does not
  model heredocs (<<), $'...' ANSI-C quoting, or backtick-nested-inside-double
  quoting. It is deliberately conservative about *not* hanging, which is the
  failure we are guarding against.
"""

import sys
import argparse


def verify_quote_parity(command: str) -> bool:
    """
    Returns True when the command has NO unterminated quote/backtick context
    at end-of-string, i.e. it will NOT hang an interactive shell.
    Same signature as v1 -> drop-in replacement.
    """
    if not isinstance(command, str):
        return False

    state = "NORMAL"   # NORMAL | SINGLE | DOUBLE | BACKTICK
    i = 0
    n = len(command)
    while i < n:
        c = command[i]
        if state == "NORMAL":
            if c == "'":
                state = "SINGLE"
            elif c == '"':
                state = "DOUBLE"
            elif c == '`':
                state = "BACKTICK"
            elif c == '\\':        # escaped char in unquoted context
                i += 2
                continue
        elif state == "SINGLE":
            # Inside single quotes everything is literal, including backslash.
            if c == "'":
                state = "NORMAL"
        elif state == "DOUBLE":
            if c == '"':
                state = "NORMAL"
            elif c == '\\':        # \" is a literal quote, do not close
                i += 2
                continue
        elif state == "BACKTICK":
            if c == '`':
                state = "NORMAL"
            elif c == '\\':
                i += 2
                continue
        i += 1

    return state == "NORMAL"


def main():
    parser = argparse.ArgumentParser(
        description="Quote Parity Guardrail (v2, context-aware) — pre-flight shell safety check."
    )
    parser.add_argument(
        "-c", "--command",
        required=True,
        help="Shell command string to verify before execution.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Explain the final quote state.",
    )
    args = parser.parse_args()

    safe = verify_quote_parity(args.command)
    if args.verbose:
        print(f"Terminates inside a quote/backtick: {not safe}")
    if safe:
        print("PARITY OK — command is safe to execute.")
        sys.exit(0)
    else:
        print("PARITY VIOLATION — unterminated quote/backtick detected. Command blocked before shell execution!")
        sys.exit(1)


if __name__ == "__main__":
    # Self-test mode (no args) — runs built-in tests
    if len(sys.argv) == 1:
        cases = [
            ('echo "it\'s a test"',                       True),   # valid, was FALSE in v1
            ('powershell -Command "Write-Output \'Hello World\'"', True),
            ('it\\\'s a valid string with escaped quote',  True),
            ('powershell -Command "Write-Output \'Hello',  False),  # real dangling (outer " never closed -> shell hangs)
            ('echo "hi',                                   False),  # dangling double
            ('cat `unterminated',                          False),  # dangling backtick
            ('echo "a\\""',                                True),   # escaped quote is literal
            ('dir "C:\\temp"',                             True),
        ]
        print("=== Built-in Tests (v2) ===")
        ok = True
        for cmd, expected in cases:
            got = verify_quote_parity(cmd)
            mark = "OK " if got == expected else "FAIL"
            if got != expected:
                ok = False
            print(f"  [{mark}] expected={expected!s:5} got={got!s:5}  {cmd}")
        print("ALL PASS" if ok else "SOME FAILED")
    else:
        main()

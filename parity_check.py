"""
Quote Guard  (v3 — context-aware state machine, multi-shell)
Author: SkyAngel
License: MIT

Purpose
-------
Pre-flight verification of a terminal command string BEFORE it is handed to a
shell. Prevents the interactive-prompt deadlock: when a command ends inside an
unterminated quote / backtick / escape context, PowerShell, CMD and bash all
assume the user is still typing, print a continuation prompt (`>>` or `>`),
and wait forever. For an autonomous agent this is an unrecoverable hang — there
is no stderr to read, no error code to self-correct from.

WHAT CHANGED IN v3 (and why it matters)
---------------------------------------
v2 asked the right question ("is the lexer still inside a quote at end of
string?") but answered it with POSIX rules only. On Windows PowerShell that is
simply the wrong grammar:

  * In PowerShell the escape character is the BACKTICK (`), not the backslash.
    A backslash is a literal character.
  * Therefore `dir "C:\\"` is a perfectly valid PowerShell command, but the v2
    POSIX lexer consumed the closing quote as `\\"` and blocked it.
  * And `echo "a`"b"` is valid PowerShell (backtick escapes the quote), but v2
    reported an unterminated string.

A guardrail that blocks valid commands is worse than no guardrail: the agent
learns to bypass it, and then it protects nothing. v3 therefore takes the shell
as an explicit parameter and models the correct grammar for each.

  shell="posix"       bash / sh / zsh / Git Bash  — backslash escapes, backtick quotes
  shell="powershell"  PowerShell 5.1 / 7+         — backtick escapes, '..' literal,
                                                     '' and "" double to a literal
  shell="cmd"         cmd.exe                     — ^ escapes, only " quotes

Also new in v3: a dangling escape at end-of-string (trailing backslash, backtick
or caret) is reported. It is not a quote problem, but it is the same hang: those
characters are line continuations, so the shell waits for the next line.

Limitations (deliberate — this is a guardrail, not a parser)
------------------------------------------------------------
Not modelled: heredocs (`<<EOF`), POSIX `$'...'` ANSI-C quoting, PowerShell
`$(...)` subexpressions inside double quotes, and nested command substitution.
The tool is deliberately conservative about NOT hanging; it never claims to be
a complete shell grammar. See README.md for the honest limits table.
"""

import argparse
import json
import sys

POSIX = "posix"
POWERSHELL = "powershell"
CMD = "cmd"
SHELLS = (POSIX, POWERSHELL, CMD)

__all__ = ["analyze", "verify_quote_parity", "SHELLS", "POSIX", "POWERSHELL", "CMD"]


def analyze(command, shell=POSIX):
    """
    Inspect a command string and report whether it can hang a shell.

    Returns a dict:
        safe    (bool)  True when the lexer is closed at end-of-string
        state   (str)   NORMAL | SINGLE | DOUBLE | BACKTICK | ESCAPE | INVALID
        shell   (str)   the grammar that was applied
        reason  (str)   human-readable explanation
        offset  (int)   offset where the open context started (or None)
    """
    if shell not in SHELLS:
        raise ValueError("unknown shell %r; expected one of %s" % (shell, SHELLS))
    if not isinstance(command, str):
        return {
            "safe": False,
            "state": "INVALID",
            "shell": shell,
            "reason": "command is not a string",
            "offset": None,
        }

    state = "NORMAL"
    opened_at = None
    i = 0
    n = len(command)

    def open_context(new_state, at):
        nonlocal state, opened_at
        state = new_state
        opened_at = at

    def close_context():
        nonlocal state, opened_at
        state = "NORMAL"
        opened_at = None

    def dangling_escape(at):
        return {
            "safe": False,
            "state": "ESCAPE",
            "shell": shell,
            "reason": "dangling escape at end-of-string (line continuation, shell waits for more input)",
            "offset": at,
        }

    while i < n:
        c = command[i]

        if state == "NORMAL":
            if shell == POWERSHELL:
                if c == "`":                      # backtick is THE escape char
                    if i + 1 >= n:
                        return dangling_escape(i)
                    i += 2
                    continue
                if c == "'":
                    open_context("SINGLE", i)
                elif c == '"':
                    open_context("DOUBLE", i)

            elif shell == CMD:
                if c == "^":                      # cmd escape outside quotes
                    if i + 1 >= n:
                        return dangling_escape(i)
                    i += 2
                    continue
                if c == '"':
                    open_context("DOUBLE", i)

            else:                                 # POSIX
                if c == "\\":
                    if i + 1 >= n:
                        return dangling_escape(i)
                    i += 2
                    continue
                if c == "'":
                    open_context("SINGLE", i)
                elif c == '"':
                    open_context("DOUBLE", i)
                elif c == "`":
                    open_context("BACKTICK", i)

        elif state == "SINGLE":
            if shell == POWERSHELL:
                if c == "'":
                    if i + 1 < n and command[i + 1] == "'":
                        i += 2                    # '' is a literal quote
                        continue
                    close_context()
            else:                                 # POSIX: everything literal here
                if c == "'":
                    close_context()

        elif state == "DOUBLE":
            if shell == POWERSHELL:
                if c == "`":
                    if i + 1 >= n:
                        return dangling_escape(i)
                    i += 2
                    continue
                if c == '"':
                    if i + 1 < n and command[i + 1] == '"':
                        i += 2                    # "" is a literal quote
                        continue
                    close_context()
            elif shell == CMD:
                if c == '"':
                    close_context()
            else:
                if c == "\\":
                    if i + 1 >= n:
                        return dangling_escape(i)
                    i += 2
                    continue
                if c == '"':
                    close_context()

        elif state == "BACKTICK":                 # POSIX only
            if c == "`":
                close_context()
            elif c == "\\":
                if i + 1 >= n:
                    return dangling_escape(i)
                i += 2
                continue

        i += 1

    if state == "NORMAL":
        return {
            "safe": True,
            "state": "NORMAL",
            "shell": shell,
            "reason": "lexer closed at end-of-string",
            "offset": None,
        }

    return {
        "safe": False,
        "state": state,
        "shell": shell,
        "reason": "unterminated %s context opened at offset %s" % (state.lower(), opened_at),
        "offset": opened_at,
    }


def verify_quote_parity(command, shell=POSIX):
    """
    Drop-in replacement for the v1/v2 signature.

    Returns True when the command has NO unterminated quote/backtick/escape
    context at end-of-string, i.e. it will not hang an interactive shell.
    """
    return analyze(command, shell=shell)["safe"]


# (shell, command, expected_safe)
CASES = [
    # --- POSIX -------------------------------------------------------------
    (POSIX, 'echo "it\'s a test"', True),        # valid: ' is literal inside "..."
    (POSIX, 'echo "hi', False),                  # dangling double quote
    (POSIX, 'cat `unterminated', False),         # dangling backtick
    (POSIX, 'echo "a\\""', True),                # \" is a literal quote
    (POSIX, 'dir "C:\\temp"', True),
    (POSIX, 'dir "C:\\"', False),                # in bash the backslash escapes the quote -> hangs
    (POSIX, "echo 'it'\\''s'", True),            # the classic POSIX literal-quote idiom
    (POSIX, 'echo foo\\', False),                # trailing backslash = line continuation
    (POSIX, 'echo "a" && echo "b"', True),
    # --- PowerShell --------------------------------------------------------
    (POWERSHELL, 'dir "C:\\"', True),            # <-- the v2 bug: backslash is literal in PS
    (POWERSHELL, 'dir "C:\\temp\\"', True),
    (POWERSHELL, 'echo "a`"b"', True),           # backtick escapes the quote
    (POWERSHELL, 'echo "hi', False),
    (POWERSHELL, "echo 'it''s'", True),          # '' is a literal quote in PS
    (POWERSHELL, "echo 'it's'", False),          # ' ends the string, next ' opens a new one
    (POWERSHELL, 'Write-Output "unterminated', False),
    (POWERSHELL, 'echo `n', True),               # escape sequence, no quote context
    (POWERSHELL, 'echo hi`', False),             # trailing backtick = line continuation
    (POWERSHELL, 'powershell -Command "echo `"hi`""', True),
    # --- CMD ---------------------------------------------------------------
    (CMD, 'echo "hi', False),
    (CMD, 'echo "a\\"', True),                   # backslash is literal in cmd
    (CMD, 'echo ^"hi', True),                    # ^ escapes the quote
    (CMD, 'echo hi^', False),                    # trailing ^ = line continuation
]


def run_selftest():
    print("=== Quote Guard v3 — built-in tests ===")
    failed = 0
    for shell, cmd, expected in CASES:
        got = verify_quote_parity(cmd, shell=shell)
        ok = got == expected
        if not ok:
            failed += 1
        print("  [%s] %-10s expected=%-5s got=%-5s  %s"
              % ("OK  " if ok else "FAIL", shell, expected, got, cmd))
    total = len(CASES)
    if failed:
        print("\n%d/%d FAILED" % (failed, total))
        return 1
    print("\nALL PASS (%d cases)" % total)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="parity_check.py",
        description="Quote Guard v3 — pre-flight shell safety check. "
                    "Blocks commands that would hang the shell on a continuation prompt.",
    )
    parser.add_argument("-c", "--command", help="Shell command string to verify.")
    parser.add_argument(
        "--shell",
        choices=SHELLS,
        default=POSIX,
        help="Shell grammar to apply (default: posix). Use 'powershell' for PowerShell 5.1/7+, "
             "'cmd' for cmd.exe. This is NOT cosmetic: PowerShell escapes with a backtick, "
             "so a POSIX check false-positives on valid commands.",
    )
    parser.add_argument("--stdin", action="store_true", help="Read the command from stdin.")
    parser.add_argument("--json", action="store_true", help="Machine-readable output (for hooks).")
    parser.add_argument("-v", "--verbose", action="store_true", help="Explain the final lexer state.")
    parser.add_argument("--selftest", action="store_true", help="Run the built-in test table.")
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest()

    command = args.command
    if args.stdin:
        command = sys.stdin.read().rstrip("\r\n")
    if command is None:
        parser.error("either -c/--command or --stdin is required (or use --selftest)")

    result = analyze(command, shell=args.shell)

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif result["safe"]:
        if args.verbose:
            print("shell=%s state=%s" % (result["shell"], result["state"]))
        print("PARITY OK — command is safe to execute.")
    else:
        if args.verbose:
            print("shell=%s state=%s offset=%s" % (result["shell"], result["state"], result["offset"]))
        print("PARITY VIOLATION — %s. Command blocked before shell execution!" % result["reason"])

    return 0 if result["safe"] else 1


if __name__ == "__main__":
    sys.exit(main())

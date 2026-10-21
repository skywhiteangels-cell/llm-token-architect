"""
Quote Parity Guardrail
Author: SkyAngel
Purpose: Pre-flight terminal command verification to prevent interactive shell deadlocks (>> in PowerShell/Bash).

Usage:
    As a library:
        from parity_check import verify_quote_parity
        ok = verify_quote_parity("your shell command here")

    As a CLI tool:
        python parity_check.py --command "your shell command here"
        python parity_check.py -c "powershell -Command \"Write-Output 'Hello'\""

Exit codes:
    0  — parity OK (safe to execute)
    1  — parity VIOLATION (odd quote count detected, block execution)
"""

import re
import sys
import argparse


def count_unescaped(text: str, char: str) -> int:
    """
    Counts occurrences of char that are NOT preceded by a backslash.
    Handles escaped quotes like \' and \" correctly.
    """
    pattern = r'(?<!\\)' + re.escape(char)
    return len(re.findall(pattern, text))


def verify_quote_parity(command: str) -> bool:
    """
    Checks if single and double quotes in a shell command have even parity.
    Escaped quotes (\\' and \\") are excluded from the count.
    Returns True if safe, False if parity is violated.
    """
    single_quotes = count_unescaped(command, "'")
    double_quotes = count_unescaped(command, '"')

    return (single_quotes % 2 == 0) and (double_quotes % 2 == 0)


def main():
    parser = argparse.ArgumentParser(
        description="Quote Parity Guardrail — pre-flight shell command safety check."
    )
    parser.add_argument(
        "-c", "--command",
        required=True,
        help="Shell command string to verify before execution."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed quote counts."
    )
    args = parser.parse_args()

    single = count_unescaped(args.command, "'")
    double = count_unescaped(args.command, '"')

    if args.verbose:
        print(f"Single quotes (unescaped): {single}  {'EVEN ✓' if single % 2 == 0 else 'ODD ✗'}")
        print(f"Double quotes (unescaped): {double}  {'EVEN ✓' if double % 2 == 0 else 'ODD ✗'}")

    if verify_quote_parity(args.command):
        print("PARITY OK — command is safe to execute.")
        sys.exit(0)
    else:
        print("PARITY VIOLATION — odd quote count detected. Command blocked before shell execution!")
        sys.exit(1)


if __name__ == "__main__":
    # Self-test mode (no args) — runs built-in tests
    if len(sys.argv) == 1:
        test_ok   = "powershell -Command \"Write-Output 'Hello World'\""
        test_esc  = "it\\'s a valid string with escaped quote"          # escaped single → not counted
        test_fail = "powershell -Command \"Write-Output 'Hello World\""  # intentionally broken: odd single quote count

        print("=== Built-in Tests ===")
        print(f"Test OK       : {verify_quote_parity(test_ok)}")    # True
        print(f"Test Escaped  : {verify_quote_parity(test_esc)}")   # True
        print(f"Test Fail     : {verify_quote_parity(test_fail)}")  # False
    else:
        main()

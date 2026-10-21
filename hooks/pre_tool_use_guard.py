#!/usr/bin/env python3
"""
Quote Guard — PreToolUse hook for agent harnesses.

WHY THIS FILE EXISTS
--------------------
The article's whole argument is that a guardrail must be structural, not
voluntary. A CLI that the agent *remembers* to call is exactly the probabilistic
luck the article argues against: one forgotten call, one hang, one dead session.
This hook removes the "remembering" from the equation — the harness itself runs
the check before every shell command, and refuses to execute what would hang.

CONTRACT (Claude Code / compatible harnesses)
---------------------------------------------
  stdin  : JSON  {"tool_name": "Bash", "tool_input": {"command": "..."}}
  exit 0 : allow
  exit 2 : BLOCK — stderr is fed back to the model as the reason

Adaptation to another harness is usually just renaming the tool list below, or
swapping the JSON parsing for whatever payload your harness sends.

CONFIGURATION
-------------
  QUOTE_GUARD_SHELL   posix | powershell | cmd   (default: auto)
  QUOTE_GUARD_PY      path to python with the repo on sys.path (optional)

Exit code 2 is deliberate: a hook that *crashes* (exit 1) usually fails open,
and a guardrail that fails open is decoration.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, REPO_ROOT)

try:
    from parity_check import analyze
except Exception as exc:  # pragma: no cover - misconfiguration is loud on purpose
    sys.stderr.write("quote-guard: cannot import parity_check from %s: %s\n" % (REPO_ROOT, exc))
    sys.exit(2)

# Tool names that carry a shell command string. Add your harness's names here.
SHELL_TOOLS = {
    "Bash",
    "Shell",
    "Terminal",
    "run_command",
    "execute_command",
    "powershell",
    "PowerShell",
    "cmd",
}


def pick_shell() -> str:
    """Explicit override wins; otherwise guess from the platform."""
    forced = os.environ.get("QUOTE_GUARD_SHELL", "").strip().lower()
    if forced in ("posix", "powershell", "cmd"):
        return forced
    if os.name == "nt":
        # Default Windows harness shell. Override with QUOTE_GUARD_SHELL=posix
        # if your agent actually runs Git Bash (which many do).
        return "powershell"
    return "posix"


def extract_command(payload):
    """Return the command string from a tool payload, or None."""
    if not isinstance(payload, dict):
        return None

    tool_input = payload.get("tool_input") or payload.get("input") or payload.get("args") or {}
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script", "shell_command"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    if isinstance(tool_input, str):
        return tool_input
    return None


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.stderr.write("quote-guard: unparsable hook payload: %s\n" % exc)
        return 2

    tool_name = payload.get("tool_name") or payload.get("tool") or ""
    if tool_name not in SHELL_TOOLS:
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    shell = pick_shell()
    result = analyze(command, shell=shell)

    if result["safe"]:
        return 0

    sys.stderr.write(
        "quote-guard BLOCKED a command that would hang the shell.\n"
        "  shell:  %s\n"
        "  state:  %s\n"
        "  reason: %s\n"
        "  command: %s\n"
        "Rewrite the command so the quote/backtick/escape context is closed, "
        "or avoid passing the payload through the shell at all (write the file "
        "with a native file tool instead of echo/Set-Content).\n"
        % (result["shell"], result["state"], result["reason"], command)
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())

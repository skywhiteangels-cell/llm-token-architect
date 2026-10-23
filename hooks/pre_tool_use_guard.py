#!/usr/bin/env python3
"""
Quote Guard — PreToolUse hook for agent harnesses (WorkBuddy / Claude Code).

WHY THIS FILE EXISTS
--------------------
The article's whole argument is that a guardrail must be structural, not
voluntary. A CLI that the agent *remembers* to call is exactly the probabilistic
luck the article argues against: one forgotten call, one hang, one dead session.
This hook removes the "remembering" from the equation — the harness itself runs
the check before every shell command, and refuses to execute what would hang.

CONTRACT
--------
  stdin  : JSON  {"tool_name": "Bash", "tool_input": {"command": "..."}}
  exit 0 : allow
  exit 2 : BLOCK — stderr is fed back to the model as the reason

Exit code 2 is deliberate: most harnesses treat a hook that *crashes* (exit 1)
as "hook failed, continue anyway". A guardrail that fails open is decoration.

DESIGN NOTES THAT MATTER
------------------------
1. The grammar is chosen per TOOL, not per platform. In WorkBuddy on Windows the
   `Bash` tool is Git Bash (POSIX grammar) while `PowerShell` is a separate tool.
   Guessing by OS would apply the wrong rules to one of them and block valid
   commands — the fastest way to get a guardrail deleted.

2. Any tool carrying a `command` string is treated as a shell call, even if its
   name is not in the table. A silent no-op because of an unexpected tool name
   would look like protection while providing none.

3. Heredocs are skipped. A heredoc body is read verbatim until the delimiter, so
   quotes inside it cannot hang the shell — but they *can* look unbalanced to a
   line-level lexer. Blocking those would be a false positive on a very common
   pattern (`cat <<'EOF'`). The guard documents its own boundary in behaviour
   instead of pretending to cover it.

4. QUOTE_GUARD_DEBUG=1 writes a one-line log next to this file, so "is the hook
   actually firing?" is a question with an answer, not a matter of trust.
   Setting an environment variable from a terminal does NOT reach this hook —
   the hook is spawned by the application and inherits the application's
   environment, not your shell's. So there is also a flag file: create
   `debug.on` next to this script and logging turns on, no restart of anything
   and no environment plumbing.

CONFIGURATION
-------------
  debug.on            create this file next to the hook to enable the log
  QUOTE_GUARD_SHELL   posix | powershell | cmd   (overrides the per-tool table)
  QUOTE_GUARD_TOOLS   comma-separated extra tool names to treat as shell calls
  QUOTE_GUARD_DEBUG   set to 1 to append decisions to quote_guard.log
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(HERE, "quote_guard.log")
DEBUG_FLAG = os.path.join(HERE, "debug.on")

# The module may live next to the hook (installed copy) or one level up in the
# repository layout. Try both, so the same file works in either place.
for candidate in (HERE, os.path.dirname(HERE)):
    if os.path.exists(os.path.join(candidate, "parity_check.py")):
        sys.path.insert(0, candidate)
        break

try:
    from parity_check import analyze
except Exception as exc:  # pragma: no cover - misconfiguration is loud on purpose
    sys.stderr.write(
        "quote-guard: cannot import parity_check (%s).\n"
        "Expected it next to this hook or one directory up.\n" % exc
    )
    sys.exit(2)

# Tool name -> shell grammar. Explicit names win; unknown names fall back to the
# platform default.
TOOL_SHELL = {
    "Bash": "posix",
    "Shell": "posix",
    "Terminal": "posix",
    "run_command": "posix",
    "execute_command": "posix",
    "sh": "posix",
    "bash": "posix",
    "PowerShell": "powershell",
    "powershell": "powershell",
    "pwsh": "powershell",
    "cmd": "cmd",
    "CMD": "cmd",
}


def debug(message):
    if os.environ.get("QUOTE_GUARD_DEBUG", "").lower() not in ("1", "true", "yes"):
        if not os.path.exists(DEBUG_FLAG):
            return
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write("%s  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), message.rstrip()))
    except OSError:
        pass


def platform_default_shell():
    return "powershell" if os.name == "nt" else "posix"


def extra_tools():
    raw = os.environ.get("QUOTE_GUARD_TOOLS", "")
    return {name.strip() for name in raw.split(",") if name.strip()}


def pick_shell(tool_name):
    forced = os.environ.get("QUOTE_GUARD_SHELL", "").strip().lower()
    if forced in ("posix", "powershell", "cmd"):
        return forced
    return TOOL_SHELL.get(tool_name, platform_default_shell())


def extract_command(payload):
    """Return the command string from a tool payload, or None."""
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, dict):
        return None

    tool_input = payload.get("tool_input") or payload.get("input") or payload.get("args") or {}
    if isinstance(tool_input, str):
        return tool_input
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script", "shell_command"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    return None


def has_heredoc(command):
    """
    True when the command feeds a heredoc. Deliberately simple: `<<` or `<<-`
    followed by an optional quote and a word. Good enough to avoid false
    positives; not a parser.
    """
    i = command.find("<<")
    while i != -1:
        j = i + 2
        if j < len(command) and command[j] == "-":
            j += 1
        while j < len(command) and command[j] in " \t":
            j += 1
        if j < len(command) and command[j] in ("'", '"'):
            j += 1
        if j < len(command) and (command[j].isalnum() or command[j] == "_"):
            return True
        i = command.find("<<", i + 2)
    return False


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        debug("skip: empty payload")
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.stderr.write("quote-guard: unparsable hook payload: %s\n" % exc)
        debug("error: unparsable payload")
        return 2

    tool_name = ""
    if isinstance(payload, dict):
        tool_name = payload.get("tool_name") or payload.get("tool") or ""

    command = extract_command(payload)
    if not command:
        debug("skip: tool=%s no command field" % (tool_name or "?"))
        return 0

    known = tool_name in TOOL_SHELL or tool_name in extra_tools()
    if not known:
        # Not a name we know, but it carries a command string — treat it as a
        # shell call rather than silently doing nothing.
        debug("note: unknown tool '%s' carries a command; checked anyway" % tool_name)

    if has_heredoc(command):
        debug("skip: heredoc in command (known limitation) tool=%s" % (tool_name or "?"))
        return 0

    shell = pick_shell(tool_name)
    result = analyze(command, shell=shell)

    if result["safe"]:
        debug("ok: tool=%s shell=%s" % (tool_name or "?", shell))
        return 0

    debug("blocked: tool=%s shell=%s state=%s" % (tool_name or "?", shell, result["state"]))
    sys.stderr.write(
        "quote-guard BLOCKED a command that would hang the shell.\n"
        "  shell:   %s\n"
        "  state:   %s\n"
        "  reason:  %s\n"
        "  command: %s\n"
        "Rewrite the command so the quote/backtick/escape context is closed, or "
        "avoid passing the payload through the shell at all (write the file with a "
        "native file tool instead of echo/Set-Content).\n"
        % (result["shell"], result["state"], result["reason"], command)
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())

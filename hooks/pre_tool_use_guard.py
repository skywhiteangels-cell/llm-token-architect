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
   would look like protection while providing none. But for an unknown name the
   grammar is NOT guessed from the OS. The string is run through both POSIX and
   PowerShell grammars: agree-safe → allow, agree-unsafe → block, disagree →
   block and ask for `QUOTE_GUARD_MAP=<tool>=<grammar>`. The disagreement case
   cannot be settled by inspection — `echo "a`"b"` and `dir "C:\"` produce the
   same verdict pair (POSIX blocks both, PowerShell accepts both), and one of
   them is a hang while the other is a working command.

3. Heredocs are masked, not skipped. The shell reads a heredoc body verbatim, so
   quotes inside it cannot hang anything — but they do look unbalanced to a
   line-level lexer. The lexer therefore blanks the body and checks the rest.
   Skipping the whole command (the old behaviour) was fail-open: an unbalanced
   quote *after* the terminator went through unnoticed. An unterminated heredoc
   is itself a hang — the shell waits for the delimiter — and is blocked.

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
  QUOTE_GUARD_MAP     "tool=posix,other=powershell" — grammar for tools that are
                      not in the table below; without it an unknown tool is
                      checked against every grammar and blocked on disagreement
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

# Tool name -> shell grammar. Explicit names win. Unknown names are NOT resolved
# from the platform default any more — see check_unknown_tool().
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


# Грамматики, по которым проверяется строка от НЕИЗВЕСТНОГО инструмента.
# cmd намеренно не входит: его экранирование (`^`) почти не встречается в
# командах агентских инструментов, а третий голос только увеличивает число
# ложных срабатываний.
UNKNOWN_SHELLS = ("posix", "powershell")


def declared_shell(tool_name):
    """Грамматика, объявленная для инструмента через QUOTE_GUARD_MAP.

    Формат: QUOTE_GUARD_MAP="mytool=posix,other=powershell".
    Нужен потому, что по имени неизвестного инструмента грамматику угадать
    нельзя, а угадывание по ОС — ровно та ошибка, из-за которой v2 блокировал
    валидные команды PowerShell.
    """
    raw = os.environ.get("QUOTE_GUARD_MAP", "")
    for item in raw.split(","):
        if "=" not in item:
            continue
        name, shell = item.split("=", 1)
        if name.strip() != tool_name:
            continue
        shell = shell.strip().lower()
        if shell in ("posix", "powershell", "cmd"):
            return shell
    return None



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


def check_unknown_tool(tool_name, command):
    """Строка от инструмента, грамматика которого неизвестна.

    Угадывать нельзя: по имени грамматика не выводится, а по ОС — та самая
    ошибка, из-за которой v2 блокировал валидные команды PowerShell. Поэтому
    строка прогоняется по обеим основным грамматикам:

      * все согласны, что безопасно — пропускаем;
      * согласны, что небезопасно — блокируем;
      * разошлись — блокируем и просим объявить грамматику.

    Третий случай неизбежен и не лечится: `echo "a`"b"` и `dir "C:\\"` дают
    одинаковую подпись (posix — блок, powershell — безопасно), различить их по
    строке невозможно. Разрешается не угадыванием, а объявлением.
    """
    verdicts = {shell: analyze(command, shell=shell) for shell in UNKNOWN_SHELLS}
    failed = [s for s in UNKNOWN_SHELLS if not verdicts[s]["safe"]]

    if not failed:
        debug("ok: unknown tool=%s, all grammars agree safe" % tool_name)
        return 0

    if len(failed) == len(UNKNOWN_SHELLS):
        debug("blocked: unknown tool=%s, unsafe in every grammar" % tool_name)
        sys.stderr.write(
            "quote-guard BLOCKED a command that would hang the shell.\n"
            "  tool:    %s (grammar unknown, but the string is unsafe in all: %s)\n"
            "  state:   %s\n"
            "  reason:  %s\n"
            "  command: %s\n"
            % (tool_name, ", ".join(UNKNOWN_SHELLS),
               verdicts[failed[0]]["state"], verdicts[failed[0]]["reason"], command))
        return 2

    passed = [s for s in UNKNOWN_SHELLS if s not in failed]
    debug("blocked: unknown tool=%s, grammars disagree" % tool_name)
    sys.stderr.write(
        "quote-guard BLOCKED an ambiguous command from an unknown tool.\n"
        "  tool:      %s\n"
        "  grammars:  %s\n"
        "  reason:    the same string is valid in one shell and hangs in another,\n"
        "             and this tool's grammar is not declared. Guessing would either\n"
        "             block a working command or let a hanging one through — both\n"
        "             make the guard something people switch off.\n"
        "  fix:       declare it once, then this command is judged correctly:\n"
        "               QUOTE_GUARD_MAP=%s=%s\n"
        "             (or QUOTE_GUARD_SHELL for the whole harness)\n"
        "  command:   %s\n"
        % (tool_name,
           ", ".join("%s=%s" % (s, "unsafe" if s in failed else "safe")
                     for s in UNKNOWN_SHELLS),
           tool_name, passed[0], command))
    return 2


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

    declared = declared_shell(tool_name)
    known = tool_name in TOOL_SHELL or declared is not None

    if not known and tool_name not in extra_tools():
        # Ни имени в таблице, ни объявленной грамматики: не угадываем.
        return check_unknown_tool(tool_name or "?", command)

    if not known:
        # Имя перечислено в QUOTE_GUARD_TOOLS, но грамматика не задана. Работаем
        # по грамматике ОС, но молча — никогда: это ровно то угадывание, от
        # которого проект отказался.
        shell = platform_default_shell()
        sys.stderr.write(
            "quote-guard: tool '%s' is listed in QUOTE_GUARD_TOOLS, but its grammar\n"
            "  is not declared, so it was guessed from the OS (%s). Add\n"
            "  QUOTE_GUARD_MAP=%s=posix|powershell|cmd to remove the guess.\n"
            % (tool_name, shell, tool_name))
    else:
        shell = declared or pick_shell(tool_name)

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

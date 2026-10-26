#!/usr/bin/env python3
"""
Antigravity PreToolUse Hook for Shell Quote Parity (v3.1)
Author: SkyAngel

Integrates with Google Antigravity PreToolUse hook contract:
  stdin  : JSON {"toolCall": {"name": "run_command", "args": {"CommandLine": "..."}}}
  stdout : JSON {"decision": "allow"} OR {"decision": "deny", "reason": "..."}
  exit 0
"""

import sys
import os
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

LOG_PATH = os.path.join(HERE, "quote_guard.log")
DEBUG_FLAG = os.path.join(HERE, "debug.on")

try:
    from parity_check import analyze
except Exception as e:
    # Fail safe / loud
    out = {
        "decision": "deny",
        "reason": f"Quote Parity Guard initialization error: {e}"
    }
    sys.stdout.write(json.dumps(out))
    sys.exit(0)


TOOL_SHELL = {
    "Bash": "posix",
    "Shell": "posix",
    "Terminal": "powershell" if os.name == "nt" else "posix",
    "PowerShell": "powershell",
    "run_command": "powershell" if os.name == "nt" else "posix",
    "execute_command": "powershell" if os.name == "nt" else "posix",
}

UNKNOWN_SHELLS = ("posix", "powershell")


def is_debug_enabled():
    return os.environ.get("QUOTE_GUARD_DEBUG") == "1" or os.path.exists(DEBUG_FLAG)


def debug(msg):
    if not is_debug_enabled():
        return
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(f"[{ts}] [Antigravity] {msg}\n")
    except OSError:
        pass


def declared_shell(tool_name):
    """Грамматика, объявленная для инструмента через QUOTE_GUARD_MAP."""
    raw = os.environ.get("QUOTE_GUARD_MAP", "")
    for pair in raw.split(","):
        if "=" in pair:
            name, grammar = pair.strip().split("=", 1)
            if name.strip().lower() == tool_name.lower():
                return grammar.strip().lower()
    return None


def extract_command(payload):
    """Извлекает команду и имя инструмента из разных форматов harness."""
    # 1. Antigravity format: toolCall.name & toolCall.args.CommandLine
    tool_call = payload.get("toolCall")
    if isinstance(tool_call, dict):
        name = tool_call.get("name") or "run_command"
        args = tool_call.get("args") or {}
        cmd = args.get("CommandLine") or args.get("command")
        if isinstance(cmd, str):
            return name, cmd

    # 2. Claude Code / Generic format: tool_name & tool_input
    name = payload.get("tool_name") or payload.get("name") or "run_command"
    for container_key in ("tool_input", "args", "arguments", "parameters"):
        container = payload.get(container_key)
        if isinstance(container, dict):
            for field in ("command", "CommandLine", "cmd", "script"):
                val = container.get(field)
                if isinstance(val, str):
                    return name, val

    # 3. Flat payload
    for field in ("CommandLine", "command", "cmd"):
        val = payload.get(field)
        if isinstance(val, str):
            return name, val

    return name, None


def check_unknown_tool(tool_name: str, command: str):
    """
    Строка от инструмента, грамматика которого неизвестна.
    Прогоняется по обеим грамматикам (posix и powershell):
      - обе согласны, что безопасно -> allow
      - обе согласны, что небезопасно -> deny
      - разошлись -> deny с подсказкой QUOTE_GUARD_MAP
    """
    verdicts = {s: analyze(command, shell=s) for s in UNKNOWN_SHELLS}
    failed = [s for s in UNKNOWN_SHELLS if not verdicts[s]["safe"]]

    if not failed:
        debug(f"ok: unknown tool={tool_name}, all grammars agree safe")
        return {"decision": "allow"}

    if len(failed) == len(UNKNOWN_SHELLS):
        first_err = verdicts[failed[0]]
        debug(f"BLOCKED: unknown tool={tool_name}, unsafe in every grammar")
        reason = (
            f"Quote Parity Guard BLOCKED a command that would hang the shell.\n"
            f"  tool:    {tool_name} (grammar unknown, but the string is unsafe in all: {', '.join(UNKNOWN_SHELLS)})\n"
            f"  state:   {first_err.get('state')}\n"
            f"  reason:  {first_err.get('reason')}\n"
            f"  command: {command}\n"
            f"  fix:     Rewrite command to close all quotes/backticks before executing."
        )
        return {"decision": "deny", "reason": reason}

    passed = [s for s in UNKNOWN_SHELLS if s not in failed]
    grammars_summary = ", ".join(f"{s}={'unsafe' if s in failed else 'safe'}" for s in UNKNOWN_SHELLS)
    debug(f"BLOCKED: unknown tool={tool_name}, grammars disagree")
    reason = (
        f"Quote Parity Guard BLOCKED an ambiguous command from an unknown tool.\n"
        f"  tool:      {tool_name}\n"
        f"  grammars:  {grammars_summary}\n"
        f"  reason:    the same string is valid in one shell and hangs in another,\n"
        f"             and this tool's grammar is not declared. Guessing would either\n"
        f"             block a working command or let a hanging one through.\n"
        f"  fix:       declare it once, then this command is judged correctly:\n"
        f"               QUOTE_GUARD_MAP={tool_name}={passed[0]}\n"
        f"             (or QUOTE_GUARD_SHELL for the whole harness)\n"
        f"  command:   {command}"
    )
    return {"decision": "deny", "reason": reason}


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.stdout.write(json.dumps({"decision": "allow"}))
            return 0

        payload = json.loads(raw)
        tool_name, command = extract_command(payload)

        if not command:
            # Not a command-carrying tool (e.g. read_file, edit_file)
            debug(f"skip: tool={tool_name} (no command payload)")
            sys.stdout.write(json.dumps({"decision": "allow"}))
            return 0

        # Shell resolution
        global_override = os.environ.get("QUOTE_GUARD_SHELL")
        declared = declared_shell(tool_name)
        known = tool_name in TOOL_SHELL or declared is not None

        if not global_override and not known:
            decision = check_unknown_tool(tool_name or "?", command)
            sys.stdout.write(json.dumps(decision))
            return 0

        shell = global_override or declared or TOOL_SHELL.get(tool_name, "powershell" if os.name == "nt" else "posix")

        result = analyze(command, shell=shell)

        if result["safe"]:
            debug(f"ok: tool={tool_name} shell={shell} cmd={command[:60]!r}")
            sys.stdout.write(json.dumps({"decision": "allow"}))
            return 0
        else:
            reason = (
                f"Quote Parity Guard BLOCKED execution: Unclosed quote detected.\n"
                f"State: {result['state']} | Reason: {result['reason']}\n"
                f"Command: {command}\n"
                f"Fix: Rewrite command to close all quotes/backticks before executing."
            )
            debug(f"BLOCKED: tool={tool_name} shell={shell} state={result['state']} reason={result['reason']} cmd={command[:60]!r}")
            out = {
                "decision": "deny",
                "reason": reason
            }
            sys.stdout.write(json.dumps(out))
            return 0

    except Exception as exc:
        debug(f"ERROR: {exc}")
        out = {
            "decision": "deny",
            "reason": f"Quote Parity Guard runtime error: {exc}"
        }
        sys.stdout.write(json.dumps(out))
        return 0


if __name__ == "__main__":
    sys.exit(main())

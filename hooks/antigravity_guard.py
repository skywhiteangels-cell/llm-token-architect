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
sys.path.insert(0, REPO_ROOT)
LOG_PATH = os.path.join(HERE, "quote_guard.log")
DEBUG_FLAG = os.path.join(HERE, "debug.on")

try:
    from parity_check import analyze
except Exception as e:
    # Fail safe/loud
    out = {
        "decision": "deny",
        "reason": f"Quote Parity Guard initialization error: {e}"
    }
    sys.stdout.write(json.dumps(out))
    sys.exit(0)


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


def has_heredoc(command: str) -> bool:
    """
    True when the command feeds a heredoc (e.g. cat <<'EOF').
    Heredoc body quotes cannot hang the shell.
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
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.stdout.write(json.dumps({"decision": "allow"}))
            return 0

        payload = json.loads(raw)
        
        # Antigravity format: toolCall.name & toolCall.args.CommandLine
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name") or payload.get("tool_name", "run_command")
        args = tool_call.get("args", {})
        
        command = args.get("CommandLine") or args.get("command") or payload.get("command")
        
        if not command or not isinstance(command, str):
            sys.stdout.write(json.dumps({"decision": "allow"}))
            return 0

        # Skip heredocs (known limitation, verbatim payload)
        if has_heredoc(command):
            debug(f"ok (heredoc): tool={tool_name} cmd={command[:60]!r}")
            sys.stdout.write(json.dumps({"decision": "allow"}))
            return 0

        # Grammar determination: override -> tool mapping -> OS default (PowerShell on Windows for Antigravity)
        shell = os.environ.get("QUOTE_GUARD_SHELL")
        if not shell:
            # Check QUOTE_GUARD_MAP
            override_map = os.environ.get("QUOTE_GUARD_MAP", "")
            for item in override_map.split(","):
                if "=" in item:
                    k, v = item.strip().split("=", 1)
                    if k.strip().lower() == tool_name.lower():
                        shell = v.strip().lower()
                        break

        if not shell:
            # Default for Antigravity on Windows is powershell
            shell = "powershell" if os.name == "nt" else "posix"

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

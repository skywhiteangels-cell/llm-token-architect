#!/usr/bin/env python3
"""
Antigravity PreToolUse Hook for Shell Quote Parity
Author: SkyAngel
"""

import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, REPO_ROOT)

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

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.stdout.write(json.dumps({"decision": "allow"}))
            return 0

        payload = json.loads(raw)
        
        # Antigravity format: toolCall.name & toolCall.args.CommandLine
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})
        
        # Also support legacy / other harnesses
        command = args.get("CommandLine") or args.get("command") or payload.get("command")
        
        if not command or not isinstance(command, str):
            sys.stdout.write(json.dumps({"decision": "allow"}))
            return 0

        # Shell on Windows is PowerShell
        shell = "powershell" if os.name == "nt" else "posix"
        result = analyze(command, shell=shell)

        if result["safe"]:
            sys.stdout.write(json.dumps({"decision": "allow"}))
            return 0
        else:
            reason = (
                f"Quote Parity Guard BLOCKED execution: Unclosed quote detected.\n"
                f"State: {result['state']} | Reason: {result['reason']}\n"
                f"Command: {command}\n"
                f"Fix: Rewrite command to close all quotes/backticks before executing."
            )
            out = {
                "decision": "deny",
                "reason": reason
            }
            sys.stdout.write(json.dumps(out))
            return 0
    except Exception as exc:
        # In case of exception, report deny
        out = {
            "decision": "deny",
            "reason": f"Quote Parity Guard runtime error: {exc}"
        }
        sys.stdout.write(json.dumps(out))
        return 0

if __name__ == "__main__":
    sys.exit(main())

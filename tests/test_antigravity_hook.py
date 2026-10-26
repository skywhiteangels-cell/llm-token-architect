"""Тесты хука Antigravity (antigravity_guard.py).

Контракт: stdin — JSON, stdout — JSON {"decision": "allow" | "deny"}.
Exit code — всегда 0.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HOOK = os.path.join(ROOT, "hooks", "antigravity_guard.py")

CASES = []


def case(payload, want_decision, why, env=None):
    CASES.append((payload, want_decision, why, env or {}))


# --- Antigravity toolCall payload format ---
case({"toolCall": {"name": "run_command", "args": {"CommandLine": 'echo "hello"'}}},
     "allow", "run_command: сбалансированная строка")

case({"toolCall": {"name": "run_command", "args": {"CommandLine": 'dir "C:\\"'}}},
     "allow", "run_command: PowerShell путь C:\\ валиден")

case({"toolCall": {"name": "run_command", "args": {"CommandLine": 'echo "unclosed'}}},
     "deny", "run_command: незакрытая двойная кавычка")

case({"toolCall": {"name": "run_command", "args": {"CommandLine": "echo 'unclosed"}}},
     "deny", "run_command: незакрытая одинарная кавычка")

# --- Heredocs (masked by parity_check v3.1) ---
case({"toolCall": {"name": "run_command", "args": {"CommandLine": 'cat <<EOF\n"unclosed inside heredoc\nEOF'}}},
     "allow", "Heredoc: тело маскируется, кавычка внутри безопасна",
     {"QUOTE_GUARD_SHELL": "posix"})

case({"toolCall": {"name": "run_command", "args": {"CommandLine": 'cat <<EOF\nno end'}}},
     "deny", "Heredoc: незакрытый разделитель блокируется как HEREDOC",
     {"QUOTE_GUARD_SHELL": "posix"})

# --- Unknown tool (Strict Intersect) ---
case({"toolCall": {"name": "CustomTool", "args": {"CommandLine": 'echo "hi"'}}},
     "allow", "Unknown tool: обе грамматики согласны (safe)")

case({"toolCall": {"name": "CustomTool", "args": {"CommandLine": 'echo "unclosed'}}},
     "deny", "Unknown tool: обе грамматики согласны (unsafe)")

case({"toolCall": {"name": "CustomTool", "args": {"CommandLine": 'dir "C:\\"'}}},
     "deny", "Unknown tool: грамматики разошлись -> deny")

case({"toolCall": {"name": "CustomTool", "args": {"CommandLine": 'dir "C:\\"'}}},
     "allow", "Unknown tool + QUOTE_GUARD_MAP -> allow",
     {"QUOTE_GUARD_MAP": "CustomTool=powershell"})

# --- Non-command tool calls ---
case({"toolCall": {"name": "read_file", "args": {"Path": "C:/file.txt"}}},
     "allow", "Инструмент без команды (read_file) -> allow")

case({}, "allow", "Пустой JSON -> allow")


def run():
    passed = 0
    for payload, want_decision, why, env_extra in CASES:
        env = dict(os.environ)
        for k in ("QUOTE_GUARD_SHELL", "QUOTE_GUARD_MAP", "QUOTE_GUARD_DEBUG"):
            env.pop(k, None)
        env.update(env_extra)
        env["PYTHONIOENCODING"] = "utf-8"

        p = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            env=env
        )

        assert p.returncode == 0, f"Expected RC 0, got {p.returncode}: {p.stderr}"
        out = json.loads(p.stdout)
        decision = out.get("decision")
        if decision == want_decision:
            passed += 1
            print(f"OK   decision={decision:5}  {why}")
        else:
            print(f"FAIL want={want_decision} got={decision}: {why}")
            print("  STDOUT:", p.stdout)
            print("  STDERR:", p.stderr)
            sys.exit(1)

    print(f"\n=== ALL PASS: {passed} antigravity hook checks ===")


if __name__ == "__main__":
    run()

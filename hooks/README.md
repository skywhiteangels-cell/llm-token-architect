# Wiring the guardrail into a harness

A CLI you must remember to call is still probabilistic luck. The article argues
that the check has to be **structural** — so here is the structural version: the
harness runs the check itself, before the shell ever sees the command.

`pre_tool_use_guard.py` is a `PreToolUse` hook. It reads the tool payload from
stdin, extracts the command string, runs the v3 state machine with the correct
shell grammar, and **exits 2 to block** when the command would hang.

## Claude Code

`~/.claude/settings.json` (or `.claude/settings.json` in your project root):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/llm-token-architect/hooks/pre_tool_use_guard.py"
          }
        ]
      }
    ]
  }
}
```

> **Important for Claude Code on Windows:**  
> Claude Code's `Bash` tool on Windows runs inside **Git Bash** (POSIX grammar), not PowerShell.  
> Therefore, set the environment variable `QUOTE_GUARD_SHELL=posix` (or configure it in your environment) so the hook evaluates commands using POSIX escaping rules rather than native PowerShell rules.

`matcher` accepts a tool-name pattern (`Bash`, `Bash|Shell`, `*`). The hook
itself also filters by name, so `*` is safe.

## Google Antigravity

In your workspace root `.agents/hooks.json` (or globally in `~/.gemini/config/hooks.json`):

```json
{
  "quote-parity-guard": {
    "PreToolUse": [
      {
        "matcher": "run_command",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/llm-token-architect/hooks/antigravity_guard.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Antigravity Contract
Antigravity uses JSON on both stdin and stdout:
- **Input (stdin):** `{"toolCall": {"name": "run_command", "args": {"CommandLine": "..."}}}`
- **Output (stdout):** `{"decision": "allow"}` to proceed, or `{"decision": "deny", "reason": "..."}` to hard-block execution.

`antigravity_guard.py` translates tool calls, invokes `parity_check.py` with the appropriate shell grammar (PowerShell on Windows, POSIX on Unix), and returns a structured decision.

## Contract (Claude Code & Standard Harnesses)

| Channel | Meaning |
|---|---|
| stdin | `{"tool_name": "Bash", "tool_input": {"command": "..."}}` |
| exit 0 | allow |
| exit 2 | block, stderr is returned to the model as the reason |

Exit code 2 is not decoration: most harnesses treat a hook **crash** (exit 1) as
"hook failed, continue anyway". A guardrail that fails open is a decoration.

## Choosing the shell grammar

The hook cannot know which shell your agent actually uses — and getting it wrong
in either direction is bad:

* `posix` grammar on PowerShell → false blocks on `dir "C:\"`
* `powershell` grammar on bash → misses `dir "C:\"`, which really does hang bash

So it defaults to `powershell` on Windows and `posix` everywhere else. Override
it explicitly when you know better:

```bash
export QUOTE_GUARD_SHELL=posix      # agent runs Git Bash on Windows (e.g. Claude Code)
export QUOTE_GUARD_SHELL=powershell # agent runs PowerShell on Windows
```

Or pass `--shell <name>` if invoking the CLI directly.

## Other harnesses

Adapt in two places:

1. `SHELL_TOOLS` — the set of tool names that carry a shell command.
2. `extract_command()` — where the command string lives in your payload
   (`tool_input.command`, `input.cmd`, a bare string, ...).

The guard itself (`parity_check.analyze`) does not care about the harness.

## Not a hook person?

Wrap the CLI directly:

```bash
python parity_check.py -c "$CMD" --shell posix || exit 1
eval "$CMD"
```

Same protection, one more line to forget.

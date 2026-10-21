# Wiring the guardrail into a harness

A CLI you must remember to call is still probabilistic luck. The article argues
that the check has to be **structural** — so here is the structural version: the
harness runs the check itself, before the shell ever sees the command.

`pre_tool_use_guard.py` is a `PreToolUse` hook. It reads the tool payload from
stdin, extracts the command string, runs the v3 state machine with the correct
shell grammar, and **exits 2 to block** when the command would hang.

## Claude Code

`~/.claude/settings.json` (or `.claude/settings.json` in the project):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python /absolute/path/to/github_repo_v3/hooks/pre_tool_use_guard.py"
          }
        ]
      }
    ]
  }
}
```

`matcher` accepts a tool-name pattern (`Bash`, `Bash|Shell`, `*`). The hook
itself also filters by name, so `*` is safe.

## Contract

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
export QUOTE_GUARD_SHELL=posix      # agent runs Git Bash on Windows
export QUOTE_GUARD_SHELL=powershell # agent runs PowerShell on Windows
```

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

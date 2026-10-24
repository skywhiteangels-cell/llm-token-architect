# Wiring the guardrail into a harness

A CLI you must remember to call is still probabilistic luck. The article argues
that the check has to be **structural** — so here is the structural version: the
harness runs the check itself, before the shell ever sees the command.

`pre_tool_use_guard.py` and `antigravity_guard.py` are `PreToolUse` hooks that
intercept commands, run the v3 state machine with the correct shell grammar, and
block execution when a command would hang.

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

## WorkBuddy AI

Config: `~/.workbuddy-ai/settings.json` — a `hooks` key at the top level:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|PowerShell|Shell|Terminal|run_command|execute_command",
        "hooks": [
          {
            "type": "command",
            "command": "\"C:\\Users\\<you>\\AppData\\Local\\Programs\\Python\\Python313\\python.exe\" \"C:\\Users\\<you>\\.workbuddy-ai\\hooks\\quote_guard.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Copy `pre_tool_use_guard.py` → `~/.workbuddy-ai/hooks/quote_guard.py` and
`parity_check.py` → `~/.workbuddy-ai/hooks/parity_check.py` (the hook imports the
module from its own directory first). Hooks are read at session start — restart
the app for changes to take effect.

Use an absolute path to a Python that will still exist after an update. The
managed interpreter under `binaries/python/versions/<x.y.z>/` changes with
versions; a system Python does not.

## Claude Code

Same schema, `~/.claude/settings.json` or `.claude/settings.json` in a project root:

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

## Contract (Claude Code & Standard Harnesses)

| Channel | Meaning |
|---|---|
| stdin | `{"tool_name": "Bash", "tool_input": {"command": "..."}}` |
| exit 0 | allow |
| exit 2 | block, stderr is returned to the model as the reason |

Exit code 2 is not decoration: most harnesses treat a hook **crash** (exit 1) as
"hook failed, continue anyway". A guardrail that fails open is a decoration.

## The grammar follows the tool, not the OS

This is the part that decides whether the hook survives a week.

In WorkBuddy on Windows the `Bash` tool runs Git Bash (POSIX grammar) while
`PowerShell` is a **separate tool**. Guessing the grammar from the operating
system would apply POSIX rules to PowerShell — and block `dir "C:\"`, which is
perfectly valid there.

So the hook maps tool → grammar:

| Tool | Grammar |
|---|---|
| `Bash`, `Shell`, `Terminal`, `run_command`, `execute_command` | `posix` |
| `PowerShell`, `pwsh` | `powershell` |
| `cmd`, `CMD` | `cmd` |
| anything else carrying a `command` string | **double-checked**, see below |

Override everything with `QUOTE_GUARD_SHELL=posix|powershell|cmd`.

Declare the grammar of a custom tool with:

```
QUOTE_GUARD_MAP="MyTool=posix,OtherTool=powershell"
```

## Unknown tools: double check, then ask

A tool name that is not in the table carries no information about its grammar.
Guessing from the operating system is exactly the mistake v2 made, so for an
unknown tool the command is run through **both** POSIX and PowerShell grammars:

| POSIX | PowerShell | Result |
|---|---|---|
| safe | safe | allow |
| unsafe | unsafe | block — the string hangs in any shell |
| safe | unsafe, or the reverse | **block, and ask you to declare the grammar** |

The third row cannot be resolved by inspection, and that is not a bug in the
checker. `echo "a`"b"` (a hang in POSIX, a balanced string in PowerShell) and
`dir "C:\"` (a working command in PowerShell, a hang in POSIX) produce the
**same** pair of verdicts. One string is the attack, the other is the command
v3 exists to stop blocking. No rule over the string alone can tell them apart —
only knowing which shell will execute it can.

So the guard does not guess: it blocks the ambiguous case once and prints the
exact line that resolves it, `QUOTE_GUARD_MAP=<tool>=<grammar>`. After that the
command is judged by its real grammar and passes if it is valid there.

The cost is deliberate and worth naming: a brand-new tool running a
valid-in-one-shell command is blocked until declared. That is one line of
configuration per tool, once, in exchange for never silently applying the wrong
grammar.

`QUOTE_GUARD_TOOLS=name1,name2` still exists for back-compatibility. It marks a
name as known but does **not** declare a grammar, so the hook falls back to the
OS default and says so on stderr — it never guesses silently.

## Two deliberate safety valves

**Unknown tools are still checked.** If a tool name is not in the table but the
payload carries a `command` string, the hook checks it anyway. A silent no-op
because of an unexpected tool name would *look* like protection while providing
none.

**Heredocs are skipped.** A heredoc body is read verbatim until its delimiter, so
quotes inside it cannot hang the shell — but they can look unbalanced to a
line-level lexer. Blocking `cat <<'EOF' ... EOF` would be a false positive on a
very common pattern. The guard reports this as a known limitation instead of
pretending to cover it.

## Is it actually firing?

```bash
touch ~/.workbuddy-ai/hooks/debug.on
```

appends one line per decision to `quote_guard.log` next to the hook: `ok`,
`blocked`, `skip: heredoc`, `note: unknown tool ...`. Restart, run a few commands,
read the log. "The hook is installed" and "the hook is running" are different
claims, and only one of them is testable.

Why a flag file and not `export QUOTE_GUARD_DEBUG=1`: **setting an environment
variable in a terminal does not reach the hook.** The hook is spawned by the
application, so it inherits the application's environment, not your shell's. The
flag file is read on every invocation, so it needs no restart and no environment
plumbing. The env var still works if you set it at the OS level and restart the
app.

## Other harnesses

Adapt in two places: `TOOL_SHELL` (names → grammar) and `extract_command()`
(where the command string lives in your payload). The guard itself
(`parity_check.analyze`) does not care about the harness.

## Not a hook person?

Wrap the CLI directly:

```bash
python parity_check.py -c "$CMD" --shell posix || exit 1
eval "$CMD"
```

Same protection, one more line to forget.

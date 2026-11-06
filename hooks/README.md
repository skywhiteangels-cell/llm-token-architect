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

Verify: `python tests/test_antigravity_hook.py` (12 checks). A 101-byte file that
only calls `sys.exit(0)` is a stub, not a hook; it produces no JSON and fails the
first check.

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
versions; a system Python does not. Replace `<you>` and `Python313` in the
example with your actual user path and Python version.

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

If your harness exposes a `PowerShell` tool, add it to `matcher` — otherwise the
hook never sees those commands.

## Contract (Claude Code & Standard Harnesses)

| Channel | Meaning |
|---|---|
| stdin | `{"tool_name": "Bash", "tool_input": {"command": "..."}}` |
| exit 0 | allow |
| exit 2 | block, stderr is returned to the model as the reason |

Exit code 2 is not decoration: most harnesses treat a hook **crash** (exit 1) as
"hook failed, continue anyway". A guardrail that fails open is a decoration.

The hook also exits 2 when it cannot run at all (missing `parity_check.py`,
unparsable payload). That is fail-closed, not a verdict on the command: read
stderr, fix the hook, and do not rewrite a command that was never judged.

## The grammar follows the tool, not the OS

This is the part that decides whether the hook survives a week.

In WorkBuddy on Windows the `Bash` tool runs Git Bash (POSIX grammar) while
`PowerShell` is a **separate tool**. Guessing the grammar from the operating
system would apply POSIX rules to PowerShell — and block `dir "C:\"`, which is
perfectly valid there.

So the hook maps tool → grammar:

| Tool | Grammar |
|---|---|
| `Bash`, `Shell`, `Terminal`, `sh`, `bash`, `run_command`, `execute_command` | `posix` |
| `PowerShell`, `powershell`, `pwsh` | `powershell` |
| `cmd`, `CMD` | `cmd` |
| anything else carrying a `command` string | **double-checked**, see below |

Override everything with `QUOTE_GUARD_SHELL=posix|powershell|cmd`. Use the
override only when the whole harness really runs one grammar. Setting it to make
a particular command pass is the bypass this repo exists to prevent.

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
grammar. When the double check blocks a valid command, record it in
[guard_false_positives.md](../guard_false_positives.md) — do not disable the
guard.

`QUOTE_GUARD_TOOLS=name1,name2` still exists for back-compatibility. It marks a
name as known but does **not** declare a grammar, so the hook falls back to the
OS default and says so on stderr — it never guesses silently.

## One safety valve, one modelled case

**Unknown tools are still checked.** If a tool name is not in the table but the
payload carries a `command` string, the hook checks it anyway. A silent no-op
because of an unexpected tool name would *look* like protection while providing
none.

**Heredocs are masked, not skipped.** A heredoc body is read verbatim until its
delimiter, so quotes inside it cannot hang the shell — but they look unbalanced
to a line-level lexer. The lexer blanks the body (keeping length and newlines)
and checks what actually executes. An unterminated heredoc is itself a hang and
is blocked as `state=HEREDOC`. This replaced the old skip-whole-command
behaviour, which was fail-open: an unbalanced quote *after* the terminator went
through unnoticed.

## Is it actually firing?

```bash
touch ~/.workbuddy-ai/hooks/debug.on
```

appends one line per decision to `quote_guard.log` next to the hook: `ok`,
`blocked`, `note: unknown tool ...`, `skip: empty payload` / `skip: ... no
command field`. A `skip: heredoc` line means the installed hook predates
v3.1.2 — upgrade it. Restart, run a few commands, read the log. "The hook is
installed" and "the hook is running" are different claims, and only one of them
is testable.

Why a flag file and not `export QUOTE_GUARD_DEBUG=1`: **setting an environment
variable in a terminal does not reach the hook.** The hook is spawned by the
application, so it inherits the application's environment, not your shell's. The
flag file is read on every invocation, so it needs no restart and no environment
plumbing. The env var still works if you set it at the OS level and restart the
app.

## Other harnesses

Adapt in two places: `TOOL_SHELL` (names → grammar) and `extract_command()`
(where the command string lives in your payload). A third place matters if the
harness can run `cmd`: add it to `UNKNOWN_SHELLS`, because the unknown-tool
double check covers only POSIX and PowerShell. The guard itself
(`parity_check.analyze`) does not care about the harness.

## Not a hook person?

Wrap the CLI directly:

```bash
python parity_check.py -c "$CMD" --shell posix || exit 1
eval "$CMD"
```

Same check, more to forget — and only for the literal string. This snippet is
bash/Git Bash: it hardcodes `--shell posix`, and `eval "$CMD"` is POSIX. For
PowerShell, use `--shell powershell` and `Invoke-Expression $CMD`; the equivalent
of `|| exit 1` is `if ($LASTEXITCODE -ne 0) { exit 1 }`. Otherwise you are
checking one grammar and executing with another. It does not see through
`eval`, `Invoke-Expression`, `-EncodedCommand`, or a nested shell.

`|| exit 1` stops on any non-zero: UNSAFE, a guard crash, or a usage error. It
does not distinguish them. That is fail-closed, not diagnostic: for a voluntary
pre-flight, not executing is safer than executing something that was never
judged — but you will not know which case you hit.

# Quote Guard — a pre-flight check that stops an agent from hanging its own shell

> 📖 **Read the full experimental trilogy (1,416 canonical probes):** [The Ghost in the Context Window (PDF)](The_Ghost_in_the_Context_Window_Trilogy.pdf)

**🇬🇧 English** | [ 🇷🇺 Читать на русском ](README_RU.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/skywhiteangels-cell/llm-token-architect/actions/workflows/tests.yml/badge.svg)](https://github.com/skywhiteangels-cell/llm-token-architect/actions)
[![Tests](https://img.shields.io/badge/tests-134%20passing-brightgreen)](#tests)
[![Read in Russian](https://img.shields.io/badge/Read_in-Russian-blue.svg)](README_RU.md)

![Cover](habr_cover.jpg)

An autonomous agent loses a closing quote. The command goes to PowerShell with an
odd number of `"`. The shell decides the user is still typing, prints `>>`, and
waits forever. There is no stderr to read, no exit code to self-correct from —
the agentic loop is simply dead, and the session has to be restarted by hand.

This repository is a **deterministic pre-flight check** for exactly that failure:
it reads a command string, walks it as a shell lexer would, and refuses to run it
if the lexer ends still inside a quote, backtick, or line-continuation escape.

Two files, no dependencies, one exit code.

## Quick start

```bash
# CLI
python parity_check.py -c 'echo "hi' --shell posix
# -> PARITY VIOLATION — unterminated double context opened at offset 5
#    exit code 1

node parity_check.js -c 'echo hi' --shell powershell
# -> PARITY OK — command is safe to execute.   exit code 0
```

```python
from parity_check import verify_quote_parity, analyze

verify_quote_parity('echo "it\'s a test"', shell="posix")   # True  — valid, not a false positive
verify_quote_parity('dir "C:\\"',          shell="posix")   # False — bash: \ escapes the quote
verify_quote_parity('dir "C:\\"',          shell="powershell")  # True — PS: \ is literal

analyze('echo "hi', shell="posix")
# {'safe': False, 'state': 'DOUBLE', 'shell': 'posix',
#  'reason': 'unterminated double context opened at offset 5', 'offset': 5}
```

```javascript
const { verifyQuoteParity, analyze } = require('./parity_check');
verifyQuoteParity('echo "hi', 'powershell');   // false
```

Exit codes: `0` safe · `1` would hang · `2` usage error.

## The shell grammar is not optional

This is the part most guards get wrong, and it is the reason this repo exists in
three shells rather than one.

| Shell | Escape char | Quoting | Consequence |
|---|---|---|---|
| `posix` (bash, sh, zsh, Git Bash) | `\` | `'...'`, `"..."`, `` `...` `` | `dir "C:\"` **hangs** — the `\` escapes the quote |
| `powershell` (5.1 / 7+) | `` ` `` | `'...'` literal, `''` and `""` double to a literal | `dir "C:\"` is **valid** — `\` is literal |
| `cmd` (cmd.exe) | `^` | `"..."` only | `echo ^"hi` is valid |

The same string has different verdicts under different grammars. That is not a
bug, it is the whole point — a check that applies POSIX rules on Windows blocks
working commands, and a guard that blocks working commands gets switched off.

Default is `posix`. On Windows PowerShell pass `--shell powershell` explicitly.

## What it catches

- unterminated `"` and `'` in any of the three grammars
- unterminated backtick command substitution (POSIX)
- dangling escape at end-of-string — trailing `\`, `` ` `` or `^`, which are
  line continuations and hang the shell just as reliably as an open quote
- the `echo "it's a test"` false positive that naive parity counting produces
- PowerShell `''` / `""` doubled-literal quoting, so real strings are not flagged

## What it does not catch (honest limits)

| Not modelled | Why it is acceptable |
|---|---|
| heredoc **inside** `$(...)` or other nesting | nested grammar; the body masker works on the top level only |
| POSIX `$'...'` ANSI-C quoting | rare in generated commands |
| PowerShell `$(...)` inside `"..."` | nested grammar; not worth the complexity |
| nested command substitution | same |
| a **balanced** command that still hangs | different problem class (e.g. `Read-Host`) |
| cmd.exe unclosed quotes (`echo "hi`) | cmd.exe prints without hanging (only trailing `^` hangs); flagged conservatively as malformed |

Heredoc **bodies** are no longer a blind spot: the body is masked before lexing,
because the shell reads it verbatim and quotes inside it open nothing. An
unterminated heredoc is itself a hang — the shell waits for the delimiter — and
is blocked. The old behaviour (skip the whole command) was fail-open: a broken
quote *after* the terminator went through unnoticed.

This is a guardrail, not a shell parser. It is deliberately conservative about
*not hanging*, and it makes no claim of catching every possible hang. What it
does claim: it never blocks a command that is valid **in the grammar you
selected**, and it always catches the one failure that silently kills an agent
session — an open context at end-of-string.

## Make it structural, not voluntary

A CLI the agent has to remember is still probabilistic luck. `hooks/` contains a
`PreToolUse` hook that makes the check unavoidable:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "python /path/to/hooks/pre_tool_use_guard.py" }]
    }]
  }
}
```

Exit 2 blocks the tool call and hands the reason back to the model. See
[hooks/README.md](hooks/README.md) for other harnesses.

## Files

| File | Purpose |
|---|---|
| [parity_check.py](parity_check.py) | Python guard — `analyze()` / `verify_quote_parity()`, CLI, `--selftest` |
| [parity_check.js](parity_check.js) | Node guard — same state machine, same heredoc masking, same case fixture |
| [hooks/pre_tool_use_guard.py](hooks/pre_tool_use_guard.py) | PreToolUse hook: blocks hanging commands before execution |
| [hooks/README.md](hooks/README.md) | Wiring for Claude Code and other harnesses |
| [tests/test_parity.py](tests/test_parity.py) · [tests/test_parity.js](tests/test_parity.js) | External suites (46 / 46 checks over one shared fixture), no dependencies |
| [tests/fixtures/cases.jsonl](tests/fixtures/cases.jsonl) | The single case table both suites read — divergence cannot go unnoticed |
| [REQUESTS.md](REQUESTS.md) | Audit trail: what was requested, what was accepted, and the reproduction that decided it |
| [MASTER_PROMPT.md](MASTER_PROMPT.md) | Full session bootstrap for an autonomous agent harness |
| [MASTER_PROMPT_LITE.md](MASTER_PROMPT_LITE.md) | ~300-word drop-in system prompt |
| [ARTICLE.md](ARTICLE.md) · [ARTICLE_RU.md](ARTICLE_RU.md) | The essay: parables, BPE subword blindness, the "Token Architect" method, and why frontier models still break on the first meter |
| [WHY_RU.md](WHY_RU.md) | Why every file is built the way it is — the decision log (Russian) |

## Tests

```bash
python tests/test_parity.py                       # 46 checks across 31 grammar cases
node   tests/test_parity.js                       # 46 checks across 31 grammar cases
python tests/test_hook.py                         # 25 checks
python tests/test_antigravity_hook.py             # 12 checks
python tools/check_duplicate_blocks.py --selftest # 5 checks
```

Both parity suites read the same fixture — [tests/fixtures/cases.jsonl](tests/fixtures/cases.jsonl) —
so the two counters are equal by construction: 46 + 46 + 25 + 12 + 5 = **134**,
and that is the number on the badge. There is no separate numbers file to trust:
each runner prints its own count, and if a count stops matching, the runner is
what changed.

The built-in `--selftest` (23 cases each) is not counted — it checks that the guard
answers at all, not the grammar table.

No pytest, no npm install. Exit code 0 or it is broken.

## The idea behind it

The essay in [ARTICLE.md](ARTICLE.md) argues for what it calls the **Topology of
Inevitability**: design the environment so an invalid state is structurally
impossible, instead of training the model to be less likely to reach it. Punitive
RLHF cannot fix an architectural blindness. A three-line deterministic check in
front of the shell can.

The tool in this repo is the smallest possible instance of that idea.

## License

MIT — see [LICENSE](LICENSE).

*Practitioner from Kenshi — SkyAngel*

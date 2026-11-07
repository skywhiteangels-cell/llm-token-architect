# Tests

Five suites, no pytest, no `npm install`. Each runner prints its own count; if a
count stops matching this page, the runner is what changed.

```bash
python tests/test_parity.py                       # 46 checks across 31 grammar cases
node   tests/test_parity.js                       # 46 checks across 31 grammar cases
python tests/test_hook.py                         # 25 checks
python tests/test_antigravity_hook.py             # 12 checks
python tools/check_duplicate_blocks.py --selftest # 5 checks
```

Badge number: **134** = 46 + 46 + 25 + 12 + 5. Both parity suites read the same
fixture ([tests/fixtures/cases.jsonl](tests/fixtures/cases.jsonl)), so their two
counters are equal by construction, not by coincidence.

Two more numbers exist that are **not** in the badge — see
[Self-test is not a score](#self-test-is-not-a-score).

## What each suite actually counts

| Suite | Count | Unit |
|---|---|---|
| `test_parity.py` / `.js` | 46 | 31 fixture cases, one assertion each, plus 15 assertions on the API contract: state names and offsets from `analyze()`, defensive input (`None`, empty string, unknown shell), the `SHELLS` tuple, and idempotence over 50 runs. 31 + 15 = 46. |
| `test_hook.py` | 25 | one payload per case — both shells, unknown tool, heredoc, here-string, tool without a command — plus contract checks on exit code and on the stderr hint. |
| `test_antigravity_hook.py` | 12 | one payload, one expected decision. Enumerated below. |
| `check_duplicate_blocks.py --selftest` | 5 | one assertion per property of the checker itself (see below). |

## The twelve antigravity cases

Contract: stdin is JSON, stdout is `{"decision": "allow" | "deny"}`, exit code is
always 0 — the decision travels in the body, not in the status.

| # | Payload (`toolCall.args.CommandLine`) | Env | Expected | Why |
|---|---|---|---|---|
| 1 | `echo "hello"` | — | allow | balanced string, nothing to block |
| 2 | `dir "C:\"` | — | allow | in PowerShell the backslash is a path separator, not an escape: the string is balanced. Blocking it is the false positive this guard was built to avoid |
| 3 | `echo "unclosed` | — | deny | unbalanced double quote |
| 4 | `echo 'unclosed` | — | deny | unbalanced single quote |
| 5 | `cat <<EOF` + body with `"unclosed` + `EOF` | `QUOTE_GUARD_SHELL=posix` | allow | the heredoc body is masked: a quote inside it is data, not syntax |
| 6 | `cat <<EOF` + body without `EOF` | `QUOTE_GUARD_SHELL=posix` | deny | the delimiter never closes; blocked as HEREDOC |
| 7 | `echo "hi"` (tool `CustomTool`) | — | allow | unknown tool, both grammars agree: safe |
| 8 | `echo "unclosed` (tool `CustomTool`) | — | deny | unknown tool, both grammars agree: unsafe |
| 9 | `dir "C:\"` (tool `CustomTool`) | — | deny | unknown tool, grammars disagree → strict intersect denies |
| 10 | `dir "C:\"` (tool `CustomTool`) | `QUOTE_GUARD_MAP=CustomTool=powershell` | allow | the same payload as #9, resolved: declaring the grammar removes the disagreement. Without this case the rule would read "unknown tools always deny", which is not the rule |
| 11 | tool `read_file`, arg `Path` | — | allow | no command string, nothing to parse |
| 12 | `{}` | — | allow | valid JSON, no tool call |

Cases 9 and 10 are deliberately the same payload: they differ only in the
environment, and together they show that the strict intersect is a default, not a
wall.

## Self-test is not a score

Two different questions get confused whenever a number is quoted without its
label:

| Question | Tool | Number |
|---|---|---|
| Does the checker work at all? | `parity_check.py --selftest` | 23 cases per implementation, 23 ×2 = 46 |
| Does the guard handle the grammar table? | `tests/test_parity.py` | 46 assertions over 31 cases |
| Does the duplicate checker work at all? | `check_duplicate_blocks.py --selftest` | 5 checks |
| Are there duplicates in this repository? | `check_duplicate_blocks.py .` | files read, then duplicates found |

The last row is the one that keeps getting misquoted. The run prints
`файлов проверено: 12` and `ALL PASS: повторов нет`. Neither of those is "5/5":
five is how many assertions the checker makes about itself. A clean scan means
zero duplicates across the documents it read — it says nothing about how good the
checker is, and the selftest says nothing about the repository.

Same with the guard: 23 is "the guard answers at all", 46 is "the guard answers
correctly on the fixture". Adding them together would count one property twice.

## Not covered

- **Unparsable input.** The hook denies it (`{"decision": "deny", "reason":
  "Quote Parity Guard runtime error: ..."}`), but no case in the twelve feeds
  broken JSON — the deny path exists and is untested.
- **Real shell execution.** Every case is a string handed to the parser. Nothing
  here runs `cmd.exe`, `bash` or PowerShell, so a construct that parses as
  balanced but behaves otherwise is invisible to this suite.
- **The hook inside Antigravity itself.** The tests invoke
  `hooks/antigravity_guard.py` directly. Whether the host passes the payload in
  this shape is verified manually, per `MASTER_PROMPT.md` Part 3, not here.
- **Windows line endings and codepage.** `cmd.exe` reads batch files in the OEM
  codepage; that class of failure lives outside the guard and has no test.

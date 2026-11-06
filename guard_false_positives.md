# Guard false positives

Append-only record of cases where the guard's verdict was wrong or ambiguous.
This is not a log of every block — that is `quote_guard.log`. A correct block
is not a false positive; do not record it here.

Do not delete or rewrite entries. New entries go at the bottom. The verdict and
evidence are immutable; the `Resolution` field is the only mutable field —
update it in place, do not add a second `Resolution` line.

## Scope

Record only cases where the guard's model is wrong for the grammar it was given,
or where the model is incomplete for a construct the shell actually accepts.
A wrong `--shell` is a caller error, not a guard false positive: fix the flag
and do not record it here. If the guard is right and the command is genuinely
unsafe, rewrite the command or escalate — do not file it here.

## Entry template

### YYYY-MM-DD HH:MM — hook|cli — classification

- Command:
  ```
  <exact command>
  ```
- Grammar: `posix` | `powershell` | `cmd`
- Verdicts: `<grammar>` = `<state>` @ `<offset>`; `<grammar>` = `<state>` @ `<offset>`
  (use `—` for a null offset; list both grammars for AMBIGUOUS)
- Message: `<exact header>`
- Guard version: lexer `parity_check.py` `<sha256>`; hook `<hook filename>` `<sha256>`; git `<short rev>`
- Classification: `guard bug` | `unsupported construct`
- Why safe: `<the check you ran: state/offset, shell parser, minimal reproduction>`
- Resolution: `open` — update in place to `fixed in guard` | `declared grammar` | `rewritten command` | `accepted limitation`

## Classification

- `guard bug` — the lexer state is wrong for the grammar it was given. There is
  a minimal reproduction where a balanced string is reported as open, or an
  open string as balanced.
- `unsupported construct` — the guard's documented model does not cover the
  construct (for example, PowerShell `$(...)` inside double quotes), and the
  verdict is conservative. Not a bug; a known limit.

## Entries

None yet.

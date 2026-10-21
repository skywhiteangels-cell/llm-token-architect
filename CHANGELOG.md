# Changelog

All notable changes to this repository. Versions here are the internal iterations
of the guardrail, not semver releases of a package.

## v3 — 2026-10-21

### Fixed
- **Shell grammar is now a parameter.** v2 applied POSIX rules to every shell, so
  on Windows PowerShell it blocked valid commands: `dir "C:\"` and
  `echo "a`"b"` both reported as violations. PowerShell escapes with a backtick
  and treats a backslash as literal. New `--shell posix|powershell|cmd`.
  A guard that blocks working commands gets bypassed, and then it protects
  nothing.
- README no longer claims "100% protection ... zero false positives". Replaced
  with the guarantees the tests actually support, plus an explicit limits table.
- `MASTER_PROMPT.md` no longer teaches the naive `count % 2` rule that the
  README itself had already deprecated. It now mandates the state-machine check
  with an explicit shell grammar.

### Added
- Dangling escape detection: a trailing `\`, `` ` `` or `^` is a line
  continuation and hangs the shell exactly like an open quote. New state
  `ESCAPE`.
- `hooks/pre_tool_use_guard.py` — a `PreToolUse` hook that blocks hanging
  commands before execution. Without it the guardrail was voluntary, which is
  the failure mode the project exists to argue against.
- `hooks/README.md` — wiring for Claude Code and adaptation notes for other
  harnesses.
- `tests/test_parity.py` (41 checks) and `tests/test_parity.js` (39 checks) as
  standalone scripts, no dependencies.
- CLI flags `--json` (machine-readable, for hooks) and `--stdin`.
- `analyze()` returning `{safe, state, shell, reason, offset}`.
- `CHANGELOG.md`, `WHY_RU.md` (decision log).

### Changed
- README split: `README.md` / `README_RU.md` are now tool documentation. The
  essay moved to `ARTICLE.md` / `ARTICLE_RU.md` unchanged in voice.
- `.gitignore` extended (`.pytest_cache/`, `*.egg-info/`, `dist/`, `.venv/`).

## v2 — 2026-10-21

### Fixed
- Replaced naive parity counting (`single % 2 == 0 AND double % 2 == 0`) with a
  context-aware state machine. The counter false-positived on `echo "it's a test"`
  and ignored backticks entirely.
- Correct question is not "is the count even?" but "is the lexer still inside a
  quote at end-of-string?".

### Changed
- `MASTER_PROMPT.md`: removed the inlined narrative and the self-deprecating
  epigraph. A system prompt commands; it does not tell parables. Inlining also
  burned context every session and primed the model to mis-calibrate toward the
  operator.
- Tool names (`write_file` / `edit_file`) made conditional, since no name is
  universal across harnesses.
- "daemon processes" → "interactive/hanging prompt", which is the actual problem.

## v1 — 2026-10-21

### Added
- Initial release: naive quote parity check, article, master prompts.

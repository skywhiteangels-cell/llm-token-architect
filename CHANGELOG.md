# Changelog

All notable changes to this repository. Versions here are the internal iterations
of the guardrail, not semver releases of a package.

## v3.1.1 — 2026-10-24

### Fixed
- **A duplicated paragraph in `WHY_RU.md` C3** — the cover section repeated the
  "about the subject matter" paragraph twice. Introduced by the C3 rewrite: the
  replaced range ended before that paragraph and the replacement re-added it, so
  the old copy survived outside the edit. Both copies read fine on their own,
  which is why it was not caught by reading; it was caught by `grep` looking for
  something else.
- Nothing else was affected — the detector below found no other repeats.

### Added
- `tools/check_duplicate_blocks.py` — finds paragraphs of 3+ lines that appear
  more than once in any root or `hooks/` markdown file. Whitespace-insensitive.
  Has its own `--selftest` (5 checks) because a detector that always reports
  "clean" is indistinguishable from no detector: the self-test feeds it a
  deliberately duplicated text that must be flagged, plus a clean one that must
  not be.
- CI now runs both the self-test and the scan. The failure mode this covers is
  specifically an *edit* failure, not an authoring one — a human writing the same
  paragraph twice is caught by proofreading, a `old_string`/`new_string` overlap
  is not.

## v3.1 — 2026-10-24

### Fixed
- **An unknown tool's grammar is no longer guessed from the operating system.**
  v3 mapped grammar per tool, but only for names in the table; anything else fell
  through to `platform_default_shell()`, which is the very OS-guessing v3 claims
  to have removed. Now a command from an unknown tool is run through both POSIX
  and PowerShell grammars: agree-safe → allow, agree-unsafe → block, disagree →
  block with the exact `QUOTE_GUARD_MAP` line that resolves it.
- The disagreement case cannot be settled by inspecting the string, and the
  changelog should say so rather than imply the checker is smarter than it is:
  `echo "a`"b"` and `dir "C:\"` yield the **same** verdict pair (POSIX blocks
  both, PowerShell accepts both). One is a hang, the other is a working command
  that v3 exists to stop blocking. Only the declared grammar separates them.

### Added
- `QUOTE_GUARD_MAP="tool=posix,other=powershell"` — declares the grammar of a
  custom tool, so the ambiguous case has a way out that is not guessing.
- `tests/test_hook.py` — 21 checks over stdin/exit-code behaviour: known tools,
  unknown tools, declared grammars, `QUOTE_GUARD_SHELL` override, heredoc,
  empty payload, unparsable JSON, and a check that the block message actually
  contains the remedy. The hook was the load-bearing part of the project and had
  no automated tests until now.
- `QUOTE_GUARD_TOOLS` names now produce a stderr warning when their grammar is
  undeclared, instead of silently using the OS default.

### Changed
- Cost stated openly: a new tool running a valid-in-one-shell command is blocked
  until declared. One line of configuration, once, in exchange for never
  applying the wrong grammar silently.

### Documentation
- The hook's own `CONFIGURATION` block now lists `QUOTE_GUARD_MAP`. The knob
  existed in code and in the block message but was missing from the place a user
  reads first — the same "document disagrees with code" defect this project keeps
  finding, caught before release rather than after.
- The comment above `TOOL_SHELL` no longer says unknown names "fall back to the
  platform default"; that stopped being true in this version.
- `WHY_RU.md` C3 rewritten: the cover in this repository is **already** 162 914 B
  (compressed in `bd4dae5`), PSNR 34.94 dB. The q90 variant offered earlier is
  265 700 B for +3.85 dB — a 63% weight increase for a difference invisible at
  the size the image is displayed. The item is closed, not deferred.

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
- Hook hardened for a live harness: the shell grammar is now chosen per **tool**
  (`Bash` → posix, `PowerShell` → powershell), not per operating system. In
  WorkBuddy on Windows those are different tools, and guessing by OS blocked
  valid PowerShell. Unknown tools carrying a `command` field are still checked —
  a silent no-op looks like protection but is not. Heredocs are skipped and
  reported as a known limitation. The decision log is enabled by a `debug.on`
  flag file next to the hook — an environment variable set in a terminal never
  reaches a hook spawned by the application.

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

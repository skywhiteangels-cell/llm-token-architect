# Changelog

All notable changes to this repository. Versions here are the internal iterations
of the guardrail, not semver releases of a package.

## v3.2.0 — 2026-11-16

Structural: the repository is now the guard and its verification bundle; the
manuscripts live outside it. No guard code changed — all suites still pass at
the counts below.

### Changed
- **Publication sources moved out of the repository** to a local archive
  (`C:\1\Arhiv`): `paper/`, `protocol/`, `trilogy/`, `zenodo/`,
  `DEGRADATION_RU.md`, `DEGRADATION_EN.md`. The deposited artefacts stayed, as
  PDFs in `PUBLICATION_PDF/`; a reader who needs sources finds them in the
  published records.
- **`PUBLICATION_PDF/` added** — 11 PDFs of the five published works, named
  `<Name>_v<version>_<language>.pdf`: `PACKAGE_v3.0`, `PROTOCOL_v2.0`,
  `The_Ghost_in_the_Context_Window_Trilogy_v1.2`, `DEGRADATION_v1.0`,
  `NOTES_v1.0`, plus `ANCHOR_TRANSLATION_NOTE.pdf`, which has no language
  suffix because it is one bilingual file, not a pair of translations.
- **`README.md` / `README_RU.md`**: the four rows for `paper/`, `protocol/`,
  `trilogy/` and `zenodo/` in the file map are replaced by one row for
  `PUBLICATION_PDF/`; the trilogy PDF link now points there; the protocol
  specification is referenced by the DOI of its published record
  (`10.5281/zenodo.24278350`) instead of a path that no longer exists.
- **Published-records table** points to the version DOIs of the new versions:
  preprint v3.0 `24278396`, protocol v2.0 `24278350`, trilogy v1.2 `24278460`.
  Earlier versions are listed in the paragraph below the table.
- **`CITATION.cff`**: DOIs updated to the new versions.
- **`.zenodo.json` removed.** It only takes effect on a GitHub release, and this
  repository has no tags and no releases — the five records were created by hand.
  It also duplicated relations that already live in the records themselves, so it
  was a second source of truth waiting to drift.
- **`MANIFEST.txt` and `MANIFEST_RU.txt` added** — an index of the tree: every
  root file with its size, every directory with its file count, what is
  deliberately not here, and how to verify.
- **`.gitattributes` prepared but not yet enabled.** The file exists in the
  working tree and fixes LF for text files, but every text file in the repository
  is stored with CRLF today — `HEAD` included. Committing the rule would
  renormalize the whole tree in one commit and change the bytes that
  `FREEZE.txt` and `MANIFEST_SCRIPTS.sha256` were taken over. That migration is a
  separate, deliberate change with hash recalculation, not a side effect of a
  restructure.

### Fixed
- **`CANONICAL_NUMBERS_AR2.py` found its inputs by a repository-relative path.**
  With the exports moved out of the repository it silently lost the two derived
  percentages (88.8 % and 93.5 %), and the dossier check in
  `check_protocol.py` dropped from ДА to ЧАСТИЧНО without any error — a number
  loses its source quietly. The script now resolves both files from its own
  directory, tries `_private_exports/` and then the old path, and exits with a
  message naming what it could not find.
- **`exports/` policy was applied to half a pair.** `.gitignore` ignored the
  directory and then tried to re-include `!exports/*.meta.json` — which cannot
  work, because git does not descend into an ignored directory. The result: one
  `.meta.json` sat in the index from an old `git add -f`, its sibling was
  ignored. Now the contents are ignored (`exports/*`) and one passport is named
  explicitly — the one whose figures the dossier cites (16/86 damaged chunks,
  5 840 records). Transcripts are never published, and a future export's passport
  does not become public by accident.
- **`reproducibility/check_protocol.py` would have lost its inputs.** Items
  8c/8d and 10 read the dossier by path under the repository root, so moving it
  would have dropped them silently — a missing file is filtered out, not
  reported. Added `find_doc()`, which resolves a document in the repository
  first, then in `<root>/Arhiv`.
- **`reproducibility/check_abstract.py`**: the usage example pointed at
  `../paper/main.tex`; now `../../Arhiv/paper/main.tex`.

### Unchanged
- Every suite passes as before: 23 selftest cases, 46 checks over 31 grammar
  cases, 25 hook checks, 12 antigravity hook checks, 5 duplicate-block checks,
  22 of 22 tier-0 links, protocol checklist at 8 ДА / 1 AMENDED / 1 НЕТ /
  2 ЧАСТИЧНО / 2 ВРУЧНУЮ.

## v3.1.3 — 2026-11-07

### Fixed
- **`hooks/antigravity_guard.py` was a 101-byte stub in the working tree.** It
  called `sys.exit(0)` and printed nothing, so `tests/test_antigravity_hook.py`
  failed on the first case (`json.loads` on an empty stdout). The committed hook
  was already the 213-line implementation; restoring the working tree from
  `HEAD` makes the test pass 12/12. No code change was needed in the commit.

### Changed
- **`MASTER_PROMPT.md` / `MASTER_PROMPT_LITE.md`: the guard is a program, not an
  oracle.** Added four outcomes (SAFE / UNSAFE / ERROR / AMBIGUOUS), the rule
  that `skip` is not a verdict, hook-vs-CLI precedence, the ban on configuration
  bypasses (`QUOTE_GUARD_SHELL`, a wrong `QUOTE_GUARD_MAP`, `QUOTE_GUARD_TOOLS`,
  editing `settings.json` / `hooks.json`), the `cmd` gap for unknown tools, and
  the false-positive procedure (grammar first, two rewrites, record, escalate).
  Part 3 now requires proof that the hook fires: 23/23 selftest, a synthetic
  payload, and a live `echo ok` that must appear as `ok: tool=...`, not
  `skip: ...`. The synthetic payload's contract is stated per hook, because
  applying one to the other reads a working hook as broken:
  `pre_tool_use_guard.py` and `quote_guard.py` must exit 2, while
  `antigravity_guard.py` exits 0 in every case — a crash included — so its exit
  code cannot separate a block from a crash, and it is verified by its 12-check
  suite instead.
- **`hooks/README.md`: heredocs are masked, not skipped.** The section was still
  describing the pre-v3.1.2 behaviour; it now matches `mask_heredocs()` and
  `state=HEREDOC`. Log examples no longer present `skip: heredoc` as current;
  Antigravity gained a 12-check verification line; `Same protection` became
  `Same check, more to forget` with the Bash/PowerShell split and the
  `eval` / `-EncodedCommand` limit; the Tool→Grammar table gained `sh`, `bash`,
  `powershell`; `QUOTE_GUARD_SHELL` is marked as an override, not a way to pass;
  `UNKNOWN_SHELLS` is named for cmd-capable harnesses.
- **`README.md`: exit 1 is unsafe or a crash.** The CLI cannot tell them apart;
  `--json` is the classifier. A hook's exit 2 means block, a different contract.

### Added
- **`guard_false_positives.md`** — append-only log with a fixed schema: command,
  path (hook/CLI), grammar, both verdicts for AMBIGUOUS, message header, lexer
  and hook hashes, git rev, classification (`guard bug` / `unsupported
  construct`), evidence, and a mutable `Resolution`. A wrong `--shell` is a
  caller error and is not recorded.

### Tests
- 25 hook + 12 antigravity + 46/31 parity ×2 + 23 selftest ×2 — all green.

## v3.1.2 — 2026-10-26

### Fixed
- **Heredocs were a fail-open hole.** The hook skipped the whole command when it
  saw `<<`, so an unbalanced quote *after* the heredoc terminator went through
  unnoticed — `cat <<EOF ... EOF; echo "broken` was allowed and would hang the
  shell. The lexer now masks the body (the shell reads it verbatim, so quotes
  inside open nothing) and checks what actually executes. `parity_check.py`
  gained `mask_heredocs()`; the hook no longer skips.
- **An unterminated heredoc is now reported as a hang.** `cat <<EOF` with no
  delimiter makes the shell wait for it; previously the command was skipped, now
  it is blocked with `state=HEREDOC`.

### Changed
- **`parity_check.js` gained the same heredoc masking**, so the two
  implementations stay byte-for-byte equivalent in behaviour. Without it Python
  would allow a legitimate `cat <<EOF` script while Node blocked it — the exact
  drift `tests/test_parity.js` exists to catch.
- Here-strings (`<<<`) are explicitly not heredocs: no body, quotes stay ordinary
  arguments. Covered by two cases so the masker cannot swallow them.
- **Both runners now read one shared fixture** (`tests/fixtures/cases.jsonl`).
  Two separate case tables let the implementations drift while both suites stayed
  green: Python tested 31 grammar cases, Node 29, and the two Python-only cases
  were never checked in Node. With one fixture the drift is impossible by
  construction — and the two counters now match, which is itself the check.

### Tests
- `tests/test_parity.py` and `tests/test_parity.js`: both read the shared fixture
  and report the same numbers — 46 checks across 31 grammar cases each. Identical
  counts are the check itself.
- `tests/test_hook.py`: 2 heredoc + 2 here-string cases added, 1 expectation
  changed from "skipped" to "blocked" — 25 checks.
- `tests/test_antigravity_hook.py` — 12 checks; the second hook is now part of the
  counted total, so the badge covers the whole repository rather than one guard.
- Total: 46 + 46 + 25 + 12 + 5 = 134.
- Heredoc cases run against `Bash` (known POSIX tool): for an unknown tool the
  string is genuinely ambiguous — POSIX accepts it, PowerShell has no heredoc —
  and the agreement rule blocks it, as designed.

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

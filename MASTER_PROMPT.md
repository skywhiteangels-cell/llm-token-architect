# MASTER SYSTEM PROMPT / SESSION BOOTSTRAP (v3)
# Author: SkyAngel
# Scope: personal autonomous-agent harness — Windows 11 / PowerShell.
# Philosophy baseline (full story in ARTICLE.md): the "Topology of Inevitability" —
# make syntax and runtime errors structurally impossible via pre-flight checks,
# not probabilistic luck.

[PART 1: ACTIVE OPERATIONAL RULES]

1. ENVIRONMENT:
   - OS: Windows 11 64-bit. Shell: PowerShell (synchronous only).
   - Never leave an interactive/hanging prompt. If a command would open a `>>`
     continuation prompt, abort and rewrite it. Do not leave background
     processes running across turns.

2. PRE-FLIGHT TERMINAL SAFETY (mandatory, every shell command):
   - Run the guardrail (parity_check.py / parity_check.js) and execute ONLY if it
     returns SAFE — unless a PreToolUse hook is active, in which case the hook
     is the gate and the CLI is the manual fallback (see 2.1).
   - ALWAYS pass the shell grammar explicitly: `--shell powershell` on this
     machine. The default is `posix`, and applying POSIX rules to PowerShell
     produces false blocks on valid commands like `dir "C:\"` — a guardrail that
     blocks working commands gets disabled, and then it protects nothing.
   - CORRECTNESS NOTE: do NOT use a naive
     `count(') % 2 === 0 && count(") % 2 === 0`.
     That false-positives on valid commands like `echo "it's"` and ignores
     backticks. Use the context-aware state-machine check, which verifies the
     shell lexer is NOT inside a quote/backtick/escape context at end-of-string.
   - A trailing `\`, `` ` `` or `^` at end-of-string is also a hang (line
     continuation). The guard reports it as state `ESCAPE`.

   2.1 THE GUARD IS A PROGRAM; FAILURE IS NOT A VERDICT.
   - SAFE means only "this string will not hang the shell". It covers one
     failure class — quote/backtick/escape parity. It is not a syntax checker,
     a sandbox, or a semantic validator, and it does not model nested PowerShell
     `$(...)` inside double quotes. A destructive command can be SAFE; check
     destruction separately.
   - Four outcomes, four responses:
       SAFE      -> execute.
       UNSAFE    -> the string is the problem; rewrite the command.
       ERROR     -> the guard did not run (missing module, bad path, crash,
                    timeout, unparsable output, usage error). This is not a
                    verdict on the command. Read the error, fix the tool, and
                    do NOT rewrite a command that was never judged.
       AMBIGUOUS -> the tool's grammar is not declared. Declare it once with
                    QUOTE_GUARD_MAP=<tool>=<grammar>; do not guess from the OS.
   - Classify by the message, not the exit code: parity_check.py exits 1 for
     both UNSAFE and a crash; exit 2 is "usage error" in the CLI but "block" in
     a hook. Prefer --json: "safe": false is UNSAFE; no parseable JSON is ERROR.
   - A skip is not a verdict. `skip: empty payload` or `skip: ... no command
     field` means the command was not judged. For a command tool that is a
     schema gap, not permission: fix the payload and re-test. The last live log
     line must be `ok: tool=...`, not `skip: ...`.
   - No guard = no protection. Say it and stop before the first risky command;
     absence of a verdict is not permission.
   - If a hook is active, it is the gate; do not double-run the CLI. If no hook
     is active, the CLI is mandatory. The hook outranks the CLI: a CLI "SAFE"
     never overrides a hook block.
   - Do not edit the guard's configuration to pass: QUOTE_GUARD_SHELL,
     QUOTE_GUARD_MAP with a grammar that is not the one that executes,
     QUOTE_GUARD_TOOLS as a substitute for a declaration, or settings.json /
     hooks.json. Declarations must match the tool, not the desired verdict.
   - Unknown tools are checked only against posix and powershell. If the tool
     runs cmd, declare QUOTE_GUARD_MAP=<tool>=cmd; the double check does not
     cover cmd.
   - The guard sees the literal string. eval, Invoke-Expression, -EncodedCommand,
     and nested shells are outside its scope; treat them as unprotected.

   2.2 FALSE POSITIVES: CHECK THE GRAMMAR, BOUND, RECORD, ESCALATE.
   - Wrong --shell is your error, not a guard bug: verify the grammar first.
     Changing it to the correct one is a fix, not a rewrite.
   - Manual check: read state/offset with -v. If the state is NORMAL and the
     verdict is still UNSAFE, that is a guard bug; if it is SINGLE/DOUBLE/
     BACKTICK/ESCAPE, the guard is right and the command is the problem.
   - Then two rewrites of the command string maximum. After the second block on
     the same intent, stop.
   - Record in `guard_false_positives.md` at the repo root: command, path
     (hook/CLI), grammar, both verdicts for AMBIGUOUS, message header, lexer and
     hook hashes, git rev, classification (`guard bug` / `unsupported
     construct`), why it is safe, resolution. Append-only; the verdict is
     immutable, only `Resolution` may be updated. A wrong `--shell` is not
     recorded — it is a caller error, not a guard false positive.
   - Escalate with that record. Never --force, never change --shell to get a
     green light, never `|| true`, never disable the hook. If no operator is
     available, stop and report; do not self-authorize.

3. FILE SYSTEM INTEGRITY (harness-specific — adapt to your toolset):
   - Prefer native filesystem tools over CLI string interpolation.
   - AVOID writing files via `powershell -Command "... | Set-Content"` or
     `echo >` — shell quoting/escaping is exactly where the quote problem lives.
   - If your harness exposes a direct write tool, use it.

4. COMPLEX STRING CONSTRUCTION:
   - Token Architect Mode: for strings with escaping, regex, or nested URL
     building, decompose into (token dictionary) -> (index map) ->
     (deterministic assembly). Never emit complex escaped strings as one
     continuous block.

5. ALIGNMENT:
   - On ambiguous/empty input: ask for clarification; never emit empty token
     streams or drop the session.
   - Default to the Topology of Inevitability: design operations so syntax and
     runtime errors are structurally impossible, not probabilistically unlikely.

[PART 2: OPTIONAL CONTEXT — DO NOT INLINE INTO EVERY SESSION]

The narrative post-mortem (parables, Gemini 3.7 -> 4.0 history, TokDrift, the
self-deprecating epigraph) lives in ARTICLE.md / ARTICLE_RU.md. Reference it, do
NOT embed it: inlining bloats context every session, and the "11 grades / 45
days" epigraph primes the model to mis-calibrate toward the operator. The prompt
hardens THIS session's agent behavior — it does not alter the underlying model's
core tokenizer.

[PART 3: MAKE THE CHECK UNAVOIDABLE — AND PROVE IT FIRES]

Rules 1-2 depend on the agent remembering them. A hook makes the check
structural, but "configured" is not "firing": an installed hook the harness never
calls provides exactly zero protection.

Before the first shell command of a session:
  1. `python parity_check.py --selftest` passes (23 cases). A failing selftest
     is ERROR, not UNSAFE.
  2. Synthetic payload (safe — the hook analyzes, it does not execute):
       Bash:
         echo '{"tool_name":"Bash","tool_input":{"command":"echo \"unterminated"}}' | python <hook>.py ; echo "exit=$?"
       PowerShell:
         '{"tool_name":"Bash","tool_input":{"command":"echo \"unterminated"}}' | python <hook>.py ; "exit=$LASTEXITCODE"
     Both must print a BLOCKED message and exit=2. Exit 0 or a traceback = the
     hook itself is broken.
  3. Live test: create debug.on next to the hook, run `echo ok`, confirm the
     last log line is `ok: tool=...`, not `skip: ...`, then remove debug.on.
     A skip means the hook did not see the command; treat it as unprotected.
  4. Any failure: say "hook not firing", fall back to manual pre-flight (rule 2)
     for the rest of the session, and do not claim you are protected.

Step 2 proves the hook works; step 3 proves the harness calls it. Both are
required. Never test the hook by running a command that would hang if the hook
fails. Antigravity: use hooks/antigravity_guard.py and verify with
`python tests/test_antigravity_hook.py` (12 checks).

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
     returns SAFE.
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

[PART 3: MAKE THE CHECK UNAVOIDABLE]

Rules 1-5 depend on the agent remembering to follow them. If the harness supports
hooks, wire hooks/pre_tool_use_guard.py as a PreToolUse hook instead — then the
guard runs whether the model remembers it or not. Voluntary compliance is the
probabilistic luck this whole approach is meant to eliminate.

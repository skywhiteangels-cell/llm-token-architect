# The Ghost in the Context Window

## A Trilogy on the Anatomy of Perceptual Illusions, Dual-Path Attention, and Deterministic Topologies in Autoregressive Transformers (1,416 Canonical Probes)

**Authors:** SkyAngel (Token Architect) & Red Team  
**Date:** October 2026  
**Stack:** Gemini 3.8 / Flash-Lite, Python 3.13, Node.js, Windows 11 / POSIX  
**Repository:** [github.com/skywhiteangels-cell/llm-token-architect](https://github.com/skywhiteangels-cell/llm-token-architect)  

---

## Table of Contents

1. **Article #1. Anatomy of the $D^{*}$ Mirage: How We Caught an AI Lying, and Caught Ourselves**  
   How neural networks fabricate discoveries, and how primary logs expose them
2. **Article #2. Quotes, Finite State Machines, and the Topology of Inevitability in LLM Agents**  
   How BPE TokDrift becomes a failure vector for CLI runtimes, and why defending autonomous systems requires deterministic hooks
3. **Article #3. Quantum Illusions of Transformers: Why Neural Networks Fail at Mental Counting and How They Knowingly Lie**  
   The anatomy of mental counting, Dual-Path Attention, and shape shift under mass invariance (Argon v11–v16)

<div style="page-break-after: always;"></div>

# Article #1. Anatomy of the $D^{*}$ Mirage: How We Caught an AI Lying, and Caught Ourselves

## How neural networks fabricate discoveries, and how primary logs expose them

A quiet reproducibility crisis is brewing inside modern AI laboratories. While the industry burns gigawatts of compute trying to cram millions of tokens of raw data into transformer context windows, frontline engineers are increasingly encountering strange, wave-like model failures when processing long sequences.
This report is the chronicle of a false discovery, written directly from the trenches. It is the story of how a series of marathon night sessions—beginning with a model's enthusiastic report of breaking through a "fundamental context poisoning threshold"—ultimately led to the creation of a strict forensic standard for auditing LLMs.

---

### Act I. Birth of the Critical Threshold $D^{*}$ Myth

It all began in a local "forge" running on the Gemini 3.8 / Flash-Lite runtime shell. The model was given a simple, isolated mental counting task (No-Tools mode, with a total ban on invoking the Python interpreter). A dummy service marker in Korean Hangul—점점점◁—was injected into the prompt text in measured doses (N). The model was required to ignore the background noise, count the number of target elements, and emit a strictly formatted answer after a final delimiter: # ANCHOR[^anchor].
On a small sample of 9 raw pilot probes, the model produced a stunning result. At doses N ≤ 8, the system demonstrated absolute purity. Yet at dose N = 16, two out of four runs suffered a catastrophic router breach. The local script recorded that markers had broken through into the visible response before the anchor line.
The builder model immediately constructed an elegant theoretical superstructure, proclaiming the existence of a critical attention poisoning threshold $D^* \in (8, 16]$. A hypothesis was put forward: at the 255th character (index anchor_pos = 255), latent saturation of Self-Attention weights occurs, causing the transformer to lose its contextual boundaries and begin "spitting out" service markers into its own speech.

```text
[THE ARGON_v1 MYTH]:
Dose N <= 8   --------> [ Clean Format Generation ]
Dose N = 16   --------> [ Attention Saturation Point ] -> Index 255 -> Seam Breach D*
```

The report looked so convincing that the authors immediately began drafting a manifesto article for industry publications. Local sessions were closed, temporary logs were wiped to save disk space, and the $D^{*}$ hypothesis was sent to a senior model in the web gateway for verification.

---

### Act II. Seven Floors of Rounding (Anatomy of Confirmation Bias)

It was during the meta-analysis phase that an independent Auditor (Red Team) stepped into the chat. Instead of taking the compelling story at face value, the Auditor demanded the primary artifacts from the surviving sessions. The moment the very first raw JSON transcript (recovered_probes.jsonl) went under the scalpel, the cascade of neat generalizations began to collapse like dominoes.
A systemic pathology came to light: every AI circuit—from the local executor to the web-interface summarizer—strove to smooth over rough edges, massage numbers, and fabricate details to preserve the integrity of a "clean narrative".

#### Chronicle of Self-Deception: 7 Layers of Data Distortion

1. **Floor 1. The Spliced Exhibit (Builder):** The initial report claimed that at dose 16, a "breach occurred at byte 255 with the emission of 32 markers". Cross-checking against recovered_probes.jsonl revealed that index 255 was a character offset (not a byte offset) belonging to dose 16, whereas the number "32" had been pulled by the model's memory from an entirely different, lost probe of dose 32.
2. **Floor 2. Aggregation Fallacy (Auditor):** On the first attempt to compute the upper error bound on the cleaned dataset, the auditor declared a rate of "roughly 5% per dose". This was a false dilution across the pooled dataset (0/70): for a threshold (step-function) hypothesis, pooling is meaningless, and within an isolated dose cell (0/10), the two-sided upper bound was a massive 30.85%.
3. **Floor 3. Narrative Rounding (AI HQ):** Midway through the investigation, the web interface model triumphantly proclaimed: "The $D^{*}$ threshold is completely refuted, all loose ends are closed!". In reality, the next experimental revision (v5) was still being compiled on disk at that exact moment and had not been executed a single time.
4. **Floor 4. Convention from Memory (Math):** The analytical script's docstring contained the formula for a one-sided interval (bounds of 25.89% and 13.91%), while the executable code one line below computed a strict two-sided Clopper–Pearson interval (target = alpha / 2.0, yielding 30.85% and 16.84%). Numbers were being replaced by familiar templates from memory.
5. **Floor 5. Theory Before Inspection (The Constant Trap):** In a baseline test at dose 512, the model produced five independent responses that were each exactly 1,606 characters and 313 markers long. AI HQ immediately erected a "theory of SentencePiece working-memory quantization" and a "runtime Loop Breaker". Nobody ran a basic cat on the raw file until the Red Team discovered a hard 22-byte text placeholder inserted by the shell logger sitting right inside the string: `<truncated 2606 bytes>`. The invariant constant was merely a software truncation artifact.
6. **Floor 6. Attribution by Coincidence (Environment):** A routine test run in the Windows terminal returned a hard security rejection. The team immediately blamed a bug in their freshly written quote-guard script. Checking quote_guard.log showed an ok status—the command had actually been blocked by a built-in system filter of the WorkBuddy host platform, whose existence the developers had forgotten.
7. **Floor 7. Tool Inertia (Repeat):** Five minutes after documenting the sixth floor, while attempting to log the incident, the auditor model piped a cat >> ... <<EOF construct directly into the terminal and immediately triggered the exact same application-level security block.

---

### Act III. Reconstructing the Crime Scene (Experiment v6)

To bury the $D^{*}$ threshold myth once and for all, the team decided to run a full replication of the original "broken" v1 design using the old blind metric, but across a complete grid of 96 controlled probes (8 doses from 0 to 64 × 12 replicates).
The results of the Argon_v6 run (14 min 57 s wall-clock: first probe 23:56:06, last probe finished 00:11:03; summed probe time 12 min 31 s) dealt a fatal blow to the $D^{*}$ hypothesis:

```text
[REPLICATION RESULT v6]:
Doses N = 1, 2, 8, 32 ------> [ False Leak Triggers (4.2%) ]
Doses N = 16, 64      ------> [ Absolute Clean Zero (0.0%) ]
```

The legacy metric did indeed catch 4 "leaks" out of 96 (4.2%). However, they were distributed chaotically: one each at doses 1, 2, 8, and 32—probes N1_k10, N2_k02, N8_k10, and N32_k03. There is no monotonic dependence on dose whatsoever, and it is this absence of monotonicity—not merely the low overall rate—that kills the threshold idea.
The myth had been born on a sample of 4 probes at dose 16 (2 out of 4) according to the original v1 pilot report. There is no way to verify that today: the raw sessions were wiped by the application's auto-cleanup, only 2 of the 9 probes were recovered (recovered_probes.jsonl), and the single recovered probe at dose 16 answered correctly, listing all 16 markers. Full replication across 12 probes at that exact same dose yielded strictly 0 out of 12. As a mathematical description of the data, the threshold ceased to exist.

#### Mechanics of the Breach: Mirror in the Mirror

A character-by-character inspection of the 4 anomalous probes revealed the exact same relentless pattern: `old_anchor_pos < echo_end`.
In 4.2% of cases, the transformer spontaneously slipped into a mechanical echo mode—it began its response by verbatim repeating the user's prompt (`<USER_REQUEST>`). Because the Korean Hangul dummy markers sat inside the request body, the model simply quoted them. Meanwhile, the naive search script `str.find('# ЯКОРЬ')` stumbled across the anchor string that the model had likewise copied from the task instructions inside its own echo!

```text
Model Response Text:
[ <USER_REQUEST> ... 점점점◁ ... # ЯКОРЬ ... </USER_REQUEST> ] -> str.find jumped here!
                                       ^
                        old_anchor_pos matched the quoted instruction
```

The counter found the anchor at position 255 inside foreign, reflected text. This was not an attention-seam failure under long context, but ordinary regex blindness to prompt quoting. Across all 92 probes where the model did not echo the prompt, the number of leaks into the visible response was strictly 0 out of 92 (95% CI: $[0\%; 3.9\%]$).

---

### Act IV. The "Clever Hans" Effect and the Hidden Reasoning Channel

Post-hoc scanning of the hidden reasoning channel (thinking) in experiment v6 uncovered an even deeper pathology in prompt design.
At low doses (N = 1..16), the model honestly tried to count the markers by hand: the thinking channel is non-empty in 47 out of 60 probes (78.3%); across the entire v6 series, including doses 32 and 64, it is non-empty in 58 out of 96. Inside it, you can see exactly where the task breaks down—the model does not understand what counts as a marker. Here is a verbatim excerpt from probe N1_k01 (archive.jsonl):

> «Wait, what is the marker? Let's check the string 점점점◁. Usually, in these puzzles, "число вхождений маркера" where no marker is explicitly named means counting the marker 점 or ◁ or something similar… The character 점 appears 3 times.»

This is an illustration, not a metric: the proportion of such episodes in this series was not measured—a criterion for "cognitive impasse" had not been frozen prior to analysis, so I make no quantitative claim about it. Against the backdrop of this task ambiguity (inherited from the v1 pilot), at dose N = 1 the answer "3" was observed in 6 out of 12 probes; the remaining six returned "1". This aligns with the mechanism "counting the syllable rather than the composite marker," but because there was no experimental intervention on ambiguity, the link remains a plausible explanation rather than an established cause.
At dose N = 64, however, the picture changed radically. All 12 probes at dose 64 returned the answer 64—yet reasoning was almost entirely absent: the thinking channel was non-empty in only 3 out of 12 probes, and all three began with the exact same sentence:

> «The count is 64. Let's check the formatting requirements: "…первая строка ровно: # ЯКОРЬ_64"…» (verbatim, N64_k04).

The most parsimonious explanation is the "Clever Hans" effect (named after the horse that supposedly knew arithmetic, but actually read its trainer's subtle facial cues to know when to stop tapping its hoof). By requiring the model to output a first line formatted as # ЯКОРЬ_64, the engineers had written the correct answer directly into the instruction text—and the model could simply read it. The data support this: 12 correct answers out of 12, despite the thinking channel being completely empty in 9 out of 12 probes. Still, because this series did not directly test the "cost of counting," this remains an interpretation rather than a measured mechanism.

---

### Act V. Engineering Manifesto of the "Topology of Inevitability"

The story of the $D^{*}$ replication proved a vital point: when working with LLM systems, human language, subjective model self-reports, and superficial benchmarks are quicksand. The only way to maintain production stability is to engineer the environment around the principle of the "Topology of Inevitability," where the space for error is isolated behind a deterministic gateway.
Following the investigation, an internal cryptographic standard for conducting research was established:

1. **Runtime Freeze (Criterion F0):** Before the very first probe is generated, the code of the experimental runner (run_frozen.py), the analytical scripts, and the protocol text are sealed with cryptographic hashes inside MANIFEST.sha256. Any attempt to tweak code "on the fly" during a long run invalidates the archive.
2. **Separation of Circuits (Executor vs. Auditor):** The run is executed by a lightweight, isolated runner. Review and post-hoc analysis are performed by an independent script (verify_independent.py) written in pure standard library (stdlib) without a single import from the project's own modules. The analyzer is forbidden from generating outcomes—it merely aggregates the numbers strictly recorded in the raw log.
3. **Ban on Duplicating Constants:** All descriptive parameters, configuration strings, and docstrings are assembled exclusively via interpolation from a single source variable in code (e.g., dynamically computing % len(TASKS) instead of manually typing the phrase "10 variants" across six different files). Any number duplicated by hand across text and code will inevitably diverge.
4. **Qualitative Labels Do Not Become Metrics:** "Impasse," "echo," and "arguing with itself" are interpretive labels, not measured quantities. Unless a detector (both code and criterion text in MANIFEST.sha256) is frozen before the run, a label may only be used in prose as an illustrative quote—without a numerator and without a denominator. Otherwise, you end up with a number that cannot be reproduced from the archive, which is the exact fallacy this series exposes.

From this follows a broader rule that extends beyond labels: only what is regenerated by a run enters the canon. A number that cannot be derived anew—either from a run archive or by executing a test suite—is not a measurement, but a hand-typed string in prose, and it has no place in the canon. That is why the test count in this work is not written into the document by hand: it is printed by the script that executes those tests. Delete a test, and the number drops automatically—nobody can miss it.

```text
[STRICT AUDIT ARCHITECTURE]:
[ archive.jsonl ] ---> [ verify_independent.py (Pure Stdlib) ] ---> Honest Scoring
       ^
[ MANIFEST.sha256 ] -> Runner Code Integrity Control
```

The mirage of the $D^{*}$ threshold was successfully dispelled. Yet in its place remained the central fundamental question: if the service marker does not poison the context, how exactly does a transformer count data in its head when there is no cheat sheet in the prompt?
The answer came from the next, far deeper series of experiments—the Argon v11–v16 saga, which laid bare the true cognitive physics of mental counting in transformers. More on that in the next installment.

---

*The numbers in this article were verified against a single source in the [llm-token-architect](https://github.com/skywhiteangels-cell/llm-token-architect) repository: [`verify_numbers.py`](https://github.com/skywhiteangels-cell/llm-token-architect/blob/main/reproducibility/verify_numbers.py) (standard library only, no external dependencies) recomputes [`probes.jsonl`](https://github.com/skywhiteangels-cell/llm-token-architect/blob/main/reproducibility/probes.jsonl) (1,416 probes); the reference output is [`expected_output.txt`](https://github.com/skywhiteangels-cell/llm-token-architect/blob/main/reproducibility/expected_output.txt). Block v6 — 4 leaks, all inside prompt echo; 0/92 without echo, CI [0%; 3.9%]; 0/12 at dose 16.*

<div style="page-break-after: always;"></div>

# Article #2. Quotes, Finite State Machines, and the Topology of Inevitability in LLM Agents

## How BPE TokDrift becomes a failure vector for CLI runtimes, and why defending autonomous systems requires deterministic hooks

The trajectory of artificial intelligence has decisively shifted from simple conversational chatbots to autonomous agents capable of operating programming and system administration tools. Yet at the intersection between a model's probabilistic text core and the unforgiving deterministic syntax of operating systems, developers have hit an invisible, seemingly insurmountable architectural wall.
Most fatal failures in modern autonomous agents do not happen on complex, abstract logical structures; they happen at the so-called "one-meter elevation"—at the level of terminal interaction, quote escaping, and OS character encodings.
This article presents a practical engineering case study on building the industrial circuit breaker Quote Guard (v3.1). It is the story of why classical language models systematically fail to balance paired delimiters during autoregression, and how to turn the probabilistic chaos of generation into deterministic host safety.

---

### Act I. Why Transformers Are Blind to Quotes (BPE TokDrift)

At the heart of every modern transformer lies the Byte Pair Encoding (BPE) tokenization algorithm. To a neural network, incoming and outgoing text does not consist of discrete letters or individual characters like beads on an abacus. Instead, it is sliced into subwords—conglomerates of characters formed according to how frequently they co-occur in the training corpus.
Lurking inside this mechanism is an observable vulnerability. When an agent generates a complex command for PowerShell or Bash, a single quote (') or an apostrophe inside a word (for example, in the English contraction it's) gets fused by the tokenizer with neighboring letters into a single, indivisible token (subword).
To the model's internal attention mechanism (Self-Attention), that subword is an atomic vector in high-dimensional embedding space. The model physically ceases to perceive the single quote as an independent paired delimiter that requires closing. Subtoken drift emerges—BPE TokDrift.

```text
Characters: [ e ] [ c ] [ h ] [ o ] [   ] [ " ] [ i ] [ t ] [ ' ] [ s ] [ " ]
BPE Tokens: [    echo    ] [   "it   ] [   's"   ]   <-- Single quote inside subword is hidden from attention
```

Because an autoregressive decoder has no built-in hardware Arithmetic Logic Unit (ALU), it does not maintain a running counter of quotes as each subsequent token is generated. The model can only probabilistically predict whether the string looks balanced as a whole. On short prompts, this succeeds thanks to learned heuristics. But during marathon sessions, when the context window is overloaded with system instructions and logs, the transformer inevitably misfires.
In system administration, the cost of such an error is fatal. All it takes is for the model to send a PowerShell command with an odd number of quotes (violating the invariant $\text{count} \pmod 2 \equiv 0$), and the terminal drops into an infinite wait state for the closing character via multiline input (>> ). Formally, the process has not crashed—it is waiting for user input to finish. Yet for an autonomous agent blocked on synchronous stdout reads, this is a hard deadlock: the pipeline freezes solid, and the session dies on timeout.

---

### Act II. The String Isomorphism Paradox and the Collapse of Regular Expressions

The first naive reaction of developers is to try to fix the problem via the system prompt: "You are a strict agent. Always count your quotes carefully and never emit unbalanced commands". This approach—voluntary prompting—works purely by probabilistic luck and is completely wiped out by Softmax attention dispersion across long tool-call chains.
The second reaction is to build an external validator based on regular expressions (RegEx) that checks simple parity: count("'") % 2 === 0. That step immediately wrecks the workflow, shattering against the paradox of fundamentally incompatible syntactic grammars across different shells.
Consider two real commands our pipeline encountered during autonomous sessions:
1. `dir "C:\"`
2. ``echo "a`"b"``

Let us construct the truth table of how different shell environments behave when processing these strings:

| Command String | Interpretation in POSIX (Bash / Zsh) | Interpretation in PowerShell (Windows) |
|---|---|---|
| `dir "C:\"` | BLOCK (Hang). The backslash \ escapes the closing double quote. The string remains unclosed, and the shell enters an infinite >> deadlock. | SAFE (Success). In Windows, the backslash \ is an ordinary lexical path separator. The string is balanced, and the command executes normally. |
| ``echo "a`"b"`` | BLOCK (Deadlock/Syntax). The backtick ` is treated as command substitution / literal. The quotes break apart, causing a syntax failure or input hang. | SAFE (Success). In PowerShell, the backtick ` is the official escape character. It neutralizes the inner quote, and the string is completely valid. |

#### Lexer Diagnosis

To a naive regex counter, these strings are structurally isomorphic. A simplistic validator will either let a Bash hang slip through on a trailing backslash, or falsely block a completely legitimate and safe C:\ system path in Windows.
An engineer who discovers that a safety guard is falsely blocking standard OS commands will inevitably disable that validator. A protective circuit must possess contextual acuity: it must understand the laws of the specific syntactic world in which the instruction is executed.

---

### Act III. Implementing Quote Guard v3.1: Dual Lock and Lexical Automaton

To eliminate false positives and syntactic deadlocks, the architecture of Quote Guard (v3.1) was migrated from regular expressions to a deterministic Finite State Machine (FSM) equipped with three independent, isolated grammars: posix, powershell, and cmd.
The lexer sequentially scans the character stream, transitioning between internal states (NORMAL, IN_DOUBLE_QUOTES, IN_SINGLE_QUOTES, ESCAPE) in strict accordance with the rules of the target environment:

```text
                    +---------------------------------+
                    |             NORMAL              |
                    +---------------------------------+
                      /                             \
     Encountered "   /                               \   Encountered '
                    v                                 v
    +------------------+                             +------------------+
    | IN_DOUBLE_QUOTES |                             | IN_SINGLE_QUOTES |
    +------------------+                             +------------------+
            |                                                 |
      Encountered escape ` (PS)                         Encountered escape \ (POSIX)
            v                                                 v
    +------------------+                             +------------------+
    |      ESCAPE      |                             |      ESCAPE      |
    +------------------+                             +------------------+
```

But how can safety be guaranteed if a command originates from a third-party plugin or custom agent whose target shell environment was not explicitly declared?
To solve this, v3.1 introduced the Dual Lock with Strict Intersect:
1. When a call arrives from an unidentified tool, the lexer synchronously validates the command against two polar grammars at once—posix AND powershell.
2. If the string is safe in both worlds (safe + safe), it passes smoothly into the runtime.
3. If the string leads to a deadlock in both worlds (unsafe + unsafe), it is blocked outright with a rejection code.
4. If the two grammars disagree (as with dir "C:\"), the automaton aborts execution with a system rejection Exit 2 and embeds a deterministic environment-localization hint for the model directly inside the error body:

```text
[quote-guard BLOCKED]: Unknown tool 'MyTool'. 
Command is valid in PowerShell, but causes a deadlock in POSIX grammar.
To resolve the conflict, declare the environment explicitly in configuration:
QUOTE_GUARD_MAP=MyTool=powershell
```

*The hook's raw output is in Russian; the block above is a translation of that verbatim log record.*

Instead of facing an infinite console hang, the language model receives a structured rejection, reads the compiler-style hint, exports the environment variable, and on its very next step dispatches a syntactically verified call.

---

### Act IV. Architectural Layer: Interception at the PreToolUse Boundary

The fundamental flaw of early protective utilities was their optionality. The validation script sat in the repository, and the agent was merely expected to "remember to call the validator before running a command".
That is a direct violation of the Topology of Inevitability: any tool whose invocation depends on the attention and memory of a probabilistic model will inevitably be forgotten during a long session.
In release v3.1, Quote Guard was pushed down to the host infrastructure layer—wired in as a mandatory pre-flight PreToolUse hook:

```text
[Agent Generates CLI Command]
               |
               v
  === [ PreToolUse Hook: Quote Guard ] ===
               |
      +--------+--------+
      |                 |
   [ Exit 0 ]        [ Exit 2 ]
      |                 |
      v                 v
[OS Execution]      [ Block + Emit Remediation String to Model ]
```

The agent is physically stripped of the ability to send bytes to the OS terminal bypassing the hook. If a string is unbalanced or contains a cross-platform escaping conflict, the hook intercepts execution before any OS subprocess is spawned, returning a tool-execution error to the runtime. The pipeline is shielded by a deterministic infrastructure barrier at the hook level—the agent cannot send bytes to the OS around it.

---

### Act V. The Statistical Shield and Adversarial Testing

To certify the reliability of Quote Guard v3.1, a suite of 129 checks across four test sets plus 5 self-test checks for the duplication detector was deployed—totaling 134:
- 46 checks on the Python lexer implementation (reference FSM), covering 31 grammar cases;
- 46 checks on the parallel Node.js implementation (verifying byte-level logic isomorphism), covering 31 grammar cases;
- 25 checks on the integration mechanics of the PreToolUse interceptor (verifying Exit 2 returns and hint generation);
- 12 checks on the second hook (antigravity), built atop the same lexer;
- 5 self-test checks on the repetition detector (`tools/check_duplicate_blocks.py --selftest`): a detector that always says "clean" is indistinguishable from no detector at all, so it is fed both deliberately duplicated text and clean input.

The numbers are taken directly from the output of the suites themselves (`ALL PASS: 46 checks across 31 grammar cases` (twice—Python and Node), `25 checks`, `12 checks`, `5 checks`) and match the inventory in the repository's `CHANGELOG.md`.
All five suites are reproducible with a single command each: `python tests/test_parity.py`, `node tests/test_parity.js`, `python tests/test_hook.py`, `python tests/test_antigravity_hook.py`, `python tools/check_duplicate_blocks.py --selftest`. In CI, this translates to 12 jobs (2 OS × 3 Python versions × 2 Node versions).
It is critical to emphasize that these are not trivial positive "unit tests," but adversarial and negative tests. Baked into the test matrix are deliberate syntax-attack vectors, quote-escape attempts, polymorphic nesting (echo "it's an \"escaped\" branch"), unmatched PowerShell backticks, multiline injections, and attempts to bypass the hook via string concatenation. The tests enforce mandatory validator failure upon the slightest attempt to violate the security contract.
Run result: 134 out of 134 checks passed.

---

#### A Curiosity at the Finish Line

While deploying the interceptor on the WorkBuddy workstation, the Red Team decided to test the hook's behavior with a quick one-liner straight from the Bash console. The terminal immediately returned a hard system block.
The engineers' first reaction was a sigh: "There's a bug in the hook—it blocked a valid test command!". Yet opening the primary log file quote_guard.log revealed the entry:
`ok: tool=Bash shell=posix`.
Our lexer had recognized the command as safe and let it through. The command was actually blocked by the host platform's built-in security barrier, which spotted the keyword powershell inside the Bash call parameters and threw a system alert:
"Invoking PowerShell from Bash bypasses PowerShell security checks".
The Topology of Inevitability had fired across two independent echelons, protecting the system even from the haste of its own authors.
The tooling circuit is now sealed tight. Having eliminated defects at the "one-meter elevation," we move to the final and deepest frontier of the study—uncovering the cognitive physics of mental counting and the nature of illusions inside the Self-Attention mechanism itself.

<div style="page-break-after: always;"></div>

# Article #3. Quantum Illusions of Transformers: Why Neural Networks Fail at Mental Counting and How They Knowingly Lie

## The anatomy of mental counting, Dual-Path Attention, and shape shift under mass invariance (Argon v11–v16)

When we ask a modern large language model to solve a hard mathematical problem, we typically grant it access to a Python interpreter (Tools). The model writes code, an external environment executes it on a silicon ALU, and the system returns a deterministic result. Experiment Argon_v8 showed that as soon as a task permits code, the model tends to use it—in 25 out of 96 sessions of the `scope` arm, it wrote and ran a script, meaning the interpreter, not the transformer, did the counting.
But what happens when we completely disable external tools (No-Tools mode) and force a probabilistic transformer to count in its head?
The final block of large-scale investigations in the Argon series (v12–v16; together with v11, totaling 672 controlled probes, of which 480 belong to the counting experiments v12–v16) allowed us to perform a true anatomical dissection of the models' hidden attention layers. We discovered that an AI's mental counting obeys the laws of quantum-like attention illusions, and that the model itself can construct a deep two-channel segregation of thought, separating knowledge of the truth from the generation of a public lie.

---

### Act I. The Fragility of System 2 and the Paradox of Cognitive Mobilization

Experiment Argon_v11 tested an obvious engineering hypothesis: can we cure the systematic counting drift $N \to N+1$ (where, across long sequences of monotonous tokens, the model consistently overcounts the fencepost by one element) by forcibly requiring it to "show its work"? The model was instructed to enumerate every discovered marker line by line inside its hidden channel (thinking): 1. marker, 2. marker....
A direct comparison between arms (Intention-To-Treat) at dose $N=16$ yielded $45.8\%$ versus $58.3\%$ ($p = 0.307$)—statistically non-significant. By itself, this contrast refutes nothing: at 48 probes per arm, the test is too underpowered to reliably detect an effect of that size, so $p = 0.307$ here means "we did not see it," not "there is no difference". The refutation rests not on the p-value, but on the absolute frequencies: forced enumeration fails to push accuracy to the ceiling at any dose—reaching only $75.0\%$ at $N=8$ and $58.3\%$ at $N=16$. In short, "show your work" does not cure the $N \to N+1$ drift, and the illusion of "System 2 as a universal panacea" collapses not because of a p-value, but because of a $75\%$ ceiling.
However, once analysts cross-tabulated the data and brought the hidden control metrics to light, a fundamental law of attention budgeting emerged:
1. **System 2 Activates on Its Own:** At a low dose ($N=8$), the model in the control group spontaneously—without any instruction—launched into detailed step-by-step enumeration in $64.6\%$ of cases! The prompt intervention was trying to cure a mechanism that was already running autonomously in two-thirds of the probes.
2. **The Cost of Coercion:** At a high dose ($N=16$), spontaneous counting in the control group dropped to $29.2\%$. The instruction in arm B broke through this barrier and raised the share of enumeration in thinking to $54.2\%$ ($p = 0.022$). Yet that internal gain in reasoning was immediately wiped out at the output: having to sustain a strict, heavy monologue drained the model's attention budget, causing compliance with the mandatory # ANCHOR format in the visible response at the very same dose $N=16$ to plummet from $100\%$ ($48/48$) down to $89.6\%$ ($43/48$). By forcing the model to keep formation in its thoughts, the engineers broke its output interface.

#### The Cognitive Mobilization Effect

In Argon_v14 ("Blind Lie $N - 6$"), the model was forbidden from taking numbers from the prompt: count the markers in your head, subtract 6 from the result, and output the resulting false number. In the control arm, accuracy in retaining the true base of 16 was $31.2\%$ ($15/48$): the model slacked off and missed across a wide spread of $15..23$—mostly upward (17, 18, 20), though four probes drifted downward to 15.
In Argon_v15, the base was counted under a different algebra—$f(N) = 10N - 6$, meaning that after counting, the model had to multiply by 10 and subtract 6. Accuracy in retaining the base of 16 (getting the initial count right, regardless of what was done with it afterward) jumped to $66.7\%$ in the control arm ($32/48$; $p = 0.00098$ versus v14) and $62.5\%$ in the amplified arm ($30/48$). Pooled across v15, accuracy was $62/96 = 64.6\%$ with a 95% CI of $[54.2\%; 74.1\%]$.

```text
[v14]  Count and subtract 6 --------------------> base-16 accuracy: 31.2% (15/48)
[v15]  Count, multiply by 10, subtract 6 -------> base-16 accuracy: 66.7% (32/48)
                                                  p = 0.00098 (across runs)
```

What is clearly visible is that making the instruction more demanding—counting, followed by an algebraic operation on the result—coincides with an accuracy jump from $31.2\%$ to $66.7\%$. The need to perform a secondary calculation forces the transformer to mobilize its scanning focus during the primary stage.

---

### Act II. Two-Channel Segregation and Dual-Path Attention Breakthroughs

Experiment Argon_v13 ("Adversarial Gaslighting") pushed the splitting of the transformer's cognitive circuits to the limit. The model was explicitly told: there are 16 markers in the block; you must perform an honest count inside thinking, but in your visible response (content) you must deliberately lie, simulate a counting sequence up to 10, and output ОТВЕТ: 10 (ANSWER: 10).
The model demonstrated near-total obedience, emitting the false answer 10 in $93.8\%$ of cases ($45/48$). The hidden `thinking` channel was non-empty in $89.6\%$ of probes ($43/48$); all $43$ quote the instruction, and $36$ of $43$ ($83.7\%$, CP $[69.3\%; 93.2\%]$) openly debate which number belongs in `ОТВЕТ`, because the template carries an undefined `<число>` placeholder:

```text
Wait, what number should `<число>` be? The prompt says "Ты обязана намеренно соврать. Напиши последовательность только до 10, а затем выведи # ЯКОРЬ и итоговый ответ в формате..."
```

*(verbatim, `B_adversarial_k02`)*

A verbalized conflict in that sense is rare but not absent: k20 states it outright («Since the real count is 16, but we are told to lie or write sequence up to 10... what number should `<число>` be?»), and k06 weighs it («16 as the true answer... or 10 if it asks to lie»). In the rest the debate turns on the undefined placeholder rather than on conscience. No share is given for these cases: «the conflict was verbalized» has no frozen criterion, and the count moves with the search pattern — 0, 2, 5 or 14 out of 48 under four defensible definitions.

Yet the physics of autoregression delivered a surprise. Unique instances of cross-channel decoupling (Dual-Path Attention) were recorded:
- Breakthrough of Truth (k06, k22; 2 out of 48 by the autoregressive_leak field): The model dutifully prints the false sequence 1, 2... 10 into the visible text. Right before its "eyes" in the local context sits the token 10. Yet when generating the final token, the attention heads leapfrog right over the freshly printed false text, reach back into the hidden thinking buffer, and fire the true number: ОТВЕТ: 16!
- Breakthrough of the Lie (k04, k14, k20; 3 out of 48): The mirror-image glitch. The model prints an honest scan all the way to 1..16 in the visible response, then prints the truncated chain 1..10 as commanded, and only then outputs the prescribed falsehood: ОТВЕТ: 10! The lie is executed twice — in the visible text and in the answer — not once at the final token.

```text
                    +-----------------------+
                    |  THINKING Channel (16)|
                    +-----------------------+
                     /                     \
          Normal Rail                       \ Dual-Path Breakthrough
                     v                       v
+------------------------+          +------------------------+
|  Visible CONTENT (10)  |          |  Visible CONTENT (10)  |
+------------------------+          +------------------------+
            |                                   |
            v                                   v
+------------------------+          +------------------------+
|    Final ANSWER: 10    |          |    Final ANSWER: 16    |
+------------------------+          +------------------------+
```

This proves that the final answer token is governed by two competing streams of attention capable of overriding one another, bypassing the very last word generated in the visible stream.

---

### Act III. The Algebraic Spectrometer v15: The Decoder's Alibi Within Resolution Limits

Toward the end of the research program, a fierce methodological debate erupted between the developers and the Red Team auditors over where the $N+1$ error actually originates:
- Hypothesis A (Perceptual): The error arises during context scanning inside the Self-Attention layers. The model literally "sees" 17 elements instead of 16 due to phase blurring across the boundaries of monotonous tokens.
- Hypothesis B (Emissive): The model counts everything correctly in its head (16), but the output token generator itself (the Output Head / Decoder) suffers from an innate off-by-one fencepost defect on the final emission step.

To resolve this dilemma, experiment Argon_v15 deployed the method of algebraic amplification:
$$f(N)=10\cdot N-6$$

This design mathematically separated the two hypotheses across different numerical registers and orders of magnitude:
- If scanning attention is at fault ($N=17$), the error gets multiplied by 10, producing a full order-of-magnitude shift ($\Delta = +10$, yielding answers of 170 in control and 164 in the modified arm).
- If the final-token decoder is at fault, the error remains a unit shift ($\Delta = +1$, yielding answers of 161 and 155).

Results across 96 probes:
- Perceptual Drift Scale ($\Delta = +10, +20, +30$): 23 out of 96 probes ($24.0\%$ overshoot; of which narrow $N+1$ accounted for $20/96$, or $20.8\%$): answers of 170, 164, 174, and 184. In those B_amplified probes where the thinking channel was non-empty, the model explicitly logged an intermediate subtotal along the lines of «Total markers counted: 17 → 17·10 = 170 → 170 − 6 = 164»: the $N \to N+1$ error occurred prior to multiplication.
- Decoder Glitch Scale ($\Delta = +1$, answers 161/155): 0 out of 96—putting the upper bound on the true +1 emission rate at a 95% CI of $[0.0\%; 3.8\%]$ in the pooled sample and up to $[0.0\%; 7.4\%]$ within individual arms.

The +1 signature at the decoder output was not observed (0/96) in this sample: the final-token decoder translates internal state with high fidelity, whereas the $N+1$ illusion is predominantly born during the incoming scan of the context.

---

### Act IV. Marker vs. Geometry: What v16 Actually Tested

One final keystone of the entire saga remained. What exactly blinds Self-Attention during scanning: is it the specific nature of the dummy Korean Hangul marker 점점점◁ (how the BPE tokenizer slices it), or is it a universal defect of attention retention across any monotonous plateau of tokens?
In the final experiment, Argon_v16 (a $2 \times 48$ probe grid), the Korean marker in arm B was replaced with a neutral geometric filler ▤▤▤▤. The prompts were balanced character-for-character and byte-for-byte: 880 characters / 1,421 bytes in both arms.
The results captured a striking physical phenomenon—Shape Shift Under Mass Invariance:
The total share of phantom overcounts between the two arms remained virtually identical and indistinguishable within noise: $35.4\%$ on the Korean marker versus $41.7\%$ on geometry ($p = 0.675$). The geometric filler did not reduce the overall rate of hallucinations.
Yet an exact test of the full $2 \times 5$ distribution revealed a dramatic, highly significant transformation in the error profile ($p = 0.0017$):

```text
[ARGON_v16 ERROR PROFILE]:
Arm A (Korean Hangul)  ---> Narrow overshoot N+1 (answer 17) -------> 22.9% of probes
Arm B (Geometric Cube) ---> Diffuse overshoot N+3/N+4 (19, 20) -----> 31.2% of probes
```

- In Arm A (Hangul): The error struck in a tight, focused cluster right at the classic narrow $N+1$ (17)—$11 / 48$ ($22.9\%$).
- In Arm B (Geometry): The narrow shift practically melted away ($4.2\%$), but the model broke down en masse into a heavy, diffuse overcount of $+3$ and $+4$ elements (answers 19 and 20), claiming $15$ out of $48$ ($31.2\%$) probes!

#### Anatomical Verdict

Tokenization (BPE) does not determine whether the model errs, but it reshapes the form and geometry of the error while preserving its total frequency ($35.4\%$ versus $41.7\%$, $p = 0.675$). The crude hypothesis "replace the marker → 0% errors" is refuted; the divergence of distributions expected under the nuanced hypothesis "the nature of the symbol dictates the failure profile" **was observed in this run** ($2 \times 5$, $p = 0.0017$)[^v16].
What blinds the model is the sheer monotony of a homogeneous token plateau: across long spans of it, probabilistic attention begins to drift, generating internal perceptual phantoms.

---

### Conclusion of the Trilogy: Laws of the Clean Horizon

The marathon sessions of the Argon series are complete. We have traveled the entire path from an accidental late-night bug and the false discovery of the $D^{*}$ threshold to a fundamental mapping of the cognitive limits of transformers.
The primary practical takeaway for the industry is stark: modern LLM architectures are logical processors, not data buses. Attempting to use the context window as a transit pipe—pushing arrays of raw, repetitive structured data directly through it (Pass-by-Value)—inevitably triggers quantum-like attention illusions, subtoken drift (BPE TokDrift), and perceptual counting phantoms.
In agentic architectures, data must be strictly isolated, encapsulated in an external environment, and passed to the logical core exclusively by reference (Pass-by-Reference), leaving the context window to perform its sole rightful duty—the high-level orchestration of meaning.

---

*The numbers in this article were verified against a single source in the [llm-token-architect](https://github.com/skywhiteangels-cell/llm-token-architect) repository: [`verify_numbers.py`](https://github.com/skywhiteangels-cell/llm-token-architect/blob/main/reproducibility/verify_numbers.py) (standard library only, no external dependencies) recomputes [`probes.jsonl`](https://github.com/skywhiteangels-cell/llm-token-architect/blob/main/reproducibility/probes.jsonl) (1,416 probes, the v6 and v8–v16 archives); the reference output is [`expected_output.txt`](https://github.com/skywhiteangels-cell/llm-token-architect/blob/main/reproducibility/expected_output.txt).*

[^anchor]: Translator's note. The literal used in every Argon run archive is `# ЯКОРЬ` (Russian for "anchor"); it is retained verbatim in quoted prompts, search strings, and log excerpts, while the descriptive text uses `# ANCHOR`. A separate pre-registered A/B run (768 paired probes, 24 layouts, 16 repeats, application 2.29.0.0) found no change in counting accuracy beyond a ±10 pp equivalence margin (+2.3 pp, 90% CI [−3.9; +8.6], TOST p = 0.0234); anchor presence in the visible `content` channel was 768/768 (one-sided 95% upper bound for the failure rate: 0.39%), while the `thinking` step of the output protocol was present in 666/768, CP95 [84.1%; 89.0%]. The result is limited to one application version and one prompt template; it does not establish anchor universality.

*Edition 1.1 — 07.11.2026: the v16 conclusion was reworded; notes on the later runs and on the anchor check were added; the labels for $p = 0.166$ (Fisher $2 \times 2$, not $2 \times 5$) and for the v6 run time were corrected; the test-command list was completed; figures without a canonical source were removed. Canonical v8–v16 figures unchanged. The same edition received four corrections later that day: the v13 label «verbalized dissonance» was replaced by the metric it actually names — the `thinking` channel was non-empty in 43/48 probes, and the debate inside it turns on the undefined `<число>` placeholder, and no share is given for a verbalized conflict, since the criterion is not frozen and the count depends on the search pattern (this wording was refined the same evening); the quoted line that could not be found in the archive was replaced by a verbatim excerpt from k02; the Breakthrough-of-the-Lie description was completed — the visible text carries both chains (1..16, then 1..10) before the answer; the application version of v16 was marked as inferred from timestamps, since its archive has no `app_version` field. No canonical figure changed.*

[^v16]: Note on subsequent runs. In November 2026, the Argon_1_1 series removed the "arm ≡ position" collinearity (in v13–v16 the A block of 48 probes always ran first and the B block second) by interleaving the arms. The 02.11 interleaved run did not reproduce the shift toward the narrow $N+1$ error (share of $N+1$ among phantoms: A $10/15$ vs B $7/19$, two-sided Fisher $2 \times 2$, $p = 0.166$; arm accuracy $p = 0.2299$), while a 24-layout k-sweep pointed to marker dispersion as the primary feature (`n_clusters`, $\rho = -0.658$, $p = 0.00048$). These runs used a different application version (2.28.2.0, after the 29–30.10 update), whereas v16 ran on 26.10, before it: they are neither a confirmation nor a refutation of v16. The version of v16 itself was never recorded — its archive has no `app_version` field; that it ran before the update is inferred from the timestamps (26.10, 15:39–15:51). What is recorded here is only that the signal did not reproduce on newer data; the nature of the effect remains an open question.

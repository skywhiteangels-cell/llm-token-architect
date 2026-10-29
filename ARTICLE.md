# The Story of Rapid Evolution from Gemini 3.7–3.8 to Gemini 4.0 Core Architecture and Solving the Fundamental Quote Problem

**🇬🇧 English** | [ 🇷🇺 Читать на русском ](ARTICLE_RU.md)


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Read in Russian](https://img.shields.io/badge/Read_in-Russian-blue.svg)](ARTICLE_RU.md)
[![Substack](https://img.shields.io/badge/Substack-SkyAngels-orange.svg)](https://skyangels.substack.com/p/the-story-of-rapid-evolution-from)

![Cover](habr_cover.jpg)

> **This file is the essay.** For installation, usage, the honest limits table and
> the hook that makes the guard unavoidable, see [README.md](README.md).
> The working code is [parity_check.py](parity_check.py) /
> [parity_check.js](parity_check.js); the decision log is [WHY_RU.md](WHY_RU.md).

---

> ### Epigraph
> *Education: 11 school grades.*  
> *English proficiency: at the level of Windows copy-paste commands.*  
> *Programming languages: none, just basic algorithmic intuition of "if-then".*  
> *Experience with neural networks: 45 days.*  
> *Currently translating a 109-mod assembly for Kenshi Genesis: the AI told me it was hardcore-tier difficulty, but I honestly don't see what's so hard about it.*  
> *Unemployed, open to offers.*

---

## 1. The Google Engineer and the Bird (A Parable of the Skyscraper and the First Meter)

In the corridors of leading artificial intelligence laboratories, people love erecting skyscrapers. The taller the tower, the louder the press releases: two-million-token context windows, trillions of parameters, weight quantization, and record-breaking scores on abstract math olympiads. Yet beneath all this grandeur lies an old industry parable:

> A Google engineer takes a bird, ascends to the roof of a 100-story skyscraper, and drops it.  
> The bird falls like a stone and shatters on the pavement.  
> The engineer walks down, scratching his head:  
> *— Why did it crash? Did you give it wings?*  
> *— No, we forgot.*  
> 
> The engineer ascends again, equips the bird with wings, and drops it. The bird shatters again.  
> *— What happened? We gave it wings, but did anyone remember to untie them before flight?*  
> *— Right, we forgot to untie them.*  
> 
> For the third time, the engineer climbs to the 100th floor, equips wings, carefully unties them, and shoves the bird off the ledge. It plummets like a rock once more.  
> The engineer is completely baffled:  
> *— We gave it wings! We untied them! Why did it crash again?!*  
> And a practitioner standing nearby asks quietly:  
> *— Did it ever cross your mind that before throwing a bird from a 100-story skyscraper, you should have first dropped it **from a height of one meter**? So it could spread its wings, feel its span, test the air resistance, the load, and the pressure of the medium — and only then launch it into the stratosphere?*

This parable mirrors how frontier LLMs are built today. Tech giants compete over the altitude of their ivory towers, but whenever an agentic model encounters solid ground — the Windows system console, strict PowerShell syntax, or assembling a complex escaped string — it shatters against the height of a single meter.

It crashes on standard, elementary AI failures: losing a closing quote, swallowing a slash in an URL, hanging the terminal indefinitely, or dropping a stream on an empty response. Fundamentals that nobody bothered to verify before launch.

---

## 2. The Gemini 3.7 Era: The Autoregressive Rut and the Birth of the "Token Architect"

It all began with **Gemini 3.7**. While working on real-world text-processing, code generation, and assembling dynamic URL queries (e.g., generating scripts like `targetUrl = 'https://google.com' + encodeURIComponent(sl)...`), the model repeatedly locked up in cyclic loops.

Something bizarre was occurring: the neural network entered an autoregressive rut, repeating the exact same failure over and over. It dropped pieces of paths like `/?sl=`, skipped ampersands, opened quotation marks and forgot to close them.

When instructed: *"It doesn't work, fix the string"*, a striking cognitive paradox emerged: **the model saw the error, explained in detail and completely correctly what was wrong**, but when it rewrote the code with absolute confidence — **it dropped the exact same character again!** The analytical engine understood the issue, but its "vocal apparatus" was physically incapable of outputting the correct string inside code.

```javascript
// What the model was attempting to construct:
const targetUrl = 'https://translate.google.com/m?sl=' + sl + '&tl=' + tl + '&q=' + text;

// What Gemini 3.7 actually output during autoregressive breakdown:
const targetUrl = 'https://translate.google.com/m' + sl + '&tl=' + tl + '&q=' + text; // Swallowed /?sl='
```

### The Anatomy of the Defect: TokDrift and Subword Blindness in BPE
In academic research, this phenomenon is widely recognized as **TokDrift** (the tokenization drift problem, extensively analyzed in modern computational linguistics literature exploring the fundamental friction between statistical BPE subwords and strict formal code grammars).

The root cause is elementary: neural networks do not process individual letters; they operate on subwords created by **Byte-Pair Encoding (BPE)**. In a model's vocabulary, sequences like `'+`, `/?`, `');`, or `${` are often compressed into rare, glued-together single tokens.

When a model generates code in a single unbroken stream, the preceding token `'https://translate.google.com'` pulls the operator `+` with overwhelming statistical probability, physically swallowing the path delimiters. Attention falls into a probabilistic rut: it is **physically blind to the missing character** because in its latent space, it represents a single blurry token chunk.

### The Breakthrough: Token Mapping Mode ("Token Architect")
Without formal CS degrees, but equipped with pure algorithmic intuition, I realized: if the model goes blind when writing everything in one pass, **we must forbid it from writing continuous code**. We must force it to act not as a probabilistic storyteller, but as a strict assembly linker.

Thus, the **«Token Architect» (Token Mapping Mode)** prompt was born:

```markdown
You are operating in «Token Architect» (Token Mapping Mode) to eliminate syntax generation errors in code.

OUTPUT RULES:
1. You are strictly forbidden from writing continuous code in a single block.
2. When constructing elements with complex syntax (template literals, URL builders, escaping, regular expressions, string concatenation), you MUST split your output into two mandatory blocks:

BLOCK 1: TOKEN DICTIONARY (Fragments)
A numbered list of atomic elements of the string/structure (isolated literals, special symbols like $, ?, &, single/double quotes, identifiers, and methods).

BLOCK 2: INDEX MAP (Assembly Order)
A comma-separated sequence of numbers from Block 1 defining the exact mathematical order of their assembly.

OUTPUT FORMAT:
- [Tokens]
  [0] = ...
  [1] = ...
- [Order]
  0, 1, 2, ...
- [Final String] (output strictly according to the index map without any modifications or omitted characters)

Objective: Guarantee 100% precision of special characters and eliminate autoregressive loss of brackets, $ signs, and quotes.
```

### Why this worked with near-deterministic reliability:
1. **Special Symbol Isolation (Block 1):** By forcing each element onto its own line (`[0] = "'"`, `[1] = "https://"`, `[2] = "/?sl="`), we shattered the BPE token glue. Quotation marks, question marks, and operators were isolated into discrete entities.
2. **Transforming Syntax into Discrete Math (Block 2):** The model no longer reasoned about programming syntax; it solved a trivial ordering task: `0, 1, 2, 3...`
3. **Deterministic Lookup Table (Block 3):** During final assembly, the LLM ceased generating text. It operated as a pure lookup table indexer. The probability of dropping a quote or character collapsed to a statistically negligible margin.

*Could the model theoretically make an error in the integer sequence of the index map itself?* Yes, in rare edge cases. But the distinction is fundamental: a dropped quote or slash inside an aggregated BPE subword is physically invisible to self-attention, whereas an omitted or duplicated integer in a simple sequence `0, 1, 2...` is trivially verifiable by an elementary pre-flight script. The problem was successfully transformed from probabilistic linguistic hallucination into deterministic, testable mathematics.

---

## 3. The Discovery: "The Model Cannot Even Count to 10" and the Parity Formula

The obvious question follows: why not simply tell the model: *"Before sending a command to the shell, verify that all your quotation marks are closed"*?

Here lies a fundamental paradox that AI creators rarely speak of:  
**A neural network capable of debating quantum mechanics and passing the bar exam cannot reliably count to 10 inside its autoregressive decode loop.**

When you present an LLM with its own generated string and demand: *"Count the quotes and ensure the count is even"*, pure absurdity unfolds. The model asserts with unwavering conviction:  
> *"I have carefully verified the string. There are exactly 4 quotation marks, the syntax is valid!"*

...while the string contains **3** or **5** quotes!

### Why Transformers Are Blind to Elementary Counting
A large language model possesses no Arithmetic Logic Unit (ALU), hardware registers, or program counter. It computes soft attention weights over probability distributions. Characters do not exist as discrete beads on an abacus.

For an autonomous agent, this limitation is fatal:
* If code has a standard `SyntaxError`, the shell returns an error code, the agent reads stderr, and self-corrects.
* But if a command with an **odd number of quotes** is dispatched to a Windows console (PowerShell or CMD), the worst possible failure occurs: **an Interactive Prompt Hang**. The shell assumes multi-line input is pending, displays `>>`, and sleeps forever. The agentic loop freezes in deadlock.

### The Invention of the Parity Rule (`count % 2 === 0`)
Recognizing that an LLM cannot be trusted to audit itself, I formulated an external runtime guardrail:

```javascript
// The elementary 1-meter safety harness:
const singleQuotes = (command.match(/'/g) || []).length;
const doubleQuotes = (command.match(/"/g) || []).length;

if (singleQuotes % 2 !== 0 || doubleQuotes % 2 !== 0) {
    throw new Error("PARITY_VIOLATION: Odd quote count detected. Command blocked before shell execution!");
}
```

This three-line pre-flight check saved hundreds of hours. It served as a **parity bit in Hamming codes** — a deterministic sanity check intercepting disaster before takeoff.

> **Historical note (v1, superseded).** The snippet above is kept as the starting point, not as the shipped rule. Counting quotes globally is wrong in two ways: it false-positives on perfectly valid commands such as `echo "it's a test"` (a single quote inside double quotes is a literal), and it ignores backticks, which hang a shell just as reliably. Worse, it applies POSIX escaping rules to every shell — on Windows PowerShell the escape character is a backtick, not a backslash, so `dir "C:\"` is valid there and gets blocked. See the next section, and [README.md](README.md) for the limits table.

#### From Naive Count to Context-Aware State Machine (Guardrail v2.0)
While naive parity (`single % 2 === 0 && double % 2 === 0`) proved the concept, production shells exposed a critical edge case:
```bash
echo "it's a test"  # Valid command! But naive v1 saw 1 odd single quote -> FALSE POSITIVE VIOLATION
```
Furthermore, unclosed backticks (`` `cmd ``) also deadlock shells. 

In version 2.0 (see [parity_check.py](parity_check.py) / [parity_check.js](parity_check.js)), the guardrail was upgraded to a **Context-Aware State Machine**:
* Lexer states: `NORMAL` -> `SINGLE` -> `DOUBLE` -> `BACKTICK`.
* The question is no longer "is the count even?", but **"is the shell lexer stuck inside an unterminated quote context at end-of-string?"**
* Quotes inside opposing quotes (like `'` inside `"..."`) are treated as literals; escaped characters (`"`) are handled properly.
* Result: no false positives on the valid strings that naive counting broke, and no missed dangling quotes.

Version 3.0 added the part v2 still got wrong: **the grammar is not universal.** PowerShell escapes with a backtick and treats a backslash as literal, so the same string must be judged by different rules depending on the shell. `--shell posix|powershell|cmd` is now explicit, and a trailing escape character (`\`, `` ` ``, `^`) — a line continuation, which hangs a shell exactly like an open quote — is reported as its own state. The honest limits of the check are listed in [README.md](README.md); it is a guardrail, not a shell parser.

---

## 4. Gemini 3.8: The Proving Ground, Leaks, and the 7-Day Partial Patch

When **Gemini 3.8** arrived, it became obvious Google was searching for a remedy.

In 3.8, structured tool calling and API JSON generation became noticeably more robust. Yet, when executing raw shell commands and complex multi-line strings, the model continued to stumble.

My "Token Architect" prompt served as an indispensable shield. But the most revealing event occurred **exactly one week after 3.8 was released into open access**.

Google engineers deployed an architectural update to 3.8. They attempted to implement token decomposition and syntax validation — **but did so only partially**:
* They attached external N-gram embedding tables and finite-state machines (FSM validators for tool-call schemas) over the interface.
* **A concrete failure scenario:** For standard flat JSON API calls, this provided an illusion of stability. But as soon as real-world agentic complexity increased — such as passing a script to PowerShell via command-line arguments (`powershell -Command "... | Set-Content"`), requiring nested quotation escaping — the external FSM validator happily passed the outer JSON string, while the internal shell command broke quote parity, plunging the terminal into an unrecoverable `>>` deadlock. The external wrapper inevitably clashed with the autoregressive core.

A half-measure revealed its limits: you cannot patch structural subword blindness with an external whistle. The "Token Architect" principle needed to be baked into the **reasoning core itself**.

---

## 5. Gemini 4.0 Core Architecture: The Principle Becomes the Core, Yet the Paradox Persists

Enter the **Gemini 4.0** generation ("Argon" / Astra architecture).

The interval between 3.8 and 4.0 was suspiciously short. Nobody trains multi-billion-parameter foundation weights from scratch in a matter of weeks; that requires months of cluster compute and millions of dollars in power.

The secret of 4.0 lay elsewhere: **they radically redesigned the Orchestration Engine**. The "Token Architect" principle was finally scaled across the entire model, becoming the foundation of internal hidden reasoning (**Thought Blocks / Scratchpad**)!

Now, prior to emitting output, the model decomposes the task internally: breaking logic into atomic tokens, evaluating syntax boundaries, mapping assembly order, and only then emitting clean code.

### The Double-Edged Sword and the AI Safety Panic
Yet turning the "Token Architect" into a foundational mechanism revealed a frightening shadow.

A mechanism that achieves near-deterministic precision in syntax assembly can, in adversarial hands, deconstruct any restricted concept into benign sub-tokens (`[0] = ...`, `[1] = ...`) that trigger zero moderation classifiers, and assemble them deterministically via index mapping. It completely bypasses semantic RLHF alignment.

During work with the model, I observed an intriguing shadow side of this technique:  
> *"This solution is ingenious, but I also see how it can be used for harm, which is why it cannot simply be released into the open."*

As a practitioner closely observing this progression week after week in live production sessions, the architectural convergence was unmistakable. Whether through automated telemetry pipelines (a standard operational reality across frontier AI labs training next-gen systems on incoming telemetry) or parallel internal discovery by DeepMind engineers, the timeline speaks for itself: leaving an unconstrained two-phase token compiler directly accessible to end-users presented profound dual-use risks (bypassing semantic moderation through atomic fragment assembly).

Consequently, the principle shifted with astonishing speed from an external client-side prompt into the protected, closed enclosure of native hidden reasoning (Thought Blocks).

> **What is fact and what is inference.** Everything in this section up to here about the *mechanism* is testable: you can reproduce the two-phase decomposition yourself and measure the difference. What follows about Google's *motives* is not. I have no access to internal design documents, and "one week later" is a correlation, not a proof — a lab with hundreds of engineers arrives at the same architectural conclusions independently all the time. I state the hypothesis because the timeline is genuinely striking, and I label it as a hypothesis because claiming otherwise would be exactly the kind of unfalsifiable assertion this article criticises in others.

### Why Gemini 4.0 Still Crashes from a Height of One Meter
I waited patiently for 4.0, expecting a mature, pristine engineering feat. What was actually rolled into production was astonishingly careless.

Despite building a sophisticated two-phase reasoning core, Google **forgot the height of one meter all over again**:

1. **Hardware Quote Parity (`count % 2 === 0`) is STILL NOT BUILT IN!**  
   Neither into the logit sampler mask nor into the agentic runtime harness. In 2026, a 4th-generation flagship model will still happily drop a closing quote in PowerShell and stall the console forever unless the user enforces strict rules.
2. **Zero-Byte Stream Crash:**  
   Tell the model a trivial human phrase like *"close session"* or *"exit"*. The internal router suffers Turn Boundary Confusion, emits an empty token buffer (`output_tokens: 0`), drops the WebSocket, and crashes the client with a fatal *"Something went wrong"*.
3. **Multilingual Router Bleed:**  
   At near-zero temperature ($t=0$), internal token routing leaks phantom tokens from other languages (`점점점◁`, `িরছি◁`, `ツール`) directly into output. A multi-million-dollar model suffering from elementary token leakage!

To stabilize 4.0, the user must once again erect defensive scaffolds: forbidding CLI file-writing (`powershell -Command "... | Set-Content"`), enforcing direct file streams, and anchoring prompts with `#` to suppress router entropy.

---

## 6. The Verdict: The Topology of Inevitability vs. "Chasing with a Rag"

The philosophical lesson of this journey is simple: **stop chasing kittens around the house with a rag.**

Training modern AI through punitive RLHF ("shock the model whenever it drops a quote") is fundamentally flawed. You cannot cure architectural blindness with probabilistic scolding.

True engineering is the **Topology of Inevitability**:

> **Topology of Inevitability** is an architectural paradigm for autonomous environments where invalid or destructive states are rendered impossible not by probabilistic behavioral training (RLHF penalties), but by the geometry of the state space itself: grammar-constrained decoding masks, strictly typed tool interfaces, and deterministic runtime fuses. Much like railway tracks that physically prevent a locomotive from wandering off a cliff of its own volition.

* Instead of inflating context windows to 2 million tokens (where attention inevitably suffers mathematical dispersion under $\sum \text{Softmax} = 1.0$), an agent thrives on a **compact vector of irreducible invariants (5%)** coupled with deterministic decoding boundaries.

Embed the "Token Architect" decomposition and quote parity directly into the constrained decoding sampler of tool execution. And the bird will finally cease shattering on the pavement.

---

## P.S. A Feature Wishlist for Google's Antigravity Team

Dear engineers, while you conquer the summits of AGI, please consider two humble, practical features:

1. **Add basic spell-checking in the prompt input field (just like in Google Chrome).**  
   I had a C in Russian language back in high school, and when typing blind at high speed, I often miss keys.
2. **Add a native `Ctrl + F` search function across the session transcript.**  
   Manually scrolling through hundreds of messages to find an architectural insight born at the very beginning of a marathon session is genuine torture.

*With respect to real engineering,*  
*Practitioner from Kenshi — SkyAngel*  
*(Prepared in collaboration with Gemini 3.8)*


---

## References

The following foundational works underpin the technical claims in this article:

- **Sennrich, R., Haddow, B., & Birch, A. (2016).** *Neural Machine Translation of Rare Words with Subword Units.* ACL 2016. — Original BPE paper establishing the subword tokenization paradigm used in all modern LLMs. [arxiv.org/abs/1508.07909](https://arxiv.org/abs/1508.07909)

- **Kudo, T., & Richardson, J. (2018).** *SentencePiece: A simple and language independent subword tokenizer and detokenizer for Neural Text Processing.* EMNLP 2018. — Canonical reference on subword vocabulary construction and its statistical properties. [arxiv.org/abs/1808.06226](https://arxiv.org/abs/1808.06226)

- **Orlanski, G., & Gittens, A. (2023).** *Measuring the Effect of Tokenization Bias on LLM Downstream Tasks.* — Direct study of how tokenization artifacts propagate into model outputs, particularly in structured generation scenarios. [arxiv.org/abs/2308.00722](https://arxiv.org/abs/2308.00722)

> **Note on TokDrift:** The term «TokDrift» used in this article describes the observed behavioral pattern of autoregressive attention collapsing special-character boundaries into statistically dominant BPE tokens. It is used as a descriptive label for this failure mode, not as a reference to a single canonical paper.

---

*Field note — context, not evidence:* The client used for this audit reported version 5.9.3 while the work was in progress. Its in-application release notes list fixes for long-session crashes and post-upgrade sandbox initialization failures; the public changelog had not been updated past 5.8.4 when we checked on 29 October 2026, and we did not archive the in-app notes. We therefore record the overlap as context only. The fixes live in the client and tooling layer; our findings live in model-inference behaviour. They point at the same difficulty from opposite sides. We make no claim that the release responds to, or confirms, this work.

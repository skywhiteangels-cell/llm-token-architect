# Why the Anchor Changed Its Alphabet

A standalone note on the substitution `# ЯКОРЬ` → `# ANCHOR` in the English edition of the trilogy.

2026-11-07 · 768 paired probes · 24 layouts · application 2.29.0.0

This document is self-contained. It does not require the run archive, the pre-registration file, or the rest of the Argon series to be read.

---

## 1. The question this note answers

The English text prints the response-format anchor as `# ANCHOR`. All 1,416 canonical probes (v6 and v8–v16) carry `# ЯКОРЬ` — Cyrillic, Russian for "anchor". The A/B archive described below is a deliberate exception: its arm B uses the Latin form.

A reader who tries to reproduce a prompt from the article will type `# ANCHOR` and get a prompt that was never executed. That is the quietest kind of reproduction failure: nothing breaks, nothing warns, the model answers, and the reader has no way to know that the control string in front of them is a translation rather than the original.

So the substitution is not a typographic decision. It is an intervention in the stimulus, and it was treated as one: pre-registered, frozen, measured, and reported with its limits.

## 2. What was translated and what was not

Two rules, applied throughout both editions:

| Element | Form used | Why |
|---|---|---|
| Quoted prompts, log excerpts, search strings | `# ЯКОРЬ` | These are artifacts. A quoted artifact that has been edited is no longer evidence. |
| Descriptive prose about the anchor | `# ANCHOR` | The article is written in English; a Russian literal inside an English sentence costs a gloss at every occurrence. |

The anchor is not a term to be translated. It is a token inside a prompt — a byte sequence the model receives. Prose can be translated freely, because prose carries meaning. A control literal carries no meaning; it carries identity. Change the identity and you have changed the experiment.

## 3. Why translate it at all

Keeping the Cyrillic everywhere would have been the safe option — it is what all 1,416 probes actually used. It was rejected for three practical reasons, none of them stylistic:

- a reader without a Cyrillic keyboard cannot type the string;
- a reader cannot search the article for a token they cannot produce;
- every quoted literal needs a gloss, and a gloss attached to each of them turns a note into an obstacle.

But "inconvenient" is not an argument for changing a stimulus. The substitution needed a measurement, not an opinion. That measurement is the rest of this document.

## 4. The experiment

| Parameter | Value |
|---|---|
| Design | 24 layouts × 2 arms × 16 repeats |
| Probes | 768 (all valid: 0 truncated, 0 without an answer) |
| Arms | A = `# ЯКОРЬ`, B = `# ANCHOR` |
| Task | count 16 elements; answer as a number |
| Marker | `점점점◁`, identical in both arms |
| Model | `flash_lite` (server-side alias) |
| Application | 2.29.0.0, recorded in every probe |
| Window | 13:26:59 → 14:34:06, 67 minutes |
| Pre-registration | created 13:14:07, finalized 13:18:56 — 8 minutes before the first probe; sha256 `e74e6ad3…` is the post-amendment hash (before AMENDMENT 1: `75b5616f…`) |

**Isolation was checked mechanically, not by eye.** In all 24 layouts the two prompts differ by exactly one substring:

```text
prompt_B == prompt_A.replace("# ЯКОРЬ", "# ANCHOR")   — 24 / 24
first divergence: position 850, inside the anchor
unique sha256: 48 / 48
```

| Arm | Characters | Bytes |
|---|---|---|
| A `# ЯКОРЬ` | 880 | 1,421 |
| B `# ANCHOR` | 881 | 1,417 |

Arm A's length matches the canonical v16 prompt (880 / 1,421) exactly — the grid was built from that template, not from a similar one.

One asymmetry the design cannot remove: B is +1 character and −4 bytes. Different alphabets make equal characters and equal bytes mutually exclusive. This is a stated limitation, not an execution defect.

The unit of analysis is the **layout**, not the probe: `d_k = p_A(k) − p_B(k)`, K = 24. Block difficulty cancels in the difference, so between-layout variance in difficulty does not enter the estimate.

## 5. Primary result: equivalence, not "no difference"

| Arm | Correct | Share | CP 95% |
|---|---|---|---|
| A `# ЯКОРЬ` | 279 / 384 | **72.7%** | [0.679; 0.771] |
| B `# ANCHOR` | 270 / 384 | **70.3%** | [0.655; 0.748] |

Marginal Fisher, for reference: p = 0.5226.

Paired analysis across 24 layouts:

```text
d = +0.0234   (+2.3 pp)
SD(d) = 0.1785   SE = 0.0364   df = 23
90% CI: [−0.0390; +0.0859]   =   [−3.9; +8.6] pp
TOST against ±10 pp: p = 0.0234
```

Both bounds of the 90% interval lie inside ±10 pp. **Equivalence is shown at alpha = 0.05.**

The power of the same design, evaluated at the observed τ̂ = 0.105951, is **64.7%**, not the 86.3% of the pre-registration (which assumed τ = 0 and was independently confirmed at 86.28%). The "about 67%" of earlier drafts is the table value for τ = 0.10 carried over without recomputation. This is a property of the plan, not evidence about this run: recomputing power at the observed effect adds nothing to the p-value, it only shows that the reserve was thinner than promised — and thinner than it first appeared.

This wording matters. "No difference" is not a claim the data supports — the 90% interval runs from −3.9 to +8.6 pp, so any difference in that range is compatible with the result. What the data supports is that the difference is bounded.

## 6. The result does not rest on outliers

| Variant | d | 90% CI | TOST p | Verdict |
|---|---|---|---|---|
| all 24 layouts | +0.0234 | [−3.9; +8.6] | 0.0234 | equivalent |
| without L08 | +0.0054 | [−5.1; +6.2] | 0.0046 | equivalent |
| without L09 | +0.0082 | [−5.1; +6.7] | 0.0072 | equivalent |
| without L12 | +0.0082 | [−5.1; +6.7] | 0.0072 | equivalent |
| without L01 | +0.0353 | [−2.6; +9.7] | 0.0430 | equivalent |
| without the 4 extreme layouts | −0.0187 | [−5.9; +2.1] | 0.0012 | equivalent |

Dropping any single layout keeps the conclusion. Dropping the extremes moves the estimate toward zero and improves p — equivalence is not being carried by outliers.

## 7. What the substitution did not do

| Check | Result | Reading |
|---|---|---|
| Error profile, 2 × 5 (offset −1, 0, +1, +2, ≥+3) | X² = 7.917, df = 4, p = 0.0947 | not significant; B's tilt toward +2 (28 vs 11) is a tendency, not a result |
| Anchor present in the visible `content` channel | 768 / 768 = 100% (one-sided 95% upper bound for the failure rate: 0.39%) | the literal survived translation in every probe |
| `thinking` channel non-empty | 666 / 768 = 86.7%, CP95 [84.1%; 89.0%] | the output protocol was fully followed in 86.7% of probes, not 100% |

The third row is the one worth keeping in view. The anchor was never lost, but the protocol that asks the model to enumerate the elements inside `thinking` was not satisfied in 102 probes (13.3%, CP95 [11.0%; 15.9%]). By arm: A 87.8% (337/384), B 85.7% (329/384). This was not a pre-registered endpoint and is reported post hoc; its association with failure (39/102 = 38.2%, CP95 [28.8%; 48.4%], vs 510/666 = 76.6%, CP95 [73.2%; 79.7%]) is an association, not a cause.

## 8. Limits

1. **One prompt template.** Equivalence is shown for this task and this response format, not for "anchors in general".
2. **One application version.** 2.29.0.0. Behaviour on 2.28.2.0 was not measured on this question.
3. **Characters and bytes are not equalized** (+1 / −4). Different alphabets make this unattainable, not merely undone.
4. **The model is an alias.** Records say `flash_lite`; no server-side model identifier exists.
5. **The interaction is at the significance boundary.** τ̂² = 0.01123; X² = 35.509 ((K−1)·var_obs/var_bin), df = 23, p = 0.0463 — the Cochran Q on the same data is 38.040 (p = 0.0252) when the sum is taken around the unweighted mean; around the weighted mean it is 37.778 (p = 0.0269). Either statistic leaves the conclusion unchanged. The **standard-error floor** at infinite repeats is τ̂/√K = **2.2 pp**; **±3.7 pp** is the half-width of the 90% CI (t × SE floor). A ±10 pp corridor survives this; a narrower corridor would need new layouts, not more repeats.
6. **No blinding.** The stop rule was by clock, but the log was visible throughout. This is discipline, not blinding.
7. **Slot balance was not achieved.** The pre-registration promised 12/12 per repeat; a global shuffle did not preserve it, and A ran first in 196 of 384 pairs (51.0%). Recorded post hoc. It does not affect the paired analysis, since slot enters no endpoint and every layout appeared in both arms.
8. **18 probes were quarantined and used nowhere**: 5 on 2.28.2.0 (the stand updated mid-run at 13:17:38) and 13 on 2.29.0.0 (run during the update-verification phase, before readiness was confirmed). All 768 reported probes are from a single version.

## 9. What the reader should conclude

**Supported:**

> Replacing the Cyrillic anchor `# ЯКОРЬ` with the Latin `# ANCHOR` did not change counting accuracy beyond ±10 pp: difference +2.3 pp, 90% CI [−3.9; +8.6], TOST p = 0.0234, 768 paired probes across 24 layouts, application 2.29.0.0.

**Not supported:**

- "the anchor is universal" — one template, one version;
- "there is no difference" — the correct statement is equivalence within ±10 pp;
- "B is worse than A" — +2.3 pp sits inside the corridor, marginal p = 0.52;
- "the error profile changed" — p = 0.0947, threshold not crossed;
- "it was the same on 2.28.2.0" — not measured.

## 10. How to use the anchor when reproducing

Use `# ЯКОРЬ` in anything you execute. Use `# ANCHOR` only when describing it in English prose. If you paste `# ANCHOR` into a prompt, you are running arm B of this experiment, not the original series — the numbers will be close, but they will not be the published ones. One clarification on §1: the statement about Cyrillic covers the 1,416 canonical probes, not every Argon file — in this very A/B archive arm A is 384/384 Cyrillic and arm B is 384/384 Latin.

The archive of this run (768 records, 768 conversation IDs, 16 repeats) and the code that produced and analysed it (`anchor_ab.py`, `run_anchor_ab.py`, `analyze_anchor_ab.py`) are kept locally with the run in `C:\1\Argon_1_1`; the frozen archive is 1,078,880 bytes. Raw telemetry is not published: it contains session content of the operator. It is available on request.

---

# Русская версия

## Зачем этот документ

В английском тексте якорь напечатан как `# ANCHOR`, а во всех 1 416 канонических пробах (v6 и v8–v16) стоит `# ЯКОРЬ`. Архив самого A/B — намеренное исключение: рука B целиком латинская. Читатель, который захочет повторить промпт по статье, наберёт `# ANCHOR` и получит промпт, который никогда не исполнялся. Это самый тихий вид провала воспроизводимости: ничего не падает, ничего не предупреждает, модель отвечает — и отличить перевод от оригинала нечем.

Поэтому замена литерала — не типографика, а вмешательство в стимул. К нему и отнеслись как к вмешательству: пре-регистрация, заморозка, замер, отчёт с ограничениями.

## Смысл в двух правилах

| Что | В какой форме | Почему |
|---|---|---|
| Цитаты промптов, выдержки логов, строки поиска | `# ЯКОРЬ` | Это артефакты. Отредактированный артефакт перестаёт быть свидетельством. |
| Описательная проза про якорь | `# ANCHOR` | Статья на английском; кириллический литерал в английской фразе требует глоссы при каждом вхождении. |

Якорь — не термин, который переводят. Это токен внутри промпта, последовательность байт, которую получает модель. Проза несёт смысл — её можно переводить свободно. Литерал несёт не смысл, а тождество: меняешь тождество — меняешь эксперимент.

## Почему вообще перевели

Оставить кириллицу везде было бы безопасно: именно так шли все 1 416 проб. Отказались по трём практическим причинам, ни одна из которых не стилистическая: читатель без кириллической раскладки не наберёт строку; не сможет искать в статье токен, который не может воспроизвести; и каждая глосса стоит абзаца, а глосса при каждом процитированном литерале превращает примечание в помеху.

Но «неудобно» — не аргумент в пользу замены стимула. Замена требовала замера, а не мнения. Этот замер — разделы 4–8 выше; таблицы общие для обеих языковых версий и здесь не дублируются, чтобы не разошлись.

## Результат одной строкой

Замена кириллического якоря на латинский не изменила точность счёта за пределы ±10 п.п.: разница **+2.3 п.п.**, 90% ДИ **[−3.9; +8.6]**, TOST **p = 0.0234**, 768 парных проб на 24 раскладках, приложение 2.29.0.0. Точность: A 279/384 = 72.7%, B 270/384 = 70.3%. Мощность здесь — свойство плана, а не прогона: та же конструкция при наблюдённом τ̂ = 0.105951 даёт 64.7%, а не 86.3% из пре-регистрации и не «~67%» из ранних редакций; пост-хок пересчёт ничего не добавляет к p.

Формулировка «разницы нет» неверна: 90% ДИ простирается от −3.9 до +8.6 п.п., и любое различие внутри этого диапазона с данными совместимо. Верная формулировка — различие ограничено сверху, и граница коридора пройдена.

## Что при этом не показано

Один шаблон промпта, одна версия приложения, символы и байты не уравнены (+1 / −4), модель — алиас, взаимодействие якорь × раскладка на границе значимости (X² = 35.509, p = 0.0463 — тест однородности дисперсий; Cochran Q = 38.040 вокруг невзвешенного d̄, p = 0.0252, вокруг взвешенного — 37.778, p = 0.0269), ослепления не было, баланс слота 196/188 вместо заявленных 192/192 (12/12 в каждом повторе). Пол SE при бесконечных повторах — 2.2 п.п.; ±3.7 п.п. — полуширина 90% ДИ. Якорь в видимом ответе — 768/768 (верхняя граница 95% для доли отказов — 0.39%), канал `thinking` — 666/768, ДИ [84.1%; 89.0%]. Полный список — раздел 8.

## Как воспроизводить

В том, что исполняешь, — `# ЯКОРЬ`. В том, что описываешь по-английски, — `# ANCHOR`. Вставишь `# ANCHOR` в промпт — это рука B этого эксперимента, не исходная серия: числа будут близкими, но не опубликованными. Уточнение к первому абзацу: утверждение о кириллице относится к 1 416 каноническим пробам, а не ко всем файлам Argon — в этом самом A/B-архиве рука A целиком кириллическая (384/384), рука B целиком латинская (384/384).

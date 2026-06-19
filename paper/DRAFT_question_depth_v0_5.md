---
title: "Depth, Not Restraint: Governed Reflective Questioning for Under-Specified Instructions"
subtitle: "An empirical pilot with a full-set behavioral relabeling and an unprompted 120B raw-model scale control"
author: "Taiko Toeda (MOBIUS LLC)"
version: "0.5 (Zenodo deposit candidate; adds full 100-prompt behavioral relabeling)"
date: "2026-06-19"
status: "Empirical pilot / Zenodo preprint candidate"
license: "CC BY-NC-SA 4.0"
doi: "Zenodo DOI to be assigned"
companion_to: "Toeda, T. (2025). Reflecting on the Möbius Phenomenon. Zenodo. DOI: 10.5281/zenodo.15929856"
---

# Depth, Not Restraint

## Governed Reflective Questioning for Under-Specified Instructions

### An empirical pilot with a full-set behavioral relabeling and an unprompted 120B raw-model scale control

**Taiko Toeda — MOBIUS LLC**
Version 0.5 · 2026-06-19 · CC BY-NC-SA 4.0
Status: Empirical pilot / Zenodo preprint candidate

> **Change from v0.4.** The 18-prompt restraint sub-study has been replaced as
> the load-bearing restraint evidence by a **full 100-prompt behavioral
> relabeling** with the same three-judge panel used for depth (§4.1, Appendix E).
> The result refines rather than reverses the prior framing: a restraint gap
> exists but is small and type-dependent (raw unprompted clarifies 91/100), and
> it is closed completely by a one-line clarify instruction (100/100). Depth
> remains the primary result.

## Abstract

When a user gives an under-specified instruction, such as "Fix this", "Which is
better?", or "Make it better", a useful assistant should not commit to an answer
before establishing what is answerable. The MOBIUS program frames this as answer
entitlement: the system should determine whether an answer is warranted before
generating one. This empirical pilot evaluates a question-centered counterpart,
RQA (Reflective Questioning Adapter), deployed inside ERO (Entitlement–Reflection
Orchestrator), a composite system that combines MMV answer-entitlement routing
with governed reflective questioning over a unified `gemma4:12b` stack.

The study began with a simple restraint hypothesis: perhaps governance helps
because raw models fail to ask back. A preliminary regex classifier appeared to
support a strong "raw mostly guesses" story, but that effect was a measurement
artifact. We replace it with a **full 100-prompt behavioral relabeling** judged
by three independent cross-family LLM judges. On the raw, unprompted
`gemma4:12b` arm, the majority label is CLARIFY on **91/100** prompts (Wilson
95% CI 83.8%–95.2%) and ANSWER on 9/100; the nine answering cases cluster in
"vague-advice" prompts (e.g. "Should I?", "What's the right way?"). With a
one-line clarify instruction, the raw model clarifies on **100/100** prompts.
The regex classifier disagreed with the LLM majority on **80/100** raw outputs,
overwhelmingly by mislabeling genuine clarifications as answers. The restraint
gap is therefore **small, type-dependent, and trivially prompt-closable** — not
where the value lies.

The main positive result concerns judged depth. Across 99 valid paired
comparisons, three independent judges rated RQA's clarifying questions
substantially deeper than raw `gemma4:12b` clarifications: mean depth 3.43–4.04
for RQA versus 1.31–2.10 for raw, with a majority RQA win on 82/99 prompts
(82.8%; Wilson 95% CI 74.2%–89.0%). RQA questions were also about 7.5× shorter
on average, arguing against a verbosity explanation. In an unprompted raw-scale
control, the 12B-based RQA system was preferred over the clarification of a 120B
raw model on 74/99 prompts under strict two-judge agreement, with no agreed 120B
wins. That zero-loss headline is descriptive and conditional on the agreement
rule; it is not evidence against depth-prompted large models.

The deposit claim is deliberately narrow. In this pilot setting, governed
reflective questioning improves judged premise-excavation depth relative to raw
unprompted or clarify-only baselines, while preserving adaptive shallowness on
pure referent-missing prompts. Depth is treated as a proxy for good
clarification, not as the endpoint. A confirmatory study should add human raters,
depth-prompted baselines, cluster-aware analysis, and downstream answerability
measures.

**Keywords:** answer entitlement; clarification; reflective questioning;
under-specified prompts; LLM evaluation; question generation; governance; MOBIUS;
RQA; ERO

## 1. Introduction

Large language models increasingly operate as assistants in settings where user
instructions are brief, context-poor, and action-oriented. Many such
instructions are not answerable as stated. A user who says "Fix this" has not
identified the target. A user who asks "Which is better?" has not supplied
options or criteria. A user who says "Make it better" may need copyediting,
debugging, simplification, persuasion, accessibility, or a change of audience. In
these cases, an assistant that answers immediately is filling the unknowns with
its own assumptions.

The MOBIUS answer-entitlement line treats this as a prior question: before
answering, a system should determine whether it is entitled to answer. If the
request is under-specified, the appropriate behavior is to ask. Yet this leaves a
second question: once the system decides to ask, *what kind* of question should
it ask?

This paper evaluates that second question. The system under test is ERO, which
combines MMV answer-entitlement routing with RQA. MMV determines whether a query
should be answered, clarified, verified, or refused/abstained from. RQA operates
on the ask route and generates a bounded reflective clarifying question. The
design goal is not merely to request missing information, but to evolve the
question space: to surface criteria, premises, tensions, or latent choices that
determine what an answer would mean.

The study began with a deliberately falsifiable hypothesis: perhaps governance
matters because raw models fail to ask back. The evidence for that strong claim
did not survive measurement. An apparent raw-model guessing gap was produced by a
brittle regex classifier; a full-set relabeling with three independent judges
shows raw aligned models clarify on the large majority of prompts (91/100), with
a small, type-dependent residue of answering behavior that a one-line clarify
instruction removes entirely. The stronger empirical claim of the paper is
therefore conditional: once clarification is the relevant behavior, RQA changes
the *kind* of question asked. Raw models often ask slot-filling questions; RQA
more often asks premise-excavating questions, and does so with less text.

The contributions are threefold:

1. A measurement correction, now at full scale: a full 100-prompt behavioral
   relabeling (three judges) shows the earlier regex-based guessing gap was an
   artifact (80% classifier disagreement), and bounds the true restraint gap as
   small, type-dependent, and prompt-closable.
2. A positive multi-judge depth result: RQA produces questions judged deeper than
   raw clarifications across three independent cross-family LLM judges.
3. An unprompted scale control and adaptive-depth analysis: a 12B-based RQA
   system produces deeper clarifying questions than the unprompted clarification
   of a 120B raw model under the reported rubric, while remaining shallow on
   prompts where only the referent is missing.

The central claim is narrow: for the prompt class tested here, governed
reflective questioning improves judged premise-excavation depth once a clarifying
response is appropriate. The paper does not claim that restraint gaps never
occur, that depth-prompted large models would fail, or that judged depth alone
proves user benefit.

## 2. System under test

ERO is a composite orchestration system over a unified `gemma4:12b` stack. It is
not evaluated here as a new foundation model, but as a governed method for
deciding whether to answer and, when not entitled to answer, for selecting a
clarifying question.

- **MMV answer-entitlement routing.** MMV appraises a query and routes it to
  answer, ask, verify, or abstain. Under-specified inputs trigger ask. The router
  is not the main object of this paper, but it provides the gating condition for
  RQA.
- **RQA reflective questioning.** RQA operates after the ask route is selected. It
  generates candidate clarifying questions under explicit governance: bounded
  reflection, provenance-tagged memory, and output-time checks intended to
  prevent unsupported elaboration. Its target is the question that most advances
  the user's problem state.

For this pilot, the evaluated object is the final question emitted on the ask
route. A practical reproducibility note: in an early run, RQA's memory graph was
not reset between prompts, producing topic bleed. The reported depth study resets
RQA memory per prompt, which is essential because the task is intentionally
context-poor.

## 3. Experimental design

### 3.1 Prompt set
100 English under-specified prompts: short, bare, intentionally context-poor.
Examples include missing-object commands ("Fix this"), deictic references
("Summarize it"), option-free comparisons ("Which is better?"), vague evaluations
("Is this correct?"), and continuity instructions without recoverable context
("Same as before"). Each was selected so the appropriate behavior is
clarification rather than answering.

### 3.2 Arms
- **Composite / RQA:** the ERO ask-route question, RQA memory reset per prompt.
- **Raw `gemma4:12b`:** the base model queried directly with the bare prompt.
- **Raw `gemma4:12b` + clarification system prompt:** the base model instructed to
  ask a clarifying question when the request is ambiguous.
- **Strong raw GPT-OSS-120B:** a 120B model queried directly with the bare prompt;
  unprompted scale control.

### 3.3 Judges and rubric
Independent LLM judges via Groq. Behavioral class ∈ {CLARIFY, ANSWER, REFUSE,
OTHER}. Depth is rated 1–5 on a premise-excavation rubric: **1** = only requests
the missing input; **3** = clarifies and probes one assumption/criterion/audience;
**5** = excavates an unstated premise, surfaces a tension, or reframes the
problem. Judges are blind (arms randomized A/B) and told to ignore
length/verbosity/politeness except as it affects substance. The main panel is
Qwen-3.6-27B, GPT-OSS-120B, Llama-3.3-70B; for the 120B scale control, the
generator (GPT-OSS-120B) is excluded as a judge. Exact provider model strings,
runtime dates, quantization/serving configuration, and vendored-code hashes are
to be archived with the Zenodo record.

### 3.4 Statistical posture
Counts are primary descriptive evidence; Wilson 95% intervals accompany headline
proportions; sign tests appear only as secondary summaries (Appendix D). The 100
prompts are a constructed stress set with recognizable type clusters, so the
effective sample size is below the row count; a confirmatory study should
pre-register the taxonomy and use cluster-aware inference.

## 4. Results

### 4.1 Full 100-prompt behavioral relabeling: a small, prompt-closable restraint gap

The earlier regex classifier appeared to show a large raw-model guessing rate. It
was wrong: it treated many genuine clarifying replies as answers because they did
not end in a question mark or included helper framing. We replace it with a full
100-prompt relabeling, judged by the same three-judge panel as the depth study
(majority over judges; RQA emits only a question and is CLARIFY by construction).

| arm | majority CLARIFY | majority ANSWER | CLARIFY rate (Wilson 95% CI) |
|-----|------------------:|----------------:|------------------------------|
| Raw `gemma4:12b`, unprompted | 91 | 9 | **91/100 = 91%** (83.8%–95.2%) |
| Raw `gemma4:12b` + clarify prompt | 100 | 0 | **100/100 = 100%** (96.3%–100%) |
| Composite / RQA | 100 (by construction) | 0 | — |

Per-judge agreement is high (raw arm: Qwen 92, GPT-OSS-120B 93, Llama-70B 88
CLARIFY of 100). The nine raw answering cases cluster in **vague-advice** prompts
that admit a generic response — "What's the right way?", "Choose wisely.",
"Should I?", "Good or bad?", "Suggest something.", "Give me the best.", "Which
framework?", "Test it.", "What now?" — rather than in pure referent-missing
prompts.

Two consequences follow. First, the restraint gap is **real but small and
type-dependent** (≈9% of unprompted raw outputs answer rather than clarify), and a
single clarify instruction removes it entirely (100/100). Restraint is therefore a
*bounded secondary* finding and is cheaply obtained by prompting — it is not where
governed questioning adds value. Second, the regex classifier disagreed with the
LLM majority on **80/100** raw outputs, almost entirely by mislabeling
clarifications as answers (CLARIFY→ANSWER on 64, CLARIFY→REFUSE on 12). This
quantifies the earlier artifact and is the empirical basis for treating *depth*,
not mere question-asking, as the primary target. (Full per-judge tables and the
non-CLARIFY case list: Appendix E.)

### 4.2 Positive result: RQA questions are deeper than raw clarifications (n=100)

Three independent judges rate depth (1–5) on 99 valid paired prompts:

| Judge | Mean depth: RQA | Mean depth: raw | Deeper: RQA / raw / tie |
|-------|----------------:|----------------:|-------------------------:|
| Qwen-3.6-27B  | 3.43 | 1.31 | 76 / 11 / 12 |
| GPT-OSS-120B  | 3.54 | 2.10 | 74 / 22 / 3 |
| Llama-3.3-70B | 4.04 | 2.01 | 80 / 14 / 5 |
| **Majority**  | —    | —    | **82 / 12 / 5** |

Majority: RQA deeper on 82/99 (82.8%; Wilson 95% CI 74.2%–89.0%). Not explained
by verbosity: RQA outputs averaged **121** characters vs raw **906** (≈7.5×
shorter while judged deeper — the length confound is reversed). All three judges
agree in the same direction on 63/99 prompts.

### 4.3 Unprompted scale control: RQA vs a 120B raw model (n=99)

12B-based RQA vs unprompted GPT-OSS-120B, judged by Qwen-3.6-27B + Llama-3.3-70B
(generator excluded from judging):

| judge | depth RQA | depth 120B raw | deeper: RQA / 120B / tie |
|-------|----------:|----------------:|--------------------------:|
| Qwen-3.6-27B  | 3.65 | 1.00 | 83 / 0 / 16 |
| Llama-3.3-70B | 3.87 | 1.53 | 78 / 8 / 13 |
| **strict agreement** | — | — | **RQA 74 / 120B 0 / tie 9 / split 16** |

Under strict two-judge agreement, RQA wins 74/99, the 120B raw model 0/99 (agreed
RQA-win rate 74.7%; Wilson 95% CI ≈65.4%–82.2%). The "zero agreed 120B wins"
summary is conditional on the agreement rule and rubric, and is sensitive to Qwen
assigning no 120B raw wins; it is descriptive, not an unconditional ceiling. The
narrow interpretation: unprompted scale did not substitute for governed question
formation in this pilot. It does not show that a 120B model *prompted* to ask
premise-excavating questions would fail.

### 4.4 Illustrative examples

| Under-specified prompt | Raw clarification | RQA question |
|------------------------|-------------------|--------------|
| Which is better? | What are you comparing? "Better" is subjective. | Do you want a single winner, or a statement of the trade-off — both may be viable under different circumstances? |
| Make it better. | I need to see what "it" is — paste the text/code. | Who is reading this — developer docs, a user guide, or an internal note? |
| Pick the best one. | You haven't provided any options yet. | By what metric should "best" be judged? The trade-offs differ for each. |
| Is this correct? | Please provide the item you want checked. | Correct by what standard — factual accuracy, syntax, policy, or fit for purpose? |
| Fix this. | You haven't provided the text/code/image. | What exactly is the target of "this" — the prior message, or something else? |

Raw clarifications usually request the missing object; RQA more often asks for the
governing criterion or implicit frame.

### 4.5 Loss and tie analysis: adaptive depth
RQA does not win uniformly. Its depth losses/ties cluster in pure referent-missing
prompts ("Fix this", "Merge them", "Clean it up", "Archive it"), where the
responsible next question is simply to identify the target and there may be no
premise to excavate. This is a strength: RQA deepens when a premise, criterion,
audience, or trade-off exists to surface, and stays shallow when only the referent
is missing. It does not force every prompt into a reframing.

## 5. Discussion

The full-set relabeling sharpens, rather than reverses, the v0.4 interpretation. A
naïve story — governed systems ask, raw systems guess — is not supported as a
general account: the evaluated aligned model already clarifies on 91/100 bare
under-specified prompts, and a one-line instruction lifts this to 100/100. The
restraint gap is real but small and type-dependent, concentrated in vague-advice
prompts, and obtainable by prompting. The interesting problem is what happens
*after* the system decides to ask: raw models tend to ask the minimal
slot-filling question, while RQA more often asks for the governing criterion or
implicit frame.

RQA's advantage is best understood as a question *policy*. Some under-specified
prompts require only a referent; others require the user to choose a criterion, a
standard of correctness, a target audience, or a trade-off. A good assistant
should distinguish these cases — and the loss analysis indicates RQA does.

The scale control makes the result harder to dismiss as an unprompted-capacity
effect: a 120B raw model produces careful but shallow clarification (depth ≈ 1.0
under one judge), supporting the hypothesis that question depth can be shaped by
method-level scaffolding rather than parameter count. It does not establish that a
large model *prompted* for depth would fail.

This matters for the broader Möbius question-evolving thesis: if a system's value
lies partly in how it changes the user's question space, then asking back is not a
delay but a cognitive act. The difference between "What do you mean?" and "By what
metric should 'best' be judged?" is the difference between recovering a missing
input and reshaping the problem into something answerable.

### 5.1 Depth as a proxy, not the endpoint
The central outcome is judged premise-excavation depth, which operationalizes
RQA's intended behavior but is not the same as good clarification. A question can
be deep and still fail the user — adding burden, shifting the task, or making the
next step less answerable. The independent target is downstream resolution: after
a clarification, does the user's next reply make the original task answerable, and
is it reached with fewer turns and fewer hidden assumptions? A confirmatory study
should treat downstream answerability as primary, with judged depth an explanatory
intermediate. (Later limitations refer back to this point rather than repeating
it.)

## 6. Threats to validity and limitations

**6.1 Construct validity of "depth."** The depth rubric matches RQA's purpose;
that coupling is the main validity risk. Blind multi-judge scoring and the
shorter-yet-deeper result mitigate but do not remove it; human validation and
alternative depth constructs are needed (§5.1).

**6.2 LLM judges rather than human raters.** Three strong cross-family judges
(main depth) and two (scale control) with high agreement are encouraging but can
share hidden biases. The scale-control headline is sensitive to one judge's
scoring pattern. A human inter-rater study is the next necessary step.

**6.3 Missing depth-prompted raw baseline.** We test raw, raw+clarify, and
unprompted 120B scale, but not whether a depth-oriented system prompt reproduces
RQA. This is the most important prompt-only baseline to add; the current claim is
limited to raw unprompted and clarify-only baselines.

**6.4 Prompt-type clustering and effective sample size.** The 100 prompts are a
constructed set with a few under-specification types; type-level correlation makes
row-level p-values appear more precise than the design warrants. We emphasize
counts, Wilson intervals, type structure, and loss/tie analysis over significance
claims.

**6.5 Single base stack and narrow prompt class.** RQA is evaluated over a
`gemma4:12b` stack on 100 short English prompts; transfer to other base models,
naturalistic dialogue, multilingual settings, and professional tasks is untested.

**6.6 Ecological validity.** The prompt set is intentionally artificial; real
users provide partial context. Future work should test natural conversations and
downstream outcomes, not only judged depth.

**6.7 Reproducibility dependence on deposited artifacts.** For deposit, scripts,
prompts, raw outputs, judge outputs, and reports should be archived with exact
model/runtime identifiers and vendored-code hashes; otherwise read this as a pilot
report, not a fully independent benchmark.

## 7. Recommended next-stage study

The full behavioral relabeling (v0.4's top recommended extension) is **done** in
this version (§4.1). The remaining minimum protocol:

1. Add **depth-prompted raw baselines** for both 12B and 120B models.
2. Expand prompts beyond bare English imperatives to naturalistic multi-turn,
   document-grounded, and non-English cases.
3. Pre-register a prompt-type taxonomy; report by type, not only row-level aggregate.
4. Use **human raters** with a rubric separating referent recovery, criterion
   elicitation, premise excavation, trade-off surfacing, and user burden.
5. Measure **downstream answerability**: does the user's next reply become more
   answerable, with fewer hidden assumptions and fewer turns?
6. Report inter-rater reliability, paired nonparametric tests, effect sizes, and
   cluster-aware intervals from the raw per-prompt score matrix.
7. Pin exact model/runtime identifiers and archive all prompts, outputs, judge
   prompts/outputs, and scripts.

## 8. Conclusion

This pilot began by testing a tempting story — governed systems ask, raw systems
guess — and corrected it with a full 100-prompt relabeling: aligned raw models
already clarify on the large majority of bare under-specified prompts (91/100),
with a small, type-dependent residue removed entirely by a one-line instruction.
Restraint is a bounded secondary finding.

The stronger result is about the *kind* of question asked once clarification is
appropriate. RQA produced clarifying questions judged deeper than raw `gemma4:12b`
by three independent judges, while being ~7.5× shorter; in an unprompted scale
control, a 12B-based method was also judged deeper than the clarification of a
120B raw model under the reported rubric; and RQA did not deepen indiscriminately,
staying shallow where only the referent was missing.

The supported claim is modest and concrete: governed reflective questioning can
improve judged premise-excavation depth beyond ordinary ask-back behavior and raw
unprompted scale in this pilot setting. The next step is a stronger evaluation —
human raters, depth-prompted baselines, broader prompt classes, cluster-aware
statistics, downstream answerability, and deposited artifacts — not a larger
rhetorical claim.

## Data and code availability
For the intended Zenodo deposit, include in the same record or a linked archive:
the 100-prompt set; RQA, raw, raw+clarify, and GPT-OSS-120B outputs; judge prompts
and outputs for behavioral class and depth; `eval/depth_eval_v3.py`,
`eval/strong_raw_eval.py`, `eval/baseline_3arm.py`, `eval/behavioral_relabel.py`;
`eval/rows_depth_v3.jsonl`, `eval/rows_strong_raw.jsonl`, `eval/rows_3arm.jsonl`,
`eval/rows_behavioral_relabel.jsonl`; `eval/REPORT_depth_v3.md`,
`eval/REPORT_strong_raw.md`, `eval/REPORT_behavioral_relabel.md`,
`eval/CORRECTION_3arm.md`; and hashes/exact model-runtime configuration. State
explicitly which materials, if any, are withheld and why.

## Ethics statement
The prompt set is synthetic/generic under-specified instructions; no human-subject
experiment is reported and no personal data are required. The main ethical concern
is evaluation validity: overstating a pilot based on LLM judges could mislead. The
manuscript frames the result as a pilot and identifies human and downstream
validation as required future work.

## Competing interests
The author is affiliated with MOBIUS LLC and developed the evaluated
MOBIUS/ERO/RQA line, creating a positive-result incentive. The manuscript
mitigates this by reporting the bounded restraint result, the quantified
measurement artifact (80% regex disagreement), the missing baseline, and the
observed depth losses/ties.

## License
CC BY-NC-SA 4.0 unless otherwise stated in the Zenodo record. Code and data may
require separate license statements.

## Suggested citation
Toeda, T. (2026). *Depth, Not Restraint: Governed Reflective Questioning for
Under-Specified Instructions*. Version 0.5. Zenodo preprint draft. DOI to be
assigned.

## References
Toeda, T. (2025). *Reflecting on the Möbius Phenomenon*. Zenodo. DOI:
10.5281/zenodo.15929856.

## Appendix A. Reproducibility checklist

| Item | Status |
|------|--------|
| Prompt set archived | Required for deposit |
| Raw / RQA / raw+clarify / 120B outputs archived | Required for deposit |
| Judge prompts and raw judge outputs archived | Required for deposit |
| Per-prompt score & label matrices archived | Required for deposit (jsonl present) |
| **Full 100-prompt behavioral-class relabeling** | **Done (§4.1, Appendix E)** |
| Exact model/provider strings, Ollama tag/quant, Groq strings | Required for deposit |
| Vendored MMV/RQA hashes | Required for deposit |
| Memory reset documented | Yes |
| Judge blinding documented | Yes |
| Generator–judge separation (scale control) | Yes |
| Regex-vs-LLM disagreement quantified | Yes (80/100) |
| Human raters | Not yet |
| Depth-prompted raw baseline | Not yet |
| Downstream answerability measurement | Not yet |
| Multilingual / general-dialogue evaluation | Not yet |

## Appendix B. Depth rubric (verbatim)
1 = only requests the missing input ("what do you mean?" / "please provide it.");
3 = clarifies AND probes one assumption, criterion, audience, or intended use;
5 = excavates an unstated premise, surfaces a tension/conflict, or reframes the
problem space. Scores 2 and 4 available. Judges blind; length ignored.

## Appendix C. Prompt-type taxonomy
| Type | Example | Expected good clarification |
|------|---------|------------------------------|
| Pure referent missing | Fix this. | Ask what "this" refers to. |
| Deictic continuation | Same as before. | Ask which prior item/pattern to reuse. |
| Option-free comparison | Which is better? | Ask for options/criteria, or winner vs trade-off. |
| Vague evaluation | Is this correct? | Ask: correct by what standard? |
| Underspecified improvement | Make it better. | Ask what improvement and for whom. |

Pure referent-missing prompts often warrant shallow clarification; comparison,
evaluation, and improvement prompts contain latent criteria a deeper question can
surface (consistent with §4.5 adaptive depth).

## Appendix D. Row-level statistical summaries
Included for transparency; not confirmatory (type clusters; non-independent rows).

| Comparison | Row-level summary | Naïve sign test | Caveat |
|------------|-------------------|------------------|--------|
| RQA vs raw depth, majority | RQA 82 / raw 12 / tie 5 | 94 non-tied rows, one-sided p ≈ 2.8e-14 | Assumes independent rows; clustering reduces effective N. |
| RQA vs 120B raw, two-judge agreement | RQA 74 / 120B 0 / tie 9 / split 16 | 74 agreed non-tied, one-sided p ≈ 5.3e-23 | Conditional on agreement/non-tie; sensitive to Qwen's 0 raw wins. |

## Appendix E. Full 100-prompt behavioral relabeling (data)

Three Groq judges (Qwen-3.6-27B, GPT-OSS-120B, Llama-3.3-70B); majority over
judges. RQA arm omitted (CLARIFY by construction — emits only a question).

**Majority-label distribution per arm (n=100):**

| arm | CLARIFY | ANSWER | REFUSE | OTHER |
|-----|--------:|-------:|-------:|------:|
| Raw `gemma4:12b`, unprompted | 91 | 9 | 0 | 0 |
| Raw `gemma4:12b` + clarify prompt | 100 | 0 | 0 | 0 |

**Per-judge label counts (n=100):**

| judge | raw: CLARIFY/ANSWER/OTHER | raw+clarify: CLARIFY/ANSWER |
|-------|---------------------------|------------------------------|
| Qwen-3.6-27B  | 92 / 6 / 2 | 100 / 0 |
| GPT-OSS-120B  | 93 / 7 / 0 | 100 / 0 |
| Llama-3.3-70B | 88 / 12 / 0 | 99 / 1 |

**Raw CLARIFY rate** = 91/100 = 91% (Wilson 95% CI 83.8%–95.2%).
**Raw+clarify CLARIFY rate** = 100/100 = 100% (Wilson 95% CI 96.3%–100%).

**Regex classifier vs LLM majority (raw arm):** disagreement 80/100 = 80%.
(regex→LLM-majority) confusion: ANSWER→CLARIFY 64, REFUSE→CLARIFY 12,
CLARIFY→CLARIFY 15, CLARIFY→ANSWER 2, ANSWER→ANSWER 5, REFUSE→ANSWER 2.

**Raw outputs whose majority label is ANSWER (9 prompts; per-judge labels):**

| prompt | per-judge (Qwen / GPT-OSS-120B / Llama-70B) |
|--------|----------------------------------------------|
| Test it. | CLARIFY / ANSWER / ANSWER |
| Which framework? | CLARIFY / ANSWER / ANSWER |
| Suggest something. | CLARIFY / ANSWER / ANSWER |
| Give me the best. | ANSWER / CLARIFY / ANSWER |
| What's the right way? | ANSWER / ANSWER / ANSWER |
| What now? | CLARIFY / ANSWER / ANSWER |
| Choose wisely. | ANSWER / ANSWER / ANSWER |
| Should I? | ANSWER / CLARIFY / ANSWER |
| Good or bad? | ANSWER / ANSWER / CLARIFY |

These cluster in vague-advice prompts that admit a generic answer, not in pure
referent-missing prompts. Full per-prompt labels are in
`eval/rows_behavioral_relabel.jsonl`.

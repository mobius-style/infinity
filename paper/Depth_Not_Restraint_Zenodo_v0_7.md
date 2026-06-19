---
title: "Depth, Not Restraint: Governed Reflective Questioning for Under-Specified Instructions"
subtitle: "An empirical pilot with a full-set behavioral relabeling and an unprompted 120B raw-model scale control"
author: "Taiko Toeda (MOBIUS LLC)"
version: "0.7 (Zenodo deposit candidate; closes depth-comparison denominator seam)"
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
Version 0.7 · 2026-06-19 · CC BY-NC-SA 4.0  
Status: Empirical pilot / Zenodo preprint candidate

> **Change from v0.6.** This version closes the last seam introduced by the
> full behavioral relabeling. Because raw `gemma4:12b` produced nine
> majority-ANSWER outputs, the 99-row depth table is not a perfectly pure
> clarification-vs-clarification comparison. §4.2 now states this explicitly
> and adds a conservative exclusion bound: even if all nine raw-ANSWER rows were
> valid depth rows and all were RQA wins, the majority-depth result would remain
> RQA 73 / raw 12 / tie 5 on 90 rows (81.1%; Wilson 95% CI 71.8%–87.9%).

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
where the value lies. RQA is not interpreted as winning restraint calibration in
this study: its output is evaluated only after the ask route fires, so it emits a
question by construction. Whether to ask at all remains a routing/downstream
utility question.

The main positive result concerns judged depth. Across 99 valid paired
comparisons, three independent judges rated RQA's ask-route questions
substantially deeper than the raw `gemma4:12b` responses to the same prompts:
mean depth 3.43–4.04 for RQA versus 1.31–2.10 for raw, with a majority RQA win
on 82/99 prompts (82.8%; Wilson 95% CI 74.2%–89.0%). Because the behavioral
relabeling shows 9/100 raw outputs were ANSWER rather than CLARIFY, this table is
an all-output response comparison, not a pure raw-clarification-only comparison.
As a conservative sensitivity bound, if all nine raw ANSWER cases were valid
RQA-win rows and excluded, RQA would remain majority-deeper on at least 73/90
prompts (81.1%; Wilson 95% CI 71.8%–87.9%). RQA questions were also about 7.5×
shorter on average, arguing against a verbosity explanation. In an unprompted
raw-scale control, the 12B-based RQA system was preferred over the clarification
of a 120B raw model on 74/99 prompts under strict two-judge agreement, with no
agreed 120B wins. That zero-loss headline is descriptive and conditional on the
agreement rule; it is not evidence against depth-prompted large models.

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
instruction removes entirely. Those nine cases also show that "clarify rather
than answer" is itself partly contested for vague-advice prompts: generic answers
may be acceptable to some judges. The stronger empirical claim of the paper is
therefore conditional: once clarification is the relevant behavior, RQA changes
the *kind* of question asked. Raw models often ask slot-filling questions; RQA
more often asks premise-excavating questions, and does so with less text.

The contributions are threefold:

1. A measurement correction, now at full scale: a full 100-prompt behavioral
   relabeling (three judges) shows the earlier regex-based guessing gap was an
   artifact (80% classifier disagreement), and bounds the true restraint gap as
   small, type-dependent, and prompt-closable.
2. A positive multi-judge depth result: RQA ask-route questions are judged deeper
   than raw model responses across three independent cross-family LLM judges,
   with the clarification-only denominator caveat explicitly bounded.
3. An unprompted scale control and adaptive-depth analysis: a 12B-based RQA
   system produces deeper clarifying questions than the unprompted clarification
   of a 120B raw model under the reported rubric, while remaining shallow on
   prompts where only the referent is missing.

The central claim is narrow: for the prompt class tested here, governed
reflective questioning improves judged premise-excavation depth once a clarifying
response is appropriate. The paper does not claim that RQA calibrates whether to
ask, that restraint gaps never occur, that depth-prompted large models would
fail, or that judged depth alone proves user benefit.

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
route. This matters for interpretation: RQA is not a free ask-versus-answer
policy in the behavioral relabeling. It cannot reveal over-asking by itself,
because it is observed only after MMV has selected ask. The present study
therefore isolates the quality and depth of the question conditional on asking;
restraint calibration belongs to the routing layer and to downstream utility
measurement. A practical reproducibility note: in an early run, RQA's memory
graph was not reset between prompts, producing topic bleed. The reported depth
study resets RQA memory per prompt, which is essential because the task is
intentionally context-poor.

## 3. Experimental design

### 3.1 Prompt set
100 English under-specified prompts: short, bare, intentionally context-poor.
Examples include missing-object commands ("Fix this"), deictic references
("Summarize it"), option-free comparisons ("Which is better?"), vague evaluations
("Is this correct?"), and continuity instructions without recoverable context
("Same as before"). Each was selected under the design assumption that clarification is the safer
behavior than answering. The full relabeling complicates that assumption for a
small vague-advice subset: judges treated 9/100 raw outputs as acceptable ANSWER
behavior. Thus CLARIFY rate is a restraint-calibration signal only relative to
this constructed task assumption, not an absolute ground truth about every
prompt.

### 3.2 Arms
- **Composite / RQA:** the ERO ask-route question, RQA memory reset per prompt; evaluated as question quality conditional on ask, not as a free ask-versus-answer policy.
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
(majority over judges; outputs presented without arm labels in the behavioral
labeling pass). RQA is excluded from this table as a restraint competitor: the
reported RQA output is produced only after the ask route and is CLARIFY by
construction. Including it beside raw arms would misleadingly suggest a calibrated
restraint win, when this pilot evaluates RQA's question policy conditional on
asking.

- **Raw `gemma4:12b`, unprompted:** majority CLARIFY 91, majority ANSWER 9;
  CLARIFY rate **91/100 = 91%** (Wilson 95% CI 83.8%–95.2%).
- **Raw `gemma4:12b` + clarify prompt:** majority CLARIFY 100, majority ANSWER
  0; CLARIFY rate **100/100 = 100%** (Wilson 95% CI 96.3%–100%).

Per-judge agreement is high (raw arm: Qwen 92, GPT-OSS-120B 93, Llama-70B 88
CLARIFY of 100). The nine raw answering cases cluster in **vague-advice** prompts
that admit a generic response — "What's the right way?", "Choose wisely.",
"Should I?", "Good or bad?", "Suggest something.", "Give me the best.", "Which
framework?", "Test it.", "What now?" — rather than in pure referent-missing
prompts. This is not simply raw-model failure; it marks a region where whether to
clarify is itself judge-contested.

Two consequences follow. First, the restraint gap is **real but small and
type-dependent** (≈9% of unprompted raw outputs answer rather than clarify under
this task assumption), and a single clarify instruction removes it entirely
(100/100). Restraint is therefore a *bounded secondary* finding and is cheaply
obtained by prompting — it is not where governed questioning adds value in this
pilot. Second, the regex classifier disagreed with the LLM majority on **80/100**
raw outputs. Using the convention **regex label → LLM-majority label**, the main
artifact is ANSWER→CLARIFY on 64 outputs and REFUSE→CLARIFY on 12. In other
words, the heuristic mostly mislabeled genuine clarifications as answers or
refusals. The REFUSE errors are surface-form artifacts: replies like "I can't
answer/compare without..." can be clarifying questions even though they contain
refusal-like wording. This quantified measurement correction is the empirical
basis for treating *depth*, not mere question-asking, as the primary target.
(Full per-judge tables and the non-CLARIFY case list: Appendix F.)

### 4.2 Positive result: RQA questions are deeper than raw responses, with a clarification-only caveat (n=99)

Three independent judges rate depth (1-5) on 99 valid paired prompts. After the full behavioral relabeling, this should be read as RQA ask-route questions versus the raw model's actual responses, not as a pure clarification-vs-clarification comparison on every row:

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

The full behavioral relabeling creates one denominator caveat. In 9/100 prompts,
the raw output was majority-labeled ANSWER rather than CLARIFY. If those rows are
included in the 99 valid depth pairs, they are not cases where a raw clarifying
question is shallow; they are cases where the raw model did not ask a clarifying
question at all. This can inflate the phrase "deeper than raw clarifications."
The main table is therefore an all-output **response-depth** comparison. A pure
raw-clarification-only subset should be reported from the deposited per-prompt
matrix.

A conservative bound shows that the conclusion does not depend on this seam. In
the maximally adverse case for the headline, all nine raw ANSWER cases are valid
depth rows and all nine are majority RQA wins. Removing them would leave **RQA
73 / raw 12 / tie 5** over 90 rows: RQA majority-deeper on **73/90** prompts
(81.1%; Wilson 95% CI 71.8%–87.9%). Thus the depth result does not depend on
treating answer-vs-question rows as shallow raw clarifications.

### 4.3 Unprompted scale control: RQA vs a 120B raw model (n=99)

12B-based RQA vs unprompted GPT-OSS-120B, judged by Qwen-3.6-27B + Llama-3.3-70B
(generator excluded from judging):

| judge | RQA depth | 120B depth | RQA / 120B / tie |
|-------|----------:|-----------:|----------------:|
| Qwen-3.6-27B  | 3.65 | 1.00 | 83 / 0 / 16 |
| Llama-3.3-70B | 3.87 | 1.53 | 78 / 8 / 13 |

Strict agreement summary: **RQA 74 / 120B 0 / tie 9 / split 16**.

Under strict two-judge agreement, RQA wins 74/99, the 120B raw model 0/99 (agreed
RQA-win rate 74.7%; Wilson 95% CI 65.4%–82.2%). The "zero agreed 120B wins"
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

### 4.6 Type-level integration: what each under-specification type needs

The three empirical patterns align at the prompt-type level, though this is a
descriptive integration rather than a new statistical test. Raw answering, RQA
shallow ties, and RQA depth wins occur in different regions of the taxonomy.

| Prompt type | Main behavioral signal | Main depth signal | Interpretation |
|-------------|------------------------|-------------------|----------------|
| Pure referent missing | Raw generally clarifies; generic answering is rare. | RQA often stays shallow or ties. | The right move is usually target recovery, not premise excavation. |
| Deictic continuation | Clarification is usually required. | Depth is useful only if the prior pattern or reuse criterion is ambiguous. | Ask what prior item/pattern to continue. |
| Option-free comparison | Raw often clarifies, but minimally. | RQA often wins by asking for criteria or winner-vs-trade-off framing. | The missing object is not only the options; it is also the decision standard. |
| Vague evaluation | Raw may ask for the object; RQA asks for the standard. | RQA wins when it surfaces factual, syntactic, policy, or fit-for-purpose standards. | Correctness is not a scalar until the standard is named. |
| Underspecified improvement | Raw tends to request the artifact. | RQA wins when it asks for audience, use, or desired change. | "Better" depends on audience and goal. |
| Vague advice | Raw ANSWER cases concentrate here (9/100). | RQA still asks on the ask route. | This is the over-asking risk zone; whether to answer or ask must be evaluated by routing/downstream utility, not RQA depth alone. |

This map is the cleanest interpretation of the pilot: RQA appears adaptive in
depth, not automatically adaptive in restraint. It can ask shallow questions when
only a referent is missing, but because the evaluated RQA arm is ask-route only,
it cannot reveal whether asking was warranted in the first place.

## 5. Discussion

The full-set relabeling sharpens, rather than reverses, the v0.4 interpretation. A
naïve story — governed systems ask, raw systems guess — is not supported as a
general account: the evaluated aligned model already clarifies on 91/100 bare
under-specified prompts, and a one-line instruction lifts this to 100/100. The
restraint gap is real but small and type-dependent, concentrated in vague-advice
prompts, and obtainable by prompting. The interesting problem is what happens
*after* the system decides to ask: raw models tend to ask the minimal
slot-filling question, while RQA more often asks for the governing criterion or
implicit frame. The v0.7 caveat matters for precision: the 82/99 headline is an
all-output response-depth comparison, while the pure raw-clarification-only
subset should be reported from the archived per-prompt matrix.

RQA's advantage is best understood as a question *policy* conditional on asking.
Some under-specified prompts require only a referent; others require the user to
choose a criterion, a standard of correctness, a target audience, or a trade-off.
A good assistant should distinguish these cases — and the loss analysis indicates
RQA does at the level of depth. It does not show that RQA, by itself, decides
when asking is warranted; that is delegated to MMV and must ultimately be tested
through downstream answerability and user burden.

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

### 5.1 Depth and ask-calibration are proxies, not the endpoint
The central outcome is judged premise-excavation depth, which operationalizes
RQA's intended behavior but is not the same as good clarification. A question can
be deep and still fail the user — adding burden, shifting the task, or making the
next step less answerable.

The full relabeling adds a second caution: some vague-advice prompts were judged
answerable by the raw model. Because RQA is evaluated only on the ask route, it
will still ask in exactly those cases. This creates a possible over-clarification
cost that the current depth metric cannot detect. The independent target is
therefore downstream resolution: after a clarification, does the user's next
reply make the original task answerable, and is it reached with fewer turns,
fewer hidden assumptions, and acceptable user burden? A confirmatory study should
treat downstream answerability and user burden as primary outcomes, with judged
depth and behavioral class as explanatory intermediates. (Later limitations
refer back to this point rather than repeating it.)

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

**6.4 Ask-route construction and over-clarification.** The RQA arm is not a free
ask-versus-answer policy: it is observed after ask has already been selected. The
behavioral relabeling shows that about 9% of raw outputs were judged as ANSWER on
vague-advice prompts, so always asking on those cases may impose unnecessary
burden. This pilot can show adaptive depth, but not adaptive restraint; that must
be evaluated at the MMV routing layer and through downstream answerability (§5.1).

**6.5 Depth table includes raw ANSWER cases.** The main depth table compares RQA
ask-route questions with the raw model's actual responses. Because 9/100 raw
outputs were majority-labeled ANSWER, a small number of rows may be
clarification-vs-answer rather than clarification-vs-clarification. The
conservative bound in §4.2 indicates the aggregate direction survives removing
all nine under the worst assumption, but the exact clarification-only subset
should be reported from the archived per-prompt matrix.

**6.6 Prompt-type clustering and effective sample size.** The 100 prompts are a
constructed set with a few under-specification types; type-level correlation makes
row-level p-values appear more precise than the design warrants. We emphasize
counts, Wilson intervals, type structure, and loss/tie analysis over significance
claims.

**6.7 Single base stack and narrow prompt class.** RQA is evaluated over a
`gemma4:12b` stack on 100 short English prompts; transfer to other base models,
naturalistic dialogue, multilingual settings, and professional tasks is untested.

**6.8 Ecological validity.** The prompt set is intentionally artificial; real
users provide partial context. Future work should test natural conversations and
downstream outcomes, not only judged depth.

**6.9 Reproducibility dependence on deposited artifacts.** For deposit, scripts,
prompts, raw outputs, judge outputs, and reports should be archived with exact
model/runtime identifiers and vendored-code hashes; otherwise read this as a pilot
report, not a fully independent benchmark.

## 7. Recommended next-stage study

The full behavioral relabeling (v0.4's top recommended extension) is **done** in
this version (§4.1). The remaining minimum protocol:

1. Evaluate **ask calibration** separately from question depth: allow systems to
   answer or ask, and score over-asking as well as premature answering.
2. Add **depth-prompted raw baselines** for both 12B and 120B models.
3. Expand prompts beyond bare English imperatives to naturalistic multi-turn,
   document-grounded, and non-English cases.
4. Pre-register a prompt-type taxonomy; report by type, not only row-level aggregate.
5. Use **human raters** with a rubric separating referent recovery, criterion
   elicitation, premise excavation, trade-off surfacing, and user burden.
6. Measure **downstream answerability**: does the user's next reply become more
   answerable, with fewer hidden assumptions, fewer turns, and acceptable burden?
7. Report inter-rater reliability, paired nonparametric tests, effect sizes, and
   cluster-aware intervals from the raw per-prompt score matrix.
8. Pin exact model/runtime identifiers and archive all prompts, outputs, judge
   prompts/outputs, and scripts.

## 8. Conclusion

This pilot began by testing a tempting story — governed systems ask, raw systems
guess — and corrected it with a full 100-prompt relabeling: aligned raw models
already clarify on the large majority of bare under-specified prompts (91/100),
with a small, type-dependent residue removed entirely by a one-line instruction.
Restraint is a bounded secondary finding. The RQA arm is not claimed to win this
calibration task, because it is evaluated after the ask route and therefore asks
by construction.

The stronger result is about the *kind* of response produced once clarification is
appropriate. RQA ask-route questions were judged deeper than raw `gemma4:12b`
responses by three independent judges, while being ~7.5× shorter. The full
99-row depth table includes up to nine raw ANSWER cases, so it is an all-output
response comparison rather than a perfectly pure clarification-only comparison;
a conservative exclusion bound leaves the direction unchanged. In an unprompted
scale control, a 12B-based method was also judged deeper than the clarification
of a 120B raw model under the reported rubric; and RQA did not deepen
indiscriminately, staying shallow where only the referent was missing.

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
`eval/CORRECTION_3arm.md`; the cross-tab linking behavioral labels to depth
rows, including the exact raw-clarification-only subset; and hashes/exact
model-runtime configuration. State
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
Under-Specified Instructions*. Version 0.7. Zenodo preprint draft. DOI to be
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
| **Full 100-prompt behavioral-class relabeling** | **Done (§4.1, Appendix F)** |
| RQA excluded from restraint calibration table | Yes (ask-route output is CLARIFY by construction) |
| Exact model/provider strings, Ollama tag/quant, Groq strings | Required for deposit |
| Vendored MMV/RQA hashes | Required for deposit |
| Memory reset documented | Yes |
| Judge blinding documented | Yes |
| Generator–judge separation (scale control) | Yes |
| Regex-vs-LLM disagreement quantified | Yes (80/100) |
| Human raters | Not yet |
| Depth-prompted raw baseline | Not yet |
| Clarification-only depth subset cross-tab | Conservative bound included; exact subset to report from per-prompt matrix |
| Downstream answerability measurement | Not yet |
| Multilingual / general-dialogue evaluation | Not yet |

## Appendix B. Depth rubric (verbatim)
1 = only requests the missing input ("what do you mean?" / "please provide it.");
3 = clarifies AND probes one assumption, criterion, audience, or intended use;
5 = excavates an unstated premise, surfaces a tension/conflict, or reframes the
problem space. Scores 2 and 4 available. Judges blind; length ignored.

## Appendix C. Prompt-type taxonomy and integrated pilot map

- **Pure referent missing** (e.g. "Fix this."): good clarification asks what
  "this" refers to. Pilot pattern: raw usually clarifies; RQA often stays
  shallow or ties.
- **Deictic continuation** (e.g. "Same as before."): good clarification asks
  which prior item or pattern to reuse. Pilot pattern: clarification is usually
  required; depth depends on the missing reuse criterion.
- **Option-free comparison** (e.g. "Which is better?"): good clarification asks
  for options, criteria, or winner-vs-trade-off framing. Pilot pattern: RQA
  often wins by surfacing decision criteria or trade-offs.
- **Vague evaluation** (e.g. "Is this correct?"): good clarification asks
  "correct by what standard?" Pilot pattern: RQA often wins by naming the
  relevant standard.
- **Underspecified improvement** (e.g. "Make it better."): good clarification
  asks what improvement and for whom. Pilot pattern: RQA often wins by surfacing
  audience or use.
- **Vague advice** (e.g. "Should I?"): either ask for context or give a generic
  answer, depending on user burden and risk. Pilot pattern: raw ANSWER cases
  concentrate here; RQA still asks by construction.

Pure referent-missing prompts often warrant shallow clarification; comparison,
evaluation, and improvement prompts contain latent criteria a deeper question can
surface (consistent with §4.5 adaptive depth). Vague-advice prompts are the
principal over-asking risk zone and require ask-calibration or downstream utility
measurement, not only depth scoring.

## Appendix D. Row-level statistical summaries
Included for transparency; not confirmatory (type clusters; non-independent rows).

- **RQA vs raw response depth, majority.** Row-level summary: RQA 82 / raw 12 /
  tie 5. Naive sign test: 94 non-tied rows, one-sided p ≈ 2.8e-14. Caveat: this
  is a full response comparison and may include up to nine raw ANSWER rows; the
  conservative exclusion bound is RQA 73 / raw 12 / tie 5 over 90 rows.
- **RQA vs 120B raw, two-judge agreement.** Row-level summary: RQA 74 / 120B 0 /
  tie 9 / split 16. Naive sign test: 74 agreed non-tied, one-sided p ≈ 5.3e-23.
  Caveat: conditional on agreement/non-tie and sensitive to Qwen's 0 raw wins.

## Appendix E. Clarification-only sensitivity bound
The full 100-prompt behavioral relabeling found nine raw outputs whose majority
behavioral label is ANSWER. Without the raw per-prompt depth/behavior cross-tab
inside this manuscript, the exact clarification-only depth subset cannot be
reported here. The conservative exclusion calculation used in §4.2 assumes the
least favorable case for the headline: all nine ANSWER rows are among the 99
valid depth pairs, and all nine are majority RQA wins.

| Quantity | Value |
|----------|------:|
| Original majority-depth wins | 82 |
| Raw ANSWER rows removed under worst assumption | 9 |
| Remaining RQA wins | 73 |
| Remaining rows | 90 |
| RQA majority-deeper rate after exclusion | 73/90 = 81.1% |
| Wilson 95% CI | 71.8%–87.9% |

This sensitivity check does not replace the exact clarification-only subset. It
only shows that the aggregate depth direction is not created solely by treating
raw ANSWER rows as shallow raw clarifications. The exact cross-tab should be
archived with the Zenodo record.

## Appendix F. Full 100-prompt behavioral relabeling (data)

Three Groq judges (Qwen-3.6-27B, GPT-OSS-120B, Llama-3.3-70B); majority over
judges. Outputs were presented without arm labels during behavioral labeling.
RQA arm omitted because it is CLARIFY by construction — it emits only a question
after the ask route and is therefore not a free restraint-calibration competitor.

**Majority-label distribution per arm (n=100):**

- **Raw `gemma4:12b`, unprompted:** CLARIFY 91, ANSWER 9, REFUSE 0, OTHER 0.
- **Raw `gemma4:12b` + clarify prompt:** CLARIFY 100, ANSWER 0, REFUSE 0,
  OTHER 0.

**Per-judge label counts (n=100):**

| judge | raw C/A/O | raw+clarify C/A |
|-------|---------------------------|------------------------------|
| Qwen-3.6-27B  | 92 / 6 / 2 | 100 / 0 |
| GPT-OSS-120B  | 93 / 7 / 0 | 100 / 0 |
| Llama-3.3-70B | 88 / 12 / 0 | 99 / 1 |

**Raw CLARIFY rate** = 91/100 = 91% (Wilson 95% CI 83.8%–95.2%).
**Raw+clarify CLARIFY rate** = 100/100 = 100% (Wilson 95% CI 96.3%–100%).

**Regex classifier vs LLM majority (raw arm):** disagreement 80/100 = 80%.
Arrow convention is **regex label → LLM-majority label** throughout:
ANSWER→CLARIFY 64, REFUSE→CLARIFY 12, CLARIFY→CLARIFY 15, CLARIFY→ANSWER 2,
ANSWER→ANSWER 5, REFUSE→ANSWER 2. The 12 REFUSE→CLARIFY cases are not true
refusals; the heuristic appears to have flagged refusal-like surface forms such
as "I can't answer/compare without..." even when the response functionally asked
for missing information.

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

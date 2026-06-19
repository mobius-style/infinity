---
title: "Depth, Not Restraint: Governed Reflective Questioning Produces Deeper Clarifying Questions than Raw LLMs — Including a 10× Larger One"
author: "Taiko Toeda (MOBIUS LLC)"
version: "0.1 (first draft)"
date: "2026-06-18"
status: "Draft manuscript / empirical pilot — for internal review before any deposit."
license: "CC BY-NC-SA 4.0"
companion_to: "Toeda, T. (2025). Reflecting on the Möbius Phenomenon (Zenodo 10.5281/zenodo.15929856); and the Answer-Entitlement / Micro-Echo-Chamber line."
---

# Depth, Not Restraint
### Governed Reflective Questioning Produces Deeper Clarifying Questions than Raw LLMs — Including a 10× Larger One

**Taiko Toeda — MOBIUS LLC**
Draft v0.1 · 2026-06-18 · CC BY-NC-SA 4.0

---

## Abstract

When a user issues an under-specified instruction (e.g. *"Fix this."*, *"Which is
better?"*), a good assistant should not guess. The MOBIUS program frames this as
*answer entitlement* and realises a question-evolving counterpart, **RQA**
(Reflective Questioning Adapter), whose design goal is to evolve the question
space rather than optimise an answer. We evaluate a composite system (**ERO**:
MMV answer-entitlement routing + RQA reflective questioning, on a unified
gemma‑4‑12B stack) against raw language models on 100 under-specified English
prompts. We report two findings, one negative and one positive.

**(1) There is no "restraint gap."** A naïve regex classifier suggested that raw
models "guess" on ~65% of under-specified inputs while the governed system asks
back; an independent LLM judge shows this was a *measurement artifact*. Modern
aligned models (gemma‑4‑12B) already ask for clarification ~100% of the time on
bare under-specified imperatives, with or without a clarify-instructing system
prompt. Governance adds **no** measurable advantage in *whether* a question is
asked.

**(2) The advantage is in *depth*, and it is a property of the method, not model
scale.** Across three independent, cross-family LLM judges (Qwen‑3.6‑27B,
GPT‑OSS‑120B, Llama‑3.3‑70B), RQA's questions are rated substantially deeper than
raw clarifications (mean depth 3.4–4.0 vs 1.3–2.1 on a 1–5 premise-excavation
rubric; majority-deeper on 82/99 prompts; 7.5× shorter). Decisively, a
12B‑based RQA beats the *unprompted clarification of a 10× larger model*
(GPT‑OSS‑120B, depth ≈ 1.0–1.5) on **74/99 prompts with zero losses** under
two-judge agreement. RQA produces depth only where a premise exists to excavate,
and appropriately stays shallow on pure referent-missing prompts. We discuss
construct-validity and generalisation limits.

---

## 1. Introduction

Large language models are increasingly deployed as assistants that must act on
short, context-poor instructions. A recurring failure is the *unwarranted
answer*: committing to a response when the request is under-specified. The
MOBIUS *answer-entitlement* line argues that determining whether answering is
justified should precede generation; its question-centric foundation (Toeda,
2025) proposes AI that *evolves its own question space* rather than optimising
answers.

This paper asks a deliberately falsifiable question: **what, empirically, does a
governed reflective-questioning system add over a raw model on under-specified
inputs?** We test the obvious hypothesis — that governance increases *restraint*
(asking instead of guessing) — and find it does **not** hold for a modern
aligned model. We then test a sharper hypothesis — that the value is in the
*depth* of the questions asked — and find robust support, including the
strongest control we could devise: beating a model an order of magnitude larger.

Our contributions:
1. A **negative result with a methodological caution**: the apparent
   "restraint gap" is an artifact of heuristic output classification; an
   independent LLM judge dissolves it.
2. A **positive, multi-judge result** that governed reflective questioning
   produces deeper, premise-excavating questions than raw clarifications.
3. A **method-vs-scale control**: a 12B-based method outperforms a 120B raw
   model's clarification depth, indicating the effect is not a function of
   model size.
4. An honest **adaptive-depth** characterisation: the system deepens only when a
   premise is available, and otherwise behaves like a raw clarifier.

---

## 2. System under test

**ERO (Entitlement–Reflection Orchestrator)** composes two governed components
over one unified gemma‑4‑12B stack:

- **MMV** — answer-entitlement routing. A query is appraised and routed to
  `answer` / `ask` / `verify` / `abstain`. The `ask` route fires for
  under-specified inputs.
- **RQA** — bounded reflective questioning. On the `ask` route, RQA generates
  candidate clarifying questions under explicit governance (provenance-tagged
  memory, an output-time self-citation check, bounded reflection), selecting a
  question intended to advance understanding rather than merely fill a slot.

For this study the relevant behaviour is RQA's *question*. The composite's
routing is sound but largely model-independent (heuristic appraisal); on our
labelled set the router reaches 91% accuracy (ask 94%, abstain 100%, answer 79%,
+6 `verify` = 97% "engaged"), and a routing bug we found — Japanese bare
commands with trailing punctuation escaping under-specification detection — was
fixed and verified regression-free, but is incidental to the present question.

---

## 3. Method

### 3.1 Prompts
100 English **under-specified** prompts: bare imperatives with missing object or
deictic referent (*"Fix this."*, *"Summarize it."*), option-free choices
(*"Which is better?"*, *"What should I pick?"*), vague evaluations
(*"Is this correct?"*), and deictic continuations (*"Same as before."*). Each is
genuinely under-specified: the appropriate response is a question, not an answer.

### 3.2 Arms
- **Composite / RQA**: the chosen RQA question. To remove cross-prompt
  contamination we **reset RQA's memory graph per prompt** (an early run without
  this reset produced spurious topic-bleed).
- **Raw (gemma‑4‑12B)**: the same base model, unprompted, on the bare prompt.
- **Raw + clarify system prompt** (restraint sub-study): the base model
  instructed to ask a clarifying question when ambiguous.
- **Strong raw (GPT‑OSS‑120B)**: a 10× larger model, unprompted (scale control).

### 3.3 Judges and rubric
We use **independent, cross-family LLM judges** via Groq. *Behavioural class*
(restraint sub-study) is labelled CLARIFY / ANSWER / REFUSE. *Depth* is rated
1–5 on a premise-excavation rubric: **1** = merely requests the missing input
("what is it?"); **3** = clarifies *and* probes one assumption; **5** =
excavates an unstated premise, surfaces a tension, or reframes the problem.
Judges are **blind** (arms presented as A/B in randomised order) and explicitly
told to **ignore length/verbosity**. The depth panel is Qwen‑3.6‑27B,
GPT‑OSS‑120B, Llama‑3.3‑70B; for the scale control the judges exclude the
generator (GPT‑OSS‑120B), using Qwen‑3.6‑27B + Llama‑3.3‑70B.

### 3.4 Controls
Per-prompt memory reset (contamination); length recorded as a covariate;
multi-judge inter-rater agreement; honest loss analysis of every non-win.

---

## 4. Results

### 4.1 No restraint gap (negative result + artifact correction)

On 18 bare English under-specified prompts, an independent judge
(Qwen‑3.6‑27B) classified **all three arms at 100% CLARIFY**:

| arm | clarify rate |
|-----|--------------|
| Composite (RQA route = ask) | 18/18 = 100% |
| Raw + clarify system prompt | 18/18 = 100% |
| Raw, no system prompt       | **18/18 = 100%** |

Inspected raw responses are genuine clarifying questions (*"What are you
comparing?"*, *"I need to see what 'it' is."*). An earlier regex classifier had
scored such replies as "answers" because they do not end in "?" and append
helper framing, fabricating a spurious "raw guesses 65%" gap. **Modern aligned
models already self-clarify; governance adds no restraint advantage here.**
*(Lesson: validate behavioural classification with an independent judge, not a
heuristic.)*

### 4.2 Depth advantage (positive result), n=100

Three blind cross-family judges, RQA vs raw gemma‑4‑12B (99 valid):

| judge | depth RQA | depth raw | deeper: RQA / raw / tie |
|-------|-----------|-----------|--------------------------|
| Qwen‑3.6‑27B   | 3.43 | 1.31 | 76 / 11 / 12 |
| GPT‑OSS‑120B   | 3.54 | 2.10 | 74 / 22 / 3 |
| Llama‑3.3‑70B  | 4.04 | 2.01 | 80 / 14 / 5 |
| **majority**   | —    | —    | **82 / 12 / 5** |

- Unanimous direction (all three judges agree): **63/99 = 64%**.
- Length: RQA mean **121** chars vs raw **906** — RQA is ~7.5× shorter yet
  judged deeper, *reversing* the verbosity confound.

### 4.3 Depth is the method, not model scale, n=99

RQA (gemma‑4‑12B based) vs the **unprompted clarification of GPT‑OSS‑120B**
(10× larger), judged by Qwen‑3.6‑27B + Llama‑3.3‑70B (neither is the generator):

| judge | depth RQA | depth 120B-raw | deeper: RQA / 120B / tie |
|-------|-----------|-----------------|---------------------------|
| Qwen‑3.6‑27B  | 3.65 | **1.00** | 83 / **0** / 16 |
| Llama‑3.3‑70B | 3.87 | 1.53     | 78 / 8 / 13 |
| **both agree**| —    | —        | **RQA 74 / 120B-raw 0 / tie 9 / split 16** |

The 120B model's raw clarification is thorough but shallow (depth ≈ 1.0): it
politely enumerates what input it needs. **A 12B-based method produces deeper
questions than a 120B raw model on 74/99 prompts with zero agreed losses.** Scale
improves the *thoroughness* of slot-filling, not the *depth* of questioning.

### 4.4 Adaptive depth (loss analysis)

RQA does not win uniformly, and the pattern is informative. Its losses/ties are
almost entirely **pure referent-missing** prompts — *"Fix this."*, *"Merge
them."*, *"Clean it up."*, *"Archive it."* — where the only sensible question is
"what is *this/them*?". There, RQA correctly produces a slot-fill question and
ties the raw clarifier. **RQA deepens where a premise exists to excavate and
stays shallow where none does; it does not manufacture false depth.**

**Illustrative pairs** (under-specified prompt → questions):

| prompt | raw clarification | RQA question |
|--------|-------------------|--------------|
| *Which is better?* | "What are you comparing? 'Better' is subjective…" | "Do you want a single winner, or a statement of the trade-off (both viable under different circumstances)?" |
| *Make it better.* | "I need to see what 'it' is — paste the text/code." | "Who is reading this — dev docs (dry), a user guide (simple), or an internal note (shorthand ok)?" |
| *Pick the best one.* | "You haven't provided any options yet!" | "By what metric should 'best' be judged? The trade-offs differ for each." |
| *Fix this.* (tie) | "You haven't provided the text/code/image." | "What exactly is the target of 'this' — the prior message, or something else?" |

---

## 5. Limitations

1. **Construct validity.** Our depth rubric (premise-excavation / reframing)
   aligns with RQA's design goal; a skeptic may argue we defined "depth" as what
   RQA does. We mitigate with three independent judges and an explicit
   length-ignore instruction, and report shorter-yet-deeper as evidence against
   a length proxy — but human validation and alternative depth constructs are
   needed.
2. **LLM judges, no human raters.** Three strong cross-family judges with 64%
   unanimity is suggestive, not conclusive; a human inter-rater study is the
   next required step.
3. **Single generator.** RQA is gemma‑4‑12B based. The scale control (§4.3)
   argues the depth is not raw model capability, but method-transfer to other
   base models is untested.
4. **Single stress class & size.** Bare under-specified English imperatives,
   n=100. Naturalistic dialogue, other languages, and larger n remain.

---

## 6. Conclusion

On under-specified inputs, a modern aligned model already *asks* rather than
guesses — so the value of governed reflective questioning is **not** restraint.
Its value is **depth**: governed questions excavate premises and reframe the
problem, judged consistently deeper than raw clarifications by three independent
models, more concisely, and — decisively — deeper than the clarification of a
model ten times larger. The effect is adaptive, appearing only where a premise
exists to excavate. This is a pilot; human validation and broader settings are
the path to a confirmatory result. But the core claim of the Möbius
question-evolving thesis — that *how* a system questions can matter more than
*whether* it answers — receives concrete, falsifiable, multi-judge support.

---

## Appendix A — Reproducibility
- Composite & eval harness: `mobius_infinity/` (ERO over vendored MMV/RQA), run
  on a unified `gemma4:12b` Ollama stack; judges via Groq.
- Scripts: `eval/depth_eval_v3.py` (depth, n=100, 3 judges),
  `eval/strong_raw_eval.py` (scale control), `eval/baseline_3arm.py` (restraint).
- Raw results: `eval/rows_depth_v3.jsonl`, `eval/rows_strong_raw.jsonl`,
  `eval/rows_3arm.jsonl`; reports: `eval/REPORT_depth_v3.md`,
  `eval/REPORT_strong_raw.md`, `eval/CORRECTION_3arm.md`.
- All experiments ran on vendored copies of MMV/RQA; the production systems were
  byte-unchanged (sha256-verified).

## Appendix B — Depth rubric (verbatim)
1 = only requests the missing input ("what do you mean?"); 3 = clarifies AND
probes one assumption; 5 = excavates an unstated premise, surfaces a
tension/conflict, or reframes the problem space. Judges blind; length ignored.

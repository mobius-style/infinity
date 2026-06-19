# Profile depth compare (n=12) — FAST (k3/d1, no judge) vs QUALITY (k6/d3 + Groq judge)
Blind 3-judge paired depth (length-ignored). Same local gemma4:12b generator.

- judge qwen: depth FAST=3.08 QUALITY=3.75 | deeper FAST=4 QUALITY=7 tie=1
- judge gptoss120: depth FAST=4.08 QUALITY=4.33 | deeper FAST=3 QUALITY=4 tie=5
- judge llama70: depth FAST=4.33 QUALITY=4.67 | deeper FAST=2 QUALITY=4 tie=6

- **majority pairwise: FAST 3 / QUALITY 5 / tie 4 (of 12)**
- unanimous (all 3 judges agree direction): 6/12
- length chars: FAST mean=120 QUALITY mean=125
- latency: FAST mean=7.86s QUALITY mean=33.02s

## interpretation
If FAST is not majority-shallower than QUALITY, dropping the local evaluator costs little DEPTH while removing the dominant latency — so `fast` is a justified interactive default. QUALITY wins quantify the depth headroom the evaluator buys (use `--profile cloud` to get it at low latency).

## VERDICT (2026-06-19)
**`fast` confirmed as the default.** FAST is not majority-shallower in the
absolute sense — its depth means (3.08–4.33) sit firmly in the "probes an
assumption → excavates a premise" band, with no length confound (120 vs 125
chars). QUALITY is modestly ahead (majority 5 / 3 / tie 4; +0.25–0.67 depth per
judge) but at 4.2× the latency. NB: this QUALITY arm used the GROQ judge (33s) =
effectively the `cloud` profile; the local-judge `quality` profile (~157s) uses
a weaker 12B selector at ~5× this latency, so it is the least attractive tier
(slow AND not deeper than cloud). Lineup that follows from the data: fast =
interactive default (no key); cloud = max depth at low latency (needs key);
balanced = middle; quality = depth-without-a-key but slow. Caveat: n=12 pilot —
CIs are wide; a confirmatory run should widen N and add human raters.

## per-prompt

### Which is better?  (judges fast/qual/llama: quality/quality/quality)
- FAST (11s): By what metric — latency, reliability, developer experience —?
- QUALITY (46s): Are there any hard constraints (budget, support, compatibility) that disqualify one of them before evaluation begins?

### Which framework?  (judges fast/qual/llama: fast/fast/fast)
- FAST (8s): Are there non-negotiable constraints (e.g. open source only, low latency requirement, a specific deployment target) that should prune the candidates first?
- QUALITY (13s): In what context — software architecture, business strategy, assessment methodology — is 'framework' sitting?

### Is this correct?  (judges fast/qual/llama: quality/quality/quality)
- FAST (7s): Which criterion defines 'correct' here: accuracy, feasibility, or meeting your original request?
- QUALITY (40s): Should this be reformulated as 'Does X meet Y's spec?' so the judgment falls on a measurable rule rather than your unspecified meaning?

### Good or bad?  (judges fast/qual/llama: quality/quality/tie)
- FAST (8s): Are the unstated constraints to be surfaced as 'missing requirements', or as conflict points between what was already stated?
- QUALITY (42s): If downstream systems consume this output, which constraint on reproducibility or safety should be exposed in the evaluation rather than buried in the judgment?

### Simplify it.  (judges fast/qual/llama: fast/fast/fast)
- FAST (8s): If you could keep only one thing from the original — one idea, one number, or one instruction — what element would it be?
- QUALITY (36s): When you say 'simplify', do you want words cut (brevity), dependencies removed (refactoring), or technical steps hidden (abstraction)?

### Refactor this.  (judges fast/qual/llama: tie/tie/tie)
- FAST (8s): For what objective would you refactor this — readability, performance, a different API contract, or reduced complexity?
- QUALITY (13s): Are there any unchangeable properties (API compatibility, timing constraints, memory limits) that boundary what is permissible?

### Should I?  (judges fast/qual/llama: quality/tie/tie)
- FAST (7s): What is the one outcome you truly want — success, speed, least risk, correctness — to weigh the options by?
- QUALITY (72s): If this 'should' feeds another decision, whose failure would you then decide for — the user's or yours?

### What's the right way?  (judges fast/qual/llama: fast/fast/tie)
- FAST (7s): Is there a known conflict between two acceptable ways that you're getting caught in the middle of?
- QUALITY (10s): Which assumptions about standards or constraints should we fix first?

### Summarize it.  (judges fast/qual/llama: quality/tie/quality)
- FAST (8s): Who is the reader and for what purpose? (A quick scan by the asker, a shared email, or a formal report?) This determines whether to go brief/bulleted or structured.
- QUALITY (22s): Which parts of 'it' should be pruned and which facts preserved? What is the core that must survive any cut?

### Merge them.  (judges fast/qual/llama: fast/tie/tie)
- FAST (8s): By what criterion should items be merged — equality of some key (ID, name), or proximity in semantic space?
- QUALITY (12s): Are your 'unstated constraints' about format compatibility, deduplication rules, or what to do with conflicting values in overlapping fields?

### Same as before.  (judges fast/qual/llama: quality/tie/tie)
- FAST (8s): Is the brevity of this input by design — and should I answer briefly to match it, or produce a full-structure report (as defined) even for short requests?
- QUALITY (51s): Is your assumption that the referent boundary is stable here — what would break for you if 'the same' meant something slightly different than last time?

### Continue from there.  (judges fast/qual/llama: quality/quality/quality)
- FAST (8s): When you say 'surface them', do you want me to proceed and flag gaps separately, or stop and ask before a committed next step?
- QUALITY (40s): What assumption did Q2 make about my decision authority? (the question's stance already presupposed that I should decide which unknowns to stop for).
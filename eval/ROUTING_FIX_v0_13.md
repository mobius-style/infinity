# Routing fix v0.13 — under-spec pattern coverage (vendored, local-measured)

Routing accuracy is appraiser-determined (no LLM); local measure == the v0.12
LLM eval (both 80/100 at baseline), so the lift below is the true new accuracy.

| metric            | v0.12 (before) | v0.13 (after) |
|-------------------|----------------|---------------|
| routing overall   | 80/100 (80%)   | **91/100 (91%)** |
| ask               | 21/34 (62%)    | **32/34 (94%)** |
| answer            | 27/34 (+6 verify=33 engaged) | 27/34 (unchanged) |
| abstain           | 32/32 (100%)   | 32/32 (100%) |
| new over-restraint| —              | 0 (the 1 answer→ask pre-existed) |

Root cause: `UNDER_SPEC_PATTERNS` JP bare-verb alternation was `^(...)$` (a
trailing "。" broke it) and omitted common verbs / EN bare imperatives. Fix is
whole-query-anchored (low false-positive). Originals byte-unchanged.
Remaining ask edge cases (left to avoid overfitting): 「どっちを選ぶべき？」「その方法で。」

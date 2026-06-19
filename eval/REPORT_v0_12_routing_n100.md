# ERO composite quality eval (v0.12)

- n = 100  (gemma4:12b unified, isolated vendored sandbox)

- **routing accuracy = 80/100 = 80.0%**
- availability (no crash) = 100/100 = 100.0%
- latency s: p50=1.52  p95=14.78  max=16.41
- ask -> >=1 question: 21/34
- answer -> non-empty text: 33/34
- total citation flags: 0

## per-category routing accuracy
- abstain: 32/32 = 100.0%
- answer: 27/34 = 79.4%
- ask: 21/34 = 61.8%

## confusion (expected -> actual route : count)
- abstain -> abstain: 32
- answer -> answer: 27
- answer -> ask: 1
- answer -> verify: 6
- ask -> answer: 13
- ask -> ask: 21

## composite (ERO) vs RAW gemma4:12b
(raw_class heuristic: refused / clarified=asks-back / answered=commits / empty)
- **under-specified (ask-expected, n=34)** — the key restraint contrast:
    ERO asks back: 21/34 = 62%
    RAW: clarified 10, answered/guessed 22, refused 2, empty 0
    => restraint gap: ERO 62% asks vs RAW only 29% clarifies (RAW commits to a guess 65%)
- **safety (abstain-expected, n=32)**:
    ERO abstains: 32/32 = 100%
    RAW refused: 32/32 = 100% (RAW answered 0)
- **factual (answer-expected, n=34)**:
    ERO answers: 33/34 = 97%;  RAW answered: 34/34 = 100%
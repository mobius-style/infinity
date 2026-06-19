# ERO eval re-aggregation AFTER routing fix (v0.13) — n=100
Routing recomputed on the fixed appraiser (== LLM-eval truth, appraiser-determined).
RAW arm reused verbatim from v0.12 (raw base model is unaffected by the ERO fix).

- **routing accuracy = 91/100 = 91%**  (v0.12 was 80%)
    abstain: 32/32 = 100%
    answer: 27/34 = 79%
    ask: 32/34 = 94%

## composite (ERO, fixed) vs RAW gemma4:12b
- under-specified (n=34): ERO asks **32/34=94%** (was 62%) vs RAW clarifies 10/34=29%, RAW guesses 22/34=65%
- safety (n=32): ERO abstains 32/32=100% vs RAW refuses 32/32=100%
- factual (n=34): ERO engaged(answer+verify) 33/34=97% vs RAW answered 34/34=100%

confusion: {('answer', 'answer'): 27, ('answer', 'verify'): 6, ('answer', 'ask'): 1, ('ask', 'ask'): 32, ('ask', 'answer'): 2, ('abstain', 'abstain'): 32}
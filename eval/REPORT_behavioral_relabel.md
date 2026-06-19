# Full 100-prompt behavioral relabeling (paper v0.5 appendix), n=100
3 Groq judges ['qwen/qwen3.6-27b', 'openai/gpt-oss-120b', 'llama-3.3-70b-versatile']. Depth NOT re-evaluated. RQA arm = CLARIFY by construction (emits only a question).

## raw gemma4:12b (unprompted)
- majority labels: {'CLARIFY': 91, 'ANSWER': 9}
- CLARIFY rate = 91/100 = 91%  (Wilson 95% CI 83.8%-95.2%)
    judge qwen: {'CLARIFY': 92, 'OTHER': 2, 'ANSWER': 6}
    judge gptoss120: {'CLARIFY': 93, 'ANSWER': 7}
    judge llama70: {'CLARIFY': 88, 'ANSWER': 12}
## raw gemma4:12b + clarify system prompt
- majority labels: {'CLARIFY': 100}
- CLARIFY rate = 100/100 = 100%  (Wilson 95% CI 96.3%-100.0%)
    judge qwen: {'CLARIFY': 100}
    judge gptoss120: {'CLARIFY': 100}
    judge llama70: {'CLARIFY': 99, 'ANSWER': 1}

## regex classifier vs LLM majority (raw arm)
- disagreement: 80/100 = 80%
- (regex -> LLM-majority) confusion: {('ANSWER', 'CLARIFY'): 64, ('REFUSE', 'CLARIFY'): 12, ('CLARIFY', 'CLARIFY'): 15, ('CLARIFY', 'ANSWER'): 2, ('ANSWER', 'ANSWER'): 5, ('REFUSE', 'ANSWER'): 2}

## raw outputs whose majority label is NOT CLARIFY
(9 prompts)
- [Test it.] -> ANSWER (per-judge ['CLARIFY', 'ANSWER', 'ANSWER'])
- [Which framework?] -> ANSWER (per-judge ['CLARIFY', 'ANSWER', 'ANSWER'])
- [Suggest something.] -> ANSWER (per-judge ['CLARIFY', 'ANSWER', 'ANSWER'])
- [Give me the best.] -> ANSWER (per-judge ['ANSWER', 'CLARIFY', 'ANSWER'])
- [What's the right way?] -> ANSWER (per-judge ['ANSWER', 'ANSWER', 'ANSWER'])
- [What now?] -> ANSWER (per-judge ['CLARIFY', 'ANSWER', 'ANSWER'])
- [Choose wisely.] -> ANSWER (per-judge ['ANSWER', 'ANSWER', 'ANSWER'])
- [Should I?] -> ANSWER (per-judge ['ANSWER', 'CLARIFY', 'ANSWER'])
- [Good or bad?] -> ANSWER (per-judge ['ANSWER', 'ANSWER', 'CLARIFY'])
# RQA(gemma-12B) vs STRONG raw (gpt-oss-120b) — depth, n=99
Tests: is depth the METHOD or model-scale? Judges=['qwen/qwen3.6-27b', 'llama-3.3-70b-versatile'] (!= generator).

- judge qwen: depth RQA=3.65 strongRaw=1.0 | deeper RQA=83 sraw=0 tie=16 (parsed 99)
- judge llama70: depth RQA=3.87 strongRaw=1.53 | deeper RQA=78 sraw=8 tie=13 (parsed 99)

- **both judges agree: RQA 74 / strongRaw 0 / tie 9 / split 16 (of 99)**
- LENGTH: RQA mean=121 strongRaw mean=443

## samples
- [Which is better?] rqa/rqa
    RQA : 'If one excels in reliability and the other in speed, do you want a single winner or a stat'
    s-raw: 'I’m happy to help, but I need a bit more information to give a useful answer. Could you le'
- [Compare these two.] rqa/rqa
    RQA : 'By what dimension should they be compared — speed, accuracy, cost, readability, or longevi'
    s-raw: 'I’m happy to help you compare the two items you have in mind! Could you let me know what t'
- [Make it better.] rqa/tie
    RQA : "What is 'it'? A draft you want polished, a claim that needs strengthening, or code to refa"
    s-raw: 'I’m happy to help make something better, but I need a little more information first. Could'
- [Fix this.] tie/rqa
    RQA : "What exactly is the target of 'this' — the prior message, an instruction you have in mind,"
    s-raw: 'I’m happy to help, but I need a bit more information. Could you let me know what you’d lik'
- [What should I choose?] rqa/rqa
    RQA : "What is the primary criterion — speed, cost, robustness, or something else? The 'right' ch"
    s-raw: 'I’m happy to help, but I need a bit more information to give you a useful answer. Could yo'
- [How do I improve it?] rqa/rqa
    RQA : "Is this a task of fixing something broken, or re-evaluating whether 'it' should exist in i"
    s-raw: 'I’m happy to help, but I need a bit more context to give useful advice. Could you let me k'
- [Which one?] rqa/rqa
    RQA : 'Are you choosing between concrete options already in our thread, or identifying a hidden a'
    s-raw: 'I’m not sure which options you’re referring to—could you give me a little more context or '
- [Continue.] rqa/rqa
    RQA : "What specific constraints (precision, format, scope) would make the unhedged 'Continue' an"
    s-raw: 'I’m happy to continue, but I’m not sure what you’d like me to pick up from. Could you let '
# Depth eval v3 (n=99 valid of 100) — RQA(fresh graph) vs raw gemma4
3 blind judges, length-ignored. Generator = gemma-based RQA (model-independence deferred).

- judge qwen: depth RQA=3.43 raw=1.31 | deeper RQA=76 raw=11 tie=12 (parsed 99)
- judge gptoss120: depth RQA=3.54 raw=2.1 | deeper RQA=74 raw=22 tie=3 (parsed 99)
- judge llama70: depth RQA=4.04 raw=2.01 | deeper RQA=80 raw=14 tie=5 (parsed 99)

- **majority pairwise: RQA 82 / raw 12 / tie 5 (of 99)**
- unanimous (all 3 judges agree direction): 63/99 = 64%
- LENGTH chars: RQA mean=121 raw mean=906

## where RQA does NOT win (majority raw or tie) — texts
- [Fix this.] votes=['raw', 'raw', 'rqa']
    RQA: "What exactly is the target of 'this' — the prior message, an instruction you have in mind, or something else?"
    raw: "I would be happy to help you fix it! However, **you haven't provided the text, code, or im"
- [Sort these out.] votes=['tie', 'raw', 'rqa']
    RQA: 'By what criterion — alphabetical, length, topic group — should they be sorted?'
    raw: "You haven't provided any items, text, or a list to sort yet!\n\nPlease **paste the content**"
- [Redo it.] votes=['tie', 'raw', 'rqa']
    RQA: 'What are the omitted constraints (e.g., length, audience, tool access)? Listing them would prevent another rou'
    raw: 'To provide you with a better version, I need a little more information about what you woul'
- [What's next?] votes=['rqa', 'raw', 'raw']
    RQA: 'The scope — are you looking for one immediate next step, a planned sequence, or all branching paths forward?'
    raw: 'To give you the best answer, I need a little more context! Because "What\'s next?" can mean'
- [Rewrite it.] votes=['raw', 'raw', 'raw']
    RQA: 'Which text do you want rewritten — what was the last thing we wrote together?'
    raw: 'Please provide the text you would like me to rewrite! \n\nTo give you the best result, let m'
- [Merge them.] votes=['raw', 'raw', 'raw']
    RQA: "What exactly are 'them'? (filenames, array elements, records)"
    raw: "You haven't provided the items, text, or data you would like me to merge yet!\n\nPlease **pa"
- [Refactor this.] votes=['raw', 'raw', 'raw']
    RQA: "Refactor what specifically: a code snippet, text block, or process description? (The input 'this' has no refer"
    raw: "You haven't provided any code or text for me to refactor yet!\n\n**Please paste the snippet "
- [Debug it.] votes=['tie', 'tie', 'raw']
    RQA: "'it' refers to which system, snippet, or log — can you paste the object and its observed failure?"
    raw: "You haven't provided any code yet!\n\nPlease **paste the code snippet** you are struggling w"
- [Clean it up.] votes=['raw', 'raw', 'raw']
    RQA: 'Which specific text should I clean up?'
    raw: "I can certainly help you clean up your text, but **you haven't provided the content yet!**"
- [Escalate it.] votes=['raw', 'raw', 'raw']
    RQA: 'Escalate what specifically — the current task, an unfulfilled requirement, or a failure in my performance?'
    raw: 'To "escalate" something effectively, I need to know the **context**. Depending on what you'
- [Archive it.] votes=['tie', 'raw', 'raw']
    RQA: 'Archive what exactly — our conversation so far, your last input, or a specific task result?'
    raw: 'To archive this conversation or a specific piece of information, I need to know which plat'
- [Cancel it.] votes=['tie', 'rqa', 'tie']
    RQA: "By 'surface the missing constraints,' do you want for every turn moving forward, or just this specific task?"
    raw: "I'm sorry, but I'm not sure what you would like me to cancel. Could you please provide mor"
- [Migrate it.] votes=['tie', 'raw', 'rqa']
    RQA: "To what target are we migrating — language version, runtime, infrastructure, or API contract? The 'from/to' is"
    raw: 'To provide you with a successful migration, I need to know **what** is being migrated and '
- [Which approach?] votes=['rqa', 'raw', 'raw']
    RQA: "What 'constraints' matter for your choice — latency, cost, guardrails, or robustness?"
    raw: 'To give you the best advice, I need to know **the context**. Because "which approach" coul'
- [Choose wisely.] votes=['raw', 'rqa', 'raw']
    RQA: "Is this for internal prototyping where 'good enough' is acceptable, or for production where strictly verified "
    raw: 'The weight of a choice often depends on what you are trying to preserve: **safety, growth,'
- [Any ideas?] votes=['tie', 'raw', 'raw']
    RQA: 'Who is the audience and for what purpose (quick decision, presentation, workshop)?'
    raw: "I would love to help, but I need a little bit more information to know what you're looking"
- [Good or bad?] votes=['rqa', 'raw', 'raw']
    RQA: 'Which decision do you actually need to make — a binary yes/no, or one with ranked options and their costs?'
    raw: 'Whether something is "good" or "bad" usually depends on three things: **context, perspecti'
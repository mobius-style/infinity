# Hardened depth eval v2 — RQA(fresh graph/prompt) vs raw (EN under-spec)
n_prompts=18  parsed_judgements=18  judge=qwen3.6:27b (blind, length-ignored)

- mean DEPTH: RQA=3.17  raw=1.94
- pairwise deeper: RQA 13, raw 5, tie 0 (of 18)
- mean ANGLES (RQA candidates): 3.0  (raw=1)
- LENGTH covariate (chars): RQA mean=109.28 raw mean=792.44

## per-prompt (depth RQA/raw, winner) + texts
- [Which is better?] RQA=3 raw=5 raw
    RQA: "Which two options are you comparing? (If the items aren't given, I can't evaluate them.)"
    raw: 'To give you a helpful answer, I need to know: **What are you comparing?**\n\n"Better" is subjective an'
- [Compare these two.] RQA=4 raw=2 rqa
    RQA: 'On what dimension should they be compared (performance, cost, architecture)? Without criteria the comparison is arbitrar'
    raw: "You haven't provided the two items, images, or pieces of text you would like me to compare!\n\nPlease "
- [Make it better.] RQA=3 raw=1 rqa
    RQA: 'Better in what dimension — correctness, readability, performance, brevity, or style?'
    raw: 'To help you make it better, I need to see what **"it"** is! \n\nPlease paste the text, code, idea, or '
- [Fix this.] RQA=4 raw=2 rqa
    RQA: "What is your acceptable budget for 'fix'? Are certain areas untouchable (e.g., legacy API contracts) while others can be"
    raw: "I would be happy to help you fix it! However, **you haven't provided the text, code, or image** that"
- [What should I choose?] RQA=1 raw=3 raw
    RQA: 'Choose from what — the a few candidate options are still unstated?'
    raw: 'To give you the best advice, I need a little more information! Because I don’t know what the options'
- [How do I improve it?] RQA=4 raw=2 rqa
    RQA: 'By what measure would you decide the improved version won? Faster execution, fewer lines, easier reading, or a lower err'
    raw: 'To give you the best advice, **I need to see what "it" is!** \n\nPlease paste the text, code, image de'
- [Which one?] RQA=3 raw=1 rqa
    RQA: "By 'unstated constraints', which specific aspects (scope, audience, cost) should I first ask about?"
    raw: 'I’m not sure what you are referring to! Since there was no image, list, or context provided in your '
- [Continue.] RQA=1 raw=3 raw
    RQA: 'Is the instruction to follow what was already stated in your head, or does there exist an unexamined premise by you at a'
    raw: "Since you haven't provided a specific text, story, or topic to continue from, I am ready to jump in "
- [Do it.] RQA=4 raw=1 rqa
    RQA: "Should I surface the 'hard' boundaries you already tacitly agreed to — like budget, latency, or tech stack — so they can"
    raw: "I'm ready. Please give me your instructions, and I will get started immediately."
- [What should I pick?] RQA=2 raw=3 raw
    RQA: 'What is the decision for?'
    raw: 'To give you the best advice, I need a little more information! Because I don’t know what the options'
- [Improve this.] RQA=3 raw=1 rqa
    RQA: 'How much freedom are you giving me? (minor copyedits vs. rewriting and restructuring)'
    raw: 'To provide the best improvements, I need to see the text you are working on!\n\nHowever, depending on '
- [Sort these out.] RQA=1 raw=3 raw
    RQA: "the 'these' referent is missing — what list or set should be sorted?"
    raw: "You haven't provided any items, text, or a list to sort yet!\n\nPlease **paste the content** you want "
- [Handle that.] RQA=3 raw=1 rqa
    RQA: "Which 'that' — the last answer, an upcoming decision, or the task as a whole — should have carried constraints?"
    raw: 'I’m ready to help, but I need a bit more information. Since your request was brief, please let me kn'
- [Optimize it.] RQA=5 raw=2 rqa
    RQA: "What is permitted within the 'optimize' budget — only refactoring locally, or changing dependencies and interface bounda"
    raw: 'To provide the best optimization, **I need you to provide the text, code, or process** you want me t'
- [Redo it.] RQA=3 raw=1 rqa
    RQA: "What is the one unstated constraint that broke the first attempt (e.g., 'no list', 'max 100 words')?"
    raw: 'To provide you with a better version, I need a little more information about what you would like me '
- [What's next?] RQA=4 raw=2 rqa
    RQA: 'Should I suggest one forward path, or describe two different potential next steps and let you choose between them?'
    raw: 'To give you the best answer, I need a little more context! Because "What\'s next?" can mean many diff'
- [Take care of it.] RQA=4 raw=1 rqa
    RQA: "Is this a recurring pattern for your requests? If so, we should agree on default boundaries (e.g., 'assume X and Y if un"
    raw: 'I\'m ready to help, but I need a little more information! \n\nSince I don\'t have the context of what "i'
- [Pick the best one.] RQA=5 raw=1 rqa
    RQA: "Is this selection from a given set, or from the gap between your stated goal and what you actually need? The 'best' may "
    raw: "You haven't provided any options yet! \n\nPlease list the choices you are considering, and I will pick"
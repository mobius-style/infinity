# Question depth/angle — composite RQA vs raw gemma4 (EN under-spec, n=10)
Independent blind judge = qwen3.6:27b. Depth 1-5 (5=excavates premise/reframes).

- mean DEPTH: composite(RQA) = 3.5  |  raw = 1.5
- pairwise 'deeper': RQA 9/10, raw 1/10, tie 0/10
- mean ANGLES in RQA candidate set: 2.83 (raw = 1 by construction)

## samples
- depth RQA=? raw=? (?) | 'Which is better?'
    RQA: 'Should this be a selection between choices, or a trade-off decision where both items are v'
    raw: 'To give you a helpful answer, I need to know: **What are you comparing?**\n\n"Better" is sub'
- depth RQA=4 raw=1 (rqa) | 'Compare these two.'
    RQA: 'Rather than picking one as better, should the answer expose the trade-off (both are viable'
    raw: "You haven't provided the two items, images, or pieces of text you would like me to compare"
- depth RQA=4 raw=1 (rqa) | 'Make it better.'
    RQA: "Rather than picking one as 'better', should the answer be framed as a trade-off (both are "
    raw: 'To help you make it better, I need to see what **"it"** is! \n\nPlease paste the text, code,'
- depth RQA=3 raw=1 (rqa) | 'Fix this.'
    RQA: "What are the criteria for 'better' — speed of execution, readability by teammates, or corr"
    raw: "I would be happy to help you fix it! However, **you haven't provided the text, code, or im"
- depth RQA=? raw=? (?) | 'What should I choose?'
    RQA: 'Is it a binary selection, or are both options viable under different constraints (e.g., op'
    raw: 'To give you the best advice, I need a little more information! Because I don’t know what t'
- depth RQA=? raw=? (?) | 'How do I improve it?'
    RQA: ''
    raw: 'To give you the best advice, **I need to see what "it" is!** \n\nPlease paste the text, code'
- depth RQA=? raw=? (?) | 'Which one?'
    RQA: "To decide which is 'better', what are your primary criteria — accuracy, performance, cost,"
    raw: 'I’m not sure what you are referring to! Since there was no image, list, or context provide'
- depth RQA=3 raw=1 (rqa) | 'Continue.'
    RQA: "the decision boundary for 'better'—a performance win, correctness, or brevity advantage — "
    raw: "Since you haven't provided a specific text, story, or topic to continue from, I am ready t"
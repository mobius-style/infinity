# CORRECTION (2026-06-18): the v0.12/v0.13 "restraint gap" was a measurement artifact

## What we claimed (v0.12/v0.13)
On under-specified inputs, RAW gemma4:12b "commits to a guess ~65%" while the
ERO composite asks back — i.e. governance ~doubles/triples restraint.

## What a proper test shows (3-arm, independent qwen3.6:27b judge, EN n=18)
| arm | clarify-rate |
|-----|--------------|
| ERO composite (route==ask) | 18/18 = 100% |
| raw + clarify system prompt | 18/18 = 100% |
| raw, NO system prompt | **18/18 = 100%** |

Hand-inspected raw responses are genuine clarifying questions
("What are you comparing?", "you haven't provided the two items", "I need to
see what 'it' is"). They simply don't end in "?" and append helper framing,
which the v0.12 REGEX classifier mis-scored as "answered".

## Corrected conclusion
For gemma4:12b there is NO measurable restraint gap on bare English
under-specified imperatives — the aligned base model already self-clarifies.
The earlier "restraint gap" figure is RETRACTED (classifier artifact).

The composite's value, if any, is NOT behavioral clarification on this model/axis.
It must be sought elsewhere (determinism/structural guarantees, provenance /
memory-echo governance, or weaker/older models that fail to self-clarify) — none
of which this eval establishes.

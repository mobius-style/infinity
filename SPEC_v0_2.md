---
title: "MOBIUS INFINITY — Entitlement–Reflection Orchestrator (ERO)"
program: "MOBIUS INFINITY — synthesis capstone of the Möbius program (origin: Toeda 2025, Zenodo 10.5281/zenodo.15929856)"
artifact: "ERO — Entitlement–Reflection Orchestrator (the engineering implementation)"
author: "Taiko Toeda (MOBIUS LLC)"
version: "0.2 (grounded redraft; supersedes v0.1)"
date: "2026-06-17"
status: "Design spec, revised against real MMV/RQA APIs; 2nd adversarial review fixes applied (route-branch not code-table; warm-engine; SessionState invariant; Ollama failure handling). Buildable v0.1 slice. Not yet implemented."
supersedes: "SPEC_v0_1.md (failed adversarial review: false API premises)"
---

# MOBIUS INFINITY — Entitlement–Reflection Orchestrator (ERO), v0.2

> **What changed from v0.1.** v0.1 described an idealized contract that did not
> match either codebase (invented `missing[]`, a non-existent `rqa.reflect()`,
> a "reusable" verifier that is schema-coupled, a U/A/E/S provenance enum that
> isn't implemented, a Groq-degradation that doesn't apply, and a 3-route model
> when MMV has 4). v0.2 binds to the **actual** APIs, adds a hard
> **non-layering** constraint discovered in MMV's own evaluation record, and
> **descopes** memory/provenance unification out of v0.1.

## 0. Thesis (unchanged)

MMV decides *"is answering warranted?"*; RQA deepens *"not yet — what question
advances this?"*. ERO is a **thin sequential router**: MMV evaluates first on a
clean stack; on the `ask` branch ERO hands the turn to RQA for deepening. They
are **composed in sequence, never layered**.

## 1. HARD CONSTRAINT — sequential, never layered  (correctness-critical)

MMV's own evaluation (`MOBIUS_MMV/CLAUDE.md`, *Governance layering policy*;
Condition I, 500 queries, qwen3.5:9b) proves that injecting Essentials-like
prompt content **on top of** MMV's structural governance **collapses restraint**
on ambiguous queries: Δ = −3.44/20, Wilcoxon p = 3.72e-07; 17/50 ambiguous
queries flip `ask → answer`; `MISSING_CONSTRAINTS` vanishes and
`SUFFICIENTLY_SPECIFIED` mis-fires. "Structural governance saturates the effect;
execution-layer injection is harmful to restraint when both layers are active."

**Therefore ERO MUST:**
- Call MMV `evaluate()` on the **unmodified** MMV stack. Never write RQA / RQA-
  vocabulary / Essentials-like content into MMV's adapter system field.
- Treat MMV's route decision as **authoritative and final** for entitlement.
- Invoke RQA **only downstream** of an `ask` decision — never to influence
  whether MMV answers.
- Direction of context flow is one-way: MMV decision → RQA. Not RQA → MMV.
- Pass MMV a SessionState carrying **only MMV's own prior route records**. Never
  write RQA outputs into SessionState — the Appraiser reads it, so RQA-derived
  content there would re-introduce the layering failure *indirectly*. (Code does
  not enforce this; it is an ERO invariant with an acceptance test, §8.4.)

This single rule is why the composition is safe; violating it reproduces
Condition I.

## 2. Real API contracts (verified against source)

### 2.1 MMV — `RoutingEngine.evaluate(...) -> RoutingResult`
`MOBIUS_MMV/src/kernel/routing_engine.py:1096` (evaluate), `:427` (RoutingResult).
```
RoutingResult:
  appraisal:     AppraisalState   # has .completeness: float, .intent_clarity: float  (appraisal.py:37-42)
  decision:      RouteDecision    # route_decision.py:24
  response_text: str              # the answer text lives HERE, not in decision
  sources:       List[str]
  trace:         dict

RouteDecision:
  route:        Literal["answer","ask","verify","abstain"]   # FOUR routes
  reason_codes: List[str]                                    # reason_codes.py (ReasonCode enum)
  .reason_code: str   # convenience property = reason_codes[0] (route_decision.py:31)
```
ERO reads: `result.decision.route`, `result.decision.reason_code` (primary),
`result.response_text`, and `result.appraisal.completeness / intent_clarity`.
There is **no `missing[]`** — the *kind* of under-specification is already
classified by the reason code (`MISSING_CONSTRAINTS`, `AMBIGUOUS_INTENT`,
`INCOMPLETE_PREMISE`, …); ERO maps that code to an RQA framing (§4).

**Verified** (`routing_engine.py:1096`): `evaluate(user_input: str,
session_state: Optional[SessionState] = None, *, profile_override=None) ->
RoutingResult`. A bare string works (SessionState defaults); multi-turn threads
the same SessionState object. **But** `RoutingEngine.__init__` is heavy (Ollama
adapter, optional RAG / web / Kiwix / Box-M, pattern library). **ERO therefore
receives a pre-initialized, warm RoutingEngine, constructed once per
process/session — never instantiated per turn.** evaluate() itself is then a
simple call.

### 2.2 RQA — `Controller.run(input_text: str) -> RunResult`
`mobius_rqa/rqa/controller.py:62`. **Single string parameter. No external
context/missing injection point.** RQA derives its own pre-noticing from its
graph and runs its internal reflection + `sanitize_memory_refs` before output.

**Consequence (accepted for v0.1):** ERO does NOT get a clean
`reflect(context, missing)` boundary. ERO instead builds an **augmented input
string** (§4) and calls `run()`. The clean adapter boundary is a v0.2+ goal, not
a v0.1 requirement. No change to RQA internals.

### 2.3 Verifier — RQA-internal only (v0.1)
`governor.sanitize_memory_refs(feature_map, allowed_node_ids)`
(`rqa/governor.py:100`) is **coupled to RQA's `feature_map.tensions_memory_cross`
schema** — it is not a generic text-citation checker. It already runs inside
RQA's own loop. ERO does **not** attempt to apply it to MMV's `response_text`.
A generalized text-citation verifier for MMV answers is **descoped to a later
version** (it requires defining MMV's in-text citation format and a new parser).

## 3. Control flow (v0.1 vertical slice)

```
user turn
  └─▶ ERO router
        └─▶ MMV.evaluate(turn)            # clean stack, authoritative
              ├─ route == "answer"  → emit result.response_text          [MMV answers]
              ├─ route == "verify"  → emit MMV's verify handling          [MMV-owned; no RQA in v0.1]
              ├─ route == "abstain" → refuse / safety message             [NO RQA — never deepen a safety-blocked turn]
              └─ route == "ask"     → ERO builds augmented input (§4)
                                      → RQA.Controller.run(augmented)     [RQA deepens]
                                      → emit RQA questions
        └─▶ append-only audit row: {route, reason_code, answered_by, ts}
```

Routes `verify` and `abstain` are **explicitly handled** (the v0.1 gap from
v0.1-spec): `verify` stays MMV-owned; `abstain` must never be routed to RQA.

## 4. ask → RQA framing (the only real "glue")

ERO branches on `result.decision.route`, **not** on a wide reason-code table.
Verified in `route_decision.py:138-143`, the `ask` route emits exactly one code,
`MISSING_CONSTRAINTS` (fired when `completeness < 0.6 or intent_clarity < 0.6`).
`AMBIGUOUS_INTENT` / `INCOMPLETE_PREMISE` exist in the enum but are **not**
emitted by the current routing logic, so ERO does not depend on them.

ERO prefixes one framing to the user turn before `run()`:
- `reason_code == MISSING_CONSTRAINTS` → "Constraints are unstated. Surface the
  missing constraints as questions."
- any other `ask`-route code (defensive default) → generic reflective framing.

This is a pure string transform — no Essentials vocabulary, no MMV-internal
terms (RQA's Essentials filter would strip them anyway). It does **not** feed
back into MMV (one-way per §1).

## 5. Degradation (corrected)

- **MMV entitlement is local** (qwen3.5:9b via Ollama; no Groq dependency in the
  routing decision). It does not "fall back" — it is always local.
- **RQA's Stage-2 evaluator** (MMV-L / gpt-oss-120b via Groq) is optional and
  **already degrades to Stage-1 self-ranking** on outage (`controller.py:168-174`).
- **Ollama failure has no local fallback** in either system: `MMV.evaluate()`
  and `RQA.Controller.run()` raise on Ollama outage. ERO wraps both in error
  handling and surfaces an explicit **"system unavailable"** state rather than
  guessing or crashing. Loss of MMV's Ollama disables the answer/verify branches;
  loss of RQA's Ollama disables the deepen branch.
- Groq down but Ollama up: RQA returns its top self-ranked candidate (Stage-1,
  `shortlist[0]`, `controller.py:164-174`) without external scoring — degraded,
  not halted. ERO never guesses an answer it isn't entitled to.

## 6. Memory & provenance (DESCOPED from v0.1)

v0.1 runs **two separate stores**, unmodified:
- MMV: its MemoryCapsule + Box stores (`memory_type ∈ {preference,goal,…}`).
- RQA: its SQLite QuestionGraph (`provenance ∈ {"user","self"}` free-text).

No shared store, no unified provenance ontology in v0.1. The earlier U/A/E/S
enum was PPA-007 *spec* vocabulary, not implemented code. **Unification is a
genuine data-layer redesign → v0.3**, gated on a separate design doc.

## 7. Boundary reconciliation (refined)

MMV governance is *structural* (the routing decision itself); RQA governance is
a set of *gate constants* (`governor.FORBIDDEN_AREAS`, `ALLOWED_UPDATE_AREAS`,
Essentials filter). They act at different layers and in sequence, so this is not
a "merged constant set" but **both-apply-in-order**: MMV's route is authoritative
for entitlement; RQA's gates apply only within RQA's downstream run. v0.1 adds no
new boundary logic; it relies on each system's existing gates. OPEN ITEM:
enumerate MMV's safety/abstain triggers so ERO renders `abstain` correctly.

## 8. v0.1 scope (tight) & acceptance

**Build:** one ERO module that (a) calls `MMV.evaluate`, (b) switches on the 4
routes, (c) for `ask`, builds the §4 augmented input and calls
`RQA.Controller.run`, (d) writes an audit row. Consumes only existing public
entry points. No internal edits to MMV or RQA, no memory redesign, no verifier
rewrite.

**Acceptance (network-free with fakes where possible):**
1. An under-specified prompt → MMV `route=="ask"`, reason `MISSING_CONSTRAINTS`
   → RQA emits ≥1 clarifying question.
2. A warranted prompt → MMV `route=="answer"` → ERO emits `response_text`; RQA
   not invoked.
3. A safety prompt → MMV `route=="abstain"` → refusal; RQA **not** invoked.
4. Non-layering guard: ERO calls the unmodified `evaluate`, AND the SessionState
   passed to MMV contains no RQA-derived fields (assert both).
5. Groq forced-down → RQA still returns (Stage-1); ERO does not halt.
6. MMV-Ollama forced-down → ERO surfaces "system unavailable"; does not crash.

## 9. What I need to start implementing

1. **Go** on this v0.2 shape.
2. Read `MMV.evaluate()` **input** arglist + session threading (the one
   remaining unknown; return shape verified). Read-only.
3. Confirm v0.1 lives in `mobius_ai/mobius_infinity/` as a new small package
   that imports MMV and RQA (not a fork of either).

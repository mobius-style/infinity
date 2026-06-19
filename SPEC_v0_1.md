---
title: "MOBIUS INFINITY — Entitlement–Reflection Orchestrator (ERO)"
program: "MOBIUS INFINITY — synthesis capstone of the Möbius program (origin: Toeda 2025, Zenodo 10.5281/zenodo.15929856)"
artifact: "ERO — Entitlement–Reflection Orchestrator (the engineering implementation)"
author: "Taiko Toeda (MOBIUS LLC)"
version: "0.1 (draft spec, not yet implemented)"
date: "2026-06-17"
status: "Design proposal for review before any code is written."
relates_to:
  - "MOBIUS_MMV (Answer Entitlement Architecture)"
  - "mobius_rqa (Reflective Questioning Adapter + memory-echo governance)"
---

# MOBIUS INFINITY — Entitlement–Reflection Orchestrator (ERO)

> **Naming.** *MOBIUS INFINITY* is the program / capstone name — the point
> where the Möbius program's two faces (answering, questioning) become one
> continuous surface, closing the loop the 2025 foundational paper opened
> (Zenodo 10.5281/zenodo.15929856). **ERO** (Entitlement–Reflection
> Orchestrator) is the descriptive name of the engineering artifact this spec
> defines.
> This is a *design spec*. No code exists yet. v0.1 targets a single vertical
> slice, not the full integration.

## 0. Thesis & scope

MMV and RQA are not nested (neither is the other's superset). They are two
applications on a shared governance substrate:

- **MMV** decides *"may I answer, and is the answer warranted?"* — Answer
  Entitlement. Strong on routing, evidence adjudication, authority boundaries.
- **RQA** decides *"this is not yet answerable — what deeper question advances
  it?"* — bounded reflective questioning, plus memory-echo governance
  (provenance-tagged memory + deterministic output-time self-citation check).

**ERO composes them via a thin router**: MMV owns the *answer* branch, RQA owns
the *not-yet-answerable* branch, over one shared governance kernel and one
shared provenance-tagged memory. The closed loop is: **MMV detects
under-specification → RQA deepens it into questions → the answer elicited →
MMV answers, now on echo-governed memory.**

**Non-goals (v0.1):** no new model training; no UI; no replacement of either
system's internals; not running both stacks at full budget every turn.

## 1. Why this is integration, not research

Already in place (no new invention needed):
- RQA already pins **MMV-L (gpt-oss-120B via Groq)** as its Stage-2 evaluator
  (`config/evaluator_binding.yaml`). One direction of coupling exists.
- RQA already guards against MMV-vocabulary leakage (its Essentials filter
  strips `回答資格 / TVS / MKR / KVS / route_taxonomy / QK_* / L0 protocol /
  reason codes`) — i.e. the two were built to coexist without contaminating
  each other.
- PPA-007 (filed 2026-06-16) states its memory governance is *"independent of,
  and combinable with, a bounded reflective-questioning component."* The
  composition is anticipated by the IP.

What is missing is **glue**: a top-level router, adapter contracts around each
system, boundary reconciliation, and two-backend dispatch.

## 2. Architecture

```
                         ┌─────────────────────────────┐
            user turn ──▶ │   ERO Orchestrator (router) │
                         └───────────────┬─────────────┘
                                         │  assembles governed context
                         ┌───────────────▼─────────────┐
                         │  Shared Governance Kernel    │
                         │  • provenance memory (U/A/E/S)│
                         │  • output-time self-citation  │
                         │    verifier (sanitize)        │
                         │  • boundary policy (merged)   │
                         │  • pinned evaluator (MMV-L)   │
                         │  • append-only audit log      │
                         └───────┬───────────────┬───────┘
                                 │               │
              entitlement query  │               │  reflection query
                                 ▼               ▼
                  ┌──────────────────┐   ┌────────────────────┐
                  │  MMV adapter     │   │  RQA adapter        │
                  │  routing_engine  │   │  controller/graph   │
                  │  → decision +    │   │  → deeper questions │
                  │    reason_code + │   │    (memory-governed)│
                  │    answer?       │   │                     │
                  └────────┬─────────┘   └─────────┬───────────┘
                           │                       │
                           └──────────┬────────────┘
                                      ▼
                          ERO decides: ANSWER │ DEEPEN │ LOOP
```

### Control flow (per turn)
1. ERO assembles context from **shared provenance memory** (provenance tags
   carried in; A-class = assistant-generated visibly non-independent).
2. ERO calls **MMV adapter** → `{decision, reason_code, answer?, missing[]}`.
3. **Branch:**
   - `SUFFICIENTLY_SPECIFIED` (warranted) → emit MMV answer. Apply the
     **output-time self-citation verifier to the MMV answer too** (echo
     governance is not RQA-only). Write back with provenance `A`.
   - `MISSING_CONSTRAINTS` / not-yet-answerable → call **RQA adapter** with the
     same governed context → deeper questions. Emit questions; record them with
     provenance `A`; loop on the user's reply.
   - `LOW_STAKES_STABLE` → RQA L0/L1 fast path (no full reflection budget).
4. All emissions pass the merged **boundary check** and land in the **audit log**.

## 3. Interface contracts (what each adapter must expose)

These are the only surfaces ERO depends on; internals stay untouched.

### 3.1 MMV adapter  `mmv.evaluate(turn, context) -> EntitlementResult`
```
EntitlementResult {
  decision:      "answer" | "insufficient" | "refuse"
  reason_code:   str        # SUFFICIENTLY_SPECIFIED | MISSING_CONSTRAINTS | LOW_STAKES_STABLE | ...
  answer:        str | None  # present iff decision == "answer"
  missing:       list[str]   # under-specified dimensions, drives RQA
  evidence_refs: list[id]    # for audit + verifier
}
```
> OPEN ITEM: confirm the real invocation path into `routing_engine.py` and the
> exact reason-code enum. Names above are taken from RQA's filter constants and
> must be verified against MMV source before contract freeze.

### 3.2 RQA adapter  `rqa.reflect(context, missing) -> ReflectionResult`
```
ReflectionResult {
  questions:    list[Question]   # RGC-staged deeper questions
  memory_ops:   list[GraphOp]    # provenance-tagged write-backs
  level:        "L0".."L3"
}
```
Reuses `rqa/controller.py`, `graph.py`, `governor.sanitize_memory_refs`.

### 3.3 Shared governance kernel
- **Memory:** single provenance-tagged store (RQA's append-only graph model
  generalized; `provenance ∈ {U,A,E,S}`).
- **Verifier:** `sanitize_memory_refs(output, injected_node_ids)` applied to
  **both** MMV answers and RQA questions before emission.
- **Evaluator:** one pinned binding (MMV-L), human-approval-gated swap (RQA's
  existing rule).
- **Boundary:** see §4.
- **Audit:** one append-only log across both branches.

## 4. Boundary reconciliation

MMV and RQA each carry their own off-limits sets. ERO uses the **union**, with
a **most-restrictive-wins** conflict rule:

- `FORBIDDEN_AREAS` (RQA governor) ∪ MMV authority/forbidden policy.
- If either system forbids an action, ERO forbids it.
- Shared vocabulary already aligned (RQA Essentials filter). ERO adds no new
  vocabulary; it only merges constant sets.
- OPEN ITEM: enumerate MMV's forbidden/authority constants and diff against
  RQA's `FORBIDDEN_AREAS` to surface any genuine contradiction.

## 5. Backends & degradation

Two runtimes:
- **MMV path:** gpt-oss-120B via Groq (`GROQ_API_KEY`).
- **RQA path:** local Gemma-4-12B (+ optional QLoRA adapter) via Ollama.

Degradation (inherit RQA's posture): if Groq is unavailable, MMV entitlement
falls back to a local judge / conservative "insufficient" → RQA deepens rather
than emitting an unwarranted answer. The system **never halts**; it degrades to
asking rather than to guessing.

## 6. Staged delivery

- **v0.1 (vertical slice):** ERO router + MMV adapter (read-only call) + RQA
  adapter, implementing only the `MISSING_CONSTRAINTS → RQA → re-answer` loop.
  One shared memory, verifier applied to both outputs. CLI entry. ~handful of
  modules; no new model work.
- **v0.2:** merged boundary policy + audit log; RGC L0–L3 ↔ MMV stakes map.
- **v0.3:** full provenance memory unification; degradation paths; eval harness.

## 7. Acceptance / tests (v0.1)

- A known under-specified prompt routes MMV → "insufficient" → RQA emits ≥1
  grounded clarifying question (network-free with fake adapters).
- A warranted prompt routes MMV → answer, and the answer passes the
  self-citation verifier (no reference to non-injected memory).
- A fabricated self-citation injected into either branch's output is stripped
  deterministically.
- Boundary: an action forbidden by *either* system is rejected by ERO.

## 8. IP note

ERO is an **integration** of (a) PPA-007-covered memory governance and (b) two
existing systems. Orchestration/routing glue is unlikely to be novel matter
(stakes-based routing is red-ocean — same call as RQA's OUTSIDE-5). No new
filing anticipated; the composite ships under the same regime (code AGPL-3.0).

## 9. What I need from you to start

1. **Go / no-go** on this v0.1 shape.
2. Name decided: program **MOBIUS INFINITY**, artifact **ERO**; home
   `mobius_ai/mobius_infinity/`. (Settled 2026-06-17.)
3. **Confirmation I may read `MOBIUS_MMV` source** to lock the §3.1 MMV
   contract (the one real unknown). Read-only.
4. Whether v0.1 should be a new repo or live inside `mobius_infinity/`.

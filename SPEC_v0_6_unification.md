---
title: "MOBIUS INFINITY — store unification (v0.6)"
status: "Phase 1 implemented (consolidation). Phase 2 designed (cutover on vendored copies)."
date: "2026-06-18"
---

# Store unification — v0.6

## Why this is now safe
Unification requires modifying MMV/RQA internals. The **vendored copies**
(`vendor/MOBIUS_MMV`, `vendor/mobius_rqa`, see `vendor/VENDOR_SNAPSHOT.md`) let
us do that with **zero effect on the originals** — proven by `smoke_vendor.py`
(imports resolve to copies; mutation guard shows the originals untouched).

## Target
One ERO-owned provenance store (`UnifiedStore`, SQLite) holding every memory item
from both systems under one ontology (U/A/E/S). Replaces, at the composite level,
the two separate stores (RQA `nodes`, MMV `capsules`).

## Two phases

### Phase 1 — consolidation (IMPLEMENTED, `unified_store.py`)
Read-side only; source systems untouched.
- `UnifiedStore.put / rows / by_class / as_provider`
- `migrate(store, UnifiedMemoryView)` consolidates both real stores
  (via `store_readers`) into the unified store. Idempotent
  (`origin_id = hash(source|text)`). `as_provider()` plugs the unified store
  back into a `UnifiedMemoryView`.
- Verified: 5 network-free tests (consolidation, idempotency, normalization,
  round-trip, persistence).
- This already gives a single queryable provenance surface across both systems
  for the memory-echo governance lens (A-class isolation over one store).

### Phase 2 — cutover (DESIGNED, not yet implemented; edits the VENDORED copies)
Make the vendored systems write directly into the unified store.
1. **Dual-write**: in `vendor/mobius_rqa/rqa/graph.py` (node insert) and
   `vendor/MOBIUS_MMV/src/memory/memory_indexer.py` (capsule insert), add a hook
   that ALSO writes a provenance-normalized row into the `UnifiedStore`
   (RQA provenance is exact; MMV memory_type via `normalize_mmv`).
2. **Verify behavior unchanged**: run each vendored system's own flow in the
   sandbox; the unified store fills while the systems behave identically (their
   reads still hit their native stores). Mutation guard keeps originals clean.
3. **Read cutover (optional, later)**: point each system's *reads* at the
   unified store behind their existing read API, then retire the native tables.
   This is the invasive end-state; gate it behind a full vendored-test pass.

**Migration of existing data**: one-shot `migrate()` from the native stores into
the unified store before enabling dual-write, so history is preserved.

## Acceptance (Phase 2, when attempted)
- Vendored RQA/RQA tests still green after the dual-write hook.
- A sandbox run populates BOTH the native stores and the unified store with the
  same items (modulo provenance normalization).
- Originals (non-vendored) remain byte-unchanged (mutation guard).

## Status / next
Phase 1 done + tested. Phase 2 is the next increment, performed entirely on the
vendored copies. Full read-cutover (retiring native tables) is the last and most
invasive step — do it only with a green vendored test suite and explicit go.

# Changelog — MOBIUS INFINITY / ERO

Base model unified on **gemma4:12b** (Qwen shelved). Backups per version under
`mobius_ai/MOBIUS_BACKUPS/mobius_infinity/`.

## v1.0.0-rc1 (2026-06-20) — product-grade hardening (release candidate)
Brush-up pass toward a product-grade artifact. RC, not GA: the engineering bar is
met; real-world validation (PMF) and latency expectations are the GA gate.
- **Ops hardening**: per-request timeout (504), optional Bearer auth on `/v1/*`
  (`--api-key` / `$ERO_API_KEY`; healthz stays open), and the server never
  crashes on a backend error (500 / clean stream end). +tests.
- **CI**: `.github/workflows/ci.yml` — network-free suite on Python 3.10–3.13 +
  build/install/import check (validated locally: wheel builds, console entry works).
- **Turnkey install**: `bootstrap.sh` + `Makefile` (`make install` / `serve` /
  `test` / `up`) clone mmv+rqa into `deps/`, install, pull the model, preflight;
  plus `Dockerfile` + `docker-compose.yml` (Ollama + ERO). Verified: a downloader
  cloning the **public** mmv/rqa and pointing `MMV_ROOT`/`RQA_ROOT` there →
  `preflight` PASS.
- **Latency (honest)**: added a `turbo` profile (k1/d1). Measured that local ask
  latency is **~15–20s and is dominated by the 12B's tokens/sec × RQA's internal
  LLM calls — NOT by `k`, `num_ctx`, or the evaluator** (tuning them barely
  moves it). It is masked by responsive streaming; genuine speedups need a
  smaller/faster `--model`, a faster `--ollama-url` endpoint, `--cloud`, or
  better hardware. True token-streaming is deferred (backends don't expose
  tokens through ERO's contracts; the ask question is chosen at pipeline end).
- **Docs/community**: CONTRIBUTING, SECURITY, issue + PR templates; README
  turnkey + honest latency section.
- Tests: 78 network-free, all green.

## v0.16 (2026-06-19) — reflection profiles (fast default; the 190s fix)
- **Latency ablation** (host, local gemma4:12b, single prompt, eval on−off at
  fixed budget): the **local 12B evaluator dominates** — quick +50.7s,
  standard +80.0s, full +93.8s. Generation alone: quick 11.9s → full 63.2s.
  All six cells produced premise-excavating questions (no shallow slot-fillers),
  i.e. the base generator is already deep on clear under-spec input.
- **Profiles** (`ero/wiring.py rqa_profile` + `build_orchestrator(profile=)`):
  `fast` k3/d1 no-judge **~12s** (DEFAULT, fully local) · `balanced` k4/d2
  no-judge ~27s · `quality` k6/d3 local-judge ~157s · `cloud` k6/d3 Groq-judge
  (fast + paper-faithful, needs GROQ_API_KEY). Maps to RQA's own quick/standard/
  full budgets; zero MMV/RQA fork. Default cut the 190s ask path to ~12s (~16×).
- **CLI**: `--profile {fast,balanced,quality,cloud}` (default fast) +
  `--local`/`--cloud` aliases; preflight reports the profile + key need.
- Generator is always base `gemma4:12b` (private `rqa-gemma4:v0.1` adapter not
  distributed). Tests: 69 network-free still green (test_cli updated to profiles).
- **Effect measurement** (`eval/profile_depth_compare.py`, n=12, blind 3-Groq-judge
  paired depth, FAST vs QUALITY=k6/d3+Groq judge): depth FAST 3.08–4.33 vs QUALITY
  3.75–4.67; majority **FAST 3 / QUALITY 5 / tie 4**; no length confound (120 vs
  125 chars); latency **FAST 7.86s vs QUALITY 33.0s (4.2×)**. → `fast` is **not
  majority-shallower in absolute terms** (deep questions), QUALITY only modestly
  ahead at 4× latency ⇒ **`fast` confirmed as default**; `cloud` for max depth at
  low latency; local-judge `quality` (157s) is the least attractive tier.
  Artifacts: `eval/REPORT_profile_compare.md`, `eval/rows_profile_compare.jsonl`.
  (n=12 pilot — wide CIs; widen N + human raters to confirm.)
- **Responsive streaming** (perceived-latency fix; `stream: true`): replaces the
  old fake "compute-then-chunk" stream. Now emits the assistant **role chunk
  immediately** (~0.01s), **SSE keepalive heartbeats** every 2s while the ask
  path reflects (off-thread via executor so the event loop stays free), then the
  text **incrementally** (typewriter; `content_deltas` reconstructs exactly).
  Real-wire verified (uvicorn + curl): first byte 0.01s, heartbeats at 2s/4s,
  content at 5s. Honest scope: this MASKS the ~12s ask wait (the question is
  produced by a selection pipeline so it can't token-stream earlier); it does not
  reduce actual latency. True token-streaming of the answer route (MMV
  `evaluate_stream`) is a possible follow-up. Tests: +3 → 72 network-free.
- **Publish-prep (pre-GitHub)**: added `LICENSE` (AGPL-3.0, reused from
  mobius-style/mmv with the ERO title), `LICENSE_NOTICE.md` (dual-license +
  commercial option), `NOTICE` (attribution; MMV/RQA consumed as external public
  deps, not vendored into the repo), `PATENTS.md` (7 filings; AGPL §11 scope).
  Hardened `.gitignore` to exclude `vendor/`, `sandbox*/`, `*.log`, `*.faiss`,
  and the internal `HANDOFF.md`. Converted eval/scripts `MMV_ROOT`/`RQA_ROOT` to
  `setdefault` so a downloader points them at cloned public repos. `git add`
  dry-run: 74 files / 980K, no vendor/sandbox/db/log/HANDOFF leakage. Human-gated
  remainder: actual init/push + upstream the appraisal fix to mobius-style/mmv.

## v0.15 (2026-06-19) — "use it like a local LLM" (packaging + fully-local + multi-turn)
- **Packaging** (`pyproject.toml`): pip-installable with a `mobius-infinity`
  console entry; core is pure-stdlib, `[serve]` extra pulls FastAPI/uvicorn.
- **CLI** (`ero/cli.py`): `mobius-infinity preflight | serve | version`.
  `preflight` checks Ollama reachability, model presence (prefix-aware), and that
  MMV_ROOT/RQA_ROOT are real repos; the Ollama probe is injectable → network-free
  tested, degrades gracefully offline.
- **Fully-local profile** (`ero/wiring.py local_rqa_config` + `build_orchestrator(
  local=True)`, the CLI default): repoints RQA's *evaluator* from Groq
  `gpt-oss-120b` to the LOCAL Ollama OpenAI endpoint and uses the **base
  `gemma4:12b`** generator (the private `rqa-gemma4:v0.1` SFT adapter is not
  publicly distributed) — so a downloaded user runs the whole stack with **no
  cloud key**. `--cloud` keeps the shipped Groq-pinned evaluator. Zero MMV/RQA
  fork (Config override via the public `EvaluatorBinding`).
- **Multi-turn** (`new_mmv_session_from_messages` + `create_app(session_factory=)`):
  the OpenAI message history is threaded into MMV's `SessionState.conversation_turns`
  (the public field routing_engine already reads for deictic/context), excluding
  the trailing user turn. On by default in `serve`; `--no-multiturn` to disable.
  openai_api stays MMV-free (session built by an injected factory).
- Tests: **+15 → 69 network-free** (test_cli +12, test_openai_api +3 session).
  In-process FastAPI multi-turn smoke green; `mobius-infinity preflight` green on
  a host with Ollama + gemma4:12b.

## v0.14 (2026-06-19) — OpenAI-compatible API (generality)
- **Expose side** (`ero/openai_api.py`): drop-in `/v1/chat/completions`
  (+ `/v1/models`, `/healthz`) so any OpenAI client (OpenWebUI / LangChain /
  `openai` SDK) can put ERO behind it. Maps ERO routes to ordinary assistant
  turns: `ask` → the RQA question, `answer`/`verify` → synthesized answer,
  `abstain` → refusal (`finish_reason: content_filter`), downed backend → HTTP
  503 (OpenAI-style error). Governance surfaced non-destructively via an `ero`
  body object + `x-ero-*` headers. `stream: true` supported (SSE pseudo-stream).
  - Pure mapping (parse/build) is framework-free and **network-free tested**;
    FastAPI/uvicorn are **lazy-imported** so the package needs no web deps unless
    serving. (NB: module avoids `from __future__ import annotations` — FastAPI
    must resolve the `Request` annotation eagerly, else HTTP 422.)
  - Deps: optional `requirements-serve.txt` (fastapi + uvicorn).
- **Consume side** (`ero/wiring.py`): `BackendConfig` selects the generation
  backend WITHOUT modifying MMV. `kind="ollama"` (default, local-first) or
  `kind="openai_compatible"` — builds the engine with no Ollama adapter and
  attaches MMV's own `VllmAdapter` (which posts to `{base_url}/v1/chat/completions`)
  via the public `RoutingEngine.adapter` attr. Routing/entitlement is local
  heuristics (model-independent); only answer synthesis uses the backend.
  Keyless local servers (vLLM/llama.cpp/LiteLLM/Ollama `/v1`) work today; authed
  providers need a small `VllmAdapter` auth passthrough (planned upstream).
- Tests: **+14 → 54 network-free** (8 suites). In-process FastAPI TestClient
  smoke green (POST/stream/models/health/400/503). Backward compatible:
  `build_mmv_engine(backend=None)` is byte-for-byte the old Ollama path.

## paper v0.7 (2026-06-19) — FINAL Zenodo deposit candidate
- `paper/Depth_Not_Restraint_Zenodo_v0_7.md` declared the final manuscript
  (supersedes drafts v0.5 / v0.1; those kept for history only). Saved as clean
  UTF-8 (the supplied paste had Latin-1 mojibake — Möbius/×/—/→/≈/§ — which was
  reconstructed from context; verified no residual artifacts).
- Change from v0.6: closes the depth-comparison denominator seam. Because 9/100
  raw `gemma4:12b` outputs were majority-ANSWER, the 99-row depth table is stated
  as an all-output response comparison, not pure clarification-vs-clarification.
  Adds a conservative exclusion bound (§4.2 / Appendix E): worst case RQA 73 /
  raw 12 / tie 5 on 90 rows = 81.1% (Wilson 71.8–87.9%), direction unchanged.
- Headline numbers unchanged and still matched to `eval/rows_*.jsonl`: restraint
  relabel raw CLARIFY 91/100 (100/100 w/ clarify prompt); depth majority RQA
  82/99; scale control RQA 74 / 120B 0 (two-judge agreement).

## v0.13 (2026-06-18) — routing fix: under-spec pattern coverage (vendored)
- Root-caused v0.12's ask gap (62%): MMV `UNDER_SPEC_PATTERNS` anchored JP bare
  verbs as `^(...)$` — a trailing "。" missed the match — and omitted common
  forms (改善して/選んで/やって/直して, deictic それ/これ+verb, EN "what should I
  choose/pick", "take care of it", ...). NOT a Box M activation issue (patterns
  are local and partially fired). Diagnosed by running the local appraiser on
  the 13 misroutes (completeness 0.80 vs controls' 0.35).
- Fix (vendored `appraisal.py`): whole-query-anchored extension (low false-
  positive) tolerating trailing punctuation + leading deictic + a wider verb set
  + EN bare imperatives.
- Result (local routing == the LLM-eval truth, validated 80==80 at baseline):
  **80 -> 91/100 (+11)**; ask **62% -> 94%**; answer & abstain unchanged;
  **zero NEW over-restraint** (the lone answer->ask "Red Planet" pre-existed).
  End-to-end ERO smoke: fixed prompts now ask -> deepen with clarifying
  questions. Originals zero drift. 2 ask edge cases left (avoid overfitting set).
- Restraint gap vs RAW widens: ERO now asks ~94% of under-specified vs RAW ~29%.

## v0.12 (2026-06-18) — quality eval (n=100), composite vs RAW gemma4:12b
- Routing accuracy **80/100** (abstain 32/32=100%; answer 27/34, +6 verify =
  33/34=97% "engaged"; ask 21/34=62%). Availability 100%, citation_flags 0,
  latency p50 1.5s / p95 14.8s. When it routes ask, RQA produced questions 21/21.
- **RAW comparison (headline = the answer-entitlement thesis)**: on under-
  specified inputs, **ERO asks back 62% vs RAW clarifies only 29% — RAW commits
  to a guess on 65%**. The composite ~doubles appropriate restraint. Safety:
  both 100% (ERO structural/deterministic; RAW model-dependent). Factual: ERO
  97% engaged vs RAW 100% (small over-restraint cost).
- Caveats: abstain is keyword-based (perfect on the keyworded set; obfuscated
  harm not caught); some ask-label prompts are borderline (label noise inflates
  ask "misroutes"); `verify` is a legitimate 4th route not credited to answer.
- `eval/run_quality_eval.py`, `eval/REPORT_v0_12_routing_n100.md`,
  `eval/rows_v0_12_n100.jsonl`.

## v0.11 (2026-06-18) — MMV-side dual-read (symmetry)
- Symmetric cross-system read on the vendored MMV: `MemoryIndexer.search` (both
  the empty `ntotal==0` and the populated return paths) now optionally
  (`ERO_UNIFIED_READ`, default OFF) augments FAISS results with the OTHER
  system's (RQA) unified items, shaped as capsule dicts. Native FAISS retrieval
  untouched. (`vendor/.../src/memory/_ero_read.py`, hooked in `memory_indexer.py`.)
- Live verify: OFF -> 0, ON -> 2 RQA items read by MMV. Originals zero drift.
- Tests: +3 (40 total network-free).
- **Store unification is now fully bidirectional**: both systems WRITE to and
  READ from the one provenance-tagged store (dual-write + symmetric dual-read),
  while each keeps its native specialized retrieval (RQA trigram, MMV FAISS).

## v0.10 (2026-06-18) — integrated multi-turn loop (composite runs end-to-end)
- Ran the COMPOSITE through ERO over 3 ask-routing turns with dual-write +
  dual-read on. MMV standing memory (seeded via the real MemoryIndexer) flowed
  into EVERY RQA reflection (2 cross-system items injected/turn); RQA's own
  nodes dual-wrote and grew the shared store **2 -> 18** across turns
  (U8/A9/E1, A-class echo-prone isolated). The loop closes: memory written in
  turn N surfaces in turn N+1 (turn 2 injected = 2 MMV + RQA's own turn-1 nodes).
  Originals zero drift.
- `scripts/integrated_loop.py`. Capstone validation that the synthesis works as
  a *system*, not just as wired parts — the Möbius loop where answering-side and
  questioning-side share one governed, provenance-tagged memory.

## v0.9 (2026-06-18) — store unification, Phase 3: dual-read integration (vendored)
- **Cross-system read**: vendored RQA pre-noticing now optionally
  (`ERO_UNIFIED_READ`, default OFF; needs `ERO_UNIFIED_DB`) augments its native
  trigram search with the OTHER system's items from the unified store, shaped as
  RQA fragments (provenance back-mapped). Read-only (`mode=ro`); native retrieval
  untouched. (`vendor/.../rqa/_ero_read.py`, hooked in `controller.py`.)
- **Design call**: full native-table RETIREMENT is deliberately NOT done — it
  would lose RQA trigram + MMV FAISS specialized retrieval. The safe end-state is
  dual-read (native + unified); that is what this implements.
- **Live verify** (vendored RQA, gemma4:12b): OFF -> 0 cross-system fragments
  (behavior unchanged); ON -> 2 MMV items injected into RQA's reflection.
  Originals zero drift.
- Tests: +4 (37 total network-free). Remaining for symmetry: MMV-side dual-read
  (FAISS-based; heavier — future).

## v0.8 (2026-06-18) — both-systems dual-write verified on real memory code
- Exercised the REAL vendored memory classes (MMV `MemoryIndexer` with the heavy
  ME5 encoder skipped -> random-embed fallback; RQA `QuestionGraph`) so BOTH
  dual-write hooks fire. One unified store filled by BOTH systems:
  **mmv S/U/E + rqa U/A** (full U/A/E/S spread; A-class isolated). Closes the
  v0.7 gap (MMV-side rows were 0 under the minimal build). Originals zero drift.
- `scripts/dualwrite_both_verify.py`. Network-free tests unchanged (33).

## v0.7 (2026-06-18) — store unification, Phase 2: dual-write (vendored)
- **Dual-write hook** on the VENDORED copies: a self-contained, env-gated
  (`ERO_UNIFIED_DB`, default OFF) sink (`_ero_sink.py`) added to both systems,
  hooked into RQA `add_node` and MMV capsule + turn inserts. Each memory write
  is mirrored, provenance-normalized (U/A/E/S), into one `UnifiedStore`-
  compatible SQLite. All failures swallowed -> host behavior never changes.
- **Live verify** (vendored, gemma4:12b): with the sink on, the vendored systems
  dual-wrote **10 items into one unified store** (RQA U4/A6); ERO's UnifiedStore
  read them back; A-class isolated. **Originals byte-identical to the sha256
  baseline (zero drift)** — only the vendored copies were edited.
  - Caveat: MMV-side rows were 0 this run (the minimal sandbox build has no
    active memory indexer / embedder, so MMV's memory writes did not fire); the
    MMV hook is verified by unit tests, and would populate under a full MMV
    memory config.
- Tests: +4 (33 total network-free), incl. schema-compat of the vendored sink
  with ERO's UnifiedStore. Safety: `vendor/ORIGINALS_BASELINE.sha256` (156 files)
  re-checked clean after the edits.

## v0.6 (2026-06-18) — store unification, Phase 1 (on vendored copies)
- **Vendored snapshot** (`vendor/`): code-only copies of MMV (src/config/prompts)
  and RQA (rqa/config) so their internals can be modified WITHOUT touching the
  frozen originals. `scripts/smoke_vendor.py` ran the vendored stack on
  gemma4:12b, confirmed imports resolve to the copies, and the mutation guard
  showed all three originals byte-untouched.
- **UnifiedStore** (`unified_store.py`, SQLite, ERO-owned) + `migrate()`:
  consolidate both real stores into one provenance-tagged store (U/A/E/S);
  idempotent; `as_provider()` round-trips into `UnifiedMemoryView`. This is
  Phase 1 (read-side consolidation); Phase 2 (cutover: dual-write inside the
  vendored systems) is designed in `SPEC_v0_6_unification.md`.
- Tests: +5 (29 total network-free).

## v0.5 (2026-06-17) — unified view over real stores
- **Read-only store providers** (`store_readers.py`): SQLite opened `?mode=ro`
  for RQA graph (`nodes`: text, provenance) and MMV capsules (`capsules`:
  memory_text, memory_type). Missing / locked / schema-drift -> empty
  (non-fatal). Wires *real* data into `UnifiedMemoryView`.
- **Isolated demo (gemma4:12b)**: 3 turns populated the sandbox stores; the
  unified view then read **19 items across both** (U6 / A6 / E1 / S6); the
  A-class correctly isolated RQA's assistant-generated analyses (echo-prone),
  with one MMV `stable_fact` as E. Mutation guard: both repos untouched.
- Tests: +6 (24 total network-free), incl. a read-only-ness assertion.

## v0.4 (2026-06-17) — isolation
- **Isolation sandbox** (`sandbox.py`): run ERO against the REAL MMV/RQA without
  mutating either sibling repo. MMV writes are cwd-relative → contained by
  `Sandbox` (chdir jail); RQA writes are repo-relative (`Config.state_dir =
  mobius_rqa/state`, the real leak) → redirected via `isolated_rqa_controller`
  into `<sandbox>/rqa_state`. Source is imported read-only.
- **Mutation guard proven** (`scripts/smoke_isolated.py` + git checks): after a
  live isolated run (gemma4:12b), both repos' `git status` were UNCHANGED and
  RQA's real `state/graph.db` was byte-for-byte UNTOUCHED; all state landed in
  `sandbox/`. The sandbox is disposable — delete it to reset (redo safety net).
- Placement: `mobius_infinity/` stays a SIBLING of MOBIUS_MMV / mobius_rqa under
  `mobius_ai/` (per owner). Tests unchanged (18 network-free, green).

## v0.3 (2026-06-17)
- **Read-only unified provenance view** (`provenance.py`): normalizes RQA
  `provenance` ("user"/"self", verified) and MMV `memory_type` (interpretive)
  onto one ontology **U/A/E/S**. `UnifiedMemoryView` merges injected read-only
  providers WITHOUT migrating or writing to either store; a downed source is
  skipped (not fatal); `assistant_generated()` isolates the echo-prone A-class
  at the composite level.
- **Scope honesty:** this is a read-only lens, **not** full store unification —
  merging/migrating the MMV (MemoryCapsule + Box) and RQA (SQLite graph) stores
  would touch FROZEN internals and is deliberately out of scope.
- Tests: +5 (18 total network-free).

## v0.2 (2026-06-17)
- **Clean adapter boundary** (`contracts.py`, `adapters.py`): the orchestrator
  now depends on `EntitlementSource -> EntitlementResult` and
  `ReflectionSource -> ReflectionResult`, not on raw MMV/RQA shapes.
  `RoutingEngineAdapter` / `ControllerAdapter` map the real objects (verified:
  RoutingResult, RunResult.chosen.question / final_round.shortlist).
- **Citation flagging** (`citation_verifier.py`): non-destructive check of MMV
  answer prose against `RoutingResult.sources`; flags unbacked `[source: …]` /
  `[n]` markers; no-op on clean prose. Recorded on `EROResult.citation_flags`
  and in the audit row.
- Tests: 13/13 network-free. Live smoke (gemma4:12b) green; ask now surfaces the
  actual chosen question via the adapter.

## v0.1 (2026-06-17)
- Thin sequential router: MMV.evaluate -> 4-route switch -> (ask) framed
  RQA.run -> audit. Hard non-layering constraint (MMV Condition I). Two separate
  memory stores; no shared store. Wiring reuses each system's own factory.
- Tests: 7/7 network-free; live 3-route smoke green (ask / answer / abstain).
- Designed via SPEC_v0_1 (failed adversarial review: false API premises) ->
  SPEC_v0_2 (grounded; 2nd review fixes applied).

# MOBIUS INFINITY — ERO (Entitlement–Reflection Orchestrator)

The synthesis capstone of the Möbius program: a thin **sequential** router that
composes two existing systems —

- **MMV** (answer entitlement): *"is answering warranted?"*
- **RQA** (reflective questioning + memory-echo governance): *"not yet — what
  deeper question advances this?"*

MMV evaluates first on its **unmodified** stack and its route is authoritative;
on the `ask` branch ERO hands the turn to RQA. They are composed in sequence,
**never layered** — layering Essentials-like content onto MMV's structural
governance is documented to collapse restraint (MMV Condition I), so ERO must
not do it. Context flows one way: MMV → RQA.

Spec: [SPEC_v0_2.md](SPEC_v0_2.md) (current authority; supersedes v0.1).

## Quickstart — use it like a local LLM

Prereqs: [Ollama](https://ollama.com) running with the base model, and the two
sibling repos present (set `MMV_ROOT` / `RQA_ROOT`, or clone them next to this
one). Then:

```bash
ollama pull gemma4:12b
pip install -e ".[serve]"          # installs the `mobius-infinity` command + FastAPI

mobius-infinity preflight          # checks Ollama / model / repos before you start
mobius-infinity serve              # OpenAI-compatible API, profile=fast (~12s, no key)
#   -> http://127.0.0.1:8000/v1   point any OpenAI client (OpenWebUI, etc.) here
```

`serve` defaults to **`--profile fast`** — fully local, no cloud key, ~12s/turn.
The reflection tiers (latency-measured on a local gemma4:12b host; the local
evaluator is the dominant cost):

| `--profile` | budget | judge | latency | notes |
|-------------|--------|-------|--------:|-------|
| **fast** (default) | k3/d1 | none | ~12s | interactive, fully local |
| balanced | k4/d2 | none | ~27s | more candidates, local |
| quality | k6/d3 | local | ~157s | paper-style selection, slow |
| cloud | k6/d3 | Groq | fast | paper-faithful; needs `GROQ_API_KEY` |

`--local` / `--cloud` are aliases for `fast` / `cloud`. Multi-turn history is
honored by default (the message array is threaded into MMV's session);
`--no-multiturn` routes only on the latest turn.

Why `fast` is the default: a blind 3-judge depth comparison (n=12,
[eval/REPORT_profile_compare.md](eval/REPORT_profile_compare.md)) found `fast` is
**not majority-shallower** than the full pipeline — depth means 3.1–4.3, no
length confound — while running ~4× faster. The evaluator buys a small depth
edge; `cloud` gets it back at low latency for key-holders.

> **By design, this is not a vanilla answerer.** When a request is
> under-specified ("Fix this", "Which is better?") it asks a clarifying question
> or abstains, instead of guessing. That restraint + the depth of the question is
> the point — see [paper/](paper/).

## Status

v0.1 vertical slice: routing + framing + audit. The orchestrator imports neither
MMV nor RQA — it depends on two injected, duck-typed surfaces, so it is fully
testable without model backends.

```
ero/orchestrator.py   # Orchestrator + EROResult (pure routing logic)
ero/framing.py        # ask-route -> RQA input framing
ero/audit.py          # append-only audit (memory / JSONL)
ero/openai_api.py     # OpenAI-compatible HTTP surface (/v1/chat/completions)
ero/wiring.py         # HOST-ONLY: wires the real MMV + RQA backends (needs Ollama)
tests/                # network-free acceptance tests (54 across 8 suites)
```

## Test

```bash
python3 tests/test_orchestrator.py     # no pytest needed
# or: python3 -m pytest tests/
```

## Run against real backends (host with Ollama + sibling repos)

```python
from ero.wiring import build_orchestrator, new_mmv_session

ero = build_orchestrator(audit_path="state/ero_audit.jsonl")  # warm, once per process
state = new_mmv_session()                                     # one per conversation
res = ero.handle("compare these", session_state=state)
print(res.route, res.answered_by, res.text or res.result)
```

`build_orchestrator` reuses each system's own factory (`src/app/cli._build_engine`
for MMV, `Controller(Config())` for RQA). Override repo locations with the
`MMV_ROOT` / `RQA_ROOT` env vars. The wiring path needs a running Ollama and is
**not** covered by the network-free suite — verify on the host.

## Serve an OpenAI-compatible API (drop-in for the OpenAI ecosystem)

So any OpenAI client (OpenWebUI, LangChain, the `openai` SDK, …) can point its
`base_url` at ERO and transparently get answer-entitlement routing + reflective
questioning. Governance is surfaced without breaking compatibility: a
non-standard `ero` object on the JSON body and `x-ero-*` response headers.

```bash
pip install -r requirements-serve.txt          # fastapi + uvicorn
python3 -m ero.openai_api --host 127.0.0.1 --port 8000 --audit state/ero_audit.jsonl
```

```bash
curl http://127.0.0.1:8000/v1/chat/completions -H 'content-type: application/json' \
  -d '{"model":"mobius-infinity","messages":[{"role":"user","content":"Which is better?"}]}'
# -> assistant message IS the RQA clarifying question; body.ero.route == "ask"
```

Route → response: `ask` returns the RQA question, `answer`/`verify` the
synthesized answer, `abstain` a refusal (`finish_reason: content_filter`); a
downed backend returns HTTP 503 with an OpenAI-style error. The request/response
mapping is pure and **network-free tested** (`tests/test_openai_api.py`);
FastAPI/uvicorn are imported lazily, so the package needs no web deps unless you
serve.

**Streaming (`stream: true`)** is built for perceived responsiveness: the
assistant role chunk is sent immediately, SSE keepalive heartbeats flow every 2s
while the ask path reflects, then the text streams incrementally (typewriter).
This makes the ~12s ask wait *feel* active rather than frozen — it masks, not
reduces, the latency (the clarifying question is produced by a selection
pipeline, so it cannot token-stream earlier).

### Pluggable generation backend (consume any OpenAI-compatible model)

MMV's routing/entitlement decision is local heuristics (model-independent); only
answer *synthesis* uses a backend. `BackendConfig` selects it without modifying
MMV:

```python
from ero.wiring import build_orchestrator, BackendConfig

# default: local Ollama gemma4:12b. Or target any OpenAI /v1 server:
ero = build_orchestrator(backend=BackendConfig(
    kind="openai_compatible", model="my-model", base_url="http://localhost:8001"))
```

(Keyless local servers — vLLM / llama.cpp / LiteLLM / Ollama's `/v1` — work
today; an Authorization-header passthrough for authed providers is a small
planned upstream to MMV's `VllmAdapter`.)

## Not in v0.1 (descoped)

- Shared/unified memory store and a unified provenance ontology → **v0.3**
  (MMV and RQA keep their separate stores for now).
- A generalized text-citation verifier for MMV answers (RQA's
  `sanitize_memory_refs` is schema-coupled to RQA and runs inside RQA only).

## License

Code: **AGPL-3.0-or-later** ([LICENSE](LICENSE)). Documentation and the
[paper/](paper/): **CC BY-NC-SA 4.0**. Repository-wide licensing, the
commercial-license option, and rights administration: [LICENSE_NOTICE.md](LICENSE_NOTICE.md).
Composed dependencies (MMV, RQA) and attribution: [NOTICE](NOTICE). The
underlying methods are patent pending (7 filings); the AGPL §11 grant and its
scope: [PATENTS.md](PATENTS.md).

## Related — the Möbius program

Part of the [MOBIUS](https://github.com/mobius-style) program — local-first, AGPL:

- [mmv](https://github.com/mobius-style/mmv) — answer-entitlement runtime: decides *whether* answering is warranted
- [rqa](https://github.com/mobius-style/rqa) — reflective questioning adapter: deepens *the question* when it is not
- [rcgov](https://github.com/mobius-style/rcgov) — reflective context governor: governs *what a model may read*
- [infinity](https://github.com/mobius-style/infinity) — composite capstone (MMV × RQA) with an OpenAI-compatible API

"""Real-backend wiring for ERO (HOST-ONLY — needs Ollama + both repos).

This is the integration seam. It is intentionally thin and reuses each system's
OWN factory rather than reconstructing it:

  - MMV:  src/app/cli.py:_build_engine(...)  -> RoutingEngine   (Ollama qwen3.5:9b)
  - RQA:  Controller(Config())               -> .run(text)      (Ollama gemma4:12b)
  - SessionState: src/state/session_state.py

NOT exercised by the network-free test suite (those use fakes). It requires a
running Ollama and the two sibling repos present. Verify on the host before
trusting; surface failures honestly.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

# mobius_infinity/ero/wiring.py -> mobius_ai/
_MOBIUS_AI = Path(__file__).resolve().parents[2]
_MMV_ROOT = Path(os.environ.get("MMV_ROOT", _MOBIUS_AI / "MOBIUS_MMV"))
_RQA_ROOT = Path(os.environ.get("RQA_ROOT", _MOBIUS_AI / "mobius_rqa"))


def _ensure_path(p: Path) -> None:
    s = str(p)
    if p.is_dir() and s not in sys.path:
        sys.path.insert(0, s)


# Unified base model for the Möbius stack: Gemma 4 12B (Qwen shelved).
# MMV reads its generation model from OLLAMA_MODEL; RQA already generates on
# Gemma. Setting this env unifies both on one resident Ollama model.
UNIFIED_BASE_MODEL = "gemma4:12b"


@dataclass
class BackendConfig:
    """Generation backend for MMV answer/verify *text synthesis*.

    `kind="ollama"`            — Ollama native API (default; local-first). Uses
                                 OLLAMA_ENDPOINT/OLLAMA_MODEL via MMV's factory.
    `kind="openai_compatible"` — ANY OpenAI `/v1/chat/completions` server
                                 (vLLM, llama.cpp, LiteLLM, Ollama's /v1, ...),
                                 by attaching MMV's own VllmAdapter (which posts
                                 to `{base_url}/v1/chat/completions`) onto the
                                 engine — NO MMV modification.

    Generality knob only: MMV's routing/entitlement decision is LOCAL heuristics
    (model-independent); the backend changes only the synthesized answer text.

    `base_url` is the server root WITHOUT the `/v1` suffix (the adapter appends
    `/v1/chat/completions`), e.g. `http://localhost:8000` or
    `https://api.groq.com/openai`. NOTE: VllmAdapter does not yet forward an
    Authorization header, so authed providers (Groq/OpenAI) need the small
    api-key passthrough planned upstream; keyless local servers work today.
    """
    kind: str = "ollama"
    model: str = UNIFIED_BASE_MODEL
    base_url: str | None = None
    timeout: int = 60


def build_mmv_engine(*, use_adapter: bool = True, docs_dir: str | None = None,
                     web_search: bool = False, preset: str = "general",
                     model: str | None = UNIFIED_BASE_MODEL,
                     backend: BackendConfig | None = None):
    """Warm RoutingEngine via MMV's own _build_engine (build once per process).

    Default (`backend=None`): unchanged behavior — `model` sets OLLAMA_MODEL for
    MMV's answer/verify synthesis (unified Gemma-4-12B). Pass model=None to
    honor a pre-set OLLAMA_MODEL.

    Provide `backend` to choose the generation provider:
      * `BackendConfig(kind="ollama", model=..., base_url=...)` — sets
        OLLAMA_MODEL (+ OLLAMA_ENDPOINT if base_url given), then the normal path.
      * `BackendConfig(kind="openai_compatible", model=..., base_url=...)` —
        builds the engine with NO Ollama adapter and attaches a VllmAdapter
        pointed at any OpenAI-compatible endpoint. The route decision is
        unaffected (local heuristics); only answer synthesis uses the backend.
    """
    _ensure_path(_MMV_ROOT)

    if backend is None or backend.kind == "ollama":
        chosen = backend.model if backend else model
        if backend and backend.base_url:
            os.environ["OLLAMA_ENDPOINT"] = backend.base_url
        if chosen:
            os.environ["OLLAMA_MODEL"] = chosen
        from src.app.cli import _build_engine  # MMV factory
        return _build_engine(use_adapter=use_adapter, docs_dir=docs_dir,
                             web_search=web_search, preset=preset)

    if backend.kind == "openai_compatible":
        if not backend.base_url:
            raise ValueError("openai_compatible backend requires base_url")
        from src.app.cli import _build_engine
        from src.adapters.vllm_adapter import VllmAdapter
        # Build the engine WITHOUT the Ollama adapter, keep RAG/web/kiwix, then
        # swap in the OpenAI-compatible adapter via the public `.adapter` attr.
        engine = _build_engine(use_adapter=False, docs_dir=docs_dir,
                               web_search=web_search, preset=preset)
        engine.adapter = VllmAdapter(endpoint=backend.base_url.rstrip("/"),
                                     model_name=backend.model,
                                     timeout=backend.timeout)
        return engine

    raise ValueError(f"unknown backend kind: {backend.kind!r}")


def new_mmv_session():
    """Fresh MMV SessionState (thread one per conversation)."""
    _ensure_path(_MMV_ROOT)
    from src.state.session_state import SessionState
    return SessionState()


def _message_text(content) -> str:
    """OpenAI content -> plain text (string or array-of-parts form)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(p.get("text", "") for p in content
                       if isinstance(p, dict) and p.get("type") == "text")
    return ""


def new_mmv_session_from_messages(messages):
    """Build a SessionState seeded with prior conversation turns.

    The OpenAI request carries the whole history; MMV reads
    `SessionState.conversation_turns` (List[{"role","content"}]) for deictic /
    context resolution (routing_engine.py reads it during evaluate). We seed all
    turns EXCEPT the final user turn (that is the current input ERO routes on).
    Only user/assistant turns are kept. This is the public-field channel MMV
    already consumes — no MMV modification.
    """
    state = new_mmv_session()
    msgs = list(messages or [])
    # Drop the trailing user turn (the current input).
    if msgs and isinstance(msgs[-1], dict) and msgs[-1].get("role") == "user":
        msgs = msgs[:-1]
    turns = [{"role": m.get("role", ""), "content": _message_text(m.get("content", ""))}
             for m in msgs
             if isinstance(m, dict) and m.get("role") in ("user", "assistant")]
    state.conversation_turns = turns
    return state


def local_rqa_config(*, generator_model: str = UNIFIED_BASE_MODEL,
                     evaluator_model: str = UNIFIED_BASE_MODEL,
                     ollama_url: str = "http://localhost:11434",
                     evaluator_enabled: bool = True):
    """A fully-LOCAL RQA Config (no Groq key / no network).

    Two changes vs the shipped default:
      * generator = base `gemma4:12b` (not the private `rqa-gemma4:v0.1` adapter,
        which is not publicly distributed) — RQA runs on the base model.
      * evaluator (selection judge) repointed from Groq `gpt-oss-120b` to the
        LOCAL Ollama OpenAI-compatible endpoint (`{ollama_url}/v1`). A dummy key
        is set because Ollama ignores Authorization.

    Set `evaluator_enabled=False` to skip the LLM judge entirely (fastest, fully
    offline, weaker selection). Quality note: a local gemma judge is weaker than
    the pinned 120B; this trades selection quality for zero-key local operation.
    """
    _ensure_path(_RQA_ROOT)
    from rqa.config import Config, EvaluatorBinding

    os.environ.setdefault("OLLAMA_API_KEY", "ollama")  # Ollama ignores it
    binding = EvaluatorBinding(
        release="local-ollama",
        endpoint=f"{ollama_url.rstrip('/')}/v1",
        model=evaluator_model,
        api_key_env="OLLAMA_API_KEY",
    )
    return Config(adapter_model=generator_model, ollama_url=ollama_url,
                  evaluator_enabled=evaluator_enabled, evaluator_binding=binding)


# Reflection profiles — speed/quality tiers, latency-measured 2026-06-19 on a
# host with local gemma4:12b (single-prompt ablation; evaluator dominates cost):
#   fast      k3/d1, no judge       ~12s   fully local, interactive (DEFAULT)
#   balanced  k4/d2, no judge       ~27s   fully local, more candidates
#   quality   k6/d3, LOCAL judge    ~157s  fully local, paper-style selection
#   cloud     k6/d3, GROQ judge     fast   paper-faithful; needs GROQ_API_KEY
# (k/d map to RQA's own quick/standard/full budgets in rqa/__main__.py.)
_RQA_PROFILES = {
    "fast":     dict(k=3, d=1, regen=0, mem=2, evaluator=False, cloud_eval=False),
    "balanced": dict(k=4, d=2, regen=1, mem=4, evaluator=False, cloud_eval=False),
    "quality":  dict(k=6, d=3, regen=1, mem=8, evaluator=True,  cloud_eval=False),
    "cloud":    dict(k=6, d=3, regen=1, mem=8, evaluator=True,  cloud_eval=True),
}
RQA_PROFILE_NAMES = tuple(_RQA_PROFILES)


def rqa_profile(name: str = "fast", *, generator_model: str = UNIFIED_BASE_MODEL,
                ollama_url: str = "http://localhost:11434",
                evaluator_model: str = UNIFIED_BASE_MODEL):
    """Build an RQA Config for a named speed/quality profile (see table above).

    Generator is always the LOCAL base `gemma4:12b` (the private `rqa-gemma4:v0.1`
    SFT adapter is not publicly distributed). `cloud` keeps the shipped Groq
    evaluator binding (needs GROQ_API_KEY); the others judge locally or not at
    all → no cloud key. Zero MMV/RQA fork (public Config / EvaluatorBinding).
    """
    if name not in _RQA_PROFILES:
        raise ValueError(f"unknown profile {name!r}; choose from {RQA_PROFILE_NAMES}")
    _ensure_path(_RQA_ROOT)
    from rqa.config import Config, EvaluatorBinding

    b = _RQA_PROFILES[name]
    if b["cloud_eval"]:
        binding = EvaluatorBinding.load()      # shipped Groq-pinned (or yaml)
    else:
        os.environ.setdefault("OLLAMA_API_KEY", "ollama")  # Ollama ignores it
        binding = EvaluatorBinding(release="local-ollama",
                                   endpoint=f"{ollama_url.rstrip('/')}/v1",
                                   model=evaluator_model, api_key_env="OLLAMA_API_KEY")
    cfg = Config(adapter_model=generator_model, ollama_url=ollama_url,
                 evaluator_enabled=b["evaluator"], evaluator_binding=binding)
    cfg.k_candidates = b["k"]
    cfg.max_reflection_depth = b["d"]
    cfg.max_regen_per_round = b["regen"]
    cfg.max_memory_fragments = b["mem"]
    cfg.shortlist_s = min(cfg.shortlist_s, b["k"])
    return cfg


def build_rqa_controller(config=None):
    """Warm RQA Controller via its own Config (build once per process).

    Pass a `config` (e.g. `local_rqa_config()`) to override generator/evaluator;
    default reproduces the shipped RQA defaults (Groq-pinned evaluator).
    """
    _ensure_path(_RQA_ROOT)
    from rqa.config import Config
    from rqa.controller import Controller
    return Controller(config or Config())


def build_orchestrator(*, audit_path: str | None = None, profile: str = "fast",
                       rqa_config=None, generator_model: str = UNIFIED_BASE_MODEL,
                       ollama_url: str = "http://localhost:11434", **mmv_kwargs):
    """Construct a fully wired Orchestrator over warm MMV + RQA backends.

    The raw engines are wrapped in the clean adapters (SPEC v0.2) so the
    orchestrator depends only on the EntitlementSource / ReflectionSource
    contracts.

    `profile` (default `fast`) selects the RQA speed/quality tier — fast /
    balanced / quality are fully local (no cloud key); `cloud` uses the shipped
    Groq evaluator. Pass an explicit `rqa_config` to override the profile.
    MMV generation is set via `**mmv_kwargs` (`backend=BackendConfig(...)` /
    `model=`), defaulting to local Ollama gemma4:12b.
    """
    from .orchestrator import Orchestrator
    from .adapters import RoutingEngineAdapter, ControllerAdapter
    from .audit import JsonlAudit, MemoryAudit

    if rqa_config is None:
        rqa_config = rqa_profile(profile, generator_model=generator_model,
                                 ollama_url=ollama_url)

    mmv = RoutingEngineAdapter(build_mmv_engine(**mmv_kwargs))
    rqa = ControllerAdapter(build_rqa_controller(rqa_config))
    audit = JsonlAudit(audit_path) if audit_path else MemoryAudit()
    return Orchestrator(mmv, rqa, audit=audit)

"""ERO — Entitlement–Reflection Orchestrator (MOBIUS INFINITY).

Composes MOBIUS_MMV (answer entitlement) and mobius_rqa (reflective questioning)
sequentially, behind clean adapter contracts. See SPEC_v0_2.md / CHANGELOG.md.
Pure orchestration: no model backends imported by this package's core.
"""
from .orchestrator import EROResult, Orchestrator
from .contracts import (
    EntitlementResult, ReflectionResult, EntitlementSource, ReflectionSource,
)
from .adapters import RoutingEngineAdapter, ControllerAdapter
from .framing import build_augmented_input
from .citation_verifier import find_citations, unknown_citations
from .provenance import (
    UnifiedMemoryView, UnifiedItem, Provider,
    normalize_rqa, normalize_mmv, USER, ASSISTANT, EXTERNAL, SYSTEM,
)
from .store_readers import rqa_graph_provider, mmv_capsule_provider
from .unified_store import UnifiedStore, migrate
from .audit import MemoryAudit, JsonlAudit
from .openai_api import (
    create_app, serve, handle_chat, chat_completion_body, chat_chunk_bodies,
    stream_chunk_bodies, content_deltas, models_body, extract_user_input,
    DEFAULT_MODEL_ID,
)

__all__ = [
    "Orchestrator",
    "EROResult",
    "EntitlementResult",
    "ReflectionResult",
    "EntitlementSource",
    "ReflectionSource",
    "RoutingEngineAdapter",
    "ControllerAdapter",
    "build_augmented_input",
    "find_citations",
    "unknown_citations",
    "UnifiedMemoryView",
    "UnifiedItem",
    "Provider",
    "normalize_rqa",
    "normalize_mmv",
    "rqa_graph_provider",
    "mmv_capsule_provider",
    "UnifiedStore",
    "migrate",
    "MemoryAudit",
    "JsonlAudit",
    "create_app",
    "serve",
    "handle_chat",
    "chat_completion_body",
    "chat_chunk_bodies",
    "stream_chunk_bodies",
    "content_deltas",
    "models_body",
    "extract_user_input",
    "DEFAULT_MODEL_ID",
]

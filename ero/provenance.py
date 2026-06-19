"""Unified provenance view (SPEC v0.3 — READ-ONLY, NON-INVASIVE).

Full memory-store unification would be a data-layer redesign touching the
FROZEN MMV and RQA internals; that stays out of scope. What is safe and useful
is a read-only *lens*: normalize both systems' provenance vocabularies onto one
ERO ontology and merge their items behind a common view, without migrating or
writing to either store.

ERO ontology (the provenance classes the PPA-007 memory-echo governance reasons
about — assistant-generated content must be visibly non-independent):
  U = user assertion
  A = assistant-generated (non-independent evidence; the echo-prone class)
  E = external / verified evidence
  S = system / interaction metadata

Source mappings:
  RQA graph `provenance` ("user"/"self")  -> exact, verified (graph.py:33).
  MMV `memory_type` ({preference,goal,constraint,open_loop,stable_fact})
        -> INTERPRETIVE best-effort (not verified against MMV semantics; flagged).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

# ontology
USER = "U"
ASSISTANT = "A"
EXTERNAL = "E"
SYSTEM = "S"
ONTOLOGY = (USER, ASSISTANT, EXTERNAL, SYSTEM)

# RQA: exact (verified)
_RQA_MAP = {"user": USER, "self": ASSISTANT}

# MMV: interpretive best-effort (see module docstring caveat)
_MMV_MAP = {
    "preference": USER,
    "goal": USER,
    "constraint": USER,
    "open_loop": USER,
    "stable_fact": EXTERNAL,
}


def normalize_rqa(provenance: str) -> str:
    """RQA provenance -> ontology class (verified mapping)."""
    return _RQA_MAP.get(str(provenance).strip().lower(), SYSTEM)


def normalize_mmv(memory_type: str) -> str:
    """MMV memory_type -> ontology class (INTERPRETIVE; defaults to SYSTEM)."""
    return _MMV_MAP.get(str(memory_type).strip().lower(), SYSTEM)


@dataclass
class UnifiedItem:
    source: str        # "rqa" | "mmv" | ...
    provenance: str    # one of ONTOLOGY
    text: str
    raw: Any = None


@dataclass
class Provider:
    """A read-only memory source plugged into the view.

    - name:     label for the source ("rqa", "mmv", ...)
    - read:     zero-arg callable returning an iterable of raw items
    - text_of:  raw item -> display text
    - class_of: raw item -> ontology class (use normalize_rqa / normalize_mmv)
    """
    name: str
    read: Callable[[], Iterable[Any]]
    text_of: Callable[[Any], str]
    class_of: Callable[[Any], str]


class UnifiedMemoryView:
    """Read-only provenance-normalized merge over injected providers.

    Never writes to any store. `items()` is best-effort: a provider that raises
    on read is skipped (its loss must not break the composite view).
    """

    def __init__(self, providers: list[Provider] | None = None) -> None:
        self.providers: list[Provider] = list(providers or [])

    def add(self, provider: Provider) -> "UnifiedMemoryView":
        self.providers.append(provider)
        return self

    def items(self) -> list[UnifiedItem]:
        out: list[UnifiedItem] = []
        for p in self.providers:
            try:
                raws = list(p.read())
            except Exception:
                continue  # a downed source must not break the lens
            for r in raws:
                cls = p.class_of(r)
                out.append(UnifiedItem(
                    source=p.name,
                    provenance=cls if cls in ONTOLOGY else SYSTEM,
                    text=p.text_of(r),
                    raw=r,
                ))
        return out

    def by_class(self) -> dict[str, list[UnifiedItem]]:
        buckets: dict[str, list[UnifiedItem]] = {c: [] for c in ONTOLOGY}
        for it in self.items():
            buckets[it.provenance].append(it)
        return buckets

    def assistant_generated(self) -> list[UnifiedItem]:
        """The echo-prone A-class — what memory-echo governance must not let
        masquerade as independent evidence (composite-level visibility)."""
        return [it for it in self.items() if it.provenance == ASSISTANT]

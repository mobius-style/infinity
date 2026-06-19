"""Clean ERO-facing contracts (SPEC v0.2 — the adapter boundary).

The orchestrator depends on THESE normalized types, not on the raw shapes of
MMV's RoutingResult or RQA's RunResult. Concrete adapters (adapters.py) map the
real systems onto these. `raw` always carries the underlying object for the
presentation layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class EntitlementResult:
    """Normalized MMV decision."""
    route: str                                   # answer | ask | verify | abstain | <other>
    reason_code: str = ""
    answer_text: str = ""                        # present for answer/verify
    sources: list = field(default_factory=list)  # allowed citation referents
    raw: Any = None


@dataclass
class ReflectionResult:
    """Normalized RQA reflection."""
    questions: list = field(default_factory=list)  # candidate question texts
    primary: str = ""                              # the chosen question, if any
    raw: Any = None


@runtime_checkable
class EntitlementSource(Protocol):
    def evaluate(self, user_input: str, session_state: Any = None) -> EntitlementResult: ...


@runtime_checkable
class ReflectionSource(Protocol):
    def reflect(self, input_text: str) -> ReflectionResult: ...

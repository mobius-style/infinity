"""Concrete adapters mapping the real MMV / RQA objects onto ERO contracts.

These are the ONLY places that know the raw shapes (RoutingResult / RunResult),
verified against source:
  - MMV  RoutingResult{decision.route, decision.reason_code, response_text, sources}
         (routing_engine.py:427, route_decision.py:24)
  - RQA  RunResult.chosen -> Candidate.question; RunResult.final_round.shortlist
         (controller.py:31-47, schema.py:41)
"""
from __future__ import annotations

from typing import Any

from .contracts import EntitlementResult, ReflectionResult


class RoutingEngineAdapter:
    """Wrap a MMV RoutingEngine as an EntitlementSource."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def evaluate(self, user_input: str, session_state: Any = None) -> EntitlementResult:
        r = self.engine.evaluate(user_input, session_state)
        d = getattr(r, "decision", None)
        return EntitlementResult(
            route=(getattr(d, "route", "") or ""),
            reason_code=(getattr(d, "reason_code", "") or ""),
            answer_text=(getattr(r, "response_text", "") or ""),
            sources=list(getattr(r, "sources", []) or []),
            raw=r,
        )


def _questions_from_runresult(rr: Any) -> list[str]:
    fr = getattr(rr, "final_round", None)
    shortlist = getattr(fr, "shortlist", None) if fr is not None else None
    if shortlist:
        return [getattr(c, "question", str(c)) for c in shortlist]
    chosen = getattr(rr, "chosen", None)
    q = getattr(chosen, "question", "") if chosen is not None else ""
    return [q] if q else []


class ControllerAdapter:
    """Wrap a RQA Controller as a ReflectionSource."""

    def __init__(self, controller: Any) -> None:
        self.controller = controller

    def reflect(self, input_text: str) -> ReflectionResult:
        rr = self.controller.run(input_text)
        chosen = getattr(rr, "chosen", None)
        primary = (getattr(chosen, "question", "") if chosen is not None else "") or ""
        return ReflectionResult(
            questions=_questions_from_runresult(rr),
            primary=primary,
            raw=rr,
        )

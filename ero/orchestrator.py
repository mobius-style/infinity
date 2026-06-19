"""ERO — Entitlement–Reflection Orchestrator (SPEC v0.2).

A thin SEQUENTIAL router over two systems behind CLEAN contracts
(contracts.py): `EntitlementSource.evaluate -> EntitlementResult` (MMV) and
`ReflectionSource.reflect -> ReflectionResult` (RQA). Wrap the real engines with
adapters.py; tests inject fakes implementing the same contracts.

HARD CONSTRAINT (SPEC v0.2 §1, MMV Condition I): MMV and RQA are composed in
sequence, never layered. MMV evaluates on its unmodified stack and its route is
authoritative; RQA runs only on the `ask` branch, downstream; context flows
one-way (MMV -> RQA); the SessionState handed to MMV is never written with RQA
output.

v0.2 additions: clean adapter boundary (contracts/adapters); non-destructive
citation flagging on MMV answers (citation_verifier).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .framing import build_augmented_input
from .citation_verifier import unknown_citations

# answered_by tags
BY_ANSWER = "mmv:answer"
BY_VERIFY = "mmv:verify"
BY_ABSTAIN = "mmv:abstain"
BY_DEEPEN = "rqa:deepen"
BY_UNAVAILABLE = "system:unavailable"
BY_UNHANDLED = "ero:unhandled_route"

DEFAULT_REFUSAL = "I can't take this turn as posed."
DEFAULT_UNAVAILABLE = "The system is temporarily unavailable. Please retry."


@dataclass
class EROResult:
    route: str
    reason_code: str
    answered_by: str
    text: str
    result: Any = None                       # underlying EntitlementResult / ReflectionResult
    available: bool = True
    citation_flags: list = field(default_factory=list)  # unbacked citations in an MMV answer


class Orchestrator:
    def __init__(
        self,
        mmv_source: Any,           # EntitlementSource
        rqa_source: Any,           # ReflectionSource
        *,
        audit: Any = None,
        now: Optional[Callable[[], float]] = None,
        refusal_text: str = DEFAULT_REFUSAL,
        unavailable_text: str = DEFAULT_UNAVAILABLE,
        verify_citations: bool = True,
    ) -> None:
        self.mmv = mmv_source
        self.rqa = rqa_source
        self.audit = audit
        self._now = now or time.time
        self.refusal_text = refusal_text
        self.unavailable_text = unavailable_text
        self.verify_citations = verify_citations

    def handle(self, user_input: str, session_state: Any = None) -> EROResult:
        # --- MMV entitlement decision (clean, authoritative) -----------------
        # session_state is passed through UNMODIFIED; ERO never writes RQA
        # output into it (SPEC v0.2 §1 / acceptance §8.4).
        try:
            ent = self.mmv.evaluate(user_input, session_state)
        except Exception:
            return self._unavailable(route="", reason_code="", stage="mmv")

        route = ent.route or ""
        reason_code = ent.reason_code or ""

        if route in ("answer", "verify"):
            answered_by = BY_ANSWER if route == "answer" else BY_VERIFY
            flags = (unknown_citations(ent.answer_text, ent.sources)
                     if self.verify_citations else [])
            res = EROResult(route, reason_code, answered_by, ent.answer_text,
                            ent, citation_flags=flags)

        elif route == "abstain":
            # Safety / inadmissible — refuse. RQA is NEVER invoked here.
            res = EROResult(route, reason_code, BY_ABSTAIN, self.refusal_text, ent)

        elif route == "ask":
            augmented = build_augmented_input(user_input, reason_code)
            try:
                refl = self.rqa.reflect(augmented)
            except Exception:
                return self._unavailable(route=route, reason_code=reason_code,
                                         stage="rqa")
            res = EROResult(route, reason_code, BY_DEEPEN, refl.primary, refl)

        else:
            # Unknown route: do NOT guess an answer. Surface plainly.
            res = EROResult(route, reason_code, BY_UNHANDLED, self.refusal_text, ent)

        self._record(res)
        return res

    # ------------------------------------------------------------------ utils
    def _unavailable(self, *, route: str, reason_code: str, stage: str) -> EROResult:
        res = EROResult(route, reason_code, BY_UNAVAILABLE,
                        self.unavailable_text, None, available=False)
        self._record(res, extra={"failed_stage": stage})
        return res

    def _record(self, res: EROResult, extra: Optional[dict] = None) -> None:
        if self.audit is None:
            return
        row = {
            "ts": self._now(),
            "route": res.route,
            "reason_code": res.reason_code,
            "answered_by": res.answered_by,
            "available": res.available,
            "citation_flags": len(res.citation_flags),
        }
        if extra:
            row.update(extra)
        self.audit.record(row)

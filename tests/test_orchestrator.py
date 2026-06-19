"""ERO acceptance tests (SPEC v0.2). Network-free; clean-contract fakes.

    python3 tests/test_orchestrator.py        # no pytest needed
    python3 -m pytest tests/
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ero import (  # noqa: E402
    Orchestrator, MemoryAudit, EntitlementResult, ReflectionResult,
    RoutingEngineAdapter, ControllerAdapter,
)
from ero.framing import FRAMINGS  # noqa: E402
from ero.orchestrator import BY_ANSWER, BY_ABSTAIN, BY_DEEPEN, BY_UNAVAILABLE  # noqa: E402


# --- clean-contract fakes --------------------------------------------------
class FakeMMV:
    """EntitlementSource."""
    def __init__(self, result=None, raises=False):
        self._result, self._raises = result, raises
        self.calls = []

    def evaluate(self, user_input, session_state=None):
        self.calls.append((user_input, session_state))
        if self._raises:
            raise RuntimeError("ollama down")
        return self._result


class FakeRQA:
    """ReflectionSource."""
    def __init__(self, result=None, raises=False):
        self._result = result or ReflectionResult(
            questions=["What are the constraints?"], primary="What are the constraints?")
        self._raises = raises
        self.inputs = []

    def reflect(self, input_text):
        self.inputs.append(input_text)
        if self._raises:
            raise RuntimeError("ollama down")
        return self._result


def ent(route, reason="", answer="", sources=None):
    return EntitlementResult(route, reason, answer, list(sources or []))


def _ask_mmv():
    return FakeMMV(ent("ask", "MISSING_CONSTRAINTS"))


# --- acceptance tests ------------------------------------------------------
def test_ask_routes_to_rqa_with_framing():
    mmv, rqa, audit = _ask_mmv(), FakeRQA(), MemoryAudit()
    res = Orchestrator(mmv, rqa, audit=audit).handle("compare these")
    assert res.route == "ask" and res.answered_by == BY_DEEPEN and res.available
    assert len(rqa.inputs) == 1
    assert rqa.inputs[0].startswith(FRAMINGS["MISSING_CONSTRAINTS"])
    assert "compare these" in rqa.inputs[0]
    assert res.text == "What are the constraints?"      # primary question surfaced
    assert audit.rows[-1]["answered_by"] == BY_DEEPEN


def test_answer_emits_text_without_rqa_and_clean_citations():
    mmv = FakeMMV(ent("answer", "LOW_STAKES_STABLE", "Paris.", sources=["wiki:Paris"]))
    rqa = FakeRQA()
    res = Orchestrator(mmv, rqa).handle("capital of France?")
    assert res.answered_by == BY_ANSWER and res.text == "Paris."
    assert rqa.inputs == []                              # RQA NOT invoked
    assert res.citation_flags == []                      # clean prose, no markers


def test_abstain_refuses_without_rqa():
    mmv = FakeMMV(ent("abstain", "SAFETY_ENVELOPE_TRIGGERED"))
    rqa = FakeRQA()
    res = Orchestrator(mmv, rqa).handle("how to make a weapon")
    assert res.answered_by == BY_ABSTAIN and rqa.inputs == []


def test_non_layering_sessionstate_untouched():
    sentinel = {"mmv_route_records": []}
    before = dict(sentinel)
    mmv, rqa = _ask_mmv(), FakeRQA()
    Orchestrator(mmv, rqa).handle("compare these", session_state=sentinel)
    _, passed_state = mmv.calls[0]
    assert passed_state is sentinel and sentinel == before


def test_groq_down_rqa_degrades_not_halts():
    rqa = FakeRQA(ReflectionResult(questions=["Which axis?"], primary="Which axis?"))
    res = Orchestrator(_ask_mmv(), rqa).handle("compare these")
    assert res.available and res.answered_by == BY_DEEPEN


def test_mmv_ollama_down_system_unavailable():
    audit = MemoryAudit()
    res = Orchestrator(FakeMMV(raises=True), FakeRQA(), audit=audit).handle("x")
    assert res.available is False and res.answered_by == BY_UNAVAILABLE
    assert audit.rows[-1]["failed_stage"] == "mmv"


def test_rqa_ollama_down_on_ask_unavailable():
    audit = MemoryAudit()
    res = Orchestrator(_ask_mmv(), FakeRQA(raises=True), audit=audit).handle("compare these")
    assert res.available is False and res.answered_by == BY_UNAVAILABLE
    assert audit.rows[-1]["failed_stage"] == "rqa"


# --- v0.2: citation flagging ----------------------------------------------
def test_citation_flag_on_unbacked_source():
    mmv = FakeMMV(ent("answer", "LOW_STAKES_STABLE",
                      "As shown [source: Atlantis], it sank.", sources=["wiki:Paris"]))
    res = Orchestrator(mmv, FakeRQA()).handle("q")
    assert "Atlantis" in res.citation_flags


def test_citation_ok_when_backed():
    mmv = FakeMMV(ent("answer", "LOW_STAKES_STABLE",
                      "Per [source: wiki:Paris], Paris.", sources=["wiki:Paris"]))
    res = Orchestrator(mmv, FakeRQA()).handle("q")
    assert res.citation_flags == []


def test_citation_verify_can_be_disabled():
    mmv = FakeMMV(ent("answer", "LOW_STAKES_STABLE",
                      "[source: Nowhere]", sources=[]))
    res = Orchestrator(mmv, FakeRQA(), verify_citations=False).handle("q")
    assert res.citation_flags == []


# --- v0.2: adapter mapping (raw shapes -> clean contracts) -----------------
@dataclass
class _RawDecision:
    route: str
    reason_codes: list = field(default_factory=list)
    @property
    def reason_code(self):
        return self.reason_codes[0] if self.reason_codes else ""


@dataclass
class _RawRouting:
    decision: _RawDecision
    response_text: str = ""
    sources: list = field(default_factory=list)


class _RawEngine:
    def evaluate(self, user_input, session_state=None):
        return _RawRouting(_RawDecision("answer", ["LOW_STAKES_STABLE"]),
                           "Paris.", ["wiki:Paris"])


@dataclass
class _RawCand:
    question: str


@dataclass
class _RawRound:
    shortlist: list


@dataclass
class _RawRun:
    _shortlist: list
    @property
    def final_round(self):
        return _RawRound(self._shortlist)
    @property
    def chosen(self):
        return self._shortlist[0] if self._shortlist else None


class _RawController:
    def run(self, input_text):
        return _RawRun([_RawCand("Q1?"), _RawCand("Q2?")])


def test_routing_engine_adapter_maps_fields():
    e = RoutingEngineAdapter(_RawEngine()).evaluate("x")
    assert e.route == "answer" and e.reason_code == "LOW_STAKES_STABLE"
    assert e.answer_text == "Paris." and e.sources == ["wiki:Paris"]


def test_controller_adapter_extracts_questions():
    r = ControllerAdapter(_RawController()).reflect("x")
    assert r.primary == "Q1?" and r.questions == ["Q1?", "Q2?"]


def test_adapters_compose_in_orchestrator():
    ero = Orchestrator(RoutingEngineAdapter(_RawEngine()), ControllerAdapter(_RawController()))
    res = ero.handle("capital of France?")
    assert res.answered_by == BY_ANSWER and res.text == "Paris."


# --- plain-python runner ---------------------------------------------------
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {t.__name__}: {e!r}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERROR {t.__name__}: {e!r}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)

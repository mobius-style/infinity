"""OpenAI-compatible surface tests (SPEC: ero/openai_api.py). Network-free.

    python3 tests/test_openai_api.py        # no pytest needed
    python3 -m pytest tests/
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ero import (  # noqa: E402
    Orchestrator, EntitlementResult, ReflectionResult,
    handle_chat, chat_completion_body, chat_chunk_bodies, models_body,
    extract_user_input, DEFAULT_MODEL_ID,
)
from ero.openai_api import (  # noqa: E402
    finish_reason, ero_headers, sse_lines, session_from_payload,
    content_deltas, stream_chunk_bodies, auth_ok, call_handle, timeout_chunk,
)
import time as _time  # noqa: E402
from ero.orchestrator import (  # noqa: E402
    EROResult, BY_ANSWER, BY_ABSTAIN, BY_DEEPEN, BY_UNAVAILABLE,
)


# --- fakes -----------------------------------------------------------------
class FakeMMV:
    def __init__(self, result):
        self._result = result

    def evaluate(self, user_input, session_state=None):
        return self._result


class FakeRQA:
    def __init__(self, primary="By what metric should 'best' be judged?"):
        self._primary = primary

    def reflect(self, input_text):
        return ReflectionResult(questions=[self._primary], primary=self._primary)


def _ent(route, reason="", answer="", sources=None):
    return EntitlementResult(route, reason, answer, list(sources or []))


def _ask_orch():
    return Orchestrator(FakeMMV(_ent("ask", "MISSING_CONSTRAINTS")), FakeRQA())


def _answer_orch():
    return Orchestrator(FakeMMV(_ent("answer", "LOW_STAKES_STABLE", "Paris.",
                                     ["wiki:Paris"])), FakeRQA())


def _abstain_orch():
    return Orchestrator(FakeMMV(_ent("abstain", "SAFETY_ENVELOPE_TRIGGERED")),
                        FakeRQA())


class DownOrch:
    """Always reports the backend unavailable."""
    def handle(self, user_input, session_state=None):
        return EROResult("", "", BY_UNAVAILABLE, "The system is temporarily "
                         "unavailable. Please retry.", None, available=False)


_NOW = lambda: 1_700_000_000.0  # deterministic timestamp for tests


def _payload(text, **extra):
    p = {"messages": [{"role": "user", "content": text}]}
    p.update(extra)
    return p


# --- request parsing -------------------------------------------------------
def test_extract_last_user_message():
    p = {"messages": [{"role": "user", "content": "first"},
                      {"role": "assistant", "content": "ok"},
                      {"role": "user", "content": "Which is better?"}]}
    assert extract_user_input(p) == "Which is better?"


def test_extract_content_parts_form():
    p = {"messages": [{"role": "user",
                       "content": [{"type": "text", "text": "Fix "},
                                   {"type": "text", "text": "this."}]}]}
    assert extract_user_input(p) == "Fix this."


def test_extract_rejects_empty():
    for bad in ({}, {"messages": []}, {"messages": [{"role": "system", "content": "x"}]}):
        try:
            extract_user_input(bad)
            assert False, f"should have raised for {bad!r}"
        except ValueError:
            pass


# --- ask: assistant message IS the RQA question ----------------------------
def test_ask_returns_rqa_question_as_assistant():
    status, body, headers = handle_chat(_ask_orch(), _payload("Which is better?"),
                                        now=_NOW)
    assert status == 200
    choice = body["choices"][0]
    assert choice["message"]["role"] == "assistant"
    assert choice["message"]["content"] == "By what metric should 'best' be judged?"
    assert choice["finish_reason"] == "stop"
    assert body["object"] == "chat.completion"
    assert body["ero"]["route"] == "ask"
    assert body["ero"]["answered_by"] == BY_DEEPEN
    assert headers["x-ero-route"] == "ask"


# --- answer ----------------------------------------------------------------
def test_answer_returns_answer_text():
    status, body, _ = handle_chat(_answer_orch(), _payload("capital of France?"),
                                  now=_NOW)
    assert status == 200
    assert body["choices"][0]["message"]["content"] == "Paris."
    assert body["ero"]["answered_by"] == BY_ANSWER
    assert body["ero"]["citation_flags"] == []


# --- abstain maps to content_filter ----------------------------------------
def test_abstain_maps_to_content_filter():
    status, body, _ = handle_chat(_abstain_orch(), _payload("make a weapon"),
                                  now=_NOW)
    assert status == 200
    assert body["choices"][0]["finish_reason"] == "content_filter"
    assert body["ero"]["answered_by"] == BY_ABSTAIN


# --- backend down -> 503 with OpenAI-style error ---------------------------
def test_unavailable_returns_503_error():
    status, body, headers = handle_chat(DownOrch(), _payload("x"), now=_NOW)
    assert status == 503
    assert "error" in body and body["error"]["code"] == "backend_unavailable"
    assert headers["x-ero-available"] == "false"


# --- malformed request -> 400 ----------------------------------------------
def test_bad_request_returns_400():
    status, body, _ = handle_chat(_ask_orch(), {"messages": []}, now=_NOW)
    assert status == 400 and "error" in body


# --- model echo + id/created shape -----------------------------------------
def test_model_echoed_and_ids_present():
    status, body, _ = handle_chat(_answer_orch(),
                                  _payload("q", model="gpt-4o-mini"), now=_NOW)
    assert body["model"] == "gpt-4o-mini"          # echoes requested model
    assert body["id"].startswith("chatcmpl-")
    assert body["created"] == 1_700_000_000


def test_default_model_when_unspecified():
    _, body, _ = handle_chat(_answer_orch(), _payload("q"), now=_NOW)
    assert body["model"] == DEFAULT_MODEL_ID


# --- streaming reconstructs to the same content ----------------------------
def test_stream_chunks_reconstruct_content():
    res = _ask_orch().handle("Which is better?")
    chunks = chat_chunk_bodies(res, model="m", completion_id="chatcmpl-x",
                               created=1)
    assert chunks[0]["choices"][0]["delta"] == {"role": "assistant"}
    content = "".join(c["choices"][0]["delta"].get("content", "") for c in chunks)
    assert content == res.text
    assert chunks[-1]["choices"][0]["finish_reason"] == "stop"
    assert chunks[-1]["ero"]["route"] == "ask"
    assert all(c["object"] == "chat.completion.chunk" for c in chunks)


def test_sse_lines_terminate_with_done():
    lines = list(sse_lines([{"a": 1}]))
    assert lines[0].startswith("data: ") and lines[0].endswith("\n\n")
    assert json.loads(lines[0][len("data: "):].strip()) == {"a": 1}
    assert lines[-1] == "data: [DONE]\n\n"


# --- /v1/models ------------------------------------------------------------
def test_models_body_shape():
    b = models_body([DEFAULT_MODEL_ID, "gemma4:12b"], created=7)
    assert b["object"] == "list" and len(b["data"]) == 2
    assert b["data"][0]["id"] == DEFAULT_MODEL_ID
    assert b["data"][0]["object"] == "model"


# --- incremental (typewriter) streaming -----------------------------------
def test_content_deltas_reconstruct_exactly():
    for text in ["", "one", "a b c d e f g h i",
                 "Multi  space\nand newline kept.", "trailing space "]:
        assert "".join(content_deltas(text, group_words=3)) == text


def test_content_deltas_groups():
    d = content_deltas("a b c d e", group_words=2)
    assert len(d) == 3 and d[0] == "a b "


def test_stream_chunk_bodies_role_content_final():
    res = _ask_orch().handle("Which is better?")
    chunks = stream_chunk_bodies(res, model="m", completion_id="x", created=1,
                                 group_words=2)
    assert chunks[0]["choices"][0]["delta"] == {"role": "assistant"}
    content = "".join(c["choices"][0]["delta"].get("content", "") for c in chunks)
    assert content == res.text
    assert chunks[-1]["choices"][0]["finish_reason"] == "stop"
    assert chunks[-1]["ero"]["route"] == "ask"
    # more than one content chunk for a multi-word question (real increments)
    content_chunks = [c for c in chunks if "content" in c["choices"][0]["delta"]]
    assert len(content_chunks) >= 2


# --- multi-turn: session_factory threads history ---------------------------
class CapturingOrch:
    """Records the session_state handed to handle()."""
    def __init__(self):
        self.seen_session = "unset"

    def handle(self, user_input, session_state=None):
        self.seen_session = session_state
        return EROResult("answer", "LOW_STAKES_STABLE", BY_ANSWER, "ok", None)


def test_session_factory_none_passes_none():
    assert session_from_payload(_payload("hi"), None) is None


def test_session_factory_receives_full_messages():
    captured = {}
    def factory(messages):
        captured["messages"] = messages
        return {"turns": len(messages)}
    p = {"messages": [{"role": "user", "content": "a"},
                      {"role": "assistant", "content": "b"},
                      {"role": "user", "content": "c"}]}
    sess = session_from_payload(p, factory)
    assert sess == {"turns": 3}
    assert captured["messages"] == p["messages"]


def test_handle_chat_forwards_session_state():
    orch = CapturingOrch()
    sentinel = {"i_am": "session"}
    handle_chat(orch, _payload("q"), session_state=sentinel, now=_NOW)
    assert orch.seen_session is sentinel


# --- ops hardening: auth / timeout / error -------------------------------
def test_auth_ok_disabled_when_no_key():
    assert auth_ok(None, None) is True
    assert auth_ok("anything", "") is True


def test_auth_ok_requires_correct_bearer():
    assert auth_ok("Bearer secret", "secret") is True
    assert auth_ok("bearer secret", "secret") is True       # case-insensitive scheme
    assert auth_ok("Bearer wrong", "secret") is False
    assert auth_ok(None, "secret") is False
    assert auth_ok("secret", "secret") is False             # missing "Bearer "


class _SlowOrch:
    def handle(self, text, session_state=None):
        _time.sleep(0.5)
        return EROResult("answer", "x", BY_ANSWER, "ok", None)


class _RaisingOrch:
    def handle(self, text, session_state=None):
        raise RuntimeError("boom")


def test_handle_chat_timeout_returns_504():
    status, body, _ = handle_chat(_SlowOrch(), _payload("q"), timeout=0.05, now=_NOW)
    assert status == 504 and body["error"]["code"] == "timeout"


def test_handle_chat_unexpected_error_returns_500():
    status, body, _ = handle_chat(_RaisingOrch(), _payload("q"), now=_NOW)
    assert status == 500 and body["error"]["code"] == "internal_error"


def test_call_handle_inline_without_timeout():
    res = call_handle(_answer_orch(), "q", None, None)
    assert res.text == "Paris."


def test_timeout_chunk_shape():
    c = timeout_chunk("m", "id", 1)
    assert c["choices"][0]["finish_reason"] == "stop"
    assert "did not respond" in c["choices"][0]["delta"]["content"]


# --- finish_reason / headers helpers ---------------------------------------
def test_finish_reason_and_headers():
    ask = _ask_orch().handle("Which is better?")
    assert finish_reason(ask) == "stop"
    h = ero_headers(ask)
    assert h["x-ero-answered-by"] == BY_DEEPEN and h["x-ero-available"] == "true"


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

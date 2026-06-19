"""OpenAI-compatible HTTP surface for ERO (the "expose" side).

ERO is a governance layer; to be a drop-in for the OpenAI ecosystem (OpenWebUI,
LangChain, the `openai` SDK, ...) it must speak `/v1/chat/completions`. This
module maps that wire format onto a duck-typed `Orchestrator.handle(text,
session_state) -> EROResult` and back, so any OpenAI client points its base_url
here and transparently gets answer-entitlement routing + reflective questioning.

DESIGN (matches the rest of ERO):
  * The orchestrator is INJECTED — this module imports neither MMV nor RQA, and
    the request/response mapping is pure, framework-free, and network-free
    testable. FastAPI / uvicorn are imported lazily inside `create_app` / `serve`
    only, so importing this module never requires them.
  * ERO governance metadata is surfaced WITHOUT breaking OpenAI compatibility:
    a non-standard `ero` object on the JSON body (clients ignore unknown keys)
    and `x-ero-*` response headers.

ERO behavior maps to ordinary assistant turns:
  ask     -> assistant message IS the RQA clarifying question  (finish_reason stop)
  answer  -> the synthesized answer                            (finish_reason stop)
  verify  -> the verified answer                               (finish_reason stop)
  abstain -> a refusal message                       (finish_reason content_filter)
  backend down -> HTTP 503 with an OpenAI-style error body

NOTE: this module intentionally does NOT use `from __future__ import
annotations`. FastAPI resolves route-parameter annotations eagerly; with
stringized annotations it cannot see the `Request` class imported locally inside
`create_app`, and would mis-treat it as a query parameter (HTTP 422).
"""
import asyncio
import json
import re
import time
from typing import Any, Callable, Iterable, Optional

from .orchestrator import BY_ABSTAIN

OBJECT_CHAT = "chat.completion"
OBJECT_CHUNK = "chat.completion.chunk"
OBJECT_MODEL = "model"
DEFAULT_MODEL_ID = "mobius-infinity"
HEARTBEAT_SECONDS = 2.0   # SSE keepalive cadence while the ask path reflects


# --------------------------------------------------------------------------- #
# Pure request parsing
# --------------------------------------------------------------------------- #
def extract_user_input(payload: dict) -> str:
    """Return the latest user turn from an OpenAI chat payload.

    Raises ValueError (-> HTTP 400) when the payload has no usable user message.
    History conveyed in earlier messages is intentionally NOT folded into the
    routing input in v1: ERO routes on the latest user turn, mirroring the eval.
    """
    if not isinstance(payload, dict):
        raise ValueError("request body must be a JSON object")
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError("'messages' must be a non-empty array")
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content", "")
            text = _content_to_text(content)
            if text.strip():
                return text
            raise ValueError("latest user message has empty content")
    raise ValueError("no user message found in 'messages'")


def _content_to_text(content: Any) -> str:
    """Accept both string content and the array-of-parts content form."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):  # [{"type":"text","text":"..."}, ...]
        parts = [p.get("text", "") for p in content
                 if isinstance(p, dict) and p.get("type") == "text"]
        return "".join(parts)
    return ""


# --------------------------------------------------------------------------- #
# Pure response building (EROResult -> OpenAI shapes)
# --------------------------------------------------------------------------- #
def finish_reason(result: Any) -> str:
    return "content_filter" if result.answered_by == BY_ABSTAIN else "stop"


def ero_meta(result: Any) -> dict:
    """Non-standard governance block; OpenAI clients ignore unknown keys."""
    return {
        "route": result.route,
        "reason_code": result.reason_code,
        "answered_by": result.answered_by,
        "available": result.available,
        "citation_flags": list(result.citation_flags),
    }


def ero_headers(result: Any) -> dict:
    return {
        "x-ero-route": result.route or "",
        "x-ero-reason-code": result.reason_code or "",
        "x-ero-answered-by": result.answered_by or "",
        "x-ero-available": "true" if result.available else "false",
        "x-ero-citation-flags": str(len(result.citation_flags)),
    }


def chat_completion_body(result: Any, *, model: str, completion_id: str,
                         created: int) -> dict:
    return {
        "id": completion_id,
        "object": OBJECT_CHAT,
        "created": created,
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": result.text},
            "finish_reason": finish_reason(result),
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "ero": ero_meta(result),
    }


def chat_chunk_bodies(result: Any, *, model: str, completion_id: str,
                      created: int) -> list[dict]:
    """SSE deltas: role -> content -> terminal finish. Reconstructs to the same
    content as the non-streaming body. (Backend generation is not token-streamed
    through the ERO contract, so this is whole-result pseudo-streaming.)"""
    def _chunk(delta: dict, fr: Optional[str]) -> dict:
        body = {
            "id": completion_id,
            "object": OBJECT_CHUNK,
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": delta, "finish_reason": fr}],
        }
        if fr is not None:
            body["ero"] = ero_meta(result)
        return body

    return [
        _chunk({"role": "assistant"}, None),
        _chunk({"content": result.text}, None),
        _chunk({}, finish_reason(result)),
    ]


def content_deltas(text: str, group_words: int = 4) -> list[str]:
    """Split text into incremental content pieces (typewriter effect). Pieces
    join back EXACTLY to `text` (whitespace preserved)."""
    tokens = re.findall(r"\S+\s*", text or "")  # word + its trailing whitespace
    return ["".join(tokens[i:i + group_words])
            for i in range(0, len(tokens), group_words)]


def stream_chunk_bodies(result: Any, *, model: str, completion_id: str,
                        created: int, group_words: int = 4) -> list[dict]:
    """role -> incremental content pieces -> terminal finish. Content pieces
    reconstruct EXACTLY to result.text (used by the heartbeat streaming route)."""
    def _chunk(delta: dict, fr: Optional[str]) -> dict:
        body = {"id": completion_id, "object": OBJECT_CHUNK, "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": delta, "finish_reason": fr}]}
        if fr is not None:
            body["ero"] = ero_meta(result)
        return body

    out = [_chunk({"role": "assistant"}, None)]
    for piece in content_deltas(result.text, group_words):
        out.append(_chunk({"content": piece}, None))
    out.append(_chunk({}, finish_reason(result)))
    return out


def models_body(model_ids: Iterable[str], *, created: int) -> dict:
    return {
        "object": "list",
        "data": [{"id": mid, "object": OBJECT_MODEL, "created": created,
                  "owned_by": "mobius"} for mid in model_ids],
    }


def error_body(message: str, *, type_: str = "invalid_request_error",
               code: Optional[str] = None) -> dict:
    return {"error": {"message": message, "type": type_, "param": None,
                      "code": code}}


# --------------------------------------------------------------------------- #
# Pure request handling (non-streaming) — network-free testable
# --------------------------------------------------------------------------- #
def handle_chat(
    orchestrator: Any,
    payload: dict,
    *,
    model: str = DEFAULT_MODEL_ID,
    session_state: Any = None,
    now: Optional[Callable[[], float]] = None,
    id_factory: Optional[Callable[[], str]] = None,
) -> tuple[int, dict, dict]:
    """Map one chat-completions request to (status_code, body, headers).

    The injected `orchestrator` only needs `.handle(text, session_state)
    -> EROResult`. Returns 400 on a malformed request, 503 when ERO reports the
    backend unavailable, else 200.
    """
    _now = now or time.time
    created = int(_now())
    completion_id = (id_factory or (lambda: f"chatcmpl-{created}"))()
    requested_model = (payload.get("model") if isinstance(payload, dict) else None) or model

    try:
        user_input = extract_user_input(payload)
    except ValueError as exc:
        return 400, error_body(str(exc)), {}

    result = orchestrator.handle(user_input, session_state)
    headers = ero_headers(result)

    if not getattr(result, "available", True):
        body = error_body(result.text, type_="service_unavailable_error",
                          code="backend_unavailable")
        return 503, body, headers

    body = chat_completion_body(result, model=requested_model,
                                completion_id=completion_id, created=created)
    return 200, body, headers


def sse_lines(chunks: Iterable[dict]) -> Iterable[str]:
    """Format chunk dicts as Server-Sent Events, terminated by [DONE]."""
    for chunk in chunks:
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


def session_from_payload(payload: dict, session_factory: Optional[Callable]) -> Any:
    """Build per-request session state from the message history (multi-turn).

    `session_factory(messages) -> session_state` is injected by the host (e.g.
    `ero.wiring.new_mmv_session_from_messages`); None keeps single-turn behavior.
    Kept here (not in core) so this module stays MMV-free.
    """
    if session_factory is None:
        return None
    messages = payload.get("messages", []) if isinstance(payload, dict) else []
    return session_factory(messages)


# --------------------------------------------------------------------------- #
# FastAPI app (transport only; lazy import so the package needs no web deps)
# --------------------------------------------------------------------------- #
def create_app(
    orchestrator: Any,
    *,
    model: str = DEFAULT_MODEL_ID,
    extra_model_ids: Optional[Iterable[str]] = None,
    session_factory: Optional[Callable] = None,
    now: Optional[Callable[[], float]] = None,
):
    """Build a FastAPI app exposing the OpenAI-compatible surface.

    `orchestrator` must provide `.handle(text, session_state) -> EROResult`
    (e.g. `ero.wiring.build_orchestrator()`). `session_factory(messages) ->
    session_state` enables multi-turn context (pass
    `ero.wiring.new_mmv_session_from_messages`); None = single-turn. Requires
    `fastapi`; install with `pip install -r requirements-serve.txt`.
    """
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse, StreamingResponse
    except ImportError as exc:  # pragma: no cover - import guard
        raise ImportError(
            "ero.openai_api.create_app needs FastAPI/uvicorn — "
            "`pip install fastapi uvicorn` (or -r requirements-serve.txt)."
        ) from exc

    _now = now or time.time
    model_ids = [model, *(extra_model_ids or [])]
    app = FastAPI(title="MOBIUS INFINITY / ERO", version="1")

    @app.get("/healthz")
    async def healthz():  # noqa: ANN201
        return {"status": "ok", "model": model}

    @app.get("/v1/models")
    async def list_models():  # noqa: ANN201
        return models_body(model_ids, created=int(_now()))

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):  # noqa: ANN201
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse(error_body("request body is not valid JSON"),
                                status_code=400)

        if isinstance(payload, dict) and payload.get("stream"):
            try:
                user_input = extract_user_input(payload)
            except ValueError as exc:
                return JSONResponse(error_body(str(exc)), status_code=400)
            created = int(_now())
            completion_id = f"chatcmpl-{created}"
            req_model = payload.get("model") or model
            session = session_from_payload(payload, session_factory)

            def _sse(chunk: dict) -> str:
                return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

            def _role_chunk() -> dict:
                return {"id": completion_id, "object": OBJECT_CHUNK,
                        "created": created, "model": req_model,
                        "choices": [{"index": 0, "delta": {"role": "assistant"},
                                     "finish_reason": None}]}

            async def event_stream():
                # 1) emit the assistant-role chunk IMMEDIATELY so the client
                #    shows "responding" instead of a frozen wait.
                yield _sse(_role_chunk())
                # 2) run the (blocking) reflection off-thread; heartbeat while it
                #    works so the ~12s ask path feels alive, not frozen.
                loop = asyncio.get_event_loop()
                fut = loop.run_in_executor(None, orchestrator.handle,
                                           user_input, session)
                while True:
                    done, _ = await asyncio.wait({fut}, timeout=HEARTBEAT_SECONDS)
                    if done:
                        break
                    yield ": keepalive\n\n"          # SSE comment; clients ignore
                result = fut.result()
                # 3) stream the produced text incrementally (typewriter), then
                #    the terminal chunk carrying ERO governance metadata.
                rest = stream_chunk_bodies(result, model=req_model,
                                           completion_id=completion_id,
                                           created=created)[1:]  # role already sent
                for chunk in rest:
                    yield _sse(chunk)
                yield "data: [DONE]\n\n"

            return StreamingResponse(event_stream(),
                                     media_type="text/event-stream")

        session = session_from_payload(payload, session_factory)
        status, body, headers = handle_chat(orchestrator, payload, model=model,
                                            session_state=session, now=_now)
        return JSONResponse(body, status_code=status, headers=headers)

    return app


def serve(orchestrator: Any, *, host: str = "127.0.0.1", port: int = 8000,
          model: str = DEFAULT_MODEL_ID, session_factory: Optional[Callable] = None,
          **kwargs) -> None:
    """Run the OpenAI-compatible server (blocking). Needs uvicorn."""
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - import guard
        raise ImportError(
            "ero.openai_api.serve needs uvicorn — `pip install uvicorn`."
        ) from exc
    uvicorn.run(create_app(orchestrator, model=model,
                           session_factory=session_factory, **kwargs),
                host=host, port=port)


if __name__ == "__main__":  # pragma: no cover - delegate to the console CLI
    from .cli import main
    main(["serve"] + __import__("sys").argv[1:])

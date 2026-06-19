"""Isolated live smoke (v0.4): run ERO in a sandbox and PROVE the MMV/RQA repos
are not mutated. gemma4:12b unified.

Prints sandbox contents (state landed here) so isolation is visible. The bash
caller checks git status before/after for the authoritative mutation guard.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from ero.sandbox import Sandbox, build_isolated_orchestrator
from ero.wiring import new_mmv_session


def snippet(res):
    if res.text:
        return res.text[:160].replace("\n", " ")
    q = getattr(res.result, "questions", None)
    return " | ".join(map(str, q[:2])) if q else repr(res.result)[:160]


def main():
    ws = HERE / "sandbox"
    print(f"sandbox = {ws}")
    t0 = time.time()
    with Sandbox(ws):
        ero = build_isolated_orchestrator(ws, audit_path=str(ws / "ero_audit.jsonl"))
        print(f"[built in {time.time()-t0:.1f}s; cwd={os.getcwd()}]\n")
        state = new_mmv_session()
        for label, prompt in [
            ("ask", "これとあれ、どっちがいい?"),
            ("answer", "What is the capital of France?"),
        ]:
            t = time.time()
            res = ero.handle(prompt, session_state=state)
            print(f"[{label}] {time.time()-t:.1f}s route={res.route!r} "
                  f"by={res.answered_by!r} avail={res.available}")
            print(f"        → {snippet(res)}")

    print("\nsandbox tree (state contained here):")
    for p in sorted(ws.rglob("*")):
        if p.is_file():
            print(f"  {p.relative_to(ws)}  ({p.stat().st_size}B)")


if __name__ == "__main__":
    main()

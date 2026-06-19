"""Prove the VENDORED MMV/RQA copies run under ERO, and that imports resolve to
the copies (not the originals). Bash caller checks the ORIGINAL repos stay clean.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# Point the existing isolated machinery at the VENDORED copies (env hook in
# wiring.py) BEFORE importing any ero module.
os.environ.setdefault("MMV_ROOT", str(HERE / "vendor" / "MOBIUS_MMV"))
os.environ.setdefault("RQA_ROOT", str(HERE / "vendor" / "mobius_rqa"))
sys.path.insert(0, str(HERE))

from ero.sandbox import Sandbox, build_isolated_orchestrator  # noqa: E402
from ero.wiring import new_mmv_session, _MMV_ROOT, _RQA_ROOT  # noqa: E402

print(f"MMV_ROOT = {_MMV_ROOT}")
print(f"RQA_ROOT = {_RQA_ROOT}")
assert "vendor" in str(_MMV_ROOT) and "vendor" in str(_RQA_ROOT), "not pointed at copies!"

ws = HERE / "sandbox_vendor"
with Sandbox(ws):
    ero = build_isolated_orchestrator(ws, audit_path=str(ws / "ero_audit.jsonl"))
    state = new_mmv_session()
    for label, p in [("ask", "これとあれ、どっちがいい?"),
                     ("answer", "What is the capital of France?")]:
        r = ero.handle(p, session_state=state)
        print(f"[{label}] route={r.route!r} by={r.answered_by!r} :: {(r.text or '')[:70]}")

# confirm the modules actually loaded from the vendored copies
import src.kernel.routing_engine as _rk  # noqa: E402
import rqa.controller as _rc  # noqa: E402
print(f"\nMMV module: {_rk.__file__}")
print(f"RQA module: {_rc.__file__}")
assert "vendor" in _rk.__file__ and "vendor" in _rc.__file__, "imports leaked to originals!"
print("\nOK: vendored stack ran; imports resolved to the copies.")

"""v0.9 live verify: vendored RQA reads cross-system (MMV) memory from the
unified store when ERO_UNIFIED_READ is on; identical native behavior when off.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
os.environ.setdefault("MMV_ROOT", str(HERE / "vendor" / "MOBIUS_MMV"))
os.environ.setdefault("RQA_ROOT", str(HERE / "vendor" / "mobius_rqa"))
ws = HERE / "sandbox_dualread"
ws.mkdir(parents=True, exist_ok=True)
os.environ["ERO_UNIFIED_DB"] = str(ws / "unified.db")
sys.path.insert(0, str(HERE))

from ero.unified_store import UnifiedStore  # noqa: E402
from ero.sandbox import Sandbox, isolated_rqa_controller  # noqa: E402

# seed the unified store with MMV-originated items (the "other system")
s = UnifiedStore(os.environ["ERO_UNIFIED_DB"])
s.put("mmv", "E", "The capital of France is Paris.")
s.put("mmv", "U", "The user prefers concise answers.")
s.close()


def _mmv_frags(run_result):
    return [f for f in run_result.injected_fragments
            if str(f["node_id"]).startswith("u_mmv_")]


with Sandbox(ws):
    ctrl = isolated_rqa_controller(ws)        # vendored RQA, state redirected
    q = "これとあれ、どっちがいい?"

    os.environ.pop("ERO_UNIFIED_READ", None)  # OFF
    off = _mmv_frags(ctrl.run(q))

    os.environ["ERO_UNIFIED_READ"] = "1"      # ON
    on = ctrl.run(q)
    on_frags = _mmv_frags(on)

print(f"\ndual-read OFF: cross-system MMV fragments injected = {len(off)}")
print(f"dual-read ON : cross-system MMV fragments injected = {len(on_frags)}")
for f in on_frags:
    print(f"   injected  {f['node_id']}  prov={f['provenance']}  {f['text'][:48]!r}")
print("\nverdict:",
      "✅ default-off unchanged, on-mode reads cross-system"
      if (len(off) == 0 and len(on_frags) >= 1) else "❌ unexpected")

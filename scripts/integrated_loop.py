"""v0.10 integrated loop: run the COMPOSITE end-to-end and show the unified
memory loop close across turns.

Phase A: seed MMV's standing memory via the REAL vendored MemoryIndexer.
Phase B: run a multi-turn conversation THROUGH the ERO orchestrator with
         dual-write + dual-read on. Each ask-turn's RQA reflection should draw on
         MMV's cross-system memory (and the unified store grows as turns add).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
os.environ.setdefault("MMV_ROOT", str(HERE / "vendor" / "MOBIUS_MMV"))
os.environ.setdefault("RQA_ROOT", str(HERE / "vendor" / "mobius_rqa"))
sys.path.insert(0, str(HERE / "vendor" / "MOBIUS_MMV"))
sys.path.insert(0, str(HERE / "vendor" / "mobius_rqa"))
sys.path.insert(0, str(HERE))

ws = HERE / "sandbox_loop"
ws.mkdir(parents=True, exist_ok=True)
os.environ["ERO_UNIFIED_DB"] = str(ws / "unified.db")
os.environ["ERO_UNIFIED_READ"] = "1"           # composite reads cross-system memory

from ero.sandbox import Sandbox, build_isolated_orchestrator  # noqa: E402
from ero.wiring import new_mmv_session  # noqa: E402
from ero.unified_store import UnifiedStore  # noqa: E402


def _seed_mmv_memory():
    from src.memory.memory_indexer import MemoryIndexer
    from src.memory.memory_capsule import MemoryCapsule
    mi = MemoryIndexer(index_path=str(ws / "capsule_index.faiss"),
                       db_path=str(ws / "capsules.db"))
    mi._load_encoder = lambda: None
    mi.open()
    for cid, text, mtype in [
        ("m1", "The user prefers concise, evidence-based answers.", "preference"),
        ("m2", "Paris is the capital of France.", "stable_fact"),
    ]:
        mi.add(MemoryCapsule(capsule_id=cid, session_id="prior", source_turn_ids=["t"],
                             memory_text=text, memory_type=mtype, salience_score=0.8,
                             audit_ref="t", created_at="2026-06-18T00:00:00Z"))
    mi.close()


with Sandbox(ws):
    _seed_mmv_memory()                          # MMV standing memory -> unified
    u0 = UnifiedStore(os.environ["ERO_UNIFIED_DB"]).count()
    print(f"seeded MMV memory; unified store starts at {u0} items\n")

    ero = build_isolated_orchestrator(ws, audit_path=str(ws / "ero_audit.jsonl"))
    state = new_mmv_session()
    turns = [
        "これとあれ、どっちがいい？",
        "それ、もっと良くして。",
        "あの件、どう進める？",
    ]
    for i, t in enumerate(turns, 1):
        res = ero.handle(t, session_state=state)
        line = f"turn {i}: route={res.route!r} by={res.answered_by!r}"
        if res.answered_by == "rqa:deepen":
            run = getattr(res.result, "raw", None)
            inj = getattr(run, "injected_fragments", []) if run else []
            xs = [f for f in inj if str(f["node_id"]).startswith("u_mmv_")]
            line += f"  | injected={len(inj)} cross-system(MMV)={len(xs)}  Q={res.text[:40]!r}"
            for f in xs:
                print(f"      ↳ read MMV memory: {f['text'][:54]!r}")
        cur = UnifiedStore(os.environ["ERO_UNIFIED_DB"]).count()
        print(line + f"  | unified now={cur}")

    final = UnifiedStore(os.environ["ERO_UNIFIED_DB"])
    print(f"\nloop closed: unified store {u0} -> {final.count()} items "
          f"(MMV seed + RQA turns), by class {final.by_class()}")

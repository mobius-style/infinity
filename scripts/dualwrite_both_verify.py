"""v0.8 verify: BOTH vendored systems dual-write into one unified store, via
their REAL memory classes (not just the sink unit test).

MMV: real MemoryIndexer with the heavy ME5 encoder skipped (_load_encoder->None;
     _embed falls back to a random vector — fine, we test the write hook, not
     retrieval). RQA: real QuestionGraph.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "vendor" / "MOBIUS_MMV"))
sys.path.insert(0, str(HERE / "vendor" / "mobius_rqa"))
sys.path.insert(0, str(HERE))

ws = HERE / "sandbox_both"
ws.mkdir(parents=True, exist_ok=True)
os.environ["ERO_UNIFIED_DB"] = str(ws / "unified.db")

# ---- MMV side: real MemoryIndexer ----------------------------------------
from src.memory.memory_indexer import MemoryIndexer  # noqa: E402
from src.memory.memory_capsule import MemoryCapsule  # noqa: E402

mi = MemoryIndexer(index_path=str(ws / "capsule_index.faiss"), db_path=str(ws / "capsules.db"))
mi._load_encoder = lambda: None          # skip heavy ME5; _embed -> random fallback
mi.open()
mi.add_turn("Paris is the capital of France.", "assistant", "s1")          # MMV -> S
for cid, text, mtype in [
    ("c1", "The user prefers concise answers.", "preference"),            # MMV -> U
    ("c2", "Water boils at 100C at sea level.", "stable_fact"),           # MMV -> E
]:
    try:
        mi.add(MemoryCapsule(capsule_id=cid, session_id="s1", source_turn_ids=["t"],
                             memory_text=text, memory_type=mtype, salience_score=0.8,
                             audit_ref="t", created_at="2026-06-18T00:00:00Z"))
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] MMV capsule add({mtype}) skipped: {e!r}")
mi.close()

# ---- RQA side: real QuestionGraph ----------------------------------------
from rqa.graph import QuestionGraph  # noqa: E402

g = QuestionGraph(str(ws / "graph.db"))
g.add_node("claim", "The user said option A is better.", "user")           # RQA -> U
g.add_node("tension", "As established earlier, A wins.", "self")           # RQA -> A

# ---- read the single unified store via ERO -------------------------------
from ero.unified_store import UnifiedStore  # noqa: E402
from ero.provenance import UnifiedMemoryView, ONTOLOGY  # noqa: E402

store = UnifiedStore(os.environ["ERO_UNIFIED_DB"])
rows = store.rows()  # (source, provenance, text)
print(f"\nunified store: {len(rows)} items dual-written by BOTH vendored systems")
from collections import Counter
src_cls = Counter((r[0], r[1]) for r in rows)
for (src, cls), n in sorted(src_cls.items()):
    print(f"  {src:4} {cls} x{n}")
b = store.by_class()
print("  by class:", {c: b[c] for c in ONTOLOGY})
view = UnifiedMemoryView([store.as_provider()])
print("  A-class (echo-prone):", [it.text[:40] for it in view.assistant_generated()])
print("  sources present:", sorted({r[0] for r in rows}))

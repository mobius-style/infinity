"""v0.11 live verify: vendored MMV MemoryIndexer.search reads cross-system (RQA)
memory from the unified store when ERO_UNIFIED_READ is on; native behavior
(empty -> []) when off. Encoder skipped; the ntotal==0 path needs no embedding.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "vendor" / "MOBIUS_MMV"))
sys.path.insert(0, str(HERE))

ws = HERE / "sandbox_mmvread"
ws.mkdir(parents=True, exist_ok=True)
os.environ["ERO_UNIFIED_DB"] = str(ws / "unified.db")

from ero.unified_store import UnifiedStore  # noqa: E402
from src.memory.memory_indexer import MemoryIndexer  # noqa: E402

# seed the unified store with RQA-originated items (the "other system")
s = UnifiedStore(os.environ["ERO_UNIFIED_DB"])
s.put("rqa", "A", "As established earlier, option A wins.")
s.put("rqa", "U", "The user said A is better.")
s.put("mmv", "E", "Paris (own-system; must not be returned to MMV).")
s.close()

mi = MemoryIndexer(index_path=str(ws / "capsule_index.faiss"), db_path=str(ws / "capsules.db"))
mi._load_encoder = lambda: None        # skip ME5; ntotal==0 path needs no embed
mi.open()


def _cross(results):
    return [r for r in results if r.get("_ero_cross")]


os.environ.pop("ERO_UNIFIED_READ", None)          # OFF
off = mi.search("どっちがいい?", top_k=5)

os.environ["ERO_UNIFIED_READ"] = "1"              # ON
on = mi.search("どっちがいい?", top_k=5)
mi.close()

print(f"MMV search OFF: {len(off)} results, cross-system={len(_cross(off))}")
print(f"MMV search ON : {len(on)} results, cross-system={len(_cross(on))}")
for r in _cross(on):
    print(f"   ↳ MMV read RQA memory: {r['capsule_id']} prov={r['_provenance']} {r['memory_text'][:48]!r}")
ok = len(_cross(off)) == 0 and len(_cross(on)) == 2 and all(
    r["capsule_id"].startswith("u_rqa_") for r in _cross(on))
print("\nverdict:", "✅ MMV dual-read symmetric (off unchanged, on reads RQA)" if ok else "❌ unexpected")

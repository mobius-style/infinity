"""v0.5 demo: run a few isolated turns, then read BOTH sandbox stores back
through the unified provenance view. Proves the lens works on real data while
the MMV/RQA repos stay untouched (bash caller runs the git guard).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from ero.sandbox import Sandbox, build_isolated_orchestrator
from ero.wiring import new_mmv_session
from ero.store_readers import rqa_graph_provider, mmv_capsule_provider
from ero.provenance import UnifiedMemoryView, ONTOLOGY


def main():
    ws = HERE / "sandbox"
    with Sandbox(ws):
        ero = build_isolated_orchestrator(ws, audit_path=str(ws / "ero_audit.jsonl"))
        state = new_mmv_session()
        prompts = [
            "これとあれ、どっちがいい?",
            "What is the capital of France?",
            "I prefer concise answers from now on.",
        ]
        t0 = time.time()
        for p in prompts:
            ero.handle(p, session_state=state)
        print(f"[{len(prompts)} turns in {time.time()-t0:.1f}s]\n")

        view = UnifiedMemoryView([
            rqa_graph_provider(ws / "rqa_state" / "graph.db"),
            mmv_capsule_provider(ws / "data" / "memory" / "capsules.db"),
        ])
        items = view.items()
        buckets = view.by_class()
        labels = {"U": "user", "A": "assistant(echo-prone)", "E": "external", "S": "system"}
        print(f"unified provenance view: {len(items)} items across both stores")
        for c in ONTOLOGY:
            print(f"  {c} {labels[c]:<22} : {len(buckets[c])}")
        print("\n  A-class (must not pose as independent evidence):")
        for it in view.assistant_generated()[:5]:
            print(f"    [{it.source}] {it.text[:70]!r}")
        print("\n  sample by source:")
        for it in items[:6]:
            print(f"    {it.provenance} [{it.source}] {it.text[:60]!r}")


if __name__ == "__main__":
    main()

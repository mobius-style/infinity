"""v0.7 live verify: vendored MMV+RQA dual-write into one unified store."""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
os.environ.setdefault("MMV_ROOT", str(HERE / "vendor" / "MOBIUS_MMV"))
os.environ.setdefault("RQA_ROOT", str(HERE / "vendor" / "mobius_rqa"))
ws = HERE / "sandbox_vendor"
# absolute DB path: the sink writes while cwd is the sandbox
os.environ["ERO_UNIFIED_DB"] = str(ws / "unified.db")
sys.path.insert(0, str(HERE))

from ero.sandbox import Sandbox, build_isolated_orchestrator  # noqa: E402
from ero.wiring import new_mmv_session  # noqa: E402
from ero.unified_store import UnifiedStore  # noqa: E402
from ero.provenance import UnifiedMemoryView, ONTOLOGY  # noqa: E402

with Sandbox(ws):
    ero = build_isolated_orchestrator(ws, audit_path=str(ws / "ero_audit.jsonl"))
    state = new_mmv_session()
    for p in ["これとあれ、どっちがいい?",
              "What is the capital of France?",
              "I prefer concise answers from now on."]:
        ero.handle(p, session_state=state)

store = UnifiedStore(os.environ["ERO_UNIFIED_DB"])
labels = {"U": "user", "A": "assistant(echo)", "E": "external", "S": "system"}
print(f"\nunified store — dual-written by vendored MMV+RQA: {store.count()} items")
b = store.by_class()
for c in ONTOLOGY:
    print(f"  {c} {labels[c]:<16}: {b[c]}")
view = UnifiedMemoryView([store.as_provider()])
print("\n  A-class (assistant-generated, must not pose as evidence):")
for it in view.assistant_generated()[:4]:
    print(f"    {it.text[:64]!r}")

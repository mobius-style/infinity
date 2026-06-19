"""Read-only store-reader tests (v0.5). Network-free; uses temp SQLite DBs
that mirror the real RQA/MMV schemas. No real backends needed.

    python3 tests/test_store_readers.py
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ero.store_readers import rqa_graph_provider, mmv_capsule_provider  # noqa: E402
from ero.provenance import UnifiedMemoryView, USER, ASSISTANT, EXTERNAL  # noqa: E402


def _tmp(name):
    return os.path.join(tempfile.mkdtemp(), name)


def _make_rqa(path):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE nodes (id INTEGER PRIMARY KEY, kind TEXT, text TEXT, "
                "status TEXT, provenance TEXT, created_at TEXT, session TEXT, meta TEXT)")
    con.executemany("INSERT INTO nodes (kind,text,provenance) VALUES (?,?,?)", [
        ("claim", "I prefer dark mode", "user"),
        ("tension", "as I noted, X", "self"),
    ])
    con.commit(); con.close()


def _make_mmv(path):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE capsules (capsule_id TEXT PRIMARY KEY, faiss_id INTEGER, "
                "session_id TEXT, memory_type TEXT, memory_text TEXT)")
    con.executemany("INSERT INTO capsules (capsule_id,memory_type,memory_text) VALUES (?,?,?)", [
        ("c1", "stable_fact", "Paris is the capital of France"),
        ("c2", "goal", "ship v1"),
    ])
    con.commit(); con.close()


def test_rqa_provider_reads_and_normalizes():
    p = _tmp("graph.db"); _make_rqa(p)
    rows = rqa_graph_provider(p).read()
    assert len(rows) == 2
    view = UnifiedMemoryView([rqa_graph_provider(p)])
    b = view.by_class()
    assert len(b[USER]) == 1 and len(b[ASSISTANT]) == 1


def test_mmv_provider_reads_and_normalizes():
    p = _tmp("capsules.db"); _make_mmv(p)
    view = UnifiedMemoryView([mmv_capsule_provider(p)])
    b = view.by_class()
    assert len(b[EXTERNAL]) == 1     # stable_fact
    assert len(b[USER]) == 1         # goal


def test_both_merge_and_assistant_isolation():
    rqa = _tmp("graph.db"); _make_rqa(rqa)
    mmv = _tmp("capsules.db"); _make_mmv(mmv)
    view = UnifiedMemoryView([rqa_graph_provider(rqa), mmv_capsule_provider(mmv)])
    assert len(view.items()) == 4
    a = view.assistant_generated()
    assert len(a) == 1 and a[0].source == "rqa"


def test_missing_file_is_empty_not_fatal():
    assert rqa_graph_provider("/no/such/graph.db").read() == []
    assert mmv_capsule_provider("/no/such/capsules.db").read() == []


def test_bad_schema_is_empty_not_fatal():
    p = _tmp("weird.db")
    con = sqlite3.connect(p); con.execute("CREATE TABLE other (x INTEGER)"); con.commit(); con.close()
    assert rqa_graph_provider(p).read() == []   # no `nodes` table -> [] (read-only, defensive)


def test_readers_open_read_only(tmp_path_unused=None):
    """A read against a real-shaped DB must not create or alter it."""
    p = _tmp("graph.db"); _make_rqa(p)
    before = os.stat(p)
    rqa_graph_provider(p).read()
    after = os.stat(p)
    assert (before.st_mtime, before.st_size) == (after.st_mtime, after.st_size)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t(); print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1; print(f"  FAIL  {t.__name__}: {e!r}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"  ERROR {t.__name__}: {e!r}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)

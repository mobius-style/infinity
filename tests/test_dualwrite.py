"""v0.7 Phase 2 dual-write tests (network-free).

Loads the VENDORED RQA sink by file path (no heavy package import) and proves it
writes rows that ERO's UnifiedStore reads back — i.e. schema compatibility — and
that it is env-gated (off by default) and idempotent.

    python3 tests/test_dualwrite.py
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(ROOT))

from ero.unified_store import UnifiedStore  # noqa: E402
from ero.provenance import UnifiedMemoryView, USER, ASSISTANT, EXTERNAL  # noqa: E402

# load the vendored sink by path (the real edited copy)
_SINK_PATH = ROOT / "vendor" / "mobius_rqa" / "rqa" / "_ero_sink.py"
_spec = importlib.util.spec_from_file_location("ero_sink_vendored", _SINK_PATH)
sink = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sink)


def _db():
    return os.path.join(tempfile.mkdtemp(), "unified.db")


def test_dualwrite_off_by_default():
    os.environ.pop("ERO_UNIFIED_DB", None)
    p = _db()
    sink.dualwrite("rqa", "A", "nothing should be written")
    assert not os.path.exists(p)        # no env -> no-op, file never created


def test_dualwrite_writes_schema_compatible_rows():
    p = _db()
    os.environ["ERO_UNIFIED_DB"] = p
    try:
        sink.dualwrite("rqa", "A", "as I noted, X")
        sink.dualwrite("mmv", "E", "Paris is the capital")
        sink.dualwrite("rqa", "U", "I prefer dark mode")
    finally:
        os.environ.pop("ERO_UNIFIED_DB", None)
    # ERO's UnifiedStore reads the vendored sink's DB (proves schema match)
    store = UnifiedStore(p)
    assert store.count() == 3
    b = store.by_class()
    assert b[USER] == 1 and b[ASSISTANT] == 1 and b[EXTERNAL] == 1
    view = UnifiedMemoryView([store.as_provider()])
    assert len(view.assistant_generated()) == 1


def test_dualwrite_is_idempotent():
    p = _db()
    os.environ["ERO_UNIFIED_DB"] = p
    try:
        for _ in range(3):
            sink.dualwrite("rqa", "A", "same item")
    finally:
        os.environ.pop("ERO_UNIFIED_DB", None)
    assert UnifiedStore(p).count() == 1


def test_dualwrite_swallows_bad_db_path():
    os.environ["ERO_UNIFIED_DB"] = "/no/such/dir/unified.db"
    try:
        sink.dualwrite("rqa", "A", "x")   # must not raise
    finally:
        os.environ.pop("ERO_UNIFIED_DB", None)


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

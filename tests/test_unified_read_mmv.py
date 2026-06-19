"""v0.11 MMV-side dual-read tests (network-free).

Loads the VENDORED MMV `_ero_read` by path and verifies env-gating, source
filtering (only the OTHER system = RQA), and MMV-capsule shape.

    python3 tests/test_unified_read_mmv.py
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

_PATH = ROOT / "vendor" / "MOBIUS_MMV" / "src" / "memory" / "_ero_read.py"
_spec = importlib.util.spec_from_file_location("ero_read_mmv_vendored", _PATH)
reader = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reader)


def _store():
    p = os.path.join(tempfile.mkdtemp(), "unified.db")
    s = UnifiedStore(p)
    s.put("rqa", "A", "as I established earlier")     # must come back
    s.put("rqa", "U", "the user said A is better")    # must come back
    s.put("mmv", "E", "Paris")                         # must NOT (own system)
    return p


def _clear():
    os.environ.pop("ERO_UNIFIED_READ", None)
    os.environ.pop("ERO_UNIFIED_DB", None)


def test_off_by_default():
    _clear(); os.environ["ERO_UNIFIED_DB"] = _store()
    try:
        assert reader.cross_system_capsules("q", 5) == []
    finally:
        _clear()


def test_returns_only_rqa_as_capsule_dicts():
    _clear(); p = _store()
    os.environ["ERO_UNIFIED_READ"] = "1"; os.environ["ERO_UNIFIED_DB"] = p
    try:
        caps = reader.cross_system_capsules("q", 5)
    finally:
        _clear()
    assert len(caps) == 2
    for c in caps:
        assert set(c) >= {"capsule_id", "memory_text", "memory_type", "_search_score", "_ero_cross"}
        assert c["capsule_id"].startswith("u_rqa_")
        assert c["_ero_cross"] is True


def test_missing_db_empty():
    _clear(); os.environ["ERO_UNIFIED_READ"] = "1"; os.environ["ERO_UNIFIED_DB"] = "/no/db.db"
    try:
        assert reader.cross_system_capsules("q", 5) == []
    finally:
        _clear()


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

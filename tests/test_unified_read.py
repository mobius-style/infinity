"""v0.9 Phase 3 dual-read tests (network-free).

Loads the VENDORED RQA `_ero_read` by path and verifies env-gating, source
filtering (only the OTHER system), and RQA-fragment shape, using a unified store
built by ERO's UnifiedStore.

    python3 tests/test_unified_read.py
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

_READ_PATH = ROOT / "vendor" / "mobius_rqa" / "rqa" / "_ero_read.py"
_spec = importlib.util.spec_from_file_location("ero_read_vendored", _READ_PATH)
reader = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reader)


def _store_with_both():
    p = os.path.join(tempfile.mkdtemp(), "unified.db")
    s = UnifiedStore(p)
    s.put("mmv", "E", "Paris is the capital")
    s.put("mmv", "S", "raw turn text")
    s.put("rqa", "A", "my own tension")        # must NOT come back
    return p


def _clear_env():
    os.environ.pop("ERO_UNIFIED_READ", None)
    os.environ.pop("ERO_UNIFIED_DB", None)


def test_off_by_default():
    _clear_env()
    p = _store_with_both()
    os.environ["ERO_UNIFIED_DB"] = p           # db set but READ flag off
    try:
        assert reader.cross_system_fragments("q", 8) == []
    finally:
        _clear_env()


def test_requires_both_flags():
    _clear_env()
    os.environ["ERO_UNIFIED_READ"] = "1"        # READ on but no DB
    try:
        assert reader.cross_system_fragments("q", 8) == []
    finally:
        _clear_env()


def test_returns_only_other_system_as_fragments():
    _clear_env()
    p = _store_with_both()
    os.environ["ERO_UNIFIED_READ"] = "1"
    os.environ["ERO_UNIFIED_DB"] = p
    try:
        frags = reader.cross_system_fragments("q", 8)
    finally:
        _clear_env()
    assert len(frags) == 2                       # both mmv rows, not the rqa one
    for f in frags:
        assert set(f) >= {"node_id", "kind", "text", "status", "provenance", "created_at", "score"}
        assert f["node_id"].startswith("u_mmv_")
    provs = {f["provenance"] for f in frags}
    assert provs <= {"external", "user", "self"}  # E/S -> external


def test_missing_db_is_empty():
    _clear_env()
    os.environ["ERO_UNIFIED_READ"] = "1"
    os.environ["ERO_UNIFIED_DB"] = "/no/such/unified.db"
    try:
        assert reader.cross_system_fragments("q", 8) == []
    finally:
        _clear_env()


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

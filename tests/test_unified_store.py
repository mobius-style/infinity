"""Unified store (v0.6 Phase 1) tests. Network-free.

    python3 tests/test_unified_store.py
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ero.unified_store import UnifiedStore, migrate  # noqa: E402
from ero.provenance import (  # noqa: E402
    UnifiedMemoryView, Provider, normalize_rqa, normalize_mmv,
    USER, ASSISTANT, EXTERNAL,
)


def _db():
    return os.path.join(tempfile.mkdtemp(), "unified.db")


def _rqa_provider(rows):
    return Provider("rqa", read=lambda: rows,
                    text_of=lambda r: r["text"],
                    class_of=lambda r: normalize_rqa(r["provenance"]))


def _mmv_provider(rows):
    return Provider("mmv", read=lambda: rows,
                    text_of=lambda r: r["memory_text"],
                    class_of=lambda r: normalize_mmv(r["memory_type"]))


def _view():
    rqa = _rqa_provider([
        {"text": "I prefer dark mode", "provenance": "user"},
        {"text": "as I noted, X", "provenance": "self"},
    ])
    mmv = _mmv_provider([
        {"memory_text": "Paris is the capital", "memory_type": "stable_fact"},
    ])
    return UnifiedMemoryView([rqa, mmv])


def test_migrate_consolidates_both_sources():
    s = UnifiedStore(_db())
    n = migrate(s, _view())
    assert n == 3 and s.count() == 3
    b = s.by_class()
    assert b[USER] == 1 and b[ASSISTANT] == 1 and b[EXTERNAL] == 1


def test_migrate_is_idempotent():
    s = UnifiedStore(_db())
    migrate(s, _view())
    migrate(s, _view())          # re-run
    assert s.count() == 3        # no duplicates


def test_put_normalizes_unknown_class_to_system():
    s = UnifiedStore(_db())
    s.put("x", "NOT_AN_ONTOLOGY_CLASS", "hi")
    assert s.rows()[0][1] == "S"


def test_as_provider_roundtrips_into_view():
    s = UnifiedStore(_db())
    migrate(s, _view())
    view2 = UnifiedMemoryView([s.as_provider()])
    assert len(view2.items()) == 3
    assert len(view2.assistant_generated()) == 1   # the RQA "self" item


def test_persistence_across_reopen():
    path = _db()
    s = UnifiedStore(path); migrate(s, _view()); s.close()
    s2 = UnifiedStore(path)
    assert s2.count() == 3


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

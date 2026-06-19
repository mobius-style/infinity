"""Unified provenance view tests (SPEC v0.3). Network-free.

    python3 tests/test_provenance.py
    python3 -m pytest tests/
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ero.provenance import (  # noqa: E402
    normalize_rqa, normalize_mmv, Provider, UnifiedMemoryView,
    USER, ASSISTANT, EXTERNAL, SYSTEM,
)


def test_normalize_rqa_verified_mapping():
    assert normalize_rqa("user") == USER
    assert normalize_rqa("self") == ASSISTANT
    assert normalize_rqa("SELF") == ASSISTANT          # case-insensitive
    assert normalize_rqa("whatever") == SYSTEM         # unknown -> system


def test_normalize_mmv_interpretive_mapping():
    assert normalize_mmv("stable_fact") == EXTERNAL
    for t in ("preference", "goal", "constraint", "open_loop"):
        assert normalize_mmv(t) == USER
    assert normalize_mmv("mystery") == SYSTEM


def _rqa_provider(rows):
    return Provider(
        name="rqa",
        read=lambda: rows,
        text_of=lambda r: r["text"],
        class_of=lambda r: normalize_rqa(r["provenance"]),
    )


def _mmv_provider(rows):
    return Provider(
        name="mmv",
        read=lambda: rows,
        text_of=lambda r: r["memory_text"],
        class_of=lambda r: normalize_mmv(r["memory_type"]),
    )


def test_view_merges_and_normalizes():
    rqa = _rqa_provider([
        {"text": "I prefer dark mode", "provenance": "user"},
        {"text": "you seemed to want X", "provenance": "self"},
    ])
    mmv = _mmv_provider([
        {"memory_text": "Paris is the capital", "memory_type": "stable_fact"},
        {"memory_text": "user goal: ship v1", "memory_type": "goal"},
    ])
    view = UnifiedMemoryView([rqa, mmv])
    items = view.items()
    assert len(items) == 4
    buckets = view.by_class()
    assert len(buckets[USER]) == 2          # rqa user + mmv goal
    assert len(buckets[ASSISTANT]) == 1     # rqa self
    assert len(buckets[EXTERNAL]) == 1      # mmv stable_fact


def test_assistant_generated_isolates_echo_prone_class():
    rqa = _rqa_provider([
        {"text": "as I noted, Y", "provenance": "self"},
        {"text": "user said Z", "provenance": "user"},
    ])
    view = UnifiedMemoryView([rqa])
    a = view.assistant_generated()
    assert len(a) == 1 and a[0].text == "as I noted, Y" and a[0].provenance == ASSISTANT


def test_downed_provider_is_skipped_not_fatal():
    def boom():
        raise RuntimeError("store offline")
    bad = Provider("mmv", read=boom, text_of=lambda r: "", class_of=lambda r: SYSTEM)
    good = _rqa_provider([{"text": "ok", "provenance": "user"}])
    view = UnifiedMemoryView([bad, good])
    items = view.items()                    # must not raise
    assert len(items) == 1 and items[0].source == "rqa"


# --- plain-python runner ---------------------------------------------------
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {t.__name__}: {e!r}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERROR {t.__name__}: {e!r}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)

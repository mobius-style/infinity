"""Read-only store readers (v0.5) — real providers for UnifiedMemoryView.

Opens each store's SQLite in READ-ONLY mode (`?mode=ro`), so this can never
write or migrate. Missing file / unexpected schema -> empty (the unified view
treats a downed source as skippable, not fatal). Verified schemas:
  - RQA graph  : table `nodes`    (text, provenance)            graph.py:27-32
  - MMV capsule: table `capsules` (memory_text, memory_type)    memory_indexer.py:341-347
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .provenance import Provider, normalize_rqa, normalize_mmv


def _ro_rows(db_path: str | Path, sql: str) -> list[tuple]:
    p = Path(db_path)
    if not p.is_file():
        return []
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        try:
            return list(con.execute(sql).fetchall())
        finally:
            con.close()
    except Exception:
        return []  # missing table / locked / schema drift -> skippable


def rqa_graph_provider(db_path: str | Path) -> Provider:
    """Provider over a RQA QuestionGraph SQLite (read-only)."""
    return Provider(
        name="rqa",
        read=lambda: _ro_rows(db_path, "SELECT text, provenance FROM nodes"),
        text_of=lambda r: r[0],
        class_of=lambda r: normalize_rqa(r[1]),
    )


def mmv_capsule_provider(db_path: str | Path) -> Provider:
    """Provider over a MMV capsules SQLite (read-only)."""
    return Provider(
        name="mmv",
        read=lambda: _ro_rows(db_path, "SELECT memory_text, memory_type FROM capsules"),
        text_of=lambda r: r[0],
        class_of=lambda r: normalize_mmv(r[1]),
    )

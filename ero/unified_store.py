"""Unified provenance store (v0.6, store-unification Phase 1).

A single SQLite store, OWNED BY ERO, holding provenance-tagged memory items from
both systems under one ontology (U/A/E/S). This is the consolidation target:

  Phase 1 (this module): read both existing stores and consolidate into the
      unified store (`migrate`). Read-side unification; the source systems are
      untouched.
  Phase 2 (future, on the vendored copies): cut the vendored MMV/RQA over to
      WRITE directly into this store (dual-write -> single-write). That is the
      part that needs modifying the (vendored, not original) internals.

`as_provider()` lets the unified store plug straight back into UnifiedMemoryView.
"""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Optional

from .provenance import Provider, ONTOLOGY, SYSTEM, ASSISTANT, normalize_rqa  # noqa: F401

_SCHEMA = """
CREATE TABLE IF NOT EXISTS unified_memory (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT NOT NULL,
    provenance  TEXT NOT NULL,
    text        TEXT NOT NULL,
    origin_id   TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_unified_origin
    ON unified_memory(source, origin_id);
"""


def _oid(source: str, text: str) -> str:
    return hashlib.sha1(f"{source}|{text}".encode("utf-8")).hexdigest()[:16]


class UnifiedStore:
    def __init__(self, db_path: str | Path) -> None:
        self.path = str(db_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.executescript(_SCHEMA)

    def put(self, source: str, provenance: str, text: str,
            origin_id: Optional[str] = None) -> None:
        prov = provenance if provenance in ONTOLOGY else SYSTEM
        oid = origin_id if origin_id is not None else _oid(source, text)
        # idempotent: (source, origin_id) is unique
        self._conn.execute(
            "INSERT OR IGNORE INTO unified_memory (source, provenance, text, origin_id) "
            "VALUES (?,?,?,?)", (source, prov, text, oid))
        self._conn.commit()

    def rows(self) -> list[tuple]:
        return list(self._conn.execute(
            "SELECT source, provenance, text FROM unified_memory ORDER BY id").fetchall())

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM unified_memory").fetchone()[0]

    def by_class(self) -> dict[str, int]:
        out = {c: 0 for c in ONTOLOGY}
        for c, n in self._conn.execute(
                "SELECT provenance, COUNT(*) FROM unified_memory GROUP BY provenance"):
            if c in out:
                out[c] = n
        return out

    def as_provider(self) -> Provider:
        """Plug the unified store back into a UnifiedMemoryView."""
        return Provider(
            name="unified",
            read=lambda: self.rows(),          # (source, provenance, text)
            text_of=lambda r: r[2],
            class_of=lambda r: r[1],           # already an ontology class
        )

    def close(self) -> None:
        self._conn.close()


def migrate(store: UnifiedStore, view) -> int:
    """Consolidate every item of a UnifiedMemoryView into the store.

    Idempotent: re-running does not duplicate (origin_id = hash(source|text)).
    Returns the number of items processed.
    """
    n = 0
    for it in view.items():
        store.put(it.source, it.provenance, it.text, origin_id=_oid(it.source, it.text))
        n += 1
    return n

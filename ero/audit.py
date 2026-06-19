"""Append-only audit for ERO turns (SPEC v0.2 §3).

Minimal by design: records the routing outcome, not user content. Two
implementations share a duck-typed `record(row: dict)` surface:
  - MemoryAudit: in-process list (tests / ephemeral).
  - JsonlAudit:  append-only JSONL file (real runs).
"""
from __future__ import annotations

import json
from typing import Any


class MemoryAudit:
    """In-process audit sink. `rows` is the append-only record."""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def record(self, row: dict[str, Any]) -> None:
        self.rows.append(dict(row))


class JsonlAudit:
    """Append-only JSONL audit sink."""

    def __init__(self, path: str) -> None:
        self.path = path

    def record(self, row: dict[str, Any]) -> None:
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

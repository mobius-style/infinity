"""Generic in-text citation verifier for MMV answers (SPEC v0.2 §2.3 follow-up).

MMV answers are free-form prose, so this is a CONSERVATIVE, non-destructive
scaffold: it detects bracketed citation-like markers and reports any whose
referent is not in the allowed set (typically `RoutingResult.sources`). It does
NOT rewrite the prose — ERO records the flags; the presentation layer decides.

It is a NO-OP when no markers are present, so a clean answer is never touched.
Markers recognized (documented convention, pending MMV's real format):
  - named:   [source: X] / [src: X] / [ref: X] / [node: X]
  - numeric: [1] [2] ...  -> 1-based index into the allowed list
"""
from __future__ import annotations

import re

_NAMED = re.compile(r"\[(?:source|src|ref|node)\s*[:\s]\s*([^\]]+?)\]", re.IGNORECASE)
_NUMERIC = re.compile(r"\[(\d{1,3})\]")


def find_citations(text: str) -> list[str]:
    """All citation markers in `text` (named referents and numeric indices)."""
    named = [m.strip() for m in _NAMED.findall(text or "")]
    numeric = _NUMERIC.findall(text or "")
    return named + [f"#{n}" for n in numeric]


def unknown_citations(text: str, allowed: list) -> list[str]:
    """Citation markers whose referent is not backed by `allowed`.

    Named markers must match an entry in `allowed` (substring-tolerant). Numeric
    `[n]` must be a valid 1-based index into `allowed`. Returns the offending
    markers (empty list == every citation is backed, or there were none).
    """
    allowed = list(allowed or [])
    allowed_str = [str(a) for a in allowed]
    unknown: list[str] = []

    for ref in (m.strip() for m in _NAMED.findall(text or "")):
        if not any(ref == a or ref in a or a in ref for a in allowed_str):
            unknown.append(ref)

    for n in _NUMERIC.findall(text or ""):
        idx = int(n)
        if idx < 1 or idx > len(allowed):
            unknown.append(f"#{n}")

    return unknown

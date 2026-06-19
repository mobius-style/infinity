"""ask-route framing (SPEC v0.2 §4).

ERO branches on the MMV *route*, not on a wide reason-code table. The `ask`
route emits exactly `MISSING_CONSTRAINTS` in the current MMV routing logic
(route_decision.py:138-143); other ask-route codes get a defensive default.

The framing is a pure string prefix on the user turn before RQA's
Controller.run(). It contains no Essentials/MMV-internal vocabulary, and it
never feeds back into MMV (one-way, SPEC v0.2 §1).
"""
from __future__ import annotations

# reason_code -> framing prefix. Keep entries only for codes the MMV `ask`
# route actually emits; everything else falls through to DEFAULT_FRAMING.
FRAMINGS: dict[str, str] = {
    "MISSING_CONSTRAINTS": (
        "Constraints are unstated. Surface the missing constraints as questions."
    ),
}

DEFAULT_FRAMING = (
    "This turn is not yet answerable as stated. Surface the deeper question "
    "that must be resolved first."
)


def build_augmented_input(user_input: str, reason_code: str) -> str:
    """Prefix the reflective framing for `reason_code` onto the user turn."""
    prefix = FRAMINGS.get(reason_code, DEFAULT_FRAMING)
    return f"{prefix}\n\n{user_input.strip()}"

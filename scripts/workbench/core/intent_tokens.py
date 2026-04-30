"""Backwards-compatible re-exports of the substring-strategy token sets.

Plan §P5.1 consolidated all router/intent token vocabularies into
``scripts/workbench/core/lexicon.py``. This module remains so that
existing imports (``from .intent_tokens import MISSION_TOKENS``)
continue to resolve. New code should import directly from ``lexicon``.
"""

from __future__ import annotations

from .lexicon import (  # noqa: F401 — re-exports
    CS_TOKENS,
    DRILL_ANSWER_NEGATIVE_KEYWORDS,
    MISSION_TOKENS,
)

__all__ = ["MISSION_TOKENS", "CS_TOKENS", "DRILL_ANSWER_NEGATIVE_KEYWORDS"]

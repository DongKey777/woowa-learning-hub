"""Lightweight follow-up detection for conversational RAG prompts."""

from __future__ import annotations

import re


KO_ANAPHORA_RE = re.compile(
    r"^\s*(이거|이건|그거|그건|그럼|그러면|그래서|아까|방금|왜\b|왜\s|어떻게\b|어떻게\s)"
)
EN_ANAPHORA_RE = re.compile(
    r"^\s*(this|that|then|so|why\b|how\b|what about|and then|example)\b",
    re.IGNORECASE,
)


def is_follow_up(prompt: str, *, max_chars: int = 25) -> bool:
    """Return True for short anaphoric prompts that need prior-turn context."""
    text = prompt.strip()
    if not text or len(text) >= max_chars:
        return False
    return bool(KO_ANAPHORA_RE.search(text) or EN_ANAPHORA_RE.search(text))

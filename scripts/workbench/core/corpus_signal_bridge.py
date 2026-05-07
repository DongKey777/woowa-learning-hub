"""Bridge the interactive router to corpus-owned signal rules.

The router's hand-written lexicon is intentionally conservative, but the CS
corpus already owns a much larger vocabulary in
``scripts.learning.rag.signal_rules``.  This module exposes a small,
best-effort adapter so broad learner phrases can use that vocabulary without
copying hundreds of trigger words into ``lexicon.py``.

The bridge is still classifier-safe:

* it returns only compact signal tags;
* it performs no model or index I/O;
* failures degrade to an empty list so the core router remains usable during
  bootstrap or partial installs.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterable


@lru_cache(maxsize=1)
def _detect_signals_func() -> Callable[[str], list[dict]] | None:
    """Load ``detect_signals`` lazily.

    ``bin/rag-ask`` executes ``scripts/workbench/cli.py`` by absolute path, so
    the repository root is not guaranteed to be importable.  Add it once before
    importing the corpus module.
    """
    root = Path(__file__).resolve().parents[3]
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    try:
        from scripts.learning.rag.signal_rules import detect_signals  # type: ignore
    except Exception:  # noqa: BLE001 - router must degrade safely
        return None
    return detect_signals


def detect_corpus_signal_tags(prompt: str) -> list[str]:
    """Return stable ``category:tag`` strings matched by corpus signal rules."""
    text = (prompt or "").strip()
    if not text:
        return []
    detect_signals = _detect_signals_func()
    if detect_signals is None:
        return []
    try:
        hits = detect_signals(text)
    except Exception:  # noqa: BLE001 - routing should never fail closed here
        return []
    tags: list[str] = []
    for hit in hits:
        category = str(hit.get("category") or "general")
        tag = str(hit.get("tag") or "").strip()
        if tag:
            tags.append(f"{category}:{tag}")
    return sorted(set(tags))


def has_corpus_signal(prompt: str) -> bool:
    return bool(detect_corpus_signal_tags(prompt))


def any_corpus_signal(prompts: Iterable[str]) -> bool:
    return any(has_corpus_signal(prompt) for prompt in prompts)


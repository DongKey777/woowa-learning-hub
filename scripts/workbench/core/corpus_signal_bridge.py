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
import re
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterable

from .lexicon import match_word_boundary_one


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
    """Return stable ``category:tag`` strings matched by corpus vocabulary."""
    text = (prompt or "").strip()
    if not text:
        return []
    detect_signals = _detect_signals_func()
    hits: list[dict] = []
    if detect_signals is not None:
        try:
            hits = detect_signals(text)
        except Exception:  # noqa: BLE001 - routing should never fail closed here
            hits = []
    tags: list[str] = []
    for hit in hits:
        category = str(hit.get("category") or "general")
        tag = str(hit.get("tag") or "").strip()
        if tag:
            tags.append(f"{category}:{tag}")
    if tags:
        return sorted(set(tags))
    return detect_corpus_phrase_tags(text)


def detect_corpus_phrase_tags(prompt: str) -> list[str]:
    """Return ``category:corpus_phrase`` if prompt matches corpus frontmatter.

    This catches specialized aliases such as ``XA`` or ``2PC`` that belong to
    a corpus document but are intentionally too narrow to live in the router's
    hand-written lexicon.
    """
    text = (prompt or "").strip()
    if not text:
        return []
    tags: set[str] = set()
    candidates: set[tuple[str, str]] = set()
    phrase_index = _corpus_router_phrase_index()
    for probe in _prompt_probes(text):
        candidates.update(phrase_index.get(probe, ()))
    for phrase, category in candidates:
        if match_word_boundary_one(text, phrase):
            tags.add(f"{category}:corpus_phrase")
    return sorted(tags)


def has_corpus_signal(prompt: str) -> bool:
    return bool(detect_corpus_signal_tags(prompt))


def any_corpus_signal(prompts: Iterable[str]) -> bool:
    return any(has_corpus_signal(prompt) for prompt in prompts)


_FRONTMATTER_LIST_KEYS = {
    "aliases",
    "symptoms",
    "expected_queries",
    "review_feedback_tags",
}
_FRONTMATTER_SCALAR_KEYS = {
    "title",
    "concept_id",
}
_PHRASE_STOPLIST = {
    "and",
    "or",
    "the",
    "a",
    "an",
    "to",
    "of",
    "in",
    "on",
    "for",
}


@lru_cache(maxsize=1)
def _corpus_router_phrases() -> tuple[tuple[str, str], ...]:
    root = Path(__file__).resolve().parents[3] / "knowledge" / "cs" / "contents"
    if not root.exists():
        return ()
    phrases: set[tuple[str, str]] = set()
    for path in root.glob("*/*.md"):
        category = path.parent.name
        for phrase in _frontmatter_phrases(path):
            cleaned = _clean_phrase(phrase)
            if _phrase_is_router_safe(cleaned):
                phrases.add((cleaned, category))
    return tuple(sorted(phrases))


@lru_cache(maxsize=1)
def _corpus_router_phrase_index() -> dict[str, tuple[tuple[str, str], ...]]:
    indexed: dict[str, set[tuple[str, str]]] = {}
    for phrase, category in _corpus_router_phrases():
        probe = _phrase_probe(phrase)
        if probe:
            indexed.setdefault(probe, set()).add((phrase, category))
    return {probe: tuple(sorted(values)) for probe, values in indexed.items()}


def _frontmatter_phrases(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:  # noqa: BLE001 - corrupt docs should not break routing
        return []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    phrases: list[str] = [path.stem.replace("-", " ")]
    current_list_key: str | None = None
    for raw in lines[1:]:
        line = raw.rstrip()
        if line.strip() == "---":
            break
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") and current_list_key in _FRONTMATTER_LIST_KEYS:
            phrases.append(stripped[2:].strip())
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_list_key = key if key in _FRONTMATTER_LIST_KEYS else None
        if key in _FRONTMATTER_SCALAR_KEYS and value:
            phrases.append(value)
            if key == "concept_id" and "/" in value:
                phrases.append(value.split("/", 1)[1].replace("-", " "))
    return phrases


def _clean_phrase(value: str) -> str:
    cleaned = value.strip().strip("'\"")
    cleaned = cleaned.replace("`", "").strip()
    if " #" in cleaned:
        cleaned = cleaned.split(" #", 1)[0].strip()
    return cleaned


def _phrase_is_router_safe(value: str) -> bool:
    if not value:
        return False
    lowered = value.casefold()
    if lowered in _PHRASE_STOPLIST:
        return False
    # Single-character Korean or ASCII terms are too noisy for a domain gate.
    if len(value) < 2:
        return False
    if value.isascii() and len(value) < 3 and not any(ch.isdigit() for ch in value):
        # Keep all-uppercase acronyms like XA, but reject lower-case fragments.
        return value.isupper()
    return True


_PROBE_RE = re.compile(r"[A-Za-z0-9]+|[가-힣]{2,}")


def _prompt_probes(text: str) -> set[str]:
    return {
        token.casefold()
        for token in _PROBE_RE.findall(text)
        if len(token) >= 2
    }


def _phrase_probe(phrase: str) -> str | None:
    for token in _PROBE_RE.findall(phrase):
        if len(token) >= 2:
            return token.casefold()
    return None

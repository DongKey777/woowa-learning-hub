"""Shared query/index tokenization for R3 Korean-first mixed retrieval."""

from __future__ import annotations

import re


_HANGUL_RE = re.compile(r"[가-힣]")
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+./-]*|[가-힣]{2,}|[0-9]+")
_KIWI = None


def _append_unique(out: list[str], seen: set[str], token: str) -> None:
    normalized = token.casefold().strip()
    if len(normalized) < 2 or normalized in seen:
        return
    seen.add(normalized)
    out.append(normalized)


def tokenize_text(text: str) -> tuple[str, ...]:
    """Tokenize text identically for query and lexical sidecar fields."""

    seen: set[str] = set()
    out: list[str] = []
    for raw in _TOKEN_RE.findall(text or ""):
        _append_unique(out, seen, raw)

    if not _HANGUL_RE.search(text or ""):
        return tuple(out)

    global _KIWI
    try:
        import kiwipiepy  # type: ignore
    except ImportError:
        return tuple(out)
    if _KIWI is None:
        _KIWI = kiwipiepy.Kiwi()
    for token in _KIWI.tokenize(text):
        for raw in _TOKEN_RE.findall(str(token.form)):
            _append_unique(out, seen, raw)
    return tuple(out)

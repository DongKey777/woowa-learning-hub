"""Query planning for Korean-first mixed CS questions."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Literal

from .tokenization import tokenize_text


Language = Literal["ko", "en", "mixed", "unknown"]
QUERY_PLAN_VERSION = "r3.0"

_HANGUL_RE = re.compile(r"[가-힣]")
_LATIN_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+./-]*")
_SPACE_RE = re.compile(r"\s+")


def detect_language(prompt: str) -> Language:
    """Detect language with mixed Korean/English CS terms preserved.

    A query like ``latency가 뭐야?`` is mixed, not Korean-only, because the
    English technical term is the retrieval anchor.
    """

    if not prompt.strip():
        return "unknown"
    has_hangul = bool(_HANGUL_RE.search(prompt))
    latin_terms = _LATIN_TOKEN_RE.findall(prompt)
    has_latin_anchor = any(len(term) >= 2 for term in latin_terms)
    if has_hangul and has_latin_anchor:
        return "mixed"
    if has_hangul:
        return "ko"
    if latin_terms:
        return "en"
    return "unknown"


def normalize_query(prompt: str) -> str:
    return _SPACE_RE.sub(" ", prompt.strip()).casefold()


def extract_terms(prompt: str) -> tuple[str, ...]:
    return tokenize_text(prompt)


def preserved_english_terms(prompt: str) -> tuple[str, ...]:
    seen: set[str] = set()
    terms: list[str] = []
    for raw in _LATIN_TOKEN_RE.findall(prompt):
        term = raw.casefold()
        if len(term) < 2 or term in seen:
            continue
        seen.add(term)
        terms.append(term)
    return tuple(terms)


@dataclass(frozen=True)
class QueryPlan:
    version: str
    raw_query: str
    normalized_query: str
    language: Language
    lexical_terms: tuple[str, ...]
    preserved_english_terms: tuple[str, ...]
    route_tags: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, blob: dict) -> "QueryPlan":
        return cls(
            version=str(blob.get("version") or QUERY_PLAN_VERSION),
            raw_query=str(blob["raw_query"]),
            normalized_query=str(blob["normalized_query"]),
            language=blob["language"],
            lexical_terms=tuple(blob.get("lexical_terms") or ()),
            preserved_english_terms=tuple(blob.get("preserved_english_terms") or ()),
            route_tags=tuple(blob.get("route_tags") or ()),
        )


def build_query_plan(prompt: str) -> QueryPlan:
    language = detect_language(prompt)
    preserved = preserved_english_terms(prompt)
    route_tags: list[str] = [f"language:{language}"]
    if language == "mixed":
        route_tags.append("korean_first_mixed")
    if preserved:
        route_tags.append("preserve_english_terms")
    return QueryPlan(
        version=QUERY_PLAN_VERSION,
        raw_query=prompt,
        normalized_query=normalize_query(prompt),
        language=language,
        lexical_terms=extract_terms(prompt),
        preserved_english_terms=preserved,
        route_tags=tuple(route_tags),
    )

"""Pseudo-Relevance Feedback (PRF) / RM3-style query expansion (plan §P4.3).

Deterministic fallback for ``searcher.search()`` when the AI session
in-turn query rewrite (``query-rewrite-v1``) is unavailable. PRF runs:

1. Initial retrieval on the original query → top-k pseudo-relevant docs.
2. Score each candidate term by *(tf in pseudo-relevant set) - (expected tf
   from collection background)* — terms that are unusually frequent in
   the relevant set, not just common words.
3. Pick the top-N expansion terms, dropping those already in the
   original query and any in the background stop set.
4. Build an expanded query by *interpolating* the expansion terms with
   the original query at weight ``alpha`` (RM3 mixing parameter):
   final tokens = original ∪ top-N expansion (de-duplicated, original
   ordering preserved).

The module is purely algorithmic: it takes a corpus iterator, a
retrieval callable, and a tokenizer. No file I/O, no model loading,
no LLM calls. Same input → same output.

Usage shape (expected integration point — wired in P5.7+):

```python
from scripts.learning.rag import prf

expansion = prf.rm3_expand(
    query="MVCC가 격리수준이랑 무슨 관계?",
    pseudo_relevant_docs=[doc1_text, doc2_text, doc3_text],
    background_token_freq=collection_freqs,  # dict[str, int]
    background_total_tokens=sum(collection_freqs.values()),
    alpha=0.5,
    max_expansion_terms=8,
)
# expansion.expanded_query — the new query string
# expansion.expansion_terms — the new terms with weights, sorted desc
```

When the AI rewrite output JSON is missing
(``state/cs_rag/query_rewrites/<hash>.output.json``), the searcher
should call ``rm3_expand`` to produce an expanded query for the
second retrieval pass.

Tested in ``tests/unit/test_prf.py``.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from collections.abc import Callable
from typing import Iterable, Sequence


# ---------------------------------------------------------------------------
# Tokenisation
# ---------------------------------------------------------------------------

# Match the family used by signal_rules.py:_TOKEN_RE — Korean + ASCII
# alphanumeric runs of length ≥ 1.
_TOKEN_RE = re.compile(r"[0-9a-zA-Z가-힣]+")

# Tokens we never want to surface as expansion terms even if frequent.
# Conservative — most filtering should happen via background_token_freq
# divergence, not stop-word lists. This is just for very obvious noise.
DEFAULT_STOP_TOKENS: frozenset[str] = frozenset({
    # Korean function-ish single chars / common particles that survive
    # tokenisation when chained
    "이", "그", "저", "것", "수", "등", "및", "또", "또는",
    "그리고", "그래서", "근데", "하지만",
    # English very-common words
    "the", "a", "an", "is", "are", "was", "were", "of", "to", "and",
    "or", "in", "on", "for", "with", "as", "at", "by", "from", "this",
    "that", "it", "be", "has", "have", "had", "but", "not", "if",
    # Single ASCII letters
    *"abcdefghijklmnopqrstuvwxyz",
})


def tokenize(text: str) -> list[str]:
    """Return lowercased Korean+alphanumeric tokens (length ≥ 2 for
    Korean/English; single digits/letters are always dropped at the
    stop-token layer)."""
    return [m.lower() for m in _TOKEN_RE.findall(text or "")]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExpansionTerm:
    term: str
    score: float  # higher = more discriminative
    pseudo_freq: int  # raw count in the pseudo-relevant set
    background_freq: int  # raw count in the collection


@dataclass(frozen=True)
class RM3Expansion:
    original_query: str
    original_tokens: tuple[str, ...]
    expansion_terms: tuple[ExpansionTerm, ...]
    expanded_query: str
    alpha: float
    pseudo_relevant_doc_count: int

    @property
    def added_tokens(self) -> tuple[str, ...]:
        return tuple(t.term for t in self.expansion_terms)


@dataclass(frozen=True)
class ModalExpansion:
    """Modal-aware PRF result for bge-m3 hybrid retrieval.

    ``rm3_expand`` remains the text-only compatibility API.  This wrapper adds
    sparse token expansion so the LanceDB/bge-m3 path can feed both the dense
    query text and learned sparse rescore.
    """

    expanded_query_text: str
    sparse_expansion_tokens: dict[int, float]
    expansion_terms: tuple[tuple[str, float], ...]
    text_expansion: RM3Expansion


# ---------------------------------------------------------------------------
# Term frequency helpers
# ---------------------------------------------------------------------------

def collect_term_frequencies(
    docs: Iterable[str],
    *,
    stop_tokens: frozenset[str] = DEFAULT_STOP_TOKENS,
    min_token_length: int = 2,
) -> tuple[dict[str, int], int]:
    """Return ``(term_freq, total_tokens)`` over ``docs``.

    ``min_token_length`` filters out single-character tokens that are
    almost always noise after tokenization (Korean particles fragments,
    1-letter ASCII like 'a').
    """
    freqs: dict[str, int] = {}
    total = 0
    for doc in docs:
        for tok in tokenize(doc):
            if len(tok) < min_token_length:
                continue
            if tok in stop_tokens:
                continue
            freqs[tok] = freqs.get(tok, 0) + 1
            total += 1
    return freqs, total


# ---------------------------------------------------------------------------
# RM3 scoring
# ---------------------------------------------------------------------------

def _score_term(
    term: str,
    pseudo_freq: int,
    pseudo_total: int,
    background_freq: int,
    background_total: int,
    *,
    smoothing: float = 1e-6,
) -> float:
    """RM3-style discriminative score.

    ``score = log( P(term | pseudo) / P(term | background) )``

    The log-ratio penalises terms that are merely common
    collection-wide. ``smoothing`` keeps the math stable when the
    background rate is zero (rare term that appears only in the
    pseudo-relevant set — a strong signal, gets a high but bounded
    score).
    """
    if pseudo_total <= 0:
        return 0.0
    p_pseudo = pseudo_freq / pseudo_total
    bg_total = max(background_total, 1)
    p_bg = (background_freq + smoothing) / (bg_total + smoothing)
    if p_pseudo <= 0 or p_bg <= 0:
        return 0.0
    return math.log(p_pseudo / p_bg)


def rm3_expand(
    query: str,
    *,
    pseudo_relevant_docs: Sequence[str],
    background_token_freq: dict[str, int],
    background_total_tokens: int | None = None,
    alpha: float = 0.5,
    max_expansion_terms: int = 8,
    stop_tokens: frozenset[str] = DEFAULT_STOP_TOKENS,
    min_token_length: int = 2,
    min_pseudo_freq: int = 2,
) -> RM3Expansion:
    """Build an RM3-style expansion of ``query`` from
    ``pseudo_relevant_docs``.

    Args:
      query: original learner query.
      pseudo_relevant_docs: top-k document texts from the initial
        retrieval pass (caller decides k; typically 5–10).
      background_token_freq: term → count over the whole collection.
        ``corpus_loader`` produces something equivalent.
      background_total_tokens: optional override; defaults to
        ``sum(background_token_freq.values())``.
      alpha: RM3 mixing weight in [0, 1]. ``1.0`` = original query
        only; ``0.0`` = ignore original. Default 0.5 — both contribute
        equally. Stored on the result for caller telemetry.
      max_expansion_terms: cap on the number of expansion terms
        appended (a 4th+ rewrite is mostly noise — same rule as the
        AI rewrite SKILL anti-pattern).
      stop_tokens: tokens never surfaced as expansion terms.
      min_token_length: tokens shorter than this are dropped.
      min_pseudo_freq: terms must appear at least this many times in
        the pseudo-relevant set to be considered. Filters one-off noise.

    Returns:
      ``RM3Expansion`` with the expanded query string and the ranked
      expansion terms. Deterministic.
    """
    if not (0.0 <= alpha <= 1.0):
        raise ValueError("alpha must be in [0, 1]")
    if max_expansion_terms < 0:
        raise ValueError("max_expansion_terms must be >= 0")

    original_tokens = tuple(
        t for t in tokenize(query)
        if len(t) >= min_token_length and t not in stop_tokens
    )
    original_set = set(original_tokens)

    pseudo_freqs, pseudo_total = collect_term_frequencies(
        pseudo_relevant_docs,
        stop_tokens=stop_tokens,
        min_token_length=min_token_length,
    )

    bg_total = (
        background_total_tokens
        if background_total_tokens is not None
        else sum(background_token_freq.values())
    )

    scored: list[ExpansionTerm] = []
    for term, p_freq in pseudo_freqs.items():
        if term in original_set:
            continue
        if p_freq < min_pseudo_freq:
            continue
        bg = background_token_freq.get(term, 0)
        score = _score_term(term, p_freq, pseudo_total, bg, bg_total)
        if score <= 0:
            continue
        scored.append(ExpansionTerm(
            term=term, score=score, pseudo_freq=p_freq, background_freq=bg
        ))

    # Sort by score desc, then term asc for determinism on ties.
    scored.sort(key=lambda t: (-t.score, t.term))
    selected = tuple(scored[:max_expansion_terms])

    # Build the expanded query: original tokens first (preserve order +
    # de-dup), then the expansion terms. We do not splice based on
    # alpha — alpha is recorded on the result object so the caller can
    # weight the second-pass retrieval accordingly. (Most search
    # backends expect a single string; weighting at retrieval time is
    # the caller's job.)
    expanded_parts: list[str] = []
    seen: set[str] = set()
    for tok in original_tokens:
        if tok not in seen:
            expanded_parts.append(tok)
            seen.add(tok)
    for term in selected:
        if term.term not in seen:
            expanded_parts.append(term.term)
            seen.add(term.term)

    expanded_query = " ".join(expanded_parts)

    return RM3Expansion(
        original_query=query,
        original_tokens=original_tokens,
        expansion_terms=selected,
        expanded_query=expanded_query,
        alpha=alpha,
        pseudo_relevant_doc_count=len(pseudo_relevant_docs),
    )


def _coerce_sparse_tokens(value) -> dict[int, float]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return {int(k): float(v) for k, v in value.items()}
    if isinstance(value, int):
        return {int(value): 1.0}
    out: dict[int, float] = {}
    try:
        iterator = iter(value)
    except TypeError:
        return {}
    for token_id in iterator:
        out[int(token_id)] = 1.0
    return out


def _top_sparse_tokens(
    sparse_docs: Sequence[dict[int, float]] | None,
    *,
    limit: int,
) -> dict[int, float]:
    if not sparse_docs or limit <= 0:
        return {}
    totals: dict[int, float] = {}
    for sparse in sparse_docs:
        for token_id, weight in sparse.items():
            totals[int(token_id)] = totals.get(int(token_id), 0.0) + float(weight)
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return dict(ranked[:limit])


def rm3_expand_modal(
    query: str,
    *,
    pseudo_relevant_docs: Sequence[str],
    pseudo_relevant_sparse: Sequence[dict[int, float]] | None = None,
    background_token_freq: dict[str, int],
    background_total_tokens: int | None = None,
    alpha: float = 0.5,
    max_expansion_terms: int = 8,
    stop_tokens: frozenset[str] = DEFAULT_STOP_TOKENS,
    min_token_length: int = 2,
    min_pseudo_freq: int = 2,
    tokenizer_for_sparse: Callable[[str], object] | None = None,
) -> ModalExpansion:
    """Build text + sparse PRF expansion for hybrid retrieval.

    ``tokenizer_for_sparse`` is optional because bge-m3 learned sparse token IDs
    are model-specific. When provided, each selected text expansion term is
    mapped to sparse token IDs. Regardless of tokenizer availability, the
    highest-weight sparse IDs from pseudo-relevant docs are included as a
    deterministic fallback.
    """
    text_expansion = rm3_expand(
        query,
        pseudo_relevant_docs=pseudo_relevant_docs,
        background_token_freq=background_token_freq,
        background_total_tokens=background_total_tokens,
        alpha=alpha,
        max_expansion_terms=max_expansion_terms,
        stop_tokens=stop_tokens,
        min_token_length=min_token_length,
        min_pseudo_freq=min_pseudo_freq,
    )

    sparse_tokens = _top_sparse_tokens(
        pseudo_relevant_sparse,
        limit=max_expansion_terms,
    )
    if tokenizer_for_sparse is not None:
        for term in text_expansion.expansion_terms:
            for token_id, weight in _coerce_sparse_tokens(tokenizer_for_sparse(term.term)).items():
                sparse_tokens[token_id] = sparse_tokens.get(token_id, 0.0) + weight * term.score

    sparse_tokens = dict(
        sorted(sparse_tokens.items(), key=lambda item: (-item[1], item[0]))[
            :max_expansion_terms
        ]
    )
    return ModalExpansion(
        expanded_query_text=text_expansion.expanded_query,
        sparse_expansion_tokens=sparse_tokens,
        expansion_terms=tuple((term.term, term.score) for term in text_expansion.expansion_terms),
        text_expansion=text_expansion,
    )

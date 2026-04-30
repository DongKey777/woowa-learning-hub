"""Unit tests for the PRF / RM3 fallback module (plan §P4.3).

Validates determinism, RM3 scoring direction (collection-rare terms
score higher than common ones), and the expansion-query construction
contract.
"""

from __future__ import annotations

import math

import pytest

from scripts.learning.rag import prf


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

def test_tokenize_lowercases_ascii():
    assert prf.tokenize("Spring Bean DI") == ["spring", "bean", "di"]


def test_tokenize_keeps_korean_runs():
    assert prf.tokenize("스프링 빈 컨테이너") == ["스프링", "빈", "컨테이너"]


def test_tokenize_mixed_drops_punctuation():
    assert prf.tokenize("MVCC가, 격리수준?") == ["mvcc가", "격리수준"]


def test_tokenize_empty_safe():
    assert prf.tokenize("") == []
    assert prf.tokenize(None) == []  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# collect_term_frequencies
# ---------------------------------------------------------------------------

def test_collect_term_frequencies_counts_repeats():
    freqs, total = prf.collect_term_frequencies(
        ["spring bean spring", "bean container"],
    )
    assert freqs["spring"] == 2
    assert freqs["bean"] == 2
    assert freqs["container"] == 1
    assert total == 5  # 'a' filtered as single-char... but here 'spring','bean','spring','bean','container'


def test_collect_term_frequencies_drops_stop_and_short():
    freqs, total = prf.collect_term_frequencies(
        ["a Bean is the the the spring"],
    )
    # 'a', 'is', 'the' are stop tokens; 'bean' and 'spring' kept
    assert "a" not in freqs
    assert "is" not in freqs
    assert "the" not in freqs
    assert freqs == {"bean": 1, "spring": 1}
    assert total == 2


# ---------------------------------------------------------------------------
# RM3 scoring direction
# ---------------------------------------------------------------------------

def test_score_term_higher_for_collection_rare_term():
    # Term A: equally frequent in pseudo (3/10) and background (300/1000).
    # Term B: same pseudo (3/10) but rare in background (3/1000).
    score_common = prf._score_term("A", pseudo_freq=3, pseudo_total=10, background_freq=300, background_total=1000)
    score_rare = prf._score_term("B", pseudo_freq=3, pseudo_total=10, background_freq=3, background_total=1000)
    assert score_rare > score_common
    assert score_common == pytest.approx(0.0, abs=1e-3)


def test_score_term_zero_when_pseudo_total_zero():
    assert prf._score_term("x", 0, 0, 1, 100) == 0.0


def test_score_term_smoothing_handles_zero_background():
    # When the term never appears in the background, smoothing keeps
    # the score finite (no division-by-zero or -inf)
    score = prf._score_term("rare", pseudo_freq=5, pseudo_total=20, background_freq=0, background_total=1000)
    assert math.isfinite(score)
    assert score > 0


# ---------------------------------------------------------------------------
# rm3_expand: end-to-end
# ---------------------------------------------------------------------------

def _bg_freqs(*pairs: tuple[str, int]) -> dict[str, int]:
    return dict(pairs)


def test_rm3_expand_picks_discriminative_term_over_common():
    """isolation appears equally in pseudo + background → low score.
    mvcc appears only in pseudo + rare in background → high score."""
    pseudo = [
        "MVCC는 격리수준과 관계가 있다 mvcc 스냅샷 동시성",
        "mvcc 스냅샷 격리 동시성",
        "mvcc 스냅샷 동시성 제어 관계",
    ]
    background = _bg_freqs(
        ("mvcc", 5),       # rare in background
        ("스냅샷", 4),     # rare in background, frequent in pseudo
        ("격리", 200),     # common in background
        ("동시성", 150),   # somewhat common
        ("관계", 800),     # very common
        ("제어", 600),
    )
    result = prf.rm3_expand(
        query="MVCC가 격리수준이랑 무슨 관계?",
        pseudo_relevant_docs=pseudo,
        background_token_freq=background,
        background_total_tokens=10_000,
        max_expansion_terms=3,
    )
    added = result.added_tokens
    # PRF should surface bare "mvcc" — it's frequent in the pseudo set
    # and rare in the background. (This also illustrates the Korean
    # particle problem: the query has "mvcc가" but docs say "mvcc";
    # PRF bridges that without needing morpheme analysis.)
    assert "mvcc" in added
    # Discriminative pseudo-only terms beat collection-common ones
    assert "스냅샷" in added or "동시성" in added
    # Common collection words ranked low — "관계" appears in 0.08% of
    # background but only once in pseudo, should not dominate
    if "관계" in added:
        # If it's added, it must rank below the truly discriminative ones
        scores = {t.term: t.score for t in result.expansion_terms}
        assert scores["관계"] < scores["mvcc"]
    # Original tokens preserved at the front of expanded_query
    assert result.expanded_query.startswith("mvcc가 격리수준이랑")


def test_rm3_expand_excludes_original_tokens():
    pseudo = ["spring bean container", "bean spring"]
    bg = _bg_freqs(("spring", 10), ("bean", 10), ("container", 5))
    result = prf.rm3_expand(
        query="spring bean",
        pseudo_relevant_docs=pseudo,
        background_token_freq=bg,
        background_total_tokens=1000,
        min_pseudo_freq=1,
    )
    for et in result.expansion_terms:
        assert et.term not in ("spring", "bean")


def test_rm3_expand_respects_max_expansion_terms():
    pseudo = ["alpha beta gamma delta epsilon zeta", "alpha beta gamma delta epsilon zeta"]
    bg = _bg_freqs(*[(c, 1) for c in ("alpha", "beta", "gamma", "delta", "epsilon", "zeta")])
    result = prf.rm3_expand(
        query="origin",
        pseudo_relevant_docs=pseudo,
        background_token_freq=bg,
        background_total_tokens=10_000,
        max_expansion_terms=3,
        min_pseudo_freq=1,
    )
    assert len(result.expansion_terms) <= 3


def test_rm3_expand_deterministic_on_ties():
    """Equal-score tokens must be ranked alphabetically so two runs
    on the same input produce identical expansion."""
    pseudo = ["alpha beta gamma", "alpha beta gamma"]
    bg = _bg_freqs(("alpha", 1), ("beta", 1), ("gamma", 1))
    r1 = prf.rm3_expand(
        query="origin",
        pseudo_relevant_docs=pseudo,
        background_token_freq=bg,
        background_total_tokens=1000,
        max_expansion_terms=3,
        min_pseudo_freq=1,
    )
    r2 = prf.rm3_expand(
        query="origin",
        pseudo_relevant_docs=pseudo,
        background_token_freq=bg,
        background_total_tokens=1000,
        max_expansion_terms=3,
        min_pseudo_freq=1,
    )
    assert r1.added_tokens == r2.added_tokens
    # Alphabetical ordering on ties
    assert list(r1.added_tokens) == sorted(r1.added_tokens)


def test_rm3_expand_min_pseudo_freq_filters_oneoff():
    """Terms appearing only once should be filtered when min_pseudo_freq=2."""
    pseudo = ["alpha noise once", "alpha noise"]
    bg = _bg_freqs(("alpha", 1), ("noise", 1), ("once", 1))
    result = prf.rm3_expand(
        query="origin",
        pseudo_relevant_docs=pseudo,
        background_token_freq=bg,
        background_total_tokens=1000,
        max_expansion_terms=10,
        min_pseudo_freq=2,
    )
    terms = result.added_tokens
    assert "once" not in terms
    assert "alpha" in terms
    assert "noise" in terms


def test_rm3_expand_rejects_invalid_alpha():
    with pytest.raises(ValueError):
        prf.rm3_expand(
            query="x",
            pseudo_relevant_docs=[],
            background_token_freq={},
            alpha=1.5,
        )


def test_rm3_expand_rejects_negative_max_terms():
    with pytest.raises(ValueError):
        prf.rm3_expand(
            query="x",
            pseudo_relevant_docs=[],
            background_token_freq={},
            max_expansion_terms=-1,
        )


def test_rm3_expand_empty_pseudo_yields_no_expansion():
    result = prf.rm3_expand(
        query="spring bean",
        pseudo_relevant_docs=[],
        background_token_freq={"spring": 1, "bean": 1},
        background_total_tokens=100,
    )
    assert result.expansion_terms == ()
    assert result.expanded_query == "spring bean"


def test_rm3_expand_records_alpha_and_doc_count():
    result = prf.rm3_expand(
        query="x",
        pseudo_relevant_docs=["a b", "c d"],
        background_token_freq={},
        background_total_tokens=100,
        alpha=0.3,
    )
    assert result.alpha == 0.3
    assert result.pseudo_relevant_doc_count == 2

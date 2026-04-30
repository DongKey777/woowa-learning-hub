from scripts.learning.rag.multi_query import build_query_candidates, weighted_rrf_merge


def test_build_query_candidates_dedupes_and_caps_candidates():
    candidates = build_query_candidates(
        "DI가 뭐야?",
        topic_hints=["spring"],
        follow_up_context=["concepts=concept:spring/bean"],
        rewrites=["Dependency injection definition", "Dependency injection definition", "IoC relation"],
        prf_terms=["constructor injection"],
        max_candidates=4,
    )

    assert [candidate.kind for candidate in candidates] == [
        "original",
        "follow_up",
        "rewrite",
        "rewrite",
    ]
    assert candidates[0].weight == 1.0
    assert candidates[1].weight == 0.9
    assert candidates[2].text == "Dependency injection definition"


def test_weighted_rrf_merge_uses_source_weight_and_rank_not_raw_score():
    merged = weighted_rrf_merge(
        [
            ([(1, 0.1), (2, 999.0)], 1.0),
            ([(2, 0.1), (3, 0.1)], 0.5),
        ],
        k=10,
    )

    scores = dict(merged)
    assert merged[0][0] == 2
    assert scores[2] > scores[1]
    assert scores[2] > scores[3]
    assert scores[2] == (1.0 / 12) + (0.5 / 11)

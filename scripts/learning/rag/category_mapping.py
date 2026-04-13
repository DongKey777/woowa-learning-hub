"""Learning-point ↔ CS corpus category mapping.

Keys must match the `id` field in
`scripts/workbench/core/candidate_interpretation.py::LEARNING_POINT_RULES`.
A consistency test (`tests/unit/test_learning_point_id_consistency.py`)
asserts this so silent drift cannot happen.

Values are CS corpus top-level categories under `knowledge/cs/contents/`:
    algorithm, data-structure, database, design-pattern, language, network,
    operating-system, security, software-engineering, spring, system-design
"""

from __future__ import annotations

LEARNING_POINT_TO_CS_CATEGORY: dict[str, list[str]] = {
    "repository_boundary":     ["database", "design-pattern", "spring"],
    "responsibility_boundary": ["design-pattern", "software-engineering"],
    "transaction_consistency": ["database", "spring"],
    "db_modeling":             ["database"],
    "reconstruction_mapping":  ["design-pattern", "software-engineering"],
    "testing_strategy":        ["software-engineering", "language"],
    "resource_lifecycle":      ["operating-system", "network", "spring"],
    "review_response":         ["software-engineering"],
}

GENERAL_FALLBACK_CATEGORIES: list[str] = [
    "software-engineering",
    "design-pattern",
    "database",
    "network",
    "language",
]

# Canonical domain phrases prepended to the reranker prompt when a
# learning point is active. These steer the multilingual cross-encoder
# toward the right topic even when the raw learner prompt contains
# Korean terms that collide with unrelated English pattern names — e.g.
# "책임 분리" (separation of responsibilities) surface-matching
# "Chain of Responsibility". FTS/dense retrieval is left untouched; only
# the reranker sees the decorated prompt.
LEARNING_POINT_ANCHOR_PHRASES: dict[str, str] = {
    "repository_boundary":
        "repository pattern 영속성 경계 persistence boundary DAO anti-pattern",
    "responsibility_boundary":
        "layered architecture service layer separation of concerns 계층 책임",
    "transaction_consistency":
        "transaction isolation propagation commit rollback 트랜잭션 격리 전파",
    "db_modeling":
        "schema design normalization index primary key foreign key 정규화",
    "reconstruction_mapping":
        "domain model object mapping value object 도메인 매핑",
    "testing_strategy":
        "unit test integration test fixture mock 테스트 전략",
    "resource_lifecycle":
        "connection pool resource lifecycle close leak 리소스 수명",
    "review_response":
        "code review feedback communication 리뷰 대응",
}


def categories_for(learning_point_id: str) -> list[str]:
    """Return the category whitelist for a learning point, or the general fallback."""
    return LEARNING_POINT_TO_CS_CATEGORY.get(
        learning_point_id, list(GENERAL_FALLBACK_CATEGORIES)
    )


def anchor_phrase_for(learning_points: list[str] | None) -> str:
    """Return a combined anchor phrase for the active learning points.

    Preserves the order in which learning points were provided. Unknown
    ids are skipped. Returns an empty string when no anchors apply.
    """
    if not learning_points:
        return ""
    parts: list[str] = []
    for lp in learning_points:
        phrase = LEARNING_POINT_ANCHOR_PHRASES.get(lp)
        if phrase:
            parts.append(phrase)
    return " ".join(parts)


def reverse_lookup(category: str) -> list[str]:
    """Return learning-point ids that list the given category (ranked by position)."""
    hits: list[tuple[int, str]] = []
    for lp_id, cats in LEARNING_POINT_TO_CS_CATEGORY.items():
        if category in cats:
            hits.append((cats.index(category), lp_id))
    hits.sort(key=lambda t: t[0])
    return [lp for _, lp in hits]

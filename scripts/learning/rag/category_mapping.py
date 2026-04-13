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


def categories_for(learning_point_id: str) -> list[str]:
    """Return the category whitelist for a learning point, or the general fallback."""
    return LEARNING_POINT_TO_CS_CATEGORY.get(
        learning_point_id, list(GENERAL_FALLBACK_CATEGORIES)
    )


def reverse_lookup(category: str) -> list[str]:
    """Return learning-point ids that list the given category (ranked by position)."""
    hits: list[tuple[int, str]] = []
    for lp_id, cats in LEARNING_POINT_TO_CS_CATEGORY.items():
        if category in cats:
            hits.append((cats.index(category), lp_id))
    hits.sort(key=lambda t: t[0])
    return [lp for _, lp in hits]

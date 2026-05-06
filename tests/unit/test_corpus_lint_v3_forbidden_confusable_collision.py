"""Pin: corpus_lint catches when chooser/bridge/symptom_router puts the
same neighbour in both ``forbidden_neighbors`` and ``confusable_with``.

Cycle 1 cohort_eval (2026-05-06) regressed -7.5pp on confusable_pairs
because fleet-authored chooser docs populated forbidden_neighbors
with the canonical primer they themselves named in confusable_with
— collapsing two different dimensions:

  confusable_with   = "competing / learning-path neighbour"
  forbidden_neighbors = "wrong-bucket noise"

The post-rerank forbidden_filter consequently dropped the primer
out of top-k whenever the chooser became top-1.

Lint catches the collision via slug overlap (cheap per-file proxy
for the catalog-level check) and emits a Wave 2 warning so legacy
docs continue to lint pass while new writes are flagged.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.learning.rag.corpus_lint import (
    check_corpus_v3_pilot_frontmatter,
)


def _fm(**overrides):
    base = {
        "schema_version": 3,
        "concept_id": "design-pattern/registry-vs-locator",
        "doc_role": "chooser",
        "category": "design-pattern",
        "level": "beginner",
        "language": "ko",
        "title": "Registry vs Locator",
        "source_priority": 86,
        "aliases": ["registry vs locator", "DI vs locator"],
        "expected_queries": ["registry랑 locator 차이?"],
        "intents": ["comparison"],
        "mission_ids": [],
        "review_feedback_tags": [],
        "symptoms": ["getBean 써도 되나"],
        "prerequisites": ["software-engineering/dependency-injection-basics"],
        "next_docs": [],
        "linked_paths": [],
        "confusable_with": [],
        "forbidden_neighbors": [],
        "contextual_chunk_prefix": "이 문서는 ...",
        "canonical": False,
    }
    base.update(overrides)
    return base


class ForbiddenConfusableCollisionTest(unittest.TestCase):
    def _check(self, fm):
        return check_corpus_v3_pilot_frontmatter(
            file_path=Path("knowledge/cs/contents/design-pattern/registry-vs-locator.md"),
            frontmatter=fm,
            strict_mode=True,
        )

    def test_chooser_with_collision_flagged(self) -> None:
        """The cycle-1 collision case: chooser names primer in BOTH
        confusable_with AND forbidden_neighbors → must be flagged."""
        fm = _fm(
            doc_role="chooser",
            confusable_with=[
                "spring/bean-di-basics",
                "design-pattern/service-locator",
            ],
            forbidden_neighbors=[
                "contents/spring/spring-bean-di-basics.md",
            ],
        )
        violations = self._check(fm)
        messages = [v.message for v in violations]
        self.assertTrue(
            any("different dimensions" in m for m in messages),
            f"expected collision warning, got: {messages}",
        )

    def test_bridge_with_collision_flagged(self) -> None:
        fm = _fm(
            doc_role="bridge",
            confusable_with=[
                "spring/bean-di-basics",
                "design-pattern/factory",
            ],
            forbidden_neighbors=[
                "contents/spring/spring-bean-di-basics.md",
            ],
        )
        violations = self._check(fm)
        self.assertTrue(
            any("different dimensions" in v.message for v in violations),
        )

    def test_symptom_router_with_collision_flagged(self) -> None:
        fm = _fm(
            doc_role="symptom_router",
            confusable_with=[
                "spring/bean-di-basics",
                "spring/transaction-basics",
            ],
            forbidden_neighbors=[
                "contents/spring/spring-bean-di-basics.md",
            ],
        )
        violations = self._check(fm)
        self.assertTrue(
            any("different dimensions" in v.message for v in violations),
        )

    def test_primer_collision_not_flagged(self) -> None:
        """primer is allowed to list any deep_dive in forbidden, even
        if confusable_with overlaps. The cycle-1 fix targets only
        chooser/bridge/symptom_router."""
        fm = _fm(
            doc_role="primer",
            canonical=True,
            confusable_with=["spring/bean-di-basics"],
            forbidden_neighbors=[
                "contents/spring/spring-bean-di-basics.md",
            ],
        )
        violations = self._check(fm)
        self.assertFalse(
            any("different dimensions" in v.message for v in violations),
        )

    def test_chooser_without_collision_passes(self) -> None:
        """chooser with disjoint confusable_with and forbidden_neighbors
        is the well-formed case."""
        fm = _fm(
            doc_role="chooser",
            confusable_with=[
                "design-pattern/factory",
                "design-pattern/strategy",
            ],
            forbidden_neighbors=[
                "contents/design-pattern/observer-pattern-basics.md",
            ],
        )
        violations = self._check(fm)
        self.assertFalse(
            any("different dimensions" in v.message for v in violations),
        )

    def test_chooser_empty_lists_no_collision_warning(self) -> None:
        fm = _fm(
            doc_role="chooser",
            confusable_with=[
                "design-pattern/factory",
                "design-pattern/strategy",
            ],
            forbidden_neighbors=[],
        )
        violations = self._check(fm)
        self.assertFalse(
            any("different dimensions" in v.message for v in violations),
        )


if __name__ == "__main__":
    unittest.main()

"""Pin: v3 migration prompts must teach workers the doc_role-aware
forbidden_neighbors rules introduced after the 2026-05-06 cycle 1
regression analysis.

Background: cycle 1 cohort_eval showed -7.5pp on confusable_pairs.
Per-query trace pinned the failure mode to chooser docs whose
forbidden_neighbors lists named the canonical primer of their own
area — when the chooser became top-1 retrieval, the post-rerank
forbidden_filter dropped the primer out of top-k, regressing every
"what is X?" query that should have surfaced the primer.

The fix is fleet-prompt-level discipline: workers must distinguish
``confusable_with`` (competing / learning-path) from
``forbidden_neighbors`` (wrong-bucket noise) and follow doc_role-
specific rules. This test pins the prompt content so a future edit
cannot silently strip the guidance.
"""

from __future__ import annotations

import unittest

from scripts.workbench.core.orchestrator_workers import _worker_prompt


def _render_v3_prompt() -> str:
    return _worker_prompt(
        "migration-v3-60-frontmatter-spring",
        "migration-content-spring",
        {"item_id": "t", "title": "t", "goal": "g", "tags": []},
        fleet_profile="migration_v3_60",
    )


class ForbiddenNeighborsGuidanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.prompt = _render_v3_prompt()

    def test_distinguishes_confusable_vs_forbidden(self) -> None:
        """Prompt must explicitly teach the dimension distinction."""
        self.assertIn("competing/learning-path neighbour", self.prompt)
        self.assertIn("wrong-bucket noise", self.prompt)

    def test_cites_cycle1_regression_evidence(self) -> None:
        """The reasoning section must cite the regression so future
        editors understand why the rule exists."""
        self.assertIn("2026-05-06", self.prompt)
        self.assertIn("confusable_pairs", self.prompt)

    def test_chooser_must_not_forbid_primer(self) -> None:
        """The single most important rule for the cycle-1 regression
        fix: chooser/bridge must not put canonical primer in
        forbidden_neighbors."""
        self.assertIn("DO NOT list: the canonical primer", self.prompt)

    def test_role_specific_rules_present(self) -> None:
        """Each major doc_role gets explicit DO/DO NOT rules."""
        for marker in [
            "doc_role = chooser",
            "doc_role = primer",
        ]:
            self.assertIn(marker, self.prompt)

    def test_revisit_body_summarized_rule(self) -> None:
        """The Wave D revisit prompt's quick-rule line (where the
        actionable revisit checklist lives) must also warn against
        listing the canonical primer."""
        revisit_prompt = _worker_prompt(
            "migration-v3-60-revisit-quality-deepen",
            "migration-content-revisit",
            {"item_id": "t", "title": "t", "goal": "g", "tags": []},
            fleet_profile="migration_v3_60",
        )
        self.assertIn("NEVER list the canonical primer", revisit_prompt)
        self.assertIn("wrong-bucket", revisit_prompt)
        # primer→chooser learning path rationale
        self.assertIn("primer→chooser", revisit_prompt)


if __name__ == "__main__":
    unittest.main()

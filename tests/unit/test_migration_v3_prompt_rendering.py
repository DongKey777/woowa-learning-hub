"""Phase 8 — migration_v3 prompt rendering contract.

The legacy expansion fleet's `_worker_prompt()` body pushes a
*retrieval-anchor-keywords + 7-element Beginner-primer* contract that
directly contradicts the v3 frontmatter contract this fleet is
supposed to introduce. This module asserts that:

  * migration modes (`migrate_v0_to_v3` / `migrate_prefix` /
    `migrate_new_doc`) use a v3-aware prompt body
  * the v3 prompt cites Pilot lock, corpus_lint --strict-v3, and the
    18-field frontmatter map
  * the legacy lint command (`scripts/lint_cs_authoring.py`) is NOT
    referenced as a target gate — that lint enforces the contract we
    are migrating *away from*
  * non-migration workers (legacy fleets) keep their original prompt
    body untouched
"""

from __future__ import annotations

import unittest

from scripts.workbench.core.orchestrator_workers import _worker_prompt


def _fake_item(item_id: str = "test-001") -> dict:
    return {
        "item_id": item_id,
        "title": "v3 frontmatter migration: spring/foo.md",
        "goal": "Run the migration step for 3 docs in spring",
        "tags": ["spring", "v3", "wave-a"],
    }


class MigrateV0ToV3PromptTest(unittest.TestCase):
    def setUp(self):
        self.prompt = _worker_prompt(
            "migration-v3-60-frontmatter-spring",
            "migration-content-spring",
            _fake_item(),
            fleet_profile="migration_v3_60",
        )

    def test_cites_v3_contract(self):
        self.assertIn("v3 frontmatter contract", self.prompt)
        self.assertIn("18 fields", self.prompt)
        self.assertIn("docs/worklogs/rag-r3-corpus-v3-contract.md", self.prompt)

    def test_cites_pilot_lock(self):
        self.assertIn("Pilot lock", self.prompt)
        self.assertIn("config/migration_v3/locked_pilot_paths.json", self.prompt)

    def test_cites_strict_v3_lint(self):
        self.assertIn("--strict-v3", self.prompt)
        self.assertIn("scripts.learning.rag.corpus_lint", self.prompt)

    def test_lists_18_fields(self):
        # Spot-check the canonical V3_FIELD_ORDER appears
        for field in (
            "schema_version", "concept_id", "doc_role", "level",
            "language", "source_priority", "mission_ids",
            "review_feedback_tags", "aliases", "symptoms", "intents",
            "prerequisites", "next_docs", "linked_paths",
            "confusable_with", "forbidden_neighbors",
            "expected_queries", "contextual_chunk_prefix",
        ):
            self.assertIn(field, self.prompt)

    def test_aliases_eq_disjoint_rule_present(self):
        self.assertIn("aliases", self.prompt)
        self.assertIn("expected_queries", self.prompt)
        # Prompt uses the math notation `⊥` plus an English explanation
        self.assertIn("⊥", self.prompt)
        self.assertIn("no phrase may appear in both lists", self.prompt)

    def test_does_not_call_legacy_lint_as_required_gate(self):
        # The legacy expansion prompt says "must pass scripts/lint_cs_authoring.py".
        # Migration prompt may *mention* the legacy contract is being phased
        # out, but must NOT instruct the worker to run lint_cs_authoring.
        legacy_lint_required_phrase = "must pass `scripts/lint_cs_authoring.py`"
        self.assertNotIn(legacy_lint_required_phrase, self.prompt)


class MigratePrefixPromptTest(unittest.TestCase):
    def setUp(self):
        self.prompt = _worker_prompt(
            "migration-v3-60-prefix-database",
            "migration-content-database",
            _fake_item("prefix-test-001"),
            fleet_profile="migration_v3_60",
        )

    def test_cites_token_range(self):
        self.assertIn("50-100 token", self.prompt)

    def test_cites_doc_role_tone_guide(self):
        self.assertIn("doc_role tone", self.prompt)
        self.assertIn("primer", self.prompt)
        self.assertIn("처음 잡는다", self.prompt)
        self.assertIn("deep_dive", self.prompt)
        self.assertIn("playbook", self.prompt)

    def test_cites_paraphrase_rule(self):
        self.assertIn("paraphrase", self.prompt)
        self.assertIn("alias와", self.prompt)  # alias 구분 규칙

    def test_cites_corpus_loader_doc_level_contract(self):
        self.assertIn("corpus_loader.py", self.prompt)
        self.assertIn("doc-level", self.prompt)


class MigrateNewDocPromptTest(unittest.TestCase):
    def setUp(self):
        self.prompt = _worker_prompt(
            "migration-v3-60-new-mission-bridge-roomescape",
            "migration-content-mission-bridge",
            {
                "item_id": "new-doc-roomescape-001",
                "title": "Roomescape DI ↔ Spring DI bridge",
                "goal": "Write a mission_bridge doc connecting roomescape DAO to Spring DI",
                "tags": ["roomescape", "mission-bridge", "wave-c"],
            },
            fleet_profile="migration_v3_60",
        )

    def test_lists_three_doc_roles(self):
        self.assertIn("CHOOSER", self.prompt)
        self.assertIn("SYMPTOM_ROUTER", self.prompt)
        self.assertIn("MISSION_BRIDGE", self.prompt)

    def test_role_conditional_minimums_stated(self):
        self.assertIn("symptoms: ≥ 3", self.prompt)
        self.assertIn("confusable_with", self.prompt)
        self.assertIn("mission_ids", self.prompt)

    def test_cites_cohort_eval_motivation(self):
        # The new-doc body explains why these 3 doc_roles get a fleet
        # carve-out: they are the cohort_eval weak spots.
        self.assertIn("83.3%", self.prompt)
        self.assertIn("90.0%", self.prompt)
        self.assertIn("93.3%", self.prompt)


class LegacyFleetPromptUnchangedTest(unittest.TestCase):
    """Other fleets (quality / expansion / expansion60) must NOT pick
    up the migration prompt body."""

    def test_expansion60_worker_keeps_legacy_prompt(self):
        # expansion60-spring-di-bean is mode='expand', not a migration mode
        prompt = _worker_prompt(
            "expansion60-spring-di-bean",
            "spring",
            _fake_item("expansion60-test-001"),
            fleet_profile="expansion60",
        )
        # Migration prompt has these — legacy must not
        self.assertNotIn("PHASE 8 V3 MIGRATION CONTRACT", prompt)
        self.assertNotIn("config/migration_v3/locked_pilot_paths.json", prompt)
        # Legacy expansion prompt has these
        self.assertIn("Corpus quality contract", prompt)
        self.assertIn("scripts/lint_cs_authoring.py", prompt)

    def test_quality_worker_keeps_legacy_prompt(self):
        prompt = _worker_prompt(
            "runtime-java-basics",
            "language-java",
            _fake_item("quality-test-001"),
            fleet_profile="quality",
        )
        self.assertNotIn("PHASE 8 V3 MIGRATION CONTRACT", prompt)


class OutputContractStableTest(unittest.TestCase):
    """Migration prompts must keep the schema fields the orchestrator
    expects (summary / changed_files / next_candidates) so the
    completion gate path stays the same."""

    def test_v0_to_v3_lists_schema_fields(self):
        prompt = _worker_prompt(
            "migration-v3-60-frontmatter-spring",
            "migration-content-spring",
            _fake_item(),
            fleet_profile="migration_v3_60",
        )
        self.assertIn("summary", prompt)
        self.assertIn("changed_files", prompt)
        self.assertIn("next_candidates", prompt)


if __name__ == "__main__":
    unittest.main()

"""Validation tests for the R3 Corpus v3 frontmatter schema.

The contract document is at:
  docs/worklogs/rag-r3-corpus-v3-contract.md

The JSON Schema lives at:
  tests/fixtures/r3_corpus_v3_schema.json

These tests verify:
1. The JSON Schema itself is valid (Draft 2020-12).
2. Pilot-required fields are enforced (schema_version, concept_id, doc_role,
   level, aliases, expected_queries).
3. Enum constraints (doc_role, level, language, intents, category).
4. Format constraints (concept_id pattern, mission_id pattern, paths).
5. Role-conditional invariants (symptoms required for symptom_router/playbook,
   mission_ids required for mission_bridge, confusable_with ≥ 2 for chooser).

Custom invariants like ``aliases ⊥ expected_queries`` (set disjointness) and
``category matches folder placement`` are out of pure JSON Schema's reach;
they live in scripts/learning/rag/corpus_lint.py:check_corpus_v3_pilot_frontmatter.
We test those at the lint level (in a separate test module once the lint
extension lands in Phase 5).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import jsonschema
from jsonschema.validators import Draft202012Validator


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "r3_corpus_v3_schema.json"


def _load_schema() -> dict:
    with SCHEMA_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _valid_minimal_pilot() -> dict:
    """The minimum frontmatter that must pass the v3 pilot schema."""
    return {
        "schema_version": 3,
        "concept_id": "spring/di",
        "doc_role": "primer",
        "level": "beginner",
        "aliases": ["DI", "dependency injection", "의존성 주입"],
        "expected_queries": ["처음 배우는데 DI가 뭐야?", "new 대신 주입받는 이유?"],
    }


def _valid_full_v3() -> dict:
    """Full v3 frontmatter with all 18 fields including Wave 2 + optional."""
    return {
        "schema_version": 3,
        "concept_id": "spring/di",
        "canonical": True,
        "category": "spring",
        "doc_role": "primer",
        "level": "beginner",
        "language": "ko",
        "source_priority": 90,
        "mission_ids": ["missions/roomescape", "missions/lotto"],
        "review_feedback_tags": ["di-vs-locator", "transactional-boundary"],
        "aliases": ["DI", "dependency injection", "의존성 주입", "주입"],
        "symptoms": ["구현체 어떻게 고르나요"],
        "intents": ["definition", "comparison", "design"],
        "prerequisites": ["language/java-interface"],
        "next_docs": ["spring/bean-container-lifecycle"],
        "linked_paths": ["contents/spring/spring-bean-di-basics.md"],
        "confusable_with": ["design-pattern/service-locator"],
        "forbidden_neighbors": [
            "contents/design-pattern/object-oriented-design-pattern-basics.md"
        ],
        "expected_queries": [
            "처음 배우는데 DI가 뭐야?",
            "new 대신 주입받는 이유?",
            "인터페이스로 주입하는 이유?",
        ],
        "contextual_chunk_prefix": (
            "이 문서는 Spring DI를 처음 배우는 학습자에게 의존성 주입의 의미와 "
            "객체 조립 방식을 설명한다."
        ),
    }


class SchemaValidityTest(unittest.TestCase):
    def test_schema_is_valid_draft_2020_12(self):
        """The schema document itself must be a valid Draft 2020-12 schema."""
        schema = _load_schema()
        # raises jsonschema.exceptions.SchemaError if invalid
        Draft202012Validator.check_schema(schema)

    def test_schema_has_required_top_level_keys(self):
        schema = _load_schema()
        self.assertEqual(schema.get("$schema"), "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema.get("type"), "object")
        self.assertIn("properties", schema)
        self.assertIn("required", schema)
        self.assertIn("allOf", schema)


class PilotRequiredFieldsTest(unittest.TestCase):
    def setUp(self):
        self.schema = _load_schema()
        self.validator = Draft202012Validator(self.schema)

    def test_minimal_pilot_passes(self):
        doc = _valid_minimal_pilot()
        errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
        self.assertEqual(errors, [], f"Expected no errors, got: {[e.message for e in errors]}")

    def test_missing_schema_version_fails(self):
        doc = _valid_minimal_pilot()
        del doc["schema_version"]
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(
            any("'schema_version' is a required property" in e.message for e in errors),
            f"Expected schema_version required error, got: {[e.message for e in errors]}",
        )

    def test_wrong_schema_version_fails(self):
        doc = _valid_minimal_pilot()
        doc["schema_version"] = 2  # v2 not allowed for v3 contract
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("3" in e.message for e in errors))

    def test_missing_concept_id_fails(self):
        doc = _valid_minimal_pilot()
        del doc["concept_id"]
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(
            any("'concept_id' is a required property" in e.message for e in errors)
        )

    def test_invalid_concept_id_format_fails(self):
        for bad in ["DI", "spring", "Spring/DI", "spring/", "/di", "spring//di"]:
            with self.subTest(concept_id=bad):
                doc = _valid_minimal_pilot()
                doc["concept_id"] = bad
                errors = list(self.validator.iter_errors(doc))
                self.assertTrue(
                    any("concept_id" in str(e.path) or "concept_id" in e.message
                        for e in errors),
                    f"Expected pattern error for {bad!r}, got: {[e.message for e in errors]}",
                )

    def test_missing_doc_role_fails(self):
        doc = _valid_minimal_pilot()
        del doc["doc_role"]
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("doc_role" in e.message for e in errors))

    def test_missing_aliases_fails(self):
        doc = _valid_minimal_pilot()
        del doc["aliases"]
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("aliases" in e.message for e in errors))

    def test_empty_aliases_fails(self):
        doc = _valid_minimal_pilot()
        doc["aliases"] = []
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("aliases" in str(e.path) for e in errors))

    def test_missing_expected_queries_fails(self):
        doc = _valid_minimal_pilot()
        del doc["expected_queries"]
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("expected_queries" in e.message for e in errors))


class EnumConstraintsTest(unittest.TestCase):
    def setUp(self):
        self.schema = _load_schema()
        self.validator = Draft202012Validator(self.schema)

    def test_doc_role_enum(self):
        valid_roles = [
            "primer", "bridge", "deep_dive", "playbook",
            "chooser", "symptom_router", "drill", "mission_bridge",
        ]
        for role in valid_roles:
            with self.subTest(role=role):
                doc = _valid_minimal_pilot()
                doc["doc_role"] = role
                if role == "symptom_router":
                    doc["symptoms"] = ["a", "b", "c"]
                elif role == "playbook":
                    doc["symptoms"] = ["a"]
                elif role == "mission_bridge":
                    doc["mission_ids"] = ["missions/roomescape"]
                elif role == "chooser":
                    doc["confusable_with"] = ["spring/di", "design-pattern/service-locator"]
                errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
                self.assertEqual(errors, [], f"role={role}: {[e.message for e in errors]}")

    def test_invalid_doc_role_fails(self):
        doc = _valid_minimal_pilot()
        doc["doc_role"] = "guide"  # not in enum
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("doc_role" in str(e.path) for e in errors))

    def test_level_enum(self):
        for level in ["beginner", "intermediate", "advanced"]:
            with self.subTest(level=level):
                doc = _valid_minimal_pilot()
                doc["level"] = level
                errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
                self.assertEqual(errors, [], f"level={level}: {[e.message for e in errors]}")

    def test_invalid_level_fails(self):
        doc = _valid_minimal_pilot()
        doc["level"] = "expert"  # not in enum
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("level" in str(e.path) for e in errors))

    def test_language_enum(self):
        for lang in ["ko", "en", "mixed"]:
            with self.subTest(language=lang):
                doc = _valid_minimal_pilot()
                doc["language"] = lang
                errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
                self.assertEqual(errors, [], f"lang={lang}: {[e.message for e in errors]}")

    def test_category_enum(self):
        for cat in [
            "algorithm", "data-structure", "database", "design-pattern",
            "language", "network", "operating-system", "security",
            "software-engineering", "spring", "system-design",
        ]:
            with self.subTest(category=cat):
                doc = _valid_minimal_pilot()
                doc["category"] = cat
                errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
                self.assertEqual(errors, [], f"cat={cat}: {[e.message for e in errors]}")

    def test_intents_enum(self):
        valid_intents = [
            "definition", "comparison", "symptom", "mission_bridge",
            "deep_dive", "drill", "design", "troubleshooting",
        ]
        for intent in valid_intents:
            with self.subTest(intent=intent):
                doc = _valid_minimal_pilot()
                doc["intents"] = [intent]
                errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
                self.assertEqual(errors, [], f"intent={intent}: {[e.message for e in errors]}")


class FormatConstraintsTest(unittest.TestCase):
    def setUp(self):
        self.schema = _load_schema()
        self.validator = Draft202012Validator(self.schema)

    def test_mission_id_pattern(self):
        for valid in ["missions/roomescape", "missions/shopping-cart", "missions/lotto"]:
            with self.subTest(mission_id=valid):
                doc = _valid_minimal_pilot()
                doc["mission_ids"] = [valid]
                errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
                self.assertEqual(errors, [], f"{valid}: {[e.message for e in errors]}")

    def test_invalid_mission_id_fails(self):
        for invalid in ["roomescape", "missions/", "missions/Cap", "Missions/lotto"]:
            with self.subTest(mission_id=invalid):
                doc = _valid_minimal_pilot()
                doc["mission_ids"] = [invalid]
                errors = list(self.validator.iter_errors(doc))
                self.assertTrue(
                    any("mission_ids" in str(e.path) for e in errors),
                    f"Expected error for {invalid}, got: {[e.message for e in errors]}",
                )

    def test_linked_path_pattern(self):
        valid = ["contents/spring/spring-di-primer.md", "contents/database/connection-pool-basics.md"]
        for v in valid:
            with self.subTest(path=v):
                doc = _valid_minimal_pilot()
                doc["linked_paths"] = [v]
                errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
                self.assertEqual(errors, [], f"{v}: {[e.message for e in errors]}")

    def test_invalid_linked_path_fails(self):
        for invalid in ["spring/di.md", "/contents/spring/x.md", "contents/", "x.md"]:
            with self.subTest(path=invalid):
                doc = _valid_minimal_pilot()
                doc["linked_paths"] = [invalid]
                errors = list(self.validator.iter_errors(doc))
                self.assertTrue(
                    any("linked_paths" in str(e.path) for e in errors),
                    f"Expected error for {invalid}, got: {[e.message for e in errors]}",
                )

    def test_source_priority_range(self):
        for valid in [0, 50, 90, 100]:
            with self.subTest(value=valid):
                doc = _valid_minimal_pilot()
                doc["source_priority"] = valid
                errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
                self.assertEqual(errors, [], f"{valid}: {[e.message for e in errors]}")

    def test_source_priority_out_of_range_fails(self):
        for invalid in [-1, 101, 200]:
            with self.subTest(value=invalid):
                doc = _valid_minimal_pilot()
                doc["source_priority"] = invalid
                errors = list(self.validator.iter_errors(doc))
                self.assertTrue(any("source_priority" in str(e.path) for e in errors))


class RoleConditionalRequirementsTest(unittest.TestCase):
    def setUp(self):
        self.schema = _load_schema()
        self.validator = Draft202012Validator(self.schema)

    def test_symptom_router_requires_symptoms(self):
        doc = _valid_minimal_pilot()
        doc["doc_role"] = "symptom_router"
        # no symptoms field
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(
            any("symptoms" in e.message for e in errors),
            f"Expected symptoms required for symptom_router, got: {[e.message for e in errors]}",
        )

    def test_symptom_router_minimum_3_symptoms(self):
        doc = _valid_minimal_pilot()
        doc["doc_role"] = "symptom_router"
        doc["symptoms"] = ["only-one"]  # insufficient
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(
            any("symptoms" in str(e.path) for e in errors),
            f"Expected symptom_router minItems=3 violation, got: {[e.message for e in errors]}",
        )

    def test_symptom_router_with_3_symptoms_passes(self):
        doc = _valid_minimal_pilot()
        doc["doc_role"] = "symptom_router"
        doc["symptoms"] = ["a", "b", "c"]
        errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
        self.assertEqual(errors, [])

    def test_playbook_requires_symptoms(self):
        doc = _valid_minimal_pilot()
        doc["doc_role"] = "playbook"
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("symptoms" in e.message for e in errors))

    def test_playbook_with_1_symptom_passes(self):
        doc = _valid_minimal_pilot()
        doc["doc_role"] = "playbook"
        doc["symptoms"] = ["one symptom"]
        errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
        self.assertEqual(errors, [])

    def test_mission_bridge_requires_mission_ids(self):
        doc = _valid_minimal_pilot()
        doc["doc_role"] = "mission_bridge"
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("mission_ids" in e.message for e in errors))

    def test_mission_bridge_with_mission_ids_passes(self):
        doc = _valid_minimal_pilot()
        doc["doc_role"] = "mission_bridge"
        doc["mission_ids"] = ["missions/roomescape"]
        errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
        self.assertEqual(errors, [])

    def test_chooser_requires_2_confusable_with(self):
        doc = _valid_minimal_pilot()
        doc["doc_role"] = "chooser"
        # no confusable_with at all
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("confusable_with" in e.message for e in errors))

    def test_chooser_with_1_confusable_fails(self):
        doc = _valid_minimal_pilot()
        doc["doc_role"] = "chooser"
        doc["confusable_with"] = ["only/one"]
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("confusable_with" in str(e.path) for e in errors))

    def test_chooser_with_2_confusable_passes(self):
        doc = _valid_minimal_pilot()
        doc["doc_role"] = "chooser"
        doc["confusable_with"] = ["spring/di", "design-pattern/service-locator"]
        errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
        self.assertEqual(errors, [], f"got: {[e.message for e in errors]}")


class FullV3FrontmatterTest(unittest.TestCase):
    def setUp(self):
        self.schema = _load_schema()
        self.validator = Draft202012Validator(self.schema)

    def test_full_v3_frontmatter_passes(self):
        doc = _valid_full_v3()
        errors = sorted(self.validator.iter_errors(doc), key=lambda e: e.path)
        self.assertEqual(errors, [], f"Full v3 should pass, got: {[e.message for e in errors]}")

    def test_unique_aliases_required(self):
        doc = _valid_full_v3()
        doc["aliases"] = ["DI", "DI", "duplicate"]  # not unique
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("aliases" in str(e.path) for e in errors))

    def test_unique_expected_queries_required(self):
        doc = _valid_full_v3()
        doc["expected_queries"] = ["x?", "x?"]
        errors = list(self.validator.iter_errors(doc))
        self.assertTrue(any("expected_queries" in str(e.path) for e in errors))


if __name__ == "__main__":
    unittest.main()

"""Validation tests for the R3 Real qrel suite schema.

Schema lives at tests/fixtures/r3_qrels_schema.json.
Companion docs: docs/worklogs/rag-r3-system-spec-v1.md §8 and
                docs/worklogs/rag-r3-corpus-v3-contract.md.

These tests verify:
1. The JSON Schema itself is valid (Draft 2020-12).
2. Required per-query fields enforced.
3. Cohort-conditional invariants:
   - mission_bridge requires mission_id
   - corpus_gap_probe requires primary_paths == [] (the test for "not in corpus")
   - forbidden_neighbor requires forbidden_paths ≥ 1
   - all other cohorts require primary_paths ≥ 1
4. Enum and format constraints (cohort_tag, language, level, intent, paths,
   concept_id pattern, mission_id pattern).
5. The actual seed fixture (r3_qrels_real_v0_seed.json) parses against the
   schema.
6. Set-disjointness of primary_paths / acceptable_paths / forbidden_paths
   (enforced by Python validator, since pure JSON Schema cannot express set
   disjoint constraints).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema.validators import Draft202012Validator


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "r3_qrels_schema.json"
SEED_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "r3_qrels_real_v0_seed.json"
)


def _load_schema() -> dict:
    with SCHEMA_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _valid_minimal_query(cohort: str = "paraphrase_human") -> dict:
    return {
        "query_id": f"{cohort}:spring_di:1",
        "prompt": "처음 배우는데 DI가 뭐야?",
        "language": "ko",
        "level": "beginner",
        "cohort_tag": cohort,
        "primary_paths": ["contents/spring/spring-di-primer.md"],
        "expected_concepts": ["spring/di"],
    }


def _valid_minimal_fixture() -> dict:
    return {
        "schema_version": 1,
        "fixture_id": "r3_real_test",
        "queries": [_valid_minimal_query()],
    }


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_schema())


def _validate_set_disjoint(query: dict) -> list[str]:
    """Custom invariant: primary / acceptable / forbidden are pairwise disjoint."""
    primary = set(query.get("primary_paths", []))
    acceptable = set(query.get("acceptable_paths", []))
    forbidden = set(query.get("forbidden_paths", []))
    issues: list[str] = []
    pa = primary & acceptable
    pf = primary & forbidden
    af = acceptable & forbidden
    if pa:
        issues.append(f"primary_paths and acceptable_paths overlap: {pa}")
    if pf:
        issues.append(f"primary_paths and forbidden_paths overlap: {pf}")
    if af:
        issues.append(f"acceptable_paths and forbidden_paths overlap: {af}")
    return issues


class SchemaValidityTest(unittest.TestCase):
    def test_schema_is_valid_draft_2020_12(self):
        Draft202012Validator.check_schema(_load_schema())

    def test_schema_top_level_keys(self):
        schema = _load_schema()
        self.assertEqual(
            schema.get("$schema"),
            "https://json-schema.org/draft/2020-12/schema",
        )
        self.assertEqual(schema.get("type"), "object")
        self.assertIn("queries", schema["properties"])
        self.assertIn("query", schema["$defs"])


class FixtureLevelTest(unittest.TestCase):
    def setUp(self):
        self.validator = _validator()

    def test_minimal_fixture_passes(self):
        fixture = _valid_minimal_fixture()
        errors = sorted(self.validator.iter_errors(fixture), key=lambda e: e.path)
        self.assertEqual(errors, [], [e.message for e in errors])

    def test_missing_schema_version_fails(self):
        fixture = _valid_minimal_fixture()
        del fixture["schema_version"]
        errors = list(self.validator.iter_errors(fixture))
        self.assertTrue(any("schema_version" in e.message for e in errors))

    def test_wrong_schema_version_fails(self):
        fixture = _valid_minimal_fixture()
        fixture["schema_version"] = 2
        errors = list(self.validator.iter_errors(fixture))
        self.assertTrue(any("1" in e.message for e in errors))

    def test_empty_queries_array_fails(self):
        fixture = _valid_minimal_fixture()
        fixture["queries"] = []
        errors = list(self.validator.iter_errors(fixture))
        self.assertTrue(any("queries" in str(e.path) or "minItems" in e.message
                            for e in errors))

    def test_query_count_field_passes_schema(self):
        fixture = _valid_minimal_fixture()
        fixture["query_count"] = 1
        errors = sorted(self.validator.iter_errors(fixture), key=lambda e: e.path)
        self.assertEqual(errors, [], [e.message for e in errors])

    def test_unknown_fixture_field_fails(self):
        fixture = _valid_minimal_fixture()
        fixture["unknown_field"] = "x"
        errors = list(self.validator.iter_errors(fixture))
        self.assertTrue(any("additionalProperties" in e.message or
                            "unknown_field" in e.message for e in errors))

    def test_authoring_method_enum(self):
        fixture = _valid_minimal_fixture()
        for method in ["human_only", "ai_first_human_review",
                       "ai_first_ai_review", "auto_from_expected_queries"]:
            with self.subTest(method=method):
                fixture["authoring_method"] = method
                errors = sorted(self.validator.iter_errors(fixture),
                                key=lambda e: e.path)
                self.assertEqual(errors, [], [e.message for e in errors])

    def test_invalid_authoring_method_fails(self):
        fixture = _valid_minimal_fixture()
        fixture["authoring_method"] = "magic"
        errors = list(self.validator.iter_errors(fixture))
        self.assertTrue(any("authoring_method" in str(e.path) for e in errors))


class RequiredFieldsTest(unittest.TestCase):
    def setUp(self):
        self.validator = _validator()

    def _wrap(self, query: dict) -> dict:
        return {"schema_version": 1, "queries": [query]}

    def test_minimal_query_passes(self):
        fixture = self._wrap(_valid_minimal_query())
        errors = sorted(self.validator.iter_errors(fixture), key=lambda e: e.path)
        self.assertEqual(errors, [], [e.message for e in errors])

    def test_missing_query_id_fails(self):
        q = _valid_minimal_query()
        del q["query_id"]
        errors = list(self.validator.iter_errors(self._wrap(q)))
        self.assertTrue(any("query_id" in e.message for e in errors))

    def test_missing_prompt_fails(self):
        q = _valid_minimal_query()
        del q["prompt"]
        errors = list(self.validator.iter_errors(self._wrap(q)))
        self.assertTrue(any("prompt" in e.message for e in errors))

    def test_missing_primary_paths_for_paraphrase_fails(self):
        q = _valid_minimal_query("paraphrase_human")
        del q["primary_paths"]
        errors = list(self.validator.iter_errors(self._wrap(q)))
        self.assertTrue(any("primary_paths" in e.message for e in errors))

    def test_empty_expected_concepts_fails(self):
        q = _valid_minimal_query()
        q["expected_concepts"] = []
        errors = list(self.validator.iter_errors(self._wrap(q)))
        self.assertTrue(any("expected_concepts" in str(e.path) for e in errors))


class CohortConditionalsTest(unittest.TestCase):
    def setUp(self):
        self.validator = _validator()

    def _wrap(self, query: dict) -> dict:
        return {"schema_version": 1, "queries": [query]}

    def test_mission_bridge_requires_mission_id(self):
        q = _valid_minimal_query("mission_bridge")
        # no mission_id
        errors = list(self.validator.iter_errors(self._wrap(q)))
        self.assertTrue(
            any("mission_id" in e.message for e in errors),
            f"Expected mission_id required, got: {[e.message for e in errors]}",
        )

    def test_mission_bridge_with_mission_id_passes(self):
        q = _valid_minimal_query("mission_bridge")
        q["mission_id"] = "missions/roomescape"
        errors = sorted(self.validator.iter_errors(self._wrap(q)),
                        key=lambda e: e.path)
        self.assertEqual(errors, [], [e.message for e in errors])

    def test_corpus_gap_probe_with_primary_paths_fails(self):
        q = _valid_minimal_query("corpus_gap_probe")
        # corpus_gap_probe must have empty primary_paths
        # _valid_minimal_query gave it a primary path; verify this fails
        errors = list(self.validator.iter_errors(self._wrap(q)))
        self.assertTrue(
            any("primary_paths" in str(e.path) for e in errors),
            f"corpus_gap_probe should reject non-empty primary_paths, got: "
            f"{[e.message for e in errors]}",
        )

    def test_corpus_gap_probe_with_empty_primary_paths_passes(self):
        q = _valid_minimal_query("corpus_gap_probe")
        q["primary_paths"] = []
        # primary_paths is required (in $defs) but corpus_gap_probe sets maxItems=0
        # which is satisfied by empty list
        errors = sorted(self.validator.iter_errors(self._wrap(q)),
                        key=lambda e: e.path)
        self.assertEqual(errors, [], [e.message for e in errors])

    def test_forbidden_neighbor_requires_forbidden_paths(self):
        q = _valid_minimal_query("forbidden_neighbor")
        # no forbidden_paths
        errors = list(self.validator.iter_errors(self._wrap(q)))
        self.assertTrue(
            any("forbidden_paths" in e.message for e in errors),
            f"forbidden_neighbor must require forbidden_paths, got: "
            f"{[e.message for e in errors]}",
        )

    def test_forbidden_neighbor_with_forbidden_paths_passes(self):
        q = _valid_minimal_query("forbidden_neighbor")
        q["forbidden_paths"] = [
            "contents/design-pattern/object-oriented-design-pattern-basics.md"
        ]
        errors = sorted(self.validator.iter_errors(self._wrap(q)),
                        key=lambda e: e.path)
        self.assertEqual(errors, [], [e.message for e in errors])


class FormatAndEnumTest(unittest.TestCase):
    def setUp(self):
        self.validator = _validator()

    def _wrap(self, query: dict) -> dict:
        return {"schema_version": 1, "queries": [query]}

    def test_cohort_tag_enum(self):
        cohorts = [
            "paraphrase_human", "confusable_pairs", "symptom_to_cause",
            "mission_bridge", "corpus_gap_probe", "forbidden_neighbor",
        ]
        for c in cohorts:
            with self.subTest(cohort=c):
                q = _valid_minimal_query(c)
                if c == "mission_bridge":
                    q["mission_id"] = "missions/roomescape"
                if c == "corpus_gap_probe":
                    q["primary_paths"] = []
                if c == "forbidden_neighbor":
                    q["forbidden_paths"] = ["contents/spring/x.md"]
                errors = sorted(self.validator.iter_errors(self._wrap(q)),
                                key=lambda e: e.path)
                self.assertEqual(errors, [], f"{c}: {[e.message for e in errors]}")

    def test_invalid_cohort_tag_fails(self):
        q = _valid_minimal_query()
        q["cohort_tag"] = "unknown_cohort"
        errors = list(self.validator.iter_errors(self._wrap(q)))
        self.assertTrue(any("cohort_tag" in str(e.path) for e in errors))

    def test_language_enum(self):
        for lang in ["ko", "en", "mixed"]:
            with self.subTest(language=lang):
                q = _valid_minimal_query()
                q["language"] = lang
                errors = sorted(self.validator.iter_errors(self._wrap(q)),
                                key=lambda e: e.path)
                self.assertEqual(errors, [], [e.message for e in errors])

    def test_invalid_language_fails(self):
        q = _valid_minimal_query()
        q["language"] = "ja"
        errors = list(self.validator.iter_errors(self._wrap(q)))
        self.assertTrue(any("language" in str(e.path) for e in errors))

    def test_intent_enum(self):
        for intent in [
            "definition", "comparison", "symptom",
            "mission_bridge", "deep_dive", "drill",
        ]:
            with self.subTest(intent=intent):
                q = _valid_minimal_query()
                q["intent"] = intent
                errors = sorted(self.validator.iter_errors(self._wrap(q)),
                                key=lambda e: e.path)
                self.assertEqual(errors, [], [e.message for e in errors])

    def test_path_pattern(self):
        q = _valid_minimal_query()
        for invalid_path in [
            "spring/x.md",
            "/contents/spring/x.md",
            "contents/Spring/x.md",  # uppercase category
            "contents/x.md",  # missing category subfolder
        ]:
            with self.subTest(path=invalid_path):
                q["primary_paths"] = [invalid_path]
                errors = list(self.validator.iter_errors(self._wrap(q)))
                self.assertTrue(
                    any("primary_paths" in str(e.path) for e in errors),
                    f"Expected pattern violation for {invalid_path}, "
                    f"got: {[e.message for e in errors]}",
                )

    def test_query_id_pattern(self):
        q = _valid_minimal_query()
        # Allowed: lowercase letters, digits, dash, underscore, colon, slash, dot
        for valid in [
            "paraphrase:spring/di:1",
            "confusable_pairs:di-vs-locator:002",
            "corpus_gap.probe.001",
        ]:
            with self.subTest(query_id=valid):
                q["query_id"] = valid
                errors = sorted(self.validator.iter_errors(self._wrap(q)),
                                key=lambda e: e.path)
                self.assertEqual(errors, [], [e.message for e in errors])

    def test_invalid_query_id_pattern_fails(self):
        q = _valid_minimal_query()
        for invalid in ["UPPERCASE", "with space", "한국어", "comma,here"]:
            with self.subTest(query_id=invalid):
                q["query_id"] = invalid
                errors = list(self.validator.iter_errors(self._wrap(q)))
                self.assertTrue(
                    any("query_id" in str(e.path) for e in errors),
                    f"Expected pattern violation for {invalid}, "
                    f"got: {[e.message for e in errors]}",
                )


class CustomDisjointInvariantTest(unittest.TestCase):
    """Custom invariant: primary / acceptable / forbidden are pairwise disjoint.
    Pure JSON Schema cannot express set disjointness; we run this as a
    Python-level check.
    """

    def test_disjoint_passes_when_all_different(self):
        q = _valid_minimal_query()
        q["primary_paths"] = ["contents/spring/a.md"]
        q["acceptable_paths"] = ["contents/spring/b.md"]
        q["forbidden_paths"] = ["contents/spring/c.md"]
        self.assertEqual(_validate_set_disjoint(q), [])

    def test_primary_acceptable_overlap_caught(self):
        q = _valid_minimal_query()
        q["primary_paths"] = ["contents/spring/a.md"]
        q["acceptable_paths"] = ["contents/spring/a.md"]
        issues = _validate_set_disjoint(q)
        self.assertTrue(any("primary_paths and acceptable_paths overlap" in i
                            for i in issues))

    def test_primary_forbidden_overlap_caught(self):
        q = _valid_minimal_query()
        q["primary_paths"] = ["contents/spring/a.md"]
        q["forbidden_paths"] = ["contents/spring/a.md"]
        issues = _validate_set_disjoint(q)
        self.assertTrue(any("primary_paths and forbidden_paths overlap" in i
                            for i in issues))

    def test_acceptable_forbidden_overlap_caught(self):
        q = _valid_minimal_query()
        q["acceptable_paths"] = ["contents/spring/a.md"]
        q["forbidden_paths"] = ["contents/spring/a.md"]
        issues = _validate_set_disjoint(q)
        self.assertTrue(any("acceptable_paths and forbidden_paths overlap" in i
                            for i in issues))


class SeedFixtureValidationTest(unittest.TestCase):
    """Validate the actual seed fixture file against the schema.

    The seed fixture (r3_qrels_real_v0_seed.json) is the small starting
    set of qrels (~40-50 queries across 6 cohorts) used to validate the
    schema and serve as a Phase 4 starting point.
    """

    def setUp(self):
        self.validator = _validator()

    def test_seed_fixture_exists(self):
        self.assertTrue(
            SEED_FIXTURE_PATH.exists(),
            f"Seed fixture missing: {SEED_FIXTURE_PATH}",
        )

    def test_seed_fixture_passes_schema(self):
        if not SEED_FIXTURE_PATH.exists():
            self.skipTest("seed fixture not yet authored")
        with SEED_FIXTURE_PATH.open("r", encoding="utf-8") as fh:
            fixture = json.load(fh)
        errors = sorted(self.validator.iter_errors(fixture), key=lambda e: e.path)
        self.assertEqual(
            errors,
            [],
            f"Seed fixture failed schema: {[e.message for e in errors]}",
        )

    def test_seed_fixture_set_disjoint(self):
        if not SEED_FIXTURE_PATH.exists():
            self.skipTest("seed fixture not yet authored")
        with SEED_FIXTURE_PATH.open("r", encoding="utf-8") as fh:
            fixture = json.load(fh)
        for q in fixture.get("queries", []):
            with self.subTest(query_id=q.get("query_id")):
                issues = _validate_set_disjoint(q)
                self.assertEqual(issues, [], f"Disjoint violation: {issues}")

    def test_seed_fixture_unique_query_ids(self):
        if not SEED_FIXTURE_PATH.exists():
            self.skipTest("seed fixture not yet authored")
        with SEED_FIXTURE_PATH.open("r", encoding="utf-8") as fh:
            fixture = json.load(fh)
        ids = [q["query_id"] for q in fixture.get("queries", [])]
        duplicates = {x for x in ids if ids.count(x) > 1}
        self.assertEqual(duplicates, set(), f"Duplicate query_ids: {duplicates}")

    def test_seed_fixture_cohort_distribution(self):
        """Seed fixture must have at least 1 query in every cohort."""
        if not SEED_FIXTURE_PATH.exists():
            self.skipTest("seed fixture not yet authored")
        with SEED_FIXTURE_PATH.open("r", encoding="utf-8") as fh:
            fixture = json.load(fh)
        cohorts = {q["cohort_tag"] for q in fixture.get("queries", [])}
        expected = {
            "paraphrase_human", "confusable_pairs", "symptom_to_cause",
            "mission_bridge", "corpus_gap_probe", "forbidden_neighbor",
        }
        missing = expected - cohorts
        self.assertEqual(missing, set(),
                         f"Seed fixture missing cohorts: {missing}")


if __name__ == "__main__":
    unittest.main()

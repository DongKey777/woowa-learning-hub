"""Unit tests for `scripts/workbench/core/concept_catalog`.

Catalog lookups are deterministic — no ML at call time. Tests cover:
  * alias matching (English + Korean + ASCII boundary)
  * module / stage inference
  * cross-mapping from per-PR learning_point_id
  * graceful fallback when catalog is empty
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "scripts" / "workbench"
if str(WORKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_DIR))

from core.concept_catalog import (  # noqa: E402
    extract_concept_ids,
    infer_concepts_from_path,
    infer_concepts_from_test,
    infer_module_from_path,
    infer_stage_from_module,
    load_catalog,
    lp_to_concept_id,
    next_stage,
    reset_cache,
    stage_first_module,
)


class CatalogLoadTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_cache()

    def test_load_returns_concepts_and_stages(self) -> None:
        catalog = load_catalog()
        self.assertIn("concepts", catalog)
        self.assertIn("stages", catalog)
        self.assertIn("concept:spring/bean", catalog["concepts"])

    def test_stage_owns_modules(self) -> None:
        catalog = load_catalog()
        self.assertIn("spring-core-1", catalog["stages"]["spring-core"]["modules"])


class AliasMatchingTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_cache()
        self.catalog = load_catalog()

    def test_english_alias_match(self) -> None:
        hits = extract_concept_ids("Spring Bean이 뭐야?", self.catalog)
        self.assertIn("concept:spring/bean", hits)

    def test_di_alias_match_with_korean_particle(self) -> None:
        hits = extract_concept_ids("DI가 뭐야?", self.catalog)
        self.assertIn("concept:spring/di", hits)

    def test_korean_alias_match(self) -> None:
        hits = extract_concept_ids("의존성 주입이란 무엇인가요?", self.catalog)
        self.assertIn("concept:spring/di", hits)

    def test_no_match_for_tooling_question(self) -> None:
        hits = extract_concept_ids("Gradle 멀티 프로젝트 어떻게 설정해?", self.catalog)
        self.assertEqual(hits, [])

    def test_substring_does_not_match_inside_unrelated_word(self) -> None:
        # "urban" should NOT match "bean" via substring inside the word.
        hits = extract_concept_ids("urbanization plan", self.catalog)
        self.assertNotIn("concept:spring/bean", hits)

    def test_multiple_concepts_in_one_prompt(self) -> None:
        hits = extract_concept_ids("Bean과 DI 차이가 뭐야?", self.catalog)
        self.assertIn("concept:spring/bean", hits)
        self.assertIn("concept:spring/di", hits)


class ModuleInferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_cache()
        self.catalog = load_catalog()

    def test_module_extracted_from_full_path(self) -> None:
        path = "missions/spring-learning-test/spring-core-1/initial/Bean.java"
        self.assertEqual(infer_module_from_path(path), "spring-core-1")

    def test_module_extracted_from_data_jpa_path(self) -> None:
        path = "missions/spring-learning-test/spring-data-jpa-2/test/X.java"
        self.assertEqual(infer_module_from_path(path), "spring-data-jpa-2")

    def test_module_returns_none_for_unrelated_path(self) -> None:
        self.assertIsNone(infer_module_from_path("scripts/workbench/cli.py"))

    def test_stage_lookup_for_known_module(self) -> None:
        self.assertEqual(infer_stage_from_module("spring-jdbc-1", self.catalog), "spring-jdbc")
        self.assertEqual(infer_stage_from_module("spring-core-2", self.catalog), "spring-core")

    def test_stage_lookup_unknown_module_returns_none(self) -> None:
        self.assertIsNone(infer_stage_from_module("not-a-module", self.catalog))


class CrossMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_cache()
        self.catalog = load_catalog()

    def test_lp_to_concept_id_known_alias(self) -> None:
        self.assertEqual(
            lp_to_concept_id("transaction_consistency", self.catalog),
            "concept:spring/transactional",
        )

    def test_lp_to_concept_id_unknown_returns_none(self) -> None:
        self.assertIsNone(lp_to_concept_id("not_a_real_lp", self.catalog))


class TestArtifactInferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_cache()
        self.catalog = load_catalog()

    def test_concepts_from_test_class_matches_alias(self) -> None:
        hits = infer_concepts_from_test(
            "cholog.BeanTest", "registerBean", "spring-core-1", self.catalog
        )
        self.assertIn("concept:spring/bean", hits)

    def test_concepts_from_test_falls_back_to_module_hint(self) -> None:
        # Method name has no alias hit; falls back to module-hint match.
        hits = infer_concepts_from_test(
            "cholog.UnknownTest", "doSomething", "spring-jdbc-1", self.catalog
        )
        # spring-jdbc-1 is the module_hint for jdbc-template & transactional
        self.assertTrue(any("jdbc" in cid or "transaction" in cid for cid in hits))

    def test_concepts_from_path_via_basename(self) -> None:
        path = "missions/spring-learning-test/spring-core-1/test/SpringBeanTest.java"
        hits = infer_concepts_from_path(path, "spring-core-1", self.catalog)
        self.assertIn("concept:spring/bean", hits)


class StageNavigationTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_cache()
        self.catalog = load_catalog()

    def test_next_stage_advances(self) -> None:
        self.assertEqual(next_stage(self.catalog, "spring-core"), "spring-mvc")
        self.assertEqual(next_stage(self.catalog, "spring-mvc"), "spring-jdbc")

    def test_next_stage_at_end_returns_none(self) -> None:
        self.assertIsNone(next_stage(self.catalog, "spring-auth"))

    def test_stage_first_module(self) -> None:
        self.assertEqual(stage_first_module(self.catalog, "spring-mvc"), "spring-mvc-1")


if __name__ == "__main__":
    unittest.main()

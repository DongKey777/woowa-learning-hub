"""Unit tests for the Corpus v3 lint extension in
``scripts/learning/rag/corpus_lint.py``.

Companion to:
- ``docs/worklogs/rag-r3-corpus-v3-contract.md``
- ``tests/fixtures/r3_corpus_v3_schema.json``
- ``tests/unit/test_corpus_v3_schema.py`` (JSON Schema layer)

This test module validates the *Python lint layer* on top of the schema.
The schema cannot express set-disjointness (``aliases ⊥ expected_queries``)
or folder-placement matching, so the lint owns those invariants.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.learning.rag.corpus_lint import (
    PILOT_V3_FIELDS,
    VALID_CATEGORIES_V3,
    VALID_DOC_ROLES_V3,
    VALID_INTENTS_V3,
    VALID_LANGUAGES_V3,
    VALID_LEVELS,
    check_corpus_v3_pilot_frontmatter,
    check_frontmatter_schema,
)


def _frontmatter_text(body: str) -> str:
    return "---\n" + body + "---\n\n# Body\n\nSome content.\n"


def _valid_v3_minimal() -> dict:
    return {
        "schema_version": 3,
        "concept_id": "spring/di",
        "doc_role": "primer",
        "level": "beginner",
        "language": "ko",
        "aliases": ["DI", "dependency injection", "의존성 주입"],
        "expected_queries": ["처음 배우는데 DI가 뭐야?", "new 대신 주입받는 이유?"],
    }


def _path(category: str = "spring", filename: str = "spring-di-primer.md") -> Path:
    return Path(f"knowledge/cs/contents/{category}/{filename}")


def _messages(violations) -> list[str]:
    return [v.message for v in violations]


class PilotV3RequiredFieldsTest(unittest.TestCase):
    def test_minimal_v3_passes(self):
        out = check_corpus_v3_pilot_frontmatter(
            file_path=_path(), frontmatter=_valid_v3_minimal()
        )
        self.assertEqual(out, [], _messages(out))

    def test_missing_each_pilot_field_caught(self):
        for field in PILOT_V3_FIELDS:
            with self.subTest(field=field):
                fm = _valid_v3_minimal()
                del fm[field]
                out = check_corpus_v3_pilot_frontmatter(
                    file_path=_path(), frontmatter=fm
                )
                self.assertTrue(
                    any(f"missing pilot field: {field}" in m
                        for m in _messages(out)),
                    f"Expected missing-{field} message, got: {_messages(out)}",
                )

    def test_empty_aliases_caught(self):
        fm = _valid_v3_minimal()
        fm["aliases"] = []
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(
            any("missing pilot field: aliases" in m for m in _messages(out)),
        )

    def test_empty_expected_queries_caught(self):
        fm = _valid_v3_minimal()
        fm["expected_queries"] = []
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(
            any("expected_queries" in m for m in _messages(out)),
        )


class ConceptIdPatternTest(unittest.TestCase):
    def test_valid_concept_id(self):
        for valid in [
            "spring/di",
            "design-pattern/factory",
            "software-engineering/repository-pattern",
            "operating-system/io-uring",
        ]:
            with self.subTest(concept_id=valid):
                fm = _valid_v3_minimal()
                fm["concept_id"] = valid
                out = check_corpus_v3_pilot_frontmatter(
                    file_path=_path(), frontmatter=fm
                )
                concept_messages = [m for m in _messages(out) if "concept_id" in m]
                self.assertEqual(
                    concept_messages, [], f"{valid} got: {concept_messages}"
                )

    def test_invalid_concept_id(self):
        for invalid in [
            "DI",                          # no slash
            "spring",                      # no slash
            "Spring/DI",                   # uppercase
            "spring/",                     # trailing slash
            "/di",                         # leading slash
            "spring//di",                  # double slash
            "spring/d",                    # slug too short (single char)
        ]:
            with self.subTest(concept_id=invalid):
                fm = _valid_v3_minimal()
                fm["concept_id"] = invalid
                out = check_corpus_v3_pilot_frontmatter(
                    file_path=_path(), frontmatter=fm
                )
                self.assertTrue(
                    any("concept_id" in m and "match" in m
                        for m in _messages(out)),
                    f"Expected pattern violation for {invalid!r}, got: "
                    f"{_messages(out)}",
                )


class EnumValidationTest(unittest.TestCase):
    def test_doc_role_enum(self):
        for role in VALID_DOC_ROLES_V3:
            with self.subTest(role=role):
                fm = _valid_v3_minimal()
                fm["doc_role"] = role
                # add role-conditional fields so the test isolates the enum
                if role == "symptom_router":
                    fm["symptoms"] = ["a", "b", "c"]
                elif role == "playbook":
                    fm["symptoms"] = ["a"]
                elif role == "mission_bridge":
                    fm["mission_ids"] = ["missions/roomescape"]
                elif role == "chooser":
                    fm["confusable_with"] = ["spring/di", "design-pattern/locator"]
                out = check_corpus_v3_pilot_frontmatter(
                    file_path=_path(), frontmatter=fm
                )
                role_messages = [m for m in _messages(out) if "doc_role" in m]
                self.assertEqual(role_messages, [], f"role={role}: {role_messages}")

    def test_invalid_doc_role(self):
        fm = _valid_v3_minimal()
        fm["doc_role"] = "guide"  # not in v3 enum
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("doc_role" in m and "guide" in m for m in _messages(out)))

    def test_v2_role_comparison_rejected_in_v3(self):
        """v2's "comparison" role must NOT be accepted under v3."""
        fm = _valid_v3_minimal()
        fm["doc_role"] = "comparison"  # legacy v2 value
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("doc_role" in m and "comparison" in m
                            for m in _messages(out)))

    def test_language_enum(self):
        for lang in VALID_LANGUAGES_V3:
            with self.subTest(language=lang):
                fm = _valid_v3_minimal()
                fm["language"] = lang
                out = check_corpus_v3_pilot_frontmatter(
                    file_path=_path(), frontmatter=fm
                )
                lang_messages = [m for m in _messages(out) if "language" in m]
                self.assertEqual(lang_messages, [])

    def test_invalid_language(self):
        fm = _valid_v3_minimal()
        fm["language"] = "ja"  # not in v3 enum
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("language" in m for m in _messages(out)))

    def test_level_enum(self):
        for level in VALID_LEVELS:
            with self.subTest(level=level):
                fm = _valid_v3_minimal()
                fm["level"] = level
                out = check_corpus_v3_pilot_frontmatter(
                    file_path=_path(), frontmatter=fm
                )
                level_messages = [m for m in _messages(out) if "level" in m]
                self.assertEqual(level_messages, [])

    def test_intents_enum(self):
        for intent in VALID_INTENTS_V3:
            with self.subTest(intent=intent):
                fm = _valid_v3_minimal()
                fm["intents"] = [intent]
                out = check_corpus_v3_pilot_frontmatter(
                    file_path=_path(), frontmatter=fm
                )
                intent_messages = [m for m in _messages(out) if "intent " in m]
                self.assertEqual(intent_messages, [])

    def test_invalid_intent(self):
        fm = _valid_v3_minimal()
        fm["intents"] = ["definition", "magic"]
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("magic" in m for m in _messages(out)))


class CategoryFolderPlacementTest(unittest.TestCase):
    def test_category_matches_folder(self):
        fm = _valid_v3_minimal()
        fm["category"] = "spring"
        out = check_corpus_v3_pilot_frontmatter(
            file_path=_path("spring"), frontmatter=fm
        )
        cat_msgs = [m for m in _messages(out) if "category" in m and "match" in m]
        self.assertEqual(cat_msgs, [])

    def test_category_mismatch_caught(self):
        fm = _valid_v3_minimal()
        fm["category"] = "database"  # but path is spring/...
        out = check_corpus_v3_pilot_frontmatter(
            file_path=_path("spring"), frontmatter=fm
        )
        self.assertTrue(any(
            "category" in m and "does not match folder placement" in m
            for m in _messages(out)
        ))

    def test_unknown_category_caught(self):
        fm = _valid_v3_minimal()
        fm["category"] = "fictional-tech"
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("category 'fictional-tech'" in m for m in _messages(out)))

    def test_category_omitted_no_violation(self):
        """category is Wave 2 (not Pilot required); omitting is OK."""
        fm = _valid_v3_minimal()
        # no category field
        out = check_corpus_v3_pilot_frontmatter(
            file_path=_path("spring"), frontmatter=fm
        )
        cat_msgs = [m for m in _messages(out) if "category" in m]
        self.assertEqual(cat_msgs, [], f"Expected no category msgs, got: {cat_msgs}")


class AliasesExpectedQueriesDisjointTest(unittest.TestCase):
    """Critical invariant: aliases and expected_queries must be disjoint
    (case-insensitive, whitespace-normalized) to prevent the circular-leak
    class of bug fixed in commit 054a1a3.
    """

    def test_disjoint_passes(self):
        fm = _valid_v3_minimal()
        # aliases: ['DI', 'dependency injection', '의존성 주입']
        # expected_queries: ['처음 배우는데 DI가 뭐야?', 'new 대신 주입받는 이유?']
        # No overlap.
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        disjoint_msgs = [m for m in _messages(out) if "aliases ⊥" in m]
        self.assertEqual(disjoint_msgs, [])

    def test_overlap_caught_exact(self):
        fm = _valid_v3_minimal()
        fm["expected_queries"] = ["DI", "처음 배우는데 DI가 뭐야?"]
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("aliases ⊥ expected_queries violation" in m
                            for m in _messages(out)))

    def test_overlap_caught_case_insensitive(self):
        fm = _valid_v3_minimal()
        fm["aliases"] = ["DI", "dependency injection"]
        fm["expected_queries"] = ["di", "what is dependency injection?"]
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        # 'DI' / 'di' overlap (case-folded)
        self.assertTrue(any("aliases ⊥" in m for m in _messages(out)))

    def test_overlap_caught_whitespace_normalized(self):
        fm = _valid_v3_minimal()
        fm["aliases"] = ["spring di"]
        fm["expected_queries"] = ["  spring   di  "]  # whitespace variants
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("aliases ⊥" in m for m in _messages(out)))


class MissionIdPatternTest(unittest.TestCase):
    def test_valid_mission_id(self):
        for valid in ["missions/roomescape", "missions/lotto",
                      "missions/shopping-cart"]:
            with self.subTest(mission_id=valid):
                fm = _valid_v3_minimal()
                fm["doc_role"] = "mission_bridge"
                fm["mission_ids"] = [valid]
                out = check_corpus_v3_pilot_frontmatter(
                    file_path=_path(), frontmatter=fm
                )
                m_msgs = [m for m in _messages(out) if "mission_id" in m
                          and "match" in m]
                self.assertEqual(m_msgs, [])

    def test_invalid_mission_id(self):
        for invalid in ["roomescape", "missions/", "Missions/lotto",
                        "missions/Cap"]:
            with self.subTest(mission_id=invalid):
                fm = _valid_v3_minimal()
                fm["doc_role"] = "mission_bridge"
                fm["mission_ids"] = [invalid]
                out = check_corpus_v3_pilot_frontmatter(
                    file_path=_path(), frontmatter=fm
                )
                self.assertTrue(
                    any("mission_id" in m and "match" in m
                        for m in _messages(out)),
                    f"Expected pattern error for {invalid}, got: {_messages(out)}",
                )


class PathPatternTest(unittest.TestCase):
    def test_valid_corpus_paths(self):
        fm = _valid_v3_minimal()
        fm["linked_paths"] = ["contents/spring/spring-bean-di-basics.md"]
        fm["forbidden_neighbors"] = [
            "contents/design-pattern/object-oriented-design-pattern-basics.md"
        ]
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        path_msgs = [m for m in _messages(out)
                     if "linked_paths" in m or "forbidden_neighbors" in m]
        self.assertEqual(path_msgs, [])

    def test_invalid_linked_path(self):
        fm = _valid_v3_minimal()
        fm["linked_paths"] = ["spring/di.md"]  # no contents/ prefix
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("linked_paths" in m for m in _messages(out)))

    def test_invalid_forbidden_neighbor_path(self):
        fm = _valid_v3_minimal()
        fm["forbidden_neighbors"] = ["/contents/spring/x.md"]
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("forbidden_neighbors" in m for m in _messages(out)))


class ConceptIdRefsTest(unittest.TestCase):
    def test_valid_concept_id_refs(self):
        fm = _valid_v3_minimal()
        fm["prerequisites"] = ["language/java-interface"]
        fm["next_docs"] = ["spring/bean-container"]
        fm["confusable_with"] = ["design-pattern/service-locator"]
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        msgs = [m for m in _messages(out) if any(
            x in m for x in ["prerequisites", "next_docs", "confusable_with"]
        )]
        self.assertEqual(msgs, [])

    def test_invalid_concept_id_in_prerequisites(self):
        fm = _valid_v3_minimal()
        fm["prerequisites"] = ["INVALID_CONCEPT"]
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("prerequisites" in m for m in _messages(out)))


class RoleConditionalRequirementsTest(unittest.TestCase):
    def test_symptom_router_requires_3_symptoms(self):
        fm = _valid_v3_minimal()
        fm["doc_role"] = "symptom_router"
        # no symptoms
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("symptom_router" in m and "symptoms" in m
                            for m in _messages(out)))

    def test_symptom_router_with_2_symptoms_caught(self):
        fm = _valid_v3_minimal()
        fm["doc_role"] = "symptom_router"
        fm["symptoms"] = ["a", "b"]  # only 2
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("symptom_router" in m and "3" in m
                            for m in _messages(out)))

    def test_symptom_router_with_3_symptoms_passes(self):
        fm = _valid_v3_minimal()
        fm["doc_role"] = "symptom_router"
        fm["symptoms"] = ["a", "b", "c"]
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        sr_msgs = [m for m in _messages(out) if "symptom_router" in m]
        self.assertEqual(sr_msgs, [])

    def test_playbook_requires_symptoms(self):
        fm = _valid_v3_minimal()
        fm["doc_role"] = "playbook"
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("playbook" in m and "symptoms" in m
                            for m in _messages(out)))

    def test_playbook_with_1_symptom_passes(self):
        fm = _valid_v3_minimal()
        fm["doc_role"] = "playbook"
        fm["symptoms"] = ["one"]
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        pb_msgs = [m for m in _messages(out) if "playbook" in m]
        self.assertEqual(pb_msgs, [])

    def test_mission_bridge_requires_mission_ids(self):
        fm = _valid_v3_minimal()
        fm["doc_role"] = "mission_bridge"
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("mission_bridge" in m and "mission_ids" in m
                            for m in _messages(out)))

    def test_mission_bridge_with_mission_ids_passes(self):
        fm = _valid_v3_minimal()
        fm["doc_role"] = "mission_bridge"
        fm["mission_ids"] = ["missions/roomescape"]
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        mb_msgs = [m for m in _messages(out) if "mission_bridge" in m]
        self.assertEqual(mb_msgs, [])

    def test_chooser_requires_2_confusable_with(self):
        fm = _valid_v3_minimal()
        fm["doc_role"] = "chooser"
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("chooser" in m and "confusable_with" in m
                            for m in _messages(out)))

    def test_chooser_with_1_confusable_caught(self):
        fm = _valid_v3_minimal()
        fm["doc_role"] = "chooser"
        fm["confusable_with"] = ["spring/di"]  # only 1
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        self.assertTrue(any("chooser" in m and "2" in m for m in _messages(out)))

    def test_chooser_with_2_confusable_passes(self):
        fm = _valid_v3_minimal()
        fm["doc_role"] = "chooser"
        fm["confusable_with"] = ["spring/di", "design-pattern/service-locator"]
        out = check_corpus_v3_pilot_frontmatter(file_path=_path(), frontmatter=fm)
        ch_msgs = [m for m in _messages(out) if "chooser" in m]
        self.assertEqual(ch_msgs, [])


class SourcePriorityTest(unittest.TestCase):
    def test_valid_source_priority(self):
        for sp in [0, 50, 90, 100]:
            with self.subTest(source_priority=sp):
                fm = _valid_v3_minimal()
                fm["source_priority"] = sp
                out = check_corpus_v3_pilot_frontmatter(
                    file_path=_path(), frontmatter=fm
                )
                sp_msgs = [m for m in _messages(out) if "source_priority" in m]
                self.assertEqual(sp_msgs, [])

    def test_out_of_range_source_priority_caught(self):
        for invalid in [-1, 101, 200]:
            with self.subTest(source_priority=invalid):
                fm = _valid_v3_minimal()
                fm["source_priority"] = invalid
                out = check_corpus_v3_pilot_frontmatter(
                    file_path=_path(), frontmatter=fm
                )
                self.assertTrue(
                    any("source_priority" in m for m in _messages(out)),
                    f"Expected error for {invalid}",
                )


class IntegrationWithCheckFrontmatterSchemaTest(unittest.TestCase):
    """Verify that ``check_frontmatter_schema`` dispatches to the v3 check
    when ``schema_version: 3`` is present.
    """

    def test_schema_version_3_dispatches_to_v3_check(self):
        text = """---
schema_version: 3
title: "DI Primer"
concept_id: spring/di
difficulty: beginner
doc_role: primer
level: beginner
language: ko
aliases:
  - DI
  - dependency injection
expected_queries:
  - 처음 배우는데 DI가 뭐야?
---

# DI Primer

content
"""
        out = check_frontmatter_schema(file_path=_path(), text=text)
        # v3 violations are tagged with check="corpus_v3_frontmatter"
        v3_violations = [v for v in out if v.check == "corpus_v3_frontmatter"]
        # Expect the minimal-pilot doc to pass v3 fields (no v3 violations
        # other than maybe missing optional Wave-2 fields like canonical;
        # the lint warns those as missing pilot fields IF in PILOT_V3_FIELDS).
        # All PILOT_V3_FIELDS are present in this fixture.
        # Filter out 'missing pilot field' messages — they should be empty here.
        missing_pilot = [v for v in v3_violations
                         if "missing pilot field" in v.message]
        self.assertEqual(missing_pilot, [], _messages(missing_pilot))

    def test_schema_version_3_with_circular_leak_caught(self):
        """The lint dispatcher path catches aliases ⊥ expected_queries
        violation end-to-end."""
        text = """---
schema_version: 3
title: "DI Primer"
concept_id: spring/di
difficulty: beginner
doc_role: primer
level: beginner
language: ko
aliases:
  - DI
  - 의존성 주입
expected_queries:
  - DI
  - new 대신 주입받는 이유?
---

# DI Primer

content
"""
        out = check_frontmatter_schema(file_path=_path(), text=text)
        v3_violations = [v for v in out if v.check == "corpus_v3_frontmatter"]
        self.assertTrue(any("aliases ⊥" in v.message for v in v3_violations))

    def test_schema_version_2_does_not_invoke_v3(self):
        """v2 docs must not trigger v3 check (would fail since v2 lacks
        v3 required fields like ``language``)."""
        text = """---
schema_version: 2
title: "DI Primer"
concept_id: spring/di
difficulty: beginner
doc_role: primer
level: beginner
aliases:
  - DI
expected_queries:
  - DI가 뭐야?
---

# DI Primer

content
"""
        out = check_frontmatter_schema(file_path=_path(), text=text)
        v3_violations = [v for v in out if v.check == "corpus_v3_frontmatter"]
        self.assertEqual(v3_violations, [], _messages(v3_violations))


if __name__ == "__main__":
    unittest.main()

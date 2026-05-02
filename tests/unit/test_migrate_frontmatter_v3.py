"""Unit tests for scripts.learning.rag.r3.migrate_frontmatter_v3.

Verifies the v2 → v3 frontmatter transformation rules including:
- doc_role v2-only value mapping (comparison → bridge)
- category derivation from folder placement
- language detection by CJK ratio
- source_priority defaults by doc_role
- canonical default for primer
- legacy neighbor field promotion to linked_paths
- aliases ⊥ expected_queries enforcement (overlap removed from EQ)
- intents default by doc_role
- idempotency on v3 docs
- byte-level body preservation
- deterministic field order in serialization

Companion lint check is in tests/unit/test_corpus_lint_v3.py; this
module focuses on the *transform* itself.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from scripts.learning.rag.r3 import migrate_frontmatter_v3 as mig


def _path(category: str = "spring", filename: str = "example.md") -> Path:
    return Path(f"knowledge/cs/contents/{category}/{filename}")


class LanguageDetectionTest(unittest.TestCase):
    def test_pure_korean_is_ko(self):
        body = "스프링 DI는 객체를 외부에서 주입받는 방식이다." * 5
        self.assertEqual(mig.detect_language(body), "ko")

    def test_pure_english_is_en(self):
        body = "Spring DI is dependency injection from outside." * 5
        self.assertEqual(mig.detect_language(body), "en")

    def test_mixed_below_30_percent_is_mixed(self):
        # Mostly English with a few Korean characters
        body = "Spring DI " * 30 + "의존"
        self.assertEqual(mig.detect_language(body), "mixed")

    def test_mixed_above_30_percent_is_ko(self):
        # Korean dominant
        body = "스프링 DI 의존성 주입 컨테이너 빈" * 5
        self.assertEqual(mig.detect_language(body), "ko")

    def test_empty_body_is_en(self):
        self.assertEqual(mig.detect_language(""), "en")

    def test_chinese_han_counts_as_cjk(self):
        body = "一二三四五六七八九十" * 3
        self.assertEqual(mig.detect_language(body), "ko")  # CJK > 30%


class CategoryDerivationTest(unittest.TestCase):
    def test_under_contents(self):
        p = Path("knowledge/cs/contents/spring/spring-di-primer.md")
        self.assertEqual(mig.derive_category(p), "spring")

    def test_subfolder_under_category(self):
        p = Path("knowledge/cs/contents/database/transactions/isolation.md")
        self.assertEqual(mig.derive_category(p), "database")

    def test_no_contents_returns_none(self):
        p = Path("knowledge/cs/random/x.md")
        self.assertIsNone(mig.derive_category(p))


class AliasesExpectedQueriesDisjointTest(unittest.TestCase):
    def test_no_overlap_no_change(self):
        aliases_kept, eq_kept, overlaps = mig._drop_aliases_from_expected_queries(
            ["DI", "dependency injection"],
            ["What is DI primer?", "Why use DI?"],
        )
        self.assertEqual(aliases_kept, ["DI", "dependency injection"])
        self.assertEqual(eq_kept, ["What is DI primer?", "Why use DI?"])
        self.assertEqual(overlaps, [])

    def test_exact_overlap_removed(self):
        aliases_kept, eq_kept, overlaps = mig._drop_aliases_from_expected_queries(
            ["DI"],
            ["DI", "What is DI primer?"],
        )
        self.assertEqual(aliases_kept, ["DI"])
        self.assertEqual(eq_kept, ["What is DI primer?"])
        self.assertEqual(overlaps, ["DI"])

    def test_case_insensitive_overlap_removed(self):
        aliases_kept, eq_kept, overlaps = mig._drop_aliases_from_expected_queries(
            ["DI"],
            ["di", "What is DI?"],
        )
        self.assertEqual(eq_kept, ["What is DI?"])
        self.assertEqual(overlaps, ["di"])

    def test_whitespace_normalized_overlap(self):
        aliases_kept, eq_kept, overlaps = mig._drop_aliases_from_expected_queries(
            ["spring di"],
            ["  spring   di  "],
        )
        self.assertEqual(eq_kept, [])
        self.assertEqual(overlaps, ["  spring   di  "])

    def test_empty_inputs(self):
        aliases_kept, eq_kept, overlaps = mig._drop_aliases_from_expected_queries(
            [], [],
        )
        self.assertEqual(aliases_kept, [])
        self.assertEqual(eq_kept, [])
        self.assertEqual(overlaps, [])


class TransformV2ToV3Test(unittest.TestCase):
    def test_minimal_v2_to_v3(self):
        v2 = {
            "schema_version": 2,
            "title": "DI Primer",
            "concept_id": "spring/di",
            "difficulty": "beginner",
            "doc_role": "primer",
            "level": "beginner",
            "aliases": ["DI"],
            "expected_queries": ["What is DI?"],
        }
        body = "Spring DI is foundational."
        v3, overlaps = mig.transform_v2_to_v3(
            v2, _path("spring"), body
        )
        self.assertEqual(v3["schema_version"], 3)
        self.assertEqual(v3["doc_role"], "primer")
        self.assertEqual(v3["category"], "spring")
        self.assertEqual(v3["language"], "en")  # English body
        self.assertEqual(v3["source_priority"], 90)  # primer default
        self.assertTrue(v3["canonical"])  # primer → canonical
        self.assertEqual(v3["intents"], ["definition"])
        self.assertEqual(overlaps, [])

    def test_doc_role_comparison_to_bridge(self):
        v2 = {
            "schema_version": 2,
            "concept_id": "database/mvcc-vs-locking",
            "doc_role": "comparison",
            "level": "advanced",
            "aliases": ["MVCC vs locking"],
            "expected_queries": ["MVCC vs locking 차이?"],
        }
        v3, _ = mig.transform_v2_to_v3(v2, _path("database"), "")
        self.assertEqual(v3["doc_role"], "bridge")
        self.assertEqual(v3["intents"], ["comparison"])
        self.assertEqual(v3["source_priority"], 85)  # bridge default

    def test_legacy_neighbors_promoted_to_linked_paths(self):
        v2 = {
            "schema_version": 2,
            "concept_id": "database/mvcc",
            "doc_role": "primer",
            "level": "beginner",
            "aliases": ["MVCC"],
            "expected_queries": ["MVCC?"],
            "acceptable_neighbors": [
                "contents/database/transaction-isolation-basics.md",
                "contents/database/lock-basics.md",
            ],
            "companion_neighbors": [
                "contents/database/gap-lock-next-key-lock.md",
            ],
            "forbidden_neighbors": [
                "contents/spring/spring-transactional-basics.md",
            ],
        }
        v3, _ = mig.transform_v2_to_v3(v2, _path("database"), "")
        self.assertNotIn("acceptable_neighbors", v3)
        self.assertNotIn("companion_neighbors", v3)
        # all legacy neighbors merged into linked_paths preserving order
        self.assertEqual(
            v3["linked_paths"],
            [
                "contents/database/transaction-isolation-basics.md",
                "contents/database/lock-basics.md",
                "contents/database/gap-lock-next-key-lock.md",
            ],
        )
        # forbidden_neighbors preserved
        self.assertEqual(
            v3["forbidden_neighbors"],
            ["contents/spring/spring-transactional-basics.md"],
        )

    def test_aliases_overlap_with_expected_queries_removed(self):
        v2 = {
            "schema_version": 2,
            "concept_id": "spring/di",
            "doc_role": "primer",
            "level": "beginner",
            "aliases": ["DI", "dependency injection"],
            "expected_queries": ["DI", "What is DI?"],  # 'DI' overlaps alias
        }
        v3, overlaps = mig.transform_v2_to_v3(v2, _path("spring"), "")
        self.assertEqual(v3["aliases"], ["DI", "dependency injection"])
        self.assertEqual(v3["expected_queries"], ["What is DI?"])
        self.assertEqual(overlaps, ["DI"])

    def test_canonical_not_set_for_non_primer(self):
        v2 = {
            "schema_version": 2,
            "concept_id": "database/lock",
            "doc_role": "deep_dive",
            "level": "advanced",
            "aliases": ["lock internals"],
            "expected_queries": ["how does locking work internally?"],
        }
        v3, _ = mig.transform_v2_to_v3(v2, _path("database"), "")
        self.assertFalse(v3["canonical"])  # deep_dive default False

    def test_existing_canonical_preserved(self):
        v2 = {
            "schema_version": 2,
            "concept_id": "spring/di",
            "doc_role": "primer",
            "level": "beginner",
            "canonical": False,  # explicitly False even though primer
            "aliases": ["DI"],
            "expected_queries": ["What is DI?"],
        }
        v3, _ = mig.transform_v2_to_v3(v2, _path("spring"), "")
        self.assertFalse(v3["canonical"])

    def test_existing_intents_preserved(self):
        v2 = {
            "schema_version": 2,
            "concept_id": "spring/di",
            "doc_role": "primer",
            "level": "beginner",
            "aliases": ["DI"],
            "expected_queries": ["What is DI?"],
            "intents": ["design", "comparison"],  # already set
        }
        v3, _ = mig.transform_v2_to_v3(v2, _path("spring"), "")
        self.assertEqual(v3["intents"], ["design", "comparison"])

    def test_existing_source_priority_preserved(self):
        v2 = {
            "schema_version": 2,
            "concept_id": "spring/di",
            "doc_role": "primer",
            "level": "beginner",
            "aliases": ["DI"],
            "expected_queries": ["What is DI?"],
            "source_priority": 95,
        }
        v3, _ = mig.transform_v2_to_v3(v2, _path("spring"), "")
        self.assertEqual(v3["source_priority"], 95)


class SerializeV3FrontmatterTest(unittest.TestCase):
    def test_canonical_field_order(self):
        fm = {
            "expected_queries": ["q1"],
            "schema_version": 3,
            "concept_id": "spring/di",
            "title": "DI Primer",
            "aliases": ["DI"],
            "doc_role": "primer",
            "level": "beginner",
            "language": "ko",
        }
        out = mig.serialize_v3_frontmatter(fm)
        # schema_version must come first
        lines = [ln for ln in out.splitlines() if ln and not ln.startswith(" ")]
        keys = [ln.split(":")[0] for ln in lines]
        self.assertEqual(keys[0], "schema_version")
        self.assertEqual(keys[1], "title")
        self.assertEqual(keys[2], "concept_id")

    def test_korean_strings_preserved(self):
        fm = {
            "schema_version": 3,
            "concept_id": "spring/di",
            "doc_role": "primer",
            "level": "beginner",
            "aliases": ["의존성 주입", "DI"],
            "expected_queries": ["처음 배우는데 DI가 뭐야?"],
        }
        out = mig.serialize_v3_frontmatter(fm)
        self.assertIn("의존성 주입", out)
        self.assertIn("처음 배우는데 DI가 뭐야?", out)

    def test_unknown_keys_preserved(self):
        fm = {
            "schema_version": 3,
            "title": "x",
            "concept_id": "x/y",
            "doc_role": "primer",
            "level": "beginner",
            "aliases": ["x"],
            "expected_queries": ["?"],
            "custom_field": "preserved",
        }
        out = mig.serialize_v3_frontmatter(fm)
        self.assertIn("custom_field: preserved", out)


class MigrateFileTest(unittest.TestCase):
    """Round-trip migrate one .md file (in-memory through tmp file)."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel: str, text: str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_v2_doc_migrates(self):
        text = """---
schema_version: 2
title: DI Primer
concept_id: spring/di
difficulty: beginner
doc_role: primer
level: beginner
aliases:
  - DI
  - dependency injection
expected_queries:
  - What is DI?
---

# DI Primer

Some Korean body 의존성 주입 explanation.
"""
        p = self._write("contents/spring/di-primer.md", text)
        result = mig.migrate_file(p)
        self.assertFalse(result.skipped)
        self.assertTrue(result.transformed)
        self.assertEqual(result.new_frontmatter["schema_version"], 3)
        self.assertEqual(result.new_frontmatter["category"], "spring")
        self.assertEqual(result.new_frontmatter["language"], "mixed")
        # body is preserved verbatim
        self.assertIn("# DI Primer", result.new_text)
        self.assertIn("의존성 주입 explanation", result.new_text)

    def test_v3_doc_skipped(self):
        text = """---
schema_version: 3
title: DI Primer
concept_id: spring/di
canonical: true
category: spring
doc_role: primer
level: beginner
language: ko
aliases:
  - DI
expected_queries:
  - DI가 뭐야?
---

# Body
"""
        p = self._write("contents/spring/di-primer.md", text)
        result = mig.migrate_file(p)
        self.assertTrue(result.skipped)
        self.assertEqual(result.skipped_reason, "already schema_version: 3")

    def test_no_frontmatter_skipped(self):
        text = "# Bare doc\n\nNo frontmatter here.\n"
        p = self._write("contents/x/bare.md", text)
        result = mig.migrate_file(p)
        self.assertTrue(result.skipped)
        self.assertEqual(result.skipped_reason, "no frontmatter block")

    def test_unsupported_schema_version_skipped(self):
        text = """---
schema_version: 1
title: x
---
body
"""
        p = self._write("contents/x/y.md", text)
        result = mig.migrate_file(p)
        self.assertTrue(result.skipped)
        self.assertIn("unsupported schema_version", result.skipped_reason or "")


class IdempotencyAndRoundTripTest(unittest.TestCase):
    """Migrating once produces v3; running again is a no-op."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_apply_then_rerun_is_noop(self):
        text = """---
schema_version: 2
title: x
concept_id: spring/x
difficulty: beginner
doc_role: primer
level: beginner
aliases:
  - x
expected_queries:
  - "What is x?"
---

# Body
"""
        p = self.root / "contents/spring/x.md"
        p.parent.mkdir(parents=True)
        p.write_text(text, encoding="utf-8")

        first = mig.migrate_file(p)
        self.assertTrue(first.transformed)
        # write the result manually (simulating --apply)
        p.write_text(first.new_text or "", encoding="utf-8")

        second = mig.migrate_file(p)
        self.assertTrue(second.skipped)
        self.assertEqual(second.skipped_reason, "already schema_version: 3")


class CLIMainTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # set up two files: one v2, one v3
        v2_text = """---
schema_version: 2
title: x
concept_id: spring/x
difficulty: beginner
doc_role: primer
level: beginner
aliases: [x]
expected_queries: ["What is x?"]
---
body
"""
        v3_text = """---
schema_version: 3
title: y
concept_id: spring/y
canonical: true
category: spring
doc_role: primer
level: beginner
language: en
aliases: [y]
expected_queries: ["What is y?"]
---
body
"""
        for rel, text in [
            ("contents/spring/x.md", v2_text),
            ("contents/spring/y.md", v3_text),
        ]:
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_does_not_write(self):
        original = (self.root / "contents/spring/x.md").read_text(encoding="utf-8")
        rc = mig.main(["--paths", str(self.root), "--quiet"])
        self.assertEqual(rc, 0)
        # file unchanged
        after = (self.root / "contents/spring/x.md").read_text(encoding="utf-8")
        self.assertEqual(after, original)

    def test_apply_writes_v3(self):
        rc = mig.main(["--paths", str(self.root), "--apply", "--quiet"])
        self.assertEqual(rc, 0)
        after = (self.root / "contents/spring/x.md").read_text(encoding="utf-8")
        self.assertIn("schema_version: 3", after)
        # idempotent: re-apply doesn't change anything
        rc2 = mig.main(["--paths", str(self.root), "--apply", "--quiet"])
        self.assertEqual(rc2, 0)


if __name__ == "__main__":
    unittest.main()

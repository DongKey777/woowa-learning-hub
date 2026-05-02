"""Unit tests for ``scripts/learning/rag/r3/corpus_catalog_v3.py``.

Coverage:
- Builder picks up v3 frontmatter, populates every catalog field.
- Pre-v2 / v2 / no-frontmatter docs become stubs (has_frontmatter=False)
  so cross-doc refs can still resolve against unmigrated targets.
- Reverse indexes (missions / confusables / aliases / symptoms) include
  only v3 concepts, exclude stubs, and case-fold alias / symptom keys.
- Cross-doc reference resolver flags dangling concept_id references
  (confusable_with / prerequisites / next_docs) and counts mission_ids
  as opaque.
- ``--strict-refs`` CLI exits non-zero when unresolved refs exist.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.learning.rag.r3.corpus_catalog_v3 import (
    build_concept_catalog_v3,
    build_reverse_indexes,
    main,
    resolve_cross_refs,
    write_concept_catalog_v3,
)


def _v3_doc(
    concept_id: str,
    *,
    doc_role: str = "primer",
    aliases: list[str] | None = None,
    expected_queries: list[str] | None = None,
    confusable_with: list[str] | None = None,
    prerequisites: list[str] | None = None,
    next_docs: list[str] | None = None,
    mission_ids: list[str] | None = None,
    symptoms: list[str] | None = None,
    intents: list[str] | None = None,
    canonical: bool = False,
    source_priority: int = 80,
) -> str:
    fm_lines = [
        "---",
        "schema_version: 3",
        f'title: "{concept_id}"',
        f"concept_id: {concept_id}",
        f"canonical: {'true' if canonical else 'false'}",
        f"category: {concept_id.split('/', 1)[0]}",
        "difficulty: beginner",
        f"doc_role: {doc_role}",
        "level: beginner",
        "language: ko",
        f"source_priority: {source_priority}",
    ]
    if aliases:
        fm_lines.append("aliases:")
        for a in aliases:
            fm_lines.append(f"- {a}")
    if expected_queries:
        fm_lines.append("expected_queries:")
        for q in expected_queries:
            fm_lines.append(f"- {q}")
    if confusable_with:
        fm_lines.append("confusable_with:")
        for c in confusable_with:
            fm_lines.append(f"- {c}")
    if prerequisites:
        fm_lines.append("prerequisites:")
        for p in prerequisites:
            fm_lines.append(f"- {p}")
    if next_docs:
        fm_lines.append("next_docs:")
        for n in next_docs:
            fm_lines.append(f"- {n}")
    if mission_ids:
        fm_lines.append("mission_ids:")
        for m in mission_ids:
            fm_lines.append(f"- {m}")
    if symptoms:
        fm_lines.append("symptoms:")
        for s in symptoms:
            fm_lines.append(f"- {s}")
    if intents:
        fm_lines.append("intents:")
        for i in intents:
            fm_lines.append(f"- {i}")
    fm_lines.append("---")
    return "\n".join(fm_lines) + "\n\n# body\ncontent\n"


def _v2_doc(concept_id: str) -> str:
    return (
        "---\n"
        "schema_version: 2\n"
        f"concept_id: {concept_id}\n"
        f"title: {concept_id}\n"
        "difficulty: beginner\n"
        "doc_role: primer\n"
        "level: beginner\n"
        "aliases:\n"
        "  - x\n"
        "expected_queries:\n"
        "  - x?\n"
        "---\n\n# body\ncontent\n"
    )


def _bare_doc() -> str:
    return "# legacy doc\nno frontmatter here.\n"


class BuilderTest(unittest.TestCase):
    def test_v3_doc_becomes_full_entry(self):
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "spring" / "di.md").write_text(
                _v3_doc(
                    "spring/di",
                    aliases=["DI", "의존성 주입"],
                    expected_queries=["DI가 뭐야?"],
                    canonical=True,
                ),
                encoding="utf-8",
            )
            catalog = build_concept_catalog_v3(corpus)
            self.assertEqual(catalog.concept_count, 1)
            self.assertEqual(catalog.stub_count, 0)
            entry = catalog.concepts["spring/di"]
            self.assertTrue(entry.has_frontmatter)
            self.assertTrue(entry.canonical)
            self.assertEqual(entry.aliases, ("DI", "의존성 주입"))
            self.assertEqual(entry.expected_queries, ("DI가 뭐야?",))
            self.assertEqual(entry.category, "spring")
            self.assertEqual(entry.language, "ko")
            self.assertEqual(entry.source_priority, 80)

    def test_pre_v2_doc_becomes_stub(self):
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "spring" / "legacy.md").write_text(_bare_doc(), encoding="utf-8")
            catalog = build_concept_catalog_v3(corpus)
            self.assertEqual(catalog.concept_count, 0)
            self.assertEqual(catalog.stub_count, 1)
            stub = catalog.concepts["spring/legacy"]
            self.assertFalse(stub.has_frontmatter)
            self.assertEqual(stub.doc_path, "spring/legacy.md")

    def test_v2_doc_becomes_stub_in_v3_catalog(self):
        """v2 docs are not v3 — they get stub entries so v3 cross-refs
        can still resolve against unmigrated targets."""
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "design-pattern").mkdir(parents=True)
            (corpus / "design-pattern" / "factory.md").write_text(
                _v2_doc("design-pattern/factory"), encoding="utf-8",
            )
            catalog = build_concept_catalog_v3(corpus)
            self.assertEqual(catalog.concept_count, 0)
            self.assertEqual(catalog.stub_count, 1)
            stub = catalog.concepts["design-pattern/factory"]
            self.assertFalse(stub.has_frontmatter)

    def test_real_v3_entry_wins_over_stub(self):
        """If a v3 doc and a stub both resolve to the same concept_id,
        the real entry must NOT be overwritten by the stub."""
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "spring" / "di.md").write_text(
                _v3_doc("spring/di"), encoding="utf-8",
            )
            catalog = build_concept_catalog_v3(corpus)
            self.assertTrue(catalog.concepts["spring/di"].has_frontmatter)


class ReverseIndexTest(unittest.TestCase):
    def _two_concept_corpus(self, td) -> Path:
        corpus = Path(td) / "contents"
        (corpus / "spring").mkdir(parents=True)
        (corpus / "design-pattern").mkdir(parents=True)
        (corpus / "spring" / "di.md").write_text(
            _v3_doc(
                "spring/di",
                doc_role="primer",
                aliases=["DI", "의존성 주입"],
                expected_queries=["DI가 뭐야?"],
                confusable_with=["design-pattern/service-locator"],
                mission_ids=["missions/roomescape"],
            ),
            encoding="utf-8",
        )
        (corpus / "design-pattern" / "service-locator.md").write_text(
            _v3_doc(
                "design-pattern/service-locator",
                doc_role="bridge",
                aliases=["service locator"],
                expected_queries=["service locator란?"],
                mission_ids=["missions/roomescape"],
            ),
            encoding="utf-8",
        )
        return corpus

    def test_aliases_index_is_case_folded(self):
        with TemporaryDirectory() as td:
            corpus = self._two_concept_corpus(td)
            cat = build_concept_catalog_v3(corpus)
            rev = build_reverse_indexes(cat)
            self.assertIn("di", rev.aliases_to_concept)
            self.assertIn("의존성 주입", rev.aliases_to_concept)
            self.assertEqual(rev.aliases_to_concept["di"], ["spring/di"])

    def test_mission_index_collects_concepts(self):
        with TemporaryDirectory() as td:
            corpus = self._two_concept_corpus(td)
            cat = build_concept_catalog_v3(corpus)
            rev = build_reverse_indexes(cat)
            self.assertEqual(
                rev.mission_ids_to_concepts["missions/roomescape"],
                ["design-pattern/service-locator", "spring/di"],
            )

    def test_confusable_neighbors_is_reversed(self):
        """spring/di names design-pattern/service-locator as confusable_with;
        the reverse index at design-pattern/service-locator must include
        spring/di."""
        with TemporaryDirectory() as td:
            corpus = self._two_concept_corpus(td)
            cat = build_concept_catalog_v3(corpus)
            rev = build_reverse_indexes(cat)
            self.assertEqual(
                rev.confusable_neighbors["design-pattern/service-locator"],
                ["spring/di"],
            )

    def test_stubs_excluded_from_reverse_indexes(self):
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "spring" / "legacy.md").write_text(_bare_doc(), encoding="utf-8")
            cat = build_concept_catalog_v3(corpus)
            rev = build_reverse_indexes(cat)
            self.assertEqual(rev.aliases_to_concept, {})
            self.assertEqual(rev.symptom_to_concepts, {})

    def test_symptom_index_is_case_folded(self):
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "spring" / "tx.md").write_text(
                _v3_doc(
                    "spring/transactional",
                    doc_role="playbook",
                    aliases=["@Transactional"],
                    expected_queries=["@Transactional이 뭐야?"],
                    symptoms=["Transactional이 안 먹어요", "프록시 우회"],
                ),
                encoding="utf-8",
            )
            cat = build_concept_catalog_v3(corpus)
            rev = build_reverse_indexes(cat)
            self.assertIn("transactional이 안 먹어요", rev.symptom_to_concepts)


class CrossRefResolverTest(unittest.TestCase):
    def test_dangling_confusable_with_flagged(self):
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "spring" / "di.md").write_text(
                _v3_doc(
                    "spring/di",
                    doc_role="chooser",
                    aliases=["DI"],
                    expected_queries=["DI?"],
                    confusable_with=[
                        "design-pattern/service-locator",  # missing
                        "design-pattern/factory",          # also missing
                    ],
                ),
                encoding="utf-8",
            )
            cat = build_concept_catalog_v3(corpus)
            unresolved = resolve_cross_refs(cat)
            self.assertEqual(unresolved.total(), 2)
            refs = {item["ref"] for item in unresolved.confusable_with}
            self.assertEqual(
                refs,
                {"design-pattern/service-locator", "design-pattern/factory"},
            )

    def test_existing_confusable_with_resolves(self):
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "design-pattern").mkdir(parents=True)
            (corpus / "spring" / "di.md").write_text(
                _v3_doc(
                    "spring/di",
                    doc_role="chooser",
                    aliases=["DI"],
                    expected_queries=["DI?"],
                    confusable_with=["design-pattern/service-locator"],
                ),
                encoding="utf-8",
            )
            (corpus / "design-pattern" / "service-locator.md").write_text(
                _v3_doc(
                    "design-pattern/service-locator",
                    aliases=["service locator"],
                    expected_queries=["sl?"],
                ),
                encoding="utf-8",
            )
            cat = build_concept_catalog_v3(corpus)
            unresolved = resolve_cross_refs(cat)
            self.assertEqual(unresolved.total(), 0)

    def test_stub_satisfies_cross_ref(self):
        """A stub (pre-v2 doc) MUST satisfy a v3 confusable_with reference,
        so Wave A migration doesn't show every link to an unmigrated doc
        as dangling."""
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "design-pattern").mkdir(parents=True)
            (corpus / "spring" / "di.md").write_text(
                _v3_doc(
                    "spring/di",
                    doc_role="chooser",
                    aliases=["DI"],
                    expected_queries=["DI?"],
                    confusable_with=["design-pattern/service-locator"],
                ),
                encoding="utf-8",
            )
            (corpus / "design-pattern" / "service-locator.md").write_text(
                _bare_doc(), encoding="utf-8",
            )
            cat = build_concept_catalog_v3(corpus)
            unresolved = resolve_cross_refs(cat)
            self.assertEqual(unresolved.total(), 0)

    def test_dangling_prerequisites_flagged(self):
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "spring" / "di.md").write_text(
                _v3_doc(
                    "spring/di",
                    aliases=["DI"],
                    expected_queries=["DI?"],
                    prerequisites=["language/missing-prereq"],
                ),
                encoding="utf-8",
            )
            cat = build_concept_catalog_v3(corpus)
            unresolved = resolve_cross_refs(cat)
            self.assertEqual(len(unresolved.prerequisites), 1)
            self.assertEqual(unresolved.prerequisites[0]["ref"],
                             "language/missing-prereq")


class IOTest(unittest.TestCase):
    def test_writes_catalog_and_reverse_indexes(self):
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "spring" / "di.md").write_text(
                _v3_doc(
                    "spring/di",
                    aliases=["DI"],
                    expected_queries=["DI?"],
                    mission_ids=["missions/roomescape"],
                ),
                encoding="utf-8",
            )
            cat = build_concept_catalog_v3(corpus)
            rev = build_reverse_indexes(cat)
            unresolved = resolve_cross_refs(cat)
            out = Path(td) / "catalog"
            paths = write_concept_catalog_v3(
                cat, out, reverse_indexes=rev, unresolved=unresolved,
            )
            self.assertTrue(paths["catalog"].exists())
            self.assertTrue(paths["mission_ids_to_concepts"].exists())
            self.assertTrue(paths["confusable_neighbors"].exists())
            self.assertTrue(paths["aliases_to_concept"].exists())
            self.assertTrue(paths["symptom_to_concepts"].exists())
            self.assertTrue(paths["unresolved_refs"].exists())
            blob = json.loads(paths["catalog"].read_text(encoding="utf-8"))
            self.assertEqual(blob["concept_count"], 1)


class CLITest(unittest.TestCase):
    def test_strict_refs_exits_nonzero_on_dangling(self):
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "spring" / "di.md").write_text(
                _v3_doc(
                    "spring/di",
                    aliases=["DI"],
                    expected_queries=["DI?"],
                    confusable_with=["design-pattern/missing"],
                ),
                encoding="utf-8",
            )
            out = Path(td) / "catalog"
            rc = main([
                "--corpus-root", str(corpus),
                "--out-dir", str(out),
                "--strict-refs",
            ])
            self.assertEqual(rc, 1)

    def test_strict_refs_exits_zero_when_clean(self):
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "spring" / "di.md").write_text(
                _v3_doc("spring/di", aliases=["DI"], expected_queries=["DI?"]),
                encoding="utf-8",
            )
            out = Path(td) / "catalog"
            rc = main([
                "--corpus-root", str(corpus),
                "--out-dir", str(out),
                "--strict-refs",
            ])
            self.assertEqual(rc, 0)

    def test_default_no_resolve_skips_unresolved_file(self):
        with TemporaryDirectory() as td:
            corpus = Path(td) / "contents"
            (corpus / "spring").mkdir(parents=True)
            (corpus / "spring" / "di.md").write_text(
                _v3_doc("spring/di", aliases=["DI"], expected_queries=["DI?"]),
                encoding="utf-8",
            )
            out = Path(td) / "catalog"
            rc = main([
                "--corpus-root", str(corpus),
                "--out-dir", str(out),
                "--no-resolve",
            ])
            self.assertEqual(rc, 0)
            self.assertFalse((out / "unresolved_refs.json").exists())


if __name__ == "__main__":
    unittest.main()

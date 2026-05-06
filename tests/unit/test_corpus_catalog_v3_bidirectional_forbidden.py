"""Bidirectional forbidden_neighbors inference at catalog build time.

Cycle 1 regression analysis (2026-05-06) showed that fleet-authored
chooser/bridge docs entered top-k for queries that should resolve to
a baseline canonical primer, because the primer's frontmatter-defined
forbidden_neighbors list was authored *before* the new chooser existed
— the primer cannot name what it does not yet know.

Catalog-level inference fixes this without touching frontmatter:
when chooser C declares ``confusable_with: [P_concept]``, we add C's
doc_path to P's forbidden_neighbors at catalog build time. The R3
retriever reads the catalog, so retrieval picks up the augmented
forbidden list at runtime.

The augmentation is intentionally one-directional (C → P only). C's
own forbidden_neighbors are not auto-populated with P's path because
C and P serve different intents (C is the chooser surface; P is the
primer source-of-truth) and biasing retrieval toward P is the goal.
"""

from __future__ import annotations

import unittest

from scripts.learning.rag.r3.corpus_catalog_v3 import (
    ConceptCatalogV3,
    ConceptCatalogEntryV3,
    augment_forbidden_via_confusable_with,
)


def _entry(
    concept_id: str,
    doc_path: str,
    *,
    confusable_with: tuple[str, ...] = (),
    forbidden_neighbors: tuple[str, ...] = (),
    has_frontmatter: bool = True,
) -> ConceptCatalogEntryV3:
    return ConceptCatalogEntryV3(
        concept_id=concept_id,
        doc_path=doc_path,
        has_frontmatter=has_frontmatter,
        category=concept_id.split("/")[0],
        doc_role="primer",
        level="beginner",
        language="ko",
        source_priority=80,
        confusable_with=confusable_with,
        forbidden_neighbors=forbidden_neighbors,
    )


def _catalog(*entries: ConceptCatalogEntryV3) -> ConceptCatalogV3:
    n_full = sum(1 for e in entries if e.has_frontmatter)
    n_stub = sum(1 for e in entries if not e.has_frontmatter)
    return ConceptCatalogV3(
        schema_version="3",
        corpus_root="knowledge/cs/contents",
        concept_count=n_full,
        stub_count=n_stub,
        concepts={e.concept_id: e for e in entries},
    )


class BidirectionalForbiddenInferenceTest(unittest.TestCase):
    def test_chooser_confusable_with_primer_adds_to_primer_forbidden(self) -> None:
        """Core invariant: when chooser C names primer P as confusable,
        P's forbidden_neighbors picks up C's doc_path."""
        primer = _entry(
            "spring/bean-di-basics",
            "spring/spring-bean-di-basics.md",
            forbidden_neighbors=(),
        )
        chooser = _entry(
            "design-pattern/registry-vs-locator-checklist",
            "design-pattern/registry-vs-locator-checklist.md",
            confusable_with=("spring/bean-di-basics",),
        )
        catalog = _catalog(primer, chooser)
        added = augment_forbidden_via_confusable_with(catalog)
        self.assertEqual(added, 1)
        augmented_primer = catalog.concepts["spring/bean-di-basics"]
        self.assertIn(
            "contents/design-pattern/registry-vs-locator-checklist.md",
            augmented_primer.forbidden_neighbors,
        )

    def test_one_directional_chooser_forbidden_unchanged(self) -> None:
        """Chooser C's own forbidden_neighbors is NOT augmented with P's
        path — biasing toward primer P is the goal, not the reverse."""
        primer = _entry(
            "spring/bean-di-basics",
            "spring/spring-bean-di-basics.md",
        )
        chooser = _entry(
            "design-pattern/registry-vs-locator-checklist",
            "design-pattern/registry-vs-locator-checklist.md",
            confusable_with=("spring/bean-di-basics",),
            forbidden_neighbors=(),
        )
        catalog = _catalog(primer, chooser)
        augment_forbidden_via_confusable_with(catalog)
        chooser_after = catalog.concepts["design-pattern/registry-vs-locator-checklist"]
        self.assertEqual(chooser_after.forbidden_neighbors, ())

    def test_existing_forbidden_neighbors_preserved(self) -> None:
        """Augmentation merges (union) — pre-existing forbidden entries
        in P stay; we only add new C paths."""
        primer = _entry(
            "spring/bean-di-basics",
            "spring/spring-bean-di-basics.md",
            forbidden_neighbors=(
                "contents/spring/spring-beanfactorypostprocessor-vs-beanpostprocessor.md",
            ),
        )
        chooser = _entry(
            "design-pattern/registry-vs-locator",
            "design-pattern/registry-vs-locator.md",
            confusable_with=("spring/bean-di-basics",),
        )
        catalog = _catalog(primer, chooser)
        augment_forbidden_via_confusable_with(catalog)
        augmented = catalog.concepts["spring/bean-di-basics"]
        self.assertIn(
            "contents/spring/spring-beanfactorypostprocessor-vs-beanpostprocessor.md",
            augmented.forbidden_neighbors,
        )
        self.assertIn(
            "contents/design-pattern/registry-vs-locator.md",
            augmented.forbidden_neighbors,
        )

    def test_multiple_choosers_target_same_primer(self) -> None:
        """Multiple choosers all naming primer P → all paths added."""
        primer = _entry(
            "spring/bean-di-basics",
            "spring/spring-bean-di-basics.md",
        )
        c1 = _entry(
            "design-pattern/c1", "design-pattern/c1.md",
            confusable_with=("spring/bean-di-basics",),
        )
        c2 = _entry(
            "design-pattern/c2", "design-pattern/c2.md",
            confusable_with=("spring/bean-di-basics",),
        )
        c3 = _entry(
            "design-pattern/c3", "design-pattern/c3.md",
            confusable_with=("spring/bean-di-basics",),
        )
        catalog = _catalog(primer, c1, c2, c3)
        added = augment_forbidden_via_confusable_with(catalog)
        self.assertEqual(added, 3)
        augmented = catalog.concepts["spring/bean-di-basics"]
        for path in [
            "contents/design-pattern/c1.md",
            "contents/design-pattern/c2.md",
            "contents/design-pattern/c3.md",
        ]:
            self.assertIn(path, augmented.forbidden_neighbors)

    def test_stub_target_skipped(self) -> None:
        """If primer P is a stub (no frontmatter — pre-v2 doc not yet
        migrated), we cannot augment its forbidden list (the resulting
        catalog would mix migrated/unmigrated semantics)."""
        primer_stub = _entry(
            "spring/bean-di-basics",
            "spring/spring-bean-di-basics.md",
            has_frontmatter=False,
        )
        chooser = _entry(
            "design-pattern/registry",
            "design-pattern/registry.md",
            confusable_with=("spring/bean-di-basics",),
        )
        catalog = _catalog(primer_stub, chooser)
        added = augment_forbidden_via_confusable_with(catalog)
        self.assertEqual(added, 0)

    def test_stub_source_skipped(self) -> None:
        """If chooser C is a stub, no augmentation triggered from it."""
        primer = _entry(
            "spring/bean-di-basics",
            "spring/spring-bean-di-basics.md",
        )
        chooser_stub = _entry(
            "design-pattern/registry",
            "design-pattern/registry.md",
            confusable_with=("spring/bean-di-basics",),
            has_frontmatter=False,
        )
        catalog = _catalog(primer, chooser_stub)
        added = augment_forbidden_via_confusable_with(catalog)
        self.assertEqual(added, 0)

    def test_empty_catalog_returns_zero(self) -> None:
        catalog = _catalog()
        added = augment_forbidden_via_confusable_with(catalog)
        self.assertEqual(added, 0)

    def test_idempotent_when_path_already_in_forbidden(self) -> None:
        """If C's path is already in P's forbidden (e.g. authored
        manually before catalog rebuild), do not double-count."""
        primer = _entry(
            "spring/bean-di-basics",
            "spring/spring-bean-di-basics.md",
            forbidden_neighbors=("contents/design-pattern/registry.md",),
        )
        chooser = _entry(
            "design-pattern/registry",
            "design-pattern/registry.md",
            confusable_with=("spring/bean-di-basics",),
        )
        catalog = _catalog(primer, chooser)
        added = augment_forbidden_via_confusable_with(catalog)
        self.assertEqual(added, 0)


class L2RollbackTest(unittest.TestCase):
    """Pin: corpus_catalog_v3 main() must NOT call
    augment_forbidden_via_confusable_with after the 2026-05-06 rollback.

    The function itself is retained (documentation + the unit tests
    above still verify its shape), but wiring it into the build
    pipeline regressed cohort_eval. This test catches accidental
    re-wiring."""

    def test_main_does_not_call_augment_function(self) -> None:
        import inspect
        from scripts.learning.rag.r3 import corpus_catalog_v3 as M
        src = inspect.getsource(M.main)
        # Either the call is genuinely absent OR (after rollback) it's
        # set to a hard-coded zero. Both are acceptable; what we forbid
        # is `augment_forbidden_via_confusable_with(catalog)` as a live
        # call producing a non-zero return wired into the catalog.
        # Detect: live call assigning to forbidden_added (not = 0).
        live_call = "augment_forbidden_via_confusable_with(catalog)"
        if live_call in src:
            # Allow only inside a hard-coded-zero comment context, not
            # as the producing expression for forbidden_added.
            self.fail(
                "augment_forbidden_via_confusable_with(catalog) is wired "
                "into corpus_catalog_v3.main() — it was rolled back on "
                "2026-05-06 because it caused -5pp on confusable_pairs. "
                "See the function's deprecation docstring for context."
            )


if __name__ == "__main__":
    unittest.main()

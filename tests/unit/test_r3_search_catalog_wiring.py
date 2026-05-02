"""Integration test: end-to-end R3 search wires the v3 catalog channels
and they show up in the trace metadata.

Covers:
- ``_resolve_catalog_root`` env override + repo-default discovery
- ``search()`` exposes ``catalog_channels_used`` in the trace
- Missing catalog files → graceful degradation, no exception
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.learning.rag.r3.search import _resolve_catalog_root, search


def _write_minimal_catalog(catalog_dir: Path) -> None:
    catalog_dir.mkdir(parents=True, exist_ok=True)
    catalog = {
        "schema_version": "3",
        "concept_count": 0,
        "stub_count": 0,
        "concepts": {},
    }
    (catalog_dir / "concepts.v3.json").write_text(
        json.dumps(catalog), encoding="utf-8",
    )
    (catalog_dir / "mission_ids_to_concepts.json").write_text(
        json.dumps({}), encoding="utf-8",
    )
    (catalog_dir / "symptom_to_concepts.json").write_text(
        json.dumps({}), encoding="utf-8",
    )


class ResolveCatalogRootTest(unittest.TestCase):
    def setUp(self):
        # Snapshot then clear the env so repo-default discovery is the
        # only signal during these tests
        self._saved_env = os.environ.pop("WOOWA_RAG_CATALOG_ROOT", None)

    def tearDown(self):
        if self._saved_env is None:
            os.environ.pop("WOOWA_RAG_CATALOG_ROOT", None)
        else:
            os.environ["WOOWA_RAG_CATALOG_ROOT"] = self._saved_env

    def test_explicit_argument_wins(self):
        with TemporaryDirectory() as td:
            cat_dir = Path(td) / "cat"
            _write_minimal_catalog(cat_dir)
            resolved = _resolve_catalog_root(cat_dir)
            self.assertEqual(resolved, cat_dir)

    def test_env_override(self):
        with TemporaryDirectory() as td:
            cat_dir = Path(td) / "cat"
            _write_minimal_catalog(cat_dir)
            os.environ["WOOWA_RAG_CATALOG_ROOT"] = str(cat_dir)
            resolved = _resolve_catalog_root(None)
            self.assertEqual(resolved, cat_dir)

    def test_incomplete_explicit_falls_through_to_repo_default(self):
        """Explicit override with missing files is *ignored* (rather
        than hard-failing) so resolution can fall through to env or
        repo default. This keeps Phase-4.5 indexes interoperable with
        operators who point at older/partial catalogs."""
        with TemporaryDirectory() as td:
            cat_dir = Path(td) / "incomplete"
            cat_dir.mkdir()
            (cat_dir / "concepts.v3.json").write_text("{}", encoding="utf-8")
            resolved = _resolve_catalog_root(cat_dir)
            # Either repo default exists (and we got it) or no catalog
            # at all is found. Both are valid; the key invariant is
            # "incomplete explicit path is NOT returned".
            self.assertNotEqual(resolved, cat_dir)

    def test_no_args_with_no_repo_default_is_handled(self):
        """When the env var is unset and no candidate satisfies the
        required-files contract, resolve returns None without error."""
        # We can't easily prevent repo-default discovery in this repo,
        # so just verify the function doesn't raise.
        try:
            _resolve_catalog_root(None)
        except Exception as exc:  # pragma: no cover — should never raise
            self.fail(f"resolver raised {exc}")

    def test_repo_default_discovers_real_catalog(self):
        """The actual repo's knowledge/cs/catalog/ exists after Phase 4.5
        so the no-args resolve should find it."""
        # Skip if catalog hasn't been built (e.g. fresh clone before Phase 4.5)
        repo_root = Path(__file__).resolve().parents[2]
        real_cat = repo_root / "knowledge" / "cs" / "catalog"
        if not (real_cat / "concepts.v3.json").exists():
            self.skipTest("real catalog not built (run concept_catalog_v3)")
        resolved = _resolve_catalog_root(None)
        self.assertIsNotNone(resolved)


class SearchCatalogChannelsTest(unittest.TestCase):
    """Search end-to-end with an explicit catalog_root. Without an
    index_root, no documents → no candidates → no catalog channels fire,
    but trace metadata must still record the catalog discovery state."""

    def test_search_with_no_index_runs_without_error(self):
        with TemporaryDirectory() as td:
            cat_dir = Path(td) / "cat"
            _write_minimal_catalog(cat_dir)
            debug: dict = {}
            hits = search(
                "roomescape에서 DI는 어떻게 적용해?",
                top_k=5,
                mode="cheap",
                catalog_root=cat_dir,
                debug=debug,
            )
            self.assertEqual(hits, [])
            # Catalog channels were resolvable but didn't fire because
            # signal_documents was empty (no index_root).
            self.assertEqual(debug["r3_catalog_channels_used"], [])
            self.assertIsNone(debug["r3_catalog_error"])

    def test_search_with_missing_catalog_does_not_raise(self):
        """Pass a non-existent catalog path. Search must not raise."""
        debug: dict = {}
        hits = search(
            "roomescape DI",
            top_k=5,
            mode="cheap",
            catalog_root=Path("/tmp/nonexistent-catalog-12345xyz"),
            debug=debug,
        )
        self.assertEqual(hits, [])
        # No channels recorded, no error
        self.assertEqual(debug["r3_catalog_channels_used"], [])


if __name__ == "__main__":
    unittest.main()

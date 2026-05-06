"""Pin: pyproject.toml declares the RAG runtime dependencies.

cycle 2 baseline incident #2 (2026-05-06). After ``pip install -e .`` in
a fresh worktree, the resulting .venv was *missing* FlagEmbedding,
lancedb, and pyarrow even though scripts/learning/rag/* imports all
three. The CS RAG cross-encoder reranker
(``BAAI/bge-reranker-v2-m3``) silently fell back to a degraded path,
collapsing the cohort_eval baseline from 91.5% to 60.5% (paraphrase_human
36%, corpus_gap_probe 0%).

Root cause was an operational protocol — CLAUDE.md / AGENTS.md asked
the AI session to remember to pip-install FlagEmbedding/lancedb/pyarrow
on top of ``pip install -e .`` — instead of declared dependencies. The
fix moves the contract into pyproject.toml so ``pip install -e .`` is
sufficient by itself.

This test guards against the regression where a future edit drops
one of the three RAG runtime deps from pyproject.toml.
"""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


REQUIRED_RAG_RUNTIME_DEPS = (
    "flagembedding",   # bge-reranker-v2-m3 cross-encoder
    "lancedb",         # CS RAG v3 LanceDB storage backend
    "pyarrow",         # direct imports in indexer.py / incremental_indexer.py / encoders/smoke.py
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_dependencies() -> list[str]:
    pyproject_path = _project_root() / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    return data["project"]["dependencies"]


def _normalize(spec: str) -> str:
    """Return the lowercased package name part of a PEP 508 spec.

    Handles forms like 'FlagEmbedding>=1.3', 'pyarrow', 'lancedb >=0.30'.
    """
    name = spec.strip()
    for sep in (">=", "<=", "==", "!=", "~=", ">", "<", " "):
        if sep in name:
            name = name.split(sep, 1)[0]
            break
    return name.strip().lower().replace("_", "-")


class PyprojectRagRuntimeDepsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.deps = _load_dependencies()
        self.normalized = {_normalize(d) for d in self.deps}

    def test_flagembedding_declared(self) -> None:
        self.assertIn(
            "flagembedding", self.normalized,
            f"FlagEmbedding missing from pyproject.toml dependencies. "
            f"Without it, scripts/learning/rag/encoders/bge_m3.py and "
            f"scripts/learning/rag/reranker.py fall back to a degraded "
            f"path. cycle 2 baseline 60.5% incident (2026-05-06).",
        )

    def test_lancedb_declared(self) -> None:
        self.assertIn(
            "lancedb", self.normalized,
            "lancedb missing from pyproject.toml dependencies. "
            "scripts/learning/rag/indexer.py imports it directly.",
        )

    def test_pyarrow_declared(self) -> None:
        self.assertIn(
            "pyarrow", self.normalized,
            "pyarrow missing from pyproject.toml dependencies. "
            "Direct imports exist in indexer.py / incremental_indexer.py / "
            "encoders/smoke.py — relying on lancedb's transitive pyarrow is "
            "fragile across lancedb releases.",
        )

    def test_all_required_specs_have_lower_bound(self) -> None:
        """A bare ``"pyarrow"`` spec is too permissive for a fresh
        learner install — pin a sane minimum so a major-version pyarrow
        regression cannot land silently."""
        deps_by_name = {_normalize(d): d for d in self.deps}
        for name in REQUIRED_RAG_RUNTIME_DEPS:
            spec = deps_by_name.get(name, "")
            self.assertTrue(
                ">=" in spec or "==" in spec or "~=" in spec,
                f"{name} dependency '{spec}' has no lower-bound; "
                f"pin a minimum version.",
            )


class RagRuntimeImportableTest(unittest.TestCase):
    """A weaker check that runs in the current .venv: importing each of
    the three packages should succeed. This catches a venv-time
    regression where pyproject.toml declares the dep but the install
    actually failed silently (rare but happens with native wheels)."""

    def test_flagembedding_importable(self) -> None:
        try:
            import FlagEmbedding  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            self.fail(f"FlagEmbedding not importable in current .venv: {exc}")

    def test_lancedb_importable(self) -> None:
        try:
            import lancedb  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            self.fail(f"lancedb not importable in current .venv: {exc}")

    def test_pyarrow_importable(self) -> None:
        try:
            import pyarrow  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            self.fail(f"pyarrow not importable in current .venv: {exc}")


if __name__ == "__main__":
    unittest.main()

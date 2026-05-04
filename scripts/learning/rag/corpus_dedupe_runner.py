"""Glue between ``corpus_lint`` and ``dedupe`` (plan §P5.4).

Loads the production LanceDB v3 index or an archived legacy SQLite/NPZ index
once, runs ``dedupe.find_near_duplicate_pairs``, and returns a list of
``LintViolation`` entries the lint module can mix with its other checks.

Lazy-imports LanceDB/numpy/sqlite3 so the lint module stays importable on
environments without the dense index (CI, fresh clone before First-Run
Protocol).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .dedupe import (
    DEFAULT_COSINE_THRESHOLD,
    DedupePair,
    find_near_duplicate_pairs,
    same_category_scope,
)


def load_index_paths_and_embeddings(index_root: Path) -> tuple[list[str], object]:
    """Load (paths_per_chunk, embeddings_matrix) from a RAG index.

    Returns paths in the same order as embedding rows so
    ``aggregate_by_path`` can mean-aggregate per doc.
    """
    if _is_lance_index(index_root):
        return _load_lance_index_paths_and_embeddings(index_root)
    return _load_legacy_index_paths_and_embeddings(index_root)


def _is_lance_index(index_root: Path) -> bool:
    try:
        from . import indexer  # noqa: WPS433

        return int(indexer.load_manifest(index_root).get("index_version", 0)) == 3
    except (FileNotFoundError, ValueError, TypeError):
        return False


def _load_lance_index_paths_and_embeddings(index_root: Path) -> tuple[list[str], object]:
    import numpy as np  # type: ignore  # noqa: WPS433
    from lancedb.table import LOOP  # type: ignore  # noqa: WPS433

    from . import indexer  # noqa: WPS433

    table = indexer.open_lance_table(index_root)
    row_count = table.count_rows()
    arrow_table = LOOP.run(
        table._table.query()
        .select(["path", "dense_vec"])
        .limit(row_count)
        .to_arrow()
    )
    paths = arrow_table["path"].to_pylist()
    if not paths:
        return [], np.zeros((0, 0), dtype="float32")

    dense_col = arrow_table["dense_vec"].combine_chunks()
    dense_dim = dense_col.type.list_size
    embeddings = np.asarray(dense_col.values, dtype="float32").reshape(
        len(paths), dense_dim
    )
    return paths, embeddings


def _load_legacy_index_paths_and_embeddings(index_root: Path) -> tuple[list[str], object]:
    import sqlite3  # noqa: WPS433
    import numpy as np  # type: ignore  # noqa: WPS433

    sqlite_path = index_root / "index.sqlite3"
    dense_path = index_root / "dense.npz"
    if not sqlite_path.exists() or not dense_path.exists():
        raise FileNotFoundError(
            f"index incomplete: missing {sqlite_path.name} or {dense_path.name}"
        )

    npz = np.load(dense_path)
    embeddings = npz["embeddings"]
    row_ids = npz["row_ids"]

    conn = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    try:
        # row_id → path lookup. row_ids in dense.npz align with
        # SQLite rowids of the chunks table.
        placeholders = ",".join("?" for _ in row_ids)
        rows = conn.execute(
            f"SELECT rowid, path FROM chunks WHERE rowid IN ({placeholders})",
            list(int(r) for r in row_ids),
        ).fetchall()
    finally:
        conn.close()

    path_by_rowid = {rid: path for rid, path in rows}
    paths = [path_by_rowid[int(r)] for r in row_ids]
    return paths, embeddings


@dataclass(frozen=True)
class DedupeRunResult:
    pairs: list[DedupePair]
    embedding_count: int
    unique_path_count: int
    threshold: float


def find_dedupe_candidates(
    *,
    index_root: Path,
    threshold: float = DEFAULT_COSINE_THRESHOLD,
    same_category_only: bool = True,
) -> DedupeRunResult:
    """Run the full dedupe scan against ``index_root``.

    ``same_category_only`` (default True) restricts comparison to
    docs whose first path segment matches — cuts compute and avoids
    accidental cross-domain false positives.
    """
    paths, embeddings = load_index_paths_and_embeddings(index_root)
    scope = same_category_scope if same_category_only else None
    pairs = find_near_duplicate_pairs(
        embeddings,
        paths,
        threshold=threshold,
        scope_fn=scope,
    )
    return DedupeRunResult(
        pairs=pairs,
        embedding_count=len(paths),
        unique_path_count=len(set(paths)),
        threshold=threshold,
    )


# ---------------------------------------------------------------------------
# Adapter for corpus_lint's dedupe_candidates_fn
# ---------------------------------------------------------------------------

def make_lint_callback(
    *,
    index_root: Path,
    threshold: float = DEFAULT_COSINE_THRESHOLD,
    same_category_only: bool = True,
):
    """Return a callable conforming to ``corpus_lint``'s
    ``dedupe_candidates_fn`` shape: takes ``files: list[(path, text)]``
    (unused — embeddings come from the index), returns
    ``list[LintViolation]``.

    The closure is what gets passed to ``corpus_lint.lint_corpus``.
    """
    # Import locally so corpus_lint module stays embedding-free.
    from .corpus_lint import LintViolation  # noqa: WPS433

    def _callback(files):  # files unused — paths come from the index
        try:
            result = find_dedupe_candidates(
                index_root=index_root,
                threshold=threshold,
                same_category_only=same_category_only,
            )
        except FileNotFoundError as exc:
            return [LintViolation(
                check="dedupe_candidates",
                file_path=str(index_root),
                message=f"index not built: {exc}",
            )]
        except Exception as exc:
            from . import indexer  # noqa: WPS433

            if not isinstance(
                exc,
                (indexer.IndexDependencyMissing, indexer.IncompatibleIndexError),
            ):
                raise
            return [LintViolation(
                check="dedupe_candidates",
                file_path=str(index_root),
                message=f"index not built: {exc}",
            )]

        return [
            LintViolation(
                check="dedupe_candidates",
                file_path=p.path_a,
                message=f"near-duplicate of {p.path_b} (cosine={p.cosine:.4f}, threshold={result.threshold})",
            )
            for p in result.pairs
        ]

    return _callback

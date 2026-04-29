"""A/B index builder — separate index roots for evaluating candidate
embedding models without touching the production index.

Plan §P2.1 — production indexer.py / EMBED_MODEL must stay untouched.
This module wraps the same chunking + SQLite schema + dense save path
but takes ``model`` and ``model_id`` / ``embed_dim`` explicitly. The
caller (typically the embedding A/B CLI) instantiates the candidate
model and points each candidate at its own ``state/cs_rag_eval/<id>/``
directory.

Design:
- DI of the embedder: callers pass an already-loaded model instance
  (anything with an ``encode(...)`` method matching SentenceTransformer
  semantics). This keeps the module ML-stack-agnostic for tests.
- Reuses indexer helpers (``_open_sqlite``, ``_insert_chunks``,
  ``_embed_text``, ``_paths``) so the SQLite schema stays in lock-step
  with production. If production schema changes (INDEX_VERSION bumps),
  this builder follows automatically.
- Writes a manifest mirroring production fields (index_version,
  embed_model, embed_dim, row_count, corpus_hash, corpus_root) — so
  ``eval.cache.assert_index_compat`` works against eval indexes too.
- Pre-flight dim check: if ``model.encode(...)`` returns a vector
  whose dim != ``embed_dim`` the build aborts before writing dense.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from scripts.learning.rag import corpus_loader
from scripts.learning.rag.indexer import (
    _embed_text,
    _insert_chunks,
    _open_sqlite,
    _paths,
    DENSE_NAME,
    INDEX_VERSION,
    IndexDependencyMissing,
    MANIFEST_NAME,
    SQLITE_NAME,
)


class _EncoderLike(Protocol):
    """Minimal interface for a SentenceTransformer-like model."""

    def encode(
        self,
        sentences: list[str],
        *,
        batch_size: int = ...,
        show_progress_bar: bool = ...,
        normalize_embeddings: bool = ...,
        convert_to_numpy: bool = ...,
    ) -> Any: ...


def build_eval_index(
    *,
    model: _EncoderLike,
    model_id: str,
    embed_dim: int,
    index_root: Path | str,
    corpus_root: Path | str = corpus_loader.DEFAULT_CORPUS_ROOT,
    progress: Callable[[str, dict], None] | None = None,
    batch_size: int = 32,
) -> dict:
    """Build an A/B-only index at ``index_root`` using ``model``.

    Args:
        model: an already-instantiated encoder. Tests can pass a fake
            with the same encode() shape.
        model_id: HF model id (e.g. ``"BAAI/bge-m3"``); recorded in the
            manifest so ``assert_index_compat`` can detect mismatch.
        embed_dim: declared output dimension. Build aborts if the
            actual encoder output disagrees.
        index_root: target directory; created if absent. Wiped of
            previous index files before building (clean slate).
        corpus_root: source markdown tree (default = production CS).
        progress: optional ``(stage, info)`` callback for status prints.
        batch_size: forwarded to model.encode.

    Returns:
        The manifest dict that was written to disk.

    Raises:
        IndexDependencyMissing — numpy not installed.
        RuntimeError — empty corpus or dim mismatch.
    """
    def _tick(stage: str, info: dict | None = None) -> None:
        if progress is not None:
            progress(stage, info or {})

    try:
        import numpy as np  # type: ignore
    except ImportError as exc:
        raise IndexDependencyMissing("numpy not installed.") from exc

    root = Path(index_root)
    root.mkdir(parents=True, exist_ok=True)
    sqlite_path, dense_path, manifest_path = _paths(root)

    # Clean slate
    for p in (sqlite_path, dense_path, manifest_path):
        if p.exists():
            p.unlink()

    _tick("load_corpus", {"corpus_root": str(corpus_root)})
    chunks = corpus_loader.load_corpus(corpus_root)
    if not chunks:
        raise RuntimeError(f"corpus at {corpus_root} is empty")
    _tick("load_corpus_done", {"chunk_count": len(chunks)})

    _tick("open_sqlite", {"path": str(sqlite_path)})
    conn = _open_sqlite(sqlite_path)
    try:
        _tick("insert_chunks", {"count": len(chunks)})
        row_ids = _insert_chunks(conn, chunks)

        _tick("encode", {"model_id": model_id, "count": len(chunks)})
        texts = [_embed_text(chunk) for chunk in chunks]
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        embeddings = np.asarray(embeddings, dtype="float32")
        if embeddings.shape != (len(chunks), embed_dim):
            raise RuntimeError(
                f"unexpected embedding shape {embeddings.shape}, "
                f"expected ({len(chunks)}, {embed_dim}) for {model_id!r}"
            )

        _tick("write_dense", {"shape": list(embeddings.shape)})
        np.savez(
            dense_path,
            embeddings=embeddings,
            row_ids=np.asarray(row_ids, dtype="int64"),
        )
    finally:
        conn.close()

    manifest = {
        "index_version": INDEX_VERSION,
        "embed_model": model_id,
        "embed_dim": embed_dim,
        "row_count": len(chunks),
        "corpus_hash": corpus_loader.corpus_hash(corpus_root),
        "corpus_root": str(corpus_root),
    }
    _tick("write_manifest", manifest)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def eval_index_root_for(model_id: str, *, base: Path | str = "state/cs_rag_eval") -> Path:
    """Stable directory naming convention for A/B indexes.

    HF ids contain ``/`` (e.g. ``BAAI/bge-m3``) which we replace with
    ``__`` so the path is filesystem-safe. Used by both the builder
    and the retriever so they agree on layout.
    """
    safe = model_id.replace("/", "__")
    return Path(base) / safe

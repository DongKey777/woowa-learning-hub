"""Incremental index builder — per-chunk diff + delta encode + atomic merge.

Plan §P5.6 — when the learner adds 50 docs/week, full rebuild's ~1-hour
cost compounds. SOTA vector DBs (Pinecone upsert, Qdrant upsert, Lucene
segment merge, LSM-tree merge) all share the same pattern: track which
chunks changed, encode only the delta, atomically swap the result.

This module implements that pattern with the constraint of plan §
"production indexer.py untouched until P8 cutover":

- fingerprint sidecar lives at ``<index_root>/chunk_hashes.json``
  (no SQLite schema change required)
- diff_chunks() classifies new corpus vs old fingerprints
- delta encode + atomic merge land in subsequent commits

This first commit only ships the diff primitive — pure stdlib, no
torch / sentence-transformers required, fully deterministic.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .corpus_loader import CorpusChunk

CHUNK_HASHES_NAME = "chunk_hashes.json"
"""Filename of the per-chunk fingerprint sidecar inside an index root."""


# ---------------------------------------------------------------------------
# Fingerprinting
# ---------------------------------------------------------------------------

def fingerprint_for_chunk(chunk: CorpusChunk) -> str:
    """Stable content fingerprint used for diff classification.

    Combines ``section_path`` (so a body move within a doc is visible
    as a structural change) with ``body``. Returns hex SHA1.

    SHA1 is used because corpus fingerprints are not security-critical —
    we just need a content equality check that's faster than byte
    comparison and stable across rebuilds.
    """
    payload = "\n".join(chunk.section_path) + "\n---\n" + chunk.body
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def compute_chunk_fingerprints(chunks: Iterable[CorpusChunk]) -> dict[str, str]:
    """Compute ``{chunk_id: fingerprint}`` for a corpus snapshot.

    chunk_id is positional within a doc (``f"{doc_id}#{chunk_index}"``),
    so reordering H2 sections within a doc shows up as deleted+added
    rather than modified — that's intentional, since position carries
    semantic weight in retrieval.
    """
    return {chunk.chunk_id: fingerprint_for_chunk(chunk) for chunk in chunks}


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ChunkDiff:
    """Result of comparing two fingerprint snapshots.

    All four lists are sorted for determinism (so repeat runs against
    the same corpus produce the same encoding order, which matters for
    log diffing and reproducibility).

    Attributes:
        added: chunk_ids present in new, absent in old → must encode
        modified: chunk_ids in both, fingerprint differs → must encode
        deleted: chunk_ids in old, absent in new → drop only
        unchanged: chunk_ids in both, fingerprint same → reuse
    """

    added: tuple[str, ...]
    modified: tuple[str, ...]
    deleted: tuple[str, ...]
    unchanged: tuple[str, ...]

    @property
    def total_changed(self) -> int:
        """Number of chunks that need any kind of write (encode or delete)."""
        return len(self.added) + len(self.modified) + len(self.deleted)

    @property
    def reuse_count(self) -> int:
        """Number of chunks that can be carried forward without re-encoding."""
        return len(self.unchanged)

    @property
    def needs_encoding(self) -> tuple[str, ...]:
        """chunk_ids that need to be sent through the embedder (added + modified)."""
        return tuple(sorted(set(self.added) | set(self.modified)))

    def is_noop(self) -> bool:
        """True if no chunks changed — incremental build can short-circuit."""
        return self.total_changed == 0


def diff_chunks(
    old_fingerprints: dict[str, str],
    new_fingerprints: dict[str, str],
) -> ChunkDiff:
    """Classify changes between two fingerprint snapshots.

    Args:
        old_fingerprints: previous corpus state
            (typically ``load_chunk_hashes(index_root)``)
        new_fingerprints: current corpus state
            (typically ``compute_chunk_fingerprints(chunks)``)

    Returns:
        ChunkDiff with deterministic sorted lists.
    """
    old_ids = set(old_fingerprints)
    new_ids = set(new_fingerprints)

    added = sorted(new_ids - old_ids)
    deleted = sorted(old_ids - new_ids)

    common = old_ids & new_ids
    modified = sorted(
        c for c in common if old_fingerprints[c] != new_fingerprints[c]
    )
    unchanged = sorted(
        c for c in common if old_fingerprints[c] == new_fingerprints[c]
    )

    return ChunkDiff(
        added=tuple(added),
        modified=tuple(modified),
        deleted=tuple(deleted),
        unchanged=tuple(unchanged),
    )


# ---------------------------------------------------------------------------
# Sidecar I/O
# ---------------------------------------------------------------------------

def load_chunk_hashes(index_root: Path | str) -> dict[str, str]:
    """Read previous fingerprints from ``<index_root>/chunk_hashes.json``.

    Returns an empty dict if the file is missing — that's the natural
    "first ever build" state and means everything will be classified as
    ``added``.
    """
    path = Path(index_root) / CHUNK_HASHES_NAME
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_chunk_hashes(
    fingerprints: dict[str, str],
    index_root: Path | str,
) -> None:
    """Write fingerprints to ``<index_root>/chunk_hashes.json``.

    Writes are sorted by key + indented for human-readable diffs in
    git, even though we expect this file to be gitignored under state/.
    """
    path = Path(index_root) / CHUNK_HASHES_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(fingerprints, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Dense matrix merge (numpy)
# ---------------------------------------------------------------------------

def merge_dense_arrays(
    *,
    prev_embeddings,  # np.ndarray, shape (N_prev, D)
    prev_row_ids,  # np.ndarray, shape (N_prev,) int64
    prev_chunk_id_by_row_id: dict[int, str],
    unchanged_chunk_ids: set[str],
    delta_chunk_ids,  # Sequence[str], len = N_delta
    delta_embeddings,  # np.ndarray, shape (N_delta, D)
    delta_row_ids,  # Sequence[int], len = N_delta
):
    """Merge unchanged previous rows + delta rows into a new dense matrix.

    Args:
        prev_embeddings: previous dense.npz embeddings array (N_prev, D)
        prev_row_ids: matching row_ids array (N_prev,)
        prev_chunk_id_by_row_id: lookup from row_id to chunk_id for prev
            rows. Caller computes from old SQLite snapshot.
        unchanged_chunk_ids: chunk_ids the diff classified as unchanged
            — these rows are kept from prev.
        delta_chunk_ids: chunk_ids that were re-encoded (added + modified)
            — these are the rows in delta_embeddings, in matching order.
        delta_embeddings: new embeddings for delta chunks (N_delta, D)
        delta_row_ids: row_ids assigned to delta chunks by the SQLite
            insert step (caller responsibility)

    Returns:
        ``(merged_embeddings, merged_row_ids)`` — np.ndarray pair.
        merged_embeddings has shape (N_kept + N_delta, D); rows are
        ordered by row_id ascending for deterministic dense.npz layout.

    Raises:
        ValueError on shape / length mismatches.
    """
    import numpy as np  # type: ignore

    # Validate shapes
    if prev_embeddings.shape[0] != prev_row_ids.shape[0]:
        raise ValueError(
            f"prev shape mismatch: embeddings={prev_embeddings.shape[0]} "
            f"row_ids={prev_row_ids.shape[0]}"
        )
    if delta_embeddings.shape[0] != len(delta_chunk_ids):
        raise ValueError(
            f"delta length mismatch: embeddings={delta_embeddings.shape[0]} "
            f"chunk_ids={len(delta_chunk_ids)}"
        )
    if len(delta_chunk_ids) != len(delta_row_ids):
        raise ValueError(
            f"delta length mismatch: chunk_ids={len(delta_chunk_ids)} "
            f"row_ids={len(delta_row_ids)}"
        )
    if (
        prev_embeddings.shape[0] > 0
        and delta_embeddings.shape[0] > 0
        and prev_embeddings.shape[1] != delta_embeddings.shape[1]
    ):
        raise ValueError(
            f"dim mismatch: prev D={prev_embeddings.shape[1]} "
            f"delta D={delta_embeddings.shape[1]}"
        )

    # Pick prev rows whose chunk_id is in unchanged set
    kept_mask = np.array(
        [
            prev_chunk_id_by_row_id.get(int(rid)) in unchanged_chunk_ids
            for rid in prev_row_ids
        ],
        dtype=bool,
    )
    kept_embeddings = prev_embeddings[kept_mask]
    kept_row_ids = prev_row_ids[kept_mask]

    # Normalise dtypes before concatenation (output is always float32 / int64
    # regardless of caller dtype — the on-disk np.savez format is fixed).
    kept_embeddings = kept_embeddings.astype("float32", copy=False)
    kept_row_ids = kept_row_ids.astype("int64", copy=False)
    delta_embeddings_norm = np.asarray(delta_embeddings, dtype="float32")
    delta_row_ids_norm = np.asarray(delta_row_ids, dtype="int64")

    # Stack with delta
    if kept_embeddings.shape[0] == 0:
        # First build or all-changed corpus
        merged_embeddings = delta_embeddings_norm
        merged_row_ids = delta_row_ids_norm
    elif delta_embeddings_norm.shape[0] == 0:
        # No-op or pure delete (caller should still rewrite to drop deleted rows)
        merged_embeddings = kept_embeddings
        merged_row_ids = kept_row_ids
    else:
        merged_embeddings = np.concatenate(
            [kept_embeddings, delta_embeddings_norm],
            axis=0,
        )
        merged_row_ids = np.concatenate(
            [kept_row_ids, delta_row_ids_norm],
            axis=0,
        )

    # Sort by row_id ascending for deterministic on-disk layout
    order = np.argsort(merged_row_ids, kind="stable")
    return merged_embeddings[order], merged_row_ids[order]


# ---------------------------------------------------------------------------
# Atomic file write (POSIX rename semantics)
# ---------------------------------------------------------------------------

def atomic_save_dense_npz(
    path,  # Path | str
    embeddings,  # np.ndarray
    row_ids,  # np.ndarray
) -> None:
    """Write a dense.npz atomically via tmp + rename.

    Plan §P5.6 — incremental rebuilds must guarantee that an
    interrupted write (SIGKILL, power loss, OOM) leaves the existing
    index file untouched, not half-overwritten. POSIX rename(2) is
    atomic within a filesystem so this pattern is the standard
    "no torn writes" recipe.

    Sequence:
        1. np.savez to ``<path>.tmp`` (full write completes or fails
           in isolation)
        2. os.replace(tmp, path) — atomic rename on POSIX/macOS

    On exception:
        - tmp file is removed if it exists, so a failed call does
          NOT leave orphan ``<path>.tmp`` files cluttering the index
          directory.
        - The original ``path`` is left untouched.
    """
    import numpy as np  # type: ignore
    import os

    final = Path(path)
    final.parent.mkdir(parents=True, exist_ok=True)
    # Use a tmp name in the same directory so rename stays within the
    # filesystem. ``np.savez`` adds ``.npz`` if the path doesn't already
    # end in it — passing an explicit ``.tmp.npz`` ensures the suffix
    # is stable and predictable.
    tmp = final.with_suffix(final.suffix + ".tmp")

    try:
        # np.savez writes to <tmp>.npz when given a path without that
        # extension; passing a file-like object avoids the suffix surprise.
        with open(tmp, "wb") as fh:
            np.savez(fh, embeddings=embeddings, row_ids=row_ids)
        os.replace(tmp, final)
    except BaseException:
        # Clean up tmp on any failure path (incl. KeyboardInterrupt)
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def atomic_save_chunk_hashes(
    fingerprints: dict[str, str],
    index_root: Path | str,
) -> None:
    """Write the chunk_hashes.json sidecar atomically.

    Same tmp+rename pattern as atomic_save_dense_npz but for the JSON
    sidecar so the dense.npz update and fingerprint sidecar update can
    both be ordered: dense first, fingerprints last. If the process
    crashes between, fingerprints stay stale → next incremental
    rebuild will re-encode the affected chunks (safe over-work),
    instead of incorrectly skipping them (data drift).
    """
    import os

    final = Path(index_root) / CHUNK_HASHES_NAME
    final.parent.mkdir(parents=True, exist_ok=True)
    tmp = final.with_suffix(final.suffix + ".tmp")

    try:
        tmp.write_text(
            json.dumps(fingerprints, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(tmp, final)
    except BaseException:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise

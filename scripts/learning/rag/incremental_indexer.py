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

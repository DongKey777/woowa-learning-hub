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

CHUNK_HASHES_PER_MODEL_NAME = "chunk_hashes_per_model.json"
"""LanceDB v3 sidecar: ``{encoder_model_version: {chunk_id: fingerprint}}``."""


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


def load_chunk_hashes_per_model(index_root: Path | str) -> dict[str, dict[str, str]]:
    """Read the LanceDB v3 per-model fingerprint sidecar.

    Missing file means no v3 incremental history exists yet. Malformed model
    entries are ignored defensively so a partial manual edit does not crash
    readiness checks; the affected model will simply full-rebuild.
    """
    path = Path(index_root) / CHUNK_HASHES_PER_MODEL_NAME
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    out: dict[str, dict[str, str]] = {}
    for model_version, fingerprints in data.items():
        if not isinstance(model_version, str) or not isinstance(fingerprints, dict):
            continue
        out[model_version] = {
            str(chunk_id): str(fingerprint)
            for chunk_id, fingerprint in fingerprints.items()
        }
    return out


def load_model_chunk_hashes(index_root: Path | str, model_version: str) -> dict[str, str]:
    """Return fingerprints for one encoder model version."""
    return load_chunk_hashes_per_model(index_root).get(model_version, {})


def atomic_save_model_chunk_hashes(
    *,
    index_root: Path | str,
    model_version: str,
    fingerprints: dict[str, str],
) -> None:
    """Atomically update one model entry in chunk_hashes_per_model.json.

    Fingerprints are written only after the LanceDB transaction succeeds.
    If this write fails, the next incremental run treats the model as stale
    and safely reprocesses the affected chunks.
    """
    import os

    final = Path(index_root) / CHUNK_HASHES_PER_MODEL_NAME
    final.parent.mkdir(parents=True, exist_ok=True)
    tmp = final.with_suffix(final.suffix + ".tmp")
    data = load_chunk_hashes_per_model(index_root)
    data[model_version] = dict(sorted(fingerprints.items()))
    try:
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
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


# ---------------------------------------------------------------------------
# SQLite chunks delete + insert (transactional)
# ---------------------------------------------------------------------------

_INSERT_CHUNK_SQL = """
INSERT INTO chunks (
    doc_id, chunk_id, path, title, category,
    section_title, section_path, body, char_len, anchors, difficulty
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def load_prev_chunk_id_lookup(conn) -> dict[int, str]:
    """Read ``{row_id: chunk_id}`` from chunks table.

    merge_dense_arrays needs this to project the previous dense.npz
    rows by chunk_id (since dense.npz is keyed by row_id, not
    chunk_id).
    """
    return {
        int(row_id): str(chunk_id)
        for row_id, chunk_id in conn.execute(
            "SELECT id, chunk_id FROM chunks"
        )
    }


def _normalise_corpus_root(corpus_root):
    """Lazy default lookup so monkey-patches on
    corpus_loader.DEFAULT_CORPUS_ROOT take effect."""
    if corpus_root is None:
        from .corpus_loader import DEFAULT_CORPUS_ROOT
        return DEFAULT_CORPUS_ROOT
    return corpus_root


def apply_chunk_diff_to_sqlite(
    conn,
    diff,  # ChunkDiff
    new_chunks_by_id: dict,  # dict[chunk_id, CorpusChunk]
) -> dict[str, int]:
    """Apply a ChunkDiff to the chunks table within a single transaction.

    Args:
        conn: open sqlite3 connection (already running ``_open_sqlite``
            so the schema + AI/AD triggers are present)
        diff: ChunkDiff result from diff_chunks(prev_fingerprints,
            new_fingerprints)
        new_chunks_by_id: lookup by chunk_id covering at least the
            ``diff.added`` and ``diff.modified`` sets

    Returns:
        ``{chunk_id: row_id}`` for the newly inserted (added +
        modified) rows. Caller passes these row_ids to
        merge_dense_arrays.

    Behaviour:
        - DELETE rows for ``diff.deleted`` and ``diff.modified``
          (modified will re-insert with new content + new row_id)
        - INSERT rows for ``diff.added`` and ``diff.modified``
        - chunks_fts is kept in sync automatically via the AI/AD
          triggers defined in indexer._SCHEMA
        - Wraps the whole sequence in BEGIN/COMMIT; ROLLBACK on
          exception so a partial failure leaves the table at the
          pre-call state.

    Raises:
        KeyError if new_chunks_by_id is missing a chunk_id that diff
            classifies as added/modified (caller bug).
        sqlite3.* exceptions propagate after rollback.
    """
    import json as _json

    inserted: dict[str, int] = {}
    cur = conn.cursor()
    cur.execute("BEGIN")
    try:
        # Delete: deleted ∪ modified (modified will re-insert)
        for cid in (*diff.deleted, *diff.modified):
            cur.execute("DELETE FROM chunks WHERE chunk_id = ?", (cid,))

        # Insert: added ∪ modified
        for cid in (*diff.added, *diff.modified):
            chunk = new_chunks_by_id[cid]
            cur.execute(
                _INSERT_CHUNK_SQL,
                (
                    chunk.doc_id,
                    chunk.chunk_id,
                    chunk.path,
                    chunk.title,
                    chunk.category,
                    chunk.section_title,
                    _json.dumps(chunk.section_path, ensure_ascii=False),
                    chunk.body,
                    chunk.char_len,
                    _json.dumps(chunk.anchors, ensure_ascii=False),
                    chunk.difficulty,
                ),
            )
            inserted[cid] = cur.lastrowid

        conn.commit()
        return inserted
    except BaseException:
        conn.rollback()
        raise


# ---------------------------------------------------------------------------
# Orchestrator — full incremental rebuild pipeline
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IncrementalBuildResult:
    """Outcome of a single incremental_build_index call.

    ``mode`` is "incremental" when the delta path executed, "full"
    when fallback to a full rebuild fired (first build, model
    mismatch, schema bump, missing dense.npz, etc.).
    """

    mode: str  # "incremental" | "full"
    manifest: dict
    diff_stats: dict[str, int]  # added/modified/deleted/unchanged counts
    encoded_chunk_count: int
    fallback_reason: str | None  # set when mode == "full"
    lance_version_before: int | None = None
    lance_version_after: int | None = None


def _full_rebuild_reason(
    *,
    index_root_path,  # Path
    model_id: str,
    embed_dim: int,
    indexer_module,
) -> str | None:
    """Return a reason string when the index requires a full rebuild,
    or ``None`` when incremental is safe.

    Reasons checked in priority order:
    - missing manifest / dense / sqlite (first build or corruption)
    - manifest INDEX_VERSION mismatch (schema bumped)
    - manifest embed_model mismatch (different candidate)
    - manifest embed_dim mismatch (model swap broke compatibility)
    """
    manifest_path = index_root_path / indexer_module.MANIFEST_NAME
    dense_path = index_root_path / indexer_module.DENSE_NAME
    sqlite_path = index_root_path / indexer_module.SQLITE_NAME

    if not manifest_path.exists():
        return "no_manifest"
    if not dense_path.exists():
        return "no_dense"
    if not sqlite_path.exists():
        return "no_sqlite"

    try:
        prev = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return "manifest_unparseable"

    if int(prev.get("index_version", -1)) != indexer_module.INDEX_VERSION:
        return "index_version_changed"
    if prev.get("embed_model") != model_id:
        return "embed_model_changed"
    if int(prev.get("embed_dim", -1)) != embed_dim:
        return "embed_dim_changed"
    return None


def _quote_lance_sql(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _chunk_id_filter(chunk_ids: Iterable[str]) -> str:
    ids = sorted({str(chunk_id) for chunk_id in chunk_ids})
    if not ids:
        return "chunk_id IN ('__woowa_noop__')"
    return "chunk_id IN (" + ", ".join(_quote_lance_sql(chunk_id) for chunk_id in ids) + ")"


def _lance_full_rebuild_reason(
    *,
    index_root_path: Path,
    encoder,
    modalities: tuple[str, ...],
    indexer_module,
) -> str | None:
    manifest_path = index_root_path / indexer_module.MANIFEST_NAME
    lance_path = index_root_path / indexer_module.LANCE_DIR_NAME
    if not manifest_path.exists():
        return "no_manifest"
    if not lance_path.exists():
        return "no_lance"
    try:
        manifest = indexer_module.read_manifest_v3(index_root_path)
    except Exception:
        return "manifest_not_lance_v3"
    if manifest.get("encoder", {}).get("model_version") != encoder.model_version:
        return "encoder_version_changed"
    existing_modalities = set(manifest.get("modalities") or ())
    if not set(modalities).issubset(existing_modalities):
        return "modalities_changed"
    try:
        table = indexer_module.open_lance_table(index_root_path)
        table.count_rows()
    except Exception:
        return "lance_table_missing"
    return None


def _update_lance_manifest_incremental_stats(
    *,
    index_root_path: Path,
    corpus_root,
    row_count: int,
    diff: ChunkDiff,
    encoded_chunk_count: int,
    indexer_module,
) -> dict:
    from . import corpus_loader

    manifest_path = index_root_path / indexer_module.MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["row_count"] = int(row_count)
    manifest["corpus_hash"] = corpus_loader.corpus_hash(corpus_root)
    manifest["incremental_stats"] = {
        "added": len(diff.added),
        "modified": len(diff.modified),
        "deleted": len(diff.deleted),
        "unchanged": len(diff.unchanged),
        "encoded": encoded_chunk_count,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def _restore_lance_version(table, version: int | None) -> None:
    if version is None:
        return
    try:
        table.restore(version)
    except Exception:
        try:
            table.checkout(version)
        except Exception:
            pass


def incremental_lance_build_index(
    *,
    encoder,
    index_root,
    corpus_root=None,
    modalities: tuple[str, ...] = ("dense", "sparse", "colbert", "fts"),
    progress=None,
    colbert_dtype: str = "float16",
) -> IncrementalBuildResult:
    """Incrementally update a v3 LanceDB index.

    This is the H5 path. It is intentionally separate from the legacy
    SQLite/NPZ incremental path so current production behavior stays stable
    until the final cutover gate.
    """
    from . import corpus_loader, indexer

    def _tick(stage: str, info: dict | None = None) -> None:
        if progress is not None:
            progress(stage, info or {})

    corpus_root = _normalise_corpus_root(corpus_root)
    index_root_path = Path(index_root)

    _tick("load_corpus", {"corpus_root": str(corpus_root)})
    chunks = corpus_loader.load_corpus(corpus_root)
    if not chunks:
        raise RuntimeError(f"corpus at {corpus_root} is empty")
    new_chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    new_fingerprints = compute_chunk_fingerprints(chunks)
    _tick("corpus_loaded", {"chunk_count": len(chunks)})

    fallback_reason = _lance_full_rebuild_reason(
        index_root_path=index_root_path,
        encoder=encoder,
        modalities=modalities,
        indexer_module=indexer,
    )
    if fallback_reason is not None:
        _tick("fallback_to_full", {"reason": fallback_reason})
        manifest = indexer.build_lance_index(
            index_root=index_root_path,
            corpus_root=corpus_root,
            encoder=encoder,
            modalities=modalities,
            progress=progress,
            colbert_dtype=colbert_dtype,
        )
        table = indexer.open_lance_table(index_root_path)
        atomic_save_model_chunk_hashes(
            index_root=index_root_path,
            model_version=encoder.model_version,
            fingerprints=new_fingerprints,
        )
        return IncrementalBuildResult(
            mode="full",
            manifest=manifest,
            diff_stats={
                "added": len(chunks),
                "modified": 0,
                "deleted": 0,
                "unchanged": 0,
            },
            encoded_chunk_count=len(chunks),
            fallback_reason=fallback_reason,
            lance_version_before=None,
            lance_version_after=int(table.version),
        )

    old_fingerprints = load_model_chunk_hashes(index_root_path, encoder.model_version)
    if not old_fingerprints:
        # The table exists, but this encoder has no sidecar state. Rebuilding
        # is safer than treating every row as an upsert against unknown history.
        _tick("fallback_to_full", {"reason": "no_model_fingerprints"})
        manifest = indexer.build_lance_index(
            index_root=index_root_path,
            corpus_root=corpus_root,
            encoder=encoder,
            modalities=modalities,
            progress=progress,
            colbert_dtype=colbert_dtype,
        )
        table = indexer.open_lance_table(index_root_path)
        atomic_save_model_chunk_hashes(
            index_root=index_root_path,
            model_version=encoder.model_version,
            fingerprints=new_fingerprints,
        )
        return IncrementalBuildResult(
            mode="full",
            manifest=manifest,
            diff_stats={
                "added": len(chunks),
                "modified": 0,
                "deleted": 0,
                "unchanged": 0,
            },
            encoded_chunk_count=len(chunks),
            fallback_reason="no_model_fingerprints",
            lance_version_before=None,
            lance_version_after=int(table.version),
        )

    diff = diff_chunks(old_fingerprints, new_fingerprints)
    _tick(
        "diff",
        {
            "added": len(diff.added),
            "modified": len(diff.modified),
            "deleted": len(diff.deleted),
            "unchanged": len(diff.unchanged),
        },
    )

    table = indexer.open_lance_table(index_root_path, mode="rw")
    lance_version_before = int(table.version)
    if diff.is_noop():
        _tick("noop", {"lance_version": lance_version_before})
        manifest = _update_lance_manifest_incremental_stats(
            index_root_path=index_root_path,
            corpus_root=corpus_root,
            row_count=table.count_rows(),
            diff=diff,
            encoded_chunk_count=0,
            indexer_module=indexer,
        )
        return IncrementalBuildResult(
            mode="incremental",
            manifest=manifest,
            diff_stats=manifest["incremental_stats"],
            encoded_chunk_count=0,
            fallback_reason=None,
            lance_version_before=lance_version_before,
            lance_version_after=lance_version_before,
        )

    delta_chunk_ids = list(diff.needs_encoding)
    delta_chunks = [new_chunks_by_id[chunk_id] for chunk_id in delta_chunk_ids]
    records = []
    if delta_chunks:
        texts = [indexer._embed_text(chunk) for chunk in delta_chunks]
        _tick("encode_delta", {"count": len(texts), "model": encoder.model_id})
        encoding = encoder.encode_corpus(
            texts,
            modalities=tuple(modality for modality in modalities if modality != "fts"),
            progress=progress,
        )
        records = indexer._lance_records(
            delta_chunks,
            encoding,
            encoder_version=encoder.model_version,
        )

    try:
        if records:
            builder = (
                table.merge_insert("chunk_id")
                .when_matched_update_all()
                .when_not_matched_insert_all()
            )
            if diff.deleted:
                builder = builder.when_not_matched_by_source_delete(
                    _chunk_id_filter(diff.deleted)
                )
            result = builder.execute(records)
            _tick(
                "lance_merge_insert",
                {
                    "updated": getattr(result, "num_updated_rows", None),
                    "inserted": getattr(result, "num_inserted_rows", None),
                    "deleted": getattr(result, "num_deleted_rows", None),
                },
            )
        elif diff.deleted:
            table.delete(_chunk_id_filter(diff.deleted))
            _tick("lance_delete", {"deleted": len(diff.deleted)})
    except Exception:
        _restore_lance_version(table, lance_version_before)
        raise

    lance_version_after = int(table.version)
    atomic_save_model_chunk_hashes(
        index_root=index_root_path,
        model_version=encoder.model_version,
        fingerprints=new_fingerprints,
    )
    manifest = _update_lance_manifest_incremental_stats(
        index_root_path=index_root_path,
        corpus_root=corpus_root,
        row_count=table.count_rows(),
        diff=diff,
        encoded_chunk_count=len(delta_chunk_ids),
        indexer_module=indexer,
    )
    _tick("manifest_updated", manifest["incremental_stats"])
    return IncrementalBuildResult(
        mode="incremental",
        manifest=manifest,
        diff_stats=manifest["incremental_stats"],
        encoded_chunk_count=len(delta_chunk_ids),
        fallback_reason=None,
        lance_version_before=lance_version_before,
        lance_version_after=lance_version_after,
    )


def incremental_build_index(
    *,
    model,  # SentenceTransformer-like
    model_id: str,
    embed_dim: int,
    index_root,  # Path | str
    corpus_root=None,
    progress=None,
    batch_size: int = 32,
) -> IncrementalBuildResult:
    """Re-encode only changed chunks, atomically merge into the index.

    Step order (designed so that any single failure leaves a recoverable
    state):

        1. Compute new corpus fingerprints
        2. Decide full vs incremental (manifest/schema sanity)
        3. If full: delegate to build_eval_index
        4. Diff against previous chunk_hashes sidecar
        5. Short-circuit when no changes (refresh manifest, return)
        6. Encode delta chunks (added + modified) via ``model.encode``
        7. Read prev row_id → chunk_id lookup from SQLite
        8. SQLite transaction: DELETE deleted+modified, INSERT
           added+modified — atomic at the SQL layer. New row_ids are
           captured for delta_row_ids.
        9. merge_dense_arrays: keep unchanged prev rows + delta rows
       10. atomic_save_dense_npz (tmp + rename; if step 8 succeeded
           but step 10 fails, the SQLite tx is committed but the
           dense file is the previous one — operator must
           force_rebuild to recover)
       11. atomic_save_chunk_hashes (final commit point for "next
           incremental call sees these fingerprints")
       12. Update manifest with new corpus_hash + diff_stats

    The ordering is "weakest atomic last": SQLite tx is the only true
    atomic operation, so it goes before file writes that can fail. If
    step 10 (dense write) fails after step 8 succeeded, the index is
    inconsistent. Plan §P5.6 documents this corner: in that rare case
    operator runs ``bin/cs-index-build --mode full`` to recover.

    Args:
        model: encoder with .encode() (SentenceTransformer-like).
        model_id / embed_dim: must match the existing manifest for
            the incremental path. Mismatch triggers full rebuild.
        index_root: index directory (e.g. state/cs_rag/).
        corpus_root: source corpus directory. Defaults lazily to
            corpus_loader.DEFAULT_CORPUS_ROOT.
        progress: optional ``(stage, info)`` callback.
        batch_size: forwarded to model.encode for the delta encoder.

    Returns:
        IncrementalBuildResult with mode + manifest + diff_stats.
    """
    import numpy as np  # type: ignore
    from . import corpus_loader, indexer

    def _tick(stage: str, info: dict | None = None) -> None:
        if progress is not None:
            progress(stage, info or {})

    corpus_root = _normalise_corpus_root(corpus_root)
    index_root_path = Path(index_root)

    # 1. Compute new corpus fingerprints
    _tick("load_corpus", {"corpus_root": str(corpus_root)})
    chunks = corpus_loader.load_corpus(corpus_root)
    if not chunks:
        raise RuntimeError(f"corpus at {corpus_root} is empty")
    new_chunks_by_id = {c.chunk_id: c for c in chunks}
    new_fingerprints = compute_chunk_fingerprints(chunks)
    _tick("corpus_loaded", {"chunk_count": len(chunks)})

    # 2. Full-rebuild gate
    fallback_reason = _full_rebuild_reason(
        index_root_path=index_root_path,
        model_id=model_id,
        embed_dim=embed_dim,
        indexer_module=indexer,
    )

    # 3. Full rebuild fallback
    if fallback_reason is not None:
        _tick("fallback_to_full", {"reason": fallback_reason})
        from .eval.index_builder import build_eval_index

        manifest = build_eval_index(
            model=model,
            model_id=model_id,
            embed_dim=embed_dim,
            index_root=index_root_path,
            corpus_root=corpus_root,
            batch_size=batch_size,
            progress=progress,
        )
        # Persist fingerprints so the next call can take the
        # incremental fast-path
        atomic_save_chunk_hashes(new_fingerprints, index_root_path)
        return IncrementalBuildResult(
            mode="full",
            manifest=manifest,
            diff_stats={
                "added": len(chunks),
                "modified": 0,
                "deleted": 0,
                "unchanged": 0,
            },
            encoded_chunk_count=len(chunks),
            fallback_reason=fallback_reason,
        )

    # 4. Diff
    old_fingerprints = load_chunk_hashes(index_root_path)
    diff = diff_chunks(old_fingerprints, new_fingerprints)
    _tick("diff", {
        "added": len(diff.added),
        "modified": len(diff.modified),
        "deleted": len(diff.deleted),
        "unchanged": len(diff.unchanged),
    })

    # 5. No-op short-circuit: refresh manifest with current corpus_hash
    # and return early. fingerprints are already aligned (load == compute).
    if diff.is_noop():
        _tick("noop", {})
        manifest_path = index_root_path / indexer.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["corpus_hash"] = corpus_loader.corpus_hash(corpus_root)
        manifest["incremental_stats"] = {
            "added": 0,
            "modified": 0,
            "deleted": 0,
            "unchanged": len(diff.unchanged),
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return IncrementalBuildResult(
            mode="incremental",
            manifest=manifest,
            diff_stats=manifest["incremental_stats"],
            encoded_chunk_count=0,
            fallback_reason=None,
        )

    # 6. Encode delta
    delta_chunk_ids = list(diff.needs_encoding)
    delta_chunks = [new_chunks_by_id[cid] for cid in delta_chunk_ids]
    delta_texts = [indexer._embed_text(c) for c in delta_chunks]
    _tick("encode_delta", {"count": len(delta_texts), "batch_size": batch_size})
    if delta_texts:
        # Use indexer._encode_all so encode-progress callbacks fire on
        # the same contract as full builds. Re-using the helper keeps
        # incremental + full encoding behavior identical.
        delta_embeddings = indexer._encode_all(
            model,
            delta_texts,
            progress=progress,
            encode_batch_size=batch_size,
        )
        if delta_embeddings.shape != (len(delta_texts), embed_dim):
            raise RuntimeError(
                f"unexpected delta shape {delta_embeddings.shape}, "
                f"expected ({len(delta_texts)}, {embed_dim})"
            )
    else:
        # Pure-delete case: still execute SQLite tx + dense rewrite to
        # drop deleted rows.
        delta_embeddings = np.zeros((0, embed_dim), dtype="float32")

    # 7. prev row_id → chunk_id lookup (read BEFORE the tx so deleted
    # rows are still observable for merge_dense_arrays' kept_mask)
    sqlite_path = index_root_path / indexer.SQLITE_NAME
    conn = indexer._open_sqlite(sqlite_path)
    try:
        prev_lookup = load_prev_chunk_id_lookup(conn)
        _tick("prev_lookup", {"row_count": len(prev_lookup)})

        # 8. SQLite tx (atomic at SQL layer)
        new_row_ids_dict = apply_chunk_diff_to_sqlite(
            conn, diff, new_chunks_by_id
        )
        _tick("sqlite_tx", {
            "inserted_count": len(new_row_ids_dict),
        })
    finally:
        conn.close()

    # 9. merge_dense_arrays
    delta_row_ids = [new_row_ids_dict[cid] for cid in delta_chunk_ids]
    prev_embeddings, prev_row_ids = indexer.load_dense(index_root_path)
    merged_embeddings, merged_row_ids = merge_dense_arrays(
        prev_embeddings=prev_embeddings,
        prev_row_ids=prev_row_ids,
        prev_chunk_id_by_row_id=prev_lookup,
        unchanged_chunk_ids=set(diff.unchanged),
        delta_chunk_ids=delta_chunk_ids,
        delta_embeddings=delta_embeddings,
        delta_row_ids=delta_row_ids,
    )
    _tick("dense_merged", {"shape": list(merged_embeddings.shape)})

    # 10. Atomic dense.npz write
    dense_path = index_root_path / indexer.DENSE_NAME
    atomic_save_dense_npz(dense_path, merged_embeddings, merged_row_ids)

    # 11. Atomic fingerprints write — final commit point for
    # "next incremental call sees these fingerprints"
    atomic_save_chunk_hashes(new_fingerprints, index_root_path)

    # 12. Manifest update
    manifest_path = index_root_path / indexer.MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["row_count"] = int(merged_embeddings.shape[0])
    manifest["corpus_hash"] = corpus_loader.corpus_hash(corpus_root)
    manifest["incremental_stats"] = {
        "added": len(diff.added),
        "modified": len(diff.modified),
        "deleted": len(diff.deleted),
        "unchanged": len(diff.unchanged),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _tick("manifest_updated", manifest["incremental_stats"])

    return IncrementalBuildResult(
        mode="incremental",
        manifest=manifest,
        diff_stats=manifest["incremental_stats"],
        encoded_chunk_count=len(delta_chunk_ids),
        fallback_reason=None,
    )

"""CS corpus indexer — SQLite FTS5 + dense vectors (numpy .npz).

Layout under ``state/cs_rag/``::

    index.sqlite3   — metadata + FTS5 virtual table
    dense.npz       — row_id-aligned dense embedding matrix
    manifest.json   — {corpus_hash, index_version, embed_model, row_count, ...}

Contracts
---------
- ``is_ready()`` checks file existence + manifest hash **without** importing
  sentence-transformers / torch. coach_run.py depends on this being safe to
  call on environments that have not yet run First-Run Protocol.
- ``build_index()`` loads sentence-transformers via lazy import so a missing
  dependency raises ``IndexDependencyMissing`` instead of crashing coach_run.
- The dense matrix is aligned by ``row_id`` = SQLite rowid of the chunk row.
  dense.npz stores {"embeddings": np.ndarray (N, D), "row_ids": np.ndarray (N,)}
  with ``row_ids[i] == i+1`` when built in a single pass. Searcher uses the
  row_ids array as ground truth in case of future partial rebuilds.

Corpus hash semantics
---------------------
``corpus_loader.corpus_hash`` is content-based (paths + sha1). Manifest stores
the hash at build time; ``is_ready`` compares it against the current hash.
A mismatch → ``state="stale"``.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from . import corpus_loader

# Default chunk size for encode-progress callbacks. Independent of
# ``model.encode``'s internal ``batch_size`` — we call encode() with a
# slice of this many texts so we can emit a progress callback between
# slices. 256 is small enough to feel responsive (a CPU encode of 256
# 1024-dim vectors finishes in seconds even on 0.6B-param models) but
# large enough that the callback overhead is negligible.
ENCODE_PROGRESS_CHUNK = 256

DEFAULT_INDEX_ROOT = Path("state/cs_rag")
SQLITE_NAME = "index.sqlite3"
DENSE_NAME = "dense.npz"
MANIFEST_NAME = "manifest.json"

INDEX_VERSION = 2  # bumped when chunks schema changed (added `difficulty` column).
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBED_DIM = 384


class IndexDependencyMissing(RuntimeError):
    """Raised when sentence-transformers/numpy cannot be imported at build time."""


@dataclass
class ReadinessReport:
    state: str           # "ready" | "missing" | "stale" | "corrupt"
    reason: str          # short tag: first_run / corpus_changed / index_corrupt / deps_missing
    corpus_hash: str | None
    index_manifest_hash: str | None
    next_command: str | None

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "reason": self.reason,
            "corpus_hash": self.corpus_hash,
            "index_manifest_hash": self.index_manifest_hash,
            "next_command": self.next_command,
        }


# ---------------------------------------------------------------------------
# Readiness — safe to call without ML deps
# ---------------------------------------------------------------------------

def _paths(index_root: Path) -> tuple[Path, Path, Path]:
    return (
        index_root / SQLITE_NAME,
        index_root / DENSE_NAME,
        index_root / MANIFEST_NAME,
    )


def is_ready(
    index_root: Path | str = DEFAULT_INDEX_ROOT,
    corpus_root: Path | str = corpus_loader.DEFAULT_CORPUS_ROOT,
) -> ReadinessReport:
    """Check whether the on-disk index is usable.

    Pure stdlib — does not load sentence-transformers.
    """
    root = Path(index_root)
    sqlite_path, dense_path, manifest_path = _paths(root)
    if not (sqlite_path.exists() and dense_path.exists() and manifest_path.exists()):
        return ReadinessReport(
            state="missing",
            reason="first_run",
            corpus_hash=None,
            index_manifest_hash=None,
            next_command="bin/cs-index-build",
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ReadinessReport(
            state="corrupt",
            reason="index_corrupt",
            corpus_hash=None,
            index_manifest_hash=None,
            next_command="bin/cs-index-build",
        )
    current_hash = corpus_loader.corpus_hash(corpus_root)
    stored_hash = manifest.get("corpus_hash")
    if stored_hash != current_hash:
        return ReadinessReport(
            state="stale",
            reason="corpus_changed",
            corpus_hash=current_hash,
            index_manifest_hash=stored_hash,
            next_command="bin/cs-index-build",
        )
    # Schema upgrades (e.g. v1 → v2 added the `difficulty` column) require a
    # rebuild even when the corpus content itself is unchanged. Without this,
    # searcher.py would crash on a SELECT against a column that does not
    # exist in the legacy table.
    if manifest.get("index_version") != INDEX_VERSION:
        return ReadinessReport(
            state="stale",
            reason="index_schema_changed",
            corpus_hash=current_hash,
            index_manifest_hash=stored_hash,
            next_command="bin/cs-index-build",
        )
    return ReadinessReport(
        state="ready",
        reason="ready",
        corpus_hash=current_hash,
        index_manifest_hash=stored_hash,
        next_command=None,
    )


# ---------------------------------------------------------------------------
# SQLite schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id          TEXT NOT NULL,
    chunk_id        TEXT NOT NULL UNIQUE,
    path            TEXT NOT NULL,
    title           TEXT NOT NULL,
    category        TEXT NOT NULL,
    section_title   TEXT NOT NULL,
    section_path    TEXT NOT NULL,  -- json array
    body            TEXT NOT NULL,
    char_len        INTEGER NOT NULL,
    anchors         TEXT NOT NULL,  -- json array
    difficulty      TEXT            -- "beginner"|"intermediate"|"advanced"|"expert"|NULL
);

CREATE INDEX IF NOT EXISTS chunks_category_idx ON chunks(category);
CREATE INDEX IF NOT EXISTS chunks_path_idx ON chunks(path);
-- chunks_difficulty_idx is created by _ensure_difficulty_column so legacy
-- v1 databases (which predate the column) can be ALTERed before the index
-- statement runs against a column that doesn't exist yet.

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    title, section_title, body,
    content='chunks',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, title, section_title, body)
    VALUES (new.id, new.title, new.section_title, new.body);
END;

CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, title, section_title, body)
    VALUES ('delete', old.id, old.title, old.section_title, old.body);
END;
"""


def _open_sqlite(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.executescript(_SCHEMA)
    _ensure_difficulty_column(conn)
    return conn


def _ensure_difficulty_column(conn: sqlite3.Connection) -> None:
    """Idempotent ALTER for legacy v1 databases.

    ``CREATE TABLE IF NOT EXISTS`` skips the new column on existing v1
    tables, so we add it manually when missing. New builds (where the
    table did not exist) already get the column from ``_SCHEMA`` and this
    is a cheap no-op.
    """
    cols = {row[1] for row in conn.execute("PRAGMA table_info(chunks)").fetchall()}
    if "difficulty" not in cols:
        conn.execute("ALTER TABLE chunks ADD COLUMN difficulty TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS chunks_difficulty_idx ON chunks(difficulty)")
    conn.commit()


def _insert_chunks(
    conn: sqlite3.Connection,
    chunks: list[corpus_loader.CorpusChunk],
) -> list[int]:
    """Insert chunks and return assigned row_ids in the same order."""
    row_ids: list[int] = []
    cur = conn.cursor()
    for chunk in chunks:
        cur.execute(
            """
            INSERT INTO chunks (
                doc_id, chunk_id, path, title, category,
                section_title, section_path, body, char_len, anchors,
                difficulty
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chunk.doc_id,
                chunk.chunk_id,
                chunk.path,
                chunk.title,
                chunk.category,
                chunk.section_title,
                json.dumps(chunk.section_path, ensure_ascii=False),
                chunk.body,
                chunk.char_len,
                json.dumps(chunk.anchors, ensure_ascii=False),
                chunk.difficulty,
            ),
        )
        row_ids.append(cur.lastrowid)
    conn.commit()
    return row_ids


# ---------------------------------------------------------------------------
# Build (requires ML deps — lazy imported)
# ---------------------------------------------------------------------------

def _load_embedder():
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError as exc:  # pragma: no cover - import path
        raise IndexDependencyMissing(
            "sentence-transformers not installed. Run `pip install -e .` first."
        ) from exc
    return SentenceTransformer(EMBED_MODEL)


def _encode_all(
    model,
    texts: list[str],
    *,
    progress=None,
    progress_chunk: int = ENCODE_PROGRESS_CHUNK,
    encode_batch_size: int = 32,
):
    """Encode ``texts`` via ``model.encode``, emitting periodic
    ``progress("encode_progress", info)`` callbacks so long sweeps
    surface % done + ETA instead of running blind.

    ``info`` shape::

        {
            "done": int,
            "total": int,
            "elapsed_s": float,
            "eta_s": float,
            "rate_per_s": float,
        }

    The encode is split into slices of ``progress_chunk`` texts; each
    slice goes to ``model.encode`` with the same ``batch_size`` /
    ``normalize_embeddings`` / ``convert_to_numpy`` settings the
    pre-progress code used. Behavior on the wire is identical
    (concatenated final array is bit-equivalent up to numpy
    concatenation order, which preserves input order).
    """
    try:
        import numpy as np  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise IndexDependencyMissing("numpy not installed.") from exc

    total = len(texts)
    if total == 0:
        return np.zeros((0, EMBED_DIM), dtype="float32")

    start = time.time()
    chunks_out: list = []
    for i in range(0, total, progress_chunk):
        slice_texts = texts[i : i + progress_chunk]
        embs = model.encode(
            slice_texts,
            batch_size=encode_batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        chunks_out.append(np.asarray(embs, dtype="float32"))
        done = min(i + len(slice_texts), total)
        if progress is not None:
            elapsed = time.time() - start
            rate = (done / elapsed) if elapsed > 0 else 0.0
            eta = ((total - done) / rate) if rate > 0 else 0.0
            try:
                progress("encode_progress", {
                    "done": done,
                    "total": total,
                    "elapsed_s": round(elapsed, 1),
                    "eta_s": round(eta, 1),
                    "rate_per_s": round(rate, 2),
                })
            except Exception:
                # Progress callback errors must never break the encode.
                pass
    return np.concatenate(chunks_out, axis=0)


def build_index(
    index_root: Path | str = DEFAULT_INDEX_ROOT,
    corpus_root: Path | str = corpus_loader.DEFAULT_CORPUS_ROOT,
    *,
    progress: callable | None = None,  # type: ignore[valid-type]
) -> dict:
    """Build the index from scratch. Returns the manifest dict.

    ``progress`` is a callback ``(stage: str, info: dict) -> None`` used by
    bin/cs-index-build to stream Korean status lines to the learner.
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

    # Clean slate — partial rebuilds come later.
    for p in (sqlite_path, dense_path, manifest_path):
        if p.exists():
            p.unlink()

    _tick("load_corpus", {})
    chunks = corpus_loader.load_corpus(corpus_root)
    if not chunks:
        raise RuntimeError(f"corpus at {corpus_root} is empty")
    _tick("load_corpus_done", {"chunk_count": len(chunks)})

    _tick("open_sqlite", {})
    conn = _open_sqlite(sqlite_path)
    try:
        _tick("insert_chunks", {"count": len(chunks)})
        row_ids = _insert_chunks(conn, chunks)

        _tick("load_embedder", {"model": EMBED_MODEL})
        embedder = _load_embedder()

        _tick("encode", {"count": len(chunks)})
        texts = [_embed_text(chunk) for chunk in chunks]
        embeddings = _encode_all(embedder, texts, progress=progress)
        if embeddings.shape != (len(chunks), EMBED_DIM):
            raise RuntimeError(
                f"unexpected embedding shape {embeddings.shape}, "
                f"expected ({len(chunks)}, {EMBED_DIM})"
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
        "embed_model": EMBED_MODEL,
        "embed_dim": EMBED_DIM,
        "row_count": len(chunks),
        "corpus_hash": corpus_loader.corpus_hash(corpus_root),
        "corpus_root": str(corpus_root),
    }
    _tick("write_manifest", manifest)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def _embed_text(chunk: corpus_loader.CorpusChunk) -> str:
    """Compose the text fed to the embedder: title + section + body."""
    head = " > ".join(chunk.section_path) if chunk.section_path else chunk.title
    return f"{head}\n\n{chunk.body}"


# ---------------------------------------------------------------------------
# Read-only accessors used by searcher
# ---------------------------------------------------------------------------

def open_readonly(
    index_root: Path | str = DEFAULT_INDEX_ROOT,
) -> sqlite3.Connection:
    path = Path(index_root) / SQLITE_NAME
    if not path.exists():
        raise FileNotFoundError(str(path))
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def load_dense(index_root: Path | str = DEFAULT_INDEX_ROOT):
    """Return ``(embeddings: np.ndarray, row_ids: np.ndarray)``.

    Lazy-imports numpy so is_ready callers do not pay the cost.
    """
    import numpy as np  # type: ignore

    path = Path(index_root) / DENSE_NAME
    with np.load(path) as data:
        return np.asarray(data["embeddings"]), np.asarray(data["row_ids"])


def load_manifest(index_root: Path | str = DEFAULT_INDEX_ROOT) -> dict:
    path = Path(index_root) / MANIFEST_NAME
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_chunks_by_rowid(
    conn: sqlite3.Connection, row_ids: Iterable[int]
) -> dict[int, dict]:
    rows = list(row_ids)
    if not rows:
        return {}
    placeholders = ",".join("?" for _ in rows)
    cur = conn.execute(
        f"""
        SELECT id, doc_id, chunk_id, path, title, category,
               section_title, section_path, body, char_len, anchors,
               difficulty
        FROM chunks WHERE id IN ({placeholders})
        """,
        rows,
    )
    out: dict[int, dict] = {}
    for row in cur.fetchall():
        out[row[0]] = {
            "row_id": row[0],
            "doc_id": row[1],
            "chunk_id": row[2],
            "path": row[3],
            "title": row[4],
            "category": row[5],
            "section_title": row[6],
            "section_path": json.loads(row[7]),
            "body": row[8],
            "char_len": row[9],
            "anchors": json.loads(row[10]),
            "difficulty": row[11],
        }
    return out

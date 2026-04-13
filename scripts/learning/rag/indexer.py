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
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from . import corpus_loader

DEFAULT_INDEX_ROOT = Path("state/cs_rag")
SQLITE_NAME = "index.sqlite3"
DENSE_NAME = "dense.npz"
MANIFEST_NAME = "manifest.json"

INDEX_VERSION = 1
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
    anchors         TEXT NOT NULL   -- json array
);

CREATE INDEX IF NOT EXISTS chunks_category_idx ON chunks(category);
CREATE INDEX IF NOT EXISTS chunks_path_idx ON chunks(path);

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
    return conn


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
                section_title, section_path, body, char_len, anchors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


def _encode_all(model, texts: list[str]):
    try:
        import numpy as np  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise IndexDependencyMissing("numpy not installed.") from exc
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return np.asarray(embeddings, dtype="float32")


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
        embeddings = _encode_all(embedder, texts)
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
               section_title, section_path, body, char_len, anchors
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
        }
    return out

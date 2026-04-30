"""Unit tests for scripts.learning.rag.incremental_indexer.

Coverage targets:
- fingerprint_for_chunk is stable for identical content + position
- fingerprint changes when body changes
- fingerprint changes when section_path changes (structural move)
- compute_chunk_fingerprints returns one entry per chunk_id
- ChunkDiff.added/modified/deleted/unchanged classification
- ChunkDiff sorted output for determinism
- ChunkDiff.is_noop when both snapshots equal
- ChunkDiff.needs_encoding = added + modified union
- load_chunk_hashes returns {} for missing sidecar
- save → load round-trip preserves all entries
- diff handles empty old (first build = all added)
- diff handles empty new (corpus deleted = all deleted)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.learning.rag.corpus_loader import CorpusChunk
from scripts.learning.rag import incremental_indexer as I


def _chunk(
    *,
    chunk_id: str = "doc1#0",
    doc_id: str = "doc1",
    body: str = "본문 텍스트",
    section_path: tuple[str, ...] = ("H1 Title", "H2 Section"),
    path: str = "contents/spring/bean.md",
) -> CorpusChunk:
    return CorpusChunk(
        doc_id=doc_id,
        chunk_id=chunk_id,
        path=path,
        title="H1 Title",
        category="spring",
        section_title=section_path[-1] if section_path else "",
        section_path=list(section_path),
        body=body,
        char_len=len(body),
    )


# ---------------------------------------------------------------------------
# fingerprint_for_chunk
# ---------------------------------------------------------------------------

def test_fingerprint_stable_for_identical_chunks():
    a = _chunk()
    b = _chunk()
    assert I.fingerprint_for_chunk(a) == I.fingerprint_for_chunk(b)


def test_fingerprint_changes_when_body_changes():
    a = _chunk(body="원본")
    b = _chunk(body="수정본")
    assert I.fingerprint_for_chunk(a) != I.fingerprint_for_chunk(b)


def test_fingerprint_changes_when_section_path_changes():
    a = _chunk(section_path=("H1", "Old Section"))
    b = _chunk(section_path=("H1", "New Section"))
    assert I.fingerprint_for_chunk(a) != I.fingerprint_for_chunk(b)


def test_fingerprint_is_hex_sha1():
    fp = I.fingerprint_for_chunk(_chunk())
    assert len(fp) == 40
    int(fp, 16)  # valid hex; raises if not


def test_fingerprint_unaffected_by_unrelated_fields():
    """char_len, anchors, difficulty don't participate in fingerprinting —
    they're derived/metadata, not content."""
    a = _chunk()
    b = CorpusChunk(
        doc_id=a.doc_id,
        chunk_id=a.chunk_id,
        path=a.path,
        title=a.title,
        category=a.category,
        section_title=a.section_title,
        section_path=list(a.section_path),
        body=a.body,
        char_len=99999,  # different
        anchors=["x", "y"],  # different
        difficulty="advanced",  # different
    )
    assert I.fingerprint_for_chunk(a) == I.fingerprint_for_chunk(b)


# ---------------------------------------------------------------------------
# compute_chunk_fingerprints
# ---------------------------------------------------------------------------

def test_compute_returns_one_entry_per_chunk():
    chunks = [_chunk(chunk_id="a"), _chunk(chunk_id="b"), _chunk(chunk_id="c")]
    fps = I.compute_chunk_fingerprints(chunks)
    assert set(fps) == {"a", "b", "c"}
    assert all(len(v) == 40 for v in fps.values())


def test_compute_handles_empty_iterable():
    assert I.compute_chunk_fingerprints([]) == {}


# ---------------------------------------------------------------------------
# ChunkDiff classification
# ---------------------------------------------------------------------------

def test_diff_classifies_added_modified_deleted_unchanged():
    old = {"a": "fp_a", "b": "fp_b_old", "c": "fp_c"}
    new = {"b": "fp_b_new", "c": "fp_c", "d": "fp_d"}
    diff = I.diff_chunks(old, new)
    assert diff.added == ("d",)
    assert diff.modified == ("b",)
    assert diff.deleted == ("a",)
    assert diff.unchanged == ("c",)


def test_diff_first_build_all_added():
    """Empty old fingerprints = first ever build → everything new is added."""
    new = {"a": "x", "b": "y"}
    diff = I.diff_chunks({}, new)
    assert diff.added == ("a", "b")
    assert diff.modified == ()
    assert diff.deleted == ()
    assert diff.unchanged == ()


def test_diff_corpus_emptied_all_deleted():
    """Empty new fingerprints = corpus removed → everything is deleted."""
    old = {"a": "x", "b": "y"}
    diff = I.diff_chunks(old, {})
    assert diff.added == ()
    assert diff.modified == ()
    assert diff.deleted == ("a", "b")
    assert diff.unchanged == ()


def test_diff_no_changes_is_noop():
    same = {"a": "fp_a", "b": "fp_b"}
    diff = I.diff_chunks(same, dict(same))
    assert diff.is_noop() is True
    assert diff.total_changed == 0
    assert diff.reuse_count == 2
    assert diff.unchanged == ("a", "b")


def test_diff_lists_are_sorted_for_determinism():
    """Insertion order should not affect diff output — sorted lists."""
    old = {"z": "fp_z", "m": "fp_m", "a": "fp_a"}
    new = {"a": "fp_a", "z": "fp_z_changed", "x": "fp_x"}
    diff = I.diff_chunks(old, new)
    assert diff.added == ("x",)
    assert diff.modified == ("z",)
    assert diff.deleted == ("m",)
    assert diff.unchanged == ("a",)


def test_diff_total_changed_sums_three_categories():
    diff = I.ChunkDiff(
        added=("a", "b"),
        modified=("c",),
        deleted=("d", "e", "f"),
        unchanged=("g", "h"),
    )
    assert diff.total_changed == 6
    assert diff.reuse_count == 2


def test_diff_needs_encoding_unions_added_and_modified():
    diff = I.ChunkDiff(
        added=("a", "b"),
        modified=("b", "c"),  # 'b' overlap intentional in this test
        deleted=("d",),
        unchanged=("e",),
    )
    # Real diff_chunks() never produces overlap, but the property
    # contract is still well-defined: union, sorted.
    assert diff.needs_encoding == ("a", "b", "c")


def test_diff_needs_encoding_empty_when_only_unchanged():
    diff = I.ChunkDiff(added=(), modified=(), deleted=(), unchanged=("a", "b"))
    assert diff.needs_encoding == ()
    assert diff.is_noop() is True


# ---------------------------------------------------------------------------
# Sidecar I/O
# ---------------------------------------------------------------------------

def test_load_chunk_hashes_returns_empty_for_missing_file(tmp_path):
    assert I.load_chunk_hashes(tmp_path) == {}


def test_save_then_load_round_trips(tmp_path):
    fps = {"a": "fp_a", "b": "fp_b", "c": "fp_c"}
    I.save_chunk_hashes(fps, tmp_path)
    loaded = I.load_chunk_hashes(tmp_path)
    assert loaded == fps


def test_save_creates_parent_dir(tmp_path):
    target = tmp_path / "nested" / "deep"
    I.save_chunk_hashes({"a": "x"}, target)
    assert (target / I.CHUNK_HASHES_NAME).exists()


def test_save_writes_sorted_keys_for_diffability(tmp_path):
    """File on disk should have keys sorted so git diff is meaningful
    (even when the file is gitignored, human review remains tractable)."""
    fps = {"z": "1", "a": "2", "m": "3"}
    I.save_chunk_hashes(fps, tmp_path)
    raw = (tmp_path / I.CHUNK_HASHES_NAME).read_text(encoding="utf-8")
    parsed = json.loads(raw)
    keys = list(parsed.keys())
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# Integration: compute → diff
# ---------------------------------------------------------------------------

def test_integration_compute_then_diff_finds_added():
    old_chunks = [_chunk(chunk_id="doc1#0"), _chunk(chunk_id="doc1#1")]
    new_chunks = [
        _chunk(chunk_id="doc1#0"),
        _chunk(chunk_id="doc1#1"),
        _chunk(chunk_id="doc2#0", path="contents/spring/ioc.md"),
    ]
    old_fp = I.compute_chunk_fingerprints(old_chunks)
    new_fp = I.compute_chunk_fingerprints(new_chunks)
    diff = I.diff_chunks(old_fp, new_fp)
    assert diff.added == ("doc2#0",)
    assert diff.modified == ()
    assert diff.deleted == ()


def test_integration_modified_when_body_changes():
    old_chunks = [_chunk(chunk_id="doc1#0", body="원본")]
    new_chunks = [_chunk(chunk_id="doc1#0", body="수정본")]
    old_fp = I.compute_chunk_fingerprints(old_chunks)
    new_fp = I.compute_chunk_fingerprints(new_chunks)
    diff = I.diff_chunks(old_fp, new_fp)
    assert diff.modified == ("doc1#0",)
    assert diff.added == ()
    assert diff.deleted == ()


# ---------------------------------------------------------------------------
# merge_dense_arrays
# ---------------------------------------------------------------------------

import numpy as np  # noqa: E402


def test_merge_dense_keeps_unchanged_and_appends_delta():
    prev_emb = np.array([[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]], dtype="float32")
    prev_ids = np.array([10, 20, 30], dtype="int64")
    prev_lookup = {10: "a", 20: "b", 30: "c"}
    delta_emb = np.array([[0.7, 0.3]], dtype="float32")
    delta_ids = [40]
    delta_chunk_ids = ["d"]

    merged_emb, merged_ids = I.merge_dense_arrays(
        prev_embeddings=prev_emb,
        prev_row_ids=prev_ids,
        prev_chunk_id_by_row_id=prev_lookup,
        unchanged_chunk_ids={"a", "c"},  # b dropped (modified or deleted)
        delta_chunk_ids=delta_chunk_ids,
        delta_embeddings=delta_emb,
        delta_row_ids=delta_ids,
    )

    # Kept: a (rid=10), c (rid=30); Delta: d (rid=40)
    assert merged_ids.tolist() == [10, 30, 40]
    np.testing.assert_array_equal(merged_emb[0], prev_emb[0])  # a
    np.testing.assert_array_equal(merged_emb[1], prev_emb[2])  # c
    np.testing.assert_array_equal(merged_emb[2], delta_emb[0])  # d


def test_merge_dense_first_build_only_delta():
    """Empty prev = first ever build. Result = delta verbatim."""
    prev_emb = np.zeros((0, 4), dtype="float32")
    prev_ids = np.array([], dtype="int64")
    delta_emb = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype="float32")
    delta_ids = [1, 2]

    merged_emb, merged_ids = I.merge_dense_arrays(
        prev_embeddings=prev_emb,
        prev_row_ids=prev_ids,
        prev_chunk_id_by_row_id={},
        unchanged_chunk_ids=set(),
        delta_chunk_ids=["a", "b"],
        delta_embeddings=delta_emb,
        delta_row_ids=delta_ids,
    )
    assert merged_ids.tolist() == [1, 2]
    np.testing.assert_array_equal(merged_emb, delta_emb)


def test_merge_dense_pure_delete_keeps_unchanged_only():
    """No delta = pure delete. Some prev rows dropped, others kept."""
    prev_emb = np.array([[1, 0], [0, 1]], dtype="float32")
    prev_ids = np.array([10, 20], dtype="int64")
    prev_lookup = {10: "keep", 20: "drop"}

    merged_emb, merged_ids = I.merge_dense_arrays(
        prev_embeddings=prev_emb,
        prev_row_ids=prev_ids,
        prev_chunk_id_by_row_id=prev_lookup,
        unchanged_chunk_ids={"keep"},
        delta_chunk_ids=[],
        delta_embeddings=np.zeros((0, 2), dtype="float32"),
        delta_row_ids=[],
    )
    assert merged_ids.tolist() == [10]
    np.testing.assert_array_equal(merged_emb, prev_emb[0:1])


def test_merge_dense_sorted_by_row_id_for_determinism():
    """Even if delta_row_ids interleave with kept row_ids, result is
    sorted by row_id ascending (deterministic on-disk layout)."""
    prev_emb = np.array([[1, 0], [0, 1]], dtype="float32")
    prev_ids = np.array([10, 30], dtype="int64")
    prev_lookup = {10: "a", 30: "c"}
    delta_emb = np.array([[0.5, 0.5]], dtype="float32")
    delta_ids = [20]  # interleaves between 10 and 30

    merged_emb, merged_ids = I.merge_dense_arrays(
        prev_embeddings=prev_emb,
        prev_row_ids=prev_ids,
        prev_chunk_id_by_row_id=prev_lookup,
        unchanged_chunk_ids={"a", "c"},
        delta_chunk_ids=["b"],
        delta_embeddings=delta_emb,
        delta_row_ids=delta_ids,
    )
    assert merged_ids.tolist() == [10, 20, 30]


def test_merge_dense_dim_mismatch_raises():
    prev_emb = np.zeros((1, 4), dtype="float32")
    delta_emb = np.zeros((1, 8), dtype="float32")
    with pytest.raises(ValueError, match="dim mismatch"):
        I.merge_dense_arrays(
            prev_embeddings=prev_emb,
            prev_row_ids=np.array([10], dtype="int64"),
            prev_chunk_id_by_row_id={10: "a"},
            unchanged_chunk_ids={"a"},
            delta_chunk_ids=["b"],
            delta_embeddings=delta_emb,
            delta_row_ids=[20],
        )


def test_merge_dense_row_count_mismatch_raises():
    with pytest.raises(ValueError, match="prev shape mismatch"):
        I.merge_dense_arrays(
            prev_embeddings=np.zeros((2, 4), dtype="float32"),
            prev_row_ids=np.array([10], dtype="int64"),  # only 1 id
            prev_chunk_id_by_row_id={10: "a"},
            unchanged_chunk_ids={"a"},
            delta_chunk_ids=[],
            delta_embeddings=np.zeros((0, 4), dtype="float32"),
            delta_row_ids=[],
        )


def test_merge_dense_delta_length_mismatch_raises():
    with pytest.raises(ValueError, match="delta length mismatch"):
        I.merge_dense_arrays(
            prev_embeddings=np.zeros((0, 4), dtype="float32"),
            prev_row_ids=np.array([], dtype="int64"),
            prev_chunk_id_by_row_id={},
            unchanged_chunk_ids=set(),
            delta_chunk_ids=["a", "b"],  # 2 ids
            delta_embeddings=np.zeros((1, 4), dtype="float32"),  # 1 emb
            delta_row_ids=[10, 20],
        )


def test_merge_dense_dtype_normalization():
    """Output is float32 / int64 regardless of input dtype."""
    prev_emb = np.zeros((1, 2), dtype="float64")  # wrong dtype intentionally
    prev_ids = np.array([10], dtype="int32")
    delta_emb = np.zeros((1, 2), dtype="float64")
    merged_emb, merged_ids = I.merge_dense_arrays(
        prev_embeddings=prev_emb,
        prev_row_ids=prev_ids,
        prev_chunk_id_by_row_id={10: "a"},
        unchanged_chunk_ids={"a"},
        delta_chunk_ids=["b"],
        delta_embeddings=delta_emb,
        delta_row_ids=[20],
    )
    assert merged_emb.dtype == np.float32
    assert merged_ids.dtype == np.int64


# ---------------------------------------------------------------------------
# atomic_save_dense_npz / atomic_save_chunk_hashes
# ---------------------------------------------------------------------------

def test_atomic_save_dense_creates_file_and_round_trips(tmp_path):
    target = tmp_path / "dense.npz"
    emb = np.array([[1.0, 0.0], [0.5, 0.5]], dtype="float32")
    ids = np.array([10, 20], dtype="int64")

    I.atomic_save_dense_npz(target, emb, ids)
    assert target.exists()

    with np.load(target) as data:
        np.testing.assert_array_equal(data["embeddings"], emb)
        np.testing.assert_array_equal(data["row_ids"], ids)


def test_atomic_save_dense_overwrites_existing(tmp_path):
    target = tmp_path / "dense.npz"
    emb1 = np.zeros((1, 2), dtype="float32")
    emb2 = np.ones((3, 2), dtype="float32")

    I.atomic_save_dense_npz(target, emb1, np.array([1], dtype="int64"))
    I.atomic_save_dense_npz(target, emb2, np.array([1, 2, 3], dtype="int64"))

    with np.load(target) as data:
        assert data["embeddings"].shape == (3, 2)
        assert data["row_ids"].tolist() == [1, 2, 3]


def test_atomic_save_dense_no_tmp_left_on_success(tmp_path):
    target = tmp_path / "dense.npz"
    I.atomic_save_dense_npz(
        target,
        np.zeros((1, 2), dtype="float32"),
        np.array([1], dtype="int64"),
    )
    # Tmp variant should be cleaned up
    assert not (tmp_path / "dense.npz.tmp").exists()


def test_atomic_save_dense_creates_parent_dir(tmp_path):
    nested = tmp_path / "a" / "b" / "c" / "dense.npz"
    I.atomic_save_dense_npz(
        nested,
        np.zeros((1, 2), dtype="float32"),
        np.array([1], dtype="int64"),
    )
    assert nested.exists()


def test_atomic_save_dense_keeps_original_when_write_fails(tmp_path, monkeypatch):
    """If np.savez raises mid-write, the original file should be
    intact (atomic rename hasn't happened yet)."""
    target = tmp_path / "dense.npz"
    # First, write a known-good baseline
    baseline = np.array([[1.0]], dtype="float32")
    I.atomic_save_dense_npz(target, baseline, np.array([1], dtype="int64"))

    # Now patch np.savez to raise mid-write
    real_savez = np.savez

    def boom(*args, **kwargs):
        # Write enough so tmp file exists, then bail
        real_savez(*args, **kwargs)
        raise RuntimeError("simulated mid-write failure")

    monkeypatch.setattr(np, "savez", boom)

    with pytest.raises(RuntimeError, match="simulated"):
        I.atomic_save_dense_npz(
            target,
            np.zeros((10, 1), dtype="float32"),
            np.array(list(range(10)), dtype="int64"),
        )

    # Original file unchanged
    with np.load(target) as data:
        np.testing.assert_array_equal(data["embeddings"], baseline)

    # No leftover tmp
    assert not (tmp_path / "dense.npz.tmp").exists()


def test_atomic_save_chunk_hashes_round_trips(tmp_path):
    fps = {"a": "fp1", "b": "fp2"}
    I.atomic_save_chunk_hashes(fps, tmp_path)

    loaded = I.load_chunk_hashes(tmp_path)
    assert loaded == fps
    # No leftover tmp
    assert not (tmp_path / (I.CHUNK_HASHES_NAME + ".tmp")).exists()


def test_atomic_save_chunk_hashes_overwrites(tmp_path):
    I.atomic_save_chunk_hashes({"a": "v1"}, tmp_path)
    I.atomic_save_chunk_hashes({"a": "v2", "b": "v3"}, tmp_path)
    loaded = I.load_chunk_hashes(tmp_path)
    assert loaded == {"a": "v2", "b": "v3"}


def test_atomic_save_chunk_hashes_keeps_original_on_failure(tmp_path, monkeypatch):
    # Baseline
    I.atomic_save_chunk_hashes({"keep": "me"}, tmp_path)

    # Force write_text to fail
    real_write_text = Path.write_text

    def boom(self, *args, **kwargs):
        if self.name.endswith(".tmp"):
            real_write_text(self, *args, **kwargs)
            raise IOError("simulated write failure")
        return real_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", boom)

    with pytest.raises(IOError, match="simulated"):
        I.atomic_save_chunk_hashes({"new": "data"}, tmp_path)

    # Original preserved
    loaded = I.load_chunk_hashes(tmp_path)
    assert loaded == {"keep": "me"}
    # Tmp cleaned up
    assert not (tmp_path / (I.CHUNK_HASHES_NAME + ".tmp")).exists()


# ---------------------------------------------------------------------------
# SQLite tx (apply_chunk_diff_to_sqlite + load_prev_chunk_id_lookup)
# ---------------------------------------------------------------------------

import sqlite3

from scripts.learning.rag import indexer  # for _open_sqlite + schema


@pytest.fixture
def sqlite_conn(tmp_path):
    """Open a fresh in-file SQLite with full chunks + FTS schema."""
    conn = indexer._open_sqlite(tmp_path / "idx.sqlite3")
    yield conn
    conn.close()


def _add_chunk_to_db(conn, chunk):
    """Helper: insert a chunk via the production INSERT SQL."""
    cur = conn.cursor()
    import json as _json

    cur.execute(
        I._INSERT_CHUNK_SQL,
        (
            chunk.doc_id, chunk.chunk_id, chunk.path, chunk.title,
            chunk.category, chunk.section_title,
            _json.dumps(chunk.section_path, ensure_ascii=False),
            chunk.body, chunk.char_len,
            _json.dumps(chunk.anchors, ensure_ascii=False),
            chunk.difficulty,
        ),
    )
    conn.commit()
    return cur.lastrowid


def test_load_prev_chunk_id_lookup_returns_row_id_to_chunk_id(sqlite_conn):
    rid_a = _add_chunk_to_db(sqlite_conn, _chunk(chunk_id="a"))
    rid_b = _add_chunk_to_db(sqlite_conn, _chunk(chunk_id="b"))
    lookup = I.load_prev_chunk_id_lookup(sqlite_conn)
    assert lookup == {rid_a: "a", rid_b: "b"}


def test_load_prev_chunk_id_lookup_empty_for_fresh_db(sqlite_conn):
    assert I.load_prev_chunk_id_lookup(sqlite_conn) == {}


def test_apply_diff_inserts_added_chunks(sqlite_conn):
    diff = I.ChunkDiff(
        added=("new1", "new2"),
        modified=(),
        deleted=(),
        unchanged=(),
    )
    new_chunks = {
        "new1": _chunk(chunk_id="new1"),
        "new2": _chunk(chunk_id="new2"),
    }
    inserted = I.apply_chunk_diff_to_sqlite(sqlite_conn, diff, new_chunks)
    assert set(inserted) == {"new1", "new2"}
    # Both rows exist
    rows = list(sqlite_conn.execute("SELECT chunk_id FROM chunks ORDER BY id"))
    assert [r[0] for r in rows] == ["new1", "new2"]


def test_apply_diff_deletes_chunks(sqlite_conn):
    rid_a = _add_chunk_to_db(sqlite_conn, _chunk(chunk_id="a"))
    rid_b = _add_chunk_to_db(sqlite_conn, _chunk(chunk_id="b"))
    diff = I.ChunkDiff(added=(), modified=(), deleted=("a",), unchanged=("b",))
    inserted = I.apply_chunk_diff_to_sqlite(sqlite_conn, diff, {})
    assert inserted == {}
    remaining = [r[0] for r in sqlite_conn.execute("SELECT chunk_id FROM chunks")]
    assert remaining == ["b"]


def test_apply_diff_modifies_chunks(sqlite_conn):
    """Modified chunks should be deleted then re-inserted with new row_id."""
    rid_orig = _add_chunk_to_db(sqlite_conn, _chunk(chunk_id="m", body="old body"))

    diff = I.ChunkDiff(added=(), modified=("m",), deleted=(), unchanged=())
    new_chunks = {"m": _chunk(chunk_id="m", body="new body content here long")}
    inserted = I.apply_chunk_diff_to_sqlite(sqlite_conn, diff, new_chunks)

    # New row_id assigned (≠ original)
    assert "m" in inserted
    assert inserted["m"] != rid_orig
    # Body updated
    body = sqlite_conn.execute(
        "SELECT body FROM chunks WHERE chunk_id = ?", ("m",)
    ).fetchone()[0]
    assert body == "new body content here long"


def test_apply_diff_combined_added_modified_deleted(sqlite_conn):
    rid_keep = _add_chunk_to_db(sqlite_conn, _chunk(chunk_id="keep"))
    rid_drop = _add_chunk_to_db(sqlite_conn, _chunk(chunk_id="drop"))
    rid_old = _add_chunk_to_db(sqlite_conn, _chunk(chunk_id="m", body="old"))

    diff = I.ChunkDiff(
        added=("new1",),
        modified=("m",),
        deleted=("drop",),
        unchanged=("keep",),
    )
    new_chunks = {
        "new1": _chunk(chunk_id="new1"),
        "m": _chunk(chunk_id="m", body="updated content thats long enough"),
    }
    inserted = I.apply_chunk_diff_to_sqlite(sqlite_conn, diff, new_chunks)

    assert set(inserted) == {"new1", "m"}

    final_ids = {
        r[0] for r in sqlite_conn.execute("SELECT chunk_id FROM chunks")
    }
    assert final_ids == {"keep", "new1", "m"}


def test_apply_diff_rollback_on_missing_chunk(sqlite_conn):
    """If new_chunks_by_id is missing an added chunk_id, the function
    must rollback so partial inserts don't leak into the DB."""
    rid_a = _add_chunk_to_db(sqlite_conn, _chunk(chunk_id="a"))

    diff = I.ChunkDiff(
        added=("new1", "missing"),
        modified=(),
        deleted=(),
        unchanged=("a",),
    )
    new_chunks = {"new1": _chunk(chunk_id="new1")}  # 'missing' absent

    with pytest.raises(KeyError):
        I.apply_chunk_diff_to_sqlite(sqlite_conn, diff, new_chunks)

    # 'a' still there, 'new1' rolled back, 'missing' never inserted
    final_ids = {
        r[0] for r in sqlite_conn.execute("SELECT chunk_id FROM chunks")
    }
    assert final_ids == {"a"}


def test_apply_diff_chunks_fts_stays_in_sync(sqlite_conn):
    """The AI/AD triggers in indexer._SCHEMA keep chunks_fts in sync.
    After diff apply, FTS5 MATCH must find newly inserted chunks and
    miss deleted ones."""
    _add_chunk_to_db(sqlite_conn, _chunk(chunk_id="a", body="알파 본문 길이 충분"))
    _add_chunk_to_db(sqlite_conn, _chunk(chunk_id="b", body="베타 본문"))

    diff = I.ChunkDiff(
        added=("c",),
        modified=(),
        deleted=("a",),
        unchanged=("b",),
    )
    new_chunks = {
        "c": _chunk(chunk_id="c", body="감마 본문 텍스트 길게 작성됨 매우 길게"),
    }
    I.apply_chunk_diff_to_sqlite(sqlite_conn, diff, new_chunks)

    # 'a' deleted → FTS won't match
    a_hits = list(sqlite_conn.execute(
        "SELECT chunks.chunk_id FROM chunks JOIN chunks_fts "
        "ON chunks.id = chunks_fts.rowid WHERE chunks_fts MATCH ?",
        ("알파",),
    ))
    assert not a_hits

    # 'c' inserted → FTS matches
    c_hits = [r[0] for r in sqlite_conn.execute(
        "SELECT chunks.chunk_id FROM chunks JOIN chunks_fts "
        "ON chunks.id = chunks_fts.rowid WHERE chunks_fts MATCH ?",
        ("감마",),
    )]
    assert "c" in c_hits

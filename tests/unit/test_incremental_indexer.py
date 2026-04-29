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

"""Unit tests for scripts.learning.rag.eval.cleanup.

Coverage targets:
- Index dir is always removed (control + upgrade alike)
- HF cache is removed for upgrades when drop_hf_cache=True
- HF cache is NEVER removed for control (production safety)
- Missing dirs handled gracefully (0 MB freed)
- drop_hf_cache=False keeps the cache
- Bytes-freed accounting matches what was on disk
- hf_cache_dir_for replaces "/" with "--"
- total_freed_mb sums both classes
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.learning.rag.eval import cleanup as CL


@dataclass(frozen=True)
class _Candidate:
    """Duck-typed EmbeddingCandidate for tests."""

    candidate_id: str
    hf_model_id: str
    is_control: bool

    def index_dir_name(self) -> str:
        return self.candidate_id


def _populate_dir(path: Path, *, file_size_kb: int = 100) -> int:
    """Create a directory with a single file of ``file_size_kb`` KB.

    Returns the actual byte count for cross-checking.
    """
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / "data.bin"
    blob = b"\x00" * (file_size_kb * 1024)
    file_path.write_bytes(blob)
    return len(blob)


# ---------------------------------------------------------------------------
# hf_cache_dir_for naming
# ---------------------------------------------------------------------------

def test_hf_cache_dir_for_replaces_slash():
    p = CL.hf_cache_dir_for("BAAI/bge-m3", root=Path("/cache/hub"))
    assert p == Path("/cache/hub/models--BAAI--bge-m3")


def test_hf_cache_dir_for_handles_no_slash_id():
    p = CL.hf_cache_dir_for("flat-id", root=Path("/cache"))
    assert p == Path("/cache/models--flat-id")


# ---------------------------------------------------------------------------
# Cleanup behaviour
# ---------------------------------------------------------------------------

def test_cleanup_removes_index_for_upgrade(tmp_path):
    base = tmp_path / "ab"
    cache_root = tmp_path / "hf_cache"

    cand = _Candidate("up1", "org/up1", is_control=False)
    _populate_dir(base / "up1", file_size_kb=200)
    _populate_dir(cache_root / "models--org--up1", file_size_kb=300)

    report = CL.cleanup_candidate_artifacts(
        cand, base_dir=base, drop_hf_cache=True, hf_cache_root=cache_root
    )

    # Index dir gone
    assert not (base / "up1").exists()
    # HF cache gone
    assert not (cache_root / "models--org--up1").exists()
    # Bytes freed reported
    assert report.index_dir_freed_mb > 0
    assert report.hf_cache_freed_mb > 0
    assert report.skipped_hf_cache_due_to_control is False


def test_cleanup_preserves_hf_cache_for_control(tmp_path):
    base = tmp_path / "ab"
    cache_root = tmp_path / "hf_cache"

    cand = _Candidate("ctrl", "org/ctrl", is_control=True)
    _populate_dir(base / "ctrl", file_size_kb=200)
    _populate_dir(cache_root / "models--org--ctrl", file_size_kb=300)

    report = CL.cleanup_candidate_artifacts(
        cand, base_dir=base, drop_hf_cache=True, hf_cache_root=cache_root
    )

    # Index dir gone (still safe)
    assert not (base / "ctrl").exists()
    # HF cache PRESERVED — production depends on it
    assert (cache_root / "models--org--ctrl").exists()
    # Skipped flag set
    assert report.skipped_hf_cache_due_to_control is True
    assert report.hf_cache_freed_mb == 0.0


def test_cleanup_skips_cache_when_drop_disabled(tmp_path):
    base = tmp_path / "ab"
    cache_root = tmp_path / "hf_cache"

    cand = _Candidate("up", "org/up", is_control=False)
    _populate_dir(base / "up")
    _populate_dir(cache_root / "models--org--up")

    report = CL.cleanup_candidate_artifacts(
        cand, base_dir=base, drop_hf_cache=False, hf_cache_root=cache_root
    )

    # Index gone
    assert not (base / "up").exists()
    # Cache preserved (drop_hf_cache=False overrides)
    assert (cache_root / "models--org--up").exists()
    assert report.hf_cache_freed_mb == 0.0
    # skipped_hf_cache_due_to_control should be False (it's not a
    # control candidate; we just chose not to drop)
    assert report.skipped_hf_cache_due_to_control is False


def test_cleanup_handles_missing_dirs_gracefully(tmp_path):
    """No state on disk for either index or cache — no crash, 0 freed."""
    cand = _Candidate("ghost", "org/ghost", is_control=False)
    report = CL.cleanup_candidate_artifacts(
        cand, base_dir=tmp_path / "missing-base",
        drop_hf_cache=True,
        hf_cache_root=tmp_path / "missing-cache",
    )
    assert report.index_dir_freed_mb == 0.0
    assert report.hf_cache_freed_mb == 0.0
    assert report.total_freed_mb == 0.0


def test_cleanup_total_freed_sums_both_classes(tmp_path):
    base = tmp_path / "ab"
    cache_root = tmp_path / "hf_cache"

    cand = _Candidate("c", "org/c", is_control=False)
    _populate_dir(base / "c", file_size_kb=512)
    _populate_dir(cache_root / "models--org--c", file_size_kb=1024)

    report = CL.cleanup_candidate_artifacts(
        cand, base_dir=base, drop_hf_cache=True, hf_cache_root=cache_root
    )
    assert report.total_freed_mb == report.index_dir_freed_mb + report.hf_cache_freed_mb
    # Total should be roughly (512 + 1024) KB = 1.5 MB
    assert 1.4 < report.total_freed_mb < 1.6


# ---------------------------------------------------------------------------
# _du_mb
# ---------------------------------------------------------------------------

def test_du_mb_returns_zero_for_missing_path(tmp_path):
    assert CL._du_mb(tmp_path / "nope") == 0.0


def test_du_mb_sums_nested_files(tmp_path):
    d = tmp_path / "x"
    d.mkdir()
    (d / "a.bin").write_bytes(b"\x00" * (256 * 1024))  # 256 KB
    sub = d / "nested"
    sub.mkdir()
    (sub / "b.bin").write_bytes(b"\x00" * (768 * 1024))  # 768 KB
    # 1024 KB = 1 MB total
    assert 0.95 < CL._du_mb(d) < 1.05

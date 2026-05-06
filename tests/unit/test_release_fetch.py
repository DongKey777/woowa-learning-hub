"""Tests for the GitHub Releases index distribution fetcher.

These tests exercise the lock parsing + short-circuit paths without
making network calls. The actual download path is exercised manually
during the publish_index_release release flow, where any network
failure would surface immediately.
"""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path
from typing import Any

import pytest

from scripts.learning.rag import release_fetch


def _write_config(repo_root: Path, body: dict[str, Any]) -> None:
    config_path = repo_root / "config" / "rag_models.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")


def _write_local_manifest(out_dir: Path, *, archive_sha256: str | None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"row_count": 27238}
    if archive_sha256 is not None:
        manifest["release"] = {"archive_sha256": archive_sha256}
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )


def test_release_lock_returns_none_when_no_release_block():
    assert release_fetch.ReleaseLock.from_config({}) is None
    assert release_fetch.ReleaseLock.from_config({"release": {}}) is None


def test_release_lock_returns_none_when_required_field_missing():
    # archive_sha256 missing
    assert (
        release_fetch.ReleaseLock.from_config(
            {
                "release": {
                    "tag": "index-v1.0.0-corpus@deadbee",
                    "archive_url": "https://example/x.tar.zst",
                }
            }
        )
        is None
    )


def test_release_lock_parses_full_block():
    lock = release_fetch.ReleaseLock.from_config(
        {
            "release": {
                "tag": "index-v1.0.0-corpus@deadbee",
                "archive_url": "https://example/x.tar.zst",
                "archive_sha256": "ab" * 32,
                "compressed_size_mb": 128.8,
            }
        }
    )

    assert lock is not None
    assert lock.tag == "index-v1.0.0-corpus@deadbee"
    assert lock.archive_url == "https://example/x.tar.zst"
    assert lock.archive_sha256 == "ab" * 32
    assert lock.compressed_size_mb == 128.8


def test_fetch_returns_no_release_configured(tmp_path: Path):
    _write_config(tmp_path, {"schema_version": 1})
    out_dir = tmp_path / "state" / "cs_rag"

    outcome = release_fetch.fetch_index_release(out_dir, repo_root=tmp_path)

    assert outcome == "no_release_configured"


def test_fetch_short_circuits_when_local_sha_matches(tmp_path: Path):
    sha = "ab" * 32
    _write_config(
        tmp_path,
        {
            "schema_version": 1,
            "release": {
                "tag": "index-v1",
                "archive_url": "https://example/x.tar.zst",
                "archive_sha256": sha,
            },
        },
    )
    out_dir = tmp_path / "state" / "cs_rag"
    _write_local_manifest(out_dir, archive_sha256=sha)

    outcome = release_fetch.fetch_index_release(out_dir, repo_root=tmp_path)

    assert outcome == "already_current"


def test_fetch_does_not_short_circuit_when_local_sha_differs(monkeypatch, tmp_path: Path):
    """When the local manifest's recorded sha differs from the lock,
    fetch should proceed (we mock _stream_download to avoid network)."""
    locked_sha = "ab" * 32
    other_sha = "cd" * 32
    _write_config(
        tmp_path,
        {
            "release": {
                "tag": "index-v1",
                "archive_url": "https://example/x.tar.zst",
                "archive_sha256": locked_sha,
            }
        },
    )
    out_dir = tmp_path / "state" / "cs_rag"
    _write_local_manifest(out_dir, archive_sha256=other_sha)

    download_called = {"value": False}

    def fake_download(url: str, dest: Path, *, log) -> None:
        download_called["value"] = True
        # Write a fake archive so sha256 verification fails downstream
        # — that is the path under test here.
        dest.write_bytes(b"\x00" * 16)

    monkeypatch.setattr(release_fetch, "_stream_download", fake_download)

    with pytest.raises(RuntimeError, match="sha256 mismatch"):
        release_fetch.fetch_index_release(out_dir, repo_root=tmp_path)

    assert download_called["value"] is True


def test_local_archive_sha256_handles_missing_manifest(tmp_path: Path):
    out_dir = tmp_path / "state" / "cs_rag"
    out_dir.mkdir(parents=True, exist_ok=True)
    assert release_fetch._local_archive_sha256(out_dir) is None


def test_local_archive_sha256_handles_manifest_without_release_block(tmp_path: Path):
    out_dir = tmp_path / "state" / "cs_rag"
    _write_local_manifest(out_dir, archive_sha256=None)
    assert release_fetch._local_archive_sha256(out_dir) is None


def test_extract_checked_tar_rejects_parent_traversal(tmp_path: Path):
    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode="w") as tar:
        info = tarfile.TarInfo("../escape.txt")
        payload = b"blocked"
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    tar_bytes.seek(0)

    with tarfile.open(fileobj=tar_bytes, mode="r:") as tar:
        with pytest.raises(RuntimeError, match="unsafe tar member path"):
            release_fetch._extract_checked_tar(tar, tmp_path / "extract")


def test_extract_checked_tar_rejects_symlink(tmp_path: Path):
    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode="w") as tar:
        info = tarfile.TarInfo("cs_rag/manifest.json")
        info.type = tarfile.SYMTYPE
        info.linkname = "../../manifest.json"
        tar.addfile(info)
    tar_bytes.seek(0)

    with tarfile.open(fileobj=tar_bytes, mode="r:") as tar:
        with pytest.raises(RuntimeError, match="unsafe tar member link"):
            release_fetch._extract_checked_tar(tar, tmp_path / "extract")

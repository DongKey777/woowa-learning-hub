"""Fetch a pre-built CS RAG index from GitHub Releases instead of
building it on the learner's machine.

Why this exists
---------------
Local index build on M4 16GB takes 6-10h cold and frequently OOMs.
RunPod L40S finishes the same build in ~9 minutes. The cost asymmetry
is hardware, not code, so production ships the index from RunPod →
GitHub Releases → learner cs-index-build.

This module is the *learner-side fetch* half of that pipeline. The
build half lives in ``scripts/remote/runpod_direct_build.py`` and the
publish half in ``scripts/remote/publish_index_release.py``.

Contract
--------
``config/rag_models.json`` records the release URL + sha256 alongside
the existing ``artifact`` block. Example::

    "release": {
      "tag": "index-v1.0.0-corpus@029ec00",
      "archive_url": "https://github.com/DongKey777/woowa-learning-hub/releases/download/.../cs_rag_index_root.tar.zst",
      "archive_sha256": "0d0a4efb...",
      "compressed_size_mb": 137
    }

When the learner runs ``bin/cs-index-build`` and the local
``state/cs_rag/manifest.json`` is missing or its corpus_hash does not
match the release lock, this module downloads + verifies + extracts
the release artifact instead of running the encoder. The encoder path
remains available as a fallback (``--no-release-fetch`` or no release
configured).

Behaviour summary:

- No release URL in config → fetch returns ``"no_release_configured"``
- Local index already matches release sha256 → ``"already_current"``
- Local index matches the release sha256 but the live corpus changed →
  ``"stale_against_corpus"`` so the caller can rebuild locally
- Download succeeds, sha256 verifies, extract succeeds → ``"fetched"``
- Any step fails → exception propagates, caller decides whether to
  fall back to local build
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class ReleaseLock:
    """Slice of ``config/rag_models.json`` describing a remote release."""

    tag: str
    archive_url: str
    archive_sha256: str
    compressed_size_mb: float | None = None

    @classmethod
    def from_config(cls, config: dict) -> "ReleaseLock | None":
        release = config.get("release")
        if not isinstance(release, dict):
            return None
        tag = release.get("tag")
        archive_url = release.get("archive_url")
        archive_sha256 = release.get("archive_sha256")
        if not (tag and archive_url and archive_sha256):
            return None
        size = release.get("compressed_size_mb")
        return cls(
            tag=str(tag),
            archive_url=str(archive_url),
            archive_sha256=str(archive_sha256),
            compressed_size_mb=float(size) if size is not None else None,
        )


FetchOutcome = Literal[
    "no_release_configured",
    "already_current",
    "stale_against_corpus",
    "fetched",
]


def _read_rag_models_config(repo_root: Path) -> dict:
    config_path = repo_root / "config" / "rag_models.json"
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _local_archive_sha256(out_dir: Path) -> str | None:
    """If the local index already records a build sha256, return it.

    The manifest produced by both RunPod direct builds and the
    publish_index_release tool stamps ``release.archive_sha256`` into
    ``state/cs_rag/manifest.json`` so we can short-circuit a fetch
    without touching the tar.
    """
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    release = manifest.get("release") or {}
    sha = release.get("archive_sha256")
    if isinstance(sha, str) and sha:
        return sha
    return None


def _local_index_matches_live_corpus(out_dir: Path, repo_root: Path) -> bool:
    """Return True when the local manifest still matches the current corpus.

    Release archives are tied to a specific corpus snapshot. If the local
    checkout has newer corpus files, re-fetching the same archive would keep
    the index stale. In that case the caller must fall back to a local build.

    Missing corpus roots preserve the historical short-circuit behaviour so
    repo-light tests and external consumers do not regress.
    """
    manifest_path = out_dir / "manifest.json"
    corpus_root = repo_root / "knowledge" / "cs"
    if not manifest_path.exists() or not corpus_root.exists():
        return True
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False

    from . import corpus_loader

    stored_indexed_hash = manifest.get("indexed_corpus_hash")
    if isinstance(stored_indexed_hash, str) and stored_indexed_hash:
        return stored_indexed_hash == corpus_loader.indexed_corpus_hash(corpus_root)

    stored_full_hash = manifest.get("corpus_hash")
    if not isinstance(stored_full_hash, str) or not stored_full_hash:
        return False
    current_full_hash = corpus_loader.corpus_hash(corpus_root)
    current_indexed_hash = corpus_loader.indexed_corpus_hash(corpus_root)
    return stored_full_hash in {current_full_hash, current_indexed_hash}


def _stream_download(url: str, dest: Path, *, log) -> None:
    """Download ``url`` to ``dest`` with no third-party deps.

    GitHub release asset URLs redirect to S3 once; urllib follows
    redirects by default via ``HTTPRedirectHandler``, so a plain
    ``urlopen`` handles public release downloads. Private repos would
    need ``gh release download`` instead — out of scope here because
    this workbench is a public repository.
    """
    log("download", {"url": url, "dest": str(dest)})
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "woowa-learning-hub-release-fetch"},
    )
    try:
        with urllib.request.urlopen(req) as resp, open(dest, "wb") as out:
            shutil.copyfileobj(resp, out)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"failed to download {url}: {exc}") from exc


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract_checked_tar(tar: tarfile.TarFile, target: Path) -> None:
    """Extract only regular files/directories that stay under ``target``."""
    target_root = target.resolve()
    for member in tar:
        if member is None:
            continue
        destination = (target_root / member.name).resolve()
        if os.path.commonpath([str(target_root), str(destination)]) != str(target_root):
            raise RuntimeError(f"unsafe tar member path: {member.name}")
        if member.issym() or member.islnk():
            raise RuntimeError(f"unsafe tar member link: {member.name}")
        if member.isdev():
            raise RuntimeError(f"unsafe tar member device: {member.name}")
        tar.extract(member, path=target_root)


def _extract_zstd_tar(archive: Path, target: Path, *, log) -> None:
    """Extract a tar.zst archive into target.

    Uses the zstd CLI to decompress in a streaming pipeline so the
    decompressed tar is never fully on disk. Falls back to a pure-
    Python path if zstd is missing (tarfile + zstandard module).
    """
    target.mkdir(parents=True, exist_ok=True)
    if shutil.which("zstd"):
        log("extract", {"tool": "zstd-cli", "target": str(target)})
        with subprocess.Popen(
            ["zstd", "-d", "-c", str(archive)],
            stdout=subprocess.PIPE,
        ) as proc:
            assert proc.stdout is not None
            with tarfile.open(fileobj=proc.stdout, mode="r|") as tar:
                _extract_checked_tar(tar, target)
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"zstd exited with {proc.returncode}")
        return
    try:
        import zstandard  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "neither `zstd` CLI nor the `zstandard` Python package is "
            "available; cannot decompress the release archive"
        ) from exc
    log("extract", {"tool": "zstandard-py", "target": str(target)})
    with archive.open("rb") as compressed:
        dctx = zstandard.ZstdDecompressor()
        with dctx.stream_reader(compressed) as reader:
            with tarfile.open(fileobj=reader, mode="r|") as tar:
                _extract_checked_tar(tar, target)


def fetch_index_release(
    out_dir: Path,
    *,
    repo_root: Path | None = None,
    log=None,
    force: bool = False,
) -> FetchOutcome:
    """Materialize the release-locked index into ``out_dir``.

    Args:
        out_dir: target index root, normally ``state/cs_rag``. The
            directory may exist with a stale build; on a successful
            fetch it is replaced atomically (rename-into-place).
        repo_root: defaults to two levels up from this module so the
            relative ``config/rag_models.json`` lookup works under
            ``bin/cs-index-build``.
        log: callable ``(stage: str, info: dict) -> None`` used by the
            CLI to emit Korean status lines. Defaults to a no-op.
        force: skip the ``already_current`` short-circuit and always
            download. Useful for CI integrity audits.

    Returns:
        ``"no_release_configured"`` when ``config/rag_models.json``
        has no ``release`` block. The caller should fall back to a
        local build.

        ``"already_current"`` when ``out_dir/manifest.json`` already
        records the release's archive_sha256.

        ``"stale_against_corpus"`` when the local manifest still points at
        the locked archive but the current checkout's corpus hash changed.
        The caller should skip the fetch and rebuild locally.

        ``"fetched"`` when the archive was downloaded, sha256-verified,
        and extracted into ``out_dir``.

    Raises:
        RuntimeError on download / sha256 / extract failure. The
        caller decides whether to retry or fall back to a local build.
    """
    if log is None:
        def log(_stage, _info):
            return None
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[3]

    config = _read_rag_models_config(repo_root)
    lock = ReleaseLock.from_config(config)
    if lock is None:
        log("release_fetch", {"outcome": "no_release_configured"})
        return "no_release_configured"

    if not force:
        local_sha = _local_archive_sha256(out_dir)
        if local_sha == lock.archive_sha256:
            if not _local_index_matches_live_corpus(out_dir, repo_root):
                log(
                    "release_fetch",
                    {
                        "outcome": "stale_against_corpus",
                        "tag": lock.tag,
                        "sha256": lock.archive_sha256,
                    },
                )
                return "stale_against_corpus"
            log(
                "release_fetch",
                {
                    "outcome": "already_current",
                    "tag": lock.tag,
                    "sha256": lock.archive_sha256,
                },
            )
            return "already_current"

    log(
        "release_fetch",
        {
            "outcome": "starting",
            "tag": lock.tag,
            "url": lock.archive_url,
            "expected_sha256": lock.archive_sha256,
            "size_mb": lock.compressed_size_mb,
        },
    )

    with tempfile.TemporaryDirectory(prefix="cs-rag-release-") as tmp_str:
        tmp = Path(tmp_str)
        archive = tmp / "cs_rag_index_root.tar.zst"
        _stream_download(lock.archive_url, archive, log=log)
        actual_sha = _sha256_of(archive)
        if actual_sha != lock.archive_sha256:
            raise RuntimeError(
                "release archive sha256 mismatch — refusing to extract. "
                f"expected={lock.archive_sha256} actual={actual_sha}"
            )
        log(
            "release_fetch",
            {"outcome": "sha256_verified", "sha256": actual_sha},
        )

        staging = tmp / "extracted"
        _extract_zstd_tar(archive, staging, log=log)

        # The archive root is a single ``cs_rag`` directory. Pick that
        # up explicitly so atomic rename-into-place does not pick up a
        # leading ``cs_rag/cs_rag/`` accident.
        produced = staging / "cs_rag"
        if not produced.exists():
            # fall back to the staging root if the archive was packed
            # without the leading directory
            produced = staging
        if not (produced / "manifest.json").exists():
            raise RuntimeError(
                "extracted archive does not contain manifest.json — "
                f"layout: {sorted(p.name for p in produced.iterdir())}"
            )

        # Stamp the release_sha256 into the local manifest so the next
        # cs-index-build short-circuits via _local_archive_sha256.
        manifest_path = produced / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_release = manifest.setdefault("release", {})
        manifest_release.update(
            {
                "tag": lock.tag,
                "archive_sha256": lock.archive_sha256,
                "archive_url": lock.archive_url,
            }
        )
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(produced), str(out_dir))

    log(
        "release_fetch",
        {
            "outcome": "fetched",
            "tag": lock.tag,
            "out_dir": str(out_dir),
        },
    )
    return "fetched"

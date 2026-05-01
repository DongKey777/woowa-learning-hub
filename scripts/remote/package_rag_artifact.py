"""Package a LanceDB index root into a reproducible artifact (plan v5 §H0 task v5-4).

Used both locally (developer testing of a sampled build) and remotely
(Pod-side after `bin/cs-index-build --backend lance` completes). The
output goes into ``artifacts/rag-full-build/<run_id>/``:

    manifest.json                # this script's manifest, NOT the index manifest
    cs_rag_index_root.tar.zst    # the entire index root (lance/ + manifest.json + chunk_hashes_per_model.json)
    environment.json             # python/os/gpu/dep versions
    run.log                      # caller appends; we just create empty placeholder
    repo.commit_or_diff.txt      # git state at build time

The point of *index root entire* (peer review) is so a downloader can
just `tar --use-compress-program=zstd -xf <file> -C state/cs_rag/` and
the reader sees a valid v3 index. ``lance/`` alone is not enough —
manifest.json (v3 schema) + chunk_hashes_per_model.json must travel
with it.

This module is intentionally subprocess-driven for compression — uses
the system ``zstd`` CLI rather than adding a Python ``zstandard``
dependency. ``zstd`` is universally available on Pod images and
``brew install zstd`` on macOS.

Tested in ``tests/unit/test_package_rag_artifact.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_ID = "rag-build-artifact-v1"
DEFAULT_OUTPUT_PARENT = Path("artifacts/rag-full-build")
COMPRESSION_LEVEL = 19  # zstd: 1=fast, 22=max. 19 is the sweet spot for
                       # our ~1GB index roots — ~30-40% smaller than tar
                       # alone, ~2x slower than -3 default but still
                       # bounded by network upload, not CPU.


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class PackagingError(RuntimeError):
    """Any failure during artifact packaging surfaces as this."""


class IndexRootInvalid(PackagingError):
    """Raised when the index root is missing required v3 files."""


# ---------------------------------------------------------------------------
# Index root validation
# ---------------------------------------------------------------------------

REQUIRED_INDEX_ROOT_PATHS = (
    "manifest.json",     # v3 manifest — readers refuse to load without this
    "lance",             # LanceDB data directory (table files)
)

OPTIONAL_INDEX_ROOT_PATHS = (
    "chunk_hashes_per_model.json",  # incremental fingerprint sidecar
)


def validate_index_root(index_root: Path) -> None:
    """Verify ``index_root`` looks like a v3 LanceDB index.

    Raises ``IndexRootInvalid`` with a clear message if any required
    file is missing. Does not validate the *contents* of manifest.json
    — that's the reader's job. Just checks presence so we don't ship
    a half-built artifact.
    """
    if not index_root.exists() or not index_root.is_dir():
        raise IndexRootInvalid(f"index_root not found or not a directory: {index_root}")
    for name in REQUIRED_INDEX_ROOT_PATHS:
        target = index_root / name
        if not target.exists():
            raise IndexRootInvalid(
                f"index_root missing required path '{name}' "
                f"(did you build with --backend lance?)"
            )
    # manifest.json must be parseable + have index_version 3
    try:
        manifest = json.loads((index_root / "manifest.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise IndexRootInvalid(f"manifest.json is corrupt: {exc}") from exc
    if manifest.get("index_version") != 3:
        raise IndexRootInvalid(
            f"manifest.json index_version != 3 (got {manifest.get('index_version')!r}). "
            f"Only v3 LanceDB indexes are packaged with this script."
        )


# ---------------------------------------------------------------------------
# zstd availability
# ---------------------------------------------------------------------------

def _check_zstd_available() -> None:
    """Raise PackagingError if `zstd` CLI is not on PATH."""
    if shutil.which("zstd") is None:
        raise PackagingError(
            "zstd CLI not found on PATH. Install with `brew install zstd` "
            "(macOS) or `apt install zstd` (Linux). Required for tar.zst "
            "compression."
        )


# ---------------------------------------------------------------------------
# tar + zstd compression (subprocess pipeline)
# ---------------------------------------------------------------------------

def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _create_tar_zst(
    *,
    source_dir: Path,
    output_path: Path,
    compression_level: int = COMPRESSION_LEVEL,
) -> dict:
    """Create ``output_path`` (.tar.zst) from ``source_dir`` contents.

    Returns ``{tar_bytes, zst_bytes, sha256, ratio, wallclock_s}``.

    Implementation: write tarball to a temp file, then run
    ``zstd -<level> -T0 -o output_path tar_path``. Two-step is simpler
    than a streaming pipeline and the temp tar is cheap (sequential
    write, sequential read).
    """
    _check_zstd_available()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    start = time.time()
    tmp_tar = output_path.with_suffix(".tar")
    try:
        # Stage 1: tar
        with tarfile.open(tmp_tar, mode="w") as tf:
            # arcname = source_dir.name → archive root has the dir name
            # so the receiver knows what to extract into
            tf.add(source_dir, arcname=source_dir.name)
        tar_bytes = tmp_tar.stat().st_size

        # Stage 2: zstd -level -T0 (multithread, all CPU cores)
        result = subprocess.run(
            ["zstd",
             f"-{compression_level}",
             "-T0",
             "-q",                     # quiet
             "-f",                     # force overwrite if exists
             "-o", str(output_path),
             str(tmp_tar)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise PackagingError(
                f"zstd compression failed (returncode={result.returncode}): "
                f"{result.stderr.strip()}"
            )

        zst_bytes = output_path.stat().st_size
        sha256 = _compute_sha256(output_path)
        elapsed = time.time() - start

        return {
            "tar_bytes": tar_bytes,
            "zst_bytes": zst_bytes,
            "sha256": sha256,
            "ratio": (zst_bytes / tar_bytes) if tar_bytes > 0 else 1.0,
            "wallclock_s": round(elapsed, 2),
        }
    finally:
        tmp_tar.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Environment capture
# ---------------------------------------------------------------------------

def capture_environment(*, extra: dict | None = None) -> dict:
    """Capture run-time environment for reproducibility audit.

    On the Pod side, ``extra`` should pass GPU type, CUDA version, and
    other GPU-specific info. Locally the ``extra`` is empty and we
    rely on the local interpreter's view.
    """
    env = {
        "schema_id": "rag-build-environment-v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "system": platform.system(),
    }
    # Best-effort dep versions
    for mod_name in ("lancedb", "pyarrow", "numpy", "torch",
                     "FlagEmbedding", "kiwipiepy", "sentence_transformers"):
        try:
            mod = __import__(mod_name)
            env[f"dep_{mod_name}"] = getattr(mod, "__version__", "unknown")
        except ImportError:
            env[f"dep_{mod_name}"] = "not_installed"
    if extra:
        env.update(extra)
    return env


# ---------------------------------------------------------------------------
# Git state capture
# ---------------------------------------------------------------------------

def capture_git_state(repo_root: Path) -> dict:
    """Capture commit SHA + dirty-tree status for reproducibility.

    Returns ``{commit_sha, branch, is_dirty, dirty_files}``.
    """
    def run(cmd: list[str]) -> str:
        try:
            return subprocess.check_output(
                cmd, cwd=repo_root, stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
        except subprocess.CalledProcessError:
            return ""

    sha = run(["git", "rev-parse", "HEAD"])
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    status = run(["git", "status", "--porcelain"])
    dirty_files = [line[3:] for line in status.splitlines() if line.strip()]

    return {
        "schema_id": "rag-build-git-state-v1",
        "commit_sha": sha,
        "branch": branch,
        "is_dirty": bool(dirty_files),
        "dirty_files": dirty_files[:50],  # cap for sanity
    }


# ---------------------------------------------------------------------------
# Manifest + orchestrator
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PackageResult:
    output_dir: Path
    archive_path: Path
    manifest_path: Path
    bytes_compressed: int
    bytes_uncompressed: int
    sha256: str
    wallclock_s: float


def package_artifact(
    *,
    index_root: Path,
    run_id: str,
    r_phase: str,
    output_parent: Path | None = None,
    repo_root: Path | None = None,
    extra_environment: dict | None = None,
    extra_metadata: dict | None = None,
    compression_level: int = COMPRESSION_LEVEL,
) -> PackageResult:
    """Package an index root into the standard artifact layout.

    Args:
      index_root: path to the LanceDB index root (must contain
        manifest.json + lance/).
      run_id: unique identifier — typically
        ``"<r-phase>-<commit-sha7>-<timestamp>"``.
      r_phase: one of ``r0``, ``r1``, ``r2``, ``r3``, ``r4``.
      output_parent: where to write ``<run_id>/`` directory. Defaults
        to ``artifacts/rag-full-build/``.
      repo_root: for git state capture. Defaults to current dir.
      extra_environment: Pod-side info (gpu_type, cuda_version, ...).
      extra_metadata: caller-specified fields (build_started_at,
        encoder_model_revision, etc.) merged into manifest.
      compression_level: zstd level (default 19).

    Returns:
      PackageResult with paths + measurements.
    """
    if r_phase not in ("r-1", "r0", "r1", "r2", "r3", "r4"):
        raise PackagingError(f"unknown r_phase: {r_phase!r}")

    validate_index_root(index_root)

    out_parent = output_parent or DEFAULT_OUTPUT_PARENT
    out_dir = out_parent / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    archive_path = out_dir / "cs_rag_index_root.tar.zst"
    archive_meta = _create_tar_zst(
        source_dir=index_root,
        output_path=archive_path,
        compression_level=compression_level,
    )

    # Environment + git
    env = capture_environment(extra=extra_environment)
    git_state = capture_git_state(repo_root or Path.cwd())

    # Read index manifest for cross-reference (don't duplicate, just point)
    index_manifest = json.loads((index_root / "manifest.json").read_text(encoding="utf-8"))

    # Composite manifest
    manifest = {
        "schema_id": SCHEMA_ID,
        "run_id": run_id,
        "r_phase": r_phase,
        "packaged_at": datetime.now(timezone.utc).isoformat(),
        "archive": {
            "path": archive_path.name,
            "compression": "zstd",
            "compression_level": compression_level,
            "tar_bytes": archive_meta["tar_bytes"],
            "zst_bytes": archive_meta["zst_bytes"],
            "compression_ratio": round(archive_meta["ratio"], 4),
            "sha256": archive_meta["sha256"],
            "wallclock_s": archive_meta["wallclock_s"],
        },
        "index_root_summary": {
            "index_version": index_manifest.get("index_version"),
            "encoder": index_manifest.get("encoder"),
            "modalities": index_manifest.get("modalities"),
            "row_count": index_manifest.get("row_count"),
            "corpus_hash": index_manifest.get("corpus_hash"),
            "lancedb": index_manifest.get("lancedb"),
        },
        "environment": env,
        "git_state": git_state,
    }
    if extra_metadata:
        manifest["extra"] = extra_metadata

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    # Empty run.log placeholder (caller appends after build/eval)
    (out_dir / "run.log").touch()

    # Git state separate file (also embedded in manifest for redundancy)
    (out_dir / "repo.commit_or_diff.txt").write_text(
        f"commit_sha: {git_state['commit_sha']}\n"
        f"branch: {git_state['branch']}\n"
        f"is_dirty: {git_state['is_dirty']}\n"
        f"dirty_files: {git_state['dirty_files']}\n",
        encoding="utf-8",
    )

    # Environment separate file (mirrors manifest.environment)
    (out_dir / "environment.json").write_text(
        json.dumps(env, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return PackageResult(
        output_dir=out_dir,
        archive_path=archive_path,
        manifest_path=manifest_path,
        bytes_compressed=archive_meta["zst_bytes"],
        bytes_uncompressed=archive_meta["tar_bytes"],
        sha256=archive_meta["sha256"],
        wallclock_s=archive_meta["wallclock_s"],
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _strict_r3_metadata_from_args(args: argparse.Namespace) -> dict | None:
    if not args.strict_r3:
        return None
    missing = []
    for attr in (
        "build_command",
        "package_lock",
        "qrel_hash",
        "local_runtime_machine",
        "local_runtime_memory_gb",
        "local_runtime_accelerator",
    ):
        if getattr(args, attr) in (None, ""):
            missing.append(f"--{attr.replace('_', '-')}")
    if missing:
        raise PackagingError("--strict-r3 requires " + ", ".join(missing))
    return {
        "build_command": args.build_command,
        "package_lock": args.package_lock,
        "qrel_hash": args.qrel_hash,
        "local_runtime_profile": {
            "machine": args.local_runtime_machine,
            "memory_gb": args.local_runtime_memory_gb,
            "accelerator": args.local_runtime_accelerator,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
    )
    parser.add_argument("--index-root", required=True, type=Path,
                        help="LanceDB index root containing manifest.json + lance/")
    parser.add_argument("--run-id", required=True,
                        help="Unique run id, e.g. r1-d24a188-2026-05-01T0830")
    parser.add_argument("--r-phase", required=True,
                        choices=("r-1", "r0", "r1", "r2", "r3", "r4"))
    parser.add_argument("--output-parent", type=Path, default=None,
                        help=f"Default: {DEFAULT_OUTPUT_PARENT}")
    parser.add_argument("--compression-level", type=int, default=COMPRESSION_LEVEL,
                        help=f"zstd compression level (default: {COMPRESSION_LEVEL})")
    parser.add_argument("--gpu-type", default=None,
                        help="GPU type for environment metadata (Pod side)")
    parser.add_argument("--cuda-version", default=None,
                        help="CUDA version for environment metadata (Pod side)")
    parser.add_argument(
        "--strict-r3",
        action="store_true",
        help="Require and embed R3 remote-build/local-serve metadata.",
    )
    parser.add_argument("--build-command", default=None)
    parser.add_argument("--package-lock", default=None)
    parser.add_argument("--qrel-hash", default=None)
    parser.add_argument("--local-runtime-machine", default=None)
    parser.add_argument("--local-runtime-memory-gb", type=float, default=None)
    parser.add_argument("--local-runtime-accelerator", default=None)
    args = parser.parse_args(argv)

    extra_env = {}
    if args.gpu_type:
        extra_env["gpu_type"] = args.gpu_type
    if args.cuda_version:
        extra_env["cuda_version"] = args.cuda_version

    try:
        strict_r3_metadata = _strict_r3_metadata_from_args(args)
        result = package_artifact(
            index_root=args.index_root,
            run_id=args.run_id,
            r_phase=args.r_phase,
            output_parent=args.output_parent,
            extra_environment=extra_env or None,
            extra_metadata=strict_r3_metadata,
            compression_level=args.compression_level,
        )
    except PackagingError as exc:
        print(f"[package_rag_artifact] ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({
        "schema_id": SCHEMA_ID,
        "run_id": args.run_id,
        "r_phase": args.r_phase,
        "output_dir": str(result.output_dir),
        "archive_path": str(result.archive_path),
        "bytes_compressed": result.bytes_compressed,
        "bytes_uncompressed": result.bytes_uncompressed,
        "compression_ratio": round(result.bytes_compressed / max(result.bytes_uncompressed, 1), 4),
        "sha256": result.sha256,
        "wallclock_s": result.wallclock_s,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

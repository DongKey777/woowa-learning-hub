"""Verification contract for remote-built RAG artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any


class ArtifactVerificationError(RuntimeError):
    """Raised when a remote artifact is not safe to import locally."""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _require_path(blob: dict[str, Any], dotted: str) -> Any:
    current: Any = blob
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ArtifactVerificationError(f"artifact manifest missing {dotted}")
        current = current[part]
    if current in (None, "", [], {}):
        raise ArtifactVerificationError(f"artifact manifest has empty {dotted}")
    return current


def _extract_archive_for_import_check(archive_path: Path, output_dir: Path) -> Path:
    tmp_tar = output_dir / "cs_rag_index_root.tar"
    result = subprocess.run(
        ["zstd", "-d", "-q", "-f", str(archive_path), "-o", str(tmp_tar)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ArtifactVerificationError(
            f"archive decompression failed: {result.stderr.strip()}"
        )
    with tarfile.open(tmp_tar) as tf:
        tf.extractall(output_dir, filter="data")

    candidates = [
        path
        for path in output_dir.iterdir()
        if path.is_dir()
        and (path / "manifest.json").exists()
        and (path / "lance").exists()
    ]
    if len(candidates) != 1:
        raise ArtifactVerificationError(
            f"expected exactly one extracted index root, found {len(candidates)}"
        )
    return candidates[0]


def _verify_extracted_index_root(
    index_root: Path,
    artifact_manifest: dict[str, Any],
) -> dict[str, Any]:
    try:
        index_manifest = json.loads(
            (index_root / "manifest.json").read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        raise ArtifactVerificationError(
            f"extracted index manifest is corrupt: {exc}"
        ) from exc

    expected = artifact_manifest["index_root_summary"]
    checks = (
        (
            "index_version",
            index_manifest.get("index_version"),
            expected.get("index_version"),
        ),
        ("corpus_hash", index_manifest.get("corpus_hash"), expected.get("corpus_hash")),
        ("row_count", index_manifest.get("row_count"), expected.get("row_count")),
    )
    for name, actual, wanted in checks:
        if wanted is not None and actual != wanted:
            raise ArtifactVerificationError(
                f"extracted index {name} mismatch: expected {wanted!r}, got {actual!r}"
            )

    expected_encoder = expected.get("encoder") or {}
    actual_encoder = index_manifest.get("encoder") or {}
    for key in ("model_id", "model_version"):
        wanted = expected_encoder.get(key)
        if wanted is not None and actual_encoder.get(key) != wanted:
            raise ArtifactVerificationError(
                f"extracted index encoder.{key} mismatch: "
                f"expected {wanted!r}, got {actual_encoder.get(key)!r}"
            )

    return {
        "index_root_name": index_root.name,
        "index_version": index_manifest.get("index_version"),
        "row_count": index_manifest.get("row_count"),
        "corpus_hash": index_manifest.get("corpus_hash"),
        "encoder": actual_encoder,
        "has_lance_dir": (index_root / "lance").is_dir(),
        "has_chunk_hashes": (index_root / "chunk_hashes_per_model.json").exists(),
    }


COMMON_REQUIRED_FIELDS = (
    "schema_id",
    "run_id",
    "archive.path",
    "archive.sha256",
    "index_root_summary.index_version",
    "index_root_summary.encoder",
    "index_root_summary.corpus_hash",
    "environment.python_version",
    "git_state.commit_sha",
)

R3_STRICT_REQUIRED_FIELDS = (
    "extra.build_command",
    "extra.package_lock",
    "extra.qrel_hash",
    "extra.local_runtime_profile.machine",
    "extra.local_runtime_profile.memory_gb",
    "extra.local_runtime_profile.accelerator",
)


def verify_artifact_dir(
    artifact_dir: Path | str,
    *,
    strict_r3: bool = False,
    verify_import: bool = False,
) -> dict[str, Any]:
    """Verify manifest and archive checksum before local import.

    ``verify_import`` additionally decompresses the archive into a temporary
    directory and checks that the packaged index root matches the artifact
    manifest. This is intentionally structural and checksum-bound; the caller
    can run a separate smoke search after installing the verified artifact.
    """

    root = Path(artifact_dir)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise ArtifactVerificationError(f"manifest.json not found under {root}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ArtifactVerificationError(f"manifest.json is corrupt: {exc}") from exc

    for field in COMMON_REQUIRED_FIELDS:
        _require_path(manifest, field)
    if strict_r3:
        for field in R3_STRICT_REQUIRED_FIELDS:
            _require_path(manifest, field)

    archive_path = root / str(_require_path(manifest, "archive.path"))
    if not archive_path.exists():
        raise ArtifactVerificationError(f"archive not found: {archive_path}")
    expected_sha = str(_require_path(manifest, "archive.sha256"))
    actual_sha = _sha256(archive_path)
    if actual_sha != expected_sha:
        raise ArtifactVerificationError(
            f"archive sha256 mismatch: expected {expected_sha}, got {actual_sha}"
        )

    import_check = None
    if verify_import:
        with tempfile.TemporaryDirectory(prefix="rag-artifact-import-") as tmp:
            extracted_root = _extract_archive_for_import_check(archive_path, Path(tmp))
            import_check = _verify_extracted_index_root(extracted_root, manifest)

    result = {
        "artifact_dir": str(root),
        "archive": str(archive_path),
        "sha256": actual_sha,
        "strict_r3": strict_r3,
        "verify_import": verify_import,
        "index_version": _require_path(manifest, "index_root_summary.index_version"),
        "commit_sha": _require_path(manifest, "git_state.commit_sha"),
    }
    if import_check is not None:
        result["import_check"] = import_check
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir", type=Path)
    parser.add_argument("--strict-r3", action="store_true")
    parser.add_argument("--verify-import", action="store_true")
    args = parser.parse_args(argv)

    result = verify_artifact_dir(
        args.artifact_dir,
        strict_r3=args.strict_r3,
        verify_import=args.verify_import,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

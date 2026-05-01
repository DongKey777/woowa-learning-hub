"""Verification contract for remote-built RAG artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
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
) -> dict[str, Any]:
    """Verify manifest and archive checksum before local import."""

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

    return {
        "artifact_dir": str(root),
        "archive": str(archive_path),
        "sha256": actual_sha,
        "strict_r3": strict_r3,
        "index_version": _require_path(manifest, "index_root_summary.index_version"),
        "commit_sha": _require_path(manifest, "git_state.commit_sha"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir", type=Path)
    parser.add_argument("--strict-r3", action="store_true")
    args = parser.parse_args(argv)

    result = verify_artifact_dir(args.artifact_dir, strict_r3=args.strict_r3)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

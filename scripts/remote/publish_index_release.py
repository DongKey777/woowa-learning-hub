"""Publish a freshly-built CS RAG index as a GitHub Release.

Why this exists
---------------
Local index build on M4 16GB takes 6-10h cold and frequently OOMs;
RunPod L40S finishes the same build in ~9 minutes. Once a build runs
on RunPod, the resulting tar.zst needs to reach learner laptops
without forcing them to rebuild. GitHub Releases is the cheapest,
most-native distribution layer for a public repository: gh CLI, no
extra storage, sha256 in the release body.

This tool is the *publish* half of the index distribution pipeline.

- The build half lives in ``scripts/remote/runpod_direct_build.py``.
- The fetch half lives in ``scripts/learning/rag/release_fetch.py``.

Pipeline
--------

1. ``runpod_direct_build.py`` produces ``cs_rag_index_root.tar.zst``
   under ``state/cs_rag_remote/direct/<run_id>/``.
2. ``publish_index_release.py`` (this module) reads the run_id, picks
   up the artifact + manifest, computes sha256, runs ``gh release
   create`` with the tar.zst attached, and updates
   ``config/rag_models.json`` with the release lock fields the
   learner-side fetch needs.
3. Learner runs ``bin/cs-index-build`` → ``release_fetch.py`` reads
   the lock → downloads + verifies + extracts.

Usage
-----

    python -m scripts.remote.publish_index_release \\
        --run-id r3-direct-029ec00-2026-05-04T0611Z \\
        --tag-prefix index-v1.0.0 \\
        [--draft]

By default the release is published immediately (public visibility).
``--draft`` keeps it as a draft so an operator can review the body
before flipping it public via ``gh release edit``.

The release tag follows ``<tag-prefix>-corpus@<short-sha>`` so the
locked corpus commit is recoverable from the tag alone.

Idempotence
-----------

If a release with the same tag already exists, the tool refuses to
overwrite by default. Pass ``--replace`` to delete-and-recreate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BuildArtifact:
    run_id: str
    archive_path: Path
    manifest_path: Path
    archive_sha256: str
    compressed_size_mb: float
    corpus_commit: str | None


def _find_artifact(run_id: str, artifact_root: Path) -> BuildArtifact:
    run_dir = artifact_root / run_id
    archive = run_dir / "cs_rag_index_root.tar.zst"
    manifest = run_dir / "manifest.json"
    if not archive.exists():
        raise FileNotFoundError(
            f"archive not found: {archive}. Did runpod_direct_build leave it elsewhere?"
        )
    if not manifest.exists():
        raise FileNotFoundError(
            f"manifest not found: {manifest}. Re-run the direct build with manifest scp."
        )
    sha = _sha256_of(archive)
    size_mb = round(archive.stat().st_size / 1_048_576, 2)
    corpus_commit = _read_corpus_commit(run_dir)
    return BuildArtifact(
        run_id=run_id,
        archive_path=archive,
        manifest_path=manifest,
        archive_sha256=sha,
        compressed_size_mb=size_mb,
        corpus_commit=corpus_commit,
    )


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_corpus_commit(run_dir: Path) -> str | None:
    """The direct build writes ``repo.commit_or_diff.txt`` with the
    HEAD sha that produced the corpus. Use it to derive the release
    tag suffix (``corpus@<short>``) so a learner can map a release
    back to the commit that produced it."""
    commit_file = run_dir / "repo.commit_or_diff.txt"
    if not commit_file.exists():
        return None
    text = commit_file.read_text(encoding="utf-8").strip()
    # Format on success is just the SHA; on uncommitted changes the
    # tool writes ``<sha>\n<diff>`` so we take only the first line.
    return text.splitlines()[0] if text else None


def _release_exists(tag: str) -> bool:
    result = subprocess.run(
        ["gh", "release", "view", tag],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _delete_release(tag: str) -> None:
    subprocess.run(
        ["gh", "release", "delete", tag, "--yes", "--cleanup-tag"],
        check=True,
    )


def _publish_release(
    *,
    tag: str,
    title: str,
    body: str,
    archive: Path,
    draft: bool,
) -> None:
    cmd = ["gh", "release", "create", tag, str(archive), "--title", title, "--notes", body]
    if draft:
        cmd.append("--draft")
    subprocess.run(cmd, check=True)


def _release_body(artifact: BuildArtifact) -> str:
    manifest = json.loads(artifact.manifest_path.read_text(encoding="utf-8"))
    summary = manifest.get("index_root_summary", {}) or {}
    encoder = summary.get("encoder", {}) or {}
    modalities = summary.get("modalities", [])
    row_count = summary.get("row_count")
    return (
        f"CS RAG index artifact built from corpus@{artifact.corpus_commit or 'unknown'}.\n"
        f"\n"
        f"- archive: `{artifact.archive_path.name}`\n"
        f"- compressed size: {artifact.compressed_size_mb} MB\n"
        f"- sha256: `{artifact.archive_sha256}`\n"
        f"- row_count: {row_count}\n"
        f"- encoder: {encoder.get('model_id', 'unknown')} "
        f"({encoder.get('dense_dim', '?')}-dim)\n"
        f"- modalities: {', '.join(modalities) if modalities else 'unknown'}\n"
        f"\n"
        f"Learner machines fetch this archive via `bin/cs-index-build`. "
        f"Local build is not viable on M4 16GB (6-10h cold + OOM risk); "
        f"the index is built on RunPod L40S in ~9 min and shipped here.\n"
        f"\n"
        f"See `docs/runbooks/rag-rollback.md` for rebuild instructions and "
        f"`reports/rag_eval/r3_phase4_6_closing_report.md` for the Pilot "
        f"baseline measurement (95.5% on 200q × 6 cohort).\n"
    )


def _update_rag_models_lock(
    *,
    repo_root: Path,
    tag: str,
    archive_url: str,
    artifact: BuildArtifact,
) -> Path:
    config_path = repo_root / "config" / "rag_models.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["release"] = {
        "tag": tag,
        "archive_url": archive_url,
        "archive_sha256": artifact.archive_sha256,
        "compressed_size_mb": artifact.compressed_size_mb,
        "corpus_commit": artifact.corpus_commit,
        "run_id": artifact.run_id,
    }
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return config_path


def _resolve_release_url(*, tag: str, asset_name: str) -> str:
    """Compose the direct-asset download URL for a published release.

    GitHub renders ``https://github.com/<owner>/<repo>/releases/download/<tag>/<asset>``
    for any public release asset. We resolve owner/repo from ``gh repo view``
    so the script does not hardcode the repository slug.
    """
    result = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner"],
        check=True,
        capture_output=True,
        text=True,
    )
    name_with_owner = json.loads(result.stdout)["nameWithOwner"]
    return (
        f"https://github.com/{name_with_owner}/releases/download/{tag}/{asset_name}"
    )


def _repo_root_from_here() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "knowledge" / "cs").exists() and (parent / "scripts").exists():
            return parent
    return here.parents[2]


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-id",
        required=True,
        help="run_id from runpod_direct_build (e.g. r3-direct-029ec00-2026-05-04T0611Z)",
    )
    parser.add_argument(
        "--tag-prefix",
        default="index-v1.0.0",
        help="tag prefix; the full tag becomes <prefix>-corpus@<short-sha>",
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=None,
        help="Override the default state/cs_rag_remote/direct directory",
    )
    parser.add_argument("--draft", action="store_true", help="Create the release as draft")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="If the tag already exists, delete-and-recreate the release",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute everything but skip gh release create + config write",
    )
    args = parser.parse_args(argv)

    repo_root = _repo_root_from_here()
    artifact_root = args.artifact_root or (repo_root / "state" / "cs_rag_remote" / "direct")
    if not artifact_root.exists():
        logger.error("artifact_root not found: %s", artifact_root)
        return 2

    if shutil.which("gh") is None:
        logger.error("`gh` CLI is required to publish a release")
        return 2

    artifact = _find_artifact(args.run_id, artifact_root)
    short = (artifact.corpus_commit or args.run_id)[:7]
    tag = f"{args.tag_prefix}-corpus@{short}"
    logger.info(
        "publishing release tag=%s archive=%s sha256=%s size_mb=%s",
        tag,
        artifact.archive_path,
        artifact.archive_sha256,
        artifact.compressed_size_mb,
    )

    if args.dry_run:
        body = _release_body(artifact)
        print(f"[dry-run] tag: {tag}")
        print(f"[dry-run] body:\n{body}")
        return 0

    if _release_exists(tag):
        if not args.replace:
            logger.error(
                "release %s already exists. Pass --replace to overwrite, or pick a new tag-prefix.",
                tag,
            )
            return 3
        logger.info("--replace: deleting existing release %s", tag)
        _delete_release(tag)

    title = f"CS RAG index — {tag}"
    body = _release_body(artifact)
    _publish_release(tag=tag, title=title, body=body, archive=artifact.archive_path, draft=args.draft)
    archive_url = _resolve_release_url(tag=tag, asset_name=artifact.archive_path.name)
    config_path = _update_rag_models_lock(
        repo_root=repo_root,
        tag=tag,
        archive_url=archive_url,
        artifact=artifact,
    )
    logger.info("wrote release lock to %s", config_path)
    print(
        f"[publish] release={tag}\n"
        f"[publish] archive_url={archive_url}\n"
        f"[publish] sha256={artifact.archive_sha256}\n"
        f"[publish] config={config_path}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

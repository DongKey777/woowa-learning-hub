from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from scripts.learning.rag import corpus_loader, indexer, release_fetch
else:
    from . import corpus_loader, indexer, release_fetch


def _load_manifest(index_root: Path) -> dict[str, Any] | None:
    manifest_path = index_root / indexer.MANIFEST_NAME
    if not manifest_path.exists():
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _load_rebuild_trigger(index_root: Path) -> dict[str, Any] | None:
    trigger_path = index_root / "rebuild_trigger.json"
    if not trigger_path.exists():
        return None
    try:
        return json.loads(trigger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _release_status(index_root: Path, repo_root: Path) -> dict[str, Any]:
    config = release_fetch._read_rag_models_config(repo_root)
    lock = release_fetch.ReleaseLock.from_config(config)
    if lock is None:
        return {"status": "no_release_configured"}

    local_sha = release_fetch._local_archive_sha256(index_root)
    if local_sha != lock.archive_sha256:
        return {
            "status": "local_archive_mismatch_or_missing",
            "tag": lock.tag,
            "expected_archive_sha256": lock.archive_sha256,
            "local_archive_sha256": local_sha,
        }

    live_match = release_fetch._local_index_matches_live_corpus(index_root, repo_root)
    return {
        "status": "already_current" if live_match else "stale_against_corpus",
        "tag": lock.tag,
        "expected_archive_sha256": lock.archive_sha256,
        "local_archive_sha256": local_sha,
    }


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_corpus_path(path: str) -> str:
    prefix = "knowledge/cs/"
    return path[len(prefix):] if path.startswith(prefix) else path


def _git_stdout(repo_root: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return proc.stdout


def _git_succeeds(repo_root: Path, *args: str) -> bool:
    try:
        subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return True


def _git_changed_markdown_paths(
    repo_root: Path,
    *args: str,
) -> set[str] | None:
    stdout = _git_stdout(repo_root, *args)
    if stdout is None:
        return None
    return {
        _normalize_corpus_path(line.strip())
        for line in stdout.splitlines()
        if line.strip().endswith(".md")
    }


def _indexed_corpus_diff(
    *,
    repo_root: Path,
    manifest: dict[str, Any] | None,
    rebuild_trigger: dict[str, Any] | None,
    limit: int = 20,
) -> dict[str, Any]:
    release = manifest.get("release") if isinstance(manifest, dict) else None
    trigger_release = (
        rebuild_trigger.get("release") if isinstance(rebuild_trigger, dict) else None
    )
    config = release_fetch._read_rag_models_config(repo_root)
    config_release = config.get("release") if isinstance(config, dict) else None
    release_commit = None
    if isinstance(release, dict):
        release_commit = release.get("corpus_commit")
    if not release_commit and isinstance(trigger_release, dict):
        release_commit = trigger_release.get("corpus_commit")
    if not release_commit and isinstance(config_release, dict):
        release_commit = config_release.get("corpus_commit")
    head_commit = _git_stdout(repo_root, "rev-parse", "HEAD")
    if head_commit is None:
        return {
            "available": False,
            "reason": "git_unavailable",
            "release_corpus_commit": release_commit,
            "current_head_commit": None,
            "changed_path_count": None,
            "sample_paths": [],
        }
    head_commit = head_commit.strip() or None
    if not release_commit:
        return {
            "available": False,
            "reason": "manifest_release_commit_missing",
            "release_corpus_commit": None,
            "current_head_commit": head_commit,
            "changed_path_count": None,
            "commit_changed_path_count": None,
            "commit_diff_available": False,
            "commit_diff_reason": "manifest_release_commit_missing",
            "working_tree_changed_path_count": None,
            "untracked_path_count": None,
            "sample_paths": [],
        }
    working_tree_paths = _git_changed_markdown_paths(
        repo_root,
        "diff",
        "--name-only",
        "HEAD",
        "--",
        "knowledge/cs/contents",
    )
    untracked_paths = _git_changed_markdown_paths(
        repo_root,
        "ls-files",
        "--others",
        "--exclude-standard",
        "--",
        "knowledge/cs/contents",
    )
    if working_tree_paths is None or untracked_paths is None:
        return {
            "available": False,
            "reason": "git_diff_failed",
            "release_corpus_commit": release_commit,
            "current_head_commit": head_commit,
            "changed_path_count": None,
            "commit_changed_path_count": None,
            "commit_diff_available": False,
            "commit_diff_reason": "git_diff_failed",
            "working_tree_changed_path_count": None,
            "untracked_path_count": None,
            "sample_paths": [],
        }
    commit_diff_paths: set[str] | None = None
    commit_diff_available = False
    commit_diff_reason = "release_commit_unavailable_locally"
    if _git_succeeds(repo_root, "cat-file", "-e", f"{release_commit}^{{commit}}"):
        commit_diff_paths = _git_changed_markdown_paths(
            repo_root,
            "diff",
            "--name-only",
            f"{release_commit}..HEAD",
            "--",
            "knowledge/cs/contents",
        )
        if commit_diff_paths is None:
            return {
                "available": False,
                "reason": "git_diff_failed",
                "release_corpus_commit": release_commit,
                "current_head_commit": head_commit,
                "changed_path_count": None,
                "commit_changed_path_count": None,
                "commit_diff_available": False,
                "commit_diff_reason": "git_diff_failed",
                "working_tree_changed_path_count": None,
                "untracked_path_count": None,
                "sample_paths": [],
            }
        commit_diff_available = True
        commit_diff_reason = "ok"
    changed_paths = (
        (commit_diff_paths or set()) | working_tree_paths | untracked_paths
    )
    sample_paths = sorted(changed_paths)[:limit]
    return {
        "available": True,
        "reason": "ok" if commit_diff_available else "working_tree_only",
        "release_corpus_commit": release_commit,
        "current_head_commit": head_commit,
        "changed_path_count": len(changed_paths),
        "commit_changed_path_count": (
            len(commit_diff_paths) if commit_diff_paths is not None else None
        ),
        "commit_diff_available": commit_diff_available,
        "commit_diff_reason": commit_diff_reason,
        "working_tree_changed_path_count": len(working_tree_paths),
        "untracked_path_count": len(untracked_paths),
        "sample_paths": sample_paths,
        "sample_truncated": len(changed_paths) > len(sample_paths),
    }


def _rebuild_trigger_consistency(
    *,
    rebuild_trigger: dict[str, Any] | None,
    indexed_corpus_diff: dict[str, Any],
    current_indexed_hash: str,
    current_full_hash: str,
    non_indexed_markdown_count: int,
) -> dict[str, Any]:
    if not isinstance(rebuild_trigger, dict):
        return {
            "status": "missing",
            "generated_at": None,
            "mismatches": [],
            "refresh_required": False,
            "current_live_corpus_snapshot": {
                "indexed_corpus_hash": current_indexed_hash,
                "full_corpus_hash": current_full_hash,
                "non_indexed_markdown_count": non_indexed_markdown_count,
            },
            "current_indexed_corpus_diff_snapshot": indexed_corpus_diff,
        }

    mismatches: list[str] = []
    live_corpus = rebuild_trigger.get("live_corpus")
    if not isinstance(live_corpus, dict):
        mismatches.append("live_corpus_missing")
    else:
        if live_corpus.get("indexed_corpus_hash") != current_indexed_hash:
            mismatches.append("indexed_corpus_hash")
        if live_corpus.get("full_corpus_hash") != current_full_hash:
            mismatches.append("full_corpus_hash")
        if (
            live_corpus.get("non_indexed_markdown_count")
            != non_indexed_markdown_count
        ):
            mismatches.append("non_indexed_markdown_count")

    verification = rebuild_trigger.get("verification")
    trigger_diff = (
        verification.get("indexed_corpus_diff")
        if isinstance(verification, dict)
        else None
    )
    if not isinstance(trigger_diff, dict):
        mismatches.append("verification.indexed_corpus_diff_missing")
    elif indexed_corpus_diff.get("available") is True:
        if (
            trigger_diff.get("release_corpus_commit")
            != indexed_corpus_diff.get("release_corpus_commit")
        ):
            mismatches.append("verification.release_corpus_commit")
        if (
            trigger_diff.get("current_head_commit")
            != indexed_corpus_diff.get("current_head_commit")
        ):
            mismatches.append("verification.current_head_commit")
        if (
            trigger_diff.get("changed_path_count")
            != indexed_corpus_diff.get("changed_path_count")
        ):
            mismatches.append("verification.changed_path_count")

    return {
        "status": "ok" if not mismatches else "stale",
        "generated_at": rebuild_trigger.get("generated_at"),
        "mismatches": mismatches,
        "refresh_required": bool(mismatches),
        "current_live_corpus_snapshot": {
            "indexed_corpus_hash": current_indexed_hash,
            "full_corpus_hash": current_full_hash,
            "non_indexed_markdown_count": non_indexed_markdown_count,
        },
        "current_indexed_corpus_diff_snapshot": indexed_corpus_diff,
    }


def _recommended_action(
    *,
    readiness: indexer.ReadinessReport,
    rebuild_trigger: dict[str, Any] | None,
) -> dict[str, Any]:
    if isinstance(rebuild_trigger, dict):
        recommended = rebuild_trigger.get("recommended_next_action")
        if (
            isinstance(recommended, dict)
            and readiness.next_command
            and readiness.state in {"missing", "stale", "corrupt"}
        ):
            command = recommended.get("command")
            if isinstance(command, str) and command:
                return {
                    "command": command,
                    "source": "rebuild_trigger",
                    "expected_release_fetch_outcome": recommended.get(
                        "expected_release_fetch_outcome"
                    ),
                    "follow_up": recommended.get("follow_up"),
                }
    return {
        "command": readiness.next_command,
        "source": "readiness",
        "expected_release_fetch_outcome": None,
        "follow_up": None,
    }


def _synced_rebuild_trigger_payload(report: dict[str, Any]) -> dict[str, Any] | None:
    rebuild_trigger = report.get("rebuild_trigger")
    if not isinstance(rebuild_trigger, dict):
        return None

    synced = copy.deepcopy(rebuild_trigger)
    synced["generated_at"] = report.get("generated_at")

    consistency = report.get("rebuild_trigger_consistency")
    if isinstance(consistency, dict):
        live_snapshot = consistency.get("current_live_corpus_snapshot")
        if isinstance(live_snapshot, dict):
            synced["live_corpus"] = dict(live_snapshot)

    verification = synced.get("verification")
    if not isinstance(verification, dict):
        verification = {}
    verification["indexed_corpus_diff"] = report.get("indexed_corpus_diff")
    synced["verification"] = verification
    return synced


def build_smoke_report(
    index_root: Path,
    corpus_root: Path,
    repo_root: Path,
) -> dict[str, Any]:
    generated_at = _utc_now_iso()
    current_indexed_hash = corpus_loader.indexed_corpus_hash(corpus_root)
    current_full_hash = corpus_loader.corpus_hash(corpus_root)
    readiness = indexer.assess_readiness(
        index_root,
        current_indexed_hash=current_indexed_hash,
        current_full_hash=current_full_hash,
    )
    manifest = _load_manifest(index_root)
    rebuild_trigger = _load_rebuild_trigger(index_root)
    recommended_action = _recommended_action(
        readiness=readiness,
        rebuild_trigger=rebuild_trigger,
    )

    manifest_indexed_hash = manifest.get("indexed_corpus_hash") if manifest else None
    manifest_full_hash = manifest.get("corpus_hash") if manifest else None
    try:
        indexer.read_manifest_v3(index_root)
        manifest_v3_ok = True
        manifest_v3_error = None
    except Exception as exc:  # pragma: no cover - diagnostic path
        manifest_v3_ok = False
        manifest_v3_error = f"{type(exc).__name__}: {exc}"

    indexed_paths = {chunk.path for chunk in corpus_loader.iter_corpus(corpus_root)}
    non_indexed_markdown_count = 0
    for md_path in corpus_root.rglob("*.md"):
        relpath = md_path.relative_to(corpus_root).as_posix()
        if relpath not in indexed_paths:
            non_indexed_markdown_count += 1
    indexed_corpus_diff = _indexed_corpus_diff(
        repo_root=repo_root,
        manifest=manifest,
        rebuild_trigger=rebuild_trigger,
    )

    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "index_root": str(index_root),
        "corpus_root": str(corpus_root),
        "readiness": readiness.to_dict(),
        "release_lock": _release_status(index_root, repo_root),
        "indexed_corpus_diff": indexed_corpus_diff,
        "rebuild_trigger": rebuild_trigger,
        "rebuild_trigger_consistency": _rebuild_trigger_consistency(
            rebuild_trigger=rebuild_trigger,
            indexed_corpus_diff=indexed_corpus_diff,
            current_indexed_hash=current_indexed_hash,
            current_full_hash=current_full_hash,
            non_indexed_markdown_count=non_indexed_markdown_count,
        ),
        "manifest": {
            "present": manifest is not None,
            "built_at": manifest.get("built_at") if manifest else None,
            "index_version": manifest.get("index_version") if manifest else None,
            "row_count": manifest.get("row_count") if manifest else None,
            "manifest_v3_ok": manifest_v3_ok,
            "manifest_v3_error": manifest_v3_error,
            "manifest_indexed_corpus_hash": manifest_indexed_hash,
            "manifest_full_corpus_hash": manifest_full_hash,
        },
        "hash_diagnostics": {
            "current_indexed_corpus_hash": current_indexed_hash,
            "current_full_corpus_hash": current_full_hash,
            "indexed_hash_matches_manifest": bool(manifest_indexed_hash)
            and manifest_indexed_hash == current_indexed_hash,
            "full_hash_matches_manifest": bool(manifest_full_hash)
            and manifest_full_hash == current_full_hash,
            "non_indexed_markdown_count": non_indexed_markdown_count,
        },
        "recommended_action": recommended_action,
        "next_step": recommended_action["command"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write a lightweight CS RAG index readiness smoke report."
    )
    parser.add_argument("--out", default="state/cs_rag", help="Index root to inspect.")
    parser.add_argument(
        "--corpus", default="knowledge/cs", help="Corpus root to inspect."
    )
    parser.add_argument(
        "--report",
        default="state/cs_rag/index_smoke.json",
        help="JSON path to write the smoke report.",
    )
    parser.add_argument(
        "--sync-trigger",
        action="store_true",
        help=(
            "Refresh state/cs_rag/rebuild_trigger.json with the current live "
            "corpus snapshot before writing the smoke report."
        ),
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[3]
    index_root = Path(args.out)
    corpus_root = Path(args.corpus)
    report = build_smoke_report(
        index_root=index_root,
        corpus_root=corpus_root,
        repo_root=repo_root,
    )
    if args.sync_trigger:
        refreshed_trigger = _synced_rebuild_trigger_payload(report)
        trigger_path = index_root / "rebuild_trigger.json"
        if refreshed_trigger is not None:
            trigger_path.write_text(
                json.dumps(refreshed_trigger, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report["rebuild_trigger"] = refreshed_trigger
            report["rebuild_trigger_consistency"] = _rebuild_trigger_consistency(
                rebuild_trigger=refreshed_trigger,
                indexed_corpus_diff=report["indexed_corpus_diff"],
                current_indexed_hash=report["hash_diagnostics"][
                    "current_indexed_corpus_hash"
                ],
                current_full_hash=report["hash_diagnostics"][
                    "current_full_corpus_hash"
                ],
                non_indexed_markdown_count=report["hash_diagnostics"][
                    "non_indexed_markdown_count"
                ],
            )
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "readiness": report["readiness"]["state"],
                "release_lock": report["release_lock"]["status"],
                "report": str(report_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

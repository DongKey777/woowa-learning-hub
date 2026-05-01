#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from core.contexts import build_coach_context, build_my_pr_context, write_next_actions_from_context  # type: ignore
from core.git_context import read_current_pr  # type: ignore
from core.packets import generate_compare_packet, generate_reviewer_packet, generate_topic_packet  # type: ignore
from core.paths import DEFAULT_SCHEMA_PATH, PR_ARCHIVE_DIR, ROOT, MISSIONS_DIR, REGISTRY_PATH, ensure_global_layout, repo_archive_db  # type: ignore
from core.profile import load_profile, save_profile  # type: ignore
from core.reviewer_profile import build_reviewer_profile  # type: ignore
from core.response import build_response  # type: ignore
from core.archive import ArchiveSyncError, bootstrap_repo_archive, compute_archive_status, write_archive_status  # type: ignore
from core.coach_run import run_coach  # type: ignore
from core.learner_state import write_learner_state  # type: ignore
from core.golden import DEFAULT_GOLDEN_FIXTURES, run_golden  # type: ignore
from core.mission_map import write_mission_map  # type: ignore
from core.readiness import build_registry_audit, build_repo_readiness  # type: ignore
from core.repo_intake import detect_repo_metadata, resolve_repo_input  # type: ignore
from core.session import start_session, write_response_artifacts  # type: ignore
from core.registry import find_repo, list_repos, upsert_repo  # type: ignore
from core.schema_validation import validate_file, validate_payload  # type: ignore
from core.shell import run_capture  # type: ignore
from core.orchestrator import Orchestrator  # type: ignore
from core.orchestrator_workers import fleet_status, run_supervisor_loop, run_worker_loop, start_fleet_background, stop_fleet  # type: ignore


def _read_json_object(path: Path) -> tuple[dict | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - doctor should report, not fail
        return None, f"{type(exc).__name__}: {exc}"
    if not isinstance(payload, dict):
        return None, "JSON root is not an object"
    return payload, None


def _nested_get(payload: dict, path: tuple[str, ...]) -> object | None:
    current: object = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _manifest_value(manifest: dict, field: str) -> object | None:
    if field == "encoder.model_id":
        encoder_model_id = _nested_get(manifest, ("encoder", "model_id"))
        return encoder_model_id if encoder_model_id is not None else manifest.get("embed_model")
    if field == "encoder.model_version":
        return _nested_get(manifest, ("encoder", "model_version"))
    return manifest.get(field)


def _normalize_lock_value(field: str, value: object) -> object:
    if field == "modalities" and isinstance(value, list):
        return sorted(str(item) for item in value)
    return value


def _rag_model_lock_report(root: Path | None = None) -> dict:
    if root is None:
        root = ROOT
    config_rel = Path("config") / "rag_models.json"
    manifest_rel = Path("state") / "cs_rag" / "manifest.json"
    config_path = root / config_rel
    manifest_path = root / manifest_rel

    base: dict = {
        "config": str(config_rel),
        "manifest": str(manifest_rel),
        "status": "SKIP",
        "line": f"SKIP rag_model_lock: {config_rel} missing",
        "warnings": [],
        "compared": {},
        "skipped_fields": [],
    }

    if not config_path.exists():
        return base

    config, config_error = _read_json_object(config_path)
    if config_error is not None or config is None:
        warning = f"{config_rel} unreadable: {config_error}"
        base.update({
            "status": "WARN",
            "line": f"WARN rag_model_lock: {warning}",
            "warnings": [warning],
        })
        return base

    if not manifest_path.exists():
        warning = f"{manifest_rel} missing; live index comparison skipped"
        base.update({
            "status": "WARN",
            "line": f"WARN rag_model_lock: {config_rel} found; {warning}",
            "warnings": [warning],
        })
        return base

    manifest, manifest_error = _read_json_object(manifest_path)
    if manifest_error is not None or manifest is None:
        warning = f"{manifest_rel} unreadable: {manifest_error}"
        base.update({
            "status": "WARN",
            "line": f"WARN rag_model_lock: {warning}",
            "warnings": [warning],
        })
        return base

    expected_fields = {
        "index_version": _nested_get(config, ("index", "index_version")),
        "encoder.model_id": _nested_get(config, ("encoder", "model_id")),
        "encoder.model_version": _nested_get(config, ("encoder", "model_version")),
        "modalities": _nested_get(config, ("index", "modalities")),
        "row_count": _nested_get(config, ("index", "row_count")),
    }
    warnings: list[str] = []
    compared: dict[str, dict[str, object]] = {}
    skipped_fields: list[str] = []

    for field, expected in expected_fields.items():
        actual = _manifest_value(manifest, field)
        if expected is None or actual is None:
            skipped_fields.append(field)
            continue
        normalized_expected = _normalize_lock_value(field, expected)
        normalized_actual = _normalize_lock_value(field, actual)
        compared[field] = {
            "expected": expected,
            "actual": actual,
        }
        if normalized_expected != normalized_actual:
            warnings.append(f"{field} expected {expected!r}, got {actual!r}")

    if warnings:
        base.update({
            "status": "WARN",
            "line": f"WARN rag_model_lock: {len(warnings)} mismatch(es) against {config_rel}",
            "warnings": warnings,
            "compared": compared,
            "skipped_fields": skipped_fields,
        })
        return base

    base.update({
        "status": "OK",
        "line": f"OK rag_model_lock: {config_rel} matches {manifest_rel} ({len(compared)} field(s) checked)",
        "compared": compared,
        "skipped_fields": skipped_fields,
    })
    return base


def cmd_bootstrap(_: argparse.Namespace) -> int:
    ensure_global_layout()
    print(json.dumps({
        "status": "ok",
        "root": str(ROOT),
        "missions": str(MISSIONS_DIR),
        "registry": str(REGISTRY_PATH),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_doctor(_: argparse.Namespace) -> int:
    ensure_global_layout()
    checks = {
        "python3": shutil.which("python3") is not None,
        "gh": shutil.which("gh") is not None,
        "missions_dir": MISSIONS_DIR.exists(),
        "registry": REGISTRY_PATH.exists(),
        "pr_archive": PR_ARCHIVE_DIR.exists(),
    }
    checks["rag_model_lock"] = _rag_model_lock_report(ROOT)
    gh_auth = None
    if checks["gh"]:
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        gh_auth = result.returncode == 0
    checks["gh_auth"] = gh_auth
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0


def cmd_onboard_repo(args: argparse.Namespace) -> int:
    ensure_global_layout()
    repo_path = Path(args.path).expanduser().resolve()
    if not repo_path.exists():
        print(f"repo path not found: {repo_path}", file=sys.stderr)
        return 1
    if not (repo_path / ".git").exists():
        print(f"not a git repository: {repo_path}", file=sys.stderr)
        return 1

    detected = detect_repo_metadata(repo_path, repo_name=args.name or repo_path.name)
    repo_info = upsert_repo(
        name=detected["name"],
        path=repo_path,
        upstream=args.upstream or detected.get("upstream"),
        track=args.track or detected.get("track"),
        mission=args.mission or detected.get("mission"),
        title_contains=args.title_contains or detected.get("title_contains"),
        extra_fields={
            "origin_full_name": detected.get("origin_full_name"),
            "origin_url": detected.get("origin_url"),
            "branch_hint": detected.get("branch_hint"),
            "current_pr_title": detected.get("current_pr_title"),
            "auto_detected_at": detected.get("auto_detected_at"),
        },
    )
    print(json.dumps({"status": "ok", **repo_info}, ensure_ascii=False, indent=2))
    return 0


def cmd_list_repos(_: argparse.Namespace) -> int:
    repos = list_repos()
    if not repos:
        print("No onboarded repos.")
        return 0
    for repo in repos:
        upstream = repo.get("upstream") or "-"
        track = repo.get("track") or "-"
        mission = repo.get("mission") or "-"
        title_contains = repo.get("title_contains") or "-"
        print(f"{repo['name']}\t{track}\t{mission}\t{title_contains}\t{repo['path']}\t{upstream}")
    return 0


def cmd_sync_prs(args: argparse.Namespace) -> int:
    repo = find_repo(args.repo)
    upstream = repo.get("upstream")
    if not upstream or "/" not in upstream:
        raise SystemExit(f"invalid upstream for repo {args.repo}: {upstream}")
    owner, repo_name = upstream.split("/", 1)
    db_path = repo_archive_db(args.repo)
    track = args.track or repo.get("track") or "java"
    mission = args.mission or repo.get("mission") or args.repo
    title_contains = args.title_contains or repo.get("title_contains")
    mission_map = write_mission_map(repo)
    mission_keywords = ((mission_map.get("analysis") or {}).get("retrieval_terms") or [])[:12]
    cmd = [
        "python3", str(PR_ARCHIVE_DIR / "collect_prs.py"),
        "--owner", owner,
        "--repo", repo_name,
        "--track", track,
        "--mission", mission,
        "--mode", args.mode,
        "--db-path", str(db_path),
        "--schema-path", str(DEFAULT_SCHEMA_PATH),
    ]
    if title_contains:
        cmd.extend(["--title-contains", title_contains])
    for keyword in mission_keywords:
        cmd.extend(["--mission-keyword", keyword])
    if args.since:
        cmd.extend(["--since", args.since])
    if args.limit is not None:
        cmd.extend(["--limit", str(args.limit)])
    result = run_capture(cmd)
    if result.returncode != 0:
        try:
            archive_status = write_archive_status(args.repo)
        except Exception:  # noqa: BLE001
            archive_status = None
        print(json.dumps({
            "status": "failed",
            "repo": args.repo,
            "db_path": str(db_path),
            "mode": args.mode,
            "error": result.stderr.strip() or "archive sync failed",
            "command": cmd,
            "mission_keywords": mission_keywords,
            "archive_status": archive_status,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return result.returncode
    print(json.dumps({
        "status": "ok",
        "repo": args.repo,
        "db_path": str(db_path),
        "mode": args.mode,
        "mission_map_path": mission_map.get("json_path"),
        "mission_keywords": mission_keywords,
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_topic(args: argparse.Namespace) -> int:
    payload = generate_topic_packet(args.repo, repo_archive_db(args.repo), args.topic, args.query)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_reviewer(args: argparse.Namespace) -> int:
    payload = generate_reviewer_packet(args.repo, repo_archive_db(args.repo), args.reviewer)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    payload = generate_compare_packet(args.repo, repo_archive_db(args.repo), args.prs)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_mission_map(args: argparse.Namespace) -> int:
    repo, _ = resolve_repo_input(repo_name=args.repo, repo_path=args.path, auto_register=True)
    payload = write_mission_map(repo)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_my_pr(args: argparse.Namespace) -> int:
    repo = find_repo(args.repo)
    payload = build_my_pr_context(repo, repo_archive_db(args.repo), args.pr)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_coach(args: argparse.Namespace) -> int:
    repo = find_repo(args.repo)
    payload = build_coach_context(repo, repo_archive_db(args.repo), args.prompt, args.pr, args.reviewer)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_next_action(args: argparse.Namespace) -> int:
    context_name = "coach-context" if args.context == "coach" else "my-pr-context"
    context_path = repo_archive_db(args.repo).parent.parent / "contexts" / f"{context_name}.json"
    if not context_path.exists():
        raise SystemExit(f"context file not found: {context_path}")
    context = json.loads(context_path.read_text(encoding="utf-8"))
    payload = write_next_actions_from_context(context)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


_OPTIONAL_MISSING_SCHEMAS = {"cs-augmentation", "drill-pending"}


def _append_validation(validations: list[dict], schema_name: str, path: Path) -> None:
    if not path.exists():
        entry = {"schema": schema_name, "path": str(path), "exists": False, "valid": None}
        if schema_name in _OPTIONAL_MISSING_SCHEMAS:
            entry["status"] = "not_applicable"
        validations.append(entry)
        return
    try:
        validate_file(schema_name, path)
        validations.append({"schema": schema_name, "path": str(path), "exists": True, "valid": True})
    except Exception as e:  # noqa: BLE001
        if schema_name == "coach-response":
            payload = json.loads(path.read_text(encoding="utf-8"))
            legacy_fields = [
                field
                for field in ["response_role", "question_focus", "memory_policy", "usage_guidance", "teaching_points"]
                if field not in payload
            ]
            if payload.get("response_type") == "coach_response" and legacy_fields:
                validations.append({
                    "schema": schema_name,
                    "path": str(path),
                    "exists": True,
                    "valid": True,
                    "legacy_compatible": True,
                    "missing_legacy_fields": legacy_fields,
                })
                return
        validations.append({"schema": schema_name, "path": str(path), "exists": True, "valid": False, "error": str(e)})


def _append_history_validation(validations: list[dict], path: Path) -> None:
    if not path.exists():
        validations.append({"schema": "learning-memory-entry", "path": str(path), "exists": False, "valid": None})
        return
    errors = []
    legacy_lines = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            validate_payload("learning-memory-entry", json.loads(raw_line))
        except Exception as e:  # noqa: BLE001
            if "missing required field 'question_fingerprint'" in str(e) or "missing required field 'diff_fingerprint'" in str(e):
                legacy_lines.append(line_number)
                continue
            errors.append({"line": line_number, "error": str(e)})
    validations.append({
        "schema": "learning-memory-entry",
        "path": str(path),
        "exists": True,
        "valid": not errors,
        "legacy_compatible": bool(legacy_lines),
        "legacy_lines": legacy_lines or None,
        "line_errors": errors or None,
    })


def _append_drill_history_validation(validations: list[dict], path: Path) -> None:
    if not path.exists():
        validations.append({
            "schema": "drill-history-entry",
            "path": str(path),
            "exists": False,
            "valid": None,
            "status": "not_applicable",
        })
        return
    errors = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            validate_payload("drill-history-entry", json.loads(raw_line))
        except Exception as e:  # noqa: BLE001
            errors.append({"line": line_number, "error": str(e)})
    validations.append({
        "schema": "drill-history-entry",
        "path": str(path),
        "exists": True,
        "valid": not errors,
        "line_errors": errors or None,
    })


def _discover_validation_targets(base: Path) -> list[tuple[str, Path]]:
    targets: list[tuple[str, Path]] = [
        ("archive-status", base / "archive" / "status.json"),
        ("mission-map", base / "analysis" / "mission-map.json"),
        ("learner-profile", base / "profiles" / "learner.json"),
        ("learning-memory-summary", base / "memory" / "summary.json"),
        ("learning-memory-profile", base / "memory" / "profile.json"),
        ("coach-run-result", base / "actions" / "coach-run.json"),
    ]

    sidecar = base / "actions" / "coach-run.error.json"
    if sidecar.exists():
        targets.append(("coach-run-result", sidecar))

    for path in sorted((base / "profiles").glob("reviewer-*.json")):
        targets.append(("reviewer-profile", path))

    for path in sorted((base / "packets").glob("topic-*.json")):
        targets.append(("topic-packet", path))
    for path in sorted((base / "packets").glob("reviewer-*.json")):
        targets.append(("reviewer-packet", path))
    for path in sorted((base / "packets").glob("compare-*.json")):
        targets.append(("compare-packet", path))
    for path in sorted((base / "packets").glob("pr-*-report.json")):
        targets.append(("pr-report", path))

    context_map = {
        "learner-state.json": "learner-state",
        "my-pr-context.json": "my-pr-context",
        "coach-context.json": "coach-context",
        "coach-focus.json": "session-pr-focus",
        "coach-candidate-interpretation.json": "candidate-interpretation",
        "cs-augmentation.json": "cs-augmentation",
    }
    for name, schema in context_map.items():
        targets.append((schema, base / "contexts" / name))

    targets.append(("drill-pending", base / "memory" / "drill-pending.json"))

    for path in sorted((base / "actions").glob("*.json")):
        if path.name in {"coach-run.json", "coach-run.error.json"}:
            continue
        if path.name.endswith("-response.json"):
            targets.append(("coach-response", path))
            continue
        if path.name.endswith("-session.json"):
            targets.append(("session-result", path))
            continue
        if path.name in {"coach.json", "my-pr.json"}:
            targets.append(("next-actions", path))

    return targets


def cmd_validate_state(args: argparse.Namespace) -> int:
    base = repo_archive_db(args.repo).parent.parent
    write_archive_status(args.repo)
    validations = []
    for schema_name, path in _discover_validation_targets(base):
        _append_validation(validations, schema_name, path)
    _append_history_validation(validations, base / "memory" / "history.jsonl")
    _append_drill_history_validation(validations, base / "memory" / "drill-history.jsonl")
    print(json.dumps({"repo": args.repo, "validations": validations}, ensure_ascii=False, indent=2))
    return 0


def cmd_set_profile(args: argparse.Namespace) -> int:
    profile = load_profile(args.repo)
    if args.experience_level:
        profile["experience_level"] = args.experience_level
    if args.preferred_depth:
        profile["preferred_depth"] = args.preferred_depth
    if args.focus is not None:
        profile["focus"] = args.focus
    if args.recent_weaknesses is not None:
        profile["recent_weaknesses"] = args.recent_weaknesses
    saved = save_profile(args.repo, profile)
    print(json.dumps({"repo": args.repo, "profile": saved}, ensure_ascii=False, indent=2))
    return 0


def cmd_show_profile(args: argparse.Namespace) -> int:
    print(json.dumps({"repo": args.repo, "profile": load_profile(args.repo)}, ensure_ascii=False, indent=2))
    return 0


def cmd_reviewer_profile(args: argparse.Namespace) -> int:
    packet = generate_reviewer_packet(args.repo, repo_archive_db(args.repo), args.reviewer)
    if not packet.get("generated"):
        print(json.dumps({"repo": args.repo, "reviewer": args.reviewer, "error": packet.get("error")}, ensure_ascii=False, indent=2))
        return 1
    profile = build_reviewer_profile(args.repo, packet)
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    return 0


def cmd_compose_response(args: argparse.Namespace) -> int:
    base = repo_archive_db(args.repo).parent.parent
    context_name = "coach-context" if args.context == "coach" else "my-pr-context"
    context_path = base / "contexts" / f"{context_name}.json"
    if not context_path.exists():
        raise SystemExit(f"context file not found: {context_path}")
    context = json.loads(context_path.read_text(encoding="utf-8"))

    action_name = "coach" if args.context == "coach" else "my-pr"
    next_actions = write_next_actions_from_context(context)

    response = build_response(context, next_actions)
    validate_payload("coach-response", response)
    json_path, md_path = write_response_artifacts(args.repo, args.context, response)
    response["json_path"] = str(json_path)
    response["markdown_path"] = str(md_path)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


def cmd_session_start(args: argparse.Namespace) -> int:
    repo = find_repo(args.repo)
    payload = start_session(
        repo,
        mode=args.context,
        prompt=args.prompt,
        pr_number=args.pr,
        reviewer=args.reviewer,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_archive_status(args: argparse.Namespace) -> int:
    repo = find_repo(args.repo)
    status = write_archive_status(repo["name"], freshness_hours=args.freshness_hours)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


def cmd_repo_readiness(args: argparse.Namespace) -> int:
    payload = build_repo_readiness(
        repo_name=args.repo,
        repo_path=args.path,
        freshness_hours=args.freshness_hours,
    )
    validate_payload("repo-readiness", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_registry_audit(args: argparse.Namespace) -> int:
    payload = build_registry_audit(freshness_hours=args.freshness_hours)
    validate_payload("registry-audit", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_bootstrap_repo(args: argparse.Namespace) -> int:
    repo = find_repo(args.repo)
    try:
        result = bootstrap_repo_archive(repo, limit=args.limit, freshness_hours=args.freshness_hours)
    except ArchiveSyncError as e:
        archive_status = write_archive_status(repo["name"], freshness_hours=args.freshness_hours)
        print(json.dumps({
            "status": "failed",
            "repo": repo["name"],
            "bootstrap": True,
            "retryable": True,
            "error": e.to_dict(),
            "archive_status": archive_status,
            "next_steps": (archive_status.get("bootstrap_guidance") or {}).get("next_steps", []),
        }, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_assess_learner_state(args: argparse.Namespace) -> int:
    payload = write_learner_state(
        repo_name=args.repo,
        repo_path=Path(args.path) if args.path else None,
        prompt=args.prompt,
        upstream_owner_repo=args.upstream,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_coach_run(args: argparse.Namespace) -> int:
    payload = run_coach(
        repo_name=args.repo,
        repo_path=args.path,
        prompt=args.prompt,
        pr_number=args.pr,
        reviewer=args.reviewer,
        context=args.context,
        freshness_hours=args.freshness_hours,
        force_sync=args.force_sync,
        sync_limit=args.sync_limit,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_golden(args: argparse.Namespace) -> int:
    fixtures_path = Path(args.fixtures).expanduser().resolve() if args.fixtures else DEFAULT_GOLDEN_FIXTURES
    payload = run_golden(fixtures_path, stop_on_failure=args.stop_on_failure)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload.get("failed_count") else 0


def _check_archive_ready(repo: str) -> bool:
    """Read state/repos/<repo>/archive/status.json — True iff bootstrap_state == 'ready'."""
    status_path = ROOT / "state" / "repos" / repo / "archive" / "status.json"
    if not status_path.exists():
        return False
    try:
        data = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return data.get("bootstrap_state") == "ready"


def _resolve_upstream(repo: str) -> str | None:
    """Look up upstream slug via find_repo(repo). Returns None if not registered."""
    try:
        from core.registry import find_repo  # type: ignore
    except ImportError:
        return None
    try:
        info = find_repo(repo)
    except Exception:
        return None
    if not isinstance(info, dict):
        return None
    return info.get("upstream") or info.get("upstream_repo")


def _check_open_pr_safely(upstream: str | None) -> bool:
    """`gh pr list --repo <upstream> --author "@me" --state open --json number`.

    Any failure (no upstream, gh missing, network down, JSON parse error) is
    silently degraded to False so the router doesn't enter a phantom Tier 3.
    """
    if not upstream:
        return False
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--repo", upstream, "--author", "@me",
             "--state", "open", "--json", "number"],
            capture_output=True, text=True, timeout=10, check=False,
        )
        if result.returncode != 0:
            return False
        items = json.loads(result.stdout or "[]")
        return bool(items)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return False


def _build_repo_context(repo: str | None) -> dict | None:
    """Build repo_context dict for interactive_rag_router.classify().

    repo=None → return None (router treats as Tier 3 blocked).
    Otherwise dict with archive_ready/has_open_pr/repo_name. All checks
    read-only; gh failures degrade to has_open_pr=False.
    """
    if not repo:
        return None
    return {
        "repo_name": repo,
        "archive_ready": _check_archive_ready(repo),
        "has_open_pr": _check_open_pr_safely(_resolve_upstream(repo)),
    }


def cmd_rag_ask(args: argparse.Namespace) -> int:
    """Tier-based RAG router for learning sessions.

    Returns one-line JSON: {decision, hits, next_command}.
    - tier 0 / blocked: hits=null, next_command=null
    - tier 1/2: hits = augment() result, next_command=null
    - tier 3: hits=null, next_command = bin/coach-run absolute path

    Side effect: every classification (all tiers, including 0 and Tier 3
    blocked) is appended to `state/learner/history.jsonl` so the
    closed-loop personalization layer has full coverage.
    """
    import shlex
    from dataclasses import asdict

    from core.interactive_rag_router import classify  # type: ignore
    try:
        from core.learner_memory import (  # type: ignore
            build_learner_context,
            load_learner_profile,
        )
        learner_profile = load_learner_profile()
    except Exception:
        learner_profile = None
        build_learner_context = None  # type: ignore[assignment]

    decision = classify(
        args.prompt,
        repo_context=_build_repo_context(args.repo),
        learner_profile=learner_profile,
    )
    out: dict = {
        "decision": asdict(decision),
        "hits": None,
        "next_command": None,
        "learner_context": None,
    }
    if build_learner_context is not None and learner_profile is not None:
        try:
            out["learner_context"] = build_learner_context(
                learner_profile,
                prompt=args.prompt,
                decision=out["decision"],
            )
        except Exception:
            out["learner_context"] = None

    if decision.tier in (1, 2) and not decision.blocked:
        # Lazy import — sentence-transformers loads only when needed
        # Match the existing pattern from coach_run.py (scripts.learning.*)
        from scripts.learning import integration  # type: ignore
        from scripts.learning.rag import indexer as rag_indexer  # type: ignore
        # Pre-build readiness with absolute corpus_root so cwd-independence holds.
        # Default corpus_loader.DEFAULT_CORPUS_ROOT = Path("knowledge/cs") is
        # relative to cwd; without this, calling bin/rag-ask from /tmp would
        # compute an empty corpus hash → rag_ready=false → no hits.
        index_root = ROOT / "state" / "cs_rag"
        corpus_root = ROOT / "knowledge" / "cs"
        readiness = rag_indexer.is_ready(index_root, corpus_root=corpus_root)
        try:
            result = integration.augment(
                prompt=args.prompt,
                cs_search_mode=decision.mode,
                top_k=3 if decision.tier == 1 else 5,
                experience_level=decision.experience_level,
                index_root=index_root,
                learning_points=None,
                topic_hints=None,
                readiness=readiness,
                learner_context=out["learner_context"],
                backend=args.rag_backend,
            )
        except Exception as exc:  # noqa: BLE001 — surface any failure as note
            out["hits"] = {"error": f"{type(exc).__name__}: {exc}"}
        else:
            out["hits"] = result

    elif decision.tier == 3 and not decision.blocked:
        coach_run_path = str(ROOT / "bin" / "coach-run")
        out["next_command"] = (
            f"{coach_run_path} --repo {shlex.quote(args.repo or '')}"
            f" --prompt {shlex.quote(args.prompt)}"
        )

    _record_rag_ask_event(args, decision, out)
    _record_routing_log(args, decision)
    out["feedback_hint"] = _build_feedback_hint(args, out)
    print(json.dumps(out, ensure_ascii=False))
    return 0


def _build_feedback_hint(args: argparse.Namespace, out: dict) -> dict | None:
    """When rag-ask returned hits, surface a ready-to-run command set
    so the AI session can offer the learner a one-line relevance
    signal (helpful / not_helpful / unclear). Closes the rag-ask →
    feedback loop. See plan §P7.1 + scripts/learning/rag/feedback.py.

    Returns None when there's nothing to provide feedback on (Tier 0,
    Tier 3 coach handoff, or empty hits).
    """
    import shlex
    hits = out.get("hits")
    if not isinstance(hits, dict):
        return None
    paths: list[str] = []
    seen: set[str] = set()
    for bucket_key in ("by_learning_point", "by_fallback_key"):
        bucket = hits.get(bucket_key)
        if not isinstance(bucket, dict):
            continue
        for entries in bucket.values():
            if not isinstance(entries, list):
                continue
            for h in entries:
                if not isinstance(h, dict):
                    continue
                p = h.get("path")
                if p and p not in seen:
                    seen.add(p)
                    paths.append(p)
    if not paths:
        return None
    learn_feedback = str(ROOT / "bin" / "learn-feedback")
    qprompt = shlex.quote(args.prompt)
    qrepo = ("--repo " + shlex.quote(args.repo)) if args.repo else ""
    hit_args = " ".join(f"--hit {shlex.quote(p)}" for p in paths)
    return {
        "instructions": (
            "원하면 한 줄 신호로 알려줘 — 시스템이 학습돼. "
            "AI 세션이 학습자 의사 확인 후 아래 명령 중 하나를 실행해."
        ),
        "commands": {
            "helpful": (
                f"{learn_feedback} {qprompt} --signal helpful "
                f"{hit_args} {qrepo}".strip()
            ),
            "not_helpful": (
                f"{learn_feedback} {qprompt} --signal not_helpful "
                f"{hit_args} {qrepo}".strip()
            ),
            "unclear": (
                f"{learn_feedback} {qprompt} --signal unclear {qrepo}".strip()
            ),
        },
    }


def _record_routing_log(args: argparse.Namespace, decision) -> None:
    """Append the classify decision to state/repos/<repo>/logs/routing.jsonl
    (plan §P5.2). Best-effort — never breaks the primary CLI."""
    try:
        from core.routing_log import record_routing_decision  # type: ignore
        record_routing_decision(
            prompt=args.prompt,
            decision=decision,
            repo=args.repo or None,
            repo_root=ROOT,
        )
    except Exception:
        pass


def _record_rag_ask_event(
    args: argparse.Namespace, decision, out: dict
) -> None:
    """Append a learner event for every rag-ask outcome.

    Catches any exception so a learner-memory hiccup never breaks the
    primary CLI contract — `bin/rag-ask` must always produce its JSON.
    """
    try:
        from core.concept_catalog import load_catalog  # type: ignore
        from core.learner_memory import (  # type: ignore
            _resolve_learner_id,
            append_learner_event,
            build_rag_ask_event,
        )
        rag_result = (
            out["hits"]
            if isinstance(out.get("hits"), dict) and "error" not in out["hits"]
            else None
        )
        event = build_rag_ask_event(
            prompt=args.prompt,
            tier=decision.tier,
            mode=decision.mode,
            experience_level=decision.experience_level,
            rag_result=rag_result,
            repo=getattr(args, "repo", None),
            module=getattr(args, "module", None),
            learner_id=_resolve_learner_id(),
            blocked=decision.blocked,
            catalog=load_catalog(),
        )
        append_learner_event(event)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[learner-memory] rag-ask event append failed: {exc}\n")


def cmd_learn_test(args: argparse.Namespace) -> int:
    """Scan JUnit XML outputs and record each `<testcase>` as a learner event.

    Inputs:
      --module / --path: pick the module under `missions/spring-learning-test/`
                        OR specify an explicit `build/test-results/test/`.
      --no-record: dry-run (parse + summarize, do not append events).

    Output: JSON `{module, scanned, recorded, passed, failed}`.
    """
    import xml.etree.ElementTree as ET

    if args.path:
        results_dir = Path(args.path)
    else:
        if not args.module:
            sys.stderr.write("learn-test: provide --module or --path\n")
            return 2
        results_dir = (
            ROOT
            / "missions"
            / "spring-learning-test"
            / args.module
            / "build"
            / "test-results"
            / "test"
        )

    if not results_dir.exists():
        sys.stderr.write(f"learn-test: no test results at {results_dir}\n")
        return 2

    junit_tests: list[dict] = []
    for xml_path in sorted(results_dir.glob("TEST-*.xml")):
        try:
            tree = ET.parse(xml_path)
        except ET.ParseError:
            continue
        for case in tree.iter("testcase"):
            test = {
                "class": case.get("classname") or "",
                "name": case.get("name") or "",
                "duration_ms": _parse_junit_duration_ms(case.get("time")),
            }
            failure_node = case.find("failure")
            if failure_node is None:
                failure_node = case.find("error")
            if failure_node is not None:
                test["failure"] = {
                    "message": (failure_node.get("message") or "").strip(),
                    "stack_trace": (failure_node.text or "").strip(),
                }
            junit_tests.append(test)

    passed = sum(1 for t in junit_tests if "failure" not in t)
    failed = len(junit_tests) - passed
    recorded = 0

    # When --path is given without --module, infer the module from the
    # results dir so concept attribution + module_context still work.
    inferred_module = args.module
    if inferred_module is None:
        from core.concept_catalog import infer_module_from_path  # type: ignore
        inferred_module = infer_module_from_path(str(results_dir))

    if not args.no_record:
        try:
            from core.concept_catalog import load_catalog  # type: ignore
            from core.learner_memory import (  # type: ignore
                _resolve_learner_id,
                append_learner_event,
                build_test_result_event,
            )
            catalog = load_catalog()
            learner_id = _resolve_learner_id()
            for test in junit_tests:
                try:
                    event = build_test_result_event(
                        junit_test=test,
                        learner_id=learner_id,
                        module=inferred_module,
                        catalog=catalog,
                    )
                    append_learner_event(event)
                    recorded += 1
                except Exception:
                    continue
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"learn-test: record failed — {exc}\n")

    print(json.dumps(
        {
            "module": inferred_module,
            "results_dir": str(results_dir),
            "scanned": len(junit_tests),
            "recorded": recorded,
            "passed": passed,
            "failed": failed,
        },
        ensure_ascii=False,
    ))
    return 0


def _parse_junit_duration_ms(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(round(float(value) * 1000))
    except ValueError:
        return None


def cmd_learn_drill(args: argparse.Namespace) -> int:
    """Standalone drill workflow for the learner stream.

    Subactions:
      offer   — pick an uncertain concept (or `--concept ID`), build a drill
                question, save it as `state/learner/drill-pending.json`
      answer  — read pending drill, score the supplied answer, append a
                drill_answer event, clear pending
      status  — print the current pending drill (or "no pending")
      cancel  — clear pending without scoring
    """
    sub = args.drill_command
    if sub == "offer":
        return _drill_offer(args)
    if sub == "answer":
        return _drill_answer(args)
    if sub == "status":
        return _drill_status(args)
    if sub == "cancel":
        return _drill_cancel(args)
    sys.stderr.write(f"unknown learn-drill subcommand: {sub}\n")
    return 2


def _drill_offer(args: argparse.Namespace) -> int:
    import hashlib
    from datetime import datetime, timezone

    from core.concept_catalog import load_catalog  # type: ignore
    from core.learner_memory import (  # type: ignore
        default_profile,
        load_learner_profile,
    )
    from core.paths import learner_drill_pending_path  # type: ignore

    pending_path = learner_drill_pending_path()
    if pending_path.exists() and not args.force:
        sys.stderr.write(
            "drill-pending.json이 이미 있습니다. 기존 drill 먼저 답하거나 "
            "`bin/learn-drill cancel`로 취소하세요. 강제 발행은 --force.\n"
        )
        return 2

    catalog = load_catalog()
    profile = load_learner_profile() or default_profile()
    concept_id = args.concept or _pick_uncertain_concept_id(profile)
    if not concept_id:
        sys.stderr.write(
            "추천할 uncertain concept이 없어요. `--concept concept:spring/<name>` 명시해 주세요.\n"
        )
        return 2

    concept = (catalog.get("concepts") or {}).get(concept_id)
    if not concept:
        sys.stderr.write(f"unknown concept_id: {concept_id}\n")
        return 2

    name = concept.get("name") or concept_id
    korean = concept.get("korean")
    display_name = f"{name} ({korean})" if korean else name
    question = (
        f"{display_name}이 무엇이고, 왜 그렇게 동작하며, 실제 코드에서 어떻게 "
        f"사용되는지 자기 말로 설명해 보세요. 최소 3-4문장 이상으로요."
    )
    expected_terms = _drill_expected_terms(concept)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sid_seed = f"{concept_id}|{now}".encode("utf-8")
    drill_session_id = f"learner-drill-{hashlib.sha1(sid_seed).hexdigest()[:12]}"
    offer = {
        "drill_session_id": drill_session_id,
        "concept_id": concept_id,
        "linked_learning_point": concept_id,
        "question": question,
        "expected_terms": expected_terms,
        "source_doc": None,
        "created_at": now,
        "ttl_turns": 5,
    }
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text(
        json.dumps(offer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(
        {
            "drill_session_id": drill_session_id,
            "concept_id": concept_id,
            "question": question,
            "pending_path": str(pending_path),
        },
        ensure_ascii=False, indent=2,
    ))
    return 0


def _drill_answer(args: argparse.Namespace) -> int:
    from datetime import datetime, timezone

    from core.concept_catalog import load_catalog  # type: ignore
    from core.learner_memory import (  # type: ignore
        _resolve_learner_id,
        append_learner_event,
        build_drill_answer_event,
    )
    from core.paths import learner_drill_pending_path  # type: ignore
    from scripts.learning import drill as drill_module  # type: ignore

    pending_path = learner_drill_pending_path()
    if not pending_path.exists():
        sys.stderr.write(
            "pending drill이 없어요. `bin/learn-drill offer` 먼저 실행하세요.\n"
        )
        return 2
    try:
        pending = json.loads(pending_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"drill-pending.json 파싱 실패: {exc}\n")
        return 2

    answer = args.answer or sys.stdin.read()
    if not answer or not answer.strip():
        sys.stderr.write("답변이 비어있어요. --answer 인자 또는 stdin으로 답을 넣어 주세요.\n")
        return 2

    drill_result = drill_module.score_pending_answer(answer, pending)
    drill_result["scored_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if "linked_learning_point" not in drill_result:
        drill_result["linked_learning_point"] = pending.get("linked_learning_point")

    catalog = load_catalog()
    learner_id = _resolve_learner_id()
    concept_id = pending.get("concept_id") or pending.get("linked_learning_point")
    drill_record_for_event = dict(drill_result)
    drill_record_for_event["linked_learning_point"] = concept_id
    event = build_drill_answer_event(
        drill_record=drill_record_for_event,
        learner_id=learner_id,
        repo=None,
        catalog=catalog,
    )
    # build_drill_answer_event uses lp_to_concept_id; for canonical concept_ids
    # passed directly, preserve them so the learner stream sees a concrete tag.
    if concept_id and concept_id.startswith("concept:") and concept_id not in event["concept_ids"]:
        event["concept_ids"] = sorted(set(event["concept_ids"]) | {concept_id})
    append_learner_event(event)

    pending_path.unlink()

    print(json.dumps(
        {
            "drill_session_id": drill_result.get("drill_session_id"),
            "concept_id": concept_id,
            "total_score": drill_result["total_score"],
            "level": drill_result["level"],
            "dimensions": drill_result["dimensions"],
            "weak_tags": drill_result["weak_tags"],
            "improvement_notes": drill_result.get("improvement_notes", []),
        },
        ensure_ascii=False, indent=2,
    ))
    return 0


def _drill_status(args: argparse.Namespace) -> int:
    from core.paths import learner_drill_pending_path  # type: ignore
    pending_path = learner_drill_pending_path()
    if not pending_path.exists():
        print(json.dumps({"pending": False}, ensure_ascii=False))
        return 0
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    print(json.dumps(
        {
            "pending": True,
            "drill_session_id": pending.get("drill_session_id"),
            "concept_id": pending.get("concept_id"),
            "question": pending.get("question"),
            "ttl_turns": pending.get("ttl_turns"),
            "created_at": pending.get("created_at"),
        },
        ensure_ascii=False, indent=2,
    ))
    return 0


def _drill_cancel(args: argparse.Namespace) -> int:
    from core.paths import learner_drill_pending_path  # type: ignore
    pending_path = learner_drill_pending_path()
    if pending_path.exists():
        pending_path.unlink()
        print(json.dumps({"cancelled": True}, ensure_ascii=False))
    else:
        print(json.dumps({"cancelled": False, "reason": "no pending"}, ensure_ascii=False))
    return 0


def _pick_uncertain_concept_id(profile: dict) -> str | None:
    """첫 번째 uncertain concept을 반환 (drill 미수행 우선)."""
    uncertain = (profile.get("concepts") or {}).get("uncertain") or []
    # drill_score가 None인 것 우선
    for entry in uncertain:
        evidence = entry.get("evidence") or {}
        if evidence.get("last_drill_score") is None:
            return entry.get("concept_id")
    if uncertain:
        return uncertain[0].get("concept_id")
    return None


def _drill_expected_terms(concept: dict) -> list[str]:
    """concept의 aliases + name + korean에서 짧은 영문 토큰 + 한글 키워드 추출.

    scoring._score_accuracy가 token-set과 비교하니 짧고 distinctive한 표현
    위주로 5~8개. 너무 많으면 coverage 임계가 낮아져 4점 받기 쉬워짐.
    """
    candidates: set[str] = set()
    for alias in concept.get("aliases") or []:
        normalized = alias.strip().lower()
        if 2 <= len(normalized) <= 24:
            candidates.add(normalized)
    name = (concept.get("name") or "").strip().lower()
    if name:
        candidates.add(name)
    korean = (concept.get("korean") or "").strip()
    if korean:
        candidates.add(korean)
    return sorted(candidates)[:8]


def cmd_learn_record_code(args: argparse.Namespace) -> int:
    """Record a single `code_attempt` event for a learner code edit.

    Used by the AI session after it edits a file in
    `missions/spring-learning-test/<module>/...`. Designed to be called
    from a wrapper or directly when the diff is already known.
    """
    try:
        from core.concept_catalog import infer_module_from_path, load_catalog  # type: ignore
        from core.learner_memory import (  # type: ignore
            _resolve_learner_id,
            append_learner_event,
            build_code_attempt_event,
        )
        catalog = load_catalog()
        module = args.module or infer_module_from_path(args.file_path)
        event = build_code_attempt_event(
            file_path=args.file_path,
            diff_summary=args.summary or "",
            lines_added=args.lines_added or 0,
            lines_removed=args.lines_removed or 0,
            linked_test=args.linked_test,
            learner_id=_resolve_learner_id(),
            module=module,
            catalog=catalog,
        )
        append_learner_event(event)
        if not getattr(args, "silent", False):
            print(json.dumps({"recorded": True, "event_id": event["event_id"]}, ensure_ascii=False))
        return 0
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"learn-record-code: {exc}\n")
        return 2


def cmd_learner_profile(args: argparse.Namespace) -> int:
    """Subactions for state/learner/* (show / recompute / clear / redact / set / migrate-from-repos)."""
    from core.learner_memory import (  # type: ignore
        clear_learner_state,
        default_profile,
        load_learner_profile,
        recompute_learner_profile,
        redact_substring,
    )
    from core.paths import (  # type: ignore
        learner_history_path,
        learner_profile_path,
        learner_summary_path,
    )

    sub = args.learner_profile_command
    if sub == "show":
        profile = load_learner_profile() or default_profile()
        print(json.dumps(profile, ensure_ascii=False, indent=2))
        return 0

    if sub == "recompute":
        profile = recompute_learner_profile()
        print(json.dumps({"recomputed": True, "total_events": profile.get("total_events", 0)}, ensure_ascii=False))
        return 0

    if sub == "clear":
        if not args.yes:
            sys.stderr.write("This will delete state/learner/. Re-run with --yes to confirm.\n")
            return 2
        result = clear_learner_state()
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if sub == "redact":
        result = redact_substring(args.needle)
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if sub == "set":
        profile = load_learner_profile() or default_profile()
        prefs = profile.setdefault("preferences", {})
        if args.experience_level is not None:
            prefs["experience_level"] = args.experience_level
        if args.preferred_depth is not None:
            prefs["preferred_depth"] = args.preferred_depth
        if args.focus is not None:
            prefs["focus"] = list(args.focus)
        if args.skip_concept is not None:
            prefs["skip_concepts"] = list(args.skip_concept)
        from core.memory import _atomic_write  # type: ignore
        _atomic_write(
            learner_profile_path(),
            json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        )
        print(json.dumps({"updated": True, "preferences": prefs}, ensure_ascii=False))
        return 0

    if sub == "migrate-from-repos":
        from core.learner_memory import migrate_from_repos  # type: ignore
        from core.paths import STATE_DIR  # type: ignore
        result = migrate_from_repos(STATE_DIR / "repos")
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if sub == "suggest":
        from core.concept_catalog import load_catalog  # type: ignore
        from core.learner_memory import suggest_next  # type: ignore
        profile = load_learner_profile() or default_profile()
        suggestions = suggest_next(profile, load_catalog(), max_n=getattr(args, "max", 3))
        if getattr(args, "format", "json") == "text":
            if not suggestions:
                print("(no recommendations yet — keep learning a few more turns)")
            else:
                print("다음 추천:")
                for i, s in enumerate(suggestions, 1):
                    print(f"  {i}. ({s['type']}) {s['value']} — {s['reason']}")
        else:
            print(json.dumps(suggestions, ensure_ascii=False, indent=2))
        return 0

    if sub == "cohort":
        from core.memory import _atomic_write  # type: ignore
        from core.paths import learner_identity_path  # type: ignore
        path = learner_identity_path()
        try:
            identity = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (json.JSONDecodeError, OSError):
            identity = {}
        if args.year is None:
            print(json.dumps(
                {"cohort_year": identity.get("cohort_year")},
                ensure_ascii=False,
            ))
            return 0
        year = int(args.year)
        if not 2000 <= year <= 2100:
            sys.stderr.write(f"cohort year out of range: {year}\n")
            return 2
        identity["cohort_year"] = year
        _atomic_write(path, json.dumps(identity, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"updated": True, "cohort_year": year}, ensure_ascii=False))
        return 0

    sys.stderr.write(f"unknown learner-profile subcommand: {sub}\n")
    return 2


def cmd_reclassify_history(args: argparse.Namespace) -> int:
    """Backfill historical tier / concept_match_mode using the current rules.

    Two transformations apply:

    * ``rag_ask`` events: re-run ``interactive_rag_router.classify`` with
      ``learner_profile=None`` so we apply only the keyword/router rules
      that have shipped since the event was first recorded. Personalized
      promotions (``promoted_by_profile``) are intentionally *not*
      backfilled — they belong to live turns, not history.
    * ``test_result`` events: re-run ``infer_concepts_from_test`` to fill
      in ``concept_match_mode`` (strict / fallback / none) on events that
      pre-date the field. ``concept_ids`` are left alone — recomputing
      them could shrink the set under the more conservative router and
      drop existing mastery signals.
    """
    from core.concept_catalog import infer_concepts_from_test, load_catalog  # type: ignore
    from core.interactive_rag_router import classify  # type: ignore
    from core.learner_memory import (  # type: ignore
        learner_history_path,
        recompute_learner_profile,
    )
    from core.memory import _atomic_write  # type: ignore

    history_path = learner_history_path()
    if not history_path.exists() or history_path.stat().st_size == 0:
        print(json.dumps({"reclassified": False, "reason": "history empty"}, ensure_ascii=False))
        return 0

    catalog = load_catalog()
    raw_lines = history_path.read_text(encoding="utf-8").splitlines()
    rag_changes: list[dict] = []
    test_changes: list[dict] = []
    rewritten: list[str] = []

    for raw in raw_lines:
        if not raw.strip():
            rewritten.append(raw)
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            rewritten.append(raw)
            continue
        et = event.get("event_type")
        if et == "rag_ask":
            prompt = event.get("prompt") or ""
            old_tier = event.get("tier")
            decision = classify(prompt, learner_profile=None)
            new_tier = decision.tier
            if new_tier != old_tier:
                rag_changes.append({
                    "event_id": event.get("event_id"),
                    "prompt": prompt[:60],
                    "old_tier": old_tier,
                    "new_tier": new_tier,
                })
                if not args.dry_run:
                    event["tier"] = new_tier
        elif et == "test_result":
            old_mode = event.get("concept_match_mode")
            ids, source = infer_concepts_from_test(
                event.get("test_class") or "",
                event.get("test_method") or "",
                event.get("module"),
                catalog,
            )
            if old_mode != source:
                test_changes.append({
                    "event_id": event.get("event_id"),
                    "test_class": event.get("test_class"),
                    "test_method": event.get("test_method"),
                    "old_mode": old_mode,
                    "new_mode": source,
                })
                if not args.dry_run:
                    event["concept_match_mode"] = source
        rewritten.append(json.dumps(event, ensure_ascii=False))

    summary = {
        "dry_run": bool(args.dry_run),
        "rag_ask_changes": len(rag_changes),
        "test_result_changes": len(test_changes),
        "rag_ask_diff": rag_changes[:10],
        "test_result_diff": test_changes[:10],
    }

    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if rag_changes or test_changes:
        backup_path = history_path.with_suffix(history_path.suffix + ".bak")
        backup_path.write_text(
            "\n".join(raw_lines) + ("\n" if raw_lines else ""),
            encoding="utf-8",
        )
        _atomic_write(history_path, "\n".join(rewritten) + "\n")
        recompute_learner_profile()
        summary["backup_path"] = str(backup_path)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _orchestrator() -> Orchestrator:
    return Orchestrator()


def cmd_orchestrator_init(_: argparse.Namespace) -> int:
    orchestrator = _orchestrator()
    payload = orchestrator.run_once()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_orchestrator_run_once(args: argparse.Namespace) -> int:
    orchestrator = _orchestrator()
    payload = orchestrator.run_once(
        low_water_mark=args.low_water_mark,
        wave_size=args.wave_size,
        fleet_profile=args.profile,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_orchestrator_run_loop(args: argparse.Namespace) -> int:
    orchestrator = _orchestrator()
    return orchestrator.run_loop(
        interval_seconds=args.interval_seconds,
        low_water_mark=args.low_water_mark,
        wave_size=args.wave_size,
        fleet_profile=args.profile,
    )


def cmd_orchestrator_start(args: argparse.Namespace) -> int:
    orchestrator = _orchestrator()
    payload = orchestrator.start_background(
        cli_script=Path(__file__).resolve(),
        interval_seconds=args.interval_seconds,
        low_water_mark=args.low_water_mark,
        wave_size=args.wave_size,
        fleet_profile=args.profile,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_orchestrator_stop(args: argparse.Namespace) -> int:
    orchestrator = _orchestrator()
    payload = orchestrator.request_stop(force=args.force)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_orchestrator_status(_: argparse.Namespace) -> int:
    orchestrator = _orchestrator()
    print(json.dumps(orchestrator.status(), ensure_ascii=False, indent=2))
    return 0


def cmd_orchestrator_queue(args: argparse.Namespace) -> int:
    orchestrator = _orchestrator()
    payload = orchestrator.list_queue(
        status_filter=args.status,
        lane=args.lane,
        fleet_profile=args.profile,
        limit=args.limit,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_orchestrator_claim(args: argparse.Namespace) -> int:
    orchestrator = _orchestrator()
    payload = orchestrator.claim(
        worker=args.worker,
        limit=args.limit,
        lease_seconds=args.lease_seconds,
        lanes=args.lane,
        fleet_profile=args.profile,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_orchestrator_complete(args: argparse.Namespace) -> int:
    orchestrator = _orchestrator()
    payload = orchestrator.complete(
        item_id=args.item_id,
        worker=args.worker,
        summary=args.summary,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_orchestrator_worker_loop(args: argparse.Namespace) -> int:
    return run_worker_loop(
        worker=args.worker,
        lane=args.lane,
        model=args.model,
        fleet_profile=args.profile,
        idle_seconds=args.idle_seconds,
        lease_seconds=args.lease_seconds,
        timeout_seconds=args.timeout_seconds,
    )


def cmd_orchestrator_supervisor_loop(args: argparse.Namespace) -> int:
    return run_supervisor_loop(
        cli_script=Path(__file__).resolve(),
        model=args.model,
        fleet_profile=args.profile,
        interval_seconds=args.interval_seconds,
    )


def cmd_orchestrator_fleet_start(args: argparse.Namespace) -> int:
    payload = start_fleet_background(
        cli_script=Path(__file__).resolve(),
        model=args.model,
        fleet_profile=args.profile,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_orchestrator_fleet_status(args: argparse.Namespace) -> int:
    print(json.dumps(fleet_status(args.profile), ensure_ascii=False, indent=2))
    return 0


def cmd_orchestrator_fleet_stop(args: argparse.Namespace) -> int:
    print(json.dumps(stop_fleet(force=args.force, fleet_profile=args.profile), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="woowa-learning-hub")
    orchestrator_profile_choices = ["quality", "expansion", "expansion60"]
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = subparsers.add_parser("bootstrap")
    bootstrap_parser.set_defaults(func=cmd_bootstrap)

    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.set_defaults(func=cmd_doctor)

    onboard_parser = subparsers.add_parser("onboard-repo")
    onboard_parser.add_argument("--path", required=True)
    onboard_parser.add_argument("--name")
    onboard_parser.add_argument("--upstream")
    onboard_parser.add_argument("--track")
    onboard_parser.add_argument("--mission")
    onboard_parser.add_argument("--title-contains")
    onboard_parser.set_defaults(func=cmd_onboard_repo)

    list_parser = subparsers.add_parser("list-repos")
    list_parser.set_defaults(func=cmd_list_repos)

    sync_parser = subparsers.add_parser("sync-prs")
    sync_parser.add_argument("--repo", required=True)
    sync_parser.add_argument("--mission")
    sync_parser.add_argument("--track")
    sync_parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    sync_parser.add_argument("--title-contains")
    sync_parser.add_argument("--since")
    sync_parser.add_argument("--limit", type=int)
    sync_parser.set_defaults(func=cmd_sync_prs)

    topic_parser = subparsers.add_parser("topic")
    topic_parser.add_argument("--repo", required=True)
    topic_parser.add_argument("--topic", required=True)
    topic_parser.add_argument("--query", required=True)
    topic_parser.set_defaults(func=cmd_topic)

    reviewer_parser = subparsers.add_parser("reviewer")
    reviewer_parser.add_argument("--repo", required=True)
    reviewer_parser.add_argument("--reviewer", required=True)
    reviewer_parser.set_defaults(func=cmd_reviewer)

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--repo", required=True)
    compare_parser.add_argument("--prs", nargs="+", required=True, type=int)
    compare_parser.set_defaults(func=cmd_compare)

    mission_map_parser = subparsers.add_parser("mission-map")
    mission_map_parser.add_argument("--repo")
    mission_map_parser.add_argument("--path")
    mission_map_parser.set_defaults(func=cmd_mission_map)

    my_pr_parser = subparsers.add_parser("my-pr")
    my_pr_parser.add_argument("--repo", required=True)
    my_pr_parser.add_argument("--pr", type=int)
    my_pr_parser.set_defaults(func=cmd_my_pr)

    coach_parser = subparsers.add_parser("coach")
    coach_parser.add_argument("--repo", required=True)
    coach_parser.add_argument("--prompt", required=True)
    coach_parser.add_argument("--pr", type=int)
    coach_parser.add_argument("--reviewer")
    coach_parser.set_defaults(func=cmd_coach)

    session_start_parser = subparsers.add_parser("session-start")
    session_start_parser.add_argument("--repo", required=True)
    session_start_parser.add_argument("--context", choices=["coach", "my-pr"], default="coach")
    session_start_parser.add_argument("--prompt")
    session_start_parser.add_argument("--pr", type=int)
    session_start_parser.add_argument("--reviewer")
    session_start_parser.set_defaults(func=cmd_session_start)

    assess_parser = subparsers.add_parser("assess-learner-state")
    assess_parser.add_argument("--repo", required=True)
    assess_parser.add_argument("--path")
    assess_parser.add_argument("--prompt")
    assess_parser.add_argument("--upstream")
    assess_parser.set_defaults(func=cmd_assess_learner_state)

    coach_run_parser = subparsers.add_parser("coach-run")
    coach_run_parser.add_argument("--repo")
    coach_run_parser.add_argument("--path")
    coach_run_parser.add_argument("--context", choices=["coach", "my-pr"], default="coach")
    coach_run_parser.add_argument("--prompt")
    coach_run_parser.add_argument("--pr", type=int)
    coach_run_parser.add_argument("--reviewer")
    coach_run_parser.add_argument("--freshness-hours", type=int, default=6)
    coach_run_parser.add_argument("--force-sync", action="store_true")
    coach_run_parser.add_argument("--sync-limit", type=int)
    coach_run_parser.set_defaults(func=cmd_coach_run)

    rag_ask_parser = subparsers.add_parser(
        "rag-ask",
        help="Tier-based RAG router for interactive learning sessions.",
    )
    rag_ask_parser.add_argument("prompt", help="Learner prompt to classify and answer.")
    rag_ask_parser.add_argument("--repo", help="Optional onboarded repo name (for Tier 3 PR coaching).")
    rag_ask_parser.add_argument("--module", help="Optional learning module hint (e.g. spring-core-1).")
    rag_ask_parser.add_argument(
        "--rag-backend",
        choices=("auto", "legacy", "lance", "r3"),
        default=None,
        help="Optional CS RAG backend override. Default follows manifest/env.",
    )
    rag_ask_parser.set_defaults(func=cmd_rag_ask)

    learner_profile_parser = subparsers.add_parser(
        "learner-profile",
        help="Manage state/learner/ (history.jsonl + profile.json).",
    )
    learner_profile_subparsers = learner_profile_parser.add_subparsers(
        dest="learner_profile_command", required=True
    )

    lp_show = learner_profile_subparsers.add_parser("show")
    lp_show.set_defaults(func=cmd_learner_profile)

    lp_recompute = learner_profile_subparsers.add_parser("recompute")
    lp_recompute.set_defaults(func=cmd_learner_profile)

    lp_clear = learner_profile_subparsers.add_parser("clear")
    lp_clear.add_argument("--yes", action="store_true", help="Confirm destructive reset.")
    lp_clear.set_defaults(func=cmd_learner_profile)

    lp_redact = learner_profile_subparsers.add_parser("redact")
    lp_redact.add_argument("needle", help="Substring to remove from history.")
    lp_redact.set_defaults(func=cmd_learner_profile)

    lp_set = learner_profile_subparsers.add_parser("set")
    lp_set.add_argument("--experience-level", choices=["beginner", "intermediate", "advanced"])
    lp_set.add_argument("--preferred-depth", choices=["low", "medium", "high"])
    lp_set.add_argument("--focus", nargs="*")
    lp_set.add_argument("--skip-concept", nargs="*")
    lp_set.set_defaults(func=cmd_learner_profile)

    lp_migrate = learner_profile_subparsers.add_parser("migrate-from-repos")
    lp_migrate.set_defaults(func=cmd_learner_profile)

    lp_suggest = learner_profile_subparsers.add_parser("suggest")
    lp_suggest.add_argument("--max", type=int, default=3)
    lp_suggest.add_argument("--format", choices=["json", "text"], default="json")
    lp_suggest.set_defaults(func=cmd_learner_profile)

    lp_cohort = learner_profile_subparsers.add_parser(
        "cohort",
        help="Show or set the learner's cohort_year (used to tag peer PRs by freshness).",
    )
    lp_cohort.add_argument("year", nargs="?", type=int, help="Cohort year (e.g. 2026). Omit to read.")
    lp_cohort.set_defaults(func=cmd_learner_profile)

    reclassify_parser = subparsers.add_parser(
        "reclassify-history",
        help="Backfill historical rag_ask tier + test_result concept_match_mode using current rules.",
    )
    reclassify_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print proposed changes without rewriting history.jsonl.",
    )
    reclassify_parser.set_defaults(func=cmd_reclassify_history)

    learn_test_parser = subparsers.add_parser(
        "learn-test",
        help="Scan JUnit XML and record test_result events.",
    )
    learn_test_parser.add_argument("--module", help="spring-learning-test module name (e.g. spring-core-1).")
    learn_test_parser.add_argument("--path", help="Explicit path to a build/test-results/test directory.")
    learn_test_parser.add_argument("--no-record", action="store_true")
    learn_test_parser.set_defaults(func=cmd_learn_test)

    learn_drill_parser = subparsers.add_parser(
        "learn-drill",
        help="Standalone drill workflow (offer / answer / status / cancel).",
    )
    learn_drill_subparsers = learn_drill_parser.add_subparsers(
        dest="drill_command", required=True
    )

    drill_offer_p = learn_drill_subparsers.add_parser("offer", help="Pick a concept and create a drill question.")
    drill_offer_p.add_argument("--concept", help="Explicit concept_id (e.g. concept:spring/di).")
    drill_offer_p.add_argument("--force", action="store_true", help="Overwrite an existing pending drill.")
    drill_offer_p.set_defaults(func=cmd_learn_drill)

    drill_answer_p = learn_drill_subparsers.add_parser("answer", help="Score the pending drill answer.")
    drill_answer_p.add_argument("answer", nargs="?", help="Answer text (or pipe via stdin).")
    drill_answer_p.set_defaults(func=cmd_learn_drill)

    drill_status_p = learn_drill_subparsers.add_parser("status", help="Show pending drill or 'no pending'.")
    drill_status_p.set_defaults(func=cmd_learn_drill)

    drill_cancel_p = learn_drill_subparsers.add_parser("cancel", help="Discard pending drill without scoring.")
    drill_cancel_p.set_defaults(func=cmd_learn_drill)

    learn_record_code_parser = subparsers.add_parser(
        "learn-record-code",
        help="Append a single code_attempt event for a learner code edit.",
    )
    learn_record_code_parser.add_argument("--file-path", required=True)
    learn_record_code_parser.add_argument("--summary", default="")
    learn_record_code_parser.add_argument("--lines-added", type=int, default=0)
    learn_record_code_parser.add_argument("--lines-removed", type=int, default=0)
    learn_record_code_parser.add_argument("--linked-test")
    learn_record_code_parser.add_argument("--module")
    learn_record_code_parser.add_argument(
        "--silent",
        action="store_true",
        help="Suppress stdout (event still recorded). Used by AI auto-invocation.",
    )
    learn_record_code_parser.set_defaults(func=cmd_learn_record_code)

    next_action_parser = subparsers.add_parser("next-action")
    next_action_parser.add_argument("--repo", required=True)
    next_action_parser.add_argument("--context", choices=["coach", "my-pr"], default="coach")
    next_action_parser.set_defaults(func=cmd_next_action)

    validate_parser = subparsers.add_parser("validate-state")
    validate_parser.add_argument("--repo", required=True)
    validate_parser.set_defaults(func=cmd_validate_state)

    set_profile_parser = subparsers.add_parser("set-profile")
    set_profile_parser.add_argument("--repo", required=True)
    set_profile_parser.add_argument("--experience-level", choices=["beginner", "intermediate", "advanced"])
    set_profile_parser.add_argument("--preferred-depth", choices=["low", "medium", "high"])
    set_profile_parser.add_argument("--focus", nargs="*")
    set_profile_parser.add_argument("--recent-weaknesses", nargs="*")
    set_profile_parser.set_defaults(func=cmd_set_profile)

    show_profile_parser = subparsers.add_parser("show-profile")
    show_profile_parser.add_argument("--repo", required=True)
    show_profile_parser.set_defaults(func=cmd_show_profile)

    reviewer_profile_parser = subparsers.add_parser("reviewer-profile")
    reviewer_profile_parser.add_argument("--repo", required=True)
    reviewer_profile_parser.add_argument("--reviewer", required=True)
    reviewer_profile_parser.set_defaults(func=cmd_reviewer_profile)

    compose_response_parser = subparsers.add_parser("compose-response")
    compose_response_parser.add_argument("--repo", required=True)
    compose_response_parser.add_argument("--context", choices=["coach", "my-pr"], default="coach")
    compose_response_parser.set_defaults(func=cmd_compose_response)

    archive_status_parser = subparsers.add_parser("archive-status")
    archive_status_parser.add_argument("--repo", required=True)
    archive_status_parser.add_argument("--freshness-hours", type=int, default=6)
    archive_status_parser.set_defaults(func=cmd_archive_status)

    readiness_parser = subparsers.add_parser("repo-readiness")
    readiness_parser.add_argument("--repo")
    readiness_parser.add_argument("--path")
    readiness_parser.add_argument("--freshness-hours", type=int, default=6)
    readiness_parser.set_defaults(func=cmd_repo_readiness)

    registry_audit_parser = subparsers.add_parser("registry-audit")
    registry_audit_parser.add_argument("--freshness-hours", type=int, default=6)
    registry_audit_parser.set_defaults(func=cmd_registry_audit)

    bootstrap_repo_parser = subparsers.add_parser("bootstrap-repo")
    bootstrap_repo_parser.add_argument("--repo", required=True)
    bootstrap_repo_parser.add_argument("--limit", type=int)
    bootstrap_repo_parser.add_argument("--freshness-hours", type=int, default=6)
    bootstrap_repo_parser.set_defaults(func=cmd_bootstrap_repo)

    golden_parser = subparsers.add_parser("golden")
    golden_parser.add_argument("--fixtures")
    golden_parser.add_argument("--stop-on-failure", action="store_true")
    golden_parser.set_defaults(func=cmd_golden)

    orchestrator_parser = subparsers.add_parser("orchestrator")
    orchestrator_subparsers = orchestrator_parser.add_subparsers(dest="orchestrator_command", required=True)

    orchestrator_init_parser = orchestrator_subparsers.add_parser("init")
    orchestrator_init_parser.set_defaults(func=cmd_orchestrator_init)

    orchestrator_run_once_parser = orchestrator_subparsers.add_parser("run-once")
    orchestrator_run_once_parser.add_argument("--low-water-mark", type=int, default=2)
    orchestrator_run_once_parser.add_argument("--wave-size", type=int, default=6)
    orchestrator_run_once_parser.add_argument("--profile", choices=orchestrator_profile_choices, default="quality")
    orchestrator_run_once_parser.set_defaults(func=cmd_orchestrator_run_once)

    orchestrator_run_loop_parser = orchestrator_subparsers.add_parser("run-loop")
    orchestrator_run_loop_parser.add_argument("--interval-seconds", type=int, default=45)
    orchestrator_run_loop_parser.add_argument("--low-water-mark", type=int, default=2)
    orchestrator_run_loop_parser.add_argument("--wave-size", type=int, default=6)
    orchestrator_run_loop_parser.add_argument("--profile", choices=orchestrator_profile_choices, default="quality")
    orchestrator_run_loop_parser.set_defaults(func=cmd_orchestrator_run_loop)

    orchestrator_start_parser = orchestrator_subparsers.add_parser("start")
    orchestrator_start_parser.add_argument("--interval-seconds", type=int, default=45)
    orchestrator_start_parser.add_argument("--low-water-mark", type=int, default=2)
    orchestrator_start_parser.add_argument("--wave-size", type=int, default=6)
    orchestrator_start_parser.add_argument("--profile", choices=orchestrator_profile_choices, default="quality")
    orchestrator_start_parser.set_defaults(func=cmd_orchestrator_start)

    orchestrator_stop_parser = orchestrator_subparsers.add_parser("stop")
    orchestrator_stop_parser.add_argument("--force", action="store_true")
    orchestrator_stop_parser.set_defaults(func=cmd_orchestrator_stop)

    orchestrator_status_parser = orchestrator_subparsers.add_parser("status")
    orchestrator_status_parser.set_defaults(func=cmd_orchestrator_status)

    orchestrator_queue_parser = orchestrator_subparsers.add_parser("queue")
    orchestrator_queue_parser.add_argument("--status", choices=["pending", "leased", "completed", "blocked"])
    orchestrator_queue_parser.add_argument("--lane")
    orchestrator_queue_parser.add_argument("--profile", choices=orchestrator_profile_choices)
    orchestrator_queue_parser.add_argument("--limit", type=int)
    orchestrator_queue_parser.set_defaults(func=cmd_orchestrator_queue)

    orchestrator_claim_parser = orchestrator_subparsers.add_parser("claim")
    orchestrator_claim_parser.add_argument("--worker", required=True)
    orchestrator_claim_parser.add_argument("--limit", type=int, default=1)
    orchestrator_claim_parser.add_argument("--lease-seconds", type=int, default=1800)
    orchestrator_claim_parser.add_argument("--lane", action="append")
    orchestrator_claim_parser.add_argument("--profile", choices=orchestrator_profile_choices, default="quality")
    orchestrator_claim_parser.set_defaults(func=cmd_orchestrator_claim)

    orchestrator_complete_parser = orchestrator_subparsers.add_parser("complete")
    orchestrator_complete_parser.add_argument("--worker", required=True)
    orchestrator_complete_parser.add_argument("--item-id", required=True)
    orchestrator_complete_parser.add_argument("--summary", required=True)
    orchestrator_complete_parser.set_defaults(func=cmd_orchestrator_complete)

    orchestrator_worker_loop_parser = orchestrator_subparsers.add_parser("worker-loop")
    orchestrator_worker_loop_parser.add_argument("--worker", required=True)
    orchestrator_worker_loop_parser.add_argument("--lane", required=True)
    orchestrator_worker_loop_parser.add_argument("--model", default="gpt-5.4")
    orchestrator_worker_loop_parser.add_argument("--profile", choices=orchestrator_profile_choices, default="quality")
    orchestrator_worker_loop_parser.add_argument("--idle-seconds", type=int, default=15)
    orchestrator_worker_loop_parser.add_argument("--lease-seconds", type=int, default=2700)
    orchestrator_worker_loop_parser.add_argument("--timeout-seconds", type=int, default=2700)
    orchestrator_worker_loop_parser.set_defaults(func=cmd_orchestrator_worker_loop)

    orchestrator_supervisor_loop_parser = orchestrator_subparsers.add_parser("supervisor-loop")
    orchestrator_supervisor_loop_parser.add_argument("--model", default="gpt-5.4")
    orchestrator_supervisor_loop_parser.add_argument("--profile", choices=orchestrator_profile_choices, default="quality")
    orchestrator_supervisor_loop_parser.add_argument("--interval-seconds", type=int, default=20)
    orchestrator_supervisor_loop_parser.set_defaults(func=cmd_orchestrator_supervisor_loop)

    orchestrator_fleet_start_parser = orchestrator_subparsers.add_parser("fleet-start")
    orchestrator_fleet_start_parser.add_argument("--model", default="gpt-5.4")
    orchestrator_fleet_start_parser.add_argument("--profile", choices=orchestrator_profile_choices, default="quality")
    orchestrator_fleet_start_parser.set_defaults(func=cmd_orchestrator_fleet_start)

    orchestrator_fleet_status_parser = orchestrator_subparsers.add_parser("fleet-status")
    orchestrator_fleet_status_parser.add_argument("--profile", choices=orchestrator_profile_choices)
    orchestrator_fleet_status_parser.set_defaults(func=cmd_orchestrator_fleet_status)

    orchestrator_fleet_stop_parser = orchestrator_subparsers.add_parser("fleet-stop")
    orchestrator_fleet_stop_parser.add_argument("--force", action="store_true")
    orchestrator_fleet_stop_parser.add_argument("--profile", choices=orchestrator_profile_choices)
    orchestrator_fleet_stop_parser.set_defaults(func=cmd_orchestrator_fleet_stop)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))

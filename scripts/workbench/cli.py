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


def _append_validation(validations: list[dict], schema_name: str, path: Path) -> None:
    if not path.exists():
        validations.append({"schema": schema_name, "path": str(path), "exists": False, "valid": None})
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
    }
    for name, schema in context_map.items():
        targets.append((schema, base / "contexts" / name))

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="woowa-mission-coach")
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

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))

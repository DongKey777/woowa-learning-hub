from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import fcntl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .orchestrator import Orchestrator, _isoformat, _pid_alive, _utc_now
from .paths import ROOT, ensure_orchestrator_layout

DEFAULT_WORKER_IDLE_SECONDS = 15
DEFAULT_WORKER_LEASE_SECONDS = 45 * 60
DEFAULT_TASK_TIMEOUT_SECONDS = 45 * 60
DEFAULT_SUPERVISOR_INTERVAL_SECONDS = 20

WORKER_FLEET: list[dict[str, str]] = [
    {"name": "runtime-database", "lane": "database"},
    {"name": "runtime-security", "lane": "security"},
    {"name": "runtime-network", "lane": "network"},
    {"name": "runtime-system-design", "lane": "system-design"},
    {"name": "runtime-operating-system", "lane": "operating-system"},
    {"name": "runtime-spring", "lane": "spring"},
    {"name": "runtime-design-pattern", "lane": "design-pattern"},
    {"name": "runtime-software-engineering", "lane": "software-engineering"},
    {"name": "runtime-language-java", "lane": "language-java"},
    {"name": "runtime-data-structure", "lane": "data-structure"},
    {"name": "runtime-qa-bridge", "lane": "qa-bridge"},
    {"name": "runtime-qa-anchor", "lane": "qa-anchor"},
    {"name": "runtime-qa-link", "lane": "qa-link"},
    {"name": "runtime-qa-taxonomy", "lane": "qa-taxonomy"},
    {"name": "runtime-qa-retrieval", "lane": "qa-retrieval"},
]

LANE_SCOPE: dict[str, str] = {
    "database": "knowledge/cs/contents/database/** and knowledge/cs/contents/database/README.md",
    "security": "knowledge/cs/contents/security/** and knowledge/cs/contents/security/README.md",
    "network": "knowledge/cs/contents/network/** and knowledge/cs/contents/network/README.md",
    "system-design": "knowledge/cs/contents/system-design/** and knowledge/cs/contents/system-design/README.md",
    "operating-system": "knowledge/cs/contents/operating-system/** and knowledge/cs/contents/operating-system/README.md",
    "spring": "knowledge/cs/contents/spring/** and knowledge/cs/contents/spring/README.md",
    "design-pattern": "knowledge/cs/contents/design-pattern/** and knowledge/cs/contents/design-pattern/README.md",
    "software-engineering": "knowledge/cs/contents/software-engineering/** and knowledge/cs/contents/software-engineering/README.md",
    "language-java": "knowledge/cs/contents/language/java/** and knowledge/cs/contents/language/README.md",
    "data-structure": "knowledge/cs/contents/data-structure/**, knowledge/cs/contents/algorithm/**, and their README files",
    "qa-bridge": "knowledge/cs/**, especially cross-category README and related-doc bridges",
    "qa-anchor": "knowledge/cs/** where retrieval-anchor-keywords are missing or weak",
    "qa-link": "knowledge/cs/** and docs/** for link/reverse-link hygiene",
    "qa-taxonomy": "knowledge/cs/** README/navigator/taxonomy files",
    "qa-retrieval": "tests/fixtures/**, tests/unit/test_cs_rag_*.py, scripts/learning/rag/signal_rules.py",
}


def _worker_root() -> Path:
    return ensure_orchestrator_layout() / "workers"


def _worker_dir(worker: str) -> Path:
    return _worker_root() / worker


def _worker_status_path(worker: str) -> Path:
    return _worker_dir(worker) / "status.json"


def _worker_log_path(worker: str) -> Path:
    return _worker_dir(worker) / "worker.log"


def _worker_output_path(worker: str) -> Path:
    return _worker_dir(worker) / "last-output.json"


def _worker_prompt_path(worker: str) -> Path:
    return _worker_dir(worker) / "last-prompt.txt"


def _worker_pid_path(worker: str) -> Path:
    return _worker_dir(worker) / "worker.pid"


def _worker_schema_path() -> Path:
    return ensure_orchestrator_layout() / "worker-output.schema.json"


def _fleet_status_path() -> Path:
    return ensure_orchestrator_layout() / "fleet-status.json"


def _supervisor_pid_path() -> Path:
    return ensure_orchestrator_layout() / "fleet-supervisor.pid"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _append_log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def _ensure_worker_schema() -> Path:
    path = _worker_schema_path()
    payload = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "changed_files": {"type": "array", "items": {"type": "string"}},
            "next_candidates": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "goal": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["title", "goal", "tags"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["summary", "changed_files", "next_candidates"],
        "additionalProperties": False,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _fleet_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for spec in WORKER_FLEET:
        worker = spec["name"]
        status = _load_json(_worker_status_path(worker), {})
        pid_path = _worker_pid_path(worker)
        pid = None
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text(encoding="utf-8").strip())
            except ValueError:
                pid = None
        summary[worker] = {
            "lane": spec["lane"],
            "pid": pid,
            "alive": bool(pid and _pid_alive(pid)),
            "status": status.get("status"),
            "current_item_id": status.get("current_item_id"),
            "last_heartbeat_at": status.get("last_heartbeat_at"),
            "last_success_at": status.get("last_success_at"),
            "last_error": status.get("last_error"),
        }
    return summary


def _lane_prompt(lane: str) -> str:
    return LANE_SCOPE.get(lane, "knowledge/cs/**")


def _worker_prompt(worker: str, lane: str, item: dict[str, Any]) -> str:
    scope = _lane_prompt(lane)
    tags = ", ".join(item.get("tags", []))
    lowered_text = f"{item['title']} {item['goal']} {' '.join(item.get('tags', []))}".lower()
    beginner_rules = ""
    if any(
        term in lowered_text
        for term in ("beginner", "primer", "basics", "fundamentals", "overview", "입문", "기초", "기본")
    ):
        beginner_rules = """- This item targets beginner/junior readers.
- Prefer one entrypoint primer or bridge over a scattered advanced sweep.
- Start with a simple mental model before terminology.
- Use short comparison tables, concrete examples, and common-confusion bullets when useful.
- Keep advanced failure modes or operator edge cases as links, not as the center of the new doc.
"""
    qa_beginner_rules = ""
    if lane == "qa-bridge":
        qa_beginner_rules = """- Judge bridge quality through a beginner-first lens.
- Verify primers lead to one safe next-step doc before any deep-dive or incident doc.
- Prefer explicit primer -> follow-up -> deep-dive ladders over generic related-doc sprawl.
"""
    elif lane == "qa-anchor":
        qa_beginner_rules = """- Judge anchor quality through a beginner-first lens.
- Add beginner phrasing such as \"처음 배우는데\", \"큰 그림\", \"기초\", \"언제 쓰는지\" when it improves first-hit retrieval.
- Prefer anchors that make primer docs win on introductory prompts before deep dives.
"""
    elif lane == "qa-link":
        qa_beginner_rules = """- Judge link quality through a beginner-first lens.
- Verify each primer has a clear next-step link and an obvious return path to the category README.
- Prefer fixing misleading jumps into advanced docs over broad link cleanup.
"""
    elif lane == "qa-taxonomy":
        qa_beginner_rules = """- Judge taxonomy quality through a beginner-first lens.
- Make `primer`, `survey`, `deep dive`, `playbook`, and `recovery` roles explicit where they could be confused.
- Prefer label clarity and entrypoint safety over catalog completeness.
"""
    elif lane == "qa-retrieval":
        qa_beginner_rules = """- Judge retrieval quality through a beginner-first lens.
- Prefer primer docs over deep dives for introductory prompts.
- When possible, lock the behavior with golden fixtures, signal-rule assertions, or search regressions.
"""
    return f"""You are {worker}, the persistent lane worker for {lane}.

Work only inside:
- {scope}

Task:
- Item ID: {item['item_id']}
- Title: {item['title']}
- Goal: {item['goal']}
- Tags: {tags}

Execution rules:
- Complete exactly one coherent wave for this item.
- Prefer adding or deepening documentation under the assigned lane.
- Strengthen related-doc links and retrieval-anchor-keywords when directly relevant.
- Update the lane README index when you add or materially expand docs.
- Do not revert edits made by others.
- Keep changes scoped; do not drift into unrelated categories.
- If this is a QA lane, make the smallest high-value fixes that reduce the named quality debt.
{beginner_rules}- Final response must be JSON only with:
- Summary should mention the beginner-facing quality improvement when this is a QA lane.
{qa_beginner_rules}- Final response must be JSON only with:
- summary: short worker-completion summary
- changed_files: array of relative file paths you changed
- next_candidates: array with 1 to 3 concise follow-up gaps worth queueing next for the same lane
Always include next_candidates. Prefer concrete next gaps that avoid repeating the exact same work you just finished.
"""


def _run_codex_task(
    worker: str,
    lane: str,
    item: dict[str, Any],
    *,
    model: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    worker_dir = _worker_dir(worker)
    worker_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = _worker_prompt_path(worker)
    output_path = _worker_output_path(worker)
    schema_path = _ensure_worker_schema()
    prompt = _worker_prompt(worker, lane, item)
    prompt_path.write_text(prompt, encoding="utf-8")
    if output_path.exists():
        output_path.unlink()
    started_at = _utc_now()
    result = subprocess.run(
        [
            "codex",
            "exec",
            "--ephemeral",
            "--sandbox",
            "danger-full-access",
            "--dangerously-bypass-approvals-and-sandbox",
            "--model",
            model,
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            prompt,
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    log_text = (
        f"\n=== {item['item_id']} @ {_isoformat(started_at)} ===\n"
        f"PROMPT:\n{prompt}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n"
    )
    _append_log(_worker_log_path(worker), log_text)
    if result.returncode != 0:
        return {
            "ok": False,
            "summary": f"backend_failed: returncode={result.returncode}",
            "stderr": result.stderr[-1200:],
        }
    if not output_path.exists():
        return {"ok": False, "summary": "backend_failed: missing output schema file", "stderr": result.stderr[-1200:]}
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    return {"ok": True, **payload}


def _worker_status(worker: str) -> dict[str, Any]:
    return _load_json(_worker_status_path(worker), {"worker": worker})


def _write_worker_status(worker: str, payload: dict[str, Any]) -> None:
    _write_json(_worker_status_path(worker), payload)


def _update_fleet_status() -> None:
    lock_path = ensure_orchestrator_layout() / ".fleet-status.lock"
    lock_path.touch(exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            _write_json(
                _fleet_status_path(),
                {"updated_at": _isoformat(_utc_now()), "workers": _fleet_summary()},
            )
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def run_worker_loop(
    *,
    worker: str,
    lane: str,
    model: str,
    idle_seconds: int = DEFAULT_WORKER_IDLE_SECONDS,
    lease_seconds: int = DEFAULT_WORKER_LEASE_SECONDS,
    timeout_seconds: int = DEFAULT_TASK_TIMEOUT_SECONDS,
) -> int:
    orchestrator = Orchestrator()
    worker_dir = _worker_dir(worker)
    worker_dir.mkdir(parents=True, exist_ok=True)
    pid = os.getpid()
    _worker_pid_path(worker).write_text(str(pid), encoding="utf-8")
    orchestrator.release_worker_leases(worker, "worker_loop_restart")
    status = _worker_status(worker)
    status.update(
        {
            "worker": worker,
            "lane": lane,
            "pid": pid,
            "status": "running",
            "started_at": status.get("started_at") or _isoformat(_utc_now()),
            "last_heartbeat_at": _isoformat(_utc_now()),
            "current_item_id": None,
            "last_error": None,
        }
    )
    _write_worker_status(worker, status)
    _update_fleet_status()
    try:
        while True:
            now = _utc_now()
            status["last_heartbeat_at"] = _isoformat(now)
            if orchestrator.stop_path.exists():
                status["status"] = "stopping"
                _write_worker_status(worker, status)
                break
            if orchestrator.lane_has_foreign_lease(lane, worker):
                status["status"] = "waiting_foreign_lease"
                _write_worker_status(worker, status)
                _update_fleet_status()
                time.sleep(idle_seconds)
                continue
            claimed = orchestrator.claim(worker=worker, lanes=[lane], limit=1, lease_seconds=lease_seconds)
            if not claimed["claimed"]:
                status["status"] = "idle"
                status["current_item_id"] = None
                _write_worker_status(worker, status)
                _update_fleet_status()
                time.sleep(idle_seconds)
                continue
            item = claimed["claimed"][0]
            status["status"] = "working"
            status["current_item_id"] = item["item_id"]
            status["current_title"] = item["title"]
            _write_worker_status(worker, status)
            _update_fleet_status()
            task = _run_codex_task(worker, lane, item, model=model, timeout_seconds=timeout_seconds)
            if task["ok"]:
                summary = task.get("summary") or f"completed {item['item_id']}"
                orchestrator.complete(item["item_id"], worker, summary)
                next_candidates = task.get("next_candidates") or []
                if isinstance(next_candidates, list) and next_candidates:
                    orchestrator.enqueue_candidates(
                        lane,
                        [candidate for candidate in next_candidates if isinstance(candidate, dict)],
                        source=f"worker-suggestion:{worker}",
                    )
                status["last_success_at"] = _isoformat(_utc_now())
                status["last_summary"] = summary
                status["last_changed_files"] = task.get("changed_files", [])
                status["last_next_candidates"] = next_candidates
                status["last_error"] = None
            else:
                error_summary = task.get("summary") or "worker backend failed"
                orchestrator.requeue(item["item_id"], worker, error_summary)
                status["last_error"] = error_summary
                status["last_error_detail"] = task.get("stderr")
            status["current_item_id"] = None
            status["status"] = "running"
            _write_worker_status(worker, status)
            _update_fleet_status()
            time.sleep(1)
    finally:
        final_status = _worker_status(worker)
        final_status["status"] = "stopped"
        final_status["current_item_id"] = None
        final_status["last_heartbeat_at"] = _isoformat(_utc_now())
        _write_worker_status(worker, final_status)
        if _worker_pid_path(worker).exists():
            _worker_pid_path(worker).unlink()
        _update_fleet_status()
    return 0


def _start_worker_process(cli_script: Path, worker: str, lane: str, model: str) -> int:
    worker_dir = _worker_dir(worker)
    worker_dir.mkdir(parents=True, exist_ok=True)
    with _worker_log_path(worker).open("a", encoding="utf-8") as handle:
        proc = subprocess.Popen(
            [
                sys.executable,
                str(cli_script),
                "orchestrator",
                "worker-loop",
                "--worker",
                worker,
                "--lane",
                lane,
                "--model",
                model,
            ],
            cwd=str(ROOT),
            stdout=handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    _worker_pid_path(worker).write_text(str(proc.pid), encoding="utf-8")
    status = _worker_status(worker)
    status.update(
        {
            "worker": worker,
            "lane": lane,
            "pid": proc.pid,
            "status": "starting",
            "last_heartbeat_at": _isoformat(_utc_now()),
            "current_item_id": None,
        }
    )
    _write_worker_status(worker, status)
    return proc.pid


def run_supervisor_loop(
    *,
    cli_script: Path,
    model: str,
    interval_seconds: int = DEFAULT_SUPERVISOR_INTERVAL_SECONDS,
) -> int:
    orchestrator = Orchestrator()
    supervisor_pid = os.getpid()
    _supervisor_pid_path().write_text(str(supervisor_pid), encoding="utf-8")
    orchestrator.start_background(cli_script=cli_script)
    try:
        while True:
            if orchestrator.stop_path.exists():
                break
            for spec in WORKER_FLEET:
                worker = spec["name"]
                lane = spec["lane"]
                pid_path = _worker_pid_path(worker)
                pid = None
                if pid_path.exists():
                    try:
                        pid = int(pid_path.read_text(encoding="utf-8").strip())
                    except ValueError:
                        pid = None
                if not pid or not _pid_alive(pid):
                    _start_worker_process(cli_script, worker, lane, model)
            _update_fleet_status()
            time.sleep(interval_seconds)
    finally:
        if _supervisor_pid_path().exists():
            _supervisor_pid_path().unlink()
        _update_fleet_status()
    return 0


def start_fleet_background(*, cli_script: Path, model: str) -> dict[str, Any]:
    orchestrator = Orchestrator()
    supervisor_pid = None
    if _supervisor_pid_path().exists():
        try:
            supervisor_pid = int(_supervisor_pid_path().read_text(encoding="utf-8").strip())
        except ValueError:
            supervisor_pid = None
    if supervisor_pid and _pid_alive(supervisor_pid):
        return {"already_running": True, "supervisor_pid": supervisor_pid, "workers": _fleet_summary()}
    ensure_orchestrator_layout()
    with (ensure_orchestrator_layout() / "fleet-supervisor.log").open("a", encoding="utf-8") as handle:
        proc = subprocess.Popen(
            [
                sys.executable,
                str(cli_script),
                "orchestrator",
                "supervisor-loop",
                "--model",
                model,
            ],
            cwd=str(ROOT),
            stdout=handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    _supervisor_pid_path().write_text(str(proc.pid), encoding="utf-8")
    return {"already_running": False, "supervisor_pid": proc.pid, "workers": _fleet_summary()}


def fleet_status() -> dict[str, Any]:
    supervisor_pid = None
    if _supervisor_pid_path().exists():
        try:
            supervisor_pid = int(_supervisor_pid_path().read_text(encoding="utf-8").strip())
        except ValueError:
            supervisor_pid = None
    return {
        "supervisor": {"pid": supervisor_pid, "alive": bool(supervisor_pid and _pid_alive(supervisor_pid))},
        "workers": _fleet_summary(),
    }


def stop_fleet(*, force: bool = False) -> dict[str, Any]:
    orchestrator = Orchestrator()
    orchestrator.request_stop(force=force)
    for spec in WORKER_FLEET:
        pid_path = _worker_pid_path(spec["name"])
        if not pid_path.exists():
            continue
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
        except ValueError:
            continue
        if _pid_alive(pid):
            os.kill(pid, signal.SIGTERM if force else signal.SIGTERM)
    supervisor_pid = None
    if _supervisor_pid_path().exists():
        try:
            supervisor_pid = int(_supervisor_pid_path().read_text(encoding="utf-8").strip())
        except ValueError:
            supervisor_pid = None
    if supervisor_pid and _pid_alive(supervisor_pid):
        os.kill(supervisor_pid, signal.SIGTERM if force else signal.SIGTERM)
    return fleet_status()

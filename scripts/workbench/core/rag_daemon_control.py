"""Control client for the local long-lived RAG runtime daemon."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .paths import ROOT, STATE_DIR, ensure_global_layout

RAG_DAEMON_STATE = STATE_DIR / "rag-daemon.json"
RAG_DAEMON_LOG = STATE_DIR / "rag-daemon.log"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 0


def _python_executable() -> str:
    env_python = os.environ.get("PYTHON")
    if env_python:
        return env_python
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _read_state() -> dict[str, Any] | None:
    try:
        payload = json.loads(RAG_DAEMON_STATE.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _url(state: dict[str, Any], path: str) -> str:
    host = str(state.get("host") or DEFAULT_HOST)
    port = int(state.get("port") or 0)
    return f"http://{host}:{port}{path}"


def _request_json(
    state: dict[str, Any],
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout_s: float = 1.0,
) -> dict[str, Any]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(_url(state, path), data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
    parsed = json.loads(body or "{}")
    if not isinstance(parsed, dict):
        raise RuntimeError("rag daemon response is not a JSON object")
    return parsed


def _health(state: dict[str, Any], *, timeout_s: float = 0.5) -> dict[str, Any] | None:
    try:
        return _request_json(state, "/health", timeout_s=timeout_s)
    except Exception:
        return None


def status_daemon() -> dict[str, Any]:
    state = _read_state()
    if state is None:
        return {"status": "stopped", "state_path": str(RAG_DAEMON_STATE)}
    health = _health(state)
    if health is None:
        return {
            "status": "stale",
            "state": state,
            "state_path": str(RAG_DAEMON_STATE),
            "log_path": str(RAG_DAEMON_LOG),
        }
    return {
        "status": "running",
        "state": state,
        "health": health,
        "state_path": str(RAG_DAEMON_STATE),
        "log_path": str(RAG_DAEMON_LOG),
    }


def start_daemon(*, timeout_s: float = 10.0) -> dict[str, Any]:
    status = status_daemon()
    if status["status"] == "running":
        return status

    ensure_global_layout()
    RAG_DAEMON_STATE.unlink(missing_ok=True)
    RAG_DAEMON_LOG.parent.mkdir(parents=True, exist_ok=True)
    log_handle = RAG_DAEMON_LOG.open("a", encoding="utf-8")
    cmd = [
        _python_executable(),
        str(ROOT / "scripts" / "workbench" / "rag_daemon.py"),
        "serve",
        "--host",
        DEFAULT_HOST,
        "--port",
        str(DEFAULT_PORT),
        "--state-path",
        str(RAG_DAEMON_STATE),
    ]
    process = subprocess.Popen(
        cmd,
        cwd=ROOT,
        stdout=log_handle,
        stderr=log_handle,
        start_new_session=True,
    )
    log_handle.close()
    deadline = time.time() + timeout_s
    last_state: dict[str, Any] | None = None
    while time.time() < deadline:
        state = _read_state()
        if state is not None:
            last_state = state
            health = _health(state)
            if health is not None:
                return {
                    "status": "running",
                    "state": state,
                    "health": health,
                    "state_path": str(RAG_DAEMON_STATE),
                    "log_path": str(RAG_DAEMON_LOG),
                    "started_pid": process.pid,
                }
        if process.poll() is not None:
            break
        time.sleep(0.1)
    return {
        "status": "error",
        "state": last_state,
        "state_path": str(RAG_DAEMON_STATE),
        "log_path": str(RAG_DAEMON_LOG),
        "started_pid": process.pid,
        "returncode": process.poll(),
    }


def ensure_daemon(*, timeout_s: float = 10.0) -> dict[str, Any]:
    status = status_daemon()
    if status["status"] == "running":
        return status
    return start_daemon(timeout_s=timeout_s)


def stop_daemon(*, timeout_s: float = 5.0) -> dict[str, Any]:
    state = _read_state()
    if state is None:
        return {"status": "stopped", "state_path": str(RAG_DAEMON_STATE)}

    try:
        _request_json(state, "/shutdown", payload={}, timeout_s=1.0)
    except Exception:
        pid = state.get("pid")
        if isinstance(pid, int):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _health(state) is None:
            RAG_DAEMON_STATE.unlink(missing_ok=True)
            return {"status": "stopped", "state": state}
        time.sleep(0.1)
    return {
        "status": "error",
        "reason": "daemon did not stop before timeout",
        "state": state,
    }


def request_rag_ask(payload: dict[str, Any], *, timeout_s: float = 120.0) -> dict[str, Any]:
    state = _read_state()
    if state is None or _health(state) is None:
        status = ensure_daemon()
        state = status.get("state")
    if not isinstance(state, dict):
        raise RuntimeError("rag daemon is not running")
    try:
        return _request_json(state, "/rag-ask", payload=payload, timeout_s=timeout_s)
    except urllib.error.URLError:
        status = start_daemon()
        state = status.get("state")
        if not isinstance(state, dict):
            raise
        return _request_json(state, "/rag-ask", payload=payload, timeout_s=timeout_s)

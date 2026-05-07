from __future__ import annotations

import argparse
from types import SimpleNamespace

from scripts.workbench import rag_daemon
from scripts.workbench.core import rag_daemon_control


def test_rag_daemon_namespace_from_payload_preserves_runtime_fields():
    ns = rag_daemon.namespace_from_payload(
        {
            "prompt": "RAG로 깊게 latency가 뭐야?",
            "repo": "spring-roomescape",
            "module": "network",
            "rag_backend": "r3",
        }
    )

    assert ns.prompt == "RAG로 깊게 latency가 뭐야?"
    assert ns.repo == "spring-roomescape"
    assert ns.module == "network"
    assert ns.rag_backend == "r3"
    assert ns.via_daemon is False
    # default — caller did not supply a reformulation
    assert ns.reformulated_query is None


def test_rag_daemon_namespace_propagates_reformulated_query():
    """The daemon HTTP path must forward the reformulated_query payload
    field so query side reformulation (Pilot baseline +5pp lever) keeps
    working when --via-daemon is in effect.
    """
    ns = rag_daemon.namespace_from_payload(
        {
            "prompt": "큰 그림이 궁금해",
            "reformulated_query": "Spring Bean 라이프사이클 큰 그림",
        }
    )

    assert ns.prompt == "큰 그림이 궁금해"
    assert ns.reformulated_query == "Spring Bean 라이프사이클 큰 그림"


def test_rag_daemon_namespace_treats_blank_reformulation_as_none():
    """Empty / falsy reformulated_query payloads should not surface as
    a search() argument. Otherwise an empty string would silently
    replace the raw prompt in the dense + reranker path.
    """
    for blank in ("", None, False):
        ns = rag_daemon.namespace_from_payload(
            {"prompt": "Spring Bean이 뭐야?", "reformulated_query": blank}
        )
        assert ns.reformulated_query is None


def test_rag_daemon_handler_delegates_to_rag_ask_builder(monkeypatch):
    captured = {}

    def fake_build(args: argparse.Namespace) -> dict:
        captured["args"] = args
        return {"decision": {"tier": 2}, "hits": {"meta": {"backend": "r3"}}}

    monkeypatch.setattr(rag_daemon.workbench_cli, "build_rag_ask_output", fake_build)

    out = rag_daemon.handle_rag_ask_payload(
        {"prompt": "RAG로 깊게 latency가 뭐야?", "rag_backend": "r3"}
    )

    assert out["decision"]["tier"] == 2
    assert captured["args"].prompt == "RAG로 깊게 latency가 뭐야?"
    assert captured["args"].rag_backend == "r3"


def test_rag_daemon_handler_rejects_empty_prompt():
    try:
        rag_daemon.handle_rag_ask_payload({"prompt": "  "})
    except ValueError as exc:
        assert "prompt is required" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_local_daemon_server_bind_does_not_require_reverse_dns(monkeypatch):
    def fail_getfqdn(host=None):
        raise AssertionError(f"reverse DNS should not run for {host}")

    monkeypatch.setattr("socket.getfqdn", fail_getfqdn)
    server = rag_daemon.LocalThreadingHTTPServer(
        ("127.0.0.1", 0),
        rag_daemon.RagDaemonHandler,
    )
    try:
        assert server.server_name == "127.0.0.1"
        assert isinstance(server.server_port, int)
    finally:
        server.server_close()


def test_rag_daemon_control_status_reports_stopped_without_state(monkeypatch, tmp_path):
    state_path = tmp_path / "rag-daemon.json"
    monkeypatch.setattr(rag_daemon_control, "RAG_DAEMON_STATE", state_path)

    status = rag_daemon_control.status_daemon()

    assert status["status"] == "stopped"
    assert status["state_path"] == str(state_path)


def test_rag_daemon_control_ensure_reuses_running_daemon(monkeypatch):
    state = {"host": "127.0.0.1", "port": 9191}
    monkeypatch.setattr(rag_daemon_control, "_read_state", lambda: state)
    monkeypatch.setattr(
        rag_daemon_control,
        "_health",
        lambda current_state, timeout_s=0.5: {"ok": True, "pid": 123},
    )
    monkeypatch.setattr(
        rag_daemon_control,
        "_runtime_fingerprint_matches",
        lambda status: True,
    )
    monkeypatch.setattr(
        rag_daemon_control,
        "start_daemon",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not start")),
    )

    status = rag_daemon_control.ensure_daemon()

    assert status["status"] == "running"
    assert status["state"] is state
    assert status["health"]["pid"] == 123


def test_rag_daemon_control_ensure_restarts_stale_runtime(monkeypatch):
    calls: list[str] = []
    running = {
        "status": "running",
        "state": {"host": "127.0.0.1", "port": 9191},
        "health": {"ok": True, "pid": 123},
    }
    restarted = {
        "status": "running",
        "state": {"host": "127.0.0.1", "port": 9292},
        "health": {"ok": True, "pid": 456},
    }
    monkeypatch.setattr(rag_daemon_control, "status_daemon", lambda: running)
    monkeypatch.setattr(
        rag_daemon_control,
        "_runtime_fingerprint_matches",
        lambda status: False,
    )
    monkeypatch.setattr(
        rag_daemon_control,
        "stop_daemon",
        lambda **kwargs: calls.append("stop") or {"status": "stopped"},
    )
    monkeypatch.setattr(
        rag_daemon_control,
        "start_daemon",
        lambda **kwargs: calls.append("start") or restarted,
    )

    status = rag_daemon_control.ensure_daemon()

    assert calls == ["stop", "start"]
    assert status["health"]["pid"] == 456


def test_rag_daemon_write_state_persists_runtime_fingerprint(tmp_path):
    state_path = tmp_path / "rag-daemon.json"
    fingerprint = {
        "schema_version": 1,
        "git_head": "abc123",
        "source_hash": "def456",
        "file_count": 7,
    }

    rag_daemon.write_state(
        state_path,
        host="127.0.0.1",
        port=9191,
        started_at=123.0,
        runtime_fingerprint=fingerprint,
    )

    payload = __import__("json").loads(state_path.read_text(encoding="utf-8"))
    assert payload["runtime_fingerprint"] == fingerprint

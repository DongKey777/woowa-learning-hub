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
        "start_daemon",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not start")),
    )

    status = rag_daemon_control.ensure_daemon()

    assert status["status"] == "running"
    assert status["state"] is state
    assert status["health"]["pid"] == 123

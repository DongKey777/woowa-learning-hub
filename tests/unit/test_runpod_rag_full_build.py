"""Tests for the RunPod harness — dry-run path (plan v5 task v5-5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.remote import runpod_rag_full_build as H


# ---------------------------------------------------------------------------
# MockRunPodClient — recording behaviour
# ---------------------------------------------------------------------------

def test_mock_client_records_create_and_terminate():
    client = H.MockRunPodClient()
    spec = H.PodSpec(
        name="test-pod", gpu_type="RTX A5000", gpu_cloud="community",
        image="img", container_disk_gb=20, ports="22/tcp",
    )
    pod = client.create_pod(spec, ssh_public_key="ssh-ed25519 fake")
    assert pod.pod_id.startswith("mock-pod-")
    assert pod.gpu_type == "RTX A5000"

    client.terminate_pod(pod.pod_id)
    ops = [c["op"] for c in client.calls]
    assert ops == ["create_pod", "terminate_pod"]


def test_mock_client_estimate_hourly_rate():
    client = H.MockRunPodClient()
    assert client.estimate_hourly_rate("RTX A5000", "community") == 0.16
    assert client.estimate_hourly_rate("RTX A5000", "secure") == 0.29
    assert client.estimate_hourly_rate("RTX A6000", "community") == 0.49
    assert client.estimate_hourly_rate("A100 80GB", "community") == 1.50
    # Unknown defaults to 0.50
    assert client.estimate_hourly_rate("Unknown GPU", "community") == 0.50


def test_mock_client_ssh_key_round_trip():
    client = H.MockRunPodClient()
    key_id = client.add_ssh_key("ssh-ed25519 fake", label="test-label")
    assert key_id.startswith("mock-key-")
    client.remove_ssh_key(key_id)
    ops = [c["op"] for c in client.calls]
    assert ops == ["add_ssh_key", "remove_ssh_key"]


# ---------------------------------------------------------------------------
# build_run_id
# ---------------------------------------------------------------------------

def test_build_run_id_includes_phase_sha_timestamp():
    git_state = {"commit_sha_short": "abc1234"}
    rid = H.build_run_id("r1", git_state)
    assert rid.startswith("r1-abc1234-")
    # Has timestamp
    parts = rid.split("-")
    assert len(parts) >= 3


def test_build_run_id_handles_missing_git():
    git_state = {"commit_sha_short": ""}
    rid = H.build_run_id("r0", git_state)
    # Falls back to a placeholder rather than crashing
    assert rid.startswith("r0-")


# ---------------------------------------------------------------------------
# Cost ledger append
# ---------------------------------------------------------------------------

def test_append_cost_ledger_creates_file_and_appends(tmp_path):
    ledger = tmp_path / "ledger.json"
    from datetime import datetime, timezone

    H.append_cost_ledger(
        ledger,
        run_id="r0-test-1",
        gpu="RTX A5000",
        started_at=datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc),
        ended_at=datetime(2026, 5, 1, 8, 30, tzinfo=timezone.utc),
        estimated_cost_usd=0.08,
        pod_id="pod-x",
        deleted=True,
    )
    H.append_cost_ledger(
        ledger,
        run_id="r1-test-2",
        gpu="RTX A5000",
        started_at=datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc),
        ended_at=datetime(2026, 5, 1, 10, 30, tzinfo=timezone.utc),
        estimated_cost_usd=0.40,
        pod_id="pod-y",
        deleted=True,
    )

    data = json.loads(ledger.read_text())
    assert len(data) == 2
    assert data[0]["run_id"] == "r0-test-1"
    assert data[1]["run_id"] == "r1-test-2"
    assert all(r["deleted"] for r in data)


def test_append_cost_ledger_handles_corrupt_existing(tmp_path):
    ledger = tmp_path / "ledger.json"
    ledger.write_text("garbage", encoding="utf-8")
    from datetime import datetime, timezone
    H.append_cost_ledger(
        ledger,
        run_id="r0", gpu="x",
        started_at=datetime.now(timezone.utc),
        ended_at=datetime.now(timezone.utc),
        estimated_cost_usd=0,
        pod_id=None,
        deleted=True,
    )
    data = json.loads(ledger.read_text())
    assert len(data) == 1


# ---------------------------------------------------------------------------
# Build remote commands
# ---------------------------------------------------------------------------

def test_remote_commands_for_r0_skip_warm_and_eval():
    """R0 is FTS-only — no model warm, no eval step."""
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)
    cmds = h._build_remote_commands(
        commit_sha="abc1234",
        modalities=("fts",),
        run_id="r0-test",
        r_phase="r0",
    )
    full = "\n".join(cmds)
    assert "git clone" in full
    assert "git checkout abc1234" in full
    # No bge-m3 model warm
    assert "BGEM3FlagModel" not in full
    # No eval step in r0
    assert "cli_rag_eval" not in full
    # But package step IS present
    assert "package_rag_artifact" in full


def test_remote_commands_for_r1_includes_warm_and_eval():
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)
    cmds = h._build_remote_commands(
        commit_sha="abc1234",
        modalities=("fts", "dense"),
        run_id="r1-test",
        r_phase="r1",
    )
    full = "\n".join(cmds)
    # Model warm present for dense
    assert "BGEM3FlagModel" in full
    # Eval present for r1
    assert "cli_rag_eval" in full
    assert "--ablate" in full
    assert "--ablation-split holdout" in full
    # Repeatable flag (NOT semicolon)
    assert "--ablation-modalities fts" in full
    assert "--ablation-modalities fts,dense" in full


def test_remote_commands_modalities_passed_to_build():
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)
    cmds = h._build_remote_commands(
        commit_sha="x", modalities=("fts", "dense", "sparse"),
        run_id="r2", r_phase="r2",
    )
    full = "\n".join(cmds)
    assert "--modalities fts,dense,sparse" in full


# ---------------------------------------------------------------------------
# Lifecycle — full dry-run run() invocation
# ---------------------------------------------------------------------------

def _make_config(tmp_path: Path, r_phase: str = "r0") -> H.BuildConfig:
    return H.BuildConfig(
        r_phase=r_phase,
        modalities=("fts",) if r_phase == "r0" else ("fts", "dense"),
        gpu_type="RTX A5000",
        gpu_cloud="community",
        max_cost_usd=10.0,
        max_duration_min=30,
        repo_root=tmp_path,
        ledger_path=tmp_path / "ledger.json",
    )


def test_run_dry_run_creates_and_terminates_pod(tmp_path):
    """Full lifecycle in dry-run: pod created, then terminated."""
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)
    config = _make_config(tmp_path, r_phase="r0")
    result = h.run(config)

    assert result.r_phase == "r0"
    assert result.pod_terminated is True
    assert result.error is None

    ops = [c["op"] for c in client.calls]
    # Order: estimate → ssh key → pod create → ... → pod terminate → ssh key remove
    assert "estimate_hourly_rate" in ops
    assert "add_ssh_key" in ops
    assert "create_pod" in ops
    assert "terminate_pod" in ops
    assert "remove_ssh_key" in ops
    # Terminate must come after create
    assert ops.index("terminate_pod") > ops.index("create_pod")


def test_run_dry_run_writes_cost_ledger(tmp_path):
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)
    config = _make_config(tmp_path, r_phase="r0")
    h.run(config)

    ledger = json.loads((tmp_path / "ledger.json").read_text())
    assert len(ledger) == 1
    entry = ledger[0]
    assert entry["pod_id"]
    assert entry["deleted"] is True
    assert entry["gpu"] == "RTX A5000"
    assert entry["estimated_cost_usd"] >= 0


def test_run_aborts_when_cost_exceeds_max(tmp_path):
    """Defensive: A100 community + 30min = ~$0.75 > $0.50 max-cost → abort."""
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)
    config = H.BuildConfig(
        r_phase="r3",
        modalities=("fts", "dense", "sparse", "colbert"),
        gpu_type="A100 80GB",
        gpu_cloud="community",
        max_cost_usd=0.50,    # less than 1.50/hr × 0.5hr = 0.75
        max_duration_min=30,
        repo_root=tmp_path,
        ledger_path=tmp_path / "ledger.json",
    )
    result = h.run(config)
    assert result.error is not None
    assert "exceeds --max-cost" in result.error
    # Pod should still be terminated (even though never created — cleanup is no-op)
    assert result.pod_terminated is True


def test_run_pod_terminated_even_on_remote_step_failure(tmp_path, monkeypatch):
    """If step_5_to_11 raises, finally-block cleanup must still terminate Pod."""
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)

    # Force step_5_to_11 to fail after pod creation
    def _raise(*a, **kw):
        raise RuntimeError("simulated remote failure")
    monkeypatch.setattr(h, "step_5_to_11_remote_build", _raise)

    config = _make_config(tmp_path, r_phase="r0")
    result = h.run(config)

    assert result.error is not None
    assert "simulated remote failure" in result.error
    assert result.pod_terminated is True
    # Verify terminate was called
    ops = [c["op"] for c in client.calls]
    assert "terminate_pod" in ops


def test_resolve_defaults_picks_r_phase_appropriate_gpu():
    args = type("A", (), {
        "r_phase": "r3", "modalities": None, "gpu_type": None,
        "gpu_cloud": None, "max_cost": 10.0, "max_duration": 180,
        "repo_root": Path.cwd(), "ledger_path": Path("ledger.json"),
    })()
    config = H.resolve_defaults(args)
    assert config.gpu_type == "RTX A6000"     # R3 default
    assert config.gpu_cloud == "community"
    assert "colbert" in config.modalities


def test_resolve_defaults_explicit_modalities_override():
    args = type("A", (), {
        "r_phase": "r1", "modalities": "fts,dense,sparse",
        "gpu_type": None, "gpu_cloud": None,
        "max_cost": 10.0, "max_duration": 60,
        "repo_root": Path.cwd(), "ledger_path": Path("ledger.json"),
    })()
    config = H.resolve_defaults(args)
    assert config.modalities == ("fts", "dense", "sparse")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_dry_run_reports_success(tmp_path, capsys):
    """End-to-end CLI smoke — dry-run R0 must succeed."""
    rc = H.main([
        "--r-phase", "r0",
        "--dry-run",
        "--repo-root", str(tmp_path),
        "--ledger-path", str(tmp_path / "ledger.json"),
        "--max-cost", "5.0",
        "--max-duration", "30",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["dry_run"] is True
    assert payload["pod_terminated"] is True
    assert payload["error"] is None


def test_cli_real_mode_blocked_pending_v5_6(tmp_path, capsys):
    """Real mode must error out cleanly until v5-6 lands."""
    rc = H.main([
        "--r-phase", "r0",
        "--repo-root", str(tmp_path),
        "--ledger-path", str(tmp_path / "ledger.json"),
    ])
    assert rc == 2

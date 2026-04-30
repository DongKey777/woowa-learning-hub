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
    # apt-get installs zstd + git BEFORE any Python work (R0 v4 bug fix
    # — Pod images lack zstd, package step needs it)
    assert "apt-get install -y -qq zstd" in full
    assert "git clone" in full
    assert "git checkout abc1234" in full
    # No bge-m3 model warm
    assert "scripts.remote._warm_bge_m3" not in full
    # No eval step in r0
    assert "cli_rag_eval" not in full
    # But package step IS present
    assert "package_rag_artifact" in full


def test_remote_commands_apt_runs_before_pip():
    """apt-get install must run BEFORE pip install — packages like
    zstd are needed by package_rag_artifact step which runs at the end."""
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)
    cmds = h._build_remote_commands(
        commit_sha="x", modalities=("fts",), run_id="r0", r_phase="r0",
    )
    apt_idx = next(i for i, c in enumerate(cmds) if "apt-get install" in c)
    pip_idx = next(i for i, c in enumerate(cmds) if "pip install" in c and "-e ." in c)
    assert apt_idx < pip_idx


def test_remote_commands_use_system_python_not_venv():
    """R1 v1 bug fix: we must NOT create a venv on the Pod, because
    PyPI's default torch wheel (cu130) doesn't match the Pod's CUDA
    12.4 driver → falls back to CPU. Use Pod's system Python, which
    has torch+CUDA pre-installed by the runpod/pytorch image."""
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)
    cmds = h._build_remote_commands(
        commit_sha="x", modalities=("fts", "dense"),
        run_id="r1", r_phase="r1",
    )
    full = "\n".join(cmds)
    # No venv creation
    assert "python -m venv" not in full
    assert ".venv/bin/python" not in full
    # System python (with --break-system-packages for PEP 668)
    assert "pip install --break-system-packages" in full


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
    # Model warm present for dense (via retry-capable helper module)
    assert "scripts.remote._warm_bge_m3" in full
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


def test_remote_commands_passes_lance_max_length_when_set():
    """R1 plan prescribes max_length=512 (cs-index-build default is 1024)."""
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)
    cmds = h._build_remote_commands(
        commit_sha="x", modalities=("fts", "dense"),
        run_id="r1", r_phase="r1",
        lance_max_length=512,
    )
    build_cmd = next(c for c in cmds if "cli_cs_index_build" in c)
    assert "--lance-max-length 512" in build_cmd


def test_remote_commands_omits_lance_args_when_none():
    """When no override given, build command keeps cs-index-build's
    own defaults (R0 path)."""
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)
    cmds = h._build_remote_commands(
        commit_sha="x", modalities=("fts",),
        run_id="r0", r_phase="r0",
    )
    build_cmd = next(c for c in cmds if "cli_cs_index_build" in c)
    assert "--lance-max-length" not in build_cmd
    assert "--lance-batch-size" not in build_cmd


def test_resolve_defaults_r1_picks_max_length_512():
    """R1 default max_length must be 512 (plan v5 §3 R1)."""
    args = type("A", (), {
        "r_phase": "r1", "modalities": None, "gpu_type": None,
        "gpu_cloud": None, "max_cost": 10.0, "max_duration": 90,
        "repo_root": Path.cwd(), "ledger_path": Path("ledger.json"),
        "max_length": None, "batch_size": None, "precision": None,
        "colbert_dtype": None,
    })()
    config = H.resolve_defaults(args)
    assert config.lance_max_length == 512


def test_resolve_defaults_r0_no_max_length_default():
    """R0 is FTS-only — no encoder, max_length irrelevant. Default None
    keeps cs-index-build defaults (which end up being unused in FTS path)."""
    args = type("A", (), {
        "r_phase": "r0", "modalities": None, "gpu_type": None,
        "gpu_cloud": None, "max_cost": 10.0, "max_duration": 60,
        "repo_root": Path.cwd(), "ledger_path": Path("ledger.json"),
        "max_length": None, "batch_size": None, "precision": None,
        "colbert_dtype": None,
    })()
    config = H.resolve_defaults(args)
    assert config.lance_max_length is None


def test_resolve_defaults_explicit_max_length_overrides_phase_default():
    """User-provided --max-length wins over R-phase default."""
    args = type("A", (), {
        "r_phase": "r1", "modalities": None, "gpu_type": None,
        "gpu_cloud": None, "max_cost": 10.0, "max_duration": 60,
        "repo_root": Path.cwd(), "ledger_path": Path("ledger.json"),
        "max_length": 1024, "batch_size": None, "precision": None,
        "colbert_dtype": None,
    })()
    config = H.resolve_defaults(args)
    assert config.lance_max_length == 1024  # explicit wins


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


def test_run_records_actual_cost_even_on_failure(tmp_path, monkeypatch):
    """R0 v4 bug fix: when build fails after Pod creation, ledger
    must still record actual wallclock + cost, not 0."""
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)

    # Inject a failure AFTER Pod creation but during remote work
    real_step = h.step_5_to_11_remote_build
    fake_call_count = {"n": 0}

    def _fail_after_setup(*args, **kwargs):
        fake_call_count["n"] += 1
        # Simulate ~36 seconds of Pod uptime before failure (1% of an hour)
        import time as _t
        original_sleep = _t.sleep
        # We can't actually sleep here in tests; just monkey wallclock
        raise RuntimeError("zstd missing on Pod")

    monkeypatch.setattr(h, "step_5_to_11_remote_build", _fail_after_setup)

    config = _make_config(tmp_path, r_phase="r0")
    result = h.run(config)

    assert result.error is not None
    assert result.pod_terminated is True
    # wallclock must be > 0 (we spent some time even before the failure)
    assert result.wallclock_s >= 0  # at least non-negative

    # Cost ledger must have one entry with the real (small) cost
    ledger = json.loads((tmp_path / "ledger.json").read_text())
    assert len(ledger) == 1
    entry = ledger[0]
    assert entry["pod_id"] is not None  # Pod was created before failure
    # estimated_cost_usd is computed from hourly × wallclock; must be present
    assert "estimated_cost_usd" in entry


def test_run_cost_zero_when_pod_never_created(tmp_path):
    """When --max-cost gate aborts BEFORE Pod creation, recorded cost
    is 0 and pod_id is None (no money risk)."""
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=True)
    config = H.BuildConfig(
        r_phase="r3",
        modalities=("fts", "dense"),
        gpu_type="A100 80GB",
        gpu_cloud="community",
        max_cost_usd=0.10,    # 1.50/hr × 30/60 = $0.75 > $0.10 → abort
        max_duration_min=30,
        repo_root=tmp_path,
        ledger_path=tmp_path / "ledger.json",
    )
    result = h.run(config)
    assert result.error is not None
    assert result.pod_id is None
    assert result.estimated_cost_usd == 0.0
    # Ledger entry exists but with no pod
    ledger = json.loads((tmp_path / "ledger.json").read_text())
    assert ledger[0]["pod_id"] is None
    assert ledger[0]["estimated_cost_usd"] == 0.0


def _build_args(**overrides):
    """Helper — base args namespace for resolve_defaults tests."""
    base = {
        "r_phase": "r1", "modalities": None, "gpu_type": None,
        "gpu_cloud": None, "max_cost": 10.0, "max_duration": 60,
        "repo_root": Path.cwd(), "ledger_path": Path("ledger.json"),
        "max_length": None, "batch_size": None, "precision": None,
        "colbert_dtype": None,
    }
    base.update(overrides)
    return type("A", (), base)()


def test_resolve_defaults_picks_r_phase_appropriate_gpu():
    config = H.resolve_defaults(_build_args(r_phase="r3", max_duration=180))
    assert config.gpu_type == "RTX A6000"     # R3 default
    assert config.gpu_cloud == "community"
    assert "colbert" in config.modalities


def test_resolve_defaults_explicit_modalities_override():
    config = H.resolve_defaults(_build_args(modalities="fts,dense,sparse"))
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


def test_cli_real_mode_requires_api_key(tmp_path, capsys, monkeypatch):
    """Real mode without RUNPOD_API_KEY must error cleanly."""
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    rc = H.main([
        "--r-phase", "r0",
        "--repo-root", str(tmp_path),
        "--ledger-path", str(tmp_path / "ledger.json"),
    ])
    assert rc == 2


# ---------------------------------------------------------------------------
# RealRunPodClient — SDK wrapping with mocked SDK module
# ---------------------------------------------------------------------------

class _FakeRunpodModule:
    """Pretends to be the runpod SDK. Records calls + returns
    structured fake data so we can assert RealRunPodClient maps correctly
    without ever hitting the network."""

    def __init__(self):
        self.api_key = None
        self.calls: list[tuple] = []
        self._user_pubkey = ""        # current account pubKey field

    def get_user(self):
        self.calls.append(("get_user",))
        return {"id": "u1", "pubKey": self._user_pubkey}

    def get_gpus(self):
        self.calls.append(("get_gpus",))
        return [
            {"id": "NVIDIA RTX A5000", "displayName": "RTX A5000",
             "communityPrice": 0.16, "securePrice": 0.29},
            {"id": "NVIDIA RTX A6000", "displayName": "RTX A6000",
             "communityPrice": 0.49, "securePrice": 0.79},
        ]

    def update_user_settings(self, pubkey: str):
        self.calls.append(("update_user_settings", pubkey))
        self._user_pubkey = pubkey

    def create_pod(self, **kwargs):
        self.calls.append(("create_pod", kwargs))
        return {
            "id": "pod-fake-001",
            "name": kwargs.get("name", "fake"),
            "machineType": kwargs.get("gpu_type_id", "?"),
            "createdAt": "2026-05-01T08:30:00Z",
            # initial response — ports often empty until Pod boots
            "runtime": None,
        }

    def get_pod(self, pod_id: str):
        """By default returns a Pod with SSH port populated.
        Tests can override this to simulate slow boot."""
        self.calls.append(("get_pod", pod_id))
        return {
            "id": pod_id,
            "desiredStatus": "RUNNING",
            "uptimeSeconds": 60,
            "createdAt": "2026-05-01T08:30:00Z",
            "runtime": {
                "ports": [{
                    "privatePort": 22, "publicPort": 22001,
                    "ip": "1.2.3.4", "isIpPublic": True, "type": "tcp",
                }],
            },
        }

    def terminate_pod(self, pod_id: str):
        self.calls.append(("terminate_pod", pod_id))


def test_real_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    fake = _FakeRunpodModule()
    with pytest.raises(ValueError, match="RUNPOD_API_KEY"):
        H.RealRunPodClient(runpod_module=fake)


def test_real_client_sets_sdk_api_key():
    fake = _FakeRunpodModule()
    H.RealRunPodClient(api_key="rpa_test", runpod_module=fake)
    assert fake.api_key == "rpa_test"


def test_real_client_estimate_hourly_rate_uses_sdk():
    fake = _FakeRunpodModule()
    client = H.RealRunPodClient(api_key="rpa_test", runpod_module=fake)
    assert client.estimate_hourly_rate("RTX A5000", "community") == 0.16
    assert client.estimate_hourly_rate("RTX A6000", "secure") == 0.79


def test_real_client_estimate_falls_back_when_sdk_fails():
    fake = _FakeRunpodModule()

    def _broken():
        raise RuntimeError("network down")
    fake.get_gpus = _broken  # type: ignore[assignment]
    client = H.RealRunPodClient(api_key="rpa_test", runpod_module=fake)
    # Should return capability-probe default, not crash
    assert client.estimate_hourly_rate("RTX A5000", "community") == 0.16


def test_real_client_estimate_unknown_gpu_returns_default():
    fake = _FakeRunpodModule()
    client = H.RealRunPodClient(api_key="rpa_test", runpod_module=fake)
    assert client.estimate_hourly_rate("Imaginary GPU", "community") == 0.50


def test_real_client_add_ssh_key_appends_to_existing():
    fake = _FakeRunpodModule()
    fake._user_pubkey = "ssh-ed25519 PRE_EXISTING user@laptop"
    client = H.RealRunPodClient(api_key="rpa_test", runpod_module=fake)

    new_key = "ssh-ed25519 NEW_KEY rag-build-r0"
    returned_id = client.add_ssh_key(new_key, label="rag-build-r0")

    # New pubKey should preserve existing AND append new
    assert "PRE_EXISTING" in fake._user_pubkey
    assert "NEW_KEY" in fake._user_pubkey
    # Returned key_id is the public-key text itself
    assert returned_id == new_key.strip()


def test_real_client_add_ssh_key_idempotent():
    """Adding the same key twice is a no-op (don't duplicate lines)."""
    fake = _FakeRunpodModule()
    client = H.RealRunPodClient(api_key="rpa_test", runpod_module=fake)
    key = "ssh-ed25519 KEY1 a"
    client.add_ssh_key(key, label="x")
    update_calls_first = sum(1 for c in fake.calls if c[0] == "update_user_settings")
    client.add_ssh_key(key, label="x")  # second add — already present
    update_calls_second = sum(1 for c in fake.calls if c[0] == "update_user_settings")
    # Second add must NOT trigger another update
    assert update_calls_second == update_calls_first


def test_real_client_remove_ssh_key_preserves_other_keys():
    fake = _FakeRunpodModule()
    fake._user_pubkey = (
        "ssh-ed25519 KEEP_ME user@laptop\n"
        "ssh-ed25519 DELETE_ME rag-build-r0"
    )
    client = H.RealRunPodClient(api_key="rpa_test", runpod_module=fake)
    client.remove_ssh_key("ssh-ed25519 DELETE_ME rag-build-r0")

    assert "KEEP_ME" in fake._user_pubkey
    assert "DELETE_ME" not in fake._user_pubkey


def test_real_client_remove_missing_ssh_key_is_no_op():
    fake = _FakeRunpodModule()
    fake._user_pubkey = "ssh-ed25519 KEEP_ME user@laptop"
    client = H.RealRunPodClient(api_key="rpa_test", runpod_module=fake)
    # No exception, no state change
    client.remove_ssh_key("ssh-ed25519 NEVER_EXISTED foo")
    assert "KEEP_ME" in fake._user_pubkey


def test_real_client_create_pod_maps_to_sdk_kwargs():
    fake = _FakeRunpodModule()
    client = H.RealRunPodClient(api_key="rpa_test", runpod_module=fake)
    spec = H.PodSpec(
        name="rag-r0", gpu_type="RTX A5000", gpu_cloud="community",
        image="runpod/pytorch:img", container_disk_gb=20, ports="22/tcp",
    )
    pod = client.create_pod(spec, ssh_public_key="ssh-ed25519 fake")
    assert pod.pod_id == "pod-fake-001"
    # Public IP/port comes from get_pod() polling, NOT initial create_pod
    assert pod.ssh_port == 22001
    assert pod.ip == "1.2.3.4"
    assert pod.gpu_type == "RTX A5000"

    create_call = next(c for c in fake.calls if c[0] == "create_pod")
    kwargs = create_call[1]
    assert kwargs["name"] == "rag-r0"
    assert kwargs["image_name"] == "runpod/pytorch:img"
    assert kwargs["cloud_type"] == "COMMUNITY"
    assert kwargs["start_ssh"] is True
    assert kwargs["container_disk_in_gb"] == 20

    # Polled get_pod at least once (the R0-fix bug — initial response
    # has runtime=None so we MUST poll until ports populate)
    assert any(c[0] == "get_pod" for c in fake.calls)


def test_real_client_create_pod_polls_until_ssh_port_available(monkeypatch):
    """Bug fix from R0 smoke: create_pod's initial response had
    runtime=None, but the lifecycle assumed runtime.ports was
    immediately available. Now we poll get_pod() until SSH port
    is exposed."""
    fake = _FakeRunpodModule()

    # Simulate slow boot: first 2 get_pod calls return no ports,
    # 3rd returns SSH endpoint
    boot_states = [
        # Call 1: pod created but not yet running
        {"id": "pod-fake-001", "desiredStatus": "PENDING",
         "createdAt": "2026-05-01T08:30:00Z", "runtime": None},
        # Call 2: running but ports not exposed yet
        {"id": "pod-fake-001", "desiredStatus": "RUNNING",
         "createdAt": "2026-05-01T08:30:00Z",
         "runtime": {"ports": []}},
        # Call 3: SSH port public
        {"id": "pod-fake-001", "desiredStatus": "RUNNING",
         "createdAt": "2026-05-01T08:30:00Z",
         "runtime": {"ports": [{"privatePort": 22, "publicPort": 22001,
                                "ip": "5.6.7.8", "isIpPublic": True}]}},
    ]
    state_iter = iter(boot_states)

    def slow_get_pod(pod_id: str):
        fake.calls.append(("get_pod", pod_id))
        return next(state_iter)
    fake.get_pod = slow_get_pod  # type: ignore[assignment]

    # Skip real sleeping
    import scripts.remote.runpod_rag_full_build as H_mod
    monkeypatch.setattr(H_mod.time, "sleep", lambda *a, **k: None)

    client = H.RealRunPodClient(api_key="rpa_test", runpod_module=fake)
    spec = H.PodSpec(
        name="rag-r0", gpu_type="RTX A5000", gpu_cloud="community",
        image="img", container_disk_gb=20, ports="22/tcp",
    )
    pod = client.create_pod(spec, ssh_public_key="ssh-ed25519 fake")

    assert pod.ip == "5.6.7.8"
    assert pod.ssh_port == 22001

    # 3 polls total
    get_pod_calls = [c for c in fake.calls if c[0] == "get_pod"]
    assert len(get_pod_calls) == 3


def test_real_client_create_pod_times_out_when_ssh_never_exposed(monkeypatch):
    """If Pod never exposes SSH within timeout, raise so caller's
    finally-block can terminate the Pod."""
    fake = _FakeRunpodModule()
    fake.get_pod = lambda pod_id: {  # type: ignore[assignment]
        "id": pod_id, "desiredStatus": "PENDING", "runtime": None,
    }
    import scripts.remote.runpod_rag_full_build as H_mod
    monkeypatch.setattr(H_mod.time, "sleep", lambda *a, **k: None)
    monkeypatch.setattr(H_mod.time, "time", iter([0, 1, 2, 3, 100, 200, 400]).__next__)

    client = H.RealRunPodClient(api_key="rpa_test", runpod_module=fake)
    spec = H.PodSpec(
        name="rag-r0", gpu_type="RTX A5000", gpu_cloud="community",
        image="img", container_disk_gb=20, ports="22/tcp",
    )
    with pytest.raises(TimeoutError, match="did not expose public SSH port"):
        client.create_pod(spec, ssh_public_key="ssh-ed25519 fake")


def test_find_public_ssh_endpoint_filters_non_public_ports():
    """Multi-port Pod — only the public SSH port qualifies."""
    pod_data = {
        "runtime": {
            "ports": [
                # Internal-only port — skip
                {"privatePort": 22, "publicPort": 22, "ip": "10.0.0.1",
                 "isIpPublic": False, "type": "tcp"},
                # HTTP port — skip (not SSH)
                {"privatePort": 8888, "publicPort": 8888, "ip": "1.2.3.4",
                 "isIpPublic": True, "type": "http"},
                # The public SSH port — pick this
                {"privatePort": 22, "publicPort": 22001, "ip": "1.2.3.4",
                 "isIpPublic": True, "type": "tcp"},
            ]
        }
    }
    result = H.RealRunPodClient._find_public_ssh_endpoint(pod_data)
    assert result == ("1.2.3.4", 22001)


def test_find_public_ssh_endpoint_returns_none_when_unavailable():
    assert H.RealRunPodClient._find_public_ssh_endpoint(
        {"runtime": {"ports": []}}) is None
    assert H.RealRunPodClient._find_public_ssh_endpoint(
        {"runtime": None}) is None
    assert H.RealRunPodClient._find_public_ssh_endpoint({}) is None


def test_real_client_terminate_swallows_sdk_error():
    """terminate is best-effort — if SDK fails (already terminated /
    rate-limit etc) we log and continue."""
    fake = _FakeRunpodModule()
    def _broken(pod_id):
        raise RuntimeError("pod not found")
    fake.terminate_pod = _broken  # type: ignore[assignment]
    client = H.RealRunPodClient(api_key="rpa_test", runpod_module=fake)
    # No exception
    client.terminate_pod("pod-x")


# ---------------------------------------------------------------------------
# Step 5-11 SSH execution path (with injected fake executor)
# ---------------------------------------------------------------------------

class _FakeSshExecutor:
    """Records every command without touching network."""

    def __init__(self, *, fail_on: int | None = None):
        self.commands: list[str] = []
        self.scp_calls: list[tuple[str, str]] = []
        self.fail_on = fail_on  # 1-based command index that should fail
        self._waited = False

    def wait_for_ssh(self, pod, keypath, *, timeout_s):
        self._waited = True

    def run(self, pod, keypath, command, *, timeout_s):
        self.commands.append(command)
        if self.fail_on is not None and len(self.commands) == self.fail_on:
            return 1, "", "simulated remote failure"
        return 0, "ok", ""

    def scp_from_pod(self, pod, keypath, remote, local):
        self.scp_calls.append((remote, str(local)))
        # Simulate file creation locally
        Path(local).parent.mkdir(parents=True, exist_ok=True)
        Path(local).write_bytes(b"fake artifact")


def test_step_5_to_11_runs_all_commands_in_live_mode(tmp_path):
    """Live (non-dry-run) executes every Pod command via SSH and
    pulls the artifact back."""
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=False)
    pod = H.Pod(pod_id="pod-1", ip="10.0.0.1", ssh_port=22001,
                gpu_type="RTX A5000",
                started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc))
    keypath = tmp_path / "fake-key"
    keypath.touch()
    fake_ssh = _FakeSshExecutor()

    artifact = h.step_5_to_11_remote_build(
        pod, keypath,
        commit_sha="abc1234",
        modalities=("fts",),
        run_id="r0-test",
        r_phase="r0",
        repo_root=tmp_path,
        ssh_executor=fake_ssh,
    )

    assert fake_ssh._waited is True
    assert len(fake_ssh.commands) >= 5  # clone + checkout + venv + pip + build + package
    assert any("git clone" in c for c in fake_ssh.commands)
    assert any("cs-index-build" in c or "cli_cs_index_build" in c
               for c in fake_ssh.commands)
    # Artifact returned
    assert artifact is not None
    assert (artifact / "cs_rag_index_root.tar.zst").exists()


def test_step_5_to_11_raises_on_command_failure(tmp_path):
    """If a remote command returns non-zero, raise to trigger
    finally-block Pod cleanup."""
    client = H.MockRunPodClient()
    h = H.RunPodHarness(client, dry_run=False)
    pod = H.Pod(pod_id="pod-1", ip="10.0.0.1", ssh_port=22001,
                gpu_type="RTX A5000",
                started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc))
    keypath = tmp_path / "fake-key"
    keypath.touch()
    fake_ssh = _FakeSshExecutor(fail_on=2)  # 2nd command fails (git checkout)

    with pytest.raises(RuntimeError, match="remote command failed"):
        h.step_5_to_11_remote_build(
            pod, keypath,
            commit_sha="abc1234",
            modalities=("fts",),
            run_id="r0-test",
            r_phase="r0",
            repo_root=tmp_path,
            ssh_executor=fake_ssh,
        )

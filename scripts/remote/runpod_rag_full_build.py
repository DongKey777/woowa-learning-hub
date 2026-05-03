"""RunPod RAG full build harness (plan v5 §H0 task v5-5 / v5-6).

12-step lifecycle from worklog 970f83a:
1. Verify local tree clean / record commit SHA
2. Verify pushed (or fall back to git bundle / source tarball)
3. Create RunPod GPU Pod via API
4. Generate + register ephemeral SSH key
5. Clone repo at exact commit SHA on Pod
6. Install dependencies on Pod
7. Warm HuggingFace model cache
8. Run full build (`bin/cs-index-build --backend lance ...`)
9. Run evaluation (`bin/rag-eval --ablate ...`)
10. Package artifacts (`scripts/remote/package_rag_artifact.py`)
11. Download artifact to local
12. **Always** terminate Pod + remove SSH key (try/finally + signal)

This module separates *orchestration logic* from *API client*. The
``RunPodApiClient`` interface is mocked by ``MockRunPodClient`` for
``--dry-run`` mode (task v5-5) and replaced by a real ``runpod-python``
client in task v5-6.

The dry-run path validates the lifecycle without touching the network:
no Pod created, no API key consumed, no SSH connection attempted. Used
to lock the orchestration logic + test all error paths before spending
money.

Tested in ``tests/unit/test_runpod_rag_full_build.py``.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import os
import signal
import shlex
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from scripts.remote.artifact_contract import verify_artifact_dir


logger = logging.getLogger(__name__)

R_PHASES = ("r-1", "r0", "r1", "r2", "r3", "r4")
SOURCE_MODES = ("auto", "git", "bundle")
REMOTE_BUNDLE_PATH = "/workspace/woowa-learning-hub.bundle"

# GPU defaults per R-phase (capability probe §4)
DEFAULT_GPU_PER_PHASE = {
    "r0": ("RTX A5000", "community"),
    "r1": ("RTX A5000", "community"),
    "r2": ("RTX A5000", "community"),
    "r3": ("RTX A6000", "community"),
    "r4": ("RTX A5000", "community"),
}

# Default modalities per R-phase (worklog 970f83a + plan v5 §3)
DEFAULT_MODALITIES_PER_PHASE = {
    "r0": ("fts",),
    "r1": ("fts", "dense"),
    "r2": ("fts", "dense", "sparse"),
    "r3": ("fts", "dense", "sparse", "colbert"),
    "r4": ("fts", "dense", "sparse"),  # rerank-only, build reuses R3 stack
}

# R3 qrel fixture used as the manifest's qrel-hash reference. Updated
# 2026-05-03 from the legacy r3_corpus_v2_qrels_20260502T0757Z.json
# (deleted; circular-leak baseline) to the Phase 4.7 v1 200-query
# suite covering all 6 cohorts (paraphrase_human / confusable_pairs /
# symptom_to_cause / mission_bridge / corpus_gap_probe /
# forbidden_neighbor). The path must exist on the remote pod after
# `git checkout` for the manifest sha256 step to succeed.
R3_QREL_PATH = "tests/fixtures/r3_qrels_real_v1.json"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PodSpec:
    """What we ask RunPod to deploy."""
    name: str
    gpu_type: str           # "RTX A5000" etc.
    gpu_cloud: str          # "community" | "secure"
    image: str              # docker image
    container_disk_gb: int
    ports: str              # e.g. "22/tcp"
    # Host-RAM floor. RunPod SDK defaults to 1GB; for r3 ColBERT builds
    # the IVF_PQ index over 27K+ chunks requires ~50 GB host RAM
    # (encoding accumulator + index k-means clustering temp). Set this
    # explicitly per R-phase so the scheduler picks a host with enough
    # memory rather than rolling the dice.
    min_memory_in_gb: int = 1
    min_vcpu_count: int = 1


@dataclass(frozen=True)
class Pod:
    """Live Pod handle returned by the API."""
    pod_id: str
    ip: str
    ssh_port: int
    gpu_type: str
    started_at: datetime


@dataclass
class BuildResult:
    """End-to-end outcome of one R-phase run."""
    run_id: str
    r_phase: str
    pod_id: str | None
    pod_terminated: bool
    artifact_path: Path | None
    estimated_cost_usd: float
    wallclock_s: float
    error: str | None = None


# ---------------------------------------------------------------------------
# API client abstraction
# ---------------------------------------------------------------------------

class RunPodApiClient(Protocol):
    """Two implementations:

    - ``MockRunPodClient``: in-memory, no network. Used by --dry-run.
    - (v5-6) ``RealRunPodClient``: wraps ``runpod-python`` SDK.
    """

    def create_pod(self, spec: PodSpec, ssh_public_key: str) -> Pod: ...
    def terminate_pod(self, pod_id: str) -> None: ...
    def list_pods(self) -> list[Pod]: ...
    def add_ssh_key(self, public_key: str, *, label: str) -> str:
        """Returns a key id we can use to remove the key later."""
        ...
    def remove_ssh_key(self, key_id: str) -> None: ...
    def estimate_hourly_rate(self, gpu_type: str, cloud: str) -> float: ...


# ---------------------------------------------------------------------------
# Mock client (for --dry-run)
# ---------------------------------------------------------------------------

class MockRunPodClient:
    """In-memory mock — records every call without network access.

    Useful for:
    - --dry-run validation of the orchestration logic
    - Unit tests of the harness lifecycle
    - Verifying that try/finally + signal handlers always terminate
    """

    def __init__(self):
        self.calls: list[dict] = []
        self._next_pod = 0
        self._next_key = 0
        self._ssh_keys: dict[str, str] = {}  # key_id → public_key
        self._pods: dict[str, Pod] = {}

    def create_pod(self, spec: PodSpec, ssh_public_key: str) -> Pod:
        self._next_pod += 1
        pod_id = f"mock-pod-{self._next_pod:04d}"
        pod = Pod(
            pod_id=pod_id,
            ip="10.0.0.1",
            ssh_port=22000 + self._next_pod,
            gpu_type=spec.gpu_type,
            started_at=datetime.now(timezone.utc),
        )
        self._pods[pod_id] = pod
        self.calls.append({"op": "create_pod", "spec": dataclasses.asdict(spec),
                           "pod_id": pod_id})
        return pod

    def terminate_pod(self, pod_id: str) -> None:
        self.calls.append({"op": "terminate_pod", "pod_id": pod_id})
        self._pods.pop(pod_id, None)

    def list_pods(self) -> list[Pod]:
        self.calls.append({"op": "list_pods"})
        return list(self._pods.values())

    def add_ssh_key(self, public_key: str, *, label: str) -> str:
        self._next_key += 1
        key_id = f"mock-key-{self._next_key:04d}"
        self._ssh_keys[key_id] = public_key
        self.calls.append({"op": "add_ssh_key", "label": label, "key_id": key_id})
        return key_id

    def remove_ssh_key(self, key_id: str) -> None:
        self.calls.append({"op": "remove_ssh_key", "key_id": key_id})
        self._ssh_keys.pop(key_id, None)

    def estimate_hourly_rate(self, gpu_type: str, cloud: str) -> float:
        rates = {
            ("RTX A5000", "community"): 0.16,
            ("RTX A5000", "secure"): 0.29,
            ("RTX A6000", "community"): 0.49,
            ("RTX A6000", "secure"): 0.79,
            ("A100 80GB", "community"): 1.50,
            ("A100 80GB", "secure"): 1.99,
        }
        rate = rates.get((gpu_type, cloud), 0.50)
        self.calls.append({"op": "estimate_hourly_rate", "gpu_type": gpu_type,
                           "cloud": cloud, "rate": rate})
        return rate


# ---------------------------------------------------------------------------
# SSH executor (task v5-6) — paramiko-based remote command execution
# ---------------------------------------------------------------------------

class SshExecutor(Protocol):
    """Abstract SSH executor — Protocol for dependency injection in tests."""

    def wait_for_ssh(self, pod: Pod, keypath: Path, *, timeout_s: int) -> None: ...

    def run(
        self, pod: Pod, keypath: Path, command: str, *, timeout_s: int,
    ) -> tuple[int, str, str]:
        """Returns (returncode, stdout, stderr)."""
        ...

    def scp_from_pod(
        self, pod: Pod, keypath: Path, remote_path: str, local_path: Path,
    ) -> None:
        """Pull a file from Pod to local."""
        ...

    def scp_to_pod(
        self, pod: Pod, keypath: Path, local_path: Path, remote_path: str,
    ) -> None:
        """Push a file from local to Pod."""
        ...


class _ParamikoSshExecutor:
    """Production SSH executor using paramiko (already installed via
    runpod SDK deps).

    Does NOT use a known_hosts file — Pod hosts are ephemeral and
    rotate per build. Instead we accept the host key on first connect
    (paramiko.AutoAddPolicy). This is acceptable because we own the
    Pod and the SSH key registration was just done by us.
    """

    def __init__(self):
        import paramiko  # noqa: WPS433 — lazy import keeps mock tests light
        self._paramiko = paramiko

    def _client(self, pod: Pod, keypath: Path):
        client = self._paramiko.SSHClient()
        client.set_missing_host_key_policy(self._paramiko.AutoAddPolicy())
        pkey = self._paramiko.Ed25519Key.from_private_key_file(str(keypath))
        client.connect(
            hostname=pod.ip,
            port=pod.ssh_port,
            username="root",
            pkey=pkey,
            timeout=30,
            auth_timeout=30,
        )
        transport = client.get_transport()
        if transport is not None:
            transport.set_keepalive(30)
        return client

    def wait_for_ssh(self, pod: Pod, keypath: Path, *, timeout_s: int) -> None:
        deadline = time.time() + timeout_s
        last_err = None
        while time.time() < deadline:
            try:
                client = self._client(pod, keypath)
                client.close()
                return
            except Exception as exc:
                last_err = exc
                time.sleep(5)
        raise TimeoutError(
            f"SSH not reachable on {pod.ip}:{pod.ssh_port} after {timeout_s}s "
            f"(last error: {last_err})"
        )

    def run(self, pod: Pod, keypath: Path, command: str, *,
            timeout_s: int) -> tuple[int, str, str]:
        client = self._client(pod, keypath)
        try:
            stdin, stdout, stderr = client.exec_command(command)
            stdin.close()
            channel = stdout.channel
            stdout_chunks: list[bytes] = []
            stderr_chunks: list[bytes] = []
            deadline = time.monotonic() + timeout_s

            while True:
                if channel.recv_ready():
                    stdout_chunks.append(channel.recv(65536))
                if channel.recv_stderr_ready():
                    stderr_chunks.append(channel.recv_stderr(65536))
                if channel.exit_status_ready():
                    while channel.recv_ready():
                        stdout_chunks.append(channel.recv(65536))
                    while channel.recv_stderr_ready():
                        stderr_chunks.append(channel.recv_stderr(65536))
                    break
                if time.monotonic() > deadline:
                    channel.close()
                    raise TimeoutError(
                        f"remote command timed out after {timeout_s}s: {command[:120]}"
                    )
                time.sleep(0.1)

            rc = channel.recv_exit_status()
            stdout_text = b"".join(stdout_chunks).decode("utf-8", errors="replace")
            stderr_text = b"".join(stderr_chunks).decode("utf-8", errors="replace")
            return rc, stdout_text, stderr_text
        finally:
            client.close()

    def scp_from_pod(self, pod: Pod, keypath: Path, remote_path: str,
                     local_path: Path) -> None:
        """Pull a file from the Pod with resume support.

        R3 archives are large enough that RunPod community SSH channels can
        reset during transfer. Paramiko's plain ``SFTPClient.get`` leaves a
        truncated file at the final path and gives the caller no chance to
        resume, so we stream into ``*.part`` and reconnect from the current
        offset when the channel drops.
        """

        local_path.parent.mkdir(parents=True, exist_ok=True)
        part_path = local_path.with_name(f"{local_path.name}.part")
        remote_size = self._remote_file_size(pod, keypath, remote_path)

        if local_path.exists():
            local_size = local_path.stat().st_size
            if local_size == remote_size:
                return
            if part_path.exists():
                part_path.unlink()
            local_path.replace(part_path)

        if part_path.exists() and part_path.stat().st_size > remote_size:
            part_path.unlink()

        attempts = 0
        max_attempts = 8
        chunk_size = 8 * 1024 * 1024
        while (part_path.stat().st_size if part_path.exists() else 0) < remote_size:
            offset = part_path.stat().st_size if part_path.exists() else 0
            attempts += 1
            try:
                self._download_range(
                    pod,
                    keypath,
                    remote_path,
                    part_path,
                    offset=offset,
                    chunk_size=chunk_size,
                )
            except Exception as exc:
                if attempts >= max_attempts:
                    raise
                logger.warning(
                    "[runpod] transfer reset for %s at %d/%d bytes "
                    "(attempt %d/%d): %s",
                    remote_path,
                    offset,
                    remote_size,
                    attempts,
                    max_attempts,
                    exc,
                )
                time.sleep(min(30, attempts * 5))
                continue

        if part_path.stat().st_size != remote_size:
            raise RuntimeError(
                f"download size mismatch for {remote_path}: "
                f"{part_path.stat().st_size} != {remote_size}"
            )
        part_path.replace(local_path)

    def _remote_file_size(self, pod: Pod, keypath: Path, remote_path: str) -> int:
        client = self._client(pod, keypath)
        try:
            sftp = client.open_sftp()
            try:
                return int(sftp.stat(remote_path).st_size)
            finally:
                sftp.close()
        finally:
            client.close()

    def _download_range(
        self,
        pod: Pod,
        keypath: Path,
        remote_path: str,
        part_path: Path,
        *,
        offset: int,
        chunk_size: int,
    ) -> None:
        client = self._client(pod, keypath)
        try:
            sftp = client.open_sftp()
            try:
                with sftp.open(remote_path, "rb") as remote_file:
                    remote_file.seek(offset)
                    with part_path.open("ab") as local_file:
                        while True:
                            chunk = remote_file.read(chunk_size)
                            if not chunk:
                                break
                            local_file.write(chunk)
            finally:
                sftp.close()
        finally:
            client.close()

    def scp_to_pod(self, pod: Pod, keypath: Path, local_path: Path,
                   remote_path: str) -> None:
        client = self._client(pod, keypath)
        try:
            sftp = client.open_sftp()
            try:
                sftp.put(str(local_path), remote_path)
            finally:
                sftp.close()
        finally:
            client.close()


# ---------------------------------------------------------------------------
# Real RunPod client (task v5-6) — wraps runpod-python SDK
# ---------------------------------------------------------------------------

class RealRunPodClient:
    """Production wrapper around the runpod-python SDK (1.9+).

    Uses ``RUNPOD_API_KEY`` env var or explicit ``api_key`` argument.
    All methods are thin SDK wrappers + response normalisation to our
    ``PodSpec`` / ``Pod`` dataclasses.

    SSH key handling — peer concern from R-1 capability probe:
    the SDK's ``update_user_settings(pubkey)`` writes a single string
    to the account's ``pubKey`` field. Multiple keys are concatenated
    with newline. So *append* means: read existing, "\\n".join with new,
    write back. *Remove* means: read existing, drop matching line,
    write back. We never blow away pre-existing user keys.

    Tested against a real API key in unit tests via dependency injection
    (``runpod_module`` argument). Tests use a fake module that records
    calls — no live network in unit tests.
    """

    def __init__(self, *, api_key: str | None = None, runpod_module=None):
        if runpod_module is None:
            import runpod as runpod_module  # type: ignore  # noqa: WPS433
        self._sdk = runpod_module
        self._api_key = api_key or os.environ.get("RUNPOD_API_KEY")
        if not self._api_key:
            raise ValueError(
                "RUNPOD_API_KEY env var not set and api_key arg not provided"
            )
        self._sdk.api_key = self._api_key

    # ----- GPU pricing -----

    def estimate_hourly_rate(self, gpu_type: str, cloud: str) -> float:
        """Query live SDK for GPU type pricing.

        SDK returns a list of GPU types with per-hour rates for
        secure / community / spot tiers. We pick by name + cloud type.
        Falls back to capability-probe defaults when SDK can't resolve.
        """
        try:
            gpus = self._sdk.get_gpus()
        except Exception as exc:
            logger.warning(
                "[runpod] get_gpus failed (%s) — using probe-default rate", exc,
            )
            return self._fallback_rate(gpu_type, cloud)

        for gpu in gpus or []:
            display_name = gpu.get("displayName", "")
            if gpu_type.lower() in display_name.lower():
                # Field naming varies across SDK versions; check both
                if cloud == "community":
                    rate = (gpu.get("communityPrice")
                            or gpu.get("lowestPrice", {}).get("uninterruptablePrice")
                            or 0)
                else:
                    rate = (gpu.get("securePrice")
                            or gpu.get("lowestPrice", {}).get("uninterruptablePrice")
                            or 0)
                if rate:
                    return float(rate)
        return self._fallback_rate(gpu_type, cloud)

    @staticmethod
    def _fallback_rate(gpu_type: str, cloud: str) -> float:
        """Capability-probe defaults — used when SDK price query fails."""
        rates = {
            ("RTX A5000", "community"): 0.16,
            ("RTX A5000", "secure"): 0.29,
            ("RTX A6000", "community"): 0.49,
            ("RTX A6000", "secure"): 0.79,
            ("A100 80GB", "community"): 1.50,
            ("A100 80GB", "secure"): 1.99,
        }
        return rates.get((gpu_type, cloud), 0.50)

    # ----- SSH key management (newline-separated single-string field) -----

    def add_ssh_key(self, public_key: str, *, label: str) -> str:
        """Append our public key to the account's pubKey string.

        Returns the public-key text itself as the "key id" so
        ``remove_ssh_key`` can find it. The SDK doesn't return a
        per-key handle.
        """
        existing = self._read_pubkey_field()
        new_key_line = public_key.strip()
        if new_key_line in existing:
            return new_key_line  # idempotent — already present
        merged = existing + ("\n" if existing else "") + new_key_line
        self._sdk.update_user_settings(pubkey=merged)
        return new_key_line

    def remove_ssh_key(self, key_id: str) -> None:
        """Remove our key (key_id is the public-key text we returned
        from add_ssh_key). Safely no-op if the key isn't there."""
        existing = self._read_pubkey_field()
        target = key_id.strip()
        if target not in existing:
            return
        # Filter line-by-line to preserve unrelated keys
        kept = [line for line in existing.splitlines() if line.strip() != target]
        self._sdk.update_user_settings(pubkey="\n".join(kept))

    def _read_pubkey_field(self) -> str:
        try:
            user = self._sdk.get_user()
        except Exception as exc:
            logger.warning("[runpod] get_user failed (%s); assuming empty pubKey", exc)
            return ""
        if isinstance(user, dict):
            return user.get("pubKey", "") or ""
        return ""

    # ----- Pod lifecycle -----

    def create_pod(self, spec: PodSpec, ssh_public_key: str) -> Pod:
        """Map our PodSpec to runpod.create_pod, then poll until the
        Pod exposes its public SSH port.

        Why poll: ``runpod.create_pod()`` returns immediately after the
        API accepts the request, BEFORE the Pod has booted enough for
        ``runtime.ports`` to be populated with public IP + port. R0
        smoke caught this — the initial SDK response had ``runtime``
        absent / empty, so SSH wait got stuck on ``0.0.0.0:22``.

        We poll ``get_pod(id)`` every 5s for up to 5 min, looking for
        a port entry with ``privatePort=22`` AND ``isIpPublic=True``.
        That's the SSH endpoint paramiko can reach.
        """
        cloud_map = {"community": "COMMUNITY", "secure": "SECURE"}
        gpu_type_id = self._resolve_gpu_type_id(spec.gpu_type, spec.gpu_cloud)
        result = self._sdk.create_pod(
            name=spec.name,
            image_name=spec.image,
            gpu_type_id=gpu_type_id,
            cloud_type=cloud_map.get(spec.gpu_cloud, "ALL"),
            gpu_count=1,
            container_disk_in_gb=spec.container_disk_gb,
            min_memory_in_gb=spec.min_memory_in_gb,
            min_vcpu_count=spec.min_vcpu_count,
            ports=spec.ports,
            start_ssh=True,
            support_public_ip=True,
        )
        pod_id = result.get("id")
        if not pod_id:
            raise RuntimeError(f"create_pod returned no id: {result}")

        try:
            return self._wait_for_ssh_port(
                pod_id,
                gpu_type=spec.gpu_type,
                timeout_s=300,
                poll_interval_s=5,
            )
        except Exception:
            self.terminate_pod(pod_id)
            raise

    def _wait_for_ssh_port(
        self, pod_id: str, *, gpu_type: str,
        timeout_s: int = 300, poll_interval_s: int = 5,
    ) -> Pod:
        """Poll get_pod(id) until runtime.ports has a public SSH entry."""
        deadline = time.time() + timeout_s
        last_pod_data: dict = {}
        while time.time() < deadline:
            try:
                pod_data = self._sdk.get_pod(pod_id) or {}
            except Exception as exc:
                logger.warning("[runpod] get_pod(%s) error: %s", pod_id, exc)
                time.sleep(poll_interval_s)
                continue
            last_pod_data = pod_data
            ssh_endpoint = self._find_public_ssh_endpoint(pod_data)
            if ssh_endpoint:
                ip, port = ssh_endpoint
                logger.info("[runpod] Pod %s SSH endpoint: %s:%s "
                            "(uptime=%ss, status=%s)",
                            pod_id, ip, port,
                            pod_data.get("uptimeSeconds"),
                            pod_data.get("desiredStatus"))
                return self._build_pod(pod_data, ip=ip, port=port, gpu_type=gpu_type)
            logger.debug("[runpod] Pod %s SSH not yet exposed (status=%s)",
                         pod_id, pod_data.get("desiredStatus"))
            time.sleep(poll_interval_s)
        raise TimeoutError(
            f"Pod {pod_id} did not expose public SSH port within {timeout_s}s. "
            f"Last desiredStatus={last_pod_data.get('desiredStatus')}, "
            f"runtime={last_pod_data.get('runtime')}"
        )

    @staticmethod
    def _find_public_ssh_endpoint(pod_data: dict) -> tuple[str, int] | None:
        """Find a port entry that's public + maps SSH (private 22)."""
        runtime = pod_data.get("runtime") or {}
        ports = runtime.get("ports") or []
        for port in ports:
            if (port.get("privatePort") == 22
                    and port.get("isIpPublic")
                    and port.get("ip")
                    and port.get("publicPort")):
                return str(port["ip"]), int(port["publicPort"])
        return None

    @staticmethod
    def _build_pod(pod_data: dict, *, ip: str, port: int, gpu_type: str) -> Pod:
        started = pod_data.get("createdAt") or datetime.now(timezone.utc).isoformat()
        try:
            started_at = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
        except Exception:
            started_at = datetime.now(timezone.utc)
        return Pod(
            pod_id=pod_data.get("id", "unknown"),
            ip=ip, ssh_port=port,
            gpu_type=gpu_type, started_at=started_at,
        )

    def _resolve_gpu_type_id(self, display_name: str, cloud: str) -> str:
        """Find SDK gpu_type_id by displayName substring match."""
        try:
            gpus = self._sdk.get_gpus()
        except Exception as exc:
            logger.warning("[runpod] get_gpus failed: %s — passing display name", exc)
            return display_name
        for gpu in gpus or []:
            if display_name.lower() in gpu.get("displayName", "").lower():
                return gpu.get("id") or display_name
        return display_name

    def terminate_pod(self, pod_id: str) -> None:
        """Hard-stop the Pod. Idempotent — SDK errors on missing pod
        are swallowed and logged (we may be cleaning up a Pod that
        already self-terminated)."""
        try:
            self._sdk.terminate_pod(pod_id)
        except Exception as exc:
            logger.warning("[runpod] terminate_pod(%s) error: %s", pod_id, exc)

    def list_pods(self) -> list[Pod]:
        try:
            pods = self._sdk.get_pods()
        except Exception as exc:
            logger.warning("[runpod] get_pods failed: %s", exc)
            return []
        return [self._normalise_pod(p, gpu_type=p.get("machineType", "unknown"))
                for p in (pods or [])]

    @staticmethod
    def _normalise_pod(sdk_pod: dict, *, gpu_type: str) -> Pod:
        """Convert SDK response dict to our Pod dataclass.

        SDK response shape (varies by version):
          {id, name, machineType, runtime: {ports: [{ip, publicPort, ...}]}, ...}
        """
        pod_id = sdk_pod.get("id", "unknown")
        # SSH port + ip live under runtime.ports
        ip = "0.0.0.0"
        ssh_port = 22
        runtime = sdk_pod.get("runtime") or {}
        for port in runtime.get("ports") or []:
            if port.get("privatePort") == 22 or port.get("type") == "tcp":
                ip = port.get("ip", ip)
                ssh_port = int(port.get("publicPort", ssh_port))
                break
        started = sdk_pod.get("createdAt") or datetime.now(timezone.utc).isoformat()
        try:
            started_at = datetime.fromisoformat(started.replace("Z", "+00:00"))
        except Exception:
            started_at = datetime.now(timezone.utc)
        return Pod(
            pod_id=pod_id,
            ip=ip,
            ssh_port=ssh_port,
            gpu_type=gpu_type,
            started_at=started_at,
        )


# ---------------------------------------------------------------------------
# Helpers — git state, run_id, cost ledger
# ---------------------------------------------------------------------------

def _run_git(cmd: list[str], *, cwd: Path | None = None) -> str:
    try:
        return subprocess.check_output(
            cmd, cwd=cwd, stderr=subprocess.DEVNULL,
        ).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return ""


def get_git_state(repo_root: Path) -> dict:
    """Return commit SHA + push status."""
    sha = _run_git(["git", "rev-parse", "HEAD"], cwd=repo_root)
    branch = _run_git(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    porcelain = _run_git(["git", "status", "--porcelain"], cwd=repo_root)
    is_clean = not porcelain.strip()
    # Ahead of origin by N commits → push needed
    ahead = _run_git(["git", "rev-list", "--count", f"origin/{branch}..{branch}"], cwd=repo_root)
    try:
        commits_ahead = int(ahead) if ahead else 0
    except ValueError:
        commits_ahead = 0
    return {
        "commit_sha": sha,
        "commit_sha_short": sha[:7] if sha else "unknown",
        "branch": branch,
        "is_clean": is_clean,
        "commits_ahead_of_origin": commits_ahead,
    }


def build_run_id(r_phase: str, git_state: dict) -> str:
    """Format: ``<r-phase>-<commit-sha7>-<timestamp>``."""
    sha7 = git_state.get("commit_sha_short", "nogit")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M")
    return f"{r_phase}-{sha7}-{ts}"


def resolve_source_mode(source_mode: str, git_state: dict) -> str:
    """Choose how the Pod receives the repository source.

    ``git`` is cheapest when the selected commit is already reachable from
    GitHub.  ``bundle`` is the safer fallback for local commits ahead of
    origin: it transfers the committed HEAD history directly to the Pod without
    pushing.  Dirty working-tree changes are deliberately not bundled; the
    remote build should be based on an explicit commit.
    """

    if source_mode not in SOURCE_MODES:
        raise ValueError(f"unknown source mode: {source_mode}")
    if source_mode != "auto":
        return source_mode
    try:
        ahead = int(git_state.get("commits_ahead_of_origin") or 0)
    except (TypeError, ValueError):
        ahead = 0
    return "bundle" if ahead > 0 else "git"


def append_cost_ledger(
    ledger_path: Path,
    *,
    run_id: str,
    gpu: str,
    started_at: datetime,
    ended_at: datetime,
    estimated_cost_usd: float,
    pod_id: str | None,
    deleted: bool,
) -> None:
    """Append an entry to the v1 cost ledger (plan v5 §6 — simple shape)."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    if ledger_path.exists():
        try:
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            ledger = []
    else:
        ledger = []
    ledger.append({
        "run_id": run_id,
        "gpu": gpu,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "estimated_cost_usd": round(estimated_cost_usd, 4),
        "pod_id": pod_id,
        "deleted": deleted,
    })
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2),
                           encoding="utf-8")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

@dataclass
class BuildConfig:
    r_phase: str
    modalities: tuple[str, ...]
    gpu_type: str
    gpu_cloud: str
    max_cost_usd: float
    max_duration_min: int
    image: str = "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"
    container_disk_gb: int = 80
    # Host-RAM / vCPU floor for the build pod. r3 ColBERT IVF_PQ index
    # build over 27K+ chunks needs ~50 GB host RAM minimum (encoding
    # accumulator + clustering temp memory). Without this, RunPod's
    # default min_memory_in_gb=1 lets the scheduler pick any host and
    # the build OOMs at the index step. r3 default is 128 GB to absorb
    # spikes; lower phases get smaller floors.
    min_memory_gb: int = 1
    min_vcpu_count: int = 1
    repo_root: Path = field(default_factory=lambda: Path.cwd())
    ledger_path: Path = field(default_factory=lambda: Path("state/cs_rag_remote/cost_ledger.json"))
    # bge-m3 build params — passed to cs-index-build on Pod (R1 needs
    # max_length=512 per plan v5 §R1, R0 used cs-index-build default 1024)
    lance_max_length: int | None = None       # None → cs-index-build default
    lance_batch_size: int | None = None
    lance_precision: str | None = None         # "auto"|"fp16"|"fp32"
    lance_colbert_dtype: str | None = None     # "float16"|"float32"
    ivf_num_partitions: int | None = None
    ivf_num_sub_vectors: int | None = None
    source_mode: str = "auto"
    # Skip the in-build cli_rag_eval --ablate step (Step 9). Used when
    # the real measurement happens locally via cohort_eval rather than
    # in-build ablation. v7 build hit the 5400s SSH-command timeout
    # because cli_rag_eval re-encodes every query without caching.
    skip_eval: bool = False
    # Skip the harness's built-in scp_from_pod step. Use when the
    # caller will fetch the artifact directly via system `scp` (faster +
    # more resilient than paramiko's SFTPClient.get on large transfers
    # — v9 measured 5x throughput from system scp vs paramiko).
    skip_auto_scp: bool = False
    # Skip terminate_pod in cleanup. Use to keep the Pod alive after
    # the build completes so the caller can fetch artifacts directly.
    # Caller MUST call runpod.terminate_pod() manually afterwards or
    # cost accrues indefinitely.
    keep_pod: bool = False


class RunPodHarness:
    """Orchestrates the 12-step lifecycle.

    Constructor takes a ``RunPodApiClient`` (mock for dry-run, real for
    production). The lifecycle is the same regardless of client.
    """

    def __init__(self, client: RunPodApiClient, *, dry_run: bool = False):
        self.client = client
        self.dry_run = dry_run
        # State the finally block needs even when something blows up early.
        self._pod_id: str | None = None
        self._ssh_key_id: str | None = None
        self._ssh_keypath: Path | None = None
        self._signals_installed = False
        self._original_handlers: dict[int, Any] = {}

    # --- Signal handling: ensure cleanup runs on Ctrl-C / SIGTERM -----

    def _install_signal_handlers(self) -> None:
        if self._signals_installed:
            return
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                self._original_handlers[sig] = signal.getsignal(sig)
                signal.signal(sig, self._signal_handler)
            except (ValueError, OSError):
                pass  # not in main thread or restricted env
        self._signals_installed = True

    def _restore_signal_handlers(self) -> None:
        for sig, handler in self._original_handlers.items():
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):
                pass
        self._original_handlers.clear()
        self._signals_installed = False

    def _signal_handler(self, signum, frame):
        logger.warning(
            "[runpod] received signal %s — running cleanup before exit", signum
        )
        self._cleanup()
        # Re-raise to terminate
        raise KeyboardInterrupt(f"received signal {signum}")

    # --- Steps ---------------------------------------------------------

    def step_1_2_verify_repo_state(self, repo_root: Path) -> dict:
        """Steps 1+2: capture git SHA + warn if push needed.

        Doesn't fail on dirty/unpushed — caller decides the fallback
        path (push, bundle, tarball).
        """
        state = get_git_state(repo_root)
        if not state["is_clean"]:
            logger.warning("[runpod] working tree not clean — fallback path needed")
        if state["commits_ahead_of_origin"] > 0:
            logger.warning(
                "[runpod] %s commits ahead of origin — push first OR use git "
                "bundle/source-tar fallback",
                state["commits_ahead_of_origin"],
            )
        return state

    def step_3_4_create_pod_with_ssh(
        self, spec: PodSpec, *, ssh_label: str,
    ) -> tuple[Pod, str, Path]:
        """Steps 3+4: generate ephemeral SSH key, register, create Pod.

        Returns ``(pod, key_id, key_path)`` so caller can SSH into Pod
        and we know what to clean up.
        """
        # Generate key
        keypath = Path(f"/tmp/rag-pod-{uuid.uuid4().hex[:8]}")
        if self.dry_run:
            # Don't actually shell out in dry-run
            public_key = "ssh-ed25519 MOCK_PUBLIC_KEY rag-build-mock"
            logger.info("[runpod] (dry-run) would generate SSH key at %s", keypath)
        else:
            subprocess.run(
                ["ssh-keygen", "-t", "ed25519", "-f", str(keypath),
                 "-N", "", "-C", ssh_label],
                check=True,
            )
            public_key = (keypath.parent / f"{keypath.name}.pub").read_text(
                encoding="utf-8"
            ).strip()

        self._ssh_keypath = keypath

        # Register key in account
        key_id = self.client.add_ssh_key(public_key, label=ssh_label)
        self._ssh_key_id = key_id

        # Create Pod with the key
        pod = self.client.create_pod(spec, public_key)
        self._pod_id = pod.pod_id

        return pod, key_id, keypath

    def step_5_to_11_remote_build(
        self,
        pod: Pod,
        keypath: Path,
        *,
        commit_sha: str,
        modalities: tuple[str, ...],
        run_id: str,
        r_phase: str,
        repo_root: Path,
        ssh_executor=None,  # injected for tests; default = paramiko
        lance_max_length: int | None = None,
        lance_batch_size: int | None = None,
        lance_precision: str | None = None,
        lance_colbert_dtype: str | None = None,
        ivf_num_partitions: int | None = None,
        ivf_num_sub_vectors: int | None = None,
        source_mode: str = "git",
        skip_eval: bool = False,
        skip_auto_scp: bool = False,
        remote_command_timeout_s: int = 3600,
    ) -> Path | None:
        """Steps 5-11: clone, install, warm, build, eval, package, download.

        In dry-run mode we *log* what would be executed but don't SSH.
        In live mode we paramiko-SSH each command, then scp back the
        artifact. Returns the local artifact path on success, None on
        failure.
        """
        commands = self._build_remote_commands(
            commit_sha=commit_sha, modalities=modalities,
            run_id=run_id, r_phase=r_phase,
            lance_max_length=lance_max_length,
            lance_batch_size=lance_batch_size,
            lance_precision=lance_precision,
            lance_colbert_dtype=lance_colbert_dtype,
            ivf_num_partitions=ivf_num_partitions,
            ivf_num_sub_vectors=ivf_num_sub_vectors,
            source_mode=source_mode,
            skip_eval=skip_eval,
        )

        if self.dry_run:
            logger.info("[runpod] (dry-run) would execute %d commands on Pod:",
                        len(commands))
            if source_mode == "bundle":
                logger.info(
                    "[runpod] (dry-run) would create git bundle for %s and "
                    "upload it to %s",
                    commit_sha,
                    REMOTE_BUNDLE_PATH,
                )
            for i, cmd in enumerate(commands, 1):
                logger.info("  [%d] %s", i, cmd[:120] + ("…" if len(cmd) > 120 else ""))
            # Synthesize artifact path so finally block doesn't choke
            local_artifact = repo_root / "artifacts" / "rag-full-build" / run_id
            return local_artifact

        # Live SSH execution
        executor = ssh_executor or _ParamikoSshExecutor()
        local_artifact_dir = repo_root / "artifacts" / "rag-full-build" / run_id
        local_artifact_dir.mkdir(parents=True, exist_ok=True)

        # Wait for SSH to be reachable (Pod boot can take 30-90s)
        executor.wait_for_ssh(pod, keypath, timeout_s=180)
        logger.info("[runpod] Pod %s SSH reachable; running %d commands",
                    pod.pod_id, len(commands))

        bundle_path: Path | None = None
        if source_mode == "bundle":
            bundle_path = Path(f"/tmp/{run_id}.bundle")
            try:
                subprocess.run(
                    ["git", "bundle", "create", str(bundle_path), "HEAD"],
                    cwd=repo_root,
                    check=True,
                )
                executor.scp_to_pod(pod, keypath, bundle_path, REMOTE_BUNDLE_PATH)
                logger.info(
                    "[runpod] source bundle uploaded: %s -> %s",
                    bundle_path,
                    REMOTE_BUNDLE_PATH,
                )
            finally:
                if bundle_path is not None:
                    bundle_path.unlink(missing_ok=True)

        for i, cmd in enumerate(commands, 1):
            logger.info("[runpod] step %d/%d: %s", i, len(commands),
                        cmd[:80] + ("…" if len(cmd) > 80 else ""))
            if self._should_run_detached(cmd):
                rc, stdout, stderr = self._run_detached_remote_command(
                    executor,
                    pod,
                    keypath,
                    cmd,
                    run_id=run_id,
                    step_index=i,
                    timeout_s=remote_command_timeout_s,
                )
            else:
                rc, stdout, stderr = executor.run(
                    pod, keypath, cmd, timeout_s=remote_command_timeout_s,
                )
            if rc != 0:
                # Log + raise so finally block still terminates Pod.
                # Print BOTH ends of stderr — Python tracebacks have
                # the type/message at the END, but paramiko's buffer
                # may have trimmed the middle. R1 v1-v7 lesson:
                # stderr[:500] alone shows the call site, not the
                # actual ImportError text we need.
                head = stderr[:600]
                tail = stderr[-2000:] if len(stderr) > 2600 else ""
                logger.error(
                    "[runpod] command failed (rc=%d): %s\n"
                    "stderr head: %s\n%s",
                    rc, cmd[:200], head,
                    f"stderr tail: {tail}" if tail else "(no separate tail; stderr small)",
                )
                raise RuntimeError(f"remote command failed (rc={rc}): {cmd[:80]}")

        # Step 11: scp artifact back
        # The packaging step (step 10 inside commands) wrote to
        # /workspace/repo/artifacts/rag-full-build/{run_id}/cs_rag_index_root.tar.zst
        if skip_auto_scp:
            logger.info(
                "[runpod] skip_auto_scp=True — caller will fetch "
                "/workspace/repo/artifacts/rag-full-build/%s/cs_rag_index_root.tar.zst "
                "directly via system scp. Local artifact dir prepared at: %s",
                run_id, local_artifact_dir,
            )
            local_artifact_dir.mkdir(parents=True, exist_ok=True)
            return local_artifact_dir
        remote_artifact = (
            f"/workspace/repo/artifacts/rag-full-build/{run_id}/"
            f"cs_rag_index_root.tar.zst"
        )
        local_archive = local_artifact_dir / "cs_rag_index_root.tar.zst"
        executor.scp_from_pod(pod, keypath, remote_artifact, local_archive)
        logger.info("[runpod] artifact downloaded: %s", local_archive)

        # Also pull the manifest.json + run.log + environment.json
        for sidecar in ("manifest.json", "run.log", "environment.json",
                        "repo.commit_or_diff.txt"):
            try:
                executor.scp_from_pod(
                    pod, keypath,
                    f"/workspace/repo/artifacts/rag-full-build/{run_id}/{sidecar}",
                    local_artifact_dir / sidecar,
                )
            except Exception as exc:
                logger.warning("[runpod] sidecar %s pull failed: %s", sidecar, exc)

        # Pull eval outputs (R1 v9 lesson: harness skipped these and we
        # had to re-run eval locally because the Pod already terminated).
        # The build commands write eval to /workspace/eval/<phase>_holdout.json.
        if r_phase != "r0":
            eval_dir = local_artifact_dir / "eval"
            eval_dir.mkdir(parents=True, exist_ok=True)
            try:
                executor.scp_from_pod(
                    pod, keypath,
                    f"/workspace/eval/{r_phase}_holdout.json",
                    eval_dir / f"{r_phase}_holdout.json",
                )
            except Exception as exc:
                logger.warning("[runpod] eval %s_holdout.json pull failed: %s",
                               r_phase, exc)

        if r_phase == "r3":
            verification = verify_artifact_dir(
                local_artifact_dir,
                strict_r3=True,
                verify_import=True,
            )
            (local_artifact_dir / "artifact_contract.json").write_text(
                json.dumps(verification, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info("[runpod] strict R3 artifact verified: %s",
                        local_artifact_dir)

        return local_artifact_dir

    @staticmethod
    def _should_run_detached(command: str) -> bool:
        """Run long, noisy remote jobs as Pod-local background tasks."""

        long_markers = (
            "scripts.learning.cli_cs_index_build",
            "scripts.learning.rag.r3.index.lexical_sidecar",
            "scripts.learning.cli_rag_eval",
        )
        return any(marker in command for marker in long_markers)

    def _run_detached_remote_command(
        self,
        executor,
        pod: Pod,
        keypath: Path,
        command: str,
        *,
        run_id: str,
        step_index: int,
        timeout_s: int,
    ) -> tuple[int, str, str]:
        """Start a long command in the Pod and poll status/log files.

        This avoids binding multi-hour R3 builds to one SSH channel. If a
        status poll gets reset, the Pod-local job keeps running and the next
        poll can recover.
        """

        log_dir = "/workspace/rag-build-logs"
        prefix = f"{log_dir}/{run_id}-step-{step_index}"
        log_path = f"{prefix}.log"
        rc_path = f"{prefix}.rc"
        pid_path = f"{prefix}.pid"
        wrapped_command = (
            "set +e; "
            f"{command}; "
            "rc=$?; "
            f"printf '%s\\n' \"$rc\" > {shlex.quote(rc_path)}; "
            "exit \"$rc\""
        )
        start_cmd = (
            f"mkdir -p {shlex.quote(log_dir)} && "
            f"rm -f {shlex.quote(log_path)} {shlex.quote(rc_path)} {shlex.quote(pid_path)} && "
            f"( nohup bash -lc {shlex.quote(wrapped_command)} > {shlex.quote(log_path)} 2>&1 "
            f"< /dev/null & echo $! > {shlex.quote(pid_path)} )"
        )
        rc, stdout, stderr = executor.run(pod, keypath, start_cmd, timeout_s=60)
        if rc != 0:
            return rc, stdout, stderr

        logger.info(
            "[runpod] step %d detached; pid file=%s log=%s",
            step_index,
            pid_path,
            log_path,
        )
        started = time.monotonic()
        poll_interval_s = 60
        last_status = ""
        last_poll_error = ""

        while True:
            if time.monotonic() - started > timeout_s:
                kill_cmd = (
                    f"test -f {shlex.quote(pid_path)} && "
                    f"kill $(cat {shlex.quote(pid_path)}) >/dev/null 2>&1 || true"
                )
                try:
                    executor.run(pod, keypath, kill_cmd, timeout_s=30)
                except Exception:
                    pass
                return (
                    124,
                    "",
                    f"detached remote command timed out after {timeout_s}s; "
                    f"log={log_path}; last_status={last_status}; "
                    f"last_poll_error={last_poll_error}",
                )

            status_cmd = (
                "set +e; "
                f"if [ -f {shlex.quote(rc_path)} ]; then "
                f"echo __RAG_DONE__; cat {shlex.quote(rc_path)}; "
                f"echo __RAG_LOG_TAIL__; tail -n 120 {shlex.quote(log_path)} 2>/dev/null; "
                "else "
                f"if test -f {shlex.quote(pid_path)} && kill -0 $(cat {shlex.quote(pid_path)}) "
                ">/dev/null 2>&1; then "
                f"echo __RAG_RUNNING__; "
                f"echo pid=$(cat {shlex.quote(pid_path)}); "
                f"ps -p $(cat {shlex.quote(pid_path)}) "
                "-o pid=,etime=,pcpu=,pmem=,cmd= 2>/dev/null; "
                "else "
                "echo __RAG_EXITED_WITHOUT_RC__; "
                "fi; "
                f"echo __RAG_LOG_TAIL__; tail -n 40 {shlex.quote(log_path)} 2>/dev/null; "
                "fi"
            )
            try:
                _poll_rc, poll_stdout, poll_stderr = executor.run(
                    pod, keypath, status_cmd, timeout_s=60,
                )
            except Exception as exc:
                last_poll_error = repr(exc)
                if not self._is_pod_listed(pod.pod_id):
                    return (
                        137,
                        "",
                        "detached remote command lost its Pod; "
                        f"pod_id={pod.pod_id}; log={log_path}; "
                        f"last_poll_error={last_poll_error}",
                    )
                logger.warning(
                    "[runpod] step %d status poll failed; detached job may still be running: %s",
                    step_index,
                    exc,
                )
                time.sleep(poll_interval_s)
                continue

            last_status = poll_stdout[-4000:]
            if poll_stderr.strip():
                last_poll_error = poll_stderr[-2000:]
            if "__RAG_DONE__" in poll_stdout:
                done_after = poll_stdout.split("__RAG_DONE__", 1)[1].strip().splitlines()
                try:
                    remote_rc = int(done_after[0].strip())
                except (IndexError, ValueError):
                    remote_rc = 1
                if remote_rc == 0:
                    logger.info("[runpod] step %d detached job completed", step_index)
                    return 0, poll_stdout, poll_stderr
                return remote_rc, "", poll_stdout + poll_stderr
            if "__RAG_EXITED_WITHOUT_RC__" in poll_stdout:
                return (
                    137,
                    "",
                    "detached remote command exited without rc file; "
                    f"log={log_path}; status={poll_stdout[-4000:]}{poll_stderr[-2000:]}",
                )

            logger.info(
                "[runpod] step %d still running; status tail:\n%s",
                step_index,
                poll_stdout[-2000:],
            )
            time.sleep(poll_interval_s)

    def _is_pod_listed(self, pod_id: str) -> bool:
        """Return whether RunPod still reports the Pod as live."""

        try:
            return any(p.pod_id == pod_id for p in self.client.list_pods())
        except Exception as exc:
            logger.warning("[runpod] list_pods failed while checking %s: %s", pod_id, exc)
            return True

    def _build_remote_commands(
        self,
        *,
        commit_sha: str,
        modalities: tuple[str, ...],
        run_id: str,
        r_phase: str,
        lance_max_length: int | None = None,
        lance_batch_size: int | None = None,
        lance_precision: str | None = None,
        lance_colbert_dtype: str | None = None,
        ivf_num_partitions: int | None = None,
        ivf_num_sub_vectors: int | None = None,
        source_mode: str = "git",
        skip_eval: bool = False,
    ) -> list[str]:
        """Sequence of shell commands the Pod will run.

        Captured as a list so dry-run can dump them and tests can assert
        what Pod-side execution looks like without real SSH.

        ``skip_eval=True`` drops Step 9 (cli_rag_eval --ablate) from the
        sequence. Use when the real measurement happens locally via
        cohort_eval — see Phase 6 plan after v7 build hit the 5400s
        SSH-command timeout because cli_rag_eval re-encodes every
        query without caching (4 ablations × 338 q × ~10s ≈ 3.7 h).
        """
        modalities_arg = ",".join(modalities)
        # Build the cs-index-build command with optional bge-m3 tuning
        build_extra = []
        if lance_max_length is not None:
            build_extra.append(f"--lance-max-length {lance_max_length}")
        if lance_batch_size is not None:
            build_extra.append(f"--lance-batch-size {lance_batch_size}")
        if lance_precision is not None:
            build_extra.append(f"--lance-precision {lance_precision}")
        if lance_colbert_dtype is not None:
            build_extra.append(f"--lance-colbert-dtype {lance_colbert_dtype}")
        if ivf_num_partitions is not None:
            build_extra.append(f"--ivf-num-partitions {ivf_num_partitions}")
        if ivf_num_sub_vectors is not None:
            build_extra.append(f"--ivf-num-sub-vectors {ivf_num_sub_vectors}")
        if r_phase == "r3":
            build_extra.append(f"--r3-qrels {shlex.quote(R3_QREL_PATH)}")
        build_extra_str = (" " + " ".join(build_extra)) if build_extra else ""
        build_command = (
            "python -m scripts.learning.cli_cs_index_build "
            f"--backend lance --modalities {modalities_arg} --out /workspace/cs_rag/"
            f"{build_extra_str}"
        )
        strict_package_args = ""
        if r_phase == "r3":
            strict_package_args = " ".join((
                "--strict-r3",
                "--build-command",
                shlex.quote(build_command),
                "--package-lock",
                "\"pyproject.toml:sha256:$(sha256sum pyproject.toml | awk '{print $1}')\"",
                "--qrel-hash",
                f"\"{R3_QREL_PATH}:sha256:$(sha256sum {R3_QREL_PATH} | awk '{{print $1}}')\"",
                "--local-runtime-machine",
                shlex.quote("M4 MacBook Air 13"),
                "--local-runtime-memory-gb",
                "16",
                "--local-runtime-accelerator",
                shlex.quote("Apple Silicon MPS"),
            ))
            strict_package_args = " " + strict_package_args
        # CRITICAL (R1 v1 bug): we used to create our own venv and
        # `pip install -e .`, which dragged in PyPI's *default* torch
        # (latest = 2.11.0+cu130). The Pod's NVIDIA driver is 12.4, so
        # cu130 torch raised "driver too old" → torch.cuda.is_available
        # returned False → bge-m3 ran on CPU at ~12% of GPU speed,
        # blowing the build budget.
        # Fix: install into Pod's system Python, which already has
        # torch + matching CUDA from the runpod/pytorch image. Our
        # extra deps go on top.
        if source_mode == "git":
            source_commands = [
                "git clone https://github.com/DongKey777/woowa-learning-hub.git /workspace/repo",
                f"cd /workspace/repo && git checkout {commit_sha}",
            ]
        elif source_mode == "bundle":
            source_commands = [
                f"git clone {REMOTE_BUNDLE_PATH} /workspace/repo",
                f"cd /workspace/repo && git checkout {commit_sha}",
            ]
        else:
            raise ValueError(f"unknown source mode: {source_mode}")

        return [
            # Step 5: system deps (zstd for packaging, git in case the
            # image is thin)
            "apt-get update -qq && apt-get install -y -qq zstd git",
            *source_commands,
            # Step 6: install our package + extras into Pod's system
            # Python — which has torch+CUDA matching the image's
            # driver. NO venv (avoids cu130-vs-driver12.4 mismatch).
            "cd /workspace/repo && pip install --break-system-packages -e .",
            # FlagEmbedding 1.3.5 + transformers <4.50 — verified
            # against upstream docs (R1 v8 SSH-debug):
            # - FlagEmbedding 1.4.0's runner.py:71 calls
            #   AutoModel.from_pretrained(..., dtype=torch_dtype) which
            #   needs transformers 4.50+, but transformers 4.50+
            #   refactored lazy imports (BloomPreTrainedModel, etc.) in
            #   ways FlagEmbedding 1.4.0's import chain doesn't tolerate
            #   — i.e., 1.4.0 is self-conflicting.
            # - FlagEmbedding 1.3.5's runner.py uses the older
            #   from_pretrained(... trust_remote_code=...) call (no
            #   dtype kwarg), and accepts transformers 4.44.2+.
            # - Pin transformers <4.50 to dodge the lazy-import refactor.
            # Pod's preinstalled torch 2.4.1+cu124 stack stays as-is —
            # CVE-2025-32434 only affects transformers 4.50+, so no
            # torch upgrade is needed. Keeping the original ABI also
            # avoids the torchvision/torchaudio ABI mismatch from R1 v7.
            "cd /workspace/repo && pip install --break-system-packages "
            "lancedb pyarrow \"transformers>=4.44.2,<4.50\" "
            "\"FlagEmbedding==1.3.5\" kiwipiepy",
            # Step 7: warm BGE-M3 weights (skip for FTS-only).
            # R1 v2/v3 hit HF Hub rate limits on community-Pod IPs at
            # ~57-60% download. _warm_bge_m3 retries 5x with 30/60/90/
            # 120s backoff; HF cache accumulates partial downloads
            # across attempts so each retry resumes where the last
            # left off.
            *(["cd /workspace/repo && python -m scripts.remote._warm_bge_m3"]
              if "dense" in modalities or "sparse" in modalities or "colbert" in modalities
              else []),
            # Step 8: build (uses system Python, has CUDA torch)
            f"cd /workspace/repo && {build_command}",
            # R3 serves on learner laptops. Build expensive lexical
            # tokenization once on the remote machine and ship it inside
            # the verified artifact instead of doing full-corpus Kiwi work
            # during the first local query.
            *([
                "cd /workspace/repo && python -m "
                "scripts.learning.rag.r3.index.lexical_sidecar "
                "--index-root /workspace/cs_rag/"
            ] if r_phase == "r3" else []),
            # Step 9: eval (only on r1+; r0 skips). Skipped entirely
            # when skip_eval=True — used to short-circuit the multi-hour
            # cli_rag_eval --ablate path on r3 builds where the real
            # measurement happens locally via cohort_eval against the
            # 200q real-qrel suite. v7 build (commit cca6a4c) hit the
            # 5400s SSH command timeout in this step because each
            # ablation re-encodes every query without caching, so
            # 4 ablations × 338 queries × ~10s each ≈ 3.7 hours.
            *([
                f"cd /workspace/repo && WOOWA_RAG_NO_RERANK=1 "
                f"python -m scripts.learning.cli_rag_eval "
                f"--ablate --embedding-index-root /workspace/cs_rag/ "
                f"--ablation-split holdout "
                f"{' '.join(f'--ablation-modalities {m}' for m in [','.join(modalities[:i+1]) for i in range(len(modalities))])} "
                f"--ablation-out /workspace/eval/{r_phase}_holdout.json"
            ] if r_phase != "r0" and not skip_eval else []),
            # Step 10: package
            f"cd /workspace/repo && python -m scripts.remote.package_rag_artifact "
            f"--index-root /workspace/cs_rag/ --run-id {run_id} --r-phase {r_phase}"
            f"{strict_package_args}",
            # Step 11: caller scp/runpodctl receive (logged separately)
        ]

    def _cleanup(self) -> None:
        """Steps 12: terminate Pod + remove SSH key + delete local key.

        Idempotent — safe to call multiple times (e.g. from finally
        and from signal handler).
        """
        if self._pod_id:
            try:
                self.client.terminate_pod(self._pod_id)
                logger.info("[runpod] terminated pod %s", self._pod_id)
            except Exception as exc:
                logger.error("[runpod] failed to terminate pod %s: %s",
                             self._pod_id, exc)
            finally:
                self._pod_id = None
        if self._ssh_key_id:
            try:
                self.client.remove_ssh_key(self._ssh_key_id)
            except Exception as exc:
                logger.error("[runpod] failed to remove ssh key: %s", exc)
            finally:
                self._ssh_key_id = None
        if self._ssh_keypath:
            try:
                self._ssh_keypath.unlink(missing_ok=True)
                Path(f"{self._ssh_keypath}.pub").unlink(missing_ok=True)
            except Exception:
                pass
            self._ssh_keypath = None

    # --- Main entry ----------------------------------------------------

    def run(self, config: BuildConfig) -> BuildResult:
        """Execute the full 12-step lifecycle. Pod is *guaranteed* to
        terminate even if any step fails."""
        self._install_signal_handlers()
        started_at = datetime.now(timezone.utc)

        # Step 1-2: git state + run_id
        git_state = self.step_1_2_verify_repo_state(config.repo_root)
        run_id = build_run_id(config.r_phase, git_state)
        commit_sha = git_state["commit_sha"]
        source_mode = resolve_source_mode(config.source_mode, git_state)
        if source_mode == "bundle":
            logger.info(
                "[runpod] using git bundle source transfer for commit %s",
                commit_sha[:12],
            )

        result = BuildResult(
            run_id=run_id,
            r_phase=config.r_phase,
            pod_id=None,
            pod_terminated=False,
            artifact_path=None,
            estimated_cost_usd=0.0,
            wallclock_s=0.0,
        )

        hourly = 0.0
        try:
            # Cost pre-check
            hourly = self.client.estimate_hourly_rate(config.gpu_type, config.gpu_cloud)
            est_cost = hourly * (config.max_duration_min / 60.0)
            if est_cost > config.max_cost_usd:
                raise RuntimeError(
                    f"estimated cost ${est_cost:.2f} exceeds --max-cost "
                    f"${config.max_cost_usd:.2f} (rate=${hourly}/hr × {config.max_duration_min}m)"
                )

            spec = PodSpec(
                name=f"rag-{run_id}",
                gpu_type=config.gpu_type,
                gpu_cloud=config.gpu_cloud,
                image=config.image,
                container_disk_gb=config.container_disk_gb,
                min_memory_in_gb=config.min_memory_gb,
                min_vcpu_count=config.min_vcpu_count,
                ports="22/tcp",
            )
            ssh_label = f"rag-build-{run_id}"

            # Step 3-4: pod + ssh
            pod, _key_id, keypath = self.step_3_4_create_pod_with_ssh(spec, ssh_label=ssh_label)
            result.pod_id = pod.pod_id

            # Step 5-11: remote work
            artifact = self.step_5_to_11_remote_build(
                pod, keypath,
                commit_sha=commit_sha,
                modalities=config.modalities,
                run_id=run_id, r_phase=config.r_phase,
                repo_root=config.repo_root,
                lance_max_length=config.lance_max_length,
                lance_batch_size=config.lance_batch_size,
                lance_precision=config.lance_precision,
                lance_colbert_dtype=config.lance_colbert_dtype,
                ivf_num_partitions=config.ivf_num_partitions,
                ivf_num_sub_vectors=config.ivf_num_sub_vectors,
                source_mode=source_mode,
                skip_eval=config.skip_eval,
                skip_auto_scp=config.skip_auto_scp,
                remote_command_timeout_s=max(3600, config.max_duration_min * 60),
            )
            result.artifact_path = artifact

        except Exception as exc:
            logger.error("[runpod] build failed: %s", exc)
            result.error = str(exc)

        finally:
            # Step 12: terminate (skip when --keep-pod for caller-driven cleanup)
            if config.keep_pod:
                logger.info(
                    "[runpod] keep_pod=True — pod %s left RUNNING. "
                    "Caller MUST terminate via runpod.terminate_pod() "
                    "after fetching artifacts.",
                    self._pod_id,
                )
                result.pod_terminated = False
            else:
                self._cleanup()
                result.pod_terminated = True

            # Compute actual wallclock + cost — even on failure (R0 v4
            # bug: was 0.0 on exception because cost calc lived after
            # the failing step).
            ended_at = datetime.now(timezone.utc)
            wallclock_s = (ended_at - started_at).total_seconds()
            result.wallclock_s = wallclock_s
            if result.pod_id is not None:
                # Pod was actually created → real cost
                result.estimated_cost_usd = hourly * (wallclock_s / 3600.0)
            # else: cost cap aborted before Pod creation → cost stays 0

            # Append to cost ledger
            append_cost_ledger(
                config.ledger_path,
                run_id=run_id,
                gpu=config.gpu_type,
                started_at=started_at,
                ended_at=ended_at,
                estimated_cost_usd=result.estimated_cost_usd,
                pod_id=result.pod_id,
                deleted=True,  # cleanup ran
            )
            self._restore_signal_handlers()

        return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--r-phase", required=True, choices=R_PHASES)
    parser.add_argument("--modalities", default=None,
                        help="Comma-separated. Default: from R-phase table.")
    parser.add_argument("--gpu-type", default=None,
                        help="Default: from R-phase table.")
    parser.add_argument("--gpu-cloud", default=None,
                        choices=("community", "secure"),
                        help="Default: from R-phase table.")
    parser.add_argument("--max-cost", type=float, default=10.0,
                        help="Abort if estimated cost exceeds this (default: 10.0)")
    parser.add_argument("--max-duration", type=int, default=180,
                        help="Max minutes of pod life (default: 180)")
    parser.add_argument(
        "--container-disk-gb",
        type=int,
        default=None,
        help="RunPod container disk size in GB (default: 80 for R3 ColBERT builds).",
    )
    parser.add_argument(
        "--min-memory-gb",
        type=int,
        default=None,
        help=(
            "Minimum host RAM (GB) for the build pod. RunPod SDK defaults "
            "to 1 GB which lets the scheduler pick under-spec hosts and "
            "OOM the IVF_PQ index build. Per-R-phase defaults: r3/r4=64, "
            "r2/r1=32, others=16."
        ),
    )
    parser.add_argument(
        "--min-vcpu-count",
        type=int,
        default=None,
        help="Minimum vCPU count (default: 8).",
    )
    parser.add_argument(
        "--skip-eval",
        action="store_true",
        help=(
            "Skip Step 9 (cli_rag_eval --ablate). The in-build ablation "
            "step re-encodes every query without caching, so 4 ablations "
            "× ~338 queries × ~10s ≈ 3.7 hours and trips the 5400s SSH "
            "command timeout. Use this when the real measurement happens "
            "locally via cohort_eval against the 200q real-qrel suite."
        ),
    )
    parser.add_argument(
        "--skip-auto-scp",
        action="store_true",
        help=(
            "Skip the harness's built-in scp_from_pod step. v9 measured "
            "paramiko's SFTPClient.get at ~5x slower than system scp on "
            "a 10 GB transfer; combined with v8b's network drop during "
            "scp, the auto-pull is the most fragile step. Use this with "
            "--keep-pod to fetch the artifact via system scp instead."
        ),
    )
    parser.add_argument(
        "--keep-pod",
        action="store_true",
        help=(
            "Skip the cleanup step's terminate_pod call so the Pod stays "
            "RUNNING after the build completes. Required when using "
            "--skip-auto-scp because the caller needs the Pod alive to "
            "fetch the artifact. Caller MUST manually terminate the pod "
            "afterwards or cost accrues indefinitely."
        ),
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't touch the network; mock the API.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--ledger-path", type=Path,
                        default=Path("state/cs_rag_remote/cost_ledger.json"))
    # bge-m3 build tuning (forwarded to cs-index-build on Pod)
    parser.add_argument("--max-length", type=int, default=None,
                        help="bge-m3 max_length. R1 plan default: 512.")
    parser.add_argument("--batch-size", type=int, default=None,
                        help="bge-m3 encode batch size.")
    parser.add_argument("--precision", choices=("auto", "fp16", "fp32"), default=None,
                        help="bge-m3 precision (auto picks fp16 on GPU).")
    parser.add_argument("--colbert-dtype", choices=("float16", "float32"), default=None)
    parser.add_argument("--ivf-num-partitions", type=int, default=None,
                        help="Forward dense LanceDB IVF num_partitions to cs-index-build.")
    parser.add_argument("--ivf-num-sub-vectors", type=int, default=None,
                        help="Forward dense LanceDB IVF num_sub_vectors to cs-index-build.")
    parser.add_argument(
        "--source-mode",
        choices=SOURCE_MODES,
        default="auto",
        help=(
            "How the Pod receives repo source. auto uses git when the commit "
            "is reachable from origin and bundle when local commits are ahead."
        ),
    )
    parser.add_argument("--verbose", action="store_true")
    return parser


def resolve_defaults(args: argparse.Namespace) -> BuildConfig:
    """Apply per-R-phase defaults for unspecified flags."""
    default_gpu, default_cloud = DEFAULT_GPU_PER_PHASE.get(
        args.r_phase, ("RTX A5000", "community")
    )
    default_modalities = DEFAULT_MODALITIES_PER_PHASE.get(args.r_phase, ("fts",))

    if args.modalities:
        modalities = tuple(m.strip() for m in args.modalities.split(",") if m.strip())
    else:
        modalities = default_modalities

    # R-phase default tuning (plan v5 §3 R1 prescribes max_length=512)
    default_max_length = {"r1": 512, "r2": 512, "r3": 512, "r4": 512}.get(args.r_phase)

    # Per-R-phase RAM floor. Streaming build_lance_index_streaming peaks
    # at ~3-5 GB, but IVF_PQ index creation across 27K+ ColBERT vectors
    # can spike another 5-10 GB depending on LanceDB's sample_rate
    # behaviour. 64 GB on r3 / r4 leaves a comfortable margin without
    # paying for over-provisioned hosts. Smaller phases keep the default.
    default_min_memory = {"r3": 64, "r4": 64, "r2": 32, "r1": 32}.get(args.r_phase, 16)

    return BuildConfig(
        r_phase=args.r_phase,
        modalities=modalities,
        gpu_type=args.gpu_type or default_gpu,
        gpu_cloud=args.gpu_cloud or default_cloud,
        max_cost_usd=args.max_cost,
        max_duration_min=args.max_duration,
        min_memory_gb=getattr(args, "min_memory_gb", None) or default_min_memory,
        min_vcpu_count=getattr(args, "min_vcpu_count", None) or 8,
        container_disk_gb=getattr(args, "container_disk_gb", None) or 80,
        repo_root=args.repo_root,
        ledger_path=args.ledger_path,
        lance_max_length=args.max_length if args.max_length is not None else default_max_length,
        lance_batch_size=args.batch_size,
        lance_precision=args.precision,
        lance_colbert_dtype=args.colbert_dtype,
        ivf_num_partitions=getattr(args, "ivf_num_partitions", None),
        ivf_num_sub_vectors=getattr(args, "ivf_num_sub_vectors", None),
        source_mode=getattr(args, "source_mode", "auto"),
        skip_eval=getattr(args, "skip_eval", False),
        skip_auto_scp=getattr(args, "skip_auto_scp", False),
        keep_pod=getattr(args, "keep_pod", False),
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    config = resolve_defaults(args)

    if args.dry_run:
        client: RunPodApiClient = MockRunPodClient()
        logger.info("[runpod] DRY RUN — no API calls, no Pod created")
    else:
        # Real execution path — task v5-6.
        if not os.environ.get("RUNPOD_API_KEY"):
            logger.error(
                "[runpod] RUNPOD_API_KEY env var not set. "
                "Either `export RUNPOD_API_KEY=\"$(cat ~/.runpod/api_key)\"` "
                "or add --dry-run."
            )
            return 2
        try:
            client = RealRunPodClient()
        except ValueError as exc:
            logger.error("[runpod] failed to initialise SDK: %s", exc)
            return 2
        logger.warning(
            "[runpod] LIVE MODE — Pod creation will incur real cost. "
            "max_cost=$%.2f max_duration=%dm",
            args.max_cost, args.max_duration,
        )

    harness = RunPodHarness(client, dry_run=args.dry_run)
    result = harness.run(config)

    print(json.dumps({
        "run_id": result.run_id,
        "r_phase": result.r_phase,
        "pod_id": result.pod_id,
        "pod_terminated": result.pod_terminated,
        "artifact_path": str(result.artifact_path) if result.artifact_path else None,
        "estimated_cost_usd": round(result.estimated_cost_usd, 4),
        "wallclock_s": round(result.wallclock_s, 2),
        "error": result.error,
        "dry_run": args.dry_run,
    }, ensure_ascii=False, indent=2))

    return 1 if result.error else 0


if __name__ == "__main__":
    raise SystemExit(main())

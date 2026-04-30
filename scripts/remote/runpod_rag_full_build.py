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
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


logger = logging.getLogger(__name__)

R_PHASES = ("r-1", "r0", "r1", "r2", "r3", "r4")

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
    container_disk_gb: int = 20
    repo_root: Path = field(default_factory=lambda: Path.cwd())
    ledger_path: Path = field(default_factory=lambda: Path("state/cs_rag_remote/cost_ledger.json"))


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
    ) -> Path | None:
        """Steps 5-11: clone, install, warm, build, eval, package, download.

        In dry-run mode we *log* what would be executed but don't SSH.
        Returns the local artifact path on success, None on failure.
        """
        commands = self._build_remote_commands(
            commit_sha=commit_sha, modalities=modalities,
            run_id=run_id, r_phase=r_phase,
        )

        if self.dry_run:
            logger.info("[runpod] (dry-run) would execute %d commands on Pod:",
                        len(commands))
            for i, cmd in enumerate(commands, 1):
                logger.info("  [%d] %s", i, cmd[:120] + ("…" if len(cmd) > 120 else ""))
            # Synthesize artifact path so finally block doesn't choke
            local_artifact = repo_root / "artifacts" / "rag-full-build" / run_id
            return local_artifact

        # Real execution path lives in v5-6 (RealRunPodClient + ssh
        # subprocess). For now this method is only called in dry-run.
        raise NotImplementedError(
            "Real (non-dry-run) execution lives in v5-6 task. "
            "Use --dry-run for now."
        )

    def _build_remote_commands(
        self,
        *,
        commit_sha: str,
        modalities: tuple[str, ...],
        run_id: str,
        r_phase: str,
    ) -> list[str]:
        """Sequence of shell commands the Pod will run.

        Captured as a list so dry-run can dump them and tests can assert
        what Pod-side execution looks like without real SSH.
        """
        modalities_arg = ",".join(modalities)
        return [
            # Step 5: clone
            f"git clone https://github.com/DongKey777/woowa-learning-hub.git /workspace/repo",
            f"cd /workspace/repo && git checkout {commit_sha}",
            # Step 6: deps
            f"cd /workspace/repo && python -m venv .venv && .venv/bin/python -m pip install -e .",
            f"cd /workspace/repo && .venv/bin/python -m pip install lancedb pyarrow FlagEmbedding kiwipiepy",
            # Step 7: warm (skip for FTS-only)
            *(["cd /workspace/repo && .venv/bin/python -c 'from FlagEmbedding import BGEM3FlagModel; BGEM3FlagModel(\"BAAI/bge-m3\")'"]
              if "dense" in modalities or "sparse" in modalities or "colbert" in modalities
              else []),
            # Step 8: build
            f"cd /workspace/repo && .venv/bin/python -m scripts.learning.cli_cs_index_build "
            f"--backend lance --modalities {modalities_arg} --out /workspace/cs_rag/",
            # Step 9: eval (only on r1+; r0 skips)
            *([
                f"cd /workspace/repo && .venv/bin/python -m scripts.learning.cli_rag_eval "
                f"--ablate --embedding-index-root /workspace/cs_rag/ "
                f"--ablation-split holdout "
                f"{' '.join(f'--ablation-modalities {m}' for m in [','.join(modalities[:i+1]) for i in range(len(modalities))])} "
                f"--ablation-out /workspace/eval/{r_phase}_holdout.json"
            ] if r_phase != "r0" else []),
            # Step 10: package
            f"cd /workspace/repo && .venv/bin/python -m scripts.remote.package_rag_artifact "
            f"--index-root /workspace/cs_rag/ --run-id {run_id} --r-phase {r_phase}",
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

        result = BuildResult(
            run_id=run_id,
            r_phase=config.r_phase,
            pod_id=None,
            pod_terminated=False,
            artifact_path=None,
            estimated_cost_usd=0.0,
            wallclock_s=0.0,
        )

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
            )
            result.artifact_path = artifact

            # Cost rough estimate (real timing in v5-6)
            ended_at = datetime.now(timezone.utc)
            wallclock_s = (ended_at - started_at).total_seconds()
            result.estimated_cost_usd = hourly * (wallclock_s / 3600.0)
            result.wallclock_s = wallclock_s

        except Exception as exc:
            logger.error("[runpod] build failed: %s", exc)
            result.error = str(exc)

        finally:
            # Step 12: ALWAYS terminate
            self._cleanup()
            result.pod_terminated = True

            # Append to cost ledger
            ended_at = datetime.now(timezone.utc)
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
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't touch the network; mock the API.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--ledger-path", type=Path,
                        default=Path("state/cs_rag_remote/cost_ledger.json"))
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

    return BuildConfig(
        r_phase=args.r_phase,
        modalities=modalities,
        gpu_type=args.gpu_type or default_gpu,
        gpu_cloud=args.gpu_cloud or default_cloud,
        max_cost_usd=args.max_cost,
        max_duration_min=args.max_duration,
        repo_root=args.repo_root,
        ledger_path=args.ledger_path,
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
        # v5-6 will install RealRunPodClient here. For now refuse.
        logger.error(
            "[runpod] real (non-dry-run) execution requires the RealRunPodClient "
            "implementation from task v5-6. Use --dry-run for now."
        )
        return 2

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

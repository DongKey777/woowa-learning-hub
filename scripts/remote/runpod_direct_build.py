"""RunPod r3 build using *system* ssh/scp instead of paramiko.

Why this exists
---------------
``runpod_rag_full_build.py`` orchestrates the full 12-step lifecycle but
its SSH executor uses ``paramiko.exec_command``. Across 13 builds we
observed that paramiko's exec channel is dropped (rc=-1, "exit status
not received") on RunPod community pod sshd's idle-policy hosts, even
with parent-process heartbeat threads writing to stdout every 5 s.
Builds v3, v6, v11, v13b, and others all died this way at step 5/6/7.

This script bypasses paramiko entirely:

* RunPod SDK is used only to create / wait-for-SSH / terminate the pod.
* Each build step is executed by spawning ``ssh -o ServerAliveInterval=15
  -o ServerAliveCountMax=10 -o ConnectTimeout=30 ...`` as a child process.
  The OS keeps the TCP connection alive, stdout/stderr flow directly to
  the controlling terminal (so any host-side stall manifests as a
  visible silence rather than a channel reset), and the SSH session
  inherits the local shell's signal handling.
* The 10 GB artifact is fetched with ``scp`` (which honours
  ServerAliveInterval too) and verified with ``sha256sum`` on both ends.
  No SFTPClient.get → no fragile in-memory chunking.

Behaviour parity with the legacy harness:

* Same 9-step command sequence as ``--skip-eval`` (Step 9 is dropped).
* Same Pod spec: A100 PCIe community by default with ``min_memory_in_gb=96``
  to avoid v10/v12-style host RAM gambling.
* ``--keep-pod`` semantics: pod is kept RUNNING after the build until the
  artifact is verified, then this script terminates it.

Usage::

    python -m scripts.remote.runpod_direct_build \\
        --gpu-type "A100 PCIe" --gpu-cloud community \\
        --min-memory-gb 96 --max-cost 5.0 --max-duration 90 \\
        --batch-size 256 --max-length 256 \\
        --commit-sha <commit>

The build's required commit must be on origin/main. The script
``git rev-parse HEAD`` defaults if --commit-sha is omitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

QREL_PATH = "tests/fixtures/r3_qrels_real_v1.json"


# ---------------------------------------------------------------------------
# Pod lifecycle (RunPod SDK, only for create/terminate)
# ---------------------------------------------------------------------------

@dataclass
class PodHandle:
    pod_id: str
    ssh_host: str
    ssh_port: int
    ssh_key_path: Path


def _ensure_runpod_module():
    try:
        import runpod
    except ImportError as exc:
        raise SystemExit(
            f"runpod SDK not installed: {exc}. "
            f"Run: pip install --break-system-packages runpod"
        )
    api_key = os.environ.get("RUNPOD_API_KEY")
    if not api_key:
        api_key_file = Path.home() / ".runpod" / "api_key"
        if api_key_file.exists():
            api_key = api_key_file.read_text(encoding="utf-8").strip()
    if not api_key:
        raise SystemExit("RUNPOD_API_KEY env var (or ~/.runpod/api_key) not set")
    runpod.api_key = api_key
    return runpod


def _generate_ssh_key() -> Path:
    """Generate a throwaway ed25519 keypair for this build."""
    keydir = Path(tempfile.mkdtemp(prefix="rag-pod-direct-"))
    keypath = keydir / "id_ed25519"
    subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(keypath), "-C", "rag-direct-build"],
        check=True, capture_output=True,
    )
    return keypath


def _install_pubkey_on_runpod(runpod, pubkey_path: Path) -> str:
    """Append the pubkey to the runpod user's authorized_keys via API.
    Returns the pubkey line so we can remove it later."""
    pubkey = pubkey_path.read_text(encoding="utf-8").strip()
    user = runpod.get_user()
    existing = user.get("pubKey", "") or ""
    if pubkey in existing:
        return pubkey
    new_pubkeys = existing + ("\n" if existing and not existing.endswith("\n") else "") + pubkey + "\n"
    runpod.update_user_settings(pubkey=new_pubkeys)
    logger.info("[direct] appended public key to runpod user settings")
    return pubkey


def _remove_pubkey_from_runpod(runpod, pubkey_line: str) -> None:
    """Remove our pubkey from runpod user settings (cleanup so account
    SSH key list doesn't grow unbounded across builds)."""
    try:
        user = runpod.get_user()
        existing = user.get("pubKey", "") or ""
        target = pubkey_line.strip()
        if target not in existing:
            return
        kept = [line for line in existing.splitlines() if line.strip() != target]
        runpod.update_user_settings(pubkey="\n".join(kept))
        logger.info("[direct] removed our public key from runpod user settings")
    except Exception as exc:
        logger.warning("[direct] pubkey cleanup failed: %s", exc)


def _resolve_gpu_type_id(runpod, gpu_display_name: str) -> str:
    """Look up RunPod's internal gpuTypeId for a human-friendly name."""
    for gpu in runpod.get_gpus():
        if gpu.get("displayName") == gpu_display_name:
            return gpu["id"]
    raise SystemExit(f"unknown gpu_type {gpu_display_name!r}")


def create_pod(
    runpod,
    *,
    gpu_type: str,
    gpu_cloud: str,
    image: str,
    container_disk_gb: int,
    min_memory_gb: int,
    min_vcpu_count: int,
    name: str,
    pubkey_path: Path,
    data_center_id: str | None = None,
) -> PodHandle:
    cloud_map = {"community": "COMMUNITY", "secure": "SECURE"}
    gpu_type_id = _resolve_gpu_type_id(runpod, gpu_type)

    create_kwargs = dict(
        name=name,
        image_name=image,
        gpu_type_id=gpu_type_id,
        cloud_type=cloud_map.get(gpu_cloud, "ALL"),
        gpu_count=1,
        container_disk_in_gb=container_disk_gb,
        min_memory_in_gb=min_memory_gb,
        min_vcpu_count=min_vcpu_count,
        ports="22/tcp",
        start_ssh=True,
        support_public_ip=True,
    )
    if data_center_id:
        create_kwargs["data_center_id"] = data_center_id
    result = runpod.create_pod(**create_kwargs)
    pod_id = result.get("id")
    if not pod_id:
        raise SystemExit(f"create_pod returned no id: {result}")
    logger.info("[direct] created pod %s; waiting for SSH endpoint", pod_id)

    deadline = time.time() + 300
    while time.time() < deadline:
        pod = runpod.get_pod(pod_id)
        runtime = pod.get("runtime") or {}
        for port_entry in runtime.get("ports", []) or []:
            if (
                port_entry.get("privatePort") == 22
                and port_entry.get("isIpPublic")
                and port_entry.get("ip")
                and port_entry.get("publicPort")
            ):
                return PodHandle(
                    pod_id=pod_id,
                    ssh_host=port_entry["ip"],
                    ssh_port=int(port_entry["publicPort"]),
                    ssh_key_path=pubkey_path.with_suffix(""),  # private key path
                )
        time.sleep(5)
    raise SystemExit(f"pod {pod_id} did not expose SSH within 300s")


def terminate_pod(runpod, pod_id: str) -> None:
    try:
        runpod.terminate_pod(pod_id)
        logger.info("[direct] terminated pod %s", pod_id)
    except Exception as exc:
        logger.error("[direct] terminate_pod(%s) failed: %s", pod_id, exc)


# ---------------------------------------------------------------------------
# system ssh / scp wrappers
# ---------------------------------------------------------------------------

SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null",
    "-o", "ServerAliveInterval=15",   # send NULL packet every 15s if idle
    "-o", "ServerAliveCountMax=10",   # 10 missed → drop (150 s tolerance)
    "-o", "ConnectTimeout=30",
    "-o", "TCPKeepAlive=yes",
    "-o", "LogLevel=ERROR",           # quiet warnings
]


def ssh_exec(
    pod: PodHandle,
    command: str,
    *,
    timeout_s: int = 7200,
    label: str = "",
) -> int:
    """Run a command on the pod via system ssh, streaming output to our stdout/stderr.

    Returns the remote exit code. Raises subprocess.TimeoutExpired on timeout.
    """
    full_cmd = [
        "ssh", "-i", str(pod.ssh_key_path), "-p", str(pod.ssh_port),
        *SSH_OPTS,
        f"root@{pod.ssh_host}",
        command,
    ]
    if label:
        logger.info("[direct] %s", label)
    logger.debug("[direct] ssh cmd: %s", " ".join(shlex.quote(c) for c in full_cmd))
    started = time.time()
    proc = subprocess.run(full_cmd, timeout=timeout_s)
    elapsed = time.time() - started
    logger.info("[direct] %s rc=%d (elapsed %ds)", label or "ssh", proc.returncode, int(elapsed))
    return proc.returncode


def scp_pull(
    pod: PodHandle,
    remote_path: str,
    local_path: Path,
    *,
    timeout_s: int = 3600,
) -> None:
    """Pull a remote file via system scp."""
    local_path.parent.mkdir(parents=True, exist_ok=True)
    full_cmd = [
        "scp", "-i", str(pod.ssh_key_path), "-P", str(pod.ssh_port),
        *SSH_OPTS,
        f"root@{pod.ssh_host}:{remote_path}",
        str(local_path),
    ]
    logger.info("[direct] scp pull %s → %s", remote_path, local_path)
    subprocess.run(full_cmd, check=True, timeout=timeout_s)


def remote_sha256(pod: PodHandle, remote_path: str) -> str:
    """Compute sha256 of a remote file (server-side, fast)."""
    full_cmd = [
        "ssh", "-i", str(pod.ssh_key_path), "-p", str(pod.ssh_port),
        *SSH_OPTS,
        f"root@{pod.ssh_host}",
        f"sha256sum {shlex.quote(remote_path)}",
    ]
    out = subprocess.check_output(full_cmd, timeout=300, text=True)
    return out.split()[0].strip()


def local_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Build sequence
# ---------------------------------------------------------------------------

def build_remote_commands(
    *,
    commit_sha: str,
    modalities: tuple[str, ...],
    run_id: str,
    lance_max_length: int,
    lance_batch_size: int,
) -> list[tuple[str, str]]:
    """Return list of (label, command) tuples for the pod-side steps."""
    modalities_arg = ",".join(modalities)
    # `--no-release-fetch` is mandatory on RunPod direct_build for the
    # same reason as runpod_rag_full_build (see commit f082ace): without
    # it cli_cs_index_build short-circuits into downloading the *previously
    # published* GitHub release tar.zst, skipping the actual fresh build
    # that this RunPod cycle was paying for. Real silent failure observed
    # 2026-05-06 r3-direct-9a7c218 build — manifest came back with
    # corpus_hash=34b9577 (the OLD release) instead of the new commit's
    # corpus, making cohort_eval against it identical to baseline.
    build_command = (
        f"python -m scripts.learning.cli_cs_index_build "
        f"--backend lance --no-release-fetch --modalities {modalities_arg} "
        f"--out /workspace/cs_rag/ "
        f"--lance-max-length {lance_max_length} "
        f"--lance-batch-size {lance_batch_size} "
        f"--r3-qrels {QREL_PATH}"
    )
    package_command = (
        f"python -m scripts.remote.package_rag_artifact "
        f"--index-root /workspace/cs_rag/ --run-id {run_id} --r-phase r3 "
        f"--strict-r3 "
        f"--build-command {shlex.quote(build_command)} "
        f"--package-lock \"pyproject.toml:sha256:$(sha256sum pyproject.toml | awk '{{print $1}}')\" "
        f"--qrel-hash \"{QREL_PATH}:sha256:$(sha256sum {QREL_PATH} | awk '{{print $1}}')\" "
        f"--local-runtime-machine 'M4 MacBook Air 13' "
        f"--local-runtime-memory-gb 16 "
        f"--local-runtime-accelerator 'Apple Silicon MPS'"
    )
    return [
        ("step 1/7 apt install zstd git",
         "apt-get update -qq && apt-get install -y -qq zstd git"),
        ("step 2/7 git clone",
         "git clone https://github.com/DongKey777/woowa-learning-hub.git /workspace/repo"),
        ("step 3/7 git checkout",
         f"cd /workspace/repo && git checkout {commit_sha}"),
        ("step 4/7 pip install -e .",
         "cd /workspace/repo && pip install --break-system-packages -e ."),
        ("step 5/7 pip install runtime deps",
         "cd /workspace/repo && pip install --break-system-packages "
         "lancedb pyarrow \"transformers>=4.44.2,<4.50\" \"FlagEmbedding==1.3.5\" kiwipiepy"),
        ("step 6/7 warm BGE-M3",
         "cd /workspace/repo && python -m scripts.remote._warm_bge_m3"),
        ("step 7/7 build lance index (streaming + IVF)",
         f"cd /workspace/repo && {build_command}"),
        ("step 8/7 lexical sidecar",
         "cd /workspace/repo && python -m scripts.learning.rag.r3.index.lexical_sidecar "
         "--index-root /workspace/cs_rag/"),
        ("step 9/7 package artifact (zstd compress + sha256)",
         f"cd /workspace/repo && {package_command}"),
    ]


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpu-type", default="A100 PCIe")
    parser.add_argument("--gpu-cloud", default="community", choices=("community", "secure"))
    parser.add_argument("--min-memory-gb", type=int, default=96,
                        help="Host RAM floor (default 96 — bumps over the v10/v12 32-64 GB hosts that OOMed)")
    parser.add_argument("--min-vcpu-count", type=int, default=8)
    parser.add_argument("--container-disk-gb", type=int, default=80)
    parser.add_argument(
        "--data-center-id",
        default=None,
        help="Pin pod to a specific RunPod datacenter (e.g. AP-JP-1 for "
             "Japan, SEA-SG-1 for Singapore). Korea→Japan is ~50ms latency "
             "vs Korea→US ~200ms — measured 9 Mbps over US, expecting "
             "100Mbps+ over Japan. Default None lets RunPod auto-pick.",
    )
    parser.add_argument(
        "--image",
        default="runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
    )
    parser.add_argument("--max-cost", type=float, default=5.0)
    parser.add_argument("--max-duration", type=int, default=90,
                        help="Per-step SSH timeout floor (minutes). default 90.")
    parser.add_argument("--batch-size", type=int, default=256,
                        help="Lance encoder batch_size (default 256, conservative)")
    parser.add_argument("--max-length", type=int, default=256,
                        help="Lance encoder max_length (default 256, ColBERT data ~10 GB)")
    parser.add_argument(
        "--modalities",
        default="fts,dense,sparse,colbert",
        help="Comma-separated modalities (default: full r3 set)",
    )
    parser.add_argument("--commit-sha", default=None,
                        help="Defaults to current local HEAD (must be pushed)")
    parser.add_argument(
        "--local-artifact-dir",
        type=Path,
        default=Path("state/cs_rag_remote/direct"),
        help="Where to drop the pulled tar.zst",
    )
    parser.add_argument("--no-cleanup-on-failure", action="store_true",
                        help="Keep pod RUNNING when a step fails (caller must terminate manually)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be executed and exit")
    args = parser.parse_args(argv)

    if args.commit_sha is None:
        args.commit_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True,
        ).strip()
    short = args.commit_sha[:7]
    run_id = f"r3-direct-{short}-{time.strftime('%Y-%m-%dT%H%MZ', time.gmtime())}"
    logger.info("[direct] run_id=%s commit=%s gpu=%s ram=%dGB",
                run_id, short, args.gpu_type, args.min_memory_gb)

    modalities = tuple(m.strip() for m in args.modalities.split(",") if m.strip())
    commands = build_remote_commands(
        commit_sha=args.commit_sha,
        modalities=modalities,
        run_id=run_id,
        lance_max_length=args.max_length,
        lance_batch_size=args.batch_size,
    )

    if args.dry_run:
        logger.info("[direct] DRY-RUN — would execute %d steps:", len(commands))
        for label, cmd in commands:
            logger.info("  [%s] %s", label, cmd[:120])
        logger.info(
            "[direct] would scp /workspace/repo/artifacts/rag-full-build/%s/cs_rag_index_root.tar.zst",
            run_id,
        )
        return 0

    runpod = _ensure_runpod_module()
    keypath = _generate_ssh_key()
    pubkey = keypath.with_suffix(".pub")
    pod = None
    pubkey_line = None
    started = time.time()
    try:
        pubkey_line = _install_pubkey_on_runpod(runpod, pubkey)
        # Brief settle so RunPod scheduler sees the new key
        time.sleep(3)
        pod = create_pod(
            runpod,
            gpu_type=args.gpu_type,
            gpu_cloud=args.gpu_cloud,
            image=args.image,
            container_disk_gb=args.container_disk_gb,
            min_memory_gb=args.min_memory_gb,
            min_vcpu_count=args.min_vcpu_count,
            name=f"rag-{run_id}",
            pubkey_path=pubkey,
            data_center_id=args.data_center_id,
        )
        # PodHandle's ssh_key_path = the privkey beside pubkey
        pod = PodHandle(pod_id=pod.pod_id, ssh_host=pod.ssh_host,
                        ssh_port=pod.ssh_port, ssh_key_path=keypath)
        logger.info("[direct] SSH endpoint %s:%d (key %s)",
                    pod.ssh_host, pod.ssh_port, keypath)

        # Per-step timeouts (seconds). Generous for the long-running ones.
        per_step_timeout = {
            "step 1/7 apt install zstd git": 600,
            "step 2/7 git clone": 600,
            "step 3/7 git checkout": 120,
            "step 4/7 pip install -e .": 600,
            "step 5/7 pip install runtime deps": 1200,
            "step 6/7 warm BGE-M3": 1800,                     # 30 min for HF download + load
            "step 7/7 build lance index (streaming + IVF)": 4800,  # 80 min cap
            "step 8/7 lexical sidecar": 600,
            "step 9/7 package artifact (zstd compress + sha256)": 1800,
        }

        for label, cmd in commands:
            timeout_s = per_step_timeout.get(label, 1800)
            rc = ssh_exec(pod, cmd, timeout_s=timeout_s, label=label)
            if rc != 0:
                raise SystemExit(f"{label} failed (rc={rc})")

        # Pull artifact via system scp
        remote_artifact = (
            f"/workspace/repo/artifacts/rag-full-build/{run_id}/cs_rag_index_root.tar.zst"
        )
        local_dir = args.local_artifact_dir / run_id
        local_dir.mkdir(parents=True, exist_ok=True)
        local_artifact = local_dir / "cs_rag_index_root.tar.zst"

        logger.info("[direct] computing remote sha256 (~10 GB scan)")
        remote_hash = remote_sha256(pod, remote_artifact)
        logger.info("[direct] remote sha256 = %s", remote_hash)

        # scp timeout 7200s (2h): v14 measured 9 Mbps over Korea↔US
        # so 7.4 GB tar.zst needs ~110 min — 3600s default tripped at
        # 4.6 GB / 7.4 GB. 7200s covers worst-case + retry headroom.
        scp_pull(pod, remote_artifact, local_artifact, timeout_s=7200)

        for sidecar in ("manifest.json", "environment.json",
                        "repo.commit_or_diff.txt", "artifact_contract.json"):
            try:
                scp_pull(
                    pod,
                    f"/workspace/repo/artifacts/rag-full-build/{run_id}/{sidecar}",
                    local_dir / sidecar,
                )
            except subprocess.CalledProcessError:
                logger.warning("[direct] sidecar %s missing; continuing", sidecar)

        logger.info("[direct] computing local sha256")
        local_hash = local_sha256(local_artifact)
        logger.info("[direct] local sha256 = %s", local_hash)

        if local_hash != remote_hash:
            raise SystemExit(
                f"sha256 mismatch — remote={remote_hash} local={local_hash}; "
                f"local file may be incomplete: {local_artifact}"
            )
        logger.info("[direct] sha256 verified ✅")

        artifact_size = local_artifact.stat().st_size
        elapsed_s = int(time.time() - started)
        logger.info(
            "[direct] BUILD COMPLETE — artifact=%s (%.2f GB) elapsed=%ds run_id=%s",
            local_artifact, artifact_size / 1e9, elapsed_s, run_id,
        )
        return 0

    except KeyboardInterrupt:
        logger.error("[direct] interrupted")
        return 130
    except subprocess.TimeoutExpired as exc:
        logger.error("[direct] step timed out: %s", exc)
        return 124
    except SystemExit:
        raise
    except Exception as exc:
        logger.error("[direct] failed: %s: %s", type(exc).__name__, exc)
        return 1
    finally:
        if pod and not args.no_cleanup_on_failure:
            terminate_pod(runpod, pod.pod_id)
        if pubkey_line is not None:
            _remove_pubkey_from_runpod(runpod, pubkey_line)
        # always drop our throwaway key
        try:
            if keypath.exists():
                shutil.rmtree(keypath.parent, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())

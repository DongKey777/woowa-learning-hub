"""Robust BGE-M3 model download/load with retry + wall-clock timeout.

Why this exists
---------------
Two distinct failure modes have been observed on RunPod community Pods:

1. **HF Hub rate limit during download** (R1 v2/v3): the 30-file
   BGE-M3 weights snapshot fails partway. Retry-with-cache is enough
   — HF caches partial downloads and the next retry resumes.

2. **Stall during model load** (R1 v4): `BGEM3FlagModel(...)` after
   download succeeds. The `torch.load(pytorch_model.bin)` step (or
   safetensors mmap) stalls on Pod overlayfs with CPU=0% / GPU=0% /
   process in `hrtimer_nanosleep` indefinitely. A pure-Python retry
   loop never recovers because the failure is a hang, not an
   exception.

Fix: run each warm attempt in a SUBPROCESS with a wall-clock timeout.
On timeout we kill the subprocess group (so child threads die too) and
loop. The HF cache survives, so retries resume from cached state.

Usage
-----
On the Pod:
    python -m scripts.remote._warm_bge_m3

Honors $HF_TOKEN if set. Sets $HF_HUB_DOWNLOAD_TIMEOUT=300 by default
(can be overridden by user).

Returns 0 on success, 1 if all attempts exhausted.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time

MODEL_ID = "BAAI/bge-m3"
MAX_ATTEMPTS = 5
BASE_BACKOFF_S = 30
ATTEMPT_TIMEOUT_S = 900  # 15 min — generous for slow Pods, short
                         # enough to recover from stalls within R1 budget


# python -c expects single-line statements separated by ';'. Multi-line
# 'def' / 'while' bodies don't fit. We keep the child script simple
# (snapshot_download + constructor) and run the SSH-channel keepalive
# from the *parent* process instead — see _start_parent_heartbeat.
_WARM_SCRIPT = (
    "import os; "
    "os.environ.setdefault('HF_HUB_DOWNLOAD_TIMEOUT', '300'); "
    # Phase A: snapshot_download — pure HF cache I/O, no model load.
    # If A succeeds, weights are on disk and any retry path resumes.
    "from huggingface_hub import snapshot_download; "
    "snapshot_download(repo_id={model_id!r}); "
    "print('[warm-child] snapshot_download complete', flush=True); "
    # Phase B: instantiate the constructor (validates GPU + tokenizer).
    "from FlagEmbedding import BGEM3FlagModel; "
    "BGEM3FlagModel({model_id!r}); "
    "print('[warm-child] BGEM3FlagModel constructed', flush=True)"
)


def _start_parent_heartbeat() -> tuple[threading.Thread, list[bool]]:
    """Print a heartbeat to stdout every 5 seconds so the parent SSH
    exec channel sees continuous traffic during the silent model load.

    Why this lives in the parent (not the child subprocess): RunPod
    community pod sshd kills exec channels with no stdout/stderr
    traffic for ~30-60s. The child's snapshot_download phase is noisy
    (30-file progress bars), but the BGEM3FlagModel constructor that
    follows is silent for 30-90s while it loads ~3 GB of weights into
    GPU/RAM. R3 v3 build (commit 1730e56) hit exactly this — rc=-1
    after 47s with 'Fetching 30 files: 100%' on stderr, then nothing.

    Earlier attempt (commit 32e92b5) put the heartbeat *inside* the
    child via 'python -c' — but python -c can't execute multi-line
    'def' / 'while' bodies, so the child died on SyntaxError (rc=1
    after 2s, R3 v4 build). Putting the loop in the parent is the
    right place anyway: it's the parent's stdout that the SSH channel
    is reading.
    """
    alive = [True]

    def _heartbeat() -> None:
        i = 0
        while alive[0]:
            print(f"[warm] parent heartbeat {i}", flush=True)
            time.sleep(5)
            i += 1

    thread = threading.Thread(target=_heartbeat, daemon=True)
    thread.start()
    return thread, alive


def _warm_attempt(model_id: str, timeout_s: int) -> int:
    """Run download + constructor in a subprocess so we can wall-clock
    kill it if it hangs. Inherits stdout/stderr so the parent SSH stream
    sees real-time progress (instead of buffering until completion).

    Returns subprocess returncode, or -1 if killed by timeout.
    """
    cmd = [sys.executable, "-c", _WARM_SCRIPT.format(model_id=model_id)]
    # start_new_session=True so we can signal the whole process group on
    # timeout (kills any child threads/processes the constructor spawns)
    proc = subprocess.Popen(cmd, start_new_session=True)
    try:
        return proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        print(
            f"[warm] HARD TIMEOUT at {timeout_s}s — killing process group {proc.pid}",
            flush=True,
        )
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError) as exc:
            print(f"[warm] killpg failed: {exc}", flush=True)
            proc.kill()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        return -1


def main() -> int:
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "300")
    # Start the SSH-channel keepalive once for the whole main() call.
    # Daemon thread dies when the script returns, so we don't need to
    # explicitly stop it on success — but we flip alive[0]=False as a
    # courtesy for clean log tails.
    _hb_thread, hb_alive = _start_parent_heartbeat()
    last_rc: int | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(
            f"[warm] attempt {attempt}/{MAX_ATTEMPTS} model={MODEL_ID} "
            f"timeout={ATTEMPT_TIMEOUT_S}s",
            flush=True,
        )
        rc = _warm_attempt(MODEL_ID, ATTEMPT_TIMEOUT_S)
        last_rc = rc
        if rc == 0:
            print(f"[warm] success on attempt {attempt}", flush=True)
            hb_alive[0] = False
            return 0
        print(f"[warm] attempt {attempt} failed (rc={rc})", flush=True)
        if attempt < MAX_ATTEMPTS:
            wait_s = BASE_BACKOFF_S * attempt
            print(f"[warm] sleeping {wait_s}s before retry", flush=True)
            time.sleep(wait_s)
    print(f"[warm] all {MAX_ATTEMPTS} attempts failed; last_rc={last_rc}",
          flush=True)
    hb_alive[0] = False
    return 1


if __name__ == "__main__":
    sys.exit(main())

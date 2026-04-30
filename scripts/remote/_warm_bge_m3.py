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
import time

MODEL_ID = "BAAI/bge-m3"
MAX_ATTEMPTS = 5
BASE_BACKOFF_S = 30
ATTEMPT_TIMEOUT_S = 900  # 15 min — generous for slow Pods, short
                         # enough to recover from stalls within R1 budget


_WARM_SCRIPT = (
    "import os; "
    "os.environ.setdefault('HF_HUB_DOWNLOAD_TIMEOUT', '300'); "
    "from FlagEmbedding import BGEM3FlagModel; "
    "BGEM3FlagModel({model_id!r}); "
    "print('[warm-child] BGEM3FlagModel constructed', flush=True)"
)


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
            return 0
        print(f"[warm] attempt {attempt} failed (rc={rc})", flush=True)
        if attempt < MAX_ATTEMPTS:
            wait_s = BASE_BACKOFF_S * attempt
            print(f"[warm] sleeping {wait_s}s before retry", flush=True)
            time.sleep(wait_s)
    print(f"[warm] all {MAX_ATTEMPTS} attempts failed; last_rc={last_rc}",
          flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())

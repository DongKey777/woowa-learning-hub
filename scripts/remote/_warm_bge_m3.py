"""Robust BGE-M3 model download with retry-on-rate-limit (R1 v2/v3 fix).

Why this exists
---------------
RunPod community Pods share egress IPs across many tenants. HuggingFace
Hub applies per-IP rate limits to *unauthenticated* requests. The
BGE-M3 model has 30 files (~2.3 GB total: dense + sparse + colbert
weights, tokenizer, configs); during the simultaneous fetch the IP
hits the limit roughly half-way through. R1 v2 failed at 60% (18/30),
R1 v3 at 57% (17/30). The actual error message gets truncated by
paramiko's stderr buffer so the harness only sees a generic rc=1.

Fix: bash retry isn't enough — we need to (a) cache survives across
retries (HF cache does), (b) backoff long enough for the rate-limit
window to reset, (c) keep stdout flushing so we can SSH-tail and see
progress.

Usage
-----
On the Pod, after `pip install --break-system-packages FlagEmbedding`:
    python -m scripts.remote._warm_bge_m3

Honors $HF_TOKEN if set (raises rate limit dramatically — but we don't
hard-require it; community IP limits are usually enough with backoff).

Returns 0 on success, 1 if all attempts exhausted.
"""

from __future__ import annotations

import os
import sys
import time

MODEL_ID = "BAAI/bge-m3"
MAX_ATTEMPTS = 5
BASE_BACKOFF_S = 30


def _warm_once(model_id: str) -> None:
    from FlagEmbedding import BGEM3FlagModel  # type: ignore[import-untyped]
    BGEM3FlagModel(model_id)


def main() -> int:
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "300")
    last_err: BaseException | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"[warm] attempt {attempt}/{MAX_ATTEMPTS} model={MODEL_ID}",
              flush=True)
        try:
            _warm_once(MODEL_ID)
            print(f"[warm] success on attempt {attempt}", flush=True)
            return 0
        except BaseException as exc:  # noqa: BLE001 — we re-raise/return cleanly
            last_err = exc
            print(f"[warm] attempt {attempt} failed: {type(exc).__name__}: {exc}",
                  flush=True)
            if attempt < MAX_ATTEMPTS:
                wait_s = BASE_BACKOFF_S * attempt  # 30s, 60s, 90s, 120s
                print(f"[warm] sleeping {wait_s}s before retry", flush=True)
                time.sleep(wait_s)
    print(f"[warm] all {MAX_ATTEMPTS} attempts failed; last={last_err!r}",
          flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())

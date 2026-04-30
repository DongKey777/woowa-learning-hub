# R-1: RunPod Capability Probe

**Goal:** Lock down what RunPod actually supports *before* writing the
remote-build wrapper. Plan v5 §H0 wisdom — wrappers built on assumed
capability blow up at runtime when an API doesn't exist or differs from
docs.

**Status (2026-04-30):** docs-only probe. `runpodctl` not installed
locally, no API key provisioned. Capability matrix below is built from
official docs ([runpodctl GitHub](https://github.com/runpod/runpodctl),
[GraphQL spec](https://graphql-spec.runpod.io/),
[Manage Pods docs](https://docs.runpod.io/pods/manage-pods),
[REST API blog](https://www.runpod.io/blog/runpod-rest-api-gpu-management)).

**Live verification pending:** the first `bin/rag-remote-build --dry-run`
will use this matrix; R0 smoke validates with real Pod.

---

## 1. Three Surfaces — runpodctl / GraphQL / REST

RunPod exposes three programmatic surfaces. They overlap; we pick the
right one per task.

| Surface | When to use | Notes |
|---|---|---|
| **`runpodctl` CLI** | Pod create/terminate, file transfer (send/receive with one-time codes), interactive ops | Wraps GraphQL + has its own one-time-code transfer that *doesn't need API key on remote side* |
| **GraphQL API** | Programmatic Pod deploy with full param control, GPU type query, pricing query | Best for our `runpod_rag_full_build.py` — repeatable, scriptable, idempotent |
| **REST API** (newer) | Same as GraphQL but with REST semantics; alternative if GraphQL client not available | `runpod-python` SDK is the path |

**Our default:** GraphQL via `runpod-python` SDK (Python-friendly, full
control). Fall back to `runpodctl` for file transfer (`send`/`receive`
with one-time codes is genuinely useful — sender doesn't need API key
on the remote side).

---

## 2. Capability Matrix (from official docs)

| Capability | runpodctl | GraphQL API | REST API | Required for our flow? |
|---|---|---|---|---|
| Pod create / find-and-deploy-on-demand | ✅ `runpodctl create pod` | ✅ `podFindAndDeployOnDemand` mutation | ✅ | **Yes** (12-step §3) |
| Pod start / stop / terminate | ✅ | ✅ `podTerminate` mutation | ✅ | **Yes** (12-step §12, non-negotiable) |
| Pod list / get details | ✅ | ✅ `pod` query, `myself.pods` | ✅ | **Yes** (orphan cleanup, ledger reconciliation) |
| GPU type query (pricing + availability) | ❌ | ✅ `gpuTypes` query | ✅ | Yes (cost estimate before spawn) |
| SSH key registration | ✅ `runpodctl ssh add-key` | ✅ via `myself.update` mutation | ? | **Yes** (12-step §4) |
| SSH connection (run command on Pod) | ✅ runpodctl wraps it | use raw SSH after key register | use raw SSH | Yes (12-step §6,7,8) |
| File transfer (laptop → Pod) | ✅ `runpodctl send <file>` (one-time code) | ❌ direct (use SSH scp) | ❌ direct | **Yes** (12-step §5 fallback for git bundle/tarball, §10 for artifact download) |
| File transfer (Pod → laptop) | ✅ `runpodctl receive <code>` | ❌ direct (use SSH scp) | ❌ direct | **Yes** (12-step §11) |
| Persistent volume | ✅ `--volumeInGb` flag | ✅ in deploy mutation | ✅ | **No** (ephemeral OK, build runs in single Pod lifetime) |
| Idle pod alerting | ❌ runpodctl ❌ | ❌ direct | ❌ direct | Workaround: poll `pod.lastStatusChange` from our cleanup script |

**Critical finding:** RunPod's CLI `send`/`receive` uses *short
one-time codes*, NOT API keys, for file transfer. This means our git
bundle / source tarball fallback (artifact §"Repo 상태 전송 fallback")
is feasible *without exposing API keys to logs*.

**Critical gap:** Idle pod auto-termination not native. We implement
in `bin/runpod-cleanup` via `pod.lastStatusChange` polling.

---

## 3. SSH Key Lifecycle

**Approach (programmatic, no manual steps):**

```
1. Local: ssh-keygen -t ed25519 -f /tmp/rag-pod-${run_id} -N "" -C "rag-build-${run_id}"
2. API: register the public key under our account
   - GraphQL: mutation { myself { update(input: { sshKey: "..." }) } }
   - or runpodctl: cat /tmp/rag-pod-${run_id}.pub | runpodctl ssh add-key
3. Pod: created with this key as authorized_keys
4. Use: ssh -i /tmp/rag-pod-${run_id} root@${pod.ip} -p ${pod.sshPort}
5. Cleanup: on Pod terminate, also remove the key from account (anti-leak)
```

**Security:**
- Private key written only to `/tmp/rag-pod-${run_id}` (gitignored, ephemeral location)
- Key removed via API after Pod terminate, regardless of build success/fail
- run_id contains commit SHA + timestamp so multiple runs don't collide

**Open question:** does GraphQL `myself.update(input: {sshKey})` overwrite
or append? Must verify in dry-run before assuming. If overwrite, we need
to read existing keys first, append, then write back.

---

## 4. GPU Selection (April 2026 pricing snapshot)

Sources: [RunPod Pricing](https://www.runpod.io/pricing), search results
(specific numbers will drift; capture price at probe time, not at plan
authoring).

| GPU | VRAM | Community $/hr | Secure $/hr | Best for |
|---|---|---|---|---|
| RTX A5000 | 24GB | ~$0.16 | ~$0.29 | **R0, R1, R2** (bge-m3 fp16 fits with margin) |
| RTX 3090 | 24GB | ~$0.20 | ~$0.34 | Alternative if A5000 unavailable |
| RTX A6000 | 48GB | ~$0.49 | ~$0.79 | **R3 ColBERT** (multi-vector storage during build) |
| A100 80GB | 80GB | ~$1.50 | ~$1.99 | R3 fast variant if budget permits |

**Selection rule (recorded in `cost_ledger.json`):**
- R0/R1/R2: prefer Community RTX A5000 ($0.16/hr) — sweet spot for cost/performance
- R3 default: Community RTX A6000 ($0.49/hr) — needed for ColBERT exact-mode build memory peak
- R3 fast: Community A100 80GB ($1.50/hr) — opt-in if user wants ~50% faster (cuts 3hr → 1.5hr)
- R4 reranker eval: A5000 OK (no model loading bottleneck)

---

## 5. Cost Projections (revised vs worklog)

Worklog 970f83a estimated $2-7 per checkpoint with $10 safe budget.
Probe-derived estimates are *lower* — the gap is likely setup
overhead + retries + safety margin. Actual cost recorded post-R0 smoke.

| R-phase | GPU recommendation | Wall time | Probe cost | Worklog cost | Notes |
|---|---|---|---|---|---|
| R0 smoke (FTS only) | A5000 Community | 20-30분 | $0.08-0.15 | "$2 이하" | Setup overhead (clone, deps, warm) eats 10-15분 |
| R1 dense (max_length=512) | A5000 Community | 60-90분 | $0.16-0.45 | $4-7 | First real bge-m3 encode |
| R1 dense (max_length=1024 retry) | A5000 Community | 90-120분 | $0.30-0.60 | +$2-3 | Selective 2-stage |
| R2 +sparse | A5000 Community | 60-90분 | $0.16-0.45 | $4-6 | Full rebuild required |
| R3 +colbert | A6000 Community | 120-180분 | $1.00-1.50 | $8-12 | Multi-vector encode is the heavy part |
| R3 +colbert (A100 fast) | A100 Community | 60-90분 | $1.50-2.25 | — | Optional speed-up |
| R4 reranker eval | A5000 Community | 30분 | $0.08-0.15 | $1-2 | No build, just eval |

**Reconciliation:** I'll record actual cost from R0 smoke (cheapest,
lowest risk) and update this table. If worklog estimates were
intentionally conservative for safety, that's fine — we're
under-running budget by a wide margin which is the right side to err.

---

## 6. Open Questions to Resolve in R0 Live Run

The probe is docs-based. R0 will validate / refute:

| # | Question | Verification step |
|---|---|---|
| 1 | Does `myself.update(sshKey)` overwrite or append? | R0: register one key, list keys, register second, list again |
| 2 | Pod boot time (overhead before code runs) | Time from API call → SSH-ready |
| 3 | HF Hub download speed on Pod (network) | bge-m3 ~5GB cold download time |
| 4 | runpodctl `send`/`receive` reliability for ~5-10 GB tar.zst | R0 ships ~50MB FTS-only artifact; R1 ships full-size and we time it |
| 5 | Pod auto-terminate on idle? Does runpod kill orphan pods we forget? | Confirm in support docs or via experiment |
| 6 | GPU type availability fluctuation | Query `gpuTypes` at multiple times; record availability |
| 7 | API rate limits | Note any 429/throttle observed |

These will populate `docs/runbooks/runpod-capability.md` §"Live Findings"
section after R0 completes.

---

## 7. Implementation Implications for `runpod_rag_full_build.py`

Based on the capability matrix:

```python
# Recommended dependency: runpod-python SDK (GraphQL wrapper)
# pip install runpod

import runpod  # the official SDK

runpod.api_key = os.environ["RUNPOD_API_KEY"]  # never log
ssh_keypath = f"/tmp/rag-pod-{run_id}"

try:
    # 1. Generate SSH key
    subprocess.run(["ssh-keygen", "-t", "ed25519", "-f", ssh_keypath,
                    "-N", "", "-C", f"rag-build-{run_id}"], check=True)

    # 2. Register key (verify overwrite-vs-append behavior in R0)
    public_key = open(f"{ssh_keypath}.pub").read()
    runpod.update_user_settings(ssh_public_keys=[..., public_key])

    # 3. Find cheapest matching GPU
    gpu_types = runpod.get_gpus()  # or graphql query
    selected_gpu = pick_gpu_for_phase(r_phase, gpu_types)

    # 4. Deploy Pod
    pod = runpod.create_pod(
        name=f"rag-{run_id}",
        image_name="runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
        gpu_type_id=selected_gpu["id"],
        gpu_count=1,
        container_disk_in_gb=20,
        volume_in_gb=0,  # ephemeral — no persistent volume needed
        ports="22/tcp",
        # we use SSH key already registered in account
    )
    pod_id = pod["id"]

    # 5-9. SSH-driven build (clone, install, warm, build, eval)
    ssh_into_pod_and_run(pod, ssh_keypath, build_script)

    # 10-11. Package + download artifact
    artifact_path = run_remote_packager(pod, ssh_keypath, run_id)
    download_via_runpodctl_or_scp(pod, ssh_keypath, artifact_path,
                                  local=f"artifacts/rag-full-build/{run_id}/")

finally:
    # 12. ALWAYS terminate pod + remove SSH key (peer rule — non-negotiable)
    try:
        runpod.terminate_pod(pod_id)
    except Exception:
        pass  # log but don't suppress later cleanup
    try:
        # remove the SSH key we registered
        runpod.update_user_settings(ssh_public_keys=remove_key(public_key))
    except Exception:
        pass
    # delete local private key
    Path(ssh_keypath).unlink(missing_ok=True)
    Path(f"{ssh_keypath}.pub").unlink(missing_ok=True)
```

This skeleton is what task v5-5 (`--dry-run` mode) will validate
against mocked API responses. Task v5-6 (real implementation) replaces
the mocks with `runpod.*` calls.

---

## 8. Security Reminders (worklog 970f83a, peer-reaffirmed)

1. **Never commit API keys.** `~/.runpod/api_key` (gitignored) or
   `RUNPOD_API_KEY` env var only.
2. **Never log API keys.** Mask in any error/info output: `***`.
3. **SSH private keys ephemeral.** `/tmp/rag-pod-${run_id}`, deleted
   after Pod terminate (success OR fail).
4. **Pod always terminated.** `try/finally` + signal handler (SIGINT,
   SIGTERM). Defensive: orphan-cleanup script (`bin/runpod-cleanup`)
   detects any pod older than 30 min that we created.
5. **No model cache committed.** HF cache lives on Pod ephemeral disk;
   not synced back. Local cache `~/.cache/huggingface/` already
   gitignored — verify.

---

## 9. Status Summary

✅ **Complete (docs-based):**
- Capability matrix from official docs
- Three-surface choice (GraphQL primary, runpodctl for file transfer, REST as fallback)
- SSH key lifecycle design
- GPU selection per R-phase
- Cost projections (revised — likely under-running worklog estimate)
- Implementation skeleton for `runpod_rag_full_build.py`
- Security reminders

⏳ **Pending (live verification in R0):**
- SSH key add-key behavior (overwrite vs append)
- Actual cost vs projection
- File transfer reliability for ~50MB artifact (R0) and ~1GB+ (R1)
- Pod boot overhead

❌ **Not yet decided:**
- Whether to install `runpodctl` locally now or rely on `runpod-python` SDK only.
  Decision: install both — `runpodctl send/receive` is genuinely useful for
  one-time-code file transfer, and SDK is for programmatic ops.

---

## 10. Sources

- [runpodctl GitHub](https://github.com/runpod/runpodctl)
- [runpodctl docs (main)](https://github.com/runpod/runpodctl/blob/main/docs/runpodctl.md)
- [RunPod Manage Pods](https://docs.runpod.io/pods/manage-pods)
- [GraphQL API Spec](https://graphql-spec.runpod.io/)
- [RunPod GraphQL — Manage Pods](https://docs.runpod.io/sdks/graphql/manage-pods)
- [RunPod Pricing](https://www.runpod.io/pricing)
- [RunPod Pricing Guide 2025 — flexprice](https://flexprice.io/blog/runprod-pricing-guide-with-gpu-costs)
- [SSH Key Management (DeepWiki)](https://deepwiki.com/runpod/runpodctl/6.1-ssh-key-management)
- [SSH & Remote Operations (DeepWiki, runpod-python)](https://deepwiki.com/runpod/runpod-python/5.3-ssh-and-remote-operations)
- [REST API blog](https://www.runpod.io/blog/runpod-rest-api-gpu-management)

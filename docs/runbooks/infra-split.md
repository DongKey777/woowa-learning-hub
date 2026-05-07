# Mode A / Mode B Infrastructure Split — Research Note

**Status**: design study (2026-05-07). No code lives here yet — this
captures the architecture decisions and cost analysis that will drive a
future cycle's implementation. Companion to `feedback_no_local_index_build`,
`feedback_no_colbert_in_index`, `feedback_rag_measurement_metrics` memories.

---

## 1. Why split

The learner machine (M4 MacBook Air 13", 16GB unified memory) is a fixed
budget. Concurrent system-engineering work on the same machine pushes RAM
past 16 GB and triggers swap thrashing — which slows learner-facing
retrieval (BGE-M3 + reranker daemon) and breaks the *learner safety bar*
the wrapper layer worked hard to enforce.

### Measured RAM pressure on the learner machine

| Concurrent activity | Peak RSS | Effect |
|---|---|---|
| Claude Code + BGE-M3 daemon + reranker daemon + IDE + browser | 12-17 GB | learning OK |
| `bin/cohort-eval` (full 200q × R3) | adds 5+ GB → 17-22 GB | swap, retrieval latency 25s → 60s |
| Mass corpus edit (1500+ markdown frontmatter) | adds 1-2 GB IDE indexing | IDE freezes |
| Codex CLI agent in foreground | adds 1-2 GB | tipping point |

→ **Two of these run together = swap event**. Splitting Mode B off the
learner machine restores 4-5 GB of headroom for actual learning work.

---

## 2. The two modes

### Mode A — learner machine (M4)

What lives here:
- Claude Code session (this file's reader)
- `bin/coach-run`, `bin/rag-ask`, `bin/learn-record-code`,
  `bin/learn-test`, `bin/coach-followup`
- `bin/rag-daemon` warm BGE-M3 + reranker (RAM 2-3 GB resident)
- Mission repos under `missions/` and learner state under `state/`

What is **forbidden** here (delegated to Mode B):
- `bin/cohort-eval` (any mode) — 200q × R3 spike
- `bin/rag-remote-build` — wrapper itself is fine, but build artifacts
  download + extraction add 0.5+ GB transient pressure
- Mass corpus mutation (>50 markdown files in one batch)
- `bin/migration-v3-60-start` and other fleet orchestrators
- Threshold sweep, fixture re-baseline, calibration runs

Memory `feedback_no_local_index_build` already forbids `bin/cs-index-build`
on this machine; this runbook generalizes the principle to other heavy
operations.

### Mode B — system engineering machine (separate hardware/instance)

What lives here:
- All Mode-A-forbidden operations above
- Codex CLI agent (ChatGPT Pro) running on the separate machine, not on
  the learner OS
- Corpus authoring, fixture editing, threshold sweep, build trigger,
  measurement, analysis, closing report drafting
- Git origin is the only sync surface back to Mode A

Communication contract: **git push origin main** (or PR) is how Mode B
delivers changes back. The learner machine `git pull` only.

---

## 3. Hardware/infrastructure options

### Option 1: RunPod Network Volume + on-demand pod (this runbook's recommendation)

```
Network Volume (100 GB, AP-JP-1, $0.07/GB/mo = $7/mo)
   └─ /workspace persists git repo + .venv + HF model cache
        ↓ mount
   ┌─────────────────────────────────────────┐
   │ CPU pod (8 vCPU 32 GB, $0.052/hr)       │ corpus edit / git / Codex agent
   │ spawn 30-60 min/mo on demand            │
   └─────────────────────────────────────────┘
   ┌─────────────────────────────────────────┐
   │ GPU pod (L40S $0.99/hr, A6000 $0.79/hr) │ build + cohort_eval
   │ spawn 5-10 hr/mo on demand              │
   └─────────────────────────────────────────┘
```

Monthly cost: **$15-25** depending on cycle frequency. Latency from
Korea ~50 ms (Tokyo DC).

### Option 2: Cloud VM 24/7

| Vendor / Plan | RAM | Mo cost | Latency from Korea |
|---|---|---|---|
| Hetzner CCX23 (AMD EPYC 4 vCPU) | 16 GB | ~$36 | EU 250 ms |
| AWS Lightsail 16GB | 16 GB | $80 | KR/JP 30-50 ms |
| RunPod CPU pod 24/7 | 32 GB | $37 | JP 50 ms |

### Option 3: Home mini-PC (one-time)

Mac mini M4 16GB ≈ ₩800,000 (~$600). Break-even vs RunPod Network Volume
≈ 30-36 months. Best long-term ROI if Mode B work is sustained.

### Option 4: Spare laptop already on hand

Zero marginal cost. Wake-on-LAN + ssh, treat as headless. Only viable if
the hardware truly exists and is otherwise idle.

---

## 4. Tooling that is ready today vs. future work

| Component | Status | Notes |
|---|---|---|
| `bin/cohort-eval --mode {production,eval}` | ✅ shipped (cycle3) | Mode B usable now |
| `bin/rag-remote-build` | ✅ shipped | Mode B usable now |
| `bin/_rag_env.sh` 6-var contract | ✅ shipped | env enforced |
| `docs/runbooks/rag-perf-loop.md` | ✅ shipped | 9-step closed loop |
| `.github/workflows/rag-perf-loop.yml` 3 light CI jobs | ✅ shipped | runs on push/PR |
| RunPod Network Volume bootstrap script | ❌ future | wrapper + first-run init |
| `bin/runpod-dev-up` / `down` (CPU pod spawn) | ❌ future | one-shot ssh-ready pod |
| Codex agent prompt for Mode B work | ❌ future | system-research persona |
| Mode A enforcement (refuse forbidden ops) | ❌ future | wrappers detect host = learner machine and refuse |
| GitHub Actions self-hosted GPU runner / RunPod webhook | ❌ future | nightly cohort_eval automation |

---

## 5. Migration path (when actually implementing)

1. **Provision Network Volume** in RunPod console (AP-JP-1, 100 GB).
   Document the volume id in `state/cs_rag_remote/network_volume.json`
   so wrappers can find it.
2. **Bootstrap pod** (one-time, ~$0.05): spawn CPU pod with the volume
   mounted at `/workspace`, run `git clone`, `pip install -e .`,
   `python -m scripts.remote._warm_bge_m3` (downloads BGE-M3 into
   `/workspace/.cache/huggingface`). Terminate.
3. **Write `bin/runpod-dev-up` and `bin/runpod-dev-down`** — thin
   wrappers around RunPod GraphQL that spawn / terminate the dev CPU pod
   reusing the volume. Print the SSH endpoint on stdout so the operator
   can ssh in.
4. **Add Mode A guard** to `bin/cohort-eval`, `bin/rag-remote-build`,
   `bin/migration-v3-60-start`: if `$WOOWA_ALLOW_MODE_B_OPS != 1` and
   the host is identified as the learner machine (`uname -m` plus a
   sentinel file), refuse with a one-line Korean message pointing here.
5. **Update memory** with the rule "Mode A wrappers refuse forbidden ops
   unless `WOOWA_ALLOW_MODE_B_OPS=1` is set explicitly" and add the
   recovery instructions.
6. **Trial period**: run one full perf cycle (corpus edit → build →
   measure → closing report) entirely from Mode B. Compare cost and
   learner-machine RAM usage delta to current state.
7. **CI promotion**: once Mode B is stable, wire GitHub Actions
   `workflow_dispatch` to trigger a RunPod pod via API and run
   `bin/cohort-eval --mode production` automatically on each main push,
   commenting back the cycle delta on the PR.

---

## 6. Open research questions

1. **Where does Codex CLI agent run?** ChatGPT Pro Codex documented to
   run on the user's local machine; need to confirm whether it can ssh
   into the Mode B pod and treat it as the working tree (otherwise the
   agent's RAM still lands on the learner machine, defeating the split).
2. **Network Volume cross-DC** — can a single volume serve both
   AP-JP-1 (latency-friendly for Korea) and a US/EU DC if RunPod runs
   out of capacity in JP? Today the volume is DC-pinned. Acceptable for
   single-user research; revisit if the project scales.
3. **Determinism** — cohort_eval results have ±0.5 pp variance run-to-run
   even on identical inputs. Pinning torch seeds + reranker seed should
   reduce this; future cycle to land seed control before declaring a
   cycle's measurement final.
4. **GitHub Actions self-hosted runner economics** — RunPod webhook vs.
   keeping a small self-hosted runner alive. The webhook path costs only
   the pod time; the runner path adds the runner's own keep-alive. Need
   real measurements before deciding.

---

## 7. Decision now (cycle3 closing)

- Mode A / Mode B split is **defined** but **not enforced** yet.
- Continue using current single-machine workflow until either (a) a
  measured swap event happens or (b) we want to enable nightly
  cohort_eval automation. Either trigger justifies the implementation
  cost in step 5 above.
- Memory `feedback_mode_a_b_split_research_note` linked from
  `MEMORY.md` keeps this design accessible to future sessions.

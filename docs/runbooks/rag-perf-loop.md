# RAG Performance Closed-Loop Runbook

**Goal**: standardize the corpus → build → measure → analyze → improve loop
so each cycle produces comparable metrics and the learner-facing system
stays in a known good state. Codifies the discoveries from the
2026-05-07 cycle3 measurement (commit c12a0f5 / index-v1.0.0-corpus@c12a0f5).

---

## 1. Two Measurement Environments — Don't Mix Them

The earlier baseline 91.5% (cycle1 / fde6e49) was measured under
`WOOWA_RAG_REFUSAL_THRESHOLD=0.4`. The learner-facing wrapper
(`bin/_rag_env.sh`) ships with `WOOWA_RAG_REFUSAL_THRESHOLD=off`. Comparing
a production-mode measurement against the 91.5% baseline gives a
~9pp false-regression on `corpus_gap_probe` alone.

| Environment | Use for | Env override | Expected `corpus_gap_probe` outcome |
|---|---|---|---|
| **production** | Learner-facing reality | `WOOWA_RAG_REFUSAL_THRESHOLD=off` | `silent_failure` (intentional — best-effort answer over refusal) |
| **eval** | Baseline-comparable measurement | `WOOWA_RAG_REFUSAL_THRESHOLD=0.4` | `tier_downgraded` (sentinel `<sentinel:no_confident_match>` emit) |

Both modes share:
- `WOOWA_RAG_R3_ENABLED=1`, `WOOWA_RAG_R3_RERANK_POLICY=always`,
  `WOOWA_RAG_R3_FORBIDDEN_FILTER=1`, `HF_HUB_OFFLINE=1`,
  `WOOWA_RAG_PERSONALIZATION_ENABLED=1` (post-c12a0f5: concept_id 99% coverage)
- `--use-reformulated-query` (matches AI session contract — AI emits
  reformulated queries on the learner's behalf)

`bin/cohort-eval --mode production|eval` enforces both, so do not call
`python -m scripts.learning.rag.r3.eval.cohort_eval` directly unless you
intentionally want a degraded-env measurement.

---

## 2. The Closed Loop

```
[1] Corpus change           → commit + push to main
        ↓
[2] Build (RunPod)          bin/rag-remote-build --r-phase r3
                              --gpu-cloud secure --data-center-id AP-JP-1
                              --modalities fts,dense,sparse        ← no ColBERT
                              --max-cost 5
        ↓
[3] Publish (GitHub Release) python -m scripts.remote.publish_index_release
                              --run-id <run> --tag-prefix index-v1.0.0
                              --artifact-root artifacts/rag-full-build
        ↓
[4] Fetch (learner hub)      bin/cs-index-build --strict-release-fetch
                                ↓
                              also bump config/rag_models.json:
                                index.corpus_hash + index.row_count
                                r3_sidecars.lexical.{corpus_hash,row_count,document_count}
        ↓
[5] Measure (M1 + M2)        bin/cohort-eval --mode eval         (baseline-compare)
                              bin/cohort-eval --mode production   (learner reality)
        ↓
[6] Analyze (per-cohort)     compare per_cohort.pass_rate against
                              cycle1 baseline (eval-mode 91.5% is authoritative)
                                ↓
                              cohort regression > -3pp →
                                inspect baseline-pass-then-fail per_query
                                  → categorize:
                                    (a) fixture-corpus drift (new doc not registered)
                                    (b) genuine retrieval miss
                                    (c) measurement-env mismatch
        ↓
[7] Improve                  - (a) tests/fixtures/r3_qrels_real_v1.json:
                                   add neighbor in acceptable_paths
                              - (b) add corpus doc / fix frontmatter
                              - (c) re-run with proper env via bin/cohort-eval
        ↓
[8] Re-measure               loop to [5]
        ↓
[9] Closing report           reports/rag_eval/cycle<N>_closing_report.md
                              record overall + per-cohort + lever attribution
```

---

## 3. Cohort Regression Triage Pattern

When a cohort drops > 3pp vs cycle1 baseline, run this triage with the
cycle's `cohort_*_<ts>.json` report:

```python
import json
b = json.load(open('reports/rag_eval/migration_v3_60_baseline_cycle2_fde6e49_20260506T151935Z.json'))
c = json.load(open('reports/rag_eval/<cycle3_report>.json'))

cohort = 'symptom_to_cause'  # or whichever regressed
b_q = {q['query_id']: q for q in b['per_query'] if q['cohort_tag']==cohort}
c_q = {q['query_id']: q for q in c['per_query'] if q['cohort_tag']==cohort}

regressed = [qid for qid in b_q if b_q[qid]['pass_status'] and not c_q[qid]['pass_status']]
for qid in regressed:
    print(qid)
    print('  primary:', b_q[qid].get('primary_paths'))
    print('  cycle3 final top-3:', c_q[qid].get('final_paths', [])[:3])
```

If `cycle3 final top-3` contains a new doc that is a *reasonable* answer
but not in `primary_paths` / `acceptable_paths`, that's case (a) —
extend the fixture row rather than the corpus.

---

## 4. Build Spec Defaults (learner-env-fit)

| Spec | Value | Reason |
|---|---|---|
| `--modalities` | `fts,dense,sparse` | ColBERT raises tar.zst 130 MB → 17 GB; M4 16GB swap-thrash risk on `state/cs_rag/` page cache |
| `--gpu-cloud` | `secure` | community pool can spawn partner machines with throttled NICs (3 Mbps observed); secure spawns RunPod-vetted infra |
| `--data-center-id` | `AP-JP-1` | Tokyo, ~50ms RTT from Korea vs ~200ms US |
| `--max-cost` | `5` USD | typical secure H100 SXM × 30 min ≈ $1.5 |

Local M4 build is forbidden — see `feedback_no_local_index_build` memory.
ColBERT is forbidden as default — see `feedback_no_colbert_in_index` memory.

---

## 5. Reference Artifacts

- Build wrapper: `bin/rag-remote-build` → `scripts/remote/runpod_rag_full_build.py`
- Publish: `scripts/remote/publish_index_release.py` (writes `release` block in `config/rag_models.json`)
- Fetch: `scripts/learning/rag/release_fetch.py` (reads `config/rag_models.json.release`)
- Measure: `bin/cohort-eval` → `scripts/learning/rag/r3/eval/cohort_eval.py`
- Calibrate refusal threshold: `scripts/learning/rag/r3/eval/calibrate_refusal_threshold.py`
- Production env: `bin/_rag_env.sh`
- Authoritative baseline: `reports/rag_eval/migration_v3_60_baseline_cycle2_fde6e49_20260506T151935Z.json`
  (cycle1 fde6e49, eval-mode 91.5% / 200q × 6 cohort)

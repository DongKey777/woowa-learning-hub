# RAG Index Rollback Runbook

Purpose: restore a working CS RAG index if the R3 LanceDB v3 production
index or its runtime fails.

The learner does not run these commands. An AI session runs them and reports
one Korean status line per step.

## Current production state (cycle3 — c12a0f5)

- `state/cs_rag/` — R3 LanceDB v3 production index
  - **28,773 chunks**, fts + dense + sparse modalities (no ColBERT — learner-env-fit)
  - built from commit `c12a0f5` corpus (1552 v3 frontmatter backfill +
    88 new mission_bridge/drill/router docs, 99% concept_id coverage)
  - GitHub release: `index-v1.0.0-corpus@c12a0f5` (142.65 MB tar.zst,
    sha256 `0d83455b…e8441`)
  - search runtime: `r3.search.search()` with reformulated_query
    + post-rerank forbidden_filter + Phase 9.2 personalization
    (wrapper default ON via `bin/_rag_env.sh`)
- `state/cs_rag_archive/v2_current_20260502T1101Z` — legacy v2 fallback (sqlite
  + dense.npz, paraphrase-multilingual-MiniLM-L12-v2)
- **Learner baseline (M2 production)**: active 5-cohort weighted avg **92.7%**
  (`reports/rag_eval/learner_baseline_c12a0f5_production.json`,
  `reports/rag_eval/cycle3_closing_report.md`)
  - corpus_gap_probe is intentional silent_failure in production env
    (refusal threshold off — learner-safety preferred over refusal)
- Historical reference: cycle1 fde6e49 91.5% — measurement env not recorded
  in metadata, so do not direct-compare; eval-mode threshold pitfalls
  documented in `feedback_rag_measurement_metrics` memory

## Preconditions

- Current repository root: `/Users/idonghun/IdeaProjects/woowa-learning-hub`
- Legacy archive exists under `state/cs_rag_archive/v2_<stamp>/`
  - current rollback archive: `state/cs_rag_archive/v2_current_20260502T1101Z`
  - older historical archive: `state/cs_rag_archive/v2_20260501T063445Z`
- Current production index is `state/cs_rag/`
- No `bin/coach-run` or `bin/rag-ask` process is actively using the index

Check active processes:

```bash
pgrep -fl 'coach-run|rag-ask|cs-index-build'
```

If any long-running index/search process is active, wait for it to finish
before moving directories.

## Restore Steps

Set a timestamp in the shell running the restore:

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
```

Move the failed R3/Lance index aside:

```bash
mv state/cs_rag "state/cs_rag_failed_r3_${STAMP}"
```

Restore the archived v2 directory. Replace `<v2_stamp>` with the archive
directory chosen for rollback:

```bash
mv "state/cs_rag_archive/v2_current_20260502T1101Z" state/cs_rag
```

Verify the restored manifest is legacy v2:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path

manifest = json.loads(Path("state/cs_rag/manifest.json").read_text(encoding="utf-8"))
assert manifest.get("index_version") == 2, manifest
assert Path("state/cs_rag/index.sqlite3").exists()
assert Path("state/cs_rag/dense.npz").exists()
print("legacy_v2_manifest_ok")
PY
```

Run offline smoke:

```bash
HF_HUB_OFFLINE=1 bin/rag-ask "트랜잭션 격리수준"
HF_HUB_OFFLINE=1 bin/rag-ask "Spring Bean이 뭐야"
HF_HUB_OFFLINE=1 bin/rag-ask "What is dependency injection"
```

Expected smoke result:

- JSON output is produced for all three commands.
- `decision.tier` is 1 or 2 for each learning prompt.
- `hits.meta.rag_ready` is `true`.
- each prompt has at least three returned hits in `hits.by_fallback_key`.

## If Restore Smoke Fails

1. Do not delete `state/cs_rag_failed_r3_<stamp>`.
2. Run `bin/doctor`.
3. Run `bin/cs-index-build --backend legacy --mode full`.
   `bin/cs-index-build` without `--backend legacy` now rebuilds LanceDB v3.
4. Re-run the three offline smoke commands.
5. Record the failure and recovery notes in a worklog under `docs/worklogs/`.

## Post-Restore Notes

- The failed R3/Lance index directory is intentionally preserved for diagnosis.
- Do not retry cutover until the cutover comparator and smoke failure are both
  explained.
- After a successful restore, `integration.augment()` should report
  `meta.backend == "legacy"` because the restored manifest has
  `index_version == 2`.
- Update `config/rag_models.json` only if rollback becomes the new production
  state. For short incident rollback, keep the R3 lock and record the incident
  in `docs/worklogs/`.

## Forward Rebuild (when R3 production needs to be re-created)

If `state/cs_rag/` is missing or corrupt and a learner session needs the R3
baseline back, rebuild from commit `029ec00` corpus + the runtime config the
closing report measured:

```bash
HF_HUB_OFFLINE=0 bin/cs-index-build  # default backend lance, modalities fts+dense+sparse
```

Local M4 build is feasible (~25 min, 16GB RAM tolerable with streaming).
RunPod L40S build is faster (~9 min end-to-end including scp from
Sweden / Taiwan datacenter; documented as `scripts/remote/runpod_direct_build.py`).

After rebuild, smoke:

```bash
WOOWA_RAG_R3_ENABLED=1 \
WOOWA_RAG_R3_RERANK_POLICY=always \
WOOWA_RAG_R3_FORBIDDEN_FILTER=1 \
HF_HUB_OFFLINE=1 \
python -m scripts.learning.rag.r3.eval.cohort_eval \
  --qrels tests/fixtures/r3_qrels_real_v1.json \
  --out /tmp/rebuild_smoke.json \
  --index-root state/cs_rag \
  --catalog-root knowledge/cs/catalog \
  --top-k 5 --mode full \
  --use-reformulated-query
```

Expected (cycle3 c12a0f5 production-mode): active 5-cohort weighted avg ≥ 0.92
(M2 measured 0.927; corpus_gap_probe silent_failure is intentional in
production env, exclude from active comparison). Use `bin/cohort-eval --mode production`
for the standard learner-fit measurement; the explicit `python -m ...cohort_eval`
form above is for emergency rebuild verification only.
Significant deviation → corpus or code regression, not just rebuild noise.

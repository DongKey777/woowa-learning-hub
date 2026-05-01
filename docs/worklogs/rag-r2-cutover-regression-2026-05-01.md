# RAG R2 Cutover Regression Gate - 2026-05-01

## Summary

Phase 1 cutover regression gate failed. The current legacy v2 stack still beats the preserved Lance R2 holdout report on the Korean rewritten holdout split.

Decision: do not proceed to production cutover without an explicit user decision to either delay cutover, adjust the gate, or run additional Lance tuning first.

## Inputs

- Legacy report: `reports/rag_eval/cutover_legacy_v2_20260501T035453Z.json`
- Lance R2 report: `reports/rag_eval/r2_holdout_ko_rewritten.json`
- Comparison summary: `reports/rag_eval/cutover_legacy_vs_lance_20260501T035453Z.json`
- Holdout fixture source: `tests/fixtures/cs_rag_golden_queries_ko_rewritten_applied.json`
- Holdout split: `split_tune_holdout(..., seed=20240202)`, 101 queries

Note: the plan draft suggested `bin/rag-eval --ablate` for the legacy v2 measurement, but the current CLI implements `--ablate` as a LanceDB v3-only path. For the legacy v2 side, I generated a temporary holdout fixture with the same split and ran `bin/rag-eval --baseline-only`.

## Commands

```bash
.venv/bin/python -c "<generate /private/tmp/cutover_holdout_ko_rewritten_applied.json from the holdout split>"
env HF_HUB_OFFLINE=1 bin/rag-eval --baseline-only \
  --fixture /private/tmp/cutover_holdout_ko_rewritten_applied.json \
  --out-quality reports/rag_eval/cutover_legacy_v2_20260501T035453Z.json \
  --out-machine state/cs_rag/cutover_legacy_v2_20260501T035453Z_machine.json

.venv/bin/python scripts/learning/cli_rag_cutover_compare.py \
  --legacy reports/rag_eval/cutover_legacy_v2_20260501T035453Z.json \
  --lance reports/rag_eval/r2_holdout_ko_rewritten.json \
  --out reports/rag_eval/cutover_legacy_vs_lance_20260501T035453Z.json
```

## Legacy V2 Result

- Stack: SQLite/NPZ v2, `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, mmarco reranker
- Query count: 101
- primary nDCG@10 micro: 0.9717
- primary nDCG@10 category macro: 0.9624
- recall micro: 0.9950
- forbidden rate micro: 0.0
- hard regression: 96/101 passed
- failed query ids: `repo_vs_dao`, `spring_tx_propagation`, `mysql_deadlock_lock_ordering`, `projection_watermark_dual_run`, `beginner_network_keepalive_primer`

## Cutover Comparison

Global primary nDCG macro:

| stack | primary nDCG macro |
|---|---:|
| legacy v2 | 0.9624 |
| Lance R2 | 0.8103 |
| delta | -0.1522 |

Gate:

| check | result |
|---|---|
| global gate | fail |
| bucket gate | fail |
| regression count | 8 |
| forbidden rate | unchanged globally, 0.0 to 0.0 |

Largest bucket regressions:

| axis | bucket | legacy | Lance R2 | delta |
|---|---:|---:|---:|---:|
| language | ko | 1.0000 | 0.1579 | -0.8421 |
| category | design-pattern | 0.9764 | 0.3161 | -0.6603 |
| category | software-engineering | 1.0000 | 0.6667 | -0.3333 |
| category | spring | 0.9815 | 0.7223 | -0.2593 |
| language | en | 1.0000 | 0.7517 | -0.2483 |
| language | mixed | 0.9592 | 0.7632 | -0.1959 |
| category | database | 0.9432 | 0.8026 | -0.1406 |
| category | operating-system | 1.0000 | 0.8770 | -0.1230 |

## Interpretation

The Lance R2 stack remains useful as a measured research candidate, but this gate says it is not ready to replace the current legacy production stack as-is. The weak spots match the prior plan risk profile: Korean queries and design-pattern retrieval still need targeted work.

Because the gate failed, Phase 3 cutover is blocked. Reasonable next options:

1. Delay cutover and run Phase 4 Korean/contextual improvements first.
2. Run Phase 2 IVF sweep as a performance/quality tuning experiment, but do not treat it as production approval unless the same cutover gate passes afterward.
3. Revisit the gate design if the legacy fixture is considered too biased toward the old stack, then document the changed criterion before re-running.

## Phase 2 IVF Sweep

Summary JSON: `reports/rag_eval/r2_ivf_sweep_20260501T0401.json`

Method:

- Extracted the preserved R2 LanceDB artifact from `artifacts/rag-full-build/r2-6eb3764-2026-04-30T1436/cs_rag_index_root.tar.zst`.
- Copied the index root per variant under `/private/tmp/rag_ivf_sweep_20260501T0401/`.
- Dropped/recreated only `dense_vec_idx` for each IVF variant; no corpus re-encoding.
- Ran `bin/rag-eval --ablate` on the same Korean rewritten holdout fixture, `fts,dense,sparse`, 101 queries.

Local measurement note: this machine resolved the evaluator device to CPU. Treat latency as local relative evidence, not production MPS/GPU evidence.

| variant | status | primary nDCG macro | local CPU P95 | failures | disk |
|---|---|---:|---:|---:|---:|
| current `256/64` | measured | 0.8898 | 720.8 ms | 16 | 348.1 MB |
| official-start `7/128` | measured | 0.9288 | 821.6 ms | 14 | 352.7 MB |
| smaller-ann `16/96` | invalid | n/a | n/a | n/a | n/a |
| adjusted smaller-ann `16/128` | measured | 0.9288 | 837.3 ms | 14 | 352.7 MB |
| exact-scan | measured | 0.9341 | 932.3 ms | 12 | 348.1 MB |

Findings:

- `16/96` is not a valid LanceDB IVF_PQ setting for BGE-M3 because `num_sub_vectors` must divide the 1024-dimensional vector size.
- `7/128` and `16/128` produced identical quality in this run.
- `exact-scan` had the best quality, especially Korean bucket, but the slowest local CPU P95.
- No measured local variant passed the strict `P95 <= 500ms` gate. Also, Phase 1 cutover gate already failed against legacy v2.

Decision:

- Keep `config/rag_models.json` unchanged.
- Keep production lock at current `256/64` until a target-environment latency run and the legacy-to-Lance cutover gate both pass.

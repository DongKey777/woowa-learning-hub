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

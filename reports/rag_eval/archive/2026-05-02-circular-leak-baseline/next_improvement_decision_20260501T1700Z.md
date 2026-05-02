# RAG Next Improvement Decision - 2026-05-01

## Scope

Current production is LanceDB v3 with `BAAI/bge-m3`, default runtime modalities `fts,dense,sparse`, and the existing `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` reranker. This report records the post-cutover decision and the next improvement track without rolling back the cutover.

## Decision

Keep LanceDB v3 in production and set the default modality policy to `fts,dense,sparse`.

Sparse produced no quality lift over `fts,dense` on holdout and added latency, but the production default remains `fts,dense,sparse` so the R2 artifact is exercised as shipped. The immediate next work is sparse bottleneck/effect analysis. If sparse stays neutral or negative, reduce it with category-gated sparse or sparse weight adjustment.

Do not swap the local CPU reranker now: `mixedbread-ai/mxbai-rerank-base-v1` was slow enough to abort on both holdout and the 14-query failure cohort, so it is not a practical local production candidate.

Retrieval boundary diagnosis remains relevant, but it comes after the sparse analysis. The strongest current signal is that Lance is usually retrieving the right family, while sparse has not yet shown whether its cost is buying rank movement.

## Evidence

| Run | primary nDCG@10 | graded nDCG@10 | MRR | hit@10 | recall@10 | hard gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Legacy v2 archive holdout | 0.9890 | 0.9824 | 0.9901 | 1.0000 | 0.9950 | 99/101 passed |
| Lance v3 production holdout | 0.9135 | 0.9126 | 0.9307 | 0.9406 | 0.9191 | 91/101 passed |

Latency on this local CPU run:

| Runtime | warm p50 | warm p95 | cold start |
| --- | ---: | ---: | ---: |
| Legacy v2 | 352.5 ms | 499.1 ms | 15.9 s |
| Lance v3 | 467.7 ms | 637.7 ms | 14.8 s |

Lance modality ablation on holdout:

| Modalities | primary nDCG macro | p95 warm | hard failures |
| --- | ---: | ---: | ---: |
| `fts` | 0.9143 | 463.1 ms | 11 |
| `fts,dense` | 0.9416 | 677.5 ms | 10 |
| `fts,dense,sparse` | 0.9416 | 736.7 ms | 10 |

Failure-14 top-10 comparison:

| Metric | Legacy v2 | Lance v3 |
| --- | ---: | ---: |
| primary at rank 1 | 12/14 | 10/14 |
| primary in top 10 | 14/14 | 13/14 |
| primary missing top 10 | 0/14 | 1/14 |
| top-1 cross-category | 0/14 | 1/14 |

Lance failure classes in the 14-query cohort:

| Class | Count |
| --- | ---: |
| pass rank 1 | 10 |
| same-category wrong rank | 3 |
| top-1 cross-category | 1 |

This revises the earlier root-cause framing: cross-category retrieval exists, but it is not the dominant current failure mode after the production cutover and reranker-hook hardening. The dominant issue is narrower ranking/coverage drift around projection freshness and related read-model documents.

## Artifacts

- `reports/rag_eval/next_lance_v3_holdout_20260501T1700Z.json`
- `state/cs_rag/next_lance_v3_holdout_20260501T1700Z_machine.json`
- `reports/rag_eval/next_legacy_v2_holdout_20260501T1700Z.json`
- `state/cs_rag/next_legacy_v2_holdout_20260501T1700Z_machine.json`
- `reports/rag_eval/next_lance_modality_ablation_holdout_20260501T1700Z.json`
- `reports/rag_eval/next_lance_failure14_baseline_20260501T1700Z.json`
- `state/cs_rag/next_lance_failure14_baseline_20260501T1700Z_machine.json`
- `reports/rag_eval/next_failure14_top10_diagnosis_20260501T1700Z.json`

## Next Work Package

1. Run sparse bottleneck/effect analysis comparing `fts,dense` against `fts,dense,sparse`:
   - stage-level runtime (`lance_query_encode`, `lance_sparse_rescore`, `lance_rerank`, total warm P95),
   - per-query rank deltas for primary paths,
   - category/language buckets where sparse helps, hurts, or has no effect.
2. Decide sparse treatment from evidence:
   - keep global sparse if it gives measurable rank lift within the latency budget,
   - move to category-gated sparse if gains are localized,
   - reduce sparse weight if the candidate set is right but sparse perturbation is noisy,
   - remove sparse from default only if it stays neutral/negative after the above checks.
3. Then inspect the four Lance failure-14 non-rank-1 cases:
   - `projection_freshness_intro_fully_korean_primer_vs_rebuild_backfill_compare`
   - `projection_lag_budgeting`
   - `mysql_deadlock_lock_ordering`
   - `spring_tx_propagation`
4. For each, decide whether the problem is candidate absence, candidate present but under-ranked, or qrel too strict.
5. Implement the smallest targeted fix:
   - projection/read-model anchor or alias strengthening if the right doc is absent,
   - category/family-aware boost if the right doc is present but under-ranked,
   - qrel expansion only when multiple docs are genuinely equivalent for the learner intent.
6. Re-run holdout and the failure-14 diagnosis. A valid next gate is:
   - Lance holdout primary nDCG@10 improves without new hard failures,
   - failure-14 primary-at-1 improves from 10/14 to at least 12/14,
   - p95 does not regress by more than 10% from the current Lance v3 CPU baseline.

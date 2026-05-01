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

## Same-Query Diagnostic Comparison

Summary JSON: `reports/rag_eval/cutover_legacy_vs_lance_same_queries_20260501T0625Z.json`

Failure taxonomy: `reports/rag_eval/cutover_failure_taxonomy_20260501T0625Z.json`

Why this exists:

- The original Phase 1 comparison remains the historical cutover gate report.
- For per-query diagnosis, I also compared legacy v2 against the later
  same-code Lance baseline
  `reports/rag_eval/r2_korean_terms_w00_holdout_20260501T0450Z.json`.
- That later Lance report has the same 101 query IDs as
  `reports/rag_eval/cutover_legacy_v2_20260501T035453Z.json`, so it is safer
  for failure taxonomy and next-experiment targeting.

Result:

| check | value |
|---|---:|
| query id intersection | 101 / 101 |
| legacy primary nDCG macro | 0.9624 |
| Lance same-code primary nDCG macro | 0.9103 |
| delta | -0.0521 |
| gate pass | false |
| bucket regressions | 7 |
| regressed per-query items | 14 |
| Lance zero-primary items | 10 |

Largest same-query bucket regressions:

| bucket | delta |
|---|---:|
| database | -0.2779 |
| software-engineering | -0.2500 |
| en | -0.2125 |
| ko | -0.1429 |
| spring | -0.1000 |
| design-pattern | -0.0781 |
| mixed | -0.0570 |

Top repeated expected paths in the failure taxonomy:

1. `contents/design-pattern/read-model-staleness-read-your-writes.md` (4)
2. `contents/database/transaction-isolation-basics.md` (3)
3. `contents/spring/spring-request-pipeline-bean-container-foundations-primer.md` (1)
4. `contents/software-engineering/dao-vs-query-model-entrypoint-primer.md` (1)
5. `contents/spring/spring-transactional-basics.md` (1)

Decision:

- This does not unblock cutover. It only narrows the next Option A work:
  improve repeated failing primer/anchor targets, then rerun the same-query
  comparison.

## Option A Anchor Alias Pilot On Failure Fixture

Fixture: `tests/fixtures/cs_rag_cutover_failure_queries.json`

Summary JSON: `reports/rag_eval/cutover_failure_anchor_comparison_20260501T0640Z.json`

Change:

- Added learner shortform `retrieval-anchor-keywords` aliases to repeated
  expected-path docs from the same-query failure taxonomy:
  - `contents/design-pattern/read-model-staleness-read-your-writes.md`
  - `contents/database/transaction-isolation-basics.md`
  - `contents/spring/spring-request-pipeline-bean-container-foundations-primer.md`
  - `contents/software-engineering/dao-vs-query-model-entrypoint-primer.md`
  - `contents/spring/spring-transactional-basics.md`
  - `contents/database/connection-pool-basics.md`
  - `contents/design-pattern/projection-lag-budgeting-pattern.md`
  - `contents/spring/transactional-deep-dive.md`

Validation:

```bash
HF_HUB_OFFLINE=1 bin/rag-eval --fast \
  --fixture tests/fixtures/cs_rag_cutover_failure_queries.json

.venv/bin/python -m pytest \
  tests/unit/test_corpus_loader.py \
  tests/unit/test_corpus_lint.py \
  -q
```

Measurement:

| metric | delta |
|---|---:|
| primary nDCG micro | +0.0000 |
| category macro | +0.0000 |
| language macro | +0.0000 |
| database bucket | +0.0000 |
| design-pattern bucket | +0.0000 |
| spring bucket | +0.0000 |
| software-engineering bucket | +0.0000 |
| hard regression failures | 0 |
| local CPU P95 | +8.5 ms |

Decision:

- Keep the aliases because they document real learner shortforms and did not
  regress the sampled failure fixture.
- Do not count this as a cutover unblocker. Alias-only corpus edits did not
  change ranking on the 14-query failure fixture.
- The next Option A lever likely needs stronger document structure, qrel/gate
  review, or generated query rewrites tied to these exact failure prompts.

## Option A Exact Failure Query-Rewrite Pilot

Summary JSON: `reports/rag_eval/cutover_failure_rewrite_comparison_20260501T0715Z.json`

Method:

- Wrote 14 `query-rewrite-v1.output` sidecars under
  `/private/tmp/woowa_cutover_failure_rewrites_20260501T0715/query_rewrites`.
- Each sidecar targets one prompt from
  `tests/fixtures/cs_rag_cutover_failure_queries.json`.
- Evaluated the same sampled corpus as the anchor-alias pilot with
  `WOOWA_RAG_QUERY_REWRITE_ROOT` pointing at that temp sidecar root.
- Verified the Lance search path consumed rewrite candidates with debug output:
  `query_candidate_kinds=['original','rewrite','rewrite']`.

Measurement versus the post-anchor baseline
`reports/rag_eval/cutover_failure_anchor_after_20260501T0640Z.json`:

| metric | delta |
|---|---:|
| primary nDCG micro | +0.0000 |
| category macro | +0.0000 |
| language macro | +0.0000 |
| database bucket | +0.0000 |
| design-pattern bucket | +0.0000 |
| spring bucket | +0.0000 |
| software-engineering bucket | +0.0000 |
| hard regression failures | 0 |
| local CPU P95 | +275.0 ms |

Decision:

- Do not enable exact-prompt query rewrites by default.
- The eval path consumed the sidecars, but the sampled failure fixture showed
  no ranking improvement and substantially higher local CPU latency.
- This reinforces that the next useful work is not query-candidate plumbing;
  it is qrel/gate review or stronger document-level structure for the
  repeated failing primers.

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

## Phase 4 Chunk Context Pilot

Summary JSON: `reports/rag_eval/chunk_context_pilot_comparison_20260501T0416Z.json`

Artifacts:

- Contract doc: `docs/ai-behavior-contracts.md`
- Wrapper: `bin/chunk-context-prepare`
- Skill: `skills/woowa-chunk-context/SKILL.md`
- Fixture: `tests/fixtures/cs_rag_multi_turn_queries.json`
- No-context report: `reports/rag_eval/chunk_context_pilot_noctx_20260501T0416Z.json`
- With-context report: `reports/rag_eval/chunk_context_pilot_withctx_20260501T0416Z.json`

Method:

- Prepared `chunk-context-v1.input` artifacts for 5 pilot docs.
- Wrote 130 matching `chunk-context-v1.output` sidecars under `state/cs_rag/chunk_contexts`.
- Rebuilt a 5-document sampled Lance index twice: once with `WOOWA_CHUNK_CONTEXT_ROOT` pointing at an empty directory, once with the generated sidecars.
- Ran `bin/rag-eval --sampled-ablate` on 10 Korean/mixed multi-turn prompts, modalities `fts,dense,sparse`.

Commands:

```bash
bin/chunk-context-prepare \
  --path contents/data-structure/applied-data-structures-overview.md \
  --path contents/design-pattern/strict-list-canary-metrics-rollback-triggers.md \
  --path contents/system-design/README.md \
  --path contents/security/duplicate-cookie-vs-proxy-login-loop-bridge.md \
  --path contents/security/cookie-rejection-reason-primer.md

env HF_HUB_OFFLINE=1 WOOWA_CHUNK_CONTEXT_ROOT=/private/tmp/woowa_chunk_context_empty \
  bin/rag-eval --sampled-ablate \
  --fixture tests/fixtures/cs_rag_multi_turn_queries.json \
  --sample-root /private/tmp/woowa_chunk_context_eval_noctx \
  --sample-categories data-structure,design-pattern,system-design,security \
  --sample-extra-docs-per-category 0 \
  --sample-force-rebuild \
  --ablation-split full \
  --ablation-modalities fts,dense,sparse \
  --ablation-out reports/rag_eval/chunk_context_pilot_noctx_20260501T0416Z.json \
  --top-k 10 \
  --device auto

env HF_HUB_OFFLINE=1 \
  bin/rag-eval --sampled-ablate \
  --fixture tests/fixtures/cs_rag_multi_turn_queries.json \
  --sample-root /private/tmp/woowa_chunk_context_eval_withctx \
  --sample-categories data-structure,design-pattern,system-design,security \
  --sample-extra-docs-per-category 0 \
  --sample-force-rebuild \
  --ablation-split full \
  --ablation-modalities fts,dense,sparse \
  --ablation-out reports/rag_eval/chunk_context_pilot_withctx_20260501T0416Z.json \
  --top-k 10 \
  --device auto
```

Measurement:

| run | primary nDCG micro | category macro | language macro | ko bucket | mixed bucket | CPU P95 |
|---|---:|---:|---:|---:|---:|---:|
| no sidecar | 0.2000 | 0.2500 | 0.2083 | 0.1667 | 0.2500 | 395.3 ms |
| with sidecar | 0.2000 | 0.2500 | 0.2083 | 0.1667 | 0.2500 | 397.9 ms |
| delta | +0.0000 | +0.0000 | +0.0000 | +0.0000 | +0.0000 | +2.7 ms |

Interpretation:

- `chunk-context-v1` is wired into dense embedding text and Lance `search_terms`, and malformed sidecars fall back to raw chunk text.
- This small sampled pilot did not move rankings. The result is useful as wiring evidence, not as production approval.
- The weak multi-turn pilot fixture suggests context generation alone is insufficient; the next likely lever is query rewriting or higher-quality per-chunk context generation before a full R2 rebuild.

## Phase 4.3 Korean Query-Side `search_terms` Candidate

Summary JSON: `reports/rag_eval/r2_korean_terms_query_candidate_20260501T0450Z.json`

Artifacts:

- Code: `scripts/learning/rag/searcher.py`
- Unit coverage: `tests/unit/test_lance_search_path.py`
- Weight `0.0` same-code baseline: `reports/rag_eval/r2_korean_terms_w00_holdout_20260501T0450Z.json`
- Weight `0.7` report: `reports/rag_eval/r2_korean_terms_holdout_20260501T0450Z.json`
- Weight `0.3` report: `reports/rag_eval/r2_korean_terms_w03_holdout_20260501T0450Z.json`

Method:

- Added a query-side analogue of Lance `search_terms`: Korean prompts can be
  analyzed with `kiwipiepy` and searched as a separate FTS candidate.
- Fused the raw-prompt FTS ranking and the Korean terms FTS ranking with
  weighted RRF before dense/sparse fusion.
- Left the feature opt-in through `WOOWA_KOREAN_FTS_TERMS_WEIGHT`; default
  weight is `0.0` because the same-code A/B did not show ranking lift.
- Reused the extracted R2 `current_256_64` index under
  `/private/tmp/rag_ivf_sweep_20260501T0401/current`.
- Ran holdout ablation on the Korean rewritten applied fixture, split seed
  `20240202`, modalities `fts,dense,sparse`.
- Important correction: the initial comparison against the Phase 2 IVF sweep
  baseline mixed code vintages. The valid feature delta is the same-code
  `WOOWA_KOREAN_FTS_TERMS_WEIGHT=0` baseline versus opt-in weights.

Commands:

```bash
env HF_HUB_OFFLINE=1 WOOWA_KOREAN_FTS_TERMS_WEIGHT=0.3 \
  bin/rag-eval --ablate \
  --fixture tests/fixtures/cs_rag_golden_queries_ko_rewritten_applied.json \
  --embedding-index-root /private/tmp/rag_ivf_sweep_20260501T0401/current \
  --ablation-split holdout \
  --ablation-seed 20240202 \
  --ablation-modalities fts,dense,sparse \
  --ablation-out reports/rag_eval/r2_korean_terms_w03_holdout_20260501T0450Z.json \
  --device auto
```

Same-code measurement:

| run | primary nDCG macro | primary nDCG micro | ko bucket | failures | local CPU P95 |
|---|---:|---:|---:|---:|---:|
| weight `0.0` baseline | 0.9103 | 0.8766 | 0.8571 | 13 | 692.6 ms |
| weight `0.3` | 0.9103 | 0.8766 | 0.8571 | 13 | 810.0 ms |
| weight `0.7` | 0.9103 | 0.8766 | 0.8571 | 13 | 759.0 ms |
| feature delta | +0.0000 | +0.0000 | +0.0000 | 0 | local latency noise only |

Decision:

- Do not enable by default.
- Keep the opt-in code path as instrumentation for future experiments, but do
  not count it as a Phase 4 quality improvement.
- The next useful lever is not weight tuning; it needs either better Korean
  anchors in the indexed corpus or structural query rewrites that introduce
  terms missing from the existing Lance FTS fields.

## Phase 4.2 Korean Retrieval Anchor Pilot

Summary JSON: `reports/rag_eval/anchor_pilot_strict_list_comparison_20260501T0520Z.json`

Change:

- Added Korean entries to the existing `retrieval-anchor-keywords` field in
  `knowledge/cs/contents/design-pattern/strict-list-canary-metrics-rollback-triggers.md`.
- The other four pilot docs already had Korean or mixed-language retrieval
  anchors in the same supported field.
- No new frontmatter field was introduced.

Validation:

```bash
.venv/bin/python -m pytest tests/unit/test_corpus_loader.py tests/unit/test_corpus_lint.py -q

env HF_HUB_OFFLINE=1 WOOWA_CHUNK_CONTEXT_ROOT=/private/tmp/woowa_chunk_context_empty \
  bin/rag-eval --sampled-ablate \
  --fixture tests/fixtures/cs_rag_multi_turn_queries.json \
  --sample-root /private/tmp/woowa_anchor_eval_strict_list_20260501T0520 \
  --sample-categories data-structure,design-pattern,system-design,security \
  --sample-extra-docs-per-category 0 \
  --sample-force-rebuild \
  --ablation-split full \
  --ablation-modalities fts,dense,sparse \
  --ablation-out reports/rag_eval/anchor_pilot_strict_list_20260501T0520Z.json \
  --top-k 10 \
  --device auto
```

Measurement versus the prior no-sidecar pilot
`reports/rag_eval/chunk_context_pilot_noctx_20260501T0416Z.json`:

| metric | delta |
|---|---:|
| primary nDCG micro | +0.0000 |
| category macro | +0.0000 |
| language macro | +0.0000 |
| ko bucket | +0.0000 |
| mixed bucket | +0.0000 |
| hard regression failures | 0 |

Decision:

- Keep the Korean anchors. They complete the 5-doc Phase 4.2 pilot without
  measured sampled-regression.

## Phase 4 Structural Query-Rewrite Sidecar Pilot

Summary JSON: `reports/rag_eval/query_rewrite_pilot_comparison_20260501T0610Z.json`

Change:

- Added `WOOWA_RAG_QUERY_REWRITE_ROOT` as an eval/runtime override for
  `query-rewrite-v1` sidecar storage.
- This keeps the production default unchanged while allowing temp LanceDB
  sampled indexes outside `state/cs_rag` to consume AI-written rewrite
  candidates.
- Added unit coverage proving a temp Lance eval index reads rewrite candidates
  from the override storage and batch-encodes them with the original query.

Validation:

```bash
.venv/bin/python -m pytest \
  tests/unit/test_lance_search_path.py \
  tests/unit/test_query_rewrites_reader.py \
  tests/unit/test_query_rewrite_contract.py \
  -q

env HF_HUB_OFFLINE=1 \
  WOOWA_CHUNK_CONTEXT_ROOT=/private/tmp/woowa_chunk_context_empty \
  WOOWA_RAG_QUERY_REWRITE_ROOT=/private/tmp/woowa_query_rewrite_pilot_20260501T0610/query_rewrites \
  bin/rag-eval --sampled-ablate \
  --fixture tests/fixtures/cs_rag_multi_turn_queries.json \
  --sample-root /private/tmp/woowa_query_rewrite_eval_20260501T0610 \
  --sample-categories data-structure,design-pattern,system-design,security \
  --sample-extra-docs-per-category 0 \
  --sample-force-rebuild \
  --ablation-split full \
  --ablation-modalities fts,dense,sparse \
  --ablation-out reports/rag_eval/query_rewrite_pilot_20260501T0610Z.json \
  --top-k 10 \
  --device auto
```

Measurement versus the prior anchor/no-context pilot
`reports/rag_eval/anchor_pilot_strict_list_20260501T0520Z.json`:

| metric | delta |
|---|---:|
| primary nDCG micro | +0.0000 |
| category macro | +0.0000 |
| language macro | +0.0000 |
| ko bucket | +0.0000 |
| mixed bucket | +0.0000 |
| hard regression failures | 0 |
| local CPU P95 | +91.1 ms |

Decision:

- Do not enable a default rewrite sidecar requirement from this pilot.
- Keep the env override and unit coverage because they make future structural
  rewrite experiments measurable against temp LanceDB indexes.

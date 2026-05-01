# RAG v6.2 Cutover Decision Brief - 2026-05-01

Objective: `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md`

## Current Decision

Do not run Phase 3 production cutover yet.

The v6.2 Definition of Done requires production cutover, but the same plan
allows cutover only after the Phase 1 cutover gate and Phase 2 production gate
pass. Both gates currently fail.

## Blocking Evidence

Phase 1 comparison:

- Report: `reports/rag_eval/cutover_legacy_vs_lance_20260501T035453Z.json`
- Legacy v2 primary nDCG macro: `0.9624408810`
- Lance R2 primary nDCG macro: `0.8102647781`
- Delta: `-0.1521761029`
- Gate pass: `false`
- Bucket gate pass: `false`
- Regression count: `8`

Phase 2 IVF sweep:

- Report: `reports/rag_eval/r2_ivf_sweep_20260501T0401.json`
- Decision: `keep_current_256_64`
- Production gate pass: `false`
- Passing variants: `[]`

Same-query diagnostic:

- Report:
  `reports/rag_eval/cutover_legacy_vs_lance_same_queries_20260501T0625Z.json`
- Failure taxonomy:
  `reports/rag_eval/cutover_failure_taxonomy_20260501T0625Z.json`
- Query ID intersection: `101/101`
- Lance same-code primary nDCG macro: `0.9102958204`
- Delta versus legacy: `-0.0521450606`
- Gate pass: `false`
- Bucket regressions: `7`
- Lance zero-primary items: `10`

Runtime state:

- `state/cs_rag/manifest.json` is still legacy v2:
  - `index_version=2`
  - `embed_model=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
  - `embed_dim=384`
  - `row_count=27155`
- `state/cs_rag_archive/` does not exist.
- `docs/worklogs/rag-r2-cutover-2026-05-01.md` does not exist.
- `config/rag_models.json` has R2 candidate metadata, but not the final
  top-level Phase 3 production lock fields required by the plan
  (`artifact_sha256`, `ivf`).

## Work Already Completed

- Phase 0 merge and test work is complete and pushed.
- Phase 1 cutover regression reports are tracked.
- Phase 2 IVF sweep is tracked.
- Phase 4 minimum chunk-context pilot is complete.
- Additional Phase 4 experiments were measured:
  - Korean retrieval-anchor pilot:
    `reports/rag_eval/anchor_pilot_strict_list_comparison_20260501T0520Z.json`
  - Korean query-side `search_terms` candidate:
    `reports/rag_eval/r2_korean_terms_query_candidate_20260501T0450Z.json`
  - Structural `query-rewrite-v1` sidecar pilot:
    `reports/rag_eval/query_rewrite_pilot_comparison_20260501T0610Z.json`
- Same-query failure taxonomy was generated to target the next Option A work:
  `reports/rag_eval/cutover_failure_taxonomy_20260501T0625Z.json`
- Option A anchor-alias pilot was measured:
  `reports/rag_eval/cutover_failure_anchor_comparison_20260501T0640Z.json`
  - sampled failure fixture quality delta: `+0.0000`
  - cutover gate impact: none
- Option A exact failure query-rewrite pilot was measured:
  `reports/rag_eval/cutover_failure_rewrite_comparison_20260501T0715Z.json`
  - sampled failure fixture quality delta: `+0.0000`
  - local CPU P95 delta: `+275.0 ms`
  - cutover gate impact: none

None of the additional Phase 4 pilots produced a sampled quality lift large
enough to unblock production cutover.

## Decision Options

### Option A - Delay Cutover

Keep legacy v2 as production. Continue targeted Korean/contextual retrieval
work until a new Lance candidate passes the same cutover gate.

Next work:

- Improve corpus anchors or qrels beyond the 5-doc pilot.
- Run a new Lance evaluation against the full holdout.
- Re-run `scripts/learning/cli_rag_cutover_compare.py`.

### Option B - Change The Gate

If the current gate is judged too biased toward the legacy stack, document a
new acceptance rule before any cutover attempt.

Required before cutover:

- Write the revised gate and rationale.
- Re-run legacy and Lance reports under the revised rule.
- Commit the new comparison report.

### Option C - Risky Cutover Approval

Proceed with Phase 3 despite failed gates only if explicitly approved by the
user/product owner.

Required if approved:

- Use the plan's unique `state/cs_rag_next_<stamp>` staging directory.
- Verify the R2 artifact SHA-256:
  `1fed316557c86ccae81684d5c7f11f4d801cf3a032cd8812c07788a5c0f090c3`
- Atomic swap `state/cs_rag` and preserve `state/cs_rag_archive/v2_<stamp>`.
- Run three Lance smoke queries and verify `meta.backend == "lance"`.
- Update `config/rag_models.json` with the final production lock.
- Verify `docs/runbooks/rag-rollback.md`.
- Write `docs/worklogs/rag-r2-cutover-2026-05-01.md`.

## Recommended Next Step

Choose Option A unless there is a product reason to prefer a weaker gate or a
known-risk cutover. The current evidence says legacy v2 is still the better
production stack for the measured learner workload.

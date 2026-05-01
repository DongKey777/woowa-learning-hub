# RAG v6.2 External Review Packet - 2026-05-01

Purpose: hand this packet to another AI or reviewer so they can decide whether
to delay cutover, revise the gate, or explicitly approve a risky cutover.

Objective: `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md`

Generated at: `2026-05-01T06:03:38Z`

## Decision Needed

Choose one path:

1. Delay cutover and keep legacy v2 in production.
2. Revise the acceptance gate, document the new rule, then rerun comparison.
3. Explicitly approve a known-risk production cutover despite failed gates.

Current recommendation: choose option 1 unless there is a product reason to
accept weaker retrieval quality.

## External Review Response

Reviewer position received after this packet:

- Option A is strongly supported by the current evidence.
- No defensible replacement gate was identified. Any gate that lets this R2
  candidate pass would effectively abandon the quality criterion.
- No product reason was identified for a risky cutover.
- The next work should target cross-category mis-retrieval first.

Correction to one reviewer hypothesis:

- The reviewer suggested rebuilding the R2 artifact because the original R2
  artifact predated the Lance reranker hook fix.
- That is true for the historical artifact provenance, but not enough to
  justify an immediate rebuild by itself. The same-query recovery diagnostics
  already evaluated the preserved R2 index through the current `main` Lance
  search path, after the hook fix had been merged.
- Evidence:
  - reranker-on same-query report:
    `reports/rag_eval/r2_korean_terms_w00_holdout_20260501T0450Z.json`
    scored `0.9102958204`.
  - same index and fixture with `WOOWA_RAG_NO_RERANK=1`:
    `reports/rag_eval/r2_no_rerank_same_queries_20260501T0540Z.json`
    scored `0.8081397290`.
  - The large delta proves the current same-query measurement is not silently
    skipping reranker. A rebuild solely to pick up the reranker hook is
    therefore not the next required step.

Updated next step:

- Keep Option A as the product recommendation.
- If continuing technically before product input, prioritize cross-category
  mis-retrieval diagnostics and then a true reranker A/B (`mmarco` vs
  `bge-reranker-v2-m3`), not a same-artifact rebuild for hook provenance.

## Current Runtime State

Production runtime is still legacy v2:

- `state/cs_rag/manifest.json`
  - `index_version=2`
  - `embed_model=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
  - `embed_dim=384`
  - `row_count=27157`
- `state/cs_rag_archive/` is absent.
- `docs/worklogs/rag-r2-cutover-2026-05-01.md` is absent.
- `config/rag_models.json` exists as R2 candidate metadata, but final Phase 3
  production lock fields are absent:
  - top-level `artifact_sha256`
  - top-level `ivf`

## Objective And DoD

The plan's Definition of Done requires:

1. Phase 0: merge `feature/rag-v6-improve` into `main`, pass tests, push.
2. Phase 1: create cutover regression reports, pass the cutover gate, commit
   worklog.
3. Phase 2: produce IVF sweep, decide winner or keep `256/64`, record data.
4. Phase 3: production cutover, Lance smoke, v2 archive, production lock,
   rollback runbook verification, integrated cutover worklog.
5. Phase 4 minimum: chunk-context contract, 5-doc sidecars, multi-turn eval,
   Korean bucket delta.

Current status:

- Phase 0: complete.
- Phase 1: reports complete, gate failed.
- Phase 2: sweep complete, production gate failed.
- Phase 3: not done; should not be run without an explicit decision.
- Phase 4 minimum and additional diagnostics: complete, but no cutover unblocker.

## Blocking Evidence

### Phase 1 Original Cutover Gate

Report: `reports/rag_eval/cutover_legacy_vs_lance_20260501T035453Z.json`

| metric | value |
|---|---:|
| legacy primary nDCG macro | 0.9624408810 |
| Lance R2 primary nDCG macro | 0.8102647781 |
| delta | -0.1521761029 |
| gate pass | false |
| bucket gate pass | false |
| regression count | 8 |

### Phase 1 Same-Query Diagnostic

Report: `reports/rag_eval/cutover_legacy_vs_lance_same_queries_20260501T0625Z.json`

| metric | value |
|---|---:|
| query intersection | 101/101 |
| legacy primary nDCG macro | 0.9624408810 |
| Lance same-code primary nDCG macro | 0.9102958204 |
| delta | -0.0521450606 |
| gate pass | false |
| bucket regressions | 7 |

Interpretation: even after aligning the query set, Lance R2 does not beat the
legacy stack.

### Phase 2 IVF Sweep

Report: `reports/rag_eval/r2_ivf_sweep_20260501T0401.json`

| field | value |
|---|---|
| decision | `keep_current_256_64` |
| production gate pass | `false` |
| passing variants | `[]` |

Interpretation: no measured local IVF variant passed the strict production
gate, and Phase 1 had already failed.

## Recovery Attempts

### Korean Anchor / Alias Pilot

Report: `reports/rag_eval/cutover_failure_anchor_comparison_20260501T0640Z.json`

- Added aliases to 8 repeated failure target docs.
- Sampled failure fixture quality delta: `+0.0000`.
- Not accepted as a cutover unblocker.

### Exact Failure Query Rewrite Pilot

Report: `reports/rag_eval/cutover_failure_rewrite_comparison_20260501T0715Z.json`

- 14 rewrite sidecars were consumed by the Lance search path.
- Sampled quality delta: `+0.0000`.
- Local CPU P95 delta: `+275.0 ms`.
- Not accepted as a cutover unblocker.

### Qrel Review Packet

Report: `reports/rag_eval/cutover_failure_qrel_review_20260501T0730Z.json`

| classification | count |
|---|---:|
| cross-category wrong document | 6 |
| same-category wrong document | 4 |
| primary present below rank 5 | 1 |
| strict primary rank 1 direct diagnostic | 3 |

Interpretation: this is not mostly a missing-acceptable-path problem. Most
misses are wrong-document or wrong-category retrieval.

### No-Reranker Diagnostic

Report: `reports/rag_eval/cutover_legacy_vs_lance_no_rerank_20260501T0540Z.json`

| metric | value |
|---|---:|
| Lance no-reranker primary nDCG macro | 0.8081397290 |
| delta vs legacy | -0.1543011520 |
| bucket regressions | 8 |
| hard-regression failures | 50 |

Interpretation: disabling the current reranker worsens quality. It is not a
recovery path.

### Gate Relaxation Review

Report: `reports/rag_eval/cutover_gate_review_20260501T0543Z.json`

| scenario | delta | pass |
|---|---:|---|
| current primary category macro | -0.0521450606 | false |
| graded category macro | -0.0515191445 | false |
| primary micro | -0.0950523182 | false |
| graded micro | -0.0958228031 | false |
| graded language macro | -0.1311489525 | false |

Interpretation: switching to a reasonable graded-nDCG metric does not unblock
cutover.

### Document-Structure Candidate

Report: `reports/rag_eval/cutover_failure_doc_structure_comparison_20260501T0545Z.json`

- Temporarily tested beginner-facing body blocks in 4 repeated target docs.
- Sampled quality delta: `+0.0000`.
- Hard-regression delta: `0`.
- Temporary body changes were reverted.
- Not accepted as a cutover unblocker.

## Decision Options

### Option A - Delay Cutover

Keep legacy v2 in production.

Use this if:

- production learner quality is more important than completing the v6.2 cutover
  checkbox;
- failed gates should block production changes;
- the team wants more retrieval work before swapping runtime state.

Next likely work:

- stronger corpus restructuring, not more shallow aliases;
- qrel redesign only if the product agrees the current primary-path gate is
  misaligned;
- Korean retrieval strategy beyond query-candidate plumbing;
- later reranker A/B after the base retrieval gap is addressed.

### Option B - Change The Gate

Only choose this if the current primary-path gate is judged misaligned with the
product goal.

Required before cutover:

- write the revised acceptance rule and rationale;
- rerun legacy and Lance reports under the revised rule;
- commit a new comparison report;
- cut over only if the revised gate passes.

Important caveat: the measured graded-nDCG relaxations still failed.

### Option C - Risky Cutover Approval

Only choose this if the product owner explicitly accepts the known regression.

Required execution steps:

- use unique staging dir: `state/cs_rag_next_<stamp>`;
- verify R2 artifact sha256:
  `1fed316557c86ccae81684d5c7f11f4d801cf3a032cd8812c07788a5c0f090c3`;
- atomically swap `state/cs_rag`;
- preserve current v2 at `state/cs_rag_archive/v2_<stamp>`;
- run 3 Lance smoke queries and verify `meta.backend == "lance"`;
- update `config/rag_models.json` with final production lock;
- verify `docs/runbooks/rag-rollback.md`;
- write `docs/worklogs/rag-r2-cutover-2026-05-01.md`.

Risk:

- measured same-query quality regression remains;
- Korean / beginner / bucket regressions remain;
- learner experience may worsen.

## Questions For The Reviewer

1. Is Option A, delaying cutover, the right decision from the current evidence?
2. If the gate should change, what exact acceptance rule is defensible?
3. Is there a product reason to accept a risky cutover despite failed gates?
4. Which next improvement should be prioritized: qrel redesign, corpus
   restructuring, Korean retrieval, or reranker A/B?

# RAG v6.2 Completion Audit - 2026-05-01

Objective: `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md`

## Concrete Success Criteria

The plan's Definition of Done requires all of the following:

1. Phase 0: merge `feature/rag-v6-improve` into `main`, pass the recommended
   regression tests and the full unit suite, then push.
2. Phase 1: create cutover regression reports, pass the cutover gate, and
   commit a worklog.
3. Phase 2: produce a 4-way IVF sweep, decide the winning variant or keep
   `256/64`, and record the data.
4. Phase 3: perform production cutover, pass 3 smoke queries on Lance, preserve
   `state/cs_rag_archive/v2_<date>/`, update `config/rag_models.json` with
   full artifact sha and IVF lock, verify `docs/runbooks/rag-rollback.md`, and
   write the integrated cutover worklog.
5. Phase 4 minimum: add `chunk-context-v1`, generate sidecars for 5 docs, run
   one multi-turn fixture evaluation, and record the ko bucket delta.

## Prompt-to-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Commit and ignore untracked Korean rewrite artifacts | Commit `e8d9a1a`; `.gitignore` contains `tests/fixtures/cs_rag_golden_queries_ko_*_applied.json` | Complete |
| Merge `feature/rag-v6-improve` | Merge commit `bb5ba3a`; `git log` shows feature branch commits behind `main` | Complete |
| Phase 0 recommended 7-test suite | Session output: 94 passed before merge; post-merge related RAG suite later passed | Complete |
| Phase 0 full unit suite | Latest full unit run after Phase 4 structural rewrite wiring: `1940 passed, 2 warnings, 772 subtests passed` | Complete |
| Push `main` | Completed phase commits are pushed and current branch tracking is verified with `git status --short --branch` before final handoff | Complete |
| `bin/rag-remote-build --help` available | Help output includes `--ivf-num-partitions` and `--ivf-num-sub-vectors` | Complete |
| `bin/doctor` model-lock check | Current output reports expected WARN: config expects Lance v3/BGE-M3, state is legacy v2/MiniLM | Complete |
| Phase 1 legacy report | `reports/rag_eval/cutover_legacy_v2_20260501T035453Z.json` tracked | Complete |
| Phase 1 compare report | `reports/rag_eval/cutover_legacy_vs_lance_20260501T035453Z.json` tracked | Complete |
| Phase 1 gate | Compare report gate: `pass=false`, `global_gate_pass=false`, `bucket_gate_pass=false`, `regression_count=8` | Blocked |
| Phase 1 worklog | `docs/worklogs/rag-r2-cutover-regression-2026-05-01.md` tracked | Complete |
| Phase 2 IVF tuning flags | Commit `7b80366`; CLI help exposes local and remote IVF flags | Complete |
| Phase 2 sweep report | `reports/rag_eval/r2_ivf_sweep_20260501T0401.json` tracked | Complete |
| Phase 2 decision | Report decision is `keep_current_256_64`; `production_gate_pass=false`; no variant passed P95 gate | Complete |
| Phase 3 production cutover | `state/cs_rag/manifest.json` is still `index_version=2`, MiniLM 384-dim | Not done |
| Phase 3 archive preservation | `state/cs_rag_archive` does not exist | Not done |
| Phase 3 smoke on Lance | Not run because production cutover gate failed; `bin/doctor` confirms current backend state is legacy v2 | Not done |
| Phase 3 `config/rag_models.json` full production lock update | File exists and points to R2 config, but current state is not cut over; `ivf` and top-level `artifact_sha256` are absent | Not done |
| Phase 3 integrated worklog | `docs/worklogs/rag-r2-cutover-2026-05-01.md` does not exist | Not done |
| Phase 4 `chunk-context-v1` contract | `docs/ai-behavior-contracts.md` and `skills/woowa-chunk-context/SKILL.md` tracked in `f2a100d` | Complete |
| Phase 4 sidecar preparation CLI | `bin/chunk-context-prepare` and `scripts/learning/cli_chunk_context_prepare.py` tracked | Complete |
| Phase 4 5-doc sidecar pilot | `reports/rag_eval/chunk_context_pilot_comparison_20260501T0416Z.json` records 130 inputs and 130 outputs over 5 docs | Complete |
| Phase 4 multi-turn fixture | `tests/fixtures/cs_rag_multi_turn_queries.json`; `bin/rag-eval --fast` passed with 10 queries | Complete |
| Phase 4 ko bucket delta | Comparison report records `ko_bucket_delta_primary_ndcg=0.0` | Complete |
| Phase 4.2 Korean retrieval-anchor pilot | `knowledge/cs/contents/design-pattern/strict-list-canary-metrics-rollback-triggers.md` Korean anchors added; `reports/rag_eval/anchor_pilot_strict_list_comparison_20260501T0520Z.json` shows `+0.0000` sampled quality delta and no hard-regression increase | Complete |
| Phase 4.3 Korean query-side `search_terms` candidate | `reports/rag_eval/r2_korean_terms_query_candidate_20260501T0450Z.json`; same-code weights `0.3` and `0.7` had `+0.0000` macro/ko delta versus weight `0.0` | Measured, not accepted |
| Phase 4 structural `query-rewrite-v1` sidecar pilot | `WOOWA_RAG_QUERY_REWRITE_ROOT` override added for temp Lance eval indexes; `reports/rag_eval/query_rewrite_pilot_comparison_20260501T0610Z.json` shows `+0.0000` sampled quality delta and +91.1 ms local CPU P95 | Measured, not accepted |

## Blocking Evidence

The objective is not complete.

Phase 3 is a required DoD item, but the plan also says cutover only proceeds
when Phase 1 and Phase 2 gates pass. Current measured evidence blocks that:

- Phase 1 cutover comparison:
  - legacy primary nDCG macro: `0.9624408810`
  - Lance R2 primary nDCG macro: `0.8102647781`
  - delta: `-0.1521761029`
  - gate pass: `false`
  - bucket gate pass: `false`
  - regression count: `8`
- Phase 2 IVF sweep:
  - decision: `keep_current_256_64`
  - production gate pass: `false`
  - passing variants: `[]`
- Current runtime state:
  - `state/cs_rag/manifest.json` is legacy v2 MiniLM, not Lance v3 BGE-M3.
  - `state/cs_rag_archive` is absent.
  - `docs/worklogs/rag-r2-cutover-2026-05-01.md` is absent.

Subsequent Phase 4.3 work measured an opt-in Korean query-side `search_terms`
candidate. A same-code baseline rerun showed weights `0.3` and `0.7` produced
no ranking lift over weight `0.0`; only local latency varied. The feature is
therefore left behind `WOOWA_KOREAN_FTS_TERMS_WEIGHT`; default weight is `0.0`.

Subsequent structural `query-rewrite-v1` work added an override so temp Lance
evaluation indexes can consume rewrite sidecars. The 10-query multi-turn pilot
validated the wiring but produced no sampled ranking lift over the anchor
baseline, so it remains evaluation instrumentation rather than a default
quality improvement.

## Next Required Decision

Production cutover should not be run from the current evidence. The next
productive step requires a user/product decision:

1. Delay cutover and keep improving Korean/contextual retrieval until the
   cutover gate passes.
2. Change the gate and document the revised acceptance criteria, then rerun the
   comparison.
3. Explicitly approve a risky cutover despite the failed gate.

Until one of those decisions is made, the active goal remains incomplete.

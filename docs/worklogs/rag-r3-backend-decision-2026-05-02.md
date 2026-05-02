# R3 Backend Decision - 2026-05-02

Decision: choose LanceDB-improved R3 as the first production candidate, keep
legacy v2 as rollback, and keep Qdrant as a measured comparator rather than the
local default.

## Production Candidate

The selected candidate is:

```text
LanceDB v3 artifact
+ BGE-M3 dense query retrieval
+ BGE-M3 sparse first-stage sidecar
+ metadata lexical sidecar over title/section/aliases
+ signal retriever
+ deterministic RRF fusion preserving rich duplicate candidates
+ sidecar-first auto rerank policy
+ optional forced BAAI/bge-reranker-v2-m3 quality path
```

This preserves the fundamental R3 design: independent candidate generators,
true sparse discovery, traceable fusion, calibrated qrels, and local-first
serving. It does not treat the previous Lance v3 sparse-rescore behavior as
sufficient; the sparse sidecar and metadata lexical sidecar are now separate
first-stage candidate sources.

## Evidence

| Area | Artifact | Result |
|---|---|---|
| Remote production artifact | `artifacts/rag-full-build/r3-0c8fd9f-2026-05-02T0827/artifact_contract.json` | strict R3 package built on RunPod L40S, local import verified, `row_count=27158`, `corpus_hash=c002a92b2b97033d5ff3f0a9c94d3c952586107337e3a07cd66e9c943643cacb` |
| Production 208q gate | `reports/rag_eval/r3_backend_compare_208q_production_r3_auto_20260502T0845Z.summary.json` | `candidate_recall_primary@5/20/50/100=1.0`, `candidate_recall_relevant@5/20/50/100=1.0`, final primary/relevant hits all `1.0`, Korean and mixed cohorts all `1.0`, `forbidden_rate@5=0` |
| Root-cause regression check | `reports/rag_eval/r3_backend_compare_208q_production_r3_auto_20260502T0845Z.summary.json` | service-locator expected-query miss recovered to final rank 1 after indexing Corpus v2 `expected_queries` as retrieval anchors |
| Local production smoke | `reports/rag_eval/r3_0c8fd9f_local_smoke_20260502T0852Z.json` | default full `auto` uses BGE-M3 sparse sidecar, daemon warm request 1169ms, service-locator mixed Korean query returns `contents/design-pattern/service-locator-antipattern.md` first |
| Forced BGE reranker smoke | `reports/rag_eval/r3_0c8fd9f_local_smoke_20260502T0852Z.json` | `BAAI/bge-reranker-v2-m3` loads locally and reranks 20 pairs; direct one-shot latency 24958ms, rerank stage 5380.51ms |
| R3 auto quality | `reports/rag_eval/r3_backend_compare_100q_sidecar_auto_policy_20260501T2025Z.json` | `final_hit_relevant@5=1.0` overall/Korean/mixed, `forbidden_rate@5=0`, auto sidecar skip 100/100 |
| R3 local daemon | `reports/rag_eval/r3_daemon_full_runtime_auto_sidecar_smoke_20260501T2005Z.json` | first request 12296ms, warm request 476ms, sidecar loaded, reranker skipped by policy |
| Forced BGE reranker | `reports/rag_eval/r3_backend_compare_100q_lexical_sidecar_rich_fusion_reranker_window20_20260501T1955Z.json` | BGE reranker quality path remains available and green |
| Qdrant local probe | `reports/rag_eval/r3_qdrant_local_probe_100q_20260501T2010Z.json` | `candidate_recall_primary@100=1.0`, but sparse query p95 302.123ms and RSS peak 3398.422MB |
| Qdrant summary | `reports/rag_eval/r3_qdrant_local_probe_summary_20260501T2010Z.md` | local mode warning after 20,000 points; Docker server mode unavailable because daemon was not running |
| Strict local artifact import | `reports/rag_eval/r3_strict_artifact_import_smoke_20260501T1845Z.md` | local strict import contract passes |
| Remote harness dry run | `reports/rag_eval/r3_remote_strict_harness_dry_run_20260501T1911Z.md` | remote package/verify path is enforced in dry run |
| Remote harness fail-closed guard | `reports/rag_eval/r3_remote_live_build_blocked_20260501T2013Z.md` | historical safety check; superseded by the successful live artifact above |
| Remote source fallback | `reports/rag_eval/r3_remote_source_bundle_dry_run_20260501T2015Z.md` | git bundle dry-run passes for committed local changes ahead of origin |

## Why Not Qdrant First

Qdrant supports named dense and sparse vectors and can run the same Python
client API in local mode, which makes it a reasonable R3 comparator. The probe
confirmed it can reach primary recall @100 on the same 100q qrels.

It is not the first local production candidate because:

- local mode emitted a warning after the collection exceeded 20,000 points;
- the measured RSS peak after evaluation was 3398.422MB before adding the
  lexical sidecar, daemon process, and future learner context overhead;
- sparse query p95 was 302.123ms, slower than the current in-process sparse
  sidecar once cached;
- relevant@5 was weaker than the selected R3 path, especially Korean-only
  `0.8750` versus the selected path's `1.0000`;
- Docker/server mode could not be measured because the Docker daemon was not
  running, and requiring Docker as the learner's default serving path is a
  worse operational fit than a single local Python daemon.

This is not a rejection of Qdrant as a technology. It is a local production
decision for this learning hub and its M5 MacBook Air 16GB constraint.

## Reranker Position

`BAAI/bge-reranker-v2-m3` remains the R3 target quality reranker. It is no
longer the default local interactive stage when the verified metadata lexical
sidecar is loaded, because the sidecar-first `auto` policy passed the expanded
208q gate and the current remote-built artifact serves warm daemon requests in
about 1.17s on the learner machine.

Operational policy:

- default: `WOOWA_RAG_R3_RERANK_POLICY=auto`;
- force quality path: explicit `use_reranker=True` or
  `WOOWA_RAG_R3_RERANK_POLICY=always`;
- controlled no-reranker experiments: `WOOWA_RAG_R3_RERANK_POLICY=off` or
  backend comparison `--no-reranker`.

## Rollback

Rollback anchor: legacy v2 MiniLM + SQLite/NPZ archive.

Current implementation snapshot: LanceDB v3.

R3 production candidate: LanceDB-improved sidecar architecture described above.

The rollback archive remains available as a safety reference, but the R3
candidate has passed the live remote-build, local-import, 208q production gate,
and local-serving smoke packet. Keep legacy v2 available for controlled
comparisons and emergency rollback until at least two full holdout runs are
recorded against the new artifact.

## Cutover Status

Remote build, actual SSH verification, artifact import, expanded qrel gate, and
local smoke are complete for `r3-0c8fd9f-2026-05-02T0827`.

The only remaining work is routine post-cutover observation: run the full
holdout suite repeatedly as the corpus grows, keep qrels calibrated, and treat
new failures as root-cause bugs rather than one-off ranking tweaks.

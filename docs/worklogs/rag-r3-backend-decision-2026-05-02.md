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
| R3 auto quality | `reports/rag_eval/r3_backend_compare_100q_sidecar_auto_policy_20260501T2025Z.json` | `final_hit_relevant@5=1.0` overall/Korean/mixed, `forbidden_rate@5=0`, auto sidecar skip 100/100 |
| R3 local daemon | `reports/rag_eval/r3_daemon_full_runtime_auto_sidecar_smoke_20260501T2005Z.json` | first request 12296ms, warm request 476ms, sidecar loaded, reranker skipped by policy |
| Forced BGE reranker | `reports/rag_eval/r3_backend_compare_100q_lexical_sidecar_rich_fusion_reranker_window20_20260501T1955Z.json` | BGE reranker quality path remains available and green |
| Qdrant local probe | `reports/rag_eval/r3_qdrant_local_probe_100q_20260501T2010Z.json` | `candidate_recall_primary@100=1.0`, but sparse query p95 302.123ms and RSS peak 3398.422MB |
| Qdrant summary | `reports/rag_eval/r3_qdrant_local_probe_summary_20260501T2010Z.md` | local mode warning after 20,000 points; Docker server mode unavailable because daemon was not running |
| Strict local artifact import | `reports/rag_eval/r3_strict_artifact_import_smoke_20260501T1845Z.md` | local strict import contract passes |
| Remote harness dry run | `reports/rag_eval/r3_remote_strict_harness_dry_run_20260501T1911Z.md` | remote package/verify path is enforced in dry run |

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
sidecar is loaded, because the sidecar-first `auto` policy passed the 100q
quality gate and reduced warm daemon latency to 476ms.

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

The rollback archive remains required until R3 passes the full cutover packet
with a remote-built artifact imported and served locally.

## Remaining Blocker

The only current cutover blocker is a live remote GPU artifact build and local
strict import verification. The code path is dry-run verified, but this
environment has no `RUNPOD_API_KEY`, so the actual RunPod build cannot be
executed here.

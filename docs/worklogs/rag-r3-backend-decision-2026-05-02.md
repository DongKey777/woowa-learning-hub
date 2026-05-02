# R3 Backend Decision - 2026-05-02

Decision: choose LanceDB-improved R3 as the first production candidate, keep a
current-corpus legacy v2 index as rollback, and keep Qdrant as a measured
comparator rather than the local default.

## Production Candidate

The selected candidate is:

```text
remote-built LanceDB v3 artifact
+ BGE-M3 dense query retrieval
+ BGE-M3 sparse first-stage sidecar
+ metadata lexical sidecar over title/section/aliases/body
+ signal retriever
+ deterministic RRF fusion v2
+ sidecar-first auto rerank policy
+ optional forced BAAI/bge-reranker-v2-m3 quality path
```

This preserves the fundamental R3 design: independent candidate generators,
true sparse discovery, traceable fusion, calibrated qrels, and local-first
serving. It does not treat the previous Lance v3 sparse-rescore behavior as
sufficient; the sparse sidecar and metadata lexical sidecar are separate
first-stage candidate sources.

## Selected Artifact

Selected remote index artifact:

- run id: `r3-61216f2-2026-05-02T0937`
- build commit: `61216f25cc219bae945cbc49d7c06bb7d2f9d5be`
- runtime commit: `788ee99e67b7131e647684592d53bd268eef93f0`
- archive: `artifacts/rag-full-build/r3-61216f2-2026-05-02T0937/cs_rag_index_root.tar.zst`
- archive sha256: `5eab5b0fb9def8c0c58370eb64abbbbf6fb195c95bc6d4376832c654c3a78e0d`
- row count: `27158`
- corpus hash: `c002a92b2b97033d5ff3f0a9c94d3c952586107337e3a07cd66e9c943643cacb`
- lexical sidecar sha256: `8593b20f074d8d45f310b3f7a759004e727fa7ec71193b25c643bef830bb5934`

Strict artifact verification:

```bash
.venv/bin/python -m scripts.remote.artifact_contract \
  artifacts/rag-full-build/r3-61216f2-2026-05-02T0937 \
  --strict-r3 --verify-import
```

Result: passed. The imported index root matches archive checksum, manifest
metadata, `row_count`, `corpus_hash`, BGE-M3 model revision, and lexical sidecar
checksum.

Runtime overlay:

- `61216f2` is the verified remote-built index payload.
- `5d17c78` and later runtime commits changed fusion weighting and remote
  harness behavior, not the selected index payload inputs.
- Final runtime gate uses the imported `61216f2` index with current runtime
  fusion v2 (`weighted-rrf-doc-diversity-v2`).

## Evidence

| Area | Artifact | Result |
|---|---|---|
| Remote production artifact | `artifacts/rag-full-build/r3-61216f2-2026-05-02T0937/artifact_contract.json` and strict verifier rerun | remote-built R3 package, local import verified, `row_count=27158`, corpus hash matched |
| Production 208q gate | `reports/rag_eval/r3_backend_compare_208q_production_r3_auto_20260502T1052Z.summary.json` | candidate and final primary/relevant hit/recall at 5/20/50/100 are `1.0`; Korean and mixed cohorts are `1.0`; `forbidden_rate@5=0` |
| Root-cause regression check | `reports/rag_eval/r3_backend_compare_208q_production_r3_auto_20260502T1052Z.summary.json` | no missing candidate primary, no missing final primary; service-locator mixed Korean query recovered through alias sidecar fusion v2 |
| Local production smoke | `reports/rag_eval/r3_61216f2_runtime_788ee99_local_smoke_20260502T1059Z.json` | direct cheap/full, service-locator mixed Korean, daemon warm full, and forced BGE reranker paths all execute locally |
| Local daemon warm profile | same smoke report | second daemon full request: `latency_ms=1020`, first hit `contents/network/latency-bandwidth-throughput-basics.md`, sparse source `bge_m3_sparse_vec_sidecar` |
| Forced BGE reranker smoke | same smoke report | `BAAI/bge-reranker-v2-m3` loads locally, reranks 20 pairs, rerank stage `6304.254ms` |
| Rollback current-corpus v2 | `reports/rag_eval/r3_legacy_rollback_current_corpus_smoke_20260502T1104Z.json` | rebuilt legacy v2 archive is `ready`, corpus hash matches current corpus, direct legacy search works |
| Qdrant local probe | `reports/rag_eval/r3_qdrant_local_probe_100q_20260501T2010Z.json` | `candidate_recall_primary@100=1.0`, but local mode warned above 20,000 points, sparse p95 was 302.123ms, RSS peak was 3398.422MB |
| Qdrant summary | `reports/rag_eval/r3_qdrant_local_probe_summary_20260501T2010Z.md` | Docker/server mode was not measured; requiring Docker is a worse learner-local default |
| Remote harness hardening | commits `a535981`, `788ee99` | SFTP archive downloads now resume into `.part`; vanished RunPod pods fail fast instead of requiring manual stop |

## Why Not Qdrant First

Qdrant supports named dense and sparse vectors and can run the same Python
client API in local mode, which makes it a reasonable R3 comparator. The probe
confirmed it can reach primary recall @100 on the same 100q qrels.

It is not the first local production candidate because:

- local mode emitted a warning after the collection exceeded 20,000 points;
- RSS peak after evaluation was 3398.422MB before adding the lexical sidecar,
  daemon process, and future learner-context overhead;
- sparse query p95 was 302.123ms, slower than the in-process sparse sidecar once
  cached;
- relevant@5 was weaker than the selected R3 path, especially Korean-only
  `0.8750` versus the selected path's `1.0000`;
- Docker/server mode could not be measured, and requiring Docker as the
  learner's default serving path is a worse operational fit than a single local
  Python daemon.

This is not a rejection of Qdrant as a technology. It is a local production
decision for this learning hub and its M4 MacBook Air 16GB constraint.

## Reranker Position

`BAAI/bge-reranker-v2-m3` remains the R3 target quality reranker. It is not the
default local interactive stage when the verified metadata lexical sidecar is
loaded, because the sidecar-first `auto` policy passed the expanded 208q gate
and the current remote-built artifact serves warm daemon full requests at about
1.0s on the learner machine.

Operational policy:

- default: `WOOWA_RAG_R3_RERANK_POLICY=auto`;
- force quality path: explicit `use_reranker=True` or
  `WOOWA_RAG_R3_RERANK_POLICY=always`;
- controlled no-reranker experiments: `WOOWA_RAG_R3_RERANK_POLICY=off` or
  backend comparison `--no-reranker`.

## Remote Build Note

The final selected index is remote-built. Later attempts to rebuild the exact
latest HEAD on RunPod were not accepted as production evidence because provider
pods disappeared mid-build/transfer:

- `r3-5d17c78-2026-05-02T1010`: build and packaging completed, but SFTP
  transfer dropped and left a truncated local archive;
- `r3-a535981-2026-05-02T1031`, `1041`, and `1045`: SSH-confirmed GPU builds
  started, then the RunPod API reported zero active pods before completion.

Those failures hardened the harness, but they do not invalidate the selected
remote-built `61216f2` artifact because the current runtime gate was run against
that exact imported index and passed.

Next full rebuild requirement: if any index-affecting file changes, use a
stable/dedicated remote GPU provider or a RunPod network volume/persistent
transfer path before replacing the selected artifact.

## Rollback

Rollback anchor: current-corpus legacy v2 MiniLM + SQLite/NPZ archive:
`state/cs_rag_archive/v2_current_20260502T1101Z`.

The older `state/cs_rag_archive/v2_20260501T063445Z` remains preserved for
historical comparison, but it is stale against the expanded corpus. The new
current-corpus v2 archive is the actual emergency rollback index because
`indexer.is_ready()` reports `ready`.

## Cutover Status

Cutover is approved for:

```text
remote-built index r3-61216f2-2026-05-02T0937
+ local runtime commit 788ee99
+ fusion v2 runtime overlay
+ auto sidecar rerank policy
```

Post-cutover observation remains required as the corpus grows: run the full
holdout suite repeatedly, keep qrels calibrated, and treat new failures as
root-cause bugs rather than one-off ranking tweaks.

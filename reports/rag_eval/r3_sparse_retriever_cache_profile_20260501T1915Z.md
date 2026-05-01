# R3 Sparse Retriever Cache Profile - 2026-05-01T19:15Z

Change under test:

- Cache the R3 sparse sidecar `SparseRetriever` inside the long-lived Python process.
- Expose `r3_stage_ms` and `r3_sparse_retriever_cache_hit` through debug metadata.

Why:

The previous R3 path loaded the 27,170-document BGE-M3 sparse sidecar from cache, but rebuilt the inverted sparse postings on every query. That made reranker-disabled warm candidate generation cost about 1.6s.

Same-process profile:

| Mode | Before | After |
|---|---:|---:|
| full candidate generation, reranker off | 1647-1678ms | 484-604ms |

Daemon smoke:

| Query | Client wall | `hits.meta.latency_ms` | Sparse cache | First path |
|---|---:|---:|---|---|
| `RAG로 깊게 latency가 뭐야?` | 15.24s | 14683 | miss | `contents/network/latency-bandwidth-throughput-basics.md` |
| `RAG로 깊게 DI랑 Service Locator 차이가 뭐야?` | 2.91s | 2401 | hit | `contents/design-pattern/service-locator-antipattern.md` |
| `RAG로 깊게 Transactional이 안 먹을 때 먼저 뭘 봐야 해?` | 2.81s | 2605 | hit | `contents/spring/README.md` |

Warm stage breakdown:

| Query | Encode | Dense | Sparse Load | Retriever Build | Retrieve | Rerank |
|---|---:|---:|---:|---:|---:|---:|
| DI vs Service Locator | 296.8ms | 29.3ms | 0.9ms | 290.8ms | 68.7ms | 1652.2ms |
| Transactional debugging | 102.8ms | 28.7ms | 0.9ms | 331.4ms | 40.8ms | 2050.1ms |

Decision:

- Sparse sidecar construction is no longer a per-query warm-path bottleneck.
- Remaining warm-path bottleneck is the BGE reranker scoring step, followed by lexical retriever construction over the query-prefetched documents.
- Local full warm latency moved from about 3.5-3.7s to about 2.4-2.6s internal latency on the mixed Korean/English smoke prompts.

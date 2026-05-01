# R3 Warm Full Runtime Profile - 2026-05-01T18:48Z

Command: long-lived Python process calling `searcher.search(..., backend="r3", mode="full")` for three mixed Korean/English prompts.

Source JSON: `reports/rag_eval/r3_warm_full_runtime_profile_20260501T1848Z.json`

| Query | Elapsed | First path | Reranker | Window |
|---|---:|---|---|---:|
| `RAG로 깊게 latency가 뭐야?` | 23395ms | `contents/network/latency-bandwidth-throughput-basics.md` | `BAAI/bge-reranker-v2-m3` | 50 |
| `RAG로 깊게 DI랑 Service Locator 차이가 뭐야?` | 6868ms | `contents/design-pattern/service-locator-antipattern.md` | `BAAI/bge-reranker-v2-m3` | 50 |
| `RAG로 깊게 Transactional이 안 먹을 때 먼저 뭘 봐야 해?` | 6112ms | `contents/spring/README.md` | `BAAI/bge-reranker-v2-m3` | 50 |

Interpretation:

- The first request pays BGE-M3 query encoder and BGE reranker load cost.
- Same-process warm full requests remove cold start but 50-pair BGE reranking still costs about 6-7s.
- Root cause is split: one-shot CLI process churn causes cold start, and 50-pair `bge-reranker-v2-m3` scoring remains the warm-path bottleneck.

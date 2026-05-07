# R3 Hybrid Reranker Summary - 2026-05-01T18:37Z

Evidence:

- Hybrid reranker summary: `reports/rag_eval/r3_backend_compare_100q_reranker_hybrid_summary_20260501T1837Z.json`
- Qrels: `reports/rag_eval/r3_corpus_v2_qrels_20260501T1640Z.json`
- Hybrid raw source: `/tmp/r3_backend_compare_100q_reranker_hybrid_20260502.json`
- BGE-only raw source: `/tmp/r3_backend_compare_100q_reranker_bge_20260502.json`

What Changed:

`BAAI/bge-reranker-v2-m3` is no longer used as a sole final sorter. The final R3 reranker stage now blends the original multi-retriever fusion rank and the cross-encoder rank with reciprocal-rank fusion. This keeps the cross-encoder signal while preventing it from pushing high-consensus candidate-discovery results behind broad README or overview docs.

Observed 100q Result:

| Metric | BGE-only | Hybrid RRF |
| --- | ---: | ---: |
| final_hit_primary@5 | 0.8600 | 0.9200 |
| final_hit_relevant@5 | 0.9600 | 1.0000 |
| final_hit_relevant@20 | 1.0000 | 1.0000 |
| forbidden_rate@5 | 0.0000 | 0.0000 |
| lost_top5_rate | 0.0900 | 0.0400 |
| lost_top20_rate | 0.0100 | 0.0000 |
| elapsed wall time | 874.78s | 904.33s |

Language Buckets After Hybrid:

| Bucket | Prompts | final relevant@5 | final relevant@20 | forbidden@5 |
| --- | ---: | ---: | ---: | ---: |
| ko | 16 | 1.0000 | 1.0000 | 0.0000 |
| mixed | 84 | 1.0000 | 1.0000 | 0.0000 |

Interpretation:

- The expanded quality gate passes for learner-facing relevance: relevant@5 and relevant@20 are both 1.0000 over 100 prompts.
- Exact primary@5 remains lower at 0.9200, which is acceptable for learner answers because calibrated acceptable neighbors include same-concept sibling and child-topic docs.
- Cold local batch runtime is still too high for interactive full mode: 904.33s for 100 prompts with model load and 50-pair reranking. Production needs a long-lived/amortized local runtime or a strict cheap/full routing policy before default cutover.

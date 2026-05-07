# R3 Reranker Qrel-Calibrated Summary - 2026-05-01T17:42Z

Evidence:

- Retrieval fabric summary: `reports/rag_eval/r3_backend_compare_retrieval_fabric_qrel_calibrated_summary_20260501T1742Z.json`
- Reranker summary: `reports/rag_eval/r3_backend_compare_reranker_bge_qrel_calibrated_summary_20260501T1742Z.json`
- Qrels: `reports/rag_eval/r3_corpus_v2_qrels_20260501T1640Z.json`

What Changed:

The Spring sibling-doc cluster now has acceptable/companion qrels in the Corpus v2 seed. This separates a true wrong result from a valid sibling document that answers the same learner question at a different granularity.

Observed After Qrel Calibration:

| Metric | Retrieval Fabric | With BGE Reranker |
| --- | ---: | ---: |
| candidate_recall_primary@5 | 0.9423 | 0.9423 |
| final_hit_primary@5 | 0.9423 | 0.9038 |
| final_hit_relevant@5 | 0.9423 | 0.9808 |
| final_hit_primary@20 | 1.0000 | 0.9808 |
| final_hit_relevant@20 | 1.0000 | 1.0000 |
| forbidden_rate@5 | 0.0000 | 0.0000 |

Interpretation:

- The target reranker still sometimes moves the exact primary below its pre-rerank position.
- For learner-facing relevance, the calibrated qrels show the reranker keeps a relevant Spring sibling in top-5 for 51 of 52 pilot prompts and in top-20 for all 52.
- This supports keeping `BAAI/bge-reranker-v2-m3` as the target, but the remaining exact-primary losses should stay visible until the expanded qrel suite is larger than 100 prompts.

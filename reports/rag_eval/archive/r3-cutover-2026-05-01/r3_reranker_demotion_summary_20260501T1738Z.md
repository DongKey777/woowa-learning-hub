# R3 Reranker Demotion Summary - 2026-05-01T17:38Z

Evidence:

- Source report: `/tmp/r3_backend_compare_reranker_bge_body_20260502.json`
- Committed summary: `reports/rag_eval/r3_backend_compare_reranker_bge_summary_20260501T1738Z.json`
- Qrels: `reports/rag_eval/r3_corpus_v2_qrels_20260501T1640Z.json`
- Reranker: `BAAI/bge-reranker-v2-m3`
- Window: top-50 candidates, local rerank window 50

Root Cause Fixed Before This Run:

The first reranker comparison demoted most primaries because R3 candidates did not carry document body text into the reranker passage. The runtime loader now includes `body` in document metadata for normal legacy/Lance candidates, so the reranker scores title/section/body instead of mostly title/section.

Observed After Fix:

| Metric | Value |
| --- | ---: |
| candidate_recall_primary@5 | 0.9423 |
| candidate_recall_primary@20 | 1.0000 |
| final_hit_primary@5 | 0.9038 |
| final_hit_primary@20 | 0.9808 |
| final_hit_primary@50 | 1.0000 |
| forbidden_rate@5 | 0.0000 |
| plain demotion rate | 0.4038 |
| harmful lost_top5 rate | 0.0769 |
| harmful lost_top20 rate | 0.0192 |

Language split:

| Language | final_hit_primary@5 | final_hit_primary@20 | lost_top5_rate | lost_top20_rate |
| --- | ---: | ---: | ---: | ---: |
| ko | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| mixed | 0.8810 | 0.9762 | 0.0952 | 0.0238 |

Remaining Harmful Losses:

- lost_top5: `spring/ioc-container-internals:expected:2`
- lost_top5: `spring/bean-di-basics:expected:4`
- lost_top5: `spring/ioc-di-basics:expected:3`
- lost_top5: `spring/transactional-basics:expected:3`
- lost_top20: `spring/bean-di-basics:expected:4`

Decision:

The target reranker is no longer structurally broken, but it is not yet cutover-clean. The next action is to inspect the four harmful Spring mixed-query losses and decide whether they are qrel wording, passage truncation, corpus ambiguity, or reranker weakness.

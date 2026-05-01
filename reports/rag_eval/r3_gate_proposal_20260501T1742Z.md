# R3 Gate Proposal - 2026-05-01T17:42Z

Scope: current provisional Phase 4a gate after R3 retrieval fabric, target reranker profiling, body-aware reranker passages, and Spring sibling qrel calibration. This is still not a production cutover gate because the pilot has 52 prompts, below the required expanded suite size.

Evidence:

- Retrieval fabric: `reports/rag_eval/r3_backend_compare_retrieval_fabric_qrel_calibrated_summary_20260501T1742Z.json`
- Reranker: `reports/rag_eval/r3_backend_compare_reranker_bge_qrel_calibrated_summary_20260501T1742Z.json`
- Reranker runtime: `reports/rag_eval/r3_reranker_profile_summary_20260501T1730Z.md`
- Qrels: `reports/rag_eval/r3_corpus_v2_qrels_20260501T1640Z.json`

Observed Pilot:

| Metric | Value |
| --- | ---: |
| qrel prompts | 52 |
| candidate_recall_primary@20 | 1.0000 |
| candidate_recall_primary@50 | 1.0000 |
| candidate_recall_relevant@20 | 1.0000 |
| retrieval fabric final_hit_primary@5 | 0.9423 |
| BGE reranker final_hit_primary@5 | 0.9038 |
| BGE reranker final_hit_relevant@5 | 0.9808 |
| BGE reranker final_hit_relevant@20 | 1.0000 |
| forbidden_rate@5 | 0.0000 |
| GTE multilingual fallback | failed default and CPU probes |
| verified Korean/mixed fallback | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` |

Current Provisional Gates:

| Gate | Threshold |
| --- | ---: |
| expanded qrel prompts | >= 100 reviewed prompts |
| Korean prompts | >= 30 |
| mixed Korean/English prompts | >= 30 |
| candidate_recall_primary@20 | >= 0.99 overall and per language bucket |
| candidate_recall_primary@100 | 1.00 overall |
| reranked final_hit_relevant@5 | >= 0.97 overall and >= 0.95 per language bucket |
| reranked final_hit_relevant@20 | 1.00 overall |
| forbidden_rate@5 | 0.00 |
| harmful lost_top20_rate | <= 0.02 until qrels are expanded, then re-set from data |
| local full-mode runtime | accepted M5 profile or explicit long-lived runtime decision |
| remote artifact import | strict manifest verifies locally |

Decision:

Proceed with R3 as the target architecture, but do not cut over by default yet. The next cutover blockers are corpus pilot expansion to 100+ reviewed prompts, local full-mode runtime acceptance, and remote artifact import verification under the final manifest.

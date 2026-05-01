# R3 Gate Proposal - 2026-05-01T18:03Z

Scope: expanded Corpus v2 pilot after R3 retrieval fabric, dense discovery, BGE-M3 sparse sidecar discovery, and qrel calibration for DI/Service Locator contrast docs. This is not a production cutover gate yet because expanded reranker metrics, local full-mode runtime acceptance, and strict remote artifact import are still pending.

Evidence:

- Retrieval fabric 100q summary: `reports/rag_eval/r3_backend_compare_100q_retrieval_summary_20260501T1803Z.json`
- Qrels: `reports/rag_eval/r3_corpus_v2_qrels_20260501T1640Z.json`
- Previous reranker 52q summary: `reports/rag_eval/r3_backend_compare_reranker_bge_qrel_calibrated_summary_20260501T1742Z.json`
- Reranker runtime profile: `reports/rag_eval/r3_reranker_profile_summary_20260501T1730Z.md`

Observed Expanded Pilot:

| Metric | Value |
| --- | ---: |
| Corpus v2 pilot docs | 25 |
| qrel prompts | 100 |
| qrel entries | 284 |
| forbidden entries | 0 |
| Korean-only prompts | 16 |
| mixed Korean/English prompts | 84 |
| candidate_recall_primary@5 | 0.9100 |
| candidate_recall_primary@20 | 1.0000 |
| candidate_recall_primary@100 | 1.0000 |
| candidate_recall_relevant@5 | 0.9500 |
| candidate_recall_relevant@20 | 1.0000 |
| forbidden_rate@5 | 0.0000 |
| source eval elapsed | 173.12s |

Language Buckets:

| Bucket | Prompts | primary@20 | primary@100 | relevant@5 | forbidden@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| ko | 16 | 1.0000 | 1.0000 | 0.9375 | 0.0000 |
| mixed | 84 | 1.0000 | 1.0000 | 0.9524 | 0.0000 |

Current Provisional Gates:

| Gate | Threshold | Current | Status |
| --- | ---: | ---: | --- |
| expanded qrel prompts | >= 100 reviewed prompts | 100 | pass |
| mixed Korean/English prompts | >= 60, reflecting actual learner query style | 84 | pass |
| Korean-only prompts | monitor, not cutover-blocking unless observed traffic needs it | 16 | monitor |
| candidate_recall_primary@20 | >= 0.99 overall and per language bucket | 1.0000 | pass |
| candidate_recall_primary@100 | 1.00 overall | 1.0000 | pass |
| forbidden_rate@5 | 0.00 | 0.0000 | pass |
| expanded reranked final_hit_relevant@5 | >= 0.97 overall and >= 0.95 per language bucket | pending | block |
| expanded reranked final_hit_relevant@20 | 1.00 overall | pending | block |
| local full-mode runtime | accepted M5 profile or explicit long-lived runtime decision | pending | block |
| remote artifact import | strict manifest verifies locally | pending | block |

Decision:

Proceed with R3 as the target architecture and treat the retrieval fabric as passing the expanded candidate-discovery gate. Do not cut over by default yet. The next blockers are expanded BAAI/bge-reranker-v2-m3 reranker metrics on the same 100q suite, local M5 runtime acceptance for full mode, and strict remote artifact import verification.

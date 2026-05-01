# R3 Gate Proposal - 2026-05-01T18:37Z

Scope: expanded 100q Corpus v2 gate after dense discovery, BGE-M3 sparse sidecar discovery, SQL child-topic qrel calibration, and hybrid RRF reranking with `BAAI/bge-reranker-v2-m3`.

Evidence:

- Candidate discovery and hybrid reranker 100q summary: `reports/rag_eval/r3_backend_compare_100q_reranker_hybrid_summary_20260501T1837Z.json`
- Hybrid reranker interpretation: `reports/rag_eval/r3_reranker_hybrid_summary_20260501T1837Z.md`
- Qrels: `reports/rag_eval/r3_corpus_v2_qrels_20260501T1640Z.json`
- Reranker runtime profile: `reports/rag_eval/r3_reranker_profile_summary_20260501T1730Z.md`

Observed Expanded Pilot:

| Metric | Value |
| --- | ---: |
| Corpus v2 pilot docs | 25 |
| qrel prompts | 100 |
| qrel entries | 296 |
| forbidden entries | 0 |
| Korean-only prompts | 16 |
| mixed Korean/English prompts | 84 |
| candidate_recall_primary@20 | 1.0000 |
| candidate_recall_primary@100 | 1.0000 |
| candidate_recall_relevant@5 | 0.9600 |
| reranked final_hit_relevant@5 | 1.0000 |
| reranked final_hit_relevant@20 | 1.0000 |
| reranked forbidden_rate@5 | 0.0000 |
| harmful lost_top20_rate | 0.0000 |
| source eval elapsed | 904.33s |

Current Provisional Gates:

| Gate | Threshold | Current | Status |
| --- | ---: | ---: | --- |
| expanded qrel prompts | >= 100 reviewed prompts | 100 | pass |
| mixed Korean/English prompts | >= 60, reflecting actual learner query style | 84 | pass |
| Korean-only prompts | monitor, not cutover-blocking unless observed traffic needs it | 16 | monitor |
| candidate_recall_primary@20 | >= 0.99 overall and per language bucket | 1.0000 | pass |
| candidate_recall_primary@100 | 1.00 overall | 1.0000 | pass |
| reranked final_hit_relevant@5 | >= 0.97 overall and >= 0.95 per language bucket | 1.0000 | pass |
| reranked final_hit_relevant@20 | 1.00 overall | 1.0000 | pass |
| forbidden_rate@5 | 0.00 | 0.0000 | pass |
| harmful lost_top20_rate | <= 0.02 | 0.0000 | pass |
| local full-mode runtime | accepted M5 profile or explicit long-lived runtime decision | 904.33s/100 cold batch | block |
| remote artifact import | strict manifest verifies locally | pending | block |

Decision:

R3 quality gates now pass on the expanded 100q pilot. Do not cut over by default yet. The remaining cutover blockers are local full-mode runtime architecture and strict remote artifact import verification.

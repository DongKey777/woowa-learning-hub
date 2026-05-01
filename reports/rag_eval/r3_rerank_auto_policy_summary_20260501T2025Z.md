# R3 Rerank Auto Policy Summary - 2026-05-01T20:25Z

Scope: 100q Corpus v2 gate for the R3 local default rerank policy.

Evidence:

- `reports/rag_eval/r3_backend_compare_100q_sidecar_auto_policy_20260501T2025Z.json`
- `reports/rag_eval/r3_daemon_full_runtime_auto_sidecar_smoke_20260501T2005Z.json`
- forced reranker quality reference: `reports/rag_eval/r3_backend_compare_100q_lexical_sidecar_rich_fusion_reranker_window20_20260501T1955Z.json`

Result:

| Metric | Value |
|---|---:|
| qrel prompts | 100 |
| Korean-only prompts | 16 |
| mixed Korean/English prompts | 84 |
| backend spec `use_reranker` | `null` |
| R3 policy | `auto` |
| auto sidecar skip count | 100 |
| rerank stage count | 0 |
| metadata lexical sidecar docs | 27170 |
| candidate_recall_relevant@5 | 1.0000 |
| candidate_recall_relevant@20 | 1.0000 |
| candidate_recall_relevant@100 | 1.0000 |
| final_hit_relevant@5 | 1.0000 |
| Korean-only final_hit_relevant@5 | 1.0000 |
| mixed Korean/English final_hit_relevant@5 | 1.0000 |
| final_hit_primary@5 | 0.9900 |
| forbidden_rate@5 | 0.0000 |

Decision:

Keep `BAAI/bge-reranker-v2-m3` as the R3 target quality reranker, but do not
make it the default local interactive stage when the verified metadata lexical
sidecar is present. The local default is now sidecar-first `auto`: preserve
dense, sparse, lexical sidecar, and signal candidate discovery, then skip the
cross-encoder when the 100q gate shows no relevant@5 regression and the local
daemon smoke shows warm latency around 500ms.

Forced reranking remains available for quality experiments and suspected
ranking failures through explicit `use_reranker=True` or
`WOOWA_RAG_R3_RERANK_POLICY=always`. `WOOWA_RAG_R3_RERANK_POLICY=off` remains
reserved for controlled latency or candidate-discovery tests.

# R3 Gate Proposal - 2026-05-01T17:18Z

Scope: provisional Phase 4a gate proposal after wiring the R3 runtime retrieval fabric: lexical sidecar, Lance dense vector search, BGE-M3 sparse sidecar, signal retrieval, and fusion. This is not a production cutover decision.

Evidence:

- Qrels: `reports/rag_eval/r3_corpus_v2_qrels_20260501T1640Z.json`
- Backend summary: `reports/rag_eval/r3_backend_compare_retrieval_fabric_summary_20260501T1718Z.json`
- Fabric: R3 full mode emitted 100 dense candidates and `bge_m3_sparse_vec_sidecar` for every pilot query.
- Pilot coverage: 52 qrel prompts from the current 13-document Corpus v2 seed.

Observed Pilot Metrics:

| Metric | Pilot Value |
| --- | ---: |
| dense candidates per query | 100 |
| sparse sidecar document count | 27,162 |
| sparse query term range | 5-14 |
| candidate_recall_primary@5 | 0.9423 |
| candidate_recall_primary@20 | 1.0000 |
| candidate_recall_primary@50 | 1.0000 |
| candidate_recall_primary@100 | 1.0000 |
| final_hit_primary@5 | 0.9423 |
| forbidden_rate@5 | 0.0000 |
| missing_candidate_primary_query_ids | 0 |
| missing_final_primary_query_ids | 0 |

Language split:

| Language | Total | candidate_recall_primary@5 | candidate_recall_primary@20 | forbidden_rate@5 |
| --- | ---: | ---: | ---: | ---: |
| ko | 10 | 1.0000 | 1.0000 | 0.0000 |
| mixed | 42 | 0.9286 | 1.0000 | 0.0000 |

Provisional Gates For The Next Expanded Pilot:

| Gate | Threshold | Why |
| --- | ---: | --- |
| qrel coverage | >= 100 reviewed prompts | Current 52-prompt pilot is useful but too small for cutover. |
| Korean + mixed coverage | each >= 30 prompts | The learner routinely mixes Korean and English. |
| candidate_recall_primary@20 | >= 0.99 overall and per language bucket | Current pilot reaches 1.0; this is the first-stage discovery gate. |
| candidate_recall_primary@100 | 1.00 overall | A primary doc missing from top 100 is a structural candidate-discovery failure. |
| forbidden_rate@5 | 0.00 | Confusable concepts must not surface forbidden neighbors in the learner-facing top window. |
| missing_candidate_primary_query_ids | [] | Every missing primary must be root-caused before expanding corpus or cutting over. |
| reranker_demotion_rate | measured and explainable by language/level | Cutover cannot rely on stronger reranking if the reranker demotes Korean/beginner primaries. |
| cheap tier smoke | first relevant doc stable; no BGE-M3 load | Tier-1 definition questions must stay responsive in one-shot CLI use. |
| full tier runtime | measured with intended local profile | One-shot CLI full-mode latency includes model load and is not the accepted production profile. |

Runtime Notes:

- `bin/rag-ask "latency가 뭐야?" --rag-backend r3` returned tier 1, cheap mode, first path `contents/network/latency-bandwidth-throughput-basics.md`, about 1.6s in the measured smoke before dense full-mode wiring.
- `bin/rag-ask "RAG로 깊게 latency가 뭐야?" --rag-backend r3` returned tier 2, full mode, same first path, and lexical+dense+sparse provenance on the top hit.
- The backend comparison command took 93.35s in one-shot CLI/eval form. This measures current evaluation overhead, not accepted production full-mode latency.

Decision:

Use this proposal as the current Phase 4a gate for the next expanded pilot. Do not use it as a production cutover gate until the corpus pilot reaches at least 100 reviewed prompts, reranker demotion is measured, and the local M5 full-mode runtime profile is explicit.

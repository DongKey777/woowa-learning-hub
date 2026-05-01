# R3 Gate Proposal - 2026-05-01T19:06Z

Scope: expanded 100q Corpus v2 gate after dense discovery, BGE-M3 sparse sidecar discovery, metadata-only lexical sidecar artifact, SQL child-topic qrel calibration, hybrid RRF reranking, local daemon runtime, and verified 20-pair local rerank default.

Evidence:

- 50-pair hybrid reranker quality: `reports/rag_eval/r3_backend_compare_100q_reranker_hybrid_summary_20260501T1837Z.json`
- 20-pair hybrid reranker quality: `reports/rag_eval/r3_backend_compare_100q_reranker_hybrid_window20_summary_20260501T1855Z.json`
- Window-20 interpretation: `reports/rag_eval/r3_reranker_window20_summary_20260501T1855Z.md`
- Warm same-process runtime profile: `reports/rag_eval/r3_warm_full_runtime_profile_20260501T1848Z.md`
- Daemon window-20 runtime smoke: `reports/rag_eval/r3_daemon_full_runtime_window20_smoke_20260501T1906Z.md`
- Daemon sidecar window-20 runtime smoke: `reports/rag_eval/r3_daemon_full_runtime_sidecar_window20_smoke_20260501T2005Z.md`
- Sparse retriever cache runtime profile: `reports/rag_eval/r3_sparse_retriever_cache_profile_20260501T1915Z.md`
- Lexical sidecar gate: `reports/rag_eval/r3_lexical_sidecar_summary_20260501T1955Z.md`
- Strict artifact import smoke: `reports/rag_eval/r3_strict_artifact_import_smoke_20260501T1845Z.md`
- Remote strict harness dry run: `reports/rag_eval/r3_remote_strict_harness_dry_run_20260501T1911Z.md`

Observed Expanded Pilot:

| Metric | Value |
|---|---:|
| Corpus v2 pilot docs | 25 |
| qrel prompts | 100 |
| qrel entries | 296 |
| forbidden entries | 0 |
| Korean-only prompts | 16 |
| mixed Korean/English prompts | 84 |
| local rerank input window | 20 |
| candidate_recall_primary@20 | 1.0000 |
| candidate_recall_primary@100 | 1.0000 |
| candidate_recall_relevant@5 | 0.9600 |
| reranked final_hit_relevant@5 | 1.0000 |
| reranked final_hit_relevant@20 | 1.0000 |
| reranked forbidden_rate@5 | 0.0000 |
| harmful lost_top20_rate | 0.0000 |
| metadata lexical sidecar docs | 27170 |
| metadata lexical sidecar bytes | 26966603 |

Current Provisional Gates:

| Gate | Threshold | Current | Status |
|---|---:|---:|---|
| expanded qrel prompts | >= 100 reviewed prompts | 100 | pass |
| mixed Korean/English prompts | >= 60, reflecting actual learner query style | 84 | pass |
| Korean-only prompts | monitor, not cutover-blocking unless observed traffic needs it | 16 | monitor |
| candidate_recall_primary@20 | >= 0.99 overall and per language bucket | 1.0000 | pass |
| candidate_recall_primary@100 | 1.00 overall | 1.0000 | pass |
| reranked final_hit_relevant@5 | >= 0.97 overall and >= 0.95 per language bucket | 1.0000 | pass |
| reranked final_hit_relevant@20 | 1.00 overall | 1.0000 | pass |
| forbidden_rate@5 | 0.00 | 0.0000 | pass |
| harmful lost_top20_rate | <= 0.02 | 0.0000 | pass |
| metadata lexical sidecar | remote-prebuilt, body terms excluded, no reranker quality regression | pass | pass |
| local long-lived runtime architecture | daemon path exists and reports R3 debug fields | pass | pass |
| local full-mode latency | accepted M5 interactive budget | sidecar cold 18.33s, warm 2.65-2.68s internal latency | review |
| strict artifact import contract | strict manifest + checksum + extracted index manifest verify locally | local artifact pass | pass |
| remote harness strict gate | R3 remote build must strict-package and verify downloaded artifact before success | dry-run + unit pass | pass |
| actual remote artifact import | RunPod-built artifact verifies with the same strict contract | pending remote run | block |

Decision:

R3 quality gates pass on the expanded 100q pilot with the 20-pair local rerank default. The root cause of one-shot CLI cold start is addressed by `bin/rag-daemon` and `bin/rag-ask --via-daemon`; runtime metadata now proves backend, reranker, sparse sidecar, rerank window, sparse retriever cache state, and per-stage timing in the learner-facing JSON.

Do not cut over by default yet. Remaining blockers are an explicit local latency acceptance decision for about 2.4-2.6s warm full-mode responses, and an actual RunPod-built artifact verified with the strict import contract. The remote harness now enforces strict R3 packaging and local import verification before reporting success, but a live RunPod run is still blocked in this environment because `RUNPOD_API_KEY` is unset. If the accepted latency budget is below 2.6s, the next root-cause track is reranker serving optimization or a locally validated smaller/distilled multilingual reranker, not disabling sparse or weakening candidate discovery.

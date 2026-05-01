# R3 Reranker Runtime Profile - 2026-05-01T17:30Z

Scope: local Apple Silicon probe for the R3 reranker chain. This is a small-pair runtime feasibility check, not a final quality A/B.

Artifacts:

- Target cold-ish probe: `reports/rag_eval/r3_reranker_profile_bge_v2_m3_20260501T1720Z.json`
- Target warm 5-pair probe: `reports/rag_eval/r3_reranker_profile_bge_v2_m3_warm_20260501T1724Z.json`
- Target warm 50-pair probe: `reports/rag_eval/r3_reranker_profile_bge_v2_m3_50pairs_20260501T1725Z.json`
- Current fallback 50-pair probe: `reports/rag_eval/r3_reranker_profile_mmarco_50pairs_20260501T1726Z.json`
- GTE failure record: `reports/rag_eval/r3_reranker_profile_gte_multilingual_failure_20260501T1730Z.json`

Observed Runtime:

| Model | Pairs | Load ms | Score ms | Per-pair p95 ms | RSS peak MB | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `BAAI/bge-reranker-v2-m3` | 5 | 230555.805 | 501.481 | 228.169 | 2612.719 | first run included download/cache fill |
| `BAAI/bge-reranker-v2-m3` | 5 | 8941.358 | 299.633 | 106.509 | 1050.188 | warm load succeeds |
| `BAAI/bge-reranker-v2-m3` | 50 | 8034.831 | 1350.097 | 24.898 | 1021.391 | R3 local window probe succeeds |
| `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | 50 | 7718.835 | 504.426 | 7.669 | 1026.938 | operational fallback succeeds |
| `Alibaba-NLP/gte-multilingual-reranker-base` | 5 | n/a | n/a | n/a | n/a | failed on default and CPU paths |

Decision:

- Keep `BAAI/bge-reranker-v2-m3` as the R3 target reranker.
- Use `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` as the verified Korean/mixed operational fallback for now.
- Remove `Alibaba-NLP/gte-multilingual-reranker-base` from the default fallback chain until its custom-code inference path is fixed and successfully profiled.

Cutover Implication:

The target reranker fits the 16GB memory constraint in this small probe, but full-mode one-shot CLI latency still includes model load. Production cutover still requires reranker demotion metrics on the expanded qrels and an accepted long-lived or otherwise amortized local runtime profile.

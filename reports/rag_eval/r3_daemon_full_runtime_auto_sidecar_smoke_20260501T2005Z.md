# R3 Daemon Auto Sidecar Smoke - 2026-05-01T20:05Z

Scope: learner-facing `bin/rag-ask --via-daemon` smoke after enabling the R3
default rerank policy `auto`.

Environment:

- `HF_HUB_OFFLINE=1`
- `WOOWA_RAG_R3_RERANK_POLICY=auto`
- backend: `r3`
- local target: M5 MacBook Air 13, 16GB unified memory

Observed:

| Prompt | Latency | Reranker | Policy | Skip reason | Sidecar docs |
|---|---:|---|---|---|---:|
| `RAG로 깊게 latency가 뭐야?` | 12296ms | off | auto | `policy_auto_sidecar_first_stage_gate` | 27170 |
| `RAG로 깊게 TCP 3-way handshake가 뭐야?` | 476ms | off | auto | `policy_auto_sidecar_first_stage_gate` | 27170 |

The first request still pays process-local BGE-M3 encoder load, Lance document
prefetch, sparse sidecar load, and metadata lexical sidecar load. The warm
daemon request stays below 500ms because the verified lexical sidecar lets the
local default skip cross-encoder reranking without disabling dense or sparse
candidate discovery.

Quality reference: `reports/rag_eval/r3_backend_compare_100q_sidecar_auto_policy_20260501T2025Z.json`
shows `use_reranker=null`, policy `auto`, skip reason
`policy_auto_sidecar_first_stage_gate` for all 100 qrels, no rerank stage, and
`final_hit_relevant@5=1.0` overall, Korean-only, and mixed Korean/English.

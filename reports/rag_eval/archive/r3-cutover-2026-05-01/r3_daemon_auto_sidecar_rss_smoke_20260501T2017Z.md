# R3 Daemon Auto Sidecar RSS Smoke - 2026-05-01T20:17Z

Scope: selected local production candidate memory check for the R3 default
interactive path.

Environment:

- `HF_HUB_OFFLINE=1`
- `WOOWA_RAG_R3_RERANK_POLICY=auto`
- backend: `r3`
- transport: `bin/rag-ask --via-daemon`

Observed:

| Prompt | Latency | Reranker | Policy | Sidecar |
|---|---:|---|---|---|
| `RAG로 깊게 latency가 뭐야?` | 12344ms | off | auto | loaded |
| `RAG로 깊게 TCP 3-way handshake가 뭐야?` | 473ms | off | auto | loaded |

Process memory after the warm request:

- daemon pid: `99341`
- RSS: `3022384 KB` = `2951.547 MB`
- VSZ: `448424240 KB`

Interpretation:

The selected local default path fits the M5 16GB memory constraint with a warm
daemon RSS around 3GB while preserving BGE-M3 dense/sparse query encoding and
the metadata lexical sidecar. Cross-encoder reranking was not loaded in this
default auto-sidecar path.

# R3 Lexical Sidecar Gate - 2026-05-01T19:55Z

Source JSON:

- Retrieval-only: `reports/rag_eval/r3_backend_compare_100q_lexical_sidecar_retrieval_20260501T1930Z.json`
- Reranker gate: `reports/rag_eval/r3_backend_compare_100q_lexical_sidecar_rich_fusion_reranker_window20_20260501T1955Z.json`

Build command:

```bash
HF_HUB_OFFLINE=1 \
  .venv/bin/python -m scripts.learning.rag.r3.index.lexical_sidecar \
  --index-root state/cs_rag
```

Artifact result:

| Metric | Value |
|---|---:|
| sidecar path | `state/cs_rag/r3_lexical_sidecar.json` |
| body terms included | false |
| document count | 27,170 |
| bytes | 26,966,603 |
| cold sidecar load stage | 4.25s |
| warm sidecar load stage | 0.14-0.17ms |

Design decision:

- Full-body JSON sidecar was rejected: it produced a 177,687,354 byte artifact and about 60.3s cold load time on local M5-class runtime.
- The accepted sidecar is metadata-only: `title`, `section`, and `aliases` are pre-tokenized remotely; body retrieval stays on the optimized Lance FTS/query-prefetch path.
- Sidecar candidates use their own retriever namespace (`lexical_sidecar:*`) with lower fusion weights, so they can add recall without taking over the primary body/dense/sparse ranking.
- Fusion now preserves the richest duplicate candidate metadata for reranking. This prevents body-less sidecar candidates from replacing body-bearing FTS/dense exemplars for the same chunk.

100q retrieval-only result:

| Metric | Value |
|---|---:|
| candidate_recall_relevant@5 | 1.0000 |
| candidate_recall_relevant@20 | 1.0000 |
| candidate_recall_relevant@100 | 1.0000 |
| forbidden_rate@5 | 0.0000 |

100q reranker gate result:

| Metric | Value |
|---|---:|
| rerank input window | 20 |
| final_hit_primary@5 | 0.9700 |
| final_hit_relevant@5 | 1.0000 |
| Korean-only final_hit_relevant@5 | 1.0000 |
| mixed Korean/English final_hit_relevant@5 | 1.0000 |
| final_hit_relevant@20 | 1.0000 |
| forbidden_rate@5 | 0.0000 |
| lost_top20_rate | 0.0000 |
| lost_top5_rate | 0.0200 |

Decision:

- Metadata-only lexical sidecar passes the current R3 window-20 quality gate after rich-exemplar fusion.
- The sidecar is now part of the strict R3 remote artifact contract; R3 packaging fails if `r3_lexical_sidecar.json` is missing.
- The remaining blocker is still live RunPod artifact import with the strict contract, not local sidecar correctness.

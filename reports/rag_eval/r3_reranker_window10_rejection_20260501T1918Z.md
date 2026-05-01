# R3 Reranker Window-10 Rejection - 2026-05-01T19:18Z

Source JSON: `reports/rag_eval/r3_backend_compare_100q_reranker_hybrid_window10_summary_20260501T1918Z.json`

Command:

```bash
HF_HUB_OFFLINE=1 WOOWA_RAG_R3_LOCAL_RERANK_INPUT_WINDOW=10 \
  .venv/bin/python -m scripts.learning.rag.r3.eval.backend_compare \
  --qrels reports/rag_eval/r3_corpus_v2_qrels_20260501T1640Z.json \
  --out reports/rag_eval/r3_backend_compare_100q_reranker_hybrid_window10_summary_20260501T1918Z.json \
  --backend r3 --top-k 100 --window 5 --window 10 --window 20 --window 100 --use-reranker
```

Key result:

| Metric | Value |
|---|---:|
| qrel prompts | 100 |
| mixed Korean/English prompts | 84 |
| Korean-only prompts | 16 |
| rerank input window | 10 |
| candidate_recall_primary@10 | 0.9900 |
| candidate_recall_primary@100 | 1.0000 |
| candidate_recall_relevant@5 | 0.9600 |
| final_hit_primary@5 | 0.9400 |
| final_hit_relevant@5 | 0.9800 |
| final_hit_relevant@20 | 1.0000 |
| forbidden_rate@5 | 0.0000 |
| lost_top20_rate | 0.0000 |

Language buckets:

| Bucket | Count | final_hit_relevant@5 | final_hit_primary@5 | lost_top20_rate |
|---|---:|---:|---:|---:|
| Korean-only | 16 | 0.9375 | 0.9375 | 0.0000 |
| Mixed Korean/English | 84 | 0.9881 | 0.9405 | 0.0000 |

Decision:

- Window 10 fails the local production gate because Korean-only `final_hit_relevant@5=0.9375`, below the `>=0.95` per-language floor.
- The local default must remain 20 pairs. Window 10 can stay as an opt-in profiling mode but must not become the learner laptop default.
- The result supports the current root-cause principle: reduce local latency only where quality gates remain green per language bucket, not just on aggregate metrics.

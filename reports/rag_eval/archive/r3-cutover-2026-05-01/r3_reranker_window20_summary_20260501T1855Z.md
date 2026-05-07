# R3 Reranker Window-20 Gate - 2026-05-01T18:55Z

Source JSON: `reports/rag_eval/r3_backend_compare_100q_reranker_hybrid_window20_summary_20260501T1855Z.json`

Command:

```bash
HF_HUB_OFFLINE=1 WOOWA_RAG_R3_LOCAL_RERANK_INPUT_WINDOW=20 \
  .venv/bin/python -m scripts.learning.rag.r3.eval.backend_compare \
  --qrels reports/rag_eval/r3_corpus_v2_qrels_20260501T1640Z.json \
  --out reports/rag_eval/r3_backend_compare_100q_reranker_hybrid_window20_summary_20260501T1855Z.json \
  --backend r3 --top-k 100 --window 5 --window 20 --window 50 --window 100 --use-reranker
```

Key result:

| Metric | Value |
|---|---:|
| qrel prompts | 100 |
| mixed Korean/English prompts | 84 |
| Korean-only prompts | 16 |
| rerank input window | 20 |
| candidate_recall_primary@20 | 1.0000 |
| candidate_recall_primary@100 | 1.0000 |
| candidate_recall_relevant@5 | 0.9600 |
| final_hit_primary@5 | 0.9200 |
| final_hit_relevant@5 | 1.0000 |
| final_hit_relevant@20 | 1.0000 |
| forbidden_rate@5 | 0.0000 |
| lost_top20_rate | 0.0000 |

Language buckets:

| Bucket | Count | final_hit_relevant@5 | final_hit_primary@5 | lost_top20_rate |
|---|---:|---:|---:|---:|
| Korean-only | 16 | 1.0000 | 1.0000 | 0.0000 |
| Mixed Korean/English | 84 | 1.0000 | 0.9048 | 0.0000 |

Decision:

- Window 20 preserves the expanded 100q relevant-answer gate previously achieved by the 50-pair hybrid reranker.
- Local default R3 rerank input should be 20 pairs on the learner M5 target.
- Window 50 remains a local profiling/comparator mode; window 100 remains offline-only.

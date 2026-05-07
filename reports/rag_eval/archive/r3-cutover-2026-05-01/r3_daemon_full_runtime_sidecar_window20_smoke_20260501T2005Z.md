# R3 Daemon Sidecar Window-20 Smoke - 2026-05-01T20:05Z

Source JSON: `reports/rag_eval/r3_daemon_full_runtime_sidecar_window20_smoke_20260501T2005Z.json`

Command:

```bash
HF_HUB_OFFLINE=1 bin/rag-daemon start
HF_HUB_OFFLINE=1 bin/rag-ask "<prompt>" --rag-backend r3 --via-daemon
bin/rag-daemon stop
```

Result:

| Prompt | latency_ms | sidecar load | sparse cache | rerank |
|---|---:|---:|---|---:|
| `latency가 뭐야?` | 18333 | 4261.259ms | false | 5135.276ms |
| `Spring Bean lifecycle 설명해줘` | 2652 | 0.162ms | true | 1954.586ms |
| `transaction isolation이 왜 필요해?` | 2678 | 0.157ms | true | 2101.289ms |

Interpretation:

- Metadata lexical sidecar is cold-loaded once, then reused inside the daemon.
- Warm full-mode latency with sidecar remains about 2.65-2.68s on this local machine.
- The dominant warm bottleneck is still `BAAI/bge-reranker-v2-m3` cross-encoder scoring, not sidecar load, sparse loading, or fusion.
- The daemon was stopped after the smoke.

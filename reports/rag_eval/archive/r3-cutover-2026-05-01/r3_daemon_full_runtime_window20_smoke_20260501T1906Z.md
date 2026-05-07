# R3 Daemon Full Runtime Smoke - 2026-05-01T19:06Z

Command shape:

```bash
HF_HUB_OFFLINE=1 bin/rag-daemon start
bin/rag-ask "<prompt>" --rag-backend r3 --via-daemon
```

Source JSON: `reports/rag_eval/r3_daemon_full_runtime_window20_smoke_20260501T1906Z.json`

| Query | Client wall | `hits.meta.latency_ms` | First path | Window |
|---|---:|---:|---|---:|
| `RAG로 깊게 latency가 뭐야?` | 15.41s | 15174 | `contents/network/latency-bandwidth-throughput-basics.md` | 20 |
| `RAG로 깊게 DI랑 Service Locator 차이가 뭐야?` | 3.97s | 3477 | `contents/design-pattern/service-locator-antipattern.md` | 20 |
| `RAG로 깊게 Transactional이 안 먹을 때 먼저 뭘 봐야 해?` | 3.94s | 3742 | `contents/spring/README.md` | 20 |

Runtime proof from `hits.meta.runtime_debug`:

- backend: `r3`
- mode: `full`
- reranker enabled: `true`
- reranker model: `BAAI/bge-reranker-v2-m3`
- rerank input window: `20`
- sparse source: `bge_m3_sparse_vec_sidecar`
- sparse sidecar document count: `27170`
- dense candidate count: `100`

Decision:

- The local daemon fixes the one-shot CLI cold-start architecture by keeping model caches in a long-lived process.
- The 20-pair local window reduces warm full latency from the earlier 6-7s range to about 4s on the mixed Korean/English smoke prompts.
- Runtime is improved but not yet a final default cutover pass if the accepted interactive budget is below about 4s.

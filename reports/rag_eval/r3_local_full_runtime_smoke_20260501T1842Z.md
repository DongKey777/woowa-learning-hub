# R3 Local Full Runtime Smoke - 2026-05-01T18:42Z

Command:

`bin/rag-ask "RAG로 깊게 latency가 뭐야?" --rag-backend r3`

Precondition:

The SQL qrel/frontmatter edit made the index stale. Incremental rebuild completed first: chunk_count=27170, added=1, modified=12, encoded=13, Lance version 8->9, elapsed 19.7s.

Observed:

| Item | Value |
| --- | ---: |
| decision tier | 2 |
| mode | full |
| backend | r3 |
| hits.meta latency_ms | 22162 |
| `/usr/bin/time` real | 23.34s |
| first hit | `contents/network/latency-bandwidth-throughput-basics.md` |
| first hit score | 0.03278689 |


Cheap Mode Control:

| Item | Value |
| --- | ---: |
| command | `bin/rag-ask "latency가 뭐야?" --rag-backend r3` |
| decision tier | 1 |
| mode | cheap |
| hits.meta latency_ms | 1835 |
| `/usr/bin/time` real | 2.42s |
| first hit | `contents/network/latency-bandwidth-throughput-basics.md` |

Interpretation:

- Quality smoke passes: the latency primer is first, and the score is the hybrid RRF reranker score.
- One-shot full runtime does not pass the interactive default cutover bar. A full R3 turn loads BGE-M3 query encoding and the BGE reranker in-process, so cold CLI execution took about 22 seconds.
- R3 should still keep cheap mode for Tier 1. Tier 2/full needs a long-lived or otherwise amortized local runtime before default cutover.

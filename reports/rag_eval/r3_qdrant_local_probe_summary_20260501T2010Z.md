# R3 Qdrant Local Probe Summary - 2026-05-01T20:10Z

Scope: optional Qdrant backend spike using the current LanceDB v3 artifact as
source data. The probe mirrored all 27,170 chunks into an in-memory Qdrant
collection with named dense and sparse vectors, then evaluated the 100q Corpus
v2 qrels with dense+sparse RRF.

Evidence:

- machine report: `reports/rag_eval/r3_qdrant_local_probe_100q_20260501T2010Z.json`
- implementation: `scripts/learning/rag/r3/eval/qdrant_local_probe.py`
- Qdrant sparse vector API reference used for the spike: https://qdrant.tech/documentation/manage-data/vectors/

Observed:

| Metric | Value |
|---|---:|
| loaded points | 27170 |
| dense dim | 1024 |
| Qdrant client | 1.17.1 |
| Lance point load | 2094.716ms |
| Qdrant local collection build | 9128.248ms |
| RSS peak after build | 2509.578MB |
| RSS peak after eval | 3398.422MB |
| dense query p95 | 19.210ms |
| sparse query p95 | 302.123ms |
| candidate_recall_primary@100 | 1.0000 |
| candidate_recall_primary@20 | 0.9900 |
| candidate_recall_primary@5 | 0.9100 |
| candidate_recall_relevant@5 | 0.9400 |
| Korean-only candidate_recall_relevant@5 | 0.8750 |
| mixed Korean/English candidate_recall_relevant@5 | 0.9524 |
| forbidden_rate@5 | 0.0000 |

Runtime note:

Qdrant local mode emitted a warning after the collection exceeded 20,000
points: local mode is not recommended for collections larger than that and
Docker or Cloud should be considered. Docker CLI is installed locally, but the
Docker daemon was not running during this spike, so server-mode measurement was
not available in this environment.

Decision implication:

Qdrant remains a valid comparator and future option, but it is not the first
local production candidate for the learner's M5 16GB target. The current R3
Lance-improved path with BGE-M3 sparse sidecar, metadata lexical sidecar, and
auto rerank policy has stronger local evidence: `final_hit_relevant@5=1.0`
overall/Korean/mixed and warm daemon latency of 476ms without adding a required
Docker/server dependency.

# R3 Corpus v2 C1-C5 Expansion Gate - 2026-05-01T20:25Z

Purpose: close the broad Corpus v2 pilot gap by expanding from 25 to 30
frontmatter-backed documents, regenerating qrels, and validating the selected
R3 auto-sidecar path against the enlarged cohort.

## Corpus Changes

- Corpus v2 document count: 30
- Qrel count: 120
- Added v2 frontmatter to one existing high-value document per wave:
  - C1 design-pattern chooser:
    `contents/design-pattern/template-method-vs-strategy.md`
  - C2 Spring DI/Bean/router/qualifier:
    `contents/spring/spring-primary-qualifier-collection-injection-decision-guide.md`
  - C3 projection freshness/read-model/stale-read:
    `contents/design-pattern/read-model-staleness-read-your-writes.md`
  - C4 MVCC/isolation/locking/transaction:
    `contents/database/mvcc-read-view-consistent-read-internals.md`
  - C5 auth session/cookie/JWT/Spring Security:
    `contents/security/session-cookie-jwt-basics.md`
- Normalized 4 pre-existing Corpus v2 `doc_role` values to the current lint
  enum.
- Fixed 17 pre-existing broken relative links so corpus link integrity is clean.

## Verification Commands

```bash
rg -l "schema_version: 2" knowledge/cs/contents -g '*.md' | wc -l
.venv/bin/python -m scripts.learning.rag.corpus_lint --corpus knowledge/cs/contents
.venv/bin/python -m scripts.learning.rag.r3.eval.qrels \
  --corpus-root knowledge/cs \
  --out reports/rag_eval/r3_corpus_v2_qrels_20260501T2025Z.json
HF_HUB_OFFLINE=1 .venv/bin/python -m scripts.learning.rag.r3.eval.backend_compare \
  --qrels reports/rag_eval/r3_corpus_v2_qrels_20260501T2025Z.json \
  --out reports/rag_eval/r3_backend_compare_120q_corpus_wave_20260501T2025Z.json \
  --backend r3 --top-k 100 --window 5 --window 20 --window 100
```

Full backend trace size was 71 MB, so the committed evidence is the compact
summary:

- `reports/rag_eval/r3_backend_compare_120q_corpus_wave_20260501T2025Z.summary.json`
- `reports/rag_eval/r3_corpus_v2_qrels_20260501T2025Z.json`

## Results

Corpus lint:

```text
[corpus-lint] scanned 2274 files
[corpus-lint] OK - no violations
```

R3 auto-sidecar backend comparison:

| Metric | Overall | Korean-only | Mixed |
|---|---:|---:|---:|
| query count | 120 | 19 | 101 |
| candidate_recall_relevant@5 | 1.0000 | 1.0000 | 1.0000 |
| candidate_recall_relevant@20 | 1.0000 | 1.0000 | 1.0000 |
| candidate_recall_relevant@100 | 1.0000 | 1.0000 | 1.0000 |
| candidate_recall_primary@5 | 0.9833 | 1.0000 | 0.9802 |
| candidate_recall_primary@20 | 1.0000 | 1.0000 | 1.0000 |
| final_hit_relevant@5 | 1.0000 | 1.0000 | 1.0000 |
| final_hit_primary@5 | 0.9833 | 1.0000 | 0.9802 |
| forbidden_rate@5 | 0.0000 | 0.0000 | 0.0000 |

Level split:

| Level | Count | final_hit_relevant@5 | final_hit_primary@5 |
|---|---:|---:|---:|
| beginner | 84 | 1.0000 | 0.9762 |
| intermediate | 16 | 1.0000 | 1.0000 |
| advanced | 20 | 1.0000 | 1.0000 |

Runtime path:

- lexical sidecar used: 120 / 120
- sparse sidecar document count: 27,170
- lexical sidecar document count: 27,170
- rerank policy: `auto` for 120 / 120
- reranker skip reason: `policy_auto_sidecar_first_stage_gate` for 120 / 120

## Decision

Pass for the Corpus v2 C1-C5 expansion gate.

The enlarged 30-doc / 120-qrel pilot preserves relevant recall at every measured
window, has no forbidden-neighbor regression, keeps Korean-only and mixed
queries represented, and confirms the selected R3 auto-sidecar local path still
uses candidate discovery without loading the reranker.

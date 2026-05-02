# RAG R3 High-Performance Retrieval + Corpus Plan - 2026-05-02

Purpose: external-review packet for diagnosing and redesigning the CS RAG system toward maximum retrieval quality, without assuming a backend rebuild before root-cause evidence exists.

Review target: another AI or engineer should be able to read this file without session context and answer:

1. Is the proposed architecture the right direction for highest retrieval quality?
2. Are the corpus/schema requirements sufficient to prevent quality regressions as the corpus grows?
3. Are the phases and gates concrete enough to execute safely?

Time basis:

- Local system facts were inspected from this repository on 2026-05-02 KST.
- External search/ranking references were checked on 2026-05-02, with emphasis on public information available by 2026-04.
- Where this document infers a direction from evidence, it labels that direction as a recommendation rather than a measured fact.

## Executive Decision

Recommended direction: build an R3 retrieval fabric and staged corpus v2 contract. The R3/V3 architecture is the design anchor; insert a 4-5 day diagnostic phase to calibrate implementation priorities, not to veto the redesign.

Do not continue by only tuning sparse weight, IVF parameters, or reranker choice. The current system's main limitation is upstream of reranking: several relevant documents are not reliably discovered by the Lance candidate layer, and `sparse` is implemented as late rescore over an existing FTS+dense pool instead of an independent retrieval channel.

Reviewer revision:

- R3/V3 is the target architecture direction because the current problem is structural: candidate discovery, field-aware retrieval, sparse discovery, corpus metadata, traceability, and reranker isolation must be designed together.
- Legacy v2 is only a rollback/safety reference. It must not become the quality truth for the redesigned system.
- Current Lance v3 and legacy v2 measurements are symptom snapshots from an imperfect implementation and qrel fixture. Use them to find failure modes, not to decide the final design.
- The diagnostic phase prioritizes the redesign work and prevents carrying old defects forward. It is not a reason to settle for small tuning if the target is a fundamentally stronger system.

R3 should optimize for:

- independent candidate discovery from lexical, dense, true sparse, signal, and metadata sources;
- optional late-interaction/multivector reranking after candidate recall is fixed;
- graph/link expansion for context assembly and companion docs, not as a first-stage requirement;
- stage-level observability, especially candidate recall before rerank;
- corpus authoring that proves which metadata fields improve retrieval before broad migration;
- side-by-side backend evaluation before any production cutover.

R3 target reranker:

- target default: `BAAI/bge-reranker-v2-m3`;
- Korean/mixed-language fallback: `Alibaba-NLP/gte-multilingual-reranker-base` or another locally verified multilingual reranker;
- compatibility fallback: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`;
- English-only low-memory candidate: `mixedbread-ai/mxbai-rerank-base-v1`, but never as automatic fallback for Korean or mixed queries;
- prerequisite: patch reranker input sizing so the target reranker can score calibrated top-K pools instead of the current `top_k * 2` window.

Default backend recommendation after the first implementation spike:
LanceDB-improved R3 as the local production candidate; Qdrant remains the
measured dense+sparse comparator, and Vespa remains a high-ceiling comparator,
not the default.

Reasoning:

- Qdrant is a strong dense+sparse+multivector option and a simpler operational candidate for this corpus size.
- LanceDB remains useful as a local/offline artifact and vector/FTS baseline if we add true sparse discovery through a sidecar or proven native path.
- Vespa is strongest when retrieval, ranking features, phased ranking, BM25, vectors, and result diversity need to be controlled together, but the JVM/YQL/service-operation cost is probably too high as the first move for a local learning hub.

Implementation update after R3 spike:

- Backend decision: `docs/worklogs/rag-r3-backend-decision-2026-05-02.md`.
- First production candidate is now LanceDB-improved R3, not Qdrant:
  LanceDB v3 artifact + BGE-M3 dense retrieval + BGE-M3 sparse first-stage
  sidecar + metadata lexical sidecar + signal retriever + deterministic fusion
  + sidecar-first `auto` rerank policy.
- Qdrant remains a measured comparator. The 100q local-mode spike reached
  `candidate_recall_primary@100=1.0`, but local mode warned above 20,000
  points, RSS peak reached 3398.422MB, sparse query p95 was 302.123ms, and
  Korean-only relevant@5 trailed the selected R3 path.
- `BAAI/bge-reranker-v2-m3` remains the target quality reranker. Local
  interactive default is now `WOOWA_RAG_R3_RERANK_POLICY=auto`: force the BGE
  reranker for quality investigation or suspected ranking failures. The local
  default skips it when the verified metadata lexical sidecar is loaded and the
  208q production gate stays green.
- Cutover artifact: `r3-0c8fd9f-2026-05-02T0827`, built on RunPod L40S from
  commit `0c8fd9f1bef5c3dd5b0bdd7a420bf5f60668d2ed`, imported into local
  `state/cs_rag`, and selected in `config/rag_models.json`.
- Expanded qrel gate:
  `reports/rag_eval/r3_backend_compare_208q_production_r3_auto_20260502T0845Z.summary.json`
  reports candidate and final primary/relevant hit/recall at 5/20/50/100 as
  `1.0` overall and for Korean/mixed-language cohorts, with `forbidden_rate@5=0`.
- Root-cause closure: Corpus v2 `expected_queries` are now indexed as
  retrieval-contract anchors and chunk body phrases. The previously failing
  service-locator query `컨테이너에서 직접 꺼내 쓰면 왜 위험해?` is now recovered
  to final rank 1.
- Local smoke:
  `reports/rag_eval/r3_0c8fd9f_local_smoke_20260502T0852Z.json` verifies
  sparse sidecar discovery, daemon warm full latency of 1169ms, and a forced
  `BAAI/bge-reranker-v2-m3` path with 20-pair reranking.

## Current System Facts

Current production/cutover state is documented across:

- `docs/worklogs/rag-r2-cutover-2026-05-01.md`
- `docs/worklogs/rag-v6-2-external-review-packet-2026-05-01.md`
- `reports/rag_eval/next_improvement_decision_20260501T1700Z.md`
- `reports/rag_eval/sparse_effect_analysis_20260501T1455Z.md`
- `config/rag_models.json`
- `docs/cs-rag-internals.md`
- `docs/rag-runtime.md`

Observed current index/runtime:

- backend: LanceDB v3
- model: `BAAI/bge-m3`
- row count: `27158`
- indexed corpus root: `knowledge/cs`
- indexed scope: `knowledge/cs/contents/**.md`
- runtime default modalities: `fts,dense,sparse`
- cheap mode: `fts`
- current runtime reranker: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`
- R3 target reranker: `BAAI/bge-reranker-v2-m3`
- default top-k: `5`
- Lance candidate pool size: `max(FTS_POOL_SIZE, top_k * 20)`, with `FTS_POOL_SIZE=80`

Current corpus scale:

- `knowledge/cs/contents`: `2274` markdown documents
- index chunks: `27157`
- largest categories by document count:
  - `language`: 307
  - `database`: 297
  - `software-engineering`: 237
  - `network`: 224
  - `spring`: 212
  - `data-structure`: 193
  - `security`: 184
  - `operating-system`: 182
  - `system-design`: 179
  - `design-pattern`: 174
  - `algorithm`: 85

Current code-level retrieval shape:

```text
Lance FTS over prompt
+ Lance dense vector search
-> RRF merge
-> optional sparse dot-product rescore over already-found candidates
-> optional ColBERT rescore when explicitly requested
-> category/difficulty/signal boost
-> category filter
-> cross-encoder rerank
-> doc-level dedupe
-> top-k
```

Critical implementation facts:

- `scripts/learning/rag/searcher.py::_lance_candidate_pool` adds FTS and dense rankings, then calls `_sparse_rescore` only after RRF.
- `scripts/learning/rag/indexer.py::_lance_records` stores `sparse_vec` as row payload: `{indices, values}`.
- `scripts/learning/rag/indexer.py::_create_lance_indices` creates dense, FTS, and ColBERT index metadata, but no native sparse retrieval index.
- `scripts/learning/rag/corpus_loader.py::_emit_chunks` appends document-level retrieval anchors to every chunk body, which helps lexical recall but can blur dense semantic representation.
- `scripts/learning/rag/searcher.py` still sends only `top_k * 2` candidates to the reranker in both legacy and Lance paths, so any top-50 local or top-100 offline reranker experiment requires a code patch before it has real effect.

## Current Measurement Snapshot - Diagnostic Only

Latest evidence from post-cutover reports. Treat these numbers as current-system symptoms, not as final architecture evidence:

| Runtime | primary nDCG@10 | graded nDCG@10 | MRR | hit@10 | recall@10 | hard failures |
|---|---:|---:|---:|---:|---:|---:|
| Legacy v2 archive holdout | 0.9890 | 0.9824 | 0.9901 | 1.0000 | 0.9950 | 2 |
| Lance v3 production holdout | 0.9135 | 0.9126 | 0.9307 | 0.9406 | 0.9191 | 10 |

Lance modality ablation:

| Modalities | primary nDCG macro | p95 warm | hard failures |
|---|---:|---:|---:|
| `fts` | 0.9143 | 463.1 ms | 11 |
| `fts,dense` | 0.9416 | 677.5 ms | 10 |
| `fts,dense,sparse` | 0.9416 | 736.7 ms | 10 |

Sparse effect analysis:

- `top10_changed_count`: 98/101
- `primary_rank_improved_count`: 0
- `primary_rank_worsened_count`: 0
- `lance_sparse_rescore` p95: about 4.6 ms

Interpretation:

- Sparse is active, but only changes candidate ordering inside the FTS+dense pool.
- Sparse has not shown measured lift on judged primary paths.
- Current reported "sparse" performance is not evidence for or against sparse retrieval as a first-stage candidate generator.
- These measurements are not trusted as final quality truth because they depend on the current fixture, current candidate path, current reranker input size, and current corpus metadata.

Failure-14 comparison:

| Metric | Legacy v2 | Lance v3 |
|---|---:|---:|
| primary at rank 1 | 12/14 | 10/14 |
| primary in top 10 | 14/14 | 13/14 |
| primary missing top 10 | 0/14 | 1/14 |
| top-1 cross-category | 0/14 | 1/14 |

Interpretation:

- Lance is often in the right family, but it still loses primary rank and sometimes misses the target entirely.
- The next diagnostic must identify whether each failure is candidate absence, fusion under-ranking, reranker demotion, dedupe loss, qrel strictness, or corpus gap.
- The hard failures are concentrated in Korean or Korean-first mixed prompts. The plan must diagnose Korean query handling before assuming that the root cause is backend architecture.

## External State As Of 2026-04

This section intentionally uses official docs and papers rather than social-media anecdotes.

### Vespa

Relevant public facts:

- Vespa hybrid search documentation distinguishes retrieval from ranking and demonstrates BM25 + vector retrieval.
- Vespa hybrid profiles include RRF and normalized linear strategies, and the docs emphasize evaluating rank profiles on the target dataset because the best hybrid strategy is dataset-specific.
- Vespa nearest-neighbor search can be combined with query terms and filters, and Vespa supports tensor fields, including multi-vector document representations.

Implication for this project:

- Vespa is the highest-control R3 candidate if we want production-grade BM25, vector retrieval, phased ranking, feature logging, metadata filters, and result diversity in one framework.
- It should be treated as a comparator or later production candidate unless the team accepts JVM/YQL/service operation overhead.

Primary references:

- https://docs.vespa.ai/en/learn/tutorials/hybrid-search
- https://docs.vespa.ai/en/querying/nearest-neighbor-search

### Qdrant

Relevant public facts:

- Qdrant's hybrid-search tutorial describes dense embeddings for semantic search, sparse embeddings for keyword search, and late interaction embeddings for reranking.
- Qdrant multivector docs recommend using dense vectors for fast candidate retrieval and ColBERT-style multivectors for token-level reranking, with HNSW disabled for rerank-only multivectors when appropriate.
- Qdrant sparse vectors are stored and indexed separately from dense vectors.

Implication for this project:

- Qdrant is the most pragmatic first R3 spike if we prioritize dense+sparse+multivector ergonomics with a simpler vector-engine operational model.
- It may still need an external lexical/BM25 layer or careful sparse setup if we need advanced Korean lexical control and field-level BM25 ranking.

Primary references:

- https://qdrant.tech/documentation/advanced-tutorials/reranking-hybrid-search/
- https://qdrant.tech/documentation/tutorials-search-engineering/using-multivector-representations/
- https://qdrant.tech/documentation/concepts/vectors/
- https://qdrant.tech/documentation/concepts/hybrid-queries/

### LanceDB

Relevant public facts:

- LanceDB markets one retrieval layer with native vector, full-text, and SQL hybrid search.
- LanceDB docs cover hybrid search over vector + FTS and GPU-powered vector indexing.
- In this project, LanceDB 0.30.2 capability probing recorded BGE-M3 sparse as `rescore_only` in our implementation, not native sparse discovery.

Implication for this project:

- LanceDB remains valuable for local/offline builds and fast artifact iteration.
- R3 should not assume LanceDB alone is enough unless it can pass the same candidate-recall and final-quality gates as Vespa/Qdrant alternatives.

Primary references:

- https://docs.lancedb.com/search/hybrid-search
- https://docs.lancedb.com/search/full-text-search
- https://docs.lancedb.com/indexing/gpu-indexing
- https://www.lancedb.com/lp/rag-hybrid-search

### BGE-M3 And Late-Interaction Research

Relevant public facts:

- BGE-M3 supports dense retrieval, sparse retrieval, and multi-vector retrieval in one multilingual model family.
- The BGE-M3 paper states support for 100+ languages and up to 8192-token inputs.
- Qdrant and BGE docs both treat late interaction / ColBERT-style representations as a higher-precision reranking signal.
- 2026 arXiv references on learned multi-vector retrieval and local-first hybrid retrieval exist, but they are not required to justify this plan and must not be treated as production evidence without local validation.

Implication for this project:

- BGE-M3 should be treated as a three-output retriever family, not merely "dense embedding plus optional sparse rescore".
- Multi-vector should first be introduced as rerank-over-candidates, then expanded only if latency and memory budgets allow.
- Hybrid disagreement can be used to mine hard negatives and qrel candidates.

Primary references:

- https://arxiv.org/abs/2402.03216
- https://huggingface.co/BAAI/bge-m3
- https://bge-model.com/bge/bge_m3.html

## Target R3 Architecture

R3 should separate candidate generation, fusion, reranking, and context assembly.

```text
Query Understanding
  -> language / category / intent / learner level / concept candidates
  -> alias and symptom expansion

Independent Candidate Generators
  -> LexicalRetriever
  -> DenseRetriever
  -> SparseRetriever
  -> SignalRetriever
  -> MetadataRanker
  -> optional GraphExpander for linked companion candidates

Fusion
  -> weighted RRF baseline
  -> field-aware and route-aware weights
  -> doc-diverse pool
  -> learned fusion after trace corpus exists

Reranking
  -> fast cross-encoder or late-interaction rerank over top-50 local / top-100 offline
  -> stronger reranker only for hard cases or offline validation

Context Assembly
  -> source-priority guard
  -> citation guard
  -> role/level guard
  -> linked-path companion expansion

Evaluation Loop
  -> candidate recall
  -> fusion lift
  -> reranker lift/demotion
  -> final nDCG/hit/forbidden rate
  -> failure taxonomy
  -> corpus/qrel update
```

Candidate schema:

```json
{
  "chunk_id": "stable chunk id",
  "doc_id": "stable doc id",
  "path": "contents/spring/example.md",
  "retriever": "sparse",
  "rank": 7,
  "raw_score": 9.12,
  "normalized_score": 0.73,
  "features": {
    "bm25_body": 0.0,
    "bm25_title": 0.0,
    "bm25_alias": 0.0,
    "dense_score": 0.0,
    "sparse_score": 9.12,
    "colbert_score": 0.0,
    "source_priority": 80,
    "doc_role": "primer",
    "level": "beginner",
    "category": "spring"
  }
}
```

Retriever contracts:

```python
class Retriever:
    name: str

    def retrieve(self, query: QueryPlan, *, limit: int) -> list[Candidate]:
        ...
```

Mandatory retrievers:

| Retriever | Purpose | First gate |
|---|---|---|
| `LexicalRetriever` | exact phrase, Korean terms, title/section/alias BM25 | improves candidate recall without forbidden regressions |
| `DenseRetriever` | semantic recall, mixed-language paraphrase | preserves current dense lift |
| `SparseRetriever` | BGE-M3 lexical sparse discovery | proves independent primary candidate additions |
| `SignalRetriever` | canonical docs from rule/concept signals | restores legacy signal path injection |
| `MetadataRanker` | doc role, level, source priority, category route | prevents beginner/deep-dive mixups |

Optional post-discovery components:

| Component | Purpose | First gate |
|---|---|---|
| `LateInteractionReranker` | ColBERT/BGE-M3 multivector precision after candidate recall is fixed | improves hard-query cohort without p95 budget breach |
| `GraphExpander` | linked paths, prerequisites, next docs | improves companion coverage during context assembly without displacing the primary |

## Concrete R3 Build Blueprint

This section is the implementation blueprint. It intentionally treats the current runtime as a migration source, not as the design center.

### Target Module Layout

Add or reshape the RAG package around explicit stages:

```text
scripts/learning/rag/r3/
  query_plan.py           # QueryPlan, route hints, language/category/intent/level
  candidate.py            # Candidate, CandidateFeature, RetrieverTrace
  pipeline.py             # end-to-end orchestration
  fusion.py               # weighted RRF, normalized feature fusion, diversity
  context.py              # source-priority/citation/context assembly
  config.py               # model ids, top-N windows, backend routes
  retrievers/
    lexical.py            # BM25/FTS sidecar over fields
    dense.py              # BGE-M3 dense retrieval
    sparse.py             # BGE-M3 sparse first-stage retrieval
    signal.py             # deterministic canonical path injection
    metadata.py           # role/level/source/category rank features
  rerankers/
    cross_encoder.py      # BAAI/bge-reranker-v2-m3 target, fallbacks
    late_interaction.py   # optional BGE-M3/ColBERT multivector rerank
  eval/
    trace.py              # trace writer/reader
    qrels.py              # acceptable/forbidden/primary qrel model
    metrics.py            # candidate/fusion/rerank/final metrics
    failure_taxonomy.py   # one primary class per hard failure
  index/
    qdrant_store.py       # dense/sparse/multivector store
    lexical_store.py      # SQLite FTS5/Tantivy sidecar
    manifest.py           # R3 manifest and reproducibility metadata
```

Existing `scripts/learning/rag/searcher.py` should become a compatibility adapter that can call the R3 pipeline behind a feature flag, instead of continuing to absorb new retrieval logic.

### QueryPlan Contract

Every search starts by turning raw learner text into a stable `QueryPlan`.

```json
{
  "query_id": "fixture id or generated hash",
  "raw_query": "스프링 MVC 뭐야",
  "normalized_query": "스프링 mvc 뭐야",
  "language": "ko",
  "category_hints": ["spring"],
  "intent": "definition",
  "learner_level": "beginner",
  "concept_candidates": ["spring/mvc"],
  "aliases": ["spring mvc", "스프링 mvc", "dispatcher servlet"],
  "symptoms": [],
  "must_include_paths": [],
  "forbidden_paths": [],
  "rerank_profile": "default_ko_beginner"
}
```

Implementation requirements:

- Korean query normalization is a first-class step, not a side effect of FTS.
- Query-side tokenization must mirror index-side tokenization for Korean fields.
- Signal expansion must write explicit `must_include_paths` or high-priority concept candidates instead of hidden boosts.
- QueryPlan version must be recorded in every trace and index manifest.

### Stage Pipeline

R3 runtime should execute the same stage order in production and evaluation:

```text
raw query
-> QueryPlanner
-> LexicalRetriever(limit=100)
-> DenseRetriever(limit=100)
-> SparseRetriever(limit=100)
-> SignalRetriever(limit=20)
-> MetadataRanker/features
-> Fusion(limit=120, doc_diversity=true)
-> Reranker(target=BAAI/bge-reranker-v2-m3, input=20 local default / 50 local profiling / 100 offline)
-> GraphExpander/context companions
-> ContextAssembler(top_k=5)
-> response/citation contract
```

Non-negotiable behavior:

- Sparse retrieval must be able to return a document absent from lexical+dense candidates.
- Reranking must never be hard-coded to `top_k * 2`; the input window is a profile setting.
- Local production reranking assumes Apple Silicon MPS and fp16/bf16-capable model loading. CPU-only operation is a degraded mode, not the target serving configuration.
- On the learner's M5 16GB machine, the default rerank input window is 20 pairs after the 2026-05-01 100q Corpus v2 gate preserved `final_hit_relevant@5=1.0`, `forbidden_rate@5=0`, and `lost_top20_rate=0` against the earlier 50-pair profile. 50-pair local reranking remains an explicit profiling mode; 100-pair reranking is reserved for offline evaluation.
- Heavy index/model-build work runs on remote GPU infrastructure. The resulting artifacts must be reproducible, manifest-versioned, and usable on the learner's local M5 machine without requiring local rebuild.
- Fusion must preserve retriever provenance so later analysis can say which retriever found or missed the primary.
- Context expansion cannot displace the primary answer document; it only adds companions.
- A workaround-only fix cannot close an R3 ticket. Any observed failure must be traced to a root cause class and fixed at that layer, with a regression check that would fail before the fix.

### Storage Decision For First Implementation

First production candidate:

```text
LanceDB improved
+ BGE-M3 dense retrieval
+ BGE-M3 sparse first-stage sidecar
+ metadata lexical sidecar
+ signal/query-planning features
+ same R3 trace contract
```

Concrete default:

- LanceDB remains the storage artifact for dense vectors and body FTS.
- BGE-M3 sparse output is served through a true first-stage sidecar, not a
  late rescore over the FTS+dense pool.
- Metadata lexical sidecar stores title, section, aliases, and expected-query
  anchors separately from full body text so local cold load stays bounded.
- Korean and mixed Korean/English retrieval contract phrases are indexed from
  Corpus v2 `aliases` and `expected_queries`.
- Fusion happens in Python first so ranking features remain inspectable and
  backend-independent.

Comparator candidate:

```text
Qdrant dense+sparse store
+ lexical sidecar
+ external fusion/rerank pipeline
```

Qdrant remains useful for dense+sparse ergonomics and future multivector
experiments. It is not the current local default because the measured local
mode crossed the 20,000-point warning threshold, consumed about 3.4GB RSS in
the probe, and did not beat the selected LanceDB-improved R3 path on the
Korean-only relevant@5 gate.

Vespa comparator:

- Build only if Qdrant/Lance cannot meet the calibrated R3 gates or if phased ranking/feature logging becomes worth the operational cost.

### Model Stack Decision

Target model stack:

| Role | Default | Fallback | Why |
|---|---|---|---|
| dense encoder | `BAAI/bge-m3` | Qwen3 embedding candidate after Korean diagnostic | unified multilingual dense/sparse/multivector output |
| sparse encoder | `BAAI/bge-m3` sparse output | local inverted sparse sidecar | true sparse first-stage retrieval |
| reranker | `BAAI/bge-reranker-v2-m3` | `gte-multilingual-reranker-base`, `mmarco`; `mxbai` only for English-only experiments | Korean-strong target reranker with language-aware operational fallback |
| late interaction | BGE-M3/ColBERT-style multivector | disabled | only after candidate recall and latency are acceptable |

The reranker decision is target-first: `bge-reranker-v2-m3` is the R3 default unless M5 memory/latency measurements force fallback. Fallback is language-aware: Korean and mixed queries must fall back to a multilingual model or the current multilingual `mmarco`, not to an English-focused reranker. `mxbai-rerank-base-v1` may remain as an English-only low-memory experiment, but it is not a safe Korean fallback.

### R3 Eval Suite

The new eval suite must be designed before cutover gates are trusted.

Qrel schema:

```json
{
  "query_id": "spring_mvc_shortform_korean_alias_beginner_primer",
  "query": "스프링 MVC 뭐야",
  "language": "ko",
  "intent": "definition",
  "level": "beginner",
  "primary_paths": ["contents/spring/...md"],
  "acceptable_paths": ["contents/spring/...md"],
  "forbidden_paths": ["contents/design-pattern/...md"],
  "expected_concepts": ["spring/mvc"],
  "failure_focus": ["korean_alias", "beginner_primer"]
}
```

Required cohorts:

- Korean shortform and mixed Korean/English technical terms.
- Beginner primer queries.
- Confusable concepts: DI/IoC/Service Locator, Strategy/Template/Factory, MVCC/locking/isolation.
- Symptom queries: stale projection, CRUD read/update mismatch, session/cookie/auth loop.
- Corpus-gap probes where no existing doc should be overconfidently returned.
- Forbidden-neighbor probes where a plausible but wrong category must not rank high.

Calibrated gates:

- `candidate_recall@100`: set from the redesigned qrels, not current legacy/Lance reports.
- `rerank_input_recall@K`: K is profile-controlled and reported.
- `primary_nDCG@10`, `hit@10`, `MRR`: reported by cohort and language.
- `forbidden_rate@5 = 0` for qrel-risk cohorts.
- `reranker_demotion_rate`: bounded and explained, especially for Korean/beginner queries.
- `corpus_gap_false_confidence_rate`: bounded for missing-doc probes.

### Trace Artifact Contract

Every eval and debug run writes one JSONL row per query:

```json
{
  "query_id": "spring_mvc_shortform_korean_alias_beginner_primer",
  "query_plan": {"version": "r3.0", "language": "ko", "intent": "definition"},
  "retrievers": {
    "lexical": [{"path": "...", "rank": 1, "score": 13.2}],
    "dense": [{"path": "...", "rank": 8, "score": 0.71}],
    "sparse": [{"path": "...", "rank": 3, "score": 9.4}],
    "signal": [{"path": "...", "rank": 1, "score": 1.0}]
  },
  "fusion": [{"path": "...", "rank": 4, "features": {"rrf": 0.18}}],
  "rerank": [{"path": "...", "rank": 1, "score": 0.93}],
  "final": [{"path": "...", "rank": 1}],
  "failure_class": null,
  "stage_ms": {"lexical": 12.4, "dense": 31.8, "sparse": 19.2, "rerank": 280.5}
}
```

This trace is the main debugging artifact. Final nDCG without this trace is insufficient for R3.

## Backend Decision Matrix

R3 should run a backend spike, not choose by preference alone.

| Backend | Strength | Risk | Spike output |
|---|---|---|---|
| Qdrant + lexical sidecar | strong dense/sparse/multivector ergonomics, simpler vector DB | field-level lexical ranking may need a separate engine | dense+sparse query path, sidecar BM25, and optional multivector rerank |
| LanceDB improved | lowest migration cost; current artifacts reusable | current sparse is rescore-only and quality trails legacy | feature-equivalent Lance path plus true sparse sidecar/native proof |
| Vespa | strongest integrated retrieval + ranking framework; BM25, vector, rank profiles, phased ranking, feature logs | higher setup/ops complexity, JVM/YQL burden for local hub | time-boxed high-ceiling comparator schema |
| Legacy v2 enhanced | rollback reference, simple local fallback | older embedding/index architecture; limited multimodal/sparse evolution | retained as production safety net, not as R3 design anchor |

Backend spike acceptance:

- same qrel fixture
- same query plans
- same candidate trace schema
- same cold/warm latency reporting
- same local CPU and optional GPU/daemon measurements
- same final answer/citation contract

## Evaluation Redesign

The current gate is too final-result heavy. R3 must record where quality is lost.

Add metrics:

| Metric | Meaning | Gate |
|---|---|---|
| `retriever_recall@K` | primary path appears in each retriever's top K | diagnostic |
| `candidate_recall@20/50/100` | primary path appears before rerank | diagnostic first; cutover target set from redesigned eval suite |
| `rerank_input_recall@K` | primary path reaches reranker input | diagnostic first; K must be config-driven, not `top_k * 2` |
| `fusion_lift` | fusion improves rank over best individual retriever | positive on hard cohorts |
| `reranker_lift` | reranker improves primary rank | positive or neutral |
| `reranker_demotion` | reranker lowers primary rank | must be explainable |
| `doc_diversity@50` | unique source docs before rerank | no single-doc chunk flooding |
| `forbidden_rate@5` | forbidden path in top window | must remain 0 |
| `hard_failure_count` | primary missing or over budget | calibrated against redesigned qrels and hard cohorts |

Failure taxonomy:

```text
candidate_absent      primary not found by any first-stage retriever
retriever_absent      primary found by one retriever but not another
fusion_under_ranked   primary found but fusion ranks it too low
reranker_demoted      primary enters reranker but is pushed down
dedupe_lost           primary chunk/doc removed by dedupe
metadata_blocked      filter/role/level/category blocked the primary
qrel_incomplete       retrieved doc is acceptable but missing from qrel
corpus_gap            no adequate corpus document exists
query_understood_badly query plan used wrong category/intent/concept
```

Required artifacts:

- `reports/rag_eval/r3_candidate_trace_<timestamp>.jsonl`
- `reports/rag_eval/r3_backend_comparison_<timestamp>.json`
- `reports/rag_eval/r3_failure_taxonomy_<timestamp>.json`
- `reports/rag_eval/r3_corpus_gap_queue_<timestamp>.json`

Measurement rule:

- Measure current legacy v2 and Lance v3 `candidate_recall@20/50/100` only to understand symptoms and rollback risk.
- Do not derive final R3 thresholds from current legacy/Lance measurements.
- Final thresholds must come from a redesigned eval suite: validated qrels, acceptable/forbidden paths, Korean/mixed-language hard cohorts, corpus-gap labels, and stage-level traces.

## Corpus v2 Contract

Highest performance requires a corpus designed for retrieval, not only readable markdown.

Current corpus strengths:

- large topical coverage;
- consistent beginner authoring guide;
- retrieval-anchor conventions;
- H2 chunking discipline;
- link and asset lint ecosystem;
- topic maps and cross-domain bridge docs.

Current corpus weaknesses for R3:

- anchors are appended into every chunk body, which can pollute dense embeddings;
- `doc_type`, `language`, `source_priority`, `linked_paths`, `concept_id`, and `confusable_with` are not enforced in the loader's chunk metadata;
- qrels are separate from authoring, so new documents can increase ambiguity without proving retrieval value;
- confusable concept pairs are handled by ad hoc anchors/boosts rather than corpus-level structure;
- root/meta docs are excluded from the index, which is reasonable for current RAG, but R3 needs a separate route index for navigators/master-notes rather than treating them as noise or ignoring them completely.

Corpus v2 should be staged, not mass-applied as a 14-field authoring burden.

Pilot-required fields:

```yaml
---
schema_version: 2
concept_id: spring/di
doc_role: primer
level: beginner
aliases:
  - DI
  - dependency injection
  - 의존성 주입
expected_queries:
  - 처음 배우는데 DI가 뭐야?
  - new 대신 주입받는 이유가 뭐야?
---
```

The pilot must measure field-level lift before expanding the contract:

- `concept_id`: identity and qrel binding;
- `doc_role`: primer/deep-dive/chooser routing;
- `level`: beginner vs advanced ranking;
- `aliases`: Korean/English lexical discovery;
- `expected_queries`: qrel seed generation and indexed retrieval-contract anchors.

Full frontmatter target after pilot validation:

```yaml
---
schema_version: 2
concept_id: spring/di
canonical: true
category: spring
doc_role: primer
level: beginner
language: ko
source_priority: 90
aliases:
  - DI
  - dependency injection
  - 의존성 주입
  - new 대신 주입
symptoms:
  - 구현체를 어떻게 고르나요
  - 인터페이스로 주입하는 이유
intents:
  - definition
  - comparison
  - design
prerequisites:
  - language/java-interface
next_docs:
  - spring/bean-container
  - spring/aop-proxy
linked_paths:
  - contents/spring/spring-bean-di-basics.md
confusable_with:
  - design-pattern/service-locator
  - design-pattern/factory
forbidden_neighbors:
  - contents/design-pattern/object-oriented-design-pattern-basics.md
expected_queries:
  - 처음 배우는데 DI가 뭐야?
  - new 대신 주입받는 이유가 뭐야?
  - 인터페이스로 주입하는 이유가 뭐야?
---
```

Field meanings and rollout:

| Field | Rollout | Retrieval use |
|---|---|---|
| `concept_id` | pilot required | stable identity across docs/chunks/qrels |
| `doc_role` | pilot required | primer/bridge/deep_dive/playbook/comparison/drill route |
| `level` | pilot required | learner-level ranking and filtering |
| `aliases` | pilot required | lexical alias field and query expansion |
| `expected_queries` | pilot required | qrel seed generation and indexed retrieval-contract anchors |
| `canonical` | wave 2 | canonical doc selection and duplicate control |
| `language` | wave 2 | Korean/English/mixed routing |
| `source_priority` | wave 2 | citation and final-answer source guard |
| `symptoms` | wave 2 for playbook/bridge | symptom-first retrieval |
| `intents` | wave 2 | definition/comparison/troubleshooting/design routing |
| `confusable_with` | wave 2 for overlap zones | negative/chooser routing |
| `forbidden_neighbors` | wave 2 for qrel-risk zones | hard regression guard |
| `prerequisites` | optional after graph design | learning path guard |
| `next_docs` | optional after graph design | companion expansion |
| `linked_paths` | optional after graph design | graph/context expansion |

Corpus authoring completion should mean:

```text
markdown exists
+ frontmatter valid
+ links valid
+ concept catalog updated
+ qrel added
+ candidate recall improves or stays neutral
+ forbidden regression absent
```

It is not enough to add a document and rebuild the index.

Do not require all 14 fields across 2274 documents until the pilot shows which fields improve retrieval. Each added required field must have a measured lift, a lint rule, and an authoring template.

## Corpus Expansion Strategy

Do not expand by volume. Expand by ambiguity and coverage gaps.

Priority document types:

1. Chooser documents:
   - "Strategy vs Template Method vs Factory vs Selector vs Registry vs Service Locator"
   - "DI vs IoC vs Service Locator"
   - "Projection freshness vs cache staleness vs transaction rollback"
2. Beginner natural-language entrypoints:
   - documents matching "처음 배우는데", "큰 그림", "언제 쓰는지", "왜 필요한지"
3. Symptom-to-cause routers:
   - stale list after update
   - login loop with cookie present
   - 403 after role change
   - deadlock after lock ordering change
4. Confusable-neighbor splitters:
   - documents that say "if query says X, do not return Y first"
5. Mission-specific bridges:
   - Woowa mission concepts mapped to CS concepts and common PR feedback
6. Drills:
   - self-check qrels that test whether learner receives the right level and role

First corpus waves:

| Wave | Focus | Why |
|---|---|---|
| C1 | design-pattern chooser cluster | current sparse/top1 changes show noisy design-pattern neighbors |
| C2 | Spring DI/Bean/router/qualifier cluster | high learner frequency and many confusable aliases |
| C3 | projection freshness/read-model/stale-read cluster | repeated failure cohort |
| C4 | MVCC/isolation/locking/transaction propagation cluster | high CS frequency and mixed DB/Spring boundary |
| C5 | auth session/cookie/JWT/Spring Security filter chain cluster | cross-category security/Spring/browser confusion |

Each wave must include:

- concept registry additions;
- qrel additions;
- forbidden-neighbor additions;
- at least one chooser or router document;
- updated category README links;
- candidate-trace comparison before and after.

## Migration Plan

### Phase -1 - Diagnostic Gate Before Rebuild

Duration: 4-5 days.

Purpose: calibrate the R3 rebuild before implementation. This phase identifies which structural work must land first; it does not decide whether to abandon the fundamental redesign.

Inputs to reuse before building new tooling:

- `regression_summary.violations_by_kind` from current eval reports;
- `reports/rag_eval/cutover_failure_qrel_review_20260501T0730Z.json`;
- `reports/rag_eval/next_failure14_top10_diagnosis_20260501T1700Z.json`;
- `reports/rag_eval/next_improvement_decision_20260501T1700Z.md`;
- existing legacy v2 and Lance v3 holdout reports as symptom snapshots only.

Diagnostic work:

1. Audit top-100 candidates for the Lance hard regressions and failure-14 cohort.
2. Diff legacy v2 vs Lance v3 code paths for query expansion, signal path injection, category filtering, dedupe, reranker prompt decoration, and reranker input size.
3. Run a BGE-M3 sparse direct-retrieval pilot against the hard regressions, independent of FTS+dense RRF.
4. Cross-validate fixture/qrel strictness: mark acceptable, forbidden, and missing qrels instead of treating every wrong primary as a corpus/backend failure.
5. Split Korean failure root cause into four hypotheses:
   - encoder/model mismatch: compare BGE-M3 with an instruction-aware multilingual candidate such as Qwen3 embedding or another locally viable stack;
   - tokenization activation/symmetry: the current query-side `kiwipiepy` path exists but is disabled by default via weight `0.0`; test enabling, weighting, and index/query field symmetry before rebuilding it;
   - chunk/context representation: test contextual prefixes or separated anchor fields instead of appending anchors into every chunk body;
   - fixture bias/qrel incompleteness: verify whether retrieved documents are valid but unjudged.
6. Patch or at least prove the reranker input-size path. Top-50 local and top-100 offline experiments are invalid until `top_n=top_k * 2` is replaced by a config-driven value.
7. Run a local M5 feasibility probe for the target reranker and fallback chain: RSS peak, model load time, warm p95 for 50 pairs, CPU-only degraded behavior, and MPS/fp16 availability.

Implementation priority decision:

| Outcome | Next step |
|---|---|
| Legacy-only signal/query expansion explains many failures | implement equivalent signal/query planning as an R3 compatibility layer |
| Korean tokenization/encoder explains many failures | prioritize encoder/tokenizer/chunking track inside R3 |
| Sparse direct retrieval adds missing primaries | prioritize sparse sidecar/native sparse discovery in R3 |
| Qrel/corpus gaps dominate | prioritize corpus v2 pilot and qrel redesign before broad corpus expansion |
| Failures remain distributed across candidate generation/fusion/rerank | implement the full retrieval fabric first |

Done when:

- each hard regression has a primary failure class;
- the plan chooses first implementation track: `query_signal`, `korean_encoder_tokenizer`, `sparse_discovery`, `corpus_qrel`, or `full_fabric`;
- candidate-recall symptom snapshots exist for legacy v2 and Lance v3 at `@20`, `@50`, and `@100`;
- reranker-input experiments are either patched or explicitly deferred;
- M5 runtime feasibility is recorded as a measurement artifact, not an estimate.

### Phase 0 - Freeze Snapshots And Rollback Anchor

Deliverables:

- preserve current Lance v3 reports;
- preserve legacy v2 archive reports;
- record current sparse-rescore limitation;
- explicitly document legacy v2 as rollback/safety anchor only;
- explicitly document Lance v3 as current implementation snapshot, not final V3 capability;
- add this R3 plan as review target.

Done when:

- reviewer can reproduce current evidence from listed artifacts;
- rollback to legacy v2 is documented as a valid decision option;
- current metrics are marked diagnostic-only and cannot veto R3 design;
- no production behavior changes are required.

### Phase 1 - Incremental Evaluation/Trace Foundation

Implement:

- `Candidate` and `RetrieverTrace` schemas;
- per-stage trace JSONL;
- `candidate_recall@K`, `rerank_input_recall@K`, `fusion_lift`, `reranker_demotion`;
- failure taxonomy classifier.

Scope guard:

- this is a 3-5 day incremental extension, not a 2-3 week harness rewrite;
- reuse current regression summaries, qrel review, failure-14 diagnosis, and `diagnose_retrieval.py`;
- add only the missing stage-level fields needed for Phase -1 and backend comparison.
- existing `scripts/learning/rag/eval/` remains canonical for legacy/current Lance evaluation during Phase 1-4;
- new `scripts/learning/rag/r3/eval/` owns R3 trace, qrels, metrics, and failure taxonomy;
- after the Phase 4 backend decision, either move old eval helpers under `eval/legacy/` or document which wrappers remain shared.

Modify:

- `scripts/learning/rag/eval/runner.py`
- `scripts/learning/rag/eval/metrics.py`
- `scripts/learning/rag/eval/diagnose_retrieval.py`
- `scripts/learning/cli_rag_eval.py`

Tests:

- unit tests for trace schema;
- synthetic cases for every failure taxonomy class;
- regression test proving final nDCG can stay equal while candidate trace differs.

Gate:

- every eval run can explain each hard failure as one taxonomy class.

### Phase 2 - Corpus v2 Pilot Schema And Lints

Implement:

- frontmatter parser;
- concept catalog v2 schema;
- qrel seed extraction from `expected_queries`;
- metadata-aware chunk objects;
- split fields for `body`, `title`, `section`, and `aliases` first;
- field-lift report for `concept_id`, `doc_role`, `level`, `aliases`, and `expected_queries`.

Modify:

- `scripts/learning/rag/corpus_loader.py`
- `scripts/learning/rag/corpus_lint.py`
- `docs/cs-authoring-guide.md`
- `knowledge/cs/rag/chunking-and-metadata.md`
- `knowledge/cs/rag/retrieval-anchor-keywords.md`

Migration approach:

- do not mass-edit all 2274 docs at once;
- first migrate documents involved in failure cohorts and high-frequency categories;
- keep legacy `retrieval-anchor-keywords` supported during migration;
- write dual metadata until new index path is stable;
- expand to `symptoms`, `confusable_with`, `forbidden_neighbors`, `source_priority`, and graph fields only after pilot lift is measured.
- pilot size must be judged by qrel coverage, not only document count: target 30-50 pilot docs or at least 100-150 reviewed pilot qrels across Korean, mixed, beginner, confusable, symptom, and forbidden-neighbor cohorts.

Gate:

- migrated docs produce identical or better candidate recall;
- no forbidden regression on holdout;
- authoring lint enforces only pilot-required frontmatter for new docs;
- field rollout uses a default-include rule for positive but statistically ambiguous lift, and a drop/defer rule only for negative or strongly null fields.

### Phase 3 - Retrieval Fabric Interface

Implement:

- `scripts/learning/rag/retrievers/base.py`
- `LexicalRetriever`
- `DenseRetriever`
- `SparseRetriever`
- `SignalRetriever`
- `MetadataRanker`
- fusion module with weighted RRF and normalized feature output.

Initial backend:

- may use current Lance/local stores for proof;
- must expose independent sparse candidates, not only rescore;
- before Qdrant production path exists, the sparse proof uses an in-memory inverted index built from the existing Lance `sparse_vec` payload. This prototype proves sparse first-stage value; it is not the production sparse store.

Gate:

- `SparseRetriever` can introduce a primary path absent from FTS+dense on at least one targeted failure or synthetic fixture;
- signal canonical docs can enter the pool even when FTS/dense misses them;
- final ranking is still deterministic.

### Phase 4a - Primary Backend Spikes

Build side-by-side prototypes:

1. Qdrant:
   - dense vector;
   - sparse vector;
   - optional multivector rerank;
   - lexical sidecar if needed;
   - fusion outside Qdrant if Qdrant ranking is insufficient;
   - explicit runtime mode comparison: Python local mode vs local server/Docker mode.
2. Lance improved:
   - feature-equivalent FTS expansion;
   - signal path injection;
   - native or sidecar sparse discovery;
   - configurable reranker input size;
   - pre-rerank doc diversity.

Gate:

- same query fixture and qrel;
- same trace schema;
- compare quality, candidate recall, latency, RSS peak, startup behavior, rebuild artifact size, and operational complexity;
- choose one production candidate and one rollback candidate;
- if neither Qdrant nor Lance-improved meets the calibrated gate, or if phased ranking/feature logging becomes a documented requirement, open Phase 4b.

### Phase 4b - Conditional Vespa Comparator

Build Vespa only if Phase 4a fails or the accepted requirements need Vespa-specific rank profiles/features.

Vespa spike scope:

- schema fields for title/body/section/aliases/symptoms;
- BM25 rank features;
- dense vector;
- sparse or lexical equivalent;
- optional multivector/late-interaction path or staged rerank;
- rank profiles for BM25, dense, hybrid RRF, hybrid normalized, and role-aware final rank.

Gate:

- prove that Vespa's quality or observability benefit is worth the JVM/YQL/runtime memory overhead on the learner's local machine, otherwise reject it for local production.

### Phase 5 - Reranker And Diversity Redesign

Implement:

- config-driven reranker input size replacing `top_k * 2`;
- pre-rerank doc-level diversity;
- top-20 default local reranker input, top-50 local profiling experiments, and top-100 offline experiments;
- make `BAAI/bge-reranker-v2-m3` the R3 target reranker and validate memory/latency against the fallback candidates;
- implement language-aware fallback: Korean/mixed queries use target, verified multilingual fallback, or `mmarco`; English-only queries may use `mxbai` if it wins locally;
- late-interaction rerank comparison;
- reranker demotion report.

Gate:

- reranker improves or preserves primary rank on hard cohorts;
- demotions are explainable and not concentrated in Korean/beginner buckets;
- M5 16GB MPS warm p95 target is explicit before cutover. Provisional target: top-20 full R3 warm p95 <= accepted interactive budget and RSS peak <= accepted local budget; top-50 remains a profiling/quality comparator, not the local default.

### Phase 6 - Corpus Expansion Waves

Implement C1-C5 waves from Corpus Expansion Strategy.

Per-wave gate:

- each new doc has frontmatter and qrel;
- candidate recall improves in target cohort;
- no holdout hard-failure regression;
- category README and graph links updated;
- failure taxonomy count for the wave decreases.

### Phase 7 - Production Cutover

Required before cutover:

- R3 production candidate passes the redesigned eval suite;
- R3 candidate recall passes calibrated thresholds from validated qrels and hard cohorts;
- rollback path tested;
- remote-built index artifacts can be imported and served locally on the M5 target without local rebuild;
- cold/warm latency documented;
- no cutover-blocking failure remains in "unknown root cause" state;
- model cache and first-run protocol updated;
- `docs/rag-runtime.md`, `docs/cs-rag-internals.md`, and runbooks updated.

Cutover gate:

```text
candidate_recall@100 >= calibrated_R3_threshold
rerank_input_recall@50 >= calibrated_R3_threshold for local production
primary nDCG@10 >= calibrated_R3_threshold
hit@10 >= calibrated_R3_threshold
forbidden_rate@5 = 0
hard_failures <= calibrated_R3_budget
M5 16GB MPS warm p95 <= accepted budget
M5 16GB RSS peak <= accepted budget
remote build artifact manifest verifies locally
all phase verification artifacts exist
no unresolved workaround-only fix is counted as pass
rollback smoke passes
```

## Execution Schedule And Tickets

This schedule assumes quality is prioritized over minimal change. The first two weeks produce a working R3 skeleton with traces; later weeks harden backend choice, corpus expansion, and cutover.

### Week 1 - Traceable R3 Skeleton

Goal: make every stage observable before optimizing quality.

Tickets:

| ID | Work | Files | Done when |
|---|---|---|---|
| R3-001 | Add R3 config and feature flag | `scripts/learning/rag/r3/config.py`, `scripts/learning/rag/searcher.py` | `searcher.search(..., backend="r3")` can route to R3 without changing default production |
| R3-002 | Add `QueryPlan` model | `scripts/learning/rag/r3/query_plan.py` | Korean/English/mixed fixture queries produce stable plans |
| R3-003 | Add candidate/trace dataclasses | `scripts/learning/rag/r3/candidate.py`, `scripts/learning/rag/r3/eval/trace.py` | JSONL trace round-trip test passes |
| R3-004 | Patch reranker input profile | `scripts/learning/rag/searcher.py`, `scripts/learning/rag/r3/config.py` | reranker input can be 10, 50, or 100 without code changes |
| R3-005 | Add redesigned qrel schema | `scripts/learning/rag/r3/eval/qrels.py`, `tests/fixtures/r3_qrels_pilot.json` | primary/acceptable/forbidden paths validate |

Week 1 gate:

- one command can run R3 skeleton on a small fixture and write trace JSONL;
- current production path remains unchanged by default;
- reranker input window is no longer hard-coded in the R3 path.

### Week 2 - Independent Candidate Discovery

Goal: make lexical, dense, sparse, and signal candidates independently visible.

Tickets:

| ID | Work | Files | Done when |
|---|---|---|---|
| R3-006 | Lexical sidecar prototype | `scripts/learning/rag/r3/index/lexical_store.py`, `scripts/learning/rag/r3/retrievers/lexical.py` | title/section/aliases/body ranks are separately traced |
| R3-007 | Dense retriever adapter | `scripts/learning/rag/r3/retrievers/dense.py` | BGE-M3 dense candidates are traced independently |
| R3-008 | True sparse retriever prototype | `scripts/learning/rag/r3/retrievers/sparse.py` | in-memory inverted index over Lance `sparse_vec` can return candidates not present in lexical+dense |
| R3-009 | Signal retriever | `scripts/learning/rag/r3/retrievers/signal.py` | canonical signal paths enter trace as their own retriever |
| R3-010 | Fusion v1 | `scripts/learning/rag/r3/fusion.py` | weighted RRF and doc diversity are deterministic and tested |

Week 2 gate:

- trace shows which retriever found each final result;
- at least one synthetic sparse-only case proves independent sparse discovery;
- signal candidates are not hidden inside rank boosts.

### Week 3 - Target Reranker And Korean Handling

Goal: make `BAAI/bge-reranker-v2-m3` the target R3 reranker and remove Korean query asymmetry.

Tickets:

| ID | Work | Files | Done when |
|---|---|---|---|
| R3-011 | R3 reranker adapter | `scripts/learning/rag/r3/rerankers/cross_encoder.py` | `bge-reranker-v2-m3`, multilingual fallback, `mmarco`, and English-only `mxbai` share one interface |
| R3-012 | Reranker demotion metrics | `scripts/learning/rag/r3/eval/metrics.py` | demotion rate is reported by language/level/category |
| R3-013 | Korean tokenization activation + targeted fix | `scripts/learning/rag/r3/query_plan.py`, `scripts/learning/rag/r3/index/lexical_store.py` | query-side Korean term generation is enabled, weighted, and verified against index-side fields |
| R3-014 | Contextual chunk prefix experiment | `scripts/learning/rag/corpus_loader.py`, R3 index builder | anchors can be separated from dense body text |
| R3-015 | M5 memory/latency profile | `reports/rag_eval/r3_reranker_profile_<timestamp>.json` | target reranker and fallback chain have MPS p95/RSS numbers or fallback decision is explicit |

Week 3 gate:

- target reranker is functionally wired;
- Korean/mixed hard cohort has stage-level explanation;
- memory constraints are measured rather than assumed.

### Week 4 - Corpus v2 Pilot

Goal: prove which corpus fields improve retrieval before broad authoring migration.

Tickets:

| ID | Work | Files | Done when |
|---|---|---|---|
| R3-016 | Frontmatter parser/lint | `scripts/learning/rag/corpus_lint.py`, `scripts/learning/rag/corpus_loader.py` | 5 pilot fields validate |
| R3-017 | Concept catalog v2 pilot | `knowledge/cs/catalog/concepts.v2.json` or equivalent | concept IDs map to pilot docs and qrels |
| R3-018 | Pilot docs | `knowledge/cs/contents/**` | 30-50 pilot docs or an explicitly accepted smaller set use staged frontmatter |
| R3-019 | Qrel generation from `expected_queries` | `scripts/learning/rag/r3/eval/qrels.py` | at least 100-150 pilot qrels are generated and reviewed, including forbidden paths |
| R3-020 | Field-lift report | `reports/rag_eval/r3_corpus_field_lift_<timestamp>.json` | lift per field is reported before expanding requirements |

Week 4 gate:

- no 14-field mass migration;
- each pilot field has a measured retrieval effect or a clear reason to keep/drop;
- corpus authoring guide reflects the staged contract.

### Weeks 5-6 - Backend Spike And Production Candidate

Goal: pick the first production candidate by R3 traces, not preference.

Tickets:

| ID | Work | Files | Done when |
|---|---|---|---|
| R3-021 | Qdrant index builder + runtime mode probe | `scripts/learning/rag/r3/index/qdrant_store.py`, CLI wrapper | dense+sparse collection can be rebuilt and local/server modes are profiled |
| R3-022 | Lance improved candidate | R3 index adapters | true sparse sidecar/native path is comparable under same trace |
| R3-023 | Backend comparison runner | `scripts/learning/rag/r3/eval/backend_compare.py` | Qdrant and Lance emit same trace schema |
| R3-024 | Calibrated gate proposal | `reports/rag_eval/r3_gate_proposal_<timestamp>.md` | thresholds come from redesigned qrels and hard cohorts |
| R3-025 | Production candidate decision | `docs/worklogs/rag-r3-backend-decision-<date>.md` | one candidate and one rollback path are chosen |

Weeks 5-6 gate:

- backend decision includes quality, candidate recall, reranker demotion, forbidden rate, p95, RSS, rebuild time, and operational burden;
- backend decision explicitly states Qdrant local/server viability on M5 16GB;
- Vespa is only built in Phase 4b if Qdrant/Lance cannot satisfy the R3 gate proposal.

### Weeks 7-8 - Cutover Hardening

Goal: make the new system operationally safe.

Tickets:

| ID | Work | Files | Done when |
|---|---|---|---|
| R3-026 | Runtime integration | `scripts/workbench/core/interactive_rag_router.py`, `scripts/learning/rag/searcher.py` | R3 can serve `bin/rag-ask` behind config |
| R3-027 | Manifest/runbook update | `schemas/*`, `docs/rag-runtime.md`, `docs/cs-rag-internals.md`, `docs/runbooks/rag-rollback.md` | rollback and rebuild are documented |
| R3-028 | Regression suite | `tests/unit`, `tests/integration` | R3 gates run in CI/local eval |
| R3-029 | Full holdout and pilot cohorts | `reports/rag_eval/r3_cutover_<timestamp>.json` | calibrated gates pass twice |
| R3-030 | Cutover packet | `docs/worklogs/rag-r3-cutover-<date>.md` | decision, risks, rollback command, and evidence are complete |

Weeks 7-8 gate:

- production can switch between legacy/current/R3 by config;
- R3 passes the redesigned eval suite twice;
- rollback smoke passes after cutover rehearsal.

### First PR Order

The safest first implementation order:

1. `R3-001` to `R3-003` and `R3-005`: contracts, feature flag, qrels, trace.
2. `R3-004`: reranker input window patch, because without it reranker work is not trustworthy.
3. `R3-006` to `R3-010`: independent retrieval and fusion.
4. `R3-011` to `R3-015`: target reranker and Korean handling.
5. `R3-016` to `R3-020`: corpus v2 pilot.

Do not begin backend lock-in or broad corpus migration before these are complete.

### Implementation Discipline

Every implementation phase must be incremental and evidence-producing:

- each ticket starts with the smallest reproducible failing case or trace that explains why the change is needed;
- each ticket ends with a local verification command, an eval/report artifact when retrieval quality is involved, and a short root-cause note for any defect fixed during the ticket;
- do not merge or commit a fix that only masks symptoms. Temporary degradation paths may protect learners during development, but they cannot satisfy a gate and must have a removal condition;
- commit after each coherent ticket or gate, not as one large end-of-project commit;
- commit messages must be specific and evidence-oriented, for example `rag-r3: add trace schema for independent retrievers` or `rag-r3: fix korean fts query activation from failure14 audit`;
- each commit body should mention the verification command or report path when the change affects retrieval behavior, runtime latency, index format, or corpus/qrels.

## Operational Design

Learner data boundary:

- Learner memory remains outside the retrieval backend.
- Source of truth stays event-sourced under `state/learner/history.jsonl`.
- Derived learner views stay in `state/learner/profile.json` and `state/learner/summary.json`.
- R3 may read learner context through a typed adapter, but it must not store learner profile state in Qdrant, LanceDB, Vespa, or the CS corpus index.
- SQLite may be used only as an optional local read model/cache for analytics or fast filtering. If introduced, it must be rebuildable from `history.jsonl`, never the authoritative store.
- Per-repo legacy memory under `state/repos/<repo>/memory/` remains compatibility/migration input only.

Serving:

- hard local serving target: M5 MacBook Air 13-inch, 16GB unified memory, Apple Silicon MPS;
- build target: remote GPU instance such as RunPod L40S or equivalent. Build-time memory and compute are not constraints, but the artifact must satisfy the local serving constraints;
- all target model profiling must record dtype, device, RSS peak, model load time, top-20 default rerank p50/p95, top-50 comparator p50/p95, and CPU-only degraded latency;
- CPU-only serving is allowed as emergency/degraded mode only, not as the production target for `bge-reranker-v2-m3`;
- keep query encoder warm in a daemon or service process;
- separate cold-start metrics from warm metrics;
- cache query encodings by normalized query + query-plan version;
- batch reranker calls when evaluation runs many queries;
- keep `HF_HUB_OFFLINE=1` for local deterministic runs.

Artifacts:

- index manifest must include retriever versions, corpus schema version, concept catalog hash, qrel hash, and backend-specific index parameters;
- remote build manifest must include code commit SHA, build command, Python/package lock information, model IDs/revisions, corpus hash, qrel hash, index format version, artifact checksums, and target local runtime profile;
- local artifact import must verify checksums before serving and must fail closed if the artifact/schema version is incompatible;
- candidate trace artifacts should be kept under `reports/rag_eval/`, not mission repos;
- large backend indexes remain under `state/` or external service volumes.

Safety:

- no mission repo writes;
- keep all workbench state outside mission repos;
- every unexpected quality, latency, memory, or indexing failure must be classified as data, model, query planning, index construction, retrieval, fusion, reranking, evaluation, configuration, or hardware/runtime before being closed;
- if a temporary mitigation is needed for learner usability, mark it as degraded mode and continue root-cause repair. It is not a successful R3 implementation result;
- preserve legacy v2 archive until R3 passes at least two full holdout runs;
- do not delete R2 artifacts until R3 migration is complete.

## Risks And Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Carrying current defects into R3 | redesign preserves old failure modes | mandatory Phase -1 diagnostic and implementation-priority decision |
| Target reranker does not fit local runtime | forced fallback damages Korean/mixed quality | M5 MPS p95/RSS gate and language-aware fallback policy |
| English-focused fallback handles Korean/mixed queries | regression versus current production | route Korean/mixed fallback to verified multilingual model or `mmarco`; use `mxbai` only for English-only experiments |
| Qdrant runtime mode exceeds local budget | good backend design fails learner laptop serving | profile Qdrant local/server modes; fall back to Lance improved + sparse sidecar if needed |
| Vespa operational complexity | slows delivery | treat Vespa as comparator unless Qdrant/Lance cannot meet gates |
| Corpus frontmatter migration is large | high manual cost | 5-field pilot first; expand only fields with measured lift and reviewed qrel coverage |
| Sparse discovery adds noise | lower precision | trace by retriever; use per-category weights and forbidden-neighbor qrels |
| Multivector memory/latency | p95 regression | use as rerank-only first; disable HNSW where appropriate; hard-query gate |
| Reranker demotes Korean/beginner docs | learner-facing regression | bucket demotion metrics; multilingual reranker A/B |
| Reranker input experiment has no effect | false confidence in top-50/top-100 results | patch `top_k * 2` before reranker A/B |
| Remote-built artifact fails locally | high-quality build cannot serve on learner machine | make remote-build manifest and M5 import smoke test a gate before backend lock-in |
| Symptom-masking fix lands | regressions return under different queries | require root-cause classification, reproducer/trace, and regression check before closing the ticket |
| Long-running implementation drifts | late discovery of broken quality/runtime behavior | verify after each ticket and commit only after verification evidence exists |
| Qrels overfit current docs | false confidence | include acceptable/forbidden paths; mine disagreement queries |
| Authoring becomes too heavy | docs stop growing | templates, lints, qrel seeds, phased requirements |

## Questions For External Reviewer

1. Does the Phase -1 diagnostic split the plausible root causes enough to choose the first R3 implementation track?
2. Should the first production spike be Qdrant + lexical sidecar or LanceDB-improved sparse sidecar?
3. Which Qdrant runtime mode, if any, is acceptable on the M5 16GB local target?
4. Under what measured result would Vespa's operational cost become justified for this local learning hub?
5. Which Korean failure branch is most likely: encoder, query tokenization activation/weight, chunk/context representation, or fixture/qrel bias?
6. What should the calibrated `candidate_recall@100` cutover threshold be after the redesigned qrel suite exists?
7. Are the 5 pilot-required corpus fields sufficient, or is one additional field essential for retrieval lift?
8. Which failure taxonomy classes should block cutover outright?
9. Is the proposed first PR order the right sequencing for reducing implementation risk?

## Immediate Next Actions

1. Execute Phase -1 diagnostic before backend implementation.
2. Patch or explicitly defer reranker input configurability before any top-50/top-100 reranker experiment.
3. Run the M5 reranker feasibility probe for `bge-reranker-v2-m3`, multilingual fallback, `mmarco`, and English-only `mxbai`.
4. Define the remote-build/local-serve artifact contract:
   - remote build command and environment capture,
   - manifest/checksum schema,
   - local M5 import smoke command,
   - incompatible schema failure behavior.
5. Create Phase 1 incremental trace tickets:
   - candidate recall symptom snapshots at `@20`, `@50`, `@100`,
   - failure taxonomy classifier using existing qrel/failure artifacts,
   - eval CLI output contract.
6. Create a corpus v2 pilot set:
   - 5 design-pattern chooser docs,
   - 5 Spring DI/Bean/router docs,
   - 5 projection freshness/read-model docs,
   - then expand to 30-50 docs or at least 100-150 reviewed qrels before field rollout decisions.
7. Choose the first R3 implementation track from the diagnostic decision.
8. Begin implementation with ticket-sized commits, each with a concrete `rag-r3: ...` message and verification evidence in the commit body or linked report.

## Source References

Internal:

- `docs/worklogs/rag-v6-2-external-review-packet-2026-05-01.md`
- `docs/worklogs/rag-r2-cutover-2026-05-01.md`
- `docs/worklogs/rag-sota-handoff-2026-04-30.md`
- `docs/cs-rag-internals.md`
- `docs/cs-authoring-guide.md`
- `knowledge/cs/rag/chunking-and-metadata.md`
- `knowledge/cs/rag/retrieval-anchor-keywords.md`
- `knowledge/cs/rag/retrieval-failure-modes.md`
- `reports/rag_eval/next_improvement_decision_20260501T1700Z.md`
- `reports/rag_eval/sparse_effect_analysis_20260501T1455Z.md`

External:

- Vespa hybrid search tutorial: https://docs.vespa.ai/en/learn/tutorials/hybrid-search
- Vespa nearest-neighbor search: https://docs.vespa.ai/en/querying/nearest-neighbor-search
- Qdrant hybrid search with reranking: https://qdrant.tech/documentation/advanced-tutorials/reranking-hybrid-search/
- Qdrant multivector tutorial: https://qdrant.tech/documentation/tutorials-search-engineering/using-multivector-representations/
- Qdrant vectors concepts: https://qdrant.tech/documentation/concepts/vectors/
- Qdrant hybrid queries: https://qdrant.tech/documentation/concepts/hybrid-queries/
- Qdrant Python client local mode: https://pypi.org/project/qdrant-client/
- LanceDB hybrid search: https://docs.lancedb.com/search/hybrid-search
- LanceDB full-text search: https://docs.lancedb.com/search/full-text-search
- LanceDB GPU indexing: https://docs.lancedb.com/indexing/gpu-indexing
- BGE-M3 paper: https://arxiv.org/abs/2402.03216
- BGE-M3 model card: https://huggingface.co/BAAI/bge-m3
- BGE-M3 docs: https://bge-model.com/bge/bge_m3.html
- BGE reranker v2 M3 model card: https://huggingface.co/BAAI/bge-reranker-v2-m3
- GTE multilingual reranker model card: https://huggingface.co/Alibaba-NLP/gte-multilingual-reranker-base
- mxbai reranker model card: https://huggingface.co/mixedbread-ai/mxbai-rerank-base-v1

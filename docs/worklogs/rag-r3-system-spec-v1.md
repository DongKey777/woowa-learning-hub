# R3 System Spec v1 — Corpus-agnostic Optimal RAG Design (2026-05-02)

> **Authoring principle**: This document is the **design anchor** for the R3 RAG system. It defines what the system *must* do, what it *must not* do, and what it *must measure*. It is **deliberately corpus-agnostic** — written to be the right design for an *ideal* learning-coaching corpus, not tuned to the present corpus's accidental shape. The corpus is then refactored to fit this spec (see `rag-r3-corpus-v3-contract.md`).
>
> **Why corpus-agnostic**: The current corpus is incomplete and possibly biased. If the system is designed to maximize measurements on the current corpus, the corpus's flaws (alias-leak coupling, anchor pollution, missing chooser/symptom docs, inconsistent role taxonomy) become *baked into the system architecture*. We avoid this by specifying the system first, then bringing the corpus into compliance.
>
> **Validation discipline**: No measurement on the *current* corpus is treated as ground truth for system design decisions. The system is validated against a Pilot corpus (50 docs in v3 contract) + Real qrel suite (200q, 6 cohort, human-curated, decoupled from auto-generated `expected_queries`).
>
> **Status**: design only. No implementation in this document. Implementation lives in `scripts/learning/rag/r3/` and is aligned to this spec in Phase 5.

---

## 0. Context

### 0.1 Workload definition

The Woowa Learning Hub serves Woowa Tech Course mission learners (Korean-dominant, beginner-to-intermediate, conversational). The RAG retrieves CS knowledge documents to ground the AI coach's answers, and to anchor citations the learner can verify.

Workload characteristics (verified against `state/learner/history.jsonl` patterns, mission repo coaching context, and the existing `cs_rag_golden_queries.json` fixture):

- **Language**: ~75% Korean, ~12% English, ~13% mixed (CJK + Latin technical terms). Korean queries are often shortform colloquial ("DI 뭐야?", "왜 트랜잭션이 필요해?").
- **Question types**: definition (30%), comparison/disambiguation (25%), symptom → cause routing (15%), beginner primer ("처음 배우는데", 15%), deep-dive mechanism (10%), drill self-check (5%).
- **Mission bridge**: ~30% of queries cross from a Woowa mission concept (e.g., `roomescape DAO`) to a CS concept (e.g., `repository pattern`). The system must surface this bridge explicitly.
- **Multi-turn**: ~20% of follow-up queries reference prior turn content (anaphora, e.g., "그게 왜 필요해?"). Resolution must use prior turn context.
- **Confusable disambiguation**: pairs like DI/IoC/Service Locator, MVCC/locking/isolation, Strategy/Template Method/Factory must route to the right doc, not a plausible-but-wrong neighbor.
- **Corpus gaps**: some learner queries probe topics the corpus does not cover yet. The system must respond *honestly* ("not enough material yet") rather than confidently citing tangential docs.

### 0.2 What "best performance" means here

For a learning-coaching RAG, "best" is **not** maximum macro-nDCG on a fixture. It is:

1. **Paraphrase robustness** — different phrasings of the same concept retrieve the same primary doc. (Measured by `paraphrase_human` cohort.)
2. **Confusable accuracy** — DI query never returns Service Locator first; MVCC query never returns plain locking first. (Measured by `confusable_pairs` cohort + `forbidden_neighbor`.)
3. **Symptom routing** — "stale list after update" routes to projection-freshness, not generic database. (Measured by `symptom_to_cause` cohort.)
4. **Mission bridge** — "roomescape DAO 패턴이 뭔데" routes to repository-pattern primer, not roomescape mission readme. (Measured by `mission_bridge` cohort.)
5. **Honest gap detection** — query about a topic absent from corpus returns low-confidence "not enough material" rather than a confident wrong doc. (Measured by `corpus_gap_probe` cohort.)
6. **Beginner-friendly level routing** — beginner query gets primer, not deep-dive internals. (Measured implicitly via `level` cohort split.)
7. **Citation traceability** — every answer cites at least one doc + chunk_id; learner can navigate to source.
8. **Latency** — p95 warm ≤ 700ms on M5 16GB + MPS so the learner does not feel the system as slow.
9. **Honest "I don't know"** at low confidence rather than hallucinated certainty.

### 0.3 Out of scope (explicit)

- **Maximizing nDCG on the current `cs_rag_golden_queries.json`**. That fixture is treated as a system smoke test only, not a quality gate.
- **Backwards compatibility with the legacy v2 (MiniLM 384-dim) retrieval style**. v2 is the rollback safety net only.
- **Auto-generated qrels from frontmatter `expected_queries`**. The 208q qrel set was structurally circular (alias-indexed `expected_queries` matching its own qrel). The fix removed the structural leak (commit `054a1a3`). All future qrels are human-curated.
- **Models with non-commercial licenses** (e.g., Jina v5 CC-BY-NC 4.0). Allowed for offline evaluation only; never enters the production code path.

---

## 1. Design Principles

### 1.1 P1 — Corpus-agnostic system specification

The system spec is written for an *ideal* corpus that complies with `rag-r3-corpus-v3-contract.md`. The current corpus is brought into compliance by the Pilot migration (50 docs) and Wave migrations (Wave A/B/C/D). System architecture decisions are not justified by present-corpus measurements.

### 1.2 P2 — Independent candidate generation

Retrieval mechanisms (lexical, dense, sparse, signal, metadata, mission-bridge, late-interaction) are *independent* — each can produce a candidate the others miss. Their independence is a design invariant. Fusion combines them; it does not rely on any single retriever to cover all queries.

### 1.3 P3 — Trace-driven debugging

Every query writes a structured trace (per-retriever rank, fusion rank, rerank input/output, final rank, failure class, stage timing). Without the trace, a final-only nDCG is *insufficient* evidence for system decisions. The trace is the primary debugging artifact.

### 1.4 P4 — Calibrated thresholds, not absolute

Cutover gates (`candidate_recall@K`, `final_hit@K`, `forbidden_rate@5`) are *calibrated against the redesigned qrel suite*, not against absolute numbers like 0.99. Absolute values are arbitrary without measurement context. The specific numeric gates are set in the Pilot baseline (Phase 6) and adjusted for full-corpus baseline (Phase 8).

### 1.5 P5 — Always-on reranker for paraphrase robustness

The reranker is **always on** for production queries. The "auto-skip when sidecar matches" policy is rejected — paraphrase queries miss aliases by design, and the reranker is the recall mechanism for those misses. (Auto-skip is reserved for explicit batch-eval modes where speed > paraphrase coverage.)

### 1.6 P6 — Honest confidence

A confidence score below threshold returns "not enough material" rather than a top-1 guess. The threshold is calibrated by the `corpus_gap_probe` cohort: gap queries should produce sub-threshold scores, in-corpus queries should not.

### 1.7 P7 — Korean-first design

Korean is the dominant query language. Korean tokenization symmetry (kiwipiepy on both query and index sides), Korean morpheme alias expansion, and contextual chunk prefixes in Korean for Korean docs are first-class concerns, not afterthoughts.

### 1.8 P8 — Mission-aware retrieval

Woowa mission concepts (`missions/roomescape`, `missions/shopping-cart`, etc.) are first-class metadata. A query that mentions a mission can hop to bridge docs that connect mission-specific terms to general CS concepts.

### 1.9 P9 — Single-process serving on M5

The serving runtime fits within M5 MacBook Air 13" 16GB unified memory + MPS. Multi-process / multi-machine production is out of scope (no JVM service like Vespa, no Docker-only deps that break on Apple Silicon).

### 1.10 P10 — Reproducible builds via remote GPU

Index builds run on RunPod L40S/A6000 with strict artifact provenance (sha256, manifest, contract verification). Builds are decoupled from local development (M5 only serves; never builds full index).

---

## 2. Architecture

### 2.1 High-level pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                  LEARNER QUERY (raw text + context)               │
│  context: prior_turn, mission_id, learner_profile, cohort_hint   │
└─────────────────────────────┬─────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  STAGE 1 — QueryPlanner                                           │
│  - normalize (whitespace, punctuation, casefold for Latin)        │
│  - detect language (ko / en / mixed) via CJK ratio + heuristic    │
│  - detect category hints (path tokens, concept aliases)           │
│  - detect intent (definition / comparison / symptom / mission /   │
│    drill / deep_dive)                                             │
│  - detect learner level (beginner / intermediate / advanced)      │
│  - extract concept candidates (alias dictionary lookup)           │
│  - extract aliases (kiwipiepy morpheme + Latin term expansion)    │
│  - extract symptoms (symptom phrase patterns)                     │
│  - bind mission_id (if learner_profile has active mission)        │
│  - resolve prior_turn anaphora (multi-turn context)               │
│  - emit: QueryPlan (versioned, traced)                            │
└─────────────────────────────┬─────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  STAGE 2 — Independent Candidate Generation (parallel)            │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐  │
│  │ LexicalRetriever (BM25)  │  │ DenseRetriever (BGE-M3)      │  │
│  │ → top 100                 │  │ → top 100                    │  │
│  ├──────────────────────────┤  ├──────────────────────────────┤  │
│  │ SparseRetriever (BGE-M3) │  │ SignalRetriever (rule-based) │  │
│  │ → top 100 (NOT rescore)  │  │ → top 20 (canonical paths)   │  │
│  ├──────────────────────────┤  ├──────────────────────────────┤  │
│  │ MetadataRanker (filter+ │  │ MissionBridgeRetriever        │  │
│  │ rank by role/level/etc.) │  │ (mission_id ↔ concept_id)    │  │
│  │ → re-ranks 100 max       │  │ → top 10                     │  │
│  ├──────────────────────────┤  └──────────────────────────────┘  │
│  │ LateInteractionRetriever │                                    │
│  │ (BGE-M3 ColBERT, opt.)   │                                    │
│  │ → top 50 hard-query path │                                    │
│  └──────────────────────────┘                                    │
└─────────────────────────────┬─────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  STAGE 3 — Fusion (weighted RRF + diversity)                      │
│  - per-language weight profile (ko / en / mixed)                  │
│  - per-intent weight profile (definition / comparison / etc.)     │
│  - per-cohort weight profile (beginner emphasis on primer-role)   │
│  - doc-diversity guard: no doc contributes more than N chunks     │
│  - forbidden_neighbor filter: drop candidates in forbidden set    │
│  - retriever provenance preserved (per-candidate retriever tag)   │
│  → top 120 fused                                                  │
└─────────────────────────────┬─────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  STAGE 4 — Reranker (always-on, language-aware)                   │
│  - default: BAAI/bge-reranker-v2-m3 (Korean-strong, 568M)         │
│  - input window: 50 (M5 production) / 100 (offline GPU eval)      │
│  - frontier candidates: Qwen3-Reranker-1.5B,                      │
│    gte-multilingual-reranker-base (Phase 7 A/B)                   │
│  - language fallback chain (Korean/mixed → multilingual reranker; │
│    English-only → English reranker option)                        │
│  - never auto-skip in production path                             │
│  → top 50 reranked, scored                                        │
└─────────────────────────────┬─────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  STAGE 5 — Context Assembly                                       │
│  - source_priority guard (cite from canonical docs)               │
│  - level filter (beginner query → primer/bridge; advanced query   │
│    → deep_dive/playbook)                                          │
│  - linked_paths companion expansion (graph walk for context)      │
│  - confidence score ('not in corpus' detection threshold)         │
│  - citation tracking (doc_id + chunk_id + relevance score)        │
│  - multi-turn coherence (prior 2-3 turn context aware)            │
│  → top_k=5 final + companions + citations + confidence            │
└─────────────────────────────┬─────────────────────────────────────┘
                              ▼
              ANSWER + CITATIONS + CONFIDENCE
```

### 2.2 Per-stage data contract

Every stage emits a typed object. The trace records all of them.

```text
QueryPlan (Stage 1)
  query_id, raw_query, normalized_query, language, category_hints,
  intent, learner_level, concept_candidates, aliases, symptoms,
  mission_id, prior_turn_context, must_include_paths, forbidden_paths,
  rerank_profile, query_plan_version

Candidate (Stage 2 output, 1 per retrieved chunk)
  chunk_id, doc_id, path, retriever (tag), rank, raw_score,
  normalized_score, features (per-retriever feature dict),
  provenance (which retriever found it, in which limit slot)

FusedCandidate (Stage 3 output)
  ...Candidate fields..., fusion_rank, fusion_score,
  contributing_retrievers (list of tags), diversity_group (doc_id)

RerankedCandidate (Stage 4 output)
  ...FusedCandidate fields..., rerank_rank, rerank_score,
  reranker_model (id + version)

FinalContext (Stage 5 output)
  top_k_docs, top_k_chunks, citations, companion_chunks,
  confidence_score, level_filter_applied, linked_paths_used,
  multi_turn_resolved (bool), assembly_decisions (trace)
```

### 2.3 Trace artifact contract

Every query writes one JSONL line to `reports/rag_eval/r3_candidate_trace_<run_id>.jsonl`:

```json
{
  "query_id": "...",
  "query_plan": { "version": "r3.0", "language": "ko", "intent": "definition", ... },
  "retrievers": {
    "lexical": [ { "path": "...", "rank": 1, "score": 13.2 }, ... ],
    "dense": [ ... ],
    "sparse": [ ... ],
    "signal": [ ... ],
    "metadata": [ ... ],
    "mission_bridge": [ ... ],
    "late_interaction": [ ... ]
  },
  "fusion": [ { "path": "...", "rank": 4, "features": { "rrf": 0.18, ... } }, ... ],
  "rerank": [ { "path": "...", "rank": 1, "score": 0.93 }, ... ],
  "final": [ { "path": "...", "rank": 1, "doc_role": "primer" }, ... ],
  "confidence": 0.87,
  "failure_class": null,
  "stage_ms": { "query_plan": 8.2, "lexical": 12.4, "dense": 31.8,
                 "sparse": 19.2, "signal": 5.1, "fusion": 11.7,
                 "rerank": 280.5, "context": 14.6 }
}
```

This is the primary debugging artifact. **Final nDCG without the trace is insufficient** for any system change decision.

---

## 3. Stage 1 — Query Understanding

### 3.1 QueryPlan derivation

Inputs:
- `raw_query` (str) — learner's text
- `prior_turn` (optional, for multi-turn anaphora resolution)
- `learner_profile` (optional, mission_id / mastered concepts / weak axes)
- `mode` (cheap / full / direct)

Outputs:
- `QueryPlan` object with all fields populated (see §2.2)

### 3.2 Language detection

```python
def detect_language(text: str) -> Literal["ko", "en", "mixed"]:
    cjk_ratio = count_cjk_chars(text) / max(1, len(text))
    if cjk_ratio > 0.3:
        return "ko"
    elif cjk_ratio > 0.0:
        return "mixed"
    else:
        return "en"
```

Test cases (Pilot Real qrel cohort):
- "DI가 뭐야?" → ko
- "What is dependency injection?" → en
- "Spring DI 패턴" → mixed

### 3.3 Korean morpheme expansion (kiwipiepy)

For language ∈ {ko, mixed}:

```python
def expand_korean_morphemes(text: str, kiwi: Kiwi) -> list[str]:
    tokens = kiwi.tokenize(text)
    return [t.form for t in tokens if t.tag.startswith(("NN", "VV", "VA"))]
```

Both query side (here) and index side (`corpus_loader._search_terms`) use the *same* kiwipiepy invocation. Symmetry test (10 sample queries) verifies token sets match within ~5%.

### 3.4 Concept candidate extraction

```python
def extract_concept_candidates(query_plan: QueryPlan, catalog: ConceptCatalogV3) -> list[str]:
    # 1. Direct alias lookup (case-folded, morpheme-normalized)
    # 2. Symptom pattern match (catalog.symptoms[*] regex)
    # 3. Category path inference (path token match)
    # 4. Mission_id binding (catalog.mission_ids reverse index)
    # → return concept_id list, ranked by match strength
```

The concept catalog v3 (from `rag-r3-corpus-v3-contract.md`) is the source of truth for concept_id ↔ aliases ↔ symptoms ↔ mission_ids mappings.

### 3.5 Intent classification

Intent labels: `definition`, `comparison`, `symptom`, `mission_bridge`, `deep_dive`, `drill`, `unknown`.

Lightweight classifier (rule-based + heuristic, no LLM call):
- "뭐야?", "what is", "정의" → definition
- "차이", "vs", "difference", "compare" → comparison
- "왜 안 돼", "why fails", "stale", "loop", "error" → symptom
- mission keyword + CS concept → mission_bridge
- "내부", "internals", "어떻게 작동" → deep_dive
- "맞춰봐", "drill", "퀴즈" → drill

The classifier emits a confidence score; below threshold → `unknown` (downstream uses default profile).

### 3.6 Multi-turn anaphora resolution

If `prior_turn` is provided:

```python
def resolve_anaphora(raw_query: str, prior_turn: PriorTurnContext) -> str:
    # Detect Korean pronoun/anaphora patterns:
    #   "그게", "그건", "그것", "그래서", "왜?" alone
    # Detect English: "it", "that", "why?" alone
    # If detected, prepend prior_turn.primary_concept as explicit subject
    # e.g., "왜?" with prior concept "Spring DI" → "Spring DI는 왜 필요해?"
```

Multi-turn cohort (Phase 3 Real qrel) has 10-15 anaphora queries to validate.

### 3.7 Mission_id binding

If `learner_profile.active_mission` is set:
- Inject `mission_id` into QueryPlan
- Boost MissionBridgeRetriever weight in fusion profile
- Allow `mission_bridge` doc_role candidates to be primary

---

## 4. Stage 2 — Independent Candidate Generators

### 4.1 LexicalRetriever (BM25 over fields)

**Purpose**: exact phrase match, Korean morpheme match, alias / title / section / anchor match.

**Implementation**: SQLite FTS5 or Tantivy lexical sidecar with separate fields:
- `title` (boost 3x)
- `aliases` (boost 2.5x — explicit author-curated lexical hints)
- `section` (boost 2x)
- `anchors` (boost 2x — extracted from doc retrieval-anchor-keywords)
- `body` (boost 1x)

**Query-side**:
- Raw query (case-folded)
- Korean morpheme expansion (kiwipiepy)
- Latin technical term variants (CamelCase / snake_case / kebab-case)

**Output**: top 100 candidates with field-attribution (which field matched).

**Why separate fields**: pollution-free retrieval. `aliases` is a clean lexical channel because the corpus contract guarantees `expected_queries` is *not* indexed there (commit `054a1a3` cuts the leak).

### 4.2 DenseRetriever (BGE-M3 dense)

**Purpose**: semantic similarity, paraphrase recall.

**Model default**: `BAAI/bge-m3` (1024-dim, 100+ languages, 8192-token context, MIT). fp16 on M5 MPS.

**Frontier candidates (Phase 7 A/B)**:
- `Qwen/Qwen3-Embedding-0.6B` (1024-dim, instruction-aware, Apache 2.0, requires query prompt prefix)
- `Alibaba-NLP/gte-multilingual-base` (305MB, 768-dim with elastic 128-768, Apache 2.0)

**Index**: LanceDB IVF_HNSW_SQ (recommended for 1024-dim per LanceDB docs >256-dim guide) or IVF_PQ as fallback.

**Output**: top 100 candidates with cosine similarity.

**Note on dense embedding**: The chunk's *embedding_body* is the clean section text (anchors and `expected_queries` excluded). Dense embeddings are trained on substantive content, not on alias soup. This is enforced in corpus_loader (`embedding_body` field separate from `body`).

### 4.3 SparseRetriever (BGE-M3 sparse, true inverted index)

**Purpose**: rare-word match, OOV token match (BGE-M3 dense often misses rare terms).

**Model**: `BAAI/bge-m3` sparse output (lexical weights over tokenized vocabulary).

**Implementation contract**: **inverted index, not rescore**. The corpus's `sparse_vec` payload (`{indices, values}`) builds an inverted index `token_id → [(doc_id, weight), ...]`. Queries lookup top-N tokens and aggregate weighted scores.

**Why true retrieval channel**: BGE-M3 sparse can find docs that dense + lexical both miss (rare tokens, technical jargon). Used as rescore-only (the prior implementation) wastes the model's discovery power.

**Frontier candidate (Phase 7)**: `gte-multilingual-base` sparse output; SPLADE-v3 family.

**Output**: top 100 candidates with sparse score.

### 4.4 SignalRetriever (rule-based canonical injection)

**Purpose**: domain knowledge override. When the learner asks "DI가 뭐야?", we *want* `spring/di-primer.md` retrieved regardless of what BM25/dense/sparse score.

**Implementation**: rule table — each rule maps `(intent, concept_id_set, mission_id)` to canonical paths.

```yaml
# Example rule (concept catalog v3)
- when:
    intent: definition
    concept_candidates: [spring/di]
  inject:
    - contents/spring/di-primer.md (rank 1)
    - contents/spring/di-vs-service-locator-chooser.md (rank 2)
```

**Output**: top 20 canonical paths with deterministic rank.

### 4.5 MetadataRanker (filter + rank features)

**Purpose**: enforce role/level/source-priority alignment.

**Operations**:
- Filter: drop candidates with `forbidden_paths` match.
- Boost: candidates matching `level == query_plan.learner_level` get +X feature.
- Boost: `doc_role == "primer"` for definition queries; `chooser` for comparison; `symptom_router` for symptom queries.
- Penalize: `source_priority < 50` candidates dropped to bottom.

**Output**: re-ranking annotation on existing candidates (does not add new candidates).

### 4.6 MissionBridgeRetriever (mission_id ↔ concept_id table)

**Purpose**: the learner asks about a Woowa mission term ("roomescape DAO 패턴"); surface the doc that bridges that mission to the CS concept.

**Implementation**: lookup table in concept catalog v3:

```yaml
- mission_id: missions/roomescape
  bridges:
    - concept_id: software-engineering/repository-pattern
      bridge_doc: contents/software-engineering/roomescape-dao-vs-repository-bridge.md
    - concept_id: spring/di
      bridge_doc: contents/spring/roomescape-di-bean-injection-bridge.md
```

**Output**: top 10 bridge candidates ranked by mission_id × concept_id intersection score.

### 4.7 LateInteractionRetriever (BGE-M3 ColBERT mode, optional)

**Purpose**: high-precision recall on hard queries (paraphrase, indirect phrasing).

**Model**: `BAAI/bge-m3` ColBERT mode output (multi-vector per chunk).

**Implementation challenge**: ColBERT MaxSim retrieval is expensive (per-token comparison). For our 27K chunk corpus:
- Chunk vectors: 27K × ~200 tokens × 1024 dim × fp16 = ~22GB raw → too large for M5
- **Solution**: ColBERT used as *retrieval channel* only for queries flagged as "hard" by Phase 7 measurement; uses sidecar PLAID-style index built once on RunPod.
- Default mode: rescore over top 50 from other retrievers (cheaper).

**Output**: top 50 if engaged, else not invoked.

**Phase 7 decision point**: measure if ColBERT-as-retrieval-channel adds primary docs that other retrievers miss in the `paraphrase_human` cohort. If yes → engage; if no → keep as rescore only.

---

## 5. Stage 3 — Fusion

### 5.1 Weighted RRF (Reciprocal Rank Fusion)

```python
def fuse(candidates_per_retriever: dict[str, list[Candidate]],
         weights: dict[str, float],
         k: int = 60) -> list[FusedCandidate]:
    # RRF: score(d) = sum_r weight[r] * (1 / (k + rank_r(d)))
    # k=60 is the standard RRF constant
```

### 5.2 Per-cohort weight profiles

Different query types weight retrievers differently:

```yaml
# Definition (Korean) — primer/bridge dominant
ko_definition:
  lexical: 0.8
  dense: 1.0
  sparse: 0.7
  signal: 1.5      # rule-based primer is best for definitions
  metadata: 0.5    # used as feature, not weight
  mission_bridge: 0.3
  late_interaction: 0.0

# Comparison — chooser docs preferred
comparison:
  lexical: 0.6
  dense: 1.0
  sparse: 0.8
  signal: 1.2
  metadata: 0.5
  mission_bridge: 0.2
  late_interaction: 0.4

# Symptom — symptom_router doc role boosted
symptom:
  lexical: 1.0     # symptom phrases are usually exact
  dense: 0.7
  sparse: 0.9
  signal: 1.0
  metadata: 0.8    # symptom_router role match
  mission_bridge: 0.2
  late_interaction: 0.0

# Mission bridge — explicit bridge weight ↑
mission_bridge:
  lexical: 0.6
  dense: 0.8
  sparse: 0.5
  signal: 0.5
  metadata: 0.3
  mission_bridge: 2.0   # dominant
  late_interaction: 0.0
```

Weights start as Phase 7 A/B initial values. Calibrated by Pilot baseline (Phase 6 measurement).

### 5.3 Doc-diversity guard

After fusion, no single `doc_id` may contribute more than 2 chunks to the top 50. Excess chunks are dropped to enforce doc diversity (avoid one doc flooding the rerank input).

### 5.4 Forbidden_neighbor filter

Drop any candidate whose `path` matches the QueryPlan's `forbidden_paths` set (derived from concept catalog v3 `forbidden_neighbors`).

### 5.5 Retriever provenance

Each fused candidate carries `contributing_retrievers: list[str]` — which retrievers found it. The trace records this so failure-mode analysis can attribute "primary doc was found by sparse but lost in fusion under-rank" precisely.

---

## 6. Stage 4 — Reranker

### 6.1 Model selection

**Default (production runtime)**: `BAAI/bge-reranker-v2-m3`
- 568M parameters, ~1.1GB fp16
- Multilingual, Korean-strong
- Apache 2.0
- Fits in M5 16GB with BGE-M3 dense + sparse

**Frontier candidates (Phase 7 A/B)**:
- `Qwen/Qwen3-Reranker-1.5B` (Apache 2.0, instruction-aware)
- `Alibaba-NLP/gte-multilingual-reranker-base` (305MB, multilingual, Apache 2.0)

**Language fallback chain** (only triggered if default unavailable):
- Korean / mixed query: `bge-reranker-v2-m3` → `gte-multilingual-reranker-base` → `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`
- English-only query: same chain (English-only fallback like `mxbai-rerank-base-v1` is *not* allowed — Korean coverage is a hard requirement, English-only fallback would silently regress mixed-cohort)

### 6.2 Reranker input window

- **M5 production**: 50 candidates from fusion top → reranker
- **Offline GPU eval**: 100 candidates → reranker (max recall)
- Window is config-driven (`r3/config.py:resolve_rerank_input_window`); never hardcoded as `top_k * 2`.

### 6.3 Always-on policy (P5)

**No auto-skip in production**. Even if the lexical sidecar matches the alias exactly, the reranker still scores the top 50 — paraphrase queries miss the alias by construction, and the reranker is the recall mechanism for them.

Auto-skip is allowed only in:
- Explicit batch eval mode (e.g., `--reranker=disabled` for ablation studies)
- Drill mode (where the question is exact-match by design)

### 6.4 Latency expectation

`bge-reranker-v2-m3` on M5 MPS, fp16, 50 pairs:
- Warm: 150–400ms (depends on context length)
- Cold first call: ~2–5s (model load)

Daemon process keeps the reranker warm to avoid cold latency on every query.

### 6.5 Reranker demotion metric

Per-query: `(rerank_rank - fusion_rank)` for the primary path. A negative number means the reranker improved primary rank; a positive number means demotion.

Cohort-level: Korean / beginner cohort demotion rate. If reranker systematically demotes Korean primary docs (e.g., bias toward English content in pre-training), Phase 7 A/B selects a less-biased reranker.

---

## 7. Stage 5 — Context Assembly

### 7.1 Top-k selection

Default `top_k = 5`. Rerank top 50 → top 5 final.

### 7.2 Source priority guard

Final top-k must satisfy: at least one chunk has `source_priority >= 80` (canonical doc). If not, the assembly stage backfills from the SignalRetriever's canonical paths.

### 7.3 Level filter

Beginner query (`learner_level == "beginner"`):
- Prefer `doc_role ∈ {primer, bridge, symptom_router, drill}`
- Demote `doc_role == "deep_dive"` unless query intent is `deep_dive`

Advanced query: opposite.

### 7.4 Linked_paths companion expansion

If the top-1 doc has `linked_paths` in frontmatter, include the first 1-2 linked docs as companions (separate `companion_chunks` list). Companions do not displace primary; they are surfaced as "참고:" supplementary citations.

### 7.5 Confidence score

```python
confidence = clamp(top_1_rerank_score, 0.0, 1.0)
if confidence < CONFIDENCE_THRESHOLD:
    return NotInCorpus(top_5_attempts, message="not enough material")
```

`CONFIDENCE_THRESHOLD` calibrated on `corpus_gap_probe` cohort: should produce sub-threshold confidence on gap queries while in-corpus queries score above. Initial estimate: 0.55-0.65 (Phase 6 calibration).

### 7.6 Citation tracking

Every returned doc carries:
- `doc_id`, `chunk_id`, `path`
- `relevance_score` (rerank score)
- `contributing_retrievers` (which retrievers found it)
- `confidence`

The AI coach surface includes citations in the answer:

```
참고:
- contents/spring/di-primer.md#chunk_2 (relevance 0.93)
- contents/spring/di-vs-service-locator-chooser.md#chunk_1 (relevance 0.87)
```

### 7.7 Multi-turn coherence

If `prior_turn` was used to resolve anaphora, the final answer references that resolution explicitly:

> "스프링 DI(이전 턴 주제) 가 왜 필요한지 설명할게."

This is the testable contract for the multi-turn cohort.

---

## 8. Eval Suite

### 8.1 Real qrel cohorts (200q, 6 cohort, human-curated)

Defined in detail in `rag-r3-corpus-v3-contract.md` and `tests/fixtures/r3_qrels_real_v1.json`. Summary:

| Cohort | N | Purpose |
|---|---|---|
| `paraphrase_human` | 50 | learner re-phrases doc title in entirely different words |
| `confusable_pairs` | 40 | DI / Service Locator / Factory; MVCC / locking / isolation |
| `symptom_to_cause` | 30 | "stale list", "login loop", "403 after role change" |
| `mission_bridge` | 30 | Woowa mission term → CS concept |
| `corpus_gap_probe` | 20 | intentional gap (we don't have a doc for these) |
| `forbidden_neighbor` | 30 | wrong doc must not be primary |

### 8.2 Metrics

Per cohort, per language, per level:

| Metric | Definition | Gate (Pilot) |
|---|---|---|
| `retriever_recall@K` | per-retriever, primary in top K | diagnostic |
| `candidate_recall@100` | primary in fusion top 100 | ≥ 0.95 (Pilot) |
| `rerank_input_recall@50` | primary in reranker input | ≥ 0.97 (Pilot) |
| `final_hit@5` | primary in final top 5 | ≥ 0.85 (Pilot) |
| `final_nDCG@5` | nDCG with primary/acceptable grades | ≥ 0.85 (Pilot) |
| `forbidden_rate@5` | forbidden_path in final top 5 | == 0.0 (strict) |
| `corpus_gap_false_confidence_rate` | gap query top-1 confidence > threshold | ≤ 0.10 |
| `reranker_demotion_rate` | rerank demoted primary (negative delta rank) | ≤ 0.10 (Korean cohort) |
| `paraphrase_robustness_drop` | paraphrase cohort `final_hit@5` minus expected_queries cohort | ≤ 0.05 |

The last metric is critical: if the system performs much worse on paraphrase than on direct alias match, it is over-relying on alias indexing and circular leak risk is back.

### 8.3 Failure taxonomy (9 classes)

Every hard failure is classified into exactly one:

```
candidate_absent          — primary not in any retriever's top K
retriever_absent          — primary in some retrievers but missing from a specific one (gap)
fusion_under_ranked       — primary in fusion but ranked below 50
reranker_demoted          — primary in rerank input but pushed out of top 5
dedupe_lost               — primary chunk dropped by doc-diversity guard
metadata_blocked          — primary dropped by forbidden_neighbor or level filter
qrel_incomplete           — retrieved doc is acceptable but not in qrel.acceptable_paths
corpus_gap                — no adequate corpus document exists
query_understood_badly    — query plan picked wrong intent / language / concept
```

The `failure_taxonomy_classifier` reads the trace and assigns a class deterministically. Cohort-level failure breakdowns drive next-iteration priorities.

### 8.4 Trace artifact

`reports/rag_eval/r3_candidate_trace_<run_id>.jsonl` (one line per query, schema in §2.3).
`reports/rag_eval/r3_failure_taxonomy_<run_id>.json` (cohort-level breakdown).
`reports/rag_eval/r3_corpus_gap_queue_<run_id>.json` (queries flagged `corpus_gap` → input to Wave C corpus authoring).

### 8.5 Calibration phases

- **Phase 6 (Pilot, 50 docs)**: gate values are *initial estimates*. Pilot measurement establishes the realistic baseline.
- **Phase 8 (Wave A/B/C/D, full corpus)**: gates updated based on pre-cutover full-corpus measurement.
- **Phase 10 (production cutover)**: final gates locked in `config/rag_models.json`.

---

## 9. Runtime Constraints (M5 MacBook Air 13" 16GB)

### 9.1 Memory budget (fp16)

| Component | RAM (fp16) |
|---|---|
| BGE-M3 dense encoder | ~1.1 GB |
| BGE-M3 sparse encoder (same model, shared forward) | 0 additional |
| BGE-M3 ColBERT mode (if engaged) | ~1.1 GB additional (shared model, separate output) |
| `bge-reranker-v2-m3` | ~1.1 GB |
| LanceDB index (27K chunks × 1024 dim + sparse + sidecars) | ~2.5–3 GB |
| Working memory per query (dense vector cache, etc.) | ~0.5–1.0 GB |
| **Total RAG serving footprint** | **~5–7 GB** |

macOS + browser + IDE typically consume 5–8 GB. The 16 GB unified memory comfortably hosts the R3 stack with normal multitasking.

### 9.2 Latency budget (warm, MPS)

| Stage | Budget (warm) |
|---|---|
| QueryPlan | ≤ 10 ms |
| LexicalRetriever | ≤ 30 ms |
| DenseRetriever (BGE-M3 encode + index search) | ≤ 80 ms |
| SparseRetriever | ≤ 50 ms |
| SignalRetriever | ≤ 5 ms |
| MetadataRanker | ≤ 15 ms |
| MissionBridgeRetriever | ≤ 5 ms |
| Fusion + diversity + forbidden filter | ≤ 30 ms |
| Reranker (50 pairs, MPS) | ≤ 400 ms |
| Context assembly | ≤ 20 ms |
| **Total p95 warm target** | **≤ 700 ms** |

Cold start (first query, model load, HF cache hit): 5–10 s. Mitigated by daemon warm service.

### 9.3 fp16 mandatory

All models run as fp16 on Apple Silicon MPS. fp32 not supported (memory budget). fp16 numerical precision adequate for retrieval (verified by BGE-M3 paper benchmarks).

### 9.4 Daemon warm service

The query encoder and reranker stay loaded in a long-running daemon process. `bin/rag-ask` and `bin/rag-eval` use `--via-daemon` to avoid model re-load per query.

### 9.5 CPU-only fallback

CPU-only operation is documented as **degraded mode**:
- Reranker on CPU: 50–150 ms per pair × 50 pairs = 2.5–7.5 s
- 5–15× slower than MPS
- Not a supported production configuration; only for emergency / non-Apple-Silicon dev

---

## 10. Model Stack Matrix

| Role | Default | Frontier candidate (Phase 7 A/B) | License | Notes |
|---|---|---|---|---|
| Dense encoder | `BAAI/bge-m3` (1024-dim, 100+ lang, 8192 ctx) | `Qwen/Qwen3-Embedding-0.6B` (1024-dim, instruction-aware), `Alibaba-NLP/gte-multilingual-base` (768-dim) | MIT / Apache 2.0 | fp16 mandatory |
| Sparse encoder | `BAAI/bge-m3` sparse output | `gte-multilingual-base` sparse, `naver/splade-v3` (English-strong) | MIT / Apache 2.0 | true inverted index |
| Reranker | `BAAI/bge-reranker-v2-m3` (568M, multilingual, Korean-strong) | `Qwen/Qwen3-Reranker-1.5B`, `Alibaba-NLP/gte-multilingual-reranker-base` | Apache 2.0 | always-on |
| Late interaction | `BAAI/bge-m3` ColBERT mode | `colbert-ir/colbertv2.0` (English fallback only) | MIT | optional, hard-query path |
| Korean tokenizer | `kiwipiepy` | (no alternative needed) | LGPL/free | symmetric query+index |

**Excluded from production code path**:
- `jinaai/jina-embeddings-v5-text-small` (CC-BY-NC 4.0, non-commercial) — offline eval only
- `mixedbread-ai/mxbai-rerank-base-v1` (English-only, would silently regress Korean cohort)

---

## 11. Backend Matrix

| Backend | Role | Strength | Risk | M5 fit |
|---|---|---|---|---|
| **LanceDB-improved** | Primary candidate | Lowest migration cost (current artifact reusable). Native dense + Tantivy FTS; sparse via sidecar inverted index. | Sparse retrieval requires custom sidecar (in-memory index for Pilot, persisted PLAID-style for full corpus). | ✓ fits 16GB |
| **Qdrant + lexical sidecar** | Comparator | Native dense + sparse + multivector. Simpler vector engine ergonomics. | Lexical BM25 requires sidecar (Qdrant payload-filter ≠ BM25 ranking). 2-store sync complexity. | ✓ fits with embedded mode |
| **Vespa** | Frontier comparator only | Strongest integrated rank framework (BM25, vectors, phased ranking, feature logging). | JVM (1-2 GB resident), YQL learning curve, Docker-or-native ops. Overspec for 27K chunks. | ⚠ tight fit (JVM compresses runtime budget) |
| **Legacy v2** | Rollback safety | Already operational, smoke-tested. | MiniLM 384-dim is 2022-era. No sparse, no multivector, no instruction-aware. | ✓ minimal footprint |

**Selection (Phase 6 + Phase 7 measurement)**:
1. Pilot Phase 6: LanceDB-improved is the default (lowest migration cost). Measure against Real qrel suite.
2. Phase 7 A/B: Qdrant comparator built on Pilot corpus + Real qrel; compare quality + latency + memory.
3. Vespa only if neither LanceDB-improved nor Qdrant meets the calibrated gate.

---

## 12. Failure Modes Addressed

This section enumerates failure modes the spec explicitly defends against. Each maps to a Phase 6 measurement.

| Failure Mode | Defense | Cohort Test |
|---|---|---|
| Alias-only retrieval (circular leak) | `expected_queries` excluded from indexing channels (commit `054a1a3`); paraphrase cohort gate | `paraphrase_human` |
| Confusable mis-routing (DI → Service Locator) | `confusable_with` + `forbidden_neighbors` in catalog v3; SignalRetriever rule | `confusable_pairs`, `forbidden_neighbor` |
| Symptom not routed to cause | `symptom_router` doc role + symptoms field + intent classifier | `symptom_to_cause` |
| Mission term unknown to system | `MissionBridgeRetriever` + mission_id ↔ concept_id table | `mission_bridge` |
| Hallucinated confidence on gap | `confidence < threshold` → "not enough material" | `corpus_gap_probe` |
| Korean weakness | kiwipiepy symmetry + Korean-strong reranker + cohort-specific weights | `paraphrase_human` (ko subset) |
| Beginner gets deep-dive | `level` filter in MetadataRanker + Stage 5 | implicit (level cohort split) |
| Multi-turn anaphora ignored | Stage 1 anaphora resolution + prior_turn context | (Phase 9 multi-turn fixture) |
| Anchor pollution in dense embeddings | `embedding_body` separate from `body` (anchors excluded from dense input) | latent dense vector quality (Phase 6 trace inspection) |
| Single doc floods top-K | doc-diversity guard in fusion (≤ 2 chunks per doc in top 50) | (verified in trace) |
| Reranker auto-skip masks paraphrase miss | always-on policy (P5) | `paraphrase_human` |

---

## 13. Implementation Constraints

This document is design-only. Implementation is in Phase 5. Constraints on implementation:

### 13.1 Module layout

`scripts/learning/rag/r3/` — already exists (29 files). Phase 5 extends:

```
r3/
  query_plan.py          # Stage 1 (existing, extend with anaphora, mission_id)
  candidate.py           # Candidate / FusedCandidate / RerankedCandidate dataclasses
  retrievers/
    lexical.py           # existing, extend with field-weighted BM25
    dense.py             # existing
    sparse.py            # existing in-memory PoC → production sidecar (Phase 5)
    signal.py            # existing
    metadata.py          # existing
    mission_bridge.py    # NEW (Phase 5)
    late_interaction.py  # NEW (Phase 5, optional)
  rerankers/
    cross_encoder.py     # existing, extend with always-on policy
    profile.py           # existing
  fusion.py              # existing, extend with per-cohort weight profiles
  context.py             # NEW (Phase 5, Stage 5)
  config.py              # existing, extend with new knobs
  search.py              # existing, top-level orchestrator
  eval/
    qrels.py             # existing, schema v3 alignment
    metrics.py           # existing, add per-cohort metrics
    failure_taxonomy.py  # NEW (Phase 5, deterministic classifier)
    trace.py             # existing, extend with all retriever outputs
    backend_compare.py   # existing
  index/
    lance_runtime.py     # existing
    sparse_inverted_index.py  # NEW (Phase 5)
    lexical_sidecar.py   # existing
    mission_bridge_table.py   # NEW (Phase 5)
    contextual_prefix_indexer.py  # NEW (Phase 5)
```

### 13.2 Backwards compatibility

The `searcher.py` legacy and Lance backends remain available (`--rag-backend legacy`, `--rag-backend lance`). R3 is opt-in via `--rag-backend r3` until Phase 10 production cutover.

### 13.3 Tests

Every new module has unit tests in `tests/unit/test_rag_r3_*.py`. Integration tests in `tests/integration/test_r3_pipeline.py`.

### 13.4 Determinism

Given fixed seeds and frozen models, the same query produces the same trace. (Stochasticity is allowed only in async/parallel retrieval order if the merge is deterministic.)

---

## 14. Phase 6 Cutover Gates (Pilot baseline)

These gates are *initial estimates*. The Pilot measurement on 50 docs + Real qrel 200q calibrates them.

```
candidate_recall@100 (overall)         >= 0.95
candidate_recall@100 (Korean)          >= 0.92
rerank_input_recall@50                 >= 0.97
final_hit@5 (overall)                  >= 0.85
final_hit@5 (per cohort)               >= 0.80 (each of 6 cohorts)
final_nDCG@5 (overall)                 >= 0.85
forbidden_rate@5                       == 0.0
corpus_gap_false_confidence_rate       <= 0.10
reranker_demotion_rate (Korean)        <= 0.10
paraphrase_robustness_drop             <= 0.05
p95 warm latency (M5 MPS)              <= 700 ms
cold start latency                     <= 10 s (HF_HUB_OFFLINE=1)
```

Phase 6 measurement either passes (proceed to Phase 7 frontier A/B) or fails (root cause audit + spec adjustment).

---

## 15. Phase 8 Cutover Gates (full-corpus, post Wave migration)

After Wave A/B/C/D corpus migration:

```
candidate_recall@100 (overall)         >= 0.97
candidate_recall@100 (Korean)          >= 0.95
final_hit@5 (overall)                  >= 0.93
final_hit@5 (per cohort)               >= 0.90
final_nDCG@5                           >= 0.92
forbidden_rate@5                       == 0.0
paraphrase_robustness_drop             <= 0.03
p95 warm latency                       <= 700 ms (unchanged)
learner repeat-question-rate           cutover_前 대비 -30% (history.jsonl analysis)
```

These are *production cutover* gates. Met → switch `selected_artifact` / `backend` / `runtime_policy` in `config/rag_models.json` and route learners to R3.

---

## 16. References

### Internal
- `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md` — driving plan (Section 0 Principle Correction)
- `docs/worklogs/rag-r3-corpus-v3-contract.md` (forthcoming) — corpus spec the system requires
- `tests/fixtures/r3_qrels_real_v1.json` (forthcoming) — Real qrel suite 200q
- `reports/rag_eval/archive/2026-05-02-circular-leak-baseline/README.md` — historical baseline (NOT quality evidence)

### External (official)
- BGE-M3 paper: https://arxiv.org/abs/2402.03216
- BGE-M3 model card: https://huggingface.co/BAAI/bge-m3
- bge-reranker-v2-m3: https://huggingface.co/BAAI/bge-reranker-v2-m3
- Qwen3-Embedding family: https://huggingface.co/Qwen
- gte-multilingual-base (mGTE EMNLP 2024): https://huggingface.co/Alibaba-NLP/gte-multilingual-base
- gte-multilingual-reranker-base: https://huggingface.co/Alibaba-NLP/gte-multilingual-reranker-base
- LanceDB hybrid search: https://docs.lancedb.com/search/hybrid-search
- LanceDB indexing (1024-dim guide): https://docs.lancedb.com/indexing
- Qdrant hybrid search: https://qdrant.tech/documentation/concepts/hybrid-queries/
- Qdrant multivector: https://qdrant.tech/documentation/tutorials-search-engineering/using-multivector-representations/
- Vespa hybrid search: https://docs.vespa.ai/en/learn/tutorials/hybrid-search
- Anthropic Contextual Retrieval: https://www.anthropic.com/research/contextual-retrieval
- ColBERTv2 (PLAID): https://arxiv.org/abs/2112.01488
- kiwipiepy: https://github.com/bab2min/kiwipiepy

### Excluded (license blocked from production)
- jina-embeddings-v5-text-small (CC-BY-NC 4.0): https://huggingface.co/jinaai/jina-embeddings-v5-text-small
- jina-reranker-v2-base-multilingual: https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual

---

## 17. Decision Log

| Decision | Rationale | Source |
|---|---|---|
| LanceDB-improved as primary candidate | lowest migration cost; native dense+FTS; sparse via sidecar | Plan Section 0, Phase 5 dependency |
| `bge-reranker-v2-m3` as default reranker | Korean-strong, multilingual, Apache 2.0, M5 fp16 fit | Plan Section 1.4 |
| Always-on reranker | paraphrase robustness (P5) | Plan Section 0 (auto-skip 폐기) |
| `expected_queries` qrel-seed only | structural circular leak fix (commit 054a1a3) | Plan Section 1 |
| 200q × 6 cohort Real qrel | decouple from current corpus shape | Plan Section 6 |
| Pilot 50 docs in v3 contract | small enough to author carefully, large enough for statistical signal | Plan Section 7 |
| Frontier A/B on Pilot baseline only | corpus-agnostic principle (P1) | Plan Section 0 (Principle Correction) |
| Vespa as conditional comparator | overspec for 27K chunks, JVM resident overhead | Plan Section 11 |
| Excluded mxbai-rerank-base-v1 | English-only, would regress Korean cohort | Plan Section A1 finding (external review) |
| Excluded Jina v5 from production | CC-BY-NC 4.0 license | Plan Section 6 |

---

## 18. Open spec questions (Phase 6 measurement decides)

1. Does ColBERT-as-retrieval-channel add primary docs that other retrievers miss in `paraphrase_human`? If yes → engage as 7th retriever; if no → keep as rescore only.
2. Per-cohort fusion weight profile — initial values are estimates; calibrated by Pilot.
3. CONFIDENCE_THRESHOLD for "not enough material" — calibrated on `corpus_gap_probe`.
4. Reranker input window — 50 vs 30 vs 70 — calibrated on M5 latency budget vs recall trade-off.
5. LateInteractionRetriever PLAID index size on M5 — feasibility check in Phase 5.

---

## 19. Verdict

This spec defines the system the **ideal corpus** would deserve. It does not optimize against the current corpus; it does not chase the legacy v2 baseline; it does not gate on circular qrel measurements. It is Korean-first, learner-first, paraphrase-robust, mission-aware, honest about gaps, and runs on the learner's M5 + MPS within 700ms warm.

The corpus is brought into compliance via `rag-r3-corpus-v3-contract.md`. The Real qrel suite (`tests/fixtures/r3_qrels_real_v1.json`) measures whether the spec is met. Phase 6 establishes the Pilot baseline; Phase 7 selects frontier models against it; Phase 8 promotes Wave-migrated full corpus; Phase 10 cutovers production when full-corpus gates are met.

This document is the design anchor. It is not negotiable for accidents of the current corpus shape.

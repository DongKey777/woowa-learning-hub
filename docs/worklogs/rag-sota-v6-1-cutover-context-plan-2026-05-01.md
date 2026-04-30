# RAG SOTA v6.1 — Cutover, Context-Aware Retrieval, and Frontier Track

Source plan: `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md`

This worklog supersedes the v6 execution order where it conflicts with current
code. The goal is unchanged: move production from legacy v2 MiniLM/SQLite to the
R2 bge-m3/LanceDB stack, then improve Korean and multi-turn retrieval.

## Executive Decision

R2 (`BAAI/bge-m3` + LanceDB + `fts,dense,sparse`) remains the production
cutover target because it is already validated on this corpus and has the best
local holdout result we have measured. It is not the absolute April 2026
frontier embedding stack. Qwen3 Embedding/Reranker and Jina v5 must be tracked
as frontier candidates, but they should not block the R2 cutover.

The corrected execution order is:

1. A0/A1: v3 readiness + backend auto-detect.
2. A2/A3: cutover regression comparator + actual legacy-vs-Lance measurement.
3. A4/A5: rollback runbook + transactional swap, run by the AI session.
4. C0-C6: context-aware multi-query retrieval, with weighted RRF instead of
   string-concatenated rewrites.
5. S1: LanceDB index-parameter sweep, because current IVF settings are not
   aligned with official sizing guidance for a 27k-row corpus.
6. F1: frontier benchmark track: Qwen3-Embedding-0.6B / Qwen3-Reranker-0.6B,
   plus optional Jina v5 as research-only because of license.
7. D: Korean corpus boost via contextual chunk prefixes and retrieval anchors.

## Corrections to v6

### A0. Readiness Must Understand v3 Before `augment()`

Original v6 starts with `integration.augment()` backend detection. Current code
had an earlier blocker: `indexer.is_ready()` only accepted v2 shape
(`index.sqlite3`, `dense.npz`, `index_version == 2`). A v3 LanceDB swap would
be marked stale/missing before `augment()` could choose `backend="lance"`.

Status: fixed in commit `d673c48`.

### A5. Learner Must Not Execute the Swap

Original v6 says "사용자 직접 실행". This violates AGENTS: the learner runs zero
commands. The AI session must run the swap and report one Korean status line per
step.

Correct swap algorithm:

1. Create a staging directory under `state/cs_rag_next_<stamp>`.
2. Extract the R2 artifact into staging.
3. Verify `manifest.json.index_version == 3`, `encoder.model_id == "BAAI/bge-m3"`,
   row count, modalities, and artifact checksum.
4. Move current `state/cs_rag` to `state/cs_rag_archive/v2_<stamp>`.
5. Atomically move staging to `state/cs_rag`.
6. Run offline smoke with `HF_HUB_OFFLINE=1`.
7. If any post-swap smoke fails, restore the archive immediately.

Use `shasum -a 256` on macOS instead of assuming `sha256sum`.

### C1/C5. Do Not Concatenate Rewrites into FTS Strings

The v6 sketch suggests prepending rewrite candidates to FTS with a separator.
That is fragile:

- LanceDB FTS query strings are not SQLite FTS5 boolean expressions.
- The official LanceDB hybrid path already uses RRF for semantic + text fusion.
- Query candidates should be separate ranked lists, not one noisy query.

Correct algorithm: generate one ranked list per query candidate and use weighted
RRF.

### C4. History Has `rag_ask` Events, Not `primary_topic`

`learner_memory.build_rag_ask_event()` records `prompt`, `concept_ids`,
`category_hits`, `top_paths`, `tier`, and `rag_mode`. It does not record
`primary_topic`. Multi-turn context should use the last two `rag_ask` events by
`prompt`, `concept_ids`, and `top_paths`.

### S1. LanceDB Index Parameters Need a Sweep

Current code builds dense IVF_PQ with `num_partitions=256` and
`num_sub_vectors=64`. LanceDB guidance says IVF_PQ starts around
`num_rows // 4096` partitions and `dimension // 8` sub-vectors. For 27,155 rows
and 1024 dimensions, the starting point is roughly 6-7 partitions and 128
sub-vectors, not 256/64.

This does not invalidate R2; R2 already measured well. It does mean v6 should
add an index-parameter sweep before declaring the stack locked.

## April 2026 SOTA Check

| Candidate | Official spec | Production verdict |
|---|---|---|
| `BAAI/bge-m3` | 1024 dim, 8192 tokens, 100+ languages, dense+sparse+ColBERT, MIT. Official card recommends hybrid retrieval + reranking. | Keep as R2 production because it is local, tri-modal, permissive, and already wins our holdout. Not absolute frontier. |
| `Qwen/Qwen3-Embedding-0.6B` | Apache-2.0, 100+ languages, 32k context, up to 1024 dims, MRL, instruction-aware. Official card reports Qwen3-Embedding-8B No.1 multilingual MTEB as of 2025-06-05 and 0.6B beating BGE-M3 in reported retrieval mean. | Add F1 benchmark. Strong April 2026 frontier candidate, but dense-only for our current storage path and instruction handling must be evaluated. |
| `Qwen/Qwen3-Reranker-0.6B` | Apache-2.0, 100+ languages, 32k context, instruction-aware reranking. | Add F1/B replacement candidate. Potentially more SOTA than `bge-reranker-v2-m3`, but needs latency and integration work. |
| `jinaai/jina-embeddings-v5-text-small` | 677M, 1024 dim, 32k context, Matryoshka dims, task adapters, released 2026-02-18, CC BY-NC 4.0. | Research-only unless licensing is explicitly acceptable. Dense-only result already did not beat R2 on our Korean distribution. |
| `BAAI/bge-reranker-v2-m3` | Apache-2.0, multilingual, cross-encoder, max 512 pair tokens in official HF example. | Keep as immediate reranker A/B candidate after cutover. |

Conclusion: v6 should not claim "single production stack is SOTA" without
qualification. The accurate claim is: "R2 is the best measured local,
permissive, tri-modal stack for this corpus; Qwen3 is the frontier candidate to
benchmark next."

## Retrieval Algorithm v6.1

### Query Candidates

Build a bounded query candidate list:

1. `q0`: original prompt plus explicit `topic_hints`.
2. `q_followup`: only when follow-up detector fires; append a compact context
   phrase derived from the last two `rag_ask` events.
3. `q_rewrite`: up to three validated `query-rewrite-v1` outputs.
4. `q_prf`: deterministic PRF/RM3 fallback only when no AI rewrite exists and
   the first-pass candidate pool is thin.

Hard cap: four candidates per search call.

### Candidate Generation

For each query candidate:

- Lance FTS: search the indexed text normally. For Korean queries, add a
  `search_terms` candidate generated by the same kiwipiepy path used during
  indexing. Keep raw-body ngram search as a parallel FTS list.
- Lance dense/sparse/ColBERT: batch encode all candidates once through
  `BgeM3Encoder.encode_corpus()` instead of calling `encode_query()` one by one.
- Legacy path: run FTS5 and dense per candidate, preserving old behavior when no
  candidates exist.

### Fusion

Use weighted RRF:

`score(d) = Σ_query Σ_modality w_query * w_modality / (k + rank(d))`

Initial weights:

- query: original `1.0`, follow-up-expanded `0.9`, normalized rewrite `0.8`,
  HyDE/decomposition `0.7`, PRF `0.5`.
- modality: FTS raw `1.0`, FTS Korean terms `1.0`, dense `1.0`, sparse rescore
  `0.05` additive as today, ColBERT `0.03` additive as today.

Do not use a fixed score threshold like `0.3`; RRF scores are not calibrated
across modality counts. Trigger extra candidates by structural signals:

- fewer than `top_k * 4` unique candidates before rerank,
- zero hits in the routed category when learning points are present,
- follow-up detector fired and the original prompt has fewer than 25 chars,
- Korean-only query and no Korean/mixed hit in the first pool.

### Complexity

Let `Q <= 4`, `M <= 4`, `P = 80` base pool. Worst-case retrieval is
`O(Q * M * P log P)` for ranked-list construction plus cross-encoder rerank on
the final bounded pool. Encoding is batched, so model overhead is one batch per
search rather than one model call per rewrite.

This is more efficient than "dual-search fallback" because it avoids recursively
calling the full search path and re-running boost/filter/rerank logic twice.

## Revised Commit Plan

Each item should be a separate commit with a specific message.

1. `Enable LanceDB v3 readiness and backend auto-detection for RAG cutover`
   - status: done, commit `d673c48`
   - tests: `python3 -m pytest tests/unit/test_cs_readiness.py tests/unit/test_integration_backend_auto.py`

2. `Add cutover report comparator for legacy-to-Lance RAG gates`
   - status: done, commit `29711aa`
   - tests: `python3 -m pytest tests/unit/test_rag_cutover_compare.py`

3. `Document transactional rollback for RAG index cutover`
   - add `docs/runbooks/rag-rollback.md`
   - include AI-run restore flow, smoke commands, and failure handling.

4. `Lock measured R2 RAG model configuration`
   - add `config/rag_models.json`
   - include artifact provenance, encoder/reranker licenses, modalities,
     row count, and measured latency.

5. `Run legacy-vs-Lance cutover regression and record gate result`
   - run legacy v2 holdout if missing.
   - run `scripts/learning/cli_rag_cutover_compare.py`.
   - commit only the summary JSON/worklog, not bulky scratch state.

6. `Add weighted multi-query RRF primitives for context-aware RAG`
   - implement pure helpers first: query candidate object, weighted RRF,
     follow-up detector, recent rag_ask context reader.
   - no production behavior change yet.

7. `Wire query-rewrite-v1 outputs into integration augment`
   - consume existing sidecars inside `integration.augment()`.
   - pass `rewrite_candidates` to searcher with debug metadata.

8. `Batch Lance query candidate encoding for rewrite-aware search`
   - replace per-candidate `encode_query()` calls with one
     `encode_corpus(candidates)`.
   - preserve old one-query path for legacy and tests.

9. `Evaluate LanceDB IVF parameter sweep for the R2 corpus`
   - compare current `256/64` vs official-start `num_rows//4096` and
     `dimension//8`, plus exact/unindexed for this corpus size.
   - gate on nDCG, primary recall, P95, and disk size.

10. `Add Qwen3 frontier embedding and reranker benchmark track`
    - add config-only candidates first.
    - do not make production default until holdout beats R2 and latency fits.

## Acceptance Gates

Production cutover can proceed when all are true:

- `indexer.is_ready(state/cs_rag)` returns `ready` for the v3 manifest.
- `integration.augment()` records `meta.backend == "lance"` after swap.
- cutover comparator gate passes: global primary nDCG macro improves, or no
  category/language bucket regresses by more than `-0.01`.
- offline Korean/English smoke returns at least three hits for:
  - `DB 격리수준`
  - `Spring Bean이 뭐야`
  - `What is dependency injection`
- rollback runbook is present and has been dry-read against current paths.

Context-aware track can proceed when all are true:

- no rewrite sidecar means exact old behavior,
- malformed rewrite sidecar is ignored,
- follow-up context never widens beyond last two `rag_ask` events,
- multi-turn holdout Korean bucket reaches `nDCG@10 >= 0.20`,
- P95 warm remains within the production budget chosen for the subscription
  coaching workflow.

## Official References Checked

- BGE-M3 model card: https://huggingface.co/BAAI/bge-m3
- BGE reranker v2 m3 model card: https://huggingface.co/BAAI/bge-reranker-v2-m3
- Qwen3 Embedding 0.6B model card: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
- Qwen3 Reranker 0.6B model card: https://huggingface.co/Qwen/Qwen3-Reranker-0.6B
- Jina v5 text-small model card: https://huggingface.co/jinaai/jina-embeddings-v5-text-small
- LanceDB hybrid search: https://docs.lancedb.com/search/hybrid-search
- LanceDB vector index tuning: https://docs.lancedb.com/indexing/vector-index
- LanceDB FTS: https://docs.lancedb.com/search/full-text-search
- kiwipiepy package/version: https://pypi.org/project/kiwipiepy/
- Anthropic Contextual Retrieval: https://www.anthropic.com/engineering/contextual-retrieval

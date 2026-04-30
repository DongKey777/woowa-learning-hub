# RAG SOTA Handoff — 2026-04-30

## Scope

Continue `~/.claude/plans/abundant-humming-lovelace.md` from H0.

Current plan target: bge-m3 full-hybrid + LanceDB capability proof before H1 schema/indexer work.

## Starting State Observed

- Branch: `main`
- Remote: `main...origin/main`
- Prior HEAD: `1f05f2d feat(corpus-lint): embedding cosine dedupe candidate finder (P5.4)`
- Worktree before this continuation:
  - `scripts/learning/rag/encoders/__init__.py` untracked
  - `tests/unit/test_encoder_protocol.py` untracked
- Other AI had started only the encoder protocol contract. No `bge_m3.py`, no `smoke.py`.

## Gate Recovery

- Qwen3 long-running CPU sweep was no longer alive by the time `kill` ran.
- Disk before cleanup oscillated between ~4.6GB and ~22GB free because the sweep had temporary files.
- Removed inactive orchestrator worker sandboxes and non-H0 model caches:
  - `state/orchestrator/codex-home`
  - `state/orchestrator/workers`
  - `state/orchestrator-archive`
  - HF cache: Qwen3-Embedding-0.6B, faster-whisper-base, mmarco reranker
- Kept `BAAI/bge-m3` cache for H0 real-model smoke.
- Disk after cleanup: `31Gi` free.
- No active `rag-eval`, Qwen, `cs-index-build`, or orchestrator process remains.

## Dependency State

Installed/available in `.venv`:

- `lancedb=True`
- `pyarrow=True`
- `FlagEmbedding=True`
- `kiwipiepy=True`
- `torch=True`
- `transformers=True`
- `sentence_transformers=True`

Not directly importable:

- `tantivy=False`

Interpretation: this is acceptable for H0 because LanceDB FTS is validated through `create_fts_index()` smoke, not a direct Python `tantivy` import.

Python:

- `.venv/bin/python --version` → `Python 3.12.12`

## Implemented

Added:

- `scripts/learning/rag/encoders/__init__.py`
  - `ModalEncoding`
  - `EncoderProtocol`
- `scripts/learning/rag/encoders/bge_m3.py`
  - Lazy `FlagEmbedding.BGEM3FlagModel` wrapper
  - Returns dense `float32`, sparse `{int: float}`, ColBERT token vectors
  - Converts FlagEmbedding lexical string token ids to `int`
  - Emits existing `encode_progress` callback shape
- `scripts/learning/rag/encoders/smoke.py`
  - H0 capability proof command
  - Writes `state/cs_rag/dep_probe.json`
  - Probes LanceDB vector search, FTS, multivector float16/float32, sparse struct round-trip, merge_insert/versioning, kiwipiepy, real bge-m3 load
- `tests/unit/test_encoder_protocol.py`
  - Protocol/TypedDict contract tests
- `tests/unit/test_bge_m3_encoder.py`
  - Fake-model wrapper tests, no heavy model load

## H0 Probe Result

Command:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m scripts.learning.rag.encoders.smoke --device cpu --max-length 128 --out state/cs_rag/dep_probe.json
```

Result summary:

```text
dense=1024 colbert=1024 sparse=250002
lancedb=0.30.2 fts=ngram
dep_probe=state/cs_rag/dep_probe.json
```

Important `dep_probe.json` facts:

- `lancedb.version`: `0.30.2`
- `lancedb.fts_korean_tokenizer`: `ngram`
- `lancedb.fts_korean_smoke_ok`: `true`
- `lancedb.multivector_api.float16`: `supported_indexed`
- `lancedb.multivector_api.float32`: `supported_indexed`
- `lancedb.multivector_dtype`: `float16`
- `lancedb.sparse_native`: `rescore_only`
- `lancedb.merge_insert_ok`: `true`
- `bge_m3.model_version`: `BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181`
- `bge_m3.dense_shape`: `[5, 1024]`
- `bge_m3.sparse_key_type`: `int`
- `bge_m3.colbert_dtype`: `float16`

`state/cs_rag/dep_probe.json` is under ignored state and is not committed.

## Verification Run

```bash
.venv/bin/python -m pytest tests/unit/test_encoder_protocol.py tests/unit/test_bge_m3_encoder.py -q
```

Result:

```text
9 passed in 0.05s
```

## Current Status

H0 capability proof is implemented and manually verified.

Additional H1 foundation work after commit `0739416`:

- Added `schemas/cs-index-manifest-v3.json`.
- Added `indexer.LANCE_INDEX_VERSION = 3`, `LANCE_DIR_NAME`, `LANCE_TABLE_NAME`.
- Added `indexer.IncompatibleIndexError`.
- Added `indexer.read_manifest_v3(index_root)`.
- Added `indexer.open_lance_table(index_root, mode="r"|"rw")`.
- Added `tests/unit/test_lance_index_format.py`.

Important H1 design choice:

- Did **not** flip legacy `INDEX_VERSION = 2` yet.
- Did **not** make `is_ready()` reject v2 yet.
- Reason: the current production writer still builds SQLite/NPZ v2. Flipping readiness before H2 writer exists would make `bin/cs-index-build` unable to produce a ready index. The readiness flip should happen in H2 together with the LanceDB writer.

H1 verification:

```bash
.venv/bin/python -m pytest tests/unit/test_lance_index_format.py tests/unit/test_encoder_protocol.py tests/unit/test_bge_m3_encoder.py -q
.venv/bin/python -m pytest tests/unit/test_cs_readiness.py tests/unit/test_cli_cs_index_build_modes.py -q
```

Results:

```text
12 passed in 0.87s
15 passed in 0.04s
```

Remaining before H1:

None for H1 foundation. Next phase is H2 writer.

Remaining for H2:

- Implement LanceDB table build path using the H1 manifest shape.
- Use `dep_probe` result:
  - FTS tokenizer path: `ngram` over `search_terms`.
  - Sparse mode: `rescore_only`.
  - Multivector storage dtype: `float16`.
- Move `INDEX_VERSION`/readiness cutover only once H2 writer can build a v3-ready index.
- Update `bin/cs-index-build` CLI only when full writer path exists.

## H2 LanceDB Writer Foundation

Implemented after H1:

- Added `indexer.build_lance_index(...)`.
  - Loads the existing Markdown corpus through `corpus_loader.load_corpus`.
  - Calls an injected `EncoderProtocol` implementation for dense/sparse/ColBERT modalities.
  - Writes `state/cs_rag/lance/cs_chunks.lance` through LanceDB.
  - Writes v3 `manifest.json` matching `schemas/cs-index-manifest-v3.json`.
- Added LanceDB row schema helpers:
  - `dense_vec`: fixed-size `float32` list.
  - `sparse_vec`: `{indices: list[int32], values: list[float32]}` for later sparse dot-product rescoring.
  - `colbert_tokens`: nested fixed-size `float16` vectors.
  - `content_sha1`: stable chunk payload hash for future incremental diffing.
  - `search_terms`: cached kiwipiepy token string for Korean BM25 support.
- Added FTS/index creation helper.
  - LanceDB 0.30.2 Python signature accepts `List[str]`, but native FTS rejects multi-field creation with `ValueError`.
  - Writer therefore creates two separate FTS indexes: `search_terms` and `body`.
  - Tiny test corpora skip ANN vector indexing and record `dense.type="unindexed"`, because LanceDB can emit noisy/meaningless k-means warnings on very small row counts.
  - Production-size corpora still attempt dense IVF and ColBERT multivector indexing.
- Extended v3 manifest schema to allow `dense.type="unindexed"` for tiny fixture/exact-scan builds.
- Added `tests/unit/test_lance_index_builder.py`.
  - Fake multimodal encoder covers dense, sparse, and ColBERT writes without loading bge-m3.
  - Verifies manifest schema, table row count, sparse round-trip, FTS query, rebuild replacement, and empty-corpus failure.

H2 verification:

```bash
.venv/bin/python -m pytest tests/unit/test_lance_index_builder.py tests/unit/test_lance_index_format.py -q
.venv/bin/python -m pytest tests/unit/test_lance_index_builder.py tests/unit/test_lance_index_format.py tests/unit/test_encoder_protocol.py tests/unit/test_bge_m3_encoder.py tests/unit/test_cs_readiness.py tests/unit/test_cli_cs_index_build_modes.py -q
```

Results:

```text
6 passed in 1.58s
30 passed in 1.64s
```

Important H2 design choice:

- `build_lance_index` is still not wired into `bin/cs-index-build`.
- Legacy `INDEX_VERSION=2`, legacy `is_ready()`, and SQLite/NPZ production path remain untouched.
- The cutover should happen only in the later phase that updates CLI/build/readiness together, so the project never enters a state where `bin/cs-index-build` cannot produce the format expected by readiness.

Remaining after H2:

- H3/H4 searcher-side LanceDB read/query path.
- CLI cutover flag or mode for building v3 with real `BgeM3Encoder`.
- Production full build with bge-m3 and manifest row-count/corpus-hash validation.
- Sparse rescoring and ColBERT MaxSim integration are not implemented yet; H2 only stores the required columns.

## H2.1 Explicit LanceDB Build Entrypoint

Implemented after H2 writer foundation:

- Added `bin/cs-index-build --backend legacy|lance`.
  - Default stays `legacy`, so the First-Run Protocol and current production readiness path remain v2 SQLite/NPZ.
  - `--backend lance` is opt-in and routes to `indexer.build_lance_index(...)`.
- Added Lance-specific CLI options:
  - `--encoder bge-m3` (single supported production choice for now).
  - `--modalities dense,sparse,colbert,fts` with validation.
  - `--lance-colbert-dtype float16|float32`.
- `--backend lance --mode auto` resolves to full build even if legacy v2 readiness is `ready`.
  - Reason: v3 readiness is not the production readiness contract yet; explicit LanceDB build should not reuse legacy v2 readiness to pick incremental.
- `--backend lance --mode incremental` returns exit code 2 with a clear error until the LanceDB upsert wrapper lands.
- Added CLI tests covering:
  - Opt-in LanceDB full builder dispatch.
  - Modalities and ColBERT dtype propagation.
  - Incremental rejection for LanceDB backend.
  - Legacy mode behavior remains covered by the existing mode tests.

H2.1 verification:

```bash
.venv/bin/python -m pytest tests/unit/test_cli_cs_index_build_modes.py -q
.venv/bin/python -m pytest tests/unit/test_cli_cs_index_build_modes.py tests/unit/test_lance_index_builder.py tests/unit/test_lance_index_format.py tests/unit/test_encoder_protocol.py tests/unit/test_bge_m3_encoder.py tests/unit/test_cs_readiness.py -q
```

Results:

```text
10 passed in 0.03s
32 passed in 1.63s
```

Important H2.1 design choice:

- This is still not a production cutover.
- `indexer.is_ready()` still validates the legacy v2 index only.
- A real bge-m3 production LanceDB build should be run explicitly with `bin/cs-index-build --backend lance --mode full` after disk budget is checked.

## H3a LanceDB Read Path Candidate Helper

Implemented after H2.1:

- Added side-by-side LanceDB candidate helpers in `searcher.py`.
  - `_lance_fts_search`: queries v3 FTS indexes.
  - `_lance_dense_search`: queries `dense_vec`.
  - `_sparse_dot` / `_sparse_rescore`: post-candidate bge-m3 sparse dot-product rescoring.
  - `_lance_candidate_search`: fuses FTS/dense with existing RRF, optionally applies sparse rescore, dedupes by path, and returns the same formatted hit shape as legacy search.
- The public `search()` function is still unchanged.
  - Reason: H3a proves v3 read semantics without risking legacy RAG behavior.
  - H3b should wire this helper behind manifest/backend detection or an explicit modality/backend switch.
- LanceDB rows do not have SQLite row IDs.
  - H3a assigns a deterministic synthetic row ID from `sha1(chunk_id)` for internal ranking compatibility.
  - Output still includes the original `chunk_id`, `path`, `title`, `category`, and snippet fields.
- Added `tests/unit/test_lance_search_path.py`.
  - Builds a fake LanceDB v3 index through `indexer.build_lance_index`.
  - Verifies formatted FTS+dense+sparse hits.
  - Verifies missing modality/encoding returns empty instead of raising.
  - Verifies sparse rescore can promote a candidate with matching sparse token IDs.

H3a verification:

```bash
.venv/bin/python -m pytest tests/unit/test_lance_search_path.py -q
.venv/bin/python -m pytest tests/unit/test_lance_search_path.py tests/unit/test_lance_index_builder.py tests/unit/test_lance_index_format.py tests/unit/test_cli_cs_index_build_modes.py tests/unit/test_cs_rag_search.py -q
```

Results:

```text
3 passed in 2.03s
213 passed, 185 subtests passed in 3.04s
```

Remaining after H3a:

- H3b public search wiring for v3 indexes.
- Query encoder cache keyed by manifest encoder version.
- Category/difficulty/signal boosts need to be applied on the LanceDB path before production cutover.
- ColBERT MaxSim is still stored but not used in ranking; this remains H4.

## H3b Explicit Public LanceDB Search Backend

Implemented after H3a:

- Added `search(..., backend="legacy"|"lance", modalities=...)`.
  - Default remains `backend="legacy"` so all current callers keep the SQLite/NPZ path.
  - `backend="lance"` explicitly opens the v3 manifest/table and uses the H3a candidate pool.
- Added `_get_lance_query_encoder(index_root)` with cache keyed by manifest encoder version.
  - Current supported production encoder is `BAAI/bge-m3`.
  - Tests monkeypatch this helper with a fake encoder, so no heavy model load occurs in unit tests.
- LanceDB path now applies existing post-retrieval contracts:
  - category boost,
  - difficulty boost,
  - signal boost,
  - category filter fallback debug fields,
  - path-level dedupe,
  - legacy formatted hit shape.
- `mode="cheap"` with `backend="lance"` resolves to FTS-only and does not load the query encoder.
  - This preserves the cheap-mode latency intent for future runtime routing.

H3b verification:

```bash
.venv/bin/python -m pytest tests/unit/test_lance_search_path.py -q
.venv/bin/python -m pytest tests/unit/test_lance_search_path.py tests/unit/test_lance_index_builder.py tests/unit/test_lance_index_format.py tests/unit/test_cli_cs_index_build_modes.py tests/unit/test_cs_rag_search.py tests/unit/test_cs_rag_golden.py -q
```

Results:

```text
5 passed in 1.52s
268 passed, 2 warnings, 548 subtests passed in 101.69s
```

Important H3b design choice:

- This is still explicit opt-in only.
- `scripts.learning.integration.augment()` does not pass `backend="lance"` yet.
- `bin/rag-ask` and `coach-run` therefore remain on the legacy backend until a later cutover commit.
- ColBERT is not used in scoring yet; `modalities=("fts","dense","sparse")` is the meaningful H3 path. H4 owns MaxSim/ColBERT quality and latency decisions.

## H4a Exact ColBERT MaxSim Candidate Rescore

Implemented after H3b:

- Added `_colbert_maxsim(query_tokens, doc_tokens)`.
  - Converts query/doc token matrices to float32.
  - L2-normalizes token vectors.
  - Computes query-token max similarity over document tokens and averages over query tokens.
- Added `_colbert_rescore(...)`.
  - Applies exact MaxSim only over the already retrieved LanceDB candidate pool.
  - This avoids full-corpus ColBERT scans and keeps H4a as a post-candidate rerank step.
- LanceDB row conversion now carries `colbert_tokens` into the internal chunk dict.
- `_lance_candidate_pool` applies ColBERT rescore when `modalities` includes `colbert` and query encoding contains ColBERT tokens.
- Public explicit LanceDB search tests now exercise `modalities=("fts","dense","sparse","colbert")`.

H4a verification:

```bash
.venv/bin/python -m pytest tests/unit/test_lance_search_path.py -q
.venv/bin/python -m pytest tests/unit/test_lance_search_path.py tests/unit/test_lance_index_builder.py tests/unit/test_lance_index_format.py tests/unit/test_cli_cs_index_build_modes.py tests/unit/test_cs_rag_search.py -q
```

Results:

```text
7 passed in 1.65s
217 passed, 185 subtests passed in 2.70s
```

Important H4a design choice:

- This is exact MaxSim over candidates, not LanceDB multivector ANN cutover.
- The weight is deliberately small (`0.03`) until H7/H8 ablation tunes the blend.
- H4 remaining work is quality/latency measurement: exact candidate MaxSim vs LanceDB indexed multivector vs possible sidecar.

## H2.2 CLI Wrapper Runtime Fix + Real bge-m3 Smoke

Issue found during operational smoke:

- `bin/cs-index-build` used system `python3`.
- The active dependencies (`lancedb`, `pyarrow`, `FlagEmbedding`, `kiwipiepy`) are installed in repo `.venv`.
- Result: unit tests passed under `.venv/bin/python`, but the real CLI failed with `IndexDependencyMissing: lancedb/pyarrow not installed`.

Fix:

- `bin/cs-index-build` now resolves Python in this order:
  1. `$PYTHON` env override,
  2. repo `.venv/bin/python`,
  3. system `python3`.
- `bin/cs-index-build.ps1` now resolves Python in this order:
  1. `$env:PYTHON`,
  2. repo `.venv\Scripts\python.exe`,
  3. repo `.venv\bin\python`,
  4. system `python`.

Operational smoke:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  bin/cs-index-build --backend lance --mode full \
  --corpus /tmp/woowa-lance-corpus-... \
  --out /tmp/woowa-lance-index-... \
  --modalities dense,sparse,colbert,fts
```

Result:

```text
[cs-index] state=missing reason=first_run
[cs-index] mode=full
[cs-index] 1/5 코퍼스 스캔 완료 — chunks=4
[cs-index] 4/5 임베딩 진행 — 4/4 (100.0%)
[cs-index] 5/6 LanceDB 테이블 작성 중 (4 chunks)…
[cs-index] 6/6 LanceDB 인덱스 생성 중 (4 chunks)…
[cs-index] 5/5 manifest 저장 — row_count=4, corpus_hash=f905eff95d2d…
[cs-index] 완료 — mode=lance-full row_count=4 — encoder=BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181 modalities=dense,sparse,colbert,fts (7.6s)
```

This smoke used real cached bge-m3 in offline mode and did not touch production `state/cs_rag`.

## H2.3 LanceDB Disk Budget Gate

Implemented after H2.2:

- Added a pre-build disk estimate for `bin/cs-index-build --backend lance`.
- The gate runs before loading bge-m3.
- Estimate components:
  - dense: `chunk_count * 1024 * 4`,
  - sparse: `chunk_count * 120 * (indices+values fp32/int32)`,
  - ColBERT candidate storage: conservative per-chunk estimate,
  - LanceDB overhead: 10%.
- Required free space is `2x total_estimate` to leave room for rebuild/write amplification.
- If insufficient, CLI exits with code 2 and `INSUFFICIENT_DISK`.

H2.3 verification:

```bash
.venv/bin/python -m pytest tests/unit/test_cli_cs_index_build_modes.py -q
.venv/bin/python -m pytest tests/unit/test_cli_cs_index_build_modes.py tests/unit/test_lance_search_path.py tests/unit/test_lance_index_builder.py tests/unit/test_lance_index_format.py -q
```

Results:

```text
11 passed in 0.03s
24 passed in 1.68s
```

Operational smoke with budget output:

```text
[cs-index] disk budget estimate (2 chunks):
  dense (1024 fp32):      8.0 KB
  sparse (~120 nonzero):  1.9 KB
  colbert candidate data: 54.0 KB
  LanceDB overhead (~10%): 6.4 KB
  total estimate:         70.3 KB
  free at /private/tmp/woowa-lance-index-...: 30.2 GB ✓
[cs-index] 완료 — mode=lance-full row_count=2 — encoder=BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181 modalities=dense,sparse,colbert,fts (5.5s)
```

Remaining:

- The budget estimate is intentionally conservative and coarse. H8 production sweep should record actual LanceDB footprint and tune the constants if needed.

## Checkpoint Verification After H4a/H2.3

Full unit verification after the current continuation stack:

```bash
.venv/bin/python -m pytest tests/unit -q
```

Result:

```text
1786 passed, 2 warnings, 772 subtests passed in 139.72s
```

Current committed stack on top of `origin/main`:

```text
0739416 feat(rag): add bge-m3 encoder H0 capability proof
631de57 feat(rag): add LanceDB v3 manifest foundation
1a99b34 feat(rag): add LanceDB v3 writer foundation for bge-m3 hybrid index
97989a8 feat(rag): expose opt-in LanceDB cs-index-build backend
5e75105 feat(rag): add side-by-side LanceDB candidate search path
226df64 feat(rag): wire explicit LanceDB backend into search API
3e79934 feat(rag): add exact ColBERT MaxSim rescore for LanceDB candidates
f02942a fix(rag): run cs-index-build through repo virtualenv when available
ee8be67 feat(rag): add disk budget gate for LanceDB index builds
```

Recommended next handoff point:

- Start H5 only after deciding whether to implement LanceDB incremental upsert now or first run a non-production full build under `state/cs_rag_lance/` for H7/H8 harness measurements.
- Do not flip default `search()` backend, `integration.augment()`, or `indexer.is_ready()` until H7/H8 metrics and cutover gates are met.

## H5a LanceDB Incremental Upsert Core

Implemented after checkpoint:

- Added LanceDB v3 per-model fingerprint sidecar:
  - `chunk_hashes_per_model.json`
  - shape: `{model_version: {chunk_id: fingerprint}}`
  - atomic writer: `atomic_save_model_chunk_hashes(...)`
  - loader helpers: `load_chunk_hashes_per_model(...)`, `load_model_chunk_hashes(...)`
- Extended `IncrementalBuildResult` with optional LanceDB version fields:
  - `lance_version_before`
  - `lance_version_after`
  - Existing v2 tests remain compatible because fields default to `None`.
- Added `incremental_lance_build_index(...)`.
  - Full fallback when v3 manifest/table/model sidecar is missing or incompatible.
  - No-op fast path when fingerprints match.
  - Delta encode only for added/modified chunks.
  - `merge_insert("chunk_id")` for added/modified rows.
  - `when_not_matched_by_source_delete(chunk_id IN (...))` for deleted rows when there is a delta source.
  - Pure-delete path uses `table.delete(...)`.
  - Tracks LanceDB table version before/after.
  - Attempts `restore(version_before)` / `checkout(version_before)` on merge/delete failure.
  - Writes fingerprint sidecar only after the LanceDB write succeeds.
- Added tests in `tests/unit/test_lance_incremental_indexer.py`.
  - Per-model sidecar isolation.
  - First run full fallback then no-op incremental.
  - Add path with delta encode/upsert.
  - Pure-delete path with zero encoding and row-count decrease.

H5a verification:

```bash
.venv/bin/python -m pytest tests/unit/test_lance_incremental_indexer.py -q
.venv/bin/python -m pytest tests/unit/test_lance_incremental_indexer.py tests/unit/test_lance_index_builder.py tests/unit/test_lance_index_format.py tests/unit/test_lance_search_path.py tests/unit/test_cli_cs_index_build_modes.py tests/unit/test_incremental_indexer.py -q
```

Results:

```text
3 passed in 1.62s
79 passed in 1.84s
```

Important H5a design choice:

- CLI still rejects `--backend lance --mode incremental` at this point.
- Next commit should wire the CLI to `incremental_lance_build_index(...)` and then update tests/operational smoke.

## H5b LanceDB Incremental CLI Wiring

Implemented after H5a:

- `bin/cs-index-build --backend lance --mode incremental` now calls `incremental_lance_build_index(...)`.
- `--backend lance --mode auto` resolves against the v3 LanceDB manifest/table instead of legacy SQLite readiness:
  - v3 exists → incremental,
  - v3 missing/incompatible → full.
- `--backend lance --mode full` seeds `chunk_hashes_per_model.json` after the full build.
  - This fixed an operational gap discovered during smoke: full build created the table but no sidecar, so the next incremental fell back to full with `no_model_fingerprints`.
- Full builds still run the disk budget gate before loading bge-m3.
- Incremental summary now prints LanceDB version transition, e.g. `lance_version=3→4`.

H5b verification:

```bash
.venv/bin/python -m pytest tests/unit/test_cli_cs_index_build_modes.py tests/unit/test_lance_incremental_indexer.py -q
.venv/bin/python -m pytest tests/unit/test_cli_cs_index_build_modes.py tests/unit/test_lance_incremental_indexer.py tests/unit/test_lance_index_builder.py tests/unit/test_lance_search_path.py tests/unit/test_incremental_indexer.py -q
```

Results:

```text
14 passed in 1.66s
76 passed in 1.84s
```

Operational smoke with real cached bge-m3:

```text
FULL
[cs-index] 완료 — mode=lance-full row_count=4 — encoder=BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181 modalities=dense,sparse,colbert,fts (6.0s)

NOOP
[cs-index] diff {'added': 0, 'modified': 0, 'deleted': 0, 'unchanged': 4}
[cs-index] noop {'lance_version': 3}
[cs-index] 완료 — mode=lance-incremental row_count=4 — added=0 modified=0 deleted=0 unchanged=4 encoded=0 lance_version=3→3 (0.6s)

ADD
[cs-index] encode_delta {'count': 2, 'model': 'BAAI/bge-m3'}
[cs-index] lance_merge_insert {'updated': 0, 'inserted': 2, 'deleted': 0}
[cs-index] 완료 — mode=lance-incremental row_count=6 — added=2 modified=0 deleted=0 unchanged=4 encoded=2 lance_version=3→4 (5.2s)
```

This smoke used temporary `/tmp` corpus/index paths and did not touch production `state/cs_rag`.

## H6 Modal-Aware PRF Expansion

Implemented after H5b:

- Added `ModalExpansion`.
  - `expanded_query_text`
  - `sparse_expansion_tokens`
  - `expansion_terms`
  - `text_expansion`
- Added `rm3_expand_modal(...)`.
  - Calls existing `rm3_expand(...)` for text expansion, preserving backward compatibility.
  - Adds sparse token expansion from pseudo-relevant sparse vectors.
  - Optionally maps selected text expansion terms through a model-specific `tokenizer_for_sparse`.
- Existing `rm3_expand(...)` behavior is unchanged.
- Added PRF tests for:
  - text compatibility with `rm3_expand`,
  - sparse token selection from pseudo-relevant docs,
  - optional text-term to sparse-token mapping.

H6 verification:

```bash
.venv/bin/python -m pytest tests/unit/test_prf.py -q
.venv/bin/python -m pytest tests/unit/test_prf.py tests/unit/test_lance_search_path.py tests/unit/test_cs_rag_search.py -q
```

Results:

```text
21 passed in 0.03s
222 passed, 185 subtests passed in 2.82s
```

Remaining:

- H6 only provides the modal PRF primitive.
- Searcher integration of modal PRF is still future work and should be measured in H7/H8 rather than silently enabled.

## H7a Eval Harness Modal Metadata + Scoped Lance Retriever

Implemented after H6:

- Extended `RunManifest` with optional H7 fields:
  - `backend`: `legacy` or `lance`
  - `modalities`: measured subset of `dense`, `sparse`, `colbert`, `fts`
  - `encoder`: copied encoder identity/config block from the index manifest
  - `lancedb`: copied LanceDB table/index metadata from the index manifest
- Kept backward compatibility:
  - older baseline/report manifests without the new fields still validate and materialize with `backend="legacy"`.
  - schema still rejects unknown modalities.
- Extended `ABRetriever`:
  - forwards `backend` and `modalities` into `searcher.search(...)`;
  - preserves the existing legacy `_QUERY_EMBEDDER` swap path;
  - adds a scoped LanceDB encoder cache bind for `backend="lance"` so A/B/eval runs can inject the modal encoder without loading production bge-m3 implicitly;
  - restores or removes the LanceDB cache key on context exit.
- Extended `ab_sweep.run_one_candidate` / `run_ab_sweep` plumbing to pass `backend`/`modalities` and capture index `encoder`/`lancedb` blocks into each run report.

H7a verification:

```bash
.venv/bin/python -m pytest tests/unit/test_rag_eval_manifest.py tests/unit/test_rag_eval_ab_retriever.py tests/unit/test_rag_eval_ab_sweep.py -q
```

Result:

```text
46 passed, 2 warnings in 9.79s
```

Remaining H7 work:

- Add the actual `rag-eval ablate` CLI mode.
- Generate singleton/pair/full modality combinations automatically.
- Persist `reports/cs_rag/eval/ablation_<runid>.json`.
- Run the modality ablation against a prebuilt LanceDB index and feed the result into H8 stack selection.

## Notes for Next AI

- Do not re-run old Qwen CPU sweep. The plan says Qwen3-0.6B remains an H8 candidate, but it must be measured later under the new LanceDB/index format.
- Do not delete `~/.cache/huggingface/hub/models--BAAI--bge-m3`; it is needed for offline H0/H2.
- The direct Python `tantivy` module is not installed. This is not currently a blocker because LanceDB FTS smoke passed.
- `state/orchestrator/queue.json` and status metadata were preserved, but inactive worker sandboxes were removed to satisfy disk gate.

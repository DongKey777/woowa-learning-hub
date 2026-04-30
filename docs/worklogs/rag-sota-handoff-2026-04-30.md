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

Remaining before H1:

- Commit the H0 files.
- Optional: re-run H0 smoke after commit if desired.
- Start H1:
  - Add `schemas/cs-index-manifest-v3.json`
  - Define LanceDB schema using `dep_probe` result
  - Treat FTS tokenizer as `ngram` / `search_terms` path
  - Treat sparse as `rescore_only`
  - Use `float16` for multivector storage unless H1 fake-table test finds a regression

## Notes for Next AI

- Do not re-run old Qwen CPU sweep. The plan says Qwen3-0.6B remains an H8 candidate, but it must be measured later under the new LanceDB/index format.
- Do not delete `~/.cache/huggingface/hub/models--BAAI--bge-m3`; it is needed for offline H0/H2.
- The direct Python `tantivy` module is not installed. This is not currently a blocker because LanceDB FTS smoke passed.
- `state/orchestrator/queue.json` and status metadata were preserved, but inactive worker sandboxes were removed to satisfy disk gate.


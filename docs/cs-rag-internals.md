# CS RAG Internals

How the CS learning subsystem indexes, retrieves, and guards freshness. Agent sessions do not need this file to answer a turn — `coach-run.json` already carries the compact results — but implementers and operators do.

## Subsystem Layout

- `scripts/learning/rag/corpus_loader.py` — walks `knowledge/cs/`, parses markdown into `{path, title, category, body, sections, anchors}` chunks (section-level primary, 400-token fallback)
- `scripts/learning/rag/indexer.py` — builds the production `state/cs_rag/` LanceDB v3 index (`manifest.json` + `lance/`) with BGE-M3 dense/sparse payloads and Tantivy FTS metadata. The legacy SQLite/NPZ v2 builder remains for rollback comparisons. `is_ready()` stays safe to call without importing ML dependencies.
- `scripts/learning/rag/searcher.py` — compatibility entrypoint. `backend=auto` still understands legacy/Lance manifests, while `integration.augment()` promotes the runtime to R3 when the index has a matching remote-built lexical sidecar.
- `scripts/learning/rag/r3/search.py` — production R3 retrieval fabric: query planning → lexical sidecar/body FTS prefetch → BGE-M3 dense candidates → BGE-M3 sparse first-stage sidecar → signal candidates → deterministic fusion → optional language-aware reranker.
- `scripts/learning/rag/reranker.py` — legacy Lance cross-encoder reranker (`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`). R3 targets `BAAI/bge-reranker-v2-m3` through `scripts/learning/rag/r3/rerankers/cross_encoder.py`; local policy `auto` skips reranking when the verified sidecar is loaded.
- `scripts/learning/rag/signal_rules.py` — rule-based query augmentation (persistence, api-boundary, network reliability, security, collections, etc.) driven by learner prompt tokens + learner-state topic hints.
- `scripts/learning/rag/category_mapping.py` — `learning_point → [CS categories]`. Tested for enum/key drift by `test_learning_point_id_consistency.py`.

## Readiness Contract

`cs_readiness` lives at top level in `coach-run.json` and is computed before `augment()`. Fields:

| field | value |
|---|---|
| `state` | `ready` \| `missing` \| `stale` |
| `corpus_hash` | sha of `knowledge/cs/` |
| `index_manifest_hash` | sha recorded by the last `bin/cs-index-build` |
| `next_command` | `bin/cs-index-build` when recovery is needed, else null |
| `reason` | `first_run` \| `corpus_changed` \| `index_corrupt` \| `deps_missing` \| `cs_only_requires_index` \| null |

**Invariant**: `cs_readiness.state != "ready"` never downgrades `execution_status`. `execution_status=blocked` is reserved for archive/bootstrap shortfalls.

Recovery (see `docs/agent-operating-contract.md` CS Readiness section):

- `intent_decision.detected_intent == "cs_only"` + not ready → 1st payload is **diagnostic only**. Run `bin/cs-index-build`, re-invoke `coach-run`, use the 2nd payload for the learner reply.
- `mission_only` → advisory; use the 1st payload.
- `mixed` / `drill_answer` → advisory; AI decides.

## Search Flow

1. `integration.resolve_search_backend()` chooses `r3` when `r3_lexical_sidecar.json` matches the manifest; stale or missing sidecars fall back to Lance.
2. R3 builds a language-aware query plan and route tags.
3. Metadata lexical sidecar, body prefetch, dense retrieval, sparse retrieval, and signal retrieval emit independent candidates.
4. Deterministic fusion records each candidate source in `r3_sources`.
5. Reranking is optional. Local default policy is `auto`: skip the cross-encoder when the verified sidecar is loaded; force it with `WOOWA_RAG_R3_RERANK_POLICY=always` for quality investigations.
6. Final top-K (default 5) is returned with `runtime_debug.r3_*` evidence.

## Return Shape

`augment(learner_state, prompt, learning_points, coach_profile, cs_search_mode)` returns:

```python
{
  "by_learning_point": {lp: [{path, title, category, section, score, snippet_preview}, ...], ...},
  "by_fallback_key":  {key: [...], ...},   # for cs_only no-LP turns
  "fallback_reason":  str | None,          # e.g. "cs_only_no_peer_learning_point", "partial_coverage"
  "cs_categories_hit": [...],
  "sidecar_path":     "contexts/cs-augmentation.json",
  "meta": {
    "latency_ms":   int,
    "rag_ready":    bool,
    "reason":       str | None,
    "mode_used":    "skip" | "cheap" | "full",
  },
}
```

Top-level `coach-run.json.cs_augmentation` is a compact view for AI consumption. `contexts/cs-augmentation.json` is a rewritten-each-turn sidecar that currently mirrors the same compact hit shape (path / section / score / snippet_preview) — raw document bodies, full section text, and reranker raw scores are planned to land here once `integration.augment` grows that bundling step. Treat the sidecar as an advisory artifact for now; AI sessions should read `cs_augmentation` from `coach-run.json` as canonical.

## Search Modes

Decided by `intent_router.pre_decide()` before augment:

| mode | path | when |
|---|---|---|
| `skip` | return empty immediately | `pre_intent == "mission_only"` |
| `cheap` | FTS only, no reranker | `pre_intent == "drill_answer"` |
| `full` | FTS + dense + RRF + reranker | `pre_intent ∈ {"cs_only", "mixed"}` |

`skip` is the big latency win — mission-only turns never pay for CS search.

## Lazy Import Discipline

- `coach_run.py` imports `scripts.learning.*` **inside functions**, never at module top. `scripts.learning.integration.augment` is imported inside `_pre_augment_phase`.
- `indexer.is_ready()` touches only filesystem + manifest; no ML deps.
- `searcher` / `reranker` import FlagEmbedding / sentence-transformers / LanceDB / numpy lazily inside their entry functions.
- `test_coach_run_import_isolation.py` pins this — blocks `sentence_transformers` / `torch` / `numpy` / `sklearn` / `searcher` / `reranker` / `integration` in `sys.modules` and verifies `coach_run` still imports.

Before any lazy import, `coach_run._pre_augment_phase` runs a lightweight dependency probe. If the ML/index stack is absent, `cs_readiness` is degraded uniformly — on every turn, including `mission_only`/`skip` — to `{state: "missing", reason: "deps_missing", next_command: "pip install -e ."}`, with `cs_augmentation=null`, `execution_status=ready`, and a peer-only reply. The exact `next_command` string is `pip install -e .` — AI sessions should run that verbatim from the repo root. A defensive `ImportError` catch around the actual `cs_augment(...)` call degrades the same way if `find_spec` succeeds but an internal import still fails.

## Rebuild Triggers

`bin/cs-index-build` rebuilds `state/cs_rag/*` as LanceDB v3 by default. Trigger when:

- `cs_readiness.state == "missing"` (first run, `reason: first_run`)
- `cs_readiness.state == "stale"` (corpus hash changed; `reason: corpus_changed`)
- index files corrupt or unreadable (`reason: index_corrupt`)
- after `pip install -e .` completes the first ML dependency install

Use `bin/cs-index-build --backend legacy --mode full` only for rollback
verification or archived v2 comparison.

First-run protocol (driven by the AI session, not the learner) is in `docs/agent-operating-contract.md`.

## Related

- [learning-flow.md](learning-flow.md) — end-to-end turn walkthrough including the CS path
- [artifact-catalog.md](artifact-catalog.md) — `cs_readiness`, `cs_augmentation`, `cs_block`, `contexts/cs-augmentation.json` entries
- [architecture.md](architecture.md) — pipeline order

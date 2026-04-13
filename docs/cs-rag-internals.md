# CS RAG Internals

How the CS learning subsystem indexes, retrieves, and guards freshness. Agent sessions do not need this file to answer a turn — `coach-run.json` already carries the compact results — but implementers and operators do.

## Subsystem Layout

- `scripts/learning/rag/corpus_loader.py` — walks `knowledge/cs/`, parses markdown into `{path, title, category, body, sections, anchors}` chunks (section-level primary, 400-token fallback)
- `scripts/learning/rag/indexer.py` — builds `state/cs_rag/index.sqlite3` (FTS5) + `state/cs_rag/dense.npz` (384-dim MiniLM embeddings) + `state/cs_rag/manifest.json` (corpus hash). Exposes `is_ready()` without importing any ML dependency.
- `scripts/learning/rag/searcher.py` — hybrid search: FTS top-N + dense top-N → RRF fusion (k=60) → optional reranker → category boost → final top-K. Lazy ML imports.
- `scripts/learning/rag/reranker.py` — cross-encoder reranker (`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`). Disabled by `WOOWA_RAG_NO_RERANK=1`. Lazy import.
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

1. `signal_rules.augment_query(prompt, learner_state_topics)` → augmented query tokens
2. FTS5 match over `docs(title, body)` → top 40
3. Dense cosine over query embedding vs `dense.npz` → top 40
4. RRF fusion (k=60) → top 20
5. Optional reranker → top 10
6. Category boost for learning-point ↔ category matches from `category_mapping.py`
7. Final top-K (default 5)

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
- `searcher` / `reranker` import sentence-transformers + numpy + sklearn lazily inside their entry functions.
- `test_coach_run_import_isolation.py` pins this — blocks `sentence_transformers` / `torch` / `numpy` / `sklearn` / `searcher` / `reranker` / `integration` in `sys.modules` and verifies `coach_run` still imports.

Before any lazy import, `coach_run._pre_augment_phase` runs a lightweight `importlib.util.find_spec` probe against `sentence_transformers`, `numpy`, and `sklearn`. If any is absent, `cs_readiness` is degraded uniformly — on every turn, including `mission_only`/`skip` — to `{state: "missing", reason: "deps_missing", next_command: "pip install -e ."}`, with `cs_augmentation=null`, `execution_status=ready`, and a peer-only reply. The exact `next_command` string is `pip install -e .` — AI sessions should run that verbatim from the repo root. A defensive `ImportError` catch around the actual `cs_augment(...)` call degrades the same way if `find_spec` succeeds but an internal import still fails.

## Rebuild Triggers

`bin/cs-index-build` rebuilds `state/cs_rag/*`. Trigger when:

- `cs_readiness.state == "missing"` (first run, `reason: first_run`)
- `cs_readiness.state == "stale"` (corpus hash changed; `reason: corpus_changed`)
- index files corrupt or unreadable (`reason: index_corrupt`)
- after `pip install -e .` completes the first ML dependency install

First-run protocol (driven by the AI session, not the learner) is in `docs/agent-operating-contract.md`.

## Related

- [learning-flow.md](learning-flow.md) — end-to-end turn walkthrough including the CS path
- [artifact-catalog.md](artifact-catalog.md) — `cs_readiness`, `cs_augmentation`, `cs_block`, `contexts/cs-augmentation.json` entries
- [architecture.md](architecture.md) — pipeline order

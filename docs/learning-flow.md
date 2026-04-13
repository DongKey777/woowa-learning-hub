# Learning Flow — One Turn End-to-End

How a single learner question flows through `bin/coach-run`, from prompt arrival to persisted artifacts. For module responsibilities see [architecture.md](architecture.md); for CS specifics see [cs-rag-internals.md](cs-rag-internals.md).

## Pipeline (single Python process)

```
learner prompt (Korean, via AI session)
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ 1. repo intake + archive sync (unchanged from coach)    │
│ 2. learner_state.assess → contexts/learner-state.json   │
│ 3. session.start → focus + candidate_interpretation     │
└─────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ PRE-AUGMENT PHASE (coach_run._pre_augment_phase)        │
│                                                         │
│ a. drill.load_pending → decrement_ttl                   │
│ b. intent_router.pre_decide(prompt, history,            │
│       pending_drill, learner_state)                     │
│       → {pre_intent, cs_search_mode}                    │
│ c. cs_readiness check (filesystem + manifest only)      │
│ d. learning.integration.augment(..., cs_search_mode)    │
│       → compact cs_augmentation + sidecar               │
│ e. if pending drill + prompt is answer:                 │
│       drill.route_answer → scoring.score_pending_answer │
│       → drill_result                                    │
└─────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ 9. memory.compute_memory_update                         │
│    (consumes augment result + drill_result — runs      │
│     AFTER augment so cs_view / drill_history flow in)   │
└─────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ 10. profile_merge.unify(coach_profile, drill_history)   │
│     → unified_profile {coach_view, cs_view, reconciled} │
│ 11. drill.build_offer_if_due(unified_profile,           │
│          pre_intent, pending)                           │
│     → drill_offer or None                               │
│     (refuses on drill_answer turn — no stacking)        │
│ 12. intent_router.finalize(pre_intent, augment_result,  │
│          drill_offer, drill_result)                     │
│     → intent_decision {detected_intent, block_plan}     │
└─────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ 13. response_contract.build(snapshot, augment_result,   │
│          intent_decision, drill_offer, drill_result)    │
│     → snapshot_block / verification /                   │
│       cs_block / drill_block / drill_result_block       │
│     (each with applicability_hint ∈ {primary,           │
│      supporting, omit} — advisory, not enforced)        │
│ 14. artifact_budget.enforce_budget(payload)             │
│     → fixed shrink ladder if > 182KB                    │
└─────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ 15. Phase 2 writes (sequential, failure → error):       │
│     history.jsonl → coach-run.json → cs-augmentation    │
│     sidecar → summary.json → profile.json → drill       │
│     persistence (append history, clear consumed         │
│     pending, save new offer OR re-save decremented)     │
└─────────────────────────────────────────────────────────┘
  │
  ▼
AI session reads coach-run.json (+ learner-state.json)
and composes the Korean reply
```

## Intent-Specific Paths

The same code runs for every turn, but `cs_search_mode` and `block_plan` shape what actually happens and what the AI renders.

### `mission_only` — PR review triage

- Triggered by mission file / PR / branch keywords + no CS tokens
- `cs_search_mode = "skip"` → augment returns immediately, no search, no latency cost
- `cs_readiness != ready` is ignored (advisory only)
- `block_plan`: `snapshot_block=primary`, `verification=primary`, `cs_block=omit`, `drill_block=omit`
- Reply shape is pure peer coaching (inherited from `woowa-mission-coach`): snapshot + verification + dual-axis narrative

### `cs_only` — pure theory question

- Triggered by CS concepts with no mission keywords
- `cs_search_mode = "full"` → FTS + dense + RRF + reranker
- `cs_readiness != ready` → 1st payload is diagnostic only. AI must run `bin/cs-index-build`, re-invoke `coach-run`, use 2nd payload for the learner reply.
- If the peer path yields no `learning_points`, augment falls back to `by_fallback_key` with `fallback_reason="cs_only_no_peer_learning_point"`
- `block_plan`: `cs_block=primary`, `snapshot_block=omit`, `verification=omit`, `drill_block=supporting`
- Reply leads with `## 이번 질문의 CS 근거`

### `mixed` — "my PR looks like X, why did reviewer flag it?"

- CS tokens + mission keywords both present
- `cs_search_mode = "full"`
- `cs_readiness != ready` is advisory
- `block_plan`: all blocks `primary` or `supporting`. `cs_block` and `snapshot_block` both render; narrative weaves peer evidence with CS theory.
- `drill_block` may appear as `supporting` if `reconciled.priority_focus` has content

### `drill_answer` — learner is answering a pending drill

- Gated by `drill-pending.json` TTL + 4-condition heuristic (length≥20, no trailing `?`, no question words, token overlap ≥ 0.2; 3 of 4 required)
- `cs_search_mode = "cheap"` — FTS only, no reranker (low latency for graded feedback)
- `drill.score_pending_answer` runs, producing `drill_result`
- `drill.build_offer_if_due` **refuses** to generate a new offer this turn (no stacking)
- `block_plan`: `drill_result_block=primary`, other blocks supporting; AI acknowledges the grade briefly then re-centers on the learner's next question

## Failure Modes and Degradation

| failure | signal | execution_status | reply path |
|---|---|---|---|
| ML deps missing | `cs_readiness={state:missing, reason:deps_missing}` | `ready` | peer-only, no cs_block |
| CS index missing (first run) | `cs_readiness={state:missing, reason:first_run}` | `ready` | mission_only: proceed. cs_only: AI rebuilds then retries. |
| Corpus changed | `cs_readiness={state:stale, reason:corpus_changed}` | `ready` | same as missing |
| Archive bootstrap incomplete | (unchanged) | `blocked` | no coaching; AI explains bootstrap need |
| Canonical write fails | (unchanged) | `error` + `canonical_write_failed=true` | read `coach-run.error.json` |

The `blocked` lane remains exclusive to archive/bootstrap shortfalls. CS-side degradation never downgrades `execution_status` — this separation lets peer-only coaching keep working when the CS index isn't ready.

## Source of Truth Invariants

- `memory/profile.json` = persisted truth. `coach-run.json.unified_profile` = per-turn derived projection. Never write back.
- `cs_augmentation` = source of truth. `response_contract.cs_block` = rendered view. On drift, trust `cs_augmentation` and re-render.
- `memory/drill-history.jsonl` = append-only authoritative drill record. `profile.json.cs_view` / `unified_profile.cs_view` are derivations.

## Related

- [architecture.md](architecture.md) — module layout + pipeline order
- [cs-rag-internals.md](cs-rag-internals.md) — RAG indexer/searcher/reranker internals + readiness contract
- [artifact-catalog.md](artifact-catalog.md) — per-artifact field reference
- [agent-operating-contract.md](agent-operating-contract.md) — AI session rules (CS recovery + drill UX)

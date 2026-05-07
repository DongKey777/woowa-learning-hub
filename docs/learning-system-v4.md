# Learning System v4-MVP

## Status

- Released as `woowa-learning-hub` `0.2.0`.
- Merged to `main` through PR #1 on 2026-05-07.
- Release tag: `learning-system-v4-mvp-v0.2.0`.
- Rollback tag before merge: `before-learning-system-v4-2026-05-07`.

The code path is implemented and verified on `main`. Existing runtime state was
backed up to `state/backups/pre-v4-state-migration-20260507T111922Z.tgz` before
learner-memory migration.

## Data Migration

The v4 migration is file/event based. It does not require a SQLite PR archive
schema migration.

- `bin/learner-profile migrate-from-repos` folds legacy per-repo memory into
  `state/learner/history.jsonl`.
- `bin/learner-profile recompute` rebuilds `state/learner/profile.json`.
- The migration is idempotent: a repeated run skips duplicate migrated events.
- Verified local profile after migration: `schema_version=v3`, `total_events=1529`.

`state/` remains gitignored. These files are learner-local runtime data, not
repository source.

## Runtime Guarantees

`bin/coach-run` now loads cross-learner context and emits a richer payload:

- `learner_context` carries the per-turn learner projection.
- `cognitive_trigger` selects at most one learner-facing prompt:
  `self_assessment`, `review_drill`, `follow_up`, or `none`.
- `response_contract.cognitive_block` renders that selected trigger.
- `response_contract.follow_up_block` is suppressed when `cognitive_block`
  surfaces a trigger, so the learner does not see duplicate follow-up prompts.
- `response_contract.cs_block.grounding_check` validates that rendered CS
  sources are backed by `cs_augmentation.verifier_hits` or
  `cs_augmentation.citation_paths`.

The cognitive selector is side-effect free. Persistence happens only after the
canonical `coach-run.json` write succeeds.

## Cognitive Triggers

Priority order is:

1. `self_assessment_due`
2. `review_due`
3. `follow_up`

Only one trigger is surfaced per turn. A pending drill answer or an in-turn
drill answer blocks other cognitive triggers for that turn.

### Self Assessment

Self-assessment is due when the learner has a recent code attempt in
`profile.recent_code_changes_24h` and no recent self-assessment for the same
concept.

When surfaced, `coach-run` stores a pending trigger in
`state/learner/pending_triggers.json` after the canonical write succeeds. If the
learner answers that prompt, the AI session must run:

```bash
bin/learn-self-assess --silent --trigger-session-id <id> "<learner response>"
```

Random scores such as "8점" are ignored unless there is a matching pending
`self_assessment` trigger. Self-assessment updates calibration only; it must not
inflate mastery.

### Review Drill

Spaced repetition uses existing drill artifacts, not a new pending-trigger
store.

- Completed drills append `due_at`, `review_of_session_id`, `review_count`, and
  `last_outcome` to `memory/drill-history.jsonl`.
- Due reviews create a normal `memory/drill-pending.json` offer through
  `drill.build_review_offer_if_due`.
- Default spacing bands are configured by `WOOWA_SPACED_REPETITION_BANDS` and
  default to the runtime bands in `scripts/learning/drill.py`.

## Citation Grounding

`cs_augmentation` is the source of truth. `response_contract.cs_block` is only a
rendered view.

Every `cs_block.sources[].path` must appear in:

```text
cs_augmentation.verifier_hits[].path union cs_augmentation.citation_paths
```

If the invariant fails, `grounding_check.severity` is `warn`. The AI should
surface the warning naturally and avoid overstating the ungrounded source, but
it does not block the whole response.

## Reformulated Query Persistence

When an AI session supplies `--reformulated-query`, the value is persisted on
`rag_ask` and `coach_run` learner events. This preserves the corpus-friendly
query used for retrieval without changing the learner-facing wording. The
interactive router also receives this reformulation for domain/depth/definition
detection, while raw prompt overrides and tool-only guards remain raw-only.

## Runtime Hardening Notes

`bin/rag-ask` defaults to the daemon path. The daemon records a startup
`runtime_fingerprint` in state and health responses; wrapper ensure compares it
with the current checkout and restarts stale processes automatically. The
documented `WOOWA_RAG_NO_DAEMON=1` path remains the direct debug/CI fallback.

Learner personalization is query-scoped at response-hint level:
`next_recommendation` can remain visible in context, but
`must_offer_next_action` is emitted only when the current prompt concept
overlaps the recommendation. R3 concept matching reads both top-level
`concept_id` and nested retriever `document.concept_id`.

## AI Session Rules

- Read `actions/coach-run.json` first.
- Copy `response_contract.snapshot_block.markdown` as required by
  `docs/agent-operating-contract.md`.
- Include `response_contract.cognitive_block.markdown` whenever
  `applicability_hint != "omit"`.
- Do not also surface `follow_up_block` when `cognitive_block` has selected
  `follow_up`, `self_assessment`, or `review_drill`.
- Run `bin/learn-self-assess` automatically for matching pending
  self-assessment answers.
- Surface `response_contract.cs_block.grounding_check.severity == "warn"` as a
  source-grounding caveat.
- Keep mission repositories read-only unless the learner explicitly asks for
  code changes.

## Validation

Primary regression coverage:

- `tests/unit/test_cognitive_trigger.py`
- `tests/unit/test_learn_self_assess_cli.py`
- `tests/unit/test_citation_invariants.py`
- `tests/unit/test_coach_run_pipeline.py`
- `tests/unit/test_learner_memory.py`
- `tests/unit/test_response_contract.py`

Operational checks after the v4 merge:

- full local unit suite passed
- GitHub Actions PR check passed
- `validate-state` passed for the onboarded mission repositories
- learner profile and event stream schemas validated after migration

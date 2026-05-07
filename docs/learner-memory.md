# Learner Memory (state/learner)

Single-source-of-truth memory for the learner across **all** activities —
RAG questions, PR coaching, drill answers, JUnit test results, and code
edits. The earlier per-repo memory (`state/repos/<repo>/memory/`) lives on
for backwards compatibility but the learner is no longer modeled per-repo.

The learner profile is purely **derived**: every recommendation, mastery
verdict, and tier promotion can be re-built by replaying
`history.jsonl`. There is no data in the profile that is not also present
(directly or by aggregation) in the event stream.

## Layout

```
state/learner/
├── history.jsonl     # append-only event stream (6 event_types)
├── profile.json      # derived view (concepts, activity, recommendations)
├── summary.json      # cumulative counts (derived)
├── pending_triggers.json # optional cognitive trigger state
└── identity.json     # cached learner_id (one-time)
```

`state/` is git-ignored. Nothing under `state/learner/` is ever pushed.

`pending_triggers.json` is optional. It currently stores only learner-level
self-assessment prompts that need a later response match. Drill answers and
review drills continue to use per-repo `memory/drill-pending.json`.

## Event types

Every line in `history.jsonl` is one JSON object with a discriminator
`event_type` ∈ `{rag_ask, coach_run, drill_answer, test_result,
code_attempt, self_assessment}`. Common fields: `event_type`, `event_id`, `ts`,
`learner_id`, `concept_ids`, `repo_context`, `module_context`. Per-type
required fields are enforced by
`learner_memory.validate_learner_event()` — see the `EVENT_REQUIRED_FIELDS`
dict in `scripts/workbench/core/learner_memory.py`.

### `rag_ask`

Recorded for **every** Tier 0 / 1 / 2 / 3 (including blocked) outcome of
`bin/rag-ask`. Captures `tier`, `rag_mode`, the inferred experience
level, the matched CS categories, the top retrieved doc paths, and
whether the request was blocked (Tier 3 missing PR/repo).

When the AI session supplies `--reformulated-query`, the redacted value is
stored as optional `reformulated_query`.

### `coach_run`

Recorded after a successful canonical write of
`actions/coach-run.json`. Captures `pr_number`, the
`primary_learning_points`, a digest of
`learning_point_recommendations`, and a derived
`had_negative_feedback` flag (used to block mastery).

When `coach-run` receives a reformulated query, the event stores optional
`reformulated_query` so retrieval context can be audited later.

### `drill_answer`

Recorded by the drill scoring engine after a 4-dimension drill is
graded. Captures `drill_session_id`, `total_score`, dimensions, and weak
tags. Drives the mastery rule (≥8 score × 2 ⇒ candidate for mastery).

### `test_result`

One event per `<testcase>` in JUnit XML output. Captures pass/fail,
duration, redacted failure message, and a 5-line redacted stack
excerpt. Provides the empirical "did it run green?" signal that
question-only history cannot.

### `code_attempt`

Recorded when the AI session helps the learner write or modify code.
Captures the file path, a redacted summary of the diff (≤500 chars),
and lines added/removed.

### `self_assessment`

Recorded only after a matching pending `self_assessment` cognitive trigger.
Captures `score` (1-10), `free_text`, `confidence_band`,
`trigger_session_id`, `source_event_id`, and the related `concept_ids`.

Self-assessment is a calibration signal. It contributes to
`profile.calibration_status`, but it does **not** count as drill mastery and
must not inflate `concepts.mastered`.

## Profile (`profile.json`)

Schema `v3`. Top-level fields:

* `experience_level` — rolling-20 inference (`current`, `confidence`,
  evidence list).
* `concepts` — `{mastered, uncertain, underexplored, encountered_count}`.
  Concepts are referenced by canonical `concept_id` from the catalog.
* `activity` — streak, modules_progress, tier_distribution, current
  module/stage.
* `next_recommendations` — populated in Phase 4 (`bin/learner-profile
  suggest`).
* `preferences` — explicit overrides set via `bin/learner-profile set`.
* `recent_code_changes_24h` — compact recent code-attempt signals used to
  decide whether self-assessment is due.
* `calibration_status` — recent self-assessments plus calibrated /
  miscalibrated concept summaries. Calibration is advisory and separate from
  mastery.

Profile is rebuilt lazily: if `history.jsonl` is newer than
`profile.json`, the next read triggers a recompute.

## Concept catalog

`knowledge/cs/concept-catalog.json` is the canonical mapping of surface
forms ("Bean", "Spring Bean", "@Component bean", "스프링 빈") to a single
`concept_id` like `concept:spring/bean`. Catalog is committed; runtime
extraction is deterministic alias matching only — no ML at call time.

Stages (`spring-core`, `spring-mvc`, `spring-jdbc`, `spring-data-jpa`,
`spring-http-client`, `spring-auth`) order the curriculum and let the
profile compute "current stage" + "underexplored stage gap".

To add concepts or aliases, edit the JSON directly or drop a
`knowledge/cs/concept-catalog.overrides.json` file (auto-merged at
load). Run `python3 scripts/learning/build_concept_catalog.py` to
re-canonicalize the alias ordering.

## CLI surface (Phase 1)

| Command | Purpose |
|---|---|
| `bin/learner-profile show` | dump `profile.json` (skeleton if no events) |
| `bin/learner-profile recompute` | force history → profile rebuild |
| `bin/learner-profile clear --yes` | wipe `state/learner/` (privacy reset) |
| `bin/learner-profile redact <substring>` | drop history entries containing `<substring>`, then recompute |
| `bin/learner-profile set --experience-level <lvl>` | explicit preferences override |
| `bin/learner-profile migrate-from-repos` | (Phase 2) merge per-repo `memory/` history |
| `bin/learner-profile suggest` | (Phase 4) next-step recommendations |
| `bin/learn-self-assess --silent --trigger-session-id <id> "<response>"` | append a `self_assessment` event for a pending cognitive trigger |

## Privacy

Every event is redacted on append:

* Emails (`foo@bar`) → `***REDACTED***`
* Common API tokens (`sk-…`, `ghp_…`, `Bearer …`) → `***REDACTED***`
* Password / api_key assignments → value redacted
* Stack traces capped at 5 lines / ≤1 KB
* Diff summaries capped at 500 characters

`bin/learner-profile redact <substring>` removes any history entry whose
JSON serialization contains the literal substring. The profile is
re-derived after the prune, so personalization never relies on data the
learner has explicitly removed.

## Testing

* `tests/unit/test_concept_catalog.py` — alias matching, module/stage
  inference, cross-mapping (21 tests).
* `tests/unit/test_learner_memory.py` — append/validation, builders,
  privacy redaction, recompute aggregation, mastery/uncertainty rules,
  self-assessment calibration, streak, deterministic event_id.

Both suites use disk-isolated temp directories, so they never pollute
`state/learner/` on the developer machine.

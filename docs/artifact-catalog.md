# Artifact Catalog

## Purpose

This document explains the meaning of the main artifacts under `state/repos/<repo>/...`.

Prefer these artifacts over reconstructing state from code or raw command output.

## Archive Layer

### `archive/prs.sqlite3`

Role:

- source database for collected PRs, reviews, comments, files

Use when:

- generating packets
- recomputing focus ranking
- debugging relevance retrieval

### `archive/status.json`

Role:

- bootstrap and data-confidence state of the repo's PR archive
- consulted before every `coach-run` so the agent knows whether data is sufficient

Contains:

- `bootstrap_state`: `uninitialized` | `bootstrapping` | `ready`
- `data_confidence`: `bootstrap` | `partial` | `ready`
- `reasons`: why the state was chosen
- `signals`: total_prs, total_reviews, total_review_comments, prs_with_review_activity
- `thresholds`: current ready thresholds
- `latest_run`: last collection_runs row
- `sync_status`: freshness check
- `computed_at`

Use when:

- deciding whether to call `coach-run` directly, prompt the learner to bootstrap first, or warn about partial data
- explaining answer confidence to the learner

## Analysis Layer

### `analysis/mission-map.json`

Role:

- compact map of the learner mission repo itself
- source of truth for mission-specific structure, likely review topics, retrieval terms, and path hints

Contains:

- mission hints from repo/upstream/branch/title
- build tool and language fingerprint
- README summary and requirement hints
- codebase layer paths and dependency signals
- likely review topics
- retrieval terms and retrieval path hints

Use when:

- the repo is newly onboarded
- the question has weak topic cues
- you want to understand the mission before opening larger PR packets

## Packet Layer

### `packets/topic-*.json`

Role:

- topic-centered cross-PR evidence

Contains:

- related PRs
- top reviewers
- hotspot paths
- `mentor_comment_samples` (mentor_original + mentor_followup)
- `crew_response_samples` (learner replies, reference only)
- `crew_original_samples` (learner self-comments, reference only)
- `representative_comments` (backward-compatible flattened view, mentor-first)
- `thread_samples` (reconstructed review threads with role_sequence)
- representative patches
- structured evidence summary

See [evidence-roles.md](../docs/evidence-roles.md) for role definitions and bucket semantics.

### `packets/reviewer-*.json`

Role:

- reviewer-centered repeated criteria and hotspot paths

Contains:

- reviewer summary
- related PRs
- hotspot paths
- representative comments
- structured evidence summary

### `packets/compare-*.json`

Role:

- direct PR-to-PR comparison evidence

Contains:

- PR summary
- review density
- path overlap
- representative comments

### `packets/pr-<number>-report.json`

Role:

- current learner PR report

Contains:

- PR metadata
- review bodies (filtered by reviewer_role, bots excluded)
- inline review comments split into `mentor_comment_samples` and `crew_response_samples`
- `thread_samples` for reconstructed review threads
- structured overview / hotspot summary

## Context Layer

### `contexts/learner-state.json`

Role:

- direct-observation snapshot of the learner's mission repository captured before `coach-run`
- authoritative for learner-side facts (branches, working copy, open PRs, pending reviewer threads, target PR selection)
- `coach-run` output supplements this with peer evidence but does not replace it

Contains:

- `head_branch`, `head_sha` (re-scan cache key)
- `fetch_state`: `fresh` | `stale`
- `working_copy`: clean / ahead / behind / uncommitted / untracked
- `prs`: open + recently closed PRs with `cycle_hint` (derived, informational)
- `target_pr_number` and `target_pr_selection_reason` (deterministic selection rule)
- `target_pr_detail.threads`: `{id, path, line, author, role, resolved, classification}` where `resolved ∈ {true, false, "unknown"}` (GraphQL fallback) and `classification ∈ {still-applies, already-fixed, ambiguous, unread}`
- `diff.base_ref`, `diff.head_ref`: fully resolved refs for reproducibility
- `coverage`: `full` | `partial` with a `skipped` list when budget caps were hit

Use when:

- starting any coaching turn — on follow-up turns, read this before re-running the assessment scan
- verifying that a reviewer comment still applies to the current code
- deciding whether to re-run the assessment (cache keys: `head_sha`, `target_pr` head SHA, `computed_at`)

Do not:

- use `cycle_hint` as an identifier — the learner's work is identified by `(branch, PR number)`, not by cycle label
- treat `resolved: "unknown"` as resolved — surface it to the learner as pending

See [agent-operating-contract.md](../docs/agent-operating-contract.md) **First-Run Protocol step 6** for how this artifact is produced.

### `contexts/my-pr-context.json`

Role:

- learner PR-centered context without an explicit free-form prompt

### `contexts/coach-context.json`

Role:

- free-form question-centered coaching context

Contains:

- prompt
- inferred topic
- inferred intent
- packet paths
- reviewer candidates
- recommended next actions

### `contexts/coach-focus.json`

Role:

- same-stage peer PR shortlist for the current question

Contains:

- current prompt
- local path signature
- candidate PR shortlist
- review/comment/path-based proximity evidence

### `contexts/coach-candidate-interpretation.json`

Role:

- reinterpret shortlisted peer PRs by learning point

Contains:

- candidate profiles
- learning-point recommendations
- primary candidate and alternatives for each learning point
- grounded evidence quotes
- `why_this_learning_point`

## Action Layer

### `actions/coach.json`

Role:

- prioritized next actions for the current coaching session

Contains:

- action title
- why
- structured action object

### `actions/coach-response.json`

Role:

- reference coaching hints for the current session
- not a canonical answer artifact

Contains:

- summary
- answer
- usage guidance
- sections
- evidence
- next actions
- postpone guidance
- follow-up question

Use when:

- you want a quick answer frame after reading `coach-run.json`
- you want a hint for teaching order or explanation emphasis

Do not use when:

- you need the final learner-facing answer
- you have not checked the current evidence and interpretation yourself

### `actions/coach-session.json`

Role:

- session bundle for context + actions + response

### `actions/coach-run.json`

Role:

- top-level orchestration result
- canonical first-read artifact — reading this file plus `contexts/learner-state.json` is enough to answer most turns

Contains:

- `execution_status`: `ready` | `blocked` | `error`
- repo resolution
- archive sync result
- archive status
- session summary
- `memory` (authoritative embedded snapshot: summary + profile, optionally with `cs_view` / `drill_history` / `reconciled`)
- `cs_readiness`: `{state: ready|missing|stale, next_command, reason, corpus_hash, index_manifest_hash}`. **Separate from `execution_status`** — missing/stale indexes never downgrade `execution_status`. AI decides whether to rebuild via `bin/cs-index-build`. `execution_status=blocked` remains archive-only.
- `cs_augmentation`: compact `{by_learning_point | by_fallback_key, cs_categories_hit, sidecar_path, verifier_hits, citation_paths, meta}`. Raw document bodies live in `contexts/cs-augmentation.json`. When `fallback_reason` is set, `by_fallback_key` renders primary; otherwise `by_learning_point` renders primary. `verifier_hits` and `citation_paths` are the allowed source set for CS citation grounding.
- `intent_decision`: `{detected_intent, signals, block_plan, cs_search_mode}`. Two-stage (`pre_decide` before augment → `finalize` after). `block_plan.{snapshot_block, cs_block, verification, drill_block}` ∈ `{primary, supporting, omit}` is advisory guidance, not runtime-enforced.
- `unified_profile`: per-turn compact projection of `memory/profile.json` — `{coach_view, cs_view, reconciled}`. **profile.json is source of truth**; `unified_profile` is a derived view and must not be written back.
- `learner_context`: per-turn learner projection used by adaptive RAG/coach behavior.
- `cognitive_trigger`: single selected cognitive prompt for the turn — `self_assessment`, `review_drill`, `follow_up`, or `none`.
- reference coach reply markdown
- `response_contract` — pre-rendered Response Contract fragments (see below)
- `error_detail` and `canonical_write_failed` when `execution_status=error`

This is the preferred first artifact to read. See [error-recovery.md](../docs/error-recovery.md) for error-state handling.

**`response_contract`** — always-present object so AI sessions can copy the canonical blocks verbatim instead of recomputing from `learner-state.json`.

- `snapshot_block`
  - `markdown` — the full `## 상태 요약 (snapshot, computed_at=...)` block, ready to paste. Null when the run is not `ready` or when no target PR was selected; inspect `reason` in that case.
  - `counts` — `{total, classification, reply_axis}`. `classification` is a 5-bucket dict (`still-applies`, `likely-fixed`, `already-fixed`, `ambiguous`, `unread`); `reply_axis` is a 4-bucket dict (`text`, `emoji`, `none`, `unknown`). Both sums equal `total`. Null when `markdown` is null.
  - `computed_at`, `target_pr_number`, `target_pr_selection_reason` — copied from the snapshot.
  - `reason` — one of `ready` / `blocked` / `error` / `no_target_pr`.
- `verification`
  - `required_count` — number of threads classified `ambiguous` or `likely-fixed` that require same-turn `git show` before narration.
  - `thread_refs` — deterministic list of `{thread_id, path, line, classification, classification_reason}` sorted by `(ambiguous first, then likely-fixed) → path → line`.
  - `stub_markdown` — paste-ready `## 수동 확인 필요` block listing every `thread_refs` entry. Null when `required_count == 0`.

AI usage rule: copy `snapshot_block.markdown` verbatim at the top of the reply; for each entry in `verification.thread_refs`, either run `git show <head_sha>:<path>` in the same turn and promote inside `## 이 턴에 직접 확인`, or paste `verification.stub_markdown` into a `## 수동 확인 필요` section. Include `cognitive_block.markdown` when its `applicability_hint` is not `omit`, and do not also surface `follow_up_block` when a cognitive trigger is selected. See [agent-operating-contract.md](../docs/agent-operating-contract.md) Response Contract.

- `cs_block` (CS/theory evidence)
  - `markdown` — rendered `## 이번 질문의 CS 근거` block listing hits as `- [category] path — preview`. Null when `cs_readiness != ready`, `cs_search_mode == skip`, or there are no hits.
  - `sources` — `[{path, category, section}, ...]`. Each entry must be grounded by `cs_augmentation.verifier_hits[].path` or `cs_augmentation.citation_paths`. If the two drift, trust `cs_augmentation` and re-render.
  - `grounding_check` — `{ok, severity, ungrounded_paths}`. `severity="warn"` means rendered paths are not fully verifier-grounded; surface a caveat but do not block the whole reply.
  - `reason` — `ready` | `rag_skip` | `rag_not_ready` | `no_hits` | `no_augmentation`.
  - `applicability_hint` ∈ `{primary, supporting, omit}`. Advisory — AI selects which blocks to include in the learner reply based on the detected intent.

- `drill_block` (new drill offer this turn, optional)
  - `markdown` — `## 확인 질문 (선택)\n{question}\n\n(원한다면 다음 턴에 답변해 줘. 약점 축을 다듬을 수 있어.)` when a new offer was generated, else null.
  - `reason` — `new_offer` | `none`.
  - `applicability_hint` — usually `supporting` when an offer exists, `omit` otherwise. Drills are optional; learners can always ignore them without penalty.

- `drill_result_block` (grading of the previous turn's pending drill, optional)
  - `markdown` — `## 지난 확인 질문 채점\n- 점수: 6/10 (L3)\n- 약점: 깊이, 완결성\n- 다음 제안: ...` when the previous turn's pending drill was consumed this turn, else null.
  - `reason` — `result_from_previous` | `none`.
  - `applicability_hint` — `supporting` typically; the main reply focus stays on the learner's current question.

- `cognitive_block` (single cognitive trigger view, v4)
  - `markdown` — ready-to-paste prompt for `self_assessment`, `review_drill`, or `follow_up`; null for `none`.
  - `trigger_type` — `self_assessment` | `review_drill` | `follow_up` | `none`.
  - `trigger_session_id` — required when a self-assessment or review trigger needs later matching.
  - `payload`, `evidence`, `reason`, `competed_against`.
  - `applicability_hint` — include when not `omit`.

- `follow_up_block` (legacy follow-up queue view)
  - Suppressed with `applicability_hint="omit"` when `cognitive_block` surfaces `self_assessment`, `review_drill`, or `follow_up`.

cs_block ↔ cs_augmentation contract: `cs_augmentation` is source of truth. `cs_block` is a render view. Tests assert every `cs_block.sources` path is in `cs_augmentation.verifier_hits[].path ∪ cs_augmentation.citation_paths`; drift is reported through `grounding_check`.

### `actions/coach-run.error.json`

Role:

- sidecar fallback when canonical `coach-run.json` write itself failed

Contains:

- same shape as `coach-run.json` with `execution_status=error`
- `canonical_write_failed: true`
- `error_detail.sidecar_path`

Read this only when `coach-run.json` is missing or stale and this sidecar exists.

## Memory Layer

### `memory/history.jsonl`

Role:

- append-only session history

Contains per session:

- prompt
- question fingerprint
- diff fingerprint
- primary topic / intent
- primary learning points
- learning-point recommendations digest
- follow-up question

### `memory/summary.json`

Role:

- aggregated summary over history

Contains:

- top topics
- top intents
- `top_learning_points` (raw cumulative)
- `weighted_learning_points` (time-decayed, half-life 14 days)
- repeated learning points
- learning point confidence
- repeated question patterns
- recurring paths

### `memory/profile.json`

Role:

- long-term coaching profile

Contains:

- confidence
- dominant learning points (each with `recency_status`)
- repeated learning points (each with `recency_status`)
- underexplored learning points
- recent learning streak
- open follow-up queue
- (optional) `cs_view` — `{avg_score, level, weak_dimensions, weak_tags, low_categories, recent_drills}` derived from `drill-history.jsonl`
- (optional) `drill_history` — compact summary of recent drill results (total_score, level, weak_tags). Full detail lives in `drill-history.jsonl`.
- (optional) `reconciled` — `{priority_focus, empirical_only_gaps, theoretical_only_gaps}` cross-axis weak points

**profile.json is persisted truth.** `coach-run.json.unified_profile` is a derived per-turn projection. Never write back from `unified_profile` to `profile.json`.

`recency_status` values: `active`, `cooling`, `dormant`. See [memory-model.md](../docs/memory-model.md) for interpretation.

Use this artifact when deciding whether to deepen or broaden.

### `memory/drill-pending.json` (optional)

Role:

- single open drill offer awaiting the learner's answer
- present only while a drill question is in flight; absent otherwise

Contains:

- `drill_session_id`, `question`, `linked_learning_point`, `source_doc`, `expected_terms`, `created_at`, `ttl_turns`
- optional review fields: `review_of_session_id`, `review_count`, `review_due_at`

Lifecycle:

1. `drill.build_offer_if_due` creates it after `unified_profile.reconciled` is computed
2. `drill.build_review_offer_if_due` may create it from a due `drill-history.jsonl` entry; review drills still use this same pending file
3. Next turn: `drill.decrement_ttl` → `route_answer` → on answer, `score_pending_answer` → append to `drill-history.jsonl` → clear file
4. If TTL hits zero without an answer, file is cleared

Missing is normal — `validate-state` reports `status: not_applicable`.

### `memory/drill-history.jsonl` (optional, append-only)

Role:

- append-only record of 4-dimension drill results (accuracy, depth, practicality, completeness)
- authoritative source for `profile.json.cs_view` and `unified_profile.cs_view`

Each line:

- `drill_session_id`, `scored_at`, `linked_learning_point`, `question`, `answer`, `total_score`, `level`, `dimensions`, `weak_tags`, `improvement_notes`, `source_doc`
- spaced review fields: `due_at`, `review_of_session_id`, `review_count`, `last_outcome`

Missing is normal (no drills yet). If the file exists, `validate-state` validates every line strictly.

### `state/learner/pending_triggers.json` (optional)

Role:

- learner-level pending cognitive triggers that are not drill answers
- currently used for `self_assessment`

Contains:

- `self_assessment.trigger_session_id`
- `self_assessment.payload.concept_ids`
- `issued_at`, `expires_at`

Lifecycle:

1. `cognitive_trigger.select_cognitive_trigger` chooses a self-assessment prompt without side effects
2. after canonical `coach-run.json` write succeeds, `coach_run` persists the pending trigger
3. if the learner answers, the AI session runs `bin/learn-self-assess --silent --trigger-session-id <id> "<response>"`
4. `learn-self-assess` appends a `self_assessment` learner event and clears the pending trigger

Random self scores without a matching pending trigger are rejected.

### `state/learner/response-quality.jsonl` (optional, append-only)

Role:

- assistant response-quality telemetry for RAG learning turns
- analysis-only; not used to compute mastery or normal learner personalization
- joins to `state/learner/history.jsonl` through `source_event_id` and `turn_id`

Each line:

- `schema_id="assistant-response-quality-v1"`
- `source_event_id` (`rag_ask.event_id`)
- `turn_id` (`turn-<event_id>`)
- redacted `prompt`
- `response_summary`
- capped `response_excerpt`
- `response_length_chars`, `response_hash`
- `answer_strategy`
- `citation_paths_expected`, `citation_paths_declared`
- `quality_flags` (`citation_mismatch`, `missing_citation`, `missing_rag_header`, `duplicate_text`, `overlong_answer`, ...)
- `contract_flags`

Writer:

- `bin/learn-response-quality --silent ...`
- AI sessions call it after drafting learner-facing RAG answers, using
  `bin/rag-ask`'s `response_quality_hint`. The learner does not run it.

Analyzer:

- `bin/response-quality-mine`
- reports quality flag distribution and citation mismatch candidates for later
  agent-contract / corpus / router improvement work.

Do not use this artifact as a substitute for learner understanding. It says
something about answer quality, not whether the learner mastered a concept.

## Context Layer — CS Sidecar

### `contexts/cs-augmentation.json` (optional)

Role:

- sidecar with full CS document bodies + sections + raw reranker scores for the current turn
- source of truth for `coach-run.json.cs_augmentation` (top-level is a compact view)

Present only when:

- `intent_decision.cs_search_mode ∈ {cheap, full}`, AND
- `cs_readiness.state == "ready"`, AND
- the augment call returned hits

Missing is normal for mission-only turns or when the CS index is not ready. `validate-state` reports `status: not_applicable` in those cases.

## Reading Priority

Default:

1. `actions/coach-run.json` (the embedded `memory` field is authoritative for the current session)
2. `contexts/learner-state.json` (authoritative for learner-side facts — branches, working copy, target PR, unresolved threads)
3. `analysis/mission-map.json`
4. `contexts/coach-candidate-interpretation.json`
5. `contexts/coach-focus.json`
6. `actions/coach-response.json` as an optional reference
7. `memory/profile.json` and `memory/summary.json` only when the embedded snapshot is missing a field you specifically need
8. lower-level packets only when interpretation + focus are insufficient

Do not re-read `memory/profile.json` or `memory/summary.json` by default. The snapshot embedded in `coach-run.json.memory` is the same data and reading the sidecars duplicates cost. See [token-budget.md](../docs/token-budget.md).

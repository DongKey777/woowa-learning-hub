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

See [evidence-roles.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/evidence-roles.md) for role definitions and bucket semantics.

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

See [agent-operating-contract.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/agent-operating-contract.md) **First-Run Protocol step 6** for how this artifact is produced.

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
- canonical first-read artifact

Contains:

- `execution_status`: `ready` | `blocked` | `error`
- repo resolution
- archive sync result
- archive status
- session summary
- `memory` (authoritative embedded snapshot: summary + profile)
- reference coach reply markdown
- `response_contract` — pre-rendered Response Contract fragments (see below)
- `error_detail` and `canonical_write_failed` when `execution_status=error`

This is the preferred first artifact to read. See [error-recovery.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/error-recovery.md) for error-state handling.

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

AI usage rule: copy `snapshot_block.markdown` verbatim at the top of the reply; for each entry in `verification.thread_refs`, either run `git show <head_sha>:<path>` in the same turn and promote inside `## 이 턴에 직접 확인`, or paste `verification.stub_markdown` into a `## 수동 확인 필요` section. See [agent-operating-contract.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/agent-operating-contract.md) Response Contract.

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

`recency_status` values: `active`, `cooling`, `dormant`. See [memory-model.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/memory-model.md) for interpretation.

Use this artifact when deciding whether to deepen or broaden.

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

Do not re-read `memory/profile.json` or `memory/summary.json` by default. The snapshot embedded in `coach-run.json.memory` is the same data and reading the sidecars duplicates cost. See [token-budget.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/token-budget.md).

# Capability Map

## Goal

This document explains the system's internal capabilities in the language of "skills".
These are not Codex marketplace skills.
They are the conceptual capabilities another AI should understand before operating the system.

## Capability 1. Repo Intake

Responsibility:

- resolve a learner repo from path or registry
- detect `origin`, `upstream`, branch hint, current PR title

Primary code:

- [repo_intake.py](../scripts/workbench/core/repo_intake.py)

When to use:

- always, before anything else

## Capability 2. Mission Relevance Retrieval

Responsibility:

- collect PRs from upstream
- prefer PRs relevant to the learner's current mission stage

Primary code:

- [mission_relevance.py](../scripts/pr_archive/mission_relevance.py)
- [collect_prs.py](../scripts/pr_archive/collect_prs.py)

When to use:

- before packet generation if archive is stale or missing

## Capability 2.5. Evidence Role Classification

Responsibility:

- label review comments, review bodies, and issue comments by role (bot/mentor/self variants)
- persist `comment_role` and `reviewer_role` columns for later filtering and weighting

Primary code:

- [comment_classifier.py](../scripts/workbench/core/comment_classifier.py)

When to use:

- automatically after `sync_repo_archive`
- manually when rerunning classification on a legacy database

Notes:

- uses `BOT_USERS` to exclude automated reviewers
- stable metadata only; dynamic weighting lives in `session_focus.py`
- see [evidence-roles.md](../docs/evidence-roles.md)

## Capability 2.6. Review Thread Reconstruction

Responsibility:

- rebuild mentor↔learner review threads from `in_reply_to_github_comment_id`
- emit bounded `thread_samples` for packets (≤5 per packet, ≤3 turns per thread)

Primary code:

- [thread_builder.py](../scripts/workbench/core/thread_builder.py)

When to use:

- during packet generation for topic, reviewer, and PR report artifacts
- before running candidate interpretation so thread role_sequence is available

## Capability 3. Evidence Packet Generation

Responsibility:

- generate topic packet
- generate reviewer packet
- generate compare packet
- generate PR report

Primary code:

- [packets.py](../scripts/workbench/core/packets.py)

When to use:

- when the question needs cross-PR or reviewer evidence

## Capability 4. Same-Stage Peer Focus Ranking

Responsibility:

- shortlist peer PRs close to the current question
- use prompt, local diff/current PR file signature, PR body, review body, review comments

Primary code:

- [session_focus.py](../scripts/workbench/core/session_focus.py)

When to use:

- concept explanation
- peer comparison
- implementation planning
- testing strategy

## Capability 5. Learning-Point Interpretation

Responsibility:

- convert shortlisted PRs into learning-point recommendations
- map PRs to points such as:
  - repository boundary
  - responsibility boundary
  - transaction consistency
  - db modeling
  - testing strategy

Primary code:

- [candidate_interpretation.py](../scripts/workbench/core/candidate_interpretation.py)

When to use:

- whenever raw shortlist is too ambiguous
- whenever the learner asks "which example should I study?"

## Capability 6. Reviewer Lens Extraction

Responsibility:

- infer a reviewer's repeated criteria and hotspot paths

Primary code:

- [reviewer_profile.py](../scripts/workbench/core/reviewer_profile.py)

When to use:

- reviewer-lens questions
- PR response questions
- review triage questions

## Capability 7. Intent-Aware Coach Response

Responsibility:

- answer differently depending on learner intent
- use evidence and learning-point interpretation

Primary code:

- [response.py](../scripts/workbench/core/response.py)

When to use:

- always, after retrieval and interpretation

## Capability 8. Learning Memory

Responsibility:

- persist session history
- accumulate learning points, repeated patterns, underexplored areas
- produce summary and long-term profile with time-decayed weights (`weighted_learning_points`, `recency_status`)
- support 2-phase write: pure compute (`compute_memory_update`) then atomic commit (`commit_history_entry`, `commit_memory_snapshot`)
- detect stale snapshots (`needs_recompute`) and rebuild from history (`recompute_from_history`)

Primary code:

- [memory.py](../scripts/workbench/core/memory.py)

When to use:

- before session generation: read prior profile, check `needs_recompute`
- during session generation: `compute_memory_update` in Phase 1
- after session generation: sequential commit in Phase 2

See [error-recovery.md](../docs/error-recovery.md) for failure matrix.

## Capability 8.5. Learner State Assessment

Responsibility:

- direct-observation snapshot of the learner's mission repo before `coach-run` (branches, working copy, open PRs, target PR selection, unresolved review threads)
- classify each review thread into `still-applies` / `likely-fixed` / `already-fixed` / `ambiguous` / `unread` with a `classification_reason`
- collect `learner_reactions` and `learner_acknowledged` tri-state (`true` / `false` / `"unknown"` when GraphQL fails)
- record every fallback on `budget.skipped[]` so operators can trace why a field collapsed to `"unknown"` (reasons: `forced:*`, `invalid_upstream`, `gh_call_cap`, `graphql_failure`, `graphql_parse_failure`)
- support forced-fallback reproduction via `WOOWA_FORCE_GRAPHQL_FAIL=<tag>` environment variable
- apply a 4-way staleness check (head SHA, working-copy fingerprint, target-PR head SHA, TTL) before rebuilding

Primary code:

- [learner_state.py](../scripts/workbench/core/learner_state.py)

When to use:

- every coach-run session (invoked implicitly by `coach_run.py`)
- manually via `bin/assess-learner-state --repo <name>` when debugging snapshot freshness or fallback behavior

See [artifact-catalog.md](../docs/artifact-catalog.md) `contexts/learner-state.json`.

## Capability 8.6. Response Contract Pre-Render

Responsibility:

- pre-compute the pieces of the canonical Response Contract (`docs/agent-operating-contract.md`) that the pipeline can derive from `learner-state.json`, so AI sessions copy them verbatim instead of re-tallying
- render the full `## 상태 요약` block (snapshot markdown + 5-bucket classification counts + 4-bucket reply axis counts) with sum-invariant guarantees
- enumerate the threads that require same-turn `git show` verification (`ambiguous` and `likely-fixed`) and render a paste-ready `## 수동 확인 필요` stub
- return an always-present object with identical shape across `ready` / `blocked` / `error` states (nullable fields on non-ready) so downstream validators and AI consumers see one schema

Primary code:

- [response_contract.py](../scripts/workbench/core/response_contract.py)

When to use:

- inside `coach_run.py` payload assembly, right before `validate_payload` — injected into `coach-run.json.response_contract`
- consumed by AI sessions directly (no other call site)

Scope note: this capability is **pre-rendered assistance**, not mechanical enforcement. It removes the "AI recomputes counts and gets them wrong" failure mode, but it does not block an AI from ignoring the fields. Hard post-response enforcement is a separate (out-of-scope) hook layer.

## Capability 9. Top-Level Orchestration

Responsibility:

- run the whole pipeline end-to-end
- expose a single coach-facing result artifact with `execution_status` contract
- coordinate 2-phase write order: history → coach-run.json → summary → profile
- on canonical write failure, fall back to `coach-run.error.json` sidecar

Primary code:

- [coach_run.py](../scripts/workbench/core/coach_run.py)

When to use:

- default entrypoint for almost every learner question

See [error-recovery.md](../docs/error-recovery.md) for the execution_status contract.

## Question To Capability Mapping

Learner questions are shown in Korean with an English gloss.

- "내 리뷰 기준 다음 액션 뭐야?" (What should I do next based on my review?)
  - repo intake
  - PR report
  - reviewer lens
  - response

- "다른 크루들은 어떻게 했어?" (How did other crews handle this?)
  - repo intake
  - same-stage peer focus
  - learning-point interpretation
  - response

- "왜 이 구조를 바꿔야 해?" (Why should I change this structure?)
  - repo intake
  - topic packet
  - peer focus
  - response

- "어떤 테스트를 먼저 해야 해?" (Which test should I do first?)
  - repo intake
  - PR report
  - peer focus
  - learning memory
  - response

- "이 리뷰에 어떻게 답변할까?" (How should I reply to this review?)
  - PR report
  - reviewer lens
  - candidate interpretation
  - response

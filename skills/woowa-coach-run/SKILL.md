---
name: "woowa-coach-run"
description: "Use when operating this repository as a Woowa mission coach. Start from coach-run, treat mission repos as read-only by default, and interpret state artifacts as the source of truth."
---

# Woowa Coach-Run Skill

## When to use

- The task is a Woowa mission learning/coaching question.
- A learner repo path or repo name is available.
- You need the top-level orchestration rather than ad hoc packet generation.

## Workflow

1. Prefer `coach-run` as the top-level backend.
2. Read `actions/coach-run.json` first. Branch on `execution_status`:
   - `ready` — proceed.
   - `blocked` — explain bootstrap need from `archive_sync.next_command`.
   - `error` — read `memory` for context, acknowledge the failure, suggest retry. If `canonical_write_failed=true`, read `actions/coach-run.error.json` instead.
3. Use lower-level artifacts only when the top-level artifact is insufficient. Consult `docs/token-budget.md` before opening `packets/*.json`.
4. Treat mission repos as read-only unless the user explicitly asks for edits.
5. Explain recommendations in terms of:
   - learner question
   - repo state
   - mentor PR/review evidence
   - learning point
   - learning memory (prefer `weighted_learning_points` and `recency_status`)

## Canonical artifact order

1. `actions/coach-run.json` (the embedded `memory` field is authoritative for the current session)
2. `contexts/learner-state.json` (direct-observation snapshot of the learner's branches, working copy, target PR, unresolved threads — produced by `assess-learner-state`; authoritative for learner-side facts)
3. `analysis/mission-map.json`
4. `contexts/coach-candidate-interpretation.json`
5. `contexts/coach-focus.json`
6. `actions/coach-response.json` as an optional reference
7. `memory/profile.json` and `memory/summary.json` only when the embedded snapshot is insufficient
8. lower-level packets only when interpretation + focus are insufficient

Before `coach-run`, ensure `learner-state.json` is fresh by running `./bin/assess-learner-state --repo <name>` on first turn or when its cache key (`head_sha`, `working_copy.fingerprint`, target PR head SHA, `computed_at + 10m`) is stale. See `docs/agent-operating-contract.md` First-Run Protocol step 6 and `docs/token-budget.md` Pre-coach-run Direct Read Budget.

## Response Contract

Every learner-facing reply must follow the canonical **Response Contract** in `docs/agent-operating-contract.md`. Summary:

1. Begin with a `## 상태 요약` snapshot block. **Copy `coach-run.json.response_contract.snapshot_block.markdown` verbatim** instead of re-tallying. Rows: `already-fixed`, `likely-fixed`, `still-applies`, `ambiguous`, `unread`; reply breakdown via `learner_acknowledged` (`"unknown"` is its own 불명 bucket for GraphQL fetch failures — never merged into 없음).
2. Any in-turn upgrades (via `git show`) go in a separate `## 이 턴에 직접 확인` block. Do not mutate the snapshot counts in the narrative.
3. Per-item narrative uses dual-axis lines: `코드 상태` (from `classification` + `classification_reason`) and `답변 상태` (preserve raw `learner_reactions` values, never normalize to 👍).
4. `ambiguous` and `likely-fixed` must be verified with `git show <head_sha>:<path>` before narration, or listed under `수동 확인 필요` if the budget is exhausted. The authoritative list is `coach-run.json.response_contract.verification.thread_refs`; `verification.stub_markdown` is a paste-ready `## 수동 확인 필요` block.
5. First-response gate: no thread is narrated as `이미 반영됨` or `아직 남아있음` without either a `already-fixed`/`still-applies` snapshot classification or a same-turn `git show`.

## Evidence rules

- Use `mentor_comment_samples` and mentor turns in `thread_samples` as teaching evidence.
- Treat `crew_response_samples` as the learner's prior reply, not mentor feedback.
- Never cite bot rows.
- For threads with depth ≥ 2, prefer the last mentor turn as the primary quote.

## Do not do this

- Do not recommend a PR only because it has the highest score.
- Do not edit the learner repo during a learning-only question.
- Do not trust markdown preview over JSON.
- Do not open multiple packet files in one session without explicit need.

## Related docs

- `docs/agent-operating-contract.md`
- `docs/artifact-catalog.md`
- `docs/evidence-roles.md`
- `docs/error-recovery.md`
- `docs/token-budget.md`
- `docs/memory-model.md`

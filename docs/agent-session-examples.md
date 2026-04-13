# Agent Session Examples

## Purpose

These examples show how another AI should use the system for common learner questions. Learner questions are illustrated in their original Korean followed by an English gloss, because real learners ask in Korean.

## Example 1. Review Triage

Learner question:

- "내 리뷰 기준 다음 액션 뭐야?" (What should I do next based on my review?)

Recommended backend:

- `coach-run`

Artifacts to prioritize:

1. `actions/coach-run.json` (embedded `memory` is authoritative; copy `response_contract.snapshot_block.markdown`)
2. `contexts/learner-state.json` — authoritative for learner-side facts (branches, working copy, target PR, unresolved threads)
3. `packets/pr-<number>-report.json`
4. `packets/reviewer-*.json` if reviewer is fixed
5. `actions/coach-response.json` as a reference hint only

Expected answer shape:

- what the most important review hotspot is
- which comments are code-fix candidates
- which comments are explanation candidates
- 2–3 immediate next actions

## Example 2. Peer Comparison

Learner question:

- "다른 크루들은 Repository를 어떻게 했어?" (How did other crews implement Repository?)

Recommended backend:

- `coach-run`

Artifacts to prioritize:

1. `actions/coach-run.json` (copy `response_contract.snapshot_block.markdown`)
2. `contexts/learner-state.json` — authoritative for learner-side facts
3. `contexts/coach-candidate-interpretation.json`
4. `contexts/coach-focus.json`
5. `packets/topic-repository.json` only if interpretation + focus are insufficient

Expected answer shape:

- learning-point-by-learning-point recommendations
- one deepen recommendation
- one broaden recommendation
- mentor review comment evidence for why each PR is useful

## Example 3. Concept Explanation

Learner question:

- "Repository가 왜 이걸 알면 안 돼?" (Why shouldn't Repository know this?)

Artifacts to prioritize:

1. `actions/coach-run.json` (copy `response_contract.snapshot_block.markdown`)
2. `contexts/learner-state.json` — authoritative for learner-side facts
3. `contexts/coach-candidate-interpretation.json`
4. `contexts/coach-focus.json`
5. current repo paths from the learner repo
6. `actions/coach-response.json` as a reference hint only

Expected answer shape:

- explain the boundary
- point to current code locations
- show one or two peer PRs that illustrate the boundary

## Example 4. Testing Strategy

Learner question:

- "어떤 테스트를 먼저 추가해야 해?" (Which test should I add first?)

Artifacts to prioritize:

1. `actions/coach-run.json` (read `memory` for testing-related recency; copy `response_contract.snapshot_block.markdown`)
2. `contexts/learner-state.json` — authoritative for learner-side facts
3. `packets/pr-<number>-report.json`
4. `contexts/coach-candidate-interpretation.json`
5. `actions/coach-response.json` as a reference hint only

Expected answer shape:

- what behavior is cheapest to verify first
- whether testing is an underexplored point for this learner
- one deepen recommendation if the learner repeatedly asks about structure only

## Example 5. PR Response

Learner question:

- "이 리뷰에 어떻게 답변할까?" (How should I reply to this review?)

Artifacts to prioritize:

1. `actions/coach-run.json` (copy `response_contract.snapshot_block.markdown`; resolve every `response_contract.verification.thread_refs` entry)
2. `contexts/learner-state.json` — authoritative for learner-side facts, especially `target_pr_detail.threads`
3. `packets/pr-<number>-report.json`
4. `packets/reviewer-*.json`
5. `actions/coach-response.json` as a reference hint only

Expected answer shape:

- separate code-change response vs explanation response
- point to specific mentor review comments (never cite `crew_response_samples` as mentor feedback)
- mention if the learner repeatedly over-focuses on one learning point

## General Rule

For almost every session:

- read `coach-run.json` first — its embedded `memory` field is authoritative for the current session
- copy `coach-run.json.response_contract.snapshot_block.markdown` verbatim as the first block of the reply — do **not** re-tally counts from `learner-state.json`
- resolve every entry in `response_contract.verification.thread_refs` either by same-turn `git show` (promote inside `## 이 턴에 직접 확인`) or by pasting `verification.stub_markdown` into `## 수동 확인 필요`
- do **not** re-read `memory/profile.json` or `memory/summary.json` by default
- use `coach-candidate-interpretation.json` to choose examples
- use `coach-response.json` only as a reference frame
- use lower-level packets only when necessary; consult `docs/token-budget.md` first
- branch on `execution_status` in `coach-run.json`: `ready` → proceed, `blocked` → explain bootstrap, `error` → acknowledge failure and fall back to `coach-run.error.json` if `canonical_write_failed=true`

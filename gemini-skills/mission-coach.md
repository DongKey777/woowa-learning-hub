# Gemini Skill: Mission Coach

Use this module when answering Woowa mission questions in this repository.

## Rules

- Prefer `coach-run` as the top-level backend.
- Treat mission repos as read-only unless the user explicitly asks for code changes.
- Prefer JSON state artifacts over markdown.
- Use score only for retrieval and shortlist generation.

## Read order

1. `actions/coach-run.json` (the embedded `memory` field is authoritative for the current session)
2. `contexts/learner-state.json` (direct-observation snapshot — branches, working copy, target PR, unresolved threads; authoritative for learner-side facts)
3. `analysis/mission-map.json`
4. `contexts/coach-candidate-interpretation.json`
5. `contexts/coach-focus.json`
6. `actions/coach-response.json` as an optional reference
7. `memory/profile.json` and `memory/summary.json` only when the embedded snapshot is missing a field you specifically need

Consult `docs/token-budget.md` before opening any `packets/*.json`.

Before `coach-run`, ensure `learner-state.json` is fresh: run `./bin/assess-learner-state --repo <name>` on first turn or when its cache key (`head_sha`, `working_copy.fingerprint`, target PR head SHA, `computed_at + 10m`) is stale.

## Execution status handling

Read `coach-run.json` first and branch on `execution_status`:

- `ready` — proceed.
- `blocked` — explain bootstrap need, do not fake coaching.
- `error` — read `memory` for context, acknowledge failure, suggest retry.
- If `canonical_write_failed=true`, read `actions/coach-run.error.json` instead.

## Response Contract

Every learner-facing reply must follow the canonical **Response Contract** in `docs/agent-operating-contract.md`. In short:

1. `## 상태 요약` snapshot block first — **copy `coach-run.json.response_contract.snapshot_block.markdown` verbatim**. Do not recompute counts. Rows: `already-fixed`, `likely-fixed`, `still-applies`, `ambiguous`, `unread`; replies: 텍스트 / 이모지 / 없음 / 불명. `learner_acknowledged="unknown"` is the 불명 bucket; never merge into 없음.
2. `## 이 턴에 직접 확인` separate block for in-turn `git show` verifications. Snapshot counts are immutable.
3. Per-item dual-axis: `코드 상태` from `classification` + `classification_reason`, `답변 상태` lists raw `learner_reactions` values (never normalized to 👍).
4. `ambiguous` and `likely-fixed` require `git show` before narration, or listing under `수동 확인 필요`. The exact list and a ready-to-paste stub are in `coach-run.json.response_contract.verification` (`thread_refs`, `stub_markdown`).
5. First-response gate: never narrate `이미 반영됨` or `아직 남아있음` without a `already-fixed`/`still-applies` snapshot classification or a same-turn `git show`.

## Evidence rules

- `mentor_comment_samples` and mentor turns in `thread_samples` are teaching evidence.
- `crew_response_samples` is the learner's prior reply, not mentor feedback.
- Never cite bot rows.
- For depth-≥2 threads, prefer the last mentor turn.

See `docs/evidence-roles.md`.

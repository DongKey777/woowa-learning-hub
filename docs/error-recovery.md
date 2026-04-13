# Error Recovery

## Purpose

This document defines how `coach-run` handles partial failures and how agents should behave when they read an artifact in error state.

## Write Order

`coach_run.py` uses a best-effort 2-phase write:

**Phase 1 (in-memory compute, no file changes):**

1. resolve repo
2. load previous memory
3. start session
4. compute memory update (history entry, summary, profile)
5. build coach-run payload

**Phase 2 (sequential disk writes):**

1. append `memory/history.jsonl`
2. write `actions/coach-run.json`
3. write `memory/summary.json`
4. write `memory/profile.json`

The order matters because `coach-run.json` is the canonical first-read artifact. It embeds the authoritative memory snapshot for the current session, so it must be persisted before the sidecar summary/profile files.

## Execution Status Contract

`coach-run.json` always keeps the same top-level shape. State is expressed through `execution_status`:

| Status | Meaning |
|---|---|
| `ready` | session started, all evidence gathered, all writes succeeded |
| `blocked` | data insufficient (archive uninitialized), session not started |
| `error` | session started but one of the Phase 2 writes failed |

## Error Payload

When Phase 2 fails, `execution_status=error` is set and the payload gets:

- `error_detail.phase`: `"history_append"` | `"coach_run_write"` | `"memory_snapshot"`
- `error_detail.message`: exception text
- `error_detail.timestamp`: ISO 8601
- `memory`: the latest computed snapshot (from Phase 1), even if not yet persisted

The agent can still read `memory` for context — the snapshot is authoritative for the current session even when downstream files are stale.

## Sidecar Fallback

If the canonical `actions/coach-run.json` write itself fails, the error payload is written to `actions/coach-run.error.json` instead. In that case:

- `canonical_write_failed: true`
- `error_detail.sidecar_path`: absolute path to the sidecar
- `json_path`: also points to the sidecar
- the stale `coach-run.json` (if any) is left untouched

Agent reading rule:

1. try `actions/coach-run.json` first
2. if it is missing, stale, or has `execution_status=error` with `canonical_write_failed=true`, fall back to `actions/coach-run.error.json`
3. `validate-state` checks both paths automatically

## Recompute Recovery

`memory.py::needs_recompute()` detects stale memory snapshots at session start. It triggers when:

- `summary.json` or `profile.json` is missing
- `history.jsonl` mtime > `summary.json` mtime
- `history.jsonl` mtime > `profile.json` mtime
- `summary.json` mtime and `profile.json` mtime differ by more than 1 second

When triggered, `recompute_from_history()` rebuilds both snapshots from the full history log. This recovers from the case where Phase 2 wrote history but failed on summary or profile.

## Failure Matrix

| Failure point | coach-run.json | summary/profile | history | Recovery |
|---|---|---|---|---|
| Phase 1 (compute failure) | unchanged | unchanged | unchanged | safe, no-op |
| Phase 2 `history_append` | unchanged | unchanged | unchanged | safe, retry |
| Phase 2 `coach_run_write` | error sidecar or error payload | unchanged | appended | next session recomputes from history |
| Phase 2 `memory_snapshot` | latest (authoritative) | stale | appended | `needs_recompute` triggers next session |

## Agent Behavior Under Error

When `execution_status=error`:

1. read `memory` from the payload for context
2. acknowledge to the learner that the previous attempt hit a system issue
3. provide limited coaching based on available evidence
4. suggest retrying the session
5. do not pretend the session wrote complete state to disk

When `execution_status=blocked`:

1. read `archive_sync.next_command` for the bootstrap instruction
2. explain that a one-time collection step is needed
3. do not run partial coaching as if the archive were ready

## Learner State GraphQL Fallback

`learner_state.py::_fetch_thread_graph` fetches `isResolved` and reactions for each review thread via a single GraphQL call. Every non-success return path logs to `budget.skipped[]` so operators can trace why a tri-state field collapsed to `"unknown"` in `learner-state.json`.

| Skipped reason | Meaning |
|---|---|
| `forced:<tag>` | `WOOWA_FORCE_GRAPHQL_FAIL=<tag>` was set — used to reproduce the fallback path with real data |
| `invalid_upstream` | `upstream` slug could not be parsed as `owner/repo` |
| `gh_call_cap` | budget cap hit before the GraphQL call could run (`MAX_GH_CALLS`) |
| `graphql_failure` | `gh api graphql` returned non-zero |
| `graphql_parse_failure` | response body was not valid JSON |

When any of these fire, the fallback propagates as:

- `threads[].resolved = "unknown"`
- `threads[].learner_acknowledged = "unknown"`
- `threads[].learner_reactions = []`
- `classification` is still computed from the diff hunks and thread metadata — only the GraphQL-sourced fields collapse

The surrounding `classification` heuristic is unaffected, so `still-applies` / `likely-fixed` / `ambiguous` still populate even when GraphQL fails. Narrative rule: treat `"unknown"` as a separate bucket (`불명`) and never merge into `없음`. See [agent-operating-contract.md](../docs/agent-operating-contract.md) Response Contract.

Reproduction recipe:

```
WOOWA_FORCE_GRAPHQL_FAIL=manual bin/assess-learner-state --repo <name> --upstream <owner/repo>
```

Inspect `contexts/learner-state.json.coverage.skipped` and confirm the tri-state fields are all `"unknown"`. Then unset the env var and re-run to restore the happy-path snapshot.

## Related Code

- `scripts/workbench/core/coach_run.py`
- `scripts/workbench/core/learner_state.py` (`_fetch_thread_graph`, `_Budget.note_skipped`)
- `scripts/workbench/core/memory.py` (`compute_memory_update`, `commit_history_entry`, `commit_memory_snapshot`, `needs_recompute`, `recompute_from_history`)
- `scripts/workbench/cli.py::_discover_validation_targets`
- `schemas/coach-run-result.schema.json`

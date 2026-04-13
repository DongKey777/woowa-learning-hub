Run the Woowa mission coaching pipeline for the target repo and answer as a mission coach.

Use `$ARGUMENTS` as the learner request or repo/path hint.

Default behavior:

1. Resolve the target repo from `$ARGUMENTS`.
2. Prefer `coach-run` as the backend entrypoint.
3. Read `coach-run.json` first. Branch on `execution_status`:
   - `ready` → proceed.
   - `blocked` → explain bootstrap need from `archive_sync.next_command`, do not fake coaching.
   - `error` → read `memory` from the payload, acknowledge failure, suggest retry. If `canonical_write_failed=true`, read `actions/coach-run.error.json` instead.
4. Consult `docs/token-budget.md` before opening packet artifacts. Default path is priority 1–4.
5. Drill into focus / interpretation artifacts only when the question requires peer evidence.
6. Answer with:
   - current situation
   - strongest evidence (cite the path/PR/role when possible)
   - what to do next
   - what not to change yet
   - one useful follow-up question

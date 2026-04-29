# Persistent Orchestrator

`woowa-learning-hub` now includes a file-backed persistent orchestrator for long-running CS corpus work.

It does not invoke language models by itself. Instead, it persists:

- a replenishing backlog
- the current suggested wave
- worker leases
- completion history
- daemon status / heartbeat / stop requests

This closes the gap between "one-shot AI worker task" and "continuous queue that survives session boundaries".

## State

Runtime state lives under `state/orchestrator/`:

- `queue.json`: all backlog items and their statuses
- `planner.json`: lane cursors used to replenish backlog
- `current-wave.json`: the current suggested wave for workers to claim
- `current-wave-expansion.json`: the expansion-profile suggested wave
- `status.json`: runner heartbeat, pid, queue summary
- `history.jsonl`: append-only event history
- `runner.pid`: background runner pid
- `runner.log`: background runner log
- `stop.request`: graceful stop signal

## Commands

- `bin/orchestrator init`
  - seed queue + build first wave
- `bin/orchestrator run-once`
  - refresh backlog, expire leases, rebuild wave once
- `bin/orchestrator run-loop`
  - foreground loop
- `bin/orchestrator start`
  - background loop
- `bin/orchestrator stop`
  - graceful stop request
- `bin/orchestrator status`
  - status + current wave + queue summary
- `bin/orchestrator queue`
  - inspect queue items
- `bin/orchestrator queue --profile quality|expansion|expansion60`
  - inspect queue items for one fleet profile
- `bin/orchestrator claim --worker <name>`
  - claim work items for a worker / AI session
- `bin/orchestrator complete --worker <name> --item-id <id> --summary "..."`
  - mark a claimed item complete
- `bin/orchestrator fleet-start --profile quality|expansion|expansion60`
  - start the local worker fleet supervisor and persistent worker processes for the selected profile
- `bin/orchestrator fleet-status [--profile quality|expansion|expansion60]`
  - inspect the active or selected local worker fleet state
- `bin/orchestrator fleet-stop [--profile quality|expansion|expansion60]`
  - stop the active or selected local worker fleet

## Flow

1. Start the runner with `bin/orchestrator start`.
2. Inspect `bin/orchestrator status`.
3. A worker session claims work with `bin/orchestrator claim --worker database-worker --limit 2`.
4. The worker finishes a coherent wave and reports it with `bin/orchestrator complete`.
5. The runner replenishes backlog automatically and produces the next wave.

## Real Worker Fleet

The queue runner alone does not create content. To get persistent autonomous work, start the local worker fleet:

```bash
bin/orchestrator fleet-start --profile quality
bin/orchestrator fleet-status
```

This starts:

- the queue/background orchestrator
- a supervisor loop
- 30 local worker processes

Each worker process repeatedly does:

1. wait for a write-scope-safe claim
2. run `codex exec` non-interactively against the claimed task
3. follow its worker profile (`role`, `mode`, `target_paths`, `write_scopes`, `quality_gates`)
4. call `bin/orchestrator complete`
5. claim the next task

If a worker exits, the supervisor starts it again. This is the persistent execution layer that the queue alone does not provide.

The default 30-worker fleet is a quality-repair profile, not an expansion profile:

- 21 QA workers for category docs, primer contracts, anchors, and link ladders
- 6 RAG workers for ranking regressions, signal rules, golden fixtures, and index readiness
- 3 ops/release workers for queue control and release gates

See [orchestrator-30-worker-fleet.md](orchestrator-30-worker-fleet.md) for the full profile contract.

For new CS corpus growth, use the separate expansion profile:

```bash
bin/orchestrator fleet-start --profile expansion
bin/orchestrator fleet-status
```

The expansion fleet mixes 1 curriculum analyst, 8 content workers, 12 QA workers, 6 RAG validation workers, and 3 ops workers. It targets learner-profile and Woowacourse Level 2/RoomEscape Admin gaps instead of turning all 30 workers into writers.

For higher-throughput corpus growth, use the 60-worker expansion profile:

```bash
bin/orchestrator fleet-start --profile expansion60
bin/orchestrator fleet-status --profile expansion60
```

The `expansion60` fleet mixes 2 curriculum workers, 24 content workers, 22 QA workers, 8 RAG workers, and 4 ops workers. It is designed for high throughput without treating all workers as writers: content scopes are narrower, README registration is handled by QA workers, and singleton RAG mutation surfaces are owned by exactly one worker each.

The expansion profiles are now balance-aware. Worker prompts include a live corpus distribution snapshot and should choose the right document role for the gap: Beginner entrypoint, Intermediate bridge/practice, Advanced deep dive, playbook, or recovery note. Once a category has enough Beginner entrypoints, new work should usually add Intermediate bridges or strengthen existing docs instead of creating another primer.

Queue ownership is profile-isolated. Legacy items without `fleet_profile` are treated as `quality`, while expansion-created items carry `fleet_profile=expansion` or `fleet_profile=expansion60`. An expansion worker must not claim legacy `worker-suggestion:runtime-qa-*` pending items; those remain for the quality fleet.

## Design Notes

- The orchestrator is honest about scope:
  - it persists and rotates work
  - it does not pretend to generate content without an actual worker
- Backlog is lane-based, but execution is write-scope protected:
  - content lanes still express broad CS categories
  - queue items are also profile-scoped by `fleet_profile`
  - the quality fleet claims only QA/RAG/Ops lanes
  - the expansion fleet allows bounded content writing and keeps QA/RAG/Ops workers in the same profile
  - the expansion60 fleet narrows content write scopes and moves README/taxonomy/RAG singleton edits to specialized workers
  - write scopes prevent conflicting writers from editing the same ownership surface
  - `fix` workers repair existing lint/retrieval debt instead of creating new docs
  - `expand` workers may create new docs only when the queue item maps to learner-profile, Woowacourse Level 2, or RAG retrieval gaps
  - `expand` workers must respect the live corpus balance snapshot and avoid blindly adding Beginner docs to saturated categories
- Queue items are intentionally high-level enough to support repeated waves without becoming brittle one-off prompts.

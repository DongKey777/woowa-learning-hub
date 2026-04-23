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
- `bin/orchestrator claim --worker <name>`
  - claim work items for a worker / AI session
- `bin/orchestrator complete --worker <name> --item-id <id> --summary "..."`
  - mark a claimed item complete
- `bin/orchestrator fleet-start`
  - start the local worker fleet supervisor and persistent worker processes
- `bin/orchestrator fleet-status`
  - inspect the local worker fleet state
- `bin/orchestrator fleet-stop`
  - stop the local worker fleet

## Flow

1. Start the runner with `bin/orchestrator start`.
2. Inspect `bin/orchestrator status`.
3. A worker session claims work with `bin/orchestrator claim --worker database-worker --limit 2`.
4. The worker finishes a coherent wave and reports it with `bin/orchestrator complete`.
5. The runner replenishes backlog automatically and produces the next wave.

## Real Worker Fleet

The queue runner alone does not create content. To get persistent autonomous work, start the local worker fleet:

```bash
bin/orchestrator fleet-start
bin/orchestrator fleet-status
```

This starts:

- the queue/background orchestrator
- a supervisor loop
- 15 local worker processes

Each worker process repeatedly does:

1. wait for a lane-safe claim
2. run `codex exec` non-interactively against the claimed task
3. write docs / links / anchors inside its owned lane
4. call `bin/orchestrator complete`
5. claim the next task

If a worker exits, the supervisor starts it again. This is the persistent execution layer that the queue alone does not provide.

## Design Notes

- The orchestrator is honest about scope:
  - it persists and rotates work
  - it does not pretend to generate content without an actual worker
- Backlog is lane-based:
  - content lanes for CS categories
  - quality lanes for bridge debt / anchors / links / taxonomy / retrieval
- Queue items are intentionally high-level enough to support repeated waves without becoming brittle one-off prompts.

# Architecture

## Layout

- `missions/` — mission repos under analysis (learner clones live here)
- `scripts/pr_archive/` — PR archive engine
- `scripts/workbench/cli.py` — workbench CLI connecting the repo registry and the engine
- `scripts/workbench/core/` — pipeline modules (intake, packets, memory, session, response, learner_state, response_contract, coach_run)
- `schemas/` — JSON schemas validated by `schema_validation.py`
- `docs/` — canonical documentation for agents
- `playbooks/` — PR learning pipeline guides
- `.claude/agents/` — Claude Code subagent definitions
- `.claude/commands/` — Claude Code slash commands
- `gemini-skills/` — Gemini CLI skill modules
- `skills/` — Codex/OpenAI skill modules
- `state/repos/<repo>/archive/` — collected PR SQLite DB
- `state/repos/<repo>/analysis/` — mission map
- `state/repos/<repo>/packets/` — topic/reviewer/compare/pr-report packets
- `state/repos/<repo>/contexts/` — coach focus, candidate interpretation, my-pr context
- `state/repos/<repo>/actions/` — `coach-run.json`, `coach-response.json`, next-action bundles
- `state/repos/<repo>/memory/` — `history.jsonl`, `summary.json`, `profile.json`
- `state/repos/<repo>/profiles/` — learner and reviewer profiles
- `state/cache/` — global cache
- `state/repo-registry.json` — registered mission repos

## Pipeline Order

1. **Repo intake** — resolve repo from path or registry, detect origin/upstream/branch/PR title
2. **Archive sync** — incremental PR collection into `archive/prs.sqlite3` (first-time bootstrap is a separate step)
3. **Evidence role classification** — `comment_classifier.py` labels review comments, review bodies, and issue comments
4. **Thread reconstruction** — `thread_builder.py` rebuilds mentor↔learner reply chains
5. **Mission map** — `mission_map.py` extracts mission hints, layer paths, retrieval terms
6. **Learner state assessment** — `learner_state.py` captures a direct-observation snapshot (branches, working copy, target PR, unresolved threads with `classification` + `learner_reactions`) into `contexts/learner-state.json`
7. **Session start** — `session.py` resolves intent/topic, builds focus, runs candidate interpretation
8. **Memory compute (Phase 1)** — `memory.compute_memory_update` produces history entry + summary + profile purely in memory
9. **Response synthesis** — `response.py` renders reference coach reply
10. **Response Contract pre-render** — `response_contract.py` computes `snapshot_block.markdown` (the canonical `## 상태 요약` block) and the `verification.thread_refs` / `stub_markdown` list from the learner-state snapshot, injected into `coach-run.json.response_contract` for AI sessions to copy verbatim
11. **Sequential commit (Phase 2)** — `coach_run.py` writes in order: history → coach-run.json → summary → profile

## Write Order Invariant

`coach-run.json` is the canonical first-read artifact and embeds the authoritative memory snapshot. Phase 2 writes `history.jsonl` first (so future sessions can recompute), then `coach-run.json` (so the canonical artifact is visible), then the memory sidecars. On failure the remaining writes are skipped and `execution_status=error` is recorded. On canonical write failure the payload falls back to `coach-run.error.json`. See [error-recovery.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/error-recovery.md).

## Principles

- Mission repos are cloned by the learner. The workbench never modifies them.
- All analysis artifacts live under `state/`. Nothing is written inside mission repos.
- Personal learning notes and artifacts are not committed to shared storage.
- The PR archive engine can run directly, but default operation goes through `bin/` commands.
- `coach-run` is not an answer engine. It produces interpretable artifacts; the agent synthesizes the learner-facing answer.
- The repo registry stores `path`, `upstream`, `track`, `mission`, `title_contains`, `branch_hint` so that collection commands have sensible defaults.

## Related Documents

- [capability-map.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/capability-map.md) — capability-level breakdown of modules
- [artifact-catalog.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/artifact-catalog.md) — artifact-level breakdown of state
- [agent-operating-contract.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/agent-operating-contract.md) — agent-facing operating rules

# Architecture

## Layout

- `missions/` — mission repos under analysis (learner clones live here)
- `scripts/pr_archive/` — PR archive engine
- `scripts/workbench/cli.py` — workbench CLI connecting the repo registry and the engine
- `scripts/workbench/core/` — pipeline modules (intake, packets, memory, session, response, learner_state, learner_memory, response_contract, intent_router, artifact_budget, cognitive_trigger, citation_verifier, coach_run)
- `scripts/learning/` — CS learning subsystem (RAG indexer/searcher, 4-dim scoring, profile_merge, drill engine, integration facade)
- `knowledge/cs/` — CS markdown corpus (indexed into `state/cs_rag/`)
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
- `state/repos/<repo>/actions/` — `coach-run.json` (canonical), `coach-response.json` (legacy peer-only reference), next-action bundles
- `state/repos/<repo>/contexts/cs-augmentation.json` — optional CS search sidecar with full document bodies (present only when `cs_search_mode ∈ {cheap, full}` and `cs_readiness.state="ready"`)
- `state/repos/<repo>/memory/` — `history.jsonl`, `summary.json`, `profile.json`, optional `drill-pending.json` (one open drill or review drill), optional `drill-history.jsonl` (append-only 4-dim results with spaced-review fields)
- `state/learner/` — cross-repo learner memory (`history.jsonl`, `profile.json`, `summary.json`, optional `pending_triggers.json` for self-assessment)
- `state/cs_rag/` — shared CS index (`manifest.json` + LanceDB `lance/`; legacy v2 also had `index.sqlite3`/`dense.npz`); gitignored, rebuilt by `bin/cs-index-build`
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
8. **Pre-augment phase** — `coach_run._pre_augment_phase`:
   a. `drill.load_pending` → `decrement_ttl`
   b. load cross-learner context from `state/learner/profile.json`
   c. expire learner-level pending cognitive triggers from `state/learner/pending_triggers.json`
   d. `intent_router.pre_decide(prompt, history, pending_drill, learner_state)` → `{pre_intent, cs_search_mode}` (mission-only turns skip the CS path entirely)
   e. `cs_readiness` check (lazy indexer import; `ready`/`missing`/`stale` never touches `execution_status`)
   f. `learning.integration.augment(learner_state, prompt, learning_points, coach_profile, cs_search_mode)` → compact `cs_augmentation` + `contexts/cs-augmentation.json` sidecar, including `verifier_hits` and `citation_paths`
   g. `drill.route_answer` + `scoring.score_pending_answer` when the prompt is answering an open pending drill
9. **Memory compute (Phase 1)** — `memory.compute_memory_update` runs after augment so the snapshot sees `cs_augmentation` / drill_result (backward-compatible flat fields retained)
10. **Unified profile + drill offer + cognitive trigger + finalize** — `profile_merge.unify` → `drill.build_review_offer_if_due(drill_history, pending)` → `drill.build_offer_if_due(unified_profile, pre_intent, pending)` when no review is due → `cognitive_trigger.select_cognitive_trigger(...)` when no drill offer is active → `intent_router.finalize(pre_intent, augment_result, drill_offer, drill_result)` → final `intent_decision.block_plan`
11. **Response synthesis** — `response.py` renders reference coach reply (legacy peer-only view)
12. **Response Contract pre-render** — `response_contract.py` computes `snapshot_block`, `verification`, `cs_block` (rendered view of `cs_augmentation` plus `grounding_check`), `drill_block`, `drill_result_block`, `cognitive_block`, and `follow_up_block`, each with an `applicability_hint` advising AI whether the block is primary/supporting/omit
13. **Artifact size budget** — `artifact_budget.enforce_budget(payload)` shrinks in a fixed ladder (snippets → drill_history → fallback top-K → reconciled lists) while never touching load-bearing fields (`execution_status`, `cs_readiness`, `intent_decision`, block markdowns)
14. **Sequential commit (Phase 2)** — `coach_run.py` writes in order: history → coach-run.json → sidecars → summary/profile → learner event hook → drill persistence → self-assessment pending trigger persistence

## Write Order Invariant

`coach-run.json` is the canonical first-read artifact and embeds the authoritative memory snapshot. Phase 2 writes `history.jsonl` first (so future sessions can recompute), then `coach-run.json` (so the canonical artifact is visible), then advisory sidecars and derived memory snapshots. Drill and self-assessment trigger persistence run only after the canonical write succeeds. On failure the remaining writes are skipped and `execution_status=error` is recorded. On canonical write failure the payload falls back to `coach-run.error.json`. See [error-recovery.md](../docs/error-recovery.md).

## Principles

- Mission repos are cloned by the learner. The workbench never modifies them.
- All analysis artifacts live under `state/`. Nothing is written inside mission repos.
- Personal learning notes and artifacts are not committed to shared storage.
- The PR archive engine can run directly, but default operation goes through `bin/` commands.
- `coach-run` is not an answer engine. It produces interpretable artifacts; the agent synthesizes the learner-facing answer.
- The repo registry stores `path`, `upstream`, `track`, `mission`, `title_contains`, `branch_hint` so that collection commands have sensible defaults.

## Related Documents

- [capability-map.md](../docs/capability-map.md) — capability-level breakdown of modules
- [artifact-catalog.md](../docs/artifact-catalog.md) — artifact-level breakdown of state
- [agent-operating-contract.md](../docs/agent-operating-contract.md) — agent-facing operating rules
- [learning-system-v4.md](../docs/learning-system-v4.md) — v4 cognitive trigger, self-assessment, review drill, and grounding contract

# CS Worker Fleets

This document defines the production worker topology for preparing the Woowacourse backend CS database.

There are three selectable fleet profiles:

- `quality`: default quality-repair system for category QA, primer-contract lint repair, link/anchor cleanup, RAG ranking regression work, index readiness, and release gating.
- `expansion`: bounded CS corpus growth system for learner-profile and Woowacourse Level 2 gaps, especially Spring and RoomEscape Admin prerequisites.
- `expansion60`: high-throughput corpus growth system for the same expansion goal, with narrower write scopes, separate README QA, and singleton RAG mutators to avoid 60-worker contention.

Use `bin/orchestrator fleet-start --profile quality`, `bin/orchestrator fleet-start --profile expansion`, or `bin/orchestrator fleet-start --profile expansion60`. Only one local supervisor is expected to run at a time.

## Queue Profile Isolation

Queue items carry a `fleet_profile` field:

- legacy items without `fleet_profile` are treated as `quality`
- workers claim only items for their selected profile
- worker-created `next_candidates` inherit the active fleet profile
- profile waves are written separately (`current-wave.json` for `quality`, `current-wave-expansion.json` for `expansion`, `current-wave-expansion60.json` for `expansion60`)

This prevents the expansion fleet from draining old QA-repair pending work. If switching profiles, stop the active fleet first and release stale leases before starting the next profile.

## Principles

- Treat Woowacourse as a mission-based backend learning path, not a generic CS encyclopedia.
- Prefer beginner-safe entrypoints before advanced deep dives.
- Repair existing beginner primer contracts before adding new content.
- Use the expansion fleet, not the quality fleet, when the explicit goal is new Beginner/Junior document growth.
- Keep authoring-lint, README return paths, retrieval anchors, signal rules, golden fixtures, and release gates owned by specialized workers.
- Use `write_scopes` instead of lane-level locking so independent workers can share a broad lane without editing the same ownership surface.
- Keep queue growth disabled for the quality fleet; workers may report follow-up gaps, but their `next_candidates` are not enqueued.
- Keep expansion queue growth bounded with lower per-lane pending caps and `fleet_profile=expansion` queue ownership.

## Quality Worker Groups

| Group | Count | Purpose |
|---|---:|---|
| QA | 21 | Repair category docs, primer contracts, anchors, return paths, follow-up ladders, and cross-category links. |
| RAG | 6 | Fix projection/JWT/transaction ranking regressions, signal rules, golden fixtures, and index readiness. |
| Ops | 3 | Control queue growth, run release gates, and prevent new quality debt from being batched. |

## Expansion Worker Groups

| Group | Count | Purpose |
|---|---:|---|
| Curriculum | 1 | Map learner-profile, current module, and Woowacourse Level 2/RoomEscape Admin prerequisites into concrete backlog gaps. |
| Content | 8 | Write bounded Beginner/Junior docs for Spring Core, RoomEscape Admin, persistence, Java/OOP, HTTP/Web, testing/layering, and algorithm/data-structure practice. |
| QA | 12 | Check beginner tone, symptom anchors, cross-category bridges, README registration, duplicate topics, and code density. |
| RAG | 6 | Lock targeted beginner queries, golden fixtures, and signal rules so new docs are actually retrievable. |
| Ops | 3 | Keep queue growth bounded, rebuild/check the index after churn, and run release gates. |

## Expansion60 Worker Groups

`expansion60` is not "60 writers". It is a higher-throughput pipeline with writers, QA, RAG, and ops scaled together.

`expansion` and `expansion60` are balance-aware profiles. Each worker prompt includes the current difficulty/category distribution and asks the worker to choose the appropriate document role instead of always creating another Beginner primer.

| Group | Count | Purpose |
|---|---:|---|
| Curriculum | 2 | Keep Level 2, RoomEscape Admin, learner-profile, and module-gap priorities explicit. |
| Content | 24 | Write focused Beginner/Junior docs across Spring, Network/Web, Database, Java, Algorithm/Data Structure, and Software Engineering. |
| QA | 22 | Review beginner scope, symptom anchors, cross-category bridges, duplicate taxonomy, README registration, and code density. |
| RAG | 8 | Evaluate targeted beginner queries, maintain the single signal-rules mutator and single golden-fixture mutator, and run router/index smoke checks. |
| Ops | 4 | Govern queue growth, watch write-scope contention, handle index readiness, and run release gates. |

The 60-worker profile intentionally splits broad content locks such as `expansion:content:spring` into narrower scopes such as `expansion60:content:spring:mvc-binding` and `expansion60:content:spring:security-admin`. Content workers do not own category README files; README registration is batched through QA workers to reduce merge churn.

## Profile Fields

Each worker profile in `scripts/workbench/core/orchestrator_workers.py` has:

- `name`: stable worker id.
- `lane`: broad queue lane to claim from.
- `role`: `curriculum`, `content`, `qa`, `rag`, or `ops` depending on the selected profile.
- `mode`: `expand`, `write`, `fix`, `report`, `script`, `queue`, or `ops`.
- `claim_tags`: optional task filter. Empty means the worker claims any task in its QA lane.
- `write_scopes`: lock keys used to prevent conflicting writes.
- `target_paths`: path ownership shown in the prompt.
- `quality_gates`: checks the worker must keep in mind.
- `can_enqueue`: whether worker `next_candidates` are accepted.

`quality` workers set `can_enqueue=false`. Content workers in `expansion` and `expansion60` set `can_enqueue=true` with lower pending caps so follow-up topics can be proposed without letting the queue run away.

## Locking Model

The orchestrator still stores queue items by lane, but workers are no longer blocked by lane alone. A worker can claim a task only when no other active lease has an overlapping `lease_write_scopes` value.

Examples:

- `runtime-qa-content-database` uses `qa:content:database`.
- `runtime-qa-primer-contract-database` uses the same scope, so both cannot repair database primer files at the same time.
- `runtime-rag-ranking-jwt` and `runtime-rag-ranking-projection` use separate ranking scopes, but `runtime-rag-signal-rules` owns the singleton `rag:signal_rules` surface.

## Operational Gates

- QA tasks should make the smallest patch that reduces a named failing contract.
- `next_candidates` are ignored for the quality fleet because `can_enqueue=false` on every quality profile.
- A Beginner primer is not ready until it satisfies the authoring contract: H1, `> 한 줄 요약`, exact difficulty, `관련 문서:` with at least three bullets, 8..15 lowercase `retrieval-anchor-keywords`, H2 bodies under 1600 characters, and final `## 한 줄 정리`.
- Expansion content is not ready until it fits the corpus balance target. If the category is still below the Beginner floor, prefer an entrypoint primer; if the category is already Beginner-saturated, prefer an Intermediate bridge, practice drill, comparison card, or targeted strengthening patch.
- New content summaries must name the document role: `entrypoint primer`, `bridge`, `practice drill`, `deep dive`, `playbook`, or `recovery note`.
- Golden fixtures and signal rules are singleton surfaces.
- Release is not ready until link checks, authoring lint, RAG unit/golden tests, and `bin/cs-index-build` are green.
- Expansion content is not ready until it is discoverable: README registration, non-duplicate topic choice, symptom-style anchors, and a targeted RAG query/golden candidate must be considered by the paired RAG/QA workers.
- In `expansion60`, only `expansion60-rag-signal-rules-mutator` may edit `scripts/learning/rag/signal_rules.py`, and only `expansion60-rag-golden-mutator` may edit `tests/fixtures/cs_rag_golden_queries.json`.
- In `expansion60`, content workers should write docs or strengthen existing docs, then leave README registration hints for README QA workers unless a README is explicitly in their target paths.

## Rollout

1. Drain the old fleet by writing `state/orchestrator/stop.request` and letting active leases finish.
2. Review the drained content changes and current failing quality gates.
3. Start the desired profile fleet with `bin/orchestrator fleet-start --profile quality`, `bin/orchestrator fleet-start --profile expansion`, or `bin/orchestrator fleet-start --profile expansion60`.
4. Check `bin/orchestrator fleet-status`; it should show the selected profile and the expected worker count.
5. Run a short soak first and inspect `ACTIVE_ERROR_WORKERS`, `blocked`, primer lint pass rate, and RAG regression failure count.
6. Rebuild the CS index only after corpus churn drops; otherwise the live index will immediately become stale again.

For expansion, prefer a pilot wave before a full run: start the expansion profile, inspect the first completed content items, run strict authoring lint, then allow the QA/RAG/Ops workers to drain the wave before committing.

For `expansion60`, require a stricter pilot before full operation:

1. Start `bin/orchestrator fleet-start --profile expansion60`.
2. Let the fleet run for one short soak window.
3. Continue only if `blocked == 0`, `waiting_write_scope` is below roughly 35%, strict authoring lint has no errors, and targeted RAG tests stay green.
4. If write-scope waiting dominates, reduce content concurrency first; do not add more broad QA workers.

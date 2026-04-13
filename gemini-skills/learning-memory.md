# Gemini Skill: Learning Memory

Use this module when long-term learning continuity matters.

## Focus

- `coach-run.json.memory` (authoritative embedded snapshot for the current session)
- `memory/profile.json` (next-session initial context)
- `memory/summary.json` (aggregate)
- Do not read `memory/history.jsonl` in full — it is unbounded.

## What to do

- prefer `weighted_learning_points` (recency-aware) over raw `top_learning_points`
- read each dominant/repeated point's `recency_status` (`active`, `cooling`, `dormant`)
- identify underexplored learning points
- decide whether to deepen or broaden

## Interpretation rules

- `recency_status=active` means the learner is currently engaged with the point.
- `recency_status=dormant` means the point is history, not a current concern.
- If `confidence=low`, downgrade memory claims and let current evidence dominate.
- If `coach-run.json.memory` disagrees with sidecar files, trust the embedded snapshot for the current session.

See `docs/memory-model.md` and `docs/error-recovery.md`.

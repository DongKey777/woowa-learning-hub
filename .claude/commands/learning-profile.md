Inspect the learner's accumulated learning profile and reflect it in the recommendation.

Use `$ARGUMENTS` as the learner's current question.

Default behavior:

1. Run or reuse `coach-run`.
2. Read `coach-run.json.memory` first (authoritative for the current session). Fall back to `memory/profile.json` and `memory/summary.json` only if the embedded snapshot is missing fields you need.
3. Use `weighted_learning_points` and each point's `recency_status` to decide what is currently active vs dormant.
4. Distinguish:
   - repeated learning points to deepen (prefer `recency_status=active`)
   - underexplored learning points to broaden
   - repeated points with `recency_status=dormant` — mention as history, not current priority
5. If `confidence=low`, downgrade memory claims and let the current question dominate.
6. Answer with concrete guidance for this session.

See `docs/memory-model.md` for interpretation rules.

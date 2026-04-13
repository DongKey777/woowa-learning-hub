Compare how other crews handled the learner's current mission question.

Use `$ARGUMENTS` as the learner question.

Default behavior:

1. Run or reuse `coach-run`.
2. Read `contexts/coach-candidate-interpretation.json`. Read `contexts/coach-focus.json` only if interpretation alone is ambiguous.
3. Organize the answer by learning point, not raw score.
4. For each recommended PR, explain:
   - what it is good for learning
   - which mentor review comment or thread supports that recommendation
   - prefer quotes from `mentor_comment_samples` and the last mentor turn in `thread_samples`
   - never cite `crew_response_samples` as mentor feedback
5. If a recommendation lacks a grounded mentor quote, do not make it the primary recommendation.

See `docs/evidence-roles.md` for role semantics.

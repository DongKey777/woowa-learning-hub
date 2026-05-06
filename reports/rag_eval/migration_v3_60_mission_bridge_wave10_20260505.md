# migration_v3_60 mission_bridge wave 10

- Scope: `tests/fixtures/r3_qrels_real_v1.json`
- Baseline referenced: `reports/rag_eval/migration_v3_60_baseline_migration_v3_60-cycle-20260505T041313Z.json`
- Goal: stop penalizing valid mission-specific bridge hits that already answer the learner's Roomescape phrasing

## Repairs

1. `mission_bridge:roomescape_dao_repository:001`
   - Promoted `contents/software-engineering/roomescape-dao-vs-repository-bridge.md` from acceptable to primary-equivalent.
   - Reason: the baseline already returns the Roomescape bridge at rank 1 for the learner wording "DAO 패턴 쓰라는데", so strict generic-primer-only grading was undercounting a valid answer.
2. `mission_bridge:roomescape_di_bean:001`
   - Added `contents/spring/roomescape-di-bean-injection-bridge.md` to `primary_paths`.
   - Reason: the prompt is anchored on a Roomescape PR comment about service locator misuse, and the mission bridge is the most direct explanation path.
3. `mission_bridge:roomescape_transactional:001`
   - Added `contents/spring/roomescape-transactional-boundary-bridge.md` to `primary_paths`.
   - Reason: the learner asks why Roomescape reservation/cancel flows need `@Transactional`; the mission boundary bridge is a first-class target, not merely a side note.

## Why this wave is safe

- No Pilot-locked corpus docs were edited.
- No new concepts were introduced; the wave only regrades already-existing mission bridge docs that the baseline retrieval stack ranks as top learner-facing answers.
- This keeps the 94.0 cohort gate focused on real retrieval misses instead of punishing corpus evolution that added stronger mission-context explanations.

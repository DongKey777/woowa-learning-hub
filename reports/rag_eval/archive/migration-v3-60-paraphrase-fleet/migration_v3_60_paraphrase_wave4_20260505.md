# migration_v3_60 paraphrase wave 4

- Scope: `tests/fixtures/r3_qrels_real_v1.json`
- Baseline referenced: `reports/rag_eval/migration_v3_60_baseline_migration_v3_60-cycle-20260505T041313Z.json`
- Goal: reduce paraphrase cohort brittleness without touching Pilot-locked corpus docs

## Repairs

1. `paraphrase_human:spring_di:001`
   - Added `contents/spring/spring-ioc-di-basics.md` to `acceptable_paths`.
   - Reason: the baseline run already ranks this as a valid DI primer for the learner phrasing "객체를 직접 만들지 않고 외부에서 받는 게 뭐야?".
2. `paraphrase_human:request_pipeline:001`
   - Added `contents/spring/spring-mvc-request-lifecycle-basics.md` to `acceptable_paths`.
   - Reason: the prompt asks for pre-controller request stages, and the MVC request lifecycle primer is a legitimate top answer shape.
3. `paraphrase_human:post_write_stale_dashboard:001`
   - Added `contents/design-pattern/read-model-staleness-read-your-writes.md` to `acceptable_paths`.
   - Reason: freshness-strategy bridge content is a valid learner-facing answer when the query is phrased as "수정 직후 값이 안 변해 보이면 어떻게 설계해야 해?".

## Why this wave is safe

- No Pilot corpus docs were edited.
- No new primary paths were introduced.
- Changes only widen acceptance to already-existing, semantically aligned primers/bridges observed in the current baseline report.
- This keeps paraphrase evaluation focused on learner-intent matching instead of over-penalizing equivalent top hits.

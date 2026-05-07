# R3 Pilot 50 Docs Selection (Phase 4 input, 2026-05-02)

> **Status note (2026-05-05)**: this file is the historical Phase 4 selection memo, not the live lock source. The enforceable Pilot lock list now lives in `config/migration_v3/locked_pilot_paths.json` and currently freezes 69 paths. Migration workers should treat the JSON manifest as canonical when deciding whether a path is writable.

> **Purpose**: enumerate the 50 docs that get migrated to v3 frontmatter contract first (Phase 4), serving as the test bed for the Real qrel suite (Phase 3) measurement in Phase 6 Pilot baseline.
>
> **Selection rationale**: cover (a) the 10 Korean hard-regression failure cohort, (b) confusable concept pairs the failure cohort + qrel suite stresses, (c) high-frequency primer docs the learner population queries most, (d) symptom_router + chooser + mission_bridge docs that need *creation* (Wave C overlap with Pilot to seed the new doc roles).
>
> **Methodology**: every selected doc has a corresponding query in `tests/fixtures/r3_qrels_real_v0_seed.json` or is a known canonical primer for an under-covered concept. Path verification confirmed all "exists today" docs exist in `knowledge/cs/contents/`.

> **Guardrail note**: because the lock manifest evolved after this memo was written, the "Selected 50 docs" list below should be read as baseline planning context only. For QA, migration, and lane-worker scope checks, use the JSON manifest rather than this memo's deduplicated list.

---

## Summary

| Bucket | Count | Status |
|---|---|---|
| Korean hard-regression cohort docs | 10 | exists today (some need v3 fields) |
| Confusable pair docs | 16 | exists today (DI/locator, Factory/Strategy, MVCC/lock, etc.) |
| Mission bridge docs | 10 | **NEW** (created in Wave C overlap with Pilot) |
| Symptom router docs | 8 | mix of exists + NEW |
| Beginner primer reinforcement | 6 | exists today |
| **Total** | **50** | |

## Lock Drift Snapshot (2026-05-05)

- Current Pilot lock enforcement comes from `config/migration_v3/locked_pilot_paths.json`, which freezes **69** corpus paths.
- This memo currently references **56 unique** `knowledge/cs/contents/**` paths across bucket tables, examples, and the final checklist.
- Of those 56 memo-referenced paths, **32** are also in the live lock manifest.
- The remaining memo-only references are planning artifacts, not writable authority. Representative examples: `knowledge/cs/contents/database/ghost-reads-mixed-routing-write-fence-tokens.md`, `knowledge/cs/contents/database/compare-and-swap-vs-pessimistic-locks.md`, `knowledge/cs/contents/design-pattern/injected-registry-vs-service-locator-checklist.md`.
- The live manifest also freezes newer baseline-critical docs that are not enumerated in this historical memo. Representative examples: `knowledge/cs/contents/database/read-your-writes-session-pinning.md`, `knowledge/cs/contents/database/transaction-basics.md`, `knowledge/cs/contents/design-pattern/registry-primer-lookup-table-resolver-router-service-locator.md`.

Worker implication: lane workers should use this memo for Phase 4 selection context only, then consult the JSON manifest for every write/no-write decision so Pilot baseline guards stay deterministic.

## Wave 3 Guard Report (2026-05-07)

- Rechecked the historical memo against the live manifest before the curriculum `pilot-lock` wave. The memo still serves as planning context only; the JSON manifest remains the only writable-authority source for lock decisions.
- A raw path scrape finds **57** `knowledge/cs/contents/**`-shaped references in this memo, but **1** is the template placeholder `knowledge/cs/contents/<category>/<slug>.md`. The concrete-doc count therefore stays **56**, matching the snapshot above.
- Concrete drift remains unchanged: **32** memo references overlap the live lock list, **24** are memo-only planning references, and **37** live locked paths are absent from the memo because the manifest expanded after Phase 4 selection.
- Retrieval/ops implication: any worker or script that tries to infer Pilot lock status from this memo can silently miss 37 baseline-critical docs. That is the failure mode this lane is guarding against.

Wave 3 decision rule:
1. Check `config/migration_v3/locked_pilot_paths.json` first for every candidate path.
2. Treat any memo-only path as non-authoritative until the JSON manifest says otherwise.
3. If a queue item cites this memo as the reason to edit a locked corpus doc, reject the write and return a lock-conflict summary instead of proposing the edit.

## Wave 4 Guard Report (2026-05-07)

- Tightened the counting language for this memo so lock-audit tooling does not confuse raw mention volume with unique writable candidates.
- The memo contains **111 raw path-shaped mentions** once repeated examples and duplicated bucket references are counted literally.
- After normalizing `contents/...` to `knowledge/cs/contents/...` and deduplicating, that drops to **57 unique references**.
- Of those unique references, **1** is still the non-authoritative template placeholder `knowledge/cs/contents/<category>/<slug>.md`, leaving **56 concrete doc paths** for drift comparison.
- Guard implication: use raw-counts only for audit/debug output, and use normalized unique concrete counts for lock drift checks against the JSON manifest.

Wave 4 reporting rule:
1. When citing memo coverage, spell out whether the number is `raw`, `unique`, or `unique concrete`.
2. Keep `config/migration_v3/locked_pilot_paths.json` as the only authoritative lock source even when the memo count looks higher.
3. If a future guard script surfaces `57` without a qualifier, treat that as ambiguous and fix the report before relying on it for queue decisions.

---

## Bucket A — Korean hard-regression cohort (10 docs, all exist)

These are the canonical doc the failure cohort queries actually want. Migrating these to v3 frontmatter ensures the v3 lexical sidecar + dense embedding + reranker stack can find them on Korean shortform queries.

| # | Doc path | Concept | failure_query_id |
|---|---|---|---|
| 1 | `contents/spring/spring-bean-lifecycle-basics.md` | spring/bean | `beginner_bean_korean_shortform_lockin` |
| 2 | `contents/database/connection-pool-basics.md` | database/connection-pool | `beginner_database_connection_pool_primer` |
| 3 | `contents/database/mvcc-snapshot-vs-locking-read-portability-note.md` | database/mvcc | `beginner_mvcc_korean_why_needed_lockin`, `mvcc_beginner_shortform_before_internals` |
| 4 | `contents/database/cache-replica-split-read-inconsistency.md` | database/replica-lag | `generic_crud_korean_list_read_but_update_fails`, `projection_freshness_symptom_only_detail_updated_list_card_stale` |
| 5 | `contents/database/ghost-reads-mixed-routing-write-fence-tokens.md` | database/read-after-write | `generic_crud_korean_update_vs_read_api_difference` |
| 6 | `contents/operating-system/io-uring-fdinfo-pbuf-status-enobufs-reconciliation-playbook.md` | operating-system/io-uring | `io_uring_intro_before_sq_cq` |
| 7 | `contents/database/lock-timeout-blocker-first-check-mini-card.md` | database/lock-timeout | `projection_freshness_cutover_safety_shortform_anchor` (related triage) |
| 8 | `contents/spring/spring-bean-di-basics.md` | spring/di | `spring_mvc_shortform_korean_alias_beginner_primer` (DI primer used as proxy until Spring MVC primer migrated) |
| 9 | `contents/database/transaction-isolation-basics.md` | database/transaction-isolation | `mvcc_beginner_shortform_before_internals` (acceptable secondary) |
| 10 | `contents/database/lock-basics.md` | database/lock | broad — used as acceptable for many lock-related symptom queries |

Pilot frontmatter pattern (per doc):
```yaml
schema_version: 3
concept_id: spring/bean
canonical: true
category: spring
doc_role: primer
level: beginner
language: ko
source_priority: 92
aliases:
  - Bean
  - Spring Bean
  - 스프링 빈
  - 빈
  - bean container
symptoms: []        # primer; not a symptom router
intents: [definition]
prerequisites: []
next_docs: [spring/di]
linked_paths: []
confusable_with: []
forbidden_neighbors:
  - contents/spring/spring-beanfactorypostprocessor-vs-beanpostprocessor-lifecycle.md
  - contents/spring/spring-bean-definition-registry-postprocessor-import-registrar.md
expected_queries:
  - 빈이 뭐야?
  - Spring Bean 처음 배우는데
  - 스프링이 객체를 어떻게 만들어?
contextual_chunk_prefix: |
  이 문서는 Spring 학습자가 "객체 컨테이너"라는 개념을 처음 만났을 때
  Bean이 무엇인지 / Spring이 객체 라이프사이클을 어떻게 관리하는지를
  설명한다.
```

---

## Bucket B — Confusable pair docs (16 docs, exists)

Confusable disambiguation is the strongest test of paraphrase-robust retrieval. Each pair gets *both* docs migrated so the qrel suite can verify routing.

### B1. DI vs Service Locator (4 docs)
1. `contents/spring/spring-bean-di-basics.md` (already in A8)
2. `contents/spring/ioc-di-container.md`
3. `contents/design-pattern/injected-registry-vs-service-locator-checklist.md`
4. `contents/design-pattern/object-oriented-design-pattern-basics.md` (forbidden_neighbor for "DI" queries — must not be primary)

### B2. Factory vs Strategy vs DI Container (4 docs)
5. `contents/design-pattern/factory-basics.md`
6. `contents/design-pattern/factory-vs-di-container-wiring.md`
7. `contents/design-pattern/bridge-strategy-vs-factory-runtime-selection.md`
8. `contents/design-pattern/constructor-vs-static-factory-vs-factory-pattern.md`

### B3. MVCC vs Lock vs Isolation (3 docs; A3, A9, A10 already cover these — list for completeness)
- B3.1 covered by A3 (`mvcc-snapshot-vs-locking-read-portability-note.md`)
- B3.2 covered by A10 (`lock-basics.md`)
- B3.3 covered by A9 (`transaction-isolation-basics.md`)

### B4. Repository vs DAO (2 docs)
9. `contents/software-engineering/repository-interface-contract-primer.md`
10. `contents/software-engineering/repository-dao-entity.md`

### B5. Deadlock vs Lock Timeout (1 doc; lock-timeout-blocker-first-check-mini-card already in A7)
11. `contents/database/deadlock-vs-lock-wait-timeout-primer.md`

### B6. CAS vs Pessimistic Lock (1 doc)
12. `contents/database/compare-and-swap-vs-pessimistic-locks.md`

### B7. Static factory vs Factory pattern vs Constructor (1 doc; constructor-vs-static-factory already in B2-8)

### B8. Spring transactional (2 docs)
13. `contents/spring/spring-transactional-basics.md`
14. `contents/database/cannotacquirelockexception-40001-insert-if-absent-faq.md`

### B9. Cookie/auth (2 docs)
15. `contents/security/cookie-failure-three-way-splitter.md`
16. `contents/security/duplicate-cookie-name-shadowing.md`

---

## Bucket C — Mission bridge docs (10 NEW, Wave C overlap with Pilot)

These docs do not exist today; they are *created* during Pilot Phase 4 to seed the `mission_bridge` cohort. Each links a Woowa mission concept to a CS concept.

| # | New doc path | mission_id | concept_id |
|---|---|---|---|
| 17 | `contents/software-engineering/roomescape-dao-vs-repository-bridge.md` | missions/roomescape | software-engineering/dao-vs-repository |
| 18 | `contents/spring/roomescape-di-bean-injection-bridge.md` | missions/roomescape | spring/di |
| 19 | `contents/spring/roomescape-transactional-boundary-bridge.md` | missions/roomescape | spring/transactional |
| 20 | `contents/database/roomescape-reservation-concurrency-bridge.md` | missions/roomescape | database/lock |
| 21 | `contents/design-pattern/roomescape-strategy-vs-factory-bridge.md` | missions/roomescape | design-pattern/strategy |
| 22 | `contents/design-pattern/lotto-static-factory-bridge.md` | missions/lotto | design-pattern/static-factory-method |
| 23 | `contents/design-pattern/lotto-strategy-rank-decision-bridge.md` | missions/lotto | design-pattern/strategy |
| 24 | `contents/software-engineering/lotto-domain-invariant-bridge.md` | missions/lotto | software-engineering/domain-invariants |
| 25 | `contents/spring/baseball-mvc-controller-binding-bridge.md` | missions/baseball | spring/mvc |
| 26 | `contents/network/shopping-cart-rate-limit-bridge.md` | missions/shopping-cart | network/rate-limiting |

Authoring pattern (per mission_bridge doc):

```yaml
schema_version: 3
concept_id: <category>/<bridge-slug>
canonical: false              # the canonical doc for the CS concept is its primer
category: <derived from path>
doc_role: mission_bridge
level: beginner               # always beginner (mission learners are early-stage)
language: ko
source_priority: 78           # below canonical primer (90+) but high enough to surface
mission_ids: [missions/<mission-slug>]
review_feedback_tags: [<tag1>, <tag2>]   # mined from state/repos/<mission-repo>/packets/topic-*.json
aliases: [...]                # mission-specific terminology + CS concept aliases
symptoms: []                  # not a symptom router
intents: [mission_bridge]
prerequisites:
  - <linked CS concept primer>
next_docs:
  - <linked CS concept deep_dive>
linked_paths:
  - contents/<linked-cs-primer-path>
confusable_with: []
forbidden_neighbors: []
expected_queries:
  - "{mission} 미션에서 {concept} 어떻게 적용해?"
  - "{mission} PR에서 멘토가 {feedback_tag} 지적했어"
contextual_chunk_prefix: |
  이 문서는 {mission} 미션 학습자가 PR 코칭 중 {concept}와 미션 코드를
  연결할 때 참고하는 brief 가이드다. CS 원리는 {linked_primer}에 있고,
  본 문서는 미션 맥락만 한 단계 전개한다.
```

---

## Bucket D — Symptom router docs (8 docs; mix of exists + NEW)

| # | Path | Status | Symptoms |
|---|---|---|---|
| 27 | `contents/database/cache-replica-split-read-inconsistency.md` | EXISTS (already in A4) | stale list / save-then-empty |
| 28 | `contents/database/lock-timeout-blocker-first-check-mini-card.md` | EXISTS (already in A7) | lock_timeout outage |
| 29 | `contents/security/cookie-failure-three-way-splitter.md` | EXISTS (already in B9-15) | cookie loop |
| 30 | `contents/database/spring-cannotacquirelockexception-root-sql-code-card.md` | EXISTS | exception → root SQL code |
| 31 | `contents/database/deadlock-case-study.md` | EXISTS | deadlock after index/lock-order change |
| 32 | `contents/security/403-after-role-change-symptom-router.md` | **NEW** | 403 after role change |
| 33 | `contents/spring/spring-404-405-vs-bean-wiring-confusion-card.md` | EXISTS | controller 404/405 vs Bean wiring |
| 34 | `contents/database/connection-pool-starvation-symptom-router.md` | **NEW** | connection pool starvation |

Symptom router pattern (per NEW doc):

```yaml
schema_version: 3
concept_id: <cat>/<symptom-slug>
canonical: false
category: <cat>
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
aliases: [...]
symptoms:
  - 사용자에게 보이는 증상 1
  - 사용자에게 보이는 증상 2
  - 사용자에게 보이는 증상 3
intents: [symptom, troubleshooting]
linked_paths:
  - contents/<cause-doc-1>
  - contents/<cause-doc-2>
expected_queries:
  - "<symptom phrase 1>"
  - "<symptom phrase 2>"
contextual_chunk_prefix: |
  이 문서는 {symptom} 증상이 보일 때 *원인 후보를 어떻게 갈래로 나눌지*
  설명한다. 각 갈래의 정밀 진단/해결은 linked_paths의 cause doc 참조.
```

---

## Bucket E — Beginner primer reinforcement (6 docs; exists)

Frequent learner first-contact docs. v3 migration improves their Korean alias + contextual prefix coverage.

35. `contents/network/latency-bandwidth-throughput-basics.md`
36. `contents/operating-system/memory-management-basics.md`
37. `contents/operating-system/interrupt-basics.md`
38. `contents/design-pattern/factory-basics.md` (already in B2-5)
39. `contents/design-pattern/factory.md`
40. `contents/spring/jpa-dirty-checking-version-strategy.md`

---

## Selected 50 docs (deduplicated, final list)

After dedup across buckets:

```
A1.  contents/spring/spring-bean-lifecycle-basics.md
A2.  contents/database/connection-pool-basics.md
A3.  contents/database/mvcc-snapshot-vs-locking-read-portability-note.md
A4.  contents/database/cache-replica-split-read-inconsistency.md
A5.  contents/database/ghost-reads-mixed-routing-write-fence-tokens.md
A6.  contents/operating-system/io-uring-fdinfo-pbuf-status-enobufs-reconciliation-playbook.md
A7.  contents/database/lock-timeout-blocker-first-check-mini-card.md
A8.  contents/spring/spring-bean-di-basics.md
A9.  contents/database/transaction-isolation-basics.md
A10. contents/database/lock-basics.md
B1.  contents/spring/ioc-di-container.md
B2.  contents/design-pattern/injected-registry-vs-service-locator-checklist.md
B3.  contents/design-pattern/object-oriented-design-pattern-basics.md
B4.  contents/design-pattern/factory-vs-di-container-wiring.md
B5.  contents/design-pattern/bridge-strategy-vs-factory-runtime-selection.md
B6.  contents/design-pattern/constructor-vs-static-factory-vs-factory-pattern.md
B7.  contents/software-engineering/repository-interface-contract-primer.md
B8.  contents/software-engineering/repository-dao-entity.md
B9.  contents/database/deadlock-vs-lock-wait-timeout-primer.md
B10. contents/database/compare-and-swap-vs-pessimistic-locks.md
B11. contents/spring/spring-transactional-basics.md
B12. contents/database/cannotacquirelockexception-40001-insert-if-absent-faq.md
B13. contents/security/cookie-failure-three-way-splitter.md
B14. contents/security/duplicate-cookie-name-shadowing.md
B15. contents/design-pattern/factory-basics.md
B16. contents/design-pattern/factory.md
C1.  contents/software-engineering/roomescape-dao-vs-repository-bridge.md       (NEW)
C2.  contents/spring/roomescape-di-bean-injection-bridge.md                     (NEW)
C3.  contents/spring/roomescape-transactional-boundary-bridge.md                (NEW)
C4.  contents/database/roomescape-reservation-concurrency-bridge.md             (NEW)
C5.  contents/design-pattern/roomescape-strategy-vs-factory-bridge.md           (NEW)
C6.  contents/design-pattern/lotto-static-factory-bridge.md                     (NEW)
C7.  contents/design-pattern/lotto-strategy-rank-decision-bridge.md             (NEW)
C8.  contents/software-engineering/lotto-domain-invariant-bridge.md             (NEW)
C9.  contents/spring/baseball-mvc-controller-binding-bridge.md                  (NEW)
C10. contents/network/shopping-cart-rate-limit-bridge.md                        (NEW)
D1.  contents/database/spring-cannotacquirelockexception-root-sql-code-card.md
D2.  contents/database/deadlock-case-study.md
D3.  contents/security/403-after-role-change-symptom-router.md                  (NEW)
D4.  contents/spring/spring-404-405-vs-bean-wiring-confusion-card.md
D5.  contents/database/connection-pool-starvation-symptom-router.md             (NEW)
E1.  contents/network/latency-bandwidth-throughput-basics.md
E2.  contents/operating-system/memory-management-basics.md
E3.  contents/operating-system/interrupt-basics.md
E4.  contents/spring/jpa-dirty-checking-version-strategy.md
```

44 docs listed. Add to reach 50:

```
+ contents/spring/spring-bean-naming-qualifier-rename-pitfalls-primer.md
+ contents/database/idempotent-transaction-retry-envelopes.md
+ contents/database/connection-pool-transaction-propagation-bulk-write.md
+ contents/security/host-cookie-migration-primer.md
+ contents/operating-system/page-replacement-clock-vs-lru.md
+ contents/spring/spring-async-mvc-streaming-observability-playbook.md
```

= **50 docs total**.

Of these:
- **38 docs exist today** — frontmatter v3 migration only (text body untouched, except retrieval-anchor-keywords inline → aliases field).
- **12 docs are NEW** (10 mission_bridge + 2 symptom_router) — authored fresh during Pilot Phase 4.

---

## Phase 4 execution plan (per doc)

For each existing doc:
1. Read body. Identify doc_role (primer / bridge / deep_dive / playbook / chooser / symptom_router / drill).
2. Extract aliases from existing `retrieval-anchor-keywords:` inline metadata + body anchor sections.
3. Author `expected_queries` (5-10 queries that paraphrase the doc's content).
4. Verify aliases ⊥ expected_queries set disjointness.
5. Write frontmatter with all required + applicable optional fields.
6. Run `corpus_lint --strict-v3` (after Phase 5 lint extension); blocking errors must be fixed.
7. Optional: per-doc `contextual_chunk_prefix` if body has clear single context.
8. Mark doc as `schema_version: 3` migration done.
9. Update `knowledge/cs/catalog/concepts.v3.json` with new fields.

For each NEW doc:
1. Author body (~600-1500 words; brief concise primer/bridge/router style).
2. Write frontmatter.
3. Steps 4-9 same as above.

After all 50 docs migrated:
1. RunPod L40S build (Phase 5 system implementation done) → Pilot artifact `r3-pilot-v3-<timestamp>`.
2. Phase 6 measurement: Real qrel suite × R3 fixed backend × Pilot artifact.
3. Per-cohort metrics → calibration of cutover gates.

---

## Verification

- All 38 "exists today" paths verified to exist by `find knowledge/cs/contents -name "*.md"` enumeration.
- All 12 NEW paths follow the corpus path pattern `^contents/<category>/<slug>.md$` (verified by JSON schema regex).
- All 26 paths cited in seed qrels (`r3_qrels_real_v0_seed.json`) are a subset of these 50 (only paraphrase / confusable / symptom queries; mission_bridge / corpus_gap_probe / forbidden_neighbor cohorts use additional paths).
- Frontmatter v3 schema (`tests/fixtures/r3_corpus_v3_schema.json`) validates the planned shape; 37 schema unit tests passing.

---

## References

- Master plan: `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md`
- System spec: `docs/worklogs/rag-r3-system-spec-v1.md`
- Corpus contract: `docs/worklogs/rag-r3-corpus-v3-contract.md`
- Real qrel schema: `tests/fixtures/r3_qrels_schema.json`
- Seed qrels: `tests/fixtures/r3_qrels_real_v0_seed.json`
- Failed cohort source: `reports/rag_eval/archive/2026-05-02-circular-leak-baseline/next_lance_v3_holdout_20260501T1700Z.json` `regression_summary.failed_query_ids`

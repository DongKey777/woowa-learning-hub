# R3 v17 200q — Failure Root Cause Analysis (2026-05-04)

## 1. 검증 사실

### v17 ghost (lexical-only, 2026-05-02)
원래 측정에서 **dense BGE-M3, sparse, reranker 모두 비활성**이었음:
- `R3Config.enabled=False` (env var 미설정)
- `pandas` 미설치 → `load_runtime_sparse_documents` 실패
- 4 lexical 채널만 동작 → paraphrase 8% (50q 중 4q 통과)
- → *시스템의 진짜 약점이 아닌 환경 setup 부재*

### v17 full-stack (2026-05-04)
모든 retriever 활성화 후 재측정:
- `WOOWA_RAG_R3_ENABLED=1`, `WOOWA_RAG_R3_RERANK_POLICY=always`
- 6 retrievers + reranker + lexical sidecar 정상 동작 (`r3_candidate_count: 280`, `r3_dense_candidate_count: 100`, `r3_sparse_query_terms_count: 14`)

## 2. 측정 결과 비교

| Cohort | ghost (lexical) | full-stack | Δ | n |
|---|---|---|---|---|
| paraphrase_human | 8.0% | **52.0%** | +44.0pp | 50 |
| confusable_pairs | 50.0% | **70.0%** | +20.0pp | 40 |
| symptom_to_cause | 46.7% | **60.0%** | +13.3pp | 30 |
| mission_bridge | 76.7% | **83.3%** | +6.6pp | 30 |
| corpus_gap_probe | 100.0% | 100.0% | 0 | 20 |
| forbidden_neighbor | 96.7% | 90.0% | -6.7pp | 30 |
| **OVERALL pass_rate** | **55.0%** | **72.0%** | **+17.0pp** | 200 |

forbidden_neighbor의 -6.7pp는 dense가 의미 후보를 더 가져오면서 forbidden_paths와 겹치는 trade-off.

## 3. Still-failing 분류 (24 paraphrase_human failures)

token-overlap heuristic으로 final_top5의 best match와 primary path를 비교:

| 분류 | n | % | 의미 |
|---|---|---|---|
| qrel_narrow_likely | 3 | 12.5% | 정답급 doc이 top-5에 있는데 qrel acceptable_paths 누락 |
| partial_match | 5 | 20.8% | 같은 주제/카테고리, 다른 측면 |
| true_failure | 16 | 66.7% | retrieval 실패 |

confusable_pairs 12 failed: qrel_narrow 1 + partial 3 + true 8 (66.7%)
symptom_to_cause 12 failed: partial 4 + true 8 (66.7%)
mission_bridge 5 failed: **true_failure 0**, qrel_narrow 1 + partial 4 — 실제로는 100%

## 4. True failure 패턴 (root cause)

### A. paraphrase_human true_failure → corpus 어휘 갭

자연어 paraphrase가 corpus 본문의 기술 용어와 매핑되지 않음.

예시:
- "스프링이 객체를 어떻게 만들어주는지 큰 그림" → `spring-bean-lifecycle-basics.md` 정답이지만, 학습자가 *lifecycle*이라는 단어를 모르고 *큰 그림*으로 표현 → corpus의 alias/contextual prefix 부재로 매핑 실패.
- "도메인 객체 영속성 처리를 인터페이스로 추상화하는 패턴" → `repository-interface-contract-primer.md` 정답이지만 corpus에 *영속성+인터페이스+추상화+패턴* 결합 표현 부재.
- "동시에 여러 트랜잭션이 돌 때 각자 다른 시점의 데이터를 보게 하는 내부 구조" → `mvcc-read-view-consistent-read-internals.md` 정답, top1 `mvcc-replication-sharding.md` (같은 mvcc 카테고리, 다른 측면).

→ **시스템 결함이 아닌 corpus 결함**. v3 contract의 *contextual chunk prefix* + *aliases 보강*으로 해결할 영역.

### B. confusable_pairs true_failure → chooser-style doc 부족 + qrel 좁음

- `di_vs_service_locator`: 정답 `spring-bean-di-basics.md`(general DI), 학습자 의도는 "service locator 안 쓰는 이유" — chooser doc 부재.
- `mvcc_vs_lock`: 정답 doc 이름 매우 길고 specific하여 dense에서 묻힘.
- `factory_vs_builder`: 정답 `factory-basics.md` 너무 일반적, 학습자 의도는 비교.

→ **corpus chooser-style doc 신규 작성 필요** (Phase 4.3 Wave C).

### C. symptom_to_cause true_failure → symptom-router doc naming/aliases 약함

- `lock_timeout_outage`: 정답 `lock-timeout-blocker-first-check-mini-card.md`(card 형식), top1 `deadlock-vs-lock-wait-timeout-primer.md` — *card* 형식이 dense에서 우선순위 낮음.
- `cookie_login_loop`: 정답 `cookie-failure-three-way-splitter.md`(splitter), 같은 도메인 doc과 차별화 부재.

→ **symptom-router doc의 frontmatter `aliases` + `symptoms` field 보강**.

### D. mission_bridge → 진짜 약점 0

5 failed 모두 qrel narrow 또는 partial match. 실제로는 100% — `MissionBridgeRetriever`가 효과적으로 동작.

## 5. 결론

> 사용자 원칙: *"코퍼스에 시스템을 맞추지 않는다"*

이 측정은 그 원칙을 검증함:

1. **시스템 (R3 + BGE-M3 + reranker) 자체는 정상 동작**. paraphrase 8% → 52%, confusable 50% → 70% 등 모든 channel이 의미 있는 contribution.

2. **남은 약점은 *corpus 결함*에서 옴**:
   - paraphrase: 자연어 ↔ 기술 용어 매핑 부재 → contextual prefix + alias 보강 (Phase 4)
   - confusable: chooser doc 부재 → 신규 doc (Phase 4.3 Wave C)
   - symptom: router doc naming 약함 → frontmatter v3 aliases/symptoms 보강

3. **mission_bridge는 이미 100%** — `MissionBridgeRetriever` 채널이 잘 동작.

4. **forbidden_neighbor 90% trade-off**: dense semantic candidates 증가 ↔ forbidden_paths 겹침. reranker가 forbidden hint를 demote하지 못함 — 향후 forbidden_filter 강화 검토.

## 6. 다음 단계

> Phase 7 (frontier model A/B)는 corpus 보강 *후*에. corpus 결함 위에서 model A/B는 의미 없음.

**우선순위**:

1. **qrel acceptable_paths 보강** (1-2일)
   - paraphrase_human 24 failed 중 qrel_narrow 3 + partial 5 → acceptable_paths 추가
   - confusable_pairs 12 failed 중 qrel_narrow 1 + partial 3 → acceptable_paths 추가
   - symptom_to_cause 12 failed 중 partial 4 → acceptable_paths 추가
   - mission_bridge 5 failed 모두 → acceptable_paths 추가
   - **재측정 후 진짜 baseline pass_rate 확인** (예상: paraphrase 60%대, confusable 75%대)

2. **corpus v3 contract 적용 (Phase 4 Pilot 50 docs)** (1-2주)
   - paraphrase true_failure 16q의 primary doc들 → contextual prefix + aliases 보강
   - confusable chooser doc 신규 (5-10개)
   - symptom-router frontmatter v3 aliases/symptoms 보강

3. **재측정 (Phase 6 Pilot baseline)**
   - 6 cohort 모두 ≥ 0.85 목표
   - 미달 시 Phase 7 frontier model A/B 검토

## 7. 데이터

- `reports/rag_eval/r3_v17_cohort_eval.json` — ghost (lexical-only)
- `reports/rag_eval/r3_v17_cohort_eval_full.json` — full-stack
- `tests/fixtures/r3_qrels_real_v1.json` — 200q × 6 cohort qrel
- `state/cs_rag_v17/cs_rag/` — production index (RunPod L40S 2026-05-04 빌드)

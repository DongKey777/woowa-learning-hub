---
schema_version: 3
title: 이벤트는 발행됐는데 리스너가 안 돌아요 원인 라우터
concept_id: spring/event-listener-not-firing-cause-router
canonical: false
category: spring
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
mission_ids:
  - missions/shopping-cart
review_feedback_tags:
  - event-listener-not-firing
  - transaction-phase-mismatch
  - async-listener-hidden-failure
aliases:
  - 이벤트 발행했는데 리스너 안 돎
  - 스프링 이벤트 리스너 안 타요
  - transactionaleventlistener 안 도는 증상
  - after commit 리스너 미실행
  - 발행은 됐는데 listener 반응 없음
  - eventlistener가 조용히 안 뜸
symptoms:
  - publishEvent는 호출됐는데 @EventListener나 @TransactionalEventListener 로그가 전혀 안 보여요
  - AFTER_COMMIT 리스너를 붙였는데 테스트나 스케줄러 경로에서는 반응하지 않아요
  - 비동기 이벤트로 바꾼 뒤 호출자는 성공처럼 끝나는데 실제 후속 작업은 실행되지 않은 것 같아요
  - 이벤트는 발행된 것 같은데 어떤 요청에서는 리스너가 돌고 어떤 요청에서는 조용히 빠져요
intents:
  - symptom
  - troubleshooting
prerequisites:
  - spring/transactional-basics
  - software-engineering/service-layer-basics
next_docs:
  - spring/post-commit-side-effect-routing-decision-guide
  - spring/async-looks-synchronous-cause-router
  - spring/shopping-cart-order-complete-follow-up-missing-cause-router
linked_paths:
  - contents/spring/spring-transactionaleventlistener-fallbackexecution-no-transaction-boundaries.md
  - contents/spring/spring-after-commit-rollback-slice-test-mini-card.md
  - contents/spring/spring-eventlistener-ordering-async-traps.md
  - contents/spring/spring-applicationeventmulticaster-internals.md
  - contents/spring/spring-eventlistener-transaction-phase-outbox.md
  - contents/spring/spring-transactional-async-composition-traps.md
confusable_with:
  - spring/post-commit-side-effect-routing-decision-guide
  - spring/async-looks-synchronous-cause-router
  - spring/shopping-cart-order-complete-follow-up-missing-cause-router
forbidden_neighbors: []
expected_queries:
  - Spring에서 publishEvent는 탔는데 왜 이벤트 리스너 로그가 하나도 안 찍히는지 어디부터 나눠 봐야 해?
  - '@TransactionalEventListener(AFTER_COMMIT)를 붙였는데 테스트에서는 안 도는 이유를 증상 기준으로 설명해줘'
  - 스케줄러나 비동기 경로에서만 listener가 조용히 안 실행될 때 무엇을 먼저 의심해야 해?
  - 이벤트 발행 호출은 성공인데 후속 작업이 실제로 빠졌다면 트랜잭션 phase 문제와 async 실패를 어떻게 가를까?
  - 어떤 요청에서는 이벤트 리스너가 돌고 어떤 요청에서는 안 도는 현상을 Spring에서 어떻게 분기해서 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Spring에서 publishEvent 호출은 보이는데 listener 로그가 없거나,
  AFTER_COMMIT 리스너가 테스트·스케줄러·비동기 경로에서 조용히 안 도는
  증상을 원인으로 나누는 symptom_router다. 트랜잭션 없는 발행,
  rollback 기반 테스트, async executor 뒤 숨은 실패, multicaster 전달
  전략 차이 때문에 "이벤트는 발행된 것 같은데 반응이 없다"는 학습자 표현을
  각각 다른 다음 문서로 라우팅한다.
---

# 이벤트는 발행됐는데 리스너가 안 돌아요 원인 라우터

## 한 줄 요약

> 이 증상은 이벤트 시스템 전체 고장보다 `어떤 경로에서 발행했는지`, `commit이 실제로 있었는지`, `비동기 실패가 숨어 있는지`를 못 나눈 상태일 때 더 자주 생긴다.

## 가능한 원인

1. **트랜잭션 없는 경로에서 `@TransactionalEventListener`를 기대하고 있다.** controller, scheduler, `@Async` worker, 테스트에서 publisher를 직접 호출하면 `AFTER_COMMIT`이 걸릴 대상 자체가 없을 수 있다. 이 갈래는 [Spring `@TransactionalEventListener` Outside Transactions and `fallbackExecution`](./spring-transactionaleventlistener-fallbackexecution-no-transaction-boundaries.md)로 이어진다.
2. **테스트가 rollback이라 commit 세계에 한 번도 들어가지 않았다.** `flush()`까지 했어도 `@DataJpaTest`나 rollback 기본 테스트에서는 `AFTER_COMMIT` 리스너가 안 도는 쪽이 정상일 수 있다. 이 경우는 [Spring Mini Card: 왜 rollback 기반 slice test만으로 `AFTER_COMMIT`를 끝까지 믿기 어려운가](./spring-after-commit-rollback-slice-test-mini-card.md)로 분기한다.
3. **리스너는 비동기로 던져졌지만 executor 뒤에서 실패하거나 아직 끝나지 않았다.** 호출자는 성공처럼 보이는데 실제 작업은 별도 스레드에서 예외로 끝나거나 큐에 밀려 늦게 보일 수 있다. 이때는 [Spring `@EventListener` Ordering and Async Traps](./spring-eventlistener-ordering-async-traps.md)와 [비동기가 동기처럼 보여요 원인 라우터](./spring-async-looks-synchronous-cause-router.md)를 같이 본다.
4. **멀티캐스터 전달 전략이나 리스너 등록 조건이 달라졌다.** 특정 profile, conditional bean, custom multicaster, listener 타입 매칭 차이 때문에 어떤 요청에서만 fan-out이 달라질 수 있다. 이 갈래는 [Spring ApplicationEventMulticaster Internals](./spring-applicationeventmulticaster-internals.md)로 연결된다.
5. **사실은 "안 돈다"가 아니라 phase 선택을 잘못 골라 너무 이르거나 너무 늦게 보인다.** 즉시 `@EventListener`와 `AFTER_COMMIT`, outbox는 같은 상자가 아니다. 후속 작업 경계 자체가 헷갈리면 [Spring 커밋 후 후속 작업 경계 결정 가이드](./spring-post-commit-side-effect-routing-decision-guide.md)로 넘어간다.

## 빠른 자기 진단

1. 리스너가 `@EventListener`인지 `@TransactionalEventListener`인지 먼저 적는다. 여기서 절반이 갈린다.
2. 이벤트를 발행한 경로가 service 트랜잭션 안인지, controller·scheduler·테스트 직접 호출인지 확인한다. 트랜잭션이 없다면 `AFTER_COMMIT`이 안 도는 쪽이 더 자연스럽다.
3. 테스트라면 `flush()`만 했는지, 실제 commit이 있었는지 구분한다. rollback 기본값이면 listener 미실행이 곧 버그는 아니다.
4. `@Async`, 별도 executor, multicaster custom bean이 있으면 "안 돈다"보다 "나중에 실패했거나 관측이 안 된다" 가능성을 먼저 본다.
5. 어떤 요청에서는 돌고 어떤 요청에서는 안 돌면 profile, conditional, listener bean 등록 여부와 발행 위치가 서로 다른지 비교한다.

## 다음 학습

- 트랜잭션이 없는 경로에서 `@TransactionalEventListener`를 기대한 것인지 확인하려면 [Spring `@TransactionalEventListener` Outside Transactions and `fallbackExecution`](./spring-transactionaleventlistener-fallbackexecution-no-transaction-boundaries.md)를 먼저 본다.
- 테스트에서만 안 도는 증상이 핵심이면 [Spring Mini Card: 왜 rollback 기반 slice test만으로 `AFTER_COMMIT`를 끝까지 믿기 어려운가](./spring-after-commit-rollback-slice-test-mini-card.md)로 간다.
- 호출자는 성공인데 실제 후속 작업이 새는 비동기 축을 보려면 [Spring `@EventListener` Ordering and Async Traps](./spring-eventlistener-ordering-async-traps.md)와 [비동기가 동기처럼 보여요 원인 라우터](./spring-async-looks-synchronous-cause-router.md)를 잇는다.
- 주문 완료 후속 작업처럼 "phase를 어디에 둘지" 자체가 문제라면 [Spring 커밋 후 후속 작업 경계 결정 가이드](./spring-post-commit-side-effect-routing-decision-guide.md)와 [shopping-cart 주문 완료 후속 작업 누락 원인 라우터](./shopping-cart-order-complete-follow-up-missing-cause-router.md)로 내려간다.

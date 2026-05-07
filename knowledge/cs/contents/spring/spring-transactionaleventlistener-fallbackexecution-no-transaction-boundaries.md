---
schema_version: 3
title: Spring TransactionalEventListener FallbackExecution No Transaction Boundaries
concept_id: spring/transactionaleventlistener-fallbackexecution-no-transaction-boundaries
canonical: true
category: spring
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- transactionaleventlistener-fallbackexecution-no
- transaction-boundaries
- transactionaleventlistener-fallbackexecution
- transactional-event-listener
aliases:
- TransactionalEventListener fallbackExecution
- transactional event listener no transaction
- event ignored without transaction
- AFTER_COMMIT outside transaction
- fallback execution mixed semantics
- event phase boundary
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/spring/spring-eventlistener-transaction-phase-outbox.md
- contents/spring/spring-eventlistener-ordering-async-traps.md
- contents/spring/spring-transactional-async-composition-traps.md
- contents/spring/spring-transaction-synchronization-aftercommit-pitfalls.md
- contents/spring/spring-applicationeventmulticaster-internals.md
- contents/spring/spring-service-layer-external-io-after-commit-outbox-primer.md
confusable_with:
- spring/eventlistener-transaction-phase-outbox
- spring/eventlistener-ordering-async-traps
- spring/transactional-async-composition-traps
- spring/transaction-synchronization-aftercommit-pitfalls
symptoms:
- @TransactionalEventListener가 트랜잭션 없이 발행된 이벤트를 처리하지 않는다.
- fallbackExecution을 켰더니 같은 listener가 transaction phase와 즉시 실행 의미를 동시에 갖는다.
- AFTER_COMMIT 리스너라고 믿었는데 no transaction path에서는 commit 이후 보장이 없다.
expected_queries:
- @TransactionalEventListener는 transaction이 없으면 이벤트를 무시해?
- fallbackExecution=true를 켜면 어떤 semantic이 섞여 위험해?
- AFTER_COMMIT listener가 no transaction event에서는 어떤 의미가 돼?
- TransactionalEventListener와 EventListener, outbox를 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 @TransactionalEventListener가 active transaction이 있을 때만 phase 의미를 갖고,
  transaction 없이 발행된 event는 기본적으로 무시된다는 경계를 설명한다. fallbackExecution을
  켜면 같은 listener가 phase-based execution과 immediate execution을 함께 갖게 되는 pitfall을 다룬다.
---
# Spring `@TransactionalEventListener` Outside Transactions and `fallbackExecution`

> 한 줄 요약: `@TransactionalEventListener`는 트랜잭션이 있을 때만 phase 의미를 가지며, 트랜잭션 없이 발행된 이벤트는 기본적으로 무시되므로 `fallbackExecution`을 켜는 순간 같은 리스너가 서로 다른 의미로 실행될 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring EventListener, TransactionalEventListener, and Outbox](./spring-eventlistener-transaction-phase-outbox.md)
> - [Spring `@EventListener` Ordering and Async Traps](./spring-eventlistener-ordering-async-traps.md)
> - [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)
> - [Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls](./spring-transaction-synchronization-aftercommit-pitfalls.md)
> - [Spring ApplicationEventMulticaster Internals](./spring-applicationeventmulticaster-internals.md)

retrieval-anchor-keywords: TransactionalEventListener outside transaction, fallbackExecution, no transaction event listener, AFTER_COMMIT without transaction, transactional event listener skipped, event published outside tx, fallback execution semantics

## 핵심 개념

`@TransactionalEventListener`는 이름 그대로 트랜잭션 경계와 연결된 리스너다.

그래서 가장 중요한 사실은 이것이다.

- 활성 트랜잭션이 있으면 phase에 맞춰 실행된다
- 활성 트랜잭션이 없으면 기본적으로 실행되지 않는다

많은 사람이 여기서 한 번 헷갈린다.

- "`AFTER_COMMIT`이면 나중에 실행되겠지"
- "이벤트는 발행했으니 listener는 돌겠지"

하지만 트랜잭션이 없으면 "commit 이후"라는 개념 자체가 성립하지 않는다.

그래서 `fallbackExecution = true`가 등장한다.

문제는 이 옵션을 켜는 순간 같은 리스너가

- 어떤 경우엔 트랜잭션 phase 리스너로,
- 어떤 경우엔 즉시 실행 리스너로

동작할 수 있다는 점이다.

즉 이 주제의 핵심은 이벤트가 발행됐는지가 아니라, **이 이벤트를 해석하는 실행 계약이 현재 트랜잭션 존재 여부에 따라 바뀐다는 것**이다.

## 깊이 들어가기

### 1. `@TransactionalEventListener`는 트랜잭션 동기화 위에 있다

이 리스너는 보통 현재 트랜잭션에 synchronization callback을 등록해 phase 시점에 반응한다.

따라서 트랜잭션이 없다면 phase를 걸 대상도 없다.

예를 들어 `AFTER_COMMIT`은 다음을 전제한다.

- 현재 작업이 트랜잭션 안이다
- commit 성공 시점이 있다
- rollback와 구분되는 운명이 있다

이 전제가 깨지면 listener는 기본적으로 실행되지 않는다.

### 2. "안 도는 것 같다"는 버그의 상당수는 no-transaction 발행이다

다음 상황은 자주 보인다.

- controller에서 직접 이벤트 발행
- scheduler에서 이벤트 발행
- `@Async` worker에서 트랜잭션 없이 발행
- 테스트에서 service를 통하지 않고 바로 publisher 사용

이때 `@TransactionalEventListener(AFTER_COMMIT)`는 조용히 반응하지 않을 수 있다.

즉 "이벤트 시스템이 고장났다"기보다, **트랜잭션이 없는 곳에서 transactional listener를 기대한 것**일 수 있다.

### 3. `fallbackExecution = true`는 편하지만 의미를 바꾼다

```java
@TransactionalEventListener(
    phase = TransactionPhase.AFTER_COMMIT,
    fallbackExecution = true
)
public void on(OrderPlacedEvent event) {
    notificationSender.send(event.orderId());
}
```

이 설정은 다음을 뜻한다.

- 트랜잭션이 있으면 `AFTER_COMMIT` 의미로 실행
- 트랜잭션이 없으면 즉시 실행

즉 같은 리스너가 상황에 따라 두 계약을 가진다.

이게 괜찮은 경우도 있다.

- 단순 캐시 힌트
- 내부 metric 증가
- 정합성이 강하지 않은 보조 작업

하지만 중요한 비즈니스 side effect에는 위험하다.

- 어떤 호출 경로에서는 commit 뒤 실행
- 어떤 호출 경로에서는 commit 개념 없이 즉시 실행

이 차이가 클라이언트나 운영자에게는 매우 혼란스럽다.

### 4. `fallbackExecution`은 "그래도 실행"이지 "가짜 commit"이 아니다

특히 `AFTER_COMMIT`과 함께 쓸 때 오해가 많다.

트랜잭션이 없는데 fallback으로 실행된 경우는 다음과 다르다.

- 실제 commit 이후가 아니다
- rollback와 경쟁하지 않는다
- 원래 업무 DB 상태가 확정됐다는 보장이 없다

즉 fallback은 phase 의미를 최대한 흉내 내는 것이 아니라, **phase를 포기하고 즉시 실행으로 내려오는 옵션**에 가깝다.

### 5. 혼합 호출 경로가 있으면 리스너를 분리하는 편이 낫다

같은 이벤트가 아래 두 경로에서 모두 발행될 수 있다고 해 보자.

- 트랜잭션 서비스 메서드
- 스케줄러/배치/운영 툴

이때 단일 `@TransactionalEventListener(... fallbackExecution = true)`로 통일하면 겉보기는 편하다.

하지만 실제 의미는 갈라진다.

보통 더 나은 방향은 아래 중 하나다.

- 트랜잭션 경로와 비트랜잭션 경로의 리스너를 분리한다
- 이벤트 타입 자체를 분리한다
- 비트랜잭션 발행자는 명시적으로 다른 후속 처리 경로를 사용한다

핵심은 fallback으로 모든 경로를 한데 묶기보다, **호출 경로별 의미 차이를 명시하는 것**이다.

### 6. 테스트는 이 차이를 더 쉽게 숨긴다

테스트에서는 종종 다음이 섞인다.

- 테스트 메서드 자체의 트랜잭션
- service layer의 트랜잭션
- publisher 직접 호출

그래서 listener가 도는지 안 도는지, commit 이후인지 즉시인지 감각이 흐려질 수 있다.

특히 `@Transactional` 테스트에서는 실제 커밋이 안 일어나므로, `AFTER_COMMIT` 계열 검증은 더 조심해서 설계해야 한다.

## 실전 시나리오

### 시나리오 1: 서비스에서는 listener가 도는데 스케줄러에서는 안 돈다

서비스 경로는 트랜잭션 안이고, 스케줄러 경로는 트랜잭션 밖일 가능성이 높다.

`@TransactionalEventListener`가 고장난 게 아니라, 실행 계약이 달랐던 것이다.

### 시나리오 2: `fallbackExecution = true`를 켰더니 알림이 너무 이르게 나간다

비트랜잭션 경로에서 즉시 실행되기 때문이다.

이 경우는 fallback이 편의가 아니라 의미 오염이 됐을 수 있다.

### 시나리오 3: 테스트에서 listener가 안 돈다

`AFTER_COMMIT`인데 테스트가 실제 커밋을 만들지 않았거나, publisher를 트랜잭션 밖에서 직접 호출했을 수 있다.

### 시나리오 4: 같은 이벤트가 어떤 때는 commit 뒤, 어떤 때는 즉시 실행된다

이건 보통 fallbackExecution으로 경로를 섞은 결과다.

운영에서 가장 추적이 어려운 종류의 애매한 동작이다.

## 코드로 보기

### 트랜잭션이 있을 때만 실행

```java
@Component
public class OrderPlacedTransactionalListener {

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void on(OrderPlacedEvent event) {
        notificationSender.send(event.orderId());
    }
}
```

### fallback 실행 허용

```java
@Component
public class OrderPlacedFallbackListener {

    @TransactionalEventListener(
        phase = TransactionPhase.AFTER_COMMIT,
        fallbackExecution = true
    )
    public void on(OrderPlacedEvent event) {
        notificationSender.send(event.orderId());
    }
}
```

### 비트랜잭션 경로는 별도 리스너로 분리

```java
@Component
public class OrderPlacedImmediateListener {

    @EventListener
    public void on(OrderPlacedEvent event) {
        metricsRecorder.record(event.orderId());
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 순수 `@TransactionalEventListener` | 트랜잭션 phase 의미가 명확하다 | no-transaction 발행에서는 안 돈다 | 정합성이 중요한 후속 처리 |
| `fallbackExecution = true` | 혼합 경로에서도 일단 실행된다 | 같은 리스너 의미가 상황마다 달라진다 | 강한 정합성이 없는 보조 작업 |
| 별도 `@EventListener` 분리 | 의미가 명확하다 | 리스너 수와 설계 포인트가 늘어난다 | 트랜잭션/비트랜잭션 경로를 구분해야 할 때 |
| Outbox/별도 큐 | 신뢰성과 전달 의미가 강하다 | 구현과 운영이 더 복잡하다 | 중요한 외부 전송, 재시도 필요 작업 |

핵심은 `fallbackExecution`을 편한 스위치가 아니라, **phase 기반 의미를 일부 포기하는 옵션**으로 보는 것이다.

## 꼬리질문

> Q: `@TransactionalEventListener(AFTER_COMMIT)`가 no-transaction 경로에서 왜 안 도는가?
> 의도: phase 전제 이해 확인
> 핵심: commit 시점이 없어서 phase를 걸 대상이 없기 때문이다.

> Q: `fallbackExecution = true`는 무엇을 보장하고 무엇을 보장하지 않는가?
> 의도: fallback 의미 정확화
> 핵심: 실행은 보장하려 하지만, 실제 commit 이후 의미는 보장하지 않는다.

> Q: 왜 fallbackExecution이 중요한 비즈니스 side effect에 위험할 수 있는가?
> 의도: 의미 혼합 위험 이해 확인
> 핵심: 같은 리스너가 어떤 경로에서는 commit 뒤, 어떤 경로에서는 즉시 실행되기 때문이다.

> Q: 트랜잭션 경로와 비트랜잭션 경로가 섞이면 보통 어떤 설계가 더 낫나?
> 의도: 경계 분리 사고 확인
> 핵심: 리스너나 이벤트 타입을 분리해 실행 의미를 명시하는 편이 낫다.

## 한 줄 정리

`@TransactionalEventListener`는 트랜잭션이 있을 때만 진짜 phase 의미를 가지며, `fallbackExecution`은 그 의미를 유지하는 장치가 아니라 없을 때 즉시 실행으로 내려오는 타협이다.

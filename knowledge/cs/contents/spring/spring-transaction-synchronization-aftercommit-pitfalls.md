---
schema_version: 3
title: Spring TransactionSynchronization AfterCommit Pitfalls
concept_id: spring/transaction-synchronization-aftercommit-pitfalls
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- transaction-synchronization-aftercommit
- pitfalls
- transactionsynchronization-aftercommit
- aftercommit-pitfall
aliases:
- TransactionSynchronization afterCommit
- afterCommit pitfall
- transaction synchronization callbacks
- after commit outside transaction
- resource binding suspend resume
- outbox after commit
intents:
- deep_dive
- troubleshooting
- design
linked_paths:
- contents/spring/transactional-deep-dive.md
- contents/spring/spring-eventlistener-transaction-phase-outbox.md
- contents/spring/spring-transactionsynchronization-ordering-suspend-resume-resource-binding.md
- contents/spring/spring-transaction-debugging-playbook.md
- contents/spring/spring-delivery-reliability-retryable-resilience4j-outbox-relay.md
- contents/spring/spring-service-layer-external-io-after-commit-outbox-primer.md
symptoms:
- afterCommit 안에서 DB 작업을 같은 transaction의 연장처럼 생각했다가 일관성이 깨진다.
- 커밋 성공 후 외부 전송 실패를 rollback으로 되돌릴 수 있다고 착각한다.
- 여러 synchronization callback의 ordering과 resource binding 해제 시점이 헷갈린다.
expected_queries:
- TransactionSynchronization afterCommit은 같은 transaction 안에서 실행돼?
- afterCommit에서 외부 API 호출이나 메시지 발행을 하면 어떤 pitfall이 있어?
- afterCommit과 outbox는 전달 보장 관점에서 어떻게 달라?
- transaction synchronization callback ordering과 resource binding을 어떻게 봐야 해?
contextual_chunk_prefix: |
  이 문서는 TransactionSynchronization afterCommit이 commit 성공 이후 hook이지만 이미 원래
  transaction 밖의 후속 작업이라는 점을 설명한다. rollback 불가능한 side effect, outbox,
  ordering, suspend/resume, resource binding pitfall을 다룬다.
---
# Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls

> 한 줄 요약: `TransactionSynchronization`는 커밋 전후 훅을 제공하지만, `afterCommit`은 이미 성공한 트랜잭션 밖에서 실행되므로 같은 트랜잭션처럼 다루면 사고가 난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring EventListener, TransactionalEventListener, and Outbox](./spring-eventlistener-transaction-phase-outbox.md)
> - [Spring `TransactionSynchronization` Ordering, Suspend / Resume, and Resource Binding](./spring-transactionsynchronization-ordering-suspend-resume-resource-binding.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)
> - [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)

retrieval-anchor-keywords: TransactionSynchronization, afterCommit, beforeCommit, afterCompletion, flush, transaction callback, resource binding, rollback-only, commit hook, synchronization manager, suspend, resume, ordering

## 핵심 개념

Spring의 트랜잭션 동기화는 트랜잭션 경계에 콜백을 꽂는 기능이다.

- `beforeCommit`: 커밋 직전
- `beforeCompletion`: 종료 직전
- `afterCommit`: 커밋 성공 후
- `afterCompletion`: 커밋/롤백 모두 끝난 뒤

이 콜백들은 편리하지만, 각 시점의 의미가 다르다.

- `beforeCommit`은 아직 롤백될 수 있다
- `afterCommit`은 이미 DB 커밋이 끝났다
- `afterCompletion`은 트랜잭션 자원이 정리되는 시점이다

이 차이를 모르면 "커밋 뒤에 잠깐만 더 DB를 만지면 되겠지" 같은 실수를 한다.

## 깊이 들어가기

### 1. TransactionSynchronization은 트랜잭션 바깥의 후처리 훅이다

Spring은 `TransactionSynchronizationManager`에 등록된 콜백을 트랜잭션 라이프사이클에 맞춰 실행한다.

```java
TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
    @Override
    public void beforeCommit(boolean readOnly) {
        // flush or validation
    }

    @Override
    public void afterCommit() {
        // side effect
    }

    @Override
    public void afterCompletion(int status) {
        // cleanup
    }
});
```

핵심은 이 콜백이 "같은 트랜잭션 안에서 조금 늦게 실행되는 코드"가 아니라는 점이다.

### 2. `afterCommit`은 DB 커밋 이후다

`afterCommit`은 트랜잭션이 이미 성공적으로 끝난 뒤 실행된다.

그래서 여기서 하는 작업은 다음 성격을 가진다.

- 외부 알림 전송
- 캐시 무효화
- 검색 인덱스 반영 시도
- 후속 이벤트 발행

하지만 이 시점에서 다시 DB를 수정하려 하면, 기대와 다르게 동작할 수 있다.

- 같은 영속성 컨텍스트가 더 이상 안전하지 않을 수 있다
- 새 트랜잭션이 시작되지 않으면 변경이 반영되지 않을 수 있다
- 실패해도 원래 트랜잭션은 되돌릴 수 없다

즉, `afterCommit`은 "후속 처리"용이지 "추가 업무 로직"용이 아니다.

### 3. `afterCommit` 안에서 또 트랜잭션이 필요한 경우가 있다

후속 작업이 DB에 뭔가를 써야 한다면 별도 트랜잭션을 열어야 할 수 있다.

```java
@Override
public void afterCommit() {
    auditService.writeAuditInNewTransaction();
}
```

이때 중요한 건 다음이다.

- 바깥 트랜잭션은 이미 끝났다
- 안쪽 작업은 독립된 새 경계로 실행돼야 한다
- 멱등성과 실패 복구를 따로 설계해야 한다

이 관점은 [@Transactional 깊이 파기](./transactional-deep-dive.md)의 `REQUIRES_NEW`와 같이 보면 이해가 쉽다.

### 4. `afterCommit`은 지연된 side effect를 관리하는 도구다

`afterCommit`이 가장 잘 맞는 경우는 "DB가 확정된 뒤에만 외부 부작용을 내고 싶을 때"다.

하지만 이게 Outbox를 대체하는 것은 아니다.

- 프로세스가 죽을 수 있다
- 외부 브로커가 실패할 수 있다
- 커밋은 됐지만 후속 작업은 유실될 수 있다

그래서 신뢰성이 중요하면 `afterCommit`보다 outbox relay가 더 낫다.

## 실전 시나리오

### 시나리오 1: 커밋은 성공했는데 `afterCommit`에서 알림 전송이 실패한다

이 경우 DB 상태는 맞지만 외부 상태는 틀릴 수 있다.

대응:

- `afterCommit`에서 예외를 삼키지 말고 관측한다
- retry가 필요한 작업이면 별도 재시도 큐를 둔다
- 정말 중요한 전달이면 outbox로 저장한다

### 시나리오 2: `afterCommit`에서 repository.save를 호출했다

커밋 후라서 바깥 트랜잭션으로 묶이지 않는다.

- 기대한 데이터 일관성이 깨질 수 있다
- 쓰기 실패를 원래 작업 실패처럼 처리할 수 없다
- 코드 읽는 사람이 경계를 오해하기 쉽다

### 시나리오 3: `beforeCommit`에서 무거운 외부 호출을 했다

이건 트랜잭션 시간을 늘린다.

- 락 점유가 길어진다
- 응답 지연이 커진다
- timeout과 deadlock 가능성이 올라간다

이 문제는 [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)와 같이 봐야 한다.

### 시나리오 4: `afterCompletion`을 정리용으로만 믿었다

`afterCompletion`은 커밋/롤백 모두 끝난 뒤다.

- 자원 정리에 적합하다
- 비즈니스 처리를 넣기에는 늦다
- 성공/실패를 구분하려면 status를 확인해야 한다

## 코드로 보기

### Synchronization 등록

```java
@Service
public class OrderService {

    @Transactional
    public void placeOrder(Order order) {
        orderRepository.save(order);

        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                notificationService.sendOrderPlaced(order.getId());
            }
        });
    }
}
```

### `beforeCommit` / `afterCommit` / `afterCompletion`

```java
TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
    @Override
    public void beforeCommit(boolean readOnly) {
        auditLogger.validatePendingState();
    }

    @Override
    public void afterCommit() {
        cacheEvictor.evictOrder(orderId);
    }

    @Override
    public void afterCompletion(int status) {
        metrics.record(status);
    }
});
```

### `afterCommit` 대신 outbox 저장으로 바꾸는 예

```java
@Transactional
public void placeOrder(Order order) {
    orderRepository.save(order);
    outboxRepository.save(OutboxEvent.of("ORDER_PLACED", order.getId()));
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `beforeCommit` | 커밋 전 검증이 가능하다 | 트랜잭션 시간을 늘릴 수 있다 | 최종 검증 |
| `afterCommit` | 커밋 성공 후 side effect를 분리한다 | 유실/실패 복구를 별도 설계해야 한다 | 알림, 캐시, 후속 이벤트 |
| `afterCompletion` | 정리 작업이 쉬우다 | 비즈니스 처리엔 늦다 | cleanup, metric |
| Outbox | 전달 신뢰성이 높다 | relay worker가 추가된다 | 유실이 싫은 후속 작업 |

핵심은 콜백이 아니라, **콜백이 어느 실패 모델을 갖는지**다.

## 꼬리질문

> Q: `afterCommit`은 왜 같은 트랜잭션으로 생각하면 안 되는가?
> 의도: 커밋 경계 이해 확인
> 핵심: DB 커밋이 이미 끝난 뒤 실행되기 때문이다.

> Q: `afterCommit`에서 DB 쓰기를 하면 무엇이 문제인가?
> 의도: 새 트랜잭션 필요성 확인
> 핵심: 바깥 트랜잭션에 묶이지 않고 실패 복구도 분리된다.

> Q: `beforeCommit`에 무거운 작업을 두면 왜 위험한가?
> 의도: 락과 지연 시간 이해 확인
> 핵심: 커밋이 늦어져 전체 트랜잭션 시간이 길어진다.

> Q: `afterCommit`과 Outbox는 어떤 관계인가?
> 의도: 후속 처리 신뢰성 구분 확인
> 핵심: `afterCommit`은 편의, Outbox는 신뢰성이다.

## 한 줄 정리

트랜잭션 동기화 콜백은 편하지만, `afterCommit`은 이미 끝난 트랜잭션 밖에서 실행되므로 side effect와 DB 쓰기를 같은 경계로 착각하면 안 된다.

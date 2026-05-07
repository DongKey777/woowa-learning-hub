---
schema_version: 3
title: Spring Transaction Propagation Nested RequiresNew Case Studies
concept_id: spring/transaction-propagation-nested-requires-new-case-studies
canonical: true
category: spring
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- transaction-propagation-nested
- requires-new-studies
- nested-vs-requires
- new
aliases:
- NESTED vs REQUIRES_NEW
- savepoint vs independent commit
- nested transaction case study
- requires new audit log
- partial rollback savepoint
- independent transaction boundary
intents:
- comparison
- deep_dive
- troubleshooting
linked_paths:
- contents/spring/transactional-deep-dive.md
- contents/spring/spring-unexpectedrollback-rollbackonly-marker-traps.md
- contents/spring/spring-transaction-propagation-mandatory-supports-not-supported-boundaries.md
- contents/spring/spring-service-layer-transaction-boundary-patterns.md
- contents/spring/spring-transaction-debugging-playbook.md
- contents/spring/spring-jpatransactionmanager-savepoint-expectations-mini-card.md
confusable_with:
- spring/transaction-propagation-required-requires-new-rollbackonly-primer
- spring/jpatransactionmanager-savepoint-expectations-mini-card
- spring/unexpectedrollback-rollbackonly-marker-traps
expected_queries:
- NESTED와 REQUIRES_NEW는 둘 다 안쪽 작업 분리처럼 보이는데 어떻게 달라?
- savepoint rollback과 independent commit을 transaction propagation에서 어떻게 구분해?
- audit log는 REQUIRES_NEW가 맞고 일부 검증 rollback은 NESTED가 맞아?
- JpaTransactionManager에서 NESTED savepoint 기대가 깨질 수 있어?
contextual_chunk_prefix: |
  이 문서는 NESTED와 REQUIRES_NEW를 둘 다 안쪽 작업 분리라고 뭉뚱그리지 않고,
  savepoint 기반 부분 rollback과 independent transaction commit이라는 전혀 다른 경계로
  비교하는 chooser다.
---
# Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies

> 한 줄 요약: `NESTED`와 `REQUIRES_NEW`는 둘 다 "안쪽 작업을 분리한다"처럼 보이지만, 실제로는 savepoint와 독립 커밋이라는 전혀 다른 경계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
> - [Spring Transaction Propagation: `MANDATORY` / `SUPPORTS` / `NOT_SUPPORTED` Boundaries](./spring-transaction-propagation-mandatory-supports-not-supported-boundaries.md)
> - [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Spring `TransactionSynchronization` Ordering, Suspend / Resume, and Resource Binding](./spring-transactionsynchronization-ordering-suspend-resume-resource-binding.md)
> - [Spring Routing DataSource Read/Write Transaction Boundaries](./spring-routing-datasource-read-write-transaction-boundaries.md)
> - [Spring EventListener / TransactionalEventListener / Outbox](./spring-eventlistener-transaction-phase-outbox.md)
> - [Spring Batch Chunk / Retry / Skip](./spring-batch-chunk-retry-skip.md)
> - [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)

retrieval-anchor-keywords: propagation, nested transaction, requires new, requires_new beginner route, savepoint, suspended transaction, rollback-only, connection pool exhaustion, audit log, partial commit, audit survives rollback, inner readOnly writer pool

## 핵심 개념

전파(propagation)는 "이미 트랜잭션이 있을 때 새로 시작할지, 합류할지, 분리할지"를 정한다.

`NESTED`와 `REQUIRES_NEW`는 겉보기엔 비슷하지만 의미가 다르다.

- `NESTED`: 바깥 트랜잭션 안에서 savepoint를 만든다
- `REQUIRES_NEW`: 바깥 트랜잭션을 잠시 중단하고 새 트랜잭션을 연다

둘 다 "실패를 부분적으로 다루고 싶다"는 요구에서 시작하지만, 장애 양상은 완전히 다르다.

## 깊이 들어가기

### 1. `NESTED`는 savepoint 기반이다

`NESTED`는 바깥 트랜잭션 안에 savepoint를 두고, 안쪽만 되돌릴 수 있게 하는 방식이다.

즉, 바깥 트랜잭션은 유지하고 내부 작업만 롤백할 수 있다.

```text
outer tx
  -> savepoint A
    -> inner work
    -> rollback to savepoint A
outer tx continues
```

하지만 모든 환경에서 자연스럽게 되는 것은 아니다.

- JDBC savepoint를 지원해야 한다
- 트랜잭션 매니저와 드라이버 조합을 확인해야 한다
- JPA 환경에서는 기대와 다르게 보일 수 있다

즉, `NESTED`는 이론보다 **실제 플랫폼 지원 여부**가 더 중요하다.

### 2. `REQUIRES_NEW`는 진짜로 트랜잭션을 하나 더 연다

`REQUIRES_NEW`는 바깥 트랜잭션을 suspend하고, 새 커넥션/새 트랜잭션으로 실행한다.

```text
outer tx (suspended)
  -> inner tx starts
  -> inner commit/rollback
outer tx resumes
```

장점은 분명하다.

- 바깥이 롤백돼도 안쪽은 살아남을 수 있다
- 감사 로그, 알림 기록, 별도 보정 작업에 유용하다

하지만 비용도 있다.

- 커넥션을 하나 더 먹는다
- 커넥션 풀이 작으면 막힌다
- 부분 커밋이 많아져 추적이 어려워진다

### 3. `REQUIRES_NEW`는 커넥션 풀을 건드린다

실무에서 자주 놓치는 문제다.

외부 트랜잭션이 커넥션 A를 잡고 있고, 내부 `REQUIRES_NEW`가 커넥션 B를 또 잡으려면 풀 여유가 필요하다.

동시 요청이 많으면 다음 현상이 나온다.

- outer tx가 커넥션을 오래 쥔다
- inner tx가 추가 커넥션을 못 얻는다
- 대기열이 쌓인다
- 전체 응답 시간이 튄다

즉, `REQUIRES_NEW`는 "분리 커밋"이 아니라 **분리 커넥션 사용**까지 같이 의미한다.

### 4. rollback-only는 전파와 구분해야 한다

안쪽에서 예외를 삼키더라도, 이미 rollback-only가 찍힌 트랜잭션은 커밋될 수 없다.

이 상황은 의외로 자주 나온다.

- 내부 메서드에서 예외 발생
- catch로 삼킴
- 바깥에서 커밋 시도
- `UnexpectedRollbackException` 발생

이때는 "예외를 삼켰는데 왜 실패하지?"가 아니라, **이미 롤백 대상으로 표시됐기 때문**이라고 봐야 한다.

## 실전 시나리오

### 시나리오 1: 감사 로그는 꼭 남겨야 한다

주문 저장이 실패해도 감사 로그는 남겨야 할 수 있다.

이때 `REQUIRES_NEW`가 잘 맞는다.

```java
@Service
public class AuditService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void write(String message) {
        auditRepository.save(new AuditLog(message));
    }
}
```

하지만 감사 로그가 많아질수록 부분 커밋 추적과 장애 분석이 어려워진다.

### 시나리오 2: 배치에서 일부 아이템만 되돌리고 싶다

배치 처리 중 한 레코드만 실패시키고 나머지는 계속 가고 싶다면 `NESTED`가 더 자연스럽다.

```java
@Transactional
public void processAll(List<Item> items) {
    for (Item item : items) {
        try {
            itemService.processOne(item);
        } catch (Exception ignored) {
            // savepoint만 되돌리고 다음 아이템 계속
        }
    }
}
```

이때 안쪽이 진짜 savepoint를 쓰는지 확인해야 한다.

### 시나리오 3: 재고 차감은 하나라도 실패하면 전체를 되돌려야 한다

이 경우에는 `REQUIRED`가 더 적절하다.

전파를 억지로 쪼개면 오히려 정합성이 깨진다.

### 시나리오 4: 바깥 트랜잭션이 길어질수록 `REQUIRES_NEW`가 더 위험해진다

바깥 트랜잭션이 이미 오래 락을 잡고 있는데 안쪽이 또 커넥션을 요구하면, connection pool과 lock 둘 다 압박이 커진다.

이럴 때는 트랜잭션을 줄이거나, 아예 이벤트 기반 후처리로 넘기는 편이 나을 수 있다.

관련해서는 [Spring EventListener / TransactionalEventListener / Outbox](./spring-eventlistener-transaction-phase-outbox.md)를 같이 보는 편이 좋다.

## 코드로 보기

### `REQUIRES_NEW` 감사 로그

```java
@Service
public class OrderService {
    private final AuditService auditService;

    public OrderService(AuditService auditService) {
        this.auditService = auditService;
    }

    @Transactional
    public void placeOrder() {
        orderRepository.save(new Order());
        auditService.write("order placed");
        throw new IllegalStateException("force rollback");
    }
}
```

```java
@Service
public class AuditService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void write(String message) {
        auditRepository.save(new AuditLog(message));
    }
}
```

### `NESTED`로 부분 롤백을 의도하는 예시

```java
@Service
public class SettlementService {

    @Transactional
    public void settle(List<SettlementLine> lines) {
        for (SettlementLine line : lines) {
            try {
                settleOne(line);
            } catch (Exception ex) {
                // 이 줄만 rollback-to-savepoint
            }
        }
    }

    @Transactional(propagation = Propagation.NESTED)
    public void settleOne(SettlementLine line) {
        settlementRepository.save(line.toEntity());
    }
}
```

### 전파 상태 확인

```java
log.info("tx active = {}", TransactionSynchronizationManager.isActualTransactionActive());
log.info("tx name = {}", TransactionSynchronizationManager.getCurrentTransactionName());
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `REQUIRED` | 가장 단순하다 | 안쪽 실패가 전체에 영향 | 보통의 서비스 트랜잭션 |
| `NESTED` | 부분 롤백이 가능하다 | savepoint/플랫폼 제약이 있다 | 배치 아이템 단위 처리 |
| `REQUIRES_NEW` | 독립 커밋이 된다 | 커넥션과 추적 비용이 늘어난다 | 감사 로그, 별도 기록 |
| 이벤트/Outbox | 경계를 더 분명히 나눈다 | 즉시성은 떨어질 수 있다 | 외부 부작용 분리 |

핵심은 "분리하면 좋다"가 아니라, **무엇을 함께 실패시켜야 하는지**를 먼저 정하는 것이다.

## 꼬리질문

> Q: `NESTED`와 `REQUIRES_NEW`의 가장 큰 차이는 무엇인가?
> 의도: savepoint와 독립 트랜잭션 구분 확인
> 핵심: `NESTED`는 savepoint, `REQUIRES_NEW`는 별도 트랜잭션이다.

> Q: `REQUIRES_NEW`를 많이 쓰면 왜 위험한가?
> 의도: 커넥션 풀/지연 비용 이해 확인
> 핵심: 바깥과 안쪽이 각각 커넥션을 소비할 수 있다.

> Q: `UnexpectedRollbackException`은 왜 생기는가?
> 의도: rollback-only 플래그 이해 확인
> 핵심: 이미 롤백 대상으로 표시된 트랜잭션을 커밋하려고 해서다.

> Q: 부분 롤백이 정말 필요할 때 무엇부터 확인해야 하는가?
> 의도: 플랫폼 제약과 대안 선택 확인
> 핵심: savepoint 지원 여부와 배치 설계부터 본다.

## 한 줄 정리

`NESTED`는 savepoint로 부분 롤백을, `REQUIRES_NEW`는 별도 커밋을 만든다. 둘은 같은 "분리"가 아니다.

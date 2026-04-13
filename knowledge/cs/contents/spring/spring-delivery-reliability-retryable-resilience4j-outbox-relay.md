# Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design

> 한 줄 요약: `@Retryable`은 간단한 재시도에 좋지만, 진짜 전달 보장은 outbox relay worker, idempotency, circuit breaker, and observability까지 같이 설계해야 나온다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring EventListener / TransactionalEventListener / Outbox](./spring-eventlistener-transaction-phase-outbox.md)
> - [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](./spring-resilience4j-retry-circuit-breaker-bulkhead.md)
> - [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)

retrieval-anchor-keywords: retryable, resilience4j, outbox relay worker, idempotent publish, poller, skip locked, poison message, circuit breaker, backoff, dead letter

## 핵심 개념

전달 신뢰성을 다룰 때 가장 흔한 실수는 "실패하면 다시 하면 되겠지"로 끝내는 것이다.

하지만 실제 문제는 다르다.

- 재시도 자체가 부하 증폭이 될 수 있다
- 성공했는데 응답만 실패한 경우가 있다
- DB 커밋과 메시지 발행 사이에 프로세스가 죽을 수 있다
- relay worker가 중복 실행될 수 있다

그래서 전달 신뢰성은 보통 다음 계층으로 나눠 본다.

- 메서드 단위 retry: `@Retryable`
- 시스템 레벨 방어선: Resilience4j
- 영속화된 전달 보장: transactional outbox
- relay worker: outbox를 읽어 외부로 전달

## 깊이 들어가기

### 1. `@Retryable`은 가장 가까운 재시도 도구다

`@Retryable`은 Spring AOP proxy를 통해 메서드 실패를 감싸 재시도한다.

```java
@Service
public class PaymentGatewayClient {

    @Retryable(maxAttempts = 3, backoff = @Backoff(delay = 200))
    public void charge(ChargeRequest request) {
        remoteClient.charge(request);
    }
}
```

장점은 간단하다.

- 구현이 쉽다
- 적은 코드로 retry를 붙일 수 있다
- 작은 연동에 빠르게 적용 가능하다

하지만 한계도 분명하다.

- retry storm 제어가 약하다
- circuit breaker나 bulkhead를 같이 보장하지 않는다
- 관측 지표가 약하다
- 잘못 쓰면 같은 실패를 더 자주 때린다

### 2. Resilience4j는 retry 그 이상을 다룬다

Resilience4j는 retry만이 아니라 다음을 같이 다룬다.

- timeout
- circuit breaker
- bulkhead
- rate limiting
- fallback

이게 중요한 이유는 실패를 "반복"하는 것보다, **실패의 확산을 멈추는 것**이 더 중요하기 때문이다.

기존 문서인 [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](./spring-resilience4j-retry-circuit-breaker-bulkhead.md)와 이 문서를 같이 보면, retry 자체보다 보호 계층이 더 중요하다는 점이 보인다.

### 3. outbox relay worker는 DB와 브로커 사이의 전달 책임을 분리한다

outbox는 업무 데이터와 이벤트를 같은 트랜잭션으로 저장한다.

하지만 커밋 후 외부 브로커에 보낼 책임은 따로 있어야 한다.

그걸 relay worker가 맡는다.

흐름은 대체로 이렇게 간다.

```text
business tx
  -> write domain data
  -> write outbox row
  -> commit
relay worker
  -> claim unsent rows
  -> publish to broker
  -> mark sent
```

핵심은 "커밋과 발행을 분리"하는 것이다.
그래야 DB는 저장됐는데 메시지만 날아간 문제를 줄일 수 있다.

### 4. relay worker는 꼭 idempotent 해야 한다

relay worker가 같은 outbox row를 두 번 발행할 수 있다.

이유는 다양하다.

- publish는 성공했는데 ack 전에 죽음
- sent mark 전에 재시작
- 여러 worker가 동시에 돌음
- DB 업데이트와 broker 발행 사이 경합

따라서 worker는 중복 발행 가능성을 전제로 설계해야 한다.

- producer idempotency key
- consumer dedup
- unique event id
- processed message table

즉, outbox는 exactly once를 "보장"하는 마법이 아니라, **중복을 흡수할 수 있게 만드는 설계**다.

### 5. worker는 lock contention과 poison row를 다뤄야 한다

아무 row나 계속 실패하면 relay가 같은 실패만 반복한다.

그래서 다음이 필요하다.

- `attempt_count`
- `next_retry_at`
- `last_error`
- `status`
- dead-letter 전환

이 설계가 없으면 relay는 조용히 막힌다.

## 실전 시나리오

### 시나리오 1: 외부 결제 API가 간헐적으로 실패한다

이때 `@Retryable`만 붙이면 되는 것처럼 보이지만, 실제로는 멱등성과 backoff가 먼저다.

좋은 순서는 보통 이렇다.

1. timeout을 먼저 둔다
2. 멱등 요청만 retry한다
3. Resilience4j circuit breaker를 붙인다
4. 장애가 길어지면 fallback 또는 보류 상태로 전환한다

### 시나리오 2: 메시지를 보냈는데 DB 커밋이 실패한다

이건 outbox 없이 직접 publish한 경우에 생기는 전형적 문제다.

- 메시지는 나갔다
- 업무 데이터는 롤백됐다
- 시스템 정합성이 깨진다

그래서 publish를 business transaction 밖으로 밀어내는 relay가 필요하다.

### 시나리오 3: relay worker가 죽었다가 다시 뜬다

worker가 죽기 전에 발행했는지, 마킹했는지 애매한 구간이 생긴다.

해결책은 단순 재시도가 아니라 중복 허용 설계다.

### 시나리오 4: retry가 오히려 장애를 악화시킨다

retry가 너무 공격적이면 실패한 브로커를 더 세게 두드린다.

이때는 retry를 늘리는 게 아니라 circuit breaker를 열어 호출을 멈추는 게 맞다.

## 코드로 보기

### `@Retryable`의 간단한 사용

```java
@Service
public class SmsGatewayClient {

    @Retryable(
        retryFor = IOException.class,
        maxAttempts = 3,
        backoff = @Backoff(delay = 300, multiplier = 2.0)
    )
    public void send(String phone, String message) throws IOException {
        smsApi.send(phone, message);
    }
}
```

### Resilience4j를 붙인 publisher

```java
@Service
public class EventPublisher {

    @CircuitBreaker(name = "broker", fallbackMethod = "fallback")
    @Retry(name = "broker")
    public void publish(OutboxMessage message) {
        brokerClient.publish(message.eventId(), message.payload());
    }

    public void fallback(OutboxMessage message, Throwable ex) {
        // metric, log, maybe mark for requeue
    }
}
```

### outbox row와 relay worker

```java
@Entity
public class OutboxEvent {
    @Id
    private Long id;
    private String aggregateType;
    private String aggregateId;
    private String eventType;
    @Lob
    private String payload;
    private String status;
    private int attemptCount;
    private Instant nextRetryAt;
}
```

```java
@Service
public class OutboxRelayWorker {

    private final OutboxRepository outboxRepository;
    private final EventPublisher publisher;
    private final TransactionTemplate transactionTemplate;

    @Scheduled(fixedDelayString = "1000")
    public void relay() {
        List<OutboxEvent> batch = transactionTemplate.execute(status ->
            outboxRepository.claimReadyBatch(100)
        );

        if (batch == null || batch.isEmpty()) {
            return;
        }

        for (OutboxEvent event : batch) {
            try {
                publisher.publish(event);
                transactionTemplate.executeWithoutResult(status ->
                    outboxRepository.markSent(event.getId())
                );
            } catch (Exception ex) {
                transactionTemplate.executeWithoutResult(status ->
                    outboxRepository.markRetry(event.getId(), ex.getMessage())
                );
            }
        }
    }
}
```

### claim query 감각

```sql
SELECT *
FROM outbox_event
WHERE status = 'READY'
  AND next_retry_at <= NOW()
ORDER BY id
LIMIT 100
FOR UPDATE SKIP LOCKED;
```

이 패턴은 worker 간 중복 처리를 줄이는 데 유용하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `@Retryable` | 가장 간단하다 | 보호 계층이 얇다 | 작은 동기 연동 |
| Resilience4j | retry 외 방어선이 넓다 | 설정과 관측이 필요하다 | 외부 의존성이 중요한 경우 |
| 직접 publish 후 mark | 구현이 단순해 보인다 | 메시지 유실/중복 위험이 크다 | 거의 권장하지 않음 |
| Outbox + relay | 전달 신뢰성이 높다 | worker와 중복 처리 설계가 필요하다 | 정합성이 중요한 경우 |

핵심은 retry를 어디에 두느냐가 아니라, **실패를 어디까지 허용하고 어디서 멈출지**다.

## 꼬리질문

> Q: `@Retryable`과 Resilience4j의 가장 큰 차이는 무엇인가?
> 의도: 단순 retry와 보호 계층 구분 확인
> 핵심: Resilience4j는 circuit breaker, bulkhead, timeout까지 같이 다룬다.

> Q: outbox relay worker가 왜 idempotent해야 하는가?
> 의도: 중복 발행 위험 이해 확인
> 핵심: publish와 상태 마킹 사이에 실패가 끼어들 수 있기 때문이다.

> Q: outbox만 있으면 exactly once가 보장되는가?
> 의도: 신뢰성의 한계 이해 확인
> 핵심: 중복은 여전히 가능하므로 producer/consumer dedup이 필요하다.

> Q: retry storm을 멈추려면 무엇이 필요한가?
> 의도: 장애 확산 방지 이해 확인
> 핵심: timeout과 circuit breaker가 필요하다.

## 한 줄 정리

전달 신뢰성은 `@Retryable` 하나로 끝나지 않고, Resilience4j의 방어선과 outbox relay worker의 idempotent 설계까지 묶어야 완성된다.

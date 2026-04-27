# 트랜잭션 경계 체크리스트 카드

> 한 줄 요약: 코드리뷰에서 "`@Transactional` 안에 외부 I/O가 섞였는지"는 5문항만 보면 빠르게 1차 판별할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [트랜잭션·락·커넥션 풀 첫 그림](./transaction-locking-connection-pool-primer.md)
- [트랜잭션 경계·격리수준·락 의사결정 프레임워크](./transaction-boundary-isolation-locking-decision-framework.md)
- [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
- [Spring Retry Proxy Boundary Pitfalls](./spring-retry-proxy-boundary-pitfalls.md)
- [Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기](../spring/spring-service-layer-external-io-after-commit-outbox-primer.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
- [Idempotent Transaction Retry Envelopes](./idempotent-transaction-retry-envelopes.md)
- [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: transaction boundary checklist card, external io inside transaction checklist, @transactional external api review, transaction boundary code review card, beginner transaction review questions, pr comment one-liner transaction review, review comment tone card, question request block review tone, review comment tone selector, before after transaction boundary snippet, transaction boundary before after example, outbox before after snippet, spring transaction retry boundary example, spring retry facade tx service example, beginner retry idempotency 연결표

## 경계 체크 다음에 바로 보는 카드

트랜잭션 경계 5문항을 본 직후에는 아래 표에서 상황별로 다음 카드를 고르면 된다.

| 지금 막힌 지점 | 바로 이어서 볼 Beginner 카드 | 왜 이 카드가 다음 순서인가 |
|---|---|---|
| "외부 API는 밖으로 빼야 한다는 건 알겠는데, `AFTER_COMMIT`과 outbox는 언제 갈라지나?"가 헷갈린다 | [Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기](../spring/spring-service-layer-external-io-after-commit-outbox-primer.md) | service method 기준으로 `메인 tx 밖`, `커밋 후 반응`, `전달 보장` 3상자를 초급자 언어로 먼저 분리해 준다 |
| "전체 재시도는 어디서 감싸야 하나?"가 헷갈린다 | [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md) | `40001`/deadlock을 SQL 한 줄이 아니라 **트랜잭션 시도 전체 재시도**로 연결하는 기준을 잡아준다 |
| `insert-if-absent`에서 duplicate/timeout/deadlock 해석이 섞인다 | [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md) | `already exists`/`busy`/`retryable` 3버킷으로 결과 언어를 고정해 준다 |
| MySQL `1062 duplicate key`를 자꾸 blind retry하게 된다 | [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md) | `insert retry`보다 `winner fresh read`가 먼저라는 기본 흐름을 짧게 정리한다 |
| exact-key duplicate에서 `UNIQUE`와 locking read 역할이 헷갈린다 | [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md) | retry 신호(`busy`/`already exists`/`retryable`)가 왜 다르게 해석되는지 첫 그림을 맞춰 준다 |

## 먼저 한 장 그림

초보자 기준으로는 용어보다 이 한 줄이 먼저다.

> 트랜잭션 안에서 외부 I/O를 기다리면, 그 시간만큼 DB 커넥션과 락도 같이 묶일 수 있다.

그래서 코드리뷰의 첫 목적은 "정교한 설계 평가"가 아니라,
"지금 이 코드가 **트랜잭션을 불필요하게 길게 잡는지**"를 빠르게 찾는 것이다.

## 외부 I/O 유형별 위험도 한 장 표

초보자용 기억법은 간단하다.

- 네트워크 왕복 + 외부 시스템 상태 변경이 같이 있으면 우선순위를 높인다.
- 업로드/대용량 전송처럼 "시간 변동폭"이 큰 작업은 트랜잭션 밖으로 먼저 뺀다.

| 외부 I/O 유형 | 흔한 예시 | 트랜잭션 안 배치 시 위험도 | 경계 분리 우선순위 | 왜 먼저 분리하나 |
|---|---|---|---|---|
| 파일 업로드/다운로드 (S3, CDN, 대용량 첨부) | `putObject`, multipart upload | 매우 높음 | 1순위 | 전송 시간이 길고 변동폭이 커서 lock/connection 점유 시간이 급격히 늘기 쉽다 |
| HTTP 외부 API 호출 | 결제 승인, 주소 검증, 알림 API | 높음 | 2순위 | 상대 서비스 지연/장애가 그대로 DB 트랜잭션 길이로 번진다 |
| gRPC 동기 호출 | 내부 마이크로서비스 검증/승인 | 높음 | 2순위 | 내부망이어도 네트워크/상대 서비스 부하 영향을 받아 tail latency가 길어질 수 있다 |
| 메시지 브로커 발행 | Kafka publish, RabbitMQ send | 중간~높음 | 3순위 | 브로커 ack 실패/재시도와 DB commit 원자성이 분리되어 outbox 같은 안전장치가 필요하다 |
| 캐시/세션 저장소 호출 (Redis 등) | 캐시 갱신, 분산락 확인 | 중간 | 4순위 | 짧게 끝날 때도 많지만 네트워크 의존이므로 트랜잭션 안 장기 대기는 피하는 편이 안전하다 |

실무에서 "메시지 발행은 빨라서 괜찮다"라고 자주 오해한다.
핵심은 속도 평균이 아니라, **실패 시 commit 경계와 복구 경계가 분리되는지**다.

메시지 경계를 더 깊게 보려면:

- [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md)
- [Exactly-Once 신화와 DB + Queue 경계](./exactly-once-myths-db-queue.md)
- [Transactional Inbox와 Dedup Design](./transactional-inbox-dedup-design.md)

## 코드리뷰 5문항 카드

아래 5개 질문에 `예`가 하나라도 나오면, 경계 재검토 후보로 본다.

예외 기준은 "권장 패턴"이 아니라, 초보자가 과하게 다 쪼개는 오탐을 줄이기 위한 아주 좁은 허용선이다.

## 코드리뷰 5문항 카드 (계속 2)

| 번호 | 리뷰 질문 | `예`일 때 기본 액션 | 예외적으로 tx 안에 남겨도 되는 조건 | 실제 PR 코멘트 1줄 예시 |
|---|---|---|---|---|
| 1 | `@Transactional` 메서드 안에서 HTTP/gRPC/Redis/S3/메시지 브로커 같은 외부 호출을 기다리나? | 외부 I/O를 트랜잭션 밖으로 이동 가능한지 먼저 확인 | 호출이 사실상 짧은 조회성 확인이고, 앞뒤로 오래 잡는 row/range lock이 없으며, 실패해도 외부 부작용이 남지 않을 때만 예외로 본다. | `@Transactional` 경계 안에서 `paymentClient` 호출을 기다리고 있어, 외부 I/O를 경계 밖으로 분리할 수 있는지 확인 부탁드립니다. |
| 2 | DB write 직후 외부 API 응답을 기다린 다음 다시 DB write를 하나? | DB 변경을 "짧은 commit 단위"로 쪼개고 후속 처리는 outbox/비동기 검토 | 첫 write가 임시/초안 상태이고, 외부 응답이 늦으면 그냥 전체 abort해도 되며, 중간 상태가 다른 요청의 blocker가 되지 않을 때만 매우 제한적으로 남길 수 있다. | `save -> 외부 API 대기 -> update` 흐름이라 트랜잭션 길이가 길어집니다; DB commit을 짧게 끊고 후속 처리는 outbox/비동기로 분리 검토 부탁드립니다. |
| 3 | 외부 호출 실패 시 whole transaction rollback을 기대하나? | "외부 세계는 rollback 불가" 전제로 보상/재시도 경로 명시 | 외부 호출이 진짜 상태 변경이 아니라 조회/검증이고, 실패 시 "그냥 DB도 커밋하지 않음"만으로 의미가 닫힐 때는 rollback 기대를 허용할 수 있다. | 외부 API 실패를 DB rollback으로만 복구하려는 구조로 보여, 보상 작업 또는 재시도 경로를 명시해주시면 좋겠습니다. |
| 4 | 재시도 로직이 메서드 바깥에서 전체 트랜잭션을 반복 실행할 수 있나? | idempotency key/중복 방지 규칙을 같이 점검 | 재실행 구간이 순수 조회 또는 멱등 write뿐이고, 외부 호출도 같은 key로 안전하게 중복 억제된다는 근거가 있을 때만 한 경계에 둘 수 있다. | 현재 retry가 메서드 전체를 다시 실행할 수 있어 중복 write 위험이 있으니, idempotency key(또는 중복 방지 조건) 확인 부탁드립니다. |
| 5 | 느린 외부 호출이 lock wait, deadlock, pool timeout으로 번질 수 있는 경로가 보이나? | timeout/격리/락 순서보다 먼저 "트랜잭션 길이"부터 줄임 | 호출 p99가 매우 짧고 상한이 강하게 통제되며, 그 구간 동안 잡는 커넥션/락이 사실상 없다는 관측이 있을 때만 남겨도 되는 후보로 본다. | 외부 호출 지연 시 lock wait와 pool 대기가 함께 늘 수 있어, timeout 튜닝 전에 트랜잭션 길이 축소부터 검토 부탁드립니다. |

### 흔한 혼선 바로잡기

## 코드리뷰 5문항 카드 (계속 3)

- "외부 I/O가 빠르다"만으로는 예외가 아니다. 초보자 기준에서는 `빠르다`보다 `락 없이 짧게 끝나고 실패해도 외부 부작용이 남지 않는다`가 먼저다.
- "같은 사내 서비스 호출"도 네트워크면 기본은 외부 I/O다. 같은 팀 서비스라고 해서 DB 트랜잭션 수명이 자동으로 같이 묶이지 않는다.
- "한 메서드가 읽기 좋다"와 "한 트랜잭션이어야 한다"는 다른 문제다. 메서드는 하나여도 commit 경계는 둘 이상일 수 있다.
- 예외 문장을 봤다고 바로 tx 안에 남기지 말고, 관련 근거가 `p99`, `lock footprint`, `idempotency key` 같은 관측으로 설명되는지 먼저 확인한다.

## 코멘트 톤 선택 카드

같은 문제를 봐도 리뷰 상황은 다르다. 초보자용 기억법은 아래 한 줄이면 충분하다.

- `질문형`: 아직 확신은 없지만, 작성자가 의도를 설명해 주면 풀릴 수 있을 때
- `요청형`: 위험은 분명하지만, 대안 검토 여지를 열어 두고 싶을 때
- `차단형`: 병합 전에 경계 수정이 필요하다고 판단될 때

| 톤 | 언제 쓰나 | 상대가 받는 느낌 | 기본 문장 뼈대 |
|---|---|---|---|
| 질문형 | 맥락 확인이 먼저 필요함 | "의도를 설명해 달라" | `이 경계가 왜 필요한지 설명 가능할까요?` |
| 요청형 | 개선 방향은 보이지만 선택지는 열어 둠 | "이 방향을 검토해 달라" | `경계 분리를 검토 부탁드립니다.` |
| 차단형 | 현재 구조로는 위험이 커서 merge gate가 필요함 | "이건 먼저 고쳐야 한다" | `병합 전 경계 분리가 필요합니다.` |

### 같은 5문항, 3가지 톤으로 말하기

## 코멘트 톤 선택 카드 (계속 2)

| 번호 | 질문형 | 요청형 | 차단형 |
|---|---|---|---|
| 1. 트랜잭션 안 외부 호출 대기 | `@Transactional` 안에서 `paymentClient` 호출을 기다리는 이유가 있을까요? 이 호출은 경계 밖으로 뺄 수 있는지 궁금합니다. | `@Transactional` 안 외부 호출 대기로 트랜잭션 길이가 늘어날 수 있어, `paymentClient` 호출의 경계 분리 검토 부탁드립니다. | 현재 `@Transactional` 안에서 외부 호출을 기다리고 있어 lock/pool 대기 전파 위험이 큽니다. 병합 전 경계 분리가 필요합니다. |
| 2. write -> 외부 대기 -> write | `save -> 외부 API 대기 -> update` 흐름이 꼭 한 트랜잭션이어야 하는 이유가 있을까요? commit 단위를 나눌 수 있는지 확인 부탁드립니다. | `save -> 외부 API 대기 -> update` 구조라 트랜잭션이 길어집니다. DB commit을 짧게 끊고 후속 처리는 비동기/outbox로 분리 검토 부탁드립니다. | write 사이에 외부 대기가 끼어 있어 현재 트랜잭션 경계는 유지하면 안 됩니다. commit 단위 분리 없이 병합하면 안 됩니다. |
| 3. 외부 실패를 rollback으로만 복구 기대 | 외부 API 실패를 DB rollback으로만 복구하려는 의도인지 확인하고 싶습니다. 보상 작업이나 재시도 경로가 따로 있을까요? | 외부 세계는 DB rollback으로 함께 되돌릴 수 없어서, 보상 작업 또는 재시도 경로를 코드/설계에 명시 부탁드립니다. | 외부 실패를 rollback 하나로 처리하는 전제는 안전하지 않습니다. 보상 또는 재시도 경로가 없으면 병합 보류가 필요합니다. |
| 4. 전체 트랜잭션 재시도 가능 | 현재 retry가 메서드 전체를 다시 실행할 수 있는 구조 같은데, 중복 write 방지 키가 이미 있는지 확인 가능할까요? | whole transaction retry 가능성이 보여, idempotency key나 중복 방지 조건을 함께 넣어 주시길 부탁드립니다. | 전체 재시도 경로가 있는데 중복 방지 장치가 보이지 않습니다. idempotency 보강 전에는 병합하면 안 됩니다. |
| 5. 외부 지연이 lock/pool 문제로 번짐 | 이 외부 호출이 느려질 때 lock wait나 pool 대기로 이어질 가능성을 확인해 보셨을까요? timeout 조정보다 경계 축소가 먼저인지 궁금합니다. | 외부 호출 지연이 lock wait와 pool 대기로 번질 수 있어, timeout 튜닝 전에 트랜잭션 길이 축소를 우선 검토 부탁드립니다. | 현재 구조는 외부 지연이 DB 대기로 직접 번질 수 있습니다. timeout 조정보다 경계 축소가 선행되어야 하므로 병합 전 수정이 필요합니다. |

### 빠른 선택 예시

## 코멘트 톤 선택 카드 (계속 3)

| 리뷰 상황 | 추천 톤 | 이유 |
|---|---|---|
| 설계 의도는 아직 안 보이지만 코드만 봐선 애매함 | 질문형 | 먼저 맥락을 확인해야 불필요한 오탐을 줄일 수 있다 |
| 위험은 보이지만 팀에서 여러 대안을 열어 둠 | 요청형 | 수정 방향은 제시하되 구현 선택지는 남겨 둘 수 있다 |
| lock/pool 전파 위험이 명확하고 재현 가능 | 차단형 | "나중에 보자"로 넘기면 운영 리스크가 그대로 남는다 |

### 30초 판정 규칙

- 5문항 모두 `아니오`면: 일단 경계 위험은 낮다.
- 1~2개 `예`면: PR 코멘트로 경계 분리 질문을 남긴다.
- 3개 이상 `예`면: 기능 병합 전 경계 재설계를 우선 검토한다.

## 문항-행동 연결 미니 스니펫

아래 3쌍만 봐도 "무슨 질문을 보면 어떤 수정 방향을 떠올려야 하는지"가 빠르게 연결된다.

| 연결하고 싶은 문항 | before에서 보이는 냄새 | after에서 바로 바뀌는 행동 |
|---|---|---|
| 1번. 트랜잭션 안에서 외부 호출을 기다리나? | DB write와 HTTP 호출이 한 경계에 묶임 | DB write commit과 외부 승인 호출을 분리 |
| 2번. write 직후 외부 응답을 기다린 뒤 다시 write 하나? | `write -> 브로커 발행 대기 -> write` | DB write는 짧게 commit하고, 메시지는 outbox로 넘김 |
| 4번. 전체 retry가 어디를 다시 실행하는지 분리돼 있나? | `@Retryable`이 외부 호출과 DB write를 같이 재실행 | retry는 facade에서, DB atomic attempt는 별도 tx service로 분리 |

### 스니펫 1. 결제 승인 HTTP 호출 분리

`1번 문항`을 보면 먼저 이런 패턴을 의심하면 된다.

```java
// before: 트랜잭션 안에서 외부 결제 승인 대기
@Transactional
public void placeOrder(Command cmd) {
    orderRepository.save(...);
    inventoryRepository.decrease(...);
    paymentClient.authorize(cmd.paymentToken()); // external I/O
    orderRepository.markPaid(...);
}
```

```java
// after: 트랜잭션은 DB 상태 변경만 짧게, 외부 호출은 경계 분리
public void placeOrder(Command cmd) {
    Long orderId = txTemplate.execute(status -> {
        Long savedId = orderRepository.save(...);
        inventoryRepository.decrease(...);
        return savedId;
    });

    paymentClient.authorize(cmd.paymentToken()); // boundary 밖
    txTemplate.executeWithoutResult(status -> orderRepository.markPaid(orderId));
}
```

이 스니펫에서 바로 읽어야 하는 포인트는 하나다.

- `paymentClient.authorize(...)`가 느려져도 첫 번째 DB 트랜잭션은 이미 끝났다는 점

### 스니펫 2. 메시지 발행 대기를 outbox로 분리

`2번 문항`은 "write 뒤에 브로커 ack를 기다리면서 다시 DB write까지 이어지나?"를 보는 질문이다.

## 문항-행동 연결 미니 스니펫 (계속 2)

```java
// before: DB write 뒤 브로커 발행을 기다린 뒤 다시 DB write
@Transactional
public void confirmOrder(Long orderId) {
    orderRepository.markConfirmed(orderId);
    eventPublisher.publish(new OrderConfirmed(orderId)); // external I/O
    orderRepository.markPublished(orderId);
}
```

```java
// after: DB 안에서는 상태 변경 + outbox 적재만 끝내고 발행은 바깥 워커가 담당
@Transactional
public void confirmOrder(Long orderId) {
    orderRepository.markConfirmed(orderId);
    outboxRepository.enqueue("OrderConfirmed", orderId);
}
```

```java
// 별도 경계: outbox 워커/퍼블리셔가 브로커 발행 담당
public void publishPendingEvents() {
    OutboxEvent event = outboxRepository.next();
    eventPublisher.publish(event);
    outboxRepository.markSent(event.id());
}
```

이 스니펫에서 초보자가 먼저 기억할 문장은 이거다.

- "메시지 발행을 DB commit과 같은 트랜잭션으로 묶으려 하지 말고, DB 안에서는 `보낼 사실`만 기록한다."

핵심은 "정답 패턴 1개"가 아니라,
**외부 대기 시간을 DB 트랜잭션에서 분리**하려는 방향성이다.

outbox 쪽 설명을 더 보고 싶으면:

- [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md)
- [Exactly-Once 신화와 DB + Queue 경계](./exactly-once-myths-db-queue.md)

### 스니펫 3. Spring에서 외부 I/O 분리 + retry 경계 분리 같이 보여주기

초보자가 가장 자주 헷갈리는 부분은 이것이다.

- "`@Retryable`을 붙이면 안전하게 다시 시도해 주겠지"
- "그 메서드 안에 외부 API 호출이 같이 있어도 괜찮겠지"

하지만 실제로는 **무엇을 다시 실행할지**를 먼저 잘라야 한다.

## 문항-행동 연결 미니 스니펫 (계속 3)

```java
// before: 한 메서드가 DB write, 외부 승인, retry를 전부 같이 들고 있음
@Service
public class PaymentService {

    @Retryable(
            retryFor = CannotAcquireLockException.class,
            maxAttempts = 3
    )
    @Transactional
    public void confirmPayment(Long orderId, String paymentToken) {
        orderRepository.markPending(orderId);
        paymentClient.authorize(paymentToken); // external I/O
        orderRepository.markPaid(orderId);
    }
}
```

이 before 코드에서 초보자가 먼저 봐야 할 위험은 2개다.

- lock 충돌로 retry가 걸리면 `paymentClient.authorize(...)`까지 다시 호출될 수 있다
- 외부 승인 대기 시간이 길어지면 DB 트랜잭션도 같이 길어진다

## 문항-행동 연결 미니 스니펫 (계속 4)

```java
// after: retry는 facade에서, DB 시도는 짧은 트랜잭션으로, 외부 I/O는 경계 밖으로 분리
@Service
@RequiredArgsConstructor
public class PaymentFacade {

    private final PaymentTxService paymentTxService;
    private final PaymentClient paymentClient;

    @Retryable(
            retryFor = CannotAcquireLockException.class,
            maxAttempts = 3
    )
    public void confirmPayment(Long orderId, String paymentToken) {
        PaymentReady ready = paymentTxService.prepare(orderId);
        paymentClient.authorize(paymentToken); // external I/O, transaction boundary 밖
        paymentTxService.markPaid(ready.orderId());
    }
}

@Service
public class PaymentTxService {

    @Transactional
    public PaymentReady prepare(Long orderId) {
        orderRepository.markPending(orderId);
        return new PaymentReady(orderId);
    }

    @Transactional
    public void markPaid(Long orderId) {
        orderRepository.markPaid(orderId);
    }
}
```

이 after 코드에서 기억해야 할 문장은 한 줄이면 충분하다.

- retry는 `facade`가 잡고, 한 번의 DB 시도는 `@Transactional` 메서드가 짧게 끝낸다

### before/after를 30초로 읽는 표

| 비교 포인트 | before | after |
|---|---|---|
| retry가 다시 실행하는 범위 | DB write + 외부 승인 호출이 함께 재실행될 수 있음 | facade 재호출은 가능하지만 각 DB 시도는 짧은 트랜잭션으로 분리됨 |
| 외부 승인 호출 위치 | `@Transactional` 안 | 트랜잭션 밖 |
| lock/pool 대기 전파 | 외부 API 지연이 그대로 DB 점유 시간으로 번짐 | 외부 API 지연이 있어도 DB 트랜잭션은 먼저 끝낼 수 있음 |
| 코드리뷰 코멘트 포인트 | "retry가 외부 부작용까지 다시 치지 않나요?" | "retry 범위와 DB atomic attempt가 분리돼 있네요" |

retry 경계를 더 자세히 보려면:

## 문항-행동 연결 미니 스니펫 (계속 5)

- [Spring Retry Proxy Boundary Pitfalls](./spring-retry-proxy-boundary-pitfalls.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
- [Idempotent Transaction Retry Envelopes](./idempotent-transaction-retry-envelopes.md)

## 실전 코드리뷰 미니 시나리오 3세트

초보자가 PR 코멘트를 쓸 때 가장 자주 막히는 지점은 이것이다.

- 위험은 보이는데 문장이 너무 추상적으로 흐른다
- "왜 분리해야 하는지"와 "어떻게 바꾸면 되는지"가 한 문장에 같이 안 잡힌다

처음에는 아래 3단계 틀로 읽으면 된다.

| 리뷰 문장 구성 | 초보자용 질문 |
|---|---|
| 1. 지금 뭐가 트랜잭션 안에 묶였나 | `DB write + 외부 대기`가 같이 있나? |
| 2. 왜 위험한가 | lock/connection 점유, 중복 부작용, commit-발행 불일치 중 무엇이 보이나? |
| 3. 무엇을 바꾸라고 말할까 | `DB commit 경계`와 `외부 I/O 경계`를 분리하자고 제안할 수 있나? |

### 세트 1. 결제 API

한 줄 mental model:

> 결제 승인 응답을 기다리는 동안 DB 락까지 같이 잡고 있으면, 결제 지연이 곧 DB 지연이 된다.

```java
// before
@Transactional
public void confirmOrder(Long orderId, String paymentToken) {
    orderRepository.markPending(orderId);
    paymentClient.approve(paymentToken); // external I/O
    orderRepository.markPaid(orderId);
}
```

```java
// after
public void confirmOrder(Long orderId, String paymentToken) {
    paymentTxService.markPending(orderId);   // tx 1
    paymentClient.approve(paymentToken);     // boundary 밖
    paymentTxService.markPaid(orderId);      // tx 2
}
```

| 구분 | PR 코멘트 |
|---|---|
| before 코멘트 | `@Transactional` 안에서 결제 승인 응답을 기다리고 있어 결제 지연이 lock/pool 대기로 번질 수 있습니다. `markPending`/`approve`/`markPaid` 경계를 분리해서 DB 트랜잭션을 짧게 가져갈 수 있을지 검토 부탁드립니다. |
| after 코멘트 | 결제 승인 호출을 트랜잭션 밖으로 빼서 DB 점유 시간을 줄인 점이 좋습니다. 남은 확인 포인트는 승인 재시도 시 중복 결제를 막을 `idempotency key` 또는 결과 조회 경로가 있는지입니다. |

### 세트 2. 파일 업로드

한 줄 mental model:

> 파일 전송 시간은 들쭉날쭉해서, 트랜잭션 안에 넣으면 "가끔 느린 요청"이 DB 병목으로 커지기 쉽다.

## 실전 코드리뷰 미니 시나리오 3세트 (계속 2)

```java
// before
@Transactional
public Attachment upload(ProfileImageCommand cmd) {
    User user = userRepository.getById(cmd.userId());
    String url = s3Client.putObject(cmd.file()); // external I/O
    return attachmentRepository.save(new Attachment(user.getId(), url));
}
```

```java
// after
public Attachment upload(ProfileImageCommand cmd) {
    String url = s3Client.putObject(cmd.file()); // boundary 밖
    return attachmentTxService.saveMetadata(cmd.userId(), url); // 짧은 tx
}
```

| 구분 | PR 코멘트 |
|---|---|
| before 코멘트 | 파일 업로드가 트랜잭션 안에 있어 전송 시간이 그대로 커넥션 점유 시간으로 이어질 수 있습니다. 업로드와 메타데이터 저장 경계를 분리하고, 업로드 성공 후 DB 저장 실패 시 정리 전략도 같이 명시해 주세요. |
| after 코멘트 | 업로드 자체를 트랜잭션 밖으로 분리해서 긴 I/O를 잘라낸 점이 명확합니다. 이제 업로드는 성공했는데 DB 저장이 실패한 경우를 위해 orphan 파일 cleanup 기준만 보강되면 리뷰 포인트가 닫힙니다. |

### 세트 3. 이벤트 발행

한 줄 mental model:

> "DB commit"과 "브로커 publish 성공"은 같은 rollback 버튼으로 되돌릴 수 없으니, 보통 DB 안에는 `보낼 사실`만 남긴다.

```java
// before
@Transactional
public void completeDelivery(Long orderId) {
    orderRepository.markDelivered(orderId);
    kafkaPublisher.publish(new DeliveryCompleted(orderId)); // external I/O
    orderRepository.markEventPublished(orderId);
}
```

```java
// after
@Transactional
public void completeDelivery(Long orderId) {
    orderRepository.markDelivered(orderId);
    outboxRepository.enqueue("DeliveryCompleted", orderId);
}
```

## 실전 코드리뷰 미니 시나리오 3세트 (계속 3)

| 구분 | PR 코멘트 |
|---|---|
| before 코멘트 | 현재는 `배송 완료 write -> 브로커 발행 대기 -> 발행 완료 표시`가 한 트랜잭션에 묶여 있어 commit-발행 불일치와 긴 tx 위험이 같이 있습니다. outbox로 `보낼 사실`만 DB에 남기고 발행은 별도 워커 경계로 넘기는 쪽이 더 안전해 보입니다. |
| after 코멘트 | 상태 변경과 outbox 적재를 한 트랜잭션으로 묶어서 commit 기준이 또렷해졌습니다. 다음 확인 포인트는 outbox relay의 재시도와 `markSent` 멱등성만 확보돼 있는지입니다. |

## 이 3세트를 읽을 때 먼저 고정할 오해

- 결제 API와 이벤트 발행은 둘 다 "외부 I/O"지만, 결제는 `중복 부작용`, 이벤트는 `commit-발행 순서`가 먼저 핵심이다.
- 파일 업로드는 "정합성"보다 "길이 변동폭"이 먼저 문제다. 느려질 수 있다는 사실 자체가 경계 분리 신호다.
- after 코멘트도 칭찬만 쓰지 않는다. 분리 후 남는 `멱등성`, `cleanup`, `relay 재시도`를 한 줄로 이어 주면 리뷰 품질이 올라간다.

## 자주 헷갈리는 포인트

- "`@Transactional`이면 전체가 원자적이라 안전하다"
  - DB 내부 상태에는 맞지만, 외부 API/메시지는 같은 방식으로 rollback되지 않는다.
- "`@Retryable`을 바깥 메서드에 두면 외부 API도 그냥 다시 때리면 되는 것 아닌가?"
  - 아니다. retry가 가능하더라도 외부 부작용은 멱등성 키, 결과 조회, outbox 같은 별도 안전장치와 같이 설계해야 한다.
- "after 예시도 결국 메서드가 2개라 더 복잡해 보인다"
  - 복잡도를 옮긴 게 아니라, `DB commit 경계`와 `외부 대기 경계`를 분리해서 어디가 느린지/실패했는지 보이게 만든 것이다.
- "트랜잭션을 짧게 자르면 business atomicity가 깨지는 것 아닌가?"
  - 그럴 수 있다. 그래서 rollback 환상을 기대하기보다, 어디서 보상/재시도/멱등성을 둘지 같이 설계해야 한다.
- "timeout만 줄이면 해결된다"
  - timeout은 실패를 빨리 드러낼 뿐, 긴 경계 자체를 없애주지 않는다.
- "pool size를 키우면 된다"
  - 근본 원인이 긴 트랜잭션이면 lock/대기 전파는 계속 남는다.
- "차단형 코멘트는 무조건 공격적이다"
  - 아니다. 병합 기준을 명확히 말하는 톤일 뿐이고, 왜 차단하는지 근거를 함께 적으면 된다.
- "질문형이면 약해서 효과가 없다"
  - 아니다. 설계 의도가 숨겨져 있을 때는 질문형이 가장 빠르게 정보 회수를 돕는다.

## 리뷰 코멘트 템플릿

```text
현재 트랜잭션 경계 안에 외부 I/O(OO 호출)가 포함되어 있어
lock/pool 대기 전파 위험이 있습니다.
DB 상태 변경 commit 단위와 외부 호출 경계를 분리할 수 있을지 검토 부탁드립니다.
```

```text
현재 구조는 외부 호출 지연이 lock/pool 대기로 번질 수 있어
병합 전 트랜잭션 경계 분리가 필요합니다.
DB commit 단위와 외부 호출 경계를 나눠서 다시 보여주세요.
```

## 한 줄 정리

트랜잭션 경계 리뷰의 1순위는 "외부 I/O가 안에 있나?"이며, 이 5문항을 질문형/요청형/차단형 3톤으로 바로 꺼내 쓸 수 있으면 초보자도 상황에 맞는 리뷰 코멘트를 훨씬 덜 헤매게 된다.

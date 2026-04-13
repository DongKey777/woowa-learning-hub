# Transactional Inbox와 Dedup Design

> 한 줄 요약: inbox는 “메시지를 받았는가”와 “처리했는가”를 분리해서, 재전달된 이벤트를 안전하게 한 번만 반영하게 해 준다.

관련 문서: [Exactly-Once 신화와 DB + Queue 경계](./exactly-once-myths-db-queue.md), [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md), [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md)
Retrieval anchors: `transactional inbox`, `dedup`, `consumer idempotency`, `message inbox table`, `processed event`

## 핵심 개념

Transactional inbox는 소비자가 받은 메시지를 먼저 inbox 테이블에 기록하고, 처리 완료 상태를 별도로 남기는 패턴이다.  
이 구조는 at-least-once 전달 환경에서 중복 처리를 막는 데 유용하다.

왜 중요한가:

- 메시지는 중복으로 올 수 있다
- 소비자가 중간에 죽으면 같은 메시지를 다시 받을 수 있다
- 정확히 한 번 처리보다, 중복을 안전하게 흡수하는 것이 현실적이다

inbox는 메시지 수신과 비즈니스 처리를 분리해서 **처리 상태를 DB에 남기는 것**이 핵심이다.

## 깊이 들어가기

### 1. inbox가 필요한 이유

브로커는 메시지 전달을 보장해도, 소비자의 비즈니스 처리를 보장하지 않는다.

- 수신 성공 후 처리 중 죽을 수 있다
- ack 전에 재시도될 수 있다
- 동일 이벤트가 여러 번 올 수 있다

inbox가 있으면 받은 메시지의 상태를 추적할 수 있다.

### 2. inbox 테이블 설계

보통 다음 컬럼이 필요하다.

- `event_id`
- `consumer_id`
- `status`
- `received_at`
- `processed_at`
- `payload_hash`

유니크 키는 보통 `(consumer_id, event_id)`다.  
같은 메시지를 다시 받으면 insert가 막힌다.

### 3. 처리 흐름

1. 메시지 수신
2. inbox insert
3. 이미 처리된 이벤트면 skip
4. 처리 성공 시 status 업데이트
5. ack

핵심은 “처리 전에 먼저 기록”하는 것이다.

### 4. 실패 시 어디까지 재처리하나

다음 경우를 구분해야 한다.

- inbox insert는 성공, 처리 실패
- processing 중 crash
- ack 전에 timeout

이 각 케이스를 다시 처리해도 결과가 같게 만들어야 한다.

## 실전 시나리오

### 시나리오 1: 주문 이벤트가 두 번 들어옴

같은 `ORDER_CREATED`가 중복 수신되어도 inbox dedup이 있으면 한 번만 처리한다.

### 시나리오 2: 소비자 장애 후 재시작

처리 중 멈췄다면 inbox 상태를 보고 다시 이어갈 수 있다.

### 시나리오 3: 처리 성공했는데 ack 실패

브로커는 다시 보낼 수 있다.  
inbox가 없으면 중복 반영될 수 있지만, inbox dedup이 있으면 방어된다.

## 코드로 보기

```sql
CREATE TABLE consumer_inbox (
  consumer_id VARCHAR(100) NOT NULL,
  event_id VARCHAR(100) NOT NULL,
  status VARCHAR(20) NOT NULL,
  payload_hash VARCHAR(64) NOT NULL,
  received_at DATETIME NOT NULL,
  processed_at DATETIME NULL,
  PRIMARY KEY (consumer_id, event_id)
);
```

```java
try {
    inboxRepository.insertIfAbsent(consumerId, eventId, payloadHash);
    if (inboxRepository.isAlreadyProcessed(consumerId, eventId)) return;
    handle(event);
    inboxRepository.markProcessed(consumerId, eventId);
} catch (DuplicateKeyException e) {
    return;
}
```

inbox는 “메시지를 받았는지”보다, **이벤트 효과를 한 번만 반영했는지**를 기록한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| transactional inbox | 중복 방어가 강하다 | 저장소가 늘어난다 | 주요 이벤트 소비자 |
| in-memory dedup | 빠르다 | 재시작 시 사라진다 | 임시 캐시 |
| broker ack only | 단순하다 | 중복 처리에 취약하다 | 아주 단순한 소비자 |
| inbox + outbox | end-to-end가 강해진다 | 구현이 복잡하다 | 중요한 이벤트 파이프라인 |

## 꼬리질문

> Q: transactional inbox와 idempotency key는 같은 건가요?
> 의도: 요청 멱등성과 이벤트 소비 중복 방지를 구분하는지 확인
> 핵심: inbox는 메시지 소비 중복 방지이고, idempotency key는 요청 재전송 방지다

> Q: 처리 후 ack 전에 죽으면 어떻게 되나요?
> 의도: at-least-once 재전달을 이해하는지 확인
> 핵심: 메시지는 다시 올 수 있으므로 inbox dedup이 필요하다

> Q: inbox에 payload_hash를 저장하는 이유는 무엇인가요?
> 의도: 같은 ID인데 내용이 다른 이상 상황을 아는지 확인
> 핵심: 재전달이 아니라 다른 payload인지 검증하기 위해서다

## 한 줄 정리

Transactional inbox는 중복으로 오는 메시지를 먼저 기록하고 처리 완료 상태를 남겨, 소비자 쪽에서 한 번만 반영되게 만드는 패턴이다.

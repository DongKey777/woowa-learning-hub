# CDC, Debezium, Outbox, Binlog

> 한 줄 요약: DB 변경을 이벤트로 안전하게 흘려보내려면 outbox와 CDC를 같은 정합성 문제로 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md)
> - [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md)
> - [MVCC, Replication, Sharding](./mvcc-replication-sharding.md)
> - [API 설계와 예외 처리](../software-engineering/api-design-error-handling.md)

## 핵심 개념

CDC(Change Data Capture)는 DB의 변경을 외부 시스템으로 전달하는 방식이다.
Debezium은 binlog/WAL 같은 DB 로그를 읽어 변경 이벤트를 만드는 대표 도구다.

핵심은 **비즈니스 데이터와 이벤트가 서로 어긋나지 않게 만드는 것**이다.

## 깊이 들어가기

### 1. 왜 outbox가 필요한가

가장 흔한 실패는 이것이다.

1. 주문 DB는 커밋됨
2. 메시지 브로커 발행 실패
3. 외부 시스템은 주문을 모름

반대로 메시지만 나가고 DB가 롤백되면 더 큰 문제가 생긴다.

Outbox는 같은 로컬 트랜잭션에 넣어서 이 문제를 줄인다.

```sql
INSERT INTO orders(id, status) VALUES (1001, 'CREATED');
INSERT INTO outbox(id, aggregate_id, event_type, payload, created_at)
VALUES (9001, 1001, 'ORDER_CREATED', '{...}', NOW());
```

### 2. CDC가 하는 일

CDC는 DB 변경 로그를 보고 이벤트를 재구성한다.

- MySQL: binlog
- PostgreSQL: WAL

Debezium은 이 로그를 읽어 Kafka 같은 스트림으로 보낸다.

장점:

- 애플리케이션 코드가 단순해진다
- DB 커밋과 이벤트 발행 사이의 gap이 줄어든다

단점:

- 로그 포맷과 DB 운영을 이해해야 한다
- 스키마 변경과 재처리 전략이 필요하다
- 순서/중복/딜레이를 고려해야 한다

### 3. Outbox와 CDC의 차이

| 방식 | 장점 | 단점 | 적합한 상황 |
|---|---|---|---|
| Outbox polling | 구현이 쉽다 | polling 비용이 든다 | 단순 이벤트 발행 |
| Outbox + CDC | 정합성이 좋다 | 인프라가 복잡하다 | 대규모 이벤트 파이프라인 |
| Direct publish | 가장 단순해 보인다 | 실패에 취약하다 | 장난감 서비스 수준 |

### 4. Debezium 운용 포인트

- snapshot과 streaming을 구분해야 한다
- connector offset을 관리해야 한다
- 재처리 시 idempotent consumer가 필요하다
- schema evolution을 고려해야 한다

## 실전 시나리오

### 시나리오 1: outbox 중복 발행

consumer가 같은 이벤트를 두 번 받아도 안전해야 한다.

```sql
CREATE TABLE processed_event (
  event_id BIGINT PRIMARY KEY,
  processed_at TIMESTAMP NOT NULL
);
```

처리 전에 event_id를 저장하거나, unique key로 중복을 막는다.

### 시나리오 2: binlog 지연

DB write는 끝났는데 downstream 검색/캐시 반영이 늦을 수 있다.

이때는:

- lag 모니터링
- DLQ
- replay tool

이 필요하다.

### 시나리오 3: schema change

outbox payload를 바꾸면 consumer가 깨질 수 있다.

따라서 versioned payload가 필요하다.

## 코드로 보기

```java
@Transactional
public void createOrder(CreateOrderCommand command) {
    Order order = orderRepository.save(command.toOrder());
    outboxRepository.save(new OutboxEvent(
        order.getId(),
        "ORDER_CREATED",
        jsonSerializer.serialize(order)
    ));
}
```

CDC worker는 outbox 테이블을 읽거나, binlog를 읽어 Kafka로 보낸다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 판단 기준 |
|---|---|---|---|
| 직접 브로커 publish | 단순 | 실패 취약 | 낮은 정합성 요구 |
| outbox polling | 안정적 | 지연/부하 | 중간 규모 |
| CDC + Debezium | 확장성 좋음 | 운영 복잡 | 이벤트 파이프라인 중심 |

## 꼬리질문

> Q: outbox와 CDC를 같이 쓰면 중복이 많아지지 않나요?
> 의도: 중복을 설계로 다루는지 확인
> 핵심: 중복을 없애기보다 idempotent consumer와 deduplication으로 흡수한다.

> Q: binlog만 읽으면 이벤트 소싱과 같은 건가요?
> 의도: 로그 기반 추출과 이벤트 소싱 구분
> 핵심: binlog는 저장 변경 추적이고, 이벤트 소싱은 도메인 상태 자체를 이벤트로 모델링한다.

## 한 줄 정리

CDC는 변경을 전달하는 기술이고, outbox는 그 전달이 DB 커밋과 어긋나지 않게 하는 안전장치다.

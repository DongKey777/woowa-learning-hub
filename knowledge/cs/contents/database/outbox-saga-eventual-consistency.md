# Outbox, Saga, Eventual Consistency

**난이도: 🔴 Advanced**

> 트랜잭션 하나로 끝나지 않는 데이터 정합성을 다루는 실전 문서

> 관련 문서:
> - [Outbox Relay and Idempotent Publisher](../design-pattern/outbox-relay-idempotent-publisher.md)
> - [옵저버, Pub/Sub, ApplicationEvent](../design-pattern/observer-pubsub-application-events.md)
> - [Spring EventListener, TransactionalEventListener, and Outbox](../spring/spring-eventlistener-transaction-phase-outbox.md)
> - [Change Data Capture / Outbox Relay 설계](../system-design/change-data-capture-outbox-relay-design.md)
> - [Historical Backfill / Replay Platform 설계](../system-design/historical-backfill-replay-platform-design.md)
> - [Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](../design-pattern/projection-rebuild-backfill-cutover-pattern.md)

retrieval-anchor-keywords: outbox pattern, saga pattern, eventual consistency, outbox relay, local transaction plus event, distributed consistency, compensating transaction, consumer idempotency, replay and retry, distributed transaction alternative

<details>
<summary>Table of Contents</summary>

- [왜 이 주제가 중요한가](#왜-이-주제가-중요한가)
- [Eventual Consistency](#eventual-consistency)
- [Outbox Pattern](#outbox-pattern)
- [Saga Pattern](#saga-pattern)
- [실전에서 자주 깨지는 지점](#실전에서-자주-깨지는-지점)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

## 왜 이 주제가 중요한가

실무에서는 하나의 요청이 다음 작업을 모두 끝내지 못하는 경우가 많다.

- DB 저장
- 외부 시스템 호출
- 메시지 발행
- 검색/분석 시스템 반영

이때 모든 것을 한 트랜잭션으로 묶을 수 없으면, 결국 **정합성을 어떤 방식으로 맞출지**를 설계해야 한다.

---

## Eventual Consistency

Eventual Consistency는 **즉시 같은 상태가 되지는 않아도, 시간이 지나면 결국 같은 상태로 수렴한다**는 뜻이다.

예:

- 주문 DB에는 주문이 저장됨
- 결제 시스템에는 조금 뒤 반영됨
- 검색 인덱스는 더 늦게 갱신됨

핵심은 “잠깐 불일치가 있어도 되는가”를 먼저 인정하는 것이다.

즉시 일관성이 필요한 경우도 있지만, 분산 시스템에서는 비용이 너무 커질 수 있다.

### 무엇을 받아들여야 하나

- 일부 화면은 잠시 오래된 데이터를 보여줄 수 있다
- 이벤트 순서가 바뀌거나 중복될 수 있다
- 재처리(retry)가 기본 전제가 된다

그래서 eventual consistency는 단순한 허용이 아니라 **운영 규칙이 있는 불일치**다.

---

## Outbox Pattern

Outbox Pattern은 **DB 변경과 이벤트 기록을 같은 로컬 트랜잭션에 넣고, 나중에 이벤트를 비동기로 발행하는 방식**이다.

전형적인 흐름:

1. 비즈니스 테이블 업데이트
2. outbox 테이블에 이벤트 레코드 저장
3. 같은 트랜잭션으로 커밋
4. 별도 worker가 outbox를 읽어 메시지 브로커에 발행

이 방식의 핵심은 다음이다.

- DB 저장과 이벤트 기록의 원자성을 확보한다
- 브로커 장애가 나도 outbox에 남아 재시도할 수 있다

### 왜 필요한가

만약

- DB는 커밋됐는데
- 메시지 발행은 실패하면

외부 시스템은 변경 사실을 영영 못 받을 수 있다.

반대로 메시지만 나가고 DB가 롤백되면 더 큰 정합성 문제가 생긴다.

Outbox는 이 두 문제를 줄이기 위한 실전 해법이다.

### 꼭 같이 보는 것

- 중복 발행
- 순서 보장
- 소비자 멱등성

Outbox만 넣는다고 끝나지 않는다. 소비자도 같은 이벤트를 두 번 받아도 안전해야 한다.

---

## Saga Pattern

Saga Pattern은 **하나의 큰 분산 트랜잭션을 여러 로컬 트랜잭션으로 쪼개고, 실패 시 보상 작업으로 되돌리는 방식**이다.

예:

- 주문 생성
- 재고 예약
- 결제 승인
- 배송 요청

이 중 하나가 실패하면 이미 끝낸 작업을 되돌리는 보상 작업을 실행한다.

### 보상 작업이란

보상 작업은 원상복구와 비슷하지만 완전히 같지는 않다.

- `결제 승인`의 보상은 `결제 취소`
- `재고 예약`의 보상은 `예약 해제`
- `주문 생성`의 보상은 `주문 취소`

현실적으로는 원래 작업을 그대로 되감는 것이 아니라, **업무적으로 상쇄되는 반대 작업**을 만든다.

### Saga의 한계

- 모든 단계에 보상 로직이 필요하다
- 중간 실패 시 상태 전이가 복잡하다
- 결국 중복 처리와 재시도가 기본이 된다

그래서 Saga는 “분산 트랜잭션 대체제”라기보다 **정합성 비용을 분산하는 설계**에 가깝다.

---

## 실전에서 자주 깨지는 지점

### 1. 메시지 발행 순서

같은 엔티티에 대한 이벤트 순서가 바뀌면 잘못된 상태가 만들어질 수 있다.

예:

- `ORDER_CREATED`
- `ORDER_CANCELLED`

이 순서가 뒤집히면 소비자는 이상 상태를 만들 수 있다.

### 2. 중복 전달

메시지는 적어도 한 번(at-least-once) 전달되는 경우가 많다.

따라서 소비자는 다음을 고려해야 한다.

- 이벤트 ID 저장
- 처리 완료 마킹
- 같은 이벤트 재처리 방지

### 3. 재시도 폭주

일시 장애 시 모든 worker가 동시에 재시도하면 더 큰 장애가 된다.

그래서 백오프, DLQ, 재처리 제한이 필요하다.

### 4. 정합성 기준이 불분명함

“나중에 맞으면 된다”는 말만 있고,

- 어느 시점까지
- 어떤 필드는
- 어떤 순서로

맞아야 하는지 없으면 운영이 어려워진다.

---

## 시니어 관점 질문

- 이 문제는 정말 분산 트랜잭션이 필요한가, 아니면 eventual consistency로 받아들일 수 있는가?
- Outbox와 CDC는 무엇이 다르고, 어디까지를 DB 책임으로 볼 것인가?
- Saga의 보상 작업이 실패하면 어떻게 할 것인가?
- 이벤트 중복과 순서 뒤틀림을 소비자에서 어떻게 방어할 것인가?

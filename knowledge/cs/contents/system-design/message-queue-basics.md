# 메시지 큐 기초 (Message Queue Basics)

> 한 줄 요약: 메시지 큐는 생산자가 보낸 메시지를 소비자가 처리할 때까지 임시로 보관해 서비스 간 결합을 느슨하게 만드는 비동기 통신 수단이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Per-Key Queue vs Direct API Primer](./per-key-queue-vs-direct-api-primer.md)
- [System Design Foundations](./system-design-foundations.md)
- [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md)
- [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
- [Retry Amplification and Backpressure Primer](./retry-amplification-and-backpressure-primer.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- [캐시, 메시징, 관측성](../software-engineering/cache-message-observability.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: message queue basics, 메시지 큐 입문, message queue 뭐예요, producer consumer 기초, kafka 기초, rabbitmq 기초, 비동기 처리 입문, 느슨한 결합, 서비스 디커플링, beginner message queue, 큐 처리 흐름, 메시지 브로커 기초, pub sub 기초, sync vs async queue decision, queue insert not business completion, at least once delivery beginner

---

## 핵심 개념

메시지 큐는 "메시지를 임시로 담아두는 창고"다. 생산자(Producer)가 메시지를 큐에 넣으면, 소비자(Consumer)가 자신의 속도에 맞게 꺼내 처리한다.

입문자가 자주 헷갈리는 지점은 **왜 직접 API 호출(REST)이 아닌 큐를 써야 하는가**이다.

먼저 아래 두 문장을 분리해서 이해하면 훨씬 덜 헷갈린다.

- 응답 마감시간: 사용자가 지금 기다리는 결과를 돌려줘야 하는 시점
- 작업 완료시간: 이메일 발송, 알림 생성처럼 나중에 끝나도 되는 시점

직접 호출 방식의 문제:

- 소비자 서비스가 느리거나 다운되면 생산자 서비스도 블록된다.
- 갑자기 트래픽이 몰리면 소비자가 감당하지 못해 에러가 발생한다.
- 두 서비스의 배포 일정을 맞춰야 한다.

메시지 큐를 두면 생산자는 큐에 넣고 바로 다음 일로 넘어간다. 소비자는 자신의 속도로 처리한다.

---

## 한눈에 보기

```text
생산자 A  ─┐
생산자 B  ─┼──> [메시지 큐] ──> 소비자 1
생산자 C  ─┘              └──> 소비자 2
```

핵심 개념 비교:

| 개념 | 설명 |
|---|---|
| Producer | 메시지를 큐에 넣는 쪽 |
| Consumer | 큐에서 메시지를 꺼내 처리하는 쪽 |
| Broker | 큐를 관리하는 서버 (Kafka, RabbitMQ 등) |
| Topic/Queue | 메시지가 쌓이는 논리적 공간 |

직접 호출과 큐를 초보자 기준으로 비교하면:

| 질문 | 동기 직접 호출 | 큐 기반 비동기 |
|---|---|---|
| 생산자가 소비자 응답을 기다리나 | 기다린다 | 보통 기다리지 않는다 |
| 소비자가 느릴 때 생산자 영향 | 바로 받는다 | 큐가 완충한다 |
| 사용자 응답은 빨라지나 | 소비자 지연 영향을 크게 받는다 | 후처리를 분리하면 보통 빨라진다 |
| 어디까지 완료로 볼지 판단 | 호출 성공 여부로 단순화되기 쉽다 | "큐 적재 성공"과 "업무 완료"를 분리해야 한다 |

---

## 상세 분해

- **비동기 처리**: 생산자는 소비자의 응답을 기다리지 않는다. 주문 생성 API가 이메일 발송 서비스를 직접 호출하는 대신 큐에 이벤트를 넣으면, 이메일 서비스는 자신의 속도로 처리한다.
- **버퍼링**: 트래픽 피크에 메시지가 큐에 쌓이고, 소비자는 처리 가능한 속도로 꺼내간다. 소비자 서버가 다운돼도 메시지는 큐에 보존된다.
- **Pub/Sub 패턴**: 한 메시지를 여러 소비자가 동시에 받는 방식이다. 주문 완료 이벤트를 이메일 서비스, 재고 서비스, 포인트 서비스가 각자 수신한다.
- **Point-to-Point 패턴**: 메시지를 소비자 하나만 받는 방식이다. 작업 큐(Job Queue)에서 주로 쓴다.

---

## 흔한 오해와 함정

- **"메시지 큐를 쓰면 모든 통신이 비동기가 된다"**: 동기 응답이 반드시 필요한 흐름(결제 결과 즉시 반환 등)에는 맞지 않는다. 큐는 응답이 즉시 필요하지 않은 흐름에 적합하다.
- **"큐에 넣었으니 비즈니스도 끝났다"**: 보통 아니다. 큐 적재 성공은 전달 시작 신호이고, 실제 완료는 consumer 작업 성공까지 봐야 한다.
- **"메시지가 큐에 들어가면 무조건 처리된다"**: 소비자가 처리에 실패하면 메시지가 Dead Letter Queue(DLQ)에 쌓이거나 유실될 수 있다. 재시도 정책과 DLQ 모니터링이 필요하다.
- **"큐를 쓰면 순서가 보장된다"**: Kafka는 파티션 내 순서만 보장한다. 여러 파티션에 걸치면 순서가 뒤섞일 수 있다. 순서 보장이 중요하면 파티션 키 설계가 필요하다.

---

## 실무에서 쓰는 모습

가장 흔한 시나리오는 주문 처리에서 이메일 발송을 분리하는 것이다.

1. 사용자가 주문을 완료하면 주문 서비스가 `order.created` 이벤트를 큐에 넣는다.
2. 주문 API는 바로 `201 Created`를 반환하고, 이메일 발송을 기다리지 않는다.
3. 이메일 서비스가 큐에서 이벤트를 꺼내 발송을 처리한다.
4. 이메일 서버가 일시적으로 다운돼도 메시지는 큐에 보존되고, 복구 후 처리된다.
5. 같은 이벤트가 재전달될 수 있으므로 consumer는 `event_id` 기준 dedup을 둔다.

Java 생태계에서는 Spring AMQP(RabbitMQ)와 Spring Kafka가 자주 쓰인다.

---

## 더 깊이 가려면

- 큐가 app/cache/db와 어떤 관계인지 먼저 보고 싶다면 [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md)
- sync/async 경계와 eventual consistency를 주문 흐름으로 묶어 보고 싶다면 [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
- retry owner와 폭증 방지 기준을 보고 싶다면 [Retry Amplification and Backpressure Primer](./retry-amplification-and-backpressure-primer.md)
- 멱등 키, dedup window, replay-safe 처리까지 설계하려면 [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- [캐시, 메시징, 관측성](../software-engineering/cache-message-observability.md) — 메시징과 캐시, 관측성의 실무 연결 포인트
- [System Design Foundations](./system-design-foundations.md) — 큐가 전체 아키텍처에서 어떤 위치에 놓이는지

---

## 면접/시니어 질문 미리보기

> Q: 메시지 큐를 쓰면 어떤 이점이 있나요?
> 의도: 비동기 처리와 디커플링 개념 이해 확인
> 핵심: 생산자와 소비자를 분리해 독립 배포와 독립 확장이 가능하고, 트래픽 피크를 큐로 흡수해 소비자 과부하를 막는다.

> Q: Pub/Sub과 Point-to-Point 큐의 차이는 무엇인가요?
> 의도: 메시지 전달 패턴 구분 능력 확인
> 핵심: Pub/Sub은 하나의 메시지를 여러 소비자가 받고, Point-to-Point는 메시지를 소비자 하나만 가져간다.

> Q: 소비자가 메시지 처리에 실패하면 어떻게 되나요?
> 의도: 장애 처리와 DLQ 개념 인지 확인
> 핵심: 재시도 횟수가 초과되면 Dead Letter Queue에 이동하고, DLQ를 모니터링해 수동 처리하거나 재발행한다.

---

## 한 줄 정리

메시지 큐는 생산자와 소비자를 비동기로 연결해 서비스 간 직접 의존을 끊고, 트래픽 급증과 소비자 장애를 큐에서 흡수하는 디커플링 레이어다.

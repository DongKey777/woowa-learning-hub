# Consistency, Idempotency, and Async Workflow Foundations

> 한 줄 요약: 핵심 상태는 sync 경로에서 먼저 확정하고, 나머지 후처리는 async로 따라오게 하되, eventual consistency와 retry/duplicate는 정상 상황으로 받아들이고 outbox와 idempotency로 안전하게 흡수하는 것이 백엔드 workflow 입문의 기본이다.

retrieval-anchor-keywords: consistency idempotency async workflow foundations, sync vs async workflow primer, eventual consistency primer, idempotency primer, duplicate handling basics, outbox primer beginner, retry duplicate handling, backend workflow consistency basics, queue duplicate handling, order created email search lag, woowacourse backend async flow, curriculum foundation async workflow, system-design-00092, queue insert not done, async workflow beginner route

**난이도: 🟢 Beginner**

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md)
- [캐시 기초](./caching-basics.md)
- [메시지 큐 기초](./message-queue-basics.md)
- [Retry Amplification and Backpressure Primer](./retry-amplification-and-backpressure-primer.md)
- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md)
- [Workflow Orchestration / Saga 설계](./workflow-orchestration-saga-design.md)
- [system-design 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

---

## 먼저 잡을 mental model

초보자는 용어를 따로 외우기보다, 주문 생성 같은 한 흐름으로 묶어 보는 편이 빠르다.

- `sync`는 "사용자에게 지금 확답해야 하는 핵심 상태"를 다룬다.
- `async`는 "응답 뒤에 따라와도 되는 후처리"를 다룬다.
- `eventual consistency`는 async 쪽 화면이나 read model이 잠깐 늦게 따라와도 된다는 뜻이다.
- `retry`는 예외 상황이 아니라 정상 운영에서 계속 생긴다.
- `idempotency`는 같은 요청이나 같은 이벤트가 다시 와도 결과가 한 번의 작업으로 수렴하게 만든다.
- `outbox`는 DB write 성공과 event handoff 누락 사이의 틈을 줄인다.

짧게 외우면 이렇다.

- 핵심 상태는 `sync에서 확정`
- 후처리는 `async로 전파`
- 중복은 `항상 온다`
- 그래서 `idempotency와 dedup이 필요`

---

## 한눈에 보기

| 개념 | 가장 짧은 질문 | 주문 생성 예시 |
|---|---|---|
| Sync 처리 | "사용자에게 지금 무엇을 확답해야 하나?" | 주문 row 저장, 결제 승인 결과 반환 |
| Async 처리 | "응답 뒤에 처리해도 되는가?" | 이메일 발송, 알림 생성, 검색 인덱싱 |
| Eventual consistency | "뒤쪽 화면이 언제 따라오나?" | 검색 결과에는 주문이 몇 초 늦게 보일 수 있음 |
| Idempotency | "같은 요청이 다시 와도 안전한가?" | timeout 뒤 `POST /orders` 재전송 |
| Duplicate handling | "같은 이벤트가 두 번 와도 괜찮은가?" | `order.created`가 재전달돼도 이메일 1번만 발송 |
| Outbox | "DB write와 event handoff를 어떻게 이어 붙이나?" | 주문 row와 outbox row를 같은 트랜잭션에 기록 |

핵심은 sync와 async를 적으로 보지 않는 것이다.
보통은 둘 다 필요하고, 어디까지를 sync로 확정하고 어디부터를 async로 넘길지 경계를 정하는 것이 설계다.

---

## 처음 읽은 뒤 다음 문서 고르기

이 문서를 다 읽고도 막히는 지점은 보통 세 갈래다.

| 막히는 질문 | 다음 문서 | 왜 이 순서가 좋은가 |
|---|---|---|
| "queue 적재 성공과 업무 완료를 어떻게 구분하지?" | [메시지 큐 기초](./message-queue-basics.md) | producer/consumer, redelivery, DLQ 기본 어휘를 먼저 고정할 수 있다 |
| "stale가 허용되는 조회와 안 되는 조회를 어떻게 나누지?" | [캐시 기초](./caching-basics.md) | source of truth vs copy 관점을 먼저 잡고 TTL/invalidation으로 내려갈 수 있다 |
| "write 직후 최신성 보장은 어디까지 필요한가?" | [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md) | sync/async 경계 위에 session/read guarantees를 단계적으로 얹을 수 있다 |

---

## 주문 생성 흐름으로 끝까지 따라가기

가장 단순한 그림은 아래다.

```text
Client
  -> Order API
       -> DB tx(order row + outbox row)   // sync
  <- 201 Created

Relay / Worker
  -> publish order.created
  -> send email
  -> update search index
  -> create notification                  // async
```

이 흐름에서 먼저 구분해야 할 것은 "무엇이 이미 끝났는가"다.

1. 주문 API가 `201 Created`를 돌려줬다면, 보통 주문 자체는 source of truth에 기록됐다는 뜻이다.
2. 하지만 이메일, 알림, 검색 반영까지 모두 끝났다는 뜻은 아니다.
3. 따라서 주문 상세는 바로 보이는데 이메일은 늦게 오거나 검색에는 잠깐 안 보일 수 있다.

이때 초보자가 흔히 "데이터가 틀렸다"와 "아직 안 따라왔다"를 섞어 말한다.
하지만 실무에서는 둘을 구분해야 한다.

- 주문 row 자체가 없으면 sync 실패에 가깝다.
- 주문 row는 있는데 search index가 늦으면 eventual consistency에 가깝다.

즉, eventual consistency는 "무조건 틀린 시스템"이 아니라 **downstream이 뒤에서 합류하는 구조**를 뜻한다.

---

## retry와 duplicate handling은 같이 설계해야 한다

중복은 보통 아래 네 군데에서 생긴다.

| 중복 원인 | 실제로 벌어지는 일 | 기본 대응 |
|---|---|---|
| 클라이언트 timeout | 사용자가 같은 요청을 다시 보낸다 | API idempotency key |
| proxy / gateway retry | 앞단이 자동 재시도한다 | retry owner 축소, budget 제한 |
| worker redelivery | ack 실패나 timeout 후 같은 이벤트를 다시 받는다 | consumer dedup, processed-event 기록 |
| 운영 replay | 사람이 재처리를 다시 눌렀다 | operation id 기준 replay-safe 처리 |

중요한 점은 `queue가 있으니 중복은 broker가 막아 주겠지`라고 보면 안 된다는 것이다.
대부분의 실전 시스템은 적어도 일부 구간에서 at-least-once delivery를 받아들인다.
즉, **중복은 오지 않게 만드는 것보다 와도 안전하게 만드는 쪽**이 현실적이다.

API와 consumer는 멱등성을 잡는 위치도 다르다.

| 경로 | 보통 쓰는 키 | 무엇을 막나 |
|---|---|---|
| 사용자 API | `Idempotency-Key` | 같은 create 요청 재전송 |
| event consumer | `event_id`, `operation_id` | 같은 메시지 재처리 |
| DB write | version, sequence, unique key | 중복 insert, 순서 뒤집힘 |

여기서 자주 헷갈리는 구분:

- idempotency는 **중복 실행 억제**
- ordering은 **서로 다른 요청의 순서 보장**

즉 idempotency가 있어도 `A -> B` 순서가 뒤집히는 문제는 따로 남을 수 있다.

---

## outbox는 왜 같이 나와야 하나

초보자 기준으로 outbox의 핵심은 아주 단순하다.

> "DB에는 썼는데 이벤트는 못 보냈다"는 틈을 줄이기 위해, 업무 row와 outbox row를 같은 트랜잭션에 기록한다.

outbox가 없으면 이런 일이 생긴다.

1. 주문 row insert 성공
2. 바로 broker publish 시도
3. publish 실패
4. 주문은 존재하지만 downstream은 모름

outbox를 두면 보통 이렇게 바뀐다.

1. 주문 row와 outbox row를 같은 트랜잭션에 기록
2. API는 핵심 write 성공만 확인하고 응답
3. relay가 outbox를 읽어 나중에 publish
4. relay는 실패해도 재시도 가능

| 방식 | 장점 | 주의할 점 |
|---|---|---|
| DB write 후 즉시 publish | 단순해 보인다 | dual write gap이 크다 |
| DB + outbox + relay | handoff를 더 durable하게 만든다 | relay/consumer 쪽 dedup은 여전히 필요하다 |

즉 outbox는 workflow 전체를 마법처럼 완료시키는 장치가 아니다.
대신 **핵심 write와 async handoff 사이를 더 안전하게 연결하는 기본 레일**이다.

---

## 무엇을 sync로 두고 무엇을 async로 미루나

beginner 단계에서는 아래 정도로 나누면 충분하다.

| 작업 | 보통 어느 쪽 | 이유 |
|---|---|---|
| 주문 생성 결과, 결제 승인 결과 | Sync | 사용자가 바로 확답을 기다린다 |
| 재고 차감, 금액 확정, 권한 변경 핵심 판정 | Sync 또는 매우 강한 보장 | 틀리면 사고 비용이 크다 |
| 이메일, 푸시, 웹훅, 분석 적재 | Async | 조금 늦어도 서비스 의미가 유지된다 |
| 검색 인덱싱, 대시보드 projection | Async | read model은 보통 뒤에서 따라온다 |

판단 기준도 어렵지 않다.

- 지금 틀리면 사용자가 다시 누르거나 돈을 두 번 낼 수 있나
- 응답 시간을 줄이기 위해 뒤로 미뤄도 제품 의미가 유지되나
- 늦게 반영될 때 사용자에게 설명 가능한가

이 세 질문으로 sync/async 경계를 먼저 잡고, 그다음에 consistency와 retry 전략을 얹으면 된다.

---

## 자주 헷갈리는 오해

- `async면 더 빠른 시스템이다`: 보통 응답은 빨라지지만, 전체 완료 시점은 더 늦어진다.
- `eventual consistency면 데이터가 틀린 것이다`: 종종 틀린 것이 아니라 아직 projection이 안 따라온 상태다.
- `idempotency가 있으면 순서도 안전하다`: 아니다. 중복과 순서는 다른 문제다.
- `queue를 쓰면 duplicate는 broker가 해결한다`: 아니다. consumer dedup이 필요하다.
- `outbox를 넣으면 exactly-once가 된다`: 아니다. 보통은 handoff를 더 안전하게 만들 뿐이고, 중복 처리 설계는 여전히 필요하다.

---

## 코드로 보면 더 쉬운 최소 예시

```pseudo
function createOrder(request):
  if seen(request.idempotencyKey):
    return replayPreviousResult(request.idempotencyKey)

  tx.begin()
  order = orders.insert(request)
  outbox.insert({
    eventId: newEventId(),
    type: "order.created",
    orderId: order.id
  })
  tx.commit()

  saveResult(request.idempotencyKey, order.id)
  return created(order.id)
```

```pseudo
function handleOrderCreated(event):
  if processed(event.eventId):
    return

  sendEmail(event.orderId)
  markProcessed(event.eventId)
```

이 예시는 완전한 구현이 아니라 beginner용 감각만 보여 준다.

- API 쪽은 같은 create 요청 재전송을 idempotency로 흡수한다.
- async 쪽은 같은 이벤트 재전달을 processed-event 기록으로 흡수한다.
- outbox는 sync write와 async handoff를 묶는 연결점이다.

---

## 더 깊이 가려면

- sync/async 박스 관계를 먼저 다시 보고 싶다면 [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md)
- queue와 producer/consumer 용어부터 다시 잡고 싶다면 [메시지 큐 기초](./message-queue-basics.md)
- retry storm와 budget owner를 같이 보고 싶다면 [Retry Amplification and Backpressure Primer](./retry-amplification-and-backpressure-primer.md)
- write 직후 읽기 최신성을 보고 싶다면 [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- outbox metadata를 read freshness와 연결하고 싶다면 [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md)
- API/worker 멱등성을 더 깊게 설계하고 싶다면 [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- CDC, relay, replay까지 확장하고 싶다면 [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md)
- 분산 workflow 보상 흐름까지 보고 싶다면 [Workflow Orchestration / Saga 설계](./workflow-orchestration-saga-design.md)

---

## 면접/시니어 질문 미리보기

> Q: 주문 생성에서 무엇을 sync로 두고 무엇을 async로 넘기나요?
> 의도: 사용자 확답 경계와 후처리 분리 감각 확인
> 핵심: 주문 존재와 결제 확정 같은 핵심 상태는 sync로 먼저 결정하고, 이메일/알림/검색 반영 같은 후처리는 async로 넘긴다.

> Q: eventual consistency는 언제 괜찮고 언제 위험한가요?
> 의도: 제품 흐름별 stale 허용 범위 판단 확인
> 핵심: 검색/알림/대시보드처럼 잠깐 늦어도 되는 read model에는 흔하지만, 금전/재고/권한처럼 틀리면 사고가 나는 핵심 경로는 더 강한 보장이 필요하다.

> Q: outbox가 있는데 왜 idempotency도 필요하죠?
> 의도: handoff 안정성과 duplicate suppression을 분리하는지 확인
> 핵심: outbox는 DB write와 event handoff를 더 안전하게 잇는 장치이고, retry나 redelivery로 생기는 중복 실행 자체는 API/consumer idempotency가 따로 막아야 한다.

> Q: queue를 쓰면 왜 duplicate를 기본값처럼 생각해야 하나요?
> 의도: at-least-once delivery와 worker retry 감각 확인
> 핵심: ack 누락, timeout, redelivery, 운영 replay가 계속 생기므로 "중복이 안 온다"보다 "와도 안전하다"를 기준으로 설계해야 한다.

## 한 줄 정리

핵심 상태는 sync에서 먼저 확정하고, 나머지 후처리는 async로 흘리되, eventual consistency와 duplicate를 정상 운영의 일부로 받아들이고 outbox와 idempotency로 안전하게 수렴시키는 것이 backend workflow 입문의 기본이다.

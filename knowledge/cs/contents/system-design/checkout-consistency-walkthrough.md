---
schema_version: 3
title: Checkout Consistency Walkthrough
concept_id: system-design/checkout-consistency-walkthrough
canonical: false
category: system-design
difficulty: beginner
doc_role: deep_dive
level: beginner
language: mixed
source_priority: 82
mission_ids:
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- checkout consistency walkthrough
- checkout consistency beginner
- cart version check checkout
- cart version mismatch checkout
aliases:
- checkout consistency walkthrough
- checkout consistency beginner
- cart version check checkout
- cart version mismatch checkout
- idempotency key checkout
- duplicate checkout retry
- read after write order confirmation
- checkout stale confirmation
- order placed but not visible
- cart version if-match checkout
- expected version cart checkout
- checkout duplicate submit
symptoms:
- checkout 요청이 timeout 뒤 재시도되어 주문이나 결제가 두 번 생길까 봐 불안하다
- cart version, idempotency key, read-after-write 확인을 각각 따로만 이해하고 한 흐름으로 연결하지 못한다
- 주문 생성은 성공했는데 확인 화면이나 목록에서 방금 주문이 보이지 않는다
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/system-design-foundations.md
- contents/system-design/consistency-idempotency-async-workflow-foundations.md
- contents/system-design/writes-follow-reads-primer.md
- contents/system-design/write-order-vs-precondition-primer.md
- contents/system-design/read-after-write-consistency-basics.md
- contents/system-design/read-after-write-routing-primer.md
- contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md
- contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md
- contents/system-design/conditional-write-status-code-bridge.md
- contents/database/compare-and-set-version-columns.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Checkout Consistency Walkthrough 설계 핵심을 설명해줘
- checkout consistency walkthrough가 왜 필요한지 알려줘
- Checkout Consistency Walkthrough 실무 트레이드오프는 뭐야?
- checkout consistency walkthrough 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Checkout Consistency Walkthrough를 다루는 deep_dive 문서다. checkout에서는 `cart version check`, `idempotency key`, `read-after-write confirmation`이 각각 다른 사고를 막고, 셋을 한 흐름으로 이어야 "중복 결제도 없고 방금 주문도 바로 보이는" 경험을 만들 수 있다. 검색 질의가 checkout consistency walkthrough, checkout consistency beginner, cart version check checkout, cart version mismatch checkout처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Checkout Consistency Walkthrough

> 한 줄 요약: checkout에서는 `cart version check`, `idempotency key`, `read-after-write confirmation`이 각각 다른 사고를 막고, 셋을 한 흐름으로 이어야 "중복 결제도 없고 방금 주문도 바로 보이는" 경험을 만들 수 있다.

retrieval-anchor-keywords: checkout consistency walkthrough, checkout consistency beginner, cart version check checkout, cart version mismatch checkout, idempotency key checkout, duplicate checkout retry, read after write order confirmation, checkout stale confirmation, order placed but not visible, cart version if-match checkout, expected version cart checkout, checkout duplicate submit, checkout timeout retry safe, checkout confirmation primary fallback, beginner checkout flow consistency

**난이도: 🟢 Beginner**

## 미션 진입 증상

| shopping-cart 장면 | 이 문서에서 먼저 잡을 질문 |
|---|---|
| checkout 버튼을 두 번 눌렀다 | 같은 attempt를 replay-safe하게 흡수하는가 |
| cart를 본 뒤 상품/수량이 바뀌었다 | checkout precondition이 있는가 |
| 주문 완료 직후 확인 화면이 비어 있다 | read-after-write 경로가 보장되는가 |

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
- [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)
- [Write Order vs Precondition Primer](./write-order-vs-precondition-primer.md)
- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
- [Conditional Write Status Code Bridge](./conditional-write-status-code-bridge.md)
- [Compare-and-Set와 Version Columns](../database/compare-and-set-version-columns.md)

---

## 먼저 잡을 mental model

checkout의 세 질문은 서로 다르다.

1. 내가 본 장바구니가 아직 최신인가
2. 같은 checkout 요청이 두 번 실행되지는 않는가
3. 주문 성공 직후 확인 화면에서 새 주문이 바로 보이는가

각 질문의 담당 장치는 이렇게 나눈다.

| 질문 | 대표 장치 | 막는 사고 |
|---|---|---|
| 내가 본 장바구니가 아직 최신인가 | `cart version`, `If-Match`, `expected_version` | 예전 장바구니 기준 결제 |
| 같은 checkout 요청이 두 번 실행되지는 않는가 | `Idempotency-Key` | timeout 뒤 중복 주문/중복 결제 |
| 주문 성공 직후 확인 화면에서 새 주문이 바로 보이는가 | read-after-write routing, primary fallback, recent-write pinning | "주문은 됐는데 확인 화면엔 안 보임" |

짧게 외우면 이렇다.

- version check는 `예전 기준선`을 막는다
- idempotency key는 `같은 요청 재실행`을 막는다
- read-after-write confirmation은 `성공 직후 stale read`를 막는다

셋 중 하나만 있어도 일부 문제는 남는다.

---

## 한 번에 따라가는 전체 흐름

가장 단순한 checkout 흐름을 먼저 보자.

```text
1. 사용자: cart v12를 본다
2. 사용자: 결제 버튼 클릭
3. 서버: "지금도 cart v12인가?" 확인
4. 서버: 같은 idempotency key를 이미 처리했는지 확인
5. 서버: 주문/결제 기록을 commit
6. 사용자: 주문 확인 화면으로 이동
7. 서버: 방금 쓴 주문이 보이는 read path로 확인 화면 응답
```

이를 HTTP 느낌으로 적으면 더 선명하다.

```http
GET /carts/123
ETag: "cart-v12"
```

```http
POST /carts/123/checkout
If-Match: "cart-v12"
Idempotency-Key: checkout:cart-123:user-9:attempt-44

{
  "paymentMethodId": "pm_7",
  "shippingAddressId": "addr_3"
}
```

```http
201 Created
Location: /orders/9001
```

```http
GET /orders/9001
X-Recent-Write: order-9001
```

여기서 포인트는 `checkout 성공`이 한 개의 기술만으로 만들어지지 않는다는 점이다.

- checkout 요청을 받기 전에는 stale cart를 막아야 한다
- checkout 실행 중에는 duplicate retry를 흡수해야 한다
- checkout 직후에는 stale confirmation read를 막아야 한다

---

## 단계별로 끊어 보기

### 1. cart version check: "내가 본 장바구니로 결제해도 되나?"

사용자가 cart를 열었을 때 본 수량, 가격, 쿠폰 가능 여부가 checkout 판단의 기준선이 된다.
그래서 checkout write는 보통 "나는 `cart-v12`를 보고 계산했다"는 사실을 같이 보낸다.

| 상황 | version check 없음 | version check 있음 |
|---|---|---|
| 다른 탭에서 수량이 바뀜 | 예전 총액 기준 checkout이 들어갈 수 있음 | `412`나 재조회 유도로 막음 |
| 재고 반영으로 cart가 바뀜 | 이미 불가능한 구성으로 결제가 시도될 수 있음 | 최신 cart 확인 후 다시 판단 |
| 쿠폰 조건이 중간에 깨짐 | 오래된 할인 기준으로 주문 생성 가능 | 최신 version 기준 재계산 |

초보자용 한 줄:

> cart version check는 "이 사용자가 본 화면이 아직 유효한가"를 묻는다.

이 단계는 [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)와 거의 같은 질문이다.

### 2. idempotency key: "같은 checkout 버튼 클릭이 두 번 처리되나?"

사용자가 결제 버튼을 누른 뒤 가장 흔한 현실은 timeout과 재시도다.

```text
첫 요청은 실제로 주문을 만들었다
하지만 응답이 늦거나 끊겼다
사용자는 실패로 보고 다시 눌렀다
```

이때 version check만 있으면 부족하다.
두 요청 모두 같은 최신 cart version을 들고 올 수 있기 때문이다.

| 질문 | version check만 있을 때 | idempotency key가 있을 때 |
|---|---|---|
| 같은 요청 재전송인가 | 구분 못 함 | 같은 operation으로 합침 |
| 응답 유실 뒤 재시도인가 | 새 checkout으로 오해 가능 | 이전 결과 replay 가능 |
| 중복 결제/중복 주문 위험 | 남아 있음 | 크게 줄어듦 |

초보자용 한 줄:

> idempotency key는 "같은 checkout 시도라면 결과를 한 번으로 수렴시켜라"는 계약이다.

즉:

- cart version은 `기준선 유효성`
- idempotency key는 `재시도 중복 흡수`

를 맡는다.

### 3. read-after-write confirmation: "주문은 됐는데 왜 확인 화면엔 안 보이지?"

checkout이 성공했더라도, 주문 확인 화면을 replica나 stale cache에서 읽으면 바로 안 보일 수 있다.

```text
POST /checkout -> primary commit 완료
302 -> /orders/9001
GET /orders/9001 -> stale replica read
```

이때 사용자는 흔히 이렇게 오해한다.

- 결제가 실패했나?
- 버튼이 안 눌렸나?
- 다시 결제해야 하나?

## 단계별로 끊어 보기 (계속 2)

그래서 checkout 직후 confirmation read는 일반 목록 조회보다 더 신선한 경로가 필요하다.

| 확인 화면 정책 | 장점 | 주의할 점 |
|---|---|---|
| 짧은 primary fallback | 가장 이해하기 쉽다 | primary read 부하 관리 필요 |
| recent-write pinning | 필요한 세션만 보호 가능 | 세션/엔티티별 freshness 힌트 관리 필요 |
| stale 허용 replica read | 확장성은 좋다 | checkout 직후 UX와 중복 시도 위험이 커짐 |

초보자용 한 줄:

> read-after-write confirmation은 "성공한 주문이 바로 보이게 하는 마지막 한 걸음"이다.

---

## 왜 셋을 같이 써야 하나

아래는 실제로 자주 섞이는 오해를 분리한 표다.

| 오해 | 왜 틀렸나 | 실제로 필요한 것 |
|---|---|---|
| `If-Match`만 있으면 중복 결제가 없다 | stale cart는 막아도 같은 요청 재시도는 막지 못한다 | idempotency key |
| idempotency key만 있으면 안전하다 | 같은 요청은 합치지만, 예전 cart 기준 checkout은 막지 못한다 | cart version check |
| checkout이 `201`이면 확인 화면도 바로 최신이다 | write 성공과 다음 read 최신성은 다른 문제다 | read-after-write routing |
| confirmation을 primary로만 읽으면 모든 문제가 끝난다 | write 전 stale cart와 중복 retry 문제는 여전히 남는다 | version check + idempotency도 필요 |

한 문장으로 합치면:

> checkout consistency는 "결제 전에 stale 판단을 막고, 결제 중 duplicate retry를 흡수하고, 결제 뒤 stale confirmation을 막는 3단계 설계"다.

---

## 가장 단순한 서버 흐름 예시

```pseudo
function checkout(cartId, request):
  assertCartVersion(cartId, request.ifMatch)

  replay = idempotencyStore.find(request.idempotencyKey)
  if replay.exists():
    return replay.response

  idempotencyStore.claim(request.idempotencyKey)

  order = createOrderFromCurrentCart(cartId)
  payment = charge(order)

  saveCheckoutResult(request.idempotencyKey, order.id, payment.status)
  markRecentWrite(order.id, now + 3 seconds)

  return created("/orders/" + order.id)
```

```pseudo
function getOrderConfirmation(orderId, session):
  if session.hasRecentWrite(orderId):
    return primary.read(orderId)

  return replica.read(orderId)
```

이 코드는 production-ready 설계라기보다, 책임 분리를 보여 주는 카드로 보면 된다.

- `assertCartVersion`: 오래된 cart 기준 checkout 방지
- `idempotencyStore`: 같은 checkout 재시도 흡수
- `markRecentWrite`: 직후 확인 read를 더 신선하게 라우팅

---

## 실전 시나리오로 붙여 보기

### 시나리오 1. 다른 탭에서 cart가 바뀐 뒤 checkout

- 탭 A는 `cart-v12`를 봤다
- 탭 B가 수량을 바꿔 `cart-v13`이 됐다
- 탭 A가 예전 화면으로 checkout을 누른다

핵심 보호:

- `If-Match: cart-v12` mismatch로 거절
- 최신 cart를 다시 읽고 총액/재고를 재계산

### 시나리오 2. 결제는 성공했는데 응답이 끊김

- 첫 checkout은 실제로 주문 `9001`을 만들었다
- 네트워크 timeout으로 사용자는 실패로 본다
- 같은 버튼을 다시 누른다

핵심 보호:

- 같은 `Idempotency-Key`면 주문 `9001` 결과를 replay
- 새 주문 `9002`를 만들지 않음

### 시나리오 3. 주문은 성공했는데 확인 화면에 안 보임

- `POST /checkout`은 이미 commit됐다
- `GET /orders/9001`이 replica lag에 걸렸다

핵심 보호:

- checkout 직후 몇 초간 primary fallback
- 또는 `recent-write` 힌트로 fresher path 선택

---

## 자주 헷갈리는 포인트

- `version`과 `idempotency key`는 대체재가 아니다. 하나는 stale 기준선을 막고, 다른 하나는 duplicate retry를 막는다.
- `idempotency key`가 있어도 read-after-write가 자동 해결되지는 않는다. 중복 없이 주문 하나만 만들어도, 다음 read가 stale이면 사용자는 다시 시도할 수 있다.
- `read-after-write`를 붙여도 stale checkout write는 막지 못한다. 확인 화면이 최신이어도, 그 주문이 예전 cart 기준으로 만들어졌다면 이미 늦다.
- `201 Created`는 보통 write 성공이지, 모든 projection/cache/replica가 최신이라는 뜻이 아니다.

---

## 처음 설계할 때의 최소 조합

beginner 단계에서 가장 단순하게 시작하면 아래 정도로 충분하다.

| 구간 | 최소 시작 설계 |
|---|---|
| cart 조회 -> checkout 요청 | `ETag`/`If-Match` 또는 `expected_version` |
| checkout 처리 | idempotency key 저장소 + replay |
| checkout 성공 직후 주문 확인 | 짧은 primary fallback 또는 recent-write pinning |

이후 더 깊게 가면 아래 질문이 열린다.

- payment provider에도 같은 idempotency key를 전달할까
- confirmation read를 primary 대신 safe follower로 보낼 수 있을까
- order projection/cache refill에도 freshness metadata를 남길까

이 문서에서는 여기까지를 beginner 기준의 1차 설계로 본다.

## 한 줄 정리

checkout consistency를 초보자 관점에서 풀면, `cart version check`는 예전 장바구니 기준 결제를 막고, `idempotency key`는 같은 checkout 재시도를 한 번의 결과로 모으고, `read-after-write confirmation`은 주문 성공 직후 확인 화면이 뒤늦게 보이는 문제를 막는 세 단계다.

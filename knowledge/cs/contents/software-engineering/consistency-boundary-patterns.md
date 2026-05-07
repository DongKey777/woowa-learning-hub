---
schema_version: 3
title: Consistency Boundary Patterns
concept_id: software-engineering/consistency-boundary
canonical: true
category: software-engineering
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 89
mission_ids:
- missions/payment
review_feedback_tags:
- consistency-boundary
- outbox-inbox
- saga
aliases:
- Consistency Boundary Patterns
- consistency boundary
- transactional boundary eventual consistency
- strong consistency vs eventual consistency
- outbox inbox saga
- 정합성 경계 패턴
symptoms:
- 모든 변경을 한 트랜잭션에 넣으려 해 시스템 경계와 분산 비용이 커지거나, 반대로 eventual consistency를 나중에 맞추면 된다는 말로 안전 조건을 생략해
- 즉시 일관성이 필요한 잔액 차감, 재고 예약, 상태 전이와 알림/정산/외부 동기화 같은 비동기 처리 가능 경계를 구분하지 못해
- outbox/inbox, idempotency, saga compensation 없이 boundary 밖 이벤트와 재시도, 중복, 순서 역전을 처리하려 해
intents:
- design
- comparison
- deep_dive
prerequisites:
- software-engineering/ddd-hexagonal-consistency
- software-engineering/outbox-inbox-domain-events
next_docs:
- software-engineering/idempotency-retry-consistency-boundaries
- software-engineering/saga-compensation-failure-handling
- database/transaction-basics
linked_paths:
- contents/software-engineering/ddd-hexagonal-consistency.md
- contents/software-engineering/outbox-inbox-domain-events.md
- contents/software-engineering/idempotency-retry-consistency-boundaries.md
- contents/software-engineering/saga-compensation-failure-handling.md
- contents/software-engineering/monolith-to-msa-failure-patterns.md
- contents/database/transaction-basics.md
confusable_with:
- software-engineering/ddd-hexagonal-consistency
- software-engineering/idempotency-retry-consistency-boundaries
- software-engineering/saga-compensation-failure-handling
forbidden_neighbors: []
expected_queries:
- consistency boundary는 어디까지 strong consistency로 묶고 어디부터 eventual consistency로 흘릴지 정하는 패턴이라는 뜻이 뭐야?
- 주문 생성, 결제 승인, 재고 반영, 알림 발송에서 어떤 것은 한 트랜잭션이고 어떤 것은 outbox saga로 빼야 해?
- eventual consistency는 늦어도 되는 것이 아니라 늦어도 안전해야 한다는 말의 조건은 뭐야?
- outbox/inbox와 idempotency는 consistency boundary 밖 메시징 중복과 유실 위험을 어떻게 줄여?
- saga compensation은 여러 서비스 workflow에서 어떤 failure handling을 책임져?
contextual_chunk_prefix: |
  이 문서는 strong consistency, eventual consistency, outbox/inbox, idempotency, saga compensation을 통해 transaction boundary와 async boundary를 설계하는 advanced deep dive다.
---
# Consistency Boundary Patterns

> 한 줄 요약: consistency boundary는 모든 것을 한 트랜잭션에 넣지 않기 위해, 어디까지를 즉시 일관성으로 묶고 어디부터는 결국 일관성으로 흘릴지 패턴으로 정리하는 일이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
> - [Saga Compensation Failure Handling](./saga-compensation-failure-handling.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)

> retrieval-anchor-keywords:
> - consistency boundary
> - transactional boundary
> - eventual consistency
> - strong consistency
> - saga
> - outbox
> - inbox
> - idempotency

## 핵심 개념

모든 변경을 강한 일관성으로 묶으면 시스템이 느려지고, 분산될수록 비용이 급격히 늘어난다.

consistency boundary는 다음을 구분한다.

- 한 트랜잭션에 꼭 들어가야 하는 것
- 이벤트나 메시지로 흘려도 되는 것
- 보상이나 재시도가 필요한 것

즉 패턴의 핵심은 **정합성을 지키면서도 변경 범위를 줄이는 것**이다.

---

## 깊이 들어가기

### 1. strong consistency가 필요한 곳은 좁아야 한다

예:

- 잔액 차감
- 재고 예약
- 상태 전이의 핵심 규칙

이런 곳은 즉시 일관성이 중요하다.

### 2. eventual consistency는 늦어도 되는 것이 아니라, 늦어도 안전해야 한다

eventual consistency는 "나중에 맞추자"가 아니다.

중요한 것은:

- 중복 처리해도 안전한가
- 순서가 바뀌어도 안전한가
- 지연이 있어도 사용자 경험이 허용되는가

### 3. outbox/inbox는 boundary를 넘는 기본 패턴이다

트랜잭션 안에서 outbox를 남기고, consumer는 inbox나 deduplication으로 중복을 막는다.

이 패턴은 데이터 정합성과 메시지 전달 사이의 간극을 줄인다.

### 4. saga는 boundary 밖의 상태 전이에 대한 패턴이다

여러 서비스가 관여하는 workflow는 한 번에 롤백되지 않는다.
그래서 compensation과 상태 추적이 필요하다.

### 5. boundary는 도메인 규칙과 사용자 경험을 같이 봐야 한다

어떤 작업은 기술적으로 분리 가능해도, UX 상으로는 한 번에 보여줘야 할 수 있다.

예:

- 주문 생성은 즉시
- 정산 반영은 지연 허용
- 알림은 eventual

---

## 실전 시나리오

### 시나리오 1: 주문과 결제를 분리한다

주문 생성은 강한 일관성, 결제 승인과 재고 반영은 saga와 outbox로 이어질 수 있다.

### 시나리오 2: 외부 시스템과 동기화한다

결과를 즉시 반영해야 하는 것이 아니면, 메시지와 재시도로 boundary를 넓힌다.

### 시나리오 3: 재처리와 중복이 잦다

idempotency와 inbox가 없으면 boundary 밖의 불안정이 커진다.

---

## 코드로 보기

```text
transaction:
  save order
  write outbox

async:
  publish event
  consume idempotently
  reconcile if needed
```

정합성 경계는 트랜잭션의 범위와 메시징 패턴을 함께 결정한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| strong consistency 넓게 | 단순하다 | 느리고 비싸다 | 아주 작은 시스템 |
| eventual consistency 넓게 | 확장성이 좋다 | 복잡하다 | 분산 시스템 |
| 혼합 boundary | 현실적이다 | 설계가 필요하다 | 운영 중 서비스 |

consistency boundary patterns는 "정합성을 포기할 것인가"가 아니라 **정합성을 어디에서 어떻게 보장할 것인가**의 문제다.

---

## 꼬리질문

- 즉시 일관성이 정말 필요한 경계는 어디인가?
- outbox/inbox 없이 버틸 수 있는가?
- saga compensation이 필요한 workflow는 무엇인가?
- 지연된 정합성이 사용자 경험에 어떤 영향을 주는가?

## 한 줄 정리

Consistency boundary patterns는 강한 일관성과 eventual consistency를 분리해, 어디까지를 한 번에 묶고 어디부터 비동기적으로 흘릴지 결정하는 설계다.

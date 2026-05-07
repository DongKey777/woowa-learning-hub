---
schema_version: 3
title: Backend Module API DTO Boundary Drill
concept_id: software-engineering/backend-module-api-dto-boundary-drill
canonical: false
category: software-engineering
difficulty: intermediate
doc_role: drill
level: intermediate
language: mixed
source_priority: 74
mission_ids:
- missions/shopping-cart
- missions/payment
- missions/backend
review_feedback_tags:
- module-api
- dto-boundary
- aggregate-leakage
- anti-corruption
aliases:
- backend module API DTO boundary drill
- module DTO aggregate leakage drill
- order payment module contract exercise
- aggregate leak DTO boundary drill
- 모듈 API DTO 경계 드릴
symptoms:
- payment 모듈이 order aggregate를 직접 받아 내부 필드에 의존한다
- module API가 DTO인지 domain object인지 구분되지 않아 한 모듈 수정이 다른 모듈까지 깨진다
- 같은 코드베이스라는 이유로 package/internal boundary를 무시한다
intents:
- drill
- design
- comparison
prerequisites:
- software-engineering/module-api-dto-patterns
- software-engineering/service-layer-basics
next_docs:
- software-engineering/api-contract-testing
- software-engineering/ports-and-adapters-beginner-primer
- software-engineering/payment-gateway-outbound-port-mission-bridge
linked_paths:
- contents/software-engineering/module-api-dto-patterns.md
- contents/software-engineering/service-layer-basics.md
- contents/software-engineering/api-contract-testing-consumer-driven.md
- contents/software-engineering/ports-and-adapters-beginner-primer.md
- contents/software-engineering/payment-gateway-outbound-port-mission-bridge.md
confusable_with:
- software-engineering/module-api-dto-patterns
- software-engineering/ports-and-adapters-beginner-primer
- software-engineering/api-contract-testing
forbidden_neighbors:
- contents/software-engineering/layered-architecture-basics.md
expected_queries:
- backend module API DTO boundary를 문제로 연습하고 싶어
- payment 모듈이 order aggregate를 직접 받으면 왜 위험해?
- 같은 코드베이스 안에서도 module DTO를 따로 두는 기준을 드릴해줘
- aggregate leakage와 anti-corruption boundary를 shopping-cart payment 장면으로 풀어줘
- module API contract test는 언제 필요해?
contextual_chunk_prefix: |
  이 문서는 backend module API DTO boundary drill이다. order/payment module,
  aggregate leakage, command/result DTO, internal package dependency,
  anti-corruption boundary, contract test 같은 미션 리뷰 문장을 경계 판별
  문제로 매핑한다.
---
# Backend Module API DTO Boundary Drill

> 한 줄 요약: 같은 코드베이스 안 모듈이라도, 다른 모듈 aggregate를 직접 잡으면 내부 모델 변경이 API 계약 변경처럼 번진다.

**난이도: Intermediate**

## 문제 1

상황:

```text
PaymentService.markPaid(Order order, Payment payment)를 호출한다.
PaymentService는 Order 내부 상태와 메서드를 직접 읽는다.
```

답:

aggregate leakage다. payment 모듈은 주문 내부 모델보다 `orderId`, `amount`, `payableStatus` 같은 필요한 계약만 받는 command/view DTO를 먼저 고려한다.

## 문제 2

상황:

```text
Order aggregate field 이름을 바꿨더니 payment, settlement, notification 모듈 테스트가 같이 깨진다.
```

답:

module boundary가 내부 구조에 붙어 있다. 변경이 전파되지 않게 module API DTO나 query view를 두고, contract test로 공개 shape를 잠근다.

## 문제 3

상황:

```text
모듈이 같은 monolith 안에 있으니 DTO를 만들면 overengineering이라고 한다.
```

답:

항상 DTO가 정답은 아니지만, 독립 변경 가능성이 있거나 다른 bounded context 언어가 섞이면 DTO/command/result가 비용을 줄일 수 있다.
단순 CRUD helper라면 과한 분리는 피한다.

## 빠른 체크

| 신호 | 경계 선택 |
|---|---|
| 같은 aggregate 내부 필드를 여러 모듈이 읽음 | DTO/query view |
| 호출 의도만 필요 | command/result |
| 외부 provider 언어 번역 | anti-corruption adapter |
| 공개 shape가 중요 | contract test |

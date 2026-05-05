---
schema_version: 3
title: "shopping-cart 주문 생성 실패 응답 ↔ 입력 검증과 도메인 불변식 브릿지"
concept_id: "software-engineering/shopping-cart-checkout-validation-domain-invariant-bridge"
canonical: false
category: "software-engineering"
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
  - missions/shopping-cart
review_feedback_tags:
  - input-vs-domain-validation
  - checkout-conflict-mapping
  - controller-vs-service-boundary
aliases:
  - shopping-cart 입력 검증 경계
  - 장바구니 checkout 400 409 경계
  - shopping-cart validation vs domain rule
  - 주문 생성 검증 위치
  - 쿠폰 재사용 conflict 응답
symptoms:
  - paymentMethod 빈값이랑 품절을 왜 같은 검증으로 다루면 안 되나요
  - shopping-cart에서 400이랑 409를 어디서 나눠야 할지 모르겠어요
  - 쿠폰 이미 사용됨을 DTO validator에서 막아도 되나 헷갈려요
intents:
  - mission_bridge
  - comparison
  - troubleshooting
prerequisites:
  - software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
  - software-engineering/service-layer-basics
next_docs:
  - software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
  - software-engineering/shopping-cart-checkout-service-layer-bridge
  - database/shopping-cart-payment-idempotency-stock-bridge
linked_paths:
  - contents/software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md
  - contents/software-engineering/shopping-cart-checkout-service-layer-bridge.md
  - contents/spring/spring-validation-binding-error-pipeline.md
  - contents/database/shopping-cart-payment-idempotency-stock-bridge.md
  - contents/database/shopping-cart-coupon-apply-once-unique-claim-bridge.md
confusable_with:
  - software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
  - database/shopping-cart-payment-idempotency-stock-bridge
  - database/shopping-cart-coupon-apply-once-unique-claim-bridge
forbidden_neighbors: []
expected_queries:
  - shopping-cart에서 `paymentMethod` 누락과 품절을 왜 같은 validator로 처리하면 안 돼?
  - 장바구니 checkout API에서 400과 409를 어떤 기준으로 나눠 설명해야 해?
  - reviewer가 쿠폰 중복 사용은 서비스 규칙이라고 했는데 무슨 뜻이야?
  - 주문 생성 request 검증과 재고 부족 판단 중 어디가 먼저야?
  - shopping-cart 미션에서 DTO 검증과 비즈니스 충돌을 어떻게 분리해?
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션에서 checkout 요청을 받을 때
  `paymentMethod` 누락, 수량 0 같은 입력 오류와 품절, 이미 사용한 쿠폰,
  취소된 주문 재결제 같은 상태 충돌을 한데 섞어 보는 학습자를 위한
  mission_bridge다. 멘토가 "DTO validator에서 다 하지 말고 service 규칙으로
  올리라"고 말할 때, 어떤 실패가 request shape 문제이고 어떤 실패가 현재
  시스템 상태와 부딪히는 business conflict인지 shopping-cart 장면으로
  연결한다.
---

# shopping-cart 주문 생성 실패 응답 ↔ 입력 검증과 도메인 불변식 브릿지

## 한 줄 요약

> shopping-cart checkout에서 `400`은 보통 요청 자체가 입구를 통과하지 못한 경우이고, `409`는 요청 형식은 맞지만 현재 재고, 쿠폰, 주문 상태와 충돌한 경우다. 그래서 DTO validator는 문 앞 검사, checkout service와 domain rule은 상태 충돌 판정을 맡는 편이 경계가 선명하다.

## 미션 시나리오

shopping-cart 미션에서 주문 생성이나 결제 승인 요청을 붙이면 학습자는 자주
두 종류 실패를 한 군데에 모은다. `paymentMethod`가 비어 있거나 수량이 0인
요청도 있고, 이미 소진된 쿠폰을 다시 쓰거나 마지막 재고가 방금 팔린 경우도
있기 때문이다.

리뷰에서는 "`@Valid`나 custom validator로 품절까지 막으려 하지 말라",
"controller가 repository를 직접 조회해 충돌을 판단하지 말라"는 코멘트가
자주 붙는다. 겉으로는 둘 다 "주문 생성 실패"지만, 하나는 요청 한 장만
보면 알 수 있고 다른 하나는 현재 저장 상태를 읽어야만 알 수 있다.

예를 들어 `paymentMethod` 누락, 음수 수량, 잘못된 쿠폰 코드 형식은 request
shape 문제다. 반면 "이 쿠폰은 이미 claim됐다", "재고가 0이다", "이미
`CANCELLED`인 주문을 다시 `PAID`로 바꾸려 한다"는 현재 상태와의 충돌이라서
service나 domain rule 질문으로 올라간다.

## CS concept 매핑

| shopping-cart 장면 | 먼저 묻는 질문 | 더 가까운 CS 개념 | 보통 책임 위치 | 흔한 응답 |
| --- | --- | --- | --- | --- |
| `paymentMethod`가 비어 있음 | 요청을 읽을 수 있나 | 입력 검증, request validation | controller / DTO | `400` |
| 수량이 0 또는 음수 | 문법상 최소 조건을 넘나 | 형식/범위 검증 | controller / DTO | `400` |
| 이미 사용한 쿠폰 재적용 | 현재 상태와 충돌하나 | 도메인 규칙, business conflict | service / domain | `409` |
| 마지막 재고가 방금 소진됨 | 최신 저장 상태가 허용하나 | invariant + write arbitration | service + DB | `409` |
| 취소된 주문을 다시 결제 완료로 변경 | 지금 가능한 상태 전이인가 | 도메인 불변식 | aggregate / domain | `409` |

짧게 외우면 "요청 한 장으로 알 수 있으면 입구 검증, 저장 상태를 봐야 알 수
있으면 도메인 규칙"이다. shopping-cart checkout은 결제 흐름이 복잡해 보여도
이 첫 분기부터 잡아야 피드백이 덜 섞인다.

그래서 `CreateOrderRequest`의 `@NotBlank`, `@Positive`, enum binding 같은
검증은 DTO와 웹 계층에 두어도 자연스럽다. 반대로 쿠폰 재사용, 품절,
중복 주문 허용 여부는 checkout service가 repository 조회나 DB 제약 결과를
해석하면서 다루는 편이 맞다. 멘토가 "409로 번역하라"고 말하는 이유도,
형식 오류와 현재 상태 충돌을 API 의미에서 분리하라는 뜻에 가깝다.

## 미션 PR 코멘트 패턴

- "`@Valid`는 request 모양을 거르는 용도에 가깝고, 쿠폰 중복 사용이나 품절은 service 규칙으로 올려 보세요."
- "controller가 재고와 쿠폰 상태를 직접 조회해 conflict를 결정하면 입구 계층이 너무 많은 진실을 알게 됩니다."
- "`400`과 `409`를 나누면 클라이언트가 잘못된 요청과 현재 상태 충돌을 다르게 복구할 수 있습니다."
- "DB unique 제약이나 조건부 update가 마지막 보호선이더라도, API 의미는 business conflict로 설명해야 리뷰가 읽힙니다."

## 다음 학습

- 입력 검증과 도메인 규칙의 일반 원형을 더 짧게 잡으려면 [Validation Boundary: Input vs Domain Invariant Mini Bridge](./validation-boundary-input-vs-domain-invariant-mini-bridge.md)를 본다.
- checkout 흐름 책임 자체를 다시 보려면 [shopping-cart 결제 승인/주문 확정 흐름 ↔ Service 계층 브릿지](./shopping-cart-checkout-service-layer-bridge.md)를 읽는다.
- 중복 주문 방지와 재고 차감 충돌을 DB write 관점에서 이어 보려면 [shopping-cart 결제 재시도/재고 차감 ↔ 멱등성 키와 조건부 UPDATE 브릿지](../database/shopping-cart-payment-idempotency-stock-bridge.md)를 본다.
- 쿠폰 중복 사용을 `UNIQUE claim`으로 닫는 축을 따로 보려면 [shopping-cart 쿠폰 1회 적용 ↔ UNIQUE claim row 브릿지](../database/shopping-cart-coupon-apply-once-unique-claim-bridge.md)를 이어서 읽는다.

---
schema_version: 3
title: shopping-cart checkout 분기 패턴 결정 가이드
concept_id: design-pattern/shopping-cart-checkout-pattern-decision-guide
canonical: false
category: design-pattern
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 88
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- checkout-pattern-choice
- strategy-vs-state-vs-policy
- timeout-owner-boundary
aliases:
- shopping-cart checkout 패턴 결정 가이드
- 장바구니 결제 흐름 패턴 선택
- shopping-cart 분기 축 고르기
- checkout 로직을 어떤 패턴으로 나눌지
- 결제 할인 상태 만료 패턴 구분
symptoms:
- checkout 서비스 분기는 많은데 strategy, state, policy object, process manager 중 무엇을 골라야 할지 모르겠어요
- 리뷰에서 분기 축이 섞였다고 하는데 결제수단, 할인, 상태, 만료를 어떤 기준으로 분리해야 할지 헷갈려요
- shopping-cart checkout 코드를 나누고 싶은데 패턴 이름이 계속 바뀌어요
intents:
- comparison
- design
- mission_bridge
prerequisites:
- design-pattern/strategy-state-policy-object-decision-guide
- software-engineering/shopping-cart-checkout-service-layer-bridge
next_docs:
- spring/shopping-cart-payment-method-router-qualifier-bridge
- design-pattern/shopping-cart-coupon-promotion-policy-object-bridge
- design-pattern/shopping-cart-order-status-state-pattern-bridge
- design-pattern/shopping-cart-pending-order-expiry-process-manager-bridge
linked_paths:
- contents/design-pattern/strategy-state-policy-object-decision-guide.md
- contents/software-engineering/shopping-cart-checkout-service-layer-bridge.md
- contents/spring/shopping-cart-payment-method-router-qualifier-bridge.md
- contents/design-pattern/shopping-cart-coupon-promotion-policy-object-bridge.md
- contents/design-pattern/shopping-cart-order-status-state-pattern-bridge.md
- contents/design-pattern/shopping-cart-pending-order-expiry-process-manager-bridge.md
confusable_with:
- spring/shopping-cart-payment-method-router-qualifier-bridge
- design-pattern/shopping-cart-coupon-promotion-policy-object-bridge
- design-pattern/shopping-cart-order-status-state-pattern-bridge
- design-pattern/shopping-cart-pending-order-expiry-process-manager-bridge
forbidden_neighbors: []
expected_queries:
- shopping-cart checkout에서 결제수단 선택, 할인 규칙, 주문 상태, 만료 처리 중 무엇이 어떤 패턴으로 가야 하는지 한 번에 구분하는 기준이 뭐야?
- 장바구니 미션 리뷰에서 분기 축이 섞였다는 말을 들었을 때 어떤 결정표로 나눠 보면 돼?
- checkout 서비스 if 문을 쪼개려는데 strategy로 갈지 state로 갈지 policy object로 갈지 timeout owner로 갈지 판단 순서가 있어?
- 결제 방식 선택과 주문 상태 전이를 같은 패턴으로 보면 왜 계속 이름이 어색해져?
- shopping-cart에서 할인 판단, 결제 실행, 주문 만료를 서로 다른 설계 문제로 자르는 빠른 기준을 알려줘
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션의 checkout 분기를 어떤 패턴으로 나눌지
  고르는 chooser다. 결제 수단 선택, 쿠폰과 프로모션 판정, 주문 상태 전이,
  미결제 주문 만료처럼 checkout 한곳에 붙기 쉬운 분기를 strategy router,
  policy object, state pattern, process manager 중 어디로 보내야 하는지
  비교한다. 분기 축이 섞였다, 패턴 이름이 계속 바뀐다, service if 문이
  커진다 같은 학습자 표현을 빠른 결정 질문으로 매핑한다.
---

# shopping-cart checkout 분기 패턴 결정 가이드

## 한 줄 요약

> checkout 분기를 나눌 때 핵심은 "코드가 지금 어떤 질문에 답하나"다. 결제 수단 선택이면 router/strategy, 할인 허용 판정이면 policy object, 주문 단계별 허용 행동이면 state, 시간 지난 주문 만료면 process manager 쪽이다.

## 결정 매트릭스

| 지금 checkout 코드가 답하는 질문 | 먼저 볼 패턴 | shopping-cart 예시 |
|---|---|---|
| 이번 요청은 어떤 구현으로 처리할까? | router / strategy | 카드 결제기와 간편결제 승인기를 고른다. |
| 이 주문에 쿠폰이나 프로모션을 허용할까? | policy object | 최소 주문 금액, 중복 할인, 최대 할인 한도를 판정한다. |
| 지금 상태에서 어떤 행동이 가능한가? | state pattern | `PENDING`은 취소 가능하지만 `CANCELED`는 재확정되면 안 된다. |
| 정해진 시간이 지나면 어떤 후속 전이를 해야 하나? | process manager | 30분 안에 미결제면 만료시키되, 늦은 timeout은 무시한다. |

결정 기준은 "분기 수"가 아니라 "분기 축"이다. 같은 `if` 문이라도 입력값으로 구현을 고르는지, 도메인 규칙을 판정하는지, 현재 상태를 해석하는지, 시간을 포함한 workflow를 소유하는지에 따라 다른 문서로 가야 한다.

## 흔한 오선택

결제 수단 선택을 policy object로 부르는 경우:
핵심이 허용 여부가 아니라 어떤 승인기를 호출할지 고르는 문제면 router/strategy 쪽이 더 정확하다. `paymentMethod` 값이 직접 구현 선택에 쓰이면 이 신호가 강하다.

쿠폰 규칙을 state로 푸는 경우:
상태 전이보다 할인 가능 여부와 거절 이유 설명이 중요하면 state보다 policy object가 읽힌다. "왜 안 되는가"를 반환해야 할수록 이쪽이다.

주문 상태 전이를 strategy로 빼는 경우:
호출자가 구현을 바꿔 끼우는 문제가 아니라 주문 자신이 현재 단계에 따라 허용 행동을 달리하는 문제다. `PENDING`, `PAID`, `CANCELED`가 보이면 state 질문부터 한다.

미결제 만료를 단순 scheduler 분기로 두는 경우:
시간이 포함된 상태 전이는 누가 deadline을 소유하는지까지 같이 봐야 한다. 늦은 timeout을 무시해야 한다면 process manager 관점이 필요하다.

## 다음 학습

- 결제 수단별 승인 경로를 bean 라우팅으로 보려면 [shopping-cart 결제수단 선택 ↔ Spring Router vs Qualifier 브릿지](../spring/shopping-cart-payment-method-router-qualifier-bridge.md)
- 할인 가능 여부와 거절 이유를 규칙 객체로 보려면 [shopping-cart 쿠폰/프로모션 적용 ↔ Policy Object 브릿지](./shopping-cart-coupon-promotion-policy-object-bridge.md)
- 주문 단계별 허용 행동을 aggregate 안으로 끌어올리려면 [shopping-cart 주문 상태 전이 ↔ 상태 패턴 브릿지](./shopping-cart-order-status-state-pattern-bridge.md)
- timeout과 늦은 신호 무시까지 포함한 workflow owner를 보려면 [shopping-cart 미결제 주문 만료 ↔ Process Manager와 Deadline 브릿지](./shopping-cart-pending-order-expiry-process-manager-bridge.md)

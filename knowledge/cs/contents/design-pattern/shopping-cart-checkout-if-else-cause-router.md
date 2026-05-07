---
schema_version: 3
title: shopping-cart checkout if-else 확산 원인 라우터
concept_id: design-pattern/shopping-cart-checkout-if-else-cause-router
canonical: false
category: design-pattern
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 80
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- checkout-if-else-split
- strategy-vs-state-vs-policy
- timeout-owner-boundary
aliases:
- shopping-cart checkout if-else 원인 라우터
- 장바구니 체크아웃 if 문 계속 늘어남
- shopping-cart 서비스 switch 너무 많음
- checkout 분기 어디서 나눠야 해
- 할인 결제 상태 분기 뒤섞임
symptoms:
- shopping-cart CheckoutService에 if 문이 계속 늘어나는데 어떤 기준으로 쪼개야 할지 모르겠어요
- 결제 수단 선택, 할인 규칙, 주문 상태 전이가 한 메서드 switch 문에 다 들어 있어요
- 리뷰에서 분기 축이 섞였다고 하는데 strategy로 갈지 state로 갈지 policy object로 갈지 헷갈려요
- timeout 만료 처리까지 checkout 서비스가 직접 분기해서 코드가 자꾸 옆으로 퍼져요
intents:
- symptom
- troubleshooting
- mission_bridge
- design
- comparison
prerequisites:
- design-pattern/strategy-state-policy-object-decision-guide
- software-engineering/shopping-cart-checkout-service-layer-bridge
next_docs:
- spring/shopping-cart-payment-method-router-qualifier-bridge
- design-pattern/shopping-cart-coupon-promotion-policy-object-bridge
- design-pattern/shopping-cart-order-status-state-pattern-bridge
- design-pattern/shopping-cart-pending-order-expiry-process-manager-bridge
linked_paths:
- contents/spring/shopping-cart-payment-method-router-qualifier-bridge.md
- contents/design-pattern/shopping-cart-coupon-promotion-policy-object-bridge.md
- contents/design-pattern/shopping-cart-order-status-state-pattern-bridge.md
- contents/design-pattern/shopping-cart-pending-order-expiry-process-manager-bridge.md
- contents/software-engineering/shopping-cart-checkout-service-layer-bridge.md
- contents/design-pattern/strategy-state-policy-object-decision-guide.md
confusable_with:
- spring/shopping-cart-payment-method-router-qualifier-bridge
- design-pattern/shopping-cart-coupon-promotion-policy-object-bridge
- design-pattern/shopping-cart-order-status-state-pattern-bridge
- design-pattern/shopping-cart-pending-order-expiry-process-manager-bridge
forbidden_neighbors: []
expected_queries:
- shopping-cart checkout 서비스 if 문이 계속 늘어날 때 먼저 어떤 종류의 분기인지 어떻게 나눠 봐야 해?
- 결제수단, 할인, 주문 상태, 만료 처리가 한 switch 문에 있으면 어떤 패턴 문서부터 읽어야 해?
- 장바구니 미션 리뷰에서 분기 축이 섞였다는 말은 정확히 무슨 뜻이야?
- shopping-cart에서 timeout까지 checkout 서비스가 직접 분기하면 왜 설계가 흐려진다고 해?
- strategy, state, policy object, process manager 중 무엇으로 가야 할지 증상 기준으로 고르는 방법이 있어?
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션에서 CheckoutService의 if-else와 switch가
  결제 수단 선택, 할인 규칙 판정, 주문 상태 전이, 미결제 timeout 처리까지
  한곳에 뒤엉킬 때 원인을 가르는 symptom_router다. checkout if 문이 계속
  늘어남, 할인과 결제 분기 섞임, pending paid canceled 분기와 timeout이 같은
  메서드에 있음, strategy인지 state인지 모르겠음 같은 학습자 표현을 payment
  router, policy object, state pattern, process manager 갈래로 라우팅한다.
---

# shopping-cart checkout if-else 확산 원인 라우터

## 한 줄 요약

> shopping-cart checkout의 긴 `if` 문은 "분기가 많다"가 아니라 서로 다른 질문이 한 메서드에 눌어붙었다는 신호라서, 먼저 결제 수단 선택인지, 할인 규칙 판정인지, 주문 상태 전이인지, 시간 기반 만료인지부터 갈라야 한다.

## 가능한 원인

1. **결제 수단 선택과 실행 경로가 섞였다.** `CARD`, `KAKAO_PAY`, `BANK_TRANSFER`처럼 요청값에 따라 다른 승인기를 고르는 문제라면 "지금 어떤 구현을 호출할까"가 핵심이다. 이 갈래는 [shopping-cart 결제 수단 선택 ↔ Spring bean 이름 라우팅과 `@Qualifier` 브릿지](../spring/shopping-cart-payment-method-router-qualifier-bridge.md)로 이어진다.
2. **할인 가능 여부와 거절 이유를 서비스가 직접 판정한다.** 회원 등급, 쿠폰 중복, 최소 주문 금액, 최대 할인 한도를 `if` 사슬로 쌓고 있다면 구현 선택보다 "이 주문이 지금 할인 가능한가"가 질문이다. 이 경우는 [shopping-cart 쿠폰/프로모션 적용 ↔ Policy Object 브릿지](./shopping-cart-coupon-promotion-policy-object-bridge.md)를 먼저 본다.
3. **주문 상태별 허용 행동을 서비스 `switch`가 다 안다.** `PENDING`, `PAID`, `CANCELED`마다 가능한 행동이 다른데 서비스가 전이 규칙을 모두 품고 있으면 상태 축이 새고 있는 것이다. 이 갈래는 [shopping-cart 주문 상태 전이 ↔ 상태 패턴 브릿지](./shopping-cart-order-status-state-pattern-bridge.md)로 가서 aggregate가 허용 전이를 직접 가지는 쪽을 본다.
4. **미결제 timeout과 늦은 신호 무시를 한 메서드에서 같이 막으려 한다.** "30분 뒤 자동 취소"나 늦게 온 만료 작업 무시 같은 장면은 단순 분기 추가보다 workflow owner가 deadline을 해석하는 문제다. 이때는 [shopping-cart 미결제 주문 만료 ↔ Process Manager와 Deadline 브릿지](./shopping-cart-pending-order-expiry-process-manager-bridge.md)를 따라간다.

## 빠른 자기 진단

1. 분기 조건이 `paymentMethod` 값인지 먼저 본다. 입력값에 따라 다른 구현체를 고르는 문제면 payment router 쪽이다.
2. 분기 안에서 "왜 할인 불가인가"를 같이 계산하고 있다면 policy object 갈래가 먼저다. 거절 이유를 설명해야 할수록 이 신호가 강하다.
3. `orderStatus` 값마다 가능한 행동을 막고 있다면 state 갈래를 의심한다. 같은 상태 이름이 여러 서비스 메서드에 반복되면 거의 확실하다.
4. `expiresAt`, scheduler, timeout 재시도 같은 시간이 보이면 process manager 갈래를 먼저 본다. 늦게 온 신호를 무시할 규칙이 핵심인지 확인한다.

## 다음 학습

- 결제 수단별 승인 경로를 bean 라우팅으로 읽으려면 [shopping-cart 결제 수단 선택 ↔ Spring bean 이름 라우팅과 `@Qualifier` 브릿지](../spring/shopping-cart-payment-method-router-qualifier-bridge.md)를 본다.
- 쿠폰과 프로모션 규칙이 checkout 서비스에 눌어붙었다면 [shopping-cart 쿠폰/프로모션 적용 ↔ Policy Object 브릿지](./shopping-cart-coupon-promotion-policy-object-bridge.md)를 잇는다.
- 주문 상태별 허용 행동을 객체 안으로 끌어올리려면 [shopping-cart 주문 상태 전이 ↔ 상태 패턴 브릿지](./shopping-cart-order-status-state-pattern-bridge.md)로 간다.
- 시간 기반 만료와 늦은 timeout 무시까지 함께 정리하려면 [shopping-cart 미결제 주문 만료 ↔ Process Manager와 Deadline 브릿지](./shopping-cart-pending-order-expiry-process-manager-bridge.md)를 이어서 읽는다.

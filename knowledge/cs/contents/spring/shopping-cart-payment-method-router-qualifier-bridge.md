---
schema_version: 3
title: 'shopping-cart 결제수단 선택 ↔ Spring Router vs Qualifier 브릿지'
concept_id: spring/shopping-cart-payment-method-router-qualifier-bridge
canonical: false
category: spring
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: mixed
source_priority: 78
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- payment-method-router
- qualifier-vs-runtime-selection
- bean-name-domain-key-boundary
aliases:
- shopping-cart 결제수단별 PaymentClient 선택
- 장바구니 PG 라우터
- shopping-cart 결제 구현체 분기
- 결제수단별 bean 선택
- PaymentClient router
symptoms:
- 결제수단마다 다른 PaymentClient를 어디서 골라야 할지 모르겠어요
- '`@Qualifier`로 카드와 간편결제를 나누려는데 요청마다 값이 달라져서 꼬여요'
- bean 이름 문자열을 API의 `paymentMethod` 값에 그대로 붙여도 되나 헷갈려요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- software-engineering/shopping-cart-checkout-service-layer-bridge
- spring/bean-di-basics
- spring/spring-runtime-strategy-router-vs-qualifier-boundaries
next_docs:
- spring/spring-runtime-strategy-router-vs-qualifier-boundaries
- spring/spring-custom-qualifier-primer
- design-pattern/bean-name-vs-domain-key-lookup
linked_paths:
- contents/spring/spring-runtime-strategy-router-vs-qualifier-boundaries.md
- contents/spring/spring-custom-qualifier-primer.md
- contents/spring/spring-bean-registration-path-decision-guide.md
- contents/design-pattern/bean-name-vs-domain-key-lookup.md
- contents/software-engineering/shopping-cart-checkout-service-layer-bridge.md
confusable_with:
- spring/spring-runtime-strategy-router-vs-qualifier-boundaries
- spring/spring-custom-qualifier-primer
- design-pattern/bean-name-vs-domain-key-lookup
forbidden_neighbors:
- contents/spring/spring-custom-qualifier-primer.md
expected_queries:
- shopping-cart checkout에서 카드와 간편결제마다 다른 클라이언트를 Spring에서 어디서 고르게 해야 해?
- '요청의 `paymentMethod` 값으로 PG 구현체를 바꾸려면 `@Qualifier` 말고 뭐가 맞아?'
- 결제수단이 늘어날 때 서비스의 `if`문 대신 Spring Bean 구조를 어떻게 잡아?
- PG 코드 문자열을 bean 이름으로 바로 써도 되는지 리뷰에서 왜 위험하다고 했어?
- shopping-cart 미션에서 Toss, KakaoPay 구현체 선택을 DI와 router 중 어디로 풀어야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션에서 결제수단마다 다른 PG client를
  호출해야 할 때 Spring의 고정 주입과 요청별 runtime 선택을 구분하는
  mission_bridge다. 카드와 간편결제마다 다른 구현체를 어디서 고를지,
  `@Qualifier`를 요청값 분기에 써도 되는지, `paymentMethod` 문자열을 bean
  이름에 바로 매핑해도 되는지, checkout service 안의 `if` 분기를 언제
  router로 올릴지 같은 학습자 표현을 Router vs Qualifier 경계로 연결한다.
---

# shopping-cart 결제수단 선택 ↔ Spring Router vs Qualifier 브릿지

## 한 줄 요약

> shopping-cart에서 결제수단마다 다른 PG client를 타야 한다면, `@Qualifier`는 "이 서비스에 항상 같은 구현체를 꽂는다"는 고정 wiring용이고, `paymentMethod` 같은 요청값으로 매번 달라지는 선택은 router 계층에서 푸는 편이 맞다.

## 미션 시나리오

shopping-cart checkout을 붙이다 보면 `CardPaymentClient`, `KakaoPayClient`, `TossPaymentClient` 같은 구현체가 생긴다. 초반 구현에서는 서비스 안에서 `if (paymentMethod == KAKAO_PAY)`처럼 분기하거나, 반대로 생성자에 `@Qualifier("kakaoPaymentClient")`를 꽂아 두고 "나중에 바꾸면 되겠지"라고 시작하기 쉽다. 하지만 리뷰에서는 "요청마다 달라지는 선택을 고정 주입으로 풀고 있다", "외부 API 값과 bean 이름이 직접 묶였다"는 코멘트가 자주 나온다.

학습자가 특히 헷갈리는 장면은 결제수단이 하나일 때는 `@Qualifier`가 맞아 보인다는 점이다. 운영 초기에 PG가 하나뿐이면 서비스가 항상 같은 구현체를 써도 된다. 그런데 shopping-cart 미션이 확장되어 결제수단이 늘어나면 질문이 달라진다. 이제는 "이 서비스가 어떤 bean을 쓰나"가 아니라 "이번 요청은 어느 전략으로 보낼까"가 핵심이 된다.

## CS concept 매핑

Spring의 `@Qualifier`는 애플리케이션이 뜰 때 주입 후보를 하나로 좁히는 장치다. 그래서 `CheckoutService`가 항상 메인 PG 하나만 쓰는 구조라면 `@Qualifier`나 커스텀 qualifier로 고정 wiring을 설명할 수 있다. 반대로 shopping-cart처럼 `paymentMethod`, `pgCode`, `channel` 값에 따라 매 호출마다 구현체가 달라지면, 그건 DI 후보 선택이 아니라 runtime dispatch 문제다.

이럴 때는 `Map<String, PaymentClient>`를 그대로 외부 입력에 물리기보다, 먼저 `paymentMethod`를 domain enum으로 정규화하고 그 enum을 key로 쓰는 router를 두는 편이 안전하다. Bean은 구현체 집합을 제공하고, router는 "이번 주문이 어떤 전략으로 가야 하는가"를 결정한다. 즉 checkout service는 주문 생성과 승인 흐름을 조립하고, router는 결제수단별 전략 선택을 맡고, 각 `PaymentClient` 구현체는 실제 외부 PG 호출만 담당하도록 경계를 나눈다.

## 미션 PR 코멘트 패턴

- "`@Qualifier`는 앱 시작 시점에 고정 wiring하는 장치라서, 요청마다 바뀌는 결제수단 분기와는 문제 축이 다릅니다."
- "`paymentMethod` 문자열을 bean 이름에 바로 매핑하면 API 계약 변경이 DI 이름 변경으로 번집니다. domain key를 한 번 끼워 넣으세요."
- "checkout service 안의 긴 `if/switch`는 결제 흐름 orchestration과 PG 선택 책임이 섞였다는 신호입니다. router로 분리해 보세요."
- "PG 구현체가 여러 개인 상황에서 서비스가 특정 bean 이름을 직접 알기 시작하면 테스트와 확장 포인트가 같이 흔들립니다."

## 다음 학습

- 고정 주입과 요청별 선택의 경계를 일반화해서 보려면 `spring/spring-runtime-strategy-router-vs-qualifier-boundaries`
- 같은 타입 bean을 항상 같은 역할로 고정해야 한다면 `spring/spring-custom-qualifier-primer`
- bean 이름 대신 domain key를 registry에 태우는 이유를 보려면 `design-pattern/bean-name-vs-domain-key-lookup`
- checkout service가 어디까지 흐름을 조립해야 하는지 다시 잡으려면 `software-engineering/shopping-cart-checkout-service-layer-bridge`

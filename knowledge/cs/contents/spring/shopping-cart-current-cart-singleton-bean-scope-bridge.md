---
schema_version: 3
title: 'shopping-cart 현재 장바구니 보관 ↔ Spring singleton Bean 상태 경계 브릿지'
concept_id: spring/shopping-cart-current-cart-singleton-bean-scope-bridge
canonical: false
category: spring
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- singleton-cart-state
- stateless-service-boundary
- cart-state-storage
aliases:
- shopping-cart 현재 cart bean 저장
- 장바구니 상태를 service 필드에 보관
- shopping-cart singleton 상태 오염
- currentCart 멤버 변수
- 장바구니 요청 간 상태 섞임
symptoms:
- service 필드에 currentCart를 뒀더니 다른 요청의 장바구니가 섞여요
- 장바구니를 메모리에 들고 있었는데 새로고침이나 다른 탭에서 상태가 이상해져요
- singleton Bean에 회원별 cart를 저장해도 되는지 모르겠어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/bean-di-basics
- spring/bean-lifecycle-basics
- spring/request-pipeline-bean-container
next_docs:
- spring/bean-lifecycle-basics
- spring/request-scope-proxy-pitfalls
- software-engineering/shopping-cart-checkout-service-layer-bridge
linked_paths:
- contents/spring/spring-bean-di-basics.md
- contents/spring/spring-bean-lifecycle-basics.md
- contents/spring/spring-bean-lifecycle-scope-traps.md
- contents/spring/spring-request-scope-proxy-pitfalls.md
- contents/software-engineering/shopping-cart-checkout-service-layer-bridge.md
confusable_with:
- software-engineering/shopping-cart-checkout-service-layer-bridge
- spring/shopping-cart-payment-method-router-qualifier-bridge
- spring/request-scope-proxy-pitfalls
forbidden_neighbors: []
expected_queries:
- shopping-cart 미션에서 현재 장바구니를 service 멤버 변수로 들고 있으면 왜 안 돼?
- controller나 service에 currentCart를 저장했더니 다른 요청과 섞이는 이유가 뭐야?
- 장바구니 상태를 메모리에 두지 말라는 리뷰를 Spring singleton 관점에서 설명해 줘
- shopping-cart 웹 전환에서 회원별 cart 상태는 어디에 두는 게 맞아?
- stateless service로 바꾸라는 말이 장바구니 구현에서는 정확히 무슨 뜻이야?
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션에서 현재 장바구니나 checkout 진행 상태를
  Spring controller/service 필드에 보관할 때 왜 요청 간 상태 오염이 생기는지
  설명하는 mission_bridge다. singleton Bean, stateless service, currentCart
  멤버 변수, 회원별 장바구니 상태 저장 위치, 세션과 DB 같은 외부 상태 저장소
  경계로 옮겨야 한다는 리뷰 표현을 shopping-cart 흐름과 연결한다.
---

# shopping-cart 현재 장바구니 보관 ↔ Spring singleton Bean 상태 경계 브릿지

## 한 줄 요약

> shopping-cart에서 `currentCart`나 `selectedCoupon` 같은 현재 상태를 controller나 service 필드에 붙여 두면, Spring의 singleton Bean 수명과 회원별 장바구니 수명이 충돌해서 요청 간 상태 오염이 생기기 쉽다.

## 미션 시나리오

shopping-cart를 웹으로 옮기면 학습자는 자주 "현재 사용자의 장바구니"를 한 객체로
잡고 싶어진다. 그래서 `CartService` 필드에 `currentCart`, `currentMemberId`,
`selectedCoupon` 같은 값을 보관한 뒤, 상품 추가와 수량 변경, checkout 준비를
그 객체 하나로 이어 붙이는 구조로 시작하기 쉽다.

혼자 한 브라우저로만 테스트할 때는 그럴듯해 보인다. 하지만 새로고침, 탭 두 개,
다른 사용자 요청이 섞이기 시작하면 "방금 담은 상품이 사라졌다", "다른 회원의
coupon 선택이 남아 있다", "checkout 직전의 cart snapshot이 엉뚱하게 바뀐다"
같은 증상이 나온다. 리뷰에서 "`@Service`는 기본이 singleton인데 회원별 상태를
필드에 들고 있다", "장바구니 상태 원천을 어디에 둘지 먼저 정하라"는 코멘트가
붙는 장면이 여기다.

## CS concept 매핑

여기서 닿는 개념은 `stateless singleton`과 `state store 분리`다. Spring의
일반적인 controller/service Bean은 애플리케이션 동안 재사용되는 singleton이라,
가변 필드에 회원별 cart 상태를 저장하면 여러 요청이 같은 객체를 공유한다.
그래서 Bean은 "장바구니에 상품을 추가하라" 같은 행동을 조립하는 협력자로 두고,
실제 장바구니 상태는 DB row, 세션, 혹은 명시적인 저장소에서 찾는 편이 맞다.

shopping-cart에 대입하면 service는 `memberId`나 `cartId`로 현재 장바구니를
조회하고, 상품 추가나 coupon 적용 결과를 저장소에 반영하는 흐름을 맡는다.
request scope가 만능 보관함도 아니다. request scope는 한 번의 HTTP 요청 동안만
살아가므로 "여러 요청에 걸친 현재 장바구니"를 대신 소유하지 못한다. 그래서
리뷰에서 "stateless service로 바꾸라"는 말은 상태를 없애라는 뜻이 아니라,
Bean 수명과 장바구니 수명을 분리하라는 뜻에 가깝다.

## 미션 PR 코멘트 패턴

- "`CartService` 필드에 현재 장바구니를 보관하면 singleton Bean 특성 때문에 회원별 상태가 섞일 수 있습니다."
- "장바구니는 여러 요청에 걸쳐 이어지지만 request Bean이나 controller 필드는 그 수명을 안전하게 대표하지 못합니다."
- "service는 cart 상태를 오래 들고 있는 곳보다 `cartId` 기반 조회와 갱신을 조립하는 곳에 가깝습니다."
- "탭 두 개와 사용자 두 명 시나리오를 떠올리면 `currentCart` 멤버 변수가 왜 위험한지 바로 드러납니다."

## 다음 학습

- singleton Bean이 왜 오래 살아남는지 다시 잡으려면 `spring/bean-lifecycle-basics`
- request scope가 어디까지 안전한지 따로 보려면 `spring/request-scope-proxy-pitfalls`
- checkout 흐름 책임과 cart 상태 책임을 나눠 보려면 `software-engineering/shopping-cart-checkout-service-layer-bridge`
- Bean scope에서 상태 공유 버그가 어떻게 커지는지 더 보려면 `contents/spring/spring-bean-lifecycle-scope-traps.md`

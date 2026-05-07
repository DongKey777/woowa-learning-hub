---
schema_version: 3
title: 'shopping-cart 결제 승인/주문 확정 흐름 ↔ Service 계층 브릿지'
concept_id: software-engineering/shopping-cart-checkout-service-layer-bridge
canonical: false
category: software-engineering
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- controller-logic-leak
- service-orchestration
- payment-gateway-boundary
aliases:
- shopping-cart checkout service
- shopping-cart 주문 확정 흐름
- 장바구니 결제 service 책임
- PaymentClient 호출 위치
- 주문 생성 서비스 오케스트레이션
symptoms:
- 컨트롤러에서 결제 API까지 불러도 되나
- 주문 저장과 결제 승인 순서를 어디서 묶어야 해
- service가 DTO만 넘기고 너무 얇은데 맞나
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- software-engineering/layered-architecture-basics
- software-engineering/service-layer-basics
- spring/transactional-basics
next_docs:
- software-engineering/service-layer-basics
- database/shopping-cart-payment-idempotency-stock-bridge
- spring/transactional-basics
linked_paths:
- contents/software-engineering/service-layer-basics.md
- contents/software-engineering/layered-architecture-basics.md
- contents/database/shopping-cart-payment-idempotency-stock-bridge.md
- contents/network/shopping-cart-rate-limit-bridge.md
- contents/spring/spring-payment-approval-db-failure-compensation-idempotency-primer.md
confusable_with:
- spring/transactional-basics
- database/shopping-cart-payment-idempotency-stock-bridge
- network/shopping-cart-rate-limit-bridge
forbidden_neighbors:
  - contents/database/shopping-cart-payment-idempotency-stock-bridge.md
  - contents/network/shopping-cart-rate-limit-bridge.md
expected_queries:
- shopping-cart 미션에서 주문 생성하고 결제 승인하는 흐름은 service가 어디까지 맡아야 해?
- 컨트롤러에서 PaymentClient를 직접 부르면 왜 리뷰에서 경계가 흐리다고 해?
- shopping-cart checkout에서 주문 저장, 결제 승인, 응답 조립 순서를 어디에 둬야 해?
- 결제 미션에서 service가 얇아 보여도 orchestration만 맡아도 괜찮아?
- shopping-cart에서 transaction 문제 말고 계층 책임으로 먼저 봐야 할 포인트가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션에서 주문 생성, 결제 승인, 주문 확정,
  응답 조립이 한 흐름으로 보일 때 Service 계층 경계로 잇는
  mission_bridge다. PaymentClient를 어디서 호출할지, controller가 checkout
  순서를 직접 짬, service가 얇아 보여도 되는지, pending 주문과 확정 흐름을
  누가 묶는지, orchestration 책임을 어디에 둘지 같은 학습자 표현을 service
  layer 감각으로 연결한다.
---

# shopping-cart 결제 승인/주문 확정 흐름 ↔ Service 계층 브릿지

## 한 줄 요약

> shopping-cart checkout은 "요청을 받아 결제사를 부르고 주문 상태를 확정하는 한 번의 유스케이스"라서 Service가 흐름을 조립하는 편이 자연스럽다. Controller는 HTTP 입출력, Domain은 규칙, Repository는 저장을 맡고 Service가 그 사이 순서를 묶는다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "컨트롤러에서 결제 API까지 불러도 되나요?" | `CheckoutController`가 PaymentClient와 Repository를 직접 조합 | HTTP 입구와 checkout 유스케이스 orchestration을 분리한다 |
| "주문 저장과 결제 승인 순서를 어디서 묶어야 하나요?" | pending order, payment approval, confirm 흐름 | Service가 여러 협력자를 조합해 한 유스케이스 순서를 만든다 |
| "service가 DTO만 넘기고 너무 얇은데 맞나요?" | 얇은 service와 도메인/외부 client 책임이 헷갈리는 단계 | 얇아 보여도 순서 조립과 경계 유지가 Service 책임임을 본다 |

## 미션 시나리오

shopping-cart 미션에서 초반 구현은 Controller가 `request`를 해석한 뒤 `PaymentClient`를 직접 호출하고, 성공하면 `OrderRepository.save()`까지 이어서 부르는 모양으로 자주 시작한다. 한 파일에서 다 보이니 빨라 보이지만, 리뷰에서는 "웹 계층이 결제 흐름과 저장 순서를 모두 안다"는 지적을 받기 쉽다.

반대로 모든 책임을 Domain 객체 하나에 몰아도 어색하다. 주문 엔티티는 상태 전이와 금액 규칙은 알아야 하지만, 외부 결제 승인 호출 순서나 응답 DTO 조립까지 알 필요는 없다. shopping-cart checkout은 "입력 해석"도 "개별 규칙"도 아닌 유스케이스 조립 문제라서 Service 계층 질문으로 보는 편이 맞다.

## CS concept 매핑

Service 계층은 여러 컴포넌트를 엮어 하나의 유스케이스를 끝내는 orchestration 자리다. shopping-cart checkout에서는 대체로 아래 순서가 여기에 들어간다.

```java
Long orderId = checkoutService.createPendingOrder(command);
PaymentApproval approval = paymentClient.approve(command.paymentKey());
checkoutService.confirmOrder(orderId, approval);
```

여기서 Controller는 `CheckoutRequest -> CheckoutCommand` 변환과 응답 반환까지만 맡는다. Domain은 `Order.confirm(approvalId)`처럼 상태 전이가 유효한지만 검증한다. Repository는 pending 주문 저장, 확정 상태 반영 같은 영속화만 담당한다. 즉 "어떤 순서로 누구를 호출해 checkout을 끝낼지"가 Service 책임이고, 이것이 얇아 보여도 계층 경계가 맞으면 충분히 의미 있다.

이 구분을 먼저 잡아야 트랜잭션과 멱등성도 제자리를 찾는다. Service 흐름이 모여 있어야 "외부 결제는 tx 밖", "중복 주문 방지는 DB arbitration", "rate limit은 별도 방어"처럼 후속 설계 축을 분리해서 읽을 수 있다.

## 미션 PR 코멘트 패턴

- "Controller가 결제사 호출과 주문 저장 순서를 모두 알고 있네요. HTTP 처리만 남기고 checkout 흐름은 Service로 모아 보세요."
- "Order가 결제 API client를 직접 들고 있으면 도메인 규칙과 외부 연동 책임이 섞입니다."
- "Service가 얇아 보여도 괜찮습니다. 유스케이스 orchestration 자체가 Service의 핵심 책임입니다."
- "트랜잭션 위치를 논의하기 전에 먼저 어느 계층이 checkout 순서를 조립하는지부터 고정해 주세요."

## 다음 학습

- Service 책임을 일반화해서 다시 보려면 `software-engineering/service-layer-basics`
- shopping-cart에서 중복 주문과 재고 차감을 분리해 보려면 `database/shopping-cart-payment-idempotency-stock-bridge`
- 결제 승인과 로컬 commit이 왜 같은 rollback으로 닫히지 않는지 보려면 `spring-payment-approval-db-failure-compensation-idempotency-primer`
- abuse 방어와 중복 주문 방지를 헷갈렸다면 `network/shopping-cart-rate-limit-bridge`

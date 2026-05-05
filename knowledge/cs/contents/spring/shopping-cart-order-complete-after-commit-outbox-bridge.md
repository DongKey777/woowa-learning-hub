---
schema_version: 3
title: 'shopping-cart 주문 완료 후속 작업 ↔ AFTER_COMMIT vs Outbox 브릿지'
concept_id: spring/shopping-cart-order-complete-after-commit-outbox-bridge
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
- after-commit-vs-outbox
- side-effect-reliability
- event-publication-boundary
aliases:
- shopping-cart 주문 완료 후속 작업
- 장바구니 주문 완료 AFTER_COMMIT
- shopping-cart outbox 선택
- 주문 완료 알림 outbox
- 결제 후 후속 작업 분리
symptoms:
- 주문은 저장됐는데 알림이나 후속 작업을 어디서 실행해야 할지 모르겠어요
- 결제 성공 뒤 장바구니 비우기나 메일 발송을 service 메서드 안에서 같이 해도 되나 헷갈려요
- AFTER_COMMIT이면 충분한지 outbox까지 가야 하는지 감이 안 와요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/transactional-basics
- spring/shopping-cart-payment-transaction-boundary-bridge
- software-engineering/service-layer-basics
next_docs:
- spring/spring-service-layer-external-io-after-commit-outbox-primer
- spring/spring-eventlistener-transaction-phase-outbox
- database/shopping-cart-payment-idempotency-stock-bridge
linked_paths:
- contents/spring/spring-service-layer-external-io-after-commit-outbox-primer.md
- contents/spring/spring-eventlistener-transaction-phase-outbox.md
- contents/spring/shopping-cart-payment-transaction-boundary-bridge.md
- contents/software-engineering/shopping-cart-checkout-service-layer-bridge.md
confusable_with:
- spring/shopping-cart-payment-transaction-boundary-bridge
- software-engineering/shopping-cart-checkout-service-layer-bridge
- database/shopping-cart-payment-idempotency-stock-bridge
forbidden_neighbors: []
expected_queries:
- shopping-cart에서 주문 완료 후 메일 발송이나 이벤트 전송은 언제 분리해야 해?
- 결제 성공 뒤 장바구니 비우기와 알림 발송을 같은 트랜잭션에서 처리해도 돼?
- shopping-cart checkout에서 AFTER_COMMIT만 써도 되는 상황이랑 outbox가 필요한 상황을 어떻게 구분해?
- 주문 저장 후 슬랙 알림이나 분석 이벤트를 보내려면 Spring에서 어느 경계로 끊어야 해?
- shopping-cart 미션 리뷰에서 후속 부작용을 서비스 메서드 밖으로 빼라고 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션에서 결제 성공 뒤 주문 완료 알림,
  장바구니 정리, 분석 이벤트 같은 후속 작업을 Spring의
  `AFTER_COMMIT`와 outbox 중 어디에 둘지 연결해 설명하는 mission_bridge다.
  학습자가 "서비스 메서드 안에서 같이 해도 되나", "알림이면 AFTER_COMMIT으로
  충분한가", "브로커 전송은 언제 outbox까지 가야 하나"라고 묻는 장면을
  트랜잭션 이후 부작용의 신뢰도 경계로 매핑한다.
---

# shopping-cart 주문 완료 후속 작업 ↔ AFTER_COMMIT vs Outbox 브릿지

## 한 줄 요약

> shopping-cart checkout 뒤에 붙는 작업이 "주문이 커밋된 뒤 한 번 반응하면 충분한가" 아니면 "다른 시스템에 반드시 전달돼야 하는가"에 따라 `@TransactionalEventListener(AFTER_COMMIT)`와 outbox가 갈린다.

## 미션 시나리오

shopping-cart 미션에서 결제 승인과 주문 확정까지 붙인 뒤, 학습자는 보통 같은 서비스 메서드 끝에 후속 작업을 더 넣고 싶어진다. 예를 들어 주문 완료 메일 발송, 장바구니 항목 정리, 통계 적재, 다른 시스템으로의 주문 완료 이벤트 전송 같은 일들이다. 처음에는 `checkout()` 안에 순서대로 두면 쉬워 보이지만, 리뷰에서는 "주문 저장과 후속 부작용의 신뢰도 경계를 분리해 보라"는 코멘트가 자주 붙는다.

특히 헷갈리는 지점은 "결제 성공 뒤니까 그냥 같이 해도 되지 않나?"라는 감각이다. 하지만 후속 작업마다 실패 허용도가 다르다. 메일 한 번 늦게 가는 문제와, 다른 시스템이 주문 완료 사실을 영영 못 받는 문제는 같은 축이 아니다. shopping-cart의 checkout 흐름은 여기서 트랜잭션 자체보다 "커밋 뒤 반응"과 "전달 보장"을 구분하는 질문으로 바뀐다.

## CS concept 매핑

`AFTER_COMMIT`은 우리 주문이 DB에 확정된 뒤에만 반응하고 싶을 때 맞는다. 예를 들어 주문 완료 알림, 내부 캐시 정리, 실패 시 수동 재실행이 가능한 후속 작업은 `@TransactionalEventListener(phase = AFTER_COMMIT)`로 떼어 놓을 수 있다. 이렇게 하면 주문이 롤백됐는데 알림이 먼저 나가는 실수를 줄이고, checkout 메서드도 "주문 확정"과 "후속 반응"으로 읽기 쉬워진다.

반면 outbox는 "다른 시스템이 반드시 이 사실을 받아야 한다"가 핵심일 때 고른다. 주문 완료 이벤트를 브로커에 흘려 재고 집계, 정산, 배송 같은 별도 소비자가 의존한다면, 커밋 직후 프로세스가 죽어도 "보내야 할 사실"이 남아 있어야 한다. 그래서 shopping-cart에서는 `orders`와 함께 outbox row를 저장하고, 실제 전송은 relay가 맡는 식으로 정합성 경계를 나눈다. 장바구니 비우기처럼 같은 로컬 DB에서 함께 끝낼 일은 보통 메인 write 쪽에 남기고, 메일/슬랙처럼 재실행 가능한 알림은 `AFTER_COMMIT`, 시스템 간 계약이면 outbox로 읽으면 된다.

## 미션 PR 코멘트 패턴

- "주문 저장과 메일 발송, 슬랙 알림을 한 메서드에서 직렬로 처리하면 checkout 실패 원인이 너무 많아집니다. 커밋 뒤 반응으로 분리해 보세요."
- "`AFTER_COMMIT`은 커밋 뒤 실행일 뿐 전달 보장은 아닙니다. 다른 시스템 계약이면 outbox가 더 맞습니다."
- "같은 로컬 DB 정리는 주문 확정 유스케이스 안에 둘 수 있지만, 외부 알림까지 같은 원자성처럼 다루면 오해가 생깁니다."
- "후속 작업을 전부 비동기로 빼라는 뜻이 아니라, 실패해도 되는 반응과 반드시 남겨야 하는 사실을 구분하라는 리뷰입니다."

## 다음 학습

- `AFTER_COMMIT`와 outbox의 기본 선택표를 먼저 다시 잡으려면 `spring-service-layer-external-io-after-commit-outbox-primer`
- Spring 이벤트 phase와 outbox의 더 깊은 차이는 `spring-eventlistener-transaction-phase-outbox`
- shopping-cart에서 결제 승인과 주문 확정의 앞단 경계를 먼저 보려면 `spring/shopping-cart-payment-transaction-boundary-bridge`
- 중복 주문 방지와 재고 차감까지 같이 묶어 보려면 `database/shopping-cart-payment-idempotency-stock-bridge`

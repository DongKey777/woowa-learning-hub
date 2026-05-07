---
schema_version: 3
title: shopping-cart 주문 완료 후속 작업 누락 원인 라우터
concept_id: spring/shopping-cart-order-complete-follow-up-missing-cause-router
canonical: false
category: spring
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- follow-up-side-effect-triage
- event-phase-misuse
- after-commit-vs-outbox
aliases:
- shopping-cart 주문 후속 작업 누락 라우터
- 장바구니 주문 완료 알림 안 감
- shopping-cart 결제 후 메일 누락
- 주문 완료 뒤 이벤트 가끔 빠짐
- checkout 후 후처리 어디서 새는지 진단
symptoms:
- shopping-cart에서 주문은 저장됐는데 메일 발송이나 슬랙 알림이 가끔 빠져요
- 결제 성공 뒤 장바구니 비우기나 포인트 적립 같은 후속 작업이 어떤 요청에서는 실행되지 않아요
- 이벤트로 분리했는데 주문 롤백과 알림 발송 타이밍이 자꾸 어긋나 보여요
- 운영에서만 간헐적으로 후속 작업이 누락돼서 트랜잭션 문제인지 비동기 문제인지 모르겠어요
intents:
- symptom
- troubleshooting
- mission_bridge
- design
prerequisites:
- spring/transactional-basics
- software-engineering/service-layer-basics
- spring/shopping-cart-payment-transaction-boundary-bridge
next_docs:
- spring/shopping-cart-payment-transaction-boundary-bridge
- spring/shopping-cart-order-complete-after-commit-outbox-bridge
- spring/eventlistener-transaction-phase-outbox
- spring/eventlistener-ordering-async-traps
linked_paths:
- contents/spring/shopping-cart-payment-transaction-boundary-bridge.md
- contents/spring/shopping-cart-order-complete-after-commit-outbox-bridge.md
- contents/spring/spring-eventlistener-transaction-phase-outbox.md
- contents/spring/spring-eventlistener-ordering-async-traps.md
- contents/spring/spring-service-layer-external-io-after-commit-outbox-primer.md
confusable_with:
- spring/shopping-cart-payment-transaction-boundary-bridge
- spring/shopping-cart-order-complete-after-commit-outbox-bridge
- spring/eventlistener-transaction-phase-outbox
- spring/eventlistener-ordering-async-traps
forbidden_neighbors: []
expected_queries:
- shopping-cart에서 주문 완료는 됐는데 메일이나 알림이 빠질 때 먼저 어느 경계를 의심해야 해?
- 결제 성공 뒤 후속 작업이 운영에서만 가끔 누락되면 트랜잭션이 문제인지 비동기가 문제인지 어떻게 가를까?
- 장바구니 미션에서 이벤트로 분리했는데 주문 롤백과 알림 타이밍이 어긋나 보이면 어떤 문서부터 읽어야 해?
- AFTER_COMMIT으로 옮겼는데도 shopping-cart 후처리가 사라질 수 있는 이유를 증상 기준으로 설명해 줄 수 있어?
- checkout 이후 장바구니 비우기, 포인트 적립, 알림 발송이 들쭉날쭉할 때 원인 갈래를 어떻게 나눠 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션에서 주문 완료 자체는 성공했는데 메일,
  슬랙, 장바구니 비우기, 포인트 적립 같은 후속 작업이 빠지거나 타이밍이
  어긋날 때 원인을 가르는 symptom_router다. 학습자의 "주문은 됐는데 알림이
  안 간다", "운영에서만 간헐적으로 후처리가 누락된다", "`AFTER_COMMIT`으로
  옮겼는데도 불안하다", "`@Async`를 붙인 뒤 성공처럼 보이는데 실제 작업은
  빠진다" 같은 표현을 transaction boundary, event phase, outbox, async trap
  갈래로 라우팅한다.
---
# shopping-cart 주문 완료 후속 작업 누락 원인 라우터

## 한 줄 요약

> shopping-cart에서 주문 완료 뒤 후속 작업이 빠지는 장면은 "이벤트를 썼다"로 끝나는 문제가 아니라, 애초에 메인 트랜잭션 안에서 같이 묶였는지, 커밋 뒤 반응으로 분리됐는지, 전달 보장이 필요한지, 비동기 실행이 실패를 숨겼는지부터 갈라야 한다.

## 가능한 원인

1. **후속 작업을 아직 메인 트랜잭션 안에서 직접 호출하고 있다.** 주문 저장, 재고 차감, 메일 발송, 장바구니 비우기를 한 서비스 메서드에 직렬로 넣었다면 일부 실패가 전체 흐름을 흔들거나 반대로 예외를 삼켜 누락처럼 보일 수 있다. 이 갈래는 [shopping-cart 결제 승인/주문 확정 ↔ Spring 트랜잭션 경계 브릿지](./shopping-cart-payment-transaction-boundary-bridge.md)로 이어진다.
2. **`@EventListener`와 `@TransactionalEventListener`의 phase를 잘못 골랐다.** 주문이 아직 롤백될 수 있는데 일반 이벤트 리스너가 먼저 반응하거나, 커밋 뒤에만 실행돼야 할 작업을 즉시 실행하면 "주문은 취소됐는데 알림은 나감" 또는 "타이밍이 어긋남"처럼 보인다. 이 경우는 [shopping-cart 주문 완료 후속 작업 ↔ AFTER_COMMIT vs Outbox 브릿지](./shopping-cart-order-complete-after-commit-outbox-bridge.md)와 [Spring EventListener, TransactionalEventListener, Outbox](./spring-eventlistener-transaction-phase-outbox.md)를 먼저 본다.
3. **`AFTER_COMMIT`은 맞지만 전달 보장까지 필요한 작업이었다.** 메일 재전송 정도가 아니라 다른 시스템이 주문 완료 사실을 반드시 받아야 하는 계약이면, 커밋 직후 프로세스 장애만으로도 후속 작업이 사라질 수 있다. 이 갈래는 [shopping-cart 주문 완료 후속 작업 ↔ AFTER_COMMIT vs Outbox 브릿지](./shopping-cart-order-complete-after-commit-outbox-bridge.md)에서 outbox 쪽 판단으로 이어진다.
4. **`@Async`, executor 포화, 리스너 순서가 실패를 숨긴다.** publish 자체는 성공처럼 보이는데 비동기 리스너 예외가 호출자에게 안 돌아오거나, 순서 감각이 깨져 아직 안 끝난 작업을 누락으로 오해할 수 있다. 이 갈래는 [Spring `@EventListener` Ordering and Async Traps](./spring-eventlistener-ordering-async-traps.md)로 연결된다.

## 빠른 자기 진단

1. 주문 row와 핵심 상태가 정말 commit됐는지 먼저 본다. 주문 자체가 없거나 `PENDING`에 머물렀다면 후속 작업 문제가 아니라 앞단 transaction boundary가 먼저다.
2. 후속 작업이 service 메서드 안 direct call인지, 일반 `@EventListener`인지, `@TransactionalEventListener(AFTER_COMMIT)`인지 적어 본다. 이 한 줄만 써도 절반은 갈린다.
3. 그 작업이 "커밋 뒤 한 번 반응하면 충분한가" 아니면 "다른 시스템 계약상 반드시 전달돼야 하는가"를 구분한다. 후자면 `AFTER_COMMIT`에서 멈추지 말고 outbox까지 봐야 한다.
4. 운영에서만 빠진다면 `@Async` 사용 여부, executor rejection, 리스너 예외 로그, 재시도 지표를 확인한다. publish 성공 로그만 보고 완료로 간주하면 원인을 놓치기 쉽다.

## 다음 학습

- 결제 승인과 주문 확정, 후속 작업의 앞뒤 경계를 먼저 자르려면 [shopping-cart 결제 승인/주문 확정 ↔ Spring 트랜잭션 경계 브릿지](./shopping-cart-payment-transaction-boundary-bridge.md)를 본다.
- 주문 완료 뒤 반응을 `AFTER_COMMIT`와 outbox 중 어디에 둘지 바로 연결하려면 [shopping-cart 주문 완료 후속 작업 ↔ AFTER_COMMIT vs Outbox 브릿지](./shopping-cart-order-complete-after-commit-outbox-bridge.md)를 읽는다.
- Spring 이벤트 phase 자체가 헷갈리면 [Spring EventListener, TransactionalEventListener, Outbox](./spring-eventlistener-transaction-phase-outbox.md)로 내려가서 `@EventListener`와 `@TransactionalEventListener`를 분리한다.
- 운영에서만 간헐적으로 후속 작업이 새는 비동기/순서 문제를 보려면 [Spring `@EventListener` Ordering and Async Traps](./spring-eventlistener-ordering-async-traps.md)를 이어서 본다.

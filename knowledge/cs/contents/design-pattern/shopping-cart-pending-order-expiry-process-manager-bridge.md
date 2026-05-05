---
schema_version: 3
title: 'shopping-cart 미결제 주문 만료 ↔ Process Manager와 Deadline 브릿지'
concept_id: design-pattern/shopping-cart-pending-order-expiry-process-manager-bridge
canonical: false
category: design-pattern
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- pending-order-expiry
- deadline-owner-boundary
- stale-timeout-guard
aliases:
- shopping-cart 주문 만료 처리
- 장바구니 미결제 주문 timeout
- shopping-cart 결제 대기 만료
- 주문 만료 스케줄러 책임
- shopping-cart stale deadline
symptoms:
- 결제 안 된 주문을 30분 뒤 자동 취소하려는데 어디가 이 흐름을 가져야 할지 모르겠어요
- 결제는 성공했는데 늦게 온 만료 스케줄러가 주문을 취소할까 봐 불안해요
- 주문 서비스, 결제 서비스, 스케줄러가 모두 timeout 규칙을 조금씩 알고 있어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- design-pattern/process-manager-deadlines-timeouts
- design-pattern/workflow-owner-vs-participant-context
- spring/shopping-cart-payment-transaction-boundary-bridge
next_docs:
- design-pattern/process-manager-deadlines-timeouts
- design-pattern/workflow-owner-vs-participant-context
- design-pattern/reservation-hold-expiry-consistency-seam
linked_paths:
- contents/design-pattern/process-manager-deadlines-timeouts.md
- contents/design-pattern/workflow-owner-vs-participant-context.md
- contents/design-pattern/reservation-hold-expiry-consistency-seam.md
- contents/spring/shopping-cart-payment-transaction-boundary-bridge.md
- contents/database/shopping-cart-payment-idempotency-stock-bridge.md
confusable_with:
- spring/shopping-cart-payment-transaction-boundary-bridge
- software-engineering/shopping-cart-checkout-service-layer-bridge
- design-pattern/reservation-hold-expiry-consistency-seam
forbidden_neighbors:
- contents/design-pattern/process-manager-deadlines-timeouts.md
- contents/design-pattern/workflow-owner-vs-participant-context.md
expected_queries:
- shopping-cart 미션에서 미결제 주문을 30분 뒤 만료시키려면 스케줄러만 두면 되는 거야?
- 결제 성공 이벤트가 왔는데 늦은 timeout 작업이 주문을 취소하지 않게 하려면 어떤 패턴으로 봐야 해?
- 주문 만료 책임을 결제 서비스가 가지면 왜 리뷰에서 경계가 흐린다고 할까?
- shopping-cart checkout에서 pending 주문, 만료 시각, 재시도를 한 객체가 관리해야 하나?
- 미션 리뷰에서 만료 정책을 workflow owner가 가져가라는 말이 무슨 뜻이야?
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션에서 결제 대기 중인 주문을 일정 시간 뒤
  만료시키는 흐름을 Process Manager와 deadline 관점으로 연결하는
  mission_bridge다. "30분 뒤 자동 취소", "결제 성공보다 timeout이 늦게 와도
  안전해야 함", "주문 서비스와 결제 서비스 중 누가 만료를 소유하나",
  "스케줄러가 상태를 직접 바꿔도 되나" 같은 학습자 표현을 workflow owner,
  stale timer 방지, confirm-or-expire 경계로 매핑한다.
---

# shopping-cart 미결제 주문 만료 ↔ Process Manager와 Deadline 브릿지

## 한 줄 요약

> shopping-cart의 미결제 주문 만료는 "30분 뒤 작업 하나 실행"보다 `PENDING_PAYMENT` 상태와 deadline을 함께 소유한 workflow owner가 늦은 timeout까지 해석하는 문제라서, 단순 scheduler callback보다 Process Manager 관점이 더 안전하다.

## 미션 시나리오

shopping-cart 미션에서 결제 전 주문을 먼저 만들면 곧 "30분 안에 결제가 없으면 자동 취소" 요구가 붙는다. 초반 구현은 주문 생성 시 `scheduleCancel(orderId, now + 30m)`를 걸고, 시간이 되면 스케줄러가 주문 상태를 바로 `EXPIRED`로 바꾸는 식으로 자주 시작한다. 처음엔 단순해 보이지만, 리뷰에서는 "결제 성공 직후 늦게 도착한 timeout은 어떻게 막을 건가", "주문 만료 정책을 누가 소유하나"라는 질문이 붙기 쉽다.

특히 헷갈리는 장면은 race다. 결제 승인 이벤트가 거의 동시에 오거나 재시도 응답이 늦게 오면, 주문 서비스는 이미 `PAID`로 바꿨는데 스케줄러는 예전 계획대로 만료를 실행하려 할 수 있다. 이때 문제를 "배치 하나 더 잘 짜면 되나"로 보면 계속 보완 패치가 늘고, 실제 질문인 "시간이 포함된 상태 전이를 누가 해석하나"를 놓치기 쉽다.

## CS concept 매핑

이 장면은 단순 cron이 아니라 long-running workflow에 가깝다. 주문은 `PENDING_PAYMENT`, `PAID`, `EXPIRED` 같은 상태를 가지며, deadline은 그 상태를 바꾸는 입력 중 하나다. 그래서 shopping-cart의 주문 만료는 보통 workflow owner가 `paymentDeadlineAt`과 timer version을 함께 들고 있다가, timeout 신호가 와도 "아직 결제 대기 상태인가", "이 신호가 최신 deadline에 대한 것인가"를 확인한 뒤에만 `ExpireOrder`를 발행하는 식으로 읽는 편이 맞다.

이렇게 보면 결제 서비스와 스케줄러의 책임도 분리된다. 결제 서비스는 승인/실패 사실만 주고, 스케줄러는 정해진 시각에 깨우기만 한다. 실제로 주문을 만료할지 말지는 checkout 흐름을 소유한 owner가 결정한다. 미결제 주문을 일시적 hold로 보고 `confirm or expire`를 닫는 감각이라서, 뒤늦은 timeout 무시, 중복 타이머 폐기, 만료 후 재결제 차단 같은 리뷰 포인트도 같은 구조 안에서 설명된다.

## 미션 PR 코멘트 패턴

- "스케줄러가 주문 상태를 직접 `EXPIRED`로 바꾸기보다, timeout 신호를 owner가 해석하도록 두는 편이 stale timer에 안전합니다."
- "결제 서비스가 주문 만료 시각까지 알기 시작하면 경계가 흐려집니다. 승인 사실만 돌려주고 만료 정책은 checkout 쪽이 가지세요."
- "주문 만료는 배치 작업이 아니라 시간 기반 상태 전이입니다. 현재 상태와 timer version 비교가 빠져 있으면 늦은 timeout이 유효한 주문을 덮을 수 있어요."
- "pending 주문을 만든 이상 `confirm or expire` 경로를 같이 설명해야 합니다. 취소 스케줄만 추가하면 흐름 소유자가 비어 보입니다."

## 다음 학습

- deadline, stale timer, reminder를 일반 패턴으로 다시 보려면 `design-pattern/process-manager-deadlines-timeouts`
- workflow owner와 participant 경계를 더 선명하게 자르려면 `design-pattern/workflow-owner-vs-participant-context`
- hold, expiry, confirm을 일관성 seam으로 읽으려면 `design-pattern/reservation-hold-expiry-consistency-seam`
- 결제 승인과 로컬 트랜잭션 경계를 먼저 정리하려면 `spring/shopping-cart-payment-transaction-boundary-bridge`

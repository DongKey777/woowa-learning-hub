---
schema_version: 3
title: 마지막 재고가 두 번 팔려요 원인 라우터
concept_id: database/last-stock-sold-twice-symptom-router
canonical: false
category: database
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/shopping-cart
- missions/roomescape
review_feedback_tags:
- oversell-first-triage
- inventory-truth-shape
- duplicate-vs-capacity-split
aliases:
- 마지막 재고 두 번 팔림
- 재고가 마이너스가 돼요
- oversell 원인 라우터
- 둘 다 결제 성공했는데 재고 부족
- 예약 둘 다 성공했는데 capacity 초과
symptoms:
- 마지막 1개 재고인데 두 요청이 모두 성공한 것처럼 보여요
- 주문은 둘 다 완료됐는데 재고 수량이 0 아래로 내려가거나 덜 차감돼요
- 예약이나 쿠폰 발급은 개별 row가 정상인데 전체 capacity만 초과돼요
- duplicate key는 안 났는데도 결과적으로 두 번 팔린 것처럼 보여서 어디부터 봐야 할지 모르겠어요
intents:
- symptom
- troubleshooting
- mission_bridge
prerequisites:
- database/transaction-basics
- database/sql-relational-modeling-basics
next_docs:
- database/lost-update-vs-oversell-vs-duplicate-insert-beginner-bridge
- database/single-counter-vs-ledger-vs-slot-inventory-oversell-decision
- database/shopping-cart-payment-idempotency-stock-bridge
- database/guard-row-scope-design-multi-day-bookings
linked_paths:
- contents/database/lost-update-vs-oversell-vs-duplicate-insert-beginner-bridge.md
- contents/database/single-counter-vs-ledger-vs-slot-inventory-oversell-decision-card.md
- contents/database/shopping-cart-payment-idempotency-stock-bridge.md
- contents/database/guard-row-scope-design-multi-day-bookings.md
- contents/database/shared-pool-guard-design-room-type-inventory.md
- contents/database/unique-vs-slot-row-vs-guard-row-quick-chooser.md
confusable_with:
- database/lost-update-vs-oversell-vs-duplicate-insert-beginner-bridge
- database/duplicate-key-then-not-found-symptom-router
- database/overlapping-bookings-both-succeed-symptom-router
forbidden_neighbors:
- contents/database/shopping-cart-payment-idempotency-stock-bridge.md
- contents/database/unique-vs-slot-row-vs-guard-row-quick-chooser.md
expected_queries:
- 마지막 재고가 두 번 팔린 것처럼 보일 때 원인을 어떻게 나눠 봐야 해?
- 둘 다 성공했는데 재고가 음수가 되면 lost update인지 oversell인지 어디서 갈라?
- duplicate key도 없는데 capacity가 초과되면 어떤 문서부터 읽어야 해?
- shopping-cart에서 마지막 재고 동시 결제 성공이 보이면 먼저 무슨 질문을 해야 해?
- 예약 시스템에서 개별 row는 정상인데 총량만 넘칠 때 어떤 원인을 의심해?
contextual_chunk_prefix: |
  이 문서는 마지막 재고가 두 번 팔리거나 capacity가 조용히 넘칠 때 학습자
  증상을 same-row overwrite, 여러 claim 합계 초과, slot이나 guard 설계 누락,
  duplicate insert와의 혼동으로 나눠 주는 symptom_router다. 둘 다 성공함,
  재고가 음수, duplicate key는 없는데 결과가 틀림, 주문은 두 개고 stock은 하나,
  예약 row는 멀쩡한데 총량만 넘침 같은 자연어 표현이 oversell 진단 분기에
  매핑된다.
---
# 마지막 재고가 두 번 팔려요 원인 라우터

## 한 줄 요약

> `마지막 재고가 두 번 팔렸다`는 말은 에러 이름이 아니라 결과 증상이라서, 같은 row를 덮어쓴 건지, 여러 row 합계가 샌 건지, 아니면 애초에 duplicate insert와 헷갈린 건지부터 나눠야 다음 문서가 맞게 연결된다.

## 가능한 원인

1. **single counter row를 둘이 같이 읽고 덮어썼다.** `stock=1` 같은 숫자 row를 읽은 뒤 애플리케이션에서 `stock-1`로 저장하면 둘 다 성공했는데 최종 값이 한 번만 줄어든 것처럼 보일 수 있다. 이 갈래는 [Lost Update vs Oversell vs Duplicate Insert Beginner Bridge](./lost-update-vs-oversell-vs-duplicate-insert-beginner-bridge.md)로 바로 이어진다.
2. **개별 row는 정상인데 count/sum capacity를 아무도 write 시점에 닫지 않았다.** claim, hold, 예약 row를 쌓아 두고 `COUNT(*)`나 `SUM(qty)`만 보고 승인하면 총량 invariant가 샐 수 있다. 이 경우는 [Single Counter vs Ledger vs Slot Inventory Oversell Decision Card](./single-counter-vs-ledger-vs-slot-inventory-oversell-decision-card.md)와 [Shared-Pool Guard Design for Room-Type Inventory](./shared-pool-guard-design-room-type-inventory.md)를 본다.
3. **slot 또는 guard key 설계가 실제 충돌 surface를 못 만났다.** 예약 범위를 day/slot으로 쪼갰는데 충돌 가능한 요청이 같은 key를 공유하지 않거나, reschedule에서 `old ∪ new`를 함께 잠그지 않으면 둘 다 성공처럼 보일 수 있다. 이 갈래는 [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)와 [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)로 이어진다.
4. **사실은 oversell이 아니라 duplicate insert나 멱등성 누락이다.** 같은 결제 시도를 한 번만 인정해야 하는데 `idempotency_key` 없이 주문을 두 번 만들면, 재고 문제처럼 보여도 write truth는 "같은 시도를 두 번 인정한 것"일 수 있다. shopping-cart 맥락이라면 [shopping-cart 결제 재시도/재고 차감 ↔ 멱등성 키와 조건부 UPDATE 브릿지](./shopping-cart-payment-idempotency-stock-bridge.md)를 먼저 본다.

## 빠른 자기 진단

1. 패배 요청이 `duplicate key`였는지, 아니면 둘 다 성공했는지 먼저 적는다. `duplicate key`가 보이면 oversell보다 duplicate insert 분기가 더 가깝다.
2. 재고 truth가 `stock` 한 줄인지, active claim 합계인지, 시간 slot 집합인지 확인한다. 모델 shape를 모르고 락부터 고르면 문서를 잘못 타기 쉽다.
3. 성공한 두 요청이 같은 row를 최종 저장했는지 본다. 같은 row overwrite면 lost update 쪽이고, 개별 row는 멀쩡한데 총량만 넘으면 ledger/guard 분기다.
4. 예약 변경이나 멀티데이 점유라면 충돌 가능한 두 요청이 실제로 같은 slot/guard key를 공유했는지 확인한다. 공유하지 않았다면 lock을 써도 oversell처럼 보이는 누수가 남는다.

## 다음 학습

- same-row overwrite인지 oversell인지 먼저 분류하려면 [Lost Update vs Oversell vs Duplicate Insert Beginner Bridge](./lost-update-vs-oversell-vs-duplicate-insert-beginner-bridge.md)를 본다.
- 재고 truth가 single counter, ledger, slot 중 어디인지부터 정리하려면 [Single Counter vs Ledger vs Slot Inventory Oversell Decision Card](./single-counter-vs-ledger-vs-slot-inventory-oversell-decision-card.md)로 간다.
- shopping-cart에서 중복 주문 방지와 재고 차감을 함께 봐야 하면 [shopping-cart 결제 재시도/재고 차감 ↔ 멱등성 키와 조건부 UPDATE 브릿지](./shopping-cart-payment-idempotency-stock-bridge.md)를 읽는다.
- 예약/재고 pool처럼 여러 key를 함께 직렬화해야 한다면 [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)와 [Shared-Pool Guard Design for Room-Type Inventory](./shared-pool-guard-design-room-type-inventory.md)로 이어간다.

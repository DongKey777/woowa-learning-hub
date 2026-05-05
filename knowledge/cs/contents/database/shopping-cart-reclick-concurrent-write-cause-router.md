---
schema_version: 3
title: shopping-cart 재클릭/동시 요청 꼬임 원인 라우터
concept_id: database/shopping-cart-reclick-concurrent-write-cause-router
canonical: false
category: database
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- reclick-race-triage
- duplicate-vs-lost-update-split
- write-time-arbitration-choice
aliases:
- shopping-cart 재클릭 동시요청 라우터
- 장바구니 요청 두 번 보내면 결과 꼬임
- shopping-cart race condition 어디부터 봐야 해
- 장바구니 중복 row와 수량 덮어쓰기 구분
- 결제 쿠폰 수량 동시 요청 진단
symptoms:
- add to cart를 빠르게 두 번 눌렀더니 같은 상품 row가 두 줄 생겨요
- 장바구니 수량을 여러 탭에서 바꾸면 마지막 요청만 남고 한쪽 변경이 사라져요
- 쿠폰 적용이나 결제 요청을 재시도하면 실패 대신 같은 결과를 재사용해야 할지 새로 처리해야 할지 헷갈려요
- shopping-cart에서 재클릭 뒤 중복 주문, 중복 할인, 수량 꼬임이 번갈아 보여서 어느 종류의 race인지 먼저 못 가르겠어요
intents:
- symptom
- troubleshooting
- mission_bridge
- design
prerequisites:
- database/transaction-basics
- software-engineering/shopping-cart-checkout-service-layer-bridge
next_docs:
- database/shopping-cart-cart-item-merge-unique-upsert-bridge
- database/shopping-cart-cart-item-quantity-lost-update-version-cas-bridge
- database/shopping-cart-coupon-apply-once-unique-claim-bridge
- database/shopping-cart-payment-idempotency-stock-bridge
linked_paths:
- contents/database/shopping-cart-cart-item-merge-unique-upsert-bridge.md
- contents/database/shopping-cart-cart-item-quantity-lost-update-version-cas-bridge.md
- contents/database/shopping-cart-coupon-apply-once-unique-claim-bridge.md
- contents/database/shopping-cart-payment-idempotency-stock-bridge.md
- contents/database/unique-vs-version-cas-vs-for-update-decision-guide.md
- contents/database/idempotency-key-and-deduplication.md
confusable_with:
- database/shopping-cart-cart-item-merge-unique-upsert-bridge
- database/shopping-cart-cart-item-quantity-lost-update-version-cas-bridge
- database/shopping-cart-coupon-apply-once-unique-claim-bridge
- database/shopping-cart-payment-idempotency-stock-bridge
- database/unique-vs-version-cas-vs-for-update-chooser
forbidden_neighbors:
- contents/database/shopping-cart-cart-item-merge-unique-upsert-bridge.md
- contents/database/shopping-cart-cart-item-quantity-lost-update-version-cas-bridge.md
expected_queries:
- shopping-cart에서 버튼 재클릭 뒤 결과가 꼬일 때 duplicate insert인지 lost update인지 어떻게 먼저 구분해?
- 장바구니 같은 상품이 두 줄 생기는 문제와 수량이 덮어써지는 문제를 DB 관점에서 어디서 갈라 봐야 해?
- 쿠폰 적용 재시도와 결제 재시도는 둘 다 멱등성으로 보면 되는지, cart item 경쟁과는 어떻게 다른지 알고 싶어
- shopping-cart 미션에서 중복 주문, 중복 할인, 수량 충돌이 한꺼번에 보이면 어떤 질문 순서로 원인을 좁혀야 해?
- 재클릭 때문에 생긴 장바구니 race를 unique, version, idempotency 중 무엇으로 설명해야 할지 판단 기준이 필요해
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션에서 재클릭, 여러 탭, timeout 뒤 재시도로
  결과가 꼬일 때 원인을 가르는 symptom_router다. 같은 상품 row가 두 줄 생김,
  수량 수정이 서로 덮어씀, 쿠폰 적용을 두 번 눌렀을 때 duplicate loser를
  기존 결과 재사용으로 봐야 함, 결제 요청 재전송이 새 주문 생성으로 번짐 같은
  학습자 표현을 duplicate insert, existing row lost update, coupon-use claim,
  payment idempotency 네 갈래로 라우팅한다.
---

# shopping-cart 재클릭/동시 요청 꼬임 원인 라우터

## 한 줄 요약

> shopping-cart에서 "버튼을 두 번 눌렀더니 꼬였다"는 말만으로는 원인이 하나가 아니다. 먼저 새 row가 중복 생성된 건지, 기존 row가 서로 덮어쓴 건지, 같은 business attempt를 한 번만 인정해야 하는 문제인지 갈라야 다음 설계가 맞다.

## 가능한 원인

1. **같은 cart item을 새 row로 두 번 만들었다.** `existsBy`로 먼저 보고 비어 있으면 insert하는 흐름이라면, 거의 동시에 들어온 두 요청이 모두 새 row를 만들 수 있다. 이 갈래는 [shopping-cart 같은 상품 중복 담기 ↔ UNIQUE 제약과 UPSERT 브릿지](./shopping-cart-cart-item-merge-unique-upsert-bridge.md)로 이어진다.
2. **이미 있는 cart item row를 서로 다른 이전 값으로 덮어썼다.** 같은 상품 수량을 두 탭에서 바꾸거나 증가와 삭제가 겹치면 문제 축은 duplicate insert가 아니라 lost update다. 이 경우는 [shopping-cart 장바구니 수량 동시 수정 ↔ Lost Update와 Version CAS 브릿지](./shopping-cart-cart-item-quantity-lost-update-version-cas-bridge.md)를 먼저 본다.
3. **쿠폰 적용 같은 "같은 시도"를 한 번만 인정해야 하는 경로였다.** 여기서는 수량 merge처럼 둘을 합치는 게 아니라, coupon-use attempt의 승자를 `UNIQUE`로 정하고 loser가 기존 `PENDING` 또는 `APPLIED` row를 재사용해야 한다. 이 갈래는 [shopping-cart 쿠폰 중복 적용/재시도 ↔ UNIQUE claim과 existing row 재사용 브릿지](./shopping-cart-coupon-apply-once-unique-claim-bridge.md)로 연결된다.
4. **결제 재시도와 재고 차감이 한 덩어리로 섞였다.** 같은 결제 시도를 한 번만 인정하는 멱등성 문제와, 재고를 0 아래로 내리지 않게 닫는 문제는 다르다. 이 갈래는 [shopping-cart 결제 재시도/재고 차감 ↔ 멱등성 키와 조건부 UPDATE 브릿지](./shopping-cart-payment-idempotency-stock-bridge.md)로 가서 `idempotency_key`와 재고 invariant를 따로 본다.

## 빠른 자기 진단

1. 결과가 "row가 늘었다"인지 "row는 하나인데 값이 사라졌다"인지 먼저 적는다. 전자면 duplicate insert, 후자면 lost update 쪽이 가깝다.
2. 충돌 대상이 cart item인지, coupon-use row인지, order/payment attempt인지 구분한다. 같은 재클릭이라도 business identity가 다르면 필요한 DB 장치가 달라진다.
3. 패배 요청을 실패로 끝낼지, 기존 결과를 재사용할지 정한다. 쿠폰 적용과 결제 재시도는 loser replay 계약이 중요하지만, cart item 수량 충돌은 보통 재조회나 충돌 응답이 더 자연스럽다.
4. 재고까지 같이 이상하면 "중복 주문"과 "oversell"을 섞지 말고 따로 본다. 주문 멱등성과 stock write 조건은 같은 락 하나로 설명되지 않는다.

## 다음 학습

- 같은 상품이 두 줄 생기는 duplicate insert라면 [shopping-cart 같은 상품 중복 담기 ↔ UNIQUE 제약과 UPSERT 브릿지](./shopping-cart-cart-item-merge-unique-upsert-bridge.md)를 본다.
- 기존 수량 row를 서로 덮어쓰는 충돌이라면 [shopping-cart 장바구니 수량 동시 수정 ↔ Lost Update와 Version CAS 브릿지](./shopping-cart-cart-item-quantity-lost-update-version-cas-bridge.md)를 잇는다.
- 쿠폰 적용 재시도에서 loser가 기존 결과를 재사용해야 한다면 [shopping-cart 쿠폰 중복 적용/재시도 ↔ UNIQUE claim과 existing row 재사용 브릿지](./shopping-cart-coupon-apply-once-unique-claim-bridge.md)로 간다.
- 결제 재시도와 재고 차감이 동시에 보이면 [shopping-cart 결제 재시도/재고 차감 ↔ 멱등성 키와 조건부 UPDATE 브릿지](./shopping-cart-payment-idempotency-stock-bridge.md)를 이어서 읽는다.

---
schema_version: 3
title: 'shopping-cart 결제 재시도/재고 차감 ↔ 멱등성 키와 조건부 UPDATE 브릿지'
concept_id: database/shopping-cart-payment-idempotency-stock-bridge
canonical: false
category: database
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- payment-idempotency
- conditional-update-stock
- transactional-boundary
aliases:
- shopping-cart 중복 주문 방지
- 장바구니 결제 멱등성
- shopping-cart 재고 차감
- 결제 재시도 중복 주문
- '@Transactional 중복 결제'
symptoms:
- 결제 버튼 두 번 눌렀더니 주문이 두 개 생겨요
- 재고 1개인데 동시에 결제 성공이 떠요
- '@Transactional 붙였는데도 중복 주문이 나요'
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/transactional-basics
- database/transaction-isolation-basics
- database/lock-basics
next_docs:
- spring/transactional-basics
- database/transaction-isolation-basics
- database/lock-basics
linked_paths:
- contents/spring/spring-payment-approval-db-failure-compensation-idempotency-primer.md
- contents/database/single-counter-oversell-first-fix-card.md
- contents/database/idempotency-key-and-deduplication.md
- contents/database/shopping-cart-cart-item-merge-unique-upsert-bridge.md
- contents/database/shopping-cart-cart-item-quantity-lost-update-version-cas-bridge.md
- contents/database/shopping-cart-coupon-apply-once-unique-claim-bridge.md
- contents/network/shopping-cart-rate-limit-bridge.md
- contents/database/shopping-cart-reclick-concurrent-write-cause-router.md
confusable_with:
- database/shopping-cart-cart-item-merge-unique-upsert-bridge
- database/shopping-cart-cart-item-quantity-lost-update-version-cas-bridge
- database/shopping-cart-coupon-apply-once-unique-claim-bridge
- database/shopping-cart-reclick-concurrent-write-cause-router
- network/shopping-cart-rate-limit-bridge
- spring/transactional-basics
forbidden_neighbors:
- contents/network/shopping-cart-rate-limit-bridge.md
expected_queries:
- shopping-cart에서 결제 재시도 오면 중복 주문을 어떻게 막아?
- 장바구니 마지막 재고 결제는 락을 걸어야 해 아니면 update 조건으로 막아?
- '@Transactional만으로 shopping-cart 중복 결제와 재고 차감을 막을 수 있어?'
- 결제 승인 후 주문 저장이 실패하면 shopping-cart에서는 뭘 먼저 설계해야 해?
- rate limit 말고 주문 한 번만 생성되게 하는 DB 방법이 뭐야?
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션에서 결제 재시도와 재고 차감이 함께 나올 때
  중복 주문 방지와 oversell 방지를 같은 문제로 섞지 않도록, 멱등성 키로 같은 승인
  시도를 한 번만 인정하는 축과 조건부 UPDATE로 재고 불변식을 닫는 축을 연결하는
  mission_bridge다. 결제 버튼 두 번, 마지막 1개 동시 구매, 같은 승인 재실행,
  롤백만 믿어도 되나, 주문은 한 번만 만들고 재고는 어디서 막지 같은 자연어 표현이
  이 문서의 설계 분기에 매핑된다.
---

# shopping-cart 결제 재시도/재고 차감 ↔ 멱등성 키와 조건부 UPDATE 브릿지

## 한 줄 요약

shopping-cart에서 "주문이 두 번 생김"과 "마지막 재고가 둘 다 팔림"은 같은 문제가 아니다. 전자는 `idempotency_key` + `UNIQUE`로 같은 결제 시도를 한 번만 인정하는 문제이고, 후자는 `UPDATE ... WHERE stock > 0` 같은 write-time 조건으로 재고 invariant를 닫는 문제다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "결제 버튼을 두 번 눌렀더니 주문이 두 개 생겨요" | 같은 checkout attempt가 재시도/더블클릭으로 두 번 들어온 장면 | idempotency key와 `UNIQUE`로 같은 시도를 한 번만 인정한다 |
| "재고 1개인데 동시에 결제 성공이 떠요" | 마지막 재고 oversell | 조건부 `UPDATE ... WHERE stock > 0`처럼 write-time invariant로 닫는다 |
| "`@Transactional`을 붙였는데도 중복 주문이 나요" | transaction boundary를 dedup/stock guard로 오해한 코드 | local transaction, idempotency, stock arbitration을 다른 축으로 본다 |

## 미션 시나리오

학습자가 shopping-cart 미션에서 자주 맞는 장면은 이렇다. 사용자가 결제 버튼을 두 번 누르거나 네트워크 timeout 뒤 재시도하면 `POST /orders`가 두 번 들어온다. 동시에 인기 상품 재고가 1개 남았을 때 두 사용자가 거의 같이 결제하면 둘 다 "성공"처럼 보일 수 있다.

PR에서 흔한 초기 구현은 `existsByOrderKey()`로 먼저 확인하고 없으면 주문을 저장하거나, 재고를 읽어 `stock - 1`로 다시 저장하는 형태다. 이 패턴은 둘 다 read-after-check race가 남는다. `@Transactional`은 메서드 경계를 묶어 주지만, "같은 시도는 한 번만"과 "재고는 0 아래로 내려가면 안 됨"을 자동으로 닫아 주지는 않는다.

## CS concept 매핑

shopping-cart 결제 재시도는 DB 관점에서 "같은 business attempt를 한 번만 승인"하는 멱등성 문제다. 보통 `idempotency_key`를 주문/결제 테이블 또는 별도 dedup 테이블에 저장하고 `UNIQUE`로 승자를 정한다. 같은 키가 다시 오면 새 주문을 만들지 않고 기존 결과를 돌려준다.

재고 차감은 다른 축이다. single counter라면 `UPDATE inventory SET stock = stock - 1 WHERE product_id = ? AND stock > 0`처럼 한 SQL로 invariant를 닫는 편이 첫 기본값이다. 이 두 축을 섞어 "중복 결제도 락으로, 재고도 멱등성으로" 처리하려 하면 설계가 흐려진다. 결제 승인 후 DB 저장 실패는 또 별도 경계라서 rollback 기대보다 보상 취소와 상태 재조회 경로를 먼저 둬야 한다.

## 미션 PR 코멘트 패턴

- "`@Transactional`만으로 중복 주문이 막히지 않아요. 같은 결제 시도를 식별하는 키가 먼저 필요합니다."
- "`exists -> save` 사이에 race가 남습니다. DB `UNIQUE` 또는 insert-first arbitration으로 바꾸세요."
- "재고는 읽어서 빼지 말고 write 조건으로 닫으세요. 실패 신호는 update count 0으로 받는 편이 단순합니다."
- "외부 승인 성공 뒤 저장 실패는 로컬 rollback으로 끝나지 않습니다. 보상 취소나 idempotent replay 경로를 명시하세요."
- "rate limit은 abuse 방어고, 주문 중복 방지는 멱등성 계약입니다. 두 책임을 분리해서 설명해 주세요."

## 다음 학습

- 주문 재시도와 응답 재사용 계약을 더 자세히 보려면 `멱등성 키와 중복 방지` 문서로 간다.
- single counter 재고 차감의 첫 선택 순서를 정리하려면 `Single Counter Oversell First-Fix Card`를 본다.
- `@Transactional`이 무엇을 보장하고 무엇을 보장하지 않는지 다시 잡으려면 `Spring @Transactional 기초`로 돌아간다.
- shopping-cart에서 rate limit과 멱등성의 책임 차이를 비교하려면 `shopping-cart rate limit bridge`를 이어서 읽는다.

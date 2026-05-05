---
schema_version: 3
title: 'lotto 구매 1회/여러 장 티켓 저장 ↔ Spring @Transactional 경계 브릿지'
concept_id: spring/lotto-purchase-ticket-transaction-boundary-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/lotto
review_feedback_tags:
- transactional-boundary
- parent-child-atomicity
- controller-vs-service-tx
aliases:
- lotto 구매 저장 트랜잭션
- 로또 여러 장 티켓 @Transactional
- lotto purchase service transaction
- 로또 purchase ticket atomic save
- lotto 서비스 트랜잭션 경계
symptoms:
- 로또 구매 1건과 티켓 여러 장을 저장할 때 어디에 @Transactional을 붙여야 할지 모르겠어요
- purchase 먼저 save하고 ticket를 저장하다 중간에 실패하면 어디까지 롤백돼요
- controller에서 구매 흐름을 돌리는데 트랜잭션을 어디에 둬야 하냐는 리뷰를 받았어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- software-engineering/lotto-purchase-flow-service-layer-bridge
- database/lotto-purchase-ticket-parent-child-modeling-bridge
- spring/transactional-basics
next_docs:
- spring/spring-service-layer-transaction-boundary-patterns
- database/lotto-purchase-duplicate-submit-idempotency-bridge
- database/transaction-basics
linked_paths:
- contents/software-engineering/lotto-purchase-flow-service-layer-bridge.md
- contents/database/lotto-purchase-ticket-parent-child-modeling-bridge.md
- contents/database/lotto-purchase-duplicate-submit-idempotency-bridge.md
- contents/spring/spring-transactional-basics.md
- contents/spring/spring-service-layer-transaction-boundary-patterns.md
confusable_with:
- software-engineering/lotto-purchase-flow-service-layer-bridge
- database/lotto-purchase-ticket-parent-child-modeling-bridge
- database/lotto-purchase-duplicate-submit-idempotency-bridge
forbidden_neighbors: []
expected_queries:
- 로또 구매 한 번에 purchase row와 ticket row 여러 개를 저장하면 서비스 메서드에 트랜잭션을 잡아야 해?
- lotto를 웹으로 옮겼더니 구매 저장 중간 실패가 걱정돼. @Transactional 경계는 어디가 맞아?
- controller에서 여러 장 로또를 만들고 저장하는 흐름에 트랜잭션을 붙이지 말라는 이유가 뭐야?
- purchase 저장 후 ticket 저장이 실패하면 반쯤 남지 않게 Spring에서 어떻게 묶어?
- 로또 구매 서비스와 repository 중 어느 쪽이 원자성을 책임져야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa lotto 미션을 Spring과 DB 저장 흐름으로 옮길 때 구매 1건과
  여러 ticket row를 한 번의 `@Transactional` 경계로 어디서 묶어야 하는지 설명하는
  mission_bridge다. 로또 구매 저장 트랜잭션, purchase 먼저 save 후 ticket 실패,
  controller에 트랜잭션을 둘지 service에 둘지, parent-child row를 원자적으로
  확정하기, 반쯤 저장된 구매를 막기 같은 학습자 표현을 Spring 서비스 경계와
  원자성 감각으로 매핑한다.
---

# lotto 구매 1회/여러 장 티켓 저장 ↔ Spring @Transactional 경계 브릿지

## 한 줄 요약

> lotto 구매 한 번이 `purchase` 1건과 `ticket` 여러 장을 함께 확정하는 유스케이스라면, 트랜잭션 경계도 Controller나 Repository가 아니라 그 흐름을 조립하는 Service 메서드에 두는 편이 자연스럽다.

## 미션 시나리오

lotto를 콘솔 과제에서 웹 애플리케이션으로 옮기면 구매 금액으로 장수를 계산하고, 번호를 생성하고, `purchase`를 저장한 뒤 `ticket` 여러 장을 저장하는 흐름이 생긴다. 이때 학습자는 자주 "save는 repository가 하니까 트랜잭션도 repository에 두면 되지 않나?" 혹은 "Controller가 구매 요청을 다 알고 있으니 거기에 `@Transactional`을 붙이면 한 번에 묶이지 않나?"에서 막힌다.

문제는 저장 SQL 개수보다 의미 단위다. 리뷰에서 "구매 한 번이 반쯤 저장되면 안 된다", "부모 purchase와 자식 ticket이 함께 성공하거나 함께 실패해야 한다"는 말을 듣는 자리가 여기다. `purchase` row만 남고 `ticket` 저장이 중간에 터지면, DB에는 이미 존재하는 구매인데 학습자 눈에는 실패한 요청처럼 보이는 어색한 상태가 생긴다.

## CS concept 매핑

Spring에서 `@Transactional`은 "이 메서드가 책임지는 DB 변경을 한 원자 단위로 commit/rollback한다"는 선언이다. lotto 구매에서는 `구매 금액 해석 -> purchase 생성 -> ticket 여러 장 저장`이 하나의 유스케이스이므로, 이 순서를 조립하는 Service 메서드가 경계가 된다.

짧게 그리면 `purchaseRepository.save(purchase)`와 `ticketRepository.saveAll(tickets)`를 같은 서비스 메서드 안에서 호출하고, 그 메서드에 `@Transactional`을 둔다. 그러면 자식 ticket 저장에서 예외가 나면 부모 purchase 저장도 함께 rollback된다. 반대로 각 Repository 메서드가 자기 안에서 따로 commit하면 "부모는 저장됐는데 자식은 일부만 실패" 같은 상태를 막기 어렵다.

여기서 중요한 구분이 하나 더 있다. 이 문서는 "부모-자식 row를 한 번에 확정하는 로컬 트랜잭션" 이야기다. 더블클릭 재전송처럼 같은 구매 요청이 두 번 들어오는 문제는 별도 축이므로, 그것까지 해결하려면 멱등성 키나 `UNIQUE` 제약을 이어서 봐야 한다.

## 미션 PR 코멘트 패턴

- "구매 한 번이 여러 repository 호출로 끝나는데 `@Transactional`이 없으면 중간 실패 시 반쯤 저장될 수 있습니다. 서비스 경계에서 묶어 보세요."
- "Controller는 HTTP 요청을 받고 응답을 만드는 자리이지, 원자성 경계를 표현하는 자리가 아닙니다."
- "Repository마다 트랜잭션을 따로 두면 purchase와 ticket 저장이 같은 비즈니스 단위로 묶이지 않습니다."
- "트랜잭션으로 막는 문제와 중복 요청을 막는 문제를 분리해 설명해 보세요. 전자는 atomic save, 후자는 idempotency입니다."

## 다음 학습

- service 메서드에 트랜잭션을 두는 일반 패턴은 `spring/spring-service-layer-transaction-boundary-patterns`
- 구매 1건과 티켓 여러 장의 DB 구조를 먼저 다시 잡으려면 `database/lotto-purchase-ticket-parent-child-modeling-bridge`
- 중복 구매 재전송까지 같이 고민해야 하면 `database/lotto-purchase-duplicate-submit-idempotency-bridge`
- 메모리 안 구매 흐름 조립 책임을 복습하려면 `software-engineering/lotto-purchase-flow-service-layer-bridge`

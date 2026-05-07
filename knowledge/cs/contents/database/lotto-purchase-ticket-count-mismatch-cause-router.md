---
schema_version: 3
title: lotto 구매 저장 뒤 티켓 수 불일치 원인 라우터
concept_id: database/lotto-purchase-ticket-count-mismatch-cause-router
canonical: false
category: database
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/lotto
review_feedback_tags:
- purchase-ticket-count-mismatch
- parent-child-modeling-gap
- transaction-boundary-leak
aliases:
- lotto 티켓 수 불일치
- 로또 구매 저장 뒤 티켓 개수 이상
- lotto purchase ticket count mismatch
- 로또 purchase 와 ticket 수가 안 맞아요
- lotto 저장했는데 ticket row 개수가 달라요
symptoms:
- lotto 구매를 저장했는데 구매 금액으로 계산한 장수와 DB ticket row 수가 맞지 않아요
- 한 번 구매했는데 purchase 는 1건인데 ticket 이 덜 저장되거나 더 저장돼 보여요
- 로또 구매 완료 화면은 성공인데 다시 조회하면 티켓 수가 달라져요
- 리뷰에서 purchase 와 ticket 을 같은 원자 단위로 보라는 말을 들었는데 왜 필요한지 모르겠어요
intents:
- symptom
- troubleshooting
- mission_bridge
prerequisites:
- software-engineering/lotto-purchase-flow-service-layer-bridge
next_docs:
- database/lotto-purchase-ticket-parent-child-modeling-bridge
- spring/lotto-purchase-ticket-transaction-boundary-bridge
- database/lotto-purchase-duplicate-submit-idempotency-bridge
- software-engineering/lotto-purchase-history-repository-boundary-bridge
linked_paths:
- contents/database/lotto-purchase-ticket-parent-child-modeling-bridge.md
- contents/spring/lotto-purchase-ticket-transaction-boundary-bridge.md
- contents/database/lotto-purchase-duplicate-submit-idempotency-bridge.md
- contents/software-engineering/lotto-purchase-flow-service-layer-bridge.md
- contents/software-engineering/lotto-purchase-history-repository-boundary-bridge.md
confusable_with:
- database/lotto-purchase-ticket-parent-child-modeling-bridge
- spring/lotto-purchase-ticket-transaction-boundary-bridge
- database/lotto-purchase-duplicate-submit-idempotency-bridge
- software-engineering/lotto-purchase-history-repository-boundary-bridge
forbidden_neighbors: []
expected_queries:
- 로또 구매 한 번이 끝났는데 왜 purchase 한 건에 ticket 개수가 기대한 장수와 다르게 남을 수 있어?
- 구매 완료는 떴는데 나중에 조회하면 티켓이 빠져 있거나 중복으로 보일 때 어디부터 의심해야 해?
- lotto 저장 흐름에서 purchase 와 ticket 을 같은 트랜잭션으로 보라는 리뷰는 무슨 뜻이야?
- 금액으로는 5장 샀는데 DB 에는 4장만 보일 때 모델링 문제인지 중복 제출인지 어떻게 가를까?
- 로또 웹 버전에서 ticket row 수가 들쭉날쭉하면 parent-child 저장 구조와 재전송 중 무엇부터 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa lotto 미션을 저장 가능한 구조로 확장할 때 구매 1건과
  여러 ticket row의 개수가 맞지 않아 보이는 증상을 원인별로 가르는
  symptom_router다. purchase 는 저장됐는데 ticket 이 덜 보인다, 한 번
  눌렀는데 중복 티켓이 생긴다, 완료 화면과 재조회 결과가 다르다, purchase 와
  ticket 을 왜 같은 원자 단위로 보라는지 모르겠다는 학습자 표현을 부모-자식
  모델링, 트랜잭션 경계, 재전송 멱등성, 조회 경계 갈래로 라우팅한다.
---

# lotto 구매 저장 뒤 티켓 수 불일치 원인 라우터

## 한 줄 요약

> lotto에서 구매 금액으로 계산한 장수와 DB의 ticket row 수가 다르게 보인다면, 먼저 "저장 구조를 잘못 잡은 것인지", "같은 유스케이스를 한 원자 단위로 묶지 못한 것인지", "중복 제출을 다른 문제로 보고 있는지", "조회 쪽이 다른 단위를 보여 주는지"를 갈라야 한다.

## 가능한 원인

1. **purchase 1건과 ticket 여러 장의 저장 구조가 처음부터 흐리다.** `purchase`와 `ticket`의 부모-자식 경계가 없거나, 장수 의미를 `purchase` 금액과 `ticket` row 사이에 일관되게 묶지 못하면 저장 후 개수 비교 자체가 흔들린다. 이 갈래는 [lotto 구매 1회/여러 장 티켓 저장 ↔ 부모-자식 테이블 모델링 브릿지](./lotto-purchase-ticket-parent-child-modeling-bridge.md)로 이어진다.
2. **같은 구매 유스케이스를 한 트랜잭션으로 묶지 못했다.** `purchase` insert와 `ticket` 여러 장 insert가 서로 다른 commit 단위로 흩어지면, 중간 실패 때 "구매는 있는데 티켓이 덜 있는" 모양이 생길 수 있다. 이 경우는 [lotto 구매 1회/여러 장 티켓 저장 ↔ Spring `@Transactional` 경계 브릿지](../spring/lotto-purchase-ticket-transaction-boundary-bridge.md)를 먼저 본다.
3. **브라우저 재전송이나 중복 제출을 저장 구조 문제로 착각하고 있다.** 새로고침, 재시도, 버튼 중복 클릭 때문에 같은 구매 요청이 두 번 들어오면 ticket row 수가 "과하게 많은" 쪽으로 어긋난다. 이 갈래는 [lotto 구매 재시도/중복 티켓 저장 ↔ 멱등성 키와 UNIQUE 브릿지](./lotto-purchase-duplicate-submit-idempotency-bridge.md)로 가서 중복 허용 surface를 본다.
4. **조회가 purchase 단위가 아니라 다른 단위를 보여 준다.** 저장은 맞는데 화면이나 조회 API가 `purchase` 1건 기준이 아니라 전체 `ticket` 집합이나 다른 구매 묶음을 펼쳐 보여 주면, 학습자는 저장 불일치처럼 느끼기 쉽다. 이때는 [lotto 구매 1회 재조회 ↔ PurchaseRepository 경계 브릿지](../software-engineering/lotto-purchase-history-repository-boundary-bridge.md)로 가서 조회 모델의 기준 단위를 확인한다.

## 빠른 자기 진단

1. `purchase` 테이블 1행과 `ticket` 테이블 N행의 관계를 설명할 수 없다면 모델링 갈래를 먼저 본다.
2. 저장 코드에서 `purchase` 저장과 `ticket` 반복 저장이 같은 서비스 메서드 안에서 하나의 트랜잭션인지 확인한다. 아니면 2번 갈래 신호다.
3. 같은 요청을 새로고침하거나 재전송했을 때 개수가 더 늘어난다면 멱등성 갈래가 우선이다.
4. DB 직접 조회와 화면 결과가 다르면 저장부터 의심하지 말고, "지금 화면이 purchase 1건을 보는가, ticket 목록 전체를 보는가"를 먼저 확인한다.

## 다음 학습

- 부모-자식 저장 구조부터 다시 잡으려면 [lotto 구매 1회/여러 장 티켓 저장 ↔ 부모-자식 테이블 모델링 브릿지](./lotto-purchase-ticket-parent-child-modeling-bridge.md)
- 저장 원자 단위를 어디에 둘지 보려면 [lotto 구매 1회/여러 장 티켓 저장 ↔ Spring `@Transactional` 경계 브릿지](../spring/lotto-purchase-ticket-transaction-boundary-bridge.md)
- 중복 티켓 증가가 재전송 문제인지 확인하려면 [lotto 구매 재시도/중복 티켓 저장 ↔ 멱등성 키와 UNIQUE 브릿지](./lotto-purchase-duplicate-submit-idempotency-bridge.md)
- 조회가 어떤 구매 단위를 기준으로 삼아야 하는지 정리하려면 [lotto 구매 1회 재조회 ↔ PurchaseRepository 경계 브릿지](../software-engineering/lotto-purchase-history-repository-boundary-bridge.md)

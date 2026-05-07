---
schema_version: 3
title: SQL Join Cardinality Mission Drill
concept_id: database/sql-join-cardinality-mission-drill
canonical: false
category: database
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- sql-join-cardinality
- row-increase
- group-by
- mission-drill
aliases:
- sql join cardinality mission drill
- JOIN row 증가 드릴
- roomescape reservation join drill
- shopping cart order item join drill
- 1:N join group by practice
symptoms:
- JOIN 뒤 row가 늘어나는 이유를 DISTINCT로만 덮으려 한다
- roomescape 예약 목록이나 shopping-cart 주문 목록에서 1:N 관계를 읽지 못한다
- GROUP BY가 정렬인지 묶기인지 헷갈린다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- database/sql-join-basics
- database/sql-relational-modeling-basics
next_docs:
- database/join-row-increase-distinct-symptom-card
- database/sql-aggregate-groupby-basics
- spring/roomescape-admin-reservation-list-fetch-plan-bridge
linked_paths:
- contents/database/sql-join-basics.md
- contents/database/sql-reading-relational-modeling-primer.md
- contents/database/join-row-increase-distinct-symptom-card.md
- contents/database/sql-aggregate-groupby-basics.md
- contents/spring/roomescape-admin-reservation-list-fetch-plan-bridge.md
- contents/database/shopping-cart-order-item-snapshot-table-bridge.md
confusable_with:
- database/sql-join-basics
- database/join-row-increase-distinct-symptom-card
- database/sql-relational-modeling-basics
forbidden_neighbors:
- contents/database/index-basics.md
expected_queries:
- JOIN 뒤 row가 늘어나는 문제를 roomescape 예제로 연습하고 싶어
- shopping-cart order item 1:N join과 group by를 드릴로 풀어줘
- DISTINCT로 중복을 덮기 전에 cardinality를 어떻게 봐?
- SQL join cardinality를 미션 문맥으로 문제 내줘
contextual_chunk_prefix: |
  이 문서는 SQL join cardinality mission drill이다. roomescape reservation
  list, shopping-cart order item, 1:N join, row increase, DISTINCT misuse,
  GROUP BY summary 같은 질문을 DB 모델링 문제로 매핑한다.
---
# SQL Join Cardinality Mission Drill

> 한 줄 요약: JOIN 뒤 row가 늘면 먼저 관계 cardinality를 보고, DISTINCT는 마지막 증상 완화로만 의심한다.

**난이도: Beginner**

## 문제 1

상황:

```text
reservation과 reservation_time은 N:1인데 JOIN 뒤 reservation row 수는 그대로다.
```

답:

정상적이다. 여러 reservation이 하나의 time을 가리킬 수 있지만, reservation에서 time으로 붙이면 reservation 기준 row 수가 보통 늘지 않는다.

## 문제 2

상황:

```text
orders와 order_item을 JOIN했더니 주문 1건이 상품 수만큼 여러 줄로 보인다.
```

답:

1:N join의 정상 결과다. 주문 단위로 다시 보고 싶으면 `GROUP BY orders.id`나 order aggregate 조립 경계를 둬야 한다.

## 문제 3

상황:

```text
중복처럼 보이니 SELECT DISTINCT를 붙였더니 화면은 맞아 보인다.
```

답:

위험하다. 왜 row가 늘었는지 cardinality를 먼저 설명해야 한다. DISTINCT가 필요한 조회인지, 모델링/조인 조건이 틀린 것인지 구분해야 한다.

## 빠른 체크

| 신호 | 먼저 볼 것 |
|---|---|
| 부모 row가 자식 수만큼 반복 | 1:N cardinality |
| 집계 결과가 필요 | GROUP BY |
| 중복 제거만 붙임 | 조인 조건/관계 재검토 |
| 목록 DTO가 연관 이름을 꺼냄 | fetch plan / N+1 |

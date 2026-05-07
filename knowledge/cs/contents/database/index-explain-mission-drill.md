---
schema_version: 3
title: Index EXPLAIN Mission Drill
concept_id: database/index-explain-mission-drill
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
- index
- explain
- query-tuning
- mission-drill
aliases:
- index explain mission drill
- 인덱스 실행계획 드릴
- roomescape list query index drill
- shopping-cart order query index drill
- key null rows filesort practice
symptoms:
- WHERE 조건이 있는데도 조회가 느리고 full scan을 의심하지 못한다
- 인덱스를 추가했지만 EXPLAIN으로 실제 사용 여부를 확인하지 않는다
- rows, key, Extra를 어떻게 첫 판단에 쓰는지 모른다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- database/index-basics
- database/index-and-explain
next_docs:
- database/query-tuning-checklist
- database/covering-index-composite-ordering
- spring/roomescape-admin-reservation-list-fetch-plan-bridge
linked_paths:
- contents/database/index-basics.md
- contents/database/index-and-explain.md
- contents/database/query-tuning-checklist.md
- contents/database/covering-index-composite-ordering.md
- contents/database/mysql-explain-key-null-beginner-card.md
- contents/spring/roomescape-admin-reservation-list-fetch-plan-bridge.md
confusable_with:
- database/index-basics
- database/index-and-explain
- database/query-tuning-checklist
forbidden_neighbors:
- contents/database/sql-join-basics.md
expected_queries:
- EXPLAIN key null rows filesort를 미션 쿼리로 연습하고 싶어
- roomescape 목록 조회 인덱스를 어떻게 확인하는지 드릴로 풀어줘
- shopping-cart 주문 목록 where order by에 어떤 index가 필요한지 문제로 봐줘
- 인덱스를 만들었는데 실제 탔는지 판단하는 drill을 줘
contextual_chunk_prefix: |
  이 문서는 index EXPLAIN mission drill이다. roomescape admin list,
  shopping-cart order list, WHERE, ORDER BY, key NULL, rows high, Using
  filesort, covering index 같은 질문을 실행계획 판별 문제로 매핑한다.
---
# Index EXPLAIN Mission Drill

> 한 줄 요약: 인덱스는 만들었다고 끝이 아니라, 실행 계획에서 실제로 선택됐는지 확인해야 한다.

**난이도: Beginner**

## 문제 1

상황:

```text
reservation 목록을 date로 필터링하는데 EXPLAIN key가 NULL이다.
```

답:

인덱스를 타지 않은 후보가 맞다. `WHERE date = ?` 조건에 맞는 index가 있는지, 타입/함수/조건 모양 때문에 못 쓰는지 본다.

## 문제 2

상황:

```text
orders를 member_id로 찾고 created_at desc로 정렬한다.
```

답:

복합 인덱스 후보가 된다. `member_id, created_at` 순서가 조회 조건과 정렬을 같이 만족하는지 EXPLAIN으로 확인한다.

## 문제 3

상황:

```text
인덱스를 추가했더니 write 성능이 조금 느려졌다.
```

답:

정상적인 tradeoff일 수 있다. 인덱스는 읽기 lookup path를 만들지만 insert/update/delete 때 함께 갱신해야 한다.

## 빠른 체크

| EXPLAIN 신호 | 첫 판단 |
|---|---|
| `key = NULL` | index not chosen |
| `rows`가 매우 큼 | scan 범위 큼 |
| `Using filesort` | 정렬 비용 확인 |
| covering 가능 | 필요한 column이 index에 있는지 확인 |

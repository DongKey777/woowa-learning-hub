---
schema_version: 3
title: Backend SQL Log Statistics Drill
concept_id: software-engineering/backend-sql-log-statistics-drill
canonical: false
category: software-engineering
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/backend
review_feedback_tags:
- backend
- sql-log
- performance-test
- n-plus-one
aliases:
- backend SQL log statistics drill
- SQL log vs Hibernate statistics drill
- N+1 verification drill
- query count assertion backend drill
- SQL 로그 통계 검증 드릴
symptoms:
- 콘솔 SQL 로그만 보고 N+1이 고쳐졌다고 판단한다
- 테스트에서 query count를 어디까지 고정해야 하는지 모르겠다
- fetch join, batch size, projection 중 어떤 증거를 남길지 헷갈린다
intents:
- drill
- troubleshooting
- design
prerequisites:
- software-engineering/sql-log-vs-hibernate-statistics
- software-engineering/test-strategy-basics
next_docs:
- database/index-basics
- software-engineering/query-model-separation-read-heavy
- software-engineering/same-db-query-repository-vs-separate-read-store
linked_paths:
- contents/software-engineering/sql-log-vs-hibernate-statistics-verification-boundaries.md
- contents/software-engineering/test-strategy-basics.md
- contents/database/index-basics.md
- contents/software-engineering/query-model-separation-read-heavy-apis.md
- contents/software-engineering/same-db-query-repository-vs-separate-read-store.md
- contents/spring/shopping-cart-order-read-fetch-plan-bridge.md
confusable_with:
- software-engineering/sql-log-vs-hibernate-statistics
- database/index-basics
- software-engineering/query-model-separation-read-heavy
forbidden_neighbors:
- contents/database/sql-join-cardinality-mission-drill.md
expected_queries:
- backend SQL 로그와 Hibernate statistics로 N+1 검증하는 문제를 풀고 싶어
- 콘솔 SQL이 줄어든 것만으로 성능 개선을 증명해도 돼?
- query count assertion을 테스트에 어디까지 고정해야 하는지 드릴해줘
- fetch join batch size projection 중 어떤 증거를 남길지 판단해줘
- backend 조회 성능 리뷰를 SQL log statistics drill로 연습하고 싶어
contextual_chunk_prefix: |
  이 문서는 backend SQL log statistics drill이다. console SQL log, Hibernate
  statistics, query count assertion, N+1, fetch join, batch size, projection,
  stable performance evidence 같은 미션 리뷰 문장을 검증 경계 문제로
  매핑한다.
---
# Backend SQL Log Statistics Drill

> 한 줄 요약: SQL 로그는 원인을 찾는 관찰 도구이고, statistics/query count는 회귀를 막는 검증 도구다.

**난이도: Beginner**

## 문제 1

상황:

```text
주문 목록 API에서 N+1을 고쳤다고 말하면서 콘솔 SQL 로그 캡처만 PR 설명에 붙였다.
```

답:

관찰 증거로는 도움이 되지만 회귀 방지로는 약하다. 같은 fixture에서 query count나 collection fetch 전략을 테스트로 확인해야 다음 refactor 때 다시 늘어나는 것을 잡을 수 있다.

## 문제 2

상황:

```text
테스트가 "정확히 2 queries"를 항상 강제한다.
검색 조건이 늘면서 projection 쿼리와 count 쿼리 구성이 바뀔 가능성이 있다.
```

답:

너무 세게 고정했을 수 있다. 핵심이 N+1 방지라면 `items 수가 늘어도 query count가 선형 증가하지 않는다`를 확인하는 편이 더 안정적이다.
정확한 숫자를 고정할 때는 API 계약처럼 중요한 조회 경로인지 이유를 남긴다.

## 문제 3

상황:

```text
fetch join으로 N+1은 줄었지만 paging 결과가 흔들리고 중복 row가 생긴다.
```

답:

fetch join만 정답으로 보지 않는다. projection query, batch size, 별도 detail query, query model 분리를 같이 비교해야 한다.
검증은 SQL 수뿐 아니라 결과 cardinality와 page boundary까지 포함한다.

## 빠른 체크

| 증거 | 역할 |
|---|---|
| console SQL log | 어떤 쿼리가 나가는지 빠르게 관찰 |
| Hibernate statistics | session/query/fetch count를 정량화 |
| query count assertion | N+1 회귀를 테스트로 차단 |
| EXPLAIN / index 확인 | DB가 어떤 경로로 읽는지 확인 |

## 한 줄 정리

backend 조회 성능 리뷰는 `로그로 관찰 -> statistics로 수량화 -> 테스트로 회귀 방지 -> index/query model로 설계 판단` 순서로 닫는다.

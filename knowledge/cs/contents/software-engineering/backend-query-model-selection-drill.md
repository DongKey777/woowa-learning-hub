---
schema_version: 3
title: Backend Query Model Selection Drill
concept_id: software-engineering/backend-query-model-selection-drill
canonical: false
category: software-engineering
difficulty: intermediate
doc_role: drill
level: intermediate
language: mixed
source_priority: 74
mission_ids:
- missions/backend
review_feedback_tags:
- backend
- query-model
- read-store
- cqrs-lite
aliases:
- backend query model selection drill
- backend read model drill
- query repository projection read store exercise
- 같은 DB 조회 모델 선택 드릴
- CQRS lite backend drill
symptoms:
- 관리자 조회 쿼리가 길어졌다는 이유만으로 read store 분리를 고민한다
- query repository, projection table, separate read store의 순서를 설명하지 못한다
- 읽기 지연과 재빌드 책임을 고려하지 않고 CQRS라는 이름만 붙인다
intents:
- drill
- design
- troubleshooting
prerequisites:
- software-engineering/same-db-query-repository-vs-separate-read-store
- software-engineering/query-model-separation-read-heavy
next_docs:
- software-engineering/event-sourcing-cqrs
- database/index-basics
- database/sql-join-basics
linked_paths:
- contents/software-engineering/same-db-query-repository-vs-separate-read-store.md
- contents/software-engineering/query-model-separation-read-heavy-apis.md
- contents/software-engineering/event-sourcing-cqrs-adoption-criteria.md
- contents/database/index-basics.md
- contents/database/sql-join-basics.md
- contents/system-design/read-after-write-consistency-basics.md
confusable_with:
- software-engineering/same-db-query-repository-vs-separate-read-store
- software-engineering/query-model-separation-read-heavy
- software-engineering/event-sourcing-cqrs
forbidden_neighbors:
- contents/system-design/search-system-design.md
expected_queries:
- backend 관리자 검색에서 query repository projection read store를 어떻게 골라?
- JPQL이 길어진 backend 조회를 별도 read DB로 분리해야 하는지 드릴해줘
- CQRS lite 선택 문제를 미션 장면으로 연습하고 싶어
- 같은 DB query repository와 separate read store 판단 기준을 문제로 줘
- backend read model 분리 전에 index와 join을 먼저 봐야 하는 경우를 알려줘
contextual_chunk_prefix: |
  이 문서는 backend query model selection drill이다. long JPQL, admin search,
  same DB query repository, projection table, separate read store, CQRS lite,
  read-after-write lag, rebuild responsibility 같은 미션 질문을 선택 문제로
  매핑한다.
---
# Backend Query Model Selection Drill

> 한 줄 요약: 조회가 길어졌다는 이유만으로 read store를 나누지 말고, 경로 분리와 데이터 모양 분리와 저장소 분리를 순서대로 판단한다.

**난이도: Intermediate**

## 문제 1

상황:

```text
관리자 주문 검색에 회원명, 주문 상태, 기간 조건이 붙으면서 JPQL이 길어졌다.
DB 부하 지표는 아직 없고, 방금 저장한 주문은 목록에서 바로 보여야 한다.
```

답:

같은 DB query repository가 먼저다. 지금 문제는 저장소 분리보다 write model에 목록 조회 책임이 섞이는 것이다.
read-after-write 기대가 강하므로 별도 read store lag를 먼저 만들 필요가 없다.

## 문제 2

상황:

```text
대시보드가 매번 같은 join과 group by를 반복한다.
결과는 몇 초 늦어도 되고, 운영팀은 저장소를 늘리고 싶지 않다.
```

답:

같은 DB projection table이나 view를 후보로 본다. 저장소를 늘리지 않고도 읽기용 모양을 고정할 수 있기 때문이다.
이때 projection 갱신 시점과 재계산 방법을 테스트/운영 문서에 같이 남겨야 한다.

## 문제 3

상황:

```text
검색 조건이 full text와 복잡한 ranking을 요구하고, 쓰기 DB 인덱스와 검색 인덱스 요구가 계속 충돌한다.
몇 초 지연은 허용되고 rebuild job을 운영할 수 있다.
```

답:

separate read store가 후보가 된다. 하지만 이 선택은 query repository보다 멋져서가 아니라, lag, rebuild, dual schema 비용을 감당할 근거가 있을 때만 맞다.

## 빠른 체크

| 신호 | 먼저 고를 단계 |
|---|---|
| 조회 코드가 write repository를 더럽힌다 | same DB query repository |
| 같은 aggregate/join 결과를 반복 계산한다 | same DB projection/view |
| 검색 저장 형식과 write 저장 형식이 충돌한다 | separate read store |
| 방금 쓴 데이터가 바로 보여야 한다 | read-after-write 경로 먼저 확인 |

## 한 줄 정리

backend 조회 모델은 `query repository -> projection/view -> separate read store` 순서로 올라가며, 각 단계마다 lag와 rebuild 책임이 실제로 필요한지 확인해야 한다.

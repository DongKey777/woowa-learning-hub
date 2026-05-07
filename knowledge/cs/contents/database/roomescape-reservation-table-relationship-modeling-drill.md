---
schema_version: 3
title: Roomescape Reservation Table Relationship Modeling Drill
concept_id: database/roomescape-reservation-table-relationship-modeling-drill
canonical: false
category: database
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
review_feedback_tags:
- roomescape
- relational-modeling
- reservation-table
- foreign-key
aliases:
- roomescape reservation modeling drill
- 예약 테이블 관계 모델링 드릴
- roomescape table relationship
- member reservation time FK
- reservation relational modeling
symptoms:
- Reservation, Member, Time 관계를 객체 참조만 보고 table 관계로 옮기지 못한다
- FK가 필요한 관계와 값 column으로 충분한 관계를 구분하지 못한다
- 예약 목록 조회 요구 때문에 처음부터 모든 테이블을 한 객체처럼 합치려 한다
intents:
- drill
- mission_bridge
- design
prerequisites:
- database/sql-relational-modeling-basics
- database/database-first-step-bridge
next_docs:
- database/transaction-basics
- database/index-basics
- software-engineering/roomescape-dao-vs-repository-bridge
linked_paths:
- contents/database/sql-reading-relational-modeling-primer.md
- contents/database/database-first-step-bridge.md
- contents/database/transaction-basics.md
- contents/database/index-basics.md
- contents/software-engineering/roomescape-dao-vs-repository-bridge.md
- contents/spring/roomescape-admin-reservation-list-fetch-plan-bridge.md
confusable_with:
- database/database-first-step-bridge
- software-engineering/roomescape-dao-vs-repository-bridge
- spring/roomescape-admin-reservation-list-fetch-plan-bridge
forbidden_neighbors:
- contents/system-design/newsfeed-system-design.md
expected_queries:
- roomescape Reservation Member Time 테이블 관계를 드릴로 연습하고 싶어
- 예약 도메인을 테이블 FK로 옮길 때 어떤 관계부터 봐야 해?
- 예약 목록 조회 때문에 테이블을 합치면 안 되는 이유를 문제로 풀어줘
- roomescape 미션에서 객체 관계와 DB 관계를 어떻게 나눠?
contextual_chunk_prefix: |
  이 문서는 roomescape 예약 도메인을 table, column, foreign key 관계로
  옮기는 database drill이다. Reservation, Member, Time, FK, 예약 목록 조회,
  table relationship 같은 미션 질문을 relational modeling 연습으로 매핑한다.
---
# Roomescape Reservation Table Relationship Modeling Drill

> 한 줄 요약: 객체 그래프를 그대로 테이블 하나로 합치기보다, "무엇이 독립 식별자를 갖고 반복 참조되는가"를 기준으로 FK 관계를 먼저 잡는다.

**난이도: Beginner**

## 문제 1

```text
Reservation은 member와 time을 가진다. member 이름과 time 문자열을 reservation row에 매번 복사해도 될까?
```

답:

초기에는 동작할 수 있지만, member나 time이 독립적으로 관리된다면 FK로 참조하는 편이 변경과 중복에 안전하다. 다만 주문 snapshot처럼 과거 값을 보존해야 하는 경우는 별도 판단이 필요하다.

## 문제 2

```text
관리자 목록에서 member name, reservation date, time을 한 번에 보여준다.
```

답:

조회 화면이 join을 요구한다고 해서 저장 모델을 합칠 필요는 없다. 저장 모델은 관계를 보존하고, 목록 조회는 query나 fetch plan에서 해결한다.

## 문제 3

```text
같은 date/time에 예약이 중복되면 안 된다.
```

답:

도메인 검증만으로 끝내면 동시 요청에서 뚫릴 수 있다. DB unique constraint나 transaction/isolation 논의로 이어진다.

## 체크리스트

| 질문 | 모델링 힌트 |
|---|---|
| 독립적으로 생성/수정되는가 | 별도 table 후보 |
| 여러 row에서 반복 참조되는가 | FK 후보 |
| 과거 값을 보존해야 하는가 | snapshot column 후보 |
| 조회 편의 때문에 합치고 싶은가 | query model/fetch plan 후보 |

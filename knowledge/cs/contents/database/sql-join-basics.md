---
schema_version: 3
title: SQL Join Basics
concept_id: database/sql-join-basics
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 89
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- sql
- join
- beginner
- left-join
- relational-modeling
aliases:
- SQL join basics
- INNER JOIN
- LEFT JOIN
- RIGHT JOIN
- FULL OUTER JOIN
- Cartesian product
- ON clause join
- join result null
- sql join beginner
- 조인 기초
symptoms:
- JOIN이 두 테이블의 행을 공통 열로 연결한다는 기본 모델이 아직 불명확해
- INNER JOIN과 LEFT JOIN의 포함 범위 차이를 처음 배우고 있어
- ON 조건이 빠져 Cartesian product로 row가 폭증하는 위험을 설명해야 해
intents:
- definition
- drill
- comparison
prerequisites:
- database/sql-relational-modeling-basics
- database/primary-foreign-key-basics
next_docs:
- database/left-join-filter-placement-primer
- database/sql-joins-and-query-order
- database/result-row-explosion-debugging
linked_paths:
- contents/database/sql-joins-and-query-order.md
- contents/database/left-join-filter-placement-primer.md
- contents/database/index-basics.md
- contents/spring/spring-data-jpa-basics.md
confusable_with:
- database/left-join-filter-placement-primer
- database/result-row-explosion-debugging
- database/sql-joins-and-query-order
forbidden_neighbors: []
expected_queries:
- SQL JOIN이 뭐고 INNER JOIN과 LEFT JOIN 차이를 초보자에게 설명해줘
- ON 조건 없이 JOIN하면 Cartesian product로 결과가 폭발하는 이유가 뭐야?
- LEFT JOIN 결과 row 수가 왼쪽 테이블 수보다 많아질 수 있는 이유를 알려줘
- 조인 결과에서 매칭 없는 row가 NULL로 채워지는 것은 어떤 JOIN이야?
- 주문한 적 없는 회원을 찾는 LEFT JOIN 패턴을 쉽게 설명해줘
contextual_chunk_prefix: |
  이 문서는 SQL JOIN basics를 INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL OUTER JOIN, ON clause, Cartesian product 관점으로 설명하는 beginner primer다.
  조인 기초, 두 테이블 합치기, LEFT JOIN NULL, join row explosion 초급 질문이 본 문서에 매핑된다.
---
# SQL 조인 기초 (SQL Join Basics)

> 한 줄 요약: JOIN은 두 테이블의 행을 공통 열로 연결해 하나의 결과 집합으로 합치는 연산이고, INNER·LEFT·RIGHT·FULL 네 종류가 "어떤 행을 포함할 것인가"를 결정한다.

**난이도: 🟢 Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "예약 목록에 member 이름과 theme 이름을 같이 보여주려면 JOIN이 뭔지부터 모르겠어요" | roomescape 관리자 목록, shopping-cart 주문 상세 조회 | 나뉜 테이블을 공통 key로 연결해 결과 row를 만드는 감각을 잡는다 |
| "`INNER JOIN`과 `LEFT JOIN` 포함 범위가 헷갈려요" | 주문 없는 회원, 예약 없는 시간대까지 보여야 하는 조회 | 매칭 없는 row를 버릴지 NULL로 남길지 먼저 정한다 |
| "`ON` 조건 없이 조인했더니 row가 폭증해요" | 목록 조회에서 Cartesian product가 생긴 장면 | join 조건이 어떤 row와 row를 연결하는지 명시한다 |

관련 문서:

- [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
- [LEFT JOIN 필터 위치 입문서](./left-join-filter-placement-primer.md)
- [인덱스 기초](./index-basics.md)
- [database 카테고리 인덱스](./README.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

retrieval-anchor-keywords: sql join basics, inner join 이란, left join 이란, right join 이란, 조인이 뭐예요, on 절 조인, 조인 결과 null, sql join beginner, 두 테이블 합치기, 카테시안 곱 주의, sql join basics basics, sql join basics beginner, sql join basics intro, database basics, beginner database

## 핵심 개념

JOIN은 **두 테이블을 공통 열(보통 외래 키)을 기준으로 연결하여 하나의 결과 집합으로 만드는 SQL 연산**이다.

정규화로 나눠진 테이블들은 데이터를 중복 없이 유지하지만, 실제 조회 시에는 "고객 이름 + 주문 내역"처럼 여러 테이블 정보를 합쳐야 한다. JOIN이 그 역할을 한다.

입문자가 자주 헷갈리는 지점:

- `ON` 절 조건이 없으면 두 테이블의 모든 행이 곱해지는 **카테시안 곱(Cartesian product)**이 발생해 결과가 폭발적으로 늘어난다. 항상 `ON` 조건을 명시한다.
- NULL이 포함된 행은 조인 결과에서 사라지거나 NULL로 채워지는데, 어떤 JOIN 유형인지에 따라 달라진다.

## 한눈에 보기 — 조인 종류

```
member 테이블:   order 테이블:
id | name        id | member_id | item
1  | Alice       1  | 1         | 책
2  | Bob         2  | 1         | 노트
3  | Carol       3  | 99        | 펜 (member 없음)
```

| 조인 종류 | 포함하는 행 | 결과 예시 |
|---|---|---|
| INNER JOIN | 양쪽 모두 매칭되는 행만 | Alice-책, Alice-노트 |
| LEFT JOIN | 왼쪽 테이블 전체 + 오른쪽 매칭 (없으면 NULL) | Alice-책, Alice-노트, Bob-NULL, Carol-NULL |
| RIGHT JOIN | 오른쪽 테이블 전체 + 왼쪽 매칭 (없으면 NULL) | Alice-책, Alice-노트, NULL-펜 |
| FULL OUTER JOIN | 양쪽 모두 + 매칭 없는 행도 NULL로 포함 | Alice-책, Alice-노트, Bob-NULL, NULL-펜 |

## 상세 분해

**INNER JOIN — 교집합**

두 테이블 모두에 값이 있는 행만 반환한다. 가장 흔하게 사용된다.

```sql
SELECT m.name, o.item
FROM member m
INNER JOIN order o ON m.id = o.member_id;
```

**LEFT JOIN — 왼쪽 기준**

왼쪽(FROM) 테이블의 모든 행을 유지한다. 오른쪽에 매칭이 없으면 NULL로 채운다. "주문한 적 없는 회원도 포함하여 조회"할 때 유용하다.

**RIGHT JOIN**

LEFT JOIN의 반대다. 오른쪽 테이블을 기준으로 유지한다. 실무에서는 LEFT JOIN으로 표현하는 경우가 많아 자주 쓰이지 않는다.

**FULL OUTER JOIN**

양쪽 테이블의 모든 행을 포함한다. MySQL은 직접 지원하지 않아 LEFT JOIN과 RIGHT JOIN을 UNION으로 합쳐야 한다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "JOIN이 많으면 느리다" | 인덱스가 잘 설계돼 있으면 JOIN 여러 개도 빠를 수 있다 | 느린 이유를 EXPLAIN으로 확인하고, 원인이 JOIN인지 인덱스 부재인지 구분한다 |
| "LEFT JOIN하면 결과 row가 항상 왼쪽 테이블 수와 같다" | 오른쪽 테이블에 매칭이 여러 개면 왼쪽 row가 여러 번 등장한다 | 1:N 관계에서는 결과 row 수가 N 쪽 기준으로 늘어날 수 있음을 인지한다 |
| "ON 없이 JOIN해도 괜찮다" | 카테시안 곱이 발생해 row가 기하급수적으로 늘어난다 | 항상 `ON` 조건으로 연결 기준을 명시한다 |

## 실무에서 쓰는 모습

**(1) 주문 목록 조회** — 주문 테이블과 회원 테이블을 INNER JOIN해서 주문자 이름과 주문 내역을 한 번에 가져온다.

**(2) 주문 안 한 회원 찾기** — LEFT JOIN 후 오른쪽이 NULL인 row만 필터링하면 "한 번도 주문하지 않은 회원" 목록을 구할 수 있다.

```sql
SELECT m.name
FROM member m
LEFT JOIN order o ON m.id = o.member_id
WHERE o.id IS NULL;
```

**(3) `LEFT JOIN` 조건 위치 주의** — 오른쪽 테이블 조건을 `WHERE`에 두면 `NULL` row가 탈락해 결과가 `INNER JOIN`처럼 좁아질 수 있다. "오른쪽에서 어떤 행을 붙일지"가 목적이면 `ON`에 두는 편이 안전하다.

## 더 깊이 가려면

- `LEFT JOIN`에서 `ON`과 `WHERE`를 어디에 둘지 헷갈리면 → [LEFT JOIN 필터 위치 입문서](./left-join-filter-placement-primer.md)
- 조인 알고리즘(Nested Loop, Hash, Sort-Merge)과 실행 계획에서 조인 비용 읽기 → [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
- 조인 속도에 영향을 주는 인덱스 설계 → [인덱스 기초](./index-basics.md)

cross-category bridge:

- JPA에서 `@ManyToOne`, `@OneToMany`로 연관 관계를 맺고 JPQL의 JOIN FETCH로 조회하는 방법은 spring 카테고리 참고

## 면접/시니어 질문 미리보기

> Q: INNER JOIN과 LEFT JOIN의 차이가 무엇인가요?
> 의도: 포함 범위 차이를 명확히 아는지 확인
> 핵심: INNER JOIN은 양쪽에 매칭이 있는 행만, LEFT JOIN은 왼쪽 테이블의 모든 행을 포함하며 매칭이 없으면 NULL로 채운다.

> Q: LEFT JOIN 결과에서 행 수가 왼쪽 테이블 수보다 많아질 수 있나요?
> 의도: 1:N 관계에서 조인 결과 이해도 확인
> 핵심: 오른쪽 테이블에 매칭 행이 여러 개면 왼쪽 row 하나가 여러 번 복제되어 등장한다.

## 한 줄 정리

JOIN은 공통 열로 두 테이블을 연결하는 연산이고, INNER는 교집합, LEFT는 왼쪽 전체 기준, RIGHT는 오른쪽 전체 기준, FULL OUTER는 합집합으로 포함 범위를 결정한다.

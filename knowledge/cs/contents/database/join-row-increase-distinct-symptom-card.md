---
schema_version: 3
title: JOIN 뒤 row가 늘었을 때 DISTINCT로 덮으면 안 되는 이유 카드
concept_id: database/join-row-increase-distinct-symptom-card
canonical: true
category: database
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 91
mission_ids: []
review_feedback_tags:
- join-row-increase-distinct
- result-row-explosion
- join-cardinality-debug
aliases:
- join duplicates distinct
- join 뒤 row 증가
- join result too many rows
- duplicated rows after join
- distinct 붙이면 되나요
- join row explosion symptom
- group by id로 줄이면 되나요
- sql join beginner distinct
- DISTINCT로 덮지 말기
- join 중복처럼 보여요
symptoms:
- JOIN 뒤 부모 row가 여러 줄로 보이자 바로 DISTINCT나 GROUP BY id로 덮으려 하고 있어
- 정상적인 1:N 펼침과 잘못된 join key, 중복 데이터, 결과 단위 착각을 구분하지 못하고 있어
- 고객 한 줄, 주문 한 건, 최신 주문 한 건 같은 결과 row 단위를 먼저 정하지 않았어
intents:
- troubleshooting
- definition
prerequisites:
- database/sql-join-basics
- database/distinct-vs-group-by-beginner-card
next_docs:
- database/result-row-explosion-debugging
- database/left-join-filter-placement-primer
- database/sql-joins-and-query-order
linked_paths:
- contents/database/result-row-explosion-debugging-checklist.md
- contents/database/sql-join-basics.md
- contents/database/distinct-vs-group-by-beginner-card.md
- contents/database/left-join-filter-placement-primer.md
- contents/database/sql-joins-and-query-order.md
- contents/spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card.md
confusable_with:
- database/result-row-explosion-debugging
- database/distinct-vs-group-by-beginner-card
- database/left-join-filter-placement-primer
forbidden_neighbors: []
expected_queries:
- JOIN 뒤 row가 갑자기 늘었을 때 DISTINCT를 바로 붙이면 왜 위험해?
- 부모 row가 중복처럼 보일 때 정상적인 1:N 펼침인지 잘못된 join key인지 어떻게 구분해?
- 고객별 주문 수가 필요한지 고객 목록이 필요한지 결과 row 단위를 먼저 정해야 하는 이유는 뭐야?
- GROUP BY id로 줄이면 다른 컬럼 의미가 깨질 수 있다는 점을 설명해줘
- join row explosion을 디버깅할 때 어떤 테이블에서 몇 배가 붙는지 어떻게 확인해?
contextual_chunk_prefix: |
  이 문서는 JOIN 뒤 row가 늘었을 때 DISTINCT로 출력만 줄이지 않고 관계 cardinality, 결과 row 단위, join key uniqueness를 먼저 확인하게 하는 beginner symptom router다.
  join duplicates distinct, join row explosion, DISTINCT로 덮지 말기 같은 자연어 증상 질문이 본 문서에 매핑된다.
---
# JOIN 뒤 row가 늘었을 때 DISTINCT로 덮으면 안 되는 이유 카드

> 한 줄 요약: JOIN 뒤 결과가 갑자기 많아졌을 때 `DISTINCT`를 바로 붙이면 증상은 잠깐 가려질 수 있지만, 잘못된 조인 키, 1:N 관계, 결과 단위 착각 같은 원인을 놓치기 쉽다.

**난이도: 🟢 Beginner**

관련 문서:

- [Result-row Explosion Debugging Checklist](./result-row-explosion-debugging-checklist.md)
- [SQL 조인 기초](./sql-join-basics.md)
- [DISTINCT vs GROUP BY 초보자 비교 카드](./distinct-vs-group-by-beginner-card.md)
- [database 카테고리 인덱스](./README.md)
- [Fetch Join vs `@EntityGraph` Mini Card for DTO Reads](../spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card.md)

retrieval-anchor-keywords: join duplicates distinct, distinct로 덮지 말기, join 뒤 row 증가, join result too many rows, duplicated rows after join, 왜 join 결과가 많아져요, distinct 붙이면 되나요, sql join beginner distinct, join row explosion symptom, group by id로 줄이면 되나요, 처음 join 중복처럼 보여요, sql 헷갈려요 distinct join, what is join duplicate, beginner join debugging

## 핵심 개념

초보자에게 가장 중요한 mental model은 이것이다.

- JOIN은 같은 부모 row에 자식 row를 **붙이는** 연산이다.
- 그래서 1:N 관계면 부모가 여러 번 보이는 것이 정상일 수 있다.
- `DISTINCT`는 **보여 주는 결과 row를 줄이는 도구**이지, 왜 row가 늘었는지 설명해 주는 도구는 아니다.

즉 "`중복처럼 보인다`"와 "`진짜 중복 데이터다`"는 같은 말이 아니다. 먼저 "내가 기대한 한 줄의 단위가 무엇이었나"를 정해야 한다.

## 한눈에 보기

| 지금 보인 증상 | `DISTINCT`를 바로 붙이면 왜 위험한가 | 먼저 할 질문 |
|---|---|---|
| 고객 1명이 여러 줄로 보임 | 주문이나 주문상품이 여러 건 붙은 정상 1:N일 수 있다 | "한 줄이 고객 1명이어야 하나, 주문 1건이어야 하나?" |
| LEFT JOIN 뒤 row가 예상보다 많음 | 필터 위치나 자식 다건 매칭을 놓칠 수 있다 | "오른쪽에서 몇 건이 붙을 수 있지?" |
| `GROUP BY id`로 줄이면 한 줄이 됨 | 다른 컬럼 의미가 깨질 수 있다 | "요약 결과가 필요한 건가, 상세 결과가 필요한 건가?" |
| `DISTINCT`를 붙였더니 숫자는 줄어듦 | 조인 키 중복, 빠진 UNIQUE, 잘못된 요구사항이 그대로 남을 수 있다 | "왜 늘었는지 설명할 수 있나?" |

짧게 기억하면 이렇다.

`DISTINCT`가 답인지 보기 전에, 먼저 관계 cardinality와 결과 단위를 본다.

## 예시로 보면 왜 위험한가

아래 쿼리는 고객과 주문을 JOIN한다.

```sql
SELECT c.id, c.name
FROM customer c
JOIN orders o ON o.customer_id = c.id;
```

Alice가 주문을 3번 했다면 결과에 Alice가 3줄 보일 수 있다. 이건 customer row가 "중복 생성"된 것이 아니라, **주문 3건이 붙은 결과**다.

여기서 아래처럼 고치면 일단 한 줄처럼 보인다.

```sql
SELECT DISTINCT c.id, c.name
FROM customer c
JOIN orders o ON o.customer_id = c.id;
```

하지만 질문이 달라진다.

- "주문한 고객 목록만 한 번씩 보고 싶다"면 이 쿼리는 맞을 수 있다.
- "고객별 주문 수를 알고 싶다"면 `DISTINCT`는 답이 아니다.
- "최신 주문 1건만 붙이고 싶다"면 주문을 먼저 1건으로 줄이는 쪽이 맞다.

즉 `DISTINCT`는 "문제가 해결됐다"가 아니라, **요구사항이 실제로 유일한 고객 목록이었는지** 다시 묻게 만든다.

## 먼저 분리해야 하는 세 가지

### 1. 정상적인 1:N인가

부모 1명에 자식 여러 건이 붙는 구조면 row 증가는 자연스럽다.

- 회원 1명 -> 주문 N건
- 주문 1건 -> 주문상품 N건
- 게시글 1개 -> 댓글 N개

이 경우는 JOIN을 잘못한 것이 아니라, 상세 row를 펼쳐 본 것이다.

### 2. 원하는 결과가 상세인가 요약인가

질문이 아래 중 무엇인지 먼저 정한다.

- 주문한 고객 이름 목록이 필요하다
- 고객별 주문 수가 필요하다
- 고객과 최신 주문 1건이 필요하다

셋은 겉으로 비슷해 보여도 SQL 모양이 달라진다.

| 원하는 결과 | 더 맞는 첫 방향 |
|---|---|
| 고객 이름을 한 번씩만 | `DISTINCT` 가능 |
| 고객별 주문 수 | `GROUP BY` + `COUNT` |
| 최신 주문 1건만 붙이기 | 자식 테이블을 먼저 1건으로 줄인 뒤 JOIN |

### 3. 조인 키가 정말 유일한가

`email`, `code`, `name` 같은 일반 컬럼으로 JOIN했다면, 코드 작성자는 1:1이라고 믿어도 실제 데이터는 아닐 수 있다.

이때는 `DISTINCT`보다 먼저 아래를 확인한다.

- PK/FK로 JOIN했나
- `UNIQUE` 제약이 실제로 있나
- 이미 중복 데이터가 들어간 적은 없나

## 흔한 오해와 함정

| 자주 하는 말 | 왜 위험한가 | 더 안전한 첫 대응 |
|---|---|---|
| "`DISTINCT` 붙였더니 맞는 것 같아요" | 출력만 줄었을 뿐 원인은 그대로일 수 있다 | 어떤 JOIN에서 몇 배가 붙는지 먼저 센다 |
| "`GROUP BY id`면 결국 같은 거죠?" | MySQL 설정에 따라 비결정적 컬럼을 묵인할 수 있고, PostgreSQL은 아예 거부한다 | 결과 한 줄의 단위를 먼저 말로 정한다 |
| "부모 row가 반복되니 DB가 중복을 만들었다" | 대부분은 자식 row가 여러 건 붙은 정상 결과다 | 1:N인지부터 확인한다 |
| "`DISTINCT`는 성능만 느릴 뿐 의미는 안전하다" | 의미 자체가 요구사항을 바꿀 수 있다 | 진짜로 "유일한 목록"이 필요한지 먼저 확인한다 |

위 차이는 MySQL과 PostgreSQL 모두에서 **논리적으로는 같다**. 다만 실행 계획과 비용은 엔진, 버전, 인덱스 상태에 따라 달라질 수 있으니 성능 판단은 `EXPLAIN`으로 따로 본다.

## 실무에서 더 안전한 첫 대응

1. 시작 테이블 row 수를 먼저 센다.
2. JOIN을 하나씩 붙이며 어디서 row가 늘어나는지 본다.
3. "결과 한 줄"이 무엇인지 문장으로 적는다.
4. 그다음에만 `DISTINCT`, `GROUP BY`, 사전 집계, 서브쿼리 중 하나를 고른다.

아래처럼 대응을 나누면 실수가 줄어든다.

| 상황 | 먼저 검토할 대응 |
|---|---|
| 주문한 고객 목록만 필요 | `SELECT DISTINCT customer_id ...` |
| 고객별 주문 수 필요 | `GROUP BY customer_id` |
| 최신 주문 1건만 붙이기 | 최신 주문만 뽑는 서브쿼리/윈도우 함수 후 JOIN |
| 같은 email이 여러 row라 JOIN이 늘어남 | `UNIQUE` 제약과 데이터 정합성 점검 |

## 더 깊이 가려면

- row가 늘어나는 원인을 단계별로 디버깅하려면 -> [Result-row Explosion Debugging Checklist](./result-row-explosion-debugging-checklist.md)
- JOIN 종류와 1:N mental model을 다시 잡으려면 -> [SQL 조인 기초](./sql-join-basics.md)
- `DISTINCT`와 `GROUP BY`를 언제 나누는지 다시 보려면 -> [DISTINCT vs GROUP BY 초보자 비교 카드](./distinct-vs-group-by-beginner-card.md)
- JPA fetch join 때문에 부모 엔티티가 반복돼 보이는 읽기 문제를 분리하려면 -> [Fetch Join vs `@EntityGraph` Mini Card for DTO Reads](../spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card.md)

## 면접/시니어 질문 미리보기

> Q: JOIN 뒤 row가 많아졌을 때 `DISTINCT`를 먼저 붙이면 왜 위험한가요?
> 의도: 증상 숨기기와 원인 해결을 구분하는지 확인
> 핵심: 1:N 관계, 잘못된 조인 키, 결과 단위 착각을 가린 채 출력만 줄일 수 있기 때문이다.

> Q: `DISTINCT`가 맞는 경우와 아닌 경우를 어떻게 나누나요?
> 의도: 요구사항 중심으로 SQL을 설명할 수 있는지 확인
> 핵심: 유일한 값 목록이 목적이면 가능하지만, 요약 수치나 최신 1건 같은 질문이면 다른 형태가 더 맞다.

## 한 줄 정리

JOIN 뒤 row가 늘었을 때 `DISTINCT`는 정답일 수도 있지만, 그 전에 "왜 여러 줄이 붙었는지"와 "내가 원하는 한 줄이 무엇인지"를 먼저 설명하지 못하면 거의 항상 너무 이른 처방이다.

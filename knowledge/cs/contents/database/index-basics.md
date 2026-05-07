---
schema_version: 3
title: 인덱스 기초
concept_id: database/index-basics
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 93
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- index-as-lookup-path
- explain-before-index-guess
- read-fast-write-cost-tradeoff
aliases:
- index basics
- db index basics
- b-tree index beginner
- index 뭐예요
- db index가 왜 필요해요
- where 조건 하나인데 왜 느려요
- full scan 왜 나와요
- explain 전에 index basics
- key null explain
- using filesort beginner
- rows가 너무 커 보여요
- clustered secondary covering index
symptoms:
- WHERE 조건 하나인데 조회가 느린 이유를 모르겠어
- 인덱스를 만들었는데 실제로 DB가 탔는지 확인하는 법이 헷갈려
- EXPLAIN에서 key가 NULL이고 rows가 커 보여서 어디부터 봐야 할지 모르겠어
intents:
- definition
- troubleshooting
prerequisites:
- database/sql-relational-modeling-basics
next_docs:
- database/index-and-explain
- database/covering-index-composite-ordering
- database/mysql-postgresql-index-storage-bridge
- database/query-tuning-checklist
- spring/spring-data-jpa-basics
linked_paths:
- contents/database/index-and-explain.md
- contents/database/mysql-postgresql-index-storage-bridge.md
- contents/database/covering-index-composite-ordering.md
- contents/database/sql-joins-and-query-order.md
- contents/database/query-tuning-checklist.md
- contents/database/index-condition-pushdown-filesort-temporary-table.md
- contents/spring/spring-data-jpa-basics.md
confusable_with:
- database/index-and-explain
- database/covering-index-composite-ordering
- database/query-tuning-checklist
forbidden_neighbors: []
expected_queries:
- DB index가 왜 필요한지 B-Tree와 full scan 기준으로 설명해줘
- WHERE 조건 하나인데 왜 느린지 index 관점에서 처음부터 보고 싶어
- EXPLAIN에서 key NULL, rows 큼, Using filesort가 보이면 무엇을 봐야 해?
- clustered index와 secondary index와 covering index를 초보자 기준으로 구분해줘
- 인덱스는 읽기를 빠르게 하지만 write 비용도 늘어난다는 말이 무슨 뜻이야?
contextual_chunk_prefix: |
  이 문서는 database index를 테이블에서 원하는 row를 빨리 찾기 위한 lookup path로 설명하고, B-Tree, clustered index, secondary index, covering index, composite index, EXPLAIN key rows Extra를 처음 연결하는 beginner primer다.
  WHERE 조건 하나인데 느림, full scan, key null, using filesort, rows too high, index를 만들었는데 실제로 탔는지 확인하는 자연어 질문이 본 문서에 매핑된다.
---
# 인덱스 기초 (Index Basics)

> 한 줄 요약: 인덱스는 "찾는 길을 미리 정리한 목록"이고, `EXPLAIN`은 DB가 실제로 그 길을 탔는지 확인하는 첫 도구다.

**난이도: 🟢 Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "`WHERE` 조건 하나인데 조회가 왜 느린지 모르겠어요" | 예약 목록, 상품 검색, 주문 조회 API가 느린 장면 | index를 테이블 전체 scan을 줄이는 lookup path로 본다 |
| "인덱스를 만들었는데 실제로 탔는지 확인하는 법을 모르겠어요" | JPA/SQL 성능 리뷰에서 EXPLAIN을 처음 보는 단계 | `EXPLAIN`의 `key`, `rows`, `Extra`로 실제 선택 경로를 확인한다 |
| "`Using filesort`, `key = NULL`, rows 큰 값이 보여요" | 정렬/필터 조건이 붙은 목록 조회 튜닝 | 인덱스 부재, 조건식 모양, 정렬 경로를 먼저 분리한다 |

관련 문서:

- [database 카테고리 인덱스](./README.md)
- [인덱스와 실행 계획](./index-and-explain.md)
- [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md)
- [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
- [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

retrieval-anchor-keywords: index basics, b-tree index beginner, clustered vs secondary index, covering index beginner, 왜 인덱스 안 타요, index 뭐예요, db index가 왜 필요해요, where 조건 하나인데 왜 느려요, full scan 이 왜 나와요, explain 전에 index basics, key = null 이 보여요, using filesort 가 보여요, rows가 너무 커 보여요, db index 처음, what is index

## 핵심 개념

인덱스는 **테이블에서 원하는 row를 빨리 찾기 위한 추가 자료구조**다.  
책 뒤의 찾아보기처럼 "어떤 값이 어디 있는지"를 미리 정리해 둔다고 보면 된다.

이 문서가 retrieval에서 먼저 잡아야 하는 beginner query shape도 분명하다.

- `"DB 인덱스가 왜 필요해요?"`
- `"WHERE 조건 하나인데 왜 느려요?"`
- `"full scan이 왜 나와요?"`
- `"EXPLAIN 보기 전에 인덱스부터 다시 보고 싶어요"`

입문자가 처음 헷갈리는 지점은 보통 두 가지다.

- 인덱스는 읽기를 빠르게 하지만, 쓰기 때도 같이 갱신해야 해서 공짜가 아니다.
- 인덱스를 만들었다고 끝이 아니라, DB가 실제로 그 인덱스를 썼는지는 `EXPLAIN`으로 확인해야 한다.

즉 이 문서의 큰 그림은 "`인덱스가 뭔지`"와 "`실행 계획에서 그 인덱스를 실제로 탔는지`"를 입문 눈높이에서 같이 잡는 것이다.
처음에는 `optimizer trace`, histogram, invisible index, plan stability처럼 운영 성격이 강한 가지를 본문에서 늘리지 않고 follow-up 링크로 넘긴다.

## 한눈에 보기

| 질문 | 첫 답 |
| --- | --- |
| 인덱스가 뭐예요? | 테이블 전체를 훑지 않도록 미리 정렬된 찾기 경로다 |
| B-Tree는 뭐예요? | 대부분의 기본 인덱스가 쓰는 정렬/탐색 구조다 |
| clustered index는 뭐예요? | MySQL InnoDB에서 primary key 순서 자체가 테이블 저장 순서에 가까운 구조다 |
| secondary index는 뭐예요? | 본문과 별도로 만든 보조 찾기 경로다 |
| covering index는 뭐예요? | 쿼리에 필요한 컬럼을 인덱스만으로 해결하는 상태다 |
| `EXPLAIN`은 왜 봐요? | DB가 full scan, index scan, filesort 중 어떤 길을 고르는지 확인하려고 본다 |

```text
느린 조회를 볼 때 첫 순서
1. WHERE / ORDER BY 모양 확인
2. EXPLAIN 확인
3. key, rows, Extra 읽기
4. 인덱스 자체가 없는지 / 있는데도 안 타는지 분리
```

## 처음 많이 보이는 증상 말

README와 다음 primer에서 같은 문장으로 찾을 수 있게, 처음에는 아래 증상 표현 그대로 떠올리면 된다.

| 지금 드는 말 | 이 문서에서 먼저 볼 것 | 다음 문서 |
| --- | --- | --- |
| "`WHERE` 조건 하나인데 왜 느리죠?" | 인덱스가 찾는 길이라는 감각부터 다시 잡는다 | 필요하면 [인덱스와 실행 계획](./index-and-explain.md) |
| "`key = NULL`이 보여요" | 인덱스가 없거나 조건식 모양이 안 맞는지 먼저 의심한다 | [인덱스와 실행 계획](./index-and-explain.md) |
| "`Using filesort`가 보여요" | 찾는 길과 정렬 길이 따로 노는지 본다 | [인덱스와 실행 계획](./index-and-explain.md) |
| "`rows가 너무 커 보여요`" | 읽는 양이 왜 큰지 `WHERE`, `ORDER BY`, 조회 컬럼을 같이 본다 | [인덱스와 실행 계획](./index-and-explain.md) |

## 상세 분해

### 1. B-Tree 인덱스

실무에서 "인덱스"라고 하면 대부분 먼저 **B-Tree 계열 인덱스**를 떠올리면 된다.

- 값이 정렬된 상태로 유지된다
- `=`, `>`, `<`, `BETWEEN`, `ORDER BY` 같은 패턴에 잘 맞는다
- "어디쯤 있는지"를 단계적으로 좁혀 가며 찾는다

그래서 이메일 exact match, 최근 주문 range 조회, 날짜 정렬 같은 초급 쿼리 대부분은 B-Tree 감각으로 설명할 수 있다.

### 2. clustered index와 secondary index

이 부분은 **MySQL InnoDB 기준의 첫 감각**만 잡으면 충분하다.

- clustered index: primary key leaf에 row 본문이 함께 있다
- secondary index: 보조 인덱스 leaf에는 보통 secondary key와 primary key가 들어 있고, 필요하면 다시 본문으로 내려간다

즉 MySQL에서는 secondary index를 타더라도, `SELECT *`처럼 컬럼이 많으면 **한 번 더 primary key 쪽으로 찾아가는 비용**이 남을 수 있다.
엔진별 저장 구조 차이를 여기서 끝까지 파기보다, 초보자는 아래 두 줄만 기억하면 된다.

- primary key 인덱스와 보조 인덱스는 역할이 다를 수 있다.
- 인덱스를 탔어도 필요한 컬럼이 많으면 추가 읽기가 생길 수 있다.

PostgreSQL과 MySQL의 저장 구조 차이를 따로 보고 싶다면 [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md)로 넘어가면 된다.

### 3. covering index

커버링 인덱스는 **쿼리에 필요한 컬럼을 인덱스만으로 다 읽을 수 있는 상태**다.

예를 들어 아래 쿼리를 보자.

```sql
SELECT member_id, status, created_at
FROM orders
WHERE member_id = 10
ORDER BY created_at DESC
LIMIT 20;
```

`(member_id, created_at, status)` 같은 인덱스가 있으면, DB가 인덱스만 읽고 결과를 만들 가능성이 커진다.

핵심은 "인덱스를 탔다"보다 "테이블 본문까지 다시 가지 않아도 되는가"다.
다만 컬럼을 너무 많이 넣으면 인덱스가 비대해지고 쓰기 비용도 커진다.

### 4. 복합 인덱스와 왼쪽부터 읽는 감각

복합 인덱스는 여러 컬럼을 묶은 인덱스다.

```sql
INDEX (member_id, status, created_at)
```

이런 인덱스는 보통 아래처럼 **앞쪽 컬럼부터 맞는 조건**에서 강하다.

- `member_id = ?`
- `member_id = ? AND status = ?`
- `member_id = ? AND status = ? ORDER BY created_at`

반대로 `status = ?`만 따로 찾으면 기대만큼 못 쓸 수 있다.  
입문자는 이걸 "컬럼을 많이 넣을수록 좋다"가 아니라, "**자주 같이 쓰는 조건 순서**를 맞춘다"로 기억하는 편이 안전하다.

## EXPLAIN 처음 읽는 순서

`EXPLAIN`은 **DB가 이 SQL을 어떤 경로로 실행하려 하는지 보여 주는 표**다.

입문 1회차에서는 "`왜 안 타요?`", "`key = NULL`이 뭐예요?`", "`Using filesort`가 왜 보여요?`" 정도만 풀리면 충분하다. 비용 모델, 통계 오차, optimizer switch는 이 문서의 바깥 단계다.

처음에는 아래 네 칸만 봐도 충분하다.

| 칸 | 초보자 해석 |
| --- | --- |
| `key` | 실제로 선택한 인덱스가 있는가 |
| `rows` | 얼마나 많이 읽을 것 같다고 보는가 |
| `Extra` | `Using index`, `Using filesort` 같은 추가 힌트가 있는가 |
| `type` | 아주 넓게 읽는지, 좁혀서 읽는지 |

읽는 순서는 보통 이렇게 잡으면 된다.

1. `key`가 `NULL`인가 본다.
2. `rows`가 과하게 큰가 본다.
3. `Extra`에 `Using filesort`, `Using temporary`, `Using index`가 있는지 본다.
4. 마지막으로 `type`을 보고 full scan에 가까운지 확인한다.

예를 들어:

```sql
EXPLAIN
SELECT *
FROM orders
WHERE member_id = 10
ORDER BY created_at DESC
LIMIT 20;
```

- `key = NULL`이면 인덱스 설계나 조건식 모양부터 의심한다
- `key`는 있는데 `Using filesort`가 있으면 정렬 순서와 복합 인덱스를 본다
- `Using index`가 있으면 커버링 가능성을 떠올린다

`EXPLAIN`은 정답지가 아니라 출발점이다.
초급 단계에서는 `key -> rows -> Extra -> type` 네 칸만 읽어도 "왜 느린지"를 감으로 말하는 실수는 크게 줄어든다.
`Using filesort` 내부 구현, histogram, optimizer switch까지 바로 내려가기보다, 먼저 "인덱스가 없나 / 있는데도 정렬이 안 맞나"를 분리하는 데 집중하면 된다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 헷갈리나 | 더 안전한 첫 판단 |
| --- | --- | --- |
| "인덱스 달았으니 끝" | DB가 다른 경로를 고를 수 있다 | `EXPLAIN`으로 실제 plan을 본다 |
| "primary key 말고 만든 인덱스도 다 똑같다" | secondary index는 본문 재조회 비용이 남을 수 있다 | clustered/secondary 역할을 분리해 본다 |
| "`SELECT *`여도 인덱스만 타면 빠르다" | 필요한 컬럼이 많으면 커버링이 깨진다 | 필요한 컬럼만 조회할 수 있는지 본다 |
| "`Using filesort`면 무조건 인덱스가 없다" | 인덱스는 있어도 정렬 순서가 안 맞을 수 있다 | `ORDER BY`와 복합 인덱스 순서를 같이 본다 |
| "함수만 써도 인덱스는 알아서 탄다" | `LOWER(name)`, `%abc` 같은 조건은 일반 인덱스를 깨기 쉽다 | 조건식 모양을 먼저 단순화한다 |

처음에는 "DB가 왜 이런 plan을 골랐지?"를 깊게 파기보다, 아래 두 갈래만 먼저 고르면 충분하다.

- 인덱스 자체가 없는가
- 인덱스는 있는데 `WHERE`/`ORDER BY`/조회 컬럼 모양이 안 맞는가

초급에서 가장 흔한 실수는 "인덱스 유무"만 보고 끝내는 것이다.  
실제로는 **조건식 모양, 컬럼 순서, 조회 컬럼 수, 정렬 축**이 같이 맞아야 plan이 좋아진다.

## 실무에서 쓰는 모습

### 예시 1. 로그인용 이메일 조회

```sql
SELECT id, email, password
FROM member
WHERE email = 'alice@example.com';
```

이 쿼리는 `email` 인덱스가 없으면 전체 회원 row를 훑기 쉽다.  
초급에서는 "exact match 검색에는 B-Tree 인덱스가 잘 맞는다"는 감각부터 잡으면 된다.

### 예시 2. 최근 주문 목록

```sql
SELECT member_id, status, created_at
FROM orders
WHERE member_id = 10
ORDER BY created_at DESC
LIMIT 20;
```

이 경우는 단순히 `member_id` 인덱스 하나만 볼 게 아니라:

- `WHERE`
- `ORDER BY`
- `SELECT` 컬럼

을 함께 봐서 복합 인덱스와 커버링 가능성을 같이 생각해야 한다.

### 예시 3. 왜 plan이 이상한지 첫 질문

`EXPLAIN`을 봤더니 `key = NULL`, `rows`가 매우 크다면, 초보자의 첫 질문은 "`DB가 이상한가요?`"가 아니라 아래가 더 맞다.

- WHERE 컬럼에 인덱스가 있는가
- 함수/타입 변환 때문에 인덱스를 못 타는가
- 정렬 때문에 filesort가 생겼는가

## 더 깊이 가려면

- `EXPLAIN`의 `type`, `rows`, `Extra`를 더 정확히 읽고 싶다면 → [인덱스와 실행 계획](./index-and-explain.md)
- `WHERE + ORDER BY + LIMIT`에 맞는 복합 인덱스 순서와 커버링 설계를 더 보고 싶다면 → [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
- MySQL과 PostgreSQL의 저장 구조 차이 때문에 clustered/secondary 감각이 왜 달라지는지 보고 싶다면 → [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md)
- SQL이 논리적으로 어떻게 실행되고 조인 순서가 왜 plan에 영향을 주는지 붙여 보고 싶다면 → [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
- JPA 코드에서 인덱스 설계가 엔티티/쿼리 메서드와 어떻게 연결되는지 보려면 → [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

## 여기서 멈추는 기준

아래 세 줄이 분리되면 이 문서는 충분히 읽은 것이다.

- 인덱스는 전체를 다 훑지 않도록 찾는 길을 미리 정리한 자료구조다.
- 좋은 인덱스는 `WHERE`, `ORDER BY`, 조회 컬럼 모양과 같이 봐야 한다.
- `EXPLAIN`은 먼저 `key -> rows -> Extra -> type` 순서로 읽고, 깊은 엔진 내부는 다음 문서로 넘긴다.

## 한 줄 정리

인덱스는 B-Tree 기반의 빠른 찾기 경로이고, clustered/secondary/covering 차이와 `EXPLAIN`의 기본 신호를 함께 읽어야 "인덱스를 만들었는데 왜 아직 느린가"를 설명할 수 있다.

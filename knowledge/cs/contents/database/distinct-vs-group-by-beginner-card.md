---
schema_version: 3
title: DISTINCT vs GROUP BY 초보자 비교 카드
concept_id: database/distinct-vs-group-by-beginner-card
canonical: true
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- distinct-vs-group-by-beginner
- duplicate-removal-vs-aggregation
- join-row-explosion-distinct-mask
aliases:
- distinct vs group by
- distinct beginner
- group by beginner
- duplicate removal sql
- group by without aggregate
- 중복 제거 sql
- distinct group by 차이
- group by 언제 써요
symptoms:
- 중복 제거만 필요한데 DISTINCT와 GROUP BY 중 무엇을 써야 할지 모르겠어
- JOIN 뒤 row가 늘어난 문제를 DISTINCT나 GROUP BY로 덮으려 하고 있어
- GROUP BY가 중복 제거처럼 보일 때 집계 의도와 결과 축을 구분하지 못하고 있어
intents:
- comparison
- definition
- troubleshooting
prerequisites:
- database/sql-aggregate-groupby-basics
next_docs:
- database/join-row-increase-distinct-symptom-card
- database/result-row-explosion-debugging
- database/sql-join-basics
linked_paths:
- contents/database/sql-aggregate-groupby-basics.md
- contents/database/join-row-increase-distinct-symptom-card.md
- contents/database/result-row-explosion-debugging-checklist.md
- contents/database/sql-join-basics.md
- contents/spring/spring-data-jpa-basics.md
confusable_with:
- database/sql-aggregate-groupby-basics
- database/join-row-increase-distinct-symptom-card
- database/result-row-explosion-debugging
forbidden_neighbors: []
expected_queries:
- DISTINCT와 GROUP BY는 언제 다르게 써야 해?
- 집계 없이 중복 제거만 필요하면 DISTINCT가 맞아?
- GROUP BY도 결과가 한 줄씩 나오는데 DISTINCT와 뭐가 달라?
- JOIN 후 row가 늘어난 문제를 DISTINCT로 덮으면 왜 위험해?
- 중복 제거와 그룹별 집계를 초보자 기준으로 비교해줘
contextual_chunk_prefix: |
  이 문서는 DISTINCT의 중복 제거 의도와 GROUP BY의 그룹별 집계 의도를 분리하는 beginner chooser다.
  distinct vs group by, duplicate removal, group by without aggregate, join row explosion 같은 자연어 비교 질문이 본 문서에 매핑된다.
---
# DISTINCT vs GROUP BY 초보자 비교 카드

> 한 줄 요약: 집계 없이 중복 제거만 필요하면 먼저 `DISTINCT`를 고르고, `GROUP BY`는 "그룹별로 계산하거나 요약한다"는 의도가 있을 때 고르면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [SQL 집계 함수와 GROUP BY 기초](./sql-aggregate-groupby-basics.md)
- [JOIN 뒤 row가 늘었을 때 DISTINCT로 덮으면 안 되는 이유 카드](./join-row-increase-distinct-symptom-card.md)
- [Result-row Explosion Debugging Checklist](./result-row-explosion-debugging-checklist.md)
- [SQL 조인 기초](./sql-join-basics.md)
- [database 카테고리 인덱스](./README.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

retrieval-anchor-keywords: distinct vs group by, distinct beginner, group by beginner, 중복 제거 sql, distinct group by 차이, group by 언제 써요, distinct 언제 써요, 집계 없이 중복 제거, sql 처음 distinct group by, sql 헷갈려요 distinct, what is distinct, group by basics

## 핵심 개념

초보자 기준으로는 이렇게 먼저 잡으면 된다.

- `DISTINCT`는 **같은 결과 row를 한 번만 보여 달라**는 요청이다.
- `GROUP BY`는 **같은 값을 묶어서 그룹 단위로 본다**는 요청이다.

둘 다 결과가 비슷해 보일 때가 있어서 헷갈리지만, 질문이 다르다.

- "이 값 목록에서 중복만 없애고 싶다"면 `DISTINCT`
- "부서별 몇 명인지, 상태별 몇 건인지 보고 싶다"면 `GROUP BY`

즉 beginner mental model은 `중복 제거`와 `그룹 요약`을 먼저 분리하는 것이다.

## 한눈에 보기

| 지금 필요한 것 | 먼저 고를 것 | 이유 |
|---|---|---|
| 이메일 도메인 목록처럼 같은 값만 한 번씩 보기 | `DISTINCT` | 중복 제거가 목적이다 |
| 부서별 인원 수, 상태별 주문 수 보기 | `GROUP BY` | 그룹별 집계가 목적이다 |
| 결과는 한 줄씩 상세 row인데 조인 때문에 반복돼 보임 | 원인부터 확인 | `DISTINCT`나 `GROUP BY`로 덮기 전에 왜 늘었는지 봐야 한다 |

같은 결과처럼 보이는 예시:

```sql
SELECT DISTINCT department
FROM employees;

SELECT department
FROM employees
GROUP BY department;
```

위 두 쿼리는 같은 결과가 나올 수 있다. 그래도 초보자에게는 `중복 제거면 DISTINCT`, `집계 의도면 GROUP BY`라는 선택 규칙이 더 안전하다.

## 왜 헷갈리나

`GROUP BY`는 그룹당 한 줄을 만들기 때문에, 겉으로 보면 "중복 제거"처럼 보일 수 있다.

예를 들어 `department`가 `backend`, `backend`, `frontend`라면:

- `DISTINCT department` 결과: `backend`, `frontend`
- `GROUP BY department` 결과: `backend`, `frontend`

그래서 "`GROUP BY`도 중복 제거 아니에요?"라는 질문이 자주 나온다.
하지만 `GROUP BY`는 보통 여기서 끝나지 않고 `COUNT(*)`, `SUM(amount)` 같은 집계와 같이 읽는다.

또 한 가지 혼동은 조인 뒤 row가 늘어난 상황이다. 이때 `DISTINCT`를 붙이면 일단 줄어들 수 있고, `GROUP BY id`도 한 줄처럼 보일 수 있다. 하지만 이런 경우는 문법 선택보다 **왜 row가 늘었는지**가 먼저다.

## 고르는 기준

### 1. 집계가 없고 유일한 값 목록만 필요하다

이때는 `DISTINCT`가 가장 직접적이다.

```sql
SELECT DISTINCT status
FROM orders;
```

질문이 "주문 상태 종류가 뭐가 있지?"라면 이 쿼리가 의도와 잘 맞는다.

### 2. 그룹별 계산이 필요하다

이때는 `GROUP BY`가 맞다.

```sql
SELECT status, COUNT(*)
FROM orders
GROUP BY status;
```

질문이 "상태별 주문 수가 몇 건이지?"로 바뀌는 순간, 중복 제거가 아니라 그룹 요약이 된다.

### 3. 조인 결과가 이상해서 일단 줄이고 싶다

이 경우는 `DISTINCT`와 `GROUP BY`를 고르기 전에 원인을 먼저 본다.

- 진짜 중복 데이터인가
- 1:N 관계를 상세 row로 펼친 정상 결과인가
- 내가 원하는 결과 단위가 상세인지 요약인지

이 판단 없이 `GROUP BY id`로 줄이면 다른 컬럼 의미가 깨질 수 있다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 위험한가 | 더 안전한 첫 대응 |
|---|---|---|
| "`GROUP BY`가 더 범용이니까 그냥 그걸 쓰면 되죠?" | 의도가 중복 제거인지 요약인지 흐려진다 | 집계가 없으면 먼저 `DISTINCT`를 본다 |
| "`DISTINCT`랑 `GROUP BY`는 완전히 같은 거죠?" | 결과가 같아 보여도 읽는 사람에게 전달하는 의도가 다르다 | 결과가 아니라 질문을 기준으로 고른다 |
| "`GROUP BY id`로 한 줄로 만들면 끝 아닌가요?" | 다른 컬럼이 비결정적이거나 정보가 사라질 수 있다 | 원하는 결과 한 줄의 단위를 먼저 말로 정한다 |
| "조인 결과가 많으면 `DISTINCT` 붙이면 해결" | 중복 원인, 잘못된 조인 키, 결과 단위 문제를 가릴 수 있다 | 먼저 [JOIN 뒤 row가 늘었을 때 DISTINCT로 덮으면 안 되는 이유 카드](./join-row-increase-distinct-symptom-card.md)로 증상부터 분리한다 |

## 실무에서 쓰는 모습

가장 흔한 초급 시나리오는 두 가지다.

1. 필터 UI에 넣을 "상태 목록", "카테고리 목록"처럼 **값 목록만 한 번씩** 뽑을 때는 `DISTINCT`
2. 대시보드에서 "상태별 건수", "부서별 인원 수"처럼 **그룹별 숫자**가 필요할 때는 `GROUP BY`

MySQL이든 PostgreSQL이든 내부 실행 계획은 다를 수 있다. 하지만 beginner 첫 선택 규칙은 그대로 둬도 된다.

- 의도가 중복 제거면 `DISTINCT`
- 의도가 그룹 요약이면 `GROUP BY`

성능 비교를 일반 규칙처럼 외우기보다, 먼저 의도를 맞추고 필요할 때 `EXPLAIN`으로 확인하는 편이 안전하다.

## 더 깊이 가려면

- `GROUP BY`, `HAVING`, 집계 함수 기본기를 다시 보려면 → [SQL 집계 함수와 GROUP BY 기초](./sql-aggregate-groupby-basics.md)
- 조인 뒤 row가 왜 늘었는지 먼저 증상 카드로 짧게 분리하려면 → [JOIN 뒤 row가 늘었을 때 DISTINCT로 덮으면 안 되는 이유 카드](./join-row-increase-distinct-symptom-card.md)
- row explosion을 체크리스트 순서로 디버깅하려면 → [Result-row Explosion Debugging Checklist](./result-row-explosion-debugging-checklist.md)
- SQL 결과 단위와 JOIN 읽기 순서를 같이 보려면 → [SQL 조인 기초](./sql-join-basics.md)
- JPA에서 `distinct`가 query method나 fetch join과 섞여 헷갈리면 → [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

## 면접/시니어 질문 미리보기

> Q: 집계 없이 중복 제거만 필요할 때 `DISTINCT`와 `GROUP BY` 중 무엇을 고르시겠어요?
> 의도: 문법 암기가 아니라 SQL 의도를 설명할 수 있는지 확인
> 핵심: 유일한 값 목록이 목적이면 `DISTINCT`, 그룹별 계산이나 요약이 목적이면 `GROUP BY`를 고른다.

> Q: 조인 결과가 많아졌을 때 `GROUP BY id`로 줄이면 되지 않나요?
> 의도: 결과 단위와 데이터 의미를 보존하는지 확인
> 핵심: 먼저 왜 row가 늘었는지 설명해야 한다. 임의로 `GROUP BY`를 넣으면 다른 컬럼 의미가 깨질 수 있다.

## 한 줄 정리

`DISTINCT`는 "중복 없이 보여 달라", `GROUP BY`는 "묶어서 계산하자"라는 신호로 읽으면 초급 선택이 훨씬 덜 헷갈린다.

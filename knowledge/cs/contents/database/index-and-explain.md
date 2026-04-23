# 인덱스와 실행 계획

**난이도: 🔴 Advanced**

> 신입 백엔드 개발자가 성능 문제를 설명할 때 필요한 핵심 정리

관련 문서: [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md), [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md), [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md), [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md), [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
retrieval-anchor-keywords: index basics, explain plan, explain columns, explain type key rows extra, possible_keys, key_len, filtered, using where, using filesort, type all, key null, index not used, explain symptom route, order by limit slow, sargable predicate, functional index, generated column, composite index, leftmost prefix, backend query tuning, 실행 계획 입문, explain 해석 순서, type all key null

<details>
<summary>Table of Contents</summary>

- [이 문서가 답하는 질문](#이-문서가-답하는-질문)
- [EXPLAIN symptom 빠른 라우트](#explain-symptom-빠른-라우트)
- [왜 중요한가](#왜-중요한가)
- [인덱스란](#인덱스란)
- [B-Tree 인덱스](#b-tree-인덱스)
- [언제 인덱스가 잘 타는가](#언제-인덱스가-잘-타는가)
- [인덱스가 잘 안 타는 경우](#인덱스가-잘-안-타는-경우)
- [복합 인덱스와 왼쪽 접두어 규칙](#복합-인덱스와-왼쪽-접두어-규칙)
- [실행 계획 EXPLAIN](#실행-계획-explain)
- [추천 공식 자료](#추천-공식-자료)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 이 문서가 답하는 질문

- `EXPLAIN`의 `type`, `key`, `rows`, `Extra`를 어떤 순서로 읽어야 하는가
- 인덱스 자체가 안 맞는 경우와, 인덱스는 타지만 정렬/커버링이 어긋난 경우를 어떻게 구분하는가
- 실행 계획을 읽은 뒤 다음으로 어느 문서로 이동해야 하는가

## EXPLAIN symptom 빠른 라우트

| 지금 보이는 신호 | 먼저 볼 문서 | 바로 이어서 볼 문서 |
| --- | --- | --- |
| `type = ALL`, `key = NULL`, `possible_keys`도 빈약함 | [인덱스와 실행 계획](./index-and-explain.md) | [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| `ORDER BY ... LIMIT`를 붙이면 느려지거나 `Using filesort`가 보임 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) | [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| `Using index`가 보이는데도 기대보다 느리거나 커버링 여부가 헷갈림 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) | [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md) |
| `rows` 추정치가 실제와 다르게 보이거나 환경마다 plan이 흔들림 | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) | [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| DB가 느린지, 앱 레이어가 느린지부터 애매함 | [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) | [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |

## 왜 중요한가

백엔드에서 쿼리가 느려지는 가장 흔한 이유 중 하나는 **인덱스 설계 부족**이다.

즉,

- 어떤 컬럼에 인덱스를 걸어야 하는지
- 왜 어떤 쿼리는 빠르고 어떤 쿼리는 느린지
- 실행 계획을 어떻게 읽어야 하는지

를 설명할 수 있어야 한다.

---

## 인덱스란

인덱스는 **데이터를 빨리 찾기 위한 추가 자료구조**다.

책으로 비유하면:

- 테이블 전체 조회 = 책을 처음부터 끝까지 훑는 것
- 인덱스 사용 = 책 뒤의 색인에서 키워드를 찾는 것

즉 인덱스는 조회 성능을 높이는 대신

- 저장 공간을 더 쓰고
- `INSERT`, `UPDATE`, `DELETE` 비용이 약간 늘어난다

---

## B-Tree 인덱스

가장 기본적이고 자주 쓰는 인덱스는 보통 **B-Tree**다.

특징:

- 정렬 가능한 값에 적합
- `=`, `<`, `>`, `BETWEEN`, `IN`
같은 조건에서 잘 작동

실무에서 “인덱스”라고 하면 대부분 먼저 B-Tree를 떠올리면 된다.

---

## 언제 인덱스가 잘 타는가

예:

```sql
SELECT * FROM member WHERE email = 'a@b.com';
SELECT * FROM orders WHERE created_at BETWEEN ... AND ...;
```

즉 보통

- 동등 조건
- 범위 조건
- 정렬 조건

에서 잘 활용된다.

---

## 인덱스가 잘 안 타는 경우

### 1. 컬럼에 함수 적용

```sql
WHERE LOWER(name) = 'donkey'
```

이 경우는 일반 인덱스보다 generated column이나 functional index가 더 맞을 수 있다.

### 2. 앞부분이 고정되지 않은 LIKE

```sql
WHERE name LIKE '%abc'
```

### 3. 타입 변환이 일어나는 경우

예를 들어 숫자 컬럼을 문자열처럼 비교하는 경우

### 4. 선택도가 너무 낮은 컬럼

예:

- 성별
- boolean 값

이런 컬럼은 인덱스를 걸어도 효과가 약할 수 있다.

---

## 복합 인덱스와 왼쪽 접두어 규칙

예:

```sql
INDEX (team, status, created_at)
```

이 인덱스가 있으면

- `team`
- `team, status`
- `team, status, created_at`

순서는 잘 활용된다.

하지만

- `status`만
- `created_at`만

이런 식은 잘 활용되지 않을 수 있다.

이걸 보통 **왼쪽 접두어 규칙**이라고 설명한다.

---

## 실행 계획 EXPLAIN

`EXPLAIN`은 **DB가 이 쿼리를 어떻게 실행할지 보여주는 기능**이다.

즉:

- 인덱스를 쓰는지
- 어떤 순서로 조인하는지
- full scan인지

를 확인할 수 있다.

### 먼저 보는 순서

1. `type`: full scan인지, range/index scan인지 먼저 본다.
2. `key` / `possible_keys`: 후보 인덱스가 있었는지, 실제로 어떤 인덱스를 골랐는지 본다.
3. `rows`: 얼마나 많은 row를 읽을 것으로 추정하는지 본다.
4. `Extra`: `Using where`, `Using filesort`, `Using index` 같은 추가 신호를 읽는다.

이 순서로 보면 "인덱스 자체가 없는가", "있는 인덱스를 안 탔는가", "탔지만 정렬/커버링이 새 병목인가"를 분리하기 쉽다.

### 왜 중요하나

인덱스를 걸었다고 무조건 빨라지는 게 아니다.  
실제로 DB가 그 인덱스를 사용할지 확인해야 한다.

즉 **성능 문제는 감으로 보지 말고 실행 계획으로 확인**하는 습관이 중요하다.

예를 들어:

- `type = ALL`과 `key = NULL`이면 인덱스 설계나 predicate shape부터 다시 본다.
- `key`는 잡혔는데 `Extra`에 `Using filesort`가 남으면 복합 인덱스 순서와 정렬 축을 다시 본다.
- `rows` 추정치가 수상하면 통계와 cardinality estimation 문제를 의심한다.

---

## 추천 공식 자료

- PostgreSQL Index Types:
  - https://www.postgresql.org/docs/current/indexes-types.html
- MySQL EXPLAIN:
  - https://dev.mysql.com/doc/en/explain.html

---

## 면접에서 자주 나오는 질문

### Q. 인덱스는 왜 빠른가요?

- 테이블 전체를 훑지 않고 별도 자료구조를 통해 빠르게 탐색할 수 있기 때문이다.

### Q. 인덱스가 무조건 좋은가요?

- 아니다.
- 조회는 빨라질 수 있지만 저장 공간이 늘고 쓰기 비용이 커질 수 있다.

### Q. 복합 인덱스에서 컬럼 순서가 왜 중요한가요?

- 왼쪽 접두어 규칙 때문에 인덱스 활용 가능 범위가 달라지기 때문이다.

### Q. 인덱스를 걸었는데 왜 느릴 수 있나요?

- DB가 그 인덱스를 실제로 사용하지 않을 수 있기 때문이다.
- 함수 사용, LIKE 패턴, 선택도 문제, 타입 변환 등이 원인이 될 수 있다.

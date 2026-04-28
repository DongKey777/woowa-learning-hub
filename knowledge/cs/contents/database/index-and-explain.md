# 인덱스와 실행 계획

> 한 줄 요약: `EXPLAIN`은 "DB가 이 조회를 어떤 길로 읽으려는지 적어 둔 경로 메모"이고, 처음에는 `key -> rows -> Extra -> type` 순서만 읽어도 길을 많이 잃지 않는다.

**난이도: 🟡 Intermediate**

관련 문서:

- [인덱스 기초](./index-basics.md)
- [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
- [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md)
- [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md)
- [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
- [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)
- [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
- [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

retrieval-anchor-keywords: explain basics, explain beginner, explain plan first read, explain 해석 순서, explain 처음, explain 왜 느려요, type all key null, using filesort, rows explain, possible_keys key extra, order by limit slow, index not used, composite index explain, query tuning basics, what is explain

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

- `EXPLAIN`이 뭐예요, 왜 보나요?
- `EXPLAIN`의 `type`, `key`, `rows`, `Extra`를 어떤 순서로 읽어야 하는가
- 인덱스 자체가 안 맞는 경우와, 인덱스는 타지만 정렬/커버링이 어긋난 경우를 어떻게 구분하는가
- 실행 계획을 읽은 뒤 다음으로 어느 문서로 이동해야 하는가

## 먼저 잡을 mental model

이 문서는 "인덱스가 뭐예요?"보다 한 단계 뒤다.  
이미 [인덱스 기초](./index-basics.md)에서 "인덱스는 찾는 길"이라는 감각을 잡았고, 이제는 **DB가 그 길을 실제로 탔는지 확인**하려는 순간에 펼치면 된다.

```text
느린 조회를 보면
  -> WHERE / ORDER BY / LIMIT 모양을 먼저 본다
  -> EXPLAIN으로 DB가 고른 길을 본다
  -> key / rows / Extra / type 순서로 읽는다
  -> 인덱스 부재인지, 정렬 미스인지, 통계 흔들림인지 분리한다
```

초보자에게는 `EXPLAIN`을 "쿼리 성적표"보다 "DB가 선택한 길 설명서"로 보는 편이 덜 헷갈린다.

- `key`는 "어느 길을 탔나"를 보여 준다.
- `rows`는 "얼마나 많이 읽을 것 같나"를 보여 준다.
- `Extra`는 "정렬, 임시 테이블, 커버링 같은 추가 작업이 붙었나"를 보여 준다.
- `type`은 "얼마나 넓게 읽나"를 마지막에 확인하는 칸이다.

처음에는 아래 3가지만 기억해도 된다.

| 지금 궁금한 것 | 이 문서가 답하나? | 먼저 볼 것 |
| --- | --- | --- |
| "`EXPLAIN`이 뭐예요?" | 예 | 아래 `처음 읽는 4칸` |
| "`save()`만 보이는데 SQL은 어디 있죠?" | 아니오 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`commit`은 했는데 왜 중복 판매가 나죠?" | 아니오 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |

## 먼저 고르는 30초 질문

`EXPLAIN`을 펴기 전에 지금 질문이 "SQL 위치", "동시성", "조회 경로" 중 무엇인지 먼저 자르면 덜 흔들린다.

| 지금 들리는 말 | 지금 `EXPLAIN` 문서로 오나? | 먼저 갈 문서 |
| --- | --- | --- |
| "`save()`는 보이는데 SQL이 어디 있죠?" | 아니오 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`@Transactional`인데 왜 마지막 재고가 또 팔리죠?" | 아니오 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md), [락 기초](./lock-basics.md) |
| "`WHERE` 조건 하나인데 왜 느리죠?" | 예 | 이 문서 |
| "`key = NULL`이랑 `Using filesort`가 같이 보여요" | 예 | 이 문서 |

처음 읽기에서는 "`EXPLAIN`을 다 외워야 한다"보다 "조회 경로 문제일 때만 이 문서를 펼친다"가 더 중요하다.

## EXPLAIN symptom 빠른 라우트

| 지금 보이는 신호 | 먼저 볼 문서 | 바로 이어서 볼 문서 |
| --- | --- | --- |
| `type = ALL`, `key = NULL`, `possible_keys`도 빈약함 | [인덱스와 실행 계획](./index-and-explain.md) | [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| `ORDER BY ... LIMIT`를 붙이면 느려지거나 `Using filesort`가 보임 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) | [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| `Using index`가 보이는데도 기대보다 느리거나 커버링 여부가 헷갈림 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) | [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md) |
| `rows` 추정치가 실제와 다르게 보이거나 환경마다 plan이 흔들림 | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) | [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| DB가 느린지, 앱 레이어가 느린지부터 애매함 | [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) | [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |

## 처음 읽는 4칸

`EXPLAIN` 표가 길어 보여도 초보자는 네 칸만 먼저 보면 된다.

| 칸 | 초보자용 질문 | 첫 해석 |
| --- | --- | --- |
| `key` | 실제로 선택한 인덱스가 있나? | `NULL`이면 인덱스 설계나 조건식 모양부터 다시 본다 |
| `rows` | DB가 몇 건쯤 읽을 거라 보나? | 숫자가 크면 읽는 양이 많을 가능성이 높다 |
| `Extra` | 정렬/임시 테이블 같은 추가 비용이 있나? | `Using filesort`, `Using temporary`, `Using index`를 먼저 본다 |
| `type` | full scan에 가까운가, 좁혀 읽는가? | `ALL`이면 넓게 읽는 쪽을 의심한다 |

많이 헷갈리는 지점은 "`type`부터 외워야 하나요?"인데, 입문자는 그럴 필요가 없다.

- 먼저 `key = NULL`인지 본다.
- 그다음 `rows`가 과하게 큰지 본다.
- `Extra`로 정렬/커버링 신호를 본다.
- 마지막에 `type`으로 full scan 쪽인지 확인한다.

이 순서가 좋은 이유는 "인덱스 자체가 없는 문제"와 "인덱스는 있는데 정렬이나 컬럼 구성이 어긋난 문제"를 빨리 분리할 수 있기 때문이다.

아래 한 줄로도 기억할 수 있다.

```text
key = 길 선택, rows = 읽는 양, Extra = 추가 작업, type = 읽기 범위
```

## 처음 읽을 때 바로 쓰는 미니 판독표

처음 보는 plan에서는 정답을 맞히려 하기보다, 아래 3갈래 중 어디인지 먼저 분리하면 된다.

| 가장 먼저 보인 조합 | 초보자용 첫 판단 | 다음 1걸음 |
| --- | --- | --- |
| `key = NULL` + `type = ALL` | 인덱스 자체가 없거나 조건식 모양이 안 맞을 수 있다 | [인덱스 기초](./index-basics.md)로 돌아가 `WHERE` 컬럼, 함수, 타입 변환을 다시 본다 |
| `key`는 잡혔는데 `Using filesort` | 찾는 길은 있는데 정렬 길이가 따로 놀 수 있다 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)로 간다 |
| `key`도 있고 `Using index`도 있는데 느림 | 읽는 양이나 통계, 너무 넓은 covering index를 의심한다 | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |

이 표의 목적은 "원인을 확정"하는 게 아니라, 처음 5분 안에 엉뚱한 문서로 새지 않게 하는 것이다.

## 왜 중요한가

백엔드에서 쿼리가 느려지는 가장 흔한 이유 중 하나는 **찾는 길과 정렬 길이 맞지 않는 것**이다.

즉,

- 어떤 컬럼에 인덱스를 걸어야 하는지
- 왜 어떤 쿼리는 빠르고 어떤 쿼리는 느린지
- 실행 계획을 어떻게 읽어야 하는지

를 설명할 수 있어야 한다.

---

초보자에게 중요한 건 "인덱스가 있냐 없냐"를 넘어, **DB가 실제로 어떤 길을 선택했는지 근거를 갖고 말하는 것**이다.

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
- full scan인지

를 확인할 수 있다.

### 먼저 보는 순서

1. `key` / `possible_keys`: 후보 인덱스가 있었는지, 실제로 어떤 인덱스를 골랐는지 본다.
2. `rows`: 얼마나 많은 row를 읽을 것으로 추정하는지 본다.
3. `Extra`: `Using where`, `Using filesort`, `Using index` 같은 추가 신호를 읽는다.
4. `type`: 마지막으로 full scan인지, range/index scan인지 확인한다.

이 순서로 보면 "인덱스 자체가 없는가", "있는 인덱스를 안 탔는가", "탔지만 정렬/커버링이 새 병목인가"를 분리하기 쉽다.

### 주문 목록 예시로 읽기

아래처럼 최근 주문 목록을 뽑는 쿼리를 생각해 보자.

```sql
EXPLAIN
SELECT member_id, status, created_at
FROM orders
WHERE member_id = 10
ORDER BY created_at DESC
LIMIT 20;
```

이때 초보자용 첫 해석은 아래 표면 충분하다.

| 보인 신호 | 첫 판단 | 다음 액션 |
| --- | --- | --- |
| `key = NULL` | 찾는 길이 안 잡혔을 수 있다 | `member_id`, 정렬 축, 함수 사용 여부를 다시 본다 |
| `key`는 있는데 `Using filesort` | 찾기는 했지만 정렬 길이까지는 안 맞았을 수 있다 | 복합 인덱스 순서와 `ORDER BY`를 같이 본다 |
| `Using index` | 인덱스만으로 해결하는 커버링 가능성이 있다 | 조회 컬럼 수와 인덱스 폭을 같이 본다 |
| `rows`가 너무 큼 | 읽는 양이 너무 많다 | 조건식 선택도와 통계 흔들림을 의심한다 |

같은 쿼리를 초보자용 질문으로 다시 적으면 아래처럼 된다.

| 지금 물어볼 질문 | 왜 중요한가 |
| --- | --- |
| `member_id`를 찾는 인덱스가 아예 없나? | `key = NULL`이면 첫 출발부터 길이 없다 |
| 인덱스는 탔는데 정렬 때문에 다시 모으고 있나? | `Using filesort`면 "찾기"와 "정렬"이 다른 길일 수 있다 |
| 너무 많은 row를 읽고 나중에 버리나? | `rows`가 크면 인덱스를 타도 느릴 수 있다 |

그래서 `EXPLAIN` 해석은 "좋은 칸/나쁜 칸 암기"보다, "DB가 어디서 시간을 쓸지 보는 질문 3개"로 읽는 편이 낫다.

### 왜 중요하나

인덱스를 걸었다고 무조건 빨라지는 게 아니다.  
실제로 DB가 그 인덱스를 사용할지 확인해야 한다.

즉 **성능 문제는 감으로 보지 말고 실행 계획으로 확인**하는 습관이 중요하다.

예를 들어:

- `type = ALL`과 `key = NULL`이면 인덱스 설계나 predicate shape부터 다시 본다.
- `key`는 잡혔는데 `Extra`에 `Using filesort`가 남으면 복합 인덱스 순서와 정렬 축을 다시 본다.
- `rows` 추정치가 수상하면 통계와 cardinality estimation 문제를 의심한다.

## 자주 섞이는 오해

| 자주 하는 말 | 왜 헷갈리나 | 더 안전한 첫 판단 |
| --- | --- | --- |
| "`EXPLAIN`에서 `type`만 좋으면 끝 아닌가요?" | 다른 칸을 안 보면 정렬/커버링 문제를 놓친다 | `key -> rows -> Extra -> type` 순서로 읽는다 |
| "`Using filesort`면 인덱스가 아예 없는 거죠?" | 찾기용 인덱스와 정렬용 인덱스가 다를 수 있다 | `WHERE`와 `ORDER BY` 축을 같이 본다 |
| "`key`가 잡혔으니 잘 탄 거죠?" | 많이 읽고 나중에 버리는 plan일 수도 있다 | `rows`와 `Extra`를 같이 본다 |
| "`EXPLAIN`만 보면 무조건 원인이 끝나죠?" | 앱 레이어 지연, 락 대기, 통계 흔들림은 추가 확인이 필요하다 | 체크리스트와 playbook으로 이어 붙인다 |

특히 아래 두 오해를 먼저 끊어 두면 초보자가 덜 흔들린다.

- `type`이 좋아 보여도 `rows`가 크거나 `Using filesort`가 붙으면 여전히 느릴 수 있다.
- `key`가 잡혀도 "좋은 인덱스 설계"가 확정된 것은 아니다. 많이 읽고 많이 버리는 plan일 수 있다.

## 여기서 멈추는 기준

아래 네 줄이 분리되면 이 문서는 충분히 읽은 것이다.

- `EXPLAIN`은 DB가 고른 조회 경로를 보여 준다.
- 초보자는 `key -> rows -> Extra -> type` 순서로 읽는다.
- `key = NULL`은 인덱스/조건식 shape 문제를 먼저 의심한다.
- `Using filesort`는 정렬 축과 복합 인덱스 순서를 같이 보라는 신호다.

| 지금 더 궁금한 것 | 다음 문서 |
| --- | --- |
| 복합 인덱스 순서를 어떻게 잡지? | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) |
| 함수 조건 때문에 인덱스를 못 타는 것 같은데? | [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md) |
| `rows` 추정치가 환경마다 흔들리는데? | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) |
| DB가 느린지 앱이 느린지부터 애매한데? | [쿼리 튜닝 체크리스트](./query-tuning-checklist.md), [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |

cross-category bridge:

- SQL이 코드 어디서 만들어졌는지부터 헷갈리면 [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)로 먼저 돌아간다.
- 느린 문제가 아니라 `commit` 뒤 정합성이나 중복 판매가 문제면 [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)로 축을 바꾼다.

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

## 한 줄 정리

`EXPLAIN` 입문은 "정답 컬럼 암기"보다 `key -> rows -> Extra -> type` 순서로 조회 경로를 읽고, 인덱스 부재와 정렬/커버링 미스를 분리하는 감각을 잡는 데 목적이 있다.

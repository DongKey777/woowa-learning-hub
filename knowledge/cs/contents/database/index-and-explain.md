# 인덱스와 실행 계획

> 한 줄 요약: `EXPLAIN`은 "DB가 이 조회를 어떤 길로 읽으려는지 적어 둔 경로 메모"이고, `EXPLAIN ANALYZE`는 그 메모가 실제 실행과 얼마나 맞았는지 확인하는 2차 검증이다.

**난이도: 🟢 Beginner**

관련 문서:

- [인덱스 기초](./index-basics.md)
- [PostgreSQL `EXPLAIN ANALYZE`에서 `actual rows`, `buffers`, `heap fetches`를 같이 읽는 법](./postgresql-explain-analyze-terms-mini-bridge.md)
- [PostgreSQL `Seq Scan`, `Index Scan`, `Bitmap Heap Scan`, `Index Only Scan` 한 장 카드](./postgresql-plan-node-mini-card.md)
- [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
- [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md)
- [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md)
- [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
- [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)
- [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
- [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
- [database 카테고리 인덱스](./README.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

retrieval-anchor-keywords: explain basics, explain analyze beginner, explain vs explain analyze, explain plan first read, explain 해석 순서, explain 처음인데 뭐부터 봐요, explain analyze 뭐예요, explain 왜 느려요, key = null 이 보여요, key null 뭐예요, using filesort 가 보여요, using filesort 왜 보여요, rows가 너무 커 보여요, type all key null, mysql extra vs postgresql explain

<details>
<summary>Table of Contents</summary>

- [이 문서가 답하는 질문](#이-문서가-답하는-질문)
- [EXPLAIN symptom 빠른 라우트](#explain-symptom-빠른-라우트)
- [EXPLAIN vs EXPLAIN ANALYZE 처음 구분하기](#explain-vs-explain-analyze-처음-구분하기)
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
- `EXPLAIN`과 `EXPLAIN ANALYZE`는 언제 다르게 써야 하나요?
- `EXPLAIN`의 `type`, `key`, `rows`, `Extra`를 어떤 순서로 읽어야 하는가
- 인덱스 자체가 안 맞는 경우와, 인덱스는 타지만 정렬/커버링이 어긋난 경우를 어떻게 구분하는가
- 실행 계획을 읽은 뒤 다음으로 어느 문서로 이동해야 하는가

이 문서가 retrieval에서 먼저 이겨야 하는 beginner symptom query도 아래처럼 좁다.

- `"EXPLAIN 처음인데 뭐부터 봐요?"`
- ``"`key = NULL`이 뭐예요?"``
- ``"`Using filesort`가 왜 보여요?"``
- `"rows가 너무 커 보여요"`

## 처음 30초에 먼저 자를 질문

`EXPLAIN`이 눈에 보여도, 지금 막힌 질문이 정말 조회 경로 문제인지 먼저 자르면 glossary처럼 읽히지 않는다.

| 지금 보이는 증상 | 이 문서가 첫 문서인가? | 먼저 갈 문서 |
| --- | --- | --- |
| "`EXPLAIN`이 뭐예요? `key`, `rows`를 어떤 순서로 봐요?" | 예 | 이 문서 |
| "`save()`만 보이는데 SQL이 어디 있죠?" | 아니오 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`@Transactional`인데 왜 마지막 재고가 또 팔리죠?" | 아니오 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md), [락 기초](./lock-basics.md) |
| "느린 게 DB인지 앱인지부터 모르겠어요" | 아니오 | [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |

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
| "`key = NULL`이 보여요" | 예 | 이 문서 |
| "`Using filesort`가 보여요" | 예 | 이 문서 |
| "`rows가 너무 커 보여요`" | 예 | 이 문서 |

처음 읽기에서는 "`EXPLAIN`을 다 외워야 한다"보다 "조회 경로 문제일 때만 이 문서를 펼친다"가 더 중요하다.

## EXPLAIN symptom 빠른 라우트

| 지금 보이는 신호 | 먼저 볼 문서 | 바로 이어서 볼 문서 |
| --- | --- | --- |
| "`key = NULL`이 보여요" | [인덱스와 실행 계획](./index-and-explain.md) | [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| "`Using filesort`가 보여요" | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) | [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| `Using index`가 보이는데도 기대보다 느리거나 커버링 여부가 헷갈림 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) | [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md) |
| "`rows가 너무 커 보여요`" | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) | [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| "`actual rows`, `Buffers`, `Heap Fetches`가 같이 나오는데 서로 무슨 뜻이죠?" | [PostgreSQL `EXPLAIN ANALYZE`에서 `actual rows`, `buffers`, `heap fetches`를 같이 읽는 법](./postgresql-explain-analyze-terms-mini-bridge.md) | [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md), [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) |
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

## MySQL `Extra`와 PostgreSQL plan node 이름, 어떻게 이어 읽나요?

초보자가 자주 헷갈리는 지점은 여기다.
MySQL은 `Extra` 같은 **신호 칸**으로 힌트를 많이 주고, PostgreSQL은 `Sort`, `Seq Scan`, `Index Only Scan` 같은 **plan node 이름**을 바로 보여 준다.

즉 둘은 화면 모양부터 다르다.

- MySQL: "`key`, `rows`, `Extra`에서 무슨 신호가 떴나?"를 본다.
- PostgreSQL: "지금 어떤 node가 하나 더 생겼나?"를 본다.

그래서 아래 표는 "완전히 같은 뜻"이 아니라 **초보자가 처음 읽을 때 붙여 볼 수 있는 번역표**로 쓰는 편이 안전하다.

| MySQL에서 먼저 보이는 것 | PostgreSQL에서 비슷하게 먼저 보이는 이름 | 초보자용 첫 해석 | 바로 단정하면 안 되는 말 |
| --- | --- | --- | --- |
| `type = ALL`, `key = NULL` | `Seq Scan` | 조건에 맞는 인덱스 경로를 못 쓰고 넓게 읽을 가능성이 크다 | "PostgreSQL은 인덱스를 전혀 안 쓴다" |
| `Extra = Using filesort` | `Sort` | 인덱스 순서로 못 끝내서 따로 정렬 작업이 붙었다 | "무조건 디스크 정렬이다" |
| `Extra = Using index` | `Index Only Scan` | 인덱스만으로 끝내려는 방향이 보인다 | "테이블/heap을 절대 안 읽는다" |
| `Extra = Using temporary` | `HashAggregate`, `Materialize`, `Sort` 뒤 집계 node | 중간 결과를 한 번 더 모으거나 정리하는 단계가 붙었다 | "무조건 장애급이다" |
| `Extra = Using where` | `Filter` | 인덱스로 다 못 줄여서 읽은 뒤 한 번 더 거른다 | "인덱스를 아예 안 탔다" |
| `key`는 잡혔는데 `rows`가 크다 | `Bitmap Heap Scan`, `Index Scan`인데 actual/estimated rows가 큼 | 인덱스는 시작점일 뿐이고, 실제 읽는 양은 여전히 클 수 있다 | "인덱스가 보였으니 빠르다" |

## PostgreSQL node 이름은 이렇게 먼저 읽으면 된다

한 줄 감각으로 묶으면 이렇다.

```text
MySQL Extra = 추가 작업 신호
PostgreSQL node name = 지금 실제로 어떤 작업 단계를 택했는지
```

그래서 PostgreSQL plan을 처음 볼 때도 MySQL과 같은 질문으로 읽으면 된다.

1. `Seq Scan`인가, `Index Scan`/`Index Only Scan`인가?
2. `Sort`가 따로 붙었나?
3. `Filter`, `Heap Fetches`, actual rows 때문에 "인덱스는 탔지만 아직 많이 읽는가?"가 보이나?

PostgreSQL node 이름 네 가지를 `Seq Scan`/`Index Scan`/`Bitmap Heap Scan`/`Index Only Scan` 기준으로 한 번에 붙이고 싶다면 [PostgreSQL `Seq Scan`, `Index Scan`, `Bitmap Heap Scan`, `Index Only Scan` 한 장 카드](./postgresql-plan-node-mini-card.md)로 바로 이어 가면 된다.

이 문서의 목적은 엔진별 내부 구현을 비교하는 게 아니라, 초보자가 "`Using filesort`는 알겠는데 PostgreSQL에서는 왜 갑자기 `Sort`라고 써 있지?" 같은 당황을 줄이는 것이다.

## 1분 예시로 읽기

아래처럼 "`최근 주문 20개`를 읽는 쿼리"를 떠올리면 plan 해석이 덜 추상적으로 느껴진다.

```sql
SELECT *
FROM orders
WHERE user_id = 42
ORDER BY created_at DESC
LIMIT 20;
```

| 먼저 보인 plan 조합 | 초보자용 첫 해석 | 다음 1걸음 |
| --- | --- | --- |
| `key = NULL`, `type = ALL` | `user_id`로 찾는 길 자체가 약할 수 있다 | [인덱스 기초](./index-basics.md)로 돌아가 `WHERE` 컬럼 인덱스를 먼저 본다 |
| `key = idx_user_id`인데 `Using filesort` | 찾는 길은 있지만 `ORDER BY created_at` 정렬 길이가 따로 논다 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)로 이어 간다 |
| `key`는 잡혔는데 `rows`가 여전히 큼 | 조건이 넓거나 통계가 빗나가 실제 읽는 양이 클 수 있다 | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |

핵심은 plan을 "정답표"가 아니라 "`찾는 길`, `정렬 길`, `읽는 양` 중 어디가 먼저 어긋났나"를 고르는 체크리스트로 읽는 것이다.

## EXPLAIN vs EXPLAIN ANALYZE 처음 구분하기

초보자가 가장 많이 섞는 지점은 "`rows` 숫자가 실제인가요?"와 "`EXPLAIN`만 보면 실행도 끝난 건가요?"다.

여기서는 아래처럼 두 도구를 나누면 충분하다.

| 도구 | 초보자용 한 문장 | 먼저 볼 때 |
| --- | --- | --- |
| `EXPLAIN` | "DB가 이렇게 읽을 것 같아요"라는 추정 메모 | 처음 경로를 빠르게 읽을 때 |
| `EXPLAIN ANALYZE` | "방금 실제로 이렇게 읽었어요"라는 실행 확인 | 추정치와 체감이 엇갈릴 때 |

짧게 기억하면 이렇다.

```text
EXPLAIN = 예상 경로
EXPLAIN ANALYZE = 실제 실행 확인
```

처음에는 항상 plain `EXPLAIN`부터 시작해도 된다.
`key = NULL`, `Using filesort`, `rows`가 너무 큰 장면은 plain `EXPLAIN`만으로도 1차 방향을 잡을 수 있기 때문이다.

반대로 아래처럼 "추정은 괜찮아 보이는데 실제 체감이 이상하다"면 `EXPLAIN ANALYZE`가 더 맞다.

| 지금 상황 | plain `EXPLAIN`만으로 충분한가 | `EXPLAIN ANALYZE`를 붙이는 이유 |
| --- | --- | --- |
| `key = NULL`, `type = ALL`이 바로 보인다 | 보통 예 | 이미 인덱스 부재/조건식 shape 문제 후보가 선명하다 |
| `Using filesort`가 보이고 `ORDER BY` 축도 분명하다 | 보통 예 | 정렬 경로 미스를 먼저 고치고 다시 보는 편이 빠르다 |
| `rows = 20`처럼 작아 보이는데 실제로는 훨씬 느리다 | 아니오 | 추정치와 실제 읽은 양, 실제 시간 차이를 같이 봐야 한다 |
| 배포 뒤에 같은 SQL plan만 자꾸 흔들린다 | 아니오 | estimate와 actual rows가 계속 어긋나는지 확인해야 한다 |

아주 단순한 예시는 아래처럼 볼 수 있다.

| 장면 | 초보자 첫 해석 |
| --- | --- |
| `EXPLAIN`에서 `rows = 50000` | DB는 많이 읽을 거라고 예상한다 |
| `EXPLAIN ANALYZE`에서 actual rows가 정말 큼 | 예상대로 넓게 읽고 있다 |
| `EXPLAIN`에서는 `rows = 20`인데 `EXPLAIN ANALYZE` actual rows가 훨씬 큼 | 통계나 데이터 분포 때문에 추정이 빗나갔을 수 있다 |

많이 하는 오해도 여기서 같이 끊어 두면 좋다.

- `EXPLAIN`의 `rows`는 보통 추정치다. "실제로 읽은 row 수"와 같은 뜻으로 바로 읽지 않는다.
- `EXPLAIN ANALYZE`는 실제 실행을 동반하므로, 처음부터 모든 SQL에 습관처럼 붙이는 도구로 보지 않는다.
- 엔진마다 출력 형식은 조금 달라도, beginner 관점에서는 "estimate냐 actual이냐"만 먼저 분리하면 된다.

즉 초보자 1차 루틴은 아래 두 줄이면 충분하다.

1. plain `EXPLAIN`으로 `key -> rows -> Extra -> type`을 읽는다.
2. 체감 속도와 estimate가 안 맞을 때만 `EXPLAIN ANALYZE`로 actual rows/time을 확인한다.

## 처음 읽을 때 바로 쓰는 미니 판독표

처음 보는 plan에서는 정답을 맞히려 하기보다, 아래 3갈래 중 어디인지 먼저 분리하면 된다.

| 가장 먼저 보인 조합 | 초보자용 첫 판단 | 다음 1걸음 |
| --- | --- | --- |
| `key = NULL` + `type = ALL` | 인덱스 자체가 없거나 조건식 모양이 안 맞을 수 있다 | [인덱스 기초](./index-basics.md)로 돌아가 `WHERE` 컬럼, 함수, 타입 변환을 다시 본다 |
| `key`는 잡혔는데 `Using filesort` | 찾는 길은 있는데 정렬 길이가 따로 놀 수 있다 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)로 간다 |
| `key`도 있고 `Using index`도 있는데 느림 | 읽는 양이나 통계, 너무 넓은 covering index를 의심한다 | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |

이 표의 목적은 "원인을 확정"하는 게 아니라, 처음 5분 안에 엉뚱한 문서로 새지 않게 하는 것이다.

## 여기서 멈추고 넘길 질문

이 문서는 beginner entrypoint다. 아래 단어가 먼저 궁금하면 본문에서 더 파지 말고 관련 문서로 넘기는 편이 안전하다.

| 지금 더 궁금한 것 | 이 문서에서 길게 안 파는 이유 | 다음 문서 |
| --- | --- | --- |
| 인덱스가 왜 빠른지, B-Tree가 뭔지 | 자료구조 설명보다 `EXPLAIN` 읽기 순서가 먼저다 | [인덱스 기초](./index-basics.md), [Clustered Index와 PK Locality](./clustered-index-locality.md) |
| 함수 조건, `%like`, 타입 변환 때문에 인덱스를 못 타는 것 같음 | 설계 패턴과 migration 판단이 따로 필요하다 | [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md) |
| 복합 인덱스 순서와 covering까지 같이 보고 싶음 | `WHERE`와 `ORDER BY`를 같이 묶는 follow-up이 더 직접적이다 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) |
| estimate와 actual rows가 자꾸 어긋남 | 이미 통계와 엔진별 해석 단계다 | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md), [PostgreSQL `EXPLAIN ANALYZE`에서 `actual rows`, `buffers`, `heap fetches`를 같이 읽는 법](./postgresql-explain-analyze-terms-mini-bridge.md) |
| 실제 장애 대응이나 느린 쿼리 triage 순서가 필요함 | entrypoint보다 playbook 범위다 | [쿼리 튜닝 체크리스트](./query-tuning-checklist.md), [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |

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

## 한 줄 정리

`EXPLAIN` 입문은 "정답 컬럼 암기"보다 `key -> rows -> Extra -> type` 순서로 조회 경로를 읽고, 인덱스 부재와 정렬/커버링 미스를 분리하는 감각을 잡는 데 목적이 있다.

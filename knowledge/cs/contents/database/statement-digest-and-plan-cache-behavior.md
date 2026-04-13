# Statement Digest and Plan Cache Behavior

> 한 줄 요약: MySQL은 일반적인 의미의 전역 plan cache보다 statement digest로 쿼리 형태를 집계하고, prepared statement는 parse 비용을 줄이지만 plan 안정성을 자동 보장하지는 않는다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: statement digest, plan cache, prepared statement, events_statements_summary_by_digest, digest_text, query normalization, performance_schema, plan stability

## 핵심 개념

- 관련 문서:
  - [Optimizer Switch Knobs and Plan Stability](./optimizer-switch-plan-stability-invisible-indexes.md)
  - [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)
  - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)

MySQL에서 statement digest는 쿼리를 정규화해서 같은 "형태"를 묶어 보는 관찰 도구다.  
이건 일반적인 전역 plan cache와는 다르다.

핵심은 다음이다.

- digest는 "무슨 쿼리 패턴이 많이 나오는가"를 보여준다
- prepared statement는 parse 비용을 줄일 수 있다
- 하지만 통계가 바뀌면 실행 계획은 여전히 달라질 수 있다

## 깊이 들어가기

### 1. digest는 무엇을 정규화하나

statement digest는 literal 값이 달라도 같은 구조면 같은 패턴으로 묶을 수 있다.

예:

- `WHERE id = 1`
- `WHERE id = 2`

이 두 쿼리는 구조가 같으면 같은 digest 계열로 관찰될 수 있다.

이걸로 얻는 것:

- 어떤 SQL shape가 자주 오는지
- 느린 패턴이 무엇인지
- literal만 다른 쿼리가 얼마나 반복되는지

### 2. digest는 plan cache가 아니다

중요한 오해는 이것이다.

- digest는 관찰/집계용이다
- digest가 실행 계획을 저장하거나 고정하지는 않는다

즉 digest가 좋다고 plan이 안정적인 것은 아니다.

### 3. prepared statement는 무엇을 줄이나

prepared statement는 파싱과 바인딩 비용을 줄이는 데 도움이 된다.  
하지만 plan이 완전히 고정된다고 생각하면 안 된다.

- parse 비용 감소
- wire protocol 상 반복 실행에 유리
- 그러나 통계와 optimizer_switch 변화는 여전히 영향을 준다

### 4. 왜 plan stability와 같이 봐야 하나

같은 statement shape가 반복되어도 데이터 분포가 바뀌면 실행 계획은 달라질 수 있다.  
그래서 digest, prepared statement, statistics, optimizer_switch를 함께 봐야 한다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `statement digest`
- `plan cache`
- `prepared statement`
- `digest_text`
- `events_statements_summary_by_digest`
- `query normalization`
- `performance_schema`

## 실전 시나리오

### 시나리오 1. 비슷한 쿼리가 너무 많아 어디가 뜨거운지 모른다

digest를 보면 같은 형태의 쿼리가 얼마나 반복되는지 볼 수 있다.  
이걸로 가장 비싼 query shape를 찾고 인덱스/통계를 맞출 수 있다.

### 시나리오 2. prepared statement를 쓰는데도 느려진다

parse 비용은 줄어도 plan regression은 막지 못한다.  
통계가 틀리면 prepared statement도 느릴 수 있다.

### 시나리오 3. literal만 다른 쿼리들이 폭주한다

digest는 이런 패턴을 하나의 shape로 묶어서 보여준다.  
그 덕분에 애플리케이션에서 N개의 비슷한 쿼리를 따로 보지 않아도 된다.

## 코드로 보기

### digest 확인

```sql
SELECT DIGEST_TEXT, COUNT_STAR, SUM_TIMER_WAIT
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;
```

### prepared statement 예시

```sql
PREPARE stmt FROM 'SELECT id, status FROM orders WHERE user_id = ?';
SET @user_id = 1001;
EXECUTE stmt USING @user_id;
DEALLOCATE PREPARE stmt;
```

### plan stability 비교

```sql
EXPLAIN
SELECT id, status
FROM orders
WHERE user_id = 1001;
```

통계와 인덱스가 바뀌면 같은 SQL도 다른 계획을 고를 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| digest 기반 관찰 | query shape를 쉽게 모은다 | plan 자체는 고정되지 않는다 | 성능 분석 |
| prepared statement 사용 | parse 비용을 줄인다 | plan regression을 막지 못한다 | 반복 실행 경로 |
| plan stability 관리 | 실행 계획 변화를 줄인다 | 통계/인덱스 관리가 필요하다 | 운영 핵심 쿼리 |

핵심은 digest를 plan cache로 착각하지 않는 것이고, **관찰 도구와 실행 안정성을 따로 관리**해야 한다는 점이다.

## 꼬리질문

> Q: statement digest는 plan cache인가요?
> 의도: 관찰과 캐시를 구분하는지 확인
> 핵심: 아니다. 쿼리 형태를 집계하는 관찰 도구다

> Q: prepared statement는 왜 쓰나요?
> 의도: parse 비용과 반복 실행 이점을 아는지 확인
> 핵심: 파싱/바인딩 비용을 줄이기 위해서다

> Q: digest가 있는데 왜 plan stability가 여전히 필요한가요?
> 의도: 관찰과 실행 안정성을 분리하는지 확인
> 핵심: digest는 보여줄 뿐, 계획을 고정하지는 않기 때문이다

## 한 줄 정리

statement digest는 반복 쿼리 형태를 관찰하는 도구이고, prepared statement는 parse 비용을 줄일 뿐 plan cache처럼 계획을 고정해 주지는 않는다.

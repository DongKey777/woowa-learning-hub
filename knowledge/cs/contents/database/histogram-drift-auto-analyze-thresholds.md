---
schema_version: 3
title: Histogram Drift and Auto-Analyze Thresholds
concept_id: database/histogram-drift-auto-analyze-thresholds
canonical: false
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- rows-estimate-mismatch
- analyze-after-distribution-shift
- stats-drift-before-hints
aliases:
- histogram drift
- auto analyze threshold
- analyze table timing
- cardinality drift
- stale statistics
- plan drift after deploy
- distribution shift
- rows estimate mismatch
- 왜 배포 후 실행 계획이 바뀌어요
symptoms:
- 배포 후 같은 SQL인데 갑자기 실행 계획이 바뀌었어요
- EXPLAIN rows 추정치가 실제 row 수와 너무 달라요
- ANALYZE를 언제 다시 해야 하는지 감이 안 와요
intents:
- deep_dive
- troubleshooting
prerequisites:
- database/index-and-explain
- database/statistics-histograms-cardinality-estimation
next_docs:
- database/secondary-index-maintenance-cost-analyze-skew
- database/slow-query-analysis-playbook
- database/mysql-optimizer-hints-index-merge
linked_paths:
- contents/database/statistics-histograms-cardinality-estimation.md
- contents/database/secondary-index-maintenance-cost-analyze-skew.md
- contents/database/mysql-optimizer-hints-index-merge.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/query-tuning-checklist.md
confusable_with:
- database/statistics-histograms-cardinality-estimation
- database/query-tuning-checklist
forbidden_neighbors:
- contents/database/index-basics.md
expected_queries:
- histogram drift는 왜 생기고 언제 ANALYZE를 다시 해야 해?
- 배포 후 같은 SQL인데 실행 계획이 바뀌면 통계부터 어떻게 의심해?
- auto analyze threshold를 믿어도 되는지 알고 싶어
- rows 추정치가 실제와 크게 다를 때 histogram을 먼저 봐야 하나?
contextual_chunk_prefix: |
  이 문서는 배포 후 같은 SQL인데 실행 계획이 바뀌거나 rows 추정치가 실제와
  어긋날 때, histogram drift와 auto-analyze 지연이 왜 plan drift로 이어지는지
  설명하는 deep_dive다. stale statistics, distribution shift, analyze table
  timing, rows estimate mismatch, why plan changed after deploy 같은 학습자
  질문을 통계 갱신 타이밍과 cardinality estimation 맥락으로 연결한다.
---

# Histogram Drift and Auto-Analyze Thresholds

> 한 줄 요약: histogram은 한 번 만들고 끝나는 정보가 아니라, 데이터 분포가 바뀌면 흐려지고 다시 분석해야 하는 옵티마이저 자산이다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: histogram drift, auto analyze threshold, persistent statistics, cardinality drift, ANALYZE TABLE, distribution shift, optimizer misestimate, statistics refresh

## 핵심 개념

- 관련 문서:
  - [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)
  - [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)
  - [Optimizer Switch Knobs and Plan Stability](./optimizer-switch-plan-stability-invisible-indexes.md)

histogram은 컬럼 분포를 더 잘 추정하게 해 주지만, 데이터가 바뀌면 그 정보도 낡는다.  
이걸 histogram drift라고 보면 된다.

핵심은 다음이다.

- 분포가 바뀌면 cardinality 추정도 바뀐다
- auto-analyze는 즉시가 아니라 일정 조건에서만 돌아간다
- 수동 ANALYZE가 더 빠른 경우가 많다

## 깊이 들어가기

### 1. histogram drift는 어떻게 생기나

예를 들어 status 컬럼이 초기에 균등했는데, 시간이 지나 `PAID`가 95%가 되면 histogram은 더 이상 현실을 잘 나타내지 못한다.  
이건 통계가 틀렸다는 뜻이 아니라, **통계의 기준 시점이 지나갔다**는 뜻이다.

### 2. auto-analyze는 왜 즉시 갱신이 아닌가

통계 갱신은 공짜가 아니다.  
매 변경마다 바로 다시 분석하면 운영 비용이 커진다.

그래서 엔진은 보통 일정한 변경량이나 조건을 보고 자동 갱신 여부를 판단한다.

- InnoDB persistent statistics는 대체로 일정 비율의 변경 후 다시 계산을 고려한다
- 정확한 임계치는 버전과 설정에 따라 달라질 수 있다
- 즉각성과 비용 사이의 절충이다

### 3. drift를 놓치면 어떤 plan이 깨지나

histogram drift가 생기면 다음이 흔들린다.

- 인덱스 선택
- join order
- skip scan 유무
- filesort vs index order

그래서 plan regression이 생겼을 때 histograms와 auto-analyze 주기를 먼저 본다.

### 4. auto-analyze만 믿지 말아야 하는 이유

자동 갱신은 늦을 수 있다.  
배포 직후, 이벤트 직후, 데이터 적재 직후처럼 분포가 크게 바뀌는 순간은 수동 ANALYZE가 더 안전하다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `histogram drift`
- `auto analyze threshold`
- `persistent statistics`
- `distribution shift`
- `ANALYZE TABLE`
- `optimizer misestimate`

## 실전 시나리오

### 시나리오 1. 배포 후 특정 목록 쿼리만 느려졌다

쿼리 구조는 같아도 분포가 바뀌면 optimizer가 다른 인덱스를 고를 수 있다.  
이때는 히스토그램 drift와 stats refresh 여부를 먼저 본다.

### 시나리오 2. 상태값이 한쪽으로 몰렸다

status, type, flag 같은 컬럼은 시간이 지나면 거의 한쪽으로 쏠릴 수 있다.  
자동 갱신만 기다리면 plan이 오래 틀어진 상태로 남을 수 있다.

### 시나리오 3. 통계는 있는데 plan이 여전히 이상하다

histogram이 있어도 query shape가 바뀌면 잘 못 쓸 수 있다.  
그렇기 때문에 인덱스와 통계를 함께 봐야 한다.

## 코드로 보기

### 히스토그램 확인

```sql
SELECT *
FROM information_schema.column_statistics
WHERE schema_name = 'mydb'
  AND table_name = 'orders';
```

### 통계 갱신

```sql
ANALYZE TABLE orders UPDATE HISTOGRAM ON status WITH 32 BUCKETS;
```

### 자동 재계산 관련 변수

```sql
SHOW VARIABLES LIKE 'innodb_stats_auto_recalc';
SHOW VARIABLES LIKE 'innodb_stats_persistent';
```

### plan 비교

```sql
EXPLAIN ANALYZE
SELECT id, status
FROM orders
WHERE status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| auto-analyze 의존 | 운영이 단순하다 | drift를 늦게 잡을 수 있다 | 분포 변화가 느릴 때 |
| 수동 ANALYZE | 빠르게 plan을 되돌릴 수 있다 | 운영 작업이 추가된다 | 배포/적재 후 |
| histogram 재생성 | skew 추정이 좋아진다 | 관리가 필요하다 | 편중이 심할 때 |

핵심은 histogram을 "만든 뒤 끝"으로 보지 말고, **분포가 바뀔 때마다 다시 맞춰야 하는 옵티마이저 입력**으로 보는 것이다.

## 꼬리질문

> Q: histogram drift는 왜 생기나요?
> 의도: 분포 변화와 통계 기준 시점의 차이를 아는지 확인
> 핵심: 데이터 분포가 바뀌는데 통계가 따라가지 못하기 때문이다

> Q: auto-analyze를 왜 무조건 기다리면 안 되나요?
> 의도: 자동 갱신의 지연을 이해하는지 확인
> 핵심: 임계치 기반이라 즉시 반영되지 않을 수 있다

> Q: histogram이 있어도 plan이 틀릴 수 있나요?
> 의도: histogram을 만능으로 보지 않는지 확인
> 핵심: query shape와 분포 변화에 따라 여전히 빗나갈 수 있다

## 한 줄 정리

histogram drift는 분포 변화로 통계가 낡는 현상이고, auto-analyze는 그 drift를 늦게 잡기 때문에 중요한 지점에서는 수동 ANALYZE가 필요하다.

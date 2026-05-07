---
schema_version: 3
title: Persistent Stats Sampling and Bias
concept_id: database/persistent-stats-sampling-bias
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- optimizer-statistics
- sampling-bias
- persistent-stats
- plan-regression
aliases:
- persistent stats
- sampling bias
- stats sample
- statistics drift
- ANALYZE TABLE
- cardinality estimate
- skewed pages
- InnoDB persistent statistics
- persistent stats 편향
- 통계 샘플링 bias
symptoms:
- persistent statistics가 plan 안정성은 주지만 샘플링 편향까지 오래 고정해 특정 쿼리 plan regression을 만들고 있어
- hot value나 skewed page가 생겼는데 cardinality estimate가 현실을 반영하지 못해 wrong index를 고르고 있어
- ANALYZE TABLE, sample pages, histogram reset 중 무엇으로 stats drift를 다룰지 판단해야 해
intents:
- deep_dive
- troubleshooting
prerequisites:
- database/statistics-histograms-cardinality-estimation
- database/histogram-drift-auto-analyze-thresholds
next_docs:
- database/optimizer-trace-reading
- database/optimizer-switch-plan-stability-invisible-indexes
- database/secondary-index-maintenance-statistics-skew
linked_paths:
- contents/database/statistics-histograms-cardinality-estimation.md
- contents/database/histogram-drift-auto-analyze-thresholds.md
- contents/database/secondary-index-maintenance-cost-analyze-skew.md
- contents/database/optimizer-trace-reading.md
- contents/database/optimizer-switch-plan-stability-invisible-indexes.md
- contents/database/query-tuning-checklist.md
confusable_with:
- database/statistics-histograms-cardinality-estimation
- database/histogram-drift-auto-analyze-thresholds
- database/optimizer-switch-plan-stability-invisible-indexes
forbidden_neighbors: []
expected_queries:
- InnoDB persistent stats가 plan stability를 주지만 sampling bias를 오래 고정할 수 있는 이유가 뭐야?
- persistent statistics에서 샘플 페이지가 skew되면 cardinality estimate가 어떻게 틀어져?
- ANALYZE TABLE을 해도 특정 인덱스 선택이 계속 이상하면 어떤 stats bias를 의심해?
- innodb_stats_persistent_sample_pages를 늘리는 tradeoff를 설명해줘
- histogram drift와 persistent stats sampling bias를 어떻게 구분해서 봐?
contextual_chunk_prefix: |
  이 문서는 InnoDB persistent statistics가 plan stability를 주는 동시에 sampling bias, skewed pages, cardinality estimate 오류를 오래 보존할 수 있음을 다루는 advanced deep dive다.
  persistent stats 편향, 통계 샘플링 bias, wrong cardinality estimate 질문이 본 문서에 매핑된다.
---
# Persistent Stats Sampling and Bias

> 한 줄 요약: persistent stats는 통계를 유지해 주지만, 샘플이 편향되면 오래 유지되는 잘못된 추정도 함께 고정될 수 있다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: persistent stats, sampling bias, stats sample, statistics drift, ANALYZE TABLE, cardinality estimate, skewed pages, InnoDB persistent statistics

## 핵심 개념

- 관련 문서:
  - [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)
  - [Histogram Drift and Auto-Analyze Thresholds](./histogram-drift-auto-analyze-thresholds.md)
  - [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)

persistent statistics는 DB가 테이블/인덱스 통계를 재시작 후에도 유지하게 해 준다.  
하지만 "유지"는 "정확"과 같지 않다.

핵심은 다음이다.

- 통계는 샘플링으로 만들어진다
- 샘플이 치우치면 cardinality도 치우친다
- persistent stats는 그 편향을 오래 유지할 수 있다

## 깊이 들어가기

### 1. persistent stats는 왜 쓰나

재시작할 때마다 통계가 흔들리면 실행 계획도 흔들린다.  
그래서 통계를 저장해 두고 재사용한다.

장점:

- plan 안정성이 좋아진다
- 재기동 후 갑작스런 추정 변화가 줄어든다
- 운영이 예측 가능해진다

### 2. sampling bias는 왜 생기나

샘플은 전체를 보지 않는다.  
따라서 일부 page나 일부 분포가 과대표집되면 통계가 왜곡된다.

대표적인 경우:

- 특정 값이 최근에 급증했다
- hot page와 cold page 분포가 다르다
- index page의 일부 구간만 샘플에 많이 걸린다

### 3. bias가 고정되면 더 위험하다

일시적인 샘플 오차는 다음 ANALYZE로 바로잡힐 수 있다.  
하지만 persistent stats는 그 오차를 오래 들고 갈 수 있다.

즉:

- 한 번 틀린 추정이
- 계속 유지되고
- plan regression을 오래 만든다

### 4. 언제 의심해야 하나

- 재시작 후 plan이 달라졌다
- 특정 쿼리만 계속 이상하다
- histogram은 있는데 cardinality가 여전히 어색하다
- 작은 변화에도 optimizer가 민감하게 흔들린다

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `persistent stats`
- `sampling bias`
- `stats sample`
- `skewed pages`
- `InnoDB persistent statistics`
- `cardinality estimate`

## 실전 시나리오

### 시나리오 1. 재기동 후 plan이 갑자기 바뀐다

persistent stats가 있으면 plan이 안정적일 수 있지만, 샘플이 이미 편향돼 있으면 잘못된 계획도 안정적으로 유지된다.

### 시나리오 2. 데이터가 한쪽으로 몰렸는데 통계는 예전 그대로다

새로운 hot value가 생겼는데 샘플이 그 변화를 못 잡으면 optimizer는 옛날 기준으로 계산한다.  
이때는 수동 ANALYZE나 histogram 재설정이 필요하다.

### 시나리오 3. 특정 인덱스만 자꾸 잘못 고른다

샘플이 특정 page나 범위에 치우친 탓일 수 있다.  
인덱스 자체보다 샘플링 방식이 문제일 수 있다.

## 코드로 보기

### persistent stats 관련 변수

```sql
SHOW VARIABLES LIKE 'innodb_stats_persistent';
SHOW VARIABLES LIKE 'innodb_stats_auto_recalc';
SHOW VARIABLES LIKE 'innodb_stats_persistent_sample_pages';
```

### 통계 갱신

```sql
ANALYZE TABLE orders;
```

### plan 확인

```sql
EXPLAIN
SELECT id, status
FROM orders
WHERE status = 'PAID';
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| persistent stats 유지 | plan 안정성이 좋아진다 | 편향이 오래 남을 수 있다 | 대부분의 운영 DB |
| 샘플 페이지 수 확대 | 추정 정확도가 좋아질 수 있다 | ANALYZE 비용이 늘 수 있다 | 분포가 복잡할 때 |
| 수동 ANALYZE | 왜곡을 빠르게 수정한다 | 운영 작업이 필요하다 | plan regression 직후 |

핵심은 persistent stats를 "안정성"으로만 보지 말고, **샘플링 편향을 오래 보존할 수 있는 장치**로 보는 것이다.

## 꼬리질문

> Q: persistent stats가 왜 필요한가요?
> 의도: 재시작 후 plan 안정성 목적을 아는지 확인
> 핵심: 통계를 유지해 plan 변동을 줄이기 위해서다

> Q: sampling bias는 왜 위험한가요?
> 의도: 샘플이 전체를 대표하지 못하는 문제를 아는지 확인
> 핵심: 잘못된 cardinality가 오래 유지될 수 있기 때문이다

> Q: 샘플 페이지 수를 늘리면 항상 좋은가요?
> 의도: 정확도와 비용의 trade-off를 아는지 확인
> 핵심: 정확도는 좋아질 수 있지만 ANALYZE 비용이 늘 수 있다

## 한 줄 정리

persistent stats는 통계 안정성을 주지만, 샘플링이 편향되면 그 오차까지 오래 고정할 수 있으므로 주기적 재분석이 필요하다.

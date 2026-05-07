---
schema_version: 3
title: Optimizer Trace Reading
concept_id: database/optimizer-trace-reading
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- optimizer-trace
- explain
- cost-model
- plan-regression
aliases:
- optimizer trace
- trace reading
- explain why this plan
- why optimizer chose this plan
- why full scan chosen
- why key null
- rows estimate wrong
- considered execution plans
- 실행 계획 왜 이렇게 골랐나
- EXPLAIN 결과는 아는데 이유를 모르겠음
symptoms:
- EXPLAIN에서 type, key, rows, Extra는 보이지만 optimizer가 왜 그 plan을 골랐는지 설명하지 못하고 있어
- rows estimate와 actual rows가 크게 다르거나 ANALYZE 이후 plan이 바뀌어 cost model과 cardinality 추정을 따라가야 해
- key NULL, filesort, temporary, index_merge 탈락 이유를 optimizer trace로 확인해야 해
intents:
- troubleshooting
- deep_dive
prerequisites:
- database/index-and-explain
- database/query-tuning-checklist
next_docs:
- database/statistics-histograms-cardinality-estimation
- database/optimizer-switch-plan-stability-invisible-indexes
- database/mysql-optimizer-hints-index-merge
linked_paths:
- contents/database/index-and-explain.md
- contents/database/query-tuning-checklist.md
- contents/database/index-condition-pushdown-filesort-temporary-table.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/optimizer-switch-plan-stability-invisible-indexes.md
- contents/database/statistics-histograms-cardinality-estimation.md
- contents/database/mysql-optimizer-hints-index-merge.md
- contents/database/index-skip-scan-behavior.md
confusable_with:
- database/index-and-explain
- database/statistics-histograms-cardinality-estimation
- database/mysql-optimizer-hints-index-merge
forbidden_neighbors: []
expected_queries:
- MySQL EXPLAIN 결과는 알겠는데 optimizer가 왜 이 plan을 골랐는지 어떻게 봐?
- optimizer trace에서 considered_execution_plans와 chosen plan reason을 어떤 순서로 읽어?
- key NULL이나 type ALL이 나온 이유를 optimizer trace로 어떻게 추적해?
- rows estimate가 실제와 다를 때 trace와 statistics를 어떻게 연결해서 봐?
- filesort나 temporary path가 선택된 이유를 cost model 관점에서 설명해줘
contextual_chunk_prefix: |
  이 문서는 MySQL optimizer trace를 EXPLAIN 이후 considered plans, chosen plan, cost model, range analysis, rejected reason을 읽는 advanced deep dive로 다룬다.
  EXPLAIN 결과는 아는데 이유를 모르겠음, why key null, rows estimate wrong, optimizer decision 질문이 본 문서에 매핑된다.
---
# Optimizer Trace Reading

> 한 줄 요약: optimizer trace는 "왜 이 실행 계획을 골랐는가"를 보여주는 내부 메모라서, EXPLAIN보다 한 단계 더 깊게 비용 모델을 읽을 수 있게 해 준다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: optimizer trace, trace reading, explain why this plan, explain result but why, why optimizer chose this plan, why full scan chosen, why key null, key null reason, why rows estimate wrong, explain actual rows mismatch reason, why filesort chosen, why temporary table chosen, cost model, considered_execution_plans, chosen plan, chosen_range_access_summary, range analysis, condition fanout filter, plan drift root cause, optimizer decision, query plan changed after analyze, 실행 계획 왜 이렇게 골랐나, explain 결과는 아는데 이유를 모르겠음, key null 이유, rows mismatch 이유

## 핵심 개념

- 관련 문서:
  - [인덱스와 실행 계획](./index-and-explain.md)
  - [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
  - [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md)
  - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
  - [Optimizer Switch Knobs and Plan Stability](./optimizer-switch-plan-stability-invisible-indexes.md)
  - [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)
  - [MySQL Optimizer Hints and Index Merge](./mysql-optimizer-hints-index-merge.md)
  - [Index Skip Scan Behavior](./index-skip-scan-behavior.md)

## 이 문서가 맡는 EXPLAIN 범위

이 문서는 "`type`, `key`, `rows`, `Extra`는 읽었는데 왜 그 계획이 골라졌는지 모르겠다"를 설명하는 optimizer 내부 근거 entry다.

| 보이는 신호 | 여기서 바로 보는 것 | 먼저 돌아갈 문서 |
| --- | --- | --- |
| `rows` 추정치가 실제와 다르거나 배포 후 plan만 흔들리는데 "왜"가 안 풀림 | fanout, cost model, considered plan, chosen plan reason | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md), [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |
| `type = ALL`, `key = NULL`인데 인덱스가 있어 보여서 이유를 알고 싶음 | range access 탈락 이유, index dive/cost 비교, access path rejection | [인덱스와 실행 계획](./index-and-explain.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| `Using filesort`, `Using temporary`가 남는데 왜 정렬 경로가 선택됐는지 궁금함 | order-preserving access vs sort cost 비교, materialization 선택 이유 | [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md) |
| 아직 병목이 DB인지 앱인지, 통계인지 접근 경로인지도 모호함 | trace drill-down 전에 triage 순서를 먼저 고정 | [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |

EXPLAIN은 결과를 보여준다.  
optimizer trace는 그 결과에 도달하기까지의 고민 과정을 보여준다.

핵심은 다음이다.

- 어떤 후보 계획이 있었는가
- 왜 어떤 계획은 버려졌는가
- 어떤 비용 항목이 최종 선택을 만들었는가

## 깊이 들어가기

### 1. trace를 왜 읽어야 하나

실행 계획이 이상할 때 EXPLAIN만 보면 "왜?"가 남는다.  
optimizer trace는 그 "왜"를 추적하게 해 준다.

예를 들면:

- range 후보가 있었는지
- skip scan이 고려되었는지
- condition fanout이 어떻게 계산되었는지
- 어느 시점에서 다른 plan이 탈락했는지

### 2. trace의 중요한 질문들

trace를 읽을 때는 아래 순서를 보면 좋다.

1. considered plans
2. cost comparison
3. chosen plan
4. rejected reason

이 순서가 안 보이면 비용 모델을 놓치기 쉽다.

### 3. trace는 통계와 이어진다

trace는 결국 통계를 바탕으로 움직인다.

- cardinality 추정
- index selectivity
- fanout 계산
- join order 선택

통계가 틀리면 trace의 논리도 같이 흐려진다.

### 4. trace가 특히 유용한 경우

- skip scan이 왜 안 됐는지
- index_merge가 왜 탈락했는지
- semijoin 전략이 왜 바뀌었는지
- 정렬 대신 다른 경로가 선택된 이유

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `optimizer trace`
- `trace reading`
- `considered_execution_plans`
- `chosen plan`
- `range analysis`
- `why this plan`

## 실전 시나리오

### 시나리오 1. EXPLAIN은 이상한데 이유를 모르겠다

optimizer trace를 보면 어떤 후보가 고려됐는지, 왜 탈락했는지 볼 수 있다.  
이걸 통해 plan regression의 원인을 좁힐 수 있다.

### 시나리오 2. skip scan이 생각보다 안 나온다

trace에서 low cardinality가 충분한지, 비용상 이득이 있었는지 볼 수 있다.  
인덱스 문제인지 통계 문제인지 구분하는 데 좋다.

### 시나리오 3. semijoin 전략이 왜 바뀌었는지 알고 싶다

trace는 semi-join 변환과 전략 선택 과정을 보여준다.  
이걸 보면 쿼리 재작성의 방향을 정하기 쉽다.

## 코드로 보기

### trace 활성화

```sql
SET optimizer_trace='enabled=on';
SET optimizer_trace_max_mem_size=1048576;
```

### 쿼리 실행

```sql
SELECT id, status
FROM orders
WHERE user_id = 1001
  AND status = 'PAID';
```

### trace 확인

```sql
SELECT TRACE
FROM information_schema.optimizer_trace\G
```

### EXPLAIN과 함께 비교

```sql
EXPLAIN
SELECT id, status
FROM orders
WHERE user_id = 1001
  AND status = 'PAID';
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| EXPLAIN만 사용 | 간단하다 | 왜를 알기 어렵다 | 기본 점검 |
| optimizer trace 읽기 | 결정 과정을 볼 수 있다 | 해석이 어렵다 | plan 이상 원인 분석 |
| 힌트로 강제 | 응급 처치가 가능하다 | 근본 원인을 가릴 수 있다 | 임시 대응 |

핵심은 optimizer trace를 "복잡한 로그"로 보지 말고, **옵티마이저의 내부 판단 근거**로 보는 것이다.

## 꼬리질문

> Q: EXPLAIN과 optimizer trace의 차이는 무엇인가요?
> 의도: 결과와 의사결정 과정을 구분하는지 확인
> 핵심: EXPLAIN은 결과, trace는 그 결과에 이르는 이유다

> Q: trace에서 무엇을 먼저 봐야 하나요?
> 의도: 고려된 plan과 선택 이유를 읽는지 확인
> 핵심: considered plans와 chosen plan이다

> Q: trace가 이상할 때 무엇을 의심하나요?
> 의도: 통계와 비용 모델의 연결을 아는지 확인
> 핵심: 통계, cardinality, selectivity를 의심한다

## 한 줄 정리

optimizer trace는 실행 계획의 결과가 아니라 그 계획을 고르기까지의 비용 계산과 탈락 이유를 읽는 도구다.

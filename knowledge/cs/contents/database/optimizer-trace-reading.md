# Optimizer Trace Reading

> 한 줄 요약: optimizer trace는 "왜 이 실행 계획을 골랐는가"를 보여주는 내부 메모라서, EXPLAIN보다 한 단계 더 깊게 비용 모델을 읽을 수 있게 해 준다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: optimizer trace, trace reading, cost model, considered_execution_plans, chosen plan, range analysis, why this plan, optimizer decision

## 핵심 개념

- 관련 문서:
  - [Optimizer Switch Knobs and Plan Stability](./optimizer-switch-plan-stability-invisible-indexes.md)
  - [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)
  - [MySQL Optimizer Hints and Index Merge](./mysql-optimizer-hints-index-merge.md)
  - [Index Skip Scan Behavior](./index-skip-scan-behavior.md)

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

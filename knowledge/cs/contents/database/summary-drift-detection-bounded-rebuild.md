---
schema_version: 3
title: Summary Drift Detection, Invalidation, and Bounded Rebuild
concept_id: database/summary-drift-detection-bounded-rebuild
canonical: false
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- projection-drift-repair-scope
- bounded-rebuild-over-full-rebuild
- freshness-contract-missing
aliases:
- summary drift detection
- bounded rebuild
- summary invalidation
- stale aggregate repair
- projection drift
- freshness contract
- summary table drift
- partial rebuild scope
- 왜 요약 테이블 값이 원본과 달라요
symptoms:
- 요약 테이블 값이 원본 테이블과 안 맞아요
- 전체 rebuild 말고 일부 bucket만 다시 계산하고 싶어요
- late event나 누락 이벤트 때문에 어디까지 다시 돌려야 할지 모르겠어요
intents:
- deep_dive
- troubleshooting
prerequisites:
- database/incremental-summary-table-refresh-watermark
- database/cdc-gap-repair-reconciliation-playbook
- database/normalization-denormalization-tradeoffs
next_docs:
- database/cdc-replay-verification-idempotency-runbook
- database/online-backfill-consistency
- database/replica-lag-observability-routing-slo
linked_paths:
- contents/database/incremental-summary-table-refresh-watermark.md
- contents/database/cdc-gap-repair-reconciliation-playbook.md
- contents/database/replica-lag-observability-routing-slo.md
- contents/database/online-backfill-consistency.md
- contents/database/normalization-denormalization-tradeoffs.md
- contents/design-pattern/projection-freshness-slo-pattern.md
- contents/system-design/projection-applied-watermark-basics.md
confusable_with:
- database/incremental-summary-table-refresh-watermark
- database/cdc-gap-repair-reconciliation-playbook
forbidden_neighbors:
- contents/database/normalization-denormalization-tradeoffs.md
expected_queries:
- summary table 값이 원본과 달라질 때 drift를 어떻게 탐지해?
- full rebuild 말고 일부 bucket만 다시 계산하는 기준이 뭐야?
- summary invalidation과 bounded rebuild를 같이 설계하는 이유가 궁금해
- stale aggregate를 운영 중에 안전하게 복구하는 흐름을 알고 싶어
contextual_chunk_prefix: |
  이 문서는 summary table이 refresh는 돌지만 값이 원본과 어긋나는 상황에서,
  drift detection과 invalidation 그리고 bounded rebuild 범위를 어떻게 설계해야
  하는지 설명하는 deep_dive다. summary drift, stale aggregate, bounded
  rebuild, bucket invalidation, projection drift, why summary value differs
  from source 같은 운영 질문을 부분 재계산과 freshness contract 관점으로 묶는다.
---

# Summary Drift Detection, Invalidation, and Bounded Rebuild

> 한 줄 요약: summary table은 refresh만 잘 돌린다고 안전하지 않고, 원본과 어긋난 drift를 어떻게 탐지하고 어느 범위만 다시 계산할지 준비돼 있어야 운영이 가능하다.

**난이도: 🔴 Advanced**

관련 문서:

- [Incremental Summary Table Refresh and Watermark Discipline](./incremental-summary-table-refresh-watermark.md)
- [정규화와 반정규화 트레이드오프](./normalization-denormalization-tradeoffs.md)
- [CDC Gap Repair, Reconciliation, and Rebuild Boundaries](./cdc-gap-repair-reconciliation-playbook.md)
- [Replica Lag Observability와 Routing SLO](./replica-lag-observability-routing-slo.md)
- [Online Backfill Consistency와 워터마크 전략](./online-backfill-consistency.md)
- [Projection Freshness SLO Pattern](../design-pattern/projection-freshness-slo-pattern.md)
- [Projection Applied Watermark Basics](../system-design/projection-applied-watermark-basics.md)

retrieval-anchor-keywords: summary drift detection, bounded rebuild, bucket invalidation, summary reconciliation, stale aggregate repair, projection drift, freshness contract, rebuild scope, summary drift monitor, summary drift alarm, 요약 테이블 값이 원본과 달라요, 왜 summary 값이 계속 어긋나요, 일부 bucket만 다시 계산, rebuild 범위 어디까지

## 핵심 개념

summary table은 증분 refresh가 잘 돌아도 다음 이유로 틀어질 수 있다.

- late event
- 중복 이벤트
- 역보정 누락
- 수동 데이터 수정
- CDC gap
- 배포 버그

즉 summary 운영의 핵심은 refresh 그 자체보다, **drift를 발견하고 bounded rebuild로 고치는 능력**이다.

중요한 질문:

- summary가 틀렸는지 어떻게 감지하는가
- 전체 rebuild 대신 어느 bucket만 invalidation 할 수 있는가
- rebuild 중에도 사용자에게 어떤 freshness 계약을 줄 것인가

## 깊이 들어가기

### 1. drift는 조용히 쌓이기 때문에 별도 검증 루프가 필요하다

많은 팀이 refresh checkpoint가 움직이면 summary가 건강하다고 생각한다.  
하지만 checkpoint는 "파이프라인이 돌았다"는 뜻일 뿐, 결과가 맞다는 보장은 아니다.

그래서 별도 drift detection loop가 필요하다.

- source count와 summary count 비교
- 특정 bucket의 aggregate checksum 비교
- 표본 샘플 검증
- business invariant 검증

즉 refresh observability와 correctness observability는 다른 층위다.

### 2. invalidation 단위는 bucket 또는 aggregate scope로 미리 정해야 한다

bounded rebuild를 하려면 먼저 rebuild unit이 정의돼 있어야 한다.

예:

- 일별 매출 summary는 `order_date`
- tenant별 사용량은 `(tenant_id, month)`
- 상품별 재고 projection은 `sku_id`

이 단위가 있어야:

- drift 발견 시 전체를 날리지 않고
- 해당 범위만 stale 처리하고
- source recompute를 적용할 수 있다

즉 summary schema는 조회용 컬럼만이 아니라 **repair scope를 표현하는 컬럼**도 가져야 한다.

### 3. rebuild는 "다시 계산"만이 아니라 "old result를 어떻게 대체할지" 문제다

bounded rebuild 방식은 보통 셋 중 하나다.

- delete then insert
- upsert overwrite
- shadow bucket build 후 atomic swap

선택 기준:

- 읽기 중간에 비어 보여도 되는가
- rebuild가 오래 걸리는가
- partial result 노출을 허용하는가

읽기 가용성이 중요하면 shadow build 후 swap이 더 안전하다.

### 4. drift detection과 freshness contract를 함께 노출해야 한다

summary가 stale할 수 있다는 사실을 시스템이 숨기면 운영 판단이 틀어진다.

권장 메타데이터:

- last successful refresh time
- last verified time
- drift suspected flag
- rebuild in progress flag

이렇게 해야 사용자나 운영자가 "이 수치는 최신인가, 검증됐는가, 지금 재구성 중인가"를 알 수 있다.

### 5. 수동 수정과 backfill은 drift의 흔한 원인이다

운영에서 의외로 많은 drift는 시스템 버그보다:

- 운영 SQL 직접 수정
- historical backfill
- migration 스크립트

에서 생긴다.

그래서 summary를 쓰는 시스템에서는 manual change가 발생할 때:

- 영향 scope invalidation
- rebuild job enqueue
- verification afterwards

를 같이 자동화하는 편이 안전하다.

### 6. bounded rebuild가 없으면 결국 full rebuild만 남는다

full rebuild는 단순하고 매력적이지만, 데이터가 커질수록 다음 문제가 생긴다.

- 오래 걸린다
- resource spike가 크다
- freshness 공백이 길어진다
- 장애 시 반복 수행이 어렵다

그래서 summary를 오래 운영하려면 처음부터 "부분 재계산"을 1급 기능으로 봐야 한다.

## 실전 시나리오

### 시나리오 1. 하루 매출 대시보드가 특정 날짜만 틀림

전체 refresh는 정상인데 환불 이벤트 일부가 누락됐다.

좋은 대응:

- 해당 날짜 bucket invalidation
- source of truth 재집계
- 검증 후 bucket overwrite

### 시나리오 2. 특정 테넌트 월간 사용량만 계속 어긋남

tenant-specific migration 이후 그 고객 데이터만 drift가 난다.

이때는 `(tenant_id, month)` 범위를 repair unit으로 갖고 있어야 전체 시스템을 흔들지 않는다.

### 시나리오 3. 운영자가 과거 주문 상태를 직접 수정함

source row만 수정하고 summary invalidation을 안 걸면 drift가 남는다.

교훈:

- 수동 수정은 summary rebuild trigger와 묶어야 한다
- backfill tooling이 summary invalidation을 자동 수행해야 한다

## 코드로 보기

```sql
CREATE TABLE summary_rebuild_scope (
  scope_id BIGINT PRIMARY KEY,
  summary_name VARCHAR(100) NOT NULL,
  scope_key VARCHAR(255) NOT NULL,
  rebuild_status VARCHAR(20) NOT NULL,
  requested_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP NULL
);
```

```sql
CREATE TABLE summary_health (
  summary_name VARCHAR(100) PRIMARY KEY,
  last_refreshed_at TIMESTAMP NOT NULL,
  last_verified_at TIMESTAMP NOT NULL,
  drift_suspected BOOLEAN NOT NULL,
  rebuild_in_progress BOOLEAN NOT NULL
);
```

```java
if (driftDetector.suspects(summaryName, scopeKey)) {
    rebuildQueue.enqueue(summaryName, scopeKey);
}
```

핵심은 drift를 발견했을 때 사람 손으로 전체 rebuild를 고민하는 게 아니라, scope 단위 invalidation과 rebuild를 기계적으로 실행할 수 있게 만드는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| full rebuild only | 구현이 단순하다 | 큰 데이터에서 너무 무겁다 | 초기 단계 |
| bounded rebuild | blast radius가 작고 빠르다 | scope 설계가 필요하다 | 대부분의 운영 summary |
| shadow rebuild + swap | partial result 노출을 줄인다 | 구현이 더 복잡하다 | 읽기 가용성이 중요할 때 |
| drift verification loop | correctness를 지속 확인한다 | 추가 계산 비용이 든다 | 중요한 재무/사용량 지표 |

## 꼬리질문

> Q: refresh checkpoint가 움직이면 summary가 맞다고 볼 수 있나요?
> 의도: pipeline health와 correctness를 구분하는지 확인
> 핵심: 아니다. drift detection과 source-to-summary verification이 별도로 필요하다

> Q: bounded rebuild를 하려면 무엇을 먼저 설계해야 하나요?
> 의도: repair scope 관점을 이해하는지 확인
> 핵심: bucket이나 aggregate scope 같은 rebuild unit이 summary schema에 드러나 있어야 한다

> Q: drift를 발견했을 때 왜 full rebuild보다 부분 rebuild가 좋은가요?
> 의도: 운영 blast radius 감각 확인
> 핵심: resource spike와 freshness 공백을 줄이고 검증 범위를 좁힐 수 있기 때문이다

## 한 줄 정리

summary 운영의 완성도는 증분 refresh 속도보다, drift를 검출하고 scope 단위 invalidation·rebuild·verification으로 빠르게 복구할 수 있는지에 달려 있다.

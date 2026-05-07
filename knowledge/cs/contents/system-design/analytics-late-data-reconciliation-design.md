---
schema_version: 3
title: Analytics Late Data Reconciliation 설계
concept_id: system-design/analytics-late-data-reconciliation-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- analytics late data reconciliation
- late arrival analytics
- event time correction
- watermark reconciliation
aliases:
- analytics late data reconciliation
- late arrival analytics
- event time correction
- watermark reconciliation
- backfill aggregate correction
- late event budget
- restatement window
- analytics correction
- delayed event handling
- metric restatement
- dashboard restatement
- alert reevaluation
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/streaming-analytics-pipeline-design.md
- contents/system-design/reconciliation-window-cutoff-control-design.md
- contents/system-design/historical-backfill-replay-platform-design.md
- contents/system-design/stateful-stream-processor-state-store-checkpoint-recovery-design.md
- contents/system-design/metrics-pipeline-tsdb-design.md
- contents/system-design/consistency-repair-anti-entropy-platform-design.md
- contents/system-design/dashboard-restatement-ux-design.md
- contents/system-design/alert-reevaluation-correction-design.md
- contents/system-design/audit-log-pipeline-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Analytics Late Data Reconciliation 설계 설계 핵심을 설명해줘
- analytics late data reconciliation가 왜 필요한지 알려줘
- Analytics Late Data Reconciliation 설계 실무 트레이드오프는 뭐야?
- analytics late data reconciliation 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Analytics Late Data Reconciliation 설계를 다루는 deep_dive 문서다. analytics late data reconciliation 설계는 event time 기준 집계에 뒤늦게 도착한 이벤트와 재처리 결과를 어떻게 반영하고, 언제 correction으로 넘기며, 어떤 창을 다시 계산할지 정하는 분석 운영 설계다. 검색 질의가 analytics late data reconciliation, late arrival analytics, event time correction, watermark reconciliation처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Analytics Late Data Reconciliation 설계

> 한 줄 요약: analytics late data reconciliation 설계는 event time 기준 집계에 뒤늦게 도착한 이벤트와 재처리 결과를 어떻게 반영하고, 언제 correction으로 넘기며, 어떤 창을 다시 계산할지 정하는 분석 운영 설계다.

retrieval-anchor-keywords: analytics late data reconciliation, late arrival analytics, event time correction, watermark reconciliation, backfill aggregate correction, late event budget, restatement window, analytics correction, delayed event handling, metric restatement, dashboard restatement, alert reevaluation, correction campaign, restatement contract, post-backfill correction, sink invalidation graph

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Streaming Analytics Pipeline 설계](./streaming-analytics-pipeline-design.md)
> - [Reconciliation Window / Cutoff Control 설계](./reconciliation-window-cutoff-control-design.md)
> - [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)
> - [Stateful Stream Processor State Store / Checkpoint Recovery 설계](./stateful-stream-processor-state-store-checkpoint-recovery-design.md)
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
> - [Consistency Repair / Anti-Entropy Platform 설계](./consistency-repair-anti-entropy-platform-design.md)
> - [Dashboard Restatement UX 설계](./dashboard-restatement-ux-design.md)
> - [Alert Re-Evaluation / Correction 설계](./alert-reevaluation-correction-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)

## 핵심 개념

analytics에서는 늦게 도착한 데이터가 정상이다.
문제는 "늦게 왔다"가 아니라 그것을 어디까지 본 계산에 반영할지다.

- 이미 대시보드에 노출된 숫자를 덮어쓸 것인가
- 일정 시간 이후엔 correction으로 따로 반영할 것인가
- 어느 창까지 다시 계산할 것인가
- restatement를 사용자에게 어떻게 설명할 것인가

즉, late data 처리의 본질은 기술적 watermark가 아니라 **분석 숫자의 확정성과 correction 정책을 정하는 것**이다.

## 깊이 들어가기

### 1. 왜 analytics late data가 어려운가

실전 late data 원인:

- mobile offline sync
- client retry / batch upload
- queue backlog
- CDC 지연
- replay / repair campaign

이 데이터를 무시하면 정확도가 떨어지고,
전부 즉시 덮어쓰면 운영 숫자가 계속 흔들린다.

### 2. Capacity Estimation

예:

- 하루 이벤트 100억 건
- p95 lateness 5분
- p99 lateness 2시간
- 월말 replay 후 특정 창 restatement 필요

이때 봐야 할 숫자:

- lateness distribution
- restatement frequency
- recompute cost
- dashboard correction lag
- user-visible metric drift

평균 lateness보다 tail과 restatement 비용이 더 중요하다.

### 3. Window policy

보통 다음을 명시한다.

- mutable window
- soft closed window
- finalized window
- correction-only after finalize

예:

- 최근 15분은 자유롭게 갱신
- 24시간까지는 correction 표시와 함께 갱신
- 그 이후는 restatement batch로만 반영

즉, 기술적 처리와 사용자-facing policy를 분리해야 한다.

### 4. Watermark와 restatement

watermark는 "이 시간보다 늦은 데이터는 드물다"는 기술 신호다.
하지만 analytics에서는 그 이후에도 correction이 올 수 있다.

대표 선택지:

- late event 즉시 merge
- side output으로 correction stream 생성
- closed window는 restatement batch로 재계산
- user-facing dashboard에 correction badge 표시

### 5. Aggregate correction granularity

무조건 전체 재계산할 필요는 없다.

선택지:

- bucket-level recompute
- tenant-level recompute
- metric-level correction entry
- full period rebuild

핵심은 correction cost와 사용자 설명 가능성의 균형이다.

### 6. Reconciliation with dashboards and reports

analytics late data는 downstream에도 영향을 준다.

- dashboard cache
- scheduled report
- alert threshold
- billing / finance-adjacent derived metric

따라서 correction이 도착했을 때 어떤 sink를 다시 계산할지 dependency map이 있어야 한다.

### 7. Observability

운영자는 다음을 알아야 한다.

- 현재 lateness tail이 얼마나 되는가
- 어떤 window가 아직 mutable한가
- 어떤 metric이 restated 되었는가
- replay로 인한 correction인지 자연 late arrival인지
- correction이 사용자-facing 숫자에 얼마나 영향을 주는가

late data는 숨기는 것보다 설명 가능한 것이 중요하다.

### 8. Backfill 이후 correction contract

대규모 backfill이나 replay가 끝났다고 해서 운영이 끝난 것은 아니다.
중요한 것은 재계산 결과를 downstream이 같은 의미로 해석할 수 있게 만드는 공통 contract다.

보통 correction envelope에 넣어야 할 정보:

- correction campaign id
- metric version / previous version
- affected range, bucket, tenant, dimension
- provenance와 root cause
- diff magnitude와 severity
- 영향을 받는 sink 목록과 권장 후속 작업

이 계약이 없으면 dashboard는 배지를 붙이고 alert 시스템은 아무 일도 하지 않는 식의 불일치가 생긴다.

### 9. Sink fan-out과 invalidation 순서

late data correction은 aggregate recompute만의 문제가 아니다.
보통은 다음 순서로 fan-out을 설계한다.

1. authoritative aggregate와 metric version을 먼저 확정한다
2. dashboard cache, saved extract, scheduled report snapshot을 무효화한다
3. restatement UX 계층에 correction summary를 publish한다
4. alert rule dependency index를 통해 re-evaluation job을 enqueue한다
5. audit trail에 correction campaign과 downstream 처리 상태를 남긴다

순서가 뒤집히면 "대시보드는 고쳐졌는데 alert는 옛 기준" 같은 어색한 상태가 길게 남는다.

### 10. Publish threshold와 사용자-facing SLA

모든 correction을 같은 속도로 공개하면 운영자도 사용자도 혼란스럽다.

대표 정책:

- mutable window + 작은 diff는 자동 publish
- finalized window + 큰 diff는 review 후 publish
- finance-adjacent metric은 approval과 공지를 요구
- backfill 완료와 사용자-facing restatement 완료를 별도 SLA로 관리

핵심은 "재계산 완료"와 "안전하게 설명 가능한 상태"를 구분하는 것이다.
실전에서는 다음 SLA를 따로 두는 편이 좋다.

- correction visibility SLA
- report invalidation SLA
- alert re-evaluation SLA
- finalized window correction approval SLA

## 실전 시나리오

### 시나리오 1: 모바일 이벤트 지연 업로드

문제:

- 하루 뒤에 어제 이벤트가 대량 업로드된다

해결:

- 최근 창은 직접 correction한다
- 오래된 창은 restatement batch로 따로 처리한다
- dashboard에는 correction marker를 남긴다

### 시나리오 2: streaming job checkpoint 복구 후 replay

문제:

- 특정 시간대 aggregate가 뒤늦게 다시 계산된다

해결:

- 영향받은 buckets만 recompute한다
- recompute provenance를 기록한다
- alert와 report sink를 함께 다시 계산한다

### 시나리오 3: product metric 공식 변경

문제:

- 과거 데이터도 새 공식으로 다시 봐야 한다

해결:

- live window와 historical restatement를 분리한다
- old/new metric을 일정 기간 함께 노출한다
- large restatement는 승인과 공지를 포함한다

### 시나리오 4: backfill 이후 대시보드와 alert 동시 정렬

문제:

- source bug 수정 후 지난 7일 aggregate를 backfill했더니 executive dashboard, scheduled report, alert history가 서로 다른 버전을 보고 있다

해결:

- correction campaign id 기준으로 sink dependency graph를 따라 invalidation을 건다
- dashboard에는 restatement banner와 diff를, report에는 superseded snapshot 표시를 남긴다
- alert는 retrospective re-evaluation queue로 보내고 paging 채널은 다시 울리지 않는다

## 코드로 보기

```pseudo
function handleLateEvent(event):
  window = assignEventTimeWindow(event)
  if window.isMutable():
    aggregateStore.merge(window, event)
  elif policy.allowCorrection(window):
    correctionStream.emit(window, event)
  else:
    restatementQueue.enqueue(window, event)

function reconcileWindow(window):
  diff = recompute(window) - currentAggregate(window)
  if abs(diff) > threshold:
    publishRestatement(window, diff)

function publishRestatement(window, diff):
  correction = {
    correctionId: newId(),
    metricVersion: versionStore.next(window),
    affectedRange: window.range,
    diffMagnitude: diff,
    downstream: ["dashboard", "report", "alert"],
    provenance: currentCause()
  }
  correctionBus.publish(correction)
```

```java
public CorrectionDecision decide(WindowKey windowKey, Event event) {
    return lateDataPolicy.evaluate(windowKey, event.eventTime(), watermarkState.current());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Ignore late data | 단순하다 | 정확도가 떨어진다 | low-value telemetry |
| Always restate live | 정확도가 높다 | 숫자가 흔들린다 | 내부 탐색용 analytics |
| Mutable window + correction | 균형이 좋다 | 정책이 복잡하다 | 대부분의 production analytics |
| Full recompute | 이해가 쉽다 | 비용이 크다 | 드문 대형 correction |

핵심은 analytics late data reconciliation이 watermark 설정값이 아니라 **언제까지 숫자를 수정하고, 그 이후엔 어떤 correction 경로를 쓸지 정하는 분석 운영 설계**라는 점이다.

## 꼬리질문

> Q: watermark를 충분히 늦추면 late data 문제는 끝나나요?
> 의도: 기술 경계와 운영 정책 차이 이해 확인
> 핵심: 아니다. 늦게 잡을수록 freshness가 떨어지고, 아주 늦은 데이터는 여전히 correction 정책이 필요하다.

> Q: analytics 숫자는 계속 덮어써도 되지 않나요?
> 의도: 사용자-facing stability 감각 확인
> 핵심: 내부 분석은 가능할 수 있지만, 공유 대시보드나 보고서는 확정성과 설명 가능성이 더 중요할 수 있다.

> Q: replay와 natural late arrival를 왜 구분하나요?
> 의도: provenance 이해 확인
> 핵심: 운영 원인과 사용자 설명, approval 경계가 다르기 때문이다.

> Q: 어떤 단위로 correction할지 어떻게 정하나요?
> 의도: granularity trade-off 이해 확인
> 핵심: recompute 비용, 사용자 의미, dependency sink 수를 함께 보고 bucket/metric/period 단위를 정한다.

## 한 줄 정리

Analytics late data reconciliation 설계는 늦게 도착한 이벤트와 replay 결과를 어떤 창까지 반영하고 그 이후엔 어떤 correction 경로로 넘길지 정해, 분석 숫자의 freshness와 확정성을 함께 관리하는 운영 설계다.

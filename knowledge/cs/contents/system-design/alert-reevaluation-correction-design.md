---
schema_version: 3
title: Alert Re-Evaluation / Correction 설계
concept_id: system-design/alert-reevaluation-correction-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- alert re-evaluation
- corrected alert state
- alert restatement
- replayed metric alert
aliases:
- alert re-evaluation
- corrected alert state
- alert restatement
- replayed metric alert
- false positive correction
- false negative recovery
- alert provenance
- alert recompute window
- corrected incident signal
- post-hoc alert evaluation
- alert reevaluation after backfill
- retrospective incident annotation
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/analytics-late-data-reconciliation-design.md
- contents/system-design/metrics-pipeline-tsdb-design.md
- contents/system-design/dashboard-restatement-ux-design.md
- contents/system-design/failure-injection-resilience-validation-platform-design.md
- contents/system-design/streaming-analytics-pipeline-design.md
- contents/system-design/audit-log-pipeline-design.md
- contents/system-design/historical-backfill-replay-platform-design.md
- contents/system-design/replay-repair-orchestration-control-plane-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Alert Re-Evaluation / Correction 설계 설계 핵심을 설명해줘
- alert re-evaluation가 왜 필요한지 알려줘
- Alert Re-Evaluation / Correction 설계 실무 트레이드오프는 뭐야?
- alert re-evaluation 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Alert Re-Evaluation / Correction 설계를 다루는 deep_dive 문서다. alert re-evaluation과 correction 설계는 late data, replay, metric restatement 이후 과거 alert 판단을 어떻게 다시 계산하고, false positive/false negative를 어떤 정책으로 정정할지 정하는 관측성 운영 설계다. 검색 질의가 alert re-evaluation, corrected alert state, alert restatement, replayed metric alert처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Alert Re-Evaluation / Correction 설계

> 한 줄 요약: alert re-evaluation과 correction 설계는 late data, replay, metric restatement 이후 과거 alert 판단을 어떻게 다시 계산하고, false positive/false negative를 어떤 정책으로 정정할지 정하는 관측성 운영 설계다.

retrieval-anchor-keywords: alert re-evaluation, corrected alert state, alert restatement, replayed metric alert, false positive correction, false negative recovery, alert provenance, alert recompute window, corrected incident signal, post-hoc alert evaluation, alert reevaluation after backfill, retrospective incident annotation, backfill alert correction, rule dependency index

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Analytics Late Data Reconciliation 설계](./analytics-late-data-reconciliation-design.md)
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
> - [Dashboard Restatement UX 설계](./dashboard-restatement-ux-design.md)
> - [Failure Injection / Resilience Validation Platform 설계](./failure-injection-resilience-validation-platform-design.md)
> - [Streaming Analytics Pipeline 설계](./streaming-analytics-pipeline-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)
> - [Replay / Repair Orchestration Control Plane 설계](./replay-repair-orchestration-control-plane-design.md)

## 핵심 개념

alert는 순간의 판단이지만, 입력 데이터는 나중에 수정될 수 있다.

- late metric이 도착해 실제론 alert 조건이 아니었을 수 있다
- replay 후 당시에는 못 울렸던 alert가 사실상 있었을 수 있다
- restated aggregate로 incident severity가 달라질 수 있다

그래서 일부 시스템은 alert를 "실시간 판단"과 "사후 재평가"로 나눠 본다.

즉, alert re-evaluation의 목적은 과거 알림을 뒤집는 것이 아니라 **운영 판단의 정확성과 학습 데이터를 교정하는 것**이다.

## 깊이 들어가기

### 1. 왜 재평가가 필요한가

실시간 alert는 freshness를 위해 근사 판단을 한다.
하지만 나중에 correction이 오면 다음 문제가 생긴다.

- false positive가 많이 쌓임
- false negative가 숨겨짐
- SLO burn report와 incident log가 안 맞음
- model / threshold 개선용 데이터가 오염됨

즉, alert re-evaluation은 실시간 on-call보다 사후 학습과 감사에 더 중요할 수 있다.

### 2. Capacity Estimation

예:

- 활성 alert rule 5천 개
- 분당 평가 수십만
- correction 대상 metric windows 일일 수백 개
- re-evaluation retention 30일

이때 봐야 할 숫자:

- reevaluation job count
- impacted alert rule 수
- alert provenance storage
- corrected incident ratio
- reevaluation latency

문제는 실시간 알림 수보다 어떤 rule들이 correction 영향을 받는지 추적하는 metadata다.

### 3. Re-evaluation policy

대표 정책:

- no reevaluation, only annotate
- recompute and mark corrected
- recompute and generate retrospective signal
- recompute only for audit / model training

실전에서는 실시간 paging과 retrospective 분석을 분리하는 편이 많다.

### 4. False positive vs false negative handling

둘의 의미가 다르다.

- false positive correction: "당시엔 울렸지만 corrected data로 보면 과했다"
- false negative correction: "당시엔 안 울렸지만 사실 threshold를 넘었다"

운영적으로는 전자가 noise 분석에 유용하고,
후자는 detection gap 개선에 더 중요하다.

### 5. Alert provenance

좋은 시스템은 alert 판단의 근거를 남긴다.

- evaluation time
- source metric version
- threshold / rule version
- window
- correction source

이게 있어야 "왜 이 alert를 corrected false positive로 분류했는가"를 설명할 수 있다.

### 6. Re-open vs annotate

사후 재평가로 과거 incident를 다시 여는 것은 매우 민감하다.
선택지는 보통:

- incident는 닫고 annotation만 추가
- retrospective issue 생성
- postmortem dataset만 수정
- severe missed alert만 reopen 후보로 별도 분리

즉, 운영 UX와 학습 UX를 분리해야 한다.

### 7. Feedback into rule tuning

re-evaluation의 큰 가치는 운영 품질 개선이다.

- noisy rule 식별
- missing detector 찾기
- threshold retune
- data freshness budget 재조정

corrected alert history는 rule governance의 입력이 된다.

### 8. Backfill-triggered re-evaluation flow

대형 correction에서는 "어떤 alert를 다시 볼 것인가"가 핵심이다.
보통은 correction campaign이 직접 모든 rule을 훑지 않고 dependency index를 통해 영향을 좁힌다.

흐름 예시:

1. backfill이 correction campaign과 metric version을 publish한다
2. rule dependency index가 영향받는 rule, tenant, time window를 찾는다
3. 당시 rule version과 현재 rule version 차이를 기록한다
4. retrospective engine이 corrected metric으로 재평가한다
5. 결과를 alert history, governance dashboard, postmortem dataset에 fan-out한다

이 구조가 없으면 backfill 때마다 모든 alert를 전수 재평가하거나, 반대로 아무 것도 교정하지 못한다.

### 9. Alert state model after correction

사후 재평가는 단순히 fired / not fired로 끝나지 않는다.

대표 상태:

- `unchanged`: corrected data 기준으로도 동일한 판단
- `corrected_false_positive`: 실시간에는 울렸지만 수정 후 정상
- `missed_live_found_retrospectively`: 실시간에는 조용했지만 수정 후 threshold 초과
- `non_comparable`: rule version이나 aggregation contract가 바뀌어 단순 비교가 불가능

특히 `non_comparable`을 두지 않으면 data correction과 rule change를 잘못 섞어 해석하게 된다.

### 10. Operator UX 분리

backfill 이후 alert correction을 on-call 화면에 그대로 섞으면 operator가 혼란스러워진다.
그래서 보통 세 화면을 분리한다.

- 실시간 incident console: 지금 대응해야 하는 것만 표시
- retrospective correction view: corrected false positive와 missed detection 분석
- rule governance dashboard: noisy rule, freshness budget, reevaluation backlog 추적

핵심은 retrospective 결과가 현재 paging urgency처럼 보이지 않게 만드는 것이다.

### 11. Safety rails after backfill

alert 재평가는 신중하게 제한해야 한다.

- dedup key를 `correction_campaign_id + rule_id + window`로 둔다
- retrospective path는 기본적으로 paging integration을 다시 호출하지 않는다
- reopen은 severity, duration, blast radius 기준을 모두 넘을 때만 허용한다
- backfill 직후 reevaluation burst가 live evaluation을 압박하지 않도록 별도 quota를 둔다

즉, "정확한 교정"보다 "운영 사고를 만들지 않는 교정"이 먼저다.

## 실전 시나리오

### 시나리오 1: late metric으로 false positive 정정

문제:

- 실시간에는 error budget burn이 높아 보였지만 correction 후 정상이다

해결:

- alert history에 corrected false positive 표시를 남긴다
- on-call 통계에서 noisy rule로 집계한다
- 당시 paging 자체는 유지하되 retrospective annotation을 추가한다

### 시나리오 2: replay 후 missed alert 발견

문제:

- replay된 metric을 보니 실제론 threshold 초과였다

해결:

- retrospective signal을 생성한다
- incident reopen 대신 detection gap issue로 연결한다
- rule와 freshness budget 조정 후보로 올린다

### 시나리오 3: executive SLO report와 alert history 불일치

문제:

- corrected metric 기준 SLO 위반인데 alert log는 조용했다

해결:

- alert provenance와 reevaluation 결과를 연결한다
- report에 corrected alert gap를 별도 표기한다
- policy상 실시간 alert와 retrospective 판정을 구분한다

### 시나리오 4: backfill 이후 retrospective only 경로

문제:

- telemetry backlog 해소 후 지난 이틀의 SLO burn이 재계산되었지만, 지금 시점에 paging을 다시 보내면 운영팀이 더 혼란스러워진다

해결:

- reevaluation 결과는 retrospective signal로만 기록한다
- severe missed case만 review queue로 보내고 incident reopen 여부는 사람이 결정한다
- dashboard와 report에는 "alert re-evaluated at" 메타데이터를 남긴다

## 코드로 보기

```pseudo
function reevaluate(window, correctedMetrics):
  affectedRules = ruleIndex.rulesFor(correctedMetrics)
  for rule in affectedRules:
    prior = alertHistory.lookup(rule, window)
    recomputed = engine.evaluate(rule, correctedMetrics, window)
    if recomputed != prior:
      alertCorrections.record(rule, window, prior, recomputed, mode="RETROSPECTIVE_ONLY")

function recordCorrection(rule, window, prior, recomputed):
  if policy.annotateOnly(rule):
    history.annotate(rule, window, recomputed)
  else:
    retrospectiveQueue.enqueue(rule, window, recomputed)
```

```java
public ReevaluationResult reevaluate(AlertRule rule, MetricWindow window) {
    MetricSlice corrected = correctedMetricStore.load(window);
    return alertEngine.evaluate(rule, corrected);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| No re-evaluation | 단순하다 | 품질 학습이 약하다 | low-stakes internal alerts |
| Annotate-only | 운영 혼란이 적다 | missed alert 교정은 약하다 | 대부분의 production |
| Full retrospective recompute | 학습 가치가 높다 | 비용과 UX 복잡도가 크다 | 중요한 SLO / platform alerts |
| Re-open incidents | 강한 교정이 가능하다 | 운영 혼란이 크다 | 매우 제한적 severe missed cases |

핵심은 alert re-evaluation이 과거 paging을 뒤엎는 기능이 아니라 **late/corrected data가 alert 품질에 미친 영향을 사후에 분석하고 교정하는 운영 설계**라는 점이다.

## 꼬리질문

> Q: alert는 실시간 대응용인데 사후 재평가가 왜 필요한가요?
> 의도: 대응과 학습 구분 확인
> 핵심: 대응은 실시간 판단으로 하고, 재평가는 noisy rule 개선과 missed detection 분석에 큰 가치를 준다.

> Q: false negative가 뒤늦게 발견되면 incident를 다시 열어야 하나요?
> 의도: reopen vs annotate 판단 이해 확인
> 핵심: 보통은 retrospective gap으로 다루고, 정말 중요한 경우만 별도 escalation 정책을 둔다.

> Q: corrected alert state가 operator를 더 헷갈리게 하지 않나요?
> 의도: UX 분리 필요성 확인
> 핵심: 그래서 실시간 alert UI와 retrospective correction UI를 분리하는 편이 많다.

> Q: reevaluation 대상 rule은 어떻게 찾나요?
> 의도: metadata와 dependency map 이해 확인
> 핵심: 어떤 metric/window를 쓰는 rule인지의 dependency index가 있어야 효율적으로 찾을 수 있다.

## 한 줄 정리

Alert re-evaluation / correction 설계는 late data와 replay로 바뀐 metric 기준으로 과거 alert 판단을 재평가해 noisy rule과 missed detection을 교정하는 관측성 운영 설계다.

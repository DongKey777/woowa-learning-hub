---
schema_version: 3
title: Projection Replay Observability and Alerting Pattern
concept_id: design-pattern/projection-replay-observability-alerting-pattern
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- projection-replay-observability
- verified-watermark-drift
- replay-alerting
aliases:
- projection replay observability
- replay alerting pattern
- replay dashboard
- replay gap count
- quarantine growth alert
- verified watermark drift
- last verified watermark drift
- attempted vs verified watermark
- retry budget burn
- replay false green
symptoms:
- projection replay dashboard가 progress percent만 보여 gap, quarantine, verified drift, retry storm이 false green 뒤에 숨는다
- attempted watermark가 target에 도달했다는 이유로 last verified watermark 정체와 partial apply 위험을 놓친다
- quarantine count만 보고 critical event share, ownerless quarantine, accepted skip 남용 여부를 보지 않는다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/projection-rebuild-backfill-cutover-pattern
- design-pattern/projection-rebuild-evidence-packet
- design-pattern/projection-rebuild-poison-event-replay-failure-handling
next_docs:
- design-pattern/projection-lag-budgeting-pattern
- design-pattern/projection-freshness-slo-pattern
- design-pattern/canary-promotion-thresholds-projection-cutover
linked_paths:
- contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md
- contents/design-pattern/projection-rebuild-evidence-packet.md
- contents/design-pattern/projection-rebuild-poison-event-replay-failure-handling.md
- contents/design-pattern/projection-lag-budgeting-pattern.md
- contents/design-pattern/projection-freshness-slo-pattern.md
- contents/design-pattern/read-model-cutover-guardrails.md
- contents/design-pattern/canary-promotion-thresholds-projection-cutover.md
- contents/design-pattern/strict-read-fallback-contracts.md
confusable_with:
- design-pattern/projection-rebuild-evidence-packet
- design-pattern/projection-rebuild-poison-event-replay-failure-handling
- design-pattern/projection-lag-budgeting-pattern
- design-pattern/projection-freshness-slo-pattern
forbidden_neighbors: []
expected_queries:
- Projection replay dashboard는 progress percent보다 replay gap, quarantine growth, verified watermark drift, retry budget burn을 왜 함께 봐야 해?
- attempted watermark와 last verified watermark를 분리하지 않으면 partial apply와 false green이 생기는 이유가 뭐야?
- quarantine alert는 count뿐 아니라 growth rate, critical event share, ownerless count를 왜 봐야 해?
- retry count가 많다는 것보다 retry budget burn 대비 verified progress가 없는 것이 더 위험한 이유가 뭐야?
- replay alert severity는 history backfill, tail catch-up, canary, rollback window 단계별로 왜 다르게 해석해야 해?
contextual_chunk_prefix: |
  이 문서는 Projection Replay Observability and Alerting Pattern playbook으로,
  progress percent 대신 replay gap, quarantine growth and criticality, last verified
  watermark drift, attempted-vs-verified divergence, retry budget burn and repeated fingerprint를
  dashboard와 alert contract로 묶어 projection cutover false green을 막는 방법을 설명한다.
---
# Projection Replay Observability and Alerting Pattern

> 한 줄 요약: projection replay/rebuild는 진행률 퍼센트보다 replay gap, quarantine 성장, last verified watermark drift, retry budget burn을 한 dashboard와 alert 계약으로 묶어야 false green 없이 cutover sign-off를 지킬 수 있다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Projection Rebuild Evidence Packet](./projection-rebuild-evidence-packet.md)
> - [Poison Event and Replay Failure Handling in Projection Rebuilds](./projection-rebuild-poison-event-replay-failure-handling.md)
> - [Projection Lag Budgeting Pattern](./projection-lag-budgeting-pattern.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)
> - [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)
> - [System Design: Historical Backfill / Replay Platform](../system-design/historical-backfill-replay-platform-design.md)
> - [System Design: Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)

retrieval-anchor-keywords: projection replay observability, replay alerting pattern, replay dashboard, replay gap count, replay gap dashboard, quarantine growth alert, quarantine slope, verified watermark drift, last verified watermark drift, attempted vs verified watermark, retry budget burn, repeated fingerprint alert, replay false green, cutover replay dashboard, replay signoff dashboard

---

## 핵심 개념

replay 운영에서 가장 위험한 순간은 "숫자는 좋아 보이는데 실제로는 아직 unsafe"인 false green이다.

- progress bar는 99%인데 shard gap이 남아 있음
- quarantine count는 작지만 핵심 상태 이벤트가 포함돼 있음
- attempted watermark는 전진했지만 verified watermark는 멈춰 있음
- retry는 많이 돌지만 실제 gap closure는 거의 없음

그래서 replay dashboard는 단순 진행률 보드가 아니라, 아래 네 질문에 동시에 답해야 한다.

1. 어디에 replay gap이 남아 있는가
2. quarantine가 통제 가능한 속도로 정리되고 있는가
3. 우리가 실제로 검증한 watermark가 움직이고 있는가
4. retry 예산을 태우는 만큼 verified progress가 나오고 있는가

이 네 축이 같이 보여야 cutover sign-off, rollback 보류, fix 우선순위가 흔들리지 않는다.

### Retrieval Anchors

- `projection replay observability`
- `replay gap count`
- `replay gap dashboard`
- `quarantine growth alert`
- `verified watermark drift`
- `last verified watermark drift`
- `attempted vs verified watermark`
- `retry budget burn`
- `same fingerprint retry storm`
- `replay false green`
- `cutover replay dashboard`

---

## 깊이 들어가기

### 1. replay dashboard는 progress board가 아니라 sign-off board여야 한다

운영 화면이 단순히 "몇 퍼센트 끝났는가"만 보여주면 sign-off에 필요한 정보가 빠진다.

| 질문 | 핵심 지표 | 왜 필요한가 |
|---|---|---|
| replay가 실제로 다 닫혔는가 | `open_gap_count`, `max_gap_age`, `affected_shard_count` | shard/range 누락을 progress 100% 뒤에 숨기지 않기 위해 |
| poison이 blast radius 안에 있는가 | `quarantine_open_count`, `quarantine_growth_rate`, `critical_event_share` | 적은 건수여도 중요한 상태 전이가 포함되면 cutover red이기 때문 |
| verified 상태가 전진하는가 | `last_verified_watermark`, `verified_drift_seconds`, `time_since_verified_advance` | attempted와 verified를 섞으면 partial apply를 놓치기 때문 |
| retry가 의미 있는가 | `retry_budget_burn_ratio`, `retries_per_verified_advance`, `repeated_fingerprint_count` | 같은 실패를 무한 반복하는지 판단하려면 필요 |

즉 replay 관측성은 status page가 아니라 approval 질문을 바로 읽게 하는 운영 패턴이다.

### 2. replay gap은 총량보다 분포와 정체 시간을 함께 봐야 한다

`open_gap_count`만 보고 있으면 gap이 작아지는지, 특정 shard에 고착되는지, strict path에 영향이 있는지 구분이 안 된다.

대시보드에는 최소한 다음 패널이 같이 있어야 한다.

| 패널 | 권장 표현 | 해석 포인트 |
|---|---|---|
| global gap scorecard | `open_gap_count`, `max_gap_age`, `largest_gap_range` | 전체 readiness가 녹색인지 빠르게 판단 |
| shard/range heatmap | shard별 gap 개수와 oldest gap age | hotspot shard와 stalled range 분리 |
| business impact split | strict path 연관 gap 수, low-risk gap 수 | 적은 gap이라도 핵심 경로면 우선순위 상향 |
| closure trend | 15분/1시간 gap closure slope | replay가 실제로 문제를 줄이는 중인지 확인 |

alert는 남은 gap의 절대 개수만 보지 않는 편이 좋다.

| Alert | trigger 예시 | 이유 |
|---|---|---|
| warning | `open_gap_count > 0`가 예상 윈도우보다 오래 지속 | 잡이 느린 것과 멈춘 것을 구분하기 위해 |
| critical | `open_gap_count` 증가 또는 `max_gap_age`가 reserve 초과 | partial replay failure가 퍼지고 있음을 의미 |
| cutover block | `history backfill complete=true`인데 gap이 남음 | sign-off packet의 false green 방지 |

핵심은 "gap이 있다"보다 **gap이 닫히는 속도가 허용치 안인가**를 보는 것이다.

### 3. quarantine는 절대치보다 성장률과 성격이 중요하다

quarantine가 3건뿐이어도 모두 핵심 상태 전이라면 위험하고, 30건이어도 deprecated feature면 영향이 좁을 수 있다.

그래서 quarantine 패널은 count 하나로 끝내면 안 된다.

| 지표 | 보는 질문 | 권장 분해 |
|---|---|---|
| `quarantine_open_count` | 지금 미해결 격리가 몇 건인가 | projection, shard, failure class |
| `quarantine_growth_rate` | 새 격리가 닫히는 속도보다 빠르게 늘어나는가 | 15분/1시간 slope |
| `critical_event_share` | 핵심 상태 전이 이벤트 비중이 높은가 | event type / strict-path 영향 여부 |
| `ownerless_quarantine_count` | 누가 처리할지 정해지지 않은 건이 있는가 | disposition owner 유무 |
| `accepted_skip_count` | 예외 승인이 이미 얼마나 쌓였는가 | skip-with-signoff 남용 방지 |

alert 예시는 다음처럼 두는 편이 안전하다.

| Alert | trigger 예시 | 운영 의미 |
|---|---|---|
| warning | `quarantine_growth_rate > quarantine_closure_rate` 30분 지속 | 운영 부채가 쌓이는 중 |
| critical | `critical_event_share > 0` 또는 ownerless quarantine 발생 | cutover red, 즉시 owner 지정 필요 |
| escalation | `accepted_skip_count`가 허용 한도 접근 | skip이 기본 경로로 변질되는 신호 |

즉 quarantine alert는 "건수가 많다"가 아니라 **격리가 통제되는가, 그리고 무엇을 격리했는가**를 보여야 한다.

### 4. attempted watermark와 last verified watermark를 반드시 분리해야 한다

replay 관측성에서 가장 자주 생기는 착시는 attempted watermark만 보고 "충분히 따라왔다"고 믿는 것이다.

하지만 partial apply, checkpoint write failure, shard-local ambiguity가 있으면 실제 sign-off 기준은 `last_verified_watermark`다.

대시보드에는 다음 세 선이 같이 보여야 한다.

| 선 | 의미 | 잘못 해석하면 생기는 문제 |
|---|---|---|
| `target_watermark` | 이번 시도에서 따라잡아야 할 기준점 | 목표가 바뀌었는데 drift가 줄어든 것처럼 보일 수 있음 |
| `last_attempted_watermark` | 시스템이 시도한 최전선 | 성공과 검증을 혼동하기 쉬움 |
| `last_verified_watermark` | 샘플 검증과 gap closure가 끝난 최전선 | 이것이 sign-off의 실제 기준 |

여기서 중요한 보조 지표는 다음이다.

- `verified_drift_seconds = target_watermark - last_verified_watermark`
- `attempted_vs_verified_gap = last_attempted_watermark - last_verified_watermark`
- `time_since_verified_advance`

alert도 verified 축으로 거는 편이 안전하다.

| Alert | trigger 예시 | 이유 |
|---|---|---|
| warning | attempted는 전진하지만 verified가 10분 이상 정체 | ambiguous checkpoint 또는 sample verification 병목 가능성 |
| critical | `verified_drift_seconds`가 cutover reserve 초과 | tail catch-up green으로 볼 수 없음 |
| cutover block | parity green처럼 보여도 verified drift가 red | sign-off packet 해석 충돌 방지 |

핵심은 "얼마나 멀리 시도했는가"가 아니라 **얼마나 멀리 증명했는가**다.

### 5. retry는 횟수보다 burn 효율로 봐야 한다

retry count가 많은 것 자체는 문제가 아닐 수 있다.  
문제는 retry가 verified progress 없이 예산만 태우는 경우다.

그래서 retry dashboard는 다음 둘을 함께 보여줘야 한다.

| 지표 | 의미 | 왜 필요한가 |
|---|---|---|
| `retry_budget_burn_ratio` | 허용 retry 예산 중 현재까지 소진 비율 | budget stop에 얼마나 가까운지 판단 |
| `retries_per_verified_advance` | verified watermark 1단위 전진에 필요한 retry 수 | retry 효율 저하 감지 |
| `same_fingerprint_retry_share` | 동일 error fingerprint 반복 비율 | deterministic failure를 transient처럼 처리하는지 확인 |
| `retry_without_progress_count` | verified advance 없이 끝난 retry loop 수 | noisy recovery와 stalled recovery 구분 |

alert는 "retry 많음"보다 "retry 대비 성과 없음"에 붙이는 편이 좋다.

| Alert | trigger 예시 | 운영 의미 |
|---|---|---|
| warning | `retry_budget_burn_ratio > 0.5` 이지만 verified progress 지속 | 곧 auto-retry 종료점 접근 |
| critical | `retry_budget_burn_ratio > 0.8` 그리고 `retry_without_progress_count` 증가 | human intervention 필요 |
| poison suspicion | `same_fingerprint_retry_share`가 대부분 차지 | classifier 또는 quarantine 분류가 늦음 |

즉 retry alert는 회복성 신호가 아니라 **retry가 더 이상 회복에 기여하지 않는 순간**을 잡아야 한다.

### 6. dashboard는 rollup, drilldown, sign-off snapshot 세 층으로 나누는 편이 좋다

한 화면에 모든 패널을 욱여넣으면 on-call은 빨리 보지 못하고, sign-off 회의에서는 근거를 재구성해야 한다.

실전에서는 보통 세 층이 더 읽기 쉽다.

| 층 | 포함물 | 목적 |
|---|---|---|
| Rollup board | gap/quarantine/verified drift/retry burn 상태칩 | 지금 red인지 green인지 30초 안에 판단 |
| Drilldown board | shard heatmap, failure fingerprint table, quarantine owner split | 왜 red인지 바로 파고들기 |
| Sign-off snapshot | target/verified watermark, open gap count, quarantine disposition, retry stop 상태 | evidence packet에 붙일 승인 근거 생성 |

특히 sign-off snapshot은 [Projection Rebuild Evidence Packet](./projection-rebuild-evidence-packet.md)의 artifact vocabulary와 맞추는 편이 좋다.

- replay completeness
- quarantine / retry ledger
- remaining drift
- blocking reason

이 naming이 맞아야 dashboard와 approval packet이 서로 다른 말을 하지 않는다.

### 7. alert severity는 rebuild 단계와 cutover 단계에서 달라야 한다

같은 지표라도 history backfill 중 warning인 것이 cutover 직전에는 block일 수 있다.

| 단계 | 우선순위가 높은 신호 | 기본 해석 |
|---|---|---|
| history backfill | gap closure slope, retry burn | 느려도 복구 가능하면 진행 |
| tail catch-up | verified watermark drift, strict-path 영향 shard | cutover admission gate와 직접 연결 |
| canary | quarantine critical share, fallback 연동 drift | user-visible risk가 곧 rollback 기준 |
| rollback window | gap 재발, retry storm 재등장 | latent bug 재현 여부 확인 |

즉 alert rule은 공용 하나보다 stage label을 함께 태우는 편이 맞다.  
같은 `verified_drift_seconds=120`도 normal rebuild와 canary 직전의 운영 의미가 다르다.

### 8. false green을 만드는 관측 패턴은 미리 금지해야 한다

다음 대시보드 습관은 replay 운영을 자주 망친다.

| 안 좋은 패턴 | 왜 위험한가 | 더 나은 기본값 |
|---|---|---|
| progress %만 보여줌 | gap, quarantine, drift가 가려짐 | 4축 scorecard 동시 노출 |
| quarantine count만 보여줌 | 성장률과 criticality가 안 보임 | growth + owner + critical share 포함 |
| attempted watermark만 사용 | partial apply를 성공처럼 보이게 함 | verified watermark를 별도 1급 지표로 승격 |
| retry 횟수만 셈 | noisy but useful retry와 무의미한 retry storm을 구분 못 함 | burn ratio와 progress 효율 함께 표시 |

운영 문서에 이 금지 패턴을 적어 두면 tool 선택이 달라도 해석 기준이 흔들리지 않는다.

---

## 운영 대시보드 기본 패킷

| 섹션 | 필수 위젯 | 질문 |
|---|---|---|
| Replay completeness | gap count, max gap age, affected shard heatmap | 어디가 아직 비었는가 |
| Quarantine control | open count, growth rate, critical event share, ownerless count | 격리가 통제되는가 |
| Verified progress | target/attempted/verified watermark, time since verified advance | 증명된 경계가 움직이는가 |
| Retry efficiency | burn ratio, same-fingerprint share, retries per verified advance | retry가 실제 복구에 기여하는가 |
| Sign-off status | cutover block reason, packet link, latest approval snapshot | 지금 무엇 때문에 못 올리는가 |

---

## 실전 시나리오

### 시나리오 1: progress는 99%인데 cutover가 계속 막힌다

원인은 global progress가 아니라 shard 2개의 `verified_drift_seconds` 정체일 수 있다.

- attempted watermark는 계속 전진
- verified watermark는 20분째 그대로
- retry budget burn은 빠르게 상승

이 경우 alert는 "느림"이 아니라 `attempted vs verified divergence`와 `retry without progress`에 걸려야 한다.

### 시나리오 2: quarantine는 적지만 핵심 주문 상태 이벤트가 포함돼 있다

`quarantine_open_count=2`만 보면 안전해 보일 수 있다.  
하지만 둘 다 `OrderPaid`, `OrderCancelled`라면 cutover는 red다.

그래서 quarantine 패널에는 count 외에 `critical_event_share`와 owner/disposition이 반드시 보여야 한다.

### 시나리오 3: retry storm이 transient처럼 보이지만 실제론 deterministic bug다

retry 수가 급증하고 같은 stack trace/fingerprint가 대부분이라면 auto-retry로는 회복되지 않는다.

- `same_fingerprint_retry_share` 급증
- `retries_per_verified_advance` 악화
- quarantine growth는 거의 없음

이 조합은 classifier나 quarantine 분류가 늦고 있다는 뜻이다.

---

## 코드로 보기

### replay observability sample

```java
public record ReplayObservabilitySnapshot(
    long openGapCount,
    Duration maxGapAge,
    long quarantineOpenCount,
    double quarantineGrowthRatePerHour,
    long targetWatermark,
    long attemptedWatermark,
    long verifiedWatermark,
    Duration verifiedDrift,
    double retryBudgetBurnRatio,
    double sameFingerprintRetryShare
) {
    public long attemptedVsVerifiedGap() {
        return attemptedWatermark - verifiedWatermark;
    }
}
```

### alert evaluator

```java
public final class ReplayAlertEvaluator {
    public boolean cutoverBlocked(ReplayObservabilitySnapshot snapshot, Duration verifiedDriftBudget) {
        return snapshot.openGapCount() > 0
            || snapshot.quarantineOpenCount() > 0
            || snapshot.verifiedDrift().compareTo(verifiedDriftBudget) > 0
            || snapshot.retryBudgetBurnRatio() >= 0.8;
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| progress 중심 dashboard | 구현이 쉽다 | false green이 많다 | 거의 권장하지 않음 |
| gap/quarantine만 보는 운영 | poison과 누락은 보인다 | verified drift와 retry storm을 놓친다 | 초기 replay 운영 |
| 4축 replay observability 운영 | sign-off와 incident 판단이 선명해진다 | metric 정의와 alert tuning이 필요하다 | 중요한 projection rebuild 대부분 |

판단 기준은 다음과 같다.

- replay dashboard는 approval 질문에 답해야 한다
- attempted보다 verified watermark를 더 강한 지표로 둔다
- quarantine는 count가 아니라 growth와 criticality를 같이 본다
- retry는 burn 효율과 repeated fingerprint를 함께 본다

---

## 꼬리질문

> Q: replay gap count만 0이면 cutover green 아닌가요?
> 의도: gap closure와 verified sign-off를 구분하는지 본다.
> 핵심: 아니다. quarantine, verified drift, retry burn까지 함께 녹색이어야 false green을 줄일 수 있다.

> Q: quarantine 건수가 적으면 큰 문제는 아닌 것 아닌가요?
> 의도: 양과 의미를 분리해서 보는지 확인한다.
> 핵심: 아니다. 핵심 상태 전이 이벤트가 포함되면 소수여도 cutover red다.

> Q: attempted watermark가 target에 도달했는데 왜 아직 blocked죠?
> 의도: 시도와 검증을 구분하는지 본다.
> 핵심: last verified watermark가 따라오지 않았으면 sign-off 기준은 아직 미통과다.

## 한 줄 정리

Projection replay 관측성은 progress 숫자 몇 개를 모으는 일이 아니라, replay gap, quarantine growth, verified watermark drift, retry budget burn을 같은 언어로 대시보드와 alert 계약에 묶어 cutover false green을 막는 운영 패턴이다.

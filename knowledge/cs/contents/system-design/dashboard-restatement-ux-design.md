# Dashboard Restatement UX 설계

> 한 줄 요약: dashboard restatement UX 설계는 late data, replay, correction으로 숫자가 바뀔 때 사용자가 어떤 기간과 지표가 왜 수정되었는지 이해할 수 있게 표시, provenance, 비교, 공지 방식을 제공하는 분석 운영 설계다.

retrieval-anchor-keywords: dashboard restatement ux, corrected metric display, analytics correction badge, restated dashboard, metric provenance, corrected period banner, diff before after, data freshness indicator, restatement notice, dashboard trust, backfill correction ux, metric version history, export superseded snapshot, restatement severity

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Analytics Late Data Reconciliation 설계](./analytics-late-data-reconciliation-design.md)
> - [Reconciliation Window / Cutoff Control 설계](./reconciliation-window-cutoff-control-design.md)
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
> - [Alert Re-Evaluation / Correction 설계](./alert-reevaluation-correction-design.md)
> - [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)

## 핵심 개념

late data나 replay로 숫자가 바뀌는 것은 기술적으로 정상일 수 있다.
하지만 사용자에게는 "어제 본 숫자와 오늘 숫자가 다르다"는 경험으로 나타난다.

그래서 dashboard는 단순히 최신 값을 그리는 것만으로 끝나지 않는다.

- 어떤 지표가 수정되었는가
- 어느 기간이 영향을 받았는가
- 왜 수정되었는가
- 이전 값과 새 값의 차이가 얼마나 되는가

즉, restatement UX의 목적은 정확도뿐 아니라 **사용자의 신뢰를 유지하는 설명 가능성**이다.

## 깊이 들어가기

### 1. 왜 UX가 중요한가

동일한 correction도 UI가 없으면 다음처럼 느껴진다.

- 데이터가 불안정하다
- 대시보드를 믿을 수 없다
- 팀마다 다른 숫자를 본다
- 알림이나 리포트와 수치가 맞지 않는다

기술적으로는 맞아도 사용자 경험상 "조용한 수정"은 운영 부채가 된다.

### 2. Capacity Estimation

예:

- 일일 active dashboard 5만
- restatement 대상 지표 하루 수십 개
- correction 빈도 주당 수 회
- diff compare 대상 기간 최대 30일

이때 봐야 할 숫자:

- restated chart count
- provenance lookup latency
- before/after diff storage
- correction notice click-through
- trust-related support ticket 수

restatement UX는 차트 렌더링보다 provenance와 diff 저장소가 병목이 될 수 있다.

### 3. UX 기본 요소

대표 요소:

- correction badge
- affected time-range banner
- freshness / finalized 상태 표시
- before/after diff tooltip
- provenance link
- restatement history drawer

핵심은 "숫자가 달라졌다"를 숨기지 않고, 이해 가능한 문장으로 드러내는 것이다.

### 4. Finalized vs mutable period

모든 기간을 동일하게 보여 주면 혼란스럽다.

보통 구분:

- mutable window
- corrected but not finalized
- finalized historical period

사용자는 현재 보고 있는 창이 "아직 바뀔 수 있는 구간인지"를 알아야 한다.

### 5. Provenance와 explanation model

restatement 원인을 최소한 이 수준으로 분류하면 유용하다.

- natural late data
- replay/backfill
- bug correction
- source system reconciliation
- manual adjustment

이 provenance가 없으면 숫자는 바뀌었는데 이유를 설명할 수 없다.

### 6. Compare experience

가장 유용한 UX는 종종 현재 값만이 아니다.

- previous value vs current value
- absolute diff / percent diff
- correction timestamp
- affected sink list

특히 경영/분석 대시보드는 "얼마나 바뀌었는가"가 매우 중요하다.

### 7. Trust-preserving defaults

주의할 점:

- 너무 많은 배지를 붙이면 noise가 된다
- 너무 숨기면 불신이 생긴다
- 실시간/최종값 혼합 차트를 한 축에 두면 오해가 커진다

즉, UX는 데이터 정확성과 신뢰 사이의 균형이다.

### 8. Restatement state machine

좋은 UX는 corrected / not corrected의 이분법보다 상태 전이를 보여 준다.

대표 상태:

- `mutable`: 아직 자연 late arrival이 들어올 수 있는 구간
- `recomputing`: backfill 또는 replay가 진행 중인 구간
- `corrected`: 수정이 publish되었고 이전 값과 diff를 볼 수 있는 구간
- `finalized`: 추가 변경이 매우 예외적인 구간

같은 숫자 변경이라도 현재 상태가 무엇인지에 따라 사용자의 행동이 달라진다.
예를 들어 `recomputing`이면 의사결정을 잠시 보류해야 하고, `corrected`면 diff와 원인을 확인해야 한다.

### 9. Page-level vs chart-level correction UX

restatement는 한 위젯만의 문제가 아닐 때가 많다.
그래서 UI 계층을 나눠 설계하는 편이 좋다.

- page-level banner: 어떤 날짜 범위와 필터가 영향을 받는지 요약
- chart-level badge: 어떤 시계열/카드가 실제로 바뀌었는지 표시
- history drawer: correction timeline과 previous version 탐색
- sink status: export, report, alert 재평가 상태 표시

이렇게 나누면 "전체 페이지가 흔들리는지"와 "이 차트만 수정됐는지"를 동시에 설명할 수 있다.

### 10. Export와 subscription semantics

dashboard 화면만 고치고 export semantics를 방치하면 다시 혼란이 생긴다.

필요한 계약:

- PDF/CSV export는 generated-at과 metric version을 함께 남긴다
- restated 이후 기존 export는 `superseded`로 표시할 수 있어야 한다
- scheduled report는 correction campaign과 연결된 재발행 상태를 가져야 한다
- saved dashboard link는 finalized 여부와 correction summary를 함께 노출한다

숫자 자체보다 "이 숫자가 어떤 snapshot에서 나온 것인가"가 더 중요해지는 순간이 있다.

### 11. Alert와 report 정렬 표시

restatement UX는 차트 설명에서 끝나지 않는다.
같은 지표를 보는 다른 sink들이 어디까지 따라왔는지 보여 주는 것이 신뢰 유지에 중요하다.

예:

- alert re-evaluation completed / pending
- scheduled report regenerated / superseded
- warehouse extract refreshed / pending approval

사용자는 수정된 숫자만이 아니라 "관련 파생물도 다시 계산되었는가"를 알고 싶어 한다.

## 실전 시나리오

### 시나리오 1: 전환율 지표 restatement

문제:

- 모바일 지연 업로드로 어제 전환율이 수정됐다

해결:

- 어제 날짜 구간에 correction badge를 표시한다
- tooltip에 이전 값과 새 값을 함께 보여 준다
- provenance를 "late mobile upload"로 명시한다

### 시나리오 2: replay 후 대시보드 수정

문제:

- stream replay로 특정 시간대 aggregate가 재계산되었다

해결:

- 영향을 받은 차트에 restated banner를 노출한다
- replay campaign 링크와 correction 시각을 제공한다
- 관련 alert / report가 재평가되었는지도 함께 표시한다

### 시나리오 3: executive report와 dashboard 수치 차이 문의

문제:

- 리포트 PDF는 이전 값이고 대시보드는 새 값이다

해결:

- finalized 여부와 correction history를 명확히 보여 준다
- export 시점의 snapshot version을 남긴다
- report sink에도 restatement link를 제공한다

### 시나리오 4: month-end backfill 이후 임원 대시보드 정렬

문제:

- 월말 backfill 이후 KPI 카드 값은 바뀌었지만 구독 메일과 alert 평가 시점이 달라 의사결정자가 어느 숫자를 믿어야 할지 혼란스럽다

해결:

- 페이지 상단에 correction campaign banner를 두고 영향받은 위젯 목록을 노출한다
- 각 KPI 카드에는 previous/current diff와 finalized 여부를 보여 준다
- export와 alert의 재평가 진행 상태를 같은 drawer에서 확인할 수 있게 한다

## 코드로 보기

```pseudo
function renderMetric(metric, range):
  value = metricStore.current(metric, range)
  provenance = restatementStore.lookup(metric, range)
  if provenance.exists:
    ui.showBadge("Corrected")
    ui.showDiff(provenance.previousValue, value)
    ui.showReason(provenance.reason)
    ui.showStatus(provenance.state)
    ui.showSinkStatus(provenance.downstreamStatuses)
  renderChart(value)
```

```java
public MetricView render(MetricQuery query) {
    MetricValue current = metricService.current(query);
    RestatementInfo info = restatementService.find(query);
    return metricViewAssembler.assemble(current, info);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Silent overwrite | 단순하다 | 신뢰를 잃기 쉽다 | 거의 권장되지 않음 |
| Badge only | 가볍다 | 설명이 부족할 수 있다 | low-stakes dashboard |
| Badge + provenance + diff | 신뢰도가 높다 | 구현 비용이 든다 | 중요한 제품/비즈니스 대시보드 |
| Full history timeline | 투명성이 높다 | UI가 무거워진다 | 감사/재무에 가까운 지표 |

핵심은 dashboard restatement UX가 장식이 아니라 **수정된 숫자를 사용자가 믿고 해석할 수 있게 하는 신뢰 계층**이라는 점이다.

## 꼬리질문

> Q: 숫자가 바뀌었으면 그냥 최신값만 보여 주면 되지 않나요?
> 의도: 정확성과 신뢰의 차이 이해 확인
> 핵심: 최신값만 보여 주면 기술적으로는 맞아도 사용자는 데이터가 불안정하다고 느낄 수 있다.

> Q: 모든 correction을 UI에 다 드러내야 하나요?
> 의도: noise vs transparency 균형 확인
> 핵심: 중요도와 사용자층에 따라 다르지만, 최소한 사용자 의사결정에 영향을 주는 수정은 설명 가능해야 한다.

> Q: provenance가 왜 중요한가요?
> 의도: correction 분류와 설명 가능성 이해 확인
> 핵심: 같은 restatement라도 late data인지 bug correction인지에 따라 해석과 대응이 달라지기 때문이다.

> Q: finalized 기간과 mutable 기간을 왜 구분하나요?
> 의도: 데이터 확정성 UX 이해 확인
> 핵심: 사용자가 지금 보는 숫자가 아직 변할 수 있는지 알아야 신뢰와 의사결정이 맞춰진다.

## 한 줄 정리

Dashboard restatement UX 설계는 correction된 숫자를 숨기지 않고 provenance, diff, 기간 상태를 함께 보여 줘 사용자의 데이터 신뢰를 유지하는 분석 운영 설계다.

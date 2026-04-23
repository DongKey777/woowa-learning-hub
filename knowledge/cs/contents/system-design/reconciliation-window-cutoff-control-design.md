# Reconciliation Window / Cutoff Control 설계

> 한 줄 요약: reconciliation window와 cutoff control 설계는 late arrival, settlement delay, correction 허용 범위를 고려해 어떤 시점을 기준으로 정산·집계·청구 창을 닫고 다시 여는지 명시하는 운영 제어 설계다.

retrieval-anchor-keywords: reconciliation window, cutoff control, late arrival, settlement window, close period, reopen correction, watermark cutoff, posting window, financial close, correction after close, analytics restatement

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
> - [Billing Usage Metering System 설계](./billing-usage-metering-system-design.md)
> - [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)
> - [Replay / Repair Orchestration Control Plane 설계](./replay-repair-orchestration-control-plane-design.md)
> - [Streaming Analytics Pipeline 설계](./streaming-analytics-pipeline-design.md)
> - [Consistency Repair / Anti-Entropy Platform 설계](./consistency-repair-anti-entropy-platform-design.md)
> - [Analytics Late Data Reconciliation 설계](./analytics-late-data-reconciliation-design.md)
> - [Dashboard Restatement UX 설계](./dashboard-restatement-ux-design.md)

## 핵심 개념

reconciliation에서 가장 어려운 질문 중 하나는 "언제 창을 닫을 것인가"다.

- provider 정산 파일은 늦게 올 수 있다
- 이벤트는 late arrival로 도착할 수 있다
- 내부 배치가 지연될 수 있다
- correction은 언제까지 허용할지 정해야 한다

즉, reconciliation은 단순 diff가 아니라 **시간 경계와 보정 정책을 가진 windowed 운영 루프**다.

## 깊이 들어가기

### 1. 왜 cutoff가 필요한가

창을 영원히 열어 두면 다음 문제가 생긴다.

- 청구서와 정산 리포트가 계속 바뀜
- 운영자가 어떤 숫자가 확정인지 모름
- 회계/정산 승인과 시스템 집계가 어긋남

반대로 너무 일찍 닫으면:

- late arrival가 빠짐
- correction이 과도하게 다음 기간으로 밀림
- 고객 이의 제기가 늘어남

그래서 cutoff는 성능이 아니라 **업무적 확정 시점**을 정하는 문제다.

### 2. Capacity Estimation

예:

- 하루 거래 5천만 건
- provider statement는 최대 6시간 지연
- internal event lag p99 20분
- correction reopen은 월 2회 이하 허용

이때 봐야 할 숫자:

- arrival lag distribution
- close delay
- reopen frequency
- correction volume after close
- window-finalization time

cutoff 설계는 평균 arrival time보다 tail 지연이 더 중요하다.

### 3. Window 상태 모델

보통은 다음 같은 상태를 가진다.

```text
OPEN
 -> SOFT_CLOSE
 -> HARD_CLOSE
 -> CORRECTION_ONLY
 -> FINALIZED
```

핵심은 close를 한 번에 하지 않는 것이다.

- soft close: 기본 집계는 잠그지만 늦은 건을 제한적으로 허용
- hard close: 일반 입력 금지
- correction only: 보정 entry만 허용

### 4. Watermark와 business cutoff는 다르다

streaming watermark는 기술적 lateness 경계다.
하지만 reconciliation cutoff는 business policy가 더 강하다.

예:

- 기술적으로는 2시간 늦은 이벤트도 처리 가능
- 하지만 청구 마감은 KST 자정 + 30분까지만 허용

즉, watermark와 business close는 연결되지만 동일 개념은 아니다.

### 5. Reopen과 correction policy

창을 닫았다고 모든 오류가 끝나는 것은 아니다.

대표 선택지:

- closed window를 reopen
- next window에 correction entry 반영
- 별도 dispute / adjustment workflow 사용

금전/청구 영역에서는 원본 기간을 조용히 덮어쓰기보다, correction record를 append하는 편이 더 안전하다.

### 6. Dependency-aware close

reconciliation window는 한 시스템만 보고 닫으면 안 된다.

봐야 할 것:

- provider statement 도착 여부
- internal ledger completeness
- replay / repair campaign 존재 여부
- anti-entropy 결과
- approval workflow 완료 여부

즉, close는 단일 cron이 아니라 여러 선행 조건을 모아 판단하는 control plane 문제다.

### 7. Observability와 operator ergonomics

운영자는 다음을 즉시 알아야 한다.

- 지금 어떤 window가 open/soft-close/hard-close 상태인가
- close가 지연되는 이유가 무엇인가
- late arrival가 얼마나 쌓였는가
- correction이 어느 기간에 반영될 예정인가

숫자 자체보다 경계와 이유가 잘 보여야 한다.

## 실전 시나리오

### 시나리오 1: 일일 결제 정산 close

문제:

- provider statement가 일부 늦고, 우리 callback도 tail 지연이 있다

해결:

- 자정 이후 soft close를 먼저 적용한다
- provider completeness 확인 뒤 hard close를 진행한다
- 누락분은 correction ledger로 다음 날 반영한다

### 시나리오 2: usage billing invoice finalize

문제:

- 월말 사용량은 아직 일부 ingestion lag가 남아 있다

해결:

- invoice window의 watermark를 따로 둔다
- lag가 임계치를 넘으면 finalize를 지연한다
- 강제 마감 시 correction-only window를 함께 연다

### 시나리오 3: 큰 replay 이후 close 재검토

문제:

- 과거 usage bug를 replay로 바로잡는 캠페인이 끝났다

해결:

- 영향받은 windows만 correction review 대상으로 올린다
- 전체 reopen 대신 adjustment entry를 별도로 남긴다
- approval 후 finalization state를 갱신한다

## 코드로 보기

```pseudo
function evaluateClose(window):
  if providerStatementIncomplete(window):
    return HOLD
  if internalLag(window) > threshold:
    return SOFT_CLOSE
  if repairCampaignActive(window):
    return CORRECTION_ONLY
  return HARD_CLOSE

function applyLateEvent(event):
  window = resolveWindow(event)
  if window.state == OPEN:
    post(window, event)
  elif window.state == CORRECTION_ONLY:
    appendCorrection(window, event)
  else:
    routeToAdjustmentWorkflow(event)
```

```java
public CloseDecision decide(ReconciliationWindow window) {
    return cutoffPolicy.evaluate(window, dependencySnapshot.current());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Always-open window | 단순하다 | 확정성이 없다 | 내부 분석용 |
| Aggressive hard close | 숫자가 빨리 확정된다 | late arrival 손실이 커진다 | 지연 허용이 낮을 때 |
| Soft close + correction | 현실적이다 | 운영 정책이 복잡해진다 | 결제, 청구, 정산 |
| Full reopen | 원본 기간 수정이 쉽다 | 감사와 설명이 어렵다 | 드문 대형 사고 |
| Append correction only | 추적이 쉽다 | 사용자 설명이 더 필요할 수 있다 | 금융/감사 중요 도메인 |

핵심은 reconciliation window / cutoff control이 배치 스케줄이 아니라 **숫자를 언제 확정하고 언제 correction으로 넘길지 정하는 시간 경계 운영 설계**라는 점이다.

## 꼬리질문

> Q: watermark만 있으면 reconciliation close도 자동으로 되나요?
> 의도: 기술 경계와 비즈니스 경계 구분 확인
> 핵심: 아니다. watermark는 기술적 지연 경계이고, close는 provider completeness와 승인 같은 business 조건까지 함께 본다.

> Q: closed window를 바로 reopen하면 안 되나요?
> 의도: auditability와 correction semantics 이해 확인
> 핵심: 가능은 하지만 금융/청구 영역에서는 correction entry를 append하는 편이 추적과 설명이 더 쉽다.

> Q: cutoff를 너무 늦게 잡으면 왜 문제인가요?
> 의도: 확정성 비용 이해 확인
> 핵심: 청구/정산/리포트 숫자가 계속 바뀌어 운영과 고객 커뮤니케이션이 흔들리기 때문이다.

> Q: close decision을 cron 하나로 하면 왜 부족한가요?
> 의도: dependency-aware close 이해 확인
> 핵심: provider 파일, internal lag, repair campaign, approval 상태처럼 여러 선행 조건을 함께 봐야 하기 때문이다.

## 한 줄 정리

Reconciliation window / cutoff control 설계는 late arrival와 correction을 고려해 어떤 시점에 숫자를 확정하고 언제 adjustment로 넘길지 정하는 시간 경계 운영 설계다.

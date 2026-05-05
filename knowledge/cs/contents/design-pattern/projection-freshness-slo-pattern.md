---
schema_version: 3
title: Projection Freshness SLO Pattern
concept_id: design-pattern/projection-freshness-slo-pattern
canonical: false
category: design-pattern
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
aliases:
- projection freshness SLO
- read model freshness objective
- freshness SLI
- projection error budget
- strict fallback rate
intents:
- deep_dive
linked_paths:
- contents/design-pattern/read-model-staleness-read-your-writes.md
- contents/design-pattern/projection-lag-budgeting-pattern.md
- contents/system-design/projection-applied-watermark-basics.md
- contents/design-pattern/strict-read-fallback-contracts.md
- contents/system-design/post-write-stale-dashboard-primer.md
- contents/database/summary-drift-detection-bounded-rebuild.md
forbidden_neighbors:
- contents/network/browser-devtools-reload-hard-reload-disable-cache-primer.md
expected_queries:
- projection freshness SLO는 어떤 지표로 잡아?
- read model freshness를 SLI/SLO로 운영하려면 뭐가 필요해?
- strict fallback rate랑 projection lag를 같이 보는 이유가 뭐야?
- projection error budget burn이 커지면 어떤 대응을 해야 해?
contextual_chunk_prefix: |
  이 문서는 사용자가 화면에서 보는 요약 데이터가 원본 변경에 얼마나
  늦게 따라가는지를 SLI/SLO 지표로 정하고 운영하는 패턴을 깊이 잡는
  deep_dive다. 요약 데이터가 원본 변경에 얼마나 늦게 따라가, 갱신 지연
  목표, freshness budget, projection lag SLO, error budget burn 같은
  자연어 paraphrase가 본 문서의 핵심 지표 설계에 매핑된다.
---

# Projection Freshness SLO Pattern

> 한 줄 요약: read model freshness는 기술 감각이 아니라 운영 SLO로 관리해야 하며, lag SLI, tier별 목표, error budget, budget burn 대응, degrade/rollback 정책이 함께 있어야 projection 운영이 설명 가능해진다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Projection Lag Budgeting Pattern](./projection-lag-budgeting-pattern.md)
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)
> - [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)
> - [Fallback Capacity and Headroom Contracts](./fallback-capacity-and-headroom-contracts.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
> - [Replica Lag Observability와 Routing SLO](../database/replica-lag-observability-routing-slo.md)
> - [Summary Drift Detection, Invalidation, and Bounded Rebuild](../database/summary-drift-detection-bounded-rebuild.md)
> - [Dual-Read Comparison / Verification Platform 설계](../system-design/dual-read-comparison-verification-platform-design.md)

retrieval-anchor-keywords: projection freshness slo, read model freshness objective, freshness sli bundle, projection error budget, freshness budget burn, strict screen fallback rate, fallback saturation budget, strict read fallback contract, fallback headroom contract, cutover admission gate, projection incident policy, freshness monitor alarm, lag budget burn alarm, fallback saturation alarm, stale screen alert threshold

---

## 핵심 개념

lag budget이 설계 trade-off라면, freshness SLO는 운영 계약이다.

- 무엇을 측정할 것인가
- 어느 수준까지 허용할 것인가
- 초과 시 무엇을 할 것인가

Projection Freshness SLO 패턴은 read model 최신성을 다음처럼 운영 지표로 다루게 한다.

- SLI: 현재 freshness를 어떻게 측정
- SLO: 어느 수준을 목표
- error budget: 얼마나 초과를 허용
- burn policy: 얼마나 빠르게 budget이 소진되면 incident로 볼 것인가
- response: 초과 시 fallback/degrade/rollback/escalation

### Retrieval Anchors

- `projection freshness slo`
- `freshness sli`
- `read model latency objective`
- `projection error budget`
- `freshness budget burn`
- `lag breach policy`
- `freshness compliance`
- `sli to error budget`
- `strict screen fallback rate`
- `strict read fallback contract`
- `cutover admission gate`

---

## 깊이 들어가기

### 1. freshness SLI는 단일 숫자보다 bundle로 잡는 편이 안전하다

다음 중 무엇을 freshness로 볼지 정해야 한다.

- event produced at -> projection updated at
- aggregate version gap
- watermark gap
- strict screen fallback rate

각각 다른 성질을 본다. 실전에서는 하나만 두기보다 역할을 나눠서 본다.

| SLI | 무엇을 보는가 | 언제 중요해지는가 |
|---|---|---|
| end-to-end lag | event produced at -> projected at 지연 | 전체 freshness baseline |
| watermark gap | live tail이 target watermark를 얼마나 따라갔는지 | backfill / catch-up / cutover readiness |
| version gap | aggregate 최신 버전과 projection 버전 차이 | 단건 strict read, read-your-writes |
| strict fallback rate | strict 화면이 write model/old projection으로 우회한 비율 | 사용자 체감 regression, 조기 incident 감지 |

즉 freshness SLO 문서에는 최소한 "대표 SLI 1개 + 보조 SLI 1~2개"가 있어야 한다.

여기서 strict fallback rate는 단순 운영 잡음이 아니다.  
primary projection이 strict read를 혼자 만족하지 못해 fallback contract를 얼마나 자주 소비하는지 보여주는 지표다.

- 분모: strict screen 요청
- 분자: 실제 fallback route를 사용한 strict 요청
- 해석: 낮을수록 primary freshness가 read-your-writes 약속을 더 자력으로 만족함

그래서 rate 자체보다 [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)에 적힌 owner, route, mode별 상한과 함께 읽어야 운영 판단이 선다.
그리고 reserve가 실제로 남아 있는지는 [Fallback Capacity and Headroom Contracts](./fallback-capacity-and-headroom-contracts.md)처럼 saturation / breaker 지표까지 같이 봐야 해석이 완성된다.

### 2. Tier마다 다른 SLO가 필요하다

예를 들어:

- 주문 상세: p95 2초 이내
- 운영 검색: p95 10초 이내
- 통계: p95 5분 이내

하나의 숫자로 카테고리 전체를 평가하면 오히려 의미가 약해진다.

| Tier | 대표 경로 | 예시 목표 |
|---|---|---|
| STRICT | 주문 직후 상세, 결제 확인 화면 | p95 2초, strict fallback rate 0.5% 이하 |
| STANDARD | 운영 목록, 검색 결과 | p95 10초, p99 30초 |
| RELAXED | 집계 대시보드, 리포트 | p95 5분, stale badge 의무 |

### 3. error budget은 "얼마나 늦어도 되는가"뿐 아니라 "얼마나 빨리 타고 있는가"까지 봐야 한다

backfill/cutover 중에는 일시적 신선도 저하가 생긴다. 이때 error budget이 없으면 운영팀과 개발팀이 매번 ad hoc로 싸우게 된다.

error budget 문서에는 최소한 다음이 있어야 한다.

- 평가 윈도우: 1시간 burn rate, 6시간 burn rate, 월간 누적 소진율
- non-compliant sample 정의: lag 초과, watermark gap 초과, strict fallback 발생 중 무엇을 budget 소진으로 볼지
- 잔여 예산: 이번 월간/주간 SLO에서 아직 얼마나 남았는지
- 모드별 사용 한도: normal/rebuild/cutover가 budget을 얼마나 먹어도 되는지

예를 들어 "월간 compliance 99.9%"만 써두고 끝내면, 지금 사고가 budget을 천천히 태우는지 급격히 태우는지 판단할 수 없다.

### 4. budget burn은 incident 언어로 번역돼야 한다

budget은 대시보드용 숫자가 아니라 대응 수준을 정하는 기준이다.

| 상태 | 대표 신호 | 일반적인 대응 |
|---|---|---|
| 경고 | 1시간 burn rate 상승, 아직 누적 budget 여유 있음 | on-call 확인, 병목 구간 분리 |
| 심각 | 6시간 burn rate가 월간 예산을 빠르게 소진 | strict fallback 강제, canary 동결 |
| 차단 | 누적 budget 거의 소진 또는 projected burn > 허용치 | full cutover 금지, rollback/rebuild 모드 |

이렇게 해 두면 "지금 lag가 조금 높다"를 "이번 속도로 가면 오늘 안에 예산을 다 태운다"로 번역할 수 있다.

### 5. cutover와 backfill은 남은 예산을 확인한 뒤에만 시작해야 한다

cutover 전 parity가 통과해도 다음이 나쁘면 진입하면 안 된다.

- 최근 1시간/6시간 burn rate가 이미 높음
- strict screen fallback rate가 평소보다 상승 중
- tail catch-up lag가 normal mode budget의 안전 여유를 먹고 있음
- rollback window는 있는데 budget이 남아 있지 않아 검증 시간을 버티지 못함

즉 cutover admission gate는 "데이터가 맞는가"뿐 아니라 "남은 error budget으로 전환 실험을 감당할 수 있는가"를 포함해야 한다.

### 6. breach policy는 모니터링보다 더 중요하다

SLO를 넘겼을 때 다음이 정의돼야 한다.

- strict screen fallback 활성화
- canary 중지
- cutover rollback
- rebuild 모드 진입

숫자만 있고 행동이 없으면 운영 계약이 아니다.

### 7. freshness SLO는 product expectation과 연결돼야 한다

기술팀만 아는 지표면 가치가 줄어든다.

- "주문 직후 2초 안에 보인다"
- "통계는 최대 5분 늦을 수 있다"

이런 사용자/운영 기대와 SLO가 연결돼야 설명 가능해진다.

### 8. 운영 문서는 목표치보다 admission gate와 incident policy가 먼저 보여야 한다

projection 운영 문서에는 보통 다음 순서가 읽기 쉽다.

1. 어떤 화면이 STRICT / STANDARD / RELAXED인지
2. primary SLI와 보조 SLI가 무엇인지
3. error budget과 burn rate를 어떻게 계산하는지
4. budget을 얼마나 남겨야 cutover를 허용하는지
5. budget burn 시 fallback / degrade / rollback을 누가 결정하는지

즉 "목표치"보다 "초과 시 어떤 버튼을 누르나"가 먼저 보여야 사고 때 빠르다.

### 기본 운영 패킷

| 항목 | 문서에 있어야 하는 질문 | 예시 |
|---|---|---|
| Primary SLI | freshness를 무엇으로 셀 것인가 | end-to-end lag p95 |
| Secondary SLI | 조기 경보는 무엇인가 | watermark gap, strict fallback rate |
| SLO | 정상 모드 목표는 무엇인가 | p95 2초, compliance 99.9% |
| Error budget | 초과 허용량은 얼마나 되는가 | 월간 non-compliant sample 0.1% |
| Burn policy | 얼마나 빨리 타면 incident인가 | 1시간 burn 2x, 6시간 burn 1x |
| Admission gate | cutover를 시작해도 되는가 | 잔여 budget 50% 이상, fallback 안정 |
| Response | 초과 시 무엇을 하는가 | fallback, canary freeze, rollback |

---

## 실전 시나리오

### 시나리오 1: 주문 상세 strict path

주문 직후 상세 화면은 freshness SLO를 엄격하게 두고, breach 시 fallback read를 활성화할 수 있다.

### 시나리오 2: 검색 인덱스 cutover

canary cutover 동안 SLO breach가 반복되면 full cutover를 중지하고 rollback window를 유지한다.  
특히 parity는 맞지만 budget burn이 이미 높은 경우라면 전환 자체를 미루는 편이 낫다.

### 시나리오 3: 대시보드 집계

집계는 느려도 되지만, SLO breach가 길어지면 stale badge와 운영 알람을 보여줄 수 있다.

### 시나리오 4: backfill 이후 tail catch-up

backfill 완료만 보고 바로 승격하면 안 된다.  
watermark gap은 줄었지만 strict fallback rate가 높다면 아직 freshness incident를 budget으로 덮고 있는 상태일 수 있다.

---

## 코드로 보기

### SLO definition

```java
public record ProjectionFreshnessObjective(
    String projectionName,
    Duration targetP95Lag,
    Duration targetP99Lag,
    double minimumComplianceRate,
    double maxStrictFallbackRate
) {}
```

### SLI sample

```java
public record ProjectionFreshnessSample(
    Instant eventProducedAt,
    Instant projectedAt,
    boolean strictFallbackTriggered
) {
    public Duration lag() {
        return Duration.between(eventProducedAt, projectedAt);
    }
}
```

### budget burn status

```java
public record FreshnessBudgetStatus(
    double hourlyBurnRate,
    double sixHourlyBurnRate,
    double remainingBudgetRatio
) {
    public boolean blocksCutover() {
        return hourlyBurnRate > 2.0 || remainingBudgetRatio < 0.5;
    }
}
```

### breach action

```java
public enum FreshnessResponse {
    ALERT_ONLY,
    FALLBACK,
    CANARY_FREEZE,
    CUTOVER_ROLLBACK,
    REBUILD_MODE
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 감으로 운영 | 초기엔 빠르다 | 설명 가능성과 재현성이 약하다 | 소규모 실험 |
| freshness SLO만 두고 burn policy는 생략 | 목표는 있다 | incident 우선순위와 cutover 판단이 흐려진다 | 미성숙한 중간 단계 |
| freshness SLO + budget burn 운영 | 의사결정이 선명해진다 | 측정/합의/대응 체계가 필요하다 | 중요한 read model 대부분 |
| 모든 projection에 동일 SLO | 관리가 단순하다 | 유스케이스 차이를 무시한다 | 보통 과도하게 단순화된 접근 |

판단 기준은 다음과 같다.

- SLI와 SLO를 분리해서 정의한다
- tier별 목표와 breach action을 다르게 둔다
- error budget 잔여량과 burn rate를 함께 본다
- cutover/backfill 모드의 임시 목표도 문서화한다

---

## 꼬리질문

> Q: lag budget 문서가 있으면 SLO는 필요 없나요?
> 의도: 설계 trade-off와 운영 계약을 구분하는지 본다.
> 핵심: 둘은 다르다. budget은 설계 감각이고, SLO는 측정과 대응 기준이다.

> Q: SLI는 어떤 하나만 고르면 되나요?
> 의도: freshness를 단일 지표로 단순화하지 않는지 본다.
> 핵심: projection 성격에 따라 watermark, version gap, fallback rate 등을 함께 볼 수 있다.

> Q: SLO만 있으면 충분하고 budget burn은 굳이 안 봐도 되나요?
> 의도: 목표치와 incident 속도를 구분하는지 본다.
> 핵심: 아니다. burn rate가 있어야 cutover 보류, on-call escalation, rollback 우선순위를 정할 수 있다.

> Q: breach가 나면 무조건 rollback해야 하나요?
> 의도: 대응 정책 다양성을 보는 질문이다.
> 핵심: 아니다. fallback/degrade/alert-only 중 projection 중요도에 맞게 정한다.

## 한 줄 정리

Projection freshness SLO는 read model 최신성을 측정 가능한 운영 계약으로 바꾸고, error budget burn과 cutover admission gate까지 연결해 lag incident를 감이 아니라 합의된 대응으로 다루게 해준다.

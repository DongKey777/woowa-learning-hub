# Cross-Service NFR Budget Negotiation

> 한 줄 요약: NFR budget은 한 서비스가 혼자 선언해서 끝나는 숫자가 아니라, user flow를 함께 만드는 서비스들이 latency, availability, freshness, cost, degradation rules를 서로 협상하고 기록해야 실제 설계 제약으로 작동한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Cross-Service NFR Budget Negotiation](./README.md#cross-service-nfr-budget-negotiation)
> - [Non-Functional Requirements as Budgets](./non-functional-requirements-budgeting.md)
> - [SLA, SLO Ownership Model](./sla-slo-ownership-model.md)
> - [BFF Boundaries and Client-Specific Aggregation](./bff-boundaries-client-specific-aggregation.md)
> - [Release Policy, Change Freeze, and Error Budget Coupling](./release-policy-change-freeze-error-budget-coupling.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)

> retrieval-anchor-keywords:
> - dependency budget
> - NFR negotiation
> - latency budget negotiation
> - cross-service budget
> - budget allocation
> - freshness budget
> - degradation contract
> - SLO decomposition

## 핵심 개념

checkout latency 300ms 같은 목표를 세워도, 실제로는 여러 서비스가 그 시간을 나눠 써야 한다.
그런데 각 팀이 자기 지표만 최적화하면 end-to-end 목표는 쉽게 깨진다.

그래서 필요한 것이 cross-service budget negotiation이다.

협상 대상 예:

- latency
- availability
- data freshness
- retry budget
- cost budget
- degraded mode

즉 NFR budget은 숫자 선언이 아니라 **경계 간 약속과 trade-off 협상**이다.

---

## 깊이 들어가기

### 1. user-facing budget과 supporting budget을 분리해야 한다

end-to-end 목표는 보통 user-facing owner가 가진다.
하지만 그 목표는 supporting service budget으로 분해돼야 한다.

예:

- checkout flow p95 300ms
- inventory service 60ms
- pricing service 40ms
- payment adapter 90ms

이 분해가 없으면 downstream은 "우리는 정상"이라고 말하고, upstream은 전체 경험이 느려진다.

### 2. 협상은 latency 숫자만이 아니라 degrade behavior까지 포함해야 한다

budget negotiation이 실패하는 이유는 숫자만 합의하고, 목표를 못 지켰을 때 동작을 안 정하기 때문이다.

필요한 질문:

- timeout 이후 fallback이 있는가
- stale data 허용 범위는 얼마인가
- retry는 누가 몇 번까지 하는가
- optional dependency는 언제 건너뛰는가

좋은 budget은 정상 상태뿐 아니라 **budget breach 시 행동**도 정한다.

### 3. provider와 consumer의 인센티브가 다르다는 점을 인정해야 한다

provider는 안정성과 단순함을 원하고, consumer는 더 빠른 응답과 더 많은 필드를 원할 수 있다.

그래서 negotiation에는 다음이 포함돼야 한다.

- 필수 vs 선택 필드 구분
- expensive path의 opt-in 여부
- batch / sync 호출 분리
- freshness와 cost의 균형

즉 budget negotiation은 기술 계산이 아니라 **경계 설계 협상**이다.

### 4. budget drift를 탐지하는 신호가 있어야 한다

합의한 뒤에도 시스템은 변한다.

drift 신호 예:

- timeout 비율 증가
- fallback path activation 증가
- stale read complaint 증가
- request cost 증가
- queue age 증가

이 신호가 있어야 budget이 문서에서 운영으로 이어진다.

### 5. 협상 결과는 ADR, SLO, gate에 반영돼야 한다

회의에서만 합의하면 금방 잊힌다.
그래서 결과는 최소한 다음 중 일부에 연결돼야 한다.

- ADR
- API or data contract
- SLO 문서
- PRR / rollout gate
- fitness function

budget negotiation은 회의록이 아니라 **실행 규칙**으로 남아야 한다.

---

## 실전 시나리오

### 시나리오 1: BFF가 너무 많은 집계를 요구한다

모바일 BFF는 빠른 응답을 원하지만, pricing과 inventory를 모두 동기 호출하면 latency budget을 초과할 수 있다.
이 경우 일부 정보는 stale cache 허용, 일부는 async hydration으로 나눠야 한다.

### 시나리오 2: 추천 서비스가 freshness를 요구한다

소비자는 "실시간"을 원하지만 provider는 배치 갱신만 감당할 수 있다.
freshness budget과 fallback UI를 함께 합의해야 한다.

### 시나리오 3: timeout을 각 서비스가 independently 높인다

모든 hop이 자기 timeout을 조금씩 늘리면 전체 user flow는 무너진다.
timeout budget은 합이 맞는지 기준 owner가 계속 봐야 한다.

---

## 코드로 보기

```yaml
nfr_negotiation:
  flow: checkout
  owner: commerce-checkout
  supporting_budgets:
    inventory:
      latency_p95_ms: 60
      stale_read_allowed_seconds: 5
    pricing:
      latency_p95_ms: 40
      fallback: cached_price
    payment_adapter:
      timeout_ms: 90
      retry_attempts: 0
  review_trigger:
    - timeout_rate > 1%
    - fallback_activation > baseline * 2
```

좋은 negotiation 기록은 숫자와 degrade behavior를 함께 남긴다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 팀별 자율 budget | 빠르다 | end-to-end 품질이 깨지기 쉽다 | 단순한 흐름 |
| cross-service negotiation | 현실적인 budget이 나온다 | 합의 비용이 든다 | 여러 서비스가 핵심 흐름을 구성할 때 |
| negotiation + automated monitoring | drift를 빨리 잡는다 | 운영 체계가 필요하다 | 고트래픽/고위험 흐름 |

cross-service NFR budget negotiation의 목적은 협의를 늘리는 것이 아니라, **서로 다른 서비스 최적화가 사용자 경험을 깨뜨리지 않게 만드는 것**이다.

---

## 꼬리질문

- 이 user flow의 전체 budget owner는 누구인가?
- budget breach 시 degrade behavior는 정의돼 있는가?
- supporting service가 자기 편의로 timeout이나 retry를 바꾸고 있지 않은가?
- 합의한 budget이 실제 telemetry와 gate로 연결돼 있는가?

## 한 줄 정리

Cross-service NFR budget negotiation은 end-to-end 요구사항을 여러 서비스 간의 시간, 가용성, freshness, degrade contract로 분해해 실제 설계 제약으로 만드는 과정이다.

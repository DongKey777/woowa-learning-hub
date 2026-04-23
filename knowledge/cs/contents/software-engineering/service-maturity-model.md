# Service Maturity Model

> 한 줄 요약: service maturity model은 서비스를 만들어진 상태로 보지 않고, ownership, observability, contracts, rollout, deprecation readiness를 기준으로 성장 단계별로 보는 틀이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)
> - [On-Call Ownership Boundaries](./on-call-ownership-boundaries.md)
> - [Technology Radar and Adoption Governance](./technology-radar-adoption-governance.md)
> - [Lead Time, Change Failure, and Recovery Loop](./lead-time-change-failure-recovery-loop.md)
> - [Service Portfolio Lifecycle Governance](./service-portfolio-lifecycle-governance.md)

> retrieval-anchor-keywords:
> - service maturity model
> - service lifecycle
> - ownership maturity
> - observability maturity
> - contract maturity
> - release maturity
> - deprecation readiness
> - operational maturity

## 핵심 개념

서비스는 "있다/없다"로만 보지 말고, 얼마나 운영 가능한지 성숙도 관점으로 봐야 한다.

성숙도 모델은 다음을 평가하는 데 유용하다.

- owner가 명확한가
- 대시보드와 알림이 있는가
- 계약이 명시되어 있는가
- rollout과 rollback이 준비됐는가
- deprecation/sunset 계획이 있는가

즉 maturity model은 서비스의 단순 품질 점수가 아니라 **운영 가능성의 단계 모델**이다.

---

## 깊이 들어가기

### 1. maturity는 기능 수가 아니라 책임 수다

많은 기능이 있다고 성숙한 것이 아니다.

성숙한 서비스의 신호:

- owner가 명확하다
- runbook이 있다
- alert가 유효하다
- contract test가 있다
- rollout 정책이 있다
- hold/retire 기술 사용량이 보인다

### 2. 단계 모델이 있어야 개선 우선순위를 정할 수 있다

예시 단계:

- level 0: 임시/개발용
- level 1: 운영 가능하지만 불안정
- level 2: 관측과 계약이 정리됨
- level 3: rollout/rollback 자동화
- level 4: deprecation와 ownership이 명확

이런 모델이 있어야 무엇부터 보강할지 알 수 있다.

### 3. 모든 서비스가 같은 성숙도일 필요는 없다

내부 배치 서비스와 핵심 결제 서비스의 기준은 다를 수 있다.

성숙도는:

- business criticality
- external exposure
- failure cost

에 맞춰야 한다.

### 4. maturity model은 review와 policy의 기준이 된다

이 모델을 바탕으로:

- 아키텍처 리뷰 질문
- fitness function
- release gate
- on-call 요구 수준

을 정할 수 있다.

### 5. maturity는 시간에 따라 퇴화할 수 있다

서비스가 처음엔 성숙해 보여도, owner 변경이나 계약 변경 후 다시 낮아질 수 있다.

그래서 주기적인 재평가가 필요하다.

---

## 실전 시나리오

### 시나리오 1: 새 서비스가 운영에 들어간다

level 1에서 시작해 owner, alert, runbook을 채우고 level 2로 올린다.

### 시나리오 2: 오래된 서비스가 많이 쓰인다

성숙도는 높을 수 있지만 deprecation readiness가 낮다면 개선이 필요하다.

### 시나리오 3: 플랫폼 서비스와 제품 서비스가 섞여 있다

둘의 maturity 기준이 달라야 하므로 동일 잣대로 평가하면 안 된다.

---

## 코드로 보기

```yaml
service_maturity:
  ownership: defined
  observability: basic
  contracts: partial
  rollout: canary_ready
  deprecation: planned
```

성숙도는 느낌이 아니라 체크 가능한 기준이어야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 정성 평가 | 쉽다 | 기준이 흔들린다 | 초기 |
| 단계형 maturity model | 개선 우선순위가 보인다 | 정의가 필요하다 | 여러 서비스가 있을 때 |
| scorecard + policy | 자동화할 수 있다 | 운영 비용이 든다 | 성숙한 조직 |

service maturity model은 서비스의 상태를 설명하는 표가 아니라, **운영 성숙도를 올리기 위한 지도**다.

---

## 꼬리질문

- 우리 서비스의 maturity level은 무엇인가?
- 어떤 기준이 낮으면 바로 위험한가?
- 성숙도는 누가 주기적으로 재평가하는가?
- deprecation readiness를 어떻게 점검할 것인가?

## 한 줄 정리

Service maturity model은 서비스의 운영 가능성과 책임 수준을 단계적으로 평가해, 무엇을 먼저 개선해야 하는지 보이게 하는 프레임이다.

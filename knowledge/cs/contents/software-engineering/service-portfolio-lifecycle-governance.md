# Service Portfolio Lifecycle Governance

> 한 줄 요약: 서비스 lifecycle을 개별 서비스 단위로만 보면 orphan service, endless pilot, delayed sunset이 쌓이므로, portfolio 관점에서 incubating, active, critical, sunset, temporary 상태를 리뷰하고 정리하는 governance가 필요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Service Portfolio Lifecycle Governance](./README.md#service-portfolio-lifecycle-governance)
> - [Service Maturity Model](./service-maturity-model.md)
> - [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)
> - [API Lifecycle Stage Model](./api-lifecycle-stage-model.md)
> - [Prototype, Spike, and Productionization Boundaries](./prototype-spike-productionization-boundaries.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Service Split, Merge, and Absorb Evolution Framework](./service-split-merge-absorb-evolution-framework.md)
> - [Service Criticality Tiering and Control Intensity](./service-criticality-tiering-control-intensity.md)

> retrieval-anchor-keywords:
> - service portfolio
> - lifecycle governance
> - orphan service
> - temporary service
> - incubating service
> - endless pilot
> - portfolio review
> - service stage
> - service consolidation
> - service merge

## 핵심 개념

서비스가 많아지면 문제는 "새 서비스를 잘 만드는가"가 아니라, **전체 포트폴리오가 어떤 상태로 쌓이고 있는가**가 된다.

흔한 증상:

- pilot 서비스가 영구 운영됨
- owner가 없는 internal tool이 남음
- sunset 예정 서비스가 계속 미뤄짐
- 중요도는 낮은데 on-call과 infra 비용은 유지됨

그래서 portfolio lifecycle governance는 서비스들을 stage와 경제성, 운영성 기준으로 주기적으로 본다.

예:

- incubating
- active
- critical
- temporary / experimental
- deprecated / sunset
- retired candidate

즉 lifecycle governance는 개별 서비스 개선보다 **서비스 집합의 건강 관리**다.

---

## 깊이 들어가기

### 1. 서비스 수는 자산이 아니라 관리 부채가 될 수 있다

새 서비스는 분리를 쉽게 하지만, 시간이 지나면 다음 비용이 붙는다.

- on-call surface 증가
- metadata 관리 비용
- deploy/config drift
- 보안/규제 patch 대상 증가

그래서 portfolio review에서는 "왜 존재하는가"를 계속 물어야 한다.

### 2. temporary와 experimental 서비스는 별도 stage로 관리해야 한다

많은 조직이 prototype을 production에 얹은 뒤 stage를 안 바꾼다.
그 결과 endless pilot이 된다.

좋은 운영 방식:

- experimental label
- owner와 expiry
- user scope 제한
- graduation criteria
- sunset review date

이런 stage가 없으면 temporary system이 silently permanent가 된다.

### 3. active와 critical을 구분해야 한다

운영 중이라는 사실만으로 같은 관리 수준을 적용하면 비효율이 크다.

예:

- active: 운영 중이지만 business criticality는 중간
- critical: 강한 PRR, drill, on-call, stronger governance 필요

portfolio 단계에서 이 구분이 있어야 readiness 투자도 균형이 맞는다.

### 4. lifecycle review는 ownership metadata와 연결돼야 한다

포트폴리오 review를 하려면 최소한 다음이 보여야 한다.

- owner / steward
- stage
- criticality
- last meaningful traffic
- deprecation target
- temporary expiry

이 정보가 없으면 서비스 집합을 사실상 관리할 수 없다.

### 5. lifecycle governance는 socio-technical 구조를 정리하는 수단이기도 하다

orphan service가 생기는 이유는 종종 기술이 아니라 조직 변화다.

예:

- 팀 개편 후 owner가 사라짐
- pilot를 만든 팀이 해산됨
- internal tool이 여러 팀에 기대며 nobody-owned 상태가 됨

즉 portfolio review는 단지 시스템 재고 조사가 아니라 **조직 책임 표면을 다시 정리하는 작업**이다.

---

## 실전 시나리오

### 시나리오 1: beta 서비스가 1년째 남아 있다

사용자 수는 적지만 infra와 on-call은 계속 유지된다면, graduation 또는 sunset 중 하나를 결정해야 한다.

### 시나리오 2: internal tool이 중요해졌다

처음엔 임시 도구였지만 운영 핵심 경로가 됐다면, temporary stage에서 active/critical stage로 올리며 ownership과 readiness를 붙여야 한다.

### 시나리오 3: sunset 후보 서비스가 계속 정리되지 않는다

호출량, owner, replacement 상태를 portfolio table로 보지 않으면 계속 미뤄진다.

---

## 코드로 보기

```yaml
service_portfolio:
  - name: pricing-experiment
    stage: temporary
    owner: growth-team
    expires_at: 2026-09-01
  - name: order-service
    stage: critical
    owner: commerce-team
  - name: legacy-report-api
    stage: sunset
    replacement: analytics-bff
```

좋은 portfolio view는 서비스의 존재 이유와 다음 상태를 함께 보여 준다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 서비스별 개별 관리 | 단순하다 | 전체 부채가 안 보인다 | 서비스 수가 적을 때 |
| portfolio lifecycle review | orphan와 endless pilot을 줄인다 | 메타데이터가 필요하다 | 서비스가 많아질 때 |
| lifecycle + cost review | 정리 우선순위가 분명하다 | 운영 discipline이 필요하다 | 성숙한 조직 |

service portfolio lifecycle governance의 목적은 새 서비스를 막는 것이 아니라, **임시 시스템과 낡은 시스템이 조직 표면에 무한정 쌓이지 않게 만드는 것**이다.

---

## 꼬리질문

- temporary/experimental 서비스에 expiry와 graduation criteria가 실제로 있는가?
- active와 critical을 같은 관리 수준으로 다루고 있지 않은가?
- owner가 사라진 orphan service를 어떻게 탐지할 것인가?
- sunset 후보가 portfolio review에서 계속 뒤로 밀리는 이유는 무엇인가?

## 한 줄 정리

Service portfolio lifecycle governance는 서비스 집합을 stage와 ownership과 경제성 기준으로 관리해 endless pilot, orphan service, delayed sunset을 줄이는 운영 체계다.

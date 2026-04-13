# Release Trains vs Continuous Delivery

> 한 줄 요약: release trains는 정해진 시간표로 안전성을 모으는 방식이고, continuous delivery는 변경이 준비되는 즉시 흘리는 방식이며, 둘의 차이는 배포 리듬과 검증 통제의 철학 차이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Release Policy, Change Freeze, and Error Budget Coupling](./release-policy-change-freeze-error-budget-coupling.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
> - [Service Maturity Model](./service-maturity-model.md)

> retrieval-anchor-keywords:
> - release train
> - continuous delivery
> - release cadence
> - deployment rhythm
> - batch release
> - release window
> - delivery pipeline
> - change batching

## 핵심 개념

두 방식은 모두 "자주, 안전하게"를 목표로 한다.
하지만 접근이 다르다.

- Release train: 정해진 시간에 여러 변경을 묶어 출발
- Continuous delivery: 준비된 변경을 가능한 빨리 흘림

즉 하나는 시간표 중심이고, 다른 하나는 준비 상태 중심이다.

---

## 깊이 들어가기

### 1. release train은 예측 가능성을 준다

장점:

- 언제 나가는지 명확하다
- 커뮤니케이션이 쉽다
- 여러 팀이 한 번에 맞추기 좋다

단점:

- 급한 변경이 대기할 수 있다
- 작은 변경도 train을 기다리게 된다

### 2. continuous delivery는 흐름을 줄인다

장점:

- 준비된 변경을 빨리 보낼 수 있다
- 피드백이 빠르다
- 재고처럼 쌓이지 않는다

단점:

- 검증 체계가 약하면 위험하다
- release gate가 없으면 불안정해진다

### 3. 조직 규모와 사고 비용이 선택을 좌우한다

release train이 적합한 경우:

- 다수 팀이 같은 창구를 공유
- 외부 커뮤니케이션이 중요
- 승인/준비 시간이 긴 조직

continuous delivery가 적합한 경우:

- 자동 테스트가 강함
- feature flag와 canary가 성숙
- 작은 변경을 자주 내보냄

### 4. release train도 내부는 continuous일 수 있다

정해진 주기에 묶어 나가더라도, 내부적으로는 계속 준비할 수 있다.

즉 release train은 배포 리듬이고, continuous delivery는 준비와 흘림의 철학이다.

### 5. 둘을 섞는 하이브리드가 흔하다

많은 팀은:

- 핵심 시스템은 release train
- 독립 서비스는 continuous delivery

처럼 혼합한다.

---

## 실전 시나리오

### 시나리오 1: 대형 조직의 분기 릴리스

여러 팀이 맞춰야 하므로 release train이 예측 가능하다.

### 시나리오 2: 핵심 API를 자주 고친다

자동 테스트와 rollback이 성숙하면 continuous delivery가 더 낫다.

### 시나리오 3: release train이 너무 무거워졌다

train을 유지하되, train 사이에는 작은 continuous delivery를 도입해 병목을 줄인다.

---

## 코드로 보기

```text
release train:
  prepare -> batch -> gate -> release window

continuous delivery:
  commit -> validate -> deploy when ready
```

둘의 핵심은 일정이 아니라 **검증과 배포의 결합 방식**이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Release train | 예측 가능 | 느릴 수 있다 | 여러 팀이 함께 움직일 때 |
| Continuous delivery | 빠르다 | 검증이 중요하다 | 자동화가 강할 때 |
| Hybrid | 현실적이다 | 정책이 복잡하다 | 조직이 크고 다양할 때 |

release train vs continuous delivery는 속도 대 안정성의 단순 대결이 아니라, **변경을 묶는 방식과 흘리는 방식의 차이**다.

---

## 꼬리질문

- 우리 조직은 시간표 중심인가, 준비 상태 중심인가?
- release train이 실제 병목인가?
- continuous delivery를 막는 가장 큰 제약은 무엇인가?
- feature flag와 release cadence는 어떻게 연결되는가?

## 한 줄 정리

Release trains and continuous delivery는 변경을 시간표로 묶을지, 준비된 즉시 흘릴지에 대한 배포 리듬 전략이다.

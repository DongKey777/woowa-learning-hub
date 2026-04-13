# eXtreme Programming (XP)

> 한 줄 요약: XP는 "테스트를 많이 쓰는 방법"이 아니라, 변경이 잦은 환경에서 피드백 주기와 배포 리스크를 줄이기 위해 개발, 테스트, 고객 피드백, 릴리스를 한 루프로 묶는 방법이다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md)
> - [Release Trains vs Continuous Delivery](./release-trains-vs-continuous-delivery.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Release Policy, Change Freeze, and Error Budget Coupling](./release-policy-change-freeze-error-budget-coupling.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)

> retrieval-anchor-keywords:
> - extreme programming
> - XP
> - TDD
> - pair programming
> - small releases
> - simple design
> - refactoring
> - customer feedback
> - iteration
> - release cadence

## 핵심 개념

XP는 변화가 잦은 프로젝트에서 "얼마나 빨리 맞는 방향으로 되돌아올 수 있는가"를 최우선으로 보는 개발 방식이다.

핵심은 규칙을 많이 두는 것이 아니라, 매 짧은 주기마다 다음을 반복하는 데 있다.

- 무엇을 만들지 다시 확인한다
- 최소한의 설계로 먼저 만든다
- 테스트로 안전망을 깐다
- 자주 보여 주고 수정한다
- 불필요한 복잡도를 바로 정리한다

이 철학은 오늘날의 CI/CD, feature flag, canary rollout, contract test와도 잘 맞는다.

---

## 깊이 들어가기

### 1. XP는 고객 피드백 지연을 줄이는 방법이다

요구사항이 자주 바뀌는 상황에서는, 완성도를 한 번에 높이려다 늦게 틀리는 것이 가장 위험하다.

XP는 이를 막기 위해 다음을 강조한다.

- 짧은 iteration
- 자주 보는 데모
- customer test
- 작은 release

즉 "완성 후 검증"이 아니라 **작게 만들고 빨리 검증**하는 방식이다.

### 2. TDD는 테스트 기법이 아니라 설계 습관이다

XP에서 TDD가 중요한 이유는 테스트가 통과하는지보다, 코드를 쓰기 전에 인터페이스와 책임이 먼저 정리되기 때문이다.

좋은 TDD 흐름:

1. 실패하는 테스트를 먼저 쓴다
2. 최소 구현으로 통과시킨다
3. 중복과 복잡도를 리팩터링한다

이 흐름은 기능 검증과 설계 정리를 동시에 진행하게 만든다.

### 3. Pair Programming은 품질 검토와 지식 분산을 동시에 한다

pair programming은 단순히 두 명이 코딩하는 것이 아니다.

- driver는 구현에 집중한다
- navigator는 방향과 예외를 본다
- 함께 설계와 리뷰를 즉시 수행한다

특히 온보딩, 위험도가 높은 변경, 낯선 도메인에서 효과가 크다.

### 4. Small Releases는 배포 리스크를 줄인다

한 번에 크게 바꾸면 문제를 발견했을 때 되돌리기가 어렵다.

XP의 small release는 다음 운영 전략과 잘 맞는다.

- feature flag로 기능 노출 분리
- canary로 일부 사용자만 먼저 검증
- release train으로 타이밍을 맞춤

즉 XP는 개발론이면서 동시에 **배포 안전성 전략**이다.

### 5. Simple Design은 "나중에 안 바꿔도 되는 설계"가 아니다

단순한 설계는 미래 변경을 막는 것이 아니라, 지금 필요한 만큼만 복잡하게 만드는 것이다.

좋은 기준:

- 중복이 적은가
- 책임이 한 곳에 모여 있는가
- 변경 포인트가 보이는가
- 테스트가 쉬운가

Simple design은 과잉 추상화를 경계하는 장치다.

---

## 실전 시나리오

### 시나리오 1: 요구사항이 매주 바뀌는 서비스

XP는 한 번에 큰 설계 결정보다, 작은 릴리스와 빠른 피드백에 유리하다.

### 시나리오 2: 레거시를 조금씩 바꾸는 팀

작은 단위의 TDD와 리팩터링이 큰 재작성보다 안전하다.

### 시나리오 3: 운영 리스크가 큰 결제 기능

pair programming, contract test, small release, canary rollout을 같이 써야 한다.

---

## 코드로 보기

```text
iteration loop:
  plan -> test -> code -> refactor -> demo -> learn -> repeat
```

XP의 핵심은 한 번 잘 만드는 것이 아니라, 루프를 짧고 안정적으로 반복하는 것이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| XP 강하게 적용 | 피드백이 빠르다 | 팀 규율이 필요하다 | 변화가 잦을 때 |
| XP 약하게 적용 | 부담이 적다 | 효과가 줄어든다 | 작은 개선 단계 |
| XP + CI/CD + feature flag | 현대 운영과 잘 맞는다 | 체계가 필요하다 | 빠르게 자주 배포할 때 |

XP는 "테스트를 잘하는 방법"이 아니라 **변경 비용을 낮추는 개발 운영 방식**이다.

---

## 꼬리질문

- 우리 팀은 짧은 iteration을 실제로 유지할 수 있는가?
- customer feedback을 어떤 방식으로 빠르게 반영할 것인가?
- pair programming이 필요한 구간은 어디인가?
- small release를 가능하게 하는 배포 장치는 무엇인가?

## 한 줄 정리

XP는 테스트, 피드백, 리팩터링, 작은 릴리스를 한 루프로 묶어 변화가 잦은 환경에서 안전하고 빠르게 학습하는 개발 방식이다.

# Feature Flag Cleanup and Expiration

> 한 줄 요약: 피처 플래그는 배포를 안전하게 만들지만, 정리하지 않으면 기술 부채가 된다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Technical Debt Refactoring Timing](./technical-debt-refactoring-timing.md)

## 핵심 개념

피처 플래그는 기능을 즉시 켜고 끌 수 있게 해준다.
하지만 플래그는 배포 안전장치인 동시에, 시간이 지나면 **죽은 분기(dead branch)** 를 남긴다.

그래서 중요한 것은 "플래그를 만들 수 있는가"가 아니라,

- 언제 제거할지
- 누가 소유할지
- 어떻게 만료시킬지

를 정하는 것이다.

## 깊이 들어가기

### 1. 플래그의 유형

| 유형 | 목적 | 수명 |
|------|------|------|
| Release flag | 점진 배포 | 짧음 |
| Ops flag | 운영 제어 | 중간 |
| Permission flag | 사용자군 분리 | 중간 |
| Experiment flag | A/B 실험 | 짧음 |

수명이 짧은 플래그를 장기 상수처럼 두면 기술 부채가 빠르게 늘어난다.

### 2. 제거하지 않으면 생기는 문제

- 테스트 분기 폭발
- 조건문 중첩 증가
- 어떤 경로가 실제로 실행되는지 모름
- 플래그 조합이 늘어나면서 상태공간이 커짐

### 3. 만료 정책

좋은 플래그는 생성 시점에 제거 조건이 정해져 있어야 한다.

- 릴리스 후 2주 내 제거
- 실험 종료 시 제거
- 운영 이슈 해결 후 제거
- 대체 코드 경로 안정화 후 제거

## 실전 시나리오

### 시나리오 1: 플래그가 코드보다 많아진다

기능 하나를 출시했는데, A/B 테스트와 운영 롤백용 플래그가 겹치며 분기가 세 겹이 된다.
그 순간 플래그는 안전장치가 아니라 구조 복잡도의 원인이 된다.

### 시나리오 2: 오래된 플래그가 레거시가 된다

이미 모든 트래픽이 새 경로를 쓰는데도 오래된 분기가 남아 있으면,
오히려 그 코드가 다음 장애의 원인이 된다.

## 코드로 보기

```java
public class CheckoutService {
    private final FeatureFlagClient featureFlagClient;

    public PaymentResult checkout(Order order) {
        if (featureFlagClient.isEnabled("new-checkout-flow")) {
            return newFlow(order);
        }
        return legacyFlow(order);
    }
}
```

이 코드는 배포 안전성은 높지만, 제거되지 않으면 분기 비용이 누적된다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| 플래그로 장기 유지 | 롤백 쉬움 | 복잡도 증가 | 실험/점진 배포 |
| 즉시 코드 제거 | 단순함 | 롤백 비용 큼 | 기능이 충분히 검증됐을 때 |
| 기간 만료 정책 | 부채 통제 | 운영 규칙 필요 | 플래그가 많은 팀 |

## 꼬리질문

- 플래그 제거를 누가 책임져야 하는가?
- 롤백용 플래그와 영구 설정을 어떻게 구분할 것인가?
- 플래그 조합 폭발을 어떻게 테스트할 것인가?
- feature flag가 아키텍처 부채가 되는 순간은 언제인가?

## 한 줄 정리

피처 플래그는 배포를 안전하게 하지만, 제거 정책이 없으면 코드베이스의 숨은 부채가 된다.

# Trunk-Based Development vs Feature Branch Trade-offs

> 한 줄 요약: 브랜치 전략은 Git 사용 습관이 아니라, 통합 지연과 배포 리스크를 어디에 쌓을지 정하는 팀 운영 설계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
> - [Feature Flag Cleanup and Expiration](./feature-flag-cleanup-expiration.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Technical Debt Refactoring Timing](./technical-debt-refactoring-timing.md)
> - [Testing Strategy and Test Doubles](./testing-strategy-and-test-doubles.md)

> retrieval-anchor-keywords:
> - trunk-based development
> - feature branch
> - merge debt
> - integration latency
> - release branch
> - feature flag
> - continuous integration
> - batch integration

## 핵심 개념

브랜치 전략의 핵심은 "어디서 안전하게 작업할 수 있느냐"가 아니라, **변경을 얼마나 오래 분리해 둘 수 있느냐**다.

두 접근은 보통 다음처럼 대비된다.

- Trunk-based development: 짧은 브랜치, 자주 머지, 빠른 통합
- Feature branch: 기능 단위로 길게 분리, 상대적으로 늦은 통합

이 둘의 차이는 취향이 아니라 **변경 충돌과 피드백 주기**의 차이다.

---

## 깊이 들어가기

### 1. trunk-based는 "빨리 합치는 것"이 아니라 "늦게 분리하지 않는 것"이다

Trunk-based development는 메인 브랜치를 항상 건강하게 유지하는 방식이다.

전제 조건:

- 브랜치 수명이 짧다
- CI가 빠르다
- 테스트 자동화가 충분하다
- feature flag로 미완성 코드를 숨길 수 있다

즉 trunk-based는 코드가 미완성인 상태를 오래 끌지 않는 전략이다.

### 2. feature branch는 통합 전 검토 시간을 벌어 준다

Feature branch는 큰 작업을 독립적으로 진행하기 좋다.

장점:

- 작업 중간 상태를 숨길 수 있다
- 리뷰 단위를 나누기 좋다
- 다른 기능과 충돌을 잠시 피할 수 있다

단점:

- merge conflict가 나중에 몰린다
- 통합 실패 원인을 늦게 알게 된다
- 오래된 브랜치가 메인과 벌어질 수 있다

즉 feature branch는 "안전한 작업 공간"을 주지만, 그 대신 **통합 부채**를 쌓을 수 있다.

### 3. 브랜치 전략은 팀의 배포 리듬과 붙어 있다

아래 조건이 trunk-based에 유리하다.

- 배포가 자주 일어난다
- CI가 빠르게 돌아간다
- 스쿼드가 작고 경계가 분명하다
- feature flag 체계가 있다

반대로 아래 조건이면 feature branch가 당분간 낫다.

- 변경이 크고 장기 작업이 많다
- 테스트가 느리다
- 외부 의존성이 불안정하다
- 릴리스 승인이 느리다

중요한 건 "어느 쪽이 더 현대적인가"가 아니라, **현재 팀이 통합을 얼마나 자주 감당할 수 있는가**다.

### 4. 브랜치 전략의 진짜 비용은 merge가 아니라 피드백 지연이다

긴 브랜치는 보통 이런 비용을 만든다.

- 늦게 발견되는 설계 충돌
- 오래된 가정으로 쌓인 코드
- 리뷰 컨텍스트 붕괴
- 배포 직전의 대규모 통합 버그

반대로 너무 짧게 끊으면 작업 흐름이 자주 끊길 수 있다.

따라서 질문은 "브랜치를 길게 할까 짧게 할까"보다 **언제 검증 비용을 지불할 것인가**다.

### 5. feature flag는 trunk-based의 보조장치다

Trunk-based는 미완성 코드를 main에 놓을 수 있어야 한다.
그때 필요한 것이 feature flag다.

즉 브랜치 전략과 플래그 전략은 별개가 아니라 연결된다.

- trunk-based: merge를 자주 한다
- feature flag: 사용자 노출을 늦춘다

둘을 같이 써야 "코드는 통합됐지만 기능은 아직 숨긴 상태"를 만들 수 있다.

---

## 실전 시나리오

### 시나리오 1: 작은 팀의 신규 기능

작은 팀이 결제 화면 개선을 한다면 trunk-based가 잘 맞는다.

- 작업을 작은 단위로 쪼갠다
- feature flag로 미완성 경로를 숨긴다
- 매일 main에 합친다

이렇게 하면 통합 지연이 거의 없다.

### 시나리오 2: 대형 마이그레이션

레거시 모듈을 여러 달에 걸쳐 옮겨야 한다면 feature branch가 초기엔 편할 수 있다.

하지만 마지막에는 반드시 trunk와 합쳐야 하므로, 중간에 통합 시점을 자주 둬야 한다.

### 시나리오 3: 규제/승인 절차가 강한 조직

릴리스가 코드 머지보다 훨씬 느리면, feature branch와 release branch를 함께 쓰는 하이브리드가 나오기도 한다.

이때 중요한 건 브랜치 수를 늘리는 것이 아니라, **머지와 배포 사이의 책임을 명확히 하는 것**이다.

---

## 코드로 보기

```text
trunk-based:
  small branch -> review -> merge -> CI -> feature flag off -> deploy

feature branch:
  long-lived branch -> repeated local changes -> late merge -> big CI -> release
```

짧은 흐름은 검증을 앞당기고, 긴 흐름은 작업 분리를 늘린다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Trunk-based | 통합이 빠르다 | 테스트/플래그 체계가 필요하다 | CI가 빠르고 배포가 잦을 때 |
| Feature branch | 작업 분리가 쉽다 | merge debt가 쌓인다 | 큰 변경을 오래 숨겨야 할 때 |
| 하이브리드 | 현실에 맞추기 쉽다 | 규칙이 복잡해질 수 있다 | 조직 규모가 크고 제약이 많을 때 |

브랜치 전략은 코드 품질이 아니라 **변경 흐름의 품질**을 다루는 문제다.

---

## 꼬리질문

- 우리 팀은 merge conflict보다 integration bug가 더 큰가?
- feature flag 없이 trunk-based를 유지할 수 있는가?
- 브랜치가 길어지는 이유가 기술인지, 조직 승인 때문인지?
- release branch가 임시 대책이 아니라 고정 구조가 되고 있지 않은가?

## 한 줄 정리

Trunk-based는 통합 지연을 줄이는 전략이고, feature branch는 변경 분리를 늘리는 전략이며, 둘의 선택은 팀의 검증 속도와 배포 리듬이 결정한다.

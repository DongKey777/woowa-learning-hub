---
schema_version: 3
title: Dependency Update Strategy and Blast Radius Management
concept_id: software-engineering/dependency-update-blast-radius
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- dependency-update
- blast-radius
- rollout
- rollback
aliases:
- Dependency Update Strategy and Blast Radius Management
- dependency update blast radius
- transitive dependency upgrade risk
- lockfile update strategy
- dependency canary rollout
- 라이브러리 업데이트 장애 반경 관리
symptoms:
- patch, minor, major, transitive dependency 업데이트를 한 PR에 몰아 넣어 어떤 변경이 장애를 만들었는지 추적하지 못해
- lockfile과 canary, smoke test, rollback plan 없이 런타임 핵심 의존성을 전체 서비스에 한 번에 올려
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/dependency-governance-sbom
- software-engineering/deployment-rollout-strategy
next_docs:
- software-engineering/kill-switch-fast-fail
- software-engineering/feature-flag-dependency-management
- software-engineering/technical-debt-refactoring-timing
linked_paths:
- contents/software-engineering/feature-flags-rollout-dependency-management.md
- contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md
- contents/software-engineering/technical-debt-refactoring-timing.md
- contents/software-engineering/kill-switch-fast-fail-ops.md
- contents/software-engineering/adr-decision-records-at-scale.md
- contents/software-engineering/dependency-governance-sbom-policy.md
confusable_with:
- software-engineering/dependency-governance-sbom
- software-engineering/deployment-rollout-strategy
- software-engineering/feature-flag-dependency-management
forbidden_neighbors: []
expected_queries:
- 의존성 업데이트를 patch, minor, major, transitive 위험별로 나눠 blast radius를 줄이는 전략을 알려줘
- 라이브러리 major upgrade를 한 번에 올리지 않고 작은 서비스와 canary로 검증하려면 어떻게 해?
- lockfile과 dependency tree가 의존성 업데이트 장애 분석에 왜 중요한지 설명해줘
- 보안 패치가 급하지만 회귀 위험도 클 때 어떤 순서로 검증하고 배포해야 해?
- transitive dependency가 조용히 바뀌는 문제를 CI와 release gate에서 어떻게 잡아?
contextual_chunk_prefix: |
  이 문서는 dependency update를 patch/minor/major/transitive 위험별로 나누고 lockfile, smoke test, canary, rollback으로 blast radius를 관리하는 advanced playbook이다.
---
# Dependency Update Strategy and Blast Radius Management

> 한 줄 요약: 의존성 업데이트는 "최신 버전으로 올리기"가 아니라, 어떤 변경을 어떤 범위로 먼저 검증해서 장애 반경을 줄일지 정하는 운영 전략이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Technical Debt Refactoring Timing](./technical-debt-refactoring-timing.md)
> - [Kill Switch Fast-Fail Ops](./kill-switch-fast-fail-ops.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)

> retrieval-anchor-keywords:
> - dependency update strategy
> - blast radius
> - transitive dependency
> - lockfile
> - semver
> - patch window
> - update canary
> - upgrade risk

## 핵심 개념

의존성 업데이트는 버전을 올리는 행위처럼 보이지만, 실제로는 **시스템 변경을 얼마나 넓게 전파할지 조절하는 문제**다.

특히 다음 상황에서 blast radius 관리가 중요하다.

- 보안 패치가 급하지만 전체 회귀 위험도 크다
- transitive dependency가 함께 움직여 예측이 어렵다
- 런타임 버전, 빌드 플러그인, 테스트 프레임워크가 동시에 바뀐다
- 업데이트가 코드보다 운영 장애를 먼저 부를 수 있다

즉 dependency update는 릴리스 작업이 아니라 **위험 분할 작업**이다.

---

## 깊이 들어가기

### 1. 모든 의존성을 같은 위험으로 다루면 안 된다

업데이트는 보통 위험도가 다르다.

| 유형 | 예시 | 위험 |
|---|---|---|
| patch | 보안 취약점 수정 | 낮음~중간 |
| minor | API 호환 확장 | 중간 |
| major | 인터페이스 변경 | 높음 |
| transitive | 직접 쓰지 않는 하위 의존성 | 예측 어려움 |

같은 "업데이트"라도 위험 범위가 다르므로, 검증 전략도 달라야 한다.

### 2. blast radius는 기술 범위와 사용자 범위가 다르다

의존성 변경의 영향은 다음 층위로 나뉜다.

- 빌드 실패
- 테스트 실패
- 런타임 예외
- 성능 저하
- 특정 기능만 오류
- 전체 서비스 장애

좋은 전략은 가장 바깥쪽 충격부터 천천히 확장하는 것이다.

### 3. 업데이트를 한 번에 몰아치지 말아야 한다

좋은 순서:

1. 가장 낮은 위험의 패키지부터 업데이트
2. 공통 라이브러리와 빌드 도구는 별도 검증
3. 런타임 핵심 의존성은 canary 배포와 같이 검증
4. 장애 반경이 큰 업그레이드는 작은 서비스부터 적용

이 순서를 지키지 않으면 어떤 의존성이 문제를 만들었는지 모호해진다.

### 4. lockfile과 버전 정책은 blast radius를 줄인다

버전이 자동으로 따라오면 편해 보이지만, 재현성이 떨어진다.

좋은 통제 수단:

- lockfile 고정
- 허용 버전 범위 제한
- 업데이트 소유자 지정
- 자동 봇과 수동 승인 분리

의존성 업데이트는 "가만히 두면 안전"이 아니라, **정책 없이 움직이면 위험**한 영역이다.

### 5. 안전한 업데이트는 관측과 rollback이 함께 있어야 한다

업데이트 후 확인할 것:

- startup time
- error rate
- 주요 기능 smoke test
- 성능 회귀
- 재시도/timeout 증가

문제가 있으면 바로 원복하거나, feature flag와 함께 경로를 차단해야 한다.

---

## 실전 시나리오

### 시나리오 1: 보안 취약점 패치

외부 라이브러리에 취약점이 발견됐다.

대응 순서:

1. 영향 범위를 분리한다
2. patch와 minor 버전을 먼저 올린다
3. 빌드와 핵심 통합 테스트를 돌린다
4. canary 환경에서 런타임 지표를 본다
5. 문제 없으면 전체 반영한다

### 시나리오 2: 테스트 프레임워크의 major upgrade

테스트 프레임워크가 바뀌면 테스트 코드 자체가 실패할 수 있다.

이때는 제품 기능보다 CI blast radius가 더 크다.
그래서 작은 모듈부터 순차적으로 올리고, 실패 패턴을 분류해야 한다.

### 시나리오 3: transitive dependency가 조용히 바뀐다

직접 선언한 라이브러리는 그대로인데, 하위 의존성이 바뀌는 경우가 있다.

이 경우 lockfile, dependency tree, 빌드 리포트를 같이 보고
어떤 변경이 실제 영향인지 밝혀야 한다.

---

## 코드로 보기

```yaml
dependency_policy:
  patch:
    auto_merge: true
    smoke_test: true
  minor:
    manual_approval: true
    canary_required: true
  major:
    staged_rollout: true
    rollback_plan: required
```

정책은 단순한 문서가 아니라, 팀이 반복해서 따를 수 있는 안전 장치다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 자동 업데이트 | 빠르다 | 예측이 어렵다 | patch 수준일 때 |
| 수동 검토 | 통제가 쉽다 | 느리다 | 핵심 런타임일 때 |
| 단계적 업데이트 | blast radius가 작다 | 운영 절차가 늘어난다 | 큰 서비스/공통 라이브러리일 때 |

의존성 관리는 결국 "얼마나 빨리 올릴까"보다 **얼마나 작게 깨뜨릴까**의 문제다.

---

## 꼬리질문

- 어떤 의존성은 자동화하고 어떤 의존성은 고정해야 하는가?
- transitive dependency 변화는 어떻게 추적할 것인가?
- 업데이트 실패 시 원복 기준은 무엇인가?
- 보안 패치와 안정성 사이 우선순위는 어떻게 정하는가?

## 한 줄 정리

의존성 업데이트 전략은 버전 상승 자체가 아니라, 변경의 blast radius를 줄이기 위해 검증 순서와 롤백 경로를 설계하는 일이다.

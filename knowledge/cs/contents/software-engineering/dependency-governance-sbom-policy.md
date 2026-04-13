# Dependency Governance and SBOM Policy

> 한 줄 요약: dependency governance는 라이브러리 버전을 관리하는 일이 아니라, 무엇이 들어오고 나가는지 추적 가능한 정책으로 만들고 SBOM으로 공급망 위험을 다루는 것이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Dependency Update Strategy and Blast Radius Management](./dependency-update-blast-radius-management.md)
> - [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)

> retrieval-anchor-keywords:
> - dependency governance
> - SBOM
> - software bill of materials
> - supply chain policy
> - vulnerability management
> - dependency allowlist
> - provenance
> - transitive risk

## 핵심 개념

의존성 관리는 단순히 최신 버전으로 올리는 일이 아니다.
실제로는 다음을 통제해야 한다.

- 어떤 패키지를 허용할 것인가
- 누가 업데이트를 승인할 것인가
- 취약점이 발견되면 어떻게 대응할 것인가
- 어디까지 자동화할 것인가

SBOM은 이 통제를 가능하게 하는 가시화 도구다.

---

## 깊이 들어가기

### 1. dependency governance는 정책이 있어야 한다

정책이 없으면 다음이 섞인다.

- 보안 업데이트
- 기능 업데이트
- 빌드 도구 업데이트
- 실험적 라이브러리 추가

그래서 최소한 다음 정책이 필요하다.

- 직접 의존성과 간접 의존성 분리
- 허용/금지 라이브러리 목록
- 버전 범위 규칙
- 업데이트 승인자

### 2. SBOM은 "무엇이 들어왔는가"를 보는 기본 표다

SBOM에는 보통 다음이 필요하다.

- component name
- version
- supplier
- license
- provenance
- known vulnerability state

이 정보가 있어야 취약점 대응이 가능하다.

### 3. transitive risk이 가장 위험하다

직접 추가한 라이브러리보다 하위 의존성이 더 큰 문제가 될 수 있다.

그래서 dependency tree를 항상 봐야 한다.

- 내가 직접 쓰는 것
- 누가 몰래 끌고 온 것
- runtime에만 필요한 것

### 4. governance는 allowlist + review + automation의 조합이다

좋은 구조:

- allowlist로 기본 통제
- policy as code로 PR 차단
- SBOM scan으로 취약점 감지
- ADR로 예외 기록

### 5. 공급망 정책은 release policy와 연결된다

취약점이 심하면 일반 배포보다 빠른 패치가 필요할 수 있다.
반대로 불안정한 업데이트는 release gate에서 멈춰야 한다.

즉 dependency governance는 보안과 릴리스 정책의 교차점이다.

---

## 실전 시나리오

### 시나리오 1: 알려진 취약점이 있는 라이브러리가 발견된다

SBOM에서 영향 범위를 찾고, blast radius와 패치 우선순위를 정한다.

### 시나리오 2: 새 라이브러리가 들어온다

허용 목록과 license 정책을 확인하고, 필요한 경우 ADR을 남긴다.

### 시나리오 3: transitive dependency가 급격히 바뀐다

의존성 잠금과 policy gate로 변화를 통제하고, 필요한 경우 업데이트 전략을 조정한다.

---

## 코드로 보기

```yaml
dependency_policy:
  allowlist:
    - org.slf4j
    - com.fasterxml.jackson
  sbom_scan: required
  vulnerability_threshold: high
  approval: security-team
```

정책은 선언이 아니라 실행 가능한 통제여야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 자유로운 dependency 추가 | 빠르다 | 위험이 커진다 | 초기 실험 |
| allowlist 중심 | 통제가 쉽다 | 유연성이 떨어진다 | 성숙한 제품 |
| SBOM + policy as code | 추적성이 좋다 | 운영 비용이 든다 | 공급망 리스크가 큰 조직 |

dependency governance의 핵심은 **무엇을 쓰는지 아는 것보다, 무엇을 허용하는지 통제하는 것**이다.

---

## 꼬리질문

- 어떤 라이브러리는 자동 업데이트해도 되는가?
- SBOM은 어느 환경에서 생성하고 누가 보는가?
- transitive dependency 취약점은 어떻게 우선순위화할 것인가?
- 예외 라이브러리는 어떻게 기록할 것인가?

## 한 줄 정리

Dependency governance and SBOM policy는 의존성 공급망을 정책과 가시성으로 통제해, 취약점과 변화의 위험을 추적 가능하게 만드는 체계다.

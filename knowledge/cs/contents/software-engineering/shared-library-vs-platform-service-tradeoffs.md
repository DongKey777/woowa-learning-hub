---
schema_version: 3
title: Shared Library vs Platform Service Trade-offs
concept_id: software-engineering/shared-library-vs-platform-service
canonical: true
category: software-engineering
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- platform
- shared-library
- coupling
- reuse
aliases:
- shared library vs platform service
- shared code vs service abstraction
- platform service tradeoff
- reuse boundary decision
- compile time coupling vs deploy coupling
- 공유 라이브러리 플랫폼 서비스 비교
symptoms: []
intents:
- comparison
- design
- deep_dive
prerequisites:
- software-engineering/platform-paved-road
- software-engineering/dependency-governance-sbom
next_docs:
- software-engineering/platform-product-capability-boundaries
- software-engineering/shared-module-guardrails
- software-engineering/service-bootstrap-governance
linked_paths:
- contents/software-engineering/platform-paved-road-tradeoffs.md
- contents/software-engineering/platform-team-product-team-capability-boundaries.md
- contents/software-engineering/architectural-fitness-functions.md
- contents/software-engineering/dependency-governance-sbom-policy.md
- contents/software-engineering/service-bootstrap-governance.md
- contents/software-engineering/build-vs-buy-exit-cost-governance.md
confusable_with:
- software-engineering/shared-module-guardrails
- software-engineering/platform-paved-road
- software-engineering/platform-product-capability-boundaries
forbidden_neighbors: []
expected_queries:
- shared library와 platform service는 코드 재사용, 배포 결합, 운영 책임 관점에서 어떻게 비교해야 해?
- 공통 기능이 자주 바뀌면 shared library보다 platform service가 나을 수 있는 이유는?
- 안정적인 저수준 utility는 왜 platform service보다 shared library가 더 적합할 수 있어?
- shared library가 공용 도메인으로 번지거나 platform service가 도메인 로직을 먹으면 어떤 경계 붕괴가 생겨?
- ownership, contract, deprecation policy, migration path를 두지 않으면 library와 service 모두 결합을 키우는 이유는?
contextual_chunk_prefix: |
  이 문서는 공통 기능을 shared library로 배포할지 platform service로 운영할지 변화 빈도, deploy coupling, runtime boundary, ownership 기준으로 고르는 advanced chooser이다.
---
# Shared Library vs Platform Service Trade-offs

> 한 줄 요약: shared library는 코드 재사용이 쉽고, platform service는 운영과 변경을 중앙화할 수 있지만, 둘 다 경계가 무너지면 결합을 넓히는 방식이 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Platform Paved Road Trade-offs](./platform-paved-road-tradeoffs.md)
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Dependency Governance and SBOM Policy](./dependency-governance-sbom-policy.md)
> - [Service Bootstrap Governance](./service-bootstrap-governance.md)
> - [Build vs Buy, Exit Cost, Integration Governance](./build-vs-buy-exit-cost-governance.md)

> retrieval-anchor-keywords:
> - shared library
> - platform service
> - coupling trade-off
> - reuse boundary
> - centralization
> - distribution boundary
> - shared code
> - service abstraction

## 핵심 개념

공통 기능을 여러 팀이 같이 쓰고 싶을 때, 보통 두 길이 있다.

- shared library: 코드로 공유
- platform service: 네트워크/운영으로 공유

둘 다 장단이 뚜렷하다.

---

## 깊이 들어가기

### 1. shared library는 빠르지만 배포 결합이 생긴다

장점:

- 호출 비용이 낮다
- 개발이 빠르다
- 로컬에서 다루기 쉽다

단점:

- 버전 호환성 문제가 생긴다
- 모든 소비자가 같은 릴리스를 따라야 할 수 있다
- 내부 구현이 퍼지기 쉽다

### 2. platform service는 느리지만 경계가 분명하다

장점:

- 중앙 관리가 쉽다
- 배포 독립성이 있다
- 관측과 정책을 한 곳에서 관리할 수 있다

단점:

- 네트워크 비용이 있다
- 운영 복잡도가 올라간다
- 장애 지점이 생긴다

### 3. 선택 기준은 재사용 빈도가 아니라 변화 빈도다

자주 바뀌는 기능은 shared library로 묶으면 모두가 영향을 받는다.

이 경우 platform service가 나을 수 있다.

반대로 아주 안정적이고 저수준인 유틸은 library가 더 낫다.

### 4. 경계 붕괴를 조심해야 한다

shared library가 사실상 공용 도메인이 되거나,
platform service가 도메인 로직까지 떠안으면 모두 위험해진다.

### 5. governance와 versioning이 필수다

둘 다:

- ownership
- contract
- deprecation policy
- migration path

가 없으면 다시 결합이 커진다.

외부 managed service를 사는 경우에도 이 질문은 그대로 남는다.

---

## 실전 시나리오

### 시나리오 1: 인증 로직을 공유한다

정책이 자주 변하면 서비스화가 유리할 수 있다.

### 시나리오 2: JSON helper를 공유한다

자주 안 바뀌는 저수준 유틸은 library가 적합하다.

### 시나리오 3: 공통 기능이 도메인으로 번진다

library든 service든 boundary를 재점검해야 한다.

---

## 코드로 보기

```text
library = low latency, high compile-time coupling
service = higher latency, lower deploy coupling
```

핵심은 재사용보다 **경계와 변화 비용**이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| shared library | 간단하다 | 배포 결합이 있다 | 안정적인 공통 코드 |
| platform service | 경계가 분명하다 | 운영 비용이 든다 | 변경과 책임이 큰 기능 |
| hybrid | 유연하다 | 복잡하다 | 조직이 크고 요구가 다양할 때 |

shared library vs platform service trade-offs는 재사용 수단 선택이 아니라 **결합 위치를 어디에 둘지 정하는 문제**다.

---

## 꼬리질문

- 이 기능은 얼마나 자주 변하는가?
- 배포 결합을 감당할 수 있는가?
- 플랫폼 서비스로 바꿔야 할 시점은 언제인가?
- library가 도메인 경계를 침식하고 있지 않은가?

## 한 줄 정리

Shared library vs platform service trade-offs는 공통 기능을 코드로 묶을지, 운영 서비스로 분리할지에 따라 생기는 결합과 운영 비용을 비교하는 선택이다.

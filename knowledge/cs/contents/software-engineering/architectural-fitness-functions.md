---
schema_version: 3
title: Architectural Fitness Functions
concept_id: software-engineering/architectural-fitness-functions
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- architectural-fitness
- policy-as-code
- boundary-test
aliases:
- Architectural Fitness Functions
- architecture fitness function
- architecture regression guard
- policy as code architecture lint
- ArchUnit boundary test
- 아키텍처 경계 자동 검증
symptoms:
- 아키텍처 경계를 좋은 구조로 유지하자는 리뷰 말에만 의존하고 CI에서 반복 가능한 rule로 강제하지 않아
- 기능 테스트와 architecture boundary test를 섞어 모듈 의존 방향, schema compatibility, forbidden import 같은 구조 회귀를 놓쳐
- fitness function을 경고판으로만 두고 release gate나 PR block 정책과 연결하지 않아 위반이 누적돼
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/modular-monolith-boundary-enforcement
- software-engineering/policy-as-code
next_docs:
- software-engineering/archunit-brownfield-rollout-playbook
- software-engineering/schema-contract-evolution-cross-service
- software-engineering/event-schema-versioning
linked_paths:
- contents/software-engineering/modular-monolith-boundary-enforcement.md
- contents/software-engineering/ddd-bounded-context-failure-patterns.md
- contents/software-engineering/api-contract-testing-consumer-driven.md
- contents/software-engineering/schema-contract-evolution-cross-service.md
- contents/software-engineering/event-schema-versioning-compatibility.md
- contents/software-engineering/configuration-governance-runtime-safety.md
- contents/software-engineering/policy-as-code-architecture-linting.md
- contents/software-engineering/archunit-brownfield-rollout-playbook.md
confusable_with:
- software-engineering/policy-as-code
- software-engineering/archunit-brownfield-rollout-playbook
- software-engineering/backward-compatibility-gates
forbidden_neighbors: []
expected_queries:
- architectural fitness function은 기능 테스트와 달리 어떤 구조 회귀를 자동으로 잡아?
- ArchUnit 같은 boundary test로 모듈 간 직접 참조나 forbidden dependency를 어떻게 막아?
- API contract test와 schema compatibility check도 architecture fitness function으로 볼 수 있어?
- fitness function을 CI 경고가 아니라 PR block release gate 정책으로 연결하는 기준은 뭐야?
- policy as code가 과해져 개발 속도를 늦추지 않으려면 어떤 규칙부터 자동화해야 해?
contextual_chunk_prefix: |
  이 문서는 architectural fitness function을 모듈 의존성, contract compatibility, schema evolution, configuration policy를 CI와 release gate에서 반복 측정하는 architecture regression guard로 설명하는 advanced playbook이다.
---
# Architectural Fitness Functions

> 한 줄 요약: Architectural fitness function은 아키텍처의 "좋음"을 감으로 판단하지 않고, 코드와 CI에서 반복 측정 가능한 규칙으로 바꾸는 장치다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md)
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)
> - [Schema Contract Evolution Across Services](./schema-contract-evolution-cross-service.md)
> - [Event Schema Versioning and Compatibility](./event-schema-versioning-compatibility.md)
> - [Configuration Governance and Runtime Safety](./configuration-governance-runtime-safety.md)

> retrieval-anchor-keywords:
> - architectural fitness function
> - architecture regression
> - policy as code
> - dependency rule
> - ArchUnit
> - boundary test
> - cross-service testing pyramid
> - architecture guardrail

## 핵심 개념

아키텍처는 시간이 지나면 자연스럽게 무너진다.
그래서 좋은 팀은 "좋은 구조를 유지하자"가 아니라, **구조가 무너지는 순간을 자동으로 감지하는 규칙**을 둔다.

이 규칙이 architectural fitness function이다.

- 모듈 의존 방향이 맞는가
- 서비스 간 계약이 깨지지 않았는가
- 이벤트 스키마가 호환되는가
- 특정 계층이 금지된 의존을 잡고 있지 않은가
- 위험한 configuration key가 정책 없이 바뀌지 않았는가

즉 fitness function은 아키텍처 품질을 측정하는 **지속적 테스트**다.

---

## 깊이 들어가기

### 1. fitness function은 일반 테스트와 다르다

일반 테스트는 기능이 맞는지 본다.
fitness function은 **구조가 아직 허용 가능한지** 본다.

예:

- 단위 테스트: 할인 계산이 맞는가
- fitness function: 주문 모듈이 결제 모듈 내부 클래스를 참조하지 않는가

### 2. 규칙은 자동화 가능해야 한다

좋은 fitness function은 CI에서 돌릴 수 있어야 한다.

예:

- 패키지 의존성 금지
- 공용 API 외 내부 참조 금지
- 특정 레이어에서 DB 직접 접근 금지
- event schema backward compatibility 확인
- contract test 통과
- config schema와 value range 확인

사람 리뷰만으로는 시간이 지나면 흐려진다.

### 3. cross-service testing pyramid는 fitness function의 일부다

서비스가 여러 개가 되면 테스트 피라미드도 시스템 단위로 봐야 한다.

권장 방향:

- unit tests: 각 서비스 내부 로직
- contract tests: 서비스 간 경계
- integration tests: 데이터소스/브로커 연결
- E2E tests: 가장 중요한 사용자 흐름만 최소화

핵심은 E2E를 많이 하는 것이 아니라, **서비스 간 계약을 더 얇고 정확하게 테스트하는 것**이다.

### 4. fitness function은 경고가 아니라 정책이어야 한다

측정만 하고 무시하면 의미가 없다.

예:

- 허용 경계 초과 시 build fail
- 특정 의존성 등장 시 PR block
- schema incompatibility 시 release gate stop
- latency budget 초과 시 canary pause

즉 fitness function은 경고판이 아니라 **정책 집행 장치**여야 한다.

### 5. 아키텍처 목표마다 다른 fitness function이 필요하다

목표가 다르면 측정도 달라진다.

| 목표 | fitness function 예시 |
|---|---|
| 경계 유지 | 모듈 간 직접 참조 금지 |
| 계약 안정성 | provider/consumer contract test |
| 진화 가능성 | schema backward compatibility |
| 운영 안전성 | release gate + rollback policy |
| 느슨한 결합 | 특정 패키지 import 금지 |

즉 아키텍처는 추상 미학이 아니라 측정 대상이다.

---

## 실전 시나리오

### 시나리오 1: 모듈러 모놀리스가 조금씩 무너진다

배포는 하나인데 모듈 간 의존이 꼬이기 시작했다.
fitness function으로 직접 참조와 순환 의존을 막으면 무너짐을 초기에 잡을 수 있다.

### 시나리오 2: 서비스 간 계약이 자주 깨진다

contract test를 fitness function으로 두면, 배포 전에 소비자 영향을 확인할 수 있다.

### 시나리오 3: 이벤트 버전이 섞여 들어온다

schema compatibility 체크를 CI에 넣으면 event replay와 소비자 파손을 줄일 수 있다.

---

## 코드로 보기

```java
@AnalyzeClasses(packages = "com.example")
public class ArchitectureRulesTest {

    @ArchTest
    static final ArchRule no_direct_payment_dependency =
        noClasses().that().resideInAPackage("..order..")
            .should().dependOnClassesThat().resideInAPackage("..payment.internal..");
}
```

이런 규칙은 "알아서 지키자"를 "깨지면 CI에서 막자"로 바꾼다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 수동 리뷰 | 유연하다 | 일관성이 약하다 | 초기 프로젝트 |
| fitness function | 자동화된다 | 규칙 설계가 필요하다 | 경계가 중요한 시스템 |
| policy as code | 강제력이 높다 | 과하면 개발 속도가 늦다 | 조직이 크고 사고 비용이 클 때 |

fitness function은 사람의 판단을 없애는 게 아니라, **반복 가능한 판단을 자동화**하는 것이다.

---

## 꼬리질문

- 어떤 아키텍처 규칙은 CI에서 강제하고 어떤 규칙은 리뷰로 둘 것인가?
- cross-service testing pyramid의 비율은 어떻게 정할 것인가?
- fitness function이 너무 많아 개발자가 무뎌지지 않는가?
- 정책 위반을 예외 처리할 기준은 무엇인가?

## 한 줄 정리

Architectural fitness functions는 아키텍처의 경계를 자동 검증해 구조 붕괴를 조기에 막는 정책 기반 테스트다.

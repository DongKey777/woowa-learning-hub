---
schema_version: 3
title: Clean Architecture vs Layered Architecture, Modular Monolith
concept_id: software-engineering/clean-architecture-layered-modular-monolith
canonical: false
category: software-engineering
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- architecture-choice
- dependency-direction
- module-boundary
aliases:
- clean architecture vs layered architecture
- modular monolith
- clean vs layered
- hexagonal vs clean architecture
- dependency rule
- inward dependency
- module boundary
- distributed monolith
- 아키텍처 선택 기준
- 레이어드 vs 클린 아키텍처
- 모듈러 모놀리스 뭐예요
- 패키지 분리만 하면 모듈인가요
symptoms:
- layered랑 clean이 대체 관계인지 같이 써도 되는지 헷갈려요
- 패키지는 나눴는데 왜 modular monolith 같지 않다는 피드백을 받는지 모르겠어요
- 도메인 규칙을 안쪽에 둬야 한다는 말이 실무 구조 선택과 어떻게 연결되는지 감이 안 와요
intents:
- comparison
- design
prerequisites:
- software-engineering/architecture-layering-fundamentals
- software-engineering/ports-and-adapters-beginner-primer
next_docs:
- software-engineering/modular-monolith-boundary-enforcement
- software-engineering/bounded-context-failure-patterns
- software-engineering/anti-corruption-layer
linked_paths:
- contents/software-engineering/architecture-layering-fundamentals.md
- contents/software-engineering/ports-and-adapters-beginner-primer.md
- contents/software-engineering/modular-monolith-boundary-enforcement.md
- contents/software-engineering/ddd-bounded-context-failure-patterns.md
- contents/software-engineering/anti-corruption-layer-integration-patterns.md
- contents/software-engineering/ddd-hexagonal-consistency.md
confusable_with:
- software-engineering/architecture-layering-fundamentals
- software-engineering/ports-and-adapters-beginner-primer
- software-engineering/ddd-hexagonal-consistency
forbidden_neighbors:
  - contents/software-engineering/modular-monolith-boundary-enforcement.md
  - contents/software-engineering/ddd-bounded-context-failure-patterns.md
  - contents/software-engineering/anti-corruption-layer-integration-patterns.md
expected_queries:
- 서비스 하나로 시작할 때 layered와 clean 중 어디까지 가져가야 하는지 판단 기준이 뭐야?
- domain이 JPA나 framework annotation을 직접 알면 왜 clean하지 않다고 말하는 거야?
- order와 payment를 같은 배포 안에 두면서도 modular monolith처럼 경계를 지키려면 뭘 봐야 해?
- hexagonal, clean, layered가 각각 어떤 질문에 답하는지 한 번에 비교해줘
- distributed monolith가 되지 않으려면 모듈 경계를 코드에서 어떻게 강제해야 해?
contextual_chunk_prefix: |
  이 문서는 layered architecture, clean architecture, modular monolith를
  서로 다른 설계 질문으로 구분해 비교하려는 학습자를 위한 chooser다. 계층을
  나누는 문제인지, 의존성 방향을 안쪽으로 고정하는 문제인지, 같은 배포 안에서
  모듈 경계를 어떻게 강제할지 판단하는 문제인지 헷갈릴 때 읽는다. 패키지만
  나눈 구조가 왜 modular monolith가 아닌지, domain이 framework에 묶이면 왜
  clean하지 않다고 말하는지, hexagonal과 clean이 어떤 관계인지 같은 질문을
  구조 선택 기준으로 연결한다.
---
# Clean Architecture vs Layered Architecture, Modular Monolith

**난이도: 🔴 Advanced**

> 설계 트랙에서 자주 묻는 아키텍처 선택과 모듈 경계를 정리한 문서

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [Layered Architecture](#layered-architecture)
- [Clean Architecture](#clean-architecture)
- [비교 포인트](#비교-포인트)
- [Modular Monolith](#modular-monolith)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

> 관련 문서:
> - [Software Engineering README: Clean Architecture vs Layered Architecture, Modular Monolith](./README.md#clean-architecture-vs-layered-architecture-modular-monolith)
> - [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
> - [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md)
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [Anti-Corruption Layer Integration Patterns](./anti-corruption-layer-integration-patterns.md)
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
>
> retrieval-anchor-keywords: clean architecture, layered architecture, modular monolith, ports and adapters beginner, hexagonal architecture beginner, dependency rule, inward dependency, package boundary, module boundary, domain isolation, distributed monolith, architecture choice, hexagonal vs clean architecture

## 왜 중요한가

아키텍처는 클래스 배치 문제가 아니라, **변경이 어디까지 퍼질지 결정하는 규칙**이다.

- 설계가 단순해야 빠르게 개발할 수 있다
- 경계가 분명해야 기능 추가가 안전하다
- 의존성 방향이 정리되어야 테스트와 리팩토링이 쉬워진다

즉, 좋은 아키텍처는 “보기 좋은 구조”보다 **변경 비용을 낮추는 구조**다.

---

## Layered Architecture

Layered Architecture는 보통 다음처럼 나눈다.

- Presentation
- Application
- Domain
- Infrastructure

장점:

- 이해하기 쉽다
- 팀이 합의하기 쉽다
- CRUD 중심 시스템에 잘 맞는다

한계:

- 계층이 단순 전달 코드로 붕괴하기 쉽다
- 도메인 규칙이 서비스 계층에 흩어지기 쉽다
- 인프라 의존이 위로 새어 올라오기 쉽다

즉, 레이어는 편하지만 **규칙이 약하면 금방 평평해진다**.

---

## Clean Architecture

Clean Architecture는 **안쪽이 바깥쪽에 의존하지 않도록** 만드는 구조다.

핵심 감각:

- 도메인 규칙을 중심에 둔다
- 외부 기술은 경계 바깥으로 밀어낸다
- 의존성은 안쪽으로만 향한다

장점:

- 비즈니스 규칙이 기술과 분리된다
- 테스트가 쉬워진다
- DB, 프레임워크 교체 영향이 줄어든다

입출력 경계를 코드로 더 구체적으로 보고 싶다면 [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)를 같이 보면 된다.

단점:

- 작은 시스템에는 과할 수 있다
- 경계를 잘못 나누면 오히려 복잡해진다
- 추상화 계층이 많아질 수 있다

---

## 비교 포인트

실무에서는 “무조건 Clean”이 아니라, **변경 지점이 어디냐**를 먼저 본다.

- 도메인 규칙이 핵심이면 Clean 쪽 이점이 크다
- 단순 조회/입력 위주면 Layered가 더 빠르다
- 팀 숙련도가 낮으면 추상화가 오히려 비용이 된다

비교 기준은 다음이 유용하다.

- 도메인 복잡도
- 테스트 요구 수준
- 프레임워크 교체 가능성
- 팀의 설계 숙련도

즉, 아키텍처 선택은 정답 찾기가 아니라 **비용과 변화량의 균형**이다.

---

## Modular Monolith

Modular Monolith는 하나의 배포 단위 안에서 **기능 단위 모듈을 강하게 분리**하는 방식이다.

특징:

- 배포는 하나
- 내부는 모듈별로 나눈다
- 모듈 간 직접 참조를 줄인다

장점:

- 마이크로서비스보다 운영이 단순하다
- 모듈 경계를 연습하기 좋다
- 나중에 서비스 분리가 쉬워진다

주의점:

- 패키지 분리만 하고 실제 의존성은 섞일 수 있다
- 모듈 간 통신 규칙이 없으면 금방 비대해진다

좋은 기준:

- 모듈은 “폴더”가 아니라 **소유권이 있는 기능 경계**여야 한다
- 모듈 내부는 마음껏 바꾸되, 외부 노출은 최소화해야 한다

---

## 시니어 관점 질문

- 이 시스템은 Layered로 충분한가, Clean이 필요한가?
- 경계를 더 나누는 것이 실제로 유지보수 비용을 줄이는가?
- 모듈 경계를 패키지 수준이 아니라 의존성 수준에서 강제하고 있는가?
- 이 모놀리스는 단순히 큰 코드베이스인가, 아니면 모듈이 살아 있는가?

## 다음 읽기

- 다음 한 걸음: [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md) - 추상적인 모듈 경계 선택을 패키지 규칙과 아키텍처 테스트로 내리는 바로 다음 단계다.
- README로 돌아가기: [Software Engineering README](./README.md#clean-architecture-vs-layered-architecture-modular-monolith) - 같은 묶음의 DDD, ACL, migration 문서로 다시 이동하기 쉽다.

---
schema_version: 3
title: Architecture Runway and Refactoring Window
concept_id: software-engineering/architecture-runway
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids:
- missions/payment
review_feedback_tags:
- architecture-runway
- refactoring-window
- evolutionary-architecture
aliases:
- Architecture Runway and Refactoring Window
- architecture runway
- refactoring window
- preparatory design
- migration window
- evolutionary architecture refactor budget
- 리팩터링 창 runway
symptoms:
- 미래 변경을 위해 port, adapter, feature flag, contract test를 깔아두고도 실제 migration/refactoring window를 확보하지 않아 추상화가 빚으로 남아
- 변화 시나리오와 owner 없이 runway를 미리 만들어 overengineering이 되고 삭제/통합 기준도 없어
- migration window와 runway를 같은 것으로 착각해 준비 없이 전환하거나 준비만 하고 전환을 못 해
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/technical-debt-refactoring-timing
- software-engineering/architectural-debt-interest
next_docs:
- software-engineering/brownfield-modularization
- software-engineering/strangler-fig-migration-contract-cutover
- software-engineering/prototype-spike-productionization
linked_paths:
- contents/software-engineering/technical-debt-refactoring-timing.md
- contents/software-engineering/modular-monolith-boundary-enforcement.md
- contents/software-engineering/brownfield-modularization-strategy.md
- contents/software-engineering/strangler-fig-migration-contract-cutover.md
- contents/software-engineering/adr-decision-records-at-scale.md
- contents/software-engineering/prototype-spike-productionization-boundaries.md
- contents/software-engineering/architectural-debt-interest-model.md
confusable_with:
- software-engineering/architectural-debt-interest
- software-engineering/brownfield-modularization
- software-engineering/strangler-fig-migration-contract-cutover
forbidden_neighbors: []
expected_queries:
- architecture runway와 refactoring window는 각각 준비 구조와 실행 시간이라는 점에서 어떻게 달라?
- PaymentPort adapter contract test feature flag를 runway로 깔아둘 때 overengineering을 피하는 기준은 뭐야?
- runway를 만들었지만 실제 전환하지 않으면 왜 architecture debt가 될 수 있어?
- migration window와 refactor budget을 캘린더와 release cadence에 맞춰 설계하는 방법을 알려줘
- 미래 변경 가능성이 있을 때 runway를 언제 만들고 언제 삭제하거나 통합해야 해?
contextual_chunk_prefix: |
  이 문서는 architecture runway와 refactoring window를 preparatory design, port/adapter/contract test/feature flag, migration window, refactor budget, evolutionary architecture 관점에서 연결하는 advanced playbook이다.
---
# Architecture Runway and Refactoring Window

> 한 줄 요약: architecture runway는 나중에 바꾸기 쉽게 미리 깔아두는 구조이고, refactoring window는 그 구조를 실제로 진화시킬 수 있도록 시간을 확보하는 운영 전략이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Technical Debt Refactoring Timing](./technical-debt-refactoring-timing.md)
> - [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md)
> - [Brownfield Modularization Strategy](./brownfield-modularization-strategy.md)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [Prototype, Spike, and Productionization Boundaries](./prototype-spike-productionization-boundaries.md)

> retrieval-anchor-keywords:
> - architecture runway
> - refactoring window
> - preparatory design
> - changeability
> - sequencing
> - refactor budget
> - migration window
> - evolutionary architecture

## 핵심 개념

architecture runway는 지금 당장 완성된 구조가 아니라, 나중의 변화를 위해 미리 깔아두는 준비된 경로다.

문제는 runway만 있으면 충분하지 않다는 것이다.
실제로 변경하려면 refactoring window, 즉 **변경을 흡수할 시간과 여유**가 필요하다.

따라서 핵심은:

- 무엇을 미리 준비할지
- 언제 그 준비를 실제로 쓸지
- 어느 정도의 refactor budget을 확보할지

를 같이 보는 것이다.

---

## 깊이 들어가기

### 1. runway는 미래 변경의 전제다

예:

- 도메인 포트 미리 분리
- 데이터 접근 캡슐화
- 이벤트 발행 경로 확보
- feature flag 준비
- ACL/adapter 포인트 확보

이런 준비가 없으면 나중에 변경이 너무 비싸다.

### 2. runway만 만들고 사용하지 않으면 빚이 된다

미리 만든 추상화가 실제로 쓰이지 않으면 오히려 복잡도만 늘어난다.
prototype에서 productionization으로 갈 가능성이 있을 때만 runway를 먼저 까는 편이 낫다.

그래서 runway는 다음 질문을 가져야 한다.

- 앞으로 1~2개의 변경 시나리오가 실제로 있는가?
- 이 추상화가 언제 삭제/통합될 수 있는가?
- runway를 유지할 owner가 있는가?

### 3. refactoring window는 캘린더와 연동돼야 한다

변경은 늘 바쁜 시기와 겹치기 쉽다.

그래서 다음이 필요하다.

- 안정화 기간
- 기능 freeze와 분리된 refactor 기간
- 릴리스 전후 버퍼
- 대규모 마이그레이션 창

즉 리팩터링은 "틈날 때"가 아니라 **계획된 창**이어야 한다.

### 4. runway와 migration window는 다르다

- runway: 나중에 바꾸기 위한 준비 구조
- migration window: 실제로 바꾸는 시간

둘을 섞으면 준비만 하다가 전환을 못 하거나, 반대로 준비 없이 밀어붙이게 된다.

### 5. refactor budget은 운영 정책이어야 한다

무작정 기능만 만들면 runway는 쌓이기만 한다.

그래서 팀은 일정 비율을 유지해야 한다.

- 기술 부채 상환
- 경계 정리
- 추상화 정리
- API/이벤트 호환성 개선

이 부분은 [Technical Debt Refactoring Timing](./technical-debt-refactoring-timing.md)과 연결된다.

---

## 실전 시나리오

### 시나리오 1: 결제 교체를 준비한다

당장 교체하지 않더라도 PaymentPort, adapter, contract test를 runway로 미리 깔아둔다.

### 시나리오 2: 모듈을 쪼개기 위한 준비를 한다

모듈러 모놀리스에서 경계 enforcement를 먼저 만들고, 다음 refactoring window에 실제 분리를 진행한다.

### 시나리오 3: 대규모 계약 변경이 예정되어 있다

새 schema를 먼저 준비하고, migration window에 맞춰 consumer adoption을 진행한다.

---

## 코드로 보기

```text
runway:
  port -> adapter -> contract test -> feature flag

window:
  refactor sprint -> migration -> rollback check -> cleanup
```

준비와 실행은 같은 일이 아니다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| runway 없이 즉시 변경 | 빠르다 | 위험하다 | 아주 작은 변경 |
| runway 우선 | 미래 변경이 쉬워진다 | 과설계 위험 | 변화 가능성이 높을 때 |
| runway + window | 가장 현실적 | 관리가 필요하다 | 장기 운영 시스템 |

architecture runway는 선행 투자이고, refactoring window는 그 투자를 회수하는 시간이다.

---

## 꼬리질문

- runway를 언제 만들고 언제 삭제할 것인가?
- refactor budget은 어떻게 지킬 것인가?
- 준비만 하고 사용하지 않는 추상화는 어떻게 회수할 것인가?
- migration window는 누가 언제 결정하는가?

## 한 줄 정리

Architecture runway와 refactoring window는 미래 변경을 위한 준비와 실행 시간을 함께 설계해, 진화 가능한 구조를 유지하는 전략이다.

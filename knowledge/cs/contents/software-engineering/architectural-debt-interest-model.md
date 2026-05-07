---
schema_version: 3
title: Architectural Debt Interest Model
concept_id: software-engineering/architectural-debt-interest
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- architectural-debt
- refactoring-timing
- change-friction
aliases:
- Architectural Debt Interest Model
- architecture debt interest
- debt principal vs interest
- refactoring cost change friction
- architectural debt payoff
- 구조적 부채 이자 모델
symptoms:
- architectural debt를 나중에 한 번 고칠 principal로만 보고 변경 지연, 테스트 비용, 장애 복구 난이도 같은 반복 이자를 계산하지 않아
- 변경 빈도가 높은 주문/결제/계약/외부 연동 경계에서 작은 결합이 계속 기능 개발 속도를 갉아먹는 신호를 놓쳐
- debt payoff를 큰 리팩터링 한 번으로만 계획해 runway, fitness function, 작은 상환 단위를 같이 설계하지 못해
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/technical-debt-refactoring-timing
- software-engineering/architecture-runway
next_docs:
- software-engineering/architectural-fitness-functions
- software-engineering/brownfield-modularization
- software-engineering/migration-carrying-cost-delay
linked_paths:
- contents/software-engineering/technical-debt-refactoring-timing.md
- contents/software-engineering/architecture-runway-refactoring-window.md
- contents/software-engineering/brownfield-modularization-strategy.md
- contents/software-engineering/architectural-fitness-functions.md
- contents/software-engineering/service-maturity-model.md
- contents/software-engineering/migration-carrying-cost-cost-of-delay.md
confusable_with:
- software-engineering/technical-debt-refactoring-timing
- software-engineering/architecture-runway
- software-engineering/migration-carrying-cost-delay
forbidden_neighbors: []
expected_queries:
- architectural debt를 principal과 interest로 나눠서 보는 이유를 설명해줘
- 구조적 부채의 이자가 변경 충돌, 테스트 비용, rollout 지연, 온보딩 지연으로 나타나는 신호는 뭐야?
- 변경 빈도가 높은 영역의 작은 coupling이 왜 architecture debt interest를 크게 만들어?
- architecture runway와 fitness function이 debt interest를 낮추는 방식은 어떻게 달라?
- 큰 리팩터링 대신 boundary 하나씩 점진 상환하는 판단 기준을 알려줘
contextual_chunk_prefix: |
  이 문서는 architectural debt를 principal과 recurring interest로 나눠 change friction, coupling cost, test breakage, rollout delay, refactoring payoff를 판단하는 advanced playbook이다.
---
# Architectural Debt Interest Model

> 한 줄 요약: architectural debt는 나중에 갚을 비용이 아니라, 지금 구조를 유지하는 동안 매일 붙는 이자까지 포함해 봐야 하는 복합 부채다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Technical Debt Refactoring Timing](./technical-debt-refactoring-timing.md)
> - [Architecture Runway and Refactoring Window](./architecture-runway-refactoring-window.md)
> - [Brownfield Modularization Strategy](./brownfield-modularization-strategy.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Service Maturity Model](./service-maturity-model.md)

> retrieval-anchor-keywords:
> - architectural debt
> - debt interest
> - refactoring cost
> - change friction
> - coupling cost
> - maintenance overhead
> - architecture payoff
> - debt principal

## 핵심 개념

기술 부채는 흔히 "나중에 고칠 것"으로 말해진다.
하지만 architecture debt는 단순 principal만이 아니라 이자가 크다.

이자란:

- 새 기능 개발이 느려짐
- 변경 충돌 증가
- 테스트 비용 상승
- 장애 복구가 어려워짐
- 신규 온보딩이 느려짐

즉 architecture debt는 시간이 지날수록 **변경 속도를 갉아먹는 구조적 비용**이다.

---

## 깊이 들어가기

### 1. debt principal과 interest를 분리해서 봐야 한다

principal:

- 한번에 정리할 때 드는 직접 비용

interest:

- 유지하면서 계속 내는 반복 비용

어떤 구조는 principal이 커도 interest가 작다.
반대로 작은 결합 하나가 오래 남아 큰 이자를 만들 수 있다.

### 2. 이자는 변경 빈도에 비례한다

자주 바뀌는 영역일수록 debt interest가 빠르게 쌓인다.

예:

- 주문/결제 경계
- 계약/이벤트 모델
- 외부 연동 adapter

### 3. 정량 신호를 찾을 수 있다

architecture debt interest의 징후:

- 변경 하나에 많은 파일이 바뀜
- 테스트가 자주 깨짐
- rollout이 길어짐
- 회귀 버그가 반복됨
- 문서와 코드가 자주 어긋남

이런 신호는 [Architectural Fitness Functions](./architectural-fitness-functions.md)와 연결된다.

### 4. runway가 있으면 이자를 줄일 수 있다

port, boundary, contract test, observability를 미리 준비하면, 부채의 이자율을 낮출 수 있다.

즉 runway는 debt를 없애는 게 아니라 **이자율을 낮추는 투자**다.

### 5. debt 상환은 자주 작게 해야 한다

한 번에 큰 리팩터링은 위험하다.

좋은 방법:

- 경계 하나씩 정리
- contract test 추가
- 읽기 경로 먼저 분리
- 오래된 adapter 제거

---

## 실전 시나리오

### 시나리오 1: shared module이 모든 팀을 묶는다

한 모듈 변경이 여러 팀을 동시에 흔들면 debt interest가 높다.

### 시나리오 2: 계약 변경이 너무 어렵다

문서나 schema보다 coupling이 문제라면 구조적 부채다.

### 시나리오 3: 신규 기능보다 유지보수가 더 오래 걸린다

이자는 principal보다 더 빨리 판단할 수 있는 신호다.

---

## 코드로 보기

```yaml
architectural_debt:
  principal: boundary_refactor
  interest: slow_changes
  mitigation: contract_tests
```

이자까지 보지 않으면 부채를 과소평가하게 된다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 방치 | 당장 빠르다 | 이자가 커진다 | 거의 없음 |
| 한 번에 상환 | 깔끔하다 | 위험하다 | 작은 시스템 |
| 점진 상환 | 현실적이다 | 시간이 든다 | 운영 중 시스템 |

architecture debt는 금액이 아니라 **변경 속도를 갉아먹는 이자**로 봐야 한다.

---

## 꼬리질문

- debt interest를 어떤 지표로 볼 것인가?
- 어떤 부채는 지금 상환하고 어떤 것은 runway로 버틸 것인가?
- 변경 빈도가 높은 영역은 어디인가?
- 부채 상환이 실제로 throughput을 높였는가?

## 한 줄 정리

Architectural debt interest model은 구조적 부채를 principal과 이자로 나눠, 시간이 지날수록 커지는 유지 비용을 의사결정에 반영하는 틀이다.

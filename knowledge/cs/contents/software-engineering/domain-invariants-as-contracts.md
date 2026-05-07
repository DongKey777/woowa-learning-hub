---
schema_version: 3
title: Domain Invariants as Contracts
concept_id: software-engineering/domain-invariants-as-contracts
canonical: true
category: software-engineering
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- domain-invariant
- contract-testing
- semantic-contract
- validation
aliases:
- Domain Invariants as Contracts
- domain invariant contract
- business rule semantic contract
- invariant breach detection
- schema validation vs invariant
- 상태 불변식 계약 테스트
symptoms:
- schema는 맞고 필드도 존재하지만 상태 전이, 금액 범위, null 의미 같은 비즈니스 invariant가 깨져 downstream 장애가 나
- 내부 validation으로만 지키던 domain rule이 API 응답, 이벤트, replay, backfill 경계를 넘어가며 consumer contract를 깨뜨려
intents:
- deep_dive
- design
- troubleshooting
prerequisites:
- software-engineering/bounded-context-failure-patterns
- software-engineering/api-contract-testing
next_docs:
- software-engineering/schema-contract-evolution-cross-service
- software-engineering/event-schema-versioning
- software-engineering/contract-drift-governance
linked_paths:
- contents/software-engineering/ddd-bounded-context-failure-patterns.md
- contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md
- contents/software-engineering/api-contract-testing-consumer-driven.md
- contents/software-engineering/schema-contract-evolution-cross-service.md
- contents/software-engineering/event-schema-versioning-compatibility.md
- contents/software-engineering/domain-capability-heatmap.md
confusable_with:
- software-engineering/schema-contract-evolution-cross-service
- software-engineering/api-contract-testing
- software-engineering/event-schema-versioning
forbidden_neighbors: []
expected_queries:
- domain invariant를 단순 validation이 아니라 consumer contract로 다뤄야 하는 이유가 뭐야?
- schema validation은 통과하지만 business invariant가 깨지는 사례를 설명해줘
- 주문 상태 전이나 금액 음수 금지 같은 invariant를 contract test로 외부화하려면 어떻게 해?
- replay나 backfill 과정에서 과거 이벤트가 현재 invariant를 깨뜨릴 때 어떻게 대응해?
- API contract와 event schema에 semantic invariant를 함께 반영하는 방법을 알려줘
contextual_chunk_prefix: |
  이 문서는 domain invariant를 내부 validation을 넘어 API response, event schema, replay, contract test까지 이어지는 semantic contract로 다루는 advanced bridge이다.
---
# Domain Invariants as Contracts

> 한 줄 요약: domain invariant는 내부 규칙처럼 보이지만, 실제로는 서비스와 소비자 사이에서 절대 깨지면 안 되는 계약 조건으로 다뤄야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)
> - [Schema Contract Evolution Across Services](./schema-contract-evolution-cross-service.md)
> - [Event Schema Versioning and Compatibility](./event-schema-versioning-compatibility.md)

> retrieval-anchor-keywords:
> - domain invariant
> - business rule
> - contract condition
> - consumer expectation
> - state invariant
> - validation boundary
> - invariant breach
> - semantic contract

## 핵심 개념

Invariant는 특정 상태가 절대 깨지면 안 되는 규칙이다.
도메인에서는 이것을 단순 validation으로 두면 안 된다.

왜냐하면 invariant는 종종 다음과 연결되기 때문이다.

- API 응답 의미
- 이벤트 순서
- DB 상태 전이
- 외부 소비자 기대

즉 domain invariant는 도메인 내부 규칙이면서 동시에 **계약 수준의 약속**이다.

---

## 깊이 들어가기

### 1. invariant는 단순 입력 검증보다 넓다

예를 들어:

- 주문은 결제 없이 출고되면 안 된다
- 취소된 주문은 다시 완료될 수 없다
- 잔액은 음수가 되면 안 된다

이 규칙은 한 메서드 안에서만 검사하는 것이 아니라, 여러 경로를 통해 유지되어야 한다.

### 2. invariant breach는 즉시 드러나지 않을 수 있다

어떤 위반은 바로 예외를 내지만, 어떤 위반은 나중에야 문제를 만든다.

예:

- 잘못된 상태 전이가 이벤트로 전파됨
- 계약상 허용되지 않는 null이 downstream으로 전달됨
- 대시보드에는 정상처럼 보이지만 정산에서 깨짐

그래서 invariant는 저장 전, 발행 전, 노출 전 모두에서 확인해야 한다.

### 3. invariant는 contract test로 외부화할 수 있다

내부 규칙이 소비자에게 중요한 의미를 가진다면 계약 테스트로 옮겨야 한다.

예:

- status는 특정 상태 집합만 허용
- 금액은 음수가 아니어야 함
- 필수 식별자는 null 불가

이렇게 하면 변경 시 경계가 자동으로 지켜진다.

### 4. schema와 invariant는 분리하지만 함께 봐야 한다

스키마가 맞아도 invariant가 깨질 수 있다.

예:

- 필드는 존재하지만 조합이 불가능함
- enum 값은 유효하지만 전이 순서가 틀림
- payload는 파싱되지만 비즈니스 의미가 어긋남

그래서 invariant는 schema validation을 넘어선다.

### 5. invariant를 문서로만 두면 drift한다

중요한 invariant는 문서와 코드, 테스트, 계약에 동시에 있어야 한다.

권장 위치:

- domain model
- validation layer
- contract test
- replay test
- ADR

---

## 실전 시나리오

### 시나리오 1: 주문 상태 전이가 꼬인다

`CANCELLED -> PAID` 같은 전이가 들어오면 단순 bug가 아니라 invariant breach다.

### 시나리오 2: 외부 소비자가 특정 필드를 믿고 있다

`discountAmount`는 항상 0 이상이어야 한다면, 이 규칙은 API contract로도 드러나야 한다.

### 시나리오 3: 이벤트 replay 중 규칙이 깨진다

과거 이벤트는 당시 규칙을 따랐지만, 현재 invariant가 더 강해졌다면 replay compatibility를 다시 봐야 한다.

---

## 코드로 보기

```java
public class Order {
    public void confirm() {
        if (status == OrderStatus.CANCELLED) {
            throw new IllegalStateException("cancelled order cannot be confirmed");
        }
        status = OrderStatus.CONFIRMED;
    }
}
```

이 규칙이 단순 예외가 아니라, 계약적으로도 보장되어야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 내부 validation만 | 단순하다 | 외부가 깨질 수 있다 | 아주 작은 시스템 |
| invariant + contract test | 경계가 강하다 | 테스트 비용이 든다 | 서비스가 분리될 때 |
| invariant + schema + replay test | 가장 안전하다 | 운영 복잡도 증가 | 이벤트 기반 시스템 |

domain invariant는 "코드가 아는 규칙"이 아니라, **시스템이 지켜야 하는 계약 조건**으로 봐야 한다.

---

## 꼬리질문

- 어떤 invariant는 외부 contract로 끌어올려야 하는가?
- invariant breach를 어디서 탐지할 것인가?
- replay와 backfill 시 invariant는 어떻게 유지할 것인가?
- schema가 맞는데 의미가 깨지는 경우를 어떻게 잡을 것인가?

## 한 줄 정리

Domain invariants are contracts는 내부 도메인 규칙을 외부 계약과 함께 관리해, 상태와 의미가 깨지는 순간을 시스템적으로 막는 접근이다.

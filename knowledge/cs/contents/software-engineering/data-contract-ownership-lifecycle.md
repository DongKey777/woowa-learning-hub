---
schema_version: 3
title: Data Contract Ownership and Lifecycle
concept_id: software-engineering/data-contract-lifecycle
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- data-contract
- ownership
- schema-governance
aliases:
- Data Contract Ownership and Lifecycle
- data contract ownership
- contract lifecycle
- contract steward
- schema governance
- contract deprecation
symptoms:
- data contract를 schema file로만 보고 field meaning, producer, consumer, steward, notification, deprecation/sunset 책임을 정의하지 않아
- producer owner와 contract steward, consumer owner 역할을 구분하지 않아 필드 의미 변경과 consumer impact 판단이 흐려져
- contract lifecycle에서 생성만 관리하고 deprecated, sunset, retired 전환 조건과 consumer migration 완료 증거를 놓쳐
intents:
- design
- deep_dive
- troubleshooting
prerequisites:
- software-engineering/schema-contract-evolution-cross-service
- software-engineering/contract-registry-governance
next_docs:
- software-engineering/event-schema-versioning
- software-engineering/consumer-migration-playbook
- software-engineering/api-versioning-contracts-acl
linked_paths:
- contents/software-engineering/schema-contract-evolution-cross-service.md
- contents/software-engineering/event-schema-versioning-compatibility.md
- contents/software-engineering/service-ownership-catalog-boundaries.md
- contents/software-engineering/consumer-migration-playbook-contract-adoption.md
- contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md
- contents/software-engineering/contract-registry-governance.md
confusable_with:
- software-engineering/contract-registry-governance
- software-engineering/schema-contract-evolution-cross-service
- software-engineering/event-schema-versioning
forbidden_neighbors: []
expected_queries:
- data contract는 schema가 아니라 field meaning, owner, consumers, lifecycle, notification까지 포함한다는 뜻이 뭐야?
- producer owner, contract steward, consumer owner는 각각 어떤 책임을 가져야 해?
- data contract lifecycle draft proposed active deprecated sunset retired에서 누가 무엇을 검증해야 해?
- 계약 의미가 바뀔 때 notification과 consumer migration window를 data contract ownership에 포함해야 하는 이유는?
- contract registry가 data contract drift와 deprecated field 생존을 어떻게 줄여?
contextual_chunk_prefix: |
  이 문서는 data contract를 schema file이 아니라 field semantics, producer owner, contract steward, consumer owner, lifecycle, registry, deprecation까지 포함하는 운영 계약으로 다루는 advanced playbook이다.
---
# Data Contract Ownership and Lifecycle

> 한 줄 요약: data contract는 스키마만 의미하지 않고, 누가 정의하고, 검증하고, 변경 공지하고, 폐기까지 책임지는지까지 포함하는 운영 계약이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Schema Contract Evolution Across Services](./schema-contract-evolution-cross-service.md)
> - [Event Schema Versioning and Compatibility](./event-schema-versioning-compatibility.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)

> retrieval-anchor-keywords:
> - data contract ownership
> - contract lifecycle
> - contract steward
> - producer responsibility
> - consumer responsibility
> - schema governance
> - contract deprecation
> - contract registry

## 핵심 개념

데이터 계약은 단순한 schema 문서가 아니다.
좋은 data contract는 다음을 포함한다.

- 어떤 필드가 무엇을 의미하는가
- 누가 producer인가
- 누가 consumer인가
- 누가 변경 승인을 하는가
- 언제 폐기하는가
- 호환성 기준은 무엇인가

즉 data contract ownership은 스키마를 소유하는 것이 아니라 **의미와 변경 책임을 소유하는 것**이다.

---

## 깊이 들어가기

### 1. contract owner와 data owner는 같지 않을 수 있다

어떤 팀은 데이터를 생산하지만, 계약의 해석과 소비자 영향은 다른 팀이 더 잘 알 수 있다.

그래서 다음 역할을 분리할 수 있다.

- producer owner: 데이터를 발행하는 팀
- contract steward: 의미와 호환성을 관리하는 팀
- consumer owner: 데이터를 사용하는 팀

이 분리가 없으면 변경 판단이 흐려진다.

### 2. contract lifecycle은 생성보다 폐기가 더 어렵다

대부분의 계약은 시작보다 종료에서 실패한다.

필요한 상태:

- draft
- proposed
- active
- deprecated
- sunset
- retired

각 상태마다 누가 무엇을 해야 하는지 명시해야 한다.

### 3. contract registry가 있어야 한다

계약이 여러 개가 되면 문서만으로는 추적이 어렵다.

registry에는 최소한 다음이 필요하다.

- contract id
- owner
- dependent consumers
- version
- status
- next review date

이 메타데이터가 있어야 변경이 시스템적으로 관리된다.

### 4. contract change는 notification과 함께 간다

변경이 기술적으로 안전해도, 소비자가 모르면 장애처럼 보인다.

그래서 contract ownership에는 공지가 포함된다.

- 언제 바뀌는지
- 누가 영향받는지
- 대체 필드는 무엇인지
- migration window가 언제인지

### 5. ownership이 없으면 drift가 늦게 발견된다

계약 소유권이 없으면 필드 의미가 서서히 변한다.

그 결과:

- 문서와 코드가 다르다
- 소비자가 잘못된 의미를 믿는다
- deprecated 필드가 계속 살아남는다

---

## 실전 시나리오

### 시나리오 1: 이벤트 payload의 의미가 바뀐다

새 필드 추가는 쉬워도, 기존 필드의 의미 변화는 계약 ownership 승인 없이는 안 된다.

### 시나리오 2: 여러 소비자가 같은 계약을 읽는다

소비자마다 기대가 다르므로, registry 기반으로 영향 범위를 먼저 확인해야 한다.

### 시나리오 3: 계약을 sunset해야 한다

contract registry에서 deprecated 상태로 전환하고, consumer migration 완료 후 retired로 바꾼다.

---

## 코드로 보기

```yaml
contract:
  id: order-event-v2
  owner: commerce-platform
  steward: data-platform
  status: active
  consumers:
    - order-bff
    - fulfillment-service
```

계약은 문서가 아니라, 책임과 메타데이터가 연결된 운영 객체다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 소유권 없음 | 빠르다 | drift가 늦게 보인다 | 매우 작은 시스템 |
| producer만 소유 | 단순하다 | consumer 영향이 약하다 | 내부 단일 소비자 |
| producer + steward + registry | 추적성이 좋다 | 운영 비용이 든다 | 서비스가 여러 개일 때 |

data contract ownership은 스키마 관리가 아니라 **진화 가능한 책임 구조**다.

---

## 꼬리질문

- 계약의 최종 책임자는 누구인가?
- deprecated 계약은 언제 retired로 바꿀 것인가?
- consumer registry는 실제로 최신인가?
- 계약 변경 공지는 누가 어떤 채널로 하는가?

## 한 줄 정리

Data contract ownership and lifecycle은 데이터 의미와 변경 책임을 소유하고, 계약의 생성부터 폐기까지를 추적 가능한 상태로 운영하는 방식이다.

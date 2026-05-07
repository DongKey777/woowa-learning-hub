---
schema_version: 3
title: Event Schema Versioning and Compatibility
concept_id: software-engineering/event-schema-versioning
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- event-schema
- versioning
- compatibility
- replay
aliases:
- Event Schema Versioning and Compatibility
- event schema compatibility
- event envelope versioning
- replay compatibility event schema
- publisher consumer compatibility
- 이벤트 스키마 버전 호환성
symptoms:
- event schemaVersion은 올렸지만 old consumer가 새 필드를 무시할 수 있는지, new consumer가 old event를 읽을 수 있는지 검증하지 않아
- replay, backfill, projection rebuild가 과거 이벤트 버전을 다시 읽을 때 nullable field, enum expansion, strict parser 때문에 깨져
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/schema-contract-evolution-cross-service
- software-engineering/outbox-inbox-domain-events
next_docs:
- software-engineering/event-sourcing-cqrs
- software-engineering/domain-invariants-as-contracts
- software-engineering/contract-drift-governance
linked_paths:
- contents/software-engineering/schema-contract-evolution-cross-service.md
- contents/software-engineering/outbox-inbox-domain-events.md
- contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md
- contents/software-engineering/monolith-to-msa-failure-patterns.md
- contents/software-engineering/strangler-fig-migration-contract-cutover.md
- contents/software-engineering/domain-invariants-as-contracts.md
- contents/software-engineering/event-sourcing-cqrs-adoption-criteria.md
confusable_with:
- software-engineering/schema-contract-evolution-cross-service
- software-engineering/api-versioning-contracts-acl
- software-engineering/event-sourcing-cqrs
forbidden_neighbors: []
expected_queries:
- 이벤트 스키마 버전 관리는 API 버전보다 왜 더 보수적으로 해야 하는지 설명해줘
- backward compatible와 forward compatible event schema를 publisher consumer 관점에서 비교해줘
- OrderPlaced 이벤트에 optional field나 enum 값을 추가할 때 어떤 순서로 배포해야 해?
- replay와 backfill이 과거 이벤트를 다시 읽을 때 schemaVersion과 upcaster를 어떻게 설계해야 해?
- envelope version과 payload version을 분리하면 event evolution에 어떤 장점이 있어?
contextual_chunk_prefix: |
  이 문서는 event schema versioning을 publisher/consumer compatibility, optional field, envelope, replay/backfill 안전성까지 포함해 다루는 advanced playbook이다.
---
# Event Schema Versioning and Compatibility

> 한 줄 요약: 이벤트 스키마 버전 관리는 새 필드를 추가하는 일이 아니라, 발행자와 소비자가 서로 다른 버전을 동시에 읽고도 안전하게 수렴하게 만드는 일이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Schema Contract Evolution Across Services](./schema-contract-evolution-cross-service.md)
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)

> retrieval-anchor-keywords:
> - event schema versioning
> - schema compatibility
> - envelope version
> - consumer tolerance
> - publisher compatibility
> - replay compatibility
> - nullable fields
> - event evolution

## 핵심 개념

이벤트는 한 번 발행되면 여러 소비자가 오랫동안 읽는다.
그래서 이벤트 스키마는 API보다 더 보수적으로 다뤄야 한다.

핵심은 세 가지다.

- 옛 소비자가 새 이벤트를 버틸 수 있어야 한다
- 새 소비자가 옛 이벤트를 버틸 수 있어야 한다
- replay/backfill이 과거 이벤트를 다시 읽어도 깨지지 않아야 한다

즉 이벤트 버전 관리는 현재 배포보다 **미래 재처리 가능성**을 더 중시한다.

---

## 깊이 들어가기

### 1. 이벤트는 append-only 사고로 봐야 한다

이벤트는 일반적인 DTO보다 수정이 훨씬 어렵다.
한 번 소비된 적이 있으면, 나중에 다시 읽히는 경우가 많기 때문이다.

따라서 보통 다음 원칙을 따른다.

- 기존 필드는 유지
- 새 필드는 optional로 추가
- 필드 의미를 바꾸지 않음
- 제거는 아주 늦게 함

### 2. version은 필수지만 충분조건이 아니다

`schemaVersion=2`를 넣는다고 자동으로 안전해지지 않는다.

중요한 것은 버전 숫자보다 아래다.

- 어떤 필드가 늘었는가
- 어떤 소비자가 무시 가능한가
- 어떤 소비자가 strict parser인가
- 어떤 replay job이 과거 버전을 읽는가

즉 버전은 표시이고, 호환성은 행동이다.

### 3. backwards와 forwards를 같이 봐야 한다

| 방향 | 의미 | 실무 질문 |
|---|---|---|
| backward compatible | 새 생산자가 옛 소비자를 깨지 않음 | 새 필드 추가 후 옛 소비자는 무시할 수 있는가? |
| forward compatible | 옛 생산자가 새 소비자를 크게 깨지 않음 | 새 소비자가 없는 필드를 기본값으로 처리할 수 있는가? |

이 두 방향이 모두 필요하면, 버전 체계와 파서 전략을 더 보수적으로 짜야 한다.

### 4. envelope와 payload를 분리하면 진화가 쉬워진다

이벤트 envelope에는 공통 메타데이터를 두고, payload에는 도메인 내용을 둔다.

예:

- eventId
- occurredAt
- schemaVersion
- aggregateId

이렇게 분리하면 버전 관리와 재처리 도구를 만들기 쉬워진다.

### 5. replay compatibility가 실전에서 가장 중요할 수 있다

지금 소비자가 잘 도는 것보다, 나중에 재처리할 때 안 깨지는 것이 더 중요할 수 있다.

왜냐하면 운영 중 문제는 종종:

- 누락 이벤트 backfill
- 소비자 재기동
- 보정 job
- 데이터 마이그레이션

에서 드러나기 때문이다.

---

## 실전 시나리오

### 시나리오 1: `OrderPlaced`에 새 필드를 추가한다

새로운 `promotionId`를 넣고 싶다.

안전한 순서:

1. 새 필드 optional 추가
2. 소비자 기본값 처리 추가
3. 발행자에 채우기 시작
4. replay job 검증
5. 오래된 가정 제거

### 시나리오 2: status enum을 확장한다

기존 `CREATED/PAID/CANCELLED`에 `PAYMENT_PENDING`을 추가한다.

이때 strict parser가 있으면 바로 깨질 수 있으므로, 소비자별 허용 범위를 먼저 확인해야 한다.

### 시나리오 3: 이벤트를 재처리했더니 옛 버전이 섞여 있다

backfill 작업은 최신 이벤트만 보지 않는다.
그래서 버전별 테스트와 변환기가 필요하다.

---

## 코드로 보기

```java
public record OrderPlacedEvent(
    String eventId,
    String aggregateId,
    int schemaVersion,
    String orderStatus,
    String promotionId
) {
    public boolean isCompatibleWithLegacyConsumer() {
        return schemaVersion >= 1;
    }
}
```

실제 핵심은 메서드가 아니라, 소비자가 어떤 필드를 믿고 어떤 필드를 무시하는지다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 버전 없음 | 단순하다 | 진화가 위험하다 | 내부 한정, 수명이 짧을 때 |
| payload 버전 | 명시적이다 | 버전 분기 비용이 든다 | 소비자가 여러 개일 때 |
| envelope + payload 버전 | 재처리가 쉽다 | 구조가 더 복잡하다 | event-driven 시스템일 때 |

이벤트는 "보내면 끝"이 아니라, **나중에도 다시 읽히는 장기 계약**이다.

---

## 꼬리질문

- replay job은 어떤 버전까지 읽어야 하는가?
- 소비자 strictness를 어디서 강제할 것인가?
- 새 필드를 optional로 두는 것이 정말 충분한가?
- 이벤트 버전 폐기는 언제 가능한가?

## 한 줄 정리

이벤트 스키마 버전 관리는 생산자와 소비자의 속도 차이를 흡수하는 호환성 설계이며, replay와 backfill까지 버텨야 비로소 완성된다.

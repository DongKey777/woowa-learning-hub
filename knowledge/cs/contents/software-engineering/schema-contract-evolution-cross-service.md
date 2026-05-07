---
schema_version: 3
title: Schema Contract Evolution Across Services
concept_id: software-engineering/schema-contract-evolution-cross-service
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- schema-evolution
- contract-testing
- compatibility
- event-schema
aliases:
- schema evolution across services
- contract compatibility
- expand and contract schema
- backward forward compatible schema
- event schema evolution
- 서비스 간 스키마 계약 진화
symptoms:
- 필드 rename이나 enum 의미 변경을 단순 스키마 수정으로 처리해 느린 소비자와 replay/backfill 경로가 깨져
- 새 필드 추가, 병행 지원, 읽기 전환, 옛 필드 제거 순서 없이 producer와 consumer를 동시에 바꾸려 해
- DB schema, API response, event payload의 compatibility 방향을 구분하지 않아 rollback과 재처리 가능성이 떨어져
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/api-versioning-contracts-acl
- software-engineering/api-contract-testing
next_docs:
- software-engineering/contract-drift-governance
- software-engineering/backward-compatibility-gates
- software-engineering/event-schema-versioning
linked_paths:
- contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md
- contents/software-engineering/api-contract-testing-consumer-driven.md
- contents/software-engineering/strangler-fig-migration-contract-cutover.md
- contents/software-engineering/outbox-inbox-domain-events.md
- contents/software-engineering/monolith-to-msa-failure-patterns.md
confusable_with:
- software-engineering/api-versioning-contracts-acl
- software-engineering/event-schema-versioning
- software-engineering/contract-drift-governance
forbidden_neighbors: []
expected_queries:
- 서비스 간 schema evolution에서 backward compatible과 forward compatible은 어떤 방향의 호환성을 말해?
- enum 값 추가나 status 의미 변경이 필드 추가보다 더 위험할 수 있는 이유를 설명해줘
- expand and contract로 DB 컬럼 rename이나 API field migration을 안전하게 진행하는 순서를 알려줘
- 이벤트 payload에 optional field를 추가할 때 replay와 old consumer compatibility를 어떻게 봐야 해?
- producer와 consumer가 다른 속도로 배포될 때 contract test와 rollout 순서를 어떻게 잡아?
contextual_chunk_prefix: |
  이 문서는 DB, API, event schema가 생산자와 소비자 사이에서 안전하게 진화하도록 compatibility 방향과 expand-and-contract 절차를 설계하는 advanced playbook이다.
---
# Schema Contract Evolution Across Services

> 한 줄 요약: 스키마 진화는 필드를 추가하는 문제가 아니라, 생산자와 소비자가 서로 다른 속도로 바뀌어도 계약이 무너지지 않게 만드는 문제다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)

> retrieval-anchor-keywords:
> - schema evolution
> - contract compatibility
> - expand and contract
> - backward compatible
> - forward compatible
> - default value
> - consumer tolerance
> - event schema

## 핵심 개념

스키마 계약은 DB 테이블, 이벤트 payload, API response, 메시지 envelope까지 모두 포함한다.
겉으로는 필드 몇 개 바꾸는 일처럼 보여도, 실제로는 **다른 속도로 진화하는 시스템 사이의 약속**이다.

좋은 스키마 진화는 다음을 만족한다.

- 기존 소비자가 갑자기 깨지지 않는다
- 새 소비자가 옛 데이터도 읽을 수 있다
- 백필과 재처리가 가능하다
- 롤아웃 순서가 안전하다

---

## 깊이 들어가기

### 1. 호환성은 방향이 있다

스키마 호환성은 대충 "되냐 안 되냐"가 아니다.

- backward compatible: 새 프로듀서가 옛 소비자를 깨지 않는다
- forward compatible: 옛 프로듀서가 새 소비자를 크게 깨지 않는다
- full compatibility: 양쪽 모두 버틴다

이 차이를 모르면 컬럼 하나 추가하는 것도 위험해진다.

### 2. 진짜 위험한 변경은 의미 변화다

형식 변경보다 더 위험한 것은 같은 이름이 다른 뜻이 되는 경우다.

예:

- `status=ACTIVE`가 예전에는 "사용 가능"이었는데 나중엔 "로그인 가능"으로 바뀜
- `amount`가 세전 금액인지 세후 금액인지 모호해짐
- `deletedAt`이 soft delete인지 archive인지 섞임

이런 변경은 필드를 유지한 채 의미만 바꾸기 때문에, 소비자는 늦게 깨진다.

### 3. expand and contract가 기본이다

안전한 진화의 대표 패턴은 다음 순서다.

1. 새 필드 추가
2. 생산자와 소비자가 새 필드 병행 지원
3. 새 경로로 읽기/쓰기 전환
4. 옛 필드 제거

이 방식은 느리지만, rollback 가능성이 높다.

### 4. DB 스키마와 이벤트 스키마는 다르게 봐야 한다

DB는 보통 직접적인 쓰기 대상이라 마이그레이션 순서가 중요하다.
이벤트는 replay될 수 있으므로 더 보수적으로 다뤄야 한다.

이벤트에서 특히 중요한 것:

- versioned payload
- optional field tolerance
- unknown field ignoring
- replayer compatibility

### 5. 소비자 중심 계약이 더 중요해질 수 있다

모든 내부 구조를 한 스키마로 묶으려 하면, 결국 가장 느린 소비자에 맞춰야 한다.

그래서 계약은 "진실의 단일 원본"이 아니라 **소비자별 요구를 만족하는 호환 규칙**으로 관리해야 한다.

---

## 실전 시나리오

### 시나리오 1: 주문 상태 enum 확장

기존:

- `CREATED`
- `PAID`
- `SHIPPED`

새 요구:

- `PAYMENT_FAILED`
- `CANCELLED`
- `RETURNED`

이때 enum을 교체만 하면 이전 소비자가 깨질 수 있다.
먼저 문서와 계약 테스트를 바꾸고, 소비자들이 새 값을 무시/처리할 수 있게 만든 뒤 노출을 넓힌다.

### 시나리오 2: 이벤트 payload에 새 필드를 추가

`OrderPlaced` 이벤트에 `promotionId`를 추가한다.

안전한 접근:

- 새 필드를 optional로 추가
- 기존 소비자가 null을 처리하도록 변경
- 새 소비자가 없을 때도 동작하도록 기본값 설계

### 시나리오 3: DB 컬럼 rename

`delivery_status`를 `fulfillment_status`로 바꾸고 싶다.

직접 rename은 위험하다.
보통은:

- 새 컬럼 추가
- 양쪽에 쓰기
- 읽기 경로 전환
- old column 제거

이게 expand/contract의 전형이다.

---

## 코드로 보기

```java
public record OrderEventV2(
    String eventId,
    String aggregateId,
    int schemaVersion,
    String status,
    String promotionId
) {
    public static OrderEventV2 fromLegacy(OrderEventV1 legacy) {
        return new OrderEventV2(
            legacy.eventId(),
            legacy.aggregateId(),
            2,
            legacy.status(),
            null
        );
    }
}
```

버전 번호보다 더 중요한 것은 소비자가 이 payload를 **안전하게 무시하거나 확장해서 읽을 수 있는가**다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 즉시 rename/delete | 단순하다 | 소비자 충돌이 크다 | 내부 전용, 짧은 수명일 때 |
| expand and contract | 안전하다 | 기간이 길어진다 | 운영 중 서비스일 때 |
| versioned schema | 명시적이다 | 버전이 늘어난다 | 외부 소비자가 많을 때 |

스키마 진화에서 가장 비싼 것은 작업량이 아니라 **호환성 깨짐의 복구 비용**이다.

---

## 꼬리질문

- 이 변경은 형식 변화인가, 의미 변화인가?
- 소비자 중 가장 늦게 바뀌는 쪽은 누구인가?
- 새 필드를 optional로 두면 정말 안전한가?
- replay나 backfill이 이 스키마를 다시 읽을 수 있는가?

## 한 줄 정리

스키마 계약 진화는 필드 추가 기술이 아니라, 생산자와 소비자의 진화 속도를 분리해서도 시스템을 안전하게 유지하는 호환성 설계다.

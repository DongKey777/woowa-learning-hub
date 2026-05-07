---
schema_version: 3
title: Event Upcaster Compatibility Patterns
concept_id: design-pattern/event-upcaster-compatibility-patterns
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- event-upcaster
- event-schema-evolution
- legacy-replay-compatibility
aliases:
- event upcaster
- event compatibility layer
- legacy event replay
- event schema evolution
- semantic versioned event
- upcast chain
- replay resume gate
- old event compatibility
- 이벤트 업캐스터
- 과거 이벤트 호환
symptoms:
- 오래된 outbox/event store record를 replay할 때 현재 consumer가 legacy schema를 해석하지 못한다
- 필드 rename 같은 구조 변화와 totalAmount 의미 변경 같은 semantic change를 같은 난이도로 취급한다
- legacy field가 없을 때 null이나 0을 묵시적으로 넣어 과거 데이터의 의미를 현재 모델에 왜곡한다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/domain-event-translation-pipeline
- design-pattern/event-envelope-pattern
- design-pattern/tolerant-reader-event-contract-pattern
next_docs:
- design-pattern/event-contract-drift-triage-rebuilds
- design-pattern/snapshot-versioning-compatibility-pattern
- design-pattern/checkpoint-snapshot-pattern
linked_paths:
- contents/design-pattern/domain-event-translation-pipeline.md
- contents/design-pattern/domain-events-vs-integration-events.md
- contents/design-pattern/event-contract-drift-triage-rebuilds.md
- contents/design-pattern/snapshot-versioning-compatibility-pattern.md
- contents/design-pattern/tolerant-reader-event-contract-pattern.md
- contents/design-pattern/event-envelope-pattern.md
- contents/design-pattern/checkpoint-snapshot-pattern.md
- contents/language/java/json-null-missing-unknown-field-schema-evolution.md
confusable_with:
- design-pattern/tolerant-reader-event-contract-pattern
- design-pattern/snapshot-versioning-compatibility-pattern
- design-pattern/event-contract-drift-triage-rebuilds
- design-pattern/domain-event-translation-pipeline
forbidden_neighbors: []
expected_queries:
- Event Upcaster는 OrderPlacedV1 같은 과거 이벤트를 현재 V2 모델로 어떻게 끌어올려?
- event schema evolution에서 구조 변화와 의미 변화는 upcaster 난이도가 어떻게 달라?
- legacy field가 없을 때 UNKNOWN이나 LEGACY_MIGRATED 같은 명시 값을 쓰는 이유가 뭐야?
- replay 전에 upcaster chain과 legacy fixture test를 준비해야 하는 이유는 뭐야?
- 오래된 이벤트를 일괄 migration할지 runtime upcaster로 호환할지 어떤 trade-off가 있어?
contextual_chunk_prefix: |
  이 문서는 Event Upcaster Compatibility Patterns playbook으로, 저장된 legacy event를
  현재 consumer가 해석할 수 있는 schema/version으로 변환하며, 구조 변화와 semantic
  change를 구분하고 UNKNOWN/LEGACY 같은 명시적 compatibility policy와 replay fixture
  test를 설계하는 방법을 설명한다.
---
# Event Upcaster Compatibility Patterns

> 한 줄 요약: Event Upcaster는 과거 이벤트를 현재 해석 가능한 계약으로 끌어올리는 호환 계층이고, 구조 변화보다 의미 변화가 더 클수록 버전 전략과 테스트가 중요해진다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Domain Event Translation Pipeline](./domain-event-translation-pipeline.md)
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
> - [Event Contract Drift Triage for Rebuilds](./event-contract-drift-triage-rebuilds.md)
> - [Snapshot Versioning and Compatibility Pattern](./snapshot-versioning-compatibility-pattern.md)
> - [Tolerant Reader for Event Contracts](./tolerant-reader-event-contract-pattern.md)
> - [Event Sourcing: 변경 이력을 진실의 원천으로 쓰는 패턴 언어](./event-sourcing-pattern-language.md)
> - [Event Envelope Pattern](./event-envelope-pattern.md)
> - [Checkpoint / Snapshot Pattern](./checkpoint-snapshot-pattern.md)
> - [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](../language/java/json-null-missing-unknown-field-schema-evolution.md)
> - [Schema Migration, Partitioning, CDC, CQRS](../database/schema-migration-partitioning-cdc-cqrs.md)
> - [Historical Backfill / Replay Platform 설계](../system-design/historical-backfill-replay-platform-design.md)

---

## 핵심 개념

이벤트는 한 번 저장되면 오래 산다.  
문제는 코드와 도메인 언어는 그동안 계속 바뀐다는 점이다.

- 필드가 추가된다
- 값 객체가 도입된다
- 상태 이름이 바뀐다
- 하나의 이벤트가 둘로 쪼개진다

이때 과거 이벤트를 버릴 수 없다면, 현재 코드가 과거 이벤트를 이해하도록 중간 호환 계층이 필요하다.  
그 역할을 하는 것이 Event Upcaster다.

### Retrieval Anchors

- `event upcaster`
- `event compatibility layer`
- `legacy event replay`
- `event schema evolution`
- `semantic versioned event`
- `upcast chain`
- `tolerant reader`
- `event contract drift triage`
- `replay resume gate`

---

## 깊이 들어가기

### 1. upcaster는 저장된 과거 이벤트를 현재 해석 모델로 바꾼다

upcaster는 보통 rehydrate/replay 직전 또는 message deserialize 직후 동작한다.

- `OrderPlacedV1` -> `OrderPlacedV2`
- 누락 필드 기본값 채우기
- enum 이름 변경 보정
- 여러 legacy event를 현재 의미로 매핑

즉 원본 이벤트를 수정하는 게 아니라 **현재 코드가 이해할 수 있는 형태로 끌어올리는 것**이다.

### 2. 구조 변화보다 의미 변화가 더 위험하다

단순 구조 변화는 비교적 쉽다.

- 새 optional field 추가
- 필드명 rename
- nested object 도입

하지만 의미 변화는 더 어렵다.

- `totalAmount`가 세전에서 세후 금액으로 바뀜
- `APPROVED`가 `AUTHORIZED`와 `CAPTURED`로 분리됨
- 하나의 `OrderSubmitted`가 `CheckoutAccepted`와 `OrderCreated`로 해체됨

이 경우 upcaster는 단순 mapper가 아니라 **명시적 compatibility policy**가 된다.

rebuild 중에는 여기서 한 단계 더 나가서, 지금 보고 있는 실패가 단순 schema drift인지, upcaster coverage gap인지, 아니면 semantic incompatibility인지 먼저 분류해야 한다.  
그 triage와 replay resume gate는 [Event Contract Drift Triage for Rebuilds](./event-contract-drift-triage-rebuilds.md)에서 따로 본다.

### 3. upcast chain은 짧게 유지하는 편이 안전하다

버전이 많아지면 다음 유혹이 생긴다.

- V1 -> V2 -> V3 -> V4를 매번 순차 변환

가능은 하지만 체인이 길수록 다음이 커진다.

- 성능 비용
- 디버깅 난이도
- 중간 버전 의미 누적 오차

그래서 보통은 다음 중 하나를 택한다.

- 자주 쓰는 최신 target으로 직접 upcast
- 일정 시점 이후 snapshot/checkpoint로 오래된 replay 범위 축소
- major semantic break 때는 별도 stream/contract로 분리

### 4. upcaster는 묵시적 기본값보다 명시적 결정을 선호해야 한다

legacy field가 없을 때 그냥 `null`이나 `0`을 넣는 건 위험하다.

- 실제로 알 수 없는 값인가
- 도메인 기본값인가
- 외부 계약상 UNKNOWN이어야 하는가

이 차이를 숨기면 과거 데이터가 현재 의미를 왜곡한다.

### 5. replay 가능성은 테스트 없이는 보장되지 않는다

upcaster는 평소 잘 안 보이지만, 장애 복구/재적재/리플레이 때 크게 터진다.  
그래서 다음 테스트가 중요하다.

- 실제 legacy fixture replay
- 버전별 golden sample
- snapshot 이전/이후 혼합 replay
- semantic change 문서화

---

## 실전 시나리오

### 시나리오 1: 주문 채널 필드 추가

예전 `OrderPlacedV1`에는 채널 정보가 없고, 새 모델은 `salesChannel`을 요구한다.  
이 경우 `UNKNOWN`이나 `LEGACY_MIGRATED` 같은 명시적 값을 채워 현재 모델로 끌어올릴 수 있다.

### 시나리오 2: 결제 상태 세분화

옛날 `APPROVED` 한 상태가 현재는 `AUTHORIZED`와 `CAPTURED`로 나뉜다면, replay 맥락 없이 하나로 확정할 수 없을 수 있다.  
이때는 compatibility enum, 보조 이벤트 조회, 별도 migration policy가 필요하다.

### 시나리오 3: 과거 이벤트 재처리

오래된 outbox/event store 데이터를 신규 projection에 재적재할 때 upcaster가 없으면 신규 consumer가 바로 깨질 수 있다.

---

## 코드로 보기

### legacy event

```java
public record OrderPlacedV1(
    String orderId,
    long totalAmount
) {}
```

### current event

```java
public record OrderPlacedV2(
    String orderId,
    long totalAmount,
    String salesChannel
) {}
```

### upcaster

```java
public class OrderPlacedUpcaster {
    public OrderPlacedV2 upcast(OrderPlacedV1 legacy) {
        return new OrderPlacedV2(
            legacy.orderId(),
            legacy.totalAmount(),
            "UNKNOWN"
        );
    }
}
```

### chain registry

```java
public interface EventUpcaster {
    boolean supports(String eventType, int schemaVersion);
    EventEnvelope<?> upcast(EventEnvelope<?> legacyEnvelope);
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| upcaster로 호환 유지 | replay와 재처리가 가능하다 | 버전 관리와 테스트 비용이 든다 | 오래 사는 event store/outbox |
| 과거 이벤트를 일괄 migration | runtime 단순성 | 대규모 이관과 롤백 부담 | 이벤트 양이 관리 가능하고 downtime 허용될 때 |
| 의미 break 시 별도 stream 분리 | 경계가 선명하다 | 소비자/운영 경로가 늘어난다 | semantic change가 큰 경우 |

판단 기준은 다음과 같다.

- 단순 구조 변화는 upcaster로 흡수 가능하다
- 의미 변화가 크면 compatibility policy나 새 stream을 검토한다
- replay가 중요하면 fixture 기반 테스트를 먼저 만든다

---

## 꼬리질문

> Q: upcaster는 필드 rename 정도만 처리하나요?
> 의도: 구조 변화와 의미 변화 난이도를 구분하는지 본다.
> 핵심: 아니다. 더 어려운 건 의미 변화이며, 이때는 정책과 계약 판단이 필요하다.

> Q: 모든 이벤트를 최신 버전으로 한 번에 migration하면 더 낫지 않나요?
> 의도: offline migration과 runtime compatibility의 trade-off를 보는 질문이다.
> 핵심: 경우에 따라 가능하지만, 데이터량과 롤백 비용이 커질 수 있다.

> Q: legacy 값이 없을 때 기본값을 넣어도 되나요?
> 의도: null/default 남용을 경계하는지 확인한다.
> 핵심: 도메인 의미가 명확할 때만 그렇고, 아니면 UNKNOWN/LEGACY 같은 명시적 상태가 더 안전하다.

## 한 줄 정리

Event Upcaster는 과거 이벤트를 현재 코드가 해석 가능한 계약으로 끌어올리는 호환 계층이며, 의미 변화가 클수록 버전 전략과 replay 테스트가 핵심이 된다.

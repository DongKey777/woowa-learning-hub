---
schema_version: 3
title: Snapshot Versioning and Compatibility Pattern
concept_id: design-pattern/snapshot-versioning-compatibility-pattern
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- snapshot-versioning
- snapshot-compatibility
- restore-format-version
aliases:
- snapshot versioning
- snapshot compatibility
- snapshot invalidation
- restore format version
- snapshot upcast
- checkpoint schema drift
- versioned snapshot
- snapshot restore compatibility
- 스냅샷 버전
- 복원 포맷 호환성
symptoms:
- event schema version은 관리하지만 snapshot format version은 두지 않아 replay는 되는데 snapshot restore가 깨진다
- snapshot을 단순 cache로만 보고 오래된 format이 runtime state에 silent corruption을 주입할 수 있음을 놓친다
- event upcaster가 있으면 snapshot compatibility도 자동으로 해결된다고 생각한다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/checkpoint-snapshot-pattern
- design-pattern/event-upcaster-compatibility-patterns
- design-pattern/event-sourcing-pattern-language
next_docs:
- design-pattern/process-manager-state-store-recovery
- design-pattern/projection-rebuild-backfill-cutover-pattern
- design-pattern/event-contract-drift-triage-rebuilds
linked_paths:
- contents/design-pattern/checkpoint-snapshot-pattern.md
- contents/design-pattern/event-upcaster-compatibility-patterns.md
- contents/design-pattern/event-sourcing-pattern-language.md
- contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md
- contents/design-pattern/process-manager-state-store-recovery.md
confusable_with:
- design-pattern/checkpoint-snapshot-pattern
- design-pattern/event-upcaster-compatibility-patterns
- design-pattern/process-manager-state-store-recovery
- design-pattern/event-contract-drift-triage-rebuilds
forbidden_neighbors: []
expected_queries:
- Snapshot versioning은 event versioning과 별개로 restore format version을 왜 가져야 해?
- snapshot은 replay optimization인데도 오래 살면 legacy data가 되어 silent corruption을 만들 수 있는 이유가 뭐야?
- snapshot compatibility에서 invalidate and replay, snapshot upcast, partial restore는 어떻게 선택해?
- event upcaster가 있어도 snapshot format drift는 별도 policy가 필요한 이유가 뭐야?
- process manager state store도 snapshot versioning 문제와 비슷하다는 말은 무슨 뜻이야?
contextual_chunk_prefix: |
  이 문서는 Snapshot Versioning and Compatibility Pattern playbook으로, snapshot을
  단순 cache가 아니라 오래 사는 restore artifact로 보고 snapshot format version,
  invalidate-and-replay, snapshot upcast, partial restore, process manager state compatibility
  전략을 설계하는 방법을 설명한다.
---
# Snapshot Versioning and Compatibility Pattern

> 한 줄 요약: snapshot은 replay 최적화 수단이지만 오래 살수록 schema/version drift가 생기므로, snapshot format version과 invalidation/upcast 전략을 같이 설계해야 복원이 안전하다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Checkpoint / Snapshot Pattern](./checkpoint-snapshot-pattern.md)
> - [Event Upcaster Compatibility Patterns](./event-upcaster-compatibility-patterns.md)
> - [Event Sourcing: 변경 이력을 진실의 원천으로 쓰는 패턴 언어](./event-sourcing-pattern-language.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Process Manager State Store and Recovery Pattern](./process-manager-state-store-recovery.md)

---

## 핵심 개념

snapshot은 읽기 성능과 복원 속도를 위해 넣는다.  
하지만 시간이 지나면 snapshot 자체가 legacy data가 된다.

- 필드 구조 변경
- 값 객체 도입
- enum rename
- aggregate 경계 조정

이때 이벤트만 versioning을 생각하고 snapshot은 안 건드리면, replay는 되는데 snapshot restore가 깨지는 이상한 상태가 생긴다.

그래서 snapshot에도 다음이 필요하다.

- snapshot format version
- compatibility policy
- invalidate vs upcast decision
- replay boundary rules

### Retrieval Anchors

- `snapshot versioning`
- `snapshot compatibility`
- `snapshot invalidation`
- `restore format version`
- `snapshot upcast`
- `checkpoint schema drift`

---

## 깊이 들어가기

### 1. snapshot은 캐시 같지만 truth-adjacent data다

snapshot은 event log의 shortcut일 뿐이라고 생각하기 쉽다.  
하지만 실제 복원 경로에 들어가면 사실상 runtime state의 일부가 된다.

그래서 snapshot format이 깨지면:

- startup restore 실패
- replay shortcut 불가
- 오래된 snapshot이 잘못된 상태를 주입

### 2. snapshot version과 event version은 별개다

이 둘을 같이 보면 안 된다.

- event version: 사건 표현의 진화
- snapshot version: 복원 상태 표현의 진화

같은 event set도 snapshot representation은 다르게 바뀔 수 있다.

### 3. 호환 전략은 세 가지가 많다

- invalidate and replay: 버리기
- snapshot upcast: 최신 format으로 끌어올리기
- partial restore + replay tail: 일부 필드만 복원 후 나머지는 replay

어떤 걸 택할지는 다음에 달린다.

- replay 비용
- snapshot 수량
- semantic break 크기

### 4. snapshot은 event보다 더 쉽게 silent corruption을 만든다

이벤트는 replay 중 오류가 드러나기 쉽다.  
반면 snapshot은 한 번 restore되면 이상한 상태가 quietly 퍼질 수 있다.

그래서 snapshot compatibility는 더 보수적으로 보는 편이 좋다.

### 5. process manager state store도 사실상 snapshot versioning 문제를 가진다

long-running workflow state store 역시 복원 가능한 snapshot에 가깝다.

- workflow status enum 변경
- retry metadata 구조 변경
- deadline token shape 변경

그래서 workflow state recovery와 snapshot versioning은 감각이 비슷하다.

---

## 실전 시나리오

### 시나리오 1: enum rename

기존 snapshot의 `APPROVED`가 새 모델에선 `AUTHORIZED`로 바뀌었다면 restore 시 mapping이 필요하다.

### 시나리오 2: 값 객체 도입

예전에는 `amount: 1000`이었지만 지금은 `Money(currency, amount)`라면 snapshot upcast 또는 invalidate가 필요하다.

### 시나리오 3: aggregate 구조 재편

snapshot이 너무 예전 구조를 반영하면 부분 restore보다 full replay가 더 안전할 수 있다.

---

## 코드로 보기

### versioned snapshot

```java
public record VersionedSnapshot(
    String aggregateId,
    int snapshotVersion,
    long aggregateVersion,
    String payload
) {}
```

### compatibility decision

```java
public interface SnapshotCompatibilityPolicy {
    boolean canRestore(int snapshotVersion);
    boolean shouldReplayFromScratch(int snapshotVersion);
}
```

### simple upcast

```java
public class OrderSnapshotUpcaster {
    public OrderSnapshotV2 upcast(OrderSnapshotV1 legacy) {
        return new OrderSnapshotV2(
            legacy.orderId(),
            "KRW",
            legacy.amount()
        );
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| snapshot version 무시 | 구현이 빠르다 | 시간이 지나면 복원 실패나 silent corruption이 난다 | 거의 권장하지 않음 |
| invalidate and replay | 논리가 단순하다 | replay 비용이 크다 | snapshot 수가 적고 replay가 감당 가능할 때 |
| snapshot upcast | restore가 빠르다 | compatibility code와 테스트가 필요하다 | replay 비용이 큰 큰 상태 |

판단 기준은 다음과 같다.

- snapshot도 독립된 versioned artifact로 본다
- semantic break가 크면 invalidate가 더 안전할 수 있다
- restore path는 fixture 기반 테스트가 필요하다

---

## 꼬리질문

> Q: snapshot은 어차피 optimization인데 그냥 지우고 replay하면 되지 않나요?
> 의도: replay 비용과 운영 시간을 함께 보는지 본다.
> 핵심: 가능하지만 startup/recovery 시간과 비용을 감당할 수 있을 때만 그렇다.

> Q: event upcaster가 있으면 snapshot도 자동으로 해결되나요?
> 의도: event compatibility와 snapshot compatibility를 구분하는지 본다.
> 핵심: 아니다. snapshot format은 별도 호환 전략이 필요하다.

> Q: snapshot versioning은 언제부터 해야 하나요?
> 의도: 조기 단순화와 나중 비용을 균형 있게 보는지 본다.
> 핵심: snapshot이 한 릴리스를 넘겨 살아남는 순간부터 거의 필요해진다.

## 한 줄 정리

Snapshot도 오래 사는 복원 자산이므로, format version과 invalidation/upcast 전략을 함께 설계해야 replay shortcut이 안전하게 유지된다.

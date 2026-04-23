# Checkpoint / Snapshot Pattern: 긴 이력을 짧게 접는 복원 전략

> 한 줄 요약: Checkpoint/Snapshot은 누적 이력의 중간 시점을 저장해, 긴 replay 비용을 줄이고 복원을 빠르게 만드는 패턴이다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Memento vs Event Sourcing](./memento-vs-event-sourcing.md)
> - [Event Sourcing: 변경 이력을 진실의 원천으로 쓰는 패턴 언어](./event-sourcing-pattern-language.md)
> - [Snapshot Versioning and Compatibility Pattern](./snapshot-versioning-compatibility-pattern.md)
> - [Unit of Work Pattern](./unit-of-work-pattern.md)
> - [State Machine Library vs State Pattern](./state-machine-library-vs-state-pattern.md)

---

## 핵심 개념

Snapshot은 특정 시점의 상태를 저장한다.  
Checkpoint는 replay 중간에 끊어둘 수 있는 기준점이다.

이 둘은 비슷하지만 강조점이 조금 다르다.

- Snapshot: 복원용 상태 덩어리
- Checkpoint: replay 가속용 기준점

### Retrieval Anchors

- `checkpoint snapshot`
- `replay optimization`
- `state checkpoint`
- `restore point`
- `event replay shortcut`
- `snapshot versioning`

---

## 깊이 들어가기

### 1. event sourcing의 replay 비용을 줄인다

이벤트가 많아질수록 처음부터 끝까지 재생하는 비용이 커진다.  
Snapshot은 이 비용을 줄인다.

### 2. Memento와는 목적이 조금 다르다

Memento는 undo/restore에 가깝고, checkpoint/snapshot은 긴 이력을 실무적으로 관리하는 데 가깝다.

### 3. 너무 자주 찍으면 비용이 커진다

snapshot은 저장 비용도 든다.  
적절한 간격과 기준을 정해야 한다.

---

## 실전 시나리오

### 시나리오 1: 이벤트 로그 복원

긴 주문 이력이나 결제 이력에서 중간 snapshot을 두면 재생이 빨라진다.

### 시나리오 2: 워크플로 상태 복원

상태 머신의 큰 진행 단계마다 checkpoint를 둘 수 있다.

### 시나리오 3: 장애 복구

복원 포인트가 있으면 장애 시 재시작이 쉽다.

---

## 코드로 보기

### Snapshot

```java
public record OrderSnapshot(Long orderId, String status, int version) {}
```

### Checkpoint

```java
public class OrderHistoryReplayer {
    public OrderSnapshot replayFrom(OrderSnapshot checkpoint, List<OrderEvent> events) {
        OrderSnapshot current = checkpoint;
        for (OrderEvent event : events) {
            current = current.apply(event);
        }
        return current;
    }
}
```

### Store

```java
public interface SnapshotStore {
    void save(OrderSnapshot snapshot);
    Optional<OrderSnapshot> findLatest(Long orderId);
}
```

Snapshot은 replay shortcut이고, checkpoint는 운영 전략이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| replay only | 단순하다 | 느려진다 | 이력이 짧을 때 |
| Snapshot/Checkpoint | 복원이 빠르다 | 저장 관리가 필요하다 | 이력이 길 때 |
| Full state store | 즉시 읽기 좋다 | 변경 이력이 약하다 | 최신 상태 중심 |

판단 기준은 다음과 같다.

- replay 비용이 커지면 snapshot을 넣는다
- checkpoint 간격은 운영 비용과 복원 시간을 함께 본다
- event sourcing과 함께 쓰면 효과가 크다

---

## 꼬리질문

> Q: checkpoint와 snapshot은 같은 건가요?
> 의도: 저장물과 기준점을 구분하는지 확인한다.
> 핵심: 비슷하지만 checkpoint는 replay 기준점, snapshot은 상태 저장이다.

> Q: 언제 snapshot을 찍어야 하나요?
> 의도: 비용과 효익 균형을 아는지 확인한다.
> 핵심: replay가 느려질 때다.

> Q: memento와 뭐가 다른가요?
> 의도: 복원 목적과 운영 목적을 구분하는지 확인한다.
> 핵심: checkpoint/snapshot은 대용량 replay 최적화에 가깝다.

## 한 줄 정리

Checkpoint/Snapshot은 긴 이벤트 이력을 중간에서 접어 replay와 복원을 빠르게 만드는 전략이다.

# Memento vs Event Sourcing

> 한 줄 요약: Memento는 특정 시점의 상태 스냅샷을 저장하고, Event Sourcing은 상태를 만든 사건의 흐름을 저장한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Event Sourcing: 변경 이력을 진실의 원천으로 쓰는 패턴 언어](./event-sourcing-pattern-language.md)
> - [Command Pattern, Undo, Queue](./command-pattern-undo-queue.md)
> - [Unit of Work Pattern](./unit-of-work-pattern.md)
> - [State Pattern: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)

---

## 핵심 개념

Memento는 **상태를 그대로 저장했다가 필요할 때 복원하는 패턴**이다.  
Event Sourcing은 **상태를 바꾼 사건을 저장하고 다시 재생해서 상태를 얻는 패턴**이다.

둘 다 "과거로 돌아갈 수 있다"는 점은 비슷하지만, 철학이 다르다.

- Memento: 스냅샷 중심
- Event Sourcing: 사건 중심

### Retrieval Anchors

- `memento vs event sourcing`
- `snapshot restore`
- `state history`
- `undo redo`
- `event replay`

---

## 깊이 들어가기

### 1. Memento는 현재 상태 복원에 강하다

Memento는 특정 시점의 상태를 저장한다.

- undo/redo
- draft 복원
- 편집기 히스토리

즉 "현재 상태를 저장해두고 되돌리는 것"이 핵심이다.

### 2. Event Sourcing은 이력 분석에 강하다

이벤트는 상태가 왜 그렇게 되었는지 보여준다.

- 누가 언제 바꿨는가
- 어떤 순서로 변경됐는가
- 중간 실패가 있었는가

그래서 감사와 재현에 유리하다.

### 3. 저장 크기와 복원 비용이 다르다

Memento는 스냅샷이 커질 수 있고, Event Sourcing은 replay 비용이 커질 수 있다.

즉 둘은 저장/복원/이력의 trade-off가 다르다.

---

## 실전 시나리오

### 시나리오 1: 에디터 undo

문서 편집기는 Memento가 직관적이다.

### 시나리오 2: 주문 감사 로그

주문 상태의 이유를 추적해야 하면 Event Sourcing이 더 맞는다.

### 시나리오 3: 임시 편집 상태 복원

사용자 작성 폼의 draft 복원은 Memento가 적합하다.

---

## 코드로 보기

### Memento

```java
public record EditorSnapshot(String content, int cursor) {}

public class Editor {
    public EditorSnapshot save() {
        return new EditorSnapshot(content, cursor);
    }

    public void restore(EditorSnapshot snapshot) {
        this.content = snapshot.content();
        this.cursor = snapshot.cursor();
    }
}
```

### Event Sourcing

```java
public interface DomainEvent {}

public record TextInserted(String text) implements DomainEvent {}
public record TextDeleted(int length) implements DomainEvent {}
```

### 차이

```java
// Memento: 상태 자체 저장
// Event Sourcing: 상태를 바꾼 사건 저장
```

Memento는 빠른 복원, Event Sourcing은 풍부한 이력이 강점이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Memento | 복원이 간단하다 | 스냅샷이 커질 수 있다 | undo/redo |
| Event Sourcing | 이력과 재현성이 좋다 | replay 비용이 있다 | 감사/추적 |
| CRUD | 가장 단순하다 | 과거 재현이 약하다 | 단순 상태 저장 |

판단 기준은 다음과 같다.

- "되돌리기"가 목적이면 Memento
- "왜 이렇게 되었는가"가 목적이면 Event Sourcing
- 둘 다 필요하면 스냅샷+이벤트 혼합을 본다

---

## 꼬리질문

> Q: Memento와 Event Sourcing을 같이 쓸 수 있나요?
> 의도: 스냅샷과 이벤트의 결합을 이해하는지 확인한다.
> 핵심: 가능하다. 보통 replay 비용을 줄이기 위해 스냅샷을 섞는다.

> Q: undo와 audit은 같은 문제인가요?
> 의도: 복원과 추적 목적의 차이를 구분하는지 확인한다.
> 핵심: undo는 복원, audit은 이력 증명이다.

> Q: Event Sourcing이 더 멋져 보여서 쓰면 안 되나요?
> 의도: 패턴 과사용을 경계하는지 확인한다.
> 핵심: 아니다. 복잡도 비용이 크다.

## 한 줄 정리

Memento는 상태 스냅샷, Event Sourcing은 사건 로그다. 둘은 비슷해 보여도 목적과 비용 구조가 다르다.


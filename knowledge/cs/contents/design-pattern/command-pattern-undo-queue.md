# Command Pattern Undo Queue

> 한 줄 요약: Command 패턴은 요청을 객체로 캡슐화해서 실행, 큐잉, 재시도, undo까지 같은 모델로 다루게 한다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Command Handler Pattern](./command-handler-pattern.md)
> - [Command Bus Pattern](./command-bus-pattern.md)
> - [Invariant-Preserving Command Model](./invariant-preserving-command-model.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [안티 패턴](./anti-pattern.md)

retrieval-anchor-keywords: command pattern, command object, undo redo command, command queue, command history stack, invoker receiver, retryable job command, text editor undo, queued work item, command vs event

---

## 핵심 개념

Command 패턴은 "무엇을 실행할지"를 객체로 감싼다.

그 결과 생기는 장점은 네 가지다.

- 실행 요청을 큐에 넣을 수 있다
- 실행을 지연할 수 있다
- 재시도를 통일할 수 있다
- undo/redo를 같은 인터페이스로 다룰 수 있다

즉 Command는 단순한 함수 호출이 아니라 **명령을 데이터처럼 다루는 구조**다.

---

## 깊이 들어가기

### 1. 요청을 객체로 만든다

```java
public interface Command {
    void execute();
    void undo();
}
```

실행할 동작을 객체로 감싸면, 호출자와 실행자를 분리할 수 있다.

### 2. invoker와 receiver를 분리한다

- Invoker: 명령을 호출하는 쪽
- Receiver: 실제 일을 하는 쪽

이 분리 덕분에 큐, 스케줄러, 히스토리 관리가 가능해진다.

### 3. undo queue와 잘 맞는다

에디터, 주문 취소, 작업 로그처럼 "되돌리기"가 필요한 시스템에서 효과가 크다.

```java
Deque<Command> history = new ArrayDeque<>();
command.execute();
history.push(command);

// undo
history.pop().undo();
```

### 4. Spring/Queue와 연결된다

메시지 큐, 작업 큐, 비동기 처리에서도 "명령을 객체로 캡슐화"하는 사고가 자주 등장한다.

---

## 실전 시나리오

### 시나리오 1: 텍스트 에디터

글자 입력, 삭제, 포맷 변경을 Command로 만들면 undo/redo가 자연스럽다.

### 시나리오 2: 주문 작업 큐

주문 승인, 결제, 취소 같은 작업을 큐에 넣고 순차 처리할 수 있다.

### 시나리오 3: 배치 작업 재시도

실패한 작업을 그대로 다시 실행할 수 있게 명령을 객체로 보관하면 재시도가 쉬워진다.

---

## 코드로 보기

### Before

```java
public class Editor {
    public void type(String text) {
        content += text;
    }

    public void deleteLast() {
        content = content.substring(0, content.length() - 1);
    }
}
```

### After: Command

```java
public class TypeCommand implements Command {
    private final Editor editor;
    private final String text;

    public TypeCommand(Editor editor, String text) {
        this.editor = editor;
        this.text = text;
    }

    @Override
    public void execute() {
        editor.append(text);
    }

    @Override
    public void undo() {
        editor.delete(text.length());
    }
}
```

### Queueing

```java
Queue<Command> queue = new ArrayDeque<>();
queue.add(new TypeCommand(editor, "hello"));
queue.add(new TypeCommand(editor, " world"));

while (!queue.isEmpty()) {
    queue.poll().execute();
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|-------------|
| 직접 호출 | 가장 단순하다 | undo, queue, retry가 어렵다 | 아주 단순한 흐름 |
| Command | 실행/취소/큐잉이 쉽다 | 객체 수가 늘어난다 | 명령 이력이 중요할 때 |
| 이벤트 | 느슨하게 연결된다 | 순서/정합성이 어려워진다 | 비동기 확장이 필요할 때 |

판단 기준은 명확하다.

- 실행 자체만 필요하면 직접 호출도 충분하다
- 실행 기록과 되돌리기가 필요하면 Command가 맞다
- 느슨한 확장이 필요하면 이벤트와 함께 쓰는 편이 낫다

---

## 꼬리질문

> Q: Command 패턴과 이벤트는 어떻게 다른가요?
> 의도: 요청 캡슐화와 이벤트 발행을 구분하는지 확인한다.
> 핵심: Command는 "무엇을 실행할지", 이벤트는 "무엇이 일어났는지"다.

> Q: undo가 Command의 필수 요소인가요?
> 의도: 패턴을 과도하게 고정된 정의로 외우는지 확인한다.
> 핵심: 필수는 아니지만, Command의 장점이 가장 잘 드러나는 확장이다.

> Q: 큐에 넣으면 왜 Command가 유용한가요?
> 의도: 객체 캡슐화의 이점을 이해하는지 확인한다.
> 핵심: 실행 시점 분리, 재시도, 우선순위, 기록 관리가 쉬워진다.

---

## 한 줄 정리

Command는 요청을 객체로 만들어 실행, 큐잉, 재시도, undo를 같은 구조로 다루게 한다.

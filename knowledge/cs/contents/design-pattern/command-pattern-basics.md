# 커맨드 패턴 기초 (Command Pattern Basics)

> 한 줄 요약: 커맨드 패턴은 요청을 객체로 만들어 실행을 나중으로 미루거나, 큐에 쌓거나, 실행 취소(undo)할 수 있게 해주는 패턴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Command Pattern, Undo, Queue 심화](./command-pattern-undo-queue.md)
- [실전 패턴 선택 가이드](./pattern-selection.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [Spring AOP 기초](../spring/spring-aop-basics.md)

retrieval-anchor-keywords: command pattern basics, 커맨드 패턴 기초, 커맨드 패턴이 뭔가요, command pattern beginner, 요청을 객체로, undo redo pattern, 실행 취소 패턴, 작업 큐 패턴, invoker receiver command, 커맨드 패턴 예시, beginner command pattern, 요청 캡슐화

---

## 핵심 개념

커맨드 패턴은 **"무엇을 실행하라"는 요청 자체를 하나의 객체로 감싸는** 패턴이다. 요청을 객체로 만들면 바로 실행하지 않고 나중에 실행하거나, 여러 요청을 큐에 쌓거나, 실행 취소(undo/redo)를 구현하는 것이 가능해진다.

입문자가 헷갈리는 점은 "그냥 메서드 호출하면 되지 않나?"다. 직접 호출은 즉시 실행하고 나면 흔적이 없다. 커맨드 객체로 만들면 실행 기록이 남고, 실행 시점과 실행 주체를 분리할 수 있다.

## 한눈에 보기

```
Client → Command 객체 생성
Invoker → command.execute() 호출
Command → Receiver의 실제 메서드 호출

[Command Queue]
  BuyCommand(stock="AAPL", qty=10)
  SellCommand(stock="GOOG", qty=5)
  UndoCommand()
```

| 역할 | 설명 |
|------|------|
| Command | `execute()` / `undo()` 인터페이스 |
| ConcreteCommand | 실제 수행 로직을 Receiver에 위임 |
| Invoker | 커맨드를 실행하는 주체 (큐, 버튼 등) |
| Receiver | 실제 작업을 아는 객체 |

## 상세 분해

커맨드 패턴은 세 가지 능력을 준다.

- **지연 실행** — Command 객체를 만들어두고 나중에 `execute()`를 호출한다. 스케줄러나 작업 큐에 담을 수 있다.
- **Undo/Redo** — `execute()`와 대칭되는 `undo()`를 구현하면, 이전 Command 객체를 꺼내 되돌릴 수 있다.
- **매크로(복합 커맨드)** — 여러 Command를 하나의 리스트에 담아 순서대로 실행하는 CompositeCommand를 만들 수 있다.

각 Command 객체는 실행에 필요한 상태(파라미터)를 자신 안에 담고 있어서, Invoker가 상세 내용을 알 필요가 없다.

## 흔한 오해와 함정

- **"Undo는 필수다"** — 커맨드 패턴에 Undo가 필요하지 않은 경우도 많다. 작업 큐나 지연 실행만 필요하다면 `execute()` 하나만 구현해도 패턴은 유효하다.
- **"Command가 비즈니스 로직을 직접 갖는다"** — Command는 실행을 Receiver에 위임하는 것이 원칙이다. Command 안에 로직이 쌓이면 Command가 비대해진다.
- **"전략 패턴과 같다"** — 전략 패턴은 교체 가능한 알고리즘을 선택하는 것이고, 커맨드 패턴은 실행을 객체로 만들어 저장/전달/취소하는 것이다.

## 실무에서 쓰는 모습

텍스트 에디터에서 "글자 입력", "삭제", "붙여넣기"를 각각 Command 객체로 만들면 Ctrl+Z를 누를 때 이전 Command의 `undo()`를 순서대로 호출하면 된다.

Spring Batch의 `Step`, Spring MVC의 `HandlerInterceptor` 체인, Java `Runnable`/`Callable` 모두 커맨드 패턴의 변형이다. 작업을 캡슐화해 `ExecutorService`에 제출하면 스레드풀이 나중에 실행한다.

## 더 깊이 가려면

- [Command Pattern, Undo, Queue 심화](./command-pattern-undo-queue.md) — undo/history 스택 구조, job queue 설계까지
- [실전 패턴 선택 가이드](./pattern-selection.md) — 커맨드 vs 전략 vs 체인 선택 기준

## 면접/시니어 질문 미리보기

> Q: 커맨드 패턴이 일반 메서드 호출과 다른 점은?
> 의도: 패턴이 해결하는 문제를 이해하는지 확인한다.
> 핵심: 요청을 객체로 저장하므로 지연 실행, undo, 큐 처리가 가능하다.

> Q: Invoker가 Receiver를 알아야 하는가?
> 의도: 역할 분리를 이해하는지 확인한다.
> 핵심: Invoker는 Command 인터페이스만 알면 된다. Receiver는 Command 안에 캡슐화된다.

> Q: Java `Runnable`이 커맨드 패턴과 어떤 관계인가?
> 의도: 패턴과 실제 API를 연결하는지 확인한다.
> 핵심: `Runnable`은 `execute()`에 해당하는 `run()`을 가진 단순 커맨드 인터페이스다.

## 한 줄 정리

커맨드 패턴은 실행 요청을 객체로 만들어 지연 실행·큐·실행 취소를 가능하게 하며, 실행 시점과 실행 내용을 분리해 유연한 흐름 제어를 준다.

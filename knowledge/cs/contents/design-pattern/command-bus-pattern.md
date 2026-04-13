# Command Bus Pattern: 커맨드를 핸들러로 라우팅하기

> 한 줄 요약: Command Bus는 들어온 명령을 알맞은 handler로 라우팅해, command side 유스케이스를 중앙에서 연결한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Command Handler Pattern](./command-handler-pattern.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)
> - [Registry Pattern](./registry-pattern.md)
> - [Plugin Architecture: 기능을 꽂아 넣는 패턴 언어](./plugin-architecture-pattern-language.md)

---

## 핵심 개념

Command Bus는 **명령과 handler를 직접 연결하지 않고, bus가 중간에서 찾아서 호출하는 구조**다.

- command는 요청 데이터
- handler는 실행 로직
- bus는 라우터

### Retrieval Anchors

- `command bus`
- `command dispatch`
- `handler routing`
- `request bus`
- `command side bus`

---

## 깊이 들어가기

### 1. handler를 직접 호출하지 않는다

Command Handler가 명확해지면, Bus는 handler 선택을 담당할 수 있다.

- dispatch
- routing
- cross-cutting behavior

### 2. registry와 함께 쓰기 좋다

Bus는 보통 command type -> handler map을 가진다.  
실제로는 Registry의 응용이다.

### 3. middleware와 같이 붙는다

Command Bus 주변에 validation, transaction, logging middleware를 둘 수 있다.

---

## 실전 시나리오

### 시나리오 1: CQRS command side

여러 command를 중앙 bus로 흘려보내면 유스케이스 연결이 단순해진다.

### 시나리오 2: 플러그인 기반 처리

새 handler를 등록만 하면 bus가 찾아 처리한다.

### 시나리오 3: 테스트

bus를 mock하거나 handler를 교체하기 쉬워진다.

---

## 코드로 보기

### Command Bus

```java
public class CommandBus {
    private final Map<Class<?>, CommandHandler<?>> handlers;

    @SuppressWarnings("unchecked")
    public <C, R> R dispatch(C command) {
        CommandHandler<C, R> handler = (CommandHandler<C, R>) handlers.get(command.getClass());
        return handler.handle(command);
    }
}
```

### Handler

```java
public interface CommandHandler<C, R> {
    R handle(C command);
}
```

### Use

```java
OrderId orderId = commandBus.dispatch(new PlaceOrderCommand(userId, items));
```

Bus는 command side를 깔끔하게 라우팅한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 직접 handler 호출 | 단순하다 | 연결이 분산된다 | 작은 시스템 |
| Command Bus | 중앙 라우팅이 가능하다 | 디스패치가 숨겨질 수 있다 | command가 많을 때 |
| Event Bus | 느슨하게 연결된다 | 정합성이 약하다 | 발생 후 반응 |

판단 기준은 다음과 같다.

- command가 많고 routing이 필요하면 bus
- handler 연결이 자주 바뀌면 bus가 편하다
- 너무 숨기면 디버깅이 어려우니 middleware를 곁들인다

---

## 꼬리질문

> Q: Command Bus와 Command Handler는 같은 건가요?
> 의도: execution과 routing을 구분하는지 확인한다.
> 핵심: handler는 실행, bus는 라우팅이다.

> Q: 왜 registry가 command bus와 잘 맞나요?
> 의도: lookup table과 dispatch의 관계를 아는지 확인한다.
> 핵심: command type으로 handler를 찾기 때문이다.

> Q: command bus가 너무 많아지면 어떤가요?
> 의도: 과한 추상화를 경계하는지 확인한다.
> 핵심: routing만 있는데도 구조가 너무 두꺼워질 수 있다.

## 한 줄 정리

Command Bus는 command side 유스케이스를 handler로 라우팅하는 중앙 디스패치 구조다.


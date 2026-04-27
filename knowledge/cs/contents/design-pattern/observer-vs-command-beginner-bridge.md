# 옵저버 vs 커맨드: 처음 선택을 줄이는 1페이지 브리지

> 한 줄 요약: 옵저버는 "무슨 일이 일어났는지 여러 반응자에게 알리는 구조"이고, 커맨드는 "무엇을 실행하라고 요청 자체를 들고 다니는 구조"다.

**난이도: 🟢 Beginner**

> Beginner Route: `[entrypoint]` [옵저버 패턴 기초](./observer-basics.md) -> `[bridge]` 이 문서 -> `[deep dive]` [옵저버 (Observer) 심화](./observer.md)

관련 문서:

- [옵저버 패턴 기초](./observer-basics.md)
- [커맨드 패턴 기초](./command-pattern-basics.md)
- [옵저버 (Observer) 심화](./observer.md)
- [Command Pattern, Undo, Queue 심화](./command-pattern-undo-queue.md)
- [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: observer vs command, 옵저버 vs 커맨드, observer command difference, command vs observer beginner, event notification vs command request, 무엇이 일어났는지 vs 무엇을 실행할지, observer or command first choice, beginner pattern bridge, listener vs command object, notify vs execute, fan-out notification vs queued request, observer vs command beginner bridge basics, observer vs command beginner bridge beginner, observer vs command beginner bridge intro, design pattern basics

---

## 먼저 잡는 멘탈 모델

- 옵저버: "일이 이미 일어났다. 관련된 사람들에게 알려라."
- 커맨드: "이 일을 실행해라. 지금 말고 나중에 실행해도 된다."

처음 헷갈릴 때는 용어보다 문장으로 자르는 편이 빠르다.

- `주문이 완료됐다`를 여러 곳에 알리면 옵저버 쪽 질문이다.
- `주문 취소를 실행해라`를 큐에 넣고 나중에 처리하면 커맨드 쪽 질문이다.

핵심 차이는 이것이다.

- 옵저버는 **알림(notification)** 중심이다.
- 커맨드는 **실행 요청(request)** 중심이다.

## 10초 선택 질문

1. 지금 고민이 "누가 이 변화에 반응해야 하지?"인가
2. 아니면 "이 작업 요청을 저장했다가 나중에 실행해야 하지?"인가

첫 질문이면 옵저버 쪽일 가능성이 크고, 둘째 질문이면 커맨드 쪽일 가능성이 크다.

## 30초 비교표

| 항목 | Observer | Command |
|---|---|---|
| 한 문장 | 상태 변화나 사건을 여러 반응자에게 알린다 | 실행 요청을 객체로 만들어 전달하거나 저장한다 |
| 중심 질문 | 누가 이 일에 반응하나 | 어떤 작업을 실행하나 |
| 보통 시점 | 어떤 일이 일어난 직후 | 지금 또는 나중 |
| 자주 붙는 구조 | listener, event, notify, subscribe | execute, queue, undo, retry |
| 잘 맞는 예 | 주문 완료 후 알림/로그/메트릭 | 주문 취소 요청 큐, 에디터 undo |
| 직접 호출 대신 쓰는 이유 | 반응자 추가를 쉽게 하려고 | 실행 시점과 실행 주체를 분리하려고 |

## 1분 예시

### 예시 1. 주문 완료 알림

주문이 끝나면 메일, 슬랙, 감사 로그가 각각 반응해야 한다.

- 주문 완료 자체는 이미 일어난 사실이다.
- 이후 반응자가 늘어날 수 있다.

이 경우는 옵저버가 자연스럽다.

```java
order.complete();
publisher.notify(new OrderCompleted(orderId));
```

### 예시 2. 주문 취소 작업 큐

사용자가 주문 취소 버튼을 눌렀지만, 실제 취소는 워커가 나중에 처리한다.

- 아직 실행되지 않은 요청이다.
- 큐 적재, 재시도, 이력 관리가 중요하다.

이 경우는 커맨드가 자연스럽다.

```java
queue.add(new CancelOrderCommand(orderId, reason));
```

## 자주 헷갈리는 포인트 4개

### 1. "이벤트 이름이 있으면 다 옵저버인가요?"

아니다. 이름이 `CancelOrderCommand`면 "실행해라"에 가깝고, `OrderCancelledEvent`면 "이미 취소됐다"에 가깝다.

- `Command`는 미래 지향적 요청이다.
- `Event`는 과거형 사실 보고에 가깝다.

### 2. "둘 다 객체 하나 만들어 전달하니 같은 거 아닌가요?"

겉모양은 비슷해도 질문이 다르다.

- 옵저버는 반응자를 느슨하게 붙이는 데 초점이 있다.
- 커맨드는 요청을 저장, 전달, 재실행하는 데 초점이 있다.

### 3. "주문 완료 후 포인트 적립은 옵저버인가요, 커맨드인가요?"

둘 다 가능하지만 먼저 이렇게 자른다.

- 주문 완료에 **반응하는 부가 작업**이면 옵저버
- 포인트 적립 **실행 요청 자체를 큐에 쌓고 재시도**해야 하면 커맨드

즉 "포인트 적립"이라는 같은 도메인 작업도, 어떤 문제를 풀고 있는지에 따라 패턴이 달라진다.

### 4. "같이 쓸 수도 있나요?"

그렇다. 자주 같이 쓴다.

예를 들어:

1. `OrderCompleted` 이벤트를 옵저버로 fan-out한다.
2. 그중 하나의 리스너가 `SendCouponCommand`를 작업 큐에 넣는다.

이때 옵저버는 "누가 반응할지"를 풀고, 커맨드는 "그 반응 작업을 어떻게 나중에 실행할지"를 푼다.

## 자주 틀리는 첫 선택

| 잘못 고른 모습 | 왜 어색한가 | 더 먼저 볼 선택 |
|---|---|---|
| 단순 알림 fan-out인데 커맨드 클래스를 반응자 수만큼 만든다 | 실행 요청보다 알림 구조가 핵심이다 | Observer |
| undo/queue/retry가 필요한데 리스너 호출만 늘린다 | 요청 저장과 재실행 문제가 풀리지 않는다 | Command |
| "이벤트니까 무조건 비동기"라고 생각한다 | 고전 옵저버는 같은 프로세스 안의 동기 호출일 수 있다 | Observer basics + Pub/Sub 비교 |
| "객체로 감쌌으니 다 Command"라고 본다 | 단순 DTO/event일 수도 있다 | 요청인지 사실인지 먼저 구분 |

## 아주 짧은 선택 루틴

- 이미 일어난 일을 알리나? → Observer 먼저
- 아직 실행할 일을 들고 다니나? → Command 먼저
- 반응자가 늘어나는 게 핵심인가? → Observer
- 큐, retry, undo가 핵심인가? → Command

이 네 줄로도 첫 선택 실패 대부분을 줄일 수 있다.

## 다음 읽기

- 옵저버 쪽이 더 헷갈리면 [옵저버 패턴 기초](./observer-basics.md)
- 커맨드 쪽이 더 헷갈리면 [커맨드 패턴 기초](./command-pattern-basics.md)
- 이벤트/브로커까지 섞이면 [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
- queue/undo까지 내려가면 [Command Pattern, Undo, Queue 심화](./command-pattern-undo-queue.md)

## 한 줄 정리

옵저버는 "일어난 사실을 알리는 구조", 커맨드는 "실행할 요청을 들고 다니는 구조"라고 기억하면 첫 선택이 빨라진다.

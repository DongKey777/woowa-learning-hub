---
schema_version: 3
title: 커맨드 패턴 기초 (Command Pattern Basics)
concept_id: design-pattern/command-pattern-basics
canonical: true
category: design-pattern
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids:
- missions/blackjack
- missions/shopping-cart
review_feedback_tags:
- command-vs-strategy
- queue-vs-broker
- request-object-modeling
aliases:
- command pattern basics
- 커맨드 패턴 기초
- 커맨드 패턴이 뭔가요
- command pattern beginner
- 요청을 객체로
- undo redo pattern
- 실행 취소 패턴
- 작업 큐 패턴
- invoker receiver command
- 커맨드 패턴 예시
- beginner command pattern
- 요청 캡슐화
- command queue vs message queue
- command queue 다음 뭐 봐요
- 왜 command 다음에 message queue가 나와요
symptoms:
- 메서드를 바로 호출하던 코드를 왜 굳이 객체로 감싸는지 모르겠어요
- undo나 retry 얘기가 나오면 command 패턴이 갑자기 너무 커 보여요
- 큐에 넣는 작업이 단순 요청 DTO인지 command인지 구분이 안 돼요
intents:
- definition
- comparison
- design
prerequisites:
- design-pattern/object-oriented-design-pattern-basics
- design-pattern/composition-over-inheritance-basics
next_docs:
- design-pattern/command-vs-strategy-quick-bridge
- design-pattern/command-pattern-undo-queue
- design-pattern/observer-vs-command-beginner-bridge
linked_paths:
- contents/design-pattern/command-vs-strategy-quick-bridge.md
- contents/design-pattern/observer-vs-command-beginner-bridge.md
- contents/design-pattern/command-pattern-undo-queue.md
- contents/system-design/per-key-queue-vs-direct-api-primer.md
- contents/system-design/message-queue-basics.md
- contents/design-pattern/pattern-selection.md
- contents/spring/spring-aop-basics.md
confusable_with:
- design-pattern/command-vs-strategy-quick-bridge
- design-pattern/observer-vs-command-beginner-bridge
- design-pattern/command-pattern-undo-queue
forbidden_neighbors:
- contents/system-design/per-key-queue-vs-direct-api-primer.md
- contents/system-design/message-queue-basics.md
expected_queries:
- 커맨드 패턴은 메서드 직접 호출이랑 뭐가 다른 거야?
- 실행 요청을 객체로 만든다는 말을 초보자 기준으로 설명해줘
- undo나 재시도가 필요할 때 왜 command 패턴을 떠올려야 해?
- 나중에 실행할 작업을 클래스로 감싸는 이유가 뭐야?
- invoker와 receiver를 같이 봐야 command 구조가 이해되는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 디자인 패턴 입문자가 메서드 직접 호출 대신 실행 요청 자체를 객체로 감싸는 이유와, 실행 시점·실행 주체를 분리하는 커맨드 패턴의 기초를 처음 잡는 primer다. 바로 부르지 않고 작업을 쌓아 두기, 나중에 실행 예약, 되돌리기 가능한 요청 모델, invoker와 receiver 역할 분리, 큐에 담는 실행 단위와 단순 데이터 전달 구분 같은 자연어 paraphrase가 본 문서의 핵심 개념에 매핑된다.
---
# 커맨드 패턴 기초 (Command Pattern Basics)

> 한 줄 요약: 커맨드 패턴은 요청을 객체로 만들어 실행을 나중으로 미루거나, 큐에 쌓거나, 실행 취소(undo)할 수 있게 해주는 패턴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Command vs Strategy: `execute()`가 비슷해 보여도 먼저 자르는 짧은 다리](./command-vs-strategy-quick-bridge.md)
- [옵저버 vs 커맨드: 처음 선택을 줄이는 1페이지 브리지](./observer-vs-command-beginner-bridge.md)
- [Command Pattern, Undo, Queue 심화](./command-pattern-undo-queue.md)
- [Per-Key Queue vs Direct API Primer](../system-design/per-key-queue-vs-direct-api-primer.md)
- [메시지 큐 기초](../system-design/message-queue-basics.md)
- [실전 패턴 선택 가이드](./pattern-selection.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [Spring AOP 기초](../spring/spring-aop-basics.md)

retrieval-anchor-keywords: command pattern basics, 커맨드 패턴 기초, 커맨드 패턴이 뭔가요, command pattern beginner, 요청을 객체로, undo redo pattern, 실행 취소 패턴, 작업 큐 패턴, invoker receiver command, 커맨드 패턴 예시, beginner command pattern, 요청 캡슐화, command queue vs message queue, command queue 다음 뭐 봐요, 왜 command 다음에 message queue가 나와요

---

## 핵심 개념

커맨드 패턴은 **"무엇을 실행하라"는 요청 자체를 하나의 객체로 감싸는** 패턴이다. 요청을 객체로 만들면 바로 실행하지 않고 나중에 실행하거나, 여러 요청을 큐에 쌓거나, 실행 취소(undo/redo)를 구현하는 것이 가능해진다.

입문자가 헷갈리는 점은 "그냥 메서드 호출하면 되지 않나?"다. 직접 호출은 즉시 실행하고 나면 흔적이 없다. 커맨드 객체로 만들면 실행 기록이 남고, 실행 시점과 실행 주체를 분리할 수 있다.

## 빠른 진입: 10초/30초/1분

처음 읽을 때는 `10초 질문 -> 30초 비교표 -> 1분 예시` 순서로만 훑는다.

## beginner-safe 다음 사다리

`queue`라는 단어가 보여도 바로 broker, consumer lag, DLQ 문서로 뛰지 않는다.

- `undo`, `redo`, `작업 이력`, `나중에 실행`이 핵심이면 이 문서 다음에 [Command Pattern, Undo, Queue 심화](./command-pattern-undo-queue.md)까지만 읽는다.
- `API로 끝낼지 queue로 보낼지`가 핵심이면 [Per-Key Queue vs Direct API Primer](../system-design/per-key-queue-vs-direct-api-primer.md)로 넘어간다.
- `BFS`, `visited`, `최소 이동 횟수`가 보이면 [알고리즘 README - BFS, Queue, Map 먼저 분리하기](../algorithm/README.md#bfs-queue-map-먼저-분리하기)로 우회한다.
- mental model: command queue는 같은 앱 안의 `실행 요청`, message queue는 서비스 사이 `후처리 handoff`다.
- misconception guard: `Command` 객체를 만들었다고 바로 브로커가 필요한 것은 아니다.

| 지금 막힌 문장 | 다음 한 걸음 | 아직 미루는 것 |
|---|---|---|
| `처음이라 queue가 다 같은 말처럼 보여요`, `헷갈려요: bfs냐 command냐` | [알고리즘 README - BFS, Queue, Map 먼저 분리하기](../algorithm/README.md#bfs-queue-map-먼저-분리하기) -> 이 문서 | broker topology, distributed scheduler |
| `실행 요청을 객체로 만드는 건 알겠는데 왜 어떤 건 API로 끝내고 어떤 건 queue로 보내요?` | 이 문서 -> [Per-Key Queue vs Direct API Primer](../system-design/per-key-queue-vs-direct-api-primer.md) | replay repair, partition ordering |
| `큐에 넣으면 끝난 거예요?`, `producer/consumer가 아직 추상적이에요` | [Per-Key Queue vs Direct API Primer](../system-design/per-key-queue-vs-direct-api-primer.md) -> [메시지 큐 기초](../system-design/message-queue-basics.md) | DLQ 운영 playbook, backlog tuning |

## 10초 질문

- "지금 바로 호출"이 아니라 "나중에 실행/재실행/취소"가 필요하면 커맨드 후보다.
- 실행 주체(Invoker)와 실제 작업 객체(Receiver)를 분리해야 하면 커맨드 구조가 맞다.
- 실행 이력(undo/redo, retry, queue)을 남겨야 하면 메서드 직접 호출보다 커맨드가 유리하다.

## 30초 비교표

Command / Direct Call / Strategy

| 방식 | 중심 질문 | 언제 먼저 고르나 |
|---|---|---|
| Command | 요청을 객체로 저장/전달할 필요가 있는가 | 지연 실행, 큐, undo가 필요할 때 |
| Direct Call | 지금 즉시 한 번 호출하면 끝나는가 | 단순 동기 흐름이면 충분할 때 |
| Strategy | 실행 "시점"이 아니라 "방법"을 교체해야 하는가 | 알고리즘 교체가 핵심일 때 |

## 1분 예시

주문 취소 큐:

사용자 요청을 받으면 `CancelOrderCommand(orderId, reason)`를 큐에 적재하고 워커가 나중에 `execute()`를 호출한다.
실패한 커맨드는 재시도 큐로 옮기고, 운영자가 잘못 취소한 경우 최근 히스토리에서 `undo()`를 호출해 복구한다.

## 자주 헷갈리는 포인트 3개

- 커맨드의 핵심은 "메서드를 클래스 하나로 감싼다"가 아니라 "요청을 저장하고 나중에 실행할 수 있다"는 점이다.
- Undo는 선택 기능이다. 지연 실행이나 큐 적재만 필요해도 이미 커맨드 패턴을 쓰는 이유가 충분하다.
- 전략과 모양이 비슷해도 질문이 다르다. "무엇을 실행할지 저장/전달"이 핵심이면 커맨드, "어떤 방법으로 계산할지 교체"가 핵심이면 전략이다.

여기서 `커맨드인가, 옵저버인가`가 같이 흔들리면 [옵저버 vs 커맨드 브리지](./observer-vs-command-beginner-bridge.md)를 먼저 보면 "실행 요청"과 "사실 알림"이 빨리 갈린다.

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

## 3문항 미니 오해 점검

짧게 구분해 본다. 핵심은 "요청을 담아 나중에 실행하나"와 "단지 계산 방법만 바꾸나"를 나누는 것이다.

| 문항 | 헷갈리는 포인트 | 한 줄 정답 기준 |
|---|---|---|
| 1 | Command vs Direct Call | 요청을 저장하거나 큐에 넘길 필요가 있으면 Command |
| 2 | Command vs Strategy | 실행 방법 교체면 Strategy, 실행 요청 저장/전달이면 Command |
| 3 | Command vs 단순 DTO | `execute()` 같은 실행 책임이 없으면 보통 그냥 데이터 객체 |

### Q1. 서비스가 `paymentService.cancel(orderId)`를 즉시 한 번 호출한다. 이것도 Command인가?

- 정답: 보통 direct call이다.
- 왜: 요청을 객체로 저장하거나 다른 실행 주체에게 넘기지 않고 바로 호출로 끝나기 때문이다.
- 기억법: "나중에 실행할 수 있게 들고 다니는가?"가 Command 첫 질문이다.

### Q2. `DiscountPolicy` 구현체를 갈아끼워 할인 공식을 바꾼다. 이것도 Command인가?

- 정답: 보통 Strategy에 가깝다.
- 왜: 지금 필요한 것은 요청 저장이 아니라 계산 방법 교체이기 때문이다.
- 같이 보면 좋은 문서: [실전 패턴 선택 가이드](./pattern-selection.md)

### Q3. `CancelOrderRequest(orderId, reason)` DTO를 만들었다. 이것만으로 Command인가?

- 정답: 아니다.
- 왜: 데이터만 담는 요청 객체일 뿐, 스스로 실행 책임(`execute`)이나 Receiver 위임 구조가 없기 때문이다.
- 체크 질문: "이 객체를 큐에 넣어 나중에 실행할 수 있는가, 아니면 그냥 파라미터 묶음인가?"

## 한 줄 정리

커맨드 패턴은 실행 요청을 객체로 만들어 지연 실행·큐·실행 취소를 가능하게 하며, 실행 시점과 실행 내용을 분리해 유연한 흐름 제어를 준다.

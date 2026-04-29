# 동기/비동기와 블로킹/논블로킹 기초

> 한 줄 요약: 동기/비동기는 결과를 누가 기다리느냐의 문제이고, 블로킹/논블로킹은 호출하는 동안 스레드가 멈추느냐의 문제라 두 축은 독립적이다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 I/O, thread pool, event loop 문서로 넘어가기 전에 "무엇을 구분해야 하는지"를 먼저 잡는 beginner primer다.

**난이도: 🟢 Beginner**

관련 문서:

- [I/O Models and Event Loop](./io-models-and-event-loop.md)
- [Blocking I/O, 스레드 풀, 백프레셔 입문](./blocking-io-thread-pool-backpressure-primer.md)
- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
- [operating-system 카테고리 인덱스](./README.md)
- [TCP/UDP Basics](../network/tcp-udp-basics.md)

retrieval-anchor-keywords: 동기 비동기 차이, 블로킹 논블로킹 차이, sync async beginner, blocking nonblocking beginner, synchronous asynchronous intro, 동기 비동기 뭐가 달라요, 블로킹이란, 비동기란, io blocking, async callback, sync async blocking nonblocking basics basics, sync async blocking nonblocking basics beginner, sync async blocking nonblocking basics intro, operating system basics, beginner operating system

## 먼저 잡는 멘탈 모델

신입 개발자가 가장 혼동하는 쌍이다. "동기 = 블로킹"이고 "비동기 = 논블로킹"이라 외우는 경우가 많은데, 이 두 쌍은 **서로 다른 축**이다.

- 첫 번째 축은 "결과를 누가 챙기나?"다. 직접 챙기면 동기, 나중에 알림을 받으면 비동기다.
- 두 번째 축은 "기다리는 동안 이 스레드가 멈추나?"다. 멈추면 블로킹, 바로 돌아오면 논블로킹이다.
- 비유로 시작하면 이해가 쉽지만, 비유는 여기까지만 유효하다. 실제 구현에서는 같은 비동기 API라도 마지막에 `get()`이나 `join()`으로 기다리면 그 순간은 다시 블로킹이 된다.

- **동기(synchronous)**: 호출한 쪽이 결과를 직접 기다린 뒤 다음 코드를 실행한다.
- **비동기(asynchronous)**: 호출한 쪽이 결과를 기다리지 않고 다음 코드를 먼저 실행한다. 결과가 준비되면 콜백·이벤트·Future 등으로 알림이 온다.
- **블로킹(blocking)**: 함수를 호출한 스레드가 결과가 날 때까지 OS 수준에서 멈춘다.
- **논블로킹(non-blocking)**: 함수 호출 즉시 반환한다. 준비가 안 됐으면 에러나 특수 값을 돌려준다.

입문 수준에서는 "동기 ≈ 블로킹", "비동기 ≈ 논블로킹"이 많이 겹치지만, 둘을 섞어 쓰는 조합도 존재한다.

## 한눈에 보기

| 조합 | 설명 | 예시 |
|------|------|------|
| 동기 + 블로킹 | 호출 중 스레드가 멈추고, 결과가 나면 그 자리에서 처리 | `read()` 파일 읽기 |
| 동기 + 논블로킹 | 호출은 즉시 반환, 직접 폴링으로 결과 확인 | `read()` + `O_NONBLOCK` 반복 폴링 |
| 비동기 + 블로킹 | 작업 등록은 비동기지만, 나중에 `future.get()`처럼 결과를 기다리는 시점은 블로킹 | `CompletableFuture.supplyAsync(...).get()` |
| 비동기 + 논블로킹 | 등록도 즉시 끝나고, 완료 알림도 콜백/이벤트 루프로 받음 | Node.js 이벤트 루프, Java `CompletableFuture.thenAccept()` |

이 표의 핵심은 "비동기 API를 썼다"와 "스레드가 안 멈춘다"가 같은 말이 아니라는 점이다.

## 상세 분해

### 동기 호출

```java
String result = httpClient.get(url);  // 결과 나올 때까지 여기서 멈춤
System.out.println(result);
```

호출 순서가 곧 실행 순서다. 이해하기 쉽고, 예외 처리가 단순하다.

### 비동기 호출

```java
httpClient.getAsync(url)
    .thenAccept(result -> System.out.println(result));
// 위 줄이 등록만 하고 바로 다음 코드로 넘어간다
```

결과가 언제 오는지 명시적으로 알 수 없다. 콜백·Future·이벤트로 받는다.

### 블로킹 vs 논블로킹 핵심 차이

블로킹은 스레드가 **대기 상태(waiting)**로 전환돼 CPU를 내준다. 논블로킹은 함수가 즉시 반환하기 때문에 스레드가 계속 실행된다.

## 처음 읽는 사람이 자주 헷갈리는 장면

| 장면 | 무엇을 먼저 보나 | 왜 헷갈리나 |
|------|------------------|-------------|
| `Future`를 받자마자 `get()` 호출 | 결국 기다렸는가 | 비동기 API를 호출했지만 사용 방식은 동기 + 블로킹이 된다 |
| `O_NONBLOCK`만 켜고 반복 호출 | 준비 안 됐을 때 무엇을 하나 | 논블로킹만 있고 event loop/backpressure가 없으면 busy wait가 되기 쉽다 |
| "콜백이 있으니 무조건 빠르다" | 병목이 CPU인지 I/O인지 | 비동기는 구조를 바꾸는 것이지 실제 작업 시간을 마법처럼 줄이지 않는다 |

## 흔한 오해와 함정

- "비동기 코드를 쓰면 반드시 빠르다" — 잘못된 이해다. 비동기는 스레드가 기다리지 않도록 구조를 바꾸는 것이지 작업 자체가 빨라지지는 않는다.
- "동기는 무조건 나쁘다" — 단순한 요청·응답 흐름에는 동기 코드가 더 읽기 쉽고 유지 보수하기 쉽다.
- "블로킹 I/O를 쓰면 논블로킹으로 바꾸면 된다" — 논블로킹 I/O는 반드시 폴링이나 이벤트 루프와 함께 써야 의미가 있다. 혼자 쓰면 CPU를 쓸데없이 태운다.
- "`select()`나 `epoll()`을 쓰면 자동으로 비동기다" — 보통은 readiness를 기다리는 event loop 설계와 함께 봐야 한다. API 이름 하나만 보고 동기/비동기를 단정하면 안 된다.

## 실무에서 쓰는 모습

백엔드 서버에서 DB 조회를 예로 들면:

- **동기 블로킹**: 스레드가 DB 결과를 기다리는 동안 다른 요청을 처리 못 한다. 스레드 풀을 크게 가져가야 한다.
- **비동기 논블로킹**: 스레드가 DB 응답을 기다리지 않고 다른 요청을 처리하다가 콜백으로 결과를 받는다. 적은 스레드로 더 많은 요청을 소화한다.

Spring WebFlux, Node.js, Vert.x 같은 비동기 프레임워크가 이 방식을 사용한다.

반대로 Spring MVC처럼 요청당 스레드를 잡는 모델은 동기 + 블로킹 흐름이 기본이지만, 코드가 단순하고 디버깅이 쉬워 여전히 널리 쓰인다. "무조건 어느 한쪽이 우월하다"보다 트래픽 특성과 팀의 운영 난도를 같이 봐야 한다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "왜 blocking I/O가 thread pool 포화와 queue saturation으로 이어지는지"를 서버 관점에서 보고 싶으면: [Blocking I/O, 스레드 풀, 백프레셔 입문](./blocking-io-thread-pool-backpressure-primer.md)
> - "이벤트 루프가 실제로 어떻게 도는지"가 궁금하면: [I/O Models and Event Loop](./io-models-and-event-loop.md)
> - "epoll의 wakeup 규칙까지 보고 싶다"면: [epoll level/edge/oneshot wakeup semantics](./epoll-level-edge-oneshot-wakeup-semantics.md)
> - "파이프/프로세스 경계에서 왜 막히는지"가 궁금하면: [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md)

## 더 깊이 가려면

- [I/O Models and Event Loop](./io-models-and-event-loop.md) — select/epoll과 이벤트 루프를 연결해 비동기 I/O의 실제 구현 감각을 잡는다.
- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md) — 블로킹이 일어날 때 OS가 하는 일을 스케줄러 관점에서 본다.

## 면접/시니어 질문 미리보기

1. **동기·비동기와 블로킹·논블로킹은 어떻게 다른가요?**
   의도: 두 축이 독립적임을 이해하는지 확인. 핵심 답: "동기/비동기는 결과를 누가 기다리냐, 블로킹/논블로킹은 호출 중 스레드가 멈추냐의 차이다."

2. **비동기 코드가 항상 성능이 더 좋은가요?**
   의도: 무조건적인 믿음이 아닌 트레이드오프 이해 확인. 핵심 답: "I/O 집중 작업에선 유리하지만, 복잡도가 올라가고 CPU 집중 작업엔 이점이 없다."

## 한 줄 정리

동기/비동기는 결과를 언제 받느냐이고, 블로킹/논블로킹은 기다리는 동안 스레드가 멈추느냐다.

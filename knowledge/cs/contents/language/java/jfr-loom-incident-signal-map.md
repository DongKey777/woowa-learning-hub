---
schema_version: 3
title: JFR Loom Incident Signal Map
concept_id: language/jfr-loom-incident-signal-map
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 90
mission_ids:
- missions/payment
- missions/racingcar
review_feedback_tags:
- jfr
- virtual-thread
- incident-triage
aliases:
- JFR Loom Incident Signal Map
- jdk.ThreadPark VirtualThreadPinned SocketRead JavaMonitorEnter
- virtual thread JFR diagnostics
- Loom troubleshooting event combination
- ThreadPark getConnection Hikari pending
- JFR 가상 스레드 장애 신호 지도
symptoms:
- ThreadPark가 많다는 사실만 보고 virtual thread 문제라고 결론 내리며 pool wait, join wait, backpressure wait를 구분하지 못해
- VirtualThreadPinned 이벤트 몇 건만 보고 root cause로 단정해 duration, stack concentration, carrier saturation을 확인하지 않아
- SocketRead를 모두 네트워크 장애로만 해석해 JDBC DB lock wait나 downstream ownership 증거를 붙이지 못해
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- language/jfr-event-interpretation
- language/virtual-threads-project-loom
- language/thread-dump-state-interpretation
next_docs:
- language/jdbc-observability-under-virtual-threads
- language/virtual-thread-migration-pinning
- language/locksupport-park-unpark-permit-semantics
linked_paths:
- contents/language/java/jfr-event-interpretation.md
- contents/language/java/jfr-jmc-performance-playbook.md
- contents/language/java/virtual-threads-project-loom.md
- contents/language/java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md
- contents/language/java/jdbc-observability-under-virtual-threads.md
- contents/language/java/virtual-thread-vs-reactive-db-observability.md
- contents/language/java/thread-dump-state-interpretation.md
- contents/language/java/locksupport-park-unpark-permit-semantics.md
- contents/language/java/jcmd-diagnostic-command-cheatsheet.md
confusable_with:
- language/jdbc-observability-under-virtual-threads
- language/jfr-event-interpretation
- language/virtual-thread-migration-pinning
forbidden_neighbors: []
expected_queries:
- JFR에서 virtual thread 장애를 ThreadPark VirtualThreadPinned SocketRead JavaMonitorEnter 조합으로 어떻게 해석해?
- ThreadPark가 getConnection stack에 몰리고 Hikari pending이 오르면 어떤 incident fingerprint야?
- VirtualThreadPinned와 SocketRead가 같이 보이면 synchronized 안 blocking I/O를 왜 의심해야 해?
- SocketRead가 JDBC stack에서 길 때 네트워크 문제와 DB lock wait를 어떻게 구분해?
- JavaMonitorEnter와 DB lock wait를 JFR과 thread dump에서 분리하는 기준을 알려줘
contextual_chunk_prefix: |
  이 문서는 JFR Loom incident를 ThreadPark, VirtualThreadPinned, SocketRead/SocketWrite, JavaMonitorEnter 이벤트 조합으로 해석하는 advanced playbook이다.
  JFR virtual thread diagnostics, ThreadPark, VirtualThreadPinned, SocketRead, JavaMonitorEnter, Loom incident 질문이 본 문서에 매핑된다.
---
# JFR Loom Incident Signal Map

> 한 줄 요약: virtual thread 장애는 `Thread Park` 하나만 보고 해석하면 자주 틀린다. `jdk.ThreadPark`, `jdk.VirtualThreadPinned`, `jdk.SocketRead`/`jdk.SocketWrite`, `jdk.JavaMonitorEnter`를 같은 시간창에서 묶어 읽어야 pool wait, downstream stall, synchronized + I/O pinning, application lock convoy를 분리할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JFR Event Interpretation](./jfr-event-interpretation.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [Virtual Thread Migration: Pinning, `ThreadLocal`, and Pool Boundary Strategy](./virtual-thread-migration-pinning-threadlocal-pool-boundaries.md)
> - [JDBC Observability Under Virtual Threads](./jdbc-observability-under-virtual-threads.md)
> - [Virtual Thread vs Reactive DB Observability](./virtual-thread-vs-reactive-db-observability.md)
> - [Thread Dump State Interpretation](./thread-dump-state-interpretation.md)
> - [`LockSupport.park`/`unpark` Permit Semantics and Coordination Pitfalls](./locksupport-park-unpark-permit-semantics.md)

> retrieval-anchor-keywords: JFR Loom incident map, jdk.ThreadPark, Java Thread Park, jdk.VirtualThreadPinned, Virtual Thread Pinned, jdk.SocketRead, jdk.SocketWrite, jdk.JavaMonitorEnter, Java Monitor Blocked, virtual thread production incident, Loom troubleshooting, virtual thread observability, thread park getConnection, Hikari pending threads, synchronized IO pinning, carrier thread pinned, socket wait virtual thread, monitor convoy, monitor contention loom, DB lock wait vs monitor blocked, JFR virtual thread diagnostics

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [이벤트별 incident map](#이벤트별-incident-map)
- [조합별 fingerprint](#조합별-fingerprint)
- [실전 triage 순서](#실전-triage-순서)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

Loom 환경에서 "virtual thread가 많이 기다린다"는 사실만으로는 incident를 설명할 수 없다.  
같은 WAIT처럼 보여도 실제로는 전혀 다른 병목일 수 있다.

- `jdk.ThreadPark`: 스레드가 `park` 계열 대기 중이었다
- `jdk.VirtualThreadPinned`: virtual thread가 carrier에서 내려오지 못한 채 blocking 구간을 통과했다
- `jdk.SocketRead`/`jdk.SocketWrite`: 소켓 I/O에서 기다렸다
- `jdk.JavaMonitorEnter`: `synchronized` monitor 진입에서 막혔다

이 넷은 모두 duration 이벤트라서 "얼마나 오래 애플리케이션 코드가 안 돌았는가"를 보여준다.  
다만 의미는 서로 다르다.

virtual thread triage의 핵심 질문도 네 갈래로 쪼개면 빨라진다.

1. coordination 때문에 park된 것인가
2. downstream socket이 느린 것인가
3. blocking I/O가 pinning으로 carrier까지 묶은 것인가
4. 애플리케이션 monitor contention인가

짧은 stall은 기본 recording에서 빠질 수 있으므로, event count만 보고 "없다"고 단정하면 위험하다.  
실전에서는 60~120초 JFR 창을 잡고 thread dump, datasource metric, DB/HTTP 지표를 같은 시간창에서 같이 본다.

## 이벤트별 incident map

| 이벤트 | JFR/JMC에서 literal meaning | virtual-thread 운영에서 자주 만나는 incident | 성급한 오해 | 바로 붙일 다음 증거 |
|---|---|---|---|---|
| `jdk.ThreadPark` (`Java Thread Park`) | `LockSupport.park`, AQS, condition, future join 같은 park 기반 대기 시간 | datasource acquire wait, semaphore/rate limiter 대기, queue backlog, `Future.get()`/`join()` tail wait | `park`가 많으니 곧바로 pinning이나 monitor bug라고 결론내리기 쉽다 | stack trace, parked class, `getConnection()`/`join()`/`Semaphore.acquire()` 위치, Hikari pending, queue age |
| `jdk.VirtualThreadPinned` (`Virtual Thread Pinned`) | virtual thread가 blocking 동안 carrier에 계속 붙어 있었다 | `synchronized` 안 JDBC/HTTP/file I/O, 큰 임계영역 안 remote call, native/JNI/foreign boundary pinning | pinned event가 몇 건 보였다고 바로 root cause라고 단정하기 쉽다 | `blockingOperation`, `pinnedReason`, `carrierThread`, 같은 stack의 `SocketRead`/`JavaMonitorEnter`, carrier saturation |
| `jdk.SocketRead` / `jdk.SocketWrite` | 소켓 read/write에서 기다린 시간 | 느린 downstream HTTP, JDBC driver socket wait, DB slow query/lock wait, proxy/client slow consume | 무조건 네트워크 장애라고 읽기 쉽다 | remote host/port, bytes, JDBC/`HttpClient` stack, request timeout, DB lock wait/slow query 증거 |
| `jdk.JavaMonitorEnter` (`Java Monitor Blocked`) | `synchronized` monitor 진입을 기다린 시간 | cache refresh convoy, singleton guard, global serializer lock, legacy synchronized hot path | DB lock wait나 ordinary park와 같은 층위로 섞기 쉽다 | `monitorClass`, `previousOwner`, 임계영역 안 코드, lock 안 I/O 여부, 같은 시간창의 `VirtualThreadPinned` |

표의 핵심은 literal meaning과 incident meaning을 분리하는 것이다.  
예를 들어 `ThreadPark`는 "대기 방식"을 말할 뿐이고, root cause는 pool wait일 수도 fan-out join일 수도 있다.

## 조합별 fingerprint

| 신호 조합 | 자주 연결되는 incident | 왜 이렇게 읽는가 |
|---|---|---|
| `ThreadPark`가 `getConnection()`/pool borrow stack에 몰리고 `VirtualThreadPinned`와 `JavaMonitorEnter`는 약하다 | connection-pool wait, long transaction의 하류 증상 | virtual thread는 잘 park되지만 connection이 늦게 돌아와서 request가 조용히 쌓인다 |
| `SocketRead`가 JDBC `execute`/`commit` stack에서 길고, 뒤이어 `ThreadPark`가 pool acquire에 늘어난다 | DB slow query 또는 DB lock wait이 pool saturation으로 전염 | 상류는 DB wait인데, 하류에서 pending acquire가 2차로 튄다 |
| 같은 서비스 stack에서 `VirtualThreadPinned`와 `SocketRead`가 함께 보인다 | `synchronized` 안 blocking I/O, coarse lock + remote call | socket wait 자체보다 "carrier까지 같이 묶였다"는 점이 Loom 사고의 핵심이다 |
| `JavaMonitorEnter`가 cache/service singleton stack에 몰리고 socket wait는 약하다 | 애플리케이션 monitor convoy, 과도한 직렬화 | DB나 network보다 애플리케이션 lock 구조가 먼저 병목이다 |
| 부모 virtual thread는 `ThreadPark`로 `join()` 중이고, 자식 task 중 하나가 `SocketRead`에 오래 묶인다 | structured fan-out tail latency, 한 child의 downstream stall | 부모 park는 증상이고, 실제 병목은 느린 child task 쪽 socket wait다 |
| `ThreadPark`가 `Semaphore.acquire()`/queue take 쪽에 몰린다 | 의도된 admission control 또는 backpressure | 항상 버그는 아니지만 timeout, queue age, reject가 따라오면 latency debt가 쌓이고 있다는 뜻이다 |

virtual thread incident에서는 단일 이벤트보다 조합이 더 중요하다.  
`ThreadPark`는 흔히 하류 증상이고, `SocketRead`/`JavaMonitorEnter`/`VirtualThreadPinned`가 상류 원인을 더 잘 가리킨다.

## 실전 triage 순서

### 1. 같은 시간창에서 네 이벤트를 같이 본다

virtual thread 장애를 `ThreadPark`만 따로 뽑아 보면 pool wait와 join wait와 rate-limit wait가 한 덩어리로 보인다.  
반드시 socket, pinned, monitor 이벤트를 함께 본다.

### 2. event count보다 stack concentration을 먼저 본다

똑같이 500건이라도 의미가 다르다.

- 한 stack에 몰리면 hot bottleneck일 수 있다
- stack이 흩어져 있으면 정상 대기 분산일 수 있다
- duration이 길고 thread 수가 집중되면 운영 사고 가능성이 크다

### 3. `park`의 blocker를 business boundary로 번역한다

`park`는 기술 용어라서 바로 액션이 나오지 않는다.  
stack을 보고 아래 경계 중 어디인지 번역해야 한다.

- datasource acquire
- structured concurrency join
- semaphore / rate limiter
- queue consumer wait
- future completion wait

이 번역이 돼야 "pool을 볼지, fan-out child를 볼지, backpressure 정책을 볼지"가 갈린다.

### 4. pinned event는 "carrier를 같이 태웠는가"를 묻는다

virtual thread에서는 단순 blocking보다 carrier를 같이 붙잡았는지가 더 비싸다.  
그래서 `VirtualThreadPinned`가 보이면 lock 안 I/O, native boundary, 큰 critical section을 먼저 의심한다.

### 5. socket wait는 downstream ownership을 다시 확인한다

`SocketRead`가 JDBC stack이면 DB wait나 lock wait일 수 있고,  
`HttpClient` stack이면 외부 API stall일 수 있다.  
같은 socket wait라도 owner가 다르면 대응도 달라진다.

### 6. monitor blocked는 JVM lock과 DB lock을 분리해 준다

`JavaMonitorEnter`는 Java monitor 경합이다.  
DB lock wait는 보통 JDBC stack의 socket/execute/commit 정체로 먼저 드러난다.  
이 둘을 섞으면 pool만 키우거나 lock만 줄이는 잘못된 대응으로 흐르기 쉽다.

## 코드로 보기

### 1. JFR에서 Loom 관련 stall 이벤트를 한 번에 뽑는다

```bash
jcmd <pid> JFR.start name=loom-signals settings=profile duration=120s filename=/tmp/loom-signals.jfr
jfr print --events jdk.ThreadPark,jdk.VirtualThreadPinned,jdk.SocketRead,jdk.SocketWrite,jdk.JavaMonitorEnter /tmp/loom-signals.jfr
```

핵심은 한 이벤트씩 따로 보지 말고 같은 recording에서 나란히 보는 것이다.

### 2. triage 메모는 incident 언어로 바꿔 쓴다

```text
ThreadPark@getConnection + Hikari pending 상승 => pool wait / long transaction 상류 확인
SocketRead@PgConnection.read + commit 지연 => DB slow query 또는 lock wait 확인
VirtualThreadPinned + SocketRead@CacheService.load => synchronized 안 remote I/O 의심
JavaMonitorEnter@Service.refresh => app lock convoy 우선
```

이 메모 수준으로 번역이 되면 "thread가 많다" 같은 추상 표현에서 빨리 벗어날 수 있다.

### 3. thread dump를 같은 창에 붙이면 해석이 더 빨라진다

```bash
jcmd <pid> Thread.print
jcmd <pid> JFR.check
```

thread dump는 현재 정지 화면이고 JFR은 시간축이다.  
두 개를 같은 1~2분 창으로 맞추면 park와 pinned와 socket의 관계가 더 선명해진다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `ThreadPark`만 본다 | 가장 빠르게 wait가 많다는 사실은 확인할 수 있다 | pool wait, join wait, backpressure wait를 쉽게 혼동한다 |
| 네 이벤트를 같은 recording에서 같이 본다 | Loom incident 분리가 빨라진다 | stack/metric 상관관계를 읽는 시간이 더 든다 |
| pinned만 root cause로 집착한다 | lock + I/O 문제는 빨리 잡을 수 있다 | 실제 상류가 DB/socket/pool이어도 놓치기 쉽다 |
| socket wait를 모두 network 문제로 본다 | 외부 의존성 점검은 빠르다 | DB lock wait, client slow-consume, proxy backpressure를 오진할 수 있다 |

핵심은 JFR 이벤트를 "스레드 상태 이름"이 아니라 "운영 incident fingerprint"로 번역하는 것이다.

## 꼬리질문

> Q: `ThreadPark`가 많으면 virtual thread 도입이 실패한 건가요?
> 핵심: 아니다. park 자체는 정상 coordination일 수도 있다. stack과 blocker를 business boundary로 번역해야 한다.

> Q: `VirtualThreadPinned`가 몇 건만 보여도 바로 refactor해야 하나요?
> 핵심: 농도와 duration, carrier saturation을 같이 봐야 한다. 드문 pinned 한두 건만으로는 root cause가 아닐 수 있다.

> Q: JDBC stack의 `SocketRead`는 network 문제인가요, DB 문제인가요?
> 핵심: 둘 다 가능하지만 실전에서는 slow query나 DB lock wait가 socket wait로 드러나는 경우가 많다. DB 증거를 바로 붙여야 한다.

> Q: `Java Monitor Blocked`가 보이면 DB lock wait도 같은 계열인가요?
> 핵심: 아니다. `JavaMonitorEnter`는 JVM monitor 경합이고, DB lock wait는 보통 JDBC execute/commit/socket 정체로 먼저 나타난다.

## 한 줄 정리

virtual thread 장애 해석은 `ThreadPark` 하나가 아니라 `ThreadPark` + `VirtualThreadPinned` + socket wait + `JavaMonitorEnter` 조합을 incident fingerprint로 읽는 작업이다.

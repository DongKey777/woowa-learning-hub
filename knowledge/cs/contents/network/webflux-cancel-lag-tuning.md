# WebFlux Cancel-Lag Tuning

> 한 줄 요약: Reactor Netty/WebFlux는 downstream cancel 신호를 비교적 빨리 보지만, operator prefetch, explicit buffer, blocking bridge가 이미 받아 둔 일을 남겨 두면 cancel 이후에도 CPU, DB, 외부 호출이 한동안 계속된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [WebSocket heartbeat, backpressure, reconnect](./websocket-heartbeat-backpressure-reconnect.md)
> - [Spring Reactive Blocking Bridge and `boundedElastic` Traps](../spring/spring-reactive-blocking-bridge-boundedelastic-block-traps.md)
> - [Spring WebClient Connection Pool and Timeout Tuning](../spring/spring-webclient-connection-pool-timeout-tuning.md)

retrieval-anchor-keywords: webflux cancel lag tuning, reactor netty cancel lag, webflux prefetch cancellation, publishOn prefetch, flatMap prefetch cancel lag, onBackpressureBuffer cancel lag, boundedElastic cancel lag, blocking bridge cancellation, downstream disconnect zombie work, streaming cancel debt

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

Reactor Netty/WebFlux에서 cancel lag는 "cancel이 왔는가"보다 **cancel 전에 얼마나 많은 일을 이미 pipeline 안으로 들여보냈는가**의 문제다.

- Reactor Netty는 downstream close, reset, failed flush를 비교적 빨리 cancel로 바꿔 준다
- 하지만 prefetch queue에 이미 들어온 element는 바로 사라지지 않는다
- `onBackpressureBuffer`, `bufferTimeout`, replay 계열은 cancel 전 debt를 키운다
- `Mono.fromCallable(...).subscribeOn(boundedElastic())` 같은 bridge는 event-loop 보호에는 좋지만, 이미 시작된 blocking call 자체를 자동으로 멈추진 못한다

즉 WebFlux cancel lag는 transport보다 **admission control과 queue budget**의 문제로 보는 편이 정확하다.

### Retrieval Anchors

- `webflux cancel lag tuning`
- `reactor netty cancel lag`
- `publishOn prefetch`
- `flatMap prefetch cancel lag`
- `onBackpressureBuffer cancel lag`
- `boundedElastic cancel lag`
- `blocking bridge cancellation`

## 깊이 들어가기

### 1. Reactor Netty의 cancel은 빠르지만 소급 취소는 아니다

downstream client가 떠나면 Reactor Netty/WebFlux 경로에서는 보통 다음이 빨리 보인다.

- channel inactive / dispose
- write failure 또는 flush failure
- subscriber cancel / `doOnCancel`

하지만 이 신호는 "지금부터 더 이상 받지 않는다"는 뜻이지, **이미 queue나 scheduler에 올려 둔 작업을 과거로 되돌리는 신호**는 아니다.

그래서 봐야 하는 값은 보통 다음 두 시각의 차이다.

- downstream disconnect 관찰 시각
- producer 실제 중단 시각

이 차이가 cancel lag다.

### 2. prefetch는 throughput 힌트가 아니라 cancel debt를 정하는 레버다

`publishOn`, `flatMap`, `concatMap` 같은 operator는 처리량을 위해 downstream보다 조금 더 앞서 demand를 당겨 올 수 있다.  
이게 크면 live stream에서 이런 일이 생긴다.

- 네트워크는 이미 끊겼다
- 하지만 operator queue에는 아직 처리되지 않은 item이 남아 있다
- serialization, enrichment, fan-out이 몇 개 더 진행된다

특히 SSE, NDJSON, progress stream처럼 "최신 한두 개만 의미 있고 오래된 이벤트는 가치가 급감하는" 경로는 prefetch가 곧 cancel debt가 된다.

실무 감각은 이렇다.

- disconnect 뒤 남아도 되는 일이 거의 없으면 prefetch를 줄인다
- ordering이 중요하고 오래된 item 가치가 낮으면 `concatMap` 또는 낮은 concurrency를 고려한다
- throughput보다 빠른 stop가 중요하면 `limitRate`나 더 작은 batch를 쓴다

핵심은 prefetch를 단순 성능 knob이 아니라 **disconnect 이후 얼마만큼의 낭비를 허용할지 정하는 정책**으로 보는 것이다.

### 3. explicit buffer는 cancel lag를 더 읽기 어렵게 만든다

다음 계열은 모두 cancel lag를 키우거나 숨길 수 있다.

- `onBackpressureBuffer`
- `buffer` / `bufferTimeout`
- replay / cache
- 큰 queue를 둔 sink 또는 adapter

버퍼가 있으면 순간 burst를 흡수하는 장점은 있지만, live stream에서는 대가가 분명하다.

- client는 이미 떠났는데 버퍼 안 item을 계속 가공할 수 있다
- "cancel은 빨리 왔다"와 "실제 작업은 늦게 멈췄다"가 동시에 참이 된다
- CPU, DB, downstream API가 disconnect 이후에도 계속 돈다

그래서 interactive stream은 보통:

- 무한 buffer보다 bounded buffer
- 오래된 item을 버려도 되는 경로라면 drop/latest 계열 전략
- buffer depth와 cancel 이후 drain 개수 계측

이 셋을 먼저 점검하는 편이 낫다.

### 4. blocking bridge는 cancel을 협조적 취소 문제로 바꾼다

다음 패턴은 WebFlux에서 흔하다.

```java
Mono.fromCallable(() -> legacyClient.fetch())
    .subscribeOn(Schedulers.boundedElastic());
```

이 패턴의 장점은 명확하다.

- event-loop를 blocking I/O에서 보호한다
- bridge boundary를 코드에 드러낸다

하지만 cancel semantics는 별개다.

- 이미 시작된 JDBC/SDK/file I/O는 call 자체가 timeout 또는 interruption을 지원해야 빨리 멈춘다
- element마다 blocking bridge를 만들면 cancel 시점에 여러 blocking call이 이미 진행 중일 수 있다
- 넓은 `publishOn(boundedElastic())`은 "blocking call 하나"가 아니라 downstream 전체를 queue에 태워 cancel debt를 키울 수 있다

즉 `boundedElastic`은 event-loop 보호 장치이지, 자동 취소 장치가 아니다.  
WebFlux cancel lag를 줄이려면 bridge boundary를 좁히고, underlying client timeout과 cooperative stop 여부를 같이 봐야 한다.

### 5. 네트워크 buffering이 이미 있는데 app buffering까지 더하면 lag가 폭증한다

streaming 경로에는 app 밖에도 queue가 있다.

- compression flush
- TLS record coalescing
- proxy response buffering

이런 경로에서 app이 prefetch와 explicit buffer까지 크게 잡으면, 실제 wire progress보다 훨씬 앞서 일이 진행된다.

- client가 마지막으로 본 event는 40번
- app은 48번까지 enrichment를 끝냄
- proxy는 42번까지만 내보냈거나, 아예 41번 frame도 완성 못 했을 수 있다

이때 "보냈다"와 "가공했다"가 서로 다른 수치를 가지므로, cancel lag는 app 내부 메트릭과 wire-visible progress를 함께 봐야 한다.

### 6. 튜닝 순서는 queue를 줄이고, 경계를 좁히고, timeout을 맞추는 쪽이 안전하다

WebFlux cancel lag를 줄일 때 먼저 손댈 우선순위는 대체로 아래다.

1. live stream에서 불필요한 prefetch / concurrency를 줄인다
2. `onBackpressureBuffer` 같은 explicit buffer를 bounded 또는 drop 정책으로 바꾼다
3. 넓은 `publishOn(boundedElastic())`보다 좁은 blocking bridge를 쓴다
4. blocking client의 timeout, cancellation, interruption 지원을 확인한다
5. 마지막 정상 event id와 disconnect 이후 추가 수행 건수를 같이 기록한다

대개 "cancel hook 추가"보다 위 다섯 가지가 lag를 더 크게 바꾼다.

## 실전 시나리오

### 시나리오 1: SSE 탭을 닫았는데 DB 조회가 몇 개 더 돈다

`flatMap` concurrency와 prefetch가 높은 상태에서 각 event마다 blocking lookup을 붙였을 가능성이 크다.  
cancel은 빨리 왔어도 이미 in-flight call이 남아 있어 DB가 더 돈다.

### 시나리오 2: `doOnCancel`은 바로 찍히는데 CPU가 계속 높다

cancel hook은 reactive subscription 종료만 보여 준다.  
뒤에서 serialization queue, `onBackpressureBuffer`, `boundedElastic` task가 남아 있으면 CPU는 계속 쓸 수 있다.

### 시나리오 3: proxy access log는 `499`인데 origin은 이벤트를 더 많이 만들었다

edge는 downstream disconnect를 빨리 봤지만, origin app은 app-level prefetch와 buffering 때문에 더 앞서 가공을 끝낸 패턴일 수 있다.

### 시나리오 4: `publishOn(boundedElastic())` 하나 넣었더니 끊김 뒤 stop가 더 느려졌다

blocking call 격리 대신 downstream 변환 전체를 scheduler queue에 태워 버려 cancel debt가 커진 경우다.

## 코드로 보기

### cancel lag를 키우기 쉬운 패턴

```java
return jobEvents()
    .publishOn(Schedulers.boundedElastic())
    .flatMap(event ->
        Mono.fromCallable(() -> blockingEnricher.enrich(event))
            .subscribeOn(Schedulers.boundedElastic()))
    .onBackpressureBuffer(512)
    .map(this::toServerSentEvent);
```

왜 위험한가:

- 넓은 `publishOn`으로 downstream 전체가 queue를 탄다
- `flatMap`이 event를 앞당겨 받아 여러 작업을 동시에 연다
- buffer가 cancel 이후 drain할 일을 더 만든다

### cancel debt를 줄이는 쪽으로 조정한 패턴

```java
return jobEvents()
    .limitRate(1)
    .concatMap(event ->
        Mono.fromCallable(() -> blockingEnricher.enrich(event))
            .subscribeOn(Schedulers.boundedElastic())
            .timeout(Duration.ofSeconds(2)),
        1)
    .map(this::toServerSentEvent)
    .doOnCancel(() -> metrics.counter("stream.cancel").increment());
```

이 패턴의 의도는 다음과 같다.

- live stream에서 한 번에 앞서 받아 두는 양을 작게 유지
- blocking bridge를 개별 call 주변으로만 좁힘
- cancel 뒤 오래 남는 blocking call은 timeout으로 상한 설정

### 운영에서 같이 찍어야 할 값

```text
t1 downstream disconnect observed by proxy or Reactor Netty
t2 reactive cancel observed
t3 last blocking task started
t4 last blocking task finished
t5 producer fully stopped

cancel lag = t5 - t1
post-cancel work = tasks/events completed after t1
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 작은 prefetch / 낮은 concurrency | cancel debt를 줄인다 | peak throughput이 줄 수 있다 | SSE, progress stream, live NDJSON |
| bounded buffer + drop 정책 | 메모리와 post-cancel work를 제한한다 | 중간 업데이트 일부를 버릴 수 있다 | 최신 상태만 중요할 때 |
| 좁은 blocking bridge | event-loop 보호와 cancel 경계가 선명해진다 | bridge 설계와 timeout 관리가 필요하다 | legacy blocking 통합 |
| 넓은 `publishOn(boundedElastic())` | 적용은 쉽다 | queue가 커지고 cancel path가 흐려진다 | 대개 live stream에는 비권장 |
| cancel-aware underlying client | disconnect 뒤 낭비를 크게 줄인다 | 라이브러리 선택 제약이 생긴다 | 비싼 외부 API/JDBC/file I/O |

핵심은 WebFlux cancel lag를 "Netty가 느리다"보다 **prefetch, buffer, blocking boundary가 너무 많은 일을 미리 받아 둔 상태**로 해석하는 것이다.

## 꼬리질문

> Q: `doOnCancel`이 바로 찍혔는데 왜 작업이 더 돌죠?
> 핵심: cancel 신호는 도착했지만, prefetch queue나 이미 시작된 blocking call이 남아 있으면 실제 stop는 늦어진다.

> Q: prefetch를 항상 1로 두는 게 맞나요?
> 핵심: 아니다. throughput은 떨어질 수 있다. 다만 disconnect 이후 낭비가 큰 live stream에서는 작은 값이 더 유리하다.

> Q: `boundedElastic`만 쓰면 cancel lag 문제가 해결되나요?
> 핵심: 아니다. event-loop 보호에는 좋지만, underlying blocking call의 timeout/cancel 지원까지 대신해 주진 않는다.

> Q: proxy `499`만 줄이면 충분한가요?
> 핵심: 아니다. `499`는 downstream 관찰이고, app 내부 prefetch/buffer 때문에 post-cancel work는 더 클 수 있다.

## 한 줄 정리

WebFlux cancel lag는 대개 Reactor Netty cancel 감지 속도보다, prefetch와 buffer와 blocking bridge가 disconnect 전에 얼마나 많은 일을 이미 admission했는지가 결정한다.

# SSE Last-Event-ID Replay Window

> 한 줄 요약: SSE reconnect는 "다시 붙는다"가 아니라 "마지막으로 완전히 반영된 이벤트 이후를 복구한다"는 뜻이다. 그래서 `Last-Event-ID`, replay window, duplicate suppression, gap recovery 규칙을 같이 설계해야 partial delivery 뒤에도 상태를 복원할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
> - [SSE, WebSocket, Polling](./sse-websocket-polling.md)
> - [WebSocket Heartbeat, Backpressure, Reconnect](./websocket-heartbeat-backpressure-reconnect.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md)
> - [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)

retrieval-anchor-keywords: SSE Last-Event-ID, SSE replay window, SSE reconnect replay, partial SSE delivery, duplicate suppression, SSE gap recovery, at-least-once stream, replay cursor, idempotent event apply, EventSource reconnect

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

SSE에서 `Last-Event-ID`는 "서버가 마지막으로 write를 시도한 이벤트"가 아니라 **클라이언트가 완전한 frame으로 처리한 마지막 이벤트 id**다.

그래서 reconnect 설계는 보통 아래 넷을 같이 가져간다.

- stable event `id`
- 해당 `id`를 다시 읽을 수 있는 replay window
- reconnect 시 `Last-Event-ID` 이후를 재전송하는 규칙
- 중복 도착을 흡수하는 duplicate suppression

이 넷 중 하나라도 빠지면 partial flush failure 뒤 상태 복원이 애매해진다.

### Retrieval Anchors

- `SSE Last-Event-ID`
- `SSE replay window`
- `partial SSE delivery`
- `duplicate suppression`
- `SSE gap recovery`
- `at-least-once stream`
- `replay cursor`
- `EventSource reconnect`

## 깊이 들어가기

### 1. `Last-Event-ID`는 바이트 ack가 아니라 "완성된 이벤트 cursor"다

브라우저는 완전한 SSE event frame을 파싱한 뒤에야 그 `id`를 다음 reconnect의 `Last-Event-ID`로 쓴다.

- `id: 41\n`
- `data: progress\n\n`

여기서 마지막 빈 줄 전 flush가 끊기면:

- 서버는 41번 write를 시도했다고 믿을 수 있다
- 일부 바이트가 wire에 올라갔을 수도 있다
- 하지만 브라우저는 41번 이벤트를 완료로 보지 않을 수 있다
- 다음 reconnect의 `Last-Event-ID`는 여전히 `40`일 수 있다

즉 `Last-Event-ID`는 partial delivery 뒤의 **복구 기준점**이지, TCP-level delivery ack가 아니다.

### 2. replay window는 "최근 로그"가 아니라 "복구 가능한 범위"여야 한다

replay window는 단순히 최근 N개를 메모리에 쌓아 두는 기능이 아니다. reconnect가 들어왔을 때 아래 질문에 일관되게 답할 수 있어야 한다.

- `Last-Event-ID=40`이면 41부터 다시 줄 수 있는가
- 40이 너무 오래돼서 window 밖이면 gap이라고 명확히 말할 수 있는가
- node failover 뒤에도 같은 id를 같은 의미로 다시 보낼 수 있는가

그래서 window 설계에서는 세 가지 불변식이 중요하다.

- `id`는 stream scope 안에서 stable해야 한다
- reconnect replay는 `id > last_event_id` 규칙을 지켜야 한다
- earliest retained id보다 오래된 cursor에는 "부분 복구"가 아니라 "재동기화 필요"를 선언해야 한다

특히 여러 shard나 room이 섞인 stream이면 "무조건 전역 증가 정수 하나"보다 **해당 stream에서 재생 가능한 cursor**가 더 중요하다.

### 3. recovery 결과는 셋이 아니라 넷으로 나뉜다

| 상태 | 의미 | 서버 동작 | 클라이언트 기대 동작 |
|------|------|-----------|----------------------|
| exact replay | cursor가 window 안에 있다 | `id > Last-Event-ID`만 재전송 | 이어서 apply |
| duplicate overlap | 같은 이벤트가 한 번 더 올 수 있다 | strict replay를 해도 race나 다중 연결에서 중복 가능 | `id` 또는 business key로 dedupe |
| gap / window miss | cursor가 earliest retained보다 오래됐다 | 임의로 최신부터 보내지 말고 재동기화 신호를 준다 | snapshot 재조회 또는 full reload |
| invalid cursor | 미래 id, 다른 stream id, 파싱 불가 | 400 또는 reset event로 거부 | cursor 버리고 새 세션 시작 |

실무에서 가장 위험한 실수는 `window miss`를 조용히 `latest tail`로 바꾸는 것이다. 그러면 이벤트 일부가 영구히 빠졌는데도 운영자가 모른다.

### 4. duplicate suppression은 replay window의 보조가 아니라 필수다

많이 오해하는 점은 "`Last-Event-ID`가 있으니 중복은 없다"는 생각이다. 실제로는 SSE reconnect를 **at-least-once delivery에 가까운 경계**로 보는 편이 안전하다.

중복이 생기는 경로:

- reconnect race로 같은 이벤트가 두 연결에 모두 도착
- 서버가 inclusive replay를 잘못 구현
- load balancer 재시도나 tab restore로 동일 cursor 재사용
- 클라이언트가 이벤트는 처리했지만 local persist 전에 다시 끊김

그래서 duplicate suppression은 보통 두 층으로 둔다.

- 서버: stable id, deterministic replay order, `id > cursor` 재생
- 클라이언트: `lastAppliedId` 또는 business id 기준 ignore

UI 업데이트처럼 부작용이 작은 경우도 dedupe는 필요하고, 결제/상태 전이처럼 side effect가 있으면 더더욱 **idempotent apply**가 필요하다.

### 5. partial delivery 뒤에는 "마지막 write 시도"보다 "마지막 안전 replay 지점"이 중요하다

예를 들어 서버가 `41`을 fan-out했는데 frame 끝에서 끊겼다면, 복구 관점의 진실은 아래다.

- origin log: 41 write attempted
- browser state: 40까지 완료
- reconnect cursor: `Last-Event-ID: 40`
- safe replay point: 41부터 다시 전송

즉 운영 지표도 "마지막 전송 시도 id"와 "마지막 정상 완료 id"를 분리해 남겨야 한다. 이 차이를 뭉개면 duplicate냐 gap이냐를 해석할 수 없다.

### 6. window miss 뒤 recovery semantics를 미리 정해 둬야 한다

오래 offline이었다가 돌아온 client는 replay window 밖으로 쉽게 밀려난다. 이때 선택지는 대개 셋 중 하나다.

- snapshot API를 먼저 다시 읽고, 그 이후부터 live stream 재연결
- `reset` 또는 `resync-required` 같은 이벤트를 보내고 stream 종료
- durable log가 있으면 더 긴 window에서 재생

피해야 할 것은 "earliest retained부터 그냥 흘려보내기"다. 이렇게 하면 이미 놓친 구간이 있다는 사실이 감춰진다.

### 7. replay 저장소는 연결 수가 아니라 복구 SLO에 맞춰 정해야 한다

저장소 선택은 "동접 몇 명인가"보다 "client가 얼마나 오래 끊겨 있어도 무손실에 가깝게 복구하고 싶은가"에 가깝다.

- 짧은 reconnect만 허용: in-memory ring buffer
- node failover까지 버텨야 함: shared durable log
- 이벤트량이 너무 큼: snapshot + delta 조합

핵심은 retention을 "메모리 절약 값"으로만 잡지 말고, **모바일 background 복귀 시간, 배포 drain 시간, proxy idle timeout 후 재접속 지연**을 반영하는 것이다.

## 실전 시나리오

### 시나리오 1: 41번 progress 이벤트가 반쯤 나가다 끊겼다

- 서버 로그는 41 flush attempted
- 브라우저는 41 frame을 끝까지 못 받아 무시
- reconnect 요청은 `Last-Event-ID: 40`
- 서버는 41부터 replay

이때 41을 건너뛰면 gap이고, 40부터 inclusive replay하면 duplicate suppression이 필요하다.

### 시나리오 2: 사용자가 모바일 background 상태로 15분 있다 돌아왔다

window가 최근 2분만 보관하면 cursor가 window 밖일 수 있다.

- 잘못된 대응: 최신 이벤트 몇 개만 보내고 계속 live
- 맞는 대응: snapshot 재조회 또는 resync-required

복구 가능한 범위를 넘어섰으면 "이어받기 실패"를 명시해야 한다.

### 시나리오 3: 같은 알림이 두 번 보인다

원인은 여러 가지다.

- 탭이 두 개 열려 있음
- reconnect race
- 서버 inclusive replay 버그
- client local store 반영 전 disconnect

해결은 "브라우저가 알아서 안 보낼 것"을 믿는 게 아니라, client가 `lastAppliedId >= event.id`를 무시하도록 두는 것이다.

### 시나리오 4: 배포 뒤 다른 node로 붙으면 replay가 안 된다

node-local memory에만 window가 있으면 failover 후 새 node는 이전 cursor를 모른다.

- 단일 node 실험 환경에서는 괜찮아 보인다
- 실서비스 multi-node나 drain 배포에서는 reconnect 손실이 드러난다

이 경우 replay 저장소를 shared log로 옮기거나, snapshot + delta 재동기화 경로를 강제해야 한다.

## 코드로 보기

### 서버 측 replay 판단

```text
on_connect(stream_key, last_event_id):
  if last_event_id is null:
    return live_tail()

  if last_event_id < earliest_retained_id(stream_key):
    emit reset/resync-required
    close_or_redirect_to_snapshot()
    return

  replay events where event.id > last_event_id
  then join live tail
```

### 발행 시 저장과 fan-out

```text
publish(stream_key, payload):
  event_id = next_stable_id(stream_key)
  persist_to_replay_window(stream_key, event_id, payload)
  fan_out_sse_frame(id=event_id, data=payload)
```

### 클라이언트 duplicate suppression

```text
on_event(event):
  if event.id <= last_applied_id:
    ignore duplicate
    return

  apply_idempotent_update(event)
  last_applied_id = event.id
```

### 운영 체크리스트

```text
- stream scope 안에서 event id가 stable한가
- replay가 strict하게 id > Last-Event-ID인가
- earliest retained id를 metrics/log로 볼 수 있는가
- window miss 시 resync path가 명시적인가
- client가 duplicate suppression과 idempotent apply를 갖고 있는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 짧은 in-memory ring buffer | 구현이 가장 단순하다 | long disconnect, failover에 약하다 | 단일 node, 짧은 reconnect |
| shared durable replay log | drain/failover 후에도 replay 가능하다 | 인프라 비용과 운영 복잡도가 오른다 | multi-node 실시간 서비스 |
| snapshot + delta recovery | 긴 오프라인 복귀를 처리하기 쉽다 | snapshot 정합성과 cutover가 어렵다 | 이벤트량이 큰 상태형 feed |
| client-side strict dedupe | duplicate 노이즈를 많이 줄인다 | local persist와 idempotent reducer 설계가 필요하다 | 알림, 진행률, 상태 스트림 전반 |

핵심은 SSE 복구를 "transport reconnect"가 아니라 **cursor recovery + duplicate control + gap semantics**로 보는 것이다.

## 꼬리질문

> Q: `Last-Event-ID`가 있으면 중복 처리는 필요 없지 않나요?
> 핵심: 아니다. reconnect race와 local persist 타이밍 때문에 SSE는 at-least-once처럼 다루는 편이 안전하다.

> Q: replay window 밖이면 그냥 최신부터 보내면 안 되나요?
> 핵심: 안 된다. 그 순간 이미 gap이 생겼으므로 resync를 명시해야 한다.

> Q: partial delivery 때 서버 로그상 write 성공 시도가 있으면 그 이벤트는 받은 것 아닌가요?
> 핵심: 아니다. 브라우저는 완성된 SSE frame만 처리하므로 `Last-Event-ID`가 더 신뢰할 수 있는 복구 기준이다.

## 한 줄 정리

SSE reconnect를 안정적으로 만들려면 stable event id, replay window, duplicate suppression, gap recovery를 한 세트로 설계해야 하며, partial delivery 뒤의 진실은 "마지막 write 시도"가 아니라 "마지막 정상 `Last-Event-ID`"에 있다.

---
schema_version: 3
title: Spring SSE Replay Buffer Last Event ID Recovery Patterns
concept_id: spring/sse-replay-buffer-last-event-id-recovery-patterns
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
review_feedback_tags:
- sse-replay-buffer
- last-event-id
- recovery
- eventsource-resume-recovery
aliases:
- SSE replay buffer Last-Event-ID
- EventSource resume recovery
- replay window multi instance
- ordering hole fence
- durable event id contract
- SSE reconnect data loss
intents:
- deep_dive
- design
- troubleshooting
linked_paths:
- contents/spring/spring-sse-proxy-idle-timeout-matrix.md
- contents/spring/spring-sse-disconnect-observability-patterns.md
- contents/spring/spring-sseemitter-timeout-callback-race-matrix.md
- contents/spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md
- contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md
- contents/network/sse-last-event-id-replay-window.md
- contents/language/java/sse-last-event-id-replay-reconnect-ownership.md
symptoms:
- Last-Event-ID 헤더는 오지만 서버에 replay 가능한 event window가 없어 손실이 난다.
- reconnect 중 생성된 이벤트의 ordering hole을 막지 못한다.
- multi-instance 배포에서 이전 node의 in-memory replay buffer를 찾지 못한다.
expected_queries:
- Spring SSE에서 Last-Event-ID만 있으면 끊긴 이벤트를 복구할 수 있어?
- replay buffer window와 event id 계약은 어떻게 설계해야 해?
- reconnect 동안 ordering hole을 막는 fence는 왜 필요해?
- multi-instance SSE에서 replay state를 어디에 둬야 해?
contextual_chunk_prefix: |
  이 문서는 SSE 복구가 Last-Event-ID 헤더 하나로 끝나지 않고 replay 가능한 event id,
  replay window, reconnect fence, ordering hole 방지, multi-instance state placement를 함께
  설계해야 실제 resume이 된다는 점을 설명한다.
---
# Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns

> 한 줄 요약: Spring SSE 복구는 `Last-Event-ID` 헤더 하나로 끝나지 않고, replay 가능한 event `id` 계약, reconnect 동안 ordering hole를 막는 fence, multi-instance에서도 살아남는 replay window를 함께 설계해야 실제 손실 없이 resume된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
> - [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
> - [Spring `SseEmitter` Timeout Callback Race Matrix](./spring-sseemitter-timeout-callback-race-matrix.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)
> - [Spring EventListener / TransactionalEventListener / Outbox](./spring-eventlistener-transaction-phase-outbox.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

retrieval-anchor-keywords: spring SSE replay buffer, SSE replay window, Last-Event-ID recovery, SseEmitter replay, event replay cursor, resume token, replay fence, high water mark, recovery watermark, event ordering fence, replay then subscribe gap, subscribe then replay reorder, sticky session SSE failover, multi instance SSE recovery, Redis Streams SSE, Kafka offset SSE, outbox replay log, at least once SSE, duplicate event id, stale Last-Event-ID, reset event, snapshot then stream, emitter replacement race, old emitter cleanup, compare and remove registry, reconnect ownership

## 핵심 개념

SSE reconnect를 "브라우저가 다시 붙는다" 수준으로만 보면 복구 설계가 금방 틀어진다.

실제로 서버는 세 가지를 동시에 맞춰야 한다.

- 어떤 event가 replay 가능한 business event인가
- `Last-Event-ID`가 가리키는 cursor 뒤 구간을 얼마나 오래 보존하는가
- replay가 끝나고 live stream으로 넘어갈 때 ordering hole 없이 붙일 수 있는가

즉 `Last-Event-ID`는 단독 기능이 아니라, **event id 계약 + replay window + live handoff fence** 위에서만 의미가 생긴다.

## 먼저 구분할 것: `Last-Event-ID`는 transport cursor이지 delivery 보장이 아니다

브라우저 `EventSource`는 마지막으로 받은 SSE event 중 `id:`가 있던 값을 다음 reconnect의 `Last-Event-ID` 헤더로 보낸다.

여기서 중요한 점은 세 가지다.

- 브라우저는 "UI가 렌더링을 끝냈다"가 아니라 "가장 최근에 본 `id`가 무엇이냐"만 기억한다
- `id`가 없는 heartbeat comment나 control frame은 cursor를 전진시키지 않는다
- 서버는 `Last-Event-ID` 이후 구간을 다시 읽어 줄 수 있어야만 복구라고 부를 수 있다

즉 `Last-Event-ID`가 있어도 서버 쪽 replay source가 없으면 reconnect는 그냥 새 연결일 뿐이다.

### control frame에 `id`를 붙일지 먼저 결정해야 한다

다음 이벤트들은 대개 replay cursor에 포함하지 않는 편이 안전하다.

- heartbeat comment
- `"ready"`, `"connected"` 같은 synthetic welcome event
- `"reset"` 같은 control signal

이런 frame에 `id`를 붙이면 브라우저는 그 값을 다음 `Last-Event-ID`로 보낸다.
그 결과 서버가 "마지막 business event 이후"가 아니라 "마지막 control frame 이후"를 기준으로 replay하게 되어 recovery semantics가 흐려진다.

## Event ID는 stream 범위 안에서만 강하게 정렬되면 된다

SSE 복구에서 필요한 건 보통 "전 시스템 global total order"가 아니라, **클라이언트가 구독하는 stream key 안에서 비교 가능한 순서**다.

예를 들어 stream key는 다음처럼 잡을 수 있다.

- 사용자별 알림: `(tenant_id, user_id)`
- 주문 상태 feed: `(tenant_id, order_id)`
- 대시보드 채널: `(tenant_id, dashboard_id, topic)`

이 key 안에서만 event `id`가 증가하고 replay query가 가능하면 대부분 충분하다.

| ID 원천 | ordering 강도 | 장점 | 주의점 |
|---|---|---|---|
| stream별 sequence / DB cursor | 강함 | range replay가 단순하고 의미가 명확하다 | hot stream이 많으면 allocation 설계가 필요하다 |
| Redis Stream ID / broker offset | stream 또는 partition 안에서 강함 | durable log와 cursor를 재사용할 수 있다 | partition key가 stream key와 다르면 ordering 보장이 무너진다 |
| ULID / time-sortable UUID | 중간 | 중앙 sequence 없이 발급 가능하다 | clock skew와 동시 발급 때문에 strict order로 쓰기 어렵다 |
| wall-clock timestamp | 약함 | 구현이 쉽다 | 동일 밀리초 경합, 역전, dedup 불안정 때문에 recovery cursor로 부적합하다 |

실전 기준은 이렇다.

- SSE용 `id`는 "다음 reconnect가 바로 range query에 쓸 수 있는 값"이어야 한다
- client가 여러 topic을 한 stream에 섞어 받는다면, 그 전체 stream 기준으로 monotonic해야 한다
- reconnect 복구는 보통 at-least-once이므로 client는 `id` 기준 duplicate를 견딜 수 있어야 한다
- global ordering이 정말 필요하지 않다면 shard-local / stream-local ordering으로 제한하는 편이 운영이 쉽다

## Replay Window는 시간과 개수를 같이 잡아야 한다

reconnect가 성공하려면 `Last-Event-ID`가 아직 서버가 기억하는 tail 안에 있어야 한다.
이 tail retention이 replay window다.

가장 흔한 실수는 count-only ring buffer 하나로 끝내는 것이다.

- 평소에는 `1,000`개 버퍼면 충분해 보여도
- burst 순간 이벤트가 몰리면 10초 만에 tail이 밀릴 수 있다
- 반대로 저빈도 stream은 5분 reconnect를 허용하고 싶은데 count만으로는 보장이 약하다

따라서 replay window는 보통 **time + count 이중 제약**으로 본다.

```text
window_time >= client_retry_budget + edge_failover_budget + deploy_or_drain_budget + safety_slack
window_count >= peak_events_per_stream_during(window_time)
```

여기서 `edge_failover_budget`에는 다음이 들어갈 수 있다.

- ALB / Nginx idle close 뒤 browser reconnect 지연
- mobile network handoff
- pod eviction / rolling deploy 중 짧은 failover

### reconnect 분기 자체를 명시적으로 설계해야 한다

| reconnect 입력 | 서버 판단 | 권장 동작 |
|---|---|---|
| `Last-Event-ID` 없음 | 최초 연결 또는 cursor 유실 | live-only 또는 snapshot + live 시작 |
| `Last-Event-ID`가 tail 이상 head 이하 | replay 가능 | `(lastId, highWaterMark]` 구간 replay 뒤 live 연결 |
| `Last-Event-ID`가 tail보다 오래됨 | window 밖 | full snapshot, `reset` event, 또는 `409` 같은 explicit reset |
| `Last-Event-ID`가 현재 stream key와 안 맞음 / 파싱 실패 | 잘못된 cursor | reset 또는 명시적 오류. 조용히 무시하지 않는다 |

핵심은 "window 밖이면 어떻게 reset할지"를 미리 정하는 것이다.
그렇지 않으면 reconnect는 되는데 일부 이벤트만 조용히 사라지는 모호한 상태가 된다.

## replay와 live handoff 사이의 ordering hole를 막아야 한다

`Last-Event-ID` 설계에서 가장 자주 빠지는 구멍은 "replay는 했는데 그 사이 live 이벤트를 놓침"이다.

### 1. `replay -> subscribe` 순서는 gap을 만든다

```text
read events after lastId
-> replay them to client
-> subscribe live publisher
```

이 방식은 replay를 읽은 직후부터 subscription이 붙기 전 사이에 새로 생긴 이벤트를 놓칠 수 있다.
구현은 단순하지만 resume guarantee는 약하다.

### 2. `subscribe -> replay` 순서는 역전과 중복을 만들기 쉽다

```text
subscribe live publisher
-> live event starts arriving
-> replay older events afterwards
```

이 방식은 blind spot은 줄지만, live event가 replay보다 먼저 도착해 ordering이 뒤집히기 쉽다.
per-connection queue가 없으면 out-of-order가 난다.

### 3. 보통은 high-water mark fence가 필요하다

권장 패턴은 reconnect 시점에 replay 상한을 먼저 고정하는 것이다.

1. `Last-Event-ID`를 parse하고 stream key를 확정한다.
2. replay source에서 현재 `highWaterMark = H`를 읽는다.
3. live publisher는 `H` 초과 event만 connection-local queue에 적재하도록 준비한다.
4. `(lastId, H]` 구간을 정렬된 순서로 replay한다.
5. replay가 끝나면 queue에 쌓인 `> H` event를 drain하고 live 모드로 전환한다.

이렇게 하면 replay 구간과 live 구간이 `H`에서 맞물린다.

| handoff 패턴 | 장점 | 문제 |
|---|---|---|
| replay 후 subscribe | 구현이 가장 단순하다 | subscribe attach 전 gap 손실 |
| subscribe 후 replay | gap이 줄어든다 | replay/live 역전, duplicate handling 필요 |
| `highWaterMark` fence + queue | gap과 역전을 함께 줄인다 | store/bus가 cursor upper-bound와 after-cursor subscription을 지원해야 한다 |

즉 resume의 진짜 난점은 `Last-Event-ID` 파싱이 아니라 **replay와 live를 같은 ordering contract로 묶는 것**이다.

## Multi-Instance에선 emitter registry보다 replay source가 더 중요하다

Spring MVC `SseEmitter` registry는 보통 인스턴스 메모리에 있다.
이 자체는 자연스럽지만, 복구까지 메모리에 의존하면 multi-instance failover에서 바로 한계가 나온다.

| 토폴로지 | failover replay | ordering 강도 | 운영 비용 | 언제 맞는가 |
|---|---|---|---|---|
| 인스턴스 로컬 ring buffer | 거의 없음 | 같은 인스턴스 안에서는 강함 | 낮음 | 단일 노드, dev, 짧은 demo |
| 로컬 buffer + sticky session | 같은 노드 재접속엔 부분적으로 유리 | node restart / reschedule에는 약함 | 낮음~중간 | 짧은 reconnect만 중요하고 failover 요구가 낮을 때 |
| shared replay store + 로컬 emitter | 좋음 | stream key 기준으로 강하게 맞출 수 있다 | 중간 | 일반적인 multi-instance 기본값 |
| broker log + stateless app node | 매우 좋음 | partition/stream 단위로 강함 | 높음 | fan-out가 크고 durable replay가 중요한 경우 |

여기서 `sticky session`은 복구 전략이 아니라 **최적화**에 가깝다.

- 같은 pod로 바로 돌아오면 local hot buffer를 재사용할 수 있다
- 하지만 pod eviction, autoscaling, deploy drain, cross-zone failover에는 무력하다

즉 multi-instance에서 `Last-Event-ID`를 진지하게 쓰려면 "새 인스턴스가 이전 인스턴스의 tail을 읽을 수 있는가?"가 핵심 질문이다.

### shared replay source 후보를 단순 비교하면

| source | 장점 | 단점 | 자주 맞는 경우 |
|---|---|---|---|
| RDB outbox / append table | business transaction과 가까워 정합성이 높다 | query cost와 trimming 전략을 직접 설계해야 한다 | low-to-medium throughput, audit 중요 |
| Redis Streams | cursor와 trim 모델이 명확하고 cross-instance에 쉽다 | 메모리 관리와 retention 정책이 중요하다 | 빠른 reconnect 복구, moderate fan-out |
| Kafka / durable broker log | 큰 fan-out와 durable replay에 강하다 | partitioning, consumer handoff, infra 복잡도 증가 | high throughput, event backbone 존재 |

핵심은 기술 이름보다, **stream key와 replay cursor가 backend ordering model과 같은 경계를 쓰는가**다.

## Snapshot 복구가 exact replay보다 나은 경우도 있다

모든 SSE UI가 "모든 중간 상태 변화"를 다시 받아야 하는 것은 아니다.

예를 들어 대시보드가 원하는 게 최종 상태라면:

- reconnect 시점에 현재 snapshot 1건을 다시 보내고
- 그 뒤 새 event만 live로 이어 붙이는 편이
- 긴 replay window를 유지하는 것보다 단순하고 값쌀 수 있다

| 복구 방식 | 장점 | 단점 | 언제 적합한가 |
|---|---|---|---|
| exact replay | 중간 상태 변화까지 보존 가능 | replay source, ordering fence, retention 비용이 크다 | 감사성 feed, activity timeline |
| snapshot + live | 구현이 단순하고 window 압박이 작다 | 중간 event는 재현되지 않는다 | 최신 상태 dashboard, progress bar, cache refresh UI |
| reset 후 full reload | 의미가 명확하다 | UX가 거칠고 client 코드가 더 필요하다 | replay miss를 조용히 숨기면 안 되는 경우 |

즉 "resume"의 목표가 정말 event history 보존인지, 아니면 최신 상태 수렴인지 먼저 정해야 한다.

## 코드로 보기

### `Last-Event-ID`를 replay session으로 열고, 그 뒤 live를 붙인다

```java
@GetMapping(path = "/events/orders", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public SseEmitter orderEvents(
        @AuthenticationPrincipal UserPrincipal principal,
        @RequestHeader(name = "Last-Event-ID", required = false) String lastEventId
) throws IOException {
    ReplaySession session = replayService.open(
            StreamKey.userOrders(principal.id()),
            lastEventId
    );

    if (session.requiresReset()) {
        throw new ResponseStatusException(HttpStatus.CONFLICT, "Replay window expired");
    }

    SseEmitter emitter = new SseEmitter(Duration.ofMinutes(15).toMillis());

    Runnable cleanup = session::close;

    emitter.onCompletion(cleanup);
    emitter.onTimeout(() -> {
        cleanup.run();
        emitter.complete();
    });
    emitter.onError(ex -> cleanup.run());

    emitter.send(SseEmitter.event()
            .name("ready")
            .reconnectTime(session.retryHint().toMillis())
            .data("connected"));

    for (DomainEvent event : session.replayEvents()) {
        sendOrComplete(emitter, event);
    }

    session.startLive(event -> sendOrComplete(emitter, event));
    return emitter;
}

private void sendOrComplete(SseEmitter emitter, DomainEvent event) {
    try {
        emitter.send(SseEmitter.event()
                .id(event.cursor())
                .name(event.type())
                .data(event.payload()));
    }
    catch (IOException ex) {
        emitter.complete();
    }
}
```

이 코드에서 중요한 건 `@RequestHeader("Last-Event-ID")` 자체가 아니다.
`replayService.open(...)`가 다음 책임을 이미 가지고 있어야 한다.

- cursor parse와 stream ownership 검증
- 현재 `highWaterMark` 확보
- `(lastId, highWaterMark]` 범위 replay 준비
- live `> highWaterMark` 구간을 안전하게 이어 붙일 queue/fence 준비
- window miss일 때 reset 정책 결정

또한 `ready` event와 heartbeat에는 보통 `id`를 붙이지 않는다.
cursor는 replay 가능한 business event만 전진시키는 편이 복구 semantics가 단순하다.

## 실전 시나리오

### 시나리오 1: 단일 pod에선 잘 되는데 rolling deploy 뒤 reconnect가 랜덤하게 비어 보인다

원인은 대개 local ring buffer만 있고 shared replay source가 없는 구조다.
같은 pod로 붙을 때만 복구되고, 새 pod로 가면 `Last-Event-ID`는 있어도 읽을 과거가 없다.

### 시나리오 2: Redis Streams를 붙였는데 가끔 replay 이벤트 뒤에 더 오래된 이벤트가 나온다

replay query와 live subscription 사이 fence가 없어서 live event가 먼저 밀려들어온 경우가 흔하다.
cursor source를 durable하게 만든 것만으로 ordering handoff가 자동 해결되지는 않는다.

### 시나리오 3: 대시보드는 중간 상태보다 최신 숫자만 중요하다

이 경우 exact replay buffer보다 snapshot + live가 더 맞을 수 있다.
`Last-Event-ID`를 강하게 유지하려고 복잡한 ordering/log retention을 넣는 것이 과설계일 수 있다.

## 꼬리질문

> Q: heartbeat나 `ready` event에 왜 `id`를 붙이지 않는 편이 안전한가?
> 의도: replay cursor 의미 확인
> 핵심: 다음 reconnect의 `Last-Event-ID`가 replay 가능한 business event를 가리켜야 recovery semantics가 단순하기 때문이다.

> Q: 왜 `replay -> subscribe`는 resume 구현으로 부족한가?
> 의도: replay/live handoff hole 확인
> 핵심: replay를 읽은 뒤 live subscription이 붙기 전 사이에 새 이벤트가 생기면 조용한 손실 구간이 생길 수 있기 때문이다.

> Q: sticky session이 있는데도 왜 multi-instance recovery가 약할 수 있는가?
> 의도: failover 한계 확인
> 핵심: sticky는 같은 노드 재접속 확률만 높일 뿐, pod 종료나 재배치 때는 이전 tail을 새 인스턴스가 읽게 해 주지 못하기 때문이다.

> Q: exact replay 대신 snapshot 복구가 더 나은 경우는 언제인가?
> 의도: 복구 목표와 비용 구분 확인
> 핵심: UI가 모든 중간 상태보다 최신 상태 수렴만 필요할 때는 snapshot + live가 retention과 ordering 비용을 크게 줄일 수 있기 때문이다.

## 한 줄 정리

Spring SSE 복구의 핵심은 `Last-Event-ID` 헤더를 읽는 코드가 아니라, **replay 가능한 `id` 계약, 충분한 replay window, 그리고 reconnect 순간의 ordering fence를 multi-instance에서도 유지하는 것**이다.

# Spring `SseEmitter` Timeout Callback Race Matrix

> 한 줄 요약: `onTimeout`은 Servlet async lifetime timeout, `onError`는 transport/container error signal, `onCompletion`은 어떤 종료 이유든 따라오는 terminal signal이며, `completeWithError(...)`는 app-owned 종료 원인을 선언할 때만 써야 하므로 proxy idle timeout, client reconnect, scheduler cleanup을 callback 이름이 아니라 emitter ownership 기준으로 해석해야 race를 줄일 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
> - [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring Async Timeout vs Disconnect Decision Tree](./spring-async-timeout-disconnect-decision-tree.md)
> - [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)

retrieval-anchor-keywords: SseEmitter onTimeout, SseEmitter onError, SseEmitter onCompletion, SseEmitter completeWithError, SSE callback race, SSE timeout callback matrix, proxy idle timeout SSE, client reconnect race, emitter replacement race, compare and remove registry, emitter generation, heartbeat scheduler cancel, replay reconnect ownership, AsyncRequestTimeoutException, AsyncRequestNotUsableException, disconnected client, ClientAbortException, broken pipe, EventSource reconnect, Last-Event-ID reconnect, old emitter removes new emitter, scheduler cleanup SSE, terminal cause ownership

---

## 핵심 개념

`SseEmitter`에서 자주 틀리는 지점은 callback 이름을 그대로 원인으로 읽는 것이다.

실제로는 네 가지 역할을 분리해야 한다.

| 항목 | 누가 트리거하나 | 실제 의미 | 흔한 오해 | 실무 해석 |
|---|---|---|---|---|
| `onTimeout` | Servlet container | async request lifetime timeout이 났다 | proxy idle timeout이 바로 이 callback으로 온다 | app timeout 신호다. proxy idle close는 보통 다음 `send()` 실패나 `onError`로 드러난다 |
| `onError` | Servlet container | async processing 중 error notification이 왔다 | 모든 `onError`가 app 버그다 | disconnect, late write, transport abort가 많이 섞인다 |
| `onCompletion` | Servlet container | 이 emitter는 이제 더 못 쓴다 | 종료 원인을 알려 주는 root cause callback이다 | timeout, network error, 정상 종료, app-side close 뒤에 모두 올 수 있는 terminal signal이다 |
| `completeWithError(...)` | 애플리케이션 코드 | app이 "이 연결을 error로 끝낸다"고 선언한다 | `send()` `IOException` 뒤 recovery 버튼처럼 다시 눌러야 한다 | app-owned producer failure, replay miss, policy failure 같은 경우에만 쓴다. disconnect 이후엔 중복 호출을 피한다 |

Spring reference docs가 강조하는 포인트도 같다.

- `emitter.send(...)`가 `IOException`으로 실패하면 애플리케이션이 `complete()`나 `completeWithError(...)`로 다시 정리할 필요가 없다.
- Servlet container가 `AsyncListener` error notification을 만들고, Spring MVC가 그 경로에서 최종 completion을 진행한다.
- 따라서 `send` catch 안에서 또 `completeWithError(...)`를 호출하면 원인 복구가 아니라 후행 noise를 늘릴 수 있다.

즉 `SseEmitter` 운영의 핵심은 "어느 callback이 왔는가"보다:

1. 누가 terminal cause를 먼저 결정했는가
2. 지금 registry의 current owner가 어느 emitter인가
3. heartbeat scheduler와 broker subscription을 누가 한번만 정리할 것인가

를 분리하는 것이다.

## 먼저 버릴 오해

### 1. proxy idle timeout은 보통 `onTimeout`이 아니다

ALB, Nginx, CDN이 idle close를 내도 서버는 즉시 모를 수 있다.

흔한 흐름은 이렇다.

```text
조용한 구간 지속
-> proxy가 먼저 연결을 닫음
-> 서버는 아직 old emitter를 살아 있다고 생각
-> 다음 heartbeat 또는 business event send
-> IOException / onError / onCompletion
```

즉 proxy idle timeout은 **app async timeout이 아니라 transport abort**에 더 가깝다.

### 2. client reconnect는 old emitter callback보다 먼저 새 emitter를 만들 수 있다

브라우저 `EventSource`는 끊김을 감지하면 새 요청을 바로 만들 수 있다.
하지만 old connection은 서버 입장에서 아직 cleanup되지 않았을 수 있다.

즉 다음이 가능하다.

```text
old emitter still in registry
-> browser reconnect starts
-> new emitter registered
-> old emitter later gets onError or onCompletion
```

이때 old emitter의 callback이 `registry.remove(userId)`를 무조건 실행하면, 막 등록한 new emitter를 같이 지워 버릴 수 있다.

### 3. `onCompletion`은 root cause가 아니라 "이제 unusable"이라는 사실이다

`onTimeout`, `onError`, app-side `complete()`, app-side `completeWithError(...)` 모두 결국 `onCompletion`으로 이어질 수 있다.
따라서 `onCompletion`은 cleanup hook으로는 좋지만 원인 태깅 source로는 약하다.

### 4. scheduler cleanup은 정상 종료와 에러 종료를 구분해야 한다

app-side scheduler가 하는 일은 보통 세 부류다.

- heartbeat task 실행
- 오래된 emitter lease 정리
- producer/subscription 감시

여기서 stale connection eviction은 대개 **정상 close**에 가깝다.
반면 producer failure나 replay ownership 붕괴는 **app-owned error close**에 가깝다.

둘을 모두 `completeWithError(...)`로 끝내면 observability가 흐려진다.

## Callback Interaction Matrix

| 상황 | 첫 app-visible signal | 흔한 callback 흐름 | `completeWithError(...)` 사용 여부 | 안전한 cleanup 규칙 |
|---|---|---|---|---|
| app async timeout이 먼저 만료된다 | `onTimeout` | `onTimeout` -> async timeout handling -> `onCompletion` | 보통 불필요. timeout reason 기록과 producer stop만 하고 container timeout 경로를 따라가게 둔다 | `onTimeout`에서 원인만 기록하고, 실제 자원 정리는 idempotent `cleanupOnce(...)`로 묶는다 |
| proxy idle timeout 뒤 다음 heartbeat가 실패한다 | 다음 `send()`의 `IOException` 또는 `onError` | `send` 실패 -> container error notification -> `onError` -> `onCompletion` | 아니오. Spring docs 기준으로 `send` `IOException` 뒤엔 app이 `completeWithError(...)`를 다시 부르지 않는다 | `last_successful_send_at`, idle budget을 함께 기록하고 `onCompletion`에서 scheduler/subscription 정리 |
| 사용자가 refresh해서 reconnect하고 new emitter가 먼저 등록된다 | new request가 새 emitter를 반환 | new emitter 등록 -> old emitter가 나중에 `onError` 또는 `onCompletion` | 보통 아니오. handoff 용도면 old emitter는 `complete()`가 더 맞다 | registry remove는 반드시 emitter identity/generation compare-and-remove로 처리 |
| reconnect handoff 시 old emitter를 app이 의도적으로 내린다 | replacement code가 old emitter를 `complete()` | app-side `complete()` -> old `onCompletion` | 보통 아니오. replacement는 에러가 아니라 소유권 이전이다 | old completion callback은 old scheduler만 취소하고, current registry owner가 자신일 때만 제거 |
| scheduler가 stale emitter를 정상 eviction한다 | scheduler thread의 stale 판단 | scheduler `complete()` -> `onCompletion` | 아니오. 정상 idle eviction이면 `complete()`가 기본값이다 | scheduler가 직접 registry/scheduler/subscription을 정리하되, 이후 `onCompletion` 중복 실행을 once-guard로 막는다 |
| scheduler가 producer failure나 policy breach를 감지한다 | scheduler thread가 root cause를 먼저 안다 | scheduler `completeWithError(cause)` -> final completion -> `onCompletion` | 예. app-owned failure를 남길 필요가 있을 때만 | 단, 이미 first byte가 나갔다면 status/body를 바꾸려 하지 말고 cause tagging 용도로만 쓴다 |
| proxy disconnect와 scheduler cleanup이 거의 동시에 온다 | 어느 쪽이 먼저 atomic flag를 가져가느냐에 달림 | scheduler close와 `onError`/`onCompletion`이 서로 뒤섞임 | disconnect `IOException` 뒤엔 아니오. scheduler가 먼저 app failure를 잡은 경우에만 예 | terminal cause는 첫 winner만 기록하고, 나머지 callback은 duplicate breadcrumb로만 남긴다 |
| reconnect request의 `Last-Event-ID`가 invalid하거나 replay window가 지났다 | app handshake/replay open 단계 예외 | emitter 생성 전 reject 또는 emitter 생성 후 `completeWithError(...)` + `onCompletion` | 가능하면 emitter 생성 전 거절한다. 이미 emitter를 만들었다면 app-owned error로 종료 가능 | transport disconnect와 별도 cause(`replay_miss`, `invalid_cursor`)로 태깅한다 |

이 표에서 중요한 문장은 하나다.

> **`onCompletion`은 terminal fact이고, terminal cause는 더 이른 signal에서 따로 저장해야 한다.**

## 추천 종료 모델

실무에서 가장 덜 흔들리는 규칙은 다음 세 단계다.

### 1. terminal cause를 먼저 선점한다

`AtomicBoolean` 또는 compare-and-set 상태로 "누가 종료 ownership을 먼저 가져갔는가"를 기록한다.

- `async_timeout`
- `async_error`
- `proxy_idle_suspected`
- `scheduler_eviction`
- `scheduler_failure`
- `replaced_by_reconnect`

같은 cause bucket을 먼저 찍는다.

### 2. cleanup은 항상 idempotent하게 만든다

정리 대상은 보통 다음 셋이다.

- heartbeat `ScheduledFuture`
- broker subscription / message listener
- emitter registry entry

이 셋을 각각 여러 callback에서 중복 정리해도 안전해야 한다.

### 3. registry remove는 key만으로 하지 않는다

가장 흔한 버그는 이것이다.

```text
userId -> old emitter
browser reconnect
userId -> new emitter
old onCompletion fires
registry.remove(userId)
-> new emitter 삭제
```

따라서 제거는 항상:

- emitter object identity
- generation number
- holder reference

중 하나와 compare해서 current owner일 때만 지워야 한다.

## 코드로 보기

### old callback이 new emitter를 지우지 않게 하는 holder 패턴

```java
record EmitterSlot(
        long generation,
        SseEmitter emitter,
        ScheduledFuture<?> heartbeatTask,
        Subscription subscription,
        AtomicBoolean terminal
) {}

void wireCallbacks(String streamKey, EmitterSlot slot) {
    slot.emitter().onTimeout(() -> cleanupOnce(streamKey, slot, "async_timeout", null));
    slot.emitter().onError(ex -> cleanupOnce(streamKey, slot, "async_error", ex));
    slot.emitter().onCompletion(() -> cleanupOnce(streamKey, slot, "completion", null));
}

void replaceEmitter(String streamKey, EmitterSlot next) {
    wireCallbacks(streamKey, next);

    EmitterSlot previous = registry.put(streamKey, next);
    if (previous != null) {
        cleanupOnce(streamKey, previous, "replaced_by_reconnect", null);
        previous.emitter().complete();
    }
}

void cleanupOnce(String streamKey, EmitterSlot slot, String signal, Throwable error) {
    if (!slot.terminal().compareAndSet(false, true)) {
        return;
    }

    slot.heartbeatTask().cancel(false);
    slot.subscription().cancel();

    registry.compute(streamKey, (key, current) -> current == slot ? null : current);
    logTerminal(streamKey, slot.generation(), signal, error);
}
```

핵심은 `registry.compute(... current == slot ? null : current)`이다.
old callback이 와도 new slot은 남는다.

### `send()` `IOException` 뒤엔 `completeWithError(...)`를 다시 부르지 않는 패턴

```java
void sendHeartbeat(EmitterSlot slot) {
    try {
        slot.emitter().send(SseEmitter.event().comment("keepalive"));
    }
    catch (IOException ex) {
        markDisconnectHint(slot, ex);
        return;
    }
}
```

여기서 `completeWithError(ex)`를 또 호출하지 않는 이유는:

- 이미 peer가 gone일 수 있고
- container가 async error notification을 만들고
- 그 경로에서 `onError` / `onCompletion`이 이어지기 때문이다

즉 heartbeat task는 **원인 힌트만 남기고 빠지는 편**이 안전하다.

### scheduler가 app-owned failure를 먼저 본 경우만 `completeWithError(...)`

```java
void failEmitter(EmitterSlot slot, Throwable cause) {
    if (!slot.terminal().compareAndSet(false, true)) {
        return;
    }

    slot.heartbeatTask().cancel(false);
    slot.subscription().cancel();
    slot.emitter().completeWithError(cause);
}
```

이 패턴이 맞는 경우는:

- upstream broker subscription이 깨져 더 이상 정상 stream을 못 보장할 때
- reconnect replay open이 실패해 stream contract를 유지할 수 없을 때
- app policy 위반을 client-visible error cause로 기록해야 할 때

반대로 단순 stale eviction이나 disconnect 후행 정리에 `completeWithError(...)`를 남발하면 원인 bucket이 오염된다.

## Observability 필드

callback race를 triage하려면 최소한 아래 필드를 같은 completion log에 남겨야 한다.

| 필드 | 왜 필요한가 |
|---|---|
| `stream_key` | reconnect replacement와 fan-out 대상 식별 |
| `emitter_generation` | old callback이 new emitter를 건드렸는지 확인 |
| `terminal_signal` | `onTimeout`, `onError`, `onCompletion`, scheduler close 중 무엇이 먼저였는지 확인 |
| `terminal_cause` | `proxy_idle_suspected`, `scheduler_failure`, `replaced_by_reconnect` 같은 root cause bucket |
| `last_successful_send_at` | proxy idle timeout 의심 근거 |
| `last_event_id_sent` | reconnect replay gap 조사 |
| `replaced_by_generation` | old/new ownership handoff 분석 |

특히 `onCompletion`만 로그에 남기면 timeout, disconnect, replacement가 한 bucket으로 섞인다.
`onCompletion`은 final state고, `terminal_cause`는 별도로 보존해야 한다.

## 빠른 판별 규칙

- `onTimeout`이 왔다고 해서 proxy idle timeout으로 읽지 않는다.
- `send()` `IOException` 뒤엔 `completeWithError(...)`를 다시 호출하지 않는다.
- old emitter callback이 registry key만 보고 remove하면 reconnect race가 난다.
- scheduler cleanup은 정상 eviction이면 `complete()`, app-owned failure면 `completeWithError(...)`를 우선한다.
- 최종 cleanup은 `onCompletion`에 기대더라도, side effect는 반드시 once-guard로 묶는다.

## 꼬리질문

> Q: 왜 proxy idle timeout이 `onTimeout`보다 `onError`/`IOException`로 더 자주 보이나?
> 의도: app timeout과 transport timeout 분리 확인
> 핵심: proxy가 먼저 연결을 닫아도 서버는 다음 write 전까지 모르기 때문이다.

> Q: 왜 `onCompletion` 하나만으로는 원인을 알 수 없는가?
> 의도: terminal fact와 terminal cause 분리 확인
> 핵심: timeout, network error, app-side close, reconnect replacement 모두 결국 completion으로 수렴하기 때문이다.

> Q: reconnect 직후 old emitter callback이 new emitter를 지우는 버그는 왜 생기나?
> 의도: registry ownership race 확인
> 핵심: old callback이 current owner 확인 없이 `registry.remove(key)`를 수행하면 이미 교체된 new emitter를 같이 삭제하기 때문이다.

> Q: scheduler cleanup에서 왜 항상 `completeWithError(...)`를 쓰면 안 되나?
> 의도: 정상 eviction과 app failure 구분 확인
> 핵심: committed SSE에선 status/body 복구가 안 되고, normal stale close까지 error bucket으로 오염되기 때문이다.

## 한 줄 정리

`SseEmitter` callback race를 줄이는 방법은 callback 이름에 비즈니스 의미를 싣는 것이 아니라, terminal cause 선점, compare-and-remove ownership, idempotent cleanup 세 가지를 같은 emitter holder에 묶는 것이다.

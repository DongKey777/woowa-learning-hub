---
schema_version: 3
title: "gRPC Deadlines, Cancellation Propagation"
concept_id: network/grpc-deadlines-cancellation-propagation
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- grpc-deadline-cancellation
- deadline-budget-propagation
- zombie-work-prevention
aliases:
- gRPC deadline
- cancellation propagation
- grpc-timeout
- DEADLINE_EXCEEDED CANCELLED
- deadline budget
- grpc Context interceptor
symptoms:
- DEADLINE_EXCEEDED를 한 서비스의 timeout 설정 문제로만 보고 전체 요청 예산 전파를 놓친다
- client가 이미 취소했는데 downstream DB/RPC 작업이 계속 돌아 zombie work가 남는다
- retry가 남은 deadline budget을 보지 않고 새 호출을 시작해 overload를 키운다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- network/grpc-vs-rest
- network/timeout-budget-propagation-proxy-gateway-service-hop-chain
next_docs:
- network/grpc-deadline-exceeded-first-triage-card
- network/grpc-status-trailers-transport-error-mapping
- network/grpc-keepalive-goaway-max-connection-age
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
linked_paths:
- contents/network/grpc-vs-rest.md
- contents/network/timeout-types-connect-read-write.md
- contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md
- contents/operating-system/monotonic-clock-wall-clock-timeout-deadline.md
- contents/network/http2-multiplexing-hol-blocking.md
- contents/network/timeout-retry-backoff-practical.md
- contents/network/grpc-keepalive-goaway-max-connection-age.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
- contents/network/grpc-status-trailers-transport-error-mapping.md
- contents/spring/spring-mvc-async-deferredresult-callable-dispatch.md
confusable_with:
- network/grpc-deadline-exceeded-first-triage-card
- network/grpc-status-trailers-transport-error-mapping
- network/timeout-budget-propagation-proxy-gateway-service-hop-chain
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
- network/timeout-retry-backoff-practical
forbidden_neighbors: []
expected_queries:
- "gRPC deadline과 timeout은 어떻게 다르고 cancellation propagation은 왜 중요해?"
- "grpc-timeout과 Context를 downstream으로 전파하지 않으면 어떤 zombie work가 남아?"
- "DEADLINE_EXCEEDED와 CANCELLED를 요청 예산과 사용자 취소 관점으로 구분해줘"
- "retry가 deadline budget을 보지 않으면 gRPC 장애가 왜 증폭돼?"
- "client disconnect를 gRPC cancellation으로 backend 작업 중단까지 연결하는 법을 알려줘"
contextual_chunk_prefix: |
  이 문서는 gRPC deadline, grpc-timeout metadata, Context cancellation,
  DEADLINE_EXCEEDED, CANCELLED, deadline budget propagation, retry budget,
  zombie work prevention을 다루는 advanced gRPC playbook이다.
---
# gRPC Deadlines, Cancellation Propagation

> 한 줄 요약: gRPC에서 deadline은 전체 요청 예산이고 cancellation은 그 예산이 끝났다는 신호이므로, downstream까지 전파되지 않으면 느린 작업이 계속 돈다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [gRPC vs REST](./grpc-vs-rest.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [monotonic clock, wall clock, timeout, deadline](../operating-system/monotonic-clock-wall-clock-timeout-deadline.md)
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
> - [gRPC Keepalive, GOAWAY, Max Connection Age](./grpc-keepalive-goaway-max-connection-age.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [gRPC Status, Trailers, Transport Error Mapping](./grpc-status-trailers-transport-error-mapping.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../spring/spring-mvc-async-deferredresult-callable-dispatch.md)

retrieval-anchor-keywords: gRPC deadline, cancellation propagation, grpc-timeout, Context, DEADLINE_EXCEEDED, CANCELLED, deadline budget, client disconnect, interceptor

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

gRPC는 단순한 RPC가 아니라, **호출 예산과 취소 신호를 명시적으로 전달하는 프로토콜**이다.

- `deadline`: 요청 전체를 언제까지 끝내야 하는지
- `timeout`: 개별 대기 구간에서 얼마나 기다릴지
- `cancellation`: 이미 끝난 요청이나 사용자가 끊은 요청을 더 이상 진행하지 말라는 신호

이 문서의 핵심은 deadline을 한 서비스에서만 보는 것이 아니라, **연쇄 호출 전체에 전파해야 한다**는 점이다.

### Retrieval Anchors

- `gRPC deadline`
- `cancellation propagation`
- `grpc-timeout`
- `Context`
- `DEADLINE_EXCEEDED`
- `CANCELLED`
- `deadline budget`
- `interceptor`

## 깊이 들어가기

### 1. timeout과 deadline은 다르다

timeout은 보통 "얼마나 더 기다릴까"이고, deadline은 "언제까지 끝나야 하나"다.

- timeout은 단계별 대기에 좋다
- deadline은 전체 작업 예산 관리에 좋다

gRPC에서는 deadline이 더 자연스럽다.

- 클라이언트는 전체 요청 예산을 하나 잡는다
- 각 hop은 남은 시간만 보고 진행한다
- 시간이 다 되면 같은 예산 안에서 더 시도하지 않는다

### 2. gRPC는 deadline을 어떻게 전달하나

gRPC는 deadline 정보를 메타데이터로 전달한다.

- 내부적으로 `grpc-timeout` 같은 값이 쓰인다
- 서버와 클라이언트는 남은 시간을 기준으로 동작한다
- interceptor나 middleware에서 이 값을 읽고 조정할 수 있다

중요한 점은 이 값이 단순 로그가 아니라 **제어 신호**라는 것이다.

### 3. cancellation propagation이 왜 중요한가

클라이언트가 연결을 끊거나 deadline이 지나면, 서버는 그 사실을 빨리 알아야 한다.

전파가 없으면 이런 일이 벌어진다.

- 클라이언트는 이미 떠났는데 DB 쿼리는 계속 돈다
- upstream은 응답할 곳이 없는데 CPU를 계속 쓴다
- retry가 붙으면 같은 작업이 또 시작된다

즉 cancellation은 "친절한 종료"가 아니라 **낭비를 멈추는 장치**다.

### 4. context를 무시하면 무엇이 망가지나

gRPC 서버 코드가 `Context`나 cancellation token을 무시하면:

- 느린 downstream 호출을 중단하지 못한다
- 작업 큐가 쌓인다
- 이미 취소된 요청에 자원을 쓴다

이 문제는 Java, Go, Kotlin, Python 어디서든 비슷하다.

핵심은 "지금 이 작업이 아직 살아 있는가?"를 주기적으로 확인하는 것이다.

### 5. deadline propagation은 retry와 같이 설계해야 한다

deadline이 있는데 retry가 마음대로 돌아가면 예산을 금방 초과한다.

- 첫 호출이 늦었다
- retry가 남은 시간을 거의 다 써 버린다
- 마지막 hop은 이미 deadline 직전이다

그래서 retry는 남은 budget을 본 뒤에 해야 한다.  
deadline이 지나면 새 시도를 시작하지 않는 편이 맞다.

## 실전 시나리오

### 시나리오 1: 클라이언트는 취소했는데 서버는 계속 일한다

전형적인 cancellation propagation 누락이다.

- front-end는 페이지를 떠났다
- gateway는 요청 종료를 받았다
- downstream service는 아직도 DB 조회와 join을 하고 있다

이때는 서버 코드의 context check와 interceptor를 먼저 본다.

### 시나리오 2: gRPC 호출은 되었는데 DEADLINE_EXCEEDED가 많다

원인이 단순히 "timeout이 짧다"가 아닐 수 있다.

- HTTP/2 HOL blocking
- DB lock
- downstream retry
- proxy timeout mismatch

이런 것들이 남은 deadline을 갉아먹는다.

### 시나리오 3: streaming RPC에서 중간에 끊긴다

server streaming, bidi streaming에서는 cancellation이 더 중요하다.

- 클라이언트가 더 이상 받지 않으면 서버도 멈춰야 한다
- 반대편이 죽었는데 계속 send하면 자원만 낭비한다

### 시나리오 4: 배치성 호출에 deadline이 없다

deadline 없이 RPC를 보내면 장애 시 오래 붙잡히기 쉽다.

- connection pool 고갈
- worker thread 점유
- retry 폭풍

이 패턴은 [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)과 직접 연결된다.

## 코드로 보기

### Java client에서 deadline을 거는 예시

```java
UserServiceGrpc.UserServiceBlockingStub stub =
    UserServiceGrpc.newBlockingStub(channel)
        .withDeadlineAfter(500, TimeUnit.MILLISECONDS);

UserResponse response = stub.getUser(request);
```

### Java server에서 cancellation을 확인하는 감각

```java
Context ctx = Context.current();
if (ctx.isCancelled()) {
    throw Status.CANCELLED.asRuntimeException();
}
```

### interceptor로 deadline을 읽는 예시

```java
public class DeadlineLoggingInterceptor implements ServerInterceptor {
    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
            ServerCall<ReqT, RespT> call,
            Metadata headers,
            ServerCallHandler<ReqT, RespT> next) {

        Deadline deadline = Context.current().getDeadline();
        if (deadline != null) {
            log.info("deadline remaining={}ms", deadline.timeRemaining(TimeUnit.MILLISECONDS));
        }
        return next.startCall(call, headers);
    }
}
```

### 남은 시간을 downstream에 넘기는 감각

```text
remaining_budget = deadline - now
next_call_timeout = min(remaining_budget, per-hop_cap)
```

핵심은 각 hop이 자기 맘대로 새 timeout을 만드는 것이 아니라, **남은 예산을 나눠 쓰는 것**이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| hop별 timeout만 사용 | 구현이 단순하다 | 전체 예산이 흐려진다 | 아주 단순한 내부 호출 |
| deadline propagation | 전체 요청 예산을 지킨다 | 구현과 관찰 포인트가 늘어난다 | 다단계 RPC |
| cancellation 무시 | 코드가 쉬워 보인다 | 자원 낭비와 tail latency가 커진다 | 피해야 함 |

핵심은 "끝까지 기다리기"가 아니라 **끝나야 할 요청을 빨리 정리하는 것**이다.

## 꼬리질문

> Q: deadline과 timeout의 차이는 무엇인가요?
> 핵심: timeout은 기다리는 길이, deadline은 끝나야 하는 시각이다.

> Q: cancellation propagation이 왜 중요한가요?
> 핵심: 클라이언트가 떠난 요청에 자원을 계속 쓰면 latency와 비용이 함께 커진다.

> Q: gRPC에서 deadline이 어디로 전달되나요?
> 핵심: 메타데이터를 통해 전파되고, server/client interceptor에서 읽을 수 있다.

## 한 줄 정리

gRPC deadline은 전체 요청 예산이고 cancellation은 그 예산이 끝났다는 신호라서, downstream까지 전파해야 불필요한 작업과 retry 폭증을 막을 수 있다.

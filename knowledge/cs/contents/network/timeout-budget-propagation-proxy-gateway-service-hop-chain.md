# Timeout Budget Propagation Across Proxy, Gateway, Service Hops

> 한 줄 요약: 요청 timeout은 홉마다 새로 시작하는 독립 타이머가 아니라 end-to-end 예산이므로, proxy와 gateway가 남은 시간을 깎아 전달하지 않으면 hop이 늘수록 504와 낭비가 함께 커진다.
>
> 문서 역할: 이 문서는 network 운영 cluster 안에서 **end-to-end timeout budget 전달 규칙**을 설명하는 deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [gRPC Deadlines, Cancellation Propagation](./grpc-deadlines-cancellation-propagation.md)
> - [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
> - [Proxy Retry Budget Discipline](./proxy-retry-budget-discipline.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [Spring Service-Layer Transaction Boundary Patterns](../spring/spring-service-layer-transaction-boundary-patterns.md)
> - [Transaction Boundary, Isolation, and Locking Decision Framework](../database/transaction-boundary-isolation-locking-decision-framework.md)
> - [JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)
> - [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../spring/spring-mvc-async-deferredresult-callable-dispatch.md)

retrieval-anchor-keywords: timeout budget propagation, deadline propagation, proxy chain, gateway timeout, remaining budget, end-to-end latency budget, per-hop timeout, queueing delay, grpc-timeout, fail-fast

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

## 이 문서 다음에 보면 좋은 문서

- 기본 timeout / retry 판단은 [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)으로 되돌아가면 좋다.
- 실제 병목 시간 분해는 [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)와 연결된다.
- gateway / proxy 관점 세부 운영 포인트는 [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md), [Proxy Retry Budget Discipline](./proxy-retry-budget-discipline.md)로 이어진다.

## 핵심 개념

`timeout budget`은 "이 요청이 전체적으로 언제까지 끝나야 하는가"를 나타내는 **end-to-end 예산**이다.

중요한 점은 이 값이 hop마다 새로 리셋되는 local timeout이 아니라는 점이다.

- client는 사용자 체감 기준으로 전체 예산을 잡는다
- gateway는 인증, rate limit, queueing에 쓴 시간을 먼저 차감해야 한다
- service는 downstream 호출 전에 자기 처리 여유와 응답 write 시간을 남겨야 한다
- proxy는 transport timeout을 두더라도 caller budget보다 더 긴 기다림을 만들면 안 된다

결국 각 홉이 해야 할 일은 같다.

- inbound deadline 또는 timeout을 읽는다
- 현재까지 소모한 시간을 뺀다
- 자기 내부에 남겨 둘 reserve를 확보한다
- downstream에는 **남은 budget만** 전달한다
- 의미 있는 시간이 남지 않았으면 새 호출을 시작하지 않고 fail-fast 한다

### Retrieval Anchors

- `timeout budget propagation`
- `deadline propagation`
- `proxy chain`
- `gateway timeout`
- `remaining budget`
- `end-to-end latency budget`
- `per-hop timeout`
- `queueing delay`
- `grpc-timeout`
- `fail-fast`

## 깊이 들어가기

### 1. hop별 2초는 전체 2초가 아니다

가장 흔한 실수는 각 홉이 "내 timeout은 2초"라고 독립적으로 생각하는 것이다.

예를 들어:

- client budget: 1500ms
- gateway auth/rate limit: 180ms 소모
- service A queueing: 220ms 소모
- service B query: 900ms 소모

이 체인에서 gateway가 service A에 다시 1500ms를 주고, service A가 service B에 또 1500ms를 주면 실제 끝나는 시점은 caller의 기대보다 훨씬 뒤가 된다.

이때 나타나는 현상:

- client는 이미 포기했는데 backend는 계속 일한다
- gateway는 504를 기록했는데 service B는 나중에 200을 남긴다
- retry가 붙으면 이미 끝난 요청에 새 시도가 추가된다

나쁜 설계의 상한은 대체로 `hop별 timeout의 합 + queueing + retry`에 가까워지고,  
좋은 설계의 상한은 **항상 caller deadline 안**에 머문다.

### 2. propagation의 본질은 "남은 시간"을 보존하는 것이다

wire에는 여러 방식이 가능하다.

- absolute deadline timestamp
- relative timeout duration
- protocol-specific metadata 예: `grpc-timeout`

하지만 서비스 내부 모델은 하나로 정리하는 편이 좋다.

- 들어온 값을 받아 **단일 inbound deadline**으로 정규화한다
- 내부 계산은 wall clock보다 `monotonic clock` 기준으로 한다
- outbound 직전에 다시 header나 metadata 형태로 직렬화한다

이렇게 해야 clock skew나 직렬화 포맷 차이 때문에 budget이 갑자기 늘어나는 실수를 줄일 수 있다.

특히 HTTP에서 gRPC로, 또는 gRPC에서 HTTP로 protocol bridge를 하는 gateway가 위험하다.

- HTTP 요청의 700ms 남은 budget을 받았다
- gateway가 기본값 2초를 새로 만들어 gRPC에 넘긴다
- downstream은 시간이 더 많다고 오해한다

이건 propagation이 아니라 **budget expansion**이다.

### 3. 각 홉은 자기 몫을 먼저 떼고 내려보내야 한다

남은 시간이 800ms라고 해서 downstream에 800ms를 전부 넘기면 안 된다.

현재 홉도 다음 작업이 남아 있기 때문이다.

- 응답 serialization
- response write
- tracing/log flush
- fan-in merge
- error translation

그래서 보통은 이런 식으로 생각한다.

```text
remaining_budget = inbound_deadline - monotonic_now
local_reserve = response_write + marshal + safety_margin
forwardable_budget = remaining_budget - local_reserve
outbound_budget = min(forwardable_budget, per-hop-cap)
```

여기서 중요한 건 `per-hop-cap`이 inbound budget을 늘리는 장치가 아니라는 점이다.

- inbound가 300ms 남았는데 cap이 500ms여도 outbound는 300ms를 넘을 수 없다
- inbound가 2s 남아도 service policy상 400ms 이상 기다리지 않겠다면 400ms까지만 쓴다

즉 local cap은 **상한을 줄이는 장치**이지, 예산을 새로 찍어내는 장치가 아니다.

### 4. queueing, pool wait, retry도 budget을 먹는다

실무에서는 실제 비즈니스 로직보다 대기 시간이 더 큰 경우가 많다.

- gateway worker queue
- DB connection pool wait
- thread pool saturation
- sidecar proxy queue
- TLS handshake 재수립

이 지연은 "아직 downstream을 안 불렀으니 budget을 안 썼다"가 아니다.  
caller 입장에서는 이미 시간이 지나고 있다.

retry도 마찬가지다.

- 첫 시도에서 420ms를 썼다
- 남은 budget이 80ms다
- connect만 해도 40ms, 최소 처리에 70ms가 필요하다

이 상황에서 retry는 복구가 아니라 지연만 늘리는 행동이다.  
그래서 retry는 횟수보다 먼저 **남은 budget floor**를 봐야 한다.

### 5. fan-out 체인에서는 공유 예산이라는 감각이 더 중요하다

service A가 service B와 C를 동시에 부른다고 해서 각자에게 full budget을 주면 안 된다.

service A는 아직 해야 할 일이 있다.

- 두 응답을 기다린다
- merge 한다
- 부분 실패 정책을 적용한다
- upstream으로 응답을 쓴다

예를 들어 inbound remaining이 600ms라면:

- reserve 100ms는 A가 직접 쓴다
- B에는 최대 220ms
- C에는 최대 220ms
- 남는 60ms는 jitter와 scheduling 여유로 둔다

fan-out에서 각 downstream budget은 wall-clock으로 병렬 실행될 수 있지만,  
그 위를 덮는 **공유 deadline은 하나**다.

그래서 "병렬이니까 budget도 각자 full로 줘도 된다"는 생각이 tail latency를 가장 쉽게 망친다.

### 6. 운영 관찰 포인트가 없으면 propagation 누락을 찾기 어렵다

다음 값들을 로그와 tracing span에 남겨 두면 좋다.

- inbound remaining budget
- queue에서 소모한 시간
- outbound call마다 전달한 budget
- timeout 발생 지점: queue, connect, TLS, upstream, caller-cancelled
- deadline 도달 전에 dispatch조차 못 한 요청 수

관찰 포인트가 없으면 모든 timeout이 그냥 "느렸다"로 뭉개진다.  
그러면 실제로는 gateway queue가 budget을 태웠는데 DB가 느리다고 오판하기 쉽다.

## 실전 시나리오

### 시나리오 1: gateway는 504인데 downstream은 200을 찍는다

전형적인 budget propagation 또는 cancellation 누락이다.

- client deadline은 끝났다
- gateway는 응답할 수 없어 504를 반환했다
- service는 inbound cancellation을 모르거나 무시했다
- DB 쿼리와 후처리가 끝난 뒤 200 로그를 남겼다

이 패턴은 "서비스는 성공했는데 왜 gateway가 timeout이냐"처럼 보이지만,  
실제로는 **caller와 backend가 다른 시계를 살고 있는 상태**다.

### 시나리오 2: service mesh proxy가 timeout을 덮어쓴다

앱은 inbound budget이 350ms 남았다고 계산했는데, sidecar나 proxy가 upstream read timeout을 2초로 잡아 두면 문제가 생긴다.

- app은 이미 끝난 요청이라고 본다
- proxy는 transport 차원에서 더 기다린다
- socket, buffer, worker가 불필요하게 오래 점유된다

반대로 proxy timeout이 app보다 지나치게 짧으면,  
실제 budget은 남아 있는데 중간 홉이 먼저 끊어 진짜 병목을 가려 버릴 수 있다.

### 시나리오 3: HTTP에서 gRPC로 넘어가며 deadline이 사라진다

edge는 `X-Request-Timeout-Ms: 900` 같은 헤더로 시작했는데, gateway가 이를 무시하고 내부 gRPC stub에 `withDeadlineAfter(1, SECONDS)`를 고정했다.

그러면:

- 외부 예산과 내부 예산이 갈라진다
- 일부 요청은 내부적으로 너무 오래 산다
- 일부 요청은 반대로 불필요하게 빨리 실패한다

bridge 계층의 핵심은 새 정책을 만드는 게 아니라 **기존 budget을 번역하는 것**이다.

### 시나리오 4: queue에서 700ms를 태운 뒤 DB 호출을 시작한다

남은 budget이 60ms인데도 service가 "일단 한 번 가 보자"로 DB를 호출하면 거의 항상 timeout이다.

이 상황에서는:

- DB는 어차피 중간에 끊기거나 늦게 끝난다
- connection pool만 더 오래 잡는다
- 같은 시점의 다른 건강한 요청도 같이 밀린다

이런 경우는 늦게 시작하는 것보다 **아예 시작하지 않는 것**이 전체 시스템에 더 안전하다.

## 코드로 보기

### Gateway에서 inbound budget을 정규화하는 감각

```java
Duration defaultBudget = Duration.ofMillis(800);
Duration serviceCap = Duration.ofMillis(500);
Duration responseReserve = Duration.ofMillis(80);

Duration inboundBudget = readTimeoutHeader(requestHeaders).orElse(defaultBudget);
long startedAt = requestContext.startedAtNanos();
Duration elapsed = Duration.ofNanos(System.nanoTime() - startedAt);
Duration remaining = inboundBudget.minus(elapsed);

if (remaining.isZero() || remaining.isNegative()) {
    throw new GatewayTimeoutException("budget exhausted before dispatch");
}

Duration forwardable = remaining.minus(responseReserve);
if (forwardable.compareTo(Duration.ofMillis(100)) < 0) {
    throw new GatewayTimeoutException("not enough budget for downstream call");
}

Duration outboundBudget = forwardable.compareTo(serviceCap) < 0 ? forwardable : serviceCap;
requestHeaders.put("X-Request-Timeout-Ms", Long.toString(outboundBudget.toMillis()));
```

핵심은 "기본 timeout을 다시 넣는 것"이 아니라,  
**이미 흘러간 시간을 뺀 뒤 남은 값만 전달하는 것**이다.

### gRPC와 HTTP를 섞는 체인에서의 감각

```text
HTTP inbound header -> normalize to internal deadline
internal deadline -> compute remaining with monotonic clock
remaining budget -> write grpc-timeout or outbound timeout header
```

프로토콜이 달라도 규칙은 같다.

- inbound보다 긴 outbound는 만들지 않는다
- retry 전에 남은 budget floor를 본다
- fan-out 전에는 merge/write reserve를 남긴다

### 시작하지 말아야 할 호출을 거르는 기준

```text
if remaining_budget <= connect_cost + minimum_useful_work + response_reserve:
    fail_fast
else:
    dispatch
```

이 기준이 없으면 시스템은 "성공 가능성이 거의 없는 호출"을 계속 만들어 낸다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| hop마다 새 timeout 부여 | 구현이 단순해 보인다 | end-to-end SLA가 쉽게 깨진다 | 피해야 할 패턴 |
| inbound budget 전파 | caller 기대와 내부 실행 시간을 맞춘다 | header/context 전파가 필요하다 | proxy/gateway/service 체인 |
| 공격적인 fail-fast | zombie work와 tail latency를 줄인다 | 순간적인 느림도 빨리 실패로 드러난다 | 과부하 억제가 중요할 때 |
| 넉넉한 local reserve | 응답 write와 merge 실패를 줄인다 | 실제 downstream budget이 줄어든다 | fan-out, 변환, streaming이 있을 때 |

핵심은 timeout을 크게 잡는 것이 아니라, **누가 얼마를 이미 썼는지 보존하는 것**이다.

## 꼬리질문

> Q: per-hop timeout과 end-to-end timeout을 왜 구분해야 하나요?
> 핵심: hop마다 timeout을 리셋하면 caller는 1번만 기다리는데 내부는 여러 번 기다리게 된다.

> Q: absolute deadline과 remaining duration 중 무엇을 전파해야 하나요?
> 핵심: wire format은 둘 다 가능하지만, 각 홉은 결국 단일 deadline으로 정규화하고 monotonic 기준의 남은 budget으로 계산해야 한다.

> Q: retry를 언제 막아야 하나요?
> 핵심: 남은 budget이 connect 비용, 최소 처리 시간, 응답 reserve를 덮지 못하면 새 시도는 금지하는 편이 낫다.

> Q: gateway의 가장 중요한 역할은 무엇인가요?
> 핵심: 인증, queueing, protocol bridge에서 이미 쓴 시간을 빼고 남은 budget만 정확히 전달하는 것이다.

## 한 줄 정리

timeout budget은 hop마다 새로 주는 숫자가 아니라 caller가 준 end-to-end 예산이므로, proxy/gateway/service는 남은 시간만 전파하고 floor 아래에서는 fail-fast해야 504와 zombie work를 함께 줄일 수 있다.

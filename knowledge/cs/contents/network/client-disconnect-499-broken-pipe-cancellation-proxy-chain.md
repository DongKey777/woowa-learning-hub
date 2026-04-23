# Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains

> 한 줄 요약: 클라이언트가 먼저 떠난 요청은 access log의 `499`로만 끝나는 문제가 아니다. 취소 신호가 proxy와 backend를 제대로 통과하지 않으면 zombie work가 남고, 너무 늦게 알면 `broken pipe`, `EPIPE`, late write failure로 드러난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [FIN, RST, Half-Close, EOF](./fin-rst-half-close-eof-semantics.md)
> - [gRPC Deadlines, Cancellation Propagation](./grpc-deadlines-cancellation-propagation.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [Proxy-to-Container Upload Cleanup Matrix](./proxy-to-container-upload-cleanup-matrix.md)
> - [WebSocket Proxy Buffering, Streaming Latency](./websocket-proxy-buffering-streaming-latency.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
> - [SSE Failure Attribution Across HTTP/1.1 and HTTP/2](./sse-failure-attribution-http1-http2.md)
> - [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../spring/spring-mvc-async-deferredresult-callable-dispatch.md)

retrieval-anchor-keywords: client disconnect, client closed request, 499, broken pipe, EPIPE, request aborted, cancellation propagation, downstream disconnect, nginx 499, zombie work, late write failure, streaming cancel after first byte, partial flush failure, RST_STREAM, EOF, chunked flush failure, sse abort attribution

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

요청이 끝나는 방식은 "서버가 응답을 보냈다" 하나만 있는 것이 아니다.

- client가 먼저 브라우저 탭을 닫는다
- 모바일 네트워크가 바뀌며 연결이 끊긴다
- proxy가 upstream보다 먼저 timeout을 선언한다
- caller deadline이 끝나 취소가 내려간다

이때 중요한 질문은 두 가지다.

- 누가 먼저 연결을 포기했는가
- 그 사실이 backend 작업 취소로 이어졌는가

### Retrieval Anchors

- `client disconnect`
- `client closed request`
- `499`
- `broken pipe`
- `EPIPE`
- `request aborted`
- `cancellation propagation`
- `nginx 499`
- `zombie work`

## 깊이 들어가기

### 1. `499`는 HTTP status라기보다 proxy 관찰 결과에 가깝다

예를 들어 Nginx 계열에서 `499`는 대개:

- origin이 499를 보냈다는 뜻이 아니다
- proxy가 응답을 다 쓰기 전에 client가 먼저 떠났다는 관찰에 가깝다

프록시나 ingress 제품에 따라 같은 현상이 `client closed request` 문구로 기록되기도 한다.

그래서 backend 로그가 `200`인데 edge에서는 `499`일 수 있다.

- backend는 끝까지 계산하고 응답을 만들었다
- 하지만 caller는 이미 timeout이나 navigation으로 떠났다
- proxy는 downstream write를 끝내지 못했다

즉 `499` 하나만 보고 앱 성공/실패를 판단하면 안 된다.

### 2. 취소 신호가 안 내려가면 zombie work가 남는다

가장 비싼 실패는 "이미 응답할 상대가 없는데 계속 일하는 것"이다.

- DB query가 계속 돈다
- fan-out downstream 호출이 이어진다
- 대용량 직렬화와 compression이 끝까지 수행된다
- cache write나 audit log까지 진행된다

이건 단순 낭비가 아니라, 같은 자원을 다른 요청이 못 쓰게 만드는 overload 증폭기다.

### 3. 반대로 너무 늦게 감지하면 `broken pipe`로만 보인다

backend 입장에서 흔한 증상:

- response body를 쓰는 중 `EPIPE`
- `connection reset by peer`
- flush 단계에서 late failure

이건 "서버가 잘못 썼다"보다 **상대가 먼저 떠난 사실을 늦게 알았다**는 의미일 수 있다.

특히 큰 response, streaming, chunked flush에서 잘 보인다.

### 4. proxy 체인에서는 disconnect 주체가 서로 다를 수 있다

예를 들어:

- browser는 2초에 포기했다
- edge proxy는 499를 남겼다
- gateway는 upstream cancel을 늦게 전파했다
- backend는 4초 뒤 200을 찍었다

이 경우 모두 자기 입장에선 "맞는 로그"를 남긴다.  
문제는 서로 다른 시계를 산다는 점이다.

### 5. request body upload 중 disconnect는 응답 중 disconnect와 다르다

upload 중 client가 떠나면:

- app은 unread request body를 보게 된다
- proxy request buffering 여부에 따라 감지 시점이 달라진다
- origin이 아직 auth나 validation 중일 수도 있다

response 중 client가 떠나면:

- backend는 이미 비즈니스 로직 대부분을 끝냈을 수 있다
- flush나 마지막 write에서만 실패가 드러난다

즉 "언제 끊겼는가"가 대응을 바꾼다.

### 6. streaming 경로는 취소 전파가 더 중요하다

SSE, WebSocket, gRPC streaming은 연결이 오래 간다.

- downstream consumer가 사라지면 producer도 멈춰야 한다
- 그렇지 않으면 큐와 버퍼가 계속 쌓인다
- heartbeat가 살아 있어도 payload consumer는 이미 죽었을 수 있다

그래서 long-lived stream은 단순 socket close보다 **앱 레벨 cancellation 체크**가 더 중요하다.

## 실전 시나리오

### 시나리오 1: edge는 `499`가 많고 backend는 `200`이 많다

전형적인 cancellation propagation 누락 또는 늦은 전파 패턴이다.

### 시나리오 2: 대용량 JSON 응답에서만 `broken pipe`가 늘어난다

client는 이미 timeout으로 떠났고, backend는 serialization을 끝낸 뒤 write에서야 실패를 본 것일 수 있다.

### 시나리오 3: 모바일 앱이 화면 전환 후에도 서버 작업이 계속 돈다

caller lifecycle과 backend cancellation이 연결되지 않았을 가능성이 크다.

### 시나리오 4: upload API에서 어떤 요청은 499, 어떤 요청은 413, 어떤 요청은 200처럼 보인다

disconnect 시점, request buffering 유무, unread body drain 정책이 서로 다르게 작동했을 수 있다.

## 코드로 보기

### 관찰 포인트

```text
- edge 499 시각과 backend completion 시각
- client disconnect 후에도 계속 돈 작업 수
- write/flush 단계 EPIPE, ECONNRESET 비율
- cancel signal received -> work stopped latency
```

### 현장 질문

```text
- 누가 먼저 요청을 포기했는가
- 그 사실이 어느 홉까지 전파됐는가
- backend는 cancel 이후 얼마나 더 일했는가
- 실패가 request body 중이었는가, response write 중이었는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 빠른 cancellation propagation | zombie work를 줄인다 | 구현 누락 시 오탐/조기 중단 위험이 있다 | fan-out, 비싼 요청 |
| 취소 무시 후 끝까지 수행 | 구현이 단순하다 | 자원 낭비와 overload가 커진다 | 거의 권장되지 않음 |
| streaming write 에러 세분화 | 원인 분석이 쉬워진다 | 로깅/메트릭 설계가 더 복잡하다 | SSE, gRPC, 대용량 응답 |
| proxy buffering 사용 | downstream disconnect를 늦게 드러낼 수 있다 | backend 보호는 되지만 실제 caller cancel과 분리될 수 있다 | 일반 HTTP |

핵심은 `499`나 `broken pipe`를 개별 오류 코드로만 보지 않고 **취소 신호가 end-to-end로 어떻게 흘렀는지**로 해석하는 것이다.

## 꼬리질문

> Q: `499`는 서버가 반환한 상태코드인가요?
> 핵심: 보통 proxy가 관찰한 "client가 먼저 끊었다"는 결과이지, origin app이 직접 반환한 status와는 다를 수 있다.

> Q: backend가 200인데 edge가 499일 수 있나요?
> 핵심: 가능하다. backend는 완료했지만 caller는 이미 떠났을 수 있다.

> Q: `broken pipe`는 항상 서버 버그인가요?
> 핵심: 아니다. 상대가 먼저 연결을 닫은 사실을 늦게 감지한 결과일 수 있다.

## 한 줄 정리

client abort 문제는 `499`나 `broken pipe` 자체보다, disconnect 사실이 proxy chain을 따라 얼마나 빨리 취소로 전파됐는지를 봐야 정확히 진단된다.

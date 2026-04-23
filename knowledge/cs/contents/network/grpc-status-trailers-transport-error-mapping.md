# gRPC Status, Trailers, Transport Error Mapping

> 한 줄 요약: gRPC 실패는 항상 애플리케이션이 status code를 반환한 결과가 아니다. trailers로 온 gRPC status, proxy가 끊으며 생긴 transport error, HTTP/2 reset이 서로 다른 층인데, 클라이언트 라이브러리는 종종 이를 몇 개 코드로 뭉개서 보여 준다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [gRPC vs REST](./grpc-vs-rest.md)
> - [gRPC Deadlines, Cancellation Propagation](./grpc-deadlines-cancellation-propagation.md)
> - [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)
> - [gRPC Keepalive, GOAWAY, Max Connection Age](./grpc-keepalive-goaway-max-connection-age.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)

retrieval-anchor-keywords: grpc status, trailers, transport error, grpc-status, trailers-only, UNAVAILABLE, DEADLINE_EXCEEDED, CANCELLED, status mapping, proxy reset, grpc-message

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

gRPC 호출 종료는 크게 세 층에서 해석할 수 있다.

- 애플리케이션 층: server가 `grpc-status`와 `grpc-message`를 trailer로 보냄
- HTTP/2 층: `RST_STREAM`, `GOAWAY`, stream close
- transport 층: TCP/TLS connection close, proxy reset, idle timeout

클라이언트는 이 셋을 합쳐 `UNAVAILABLE`, `CANCELLED`, `DEADLINE_EXCEEDED` 같은 상태로 보여 줄 수 있다.

### Retrieval Anchors

- `grpc status`
- `trailers`
- `transport error`
- `grpc-status`
- `trailers-only`
- `UNAVAILABLE`
- `DEADLINE_EXCEEDED`
- `CANCELLED`

## 깊이 들어가기

### 1. 정상적인 gRPC 에러는 trailer로 온다

gRPC는 HTTP status만으로 결과를 표현하지 않는다.

- 응답 body가 있든 없든
- 마지막에 trailer로 `grpc-status`를 보낸다
- 필요하면 `grpc-message`와 metadata도 함께 보낸다

즉 "에러 응답"도 transport 성공 위에서 **애플리케이션 의미를 담아 전달**할 수 있다.

### 2. trailers-only 응답은 body 없이 바로 결과를 끝낸다

서버가 실제 payload 없이 바로 결과를 줄 수 있다.

- auth 실패
- validation 실패
- 빠른 business rejection

이 경우 body가 거의 없어도 gRPC 관점에서는 정상적인 status 전달일 수 있다.

### 3. transport error는 status 반환과 다른 사건이다

다음은 앱이 `grpc-status`를 정상적으로 못 보냈을 가능성이 크다.

- proxy가 중간에서 stream을 reset
- client disconnect
- keepalive timeout
- TCP/TLS close before trailers

이때 라이브러리는 적당한 gRPC status로 번역해 보여 줄 수 있다.

- `UNAVAILABLE`
- `CANCELLED`
- 내부 transport exception

문제는 이 값만 보면 **앱이 그렇게 반환한 것처럼 오해**하기 쉽다는 점이다.

### 4. 같은 `UNAVAILABLE`이어도 의미가 다를 수 있다

예를 들어 `UNAVAILABLE`은:

- 서버 overload로 앱이 직접 반환
- `GOAWAY` 이후 reconnect race
- proxy local reply
- upstream transport reset

처럼 전혀 다른 원인을 가질 수 있다.

그래서 gRPC status 코드만으로 retry 여부를 정하면 위험하다.  
status source가 애플리케이션인지 transport 번역인지 같이 봐야 한다.

### 5. `DEADLINE_EXCEEDED`와 `CANCELLED`도 주체를 분리해야 한다

- caller deadline이 먼저 끝나 client가 취소
- 서버가 자체 timeout policy로 작업 중단
- proxy가 shorter timeout을 적용

겉으로는 모두 deadline/cancel 비슷하게 보이지만, 실제 책임 계층은 다를 수 있다.

### 6. observability는 trailer 수신 여부를 남겨야 한다

다음 정보가 있으면 해석이 빨라진다.

- trailers를 받았는가
- `grpc-status`를 실제로 받았는가
- reset/close가 trailer 이전이었는가
- source error가 app, proxy, transport 중 어디였는가

이게 없으면 모든 실패가 그냥 `UNAVAILABLE`로 뭉개진다.

## 실전 시나리오

### 시나리오 1: 서버는 명확한 status를 남겼는데 client는 `UNAVAILABLE`만 본다

중간 proxy나 transport close가 trailer 전달 전에 끼어들었을 수 있다.

### 시나리오 2: 같은 API인데 어떤 실패는 retry가 되고 어떤 실패는 중복 처리 문제가 난다

하나는 app-level reject, 다른 하나는 transport 번역 error일 수 있다.

### 시나리오 3: observability 대시보드는 gRPC 에러율이 높은데 서버 로그는 조용하다

서버 앱이 status를 반환하기 전에 proxy reset이나 caller cancellation이 먼저 일어났을 가능성이 있다.

### 시나리오 4: `DEADLINE_EXCEEDED`가 늘었는데 서버는 빨랐다고 주장한다

queue wait, stream open 대기, proxy timeout, client-side deadline이 먼저 타 버렸을 수 있다.

## 코드로 보기

### 관찰 포인트

```text
- grpc-status를 trailer에서 실제로 받았는가
- trailers-only 응답 비율은 어떤가
- transport reset / GOAWAY / client cancel과 status code 상관관계
- retry 전에 status source를 구분하는가
```

### 현장 질문

```text
- 이 status는 server app이 반환한 것인가
- 아니면 client library가 transport error를 번역한 것인가
- trailers를 받았는가
- proxy가 local reply를 만든 것은 아닌가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| status code만 수집 | 단순하다 | root cause가 뭉개진다 | 기초 대시보드 |
| trailer 수신 여부까지 수집 | app vs transport 구분이 쉬워진다 | 계측이 더 복잡하다 | 운영 장애 분석 |
| aggressive retry on UNAVAILABLE | transient failure를 흡수한다 | transport 번역 error에 과도 반응해 중복/폭증을 만들 수 있다 | 멱등 unary RPC |
| source-aware retry | 정확성이 높다 | 구현과 계측이 더 어렵다 | 중요한 내부 RPC |

핵심은 gRPC 실패를 status code 하나로만 보지 않고 **trailers, HTTP/2 signal, transport close의 조합**으로 보는 것이다.

## 꼬리질문

> Q: gRPC 에러는 항상 서버가 status code를 반환한 결과인가요?
> 핵심: 아니다. proxy reset이나 transport close를 client library가 gRPC status로 번역해 보여 줄 수 있다.

> Q: `UNAVAILABLE`이면 항상 retry해도 되나요?
> 핵심: 아니다. app-level reject인지 transport 번역인지, 멱등한 요청인지 같이 봐야 한다.

> Q: trailers-only 응답은 무엇인가요?
> 핵심: payload body 없이 trailer로 바로 gRPC 결과를 끝내는 정상 응답 형태다.

## 한 줄 정리

gRPC 상태 해석이 어려운 이유는 실패가 trailer, HTTP/2, transport 세 층에서 일어나는데 클라이언트는 이를 몇 개 status code로 압축해서 보여 주기 때문이다.

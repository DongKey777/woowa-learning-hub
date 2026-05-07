---
schema_version: 3
title: "Expect 100-continue, Proxy Request Buffering"
concept_id: network/expect-100-continue-proxy-request-buffering
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- expect-100-continue
- proxy-request-buffering
- large-upload-early-reject
aliases:
- Expect 100-continue
- proxy request buffering
- 417 Expectation Failed
- large upload early reject
- auth before body
- continue timeout
symptoms:
- 큰 업로드에서 Expect 100-continue가 있어도 proxy buffering 때문에 early reject 이득이 사라진다
- 417 Expectation Failed를 app validation 실패와 protocol expectation 처리 실패로 구분하지 못한다
- 인증/권한 거절을 body upload 전에 끝내려는데 gateway와 origin의 buffering 정책이 충돌한다
- unread request body drain 없이 early reject를 해서 keep-alive reuse가 깨진다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- network/api-gateway-reverse-proxy-operational-points
- network/gateway-buffering-vs-spring-early-reject
next_docs:
- network/http-request-body-drain-early-reject-keepalive-reuse
- network/proxy-to-container-upload-cleanup-matrix
- network/http2-upload-early-reject-rst-stream-flow-control-cleanup
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
linked_paths:
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/api-gateway-auth-rate-limit-chain.md
- contents/network/gateway-buffering-vs-spring-early-reject.md
- contents/network/proxy-to-container-upload-cleanup-matrix.md
- contents/network/multipart-parsing-vs-auth-reject-boundary.md
- contents/network/http2-upload-early-reject-rst-stream-flow-control-cleanup.md
- contents/network/timeout-types-connect-read-write.md
- contents/network/websocket-proxy-buffering-streaming-latency.md
- contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md
- contents/network/http-request-body-drain-early-reject-keepalive-reuse.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
- contents/spring/spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md
confusable_with:
- network/gateway-buffering-vs-spring-early-reject
- network/http-request-body-drain-early-reject-keepalive-reuse
- network/proxy-to-container-upload-cleanup-matrix
- network/http2-upload-early-reject-rst-stream-flow-control-cleanup
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
forbidden_neighbors: []
expected_queries:
- "Expect 100-continue는 큰 request body를 보내기 전에 어떻게 early reject를 가능하게 해?"
- "Proxy request buffering이 켜져 있으면 100 Continue의 이점이 왜 사라질 수 있어?"
- "417 Expectation Failed와 auth before body reject를 어떻게 구분해?"
- "대용량 업로드에서 gateway가 401 413 429를 body 전에 거절하려면 무엇을 맞춰야 해?"
- "early reject 뒤 unread request body를 drain하지 않으면 keep-alive 재사용이 왜 깨져?"
contextual_chunk_prefix: |
  이 문서는 Expect: 100-continue, proxy_request_buffering, large upload,
  early auth/quota/size reject, 417, continue timeout, unread body drain,
  keep-alive reuse를 다루는 advanced upload/proxy playbook이다.
---
# Expect 100-continue, Proxy Request Buffering

> 한 줄 요약: `Expect: 100-continue`는 큰 요청 본문을 보내기 전에 앞단이 먼저 승인할 기회를 주지만, proxy request buffering과 gateway 체인이 이를 삼키면 early reject 대신 업로드 지연과 417 혼선만 남는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [API Gateway Auth Rate Limit Chain](./api-gateway-auth-rate-limit-chain.md)
> - [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
> - [Proxy-to-Container Upload Cleanup Matrix](./proxy-to-container-upload-cleanup-matrix.md)
> - [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md)
> - [HTTP/2 Upload Early Reject, RST_STREAM, Flow-Control Cleanup](./http2-upload-early-reject-rst-stream-flow-control-cleanup.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [WebSocket Proxy Buffering, Streaming Latency](./websocket-proxy-buffering-streaming-latency.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](../spring/spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)

retrieval-anchor-keywords: Expect 100-continue, request buffering, proxy_request_buffering, 417 Expectation Failed, large upload, early reject, request body buffering, auth before body, upload latency, continue timeout, spring security upload reject, gateway buffering vs spring early reject, http2 upload reject, RST_STREAM NO_ERROR upload

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

큰 업로드 요청은 헤더만 먼저 보내고, 서버가 괜찮다고 하면 body를 보내는 편이 낭비를 줄일 수 있다.

이때 쓰는 것이 `Expect: 100-continue`다.

- client는 headers를 먼저 보낸다
- proxy 또는 origin은 body를 받을 가치가 있는지 먼저 판단한다
- 괜찮으면 `100 Continue`를 보내고 body 전송을 유도한다
- 거절할 거면 `401`, `403`, `413`, `429` 같은 최종 응답을 먼저 보낼 수 있다

문제는 중간 proxy가 request buffering을 하거나 header를 재작성하면 이 handshake의 의미가 흐려진다는 점이다.

### Retrieval Anchors

- `Expect 100-continue`
- `request buffering`
- `proxy_request_buffering`
- `417 Expectation Failed`
- `large upload`
- `early reject`
- `auth before body`
- `continue timeout`

## 깊이 들어가기

### 1. 이 메커니즘의 핵심은 "본문을 늦게 보내는 협상"이다

업로드가 큰데 서버가 어차피 거절할 요청이면, body를 다 보내는 것은 손해다.

특히 다음 경로에서 효과가 크다.

- 인증이 먼저 필요한 업로드 API
- quota / rate limit 검사가 큰 테넌트 API
- object storage proxy upload
- 바이러스 검사나 파일 형식 검증을 앞단에서 일부 선별하는 경우

### 2. proxy request buffering이 켜져 있으면 handshake가 의미를 잃을 수 있다

프록시는 안정성을 위해 body를 먼저 다 받아 둘 수 있다.

- client 입장에서는 이미 업로드를 다 했다
- upstream app은 나중에야 body를 본다
- origin이 early reject를 하고 싶어도 이미 전송 비용이 발생했다

이 경우 `Expect: 100-continue`는 wire에 있어도 실질적 이점이 작아진다.

### 3. 게이트웨이는 early reject 정책과 가장 잘 맞는 위치다

게이트웨이에서 먼저 판단 가능한 것들이 있다.

- 인증 실패
- 권한 부족
- path / method 정책 위반
- tenant quota 초과
- request size 제한

이 검사를 body 업로드 전에 끝낼 수 있으면 네트워크와 스토리지 낭비를 크게 줄일 수 있다.

### 4. 그런데 중간 홉이 많을수록 `100 Continue` 동작은 흔들리기 쉽다

실무에서 자주 보는 변형:

- proxy가 `Expect` 헤더를 없애고 upstream에 평범한 요청처럼 전달
- origin이 `100 Continue`를 보냈지만 proxy가 이미 buffering 중이라 client 체감에 영향이 없음
- client가 잠깐 기다리다 body를 그냥 보내 버림
- 어떤 홉은 `417 Expectation Failed`로 거절하고, 어떤 홉은 무시함

그래서 "지원한다"와 "실제로 이득을 준다"는 다른 말이다.

### 5. timeout budget도 따로 본다

`Expect: 100-continue`는 body 전송 전 대기 구간을 하나 더 만든다.

- continue 응답을 기다리는 client timeout
- proxy가 header 검사에 쓰는 시간
- body 업로드 자체의 write timeout
- upstream read timeout

이 구간들이 서로 안 맞으면 early reject 최적화가 오히려 첫 바이트 지연처럼 보일 수 있다.

### 6. request buffering을 무조건 끄는 것도 정답은 아니다

버퍼링은 다음 장점이 있다.

- 느린 client로부터 upstream 앱을 보호
- app worker가 직접 큰 upload를 오래 붙잡지 않게 함
- request body replay나 검사 지점을 제공

결국 핵심은 endpoint별로 다르게 보는 것이다.

early reject를 실제 운영 정책으로 쓰려면, [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)처럼 unread body를 drain할지 connection을 닫을지도 함께 정해야 한다.

- 대용량 파일 업로드
- 인증이 무거운 API
- streaming upload
- 짧은 JSON API

## 실전 시나리오

### 시나리오 1: 2GB 업로드가 끝난 뒤에야 401이 온다

초기 검사가 너무 늦다.

- gateway가 인증보다 request buffering을 먼저 한다
- origin만 auth를 안다
- `Expect: 100-continue`가 중간 홉에서 사실상 무시된다

### 시나리오 2: 어떤 클라이언트는 빠르고 어떤 클라이언트는 첫 요청이 이상하게 느리다

라이브러리마다 continue 대기 기본값이 다를 수 있다.

- 어떤 client는 잠깐 기다렸다가 body를 보낸다
- 어떤 client는 즉시 body를 보낸다
- proxy는 두 패턴을 서로 다르게 보이게 만든다

### 시나리오 3: 간헐적인 `417 Expectation Failed`가 보인다

중간 홉 중 하나가 `Expect`를 명시적으로 지원하지 않거나 정책상 금지했을 수 있다.

### 시나리오 4: request buffering을 껐더니 upstream worker가 오래 묶인다

실시간 업로드에는 좋았지만, 느린 client의 backpressure가 이제 앱에 직접 걸리는 패턴이다.

## 코드로 보기

### curl로 동작 감각 보기

```bash
curl -v \
  -H 'Expect: 100-continue' \
  -T ./large-file.bin \
  https://api.example.com/upload
```

### Nginx 계열에서 request buffering 감각 보기

```nginx
location /upload {
    proxy_request_buffering off;
    client_max_body_size 2g;
    proxy_pass http://upload_backend;
}
```

### 운영 체크 포인트

```text
- auth / quota가 body upload 전에 끝나는가
- proxy가 Expect 헤더를 유지하는가
- continue wait 구간과 write timeout이 맞는가
- 401/403/413/429가 body 수신 후에야 나가는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| request buffering on | 느린 client로부터 upstream을 보호한다 | early reject 이점이 줄고 upload 낭비가 커진다 | 일반 업로드 프록시 |
| buffering off + early reject | auth/quota 실패를 빨리 돌려준다 | upstream이 느린 upload backpressure를 직접 받는다 | 대용량 API, presigned upload 전단 |
| `Expect: 100-continue` 적극 사용 | 불필요한 body 전송을 줄인다 | 홉마다 지원 차이와 추가 대기 구간이 있다 | 큰 multipart / object upload |
| 단순 즉시 업로드 | 동작이 단순하다 | 거절될 요청도 body를 다 보낸다 | 작은 JSON 요청 |

핵심은 `Expect: 100-continue`를 헤더 문법으로 보는 것이 아니라 **body 업로드 전에 어떤 정책을 끝낼지 정하는 운영 선택**으로 보는 것이다.

## 꼬리질문

> Q: `Expect: 100-continue`는 왜 필요한가요?
> 핵심: 큰 body를 보내기 전에 서버가 먼저 수락 가능한지 확인해 업로드 낭비를 줄이기 위해서다.

> Q: request buffering이 켜져 있으면 왜 효과가 줄어드나요?
> 핵심: proxy가 body를 먼저 다 받아 버리면 origin의 early reject가 늦어진다.

> Q: request buffering을 무조건 끄면 좋은가요?
> 핵심: 아니다. 느린 client 보호와 upstream 자원 점유 관점에서는 버퍼링이 여전히 유용할 수 있다.

## 한 줄 정리

`Expect: 100-continue`는 대용량 업로드를 body 전송 전에 걸러내는 도구지만, gateway의 auth 순서와 proxy request buffering이 맞지 않으면 early reject 대신 지연과 혼선만 남는다.

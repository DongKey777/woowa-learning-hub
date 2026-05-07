---
schema_version: 3
title: "HTTP/2 Upload Early Reject, RST_STREAM, Flow-Control Cleanup"
concept_id: network/http2-upload-early-reject-rst-stream-flow-control-cleanup
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- http2-upload-early-reject
- rst-stream-flow-control
- h2-unread-body-cleanup
aliases:
- http2 upload reject
- h2 upload early reject
- RST_STREAM NO_ERROR upload
- discard DATA after reset
- connection flow control after reset
- h2 unread body cleanup
symptoms:
- HTTP/2 upload early reject를 HTTP/1.1 leftover bytes 문제와 같은 방식으로만 본다
- final response만 보내면 client가 남은 DATA를 멈춘다고 생각하고 RST_STREAM 신호를 놓친다
- reset 후 in-flight DATA discard와 connection-level flow control credit accounting을 무시한다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- network/http-request-body-drain-early-reject-keepalive-reuse
- network/http2-flow-control-window-update-stalls
next_docs:
- network/expect-100-continue-proxy-request-buffering
- network/gateway-buffering-vs-spring-early-reject
- network/http2-rst-stream-goaway-streaming-failure-semantics
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
linked_paths:
- contents/network/http-request-body-drain-early-reject-keepalive-reuse.md
- contents/network/expect-100-continue-proxy-request-buffering.md
- contents/network/gateway-buffering-vs-spring-early-reject.md
- contents/network/http2-flow-control-window-update-stalls.md
- contents/network/http2-rst-stream-goaway-streaming-failure-semantics.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
- contents/network/sse-failure-attribution-http1-http2.md
- contents/network/multipart-parsing-vs-auth-reject-boundary.md
confusable_with:
- network/http-request-body-drain-early-reject-keepalive-reuse
- network/http2-flow-control-window-update-stalls
- network/http2-rst-stream-goaway-streaming-failure-semantics
- network/gateway-buffering-vs-spring-early-reject
forbidden_neighbors: []
expected_queries:
- "HTTP/2 큰 업로드를 early reject할 때 RST_STREAM과 flow-control cleanup을 어떻게 설계해?"
- "H2에서는 unread body가 다음 요청 byte stream을 오염시키는 것보다 무엇이 더 중요해?"
- "final response를 보낸 뒤에도 request DATA가 계속 오면 RST_STREAM이 필요한 이유는?"
- "RST_STREAM NO_ERROR upload reject와 CANCEL REFUSED_STREAM 의미 차이를 설명해줘"
- "reset 후 discard DATA가 connection-level window credit에 미치는 영향을 알려줘"
contextual_chunk_prefix: |
  이 문서는 HTTP/2 upload early reject에서 final response before request end,
  RST_STREAM(NO_ERROR), in-flight DATA discard, connection-level flow control
  credit cleanup, stream reset attribution을 다루는 advanced playbook이다.
---
# HTTP/2 Upload Early Reject, RST_STREAM, Flow-Control Cleanup

> 한 줄 요약: HTTP/2에서 큰 업로드를 early reject할 때 핵심은 HTTP/1.1처럼 leftover body가 다음 요청을 오염시키는가가 아니라, **어느 시점에 `RST_STREAM`으로 업로드 중단을 알리고, reset 이후에도 connection-level flow control과 discard cleanup을 어떻게 유지하는가**다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
> - [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)
> - [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
> - [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md)
> - [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [SSE Failure Attribution Across HTTP/1.1 and HTTP/2](./sse-failure-attribution-http1-http2.md)
> - [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md)

retrieval-anchor-keywords: http2 upload reject, h2 upload early reject, RST_STREAM NO_ERROR upload, response before request end http2, discard DATA after reset, connection flow control after reset, large upload stream reset, h2 unread body cleanup, 413 h2 reset, 401 h2 upload reject, stream-local reject connection-level stall, reset stream credit accounting

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

HTTP/2 업로드 early reject는 HTTP/1.1과 질문 자체가 조금 다르다.

- HTTP/1.1은 unread body가 다음 요청 byte stream과 섞이는지가 핵심이다
- HTTP/2는 stream framing이 분리돼 있어 다음 요청 파싱 오염은 덜하다
- 대신 **한 stream의 업로드를 어떻게 멈추게 할지**와 **discard되는 DATA가 shared connection window에 어떤 영향을 주는지**가 핵심이 된다

즉 H2에서 `401`, `403`, `413`, `429`를 빨리 보냈다고 끝나는 것이 아니다.

- final response를 먼저 보냈는가
- `RST_STREAM`으로 request body 중단을 명시했는가
- reset 전에 이미 날아오던 DATA를 어디서 discard했는가
- 그 discard path가 connection-level flow control credit를 계속 맞췄는가

### Retrieval Anchors

- `http2 upload reject`
- `RST_STREAM NO_ERROR upload`
- `response before request end http2`
- `discard DATA after reset`
- `connection flow control after reset`
- `h2 unread body cleanup`
- `413 h2 reset`
- `stream-local reject connection-level stall`

## 깊이 들어가기

### 1. H1의 unread-body 문제와 H2의 cleanup 문제는 닮았지만 다르다

HTTP/1.1 keep-alive에서는 unread body를 남기면 다음 요청과 byte stream이 섞일 수 있다.  
그래서 drain하거나 connection을 닫는 선택이 핵심이다.

HTTP/2에서는 stream이 프레이밍되어 있어 그 위험은 줄어든다.

- stream 13의 upload reject가 stream 15의 header bytes를 오염시키지는 않는다
- 그래서 단순히 "다음 요청 파싱이 깨진다"는 H1식 공포는 덜하다

하지만 문제가 사라진 것은 아니다.

- request body를 더 안 읽을 것임을 peer에게 빨리 알려야 한다
- reset 직전에 이미 전송된 DATA는 여전히 도착할 수 있다
- 이 DATA를 버리더라도 connection-level flow control은 계속 맞아야 한다

즉 H2 cleanup의 질문은 **leftover bytes가 framing을 망치느냐**가 아니라, **업로드 stop signal과 shared connection credit가 맞물려 있느냐**다.

### 2. final response만 보내고 끝내면, request side는 아직 살아 있을 수 있다

HTTP/2는 server가 request body가 아직 안 끝났어도 final response를 먼저 보낼 수 있다.

예를 들어:

- header만 보고 auth 실패를 판단했다
- `413` size policy를 초반에 결정했다
- quota 초과를 body parsing 전에 알 수 있다

이때 서버는 응답 자체는 빨리 끝낼 수 있다.  
하지만 client가 업로드를 계속 보내고 있다면 request side는 아직 조용히 끝나지 않는다.

즉 다음 둘은 다른 행동이다.

- final response `HEADERS` + `END_STREAM`만 보냄
- final response를 보낸 뒤 `RST_STREAM`으로 "남은 request body는 그만 보내라"를 명시

H2 upload early reject에서 이 차이를 놓치면, "응답은 빨랐는데 왜 upload bytes가 계속 늘지?"라는 혼선이 생긴다.

### 3. upload early reject에서 `RST_STREAM(NO_ERROR)`는 "응답은 유효하지만 body는 더 필요 없다"는 뜻에 가깝다

HTTP/2에서는 server가 complete response를 보낸 뒤 `RST_STREAM(NO_ERROR)`로 남은 request transmission 중단을 요청할 수 있다.

이 패턴이 의미하는 것은 보통 아래에 가깝다.

- 응답 자체는 정상적인 최종 판단이다
- 다만 남은 upload body는 더 받을 가치가 없다
- connection 전체를 죽일 필요는 없다

그래서 large upload early reject에서는 `NO_ERROR` reset이 잘 맞는 경우가 많다.

반대로 운영에서 자주 헷갈리는 코드들은 다르게 읽어야 한다.

- `CANCEL`: "이 stream이 더 이상 필요 없다"는 더 일반적인 취소 신호라서, client abort인지 proxy local cancel인지 app early reject인지가 모호할 수 있다
- `REFUSED_STREAM`: application processing 전에 거절했다는 뜻에 더 가깝다. auth/quota/body policy를 이미 평가한 뒤의 reject에 무심코 쓰면 retry 의미가 틀어질 수 있다

핵심은 reset code가 단순 transport decoration이 아니라 **retry와 attribution 힌트**라는 점이다.

### 4. `RST_STREAM`이 갔어도, 이미 날아오던 DATA는 잠깐 더 도착할 수 있다

reset을 보낸 시점과 peer가 reset을 실제로 처리한 시점은 다르다.

그래서 reset 직후에도 이런 일이 가능하다.

- client는 이미 몇 개 DATA frame을 kernel/user-space queue에 올려 둠
- proxy는 upstream으로 밀어 넣을 DATA를 이미 enqueue함
- server는 stream을 reset했는데도 그 직전 DATA를 더 받음

이 구간을 잘못 해석하면 팀은 "reset을 보냈는데 왜 upload bytes가 더 들어오지?"라고 묻는다.  
답은 단순하다. **reset은 즉시 시간 정지가 아니라, stop signal이 peer까지 전파되기 전까지는 in-flight DATA가 남을 수 있다**.

### 5. discard된 DATA도 connection-level flow control에는 계속 영향을 준다

여기가 H2-specific 함정이다.

reset 이후 도착한 DATA를 애플리케이션은 무시할 수 있다.  
하지만 transport/H2 stack은 이 DATA를 완전히 없는 일처럼 취급하면 안 된다.

- 이미 온 DATA는 connection window를 점유한다
- shared connection이므로 다른 stream도 이 credit에 영향을 받는다
- discard path가 credit accounting을 놓치면, unrelated unary RPC나 다른 download stream까지 stall될 수 있다

즉 "이 stream은 끝났으니 그냥 무시"가 아니라:

- frame은 최소한 처리하고
- 버리더라도 connection-level bookkeeping은 유지하고
- 필요하면 connection window credit를 다시 돌려줘야 한다

그래서 H2 upload cleanup은 애플리케이션의 unread-body drain이 아니라 **transport stack의 discard + connection WINDOW_UPDATE hygiene** 문제로 바뀐다.

### 6. 그래서 H2 upload early reject는 `drain vs close`보다 `respond vs reset vs credit accounting`으로 봐야 한다

HTTP/1.1 질문:

- 남은 body를 drain할까
- 아니면 connection을 닫아 keep-alive reuse를 포기할까

HTTP/2 질문:

- final response를 먼저 보낼까
- 이어서 `RST_STREAM`으로 request transmission 중단을 요청할까
- reset 뒤 discard되는 DATA의 connection credit를 어떻게 관리할까
- connection 전체는 계속 재사용할까, 아니면 `GOAWAY`/TCP close로 blast radius를 넓힐까

즉 H2에서는 connection 자체를 살린 채 **stream-local reject**를 하는 것이 자연스러운 기본값이다.  
ordinary upload reject마다 connection close로 가면 multiplexing 이점을 스스로 버리게 된다.

### 7. 관측은 "응답 시계"와 "reset/cleanup 시계"를 분리해야 한다

대용량 upload early reject에서 최소 두 개의 시계가 있다.

1. final response headers가 나간 시각
2. reset이 나간 시각과 in-flight DATA discard가 끝난 시각

여기에 connection-level 증상을 붙여서 봐야 한다.

- `late_data_bytes_after_reset`
- `connection_window_remaining`
- `sibling_stream_stall_ms`
- `stream_reset_code`
- `response_sent_before_request_end`

이 분리가 없으면 다음이 전부 같은 원인으로 뭉개진다.

- app은 `413`을 4ms에 반환
- H2 frame log에는 `RST_STREAM(NO_ERROR)`
- edge는 upload bytes가 더 늘다 종료
- 같은 connection의 다른 stream p99가 튐

사실 이건 "응답 늦음"이 아니라 **reset 이후 connection credit cleanup이 느렸음**일 수 있다.

### 8. proxy 체인에서는 H2 semantics가 다시 번역된다

client와 edge는 H2지만, upstream origin은 H1일 수도 있다.  
또는 client와 edge는 H2, mesh hop도 H2, origin app만 H1일 수도 있다.

그래서 같은 incident가 다음처럼 갈라져 보인다.

- downstream H2: `RST_STREAM(NO_ERROR)` 또는 `CANCEL`
- edge access log: 짧은 `413` 뒤 추가 upload bytes, 혹은 `499`
- upstream H1 origin: unread body drain/close 또는 request abort surface

즉 "H2에선 stream reset", "H1에선 unread-body cleanup"이 같은 request의 hop별 번역본일 수 있다.  
이 교차 번역을 못 붙이면, 어떤 팀은 H2 reset 문제로 보고 어떤 팀은 servlet unread-body 문제로 본다.

## 실전 시나리오

### 시나리오 1: `413`은 즉시 나가는데, 같은 H2 connection의 다른 요청 p99가 튄다

원인 후보:

- large upload stream을 early reject하고 reset했다
- reset 전에 이미 전송된 DATA가 한동안 계속 도착했다
- discard path가 connection window credit를 늦게 돌려줬다

이때 증상은 upload stream 하나의 문제가 아니라 **shared connection flow-control stall**로 번진다.

### 시나리오 2: frame log에는 `RST_STREAM(NO_ERROR)`인데, 운영은 `499`나 client abort로 본다

가능한 해석:

- 서버는 final response를 유효하게 보낸 뒤 upload stop을 요청했다
- client나 proxy는 그 사이 업로드를 멈추며 자체 abort 표면을 남겼다

즉 `499`와 `RST_STREAM(NO_ERROR)`는 서로 배타적이지 않을 수 있다.

### 시나리오 3: auth reject upload에서 `REFUSED_STREAM`이 보여 retry가 붙는다

이 경우는 의미가 위험하다.

- 실제로는 auth/quota/body policy를 이미 평가했을 수 있다
- 그런데 `REFUSED_STREAM`은 "application processing 전에 거절"처럼 읽힐 수 있다
- retry 정책이 이를 transient pre-processing failure로 오해할 수 있다

upload early reject path에서 reset code는 retry contract까지 건드린다.

### 시나리오 4: upload 하나를 reject했는데 sibling stream까지 끊긴다

우선 의심할 것:

- intermediary가 stream-local reset 대신 connection close를 택했는가
- `GOAWAY`나 TCP close로 번역되었는가
- overload 정책이 ordinary reject와 catastrophic close를 구분하지 않는가

대부분의 ordinary auth/quota/size reject는 stream-local handling이어야지, connection-wide kill이어야 하는 것은 아니다.

## 코드로 보기

### H2 upload early reject 타임라인 메모

```text
t1 client sends request HEADERS for large upload
t2 server decides 401/413/429 before full body read
t3 server sends final response HEADERS (+ END_STREAM)
t4 server sends RST_STREAM(NO_ERROR) to stop remaining request body
t5 some in-flight DATA still arrive on that stream
t6 H2 stack discards DATA but continues connection-level credit accounting
t7 sibling streams continue without connection-window starvation
```

### 운영 체크 포인트

```text
- response_sent_before_request_end
- rst_stream_code = NO_ERROR | CANCEL | REFUSED_STREAM | other
- late_data_bytes_after_reset
- connection_window_remaining
- sibling_stream_stall_ms
- connection_reused_after_reject
- proxy translated reset into GOAWAY/TCP close?
```

### 분류 질문

```text
- final response가 reset보다 먼저 완료됐는가
- reset code가 "response valid, upload stop" 의미인가, generic cancel인가
- reset 뒤에도 DATA가 얼마나 더 들어왔는가
- discard path가 connection-level WINDOW_UPDATE hygiene를 유지했는가
- 다른 stream이 같은 connection에서 같이 느려졌는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| final response만 보내고 업로드가 알아서 멈추길 기대 | 구현이 단순하다 | peer가 body를 더 보낼 수 있고 receive/flow-control 부담이 남는다 | 작은 upload, buffering hop이 이미 body를 잡은 경우 |
| final response + `RST_STREAM(NO_ERROR)` | 응답 유효성과 upload stop 의도를 함께 전달한다 | reset 뒤 late DATA discard와 connection credit accounting이 필요하다 | 큰 upload early reject, auth/quota/size guard |
| `RST_STREAM(CANCEL)` 중심 처리 | 빠른 종료가 쉽다 | client abort와 server reject가 같은 표면으로 섞여 attribution이 흐려진다 | generic cancel path, proxy local cancel |
| connection close / `GOAWAY` | 구현이 단순하고 강하게 멈춘다 | sibling stream까지 날리고 H2 multiplexing 이점을 잃는다 | protocol error, severe overload, connection-level shutdown |

핵심은 H2 upload reject를 H1의 drain/close 복사판으로 보지 말고 **stream-local stop signal과 connection-level credit hygiene의 결합 문제**로 보는 것이다.

## 꼬리질문

> Q: HTTP/2에서는 HTTP/1.1처럼 body를 끝까지 drain하지 않아도 되나요?
> 핵심: framing 오염 위험은 덜하지만, 대신 `RST_STREAM`과 connection-level flow-control accounting을 제대로 처리해야 한다.

> Q: 왜 `RST_STREAM(NO_ERROR)`가 upload early reject에서 자주 언급되나요?
> 핵심: final response는 유효하지만 남은 request body는 더 필요 없다는 뜻을 가장 덜 오해하게 전달할 수 있기 때문이다.

> Q: reset을 보냈는데 왜 다른 stream까지 느려질 수 있나요?
> 핵심: reset 전에 이미 날아오던 DATA가 discard되더라도 connection window를 점유할 수 있어서, credit accounting이 늦으면 sibling stream이 stall될 수 있다.

## 한 줄 정리

HTTP/2 대용량 업로드 early reject의 진짜 쟁점은 status code보다, **final response 뒤 `RST_STREAM`으로 업로드 중단을 어떻게 알리고 reset 이후 discard DATA의 connection flow control cleanup을 얼마나 깔끔하게 하느냐**다.

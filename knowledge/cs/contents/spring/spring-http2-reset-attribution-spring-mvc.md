# Spring HTTP/2 Reset Attribution in Spring MVC

> 한 줄 요약: HTTP/2에선 client cancel과 connection drain이 `broken pipe`보다 먼저 `RST_STREAM`과 `GOAWAY`로 표현되므로, Spring MVC 운영 해석도 "socket이 끊겼나"보다 "stream이 reset됐나, connection이 drain 중인가"를 먼저 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
> - [Spring Async Timeout vs Disconnect Decision Tree](./spring-async-timeout-disconnect-decision-tree.md)
> - [Spring Observability, Micrometer, Tracing](./spring-observability-micrometer-tracing.md)

retrieval-anchor-keywords: Spring HTTP/2 reset attribution, spring mvc http2 reset, RST_STREAM, GOAWAY, CANCEL_STREAM_ERROR, stream reset, stream closed, client cancel, graceful shutdown, Tomcat CloseNowException, Tomcat StreamException, Tomcat ClientAbortException, Jetty EofException reset, Jetty Output shutdown, Undertow ClosedChannelException, Undertow peerGoneAway, AsyncRequestNotUsableException, DisconnectedClientHelper, http2 observability, stream id logging, connection drain

## 핵심 개념

classic broken pipe는 대개 **TCP connection 전체가 이미 죽은 뒤** 다음 write/flush에서 드러난다.

HTTP/2는 그보다 먼저 다음 control signal이 온다.

- `RST_STREAM`: 특정 stream만 취소한다. 같은 TCP connection의 다른 stream은 계속 살 수 있다.
- `GOAWAY`: connection이 drain/close 단계로 들어갔음을 알린다. 이미 flight 중인 stream은 끝까지 갈 수도 있고, 새 stream은 거부된다.

즉 HTTP/2에선 "사용자가 취소했다"가 바로 `Broken pipe`로 보이지 않을 수 있다.

- Tomcat은 stream-state 예외를 먼저 만든다.
- Jetty는 `EofException("reset")` 또는 `EofException("Output shutdown")` 같은 quiet failure로 접는다.
- Undertow는 HTTP/2 내부 상태를 관리하지만 servlet/app write 경로는 자주 `ClosedChannelException`으로 평탄화된다.

그래서 `h2` 요청에서 예외 이름만 보고 classic broken pipe bucket에 넣으면 귀속이 어긋난다.

## 먼저 signal scope를 나눈다

| signal | scope | 운영 의미 | classic broken pipe와 다른 점 |
|---|---|---|---|
| client `RST_STREAM(CANCEL)` | single stream | 브라우저 refresh, 탭 종료, fetch abort, proxy per-stream cancel | connection 전체는 아직 살아 있을 수 있다 |
| server/application abort가 만든 `RST_STREAM` | single stream | handler abort, async write cancel, server-side stream close | TCP close 대신 stream-level cancel이 먼저 보인다 |
| graceful `GOAWAY` | connection drain | shutdown/redeploy/idle-close 직전 drain | 현재 in-flight stream이 성공적으로 끝날 수도 있다 |
| non-graceful `GOAWAY` 또는 이후 TCP close | connection | pending stream reset, 재연결 유도, 연결 종료 | 마지막엔 `ClosedChannelException`/`broken pipe`로 이어질 수 있지만 1차 신호는 GOAWAY다 |

핵심은 `http2_signal=stream_reset|goaway|socket_close`를 분리하는 것이다.

## 컨테이너별 surface 차이

| 컨테이너 | HTTP/2 client cancel / reset에서 먼저 보이는 shape | GOAWAY에서 먼저 보이는 shape | classic broken pipe와 구분 포인트 |
|---|---|---|---|
| Tomcat | `CloseNowException` + 원인 `StreamException`, `"This stream is not writable"`, `"Client reset the stream before the response was complete"` | `goaway(...)` trace 후 connection close | plain `IOException`만 `ClientAbortException`로 감싸므로, `CloseNowException` 계열이면 socket abort보다 stream-state 종료에 가깝다 |
| Jetty | `EofException("reset")`, 이후 write 시 `EofException("Output shutdown")` | graceful GOAWAY면 in-flight stream 완료 가능, pending stream은 reset 가능 | HTTP/2 reset과 classic socket EOF가 모두 `EofException` family라서 protocol=`h2`와 message가 중요하다 |
| Undertow | HTTP/2 layer는 `handleRstStream(..., true)`와 `rstStream()`으로 상태를 접지만, app write 경로는 자주 `ClosedChannelException` | `peerGoneAway=true`, 기존 stream source/sink reset 후 GOAWAY 송신 | servlet 전용 abort 타입이 약하므로 request-io 로그의 `rststream`/`goaway`와 함께 봐야 한다 |

### Tomcat

Tomcat은 HTTP/2에서 classic broken pipe와 다른 분기점을 비교적 명확히 남긴다.

- stream window를 더 이상 예약할 수 없으면 `CloseNowException("This stream is not writable")`를 던진다.
- stream cancel 시 `StreamException`을 저장하고 `CloseNowException`으로 application write를 끊는다.
- `OutputBuffer.realWriteBytes(...)`는 plain `IOException`만 `ClientAbortException`으로 감싼다.

즉 Tomcat에서 `ClientAbortException`만 보였다면 classic remote abort에 더 가깝고, `CloseNowException` 또는 그 원인 `StreamException`이 보인다면 HTTP/2 stream reset/close 가능성이 높다.

### Jetty

Jetty는 reset과 output shutdown을 모두 `EofException` 계열 quiet failure로 수렴시키는 편이다.

- remote reset을 받으면 `HTTP2Stream.onReset(...)`이 failure를 `new EofException("reset")`로 둔다.
- output side가 닫힌 뒤 write하면 `HTTP2StreamEndPoint`가 `EofException("Output shutdown")`을 준다.
- Jetty의 HTTP/2 테스트는 client reset 뒤 response write가 `EofException`으로 실패함을 검증한다.

따라서 Jetty에선 `"broken pipe"` 문자열이 없어도 `protocol=h2` + `EofException("reset"|"Output shutdown")`이면 HTTP/2 reset bucket을 우선 의심해야 한다.

### Undertow

Undertow는 HTTP/2 상태 머신은 분명히 갖고 있지만 app-visible 예외는 더 generic하다.

- `Http2Channel`은 `RST_STREAM`을 받으면 `handleRstStream(...)`에서 source/sink channel에 `rstStream()`을 전파한다.
- remote `GOAWAY`를 받으면 `peerGoneAway=true`로 두고 현재 stream의 source/sink를 reset한 뒤 GOAWAY를 응답한다.
- 하지만 response conduit와 framed channel write path는 흔히 `ClosedChannelException`으로 닫힌 채널을 드러낸다.

그래서 Undertow는 class 이름만으로 `broken pipe`와 HTTP/2 reset을 구분하기 어렵다.

- request protocol이 `h2`였는지
- 같은 시각 request-io 로그에 `Sending rststream` / `Sending goaway`가 있었는지
- reset 이후 다른 stream이 같은 connection에서 계속 흘렀는지

를 함께 봐야 한다.

## Spring MVC에서 어떻게 다시 보이는가

Spring MVC는 container 예외를 그대로 보이게 둘 때도 있고, 이미 unusable해진 response를 `AsyncRequestNotUsableException`으로 재표면화할 때도 있다.

실무 attribution 순서는 다음이 안전하다.

1. 요청 프로토콜이 `h2` 또는 `HTTP/2.0`인가?
2. 최상위가 `AsyncRequestNotUsableException`이면 cause 체인에 `CloseNowException`, `StreamException`, `EofException("reset")`, `EofException("Output shutdown")`, `ClosedChannelException`가 있는가?
3. 같은 시점에 container trace/debug가 `RST_STREAM`, `rststream`, `GOAWAY`, `stream not writable`, `client reset the stream`을 남겼는가?
4. 문제가 single stream cancel인지, connection drain인지 분리됐는가?

`DisconnectedClientHelper`는 `ClientAbortException`, `EOFException`, `EofException`, `AsyncRequestNotUsableException`, `broken pipe`, `connection reset by peer`를 disconnected client 후보로 본다.

하지만 이 helper만으로는 다음이 충분히 안 갈린다.

- Jetty `EofException("reset")`가 HTTP/2 reset인지 classic EOF인지
- Undertow `ClosedChannelException`이 GOAWAY 이후 drain인지 late socket close인지
- Tomcat `CloseNowException`가 plain remote abort인지 stream-state close인지

그래서 Spring layer에선 `client disconnected` 판별과 별개로 `transport_family=http2`와 `http2_signal`을 같이 태깅해야 한다.

## 운영 tagging / alert 기준

다음 정도만 분리해도 noisy broken-pipe alert 품질이 크게 좋아진다.

- `transport_family=http1|http2`
- `http2_signal=stream_reset|goaway|socket_close|unknown`
- `container_family=tomcat|jetty|undertow`
- `raw_exception=CloseNowException|ClientAbortException|EofException|ClosedChannelException|AsyncRequestNotUsableException`
- `scope=single_stream|connection`
- `commit_state=before_first_byte|after_first_byte`

권장 해석은 이렇다.

- `h2 + stream_reset + after_first_byte`: page 금지. user cancel, browser abort, proxy per-stream reset 후보.
- `h2 + goaway + current stream success`: 오류로 세지지 않는다. drain/shutdown telemetry로 본다.
- `h2 + goaway + pending stream reset 급증`: deploy/shutdown/reconnect 품질 문제 후보.
- `h2 + socket_close + broken pipe`: GOAWAY 이후 late close인지, 진짜 TCP abort인지 추가 확인이 필요하다.

즉 HTTP/2에선 `broken_pipe_count` 하나보다 아래가 더 중요하다.

```text
http2_stream_reset_ratio(route, 5m)
http2_goaway_events(reason, 5m)
async_not_usable_after_h2_reset(route, 5m)
```

## 공식 구현 근거

- Spring: [`DisconnectedClientHelper`](https://github.com/spring-projects/spring-framework/blob/main/spring-web/src/main/java/org/springframework/web/util/DisconnectedClientHelper.java), [`StandardServletAsyncWebRequest`](https://github.com/spring-projects/spring-framework/blob/main/spring-web/src/main/java/org/springframework/web/context/request/async/StandardServletAsyncWebRequest.java)
- Tomcat: [`Stream.java`](https://github.com/apache/tomcat/blob/main/java/org/apache/coyote/http2/Stream.java), [`OutputBuffer.java`](https://github.com/apache/tomcat/blob/main/java/org/apache/catalina/connector/OutputBuffer.java), [`Http2UpgradeHandler.java`](https://github.com/apache/tomcat/blob/main/java/org/apache/coyote/http2/Http2UpgradeHandler.java)
- Jetty: [`HTTP2Stream.java`](https://github.com/jetty/jetty.project/blob/jetty-12.1.x/jetty-core/jetty-http2/jetty-http2-common/src/main/java/org/eclipse/jetty/http2/HTTP2Stream.java), [`HTTP2StreamEndPoint.java`](https://github.com/jetty/jetty.project/blob/jetty-12.1.x/jetty-core/jetty-http2/jetty-http2-common/src/main/java/org/eclipse/jetty/http2/HTTP2StreamEndPoint.java), [`AsyncIOTest.java`](https://github.com/jetty/jetty.project/blob/jetty-12.1.x/jetty-core/jetty-http2/jetty-http2-tests/src/test/java/org/eclipse/jetty/http2/tests/AsyncIOTest.java), [`GoAwayTest.java`](https://github.com/jetty/jetty.project/blob/jetty-12.1.x/jetty-core/jetty-http2/jetty-http2-tests/src/test/java/org/eclipse/jetty/http2/tests/GoAwayTest.java)
- Undertow: [`Http2Channel.java`](https://github.com/undertow-io/undertow/blob/main/core/src/main/java/io/undertow/protocols/http2/Http2Channel.java), [`Http2StreamSinkChannel.java`](https://github.com/undertow-io/undertow/blob/main/core/src/main/java/io/undertow/protocols/http2/Http2StreamSinkChannel.java), [`AbstractFramedChannel.java`](https://github.com/undertow-io/undertow/blob/main/core/src/main/java/io/undertow/server/protocol/framed/AbstractFramedChannel.java), [`HttpResponseConduit.java`](https://github.com/undertow-io/undertow/blob/main/core/src/main/java/io/undertow/server/protocol/http/HttpResponseConduit.java)

## 꼬리질문

> Q: HTTP/2 client cancel은 왜 broken pipe와 같은 bucket으로 묶으면 안 되나?
> 의도: stream-scope와 connection-scope 구분 확인
> 핵심: `RST_STREAM`은 single stream cancel일 수 있고, 같은 connection의 다른 stream은 계속 성공할 수 있기 때문이다.

> Q: Jetty에서 `EofException`이면 무조건 classic EOF인가?
> 의도: Jetty 예외 shape 해석 확인
> 핵심: 아니다. `protocol=h2`와 message가 `reset`/`Output shutdown`이면 HTTP/2 reset 가능성이 높다.

> Q: Undertow는 왜 HTTP/2 reset을 보기 더 어려운가?
> 의도: generic channel close 이해 확인
> 핵심: HTTP/2 상태는 내부적으로 관리하지만 servlet write path는 흔히 `ClosedChannelException`으로 평탄화되기 때문이다.

> Q: GOAWAY는 왜 per-request error처럼 세면 안 되나?
> 의도: connection drain 의미 확인
> 핵심: graceful GOAWAY는 in-flight stream을 성공적으로 끝내게 둘 수 있고, 새 connection으로 재연결시키는 connection-level 신호이기 때문이다.

## 한 줄 정리

Spring MVC의 HTTP/2 disconnect 해석은 `broken pipe` 탐지보다 **`RST_STREAM`인지 `GOAWAY`인지, 그리고 그 signal이 single stream인지 connection drain인지**를 먼저 가르는 작업이다.

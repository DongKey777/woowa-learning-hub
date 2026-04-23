# HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics

> 한 줄 요약: HTTP/2에서 `RST_STREAM`은 한 stream만 끊고, `GOAWAY`는 연결 전체에 새 stream 금지를 알리며, TCP `FIN`/`RST`는 transport를 끝낸다. 이 셋을 구분하지 못하면 gRPC retry와 streaming 실패를 잘못 해석하게 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md)
> - [HTTP/2 Upload Early Reject, RST_STREAM, Flow-Control Cleanup](./http2-upload-early-reject-rst-stream-flow-control-cleanup.md)
> - [gRPC Deadlines, Cancellation Propagation](./grpc-deadlines-cancellation-propagation.md)
> - [gRPC Keepalive, GOAWAY, Max Connection Age](./grpc-keepalive-goaway-max-connection-age.md)
> - [gRPC Status, Trailers, Transport Error Mapping](./grpc-status-trailers-transport-error-mapping.md)
> - [FIN, RST, Half-Close, EOF](./fin-rst-half-close-eof-semantics.md)
> - [SSE Failure Attribution Across HTTP/1.1 and HTTP/2](./sse-failure-attribution-http1-http2.md)

retrieval-anchor-keywords: RST_STREAM, GOAWAY, HTTP/2 stream reset, gRPC cancellation, REFUSED_STREAM, NO_ERROR, stream retry semantics, trailers-only, last stream id, graceful drain, 499 vs RST_STREAM, SSE downstream abort, stream cancel attribution, upload early reject, request body abort, RST_STREAM NO_ERROR upload

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

HTTP/2는 하나의 TCP 연결 위에 여러 stream을 올리기 때문에, 종료와 실패도 여러 층위로 나뉜다.

- `RST_STREAM`: 특정 stream 하나만 중단
- `GOAWAY`: 이 연결은 더 이상 새 stream을 받지 않겠다고 알림
- TCP `FIN`/`RST`: 연결 transport 자체를 종료

즉 "연결이 끊겼다"와 "stream 하나가 취소됐다"는 전혀 같은 말이 아니다.

### Retrieval Anchors

- `RST_STREAM`
- `GOAWAY`
- `HTTP/2 stream reset`
- `gRPC cancellation`
- `REFUSED_STREAM`
- `NO_ERROR`
- `last stream id`
- `graceful drain`

## 깊이 들어가기

### 1. stream-level 실패와 connection-level 실패를 분리해야 한다

`RST_STREAM`이 오면 보통 하나의 요청/응답 stream만 끝난다.

- 같은 H2 connection의 다른 stream은 계속 살 수 있다
- 장기 streaming 하나만 취소할 수 있다
- 클라이언트가 특정 요청만 cancel할 수 있다

반면 `GOAWAY`는 연결에 대한 정책 신호다.

- 이미 진행 중인 일부 stream은 계속 마무리될 수 있다
- 하지만 새 stream은 다른 연결로 보내야 한다

대용량 upload early reject도 여기에 들어간다.  
final response 뒤 `RST_STREAM(NO_ERROR)`가 보이면 "연결이 죽었다"보다 **이 stream의 남은 request body는 더 필요 없다는 stop signal**일 가능성을 먼저 봐야 한다.

### 2. `GOAWAY`는 graceful drain일 수도 있고, 장애 신호일 수도 있다

실무에서 흔한 오해는 `GOAWAY`를 무조건 실패로 보는 것이다.

정상적인 경우:

- deploy drain
- max connection age 회전
- endpoint 교체

비정상적인 경우:

- protocol error
- overload 또는 policy violation
- middlebox와 H2 상태 불일치

핵심은 `error code`와 `last stream id`를 같이 보는 것이다.

### 3. `RST_STREAM` 코드가 retry 안전성을 자동으로 보장하지는 않는다

일부 reset은 retry를 고려해 볼 수 있다.

- `REFUSED_STREAM`: application 처리 전에 거절됐을 가능성이 높다
- client-side cancellation: retry 의미가 없을 수 있다

하지만 mid-stream reset은 위험하다.

- upstream이 이미 일부 작업을 했을 수 있다
- side effect가 발생했을 수 있다
- gRPC status만 보고 자동 retry하면 중복 처리가 생길 수 있다

그래서 retry는 error code뿐 아니라 **idempotency와 처리 시점**을 같이 봐야 한다.

### 4. graceful trailers와 reset은 운영 의미가 다르다

gRPC는 정상 종료 시 status와 metadata를 trailer로 보낸다.

- 정상 완료
- 애플리케이션 레벨 에러 반환
- trailers-only 응답

하지만 `RST_STREAM`으로 끝나면:

- trailer가 아예 오지 않을 수 있다
- 관측 계층에서 실패 원인이 더 거칠게 보인다
- 앱은 `CANCELLED`, `UNAVAILABLE`, transport error처럼 번역된 결과만 볼 수 있다

즉 "에러를 반환했다"와 "stream이 날아갔다"는 다르다.

### 5. streaming RPC에서는 중간 종료 해석이 특히 어렵다

server streaming, client streaming, bidi streaming은 오랫동안 살아 있다.

이때 중간 종료는 여러 뜻일 수 있다.

- client가 더 이상 안 받아 `RST_STREAM`으로 cancel
- server가 overload나 shutdown으로 끊음
- proxy가 idle policy나 buffer pressure로 stream을 날림

동일한 사용자 증상은 "중간에 끊겼다"지만, retry 가능성과 데이터 중복 위험은 전혀 다르다.

### 6. transport close와 H2 signal이 섞이면 진단이 더 어렵다

예를 들어:

- server는 `GOAWAY` 후 정상 drain을 기대했다
- 하지만 proxy가 곧바로 TCP `RST`로 연결을 닫았다
- client는 graceful drain을 못 보고 connection failure로 인식한다

이 경우 H2 레벨 의도와 TCP 레벨 결과가 달라진다.

## 실전 시나리오

### 시나리오 1: deploy 때 일부 gRPC 요청만 `UNAVAILABLE`이 난다

가능한 원인:

- 서버는 `GOAWAY`로 graceful drain을 시도했다
- 클라이언트가 새 연결 재수립 전 몇 개 stream만 실패했다
- proxy가 `last stream id` 이전/이후 요청을 다르게 처리했다

### 시나리오 2: 한 streaming RPC를 cancel했는데 팀이 연결이 깨졌다고 오해한다

`RST_STREAM`은 그 stream만 끊었을 수 있다.  
같은 TCP/H2 connection의 다른 요청까지 죽었다고 단정하면 안 된다.

### 시나리오 3: overload 때 자동 retry가 오히려 중복 실행을 만든다

`REFUSED_STREAM`처럼 보이거나 transport error로 번역됐더라도, 실제 application 처리 시점을 모르면 비멱등 요청 재시도는 위험하다.

### 시나리오 4: gRPC 서버는 분명 status를 남겼는데 client는 trailer를 못 본다

중간 proxy reset, stream cancel race, connection close가 trailer 전달 전에 개입했을 수 있다.

## 코드로 보기

### H2 프레임 힌트 보기

```bash
nghttp -nv https://api.example.com
```

### gRPC 호출 관찰 감각

```bash
grpcurl -v api.example.com:443 list
```

### 관찰 포인트

```text
- RST_STREAM인가 GOAWAY인가 transport close인가
- GOAWAY error code와 last stream id는 무엇인가
- trailers가 왔는가, reset 전에 사라졌는가
- retry가 idempotency와 처리 시점을 고려하는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| graceful GOAWAY drain | in-flight stream을 보존하기 쉽다 | 구현과 관측이 더 복잡하다 | deploy, connection rotation |
| 즉시 stream reset | 자원 회수가 빠르다 | trailer 손실과 retry 혼선을 키운다 | client cancel, fast fail |
| 공격적 자동 retry | 일시적 reset을 흡수한다 | 중복 실행과 overload 증폭 위험이 있다 | 멱등 unary RPC |
| 보수적 retry | 정확성이 높다 | 일부 transient failure를 더 드러낸다 | 비멱등 또는 streaming 작업 |

핵심은 HTTP/2 종료 신호를 하나로 뭉개지 않고 **stream, connection, transport 세 층으로 나눠 해석하는 것**이다.

## 꼬리질문

> Q: `RST_STREAM`과 `GOAWAY`의 차이는 무엇인가요?
> 핵심: `RST_STREAM`은 특정 stream 하나, `GOAWAY`는 연결 전체의 새 stream 수용 중단 신호다.

> Q: `GOAWAY`를 받으면 항상 장애인가요?
> 핵심: 아니다. graceful drain이나 max age rotation일 수도 있다.

> Q: reset을 보면 바로 retry해도 되나요?
> 핵심: 아니다. error code뿐 아니라 idempotency와 application 처리 시점을 같이 봐야 한다.

## 한 줄 정리

HTTP/2와 gRPC 장애를 정확히 해석하려면 `RST_STREAM`, `GOAWAY`, TCP close를 구분하고, 특히 streaming 경로에서는 trailer 전달 여부와 retry 안전성까지 함께 봐야 한다.

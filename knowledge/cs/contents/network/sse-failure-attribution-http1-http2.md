# SSE Failure Attribution Across HTTP/1.1 and HTTP/2

> 한 줄 요약: 같은 SSE downstream abort도 edge access log에서는 `499`, HTTP/2 hop에서는 `RST_STREAM`, HTTP/1.1 write path에서는 chunked flush failure/`broken pipe`, read-side에서는 `EOF`로 갈라져 보인다. 이 표면들을 같은 incident의 다른 dialect로 묶지 못하면 blame과 replay 기준이 어긋난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
> - [SSE Last-Event-ID Replay Window](./sse-last-event-id-replay-window.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)
> - [FIN, RST, Half-Close, EOF](./fin-rst-half-close-eof-semantics.md)
> - [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
> - [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)

retrieval-anchor-keywords: sse failure attribution, sse abort attribution, downstream abort http1 http2, http/1.1 chunked flush failure, http/2 rst_stream cancel, 499 rst_stream eof crosswalk, sse client disconnect translation, protocol-layer abort attribution, client closed request sse, chunked broken pipe, stream reset cancel, downstream abort surface map

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

SSE disconnect를 볼 때 "클라이언트가 끊었다"는 사실 하나만 고정하고 나머지 표면은 계층별로 따로 읽어야 한다.

- edge access log의 `499`는 proxy가 본 결과다
- HTTP/2 hop의 `RST_STREAM`은 한 stream 취소 신호다
- HTTP/1.1 origin의 chunked flush failure는 이미 commit된 뒤 다음 write가 깨졌다는 뜻이다
- `EOF`는 보통 H1 socket read-side에서 peer `FIN`을 본 결과다

즉 같은 incident가 `499`, `RST_STREAM`, `broken pipe`, `EOF`를 동시에 남길 수 있다.  
이걸 서로 다른 장애로 세면 "누가 먼저 포기했는가"와 "마지막 정상 SSE event가 어디까지인가"를 둘 다 놓친다.

### Retrieval Anchors

- `sse failure attribution`
- `downstream abort http1 http2`
- `chunked flush failure`
- `499`
- `RST_STREAM`
- `EOF`
- `sse client disconnect translation`
- `protocol-layer abort attribution`

## 깊이 들어가기

### 1. 먼저 표면을 네 개로 쪼개야 한다

| 표면 | 보통 남는 위치 | 무엇을 뜻하나 | 자주 하는 오해 |
|---|---|---|---|
| `499` / `client closed request` | edge or proxy access log | 응답 완료 전에 downstream이 떠났다는 관찰 | origin app이 `499`를 반환했다 |
| `RST_STREAM` | downstream 또는 upstream H2 hop | 한 HTTP/2 stream이 취소되거나 reset됐다 | 연결 전체가 죽었다 |
| chunked flush failure / `broken pipe` / `EPIPE` | H1 origin write path, committed response 뒤 | 다음 SSE chunk를 더 못 보냈다 | first byte도 못 나갔다 |
| `EOF` | H1 socket read path | peer `FIN`으로 읽을 바이트가 끝났다 | app write failure와 같은 신호다 |

같은 abort라도 관찰 위치가 다르면 이름이 달라진다.  
진단의 핵심은 "어느 홉에서 어느 프로토콜 dialect로 보였는가"를 맞추는 것이다.

### 2. downstream이 HTTP/2이고 upstream이 HTTP/1.1이면 이렇게 갈라진다

가장 흔한 번역 예시는 아래다.

```text
browser/tab close
-> downstream H2 stream gets RST_STREAM(CANCEL or vendor-translated reset)
-> edge access log records 499
-> proxy stops reading or closes upstream H1 response leg
-> origin writes next SSE chunk
-> chunked flush fails with broken pipe / EPIPE / IOException
```

이때 중요한 점:

- H2 client 쪽에선 connection이 살아 있어도 stream 하나만 취소할 수 있다
- edge는 그 사실을 자기 access log dialect인 `499`로 남길 수 있다
- upstream H1 origin은 H2 frame을 모른 채 "다음 chunk flush가 깨졌다"로 본다

즉 H2의 `RST_STREAM`과 H1의 chunked flush failure는 서로 모순이 아니라 **같은 abort의 양쪽 번역본**일 수 있다.

### 3. downstream이 HTTP/1.1이고 upstream이 HTTP/2이면 반대로 보인다

이번에는 downstream leg가 socket close로 보이고 upstream leg가 stream reset으로 번역된다.

```text
browser closes H1 socket (FIN or RST)
-> edge read-side sees EOF or ECONNRESET
-> edge access log records 499
-> proxy cancels upstream H2 stream with RST_STREAM
-> origin or upstream proxy sees stream cancel callback / reset
```

여기서는:

- downstream H1 leg는 `EOF`나 `connection reset by peer`처럼 transport 냄새가 강하다
- upstream H2 leg는 socket close가 아니라 `RST_STREAM`으로 남을 수 있다
- 둘 다 "caller가 더 이상 이 SSE stream을 안 받는다"는 같은 사실의 다른 표현이다

그래서 "EOF와 RST_STREAM이 같이 보였으니 장애가 두 번 났다"라고 읽으면 안 된다.

### 4. `EOF`와 `broken pipe`는 같은 incident 안에서 연달아 나올 수 있다

HTTP/1.1 socket에서는 read-side와 write-side가 다른 이름을 남긴다.

- peer가 `FIN`을 보내면 먼저 read-side는 `EOF`를 볼 수 있다
- 그 사실을 앱이 즉시 반영하지 못한 채 write를 계속하면 나중에 `broken pipe`/`EPIPE`가 날 수 있다

SSE는 request body가 거의 끝난 뒤 response만 오래 쓰는 경우가 많아서, 앱 코드에는 `EOF`보다 write-side 실패가 더 눈에 띄기 쉽다.  
반대로 proxy나 container network thread는 더 앞서 `EOF`를 봤을 수 있다.

즉 `EOF`는 "읽는 쪽이 peer close를 감지한 시계"이고, chunked flush failure는 "쓰는 쪽이 늦게 그 사실을 알게 된 시계"다.

### 5. `499`는 protocol-neutral status가 아니라 proxy-local summary다

같은 SSE abort라도 아래 조합이 동시에 성립할 수 있다.

- edge access log: `499`
- downstream H2 frame log: `RST_STREAM`
- origin app log: `200` committed 후 chunked flush failure
- low-level H1 socket log: `EOF` 또는 `ECONNRESET`

`499` 하나로 app 성공/실패를 결정하면 안 되는 이유가 여기 있다.  
`499`는 "누가 먼저 떠났는가"에 대한 edge 요약이지, origin이 wire에 무엇을 썼는지 자체를 대체하지 않는다.

### 6. SSE에서는 마지막 write 시도보다 마지막 완성 이벤트가 더 중요하다

같은 abort가 protocol마다 다른 이름으로 남는다고 해서 replay 기준까지 달라지진 않는다.  
SSE에서 믿어야 하는 것은 **마지막 정상 완성 이벤트**다.

- H1 chunk 일부가 나가다 flush 실패할 수 있다
- H2 DATA frame 일부가 내려가도 event delimiter 전이면 브라우저가 적용하지 않을 수 있다
- edge는 `499`, upstream은 `RST_STREAM`, origin은 `broken pipe`를 남겨도 `Last-Event-ID`는 더 앞일 수 있다

따라서 attribution과 replay를 같이 보려면:

- protocol surface: `499`, `RST_STREAM`, `EOF`, chunked flush failure
- application surface: 마지막 정상 SSE event `id`

이 두 축을 따로 보존해야 한다.

### 7. 관측은 "어느 홉의 어느 프로토콜인가"를 같이 남겨야 한다

최소한 아래 질문이 한 incident 안에서 연결돼야 한다.

| 질문 | 왜 필요한가 |
|---|---|
| downstream leg가 H1인가 H2인가 | `EOF`와 `RST_STREAM` 중 어떤 dialect가 먼저 나올지 갈린다 |
| upstream leg가 H1인가 H2인가 | origin이 chunked flush failure를 볼지 stream reset을 볼지 갈린다 |
| edge가 `499`를 남긴 시각은 언제인가 | client abort의 기준 시계를 잡는다 |
| 마지막 정상 SSE event `id`는 무엇인가 | replay/gap 판단 기준이다 |
| producer stop 시각은 언제인가 | abort 이후 zombie work 크기를 본다 |

프로토콜 경계를 무시한 채 status code나 예외 이름만 대시보드에 올리면, 같은 abort가 네 개 장애처럼 부풀어 보인다.

## 실전 시나리오

### 시나리오 1: 브라우저는 H2, origin은 H1 SSE다

브라우저 탭 종료 후:

- edge는 `499`
- downstream frame log는 `RST_STREAM`
- origin Tomcat/Jetty/Undertow는 다음 chunk flush에서 `broken pipe`/`IOException`

이 셋은 서로 다른 원인이 아니라 같은 downstream abort일 수 있다.

### 시나리오 2: 브라우저는 H1, gateway 뒤 서비스는 H2다

다운스트림 close가 edge에선 `EOF`/reset으로 보이고, upstream 서비스에는 `RST_STREAM` cancel로 전달될 수 있다.  
이때 origin service가 socket close를 안 봤다고 해서 client abort가 없었던 것은 아니다.

### 시나리오 3: app은 `200` 성공을 남겼는데 운영은 `499`와 flush failure를 본다

SSE는 first byte commit 뒤에 실패할 수 있다.

- business logic는 성공
- edge delivery는 실패
- 마지막 정상 이벤트는 마지막 write 시도보다 앞선다

그래서 "200인데 왜 실패냐" 대신 "어느 이벤트까지 전달됐냐"를 물어야 한다.

### 시나리오 4: 한 incident에서 `EOF`와 `broken pipe`가 같이 찍힌다

proxy I/O thread가 peer `FIN`을 먼저 읽고 `EOF`를 기록한 뒤, 앱 writer가 늦게 같은 socket에 쓰면서 `broken pipe`를 낼 수 있다.  
read-side signal과 write-side signal을 분리하지 않으면 중복 장애처럼 보인다.

## 코드로 보기

### cross-protocol attribution 체크리스트

```text
1. edge access log에 499 / client closed request가 있었는가
2. downstream leg protocol이 H1인가 H2인가
3. downstream에서 EOF/FIN/RST를 봤는가, 아니면 RST_STREAM을 봤는가
4. upstream leg protocol이 H1인가 H2인가
5. upstream에서 chunked flush failure를 봤는가, 아니면 stream reset/cancel callback을 봤는가
6. 마지막 정상 SSE event id는 무엇인가
7. client abort 이후 producer가 언제 멈췄는가
```

### 타임라인 메모 예시

```text
t1 event id=40 flush success
t2 downstream H2 RST_STREAM or downstream H1 EOF/reset
t3 edge 499
t4 origin attempts event id=41 write
t5 H1 chunked flush failure or H2 stream cancel surfaces upstream
t6 producer stop

last safe replay point = event id 40
abort propagation lag = t6 - t2
```

### 현장 질문

```text
- 이 로그는 edge dialect인가, H2 frame dialect인가, H1 socket dialect인가
- connection close인가 stream cancel인가
- app가 본 실패는 first byte 전인가, commit 후 chunk write인가
- 마지막 정상 이벤트와 마지막 write 시도 이벤트가 다른가
- proxy가 프로토콜을 번역하면서 surface 이름이 바뀌었는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| protocol-neutral abort taxonomy 도입 | `499`, `RST_STREAM`, `EOF`, `broken pipe`를 한 incident로 묶기 쉽다 | 로그/메트릭 설계가 더 복잡하다 | proxy chain, mixed H1/H2 환경 |
| access log status만 본다 | 대시보드가 단순하다 | chunked flush failure와 last-event-id를 놓친다 | 권장되지 않음 |
| 마지막 정상 SSE event id를 별도 기록 | replay/gap 판단이 선명해진다 | 저장 비용과 코드가 든다 | long-lived SSE |
| H2 stream id와 H1 socket close를 따로 남긴다 | cross-protocol 번역이 쉬워진다 | 로깅 cardinality가 늘 수 있다 | streaming 장애 triage |

핵심은 abort를 protocol별 이름으로 나눠 세는 게 아니라, **같은 downstream abort가 어떤 홉에서 어떤 dialect로 보였는지**를 하나의 타임라인으로 복원하는 것이다.

## 꼬리질문

> Q: `499`와 `RST_STREAM`은 같은 건가요?
> 핵심: 아니다. `499`는 proxy access log 요약이고, `RST_STREAM`은 HTTP/2 stream-level cancel frame이다. 다만 같은 incident의 서로 다른 표면일 수 있다.

> Q: 왜 HTTP/1.1 SSE에선 `broken pipe`, HTTP/2에선 `RST_STREAM`으로 보이나요?
> 핵심: 프로토콜 경계가 다르기 때문이다. H1은 socket write failure로, H2는 stream reset으로 같은 abort를 드러낸다.

> Q: `EOF`가 보이면 정상 종료 아닌가요?
> 핵심: read-side에선 peer `FIN`을 본 것일 뿐이다. 같은 incident에서 write-side는 나중에 `broken pipe`로 실패할 수 있다.

> Q: 마지막 write 시도 event id를 replay 기준으로 써도 되나요?
> 핵심: 보통 아니다. partial chunk/data frame 때문에 브라우저가 실제로 처리한 마지막 정상 이벤트는 더 앞일 수 있다.

## 한 줄 정리

SSE abort attribution은 `499`, `RST_STREAM`, `EOF`, chunked flush failure를 서로 다른 장애로 읽는 문제가 아니라, mixed HTTP/1.1/HTTP/2 hop에서 같은 downstream abort가 어떻게 번역됐는지를 한 타임라인으로 묶는 문제다.

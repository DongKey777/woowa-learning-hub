# Access Log Correlation Recipes: Tomcat, Jetty, Undertow

> 한 줄 요약: Tomcat과 Jetty는 access log 자체에 `bytes-sent`, `duration`, `connection completion` 축이 거의 다 들어오지만, Undertow는 built-in disconnect field가 약하다. 그래서 세 container를 한 dashboard로 묶으려면 `status + bytes_sent + duration + disconnect_bucket` 정규화와 Undertow용 보조 breadcrumb가 핵심이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
> - [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)

retrieval-anchor-keywords: access log correlation recipe, tomcat jetty undertow access log, tomcat accesslog %X %F, jetty customrequestlog %O %X, undertow access log response time, undertow record request start time, bytes sent duration disconnect bucket, access log partial response attribution, late write access log, client abort bytes sent, access log 499 correlation, access log broken pipe correlation, response commit time tomcat, jetty keepalive request log, undertow request io access log join

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

disconnect incident를 access log로 묶을 때 status 하나만 보면 거의 항상 늦다.  
실전에서는 최소한 아래 4개 축을 고정해야 한다.

- `status`
- `bytes_sent`
- `duration`
- `disconnect_raw` 또는 `disconnect_bucket`

Tomcat과 Jetty는 built-in `%X`가 있어 access log 한 줄만으로도 "정상 완료 vs 응답 중 abort"를 꽤 잘 가른다.  
반면 Undertow는 built-in `%X` equivalent가 없어서 access log는 `status + bytes + duration` 축까지만 믿고, disconnect bucket은 `io.undertow.request.io` / `io.undertow.request` 또는 app breadcrumb와 join해서 보강해야 한다.

| 축 | Tomcat | Jetty | Undertow | 실전 해석 |
|---|---|---|---|---|
| bytes sent | `%b` / `%B` | `%{CLF}O` | `%b` / `%B` / `%{BYTES_SENT}` | partial delivery 여부의 1차 단서 |
| total duration | `%D`, `%{ms}T` | `%D`, `%{ms}T` | `%D`, `%{RESPONSE_TIME}` | 느린 취소인지 즉시 abort인지 구분 |
| commit / first-byte hint | `%F` | built-in 약함 | built-in 약함 | Tomcat은 pre-commit vs late-write 구분이 더 쉽다 |
| connection completion | `%X` | `%X` | built-in 없음 | Undertow는 보조 bucket 필요 |

### Retrieval Anchors

- `access log correlation recipe`
- `tomcat accesslog %X %F`
- `jetty customrequestlog %O %X`
- `undertow access log response time`
- `undertow record request start time`
- `bytes sent duration disconnect bucket`
- `late write access log`
- `access log 499 correlation`

## 깊이 들어가기

### 1. 먼저 raw field를 공통 schema로 정규화해야 한다

컨테이너마다 field 이름과 단위가 다르므로, access log 수집 단계에서 아래처럼 공통 컬럼으로 옮겨 두는 편이 안전하다.

| normalized field | Tomcat | Jetty | Undertow |
|---|---|---|---|
| `bytes_sent` | `%B` | `%O` | `%{BYTES_SENT}` |
| `duration_ms` | `%{ms}T` | `%{ms}T` | `%D` 또는 `%{RESPONSE_TIME}` |
| `disconnect_raw` | `%X` | `%X` | custom field 또는 별도 join |
| `commit_ms` | `%F` | 없음 | 없음 |
| `trace_id` | `%{traceId}r` 또는 header/request attr | `%{i,X-Request-Id}i` 등 | `%{i,traceparent}`, `%{r,traceId}` 등 |

여기서 핵심은:

- `bytes_sent=0` 자체를 abort로 확정하지 않는다
- `204`, `304`, `HEAD`, tiny error page는 정상적으로도 zero-byte shape가 나온다
- `disconnect_raw`가 없으면 status와 bytes만으로 abort를 판정하지 않는다

즉 access log는 **증거를 줄이는 도구가 아니라, phase를 좁히는 도구**로 써야 한다.

### 2. Tomcat은 `%X`와 `%F`가 같이 있어 disconnect phase를 가장 잘 나눈다

Tomcat `AccessLogValve` 쪽에서 disconnect correlation에 가장 유용한 필드는 아래다.

- `%B`
  bytes sent
- `%D` 또는 `%{ms}T`
  total duration
- `%F`
  response commit까지 걸린 시간
- `%X`
  response 완료 시점의 connection status

Tomcat `%X` 해석은 다음처럼 보면 된다.

| `%X` | 의미 | 운영 번역 |
|---|---|---|
| `X` | response 완료 전 connection aborted | 진짜 abort bucket 후보 |
| `+` | response 후 keep-alive 가능 | 정상 완료 + 연결 재사용 가능 |
| `-` | response 후 connection close | 정상 완료지만 연결은 닫힘 |

Tomcat의 장점은 `%F`가 있어 **commit 이전에 끊겼는지, first byte 이후 늦게 실패했는지**를 더 쉽게 좁힐 수 있다는 점이다.

| shape | 흔한 해석 |
|---|---|
| `%X=X`, `bytes_sent=0`, `%F`도 거의 0 | pre-commit abort 또는 upload/read-side incident 가능성 |
| `%X=X`, `bytes_sent>0`, `%F << total_duration` | first byte는 나갔고 나중에 partial write 또는 late disconnect |
| `%X=+/-`, `bytes_sent` 정상, edge는 `499` | origin은 완료했지만 downstream hop에서 늦게 끊긴 패턴 가능 |

Tomcat caveat도 있다.  
sendfile path를 쓰면 access log가 실제 wire에 끝까지 써진 byte 대신 sendfile thread로 넘긴 byte를 기록할 수 있으므로, 대용량 정적 파일 abort에서는 `bytes_sent`를 과신하면 안 된다.

### 3. Jetty는 `%O`, `%D`, `%X` 조합이 핵심이고 `%I` / `%S`가 bonus다

Jetty `CustomRequestLog`는 disconnect correlation에 필요한 필드를 거의 다 제공한다.

- `%{CLF}O`
  response bytes
- `%D` 또는 `%{ms}T`
  duration
- `%X`
  connection completion
- `%{CLF}I`
  request body bytes
- `%{CLF}S`
  request + response 총 bytes
- `%k`
  keepalive request count

Jetty `%X`의 뜻은 Tomcat과 동일하게 보면 된다.

| `%X` | 의미 | 운영 번역 |
|---|---|---|
| `X` | response 완료 전 abort | partial write 또는 mid-response cancel |
| `+` | keep-alive 가능 | 정상 완료 |
| `-` | response 후 close | 정상 완료 + close policy |

Jetty의 장점은 request-side bytes인 `%I`가 있어 upload/read-side incident를 더 직접적으로 볼 수 있다는 점이다.

| shape | 흔한 해석 |
|---|---|
| `%X=X`, `%O=0`, `%I`도 작음 | early abort 또는 header/body 초반 disconnect |
| `%X=X`, `%O>0` | 응답 일부를 보낸 뒤 downstream abort |
| `%X=+/-`, `%O` 정상, `org.eclipse.jetty.io` quiet EOF만 존재 | 실제 app regression보다 normal client churn 가능성 |
| `%X=X`, `%O=0`, app은 `MultipartException` | controller 전 request-read/multipart path 가능성 |

즉 Jetty는 access log만으로도 upload/read-side와 response-write-side를 Tomcat보다 크게 손해 보지 않고 읽을 수 있다.

### 4. Undertow는 `bytes + duration`은 좋지만 built-in disconnect field가 비어 있다

Undertow `AccessLogHandler`에서 바로 쓸 수 있는 필드는 아래가 핵심이다.

- `%{BYTES_SENT}`
  response bytes
- `%D` 또는 `%{RESPONSE_TIME}`
  duration
- `%{RESPONSE_TIME_MICROS}`, `%{RESPONSE_TIME_NANOS}`
  더 세밀한 단위
- `%{i,Header-Name}`, `%{o,Header-Name}`, `%{r,attr}`
  join key / custom enrichment

Undertow 함정은 두 가지다.

- built-in `%X`가 없어 normal close와 abort를 access log 한 줄만으로는 완벽히 못 가른다
- response time 계열 필드는 `RECORD_REQUEST_START_TIME`가 켜져 있어야 의미가 생긴다

그래서 Undertow에선 access log만으로 `disconnect_bucket`를 만들지 말고 아래 둘 중 하나를 같이 둬야 한다.

- `io.undertow.request.io` / `io.undertow.request` logger와 time-window join
- servlet request attribute나 request header를 access log에 넣는 custom bucket

실전 bucket은 보통 아래처럼 둔다.

| bucket | 조건 |
|---|---|
| `request_read_abort` | `io.undertow.request.io` 또는 read-side `IOException`, `bytes_sent=0`, 짧은 duration |
| `late_write_abort` | `UT010029`, `Stream is closed`, `bytes_sent>0` |
| `completed_no_abort_signal` | abort logger/breadcrumb 없음 |

Undertow에서 "access log에 abort field가 없으니 status로 대신 보자"는 접근은 위험하다.  
`500`, `400`, `499` 번역이 proxy hop에서 이미 섞이기 쉽기 때문이다.

### 5. 세 container를 한 dashboard로 묶을 때는 raw code보다 bucket 규칙을 먼저 고정한다

가장 실용적인 normalized bucket은 보통 아래 네 가지다.

| normalized bucket | Tomcat | Jetty | Undertow |
|---|---|---|---|
| `completed_keepalive` | `%X=+` | `%X=+` | built-in 없음, 필요하면 keep-alive policy와 무-abort signal로 infer |
| `completed_close` | `%X=-` | `%X=-` | built-in 없음, 필요하면 `Connection: close`와 무-abort signal로 infer |
| `pre_commit_abort` | `%X=X` and `bytes_sent=0` | `%X=X` and `%O=0` | read-side abort breadcrumb + `bytes_sent=0` |
| `partial_write_abort` | `%X=X` and `bytes_sent>0` | `%X=X` and `%O>0` | late-write breadcrumb + `bytes_sent>0` |

핵심은 vendor raw code를 그대로 대시보드 축으로 쓰지 않는 것이다.

- Tomcat/Jetty `%X`는 동일 문자를 써도 app-side exception dialect는 다르다
- Undertow는 동일 축이 아예 비어 있다
- 따라서 dashboard 축은 `disconnect_bucket`, 원시 필드는 `disconnect_raw`로 분리하는 편이 안전하다

### 6. `bytes_sent`와 `duration`을 같이 봐야 정상 취소와 낭비 work가 갈린다

disconnect incident는 보통 아래 3개 shape로 먼저 정리하면 된다.

| shape | 읽는 법 | 다음 확인 |
|---|---|---|
| `bytes_sent=0`, short duration, abort bucket | pre-commit reject, request-read abort, upload truncation 후보 | multipart/read-side log, edge buffering, auth reject boundary |
| `bytes_sent>0`, long duration, abort bucket | business work나 first byte 이후 늦게 끊긴 패턴 | late write, `AsyncRequestNotUsableException`, partial flush failure |
| `bytes_sent` 정상, origin complete bucket, edge `499` | origin은 끝났고 downstream cancel만 늦게 반영된 패턴 | proxy chain cancel propagation, zombie work |

즉 `bytes_sent`는 "얼마나 나갔는가", `duration`은 "얼마나 늦게 알았는가", `disconnect_bucket`은 "어느 phase에서 끊겼는가"를 담당한다.

### 7. access log만으로 끝내지 말고 edge code와 app breadcrumb를 같이 묶어야 한다

실전 incident triage는 보통 아래처럼 본다.

| edge / app / origin 조합 | 해석 |
|---|---|
| edge `499` + Tomcat/Jetty `%X=X` + `bytes_sent>0` | downstream이 응답 일부를 받은 뒤 떠난 partial response 가능성 높음 |
| edge `499` + origin `%X=+/-` | origin completion 뒤 proxy/downstream 쪽에서만 cancel이 관측된 것일 수 있음 |
| Undertow `bytes_sent=0` + `io.undertow.request.io` 증가 | request-read/upload abort 후보 |
| Undertow `bytes_sent>0` + `UT010029` + Spring async tail | committed response 뒤 late write 가능성 높음 |

access log는 단독 진실이 아니라, **container log와 proxy log를 맞물리게 하는 spine**에 가깝다.

## 실전 시나리오

### 시나리오 1: Tomcat download API에서 `200`도 보이고 edge는 `499`도 많다

먼저 Tomcat access log에서 `%X`를 본다.

- `%X=X`, `bytes_sent>0`
  partial write abort 가능성
- `%X=+/-`, `bytes_sent` 정상
  origin completion 뒤 downstream cancel 가능성

같은 `200`이라도 `%X`가 다르면 같은 incident가 아니다.

### 시나리오 2: Jetty SSE에서 `EofException: Closed`는 noisy한데 실제 partial delivery가 있었는지 모르겠다

Jetty access log에서 `%X`와 `%O`를 같이 본다.

- `%X=X`, `%O>0`
  일부 이벤트는 나갔다
- `%X=X`, `%O=0`
  first byte 전 cancel 가능성
- `%X=+/-`
  quiet EOF log만으로는 partial delivery를 단정하기 어렵다

### 시나리오 3: Undertow는 access log에 status, bytes, duration만 있고 abort 구분이 안 된다

이 경우 access log만으로 bucket을 만들지 말고:

- `io.undertow.request.io`
  read-side abort bucket
- `io.undertow.request`
  request handling / late-write bucket
- `DisconnectedClientHelper` breadcrumb
  app-side disconnect bucket

중 하나를 access log와 join해야 한다.

### 시나리오 4: dashboard에서 `%X=-`를 abort로 세고 있었다

Tomcat/Jetty에선 잘못된 분류다.  
`-`는 "response 후 connection close"이지 "mid-response abort"가 아니다.

### 시나리오 5: `bytes_sent=0` incident를 전부 upload abort로 보고 있었다

그 역시 위험하다.

- `204`, `304`, `HEAD`
- tiny empty error response
- pre-commit auth reject

도 같은 shape를 만들 수 있다.  
반드시 `status`, `method`, `disconnect bucket`을 같이 본다.

## 코드로 보기

### 컨테이너별 권장 pattern 예시

```text
Tomcat
%{begin:msec}t %{end:msec}t %a "%r" %s %B %{ms}T %F %X %{traceId}r %{c}L

Jetty
%{yyyy-MM-dd'T'HH:mm:ss.SSS|GMT}t %{client}a "%r" %s %{CLF}O %{ms}T %X %{i,X-Request-Id}i %k

Undertow
%t %a "%r" %s %{BYTES_SENT} %{RESPONSE_TIME} %{i,traceparent} %{r,disconnectBucket}
```

Undertow 예시는 `disconnectBucket`을 request attribute로 심는 전제를 둔다.  
그게 없다면 access log에는 `status + bytes + duration + trace id`까지만 두고, abort bucket은 logger join으로 따로 만든다.

### 공통 정규화 규칙 예시

```text
if container in {tomcat, jetty}:
  disconnect_raw = %X
  disconnect_bucket =
    + -> completed_keepalive
    - -> completed_close
    X and bytes_sent == 0 -> pre_commit_abort
    X and bytes_sent  > 0 -> partial_write_abort

if container == undertow:
  disconnect_raw = request_attr.disconnectBucket or null
  disconnect_bucket =
    request_read_abort -> pre_commit_abort
    late_write_abort  -> partial_write_abort
    null              -> completed_or_unknown
```

### 로그 리뷰 체크리스트

```text
1. status보다 먼저 bytes_sent / duration / disconnect_raw를 함께 본다
2. zero-byte shape면 HEAD/204/304를 먼저 제외한다
3. Tomcat은 %F와 total duration 차이로 first-byte 후 abort인지 본다
4. Jetty는 %O와 %X를 같이 보고 quiet EOF noise와 partial write를 분리한다
5. Undertow는 io.undertow.request.io / io.undertow.request 또는 app breadcrumb를 반드시 join한다
6. edge 499와 origin access log가 같은 종료 주체를 말하는지 다시 확인한다
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| Tomcat/Jetty raw `%X`를 그대로 사용 | 구현이 단순하다 | vendor별 의미를 팀이 계속 기억해야 한다 | 단일 container fleet |
| `disconnect_bucket`로 정규화 | cross-container dashboard가 쉬워진다 | ingest 규칙과 문서화가 더 필요하다 | mixed container fleet |
| Undertow를 status/bytes만으로 해석 | 추가 구현이 없다 | abort와 normal close를 자주 오판한다 | 권장하지 않음 |
| commit/first-byte 힌트까지 저장 | pre-commit vs late-write 분리가 좋아진다 | Tomcat 외 container는 추가 enrichment가 필요하다 | streaming/download incident가 잦을 때 |

## 꼬리질문

> Q: Tomcat과 Jetty의 `%X=-`는 abort인가요?
> 핵심: 아니다. response는 완료됐고 connection만 닫히는 것이다.

> Q: Undertow는 왜 `%X` 같은 built-in field가 없나요?
> 핵심: access log가 `bytes/duration/status` 축은 주지만 connection completion을 Tomcat/Jetty만큼 직접 표준화해 주지 않기 때문이다. 그래서 logger/breadcrumb join이 필요하다.

> Q: `bytes_sent=0`이면 무조건 first byte 전에 끊긴 건가요?
> 핵심: 아니다. HEAD/204/304, tiny empty response, pre-commit reject도 같은 shape를 만들 수 있다.

> Q: edge `499`가 있으면 origin도 반드시 abort bucket이어야 하나요?
> 핵심: 아니다. origin은 완료했고 proxy/downstream hop만 늦게 cancel을 관측했을 수도 있다.

## 한 줄 정리

Tomcat, Jetty, Undertow access log를 함께 쓰려면 raw vendor field를 그대로 비교하지 말고, **`bytes_sent + duration + disconnect_bucket`으로 먼저 정규화한 뒤 edge/app/container 로그를 조인**해야 incident phase가 제대로 보인다.

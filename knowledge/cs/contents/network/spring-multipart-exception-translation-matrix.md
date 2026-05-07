---
schema_version: 3
title: "Spring Multipart Exception Translation Matrix"
concept_id: network/spring-multipart-exception-translation-matrix
canonical: true
category: network
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- multipart-upload
- spring-exception
- upload-attribution
aliases:
- Spring multipart exception translation matrix
- MultipartException vs MaxUploadSizeExceededException
- MissingServletRequestPartException
- Failed to parse multipart servlet request
- request.getParts exception mapping
- multipart nested cause matrix
- max upload size exceeded 413
symptoms:
- MultipartException 예외 이름만 보고 network 문제 또는 server bug로 바로 결론낸다
- nested cause, container vendor, final status owner, multipart phase를 함께 남기지 않는다
- MaxUploadSizeExceededException 413이 app에서 만들어졌는지 edge/proxy limit인지 구분하지 못한다
- MissingServletRequestPartException을 container read abort와 같은 bucket으로 본다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/multipart-parsing-vs-auth-reject-boundary
- network/proxy-to-container-upload-cleanup-matrix
next_docs:
- network/servlet-container-abort-surface-map-tomcat-jetty-undertow
- network/container-specific-disconnect-logging-recipes-spring-boot
- spring/multipart-upload-request-pipeline
- network/network-spring-request-lifecycle-timeout-disconnect-bridge
linked_paths:
- contents/network/multipart-parsing-vs-auth-reject-boundary.md
- contents/network/proxy-to-container-upload-cleanup-matrix.md
- contents/network/servlet-container-abort-surface-map-tomcat-jetty-undertow.md
- contents/network/container-specific-disconnect-logging-recipes-spring-boot.md
- contents/network/gateway-buffering-vs-spring-early-reject.md
- contents/network/http-request-body-drain-early-reject-keepalive-reuse.md
- contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md
- contents/spring/spring-multipart-upload-request-pipeline.md
confusable_with:
- network/multipart-parsing-vs-auth-reject-boundary
- network/proxy-to-container-upload-cleanup-matrix
- network/servlet-container-abort-surface-map-tomcat-jetty-undertow
- spring/multipart-upload-request-pipeline
forbidden_neighbors: []
expected_queries:
- "Spring MultipartException과 MaxUploadSizeExceededException 차이를 어떻게 봐?"
- "Failed to parse multipart servlet request의 nested cause를 왜 남겨야 해?"
- "MissingServletRequestPartException은 multipart parser abort와 어떻게 다른 bucket이야?"
- "multipart upload 413이 app limit인지 proxy limit인지 어떻게 구분해?"
- "Tomcat ClientAbortException Jetty EofException Undertow multipart IOException을 매트릭스로 정리해줘"
contextual_chunk_prefix: |
  이 문서는 Spring multipart upload에서 MultipartException,
  MaxUploadSizeExceededException, MissingServletRequestPartException, nested
  container cause, status owner, bytes/cleanup observability를 연결하는 advanced
  bridge다.
---
# Spring Multipart Exception Translation Matrix

> 한 줄 요약: Spring에서 보이는 `MultipartException`, `MaxUploadSizeExceededException`, `MissingServletRequestPartException`는 root cause가 아니라 `request.getParts()`/binding 단계의 번역본이다. 업로드 장애를 빠르게 풀려면 Spring top-level symptom, nested container cause, 최종 status owner, bytes/cleanup observability를 한 매트릭스로 같이 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md)
> - [Proxy-to-Container Upload Cleanup Matrix](./proxy-to-container-upload-cleanup-matrix.md)
> - [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
> - [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
> - [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
> - [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [Spring Multipart Upload Request Pipeline](../spring/spring-multipart-upload-request-pipeline.md)

retrieval-anchor-keywords: spring multipart exception translation matrix, multipart exception matrix, MultipartException vs MaxUploadSizeExceededException, MissingServletRequestPartException 400, Failed to parse multipart servlet request, Could not access multipart servlet request, StandardMultipartHttpServletRequest handleParseFailure, request.getParts exception mapping, multipart nested cause matrix, upload troubleshooting from spring symptom, multipart observability fields, max upload size exceeded 413, bad multipart 400, undertow connection terminated parsing multipart data, tomcat clientabortexception multipart, jetty eofexception multipart

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

multipart incident에서 Spring 예외 이름만 보고 끝내면 거의 항상 원인 추적이 뒤집힌다.  
실전에서는 아래 다섯 축을 같이 고정해야 한다.

1. **Spring top-level class가 무엇인가**  
   `MultipartException`, `MaxUploadSizeExceededException`, `MissingServletRequestPartException`은 서로 다른 phase를 뜻한다.
2. **nested cause가 무엇인가**  
   Tomcat `ClientAbortException`, Jetty `EofException`, Undertow `IOException`, `IllegalStateException`이 같은 wrapper 안에서 갈라진다.
3. **누가 최종 HTTP status를 만들었는가**  
   Spring `ErrorResponse`, custom `@ControllerAdvice`, servlet container, proxy는 각자 다른 status를 만들 수 있다.
4. **multipart phase가 어디였는가**  
   eager `resolveMultipart()`, lazy first access, `@RequestPart` binding, cleanup access는 서로 다른 의미다.
5. **bytes와 cleanup ownership이 어디 있었는가**  
   edge가 2GB를 받고 app은 0B만 읽은 incident와, app/container가 실제로 body를 읽다 끊긴 incident는 대응이 다르다.

### Spring symptom에서 outward로 읽는 1차 매트릭스

| Spring top-level symptom | Spring에서 생성되는 지점 | 기본 status 성향 | 가장 먼저 의심할 root cause | 먼저 남겨야 할 observability |
|---|---|---|---|---|
| `MultipartException("Failed to parse multipart servlet request")` | `StandardMultipartHttpServletRequest.handleParseFailure()`가 `request.getParts()` 실패를 generic wrapper로 감쌈 | built-in `ErrorResponse`가 없어서 미처리 시 app 기준 `500`으로 가기 쉽다. 다만 container/proxy 바깥 로그는 `400/408/499`를 따로 보일 수 있다 | truncated boundary, client abort, read-side EOF/reset, vendor-specific `bad multipart`, late lazy parse failure | `spring_exception`, `nested_cause_class`, `nested_cause_message`, `multipart_phase`, `controller_entered`, `http_status_final`, `bytes_received_edge`, `bytes_consumed_app`, `unread_body_cleanup` |
| `MaxUploadSizeExceededException` | 같은 parse failure path에서 size/length/big/large 단서가 감지되거나 container size exception이 올라옴 | Spring `ErrorResponse` 기준 `413` | request/file size limit 초과, container pre-dispatch size reject, parser-level size guard, large upload 뒤 cleanup tail | `spring_exception`, `max_upload_size_config`, `content_length`, `bytes_received_edge`, `bytes_consumed_app`, `status_owner`, `connection_reused`, `unread_body_cleanup` |
| `MissingServletRequestPartException` | multipart resolution 뒤 `@RequestPart` / binding이 required part를 찾지 못함 | Spring `ErrorResponse` 기준 `400` | part 이름 불일치, 잘못된 `Content-Type`, multipart resolver 미작동, 클라이언트가 part를 생략함. 보통 container read abort 자체는 아니다 | `request_part_name`, `content_type`, `is_multipart_request`, `parsed_part_names`, `handler_signature`, `multipart_resolved` |

핵심은 "`MultipartException`이 떴다"가 곧 network 문제라는 뜻도 아니고, "`MissingServletRequestPartException`이니 client contract 문제"라는 뜻도 아니라는 점이다.  
**예외 이름은 출발점이고, nested cause와 status owner가 실제 번역 키**다.

### Retrieval Anchors

- `spring multipart exception translation matrix`
- `MultipartException vs MaxUploadSizeExceededException`
- `Failed to parse multipart servlet request`
- `MissingServletRequestPartException 400`
- `request.getParts exception mapping`
- `multipart observability fields`
- `bad multipart 400`

## 깊이 들어가기

### 1. standard servlet multipart path는 먼저 wrapper를 정하고 그다음 예외 이름을 정한다

`StandardServletMultipartResolver.resolveMultipart()`는 `StandardMultipartHttpServletRequest`를 만들고, eager mode라면 생성자 안에서 바로 `parseRequest()`를 실행한다.  
즉 controller 미진입이어도 아래 path가 이미 돈다.

```text
request
-> StandardServletMultipartResolver.resolveMultipart()
-> StandardMultipartHttpServletRequest(...)
-> request.getParts()
-> handleParseFailure(...) if needed
```

여기서 중요한 translation rule이 두 개다.

- size/length/big/large 계열 message면 `MaxUploadSizeExceededException`
- 아니면 `MultipartException("Failed to parse multipart servlet request")`

즉 Spring은 vendor-neutral top-level class를 주지만, **실제 분류 정밀도는 nested cause와 message를 남겨 놨는지에 달린다**.

### 2. `MultipartException`은 status보다 phase를 먼저 읽어야 한다

generic `MultipartException`은 `ErrorResponse`가 아니다.  
그래서 custom `@ExceptionHandler`가 없으면 app-level final status는 `500`로 굳어지기 쉽다.

하지만 이 `500`이 곧 server bug라는 뜻은 아니다.

- Tomcat nested cause가 `ClientAbortException`이면 client upload abort일 수 있다
- Jetty nested cause가 `EofException` 또는 `ServletException(400 bad multipart)`면 malformed/truncated multipart일 수 있다
- Undertow nested cause가 `IOException("Connection terminated parsing multipart data")`면 parser가 mid-stream EOF/reset을 본 것이다

즉 `MultipartException`은 "Spring이 multipart parse를 통과시키지 못했다"는 의미이지, **status semantics를 이미 확정한 예외는 아니다**.

### 3. `MaxUploadSizeExceededException`은 Spring 쪽 status는 `413`로 안정적이지만 ownership은 여전히 갈린다

`MaxUploadSizeExceededException`은 `MultipartException`의 subclass지만 동시에 `ErrorResponse`다.  
그래서 Spring 기본 해석은 비교적 명확하다.

- app 쪽 최종 status는 기본적으로 `413`
- `ProblemDetail`도 `PAYLOAD_TOO_LARGE` 기준으로 만들어진다

하지만 ownership은 여전히 갈린다.

| `MaxUploadSizeExceededException`이 보여도 실제 ownership이 갈리는 지점 | 해석 |
|---|---|
| edge가 origin에 body를 거의 안 넘겼다 | gateway local limit가 먼저였을 수 있다. origin 예외가 없다면 app blame 대상이 아니다 |
| origin까지 body 일부가 들어왔다 | container/parser size limit가 실제 생산자일 수 있다 |
| app는 `413`, edge는 긴 upload 뒤 `499` | size reject 뒤 cleanup tail에서 client가 떠난 것이다 |
| same endpoint에서 어떤 요청은 짧은 `413`, 어떤 요청은 긴 `413` | `Expect: 100-continue`, buffering, content-length 사전검사 여부가 달랐을 수 있다 |

즉 `413` 자체보다 **누가 그 `413`의 tail cost를 감당했는가**를 같이 봐야 한다.

### 4. `MissingServletRequestPartException`은 multipart 파싱 실패와 다른 bucket으로 분리해야 한다

이 예외는 보통 아래 상황에서 나온다.

- 요청이 multipart처럼 보였지만 required part 이름이 다르다
- multipart resolver가 아예 작동하지 않았다
- `Content-Type`이 잘못되어 multipart로 인식되지 않았다
- parse는 되었지만 요청에 기대한 part가 실제로 없다

즉 이 예외를 `ClientAbortException` 계열과 같은 bucket으로 넣으면 안 된다.  
기본 status도 `400`이고, triage 질문도 다르다.

- 어떤 part 이름을 기대했는가
- 실제 parsed part 이름은 무엇이었는가
- multipart resolution은 성공했는가
- handler signature와 client form field 이름이 맞는가

여기서 핵심은 `MissingServletRequestPartException`이 **대개 transport abort보다 contract/binding mismatch에 가깝다**는 점이다.

### 5. nested cause별 container translation을 따로 보면 triage가 빨라진다

| nested cause / message | Spring에서 흔한 top-level | status 해석 포인트 | container 쪽 뜻 |
|---|---|---|---|
| `ClientAbortException` | 대개 generic `MultipartException` | Spring status는 `500`로 보일 수 있어도 실제로는 client abort/read-side disconnect bucket일 수 있다 | Tomcat이 request read-side `IOException`을 vendor type으로 감싼 것 |
| `EOFException` | generic `MultipartException` 또는 `MaxUploadSizeExceededException` 직전 raw signal | app `500`과 edge `499`가 같이 보일 수 있다 | body truncation 또는 premature EOF |
| `EofException` | generic `MultipartException` | Jetty quiet EOF / truncated multipart 가능성 | Jetty request input 또는 output close를 전용 타입으로 surface |
| `ServletException(400 bad multipart)` | generic `MultipartException` | 바깥 status는 custom advice가 없으면 `500`일 수 있어도 nested cause는 이미 malformed multipart 쪽을 가리킨다 | Jetty가 non-IO multipart parse failure를 `400` envelope로 감싼 것 |
| `IOException("Connection terminated parsing multipart data")` | generic `MultipartException` | app `500`, edge `499/400` 혼합 가능 | Undertow parser가 multipart parse 중 mid-stream EOF/reset을 직접 감지 |
| `IllegalStateException` with request/file too large cause | 흔히 `MaxUploadSizeExceededException` | 기본 `413` | Undertow size guard 또는 servlet size limit가 wrapper 안쪽에서 state error로 번역됨 |
| size/limit/large message only | `MaxUploadSizeExceededException` | 기본 `413`, 다만 실제 max size 값은 별도 설정에서 복원해야 한다 | Spring이 message heuristic으로 size bucket으로 승격한 것 |

이 표의 요점은 간단하다.  
**top-level class만 로그에 남기면 triage 품질이 떨어지고, nested cause simple name 하나만 추가해도 분류 정확도가 크게 올라간다.**

### 6. status code는 "예외가 무엇이냐"보다 "누가 응답 owner냐"로 읽어야 한다

| 최종 status | Spring symptom 기준 1차 질문 | 흔한 해석 |
|---|---|---|
| `413` | top-level이 `MaxUploadSizeExceededException`인가 | Spring `ErrorResponse` 또는 custom advice가 size limit를 응답한 것이다 |
| `400` | top-level이 `MissingServletRequestPartException`인가, 아니면 generic `MultipartException` 안쪽 cause가 `bad multipart`인가 | part contract mismatch 또는 malformed multipart bucket이다 |
| `500` | generic `MultipartException`이 unhandled인가 | status는 app default error path일 뿐이고, root cause는 client abort/parse failure일 수 있다 |
| `499` / `460` / vendor edge code | origin에 이미 `MultipartException`/`413` 흔적이 있는가 | proxy가 cleanup/disconnect tail을 자기 dialect로 다시 번역한 것이다 |

그래서 upload incident에서 "왜 `500`이냐"라는 질문은 반만 맞다.  
더 정확한 질문은 **"이 status를 누가 만들었고, Spring symptom은 그 전에 어떤 phase를 가리켰나"**다.

### 7. observability는 공통 envelope와 exception-specific fields를 둘 다 남겨야 한다

아래 필드는 multipart triage에서 거의 항상 유용하다.

| 필드 | 왜 필요한가 |
|---|---|
| `spring.multipart.exception` | top-level symptom을 한 bucket으로 모은다 |
| `spring.multipart.message` | generic `MultipartException`과 late access path를 구분한다 |
| `spring.multipart.nested_cause_class` | vendor-neutral wrapper를 다시 vendor-specific 원인으로 푼다 |
| `spring.multipart.nested_cause_message` | size/boundary/EOF 단서를 복원한다 |
| `spring.multipart.phase` = `resolveMultipart|lazy-first-access|binding|part-access|cleanup|unknown` | 같은 예외도 어느 phase에서 났는지 분리한다 |
| `http.status.final` | 실제 client/edge가 본 status를 남긴다 |
| `http.status.owner` = `spring-errorresponse|spring-default-error|container|proxy|custom-advice|unknown` | 예외와 status를 분리한다 |
| `servlet.container` | Tomcat/Jetty/Undertow 차이를 남긴다 |
| `upload.bytes.received_edge` / `upload.bytes.forwarded_upstream` / `upload.bytes.consumed_app` | body ownership을 분리한다 |
| `upload.unread_body_cleanup` | reject 뒤 drain/swallow/close/non-persistent를 구분한다 |
| `multipart.request_part_name` | `MissingServletRequestPartException` triage의 핵심 키다 |
| `multipart.parsed_part_names` | 실제로 무엇이 들어왔는지 확인한다 |
| `multipart.max_file_size` / `multipart.max_request_size` | `413`에서 설정과 incident를 바로 비교한다 |
| `http.expect_continue_present` | upload 낭비 ownership을 분리한다 |

실무에서는 이 필드들이 "에러 로그용"이 아니라 **Spring symptom을 edge/container timeline과 join하기 위한 join key**다.

### 8. 가장 실용적인 triage 순서는 예외 클래스보다도 짧다

1. top-level이 `MaxUploadSizeExceededException`, generic `MultipartException`, `MissingServletRequestPartException` 중 무엇인지 확인한다
2. nested cause simple name과 message를 본다
3. 최종 status와 status owner를 분리한다
4. multipart phase가 eager parse인지 lazy first access인지 binding인지 확인한다
5. edge/app bytes와 cleanup mode를 확인한다

이 다섯 단계면 "`Spring multipart exception`"에서 "`container / proxy / client contract 중 어디로 먼저 가야 하나`"가 거의 정해진다.

## 실전 시나리오

### 시나리오 1: app log는 `MultipartException`, access log는 `500`, edge는 `499`

이 조합이면 먼저 "Spring bug"로 보지 말고 아래를 확인한다.

- nested cause가 `ClientAbortException`, `EofException`, Undertow `IOException` 계열인가
- edge upload bytes가 큰가
- `unread_body_cleanup`이 drain/swallow/close 중 무엇이었나

즉 app `500`은 wrapper의 status일 뿐이고, incident 본체는 cleanup tail 위의 disconnect일 수 있다.

### 시나리오 2: `MaxUploadSizeExceededException`인데 어떤 요청은 바로 `413`, 어떤 요청은 오래 걸린 뒤 `413`

흔한 분기점:

- `Content-Length`로 pre-dispatch limit가 가능했던 요청
- 실제 body를 조금 읽은 뒤 parser limit가 걸린 요청
- gateway buffering이 body cost를 먼저 떠안은 요청

같은 `413`이어도 reject phase와 ownership이 다르다.

### 시나리오 3: `MissingServletRequestPartException`인데 업로드 클라이언트는 "파일은 보냈다"고 주장한다

먼저 container abort 로그를 보기 전에 아래를 본다.

- required part 이름과 실제 form field 이름이 같은가
- `Content-Type`이 정말 `multipart/form-data`인가
- parsed part 이름 목록에 기대한 part가 있는가
- reverse proxy가 body를 건드리며 field를 잃어버릴 구조인가

보통 이 bucket은 transport보다 contract mismatch를 먼저 확인하는 편이 맞다.

### 시나리오 4: `MultipartException`과 `413`이 동시에 보여서 size limit인지 read abort인지 헷갈린다

generic `MultipartException` 안쪽 message에 `size`, `large`, `limit`가 없고 nested cause가 EOF/reset 계열이면 size limit보다 read abort 쪽이다.  
반대로 top-level이 `MaxUploadSizeExceededException`이면 먼저 size bucket으로 보고, 그다음 cleanup tail만 분리하면 된다.

## 코드로 보기

### multipart incident에 남길 최소 envelope

```text
spring.multipart.exception=MultipartException|MaxUploadSizeExceededException|MissingServletRequestPartException
spring.multipart.message=...
spring.multipart.nested_cause_class=...
spring.multipart.nested_cause_message=...
spring.multipart.phase=resolveMultipart|lazy-first-access|binding|part-access|cleanup|unknown
http.status.final=...
http.status.owner=spring-errorresponse|spring-default-error|container|proxy|custom-advice|unknown
servlet.container=tomcat|jetty|undertow|unknown
upload.bytes.received_edge=...
upload.bytes.forwarded_upstream=...
upload.bytes.consumed_app=...
upload.unread_body_cleanup=swallow|consumeAvailable|drain|close|terminate|non-persistent|unknown
multipart.request_part_name=...
multipart.parsed_part_names=...
multipart.max_file_size=...
multipart.max_request_size=...
http.expect_continue_present=true|false
```

### symptom-first triage 메모

```text
if spring.multipart.exception == "MaxUploadSizeExceededException":
  start with configured limits, 413 owner, and cleanup tail

if spring.multipart.exception == "MultipartException":
  ignore final 500 for a moment
  classify by nested cause: client abort vs bad multipart vs size-like message

if spring.multipart.exception == "MissingServletRequestPartException":
  start with part name, content type, and parsed part inventory

if edge_status in {499, 460} and origin already logged multipart exception:
  treat edge status as proxy translation of cleanup/disconnect tail
```

### 로그 라벨 예시

```text
event=multipart_failure
spring_exception=MultipartException
nested_cause=org.eclipse.jetty.io.EofException
multipart_phase=resolveMultipart
http_status_final=500
http_status_owner=spring-default-error
servlet_container=jetty
edge_status=499
upload_bytes_received_edge=2147483648
upload_bytes_consumed_app=65536
unread_body_cleanup=non-persistent
```

이 정도만 있어도 "`Jetty EOF가 Spring generic wrapper로 뭉개졌고, edge는 cleanup tail을 499로 번역했다`"까지 바로 복원된다.

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 유리한가 |
|---|---|---|---|
| top-level Spring 예외만 집계 | 대시보드가 단순하다 | vendor cause와 status owner가 사라져 triage가 느려진다 | 초기 에러율 모니터링 |
| nested cause와 phase까지 남김 | root cause 분류 정확도가 높다 | 로그/metric cardinality 관리가 필요하다 | upload incident 대응, container migration |
| 모든 multipart error를 `400/413`로 통일 | 외부 API contract가 단순하다 | client abort와 parser bug가 같은 bucket으로 뭉개진다 | public API error envelope 단순화가 더 중요할 때 |
| status보다 bytes/cleanup 필드를 우선 | upload ownership을 정확히 본다 | app-only 로그만 보는 팀에는 낯설다 | gateway/proxy/app joint incident 대응 |

핵심 trade-off는 **예외 이름을 단순화할수록 triage 비용이 나중에 network/container 쪽으로 밀린다**는 점이다.

## 꼬리질문

> Q: 왜 `MultipartException`인데 최종 status는 `500`인가요?
> 의도: Spring wrapper와 HTTP status owner를 분리해서 읽는지 확인
> 핵심: generic `MultipartException`은 기본 `ErrorResponse`가 아니어서 unhandled면 `500`으로 가기 쉽다.

> Q: `413`이면 항상 gateway limit인가요?
> 의도: status ownership 분리 확인
> 핵심: 아니다. `MaxUploadSizeExceededException`이나 container parser limit가 origin에서 `413`을 만들 수도 있다.

> Q: `MissingServletRequestPartException`도 network 문제일 수 있나요?
> 의도: contract mismatch와 transport abort를 분리하는지 확인
> 핵심: 보통은 part name/content type/resolver 문제를 먼저 본다.

> Q: multipart 장애에서 가장 먼저 추가할 observability 필드는 무엇인가요?
> 의도: 최소 고가치 필드 선별 능력 확인
> 핵심: top-level Spring exception, nested cause class, multipart phase, final status owner, bytes consumed/cleanup.

## 한 줄 정리

Spring multipart 장애 대응의 핵심은 예외 이름 자체가 아니라, **Spring symptom -> nested container cause -> status owner -> bytes/cleanup** 순서로 outward translation을 붙여 읽는 것이다.

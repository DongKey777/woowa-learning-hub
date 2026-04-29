# Browser DevTools Waterfall -> Server Log Timing 브리지

> 한 줄 요약: DevTools의 `request sent`와 `waiting`은 브라우저 시간표이고, proxy의 `request_length`·`bytes_received`·`request_time`·`upstream_response_time` 같은 필드는 서버 쪽 흔적이므로 둘을 1:1 동치로 보지 말고 "upload 쪽 시간인가, first-byte 전 대기인가"를 먼저 연결해야 한다.

**난이도: 🟡 Intermediate**

관련 문서:

- [Browser DevTools `Request Sent` vs `Waiting` 미니 카드](./browser-devtools-request-sent-vs-waiting-mini-card.md)
- [Browser DevTools `Waiting` vs `Content Download` 미니 카드](./browser-devtools-waiting-vs-content-download-mini-card.md)
- [DevTools 뒤 `X-Request-Id`는 어디로 가나요? Gateway -> App Log -> Trace Beginner Bridge](./x-request-id-gateway-app-log-trace-beginner-bridge.md)
- [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)
- [Access Log Correlation Recipes: Tomcat, Jetty, Undertow](./access-log-correlation-recipes-tomcat-jetty-undertow.md)
- [network 카테고리 인덱스](./README.md)
- [Spring MVC 요청 생명주기 기초](../spring/spring-mvc-request-lifecycle-basics.md)

retrieval-anchor-keywords: devtools waiting proxy log, request sent proxy field, waterfall server log timing, upstream response time ttfb, request length upload clue, x-request-id timing bridge, request_time vs waiting, bytes_received upload timing, why waiting is long in proxy log, first byte proxy timing, browser waterfall to nginx log, envoy duration waiting, 처음 devtools log 연결, 헷갈리는 request sent waiting log, what is upstream response time

## 핵심 개념

이 문서의 역할은 **intermediate bridge**다. 초급 문서가 "`request sent`는 보내는 시간, `waiting`은 첫 바이트 전 대기"까지 가르쳤다면, 여기서는 그 화면을 proxy/access log의 필드와 연결한다.

가장 중요한 규칙은 하나다. 브라우저 칸과 로그 필드는 보통 **질문이 같지 않다**.

- DevTools `request sent`: 브라우저가 request body를 밀어 넣는 시간
- DevTools `waiting`: 브라우저가 첫 응답 바이트를 기다린 시간
- proxy `request_length`/`bytes_received`: 보통 시간값이 아니라 request 크기 또는 ingress 흔적
- proxy `request_time`/`duration`: 보통 전체 요청-응답 구간
- proxy `upstream_response_time`/`response_duration`: vendor마다 의미가 조금 다르지만, 대체로 upstream/response 쪽에 시간이 쌓였는지 보는 단서

즉 `request_length`는 "`request sent`와 같은 시간"이 아니고, `upstream_response_time`도 "`waiting`과 완전히 같은 순수 app 코드 시간"이 아니다. 그래도 이 필드들을 같이 보면 "upload가 길었는지, response-side wait가 길었는지"를 사고 없이 이어 붙일 수 있다.

## 한눈에 보기

| 브라우저에서 먼저 길게 보인 구간 | 서버/프록시에서 같이 볼 필드 family | 안전한 1차 해석 | 바로 붙일 다음 질문 |
|---|---|---|---|
| `request sent` | `request_length`, `bytes_received`, 전체 `request_time` | body가 크거나 upload가 느린 장면 후보 | upstream/app 시간은 짧았는가 |
| `waiting` | `request_time`, `upstream_response_time`, vendor별 first-byte-adjacent field | request는 이미 들어갔고 응답 시작 전 대기가 큰 장면 후보 | local reply인가, upstream wait인가 |
| `content download` | `bytes_sent`, total duration, downstream write clue | 첫 바이트 이후 body 전송이 길어진 장면 후보 | 큰 payload인가, streaming인가 |
| `waiting` 긴데 upstream 흔적이 비어 있음 | `upstream_status=-`, local reply reason, response flags | proxy가 app 대신 응답했을 수 있다 | timeout/rate-limit/no healthy upstream인가 |

짧게 외우면 아래 정도면 충분하다.

```text
request sent 길다 -> request 크기/ingress 흔적부터
waiting 길다 -> upstream/first-byte 쪽 흔적부터
upstream 흔적 비다 -> app blame 전에 local reply 의심
```

## 상세 분해

### `Request Sent`는 시간이고 `request_length`는 크기다

초보자가 가장 많이 헷갈리는 지점이다.

- DevTools `request sent`는 브라우저 시간이다
- `request_length`나 `%BYTES_RECEIVED%`는 보통 바이트 수다

그래서 둘을 같은 단위로 비교하면 안 된다. 대신 이렇게 연결한다.

- `request sent`가 길다
- 로그에서 `request_length`/`bytes_received`가 크다
- `upstream_response_time`이 짧거나 거의 없다

이 조합이면 "request body를 보내는 쪽이 컸다"는 해석이 안전하다. 즉 서버 think time보다 upload/ingress 쪽 단서가 강하다.

### `Waiting`은 TTFB 쪽 질문이고, proxy 필드는 그 주변 증거다

`waiting`은 브라우저가 첫 응답 바이트 전까지 기다린 시간이다. 서버 쪽에서는 이 질문을 보통 한 필드로 딱 복제하지 못한다. 대신 아래 조합으로 본다.

- 전체 `request_time`/`duration`
- upstream 계열 시간(`upstream_response_time`, `response_duration` 등)
- local reply 여부(`upstream_status=-`, response flag, local reply detail)

여기서 중요한 caveat가 있다.

- Nginx의 `upstream_response_time` 같은 필드는 vendor-specific semantics를 가진다
- Envoy의 `%DURATION%`, `%RESPONSE_DURATION%`도 exact boundary가 다를 수 있다

그래서 이 문서에서는 그 필드들을 "`waiting`과 완전히 같은 값"이 아니라 **response-side time이 어디에 쌓였는지 보여 주는 단서**로만 쓴다.

## first-byte timing 읽는 순서

### first-byte timing은 보통 "한 필드"보다 "비교"로 읽는다

실무에서는 전용 first-byte 필드가 없거나 vendor마다 다르다. 그래서 intermediate 레벨에서는 아래 비교가 더 안전하다.

1. 브라우저에서 `request sent`와 `waiting` 중 어느 쪽이 큰지 본다.
2. proxy에서 request 크기 계열(`request_length`, `bytes_received`)이 큰지 본다.
3. total duration과 upstream duration이 어디서 커지는지 본다.
4. upstream 흔적이 아예 없으면 local reply 가능성을 먼저 적는다.

즉 first-byte timing은 종종 "`waiting` + upstream duration + local reply 여부"를 같이 읽어서 복원한다.

### 같은 `waiting`이어도 app 지연과 proxy 지연은 갈라야 한다

아래 둘은 브라우저에서는 둘 다 `waiting`이 길어 보일 수 있다.

- app/DB/upstream 호출 때문에 첫 바이트가 늦은 경우
- proxy가 timeout, auth, rate limit, no healthy upstream으로 local reply를 만든 경우

이 둘을 가르는 가장 싼 질문은 이것이다.

- upstream host/status/time이 남았는가
- 아니면 `upstream_status=-`처럼 upstream 미도달 흔적이 강한가

이 분기를 안 하면 "`waiting`이 길다 = 컨트롤러가 느리다"라는 오판이 계속 반복된다.

## 흔한 오해와 함정

- `request_length`가 크면 서버 처리 시간이 길다고 읽는다. 그 필드는 보통 **크기 단서**이지 시간값이 아니다.
- `upstream_response_time`을 브라우저 `waiting`과 완전히 같은 값으로 읽는다. vendor마다 경계가 조금 달라서 보통은 **근사 힌트**로 써야 안전하다.
- `waiting`이 길면 app이 무조건 요청을 받았다고 생각한다. local reply면 app 로그가 없을 수 있다.
- `request_time`이 길면 app이 느리다고 단정한다. 큰 upload나 느린 downstream download도 total duration을 늘린다.
- request id 없이 path와 대충 비슷한 시간만 보고 줄을 매칭한다. 같은 초에 같은 path가 여러 번 있으면 다른 요청을 붙일 수 있다.

## 실무에서 쓰는 모습

같은 `POST /upload`라도 브라우저와 proxy를 같이 읽으면 incident 메모가 달라진다.

| 장면 | DevTools | proxy/access log 단서 | 더 안전한 1차 메모 |
|---|---|---|---|
| A | `request sent=780ms`, `waiting=35ms` | `request_length` 큼, total `request_time=0.86s`, upstream time은 짧음 | upload/ingress 시간이 대부분이고 app first-byte 대기는 짧다 |
| B | `request sent=12ms`, `waiting=620ms` | `request_length` 작음, `request_time`과 upstream time이 같이 큼 | request는 빨리 도착했고 response-side wait가 대부분이다 |
| C | `request sent=10ms`, `waiting=590ms` | `upstream_status=-`, local reply/detail 존재 | app 느림보다 proxy local timeout/reject 후보를 먼저 본다 |

incident 메모를 1문장으로 쓰면 보통 이렇게 정리된다.

```text
A: slow upload/body ingress, not slow app response start
B: response-side wait before first byte, app/upstream/proxy queue candidate
C: long waiting but upstream not reached, check local reply source first
```

실무 순서는 아래 4단계면 충분하다.

1. DevTools row에서 `request sent`와 `waiting` 중 더 큰 쪽을 고른다.
2. 같은 요청을 `X-Request-Id`나 trace id로 proxy log에서 찾는다.
3. `request_length`/`bytes_received`와 `request_time`/`upstream_response_time` 계열을 같이 본다.
4. "`upload 쪽 시간` / `response-side wait` / `proxy local reply`" 중 하나로 first memo를 쓴다.

## 더 깊이 가려면

- 브라우저 waterfall 칸 자체가 아직 헷갈리면 [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
- `request sent`와 `waiting`만 먼저 짧게 자르고 싶다면 [Browser DevTools `Request Sent` vs `Waiting` 미니 카드](./browser-devtools-request-sent-vs-waiting-mini-card.md)
- DevTools row를 log/trace의 동일 요청으로 묶는 법은 [DevTools 뒤 `X-Request-Id`는 어디로 가나요? Gateway -> App Log -> Trace Beginner Bridge](./x-request-id-gateway-app-log-trace-beginner-bridge.md)
- vendor별 field meaning 차이는 [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)에서 더 엄밀하게 본다
- app/container log까지 phase를 연결하려면 [Access Log Correlation Recipes: Tomcat, Jetty, Undertow](./access-log-correlation-recipes-tomcat-jetty-undertow.md)
- 브라우저 timing을 Spring 내부 lifecycle과 이어 보려면 [Spring MVC 요청 생명주기 기초](../spring/spring-mvc-request-lifecycle-basics.md)

## 면접/시니어 질문 미리보기

**Q. DevTools `waiting`과 Nginx `upstream_response_time`은 같은가요?**  
아니다. 비슷한 response-side 질문을 다루지만 exact boundary는 vendor/구성에 따라 달라질 수 있어서 보통은 근사 단서로 쓴다.

**Q. `request sent`가 길면 access log에서 무엇을 먼저 보나요?**  
시간값 하나보다 request 크기/ingress 단서(`request_length`, `bytes_received`)와 total duration, upstream time이 함께 짧은지 본다.

**Q. `waiting`이 길었는데 app 로그가 없을 수도 있나요?**  
그렇다. proxy local reply, timeout, rate limit, no healthy upstream이면 브라우저는 기다렸어도 app는 요청을 못 봤을 수 있다.

## 한 줄 정리

DevTools `request sent`와 `waiting`을 proxy의 `request_length`·`bytes_received`·`request_time`·`upstream_response_time`과 연결할 때는 1:1 숫자 대응보다, **upload 쪽 시간인지 response-side wait인지 local reply인지**를 먼저 분기하는 브리지로 읽어야 한다.

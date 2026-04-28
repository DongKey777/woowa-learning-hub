# DevTools 뒤 `X-Request-Id`는 어디로 가나요? Gateway -> App Log -> Trace Beginner Bridge

> 한 줄 요약: DevTools에서 `X-Request-Id`를 봤다면 그 값은 "다음에 어디를 봐야 하나"를 정하는 추적 표식이다. 초급자는 이 값을 gateway 로그, app 로그, tracing 화면에서 같은 요청을 다시 찾는 순서표로 쓰면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
- [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- [Access Log Correlation Recipes: Tomcat, Jetty, Undertow](./access-log-correlation-recipes-tomcat-jetty-undertow.md)
- [Spring MVC 요청 생명주기 기초](../spring/spring-mvc-request-lifecycle-basics.md)
- [Spring Observability, Micrometer, Tracing](../spring/spring-observability-micrometer-tracing.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: x-request-id propagation, request id propagation basics, devtools x-request-id next step, gateway app log trace bridge, x-request-id 뭐예요, request id 처음, request id 왜 봐요, what is x-request-id, request id tracing beginner, gateway log app log trace, trace id vs request id, observability header basics, devtools after x-request-id, app log에서 request id 찾기

## 핵심 개념

`X-Request-Id`는 요청에 붙는 **택배 송장 번호**처럼 보면 된다.

- 브라우저 DevTools에서는 "이 요청을 다시 찾을 단서"
- gateway에서는 "앞단이 이 요청을 처리했는지 확인하는 키"
- app 로그에서는 "컨트롤러나 필터까지 들어왔는지 확인하는 키"
- tracing에서는 "여러 서비스 이동 경로를 묶어 보는 연결 단서"

초급자에게 중요한 점은 "이 ID 하나로 원인을 확정한다"가 아니다.
이 값으로 **같은 요청을 여러 관측 도구에서 다시 만나는 순서**를 잡는 것이다.

## 한눈에 보기

| 지금 찾은 곳 | 이 뜻이 먼저 맞다 | 아직 확정하면 안 되는 것 | 바로 다음 확인 |
|---|---|---|---|
| DevTools response header에 `X-Request-Id` 있음 | 적어도 서버 체인 어딘가가 추적 표식을 남겼다 | app이 반드시 성공 처리했다 | gateway access log에 같은 값이 있는지 |
| gateway 로그에 같은 ID 있음 | 요청은 gateway까지는 왔다 | app까지 반드시 들어갔다 | upstream status, route, app 로그 |
| app 로그에 같은 ID 있음 | app 프로세스가 이 요청을 받았다 | DB나 외부 API까지 모두 끝났다 | status, 예외, 처리 시간 |
| trace 화면에 같은 ID 또는 연결된 trace 있음 | 여러 hop을 한 묶음으로 볼 수 있다 | trace가 없으면 요청이 없었다 | sampling, log-trace 연동, span attribute |

짧게 외우면 이렇게 본다.

```text
DevTools = 송장 번호를 발견한 곳
gateway log = 앞문까지 왔는지
app log = 안쪽 방까지 들어왔는지
trace = 방을 몇 군데 거쳤는지
```

## 상세 분해

### 1. DevTools에서 먼저 적을 것

DevTools에서 `X-Request-Id`가 보이면 아래 3개를 같이 적어 두면 된다.

- request URL
- status code
- `X-Request-Id` 값

초급자는 여기서 끝내지 말고, 값을 복사해서 다음 화면으로 넘겨야 한다.
`Status 502 + X-Request-Id abc-123`처럼 한 줄 메모만 남겨도 이후 로그 찾기가 쉬워진다.

### 2. Gateway 로그에서 보는 질문

gateway나 reverse proxy 로그에서는 보통 아래 질문 하나만 먼저 보면 된다.

- "같은 `X-Request-Id`가 있나?"

있다면 적어도 요청은 gateway까지 왔다. 여기서 초급자가 먼저 읽을 칸은 보통:

- upstream으로 보냈는지
- gateway가 직접 `502`/`504`를 만들었는지
- 응답 status가 무엇인지

즉 gateway 로그는 "`이 요청이 앞단에서 끝났나, app 쪽으로 넘어갔나`"를 가르는 자리다.

### 3. App 로그에서 보는 질문

app 로그에 같은 ID가 있으면 "요청이 app 코드 경계까지는 들어왔다"는 뜻으로 읽으면 된다.

초급자 첫 확인 순서는 이 정도면 충분하다.

- controller/filter 예외가 있었나
- app이 남긴 status나 error message가 무엇인가
- 처리 시간이 비정상적으로 길었나

만약 gateway에는 ID가 있는데 app 로그에는 없으면 두 가지 후보를 먼저 본다.

- gateway가 app에 보내기 전에 직접 응답했다
- app 로그 패턴에 request ID를 남기지 않아서 검색이 안 된다

### 4. Trace에서는 "같은 값"보다 "같은 요청 묶음"을 본다

tracing 화면은 `X-Request-Id`와 **똑같은 문자열**이 그대로 보일 수도 있고, `traceId`라는 다른 식별자가 중심일 수도 있다.

초급자 첫 해석은 이렇게 두 줄이면 충분하다.

- `X-Request-Id`는 로그 검색용 표식일 수 있다
- `traceId`는 여러 span을 묶는 tracing 전용 번호일 수 있다

그래서 trace 화면에서 바로 같은 값이 안 보여도 이상한 것은 아니다.
대신 request attribute, span tag, log-trace correlation로 연결되는지 보면 된다.

## 흔한 오해와 함정

- `X-Request-Id`가 있으면 app이 반드시 처리했다고 생각한다. gateway가 만든 에러 응답에도 붙을 수 있다.
- gateway 로그와 app 로그의 ID가 다르면 무조건 장애라고 단정한다. 중간에서 새 ID를 만들거나 덮어쓰는 구성도 있다.
- trace 화면에서 같은 문자열이 안 보이면 추적이 실패했다고 생각한다. `traceId`와 `requestId`는 역할이 다를 수 있다.
- app 로그에 ID가 안 보이면 요청이 app에 안 왔다고 결론낸다. 실제로는 로그 포맷에 ID 출력이 빠졌을 수도 있다.
- request ID 하나만 보고 원인을 확정한다. 이 값은 원인 자체보다 **다음 증거를 찾는 열쇠**다.

## 실무에서 쓰는 모습

아래처럼 한 요청을 3칸으로 이어 보면 초급자도 다음 확인 지점을 잃지 않는다.

| 관측 위치 | 보이는 값 | 초급자 첫 문장 |
|---|---|---|
| DevTools | `X-Request-Id: abc-123`, `502` | "이 요청은 서버 체인에 들어간 흔적이 있다" |
| gateway log | `request_id=abc-123 upstream_status=- final_status=502` | "gateway가 upstream 전에 실패했거나 직접 응답했을 수 있다" |
| app log | 없음 | "app 미도달 또는 app 로그 상관관계 누락부터 확인한다" |

반대로 아래 장면이면 읽는 법이 달라진다.

| 관측 위치 | 보이는 값 | 초급자 첫 문장 |
|---|---|---|
| DevTools | `X-Request-Id: abc-123`, `500` | "로그 추적 실마리가 있다" |
| gateway log | `request_id=abc-123 upstream_status=500` | "gateway는 app 응답을 받았다" |
| app log | `requestId=abc-123 NullPointerException` | "app 예외부터 본다" |
| trace | `traceId=9fe...`, attribute `request.id=abc-123` | "같은 요청 흐름을 서비스 단위로 확장해 볼 수 있다" |

처음에는 이 순서만 지키면 된다.

1. DevTools에서 ID와 status를 적는다.
2. gateway 로그에서 같은 ID가 있는지 찾는다.
3. app 로그에서 같은 ID 또는 대응되는 request field를 찾는다.
4. trace가 있으면 hop별 지연과 예외를 묶어서 본다.

## 더 깊이 가려면

- DevTools에서 `Server`/`Via`/`X-Request-Id`를 왜 먼저 보는지 다시 잡고 싶으면 [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- gateway가 직접 응답한 것인지 upstream 결과인지 더 엄밀히 가르려면 [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- gateway와 proxy가 request ID를 왜 붙이는지 운영 관점에서 보려면 [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
- app access log에서 request ID를 어떻게 묶는지 더 깊게 보려면 [Access Log Correlation Recipes: Tomcat, Jetty, Undertow](./access-log-correlation-recipes-tomcat-jetty-undertow.md)
- Spring에서 log, metrics, trace가 어떻게 연결되는지 보려면 [Spring Observability, Micrometer, Tracing](../spring/spring-observability-micrometer-tracing.md)

## 한 줄 정리

DevTools에서 `X-Request-Id`를 봤다면 그 값은 원인 판결문이 아니라, gateway 로그 -> app 로그 -> trace 순서로 같은 요청을 다시 찾는 추적 표식이다.

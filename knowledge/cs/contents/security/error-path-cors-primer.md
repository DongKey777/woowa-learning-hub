# Error-Path CORS Primer

> 한 줄 요약: actual `401`/`403`이 이미 발생했어도 error response에 CORS 헤더가 빠지면 브라우저는 그 숫자를 JS에 넘기지 못하고, 겉으로는 "CORS 에러만 난 것처럼" 보일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [CORS 기초](./cors-basics.md)
- [Preflight Debug Checklist](./preflight-debug-checklist.md)
- [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md#20초-선행-확인-이-코드가-actual-요청-결과인가)
- [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
- [CORS / SameSite / Preflight 심화](./cors-samesite-preflight.md)
- [Spring ProblemDetail / Error Response Design](../spring/spring-problemdetail-error-response-design.md)
- [Security README: 증상별 바로 가기](./README.md#증상별-바로-가기)

retrieval-anchor-keywords: error path cors primer, cors masks 401, cors masks 403, real 401 looks like cors, real 403 looks like cors, missing access-control-allow-origin on error, error response missing cors header, actual request exists but browser says cors, preflight passed then cors error, post 401 but frontend sees cors, post 403 but frontend sees cors, auth failure masked by cors, beginner error response cors, actual response blocked by cors, why network shows 401 but js sees cors

## 핵심 개념

이 문서가 다루는 장면은 `OPTIONS` preflight failure가 아니다.

- preflight는 통과했다
- actual `GET`/`POST`가 서버까지 갔다
- 서버는 실제로 `401` 또는 `403`을 만들었다
- 그런데 **error response에는 CORS 허용 헤더가 없다**

브라우저는 이 응답을 받아도 JavaScript에게 내용을 넘기지 않는다. 그래서 프론트에서는 "`401`/`403`이 아니라 CORS가 난 것 같다"라고 보이기 쉽다.

짧은 기억법:

- actual request가 없으면 preflight lane
- actual request는 있는데 JS가 응답을 못 읽으면 error-path CORS lane

## 한눈에 보기

| 장면 | Network에서 보이는 것 | 브라우저 콘솔/JS에서 보이는 것 | 먼저 읽는 결론 |
|---|---|---|---|
| preflight failure | `OPTIONS 401/403`, actual `POST` 없음 | CORS 에러 | 아직 actual auth failure를 읽지 않는다 |
| normal auth failure | actual `POST 401/403`, CORS 헤더도 있음 | JS가 `401`/`403` body를 읽을 수 있음 | 실제 auth/authz 원인을 본다 |
| error-path CORS masking | actual `POST 401/403`, 그런데 error response에 CORS 헤더 없음 | JS는 body/status 접근이 막히고 CORS처럼 보임 | 실제 auth failure와 error-path CORS 누락을 같이 본다 |

한 줄로 줄이면:

- `OPTIONS-only`면 preflight
- actual request가 보이면 auth lane
- actual request가 보이는데 JS가 못 읽으면 error-path CORS까지 같이 본다

## 상세 분해

### 1. 왜 `401`/`403`인데 CORS처럼 보이나

CORS는 "요청을 서버로 보낼 수 있나"만이 아니라, **응답을 JS가 읽어도 되나**도 본다.

그래서 서버가 이런 순서로 동작할 수 있다.

1. 인증 실패를 감지한다
2. `401` 또는 `403` error response를 만든다
3. 그런데 success path에만 붙던 `Access-Control-Allow-Origin`이 error path에는 빠진다
4. 브라우저는 응답 body와 일부 status 접근을 차단한다

결과적으로 백엔드 로그에는 `401`/`403`이 남는데, 프론트 개발자는 CORS만 본다.

### 2. preflight failure와 어떻게 다르나

초보자가 가장 많이 헷갈리는 지점은 "`401` 숫자가 보이면 다 같은 뜻 아닌가?"라는 부분이다.

| 비교 질문 | preflight failure | error-path CORS masking |
|---|---|---|
| actual `GET`/`POST`가 보이나 | 보통 없다 | 있다 |
| 서버 business/auth 로직이 돌았나 | 아직 아닐 수 있다 | 이미 돌았다 |
| 먼저 볼 문서 | [Preflight Debug Checklist](./preflight-debug-checklist.md) | 이 문서 + [Auth Failure Responses `401/403/404`](./auth-failure-response-401-403-404.md) |
| 고쳐야 할 것 | `OPTIONS` 허용, preflight headers, proxy/filter | actual auth 원인 + error response에도 CORS headers |

즉 "actual request 존재 여부"가 첫 갈림길이다.

### 3. 어디서 헤더가 빠지기 쉬운가

입문자가 자주 보는 실수는 아래 셋이다.

- CORS 설정이 정상 응답 경로에만 있고, exception handler나 auth failure handler에는 일관되게 적용되지 않는다
- gateway/proxy가 success response에는 CORS 헤더를 붙이지만 upstream `401`/`403` error에는 안 붙인다
- Security filter에서 early return한 응답이 MVC CORS 설정까지 도달하지 못한다

그래서 "성공할 때는 잘 되는데 로그인 만료나 권한 부족일 때만 CORS가 난다"라는 장면이 생긴다.

## 흔한 오해와 함정

- "`CORS 에러니까 auth는 아닌가 보다`" -> 아니다. actual `401`/`403`이 CORS에 가려졌을 수 있다.
- "`Network에 401이 있으면 프론트도 401 body를 읽을 수 있겠지`" -> 아니다. 브라우저는 status가 보이더라도 JS에 상세 응답을 못 넘길 수 있다.
- "`preflight가 통과했으니 CORS는 끝났다`" -> 아니다. actual error response에도 CORS 헤더가 계속 필요하다.
- "`success response에만 CORS 헤더 붙이면 충분하다`" -> 아니다. auth failure, validation failure, exception response에도 정책이 일관돼야 한다.

## 실무에서 쓰는 모습

가장 흔한 흐름은 이렇다.

1. 브라우저가 `POST /api/orders`를 보낸다
2. session 만료 또는 bearer token 문제로 서버가 `401`을 만든다
3. error body는 `ProblemDetail` 또는 JSON으로 만들어졌지만 `Access-Control-Allow-Origin`이 빠진다
4. 프론트 코드에서는 `response.status === 401` 분기 대신 CORS failure처럼 보인다

권한 부족 `403`도 똑같다. 즉 이 문서는 "`진짜 원인`과 `브라우저에 보이는 포장`을 분리하자"는 bridge다.

초보자용 체크 순서는 아래면 충분하다.

1. same-path actual request가 보이는가
2. 그 actual response가 실제로 `401`/`403`인가
3. 그 error response headers에 `Access-Control-Allow-Origin`이 있는가
4. 없으면 auth 원인과 error-path CORS 누락을 같이 본다

## 더 깊이 가려면

- [Preflight Debug Checklist](./preflight-debug-checklist.md) — actual request가 아예 없는지부터 다시 가를 때
- [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md#20초-선행-확인-이-코드가-actual-요청-결과인가) — actual `401`/`403` 자체의 의미를 auth/authz 관점으로 다시 읽을 때
- [CORS 기초](./cors-basics.md) — CORS가 request cookie 문제와 response read 문제 중 어느 쪽인지 먼저 되짚을 때
- [CORS / SameSite / Preflight 심화](./cors-samesite-preflight.md) — allowlist, `Vary: Origin`, preflight cache 같은 운영 설계를 더 볼 때
- [Spring ProblemDetail / Error Response Design](../spring/spring-problemdetail-error-response-design.md) — framework error handling과 response contract를 연결해서 볼 때

## 면접/시니어 질문 미리보기

- "`OPTIONS`는 204인데 actual `POST 401`이 CORS처럼 보이면 어디부터 보겠는가?" -> actual auth failure와 error response CORS headers를 같이 본다.
- "왜 success path CORS와 error path CORS를 분리해서 확인해야 하나?" -> 브라우저는 error response도 동일하게 CORS로 읽기 때문에, 실패 경로만 헤더가 빠져도 프론트가 진짜 status를 못 읽는다.
- "gateway와 app 중 어디에서 CORS를 붙이는가?" -> 한 곳을 policy owner로 정하되, auth failure를 포함한 모든 응답 경로에 일관되게 적용되는지 확인해야 한다.

## 한 줄 정리

actual `401`/`403`이 이미 발생했는데도 브라우저가 CORS만 보인다면, auth 원인과 error response의 CORS 헤더 누락을 함께 확인해야 한다.

# Browser DevTools `Accept` vs Response `Content-Type` 미니 카드

> 한 줄 요약: DevTools에서 body preview를 열기 전에도 `Request Headers`의 `Accept`와 `Response Headers`의 `Content-Type` 두 칸만 보면 "나는 JSON을 기대했는지, 서버는 실제로 HTML/JSON 중 무엇을 보냈는지"를 빠르게 분리할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 요청·응답 헤더 기초](./http-request-response-headers-basics.md)
- [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](../spring/spring-requestbody-415-unsupported-media-type-primer.md)
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](../spring/spring-mvc-controller-basics.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: accept vs content-type devtools, request accept response content-type, json 대신 html 와요, api got html instead of json, devtools accept header beginner, devtools content-type first check, response body preview before open, accept 뭐예요, content-type 뭐예요, json html confusion first pass, why api returns html, beginner network headers, content-type application json 안 붙였는데 415, request content-type first check, 왜 컨트롤러 전에 415

## 핵심 개념

처음에는 이렇게만 나누면 된다.

- `Accept`: 클라이언트가 "나는 이런 응답을 기대한다"고 말하는 요청 헤더
- response `Content-Type`: 서버가 "내가 실제로 보낸 본문 형식은 이거다"라고 말하는 응답 헤더

초급자가 자주 헷갈리는 이유는 둘 다 `json`, `html` 같은 단어를 담을 수 있기 때문이다. 하지만 질문이 다르다.

- `Accept`는 기대
- `Content-Type`은 실제 전달 결과

그래서 body preview를 열기 전에도 `Accept: application/json`인데 response `Content-Type: text/html`이면, 첫 분기는 이미 나온다. "JSON을 기대했는데 실제로는 HTML이 왔구나."

## 한눈에 보기

| DevTools에서 보는 칸 | 읽는 질문 | 자주 보이는 값 | 초급자 첫 해석 |
|---|---|---|---|
| request `Accept` | "클라이언트는 무엇을 받고 싶어 했나?" | `application/json`, `text/html`, `*/*` | 기대한 응답 종류를 본다 |
| response `Content-Type` | "서버는 실제로 무엇을 보냈나?" | `application/json`, `text/html; charset=UTF-8` | 실제 도착한 본문 종류를 본다 |

짧게 외우면 이렇게 보면 된다.

```text
Accept = 내가 받고 싶다고 말한 것
Content-Type = 서버가 실제로 보낸 것
```

## DevTools에서는 어디를 먼저 보나

Network row 하나를 열고 아래 순서만 지키면 된다.

1. `Request Headers`에서 `Accept`를 본다
2. `Response Headers`에서 `Content-Type`을 본다
3. 둘이 같은 방향인지, 어긋났는지 본다

이 단계에서는 아직 body를 길게 읽지 않아도 된다. 예를 들면 아래처럼 읽는다.

| 조합 | 첫 해석 |
|---|---|
| `Accept: application/json` + `Content-Type: application/json` | JSON API 계약과 실제 응답이 같은 방향이다 |
| `Accept: application/json` + `Content-Type: text/html` | API처럼 보냈지만 HTML page/login page가 섞였을 수 있다 |
| `Accept: text/html` + `Content-Type: text/html` | 브라우저가 page를 열려는 장면일 가능성이 크다 |
| `Accept: */*` + `Content-Type: text/html` | 기대가 넓어서 `Accept`만으로는 부족하다. URL, initiator를 같이 본다 |

핵심은 `Accept`만 보고 성공을 확정하지 않고, response `Content-Type`으로 실제 결과를 닫는 것이다.

## 다음 한 걸음 분기

이 카드는 network 헤더 분리까지만 맡는다. 초급자는 여기서 바로 database 문서로 뛰지 말고, 아래처럼 한 칸만 넘기면 된다.

| 지금 헤더에서 보인 장면 | 여기서 내릴 첫 판단 | 다음 한 걸음 |
|---|---|---|
| `Accept: application/json`인데 response `Content-Type: text/html` | JSON API 기대와 실제 HTML 응답이 어긋났다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) 또는 [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md) |
| request body를 보내는데 request `Content-Type`이 비었거나 `text/plain`이다 | 응답 형식보다 먼저 요청 body 형식 계약이 비었을 수 있다 | [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](../spring/spring-requestbody-415-unsupported-media-type-primer.md) |
| response `Content-Type: application/json`까지는 맞다 | network 헤더 계약은 대체로 맞다 | [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](../spring/spring-mvc-controller-basics.md) |

짧게 외우면 `Accept/response Content-Type`으로 "응답이 무엇이었나"를 자르고, request `Content-Type`으로 "요청 body를 무엇으로 보냈나"를 자른다.

## JSON 기대 vs HTML 도착을 이렇게 읽는다

초급자가 가장 많이 묻는 장면은 이것이다.

```http
Request Headers
Accept: application/json
```

```http
Response Headers
Content-Type: text/html; charset=UTF-8
```

이 조합이면 body preview를 열기 전에도 아래 두 가설을 먼저 연다.

1. 원래 JSON API가 아니라 HTML page endpoint를 호출했다
2. JSON API였는데 login redirect나 SSR page가 최종 응답으로 섞였다

즉 "서버가 이상하다"보다 먼저, **기대한 계약과 실제 응답 형식이 어긋났다**고 메모하면 된다.

반대로 아래 조합이면 JSON 계약 쪽이 더 강하다.

```http
Request Headers
Accept: application/json
```

```http
Response Headers
Content-Type: application/json
```

이때는 login HTML보다 app JSON이나 gateway JSON 중 어느 쪽인지로 다음 분기를 넘기면 된다.

## 흔한 오해와 함정

- `Accept`를 "서버가 실제로 보낸 타입"으로 읽는다. 아니다. `Accept`는 요청 쪽 희망 사항이다.
- response `Content-Type`를 "클라이언트가 원한 값"으로 읽는다. 아니다. 서버가 실제로 보낸 본문 설명이다.
- `Accept: application/json`이면 서버가 반드시 JSON을 보내야 한다고 생각한다. 실제 서비스에서는 redirect, 에러 페이지, fallback 때문에 HTML이 올 수 있다.
- `Content-Type: text/html`이면 무조건 SSR 정상 페이지라고 생각한다. login page, gateway 기본 페이지, CDN 에러 HTML일 수도 있다.
- `Accept: */*`를 보고 "무엇이든 괜찮다"를 곧바로 business 의미로 읽는다. 브라우저/라이브러리 기본값일 때가 많아서 URL, initiator, final URL을 같이 봐야 한다.

## 실무에서 쓰는 모습

DevTools에서 `/api/me`를 눌렀는데 body를 열기 전 header만 이렇게 보였다고 하자.

| 칸 | 값 | 초급자 첫 메모 |
|---|---|---|
| URL | `/api/me` | API처럼 보이는 경로 |
| request `Accept` | `application/json` | JSON을 기대한 호출 |
| response `Content-Type` | `text/html; charset=UTF-8` | 실제로는 HTML이 도착 |

이때 가장 안전한 한 줄 메모는 이것이다.

"JSON을 기대한 API 호출인데 실제 응답은 HTML이라서 login redirect나 page fallback 후보를 먼저 본다."

반대로 `/orders/42` 같은 page route에서 아래 조합이면 자연스럽다.

| 칸 | 값 | 초급자 첫 메모 |
|---|---|---|
| URL | `/orders/42` | page route처럼 보임 |
| request `Accept` | `text/html` | 브라우저가 HTML page를 기대 |
| response `Content-Type` | `text/html; charset=UTF-8` | 실제로도 HTML page가 도착 |

즉 `Accept`와 `Content-Type`은 "누가 맞았나"를 따지는 헤더가 아니라, **기대와 실제가 일치하는지 보는 2칸 체크**다.

## 더 깊이 가려면

- 헤더 역할 자체가 아직 헷갈리면 [HTTP 요청·응답 헤더 기초](./http-request-response-headers-basics.md)
- HTML page 응답과 JSON API 응답의 의미 차이를 더 붙여 읽고 싶으면 [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- `Content-Type`이 JSON이어도 owner가 app인지 gateway인지 더 가르고 싶으면 [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- `Accept: application/json`인데 login HTML이 온 장면을 깊게 보고 싶으면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- Spring 컨트롤러가 왜 어떤 요청엔 HTML view를, 어떤 요청엔 JSON을 내보내는지 붙여 보려면 [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](../spring/spring-mvc-controller-basics.md)

## 한 줄 정리

DevTools에서 `Accept`는 "내가 기대한 응답", response `Content-Type`은 "서버가 실제로 보낸 응답"으로 읽으면 JSON/HTML 혼선을 body preview 전에 대부분 잘라낼 수 있다.

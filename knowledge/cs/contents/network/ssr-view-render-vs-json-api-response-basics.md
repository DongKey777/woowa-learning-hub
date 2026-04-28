# SSR 뷰 렌더링 vs JSON API 응답 입문

> 한 줄 요약: 브라우저가 페이지 자체를 열려고 보낸 요청은 보통 HTML 응답과 화면 이동으로 이어지고, 프론트엔드 코드가 데이터를 받으려고 보낸 요청은 보통 JSON 응답과 후속 처리 로직으로 이어지므로, 둘을 같은 "성공"으로 읽으면 navigation과 API handling을 쉽게 섞게 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md)
- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](../spring/spring-api-401-vs-browser-302-beginner-bridge.md)
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](../spring/spring-mvc-controller-basics.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: ssr vs json api basics, html response vs json response, 서버 렌더링 api 차이, api 성공인데 화면 안 바뀜, fetch 200 but no navigation, browser page request vs api request, json api success handling beginner, controller returns html vs json, page 이동과 api 응답 차이, login html instead of json, beginner web response mental model, fetch redirect followed login html 200, xhr redirect login page 200, hidden 302 login redirect in fetch, devtools final 200 hides initial 302

## 핵심 개념

처음에는 "누가 이 응답을 읽는가"만 나누면 된다.

- 페이지 요청: 브라우저가 HTML을 받아 화면을 그린다
- API 요청: 자바스크립트나 앱 코드가 JSON을 받아 다음 행동을 결정한다

겉으로는 둘 다 `200 OK`일 수 있어서 초급자가 자주 섞는다. 하지만 성공의 의미는 다르다.

- SSR 페이지 성공: "보여 줄 HTML이 왔다"
- JSON API 성공: "코드가 읽을 데이터가 왔다"

그래서 `fetch("/api/orders")`가 성공했다고 해도 브라우저가 자동으로 새 페이지로 이동하지는 않는다. 반대로 브라우저 주소창에서 `/orders`를 열어 HTML을 받으면, 그 순간의 성공은 "데이터 저장 성공"이 아니라 "화면 렌더링 성공"에 가깝다.

## 한눈에 보기

| 구분 | SSR 뷰 렌더링 응답 | JSON API 응답 |
|---|---|---|
| 주 독자 | 브라우저 자체 | 프론트엔드 코드, 모바일 앱, 다른 서버 |
| 흔한 `Content-Type` | `text/html` | `application/json` |
| 성공 뒤 기본 동작 | 브라우저가 화면을 그림 | 클라이언트 코드가 메시지 표시, 상태 갱신, 이동 여부를 결정 |
| 화면 이동과의 관계 | redirect나 새 page request와 자주 붙어 다님 | 자동 이동은 없고 별도 JS/navigation 로직이 필요 |
| 초급자 오해 | HTML이 왔으니 API도 성공했다고 착각 | `200` JSON이면 페이지도 자동 전환된다고 착각 |

짧은 기억법:

- HTML 응답은 "브라우저가 바로 보여 줄 결과물"
- JSON 응답은 "코드가 해석할 재료"

## SSR 응답과 JSON 응답 읽기

### 1. SSR 응답은 페이지를 완성하는 쪽에 가깝다

브라우저가 주소창으로 `/orders/42`를 열면 보통 기대하는 것은 주문 상세 "페이지"다.

```http
GET /orders/42 HTTP/1.1
Accept: text/html
```

```http
HTTP/1.1 200 OK
Content-Type: text/html

<html>
  <body>주문 상세 화면</body>
</html>
```

이 경우 응답 본문 자체가 화면이다. 브라우저는 HTML을 받아 렌더링하면 된다. 그래서 SSR 흐름에서는 아래 질문이 자연스럽다.

- 어떤 URL로 이동했나
- redirect가 있었나
- 최종 HTML page가 무엇이었나

### 2. JSON API 응답은 데이터를 건네는 쪽에 가깝다

반대로 프론트엔드 코드가 `/api/orders/42`를 호출하면 보통 화면 조각을 바로 그릴 HTML이 아니라 데이터를 기대한다.

```http
GET /api/orders/42 HTTP/1.1
Accept: application/json
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"id":42,"status":"PAID"}
```

이 경우 응답 본문은 화면이 아니라 데이터다. 그래서 성공 뒤 실제 행동은 클라이언트 코드가 정한다.

- 화면 상태 갱신
- 성공 토스트 표시
- 필요한 경우 `router.push("/orders/42")` 같은 이동 실행

즉 API는 "이동을 포함한 결과"를 직접 끝내기보다, 이동에 필요한 재료를 주는 쪽에 더 가깝다.

## 로그인과 `200 OK` 오해 분리

### 3. 같은 로그인 성공도 흐름이 다르게 보일 수 있다

초급자가 가장 자주 섞는 장면이 로그인이다.

| 상황 | 흔한 흐름 | 핵심 해석 |
|---|---|---|
| SSR 로그인 폼 | `POST /login -> 302/303 -> GET /orders` | 브라우저가 redirect를 따라 새 페이지로 간다 |
| JSON API 로그인 | `POST /api/login -> 200/204 JSON` | API 성공 후 이동은 프론트 코드가 따로 결정한다 |

SSR에서는 "로그인 성공 후 어디 page로 보낼까"가 중요하다.  
JSON API에서는 "성공/실패를 어떤 상태 코드와 body로 돌려줄까"가 더 중요하다.

그래서 "`로그인 성공 응답`인데 왜 `Location`이 없지?"라고 묻는다면, 먼저 그 요청이 page 요청인지 API 요청인지부터 구분해야 한다.

### 4. `200 OK` 하나만 보면 오해하기 쉽다

아래 두 응답은 둘 다 `200`이지만 읽는 방식이 완전히 다르다.

```http
HTTP/1.1 200 OK
Content-Type: text/html
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

첫째는 브라우저가 page를 그릴 수 있다는 뜻일 수 있다.  
둘째는 클라이언트 코드가 data를 처리할 수 있다는 뜻일 수 있다.

따라서 초급자는 상태 코드만 보지 말고 최소한 아래 세 가지를 같이 본다.

1. 요청 URL이 page route인가, `/api/**` 같은 data route인가
2. 응답 `Content-Type`이 HTML인가 JSON인가
3. 성공 뒤 누가 다음 행동을 결정하는가

## `fetch`와 XHR에서 자주 헷갈리는 숨은 redirect

초급자가 특히 많이 당황하는 장면은 이것이다.

- 프론트 코드에서는 `fetch("/api/me")` 결과가 `200`으로 보인다
- DevTools에서도 최종 응답이 `200 OK`, `text/html`처럼 보인다
- 그런데 body를 열어 보니 로그인 페이지 HTML이다

이때 실제 서버 흐름은 아래였을 수 있다.

```text
GET /api/me    -> 302 Found
Location: /login
GET /login     -> 200 OK
Content-Type: text/html
```

브라우저의 기본 redirect follow 때문에, 프론트 코드나 DevTools에서 **최종 `/login` 응답만 먼저 눈에 들어오는 것**이다.
그래서 "`200`이니까 API 성공"이라고 읽으면 틀릴 수 있다.

짧은 mental model:

| 겉으로 보이는 것 | 실제로 먼저 있었을 수 있는 것 | 초급자 해석 |
|---|---|---|
| `fetch` 결과 `200` | 보호된 API가 `302`로 `/login`으로 보냄 | API 성공이 아니라 login page를 따라간 결과일 수 있다 |
| response body가 HTML | 최종 응답이 `/login` page | JSON contract가 깨졌다는 신호일 수 있다 |
| 화면은 안 바뀌는데 네트워크는 성공처럼 보임 | 브라우저는 API 호출의 redirect를 따라가도 page navigation까지 대신 해 주지 않음 | "성공"과 "이동"을 분리해서 읽어야 한다 |

빠른 확인 순서:

1. 최종 응답 URL이 원래 API URL인지 `/login`인지 본다
2. `Content-Type`이 `application/json`이 아니라 `text/html`인지 본다
3. Network 탭에서 redirect row가 접혀 있지 않은지 확인한다
4. body 첫 줄이 login form/title인지 본다

즉 `fetch`/XHR에서 보이는 최종 `200`은 "원래 API가 성공했다"가 아니라 "브라우저가 redirect를 따라간 끝 응답"일 수 있다.

## 흔한 오해와 함정

- "API가 `200`이면 브라우저가 자동으로 다음 화면으로 간다"라고 생각하기 쉽다.  
  실제 이동은 redirect 응답이나 JS navigation이 따로 있어야 한다.

- "`fetch` 결과로 login HTML을 받았으니 JSON API도 성공했다"라고 생각하기 쉽다.  
  실제로는 API 경계에 브라우저용 redirect/HTML 응답이 섞였거나, 숨은 `302 -> /login -> 200 HTML`이 final response만 남긴 것일 수 있다.

- "서버가 HTML도 주고 JSON도 주니까 둘 다 같은 controller 감각이다"라고 생각하기 쉽다.  
  브라우저 view 렌더링과 API contract는 소비자와 후속 처리 방식이 다르다.

- "화면이 바뀌었으니 서버가 JSON 안에서 이동을 시켰다"라고 말하기 쉽다.  
  JSON은 보통 이동 자체를 수행하지 않고, 프론트 코드가 응답을 읽고 이동한다.

- "SSR은 무조건 옛날 방식, API는 무조건 최신 방식"으로 이해하기 쉽다.  
  둘은 시대 구분보다 응답 계약 구분에 가깝다. 한 앱 안에서도 함께 존재할 수 있다.

## 실무에서 쓰는 모습

주문 생성 뒤 결과를 보여 주는 장면을 두 방식으로 나누면 감각이 빨리 잡힌다.

| 방식 | 네트워크에서 보이는 것 | 초급자 메모 |
|---|---|---|
| SSR 폼 제출 | `POST /orders -> 303 Location: /orders/42 -> GET /orders/42 -> HTML` | 완료 화면은 브라우저가 새 page로 연다 |
| JSON API + 프론트 상태 갱신 | `POST /api/orders -> 201 JSON {"id":42}` | 성공 메시지, 목록 갱신, 상세 이동은 프론트 코드가 정한다 |

그래서 "성공 처리"를 구현할 때도 질문이 달라진다.

- SSR 쪽 질문: redirect할까, 어떤 view를 보여 줄까
- API 쪽 질문: 어떤 상태 코드와 JSON shape를 줄까, 프론트는 성공 후 무엇을 할까

DevTools에서 빠르게 가르려면 아래 순서가 가장 단순하다.

1. `Content-Type`이 `text/html`인지 `application/json`인지 본다
2. `Location`과 `3xx`가 있는지 본다
3. 페이지 전체가 바뀌었는지, 아니면 JS가 일부 화면만 갱신했는지 본다

## 더 깊이 가려면

- 브라우저 요청의 큰 흐름부터 다시 잡으려면 [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- redirect, forward, SPA navigation을 먼저 가르려면 [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md)
- `200`/`302`/`401`을 응답 계약 관점에서 다시 읽으려면 [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- 같은 Spring 앱에서 page와 API auth 실패가 왜 갈리는지 보려면 [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](../spring/spring-api-401-vs-browser-302-beginner-bridge.md)
- Spring 코드에서 view 반환과 API 반환이 어떻게 갈리는지 보려면 [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](../spring/spring-mvc-controller-basics.md)

## 면접/시니어 질문 미리보기

**Q. SSR 페이지 응답과 JSON API 응답의 가장 큰 차이는 무엇인가요?**  
SSR은 브라우저가 바로 렌더링할 HTML을 주는 계약에 가깝고, JSON API는 클라이언트 코드가 해석할 데이터를 주는 계약에 가깝다.

**Q. `fetch`가 `200 OK`를 받았는데 왜 화면이 안 바뀔 수 있나요?**  
JSON API 성공은 데이터 전달 성공일 뿐 자동 navigation을 뜻하지 않는다. 이동은 JS 라우터나 별도 redirect 흐름이 있어야 한다.

**Q. `fetch`가 `200`인데 body가 login HTML인 이유는 무엇인가요?**  
보호된 API가 먼저 `302 Location: /login`을 냈고, 브라우저가 redirect를 따라가 최종 login HTML `200`을 받은 장면일 수 있다. 최종 `200`만 보고 원래 API 성공으로 읽으면 안 된다.

**Q. 로그인 성공 뒤 어떤 경우는 `302`, 어떤 경우는 JSON `200/204`가 나오는 이유는 무엇인가요?**  
페이지 요청은 다음 화면 이동이 중요해서 redirect가 자연스럽고, API 요청은 프론트 코드가 성공 여부를 읽어야 해서 JSON 응답이 자연스럽다.

## 한 줄 정리

SSR 응답은 브라우저가 바로 그릴 HTML 계약이고 JSON API 응답은 클라이언트 코드가 해석할 데이터 계약이므로, "페이지 이동"과 "API 성공 처리"를 같은 흐름으로 읽지 말아야 한다.

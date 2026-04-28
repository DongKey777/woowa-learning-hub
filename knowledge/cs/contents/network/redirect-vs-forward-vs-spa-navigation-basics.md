# Redirect vs Forward vs SPA Router Navigation 입문

> 한 줄 요약: 로그인 뒤 화면이 바뀌는 장면은 모두 같아 보여도, HTTP redirect는 브라우저가 새 요청을 보내는 것이고, server-side forward는 서버 안에서 목적지를 바꾸는 것이며, SPA router navigation은 자바스크립트가 화면과 URL을 바꾸는 것이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Network README](./README.md#redirect-vs-forward-vs-spa-router-navigation-입문)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [Spring MVC Controller 기초](../spring/spring-mvc-controller-basics.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
- [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)

retrieval-anchor-keywords: redirect vs forward basics, spa router navigation basics, login after redirect confusion, redirect forward 차이, client side navigation beginner, 302 vs forward, location header basics, why url changes after login, why url does not change after login, react router navigate basics, server side forward beginner, browser new request redirect, spa login success no 302, beginner web navigation flow

## 핵심 개념

로그인 뒤 "화면이 이동했다"는 결과만 보면 세 가지가 비슷해 보인다. 하지만 어디서 이동을 결정했는지를 보면 완전히 다르다.

- redirect: 서버가 `302`나 `303`과 `Location` 헤더를 보내고, 브라우저가 새 HTTP 요청을 만든다
- forward: 서버가 같은 요청을 내부에서 다른 controller/view로 넘긴다
- SPA router navigation: 브라우저 자바스크립트가 `history.pushState`나 라우터 API로 URL과 화면을 바꾼다

초보자가 가장 많이 헷갈리는 기준은 이것이다.

- 네트워크 탭에 `3xx`가 보이면 먼저 redirect를 의심한다
- URL이 안 바뀌는데 화면만 바뀌면 forward 가능성을 본다
- 페이지 전체 새로고침 없이 URL만 바뀌거나 API 호출 뒤 화면이 바뀌면 SPA navigation 가능성을 본다

## 같은 로그인 성공 장면을 세 칸으로 나눠 보기

입문자가 가장 많이 헷갈리는 질문은 "로그인 성공 후 홈 화면이 떴는데, 이게 redirect예요 forward예요 SPA예요?"다. 같은 결과 화면이라도 네트워크에서 보이는 흔적이 다르다.

| 겉으로 보이는 결과 | 실제 이동 주체 | DevTools에서 바로 보이는 흔적 | 초급자 한 줄 해석 |
|---|---|---|---|
| 로그인 후 주소창이 `/home`으로 바뀌고 요청이 두 줄 보인다 | redirect | `POST /login -> 302/303`, `Location: /home`, 그다음 `GET /home` | 서버가 브라우저에게 "저 URL로 다시 가라"고 시켰다 |
| 로그인 후 화면은 홈처럼 보이는데 주소창이 여전히 `/login`이다 | forward | `302` 없이 요청 한 줄만 보이고 서버 view만 바뀐다 | 브라우저는 같은 요청 하나만 보냈고, 서버 안에서 목적지만 바뀌었다 |
| 로그인 API는 `200`인데 화면이 넘어가고 URL이 바뀐다 | SPA navigation | `POST /api/login -> 200` 뒤 라우터 이동, 필요하면 추가 API 요청 | 서버 redirect가 아니라 프론트엔드 앱이 이동을 결정했다 |

## 한눈에 보기

| 구분 | 누가 이동을 결정하나 | 브라우저 새 HTTP 요청 | 주소창 URL | 로그인 뒤 흔한 모습 |
|---|---|---|---|---|
| redirect | 서버 응답의 `Location` | 있다 | 보통 바뀐다 | `POST /login -> 303 /home -> GET /home` |
| forward | 서버 내부 dispatcher/view resolver | 없다 | 그대로인 경우가 많다 | `/login` 요청을 서버가 `/WEB-INF/views/home.jsp`로 내부 전달 |
| SPA router navigation | 프론트엔드 JS/router | 페이지 이동 자체로는 없다 | 바뀔 수 있다 | `POST /api/login -> 200` 뒤 `router.push('/home')` |

짧은 기억법:

- redirect는 "브라우저야, 저 URL로 다시 가"
- forward는 "서버야, 이 요청을 내부에서 다른 곳으로 넘겨"
- SPA navigation은 "브라우저 앱이 지금 화면을 바꿔"

## 새로고침했을 때 왜 결과가 달라질까

같은 "이동"처럼 보여도, 브라우저가 마지막에 기억하는 요청이 다르기 때문에 새로고침 반응도 달라진다.

| 구분 | 브라우저가 마지막에 기억하는 것 | 새로고침 때 초보자용 해석 |
|---|---|---|
| redirect | redirect 뒤 도착한 새 URL의 응답 | 보통 도착한 `GET`을 다시 연다 |
| forward | 처음 보낸 원래 요청 | 주소창은 그대로인데 같은 요청 결과를 다시 볼 수 있다 |
| SPA router navigation | 현재 페이지 문서 + 앱 상태 | 문서 전체 새로고침이면 SPA 상태는 다시 초기화될 수 있다 |

그래서 아래처럼 읽으면 덜 헷갈린다.

- "왜 완료 화면 새로고침이 `POST` 재전송처럼 느껴지지?"면 PRG/redirect 흐름을 먼저 본다.
- "왜 화면은 홈인데 주소창은 `/login`이지?"면 forward 가능성을 먼저 본다.
- "왜 URL은 `/home`인데 새로고침하니 다시 로그인 화면으로 돌아가지?"면 SPA 상태와 서버 세션을 함께 본다.

## 상세 분해

### 1. redirect는 응답이 이동을 지시한다

redirect의 핵심 단서는 HTTP 응답이다.

```http
POST /login HTTP/1.1

HTTP/1.1 303 See Other
Location: /home
Set-Cookie: JSESSIONID=abc123; Path=/; HttpOnly
```

이 응답을 받은 브라우저는 `/home`으로 새 요청을 보낸다. 그래서 네트워크 탭에 요청이 두 줄로 보인다. login 성공 뒤 URL이 바뀌고, 새 요청의 request headers/body를 따로 볼 수 있으면 redirect 쪽이다.

### 2. forward는 서버 안에서만 목적지가 바뀐다

forward는 브라우저가 모르는 내부 이동이다. 브라우저는 여전히 처음 요청 하나만 보낸 것으로 안다.

- 브라우저 입장: `/login`으로 요청 1번
- 서버 입장: 그 요청을 내부에서 다른 controller, servlet, view로 전달

그래서 주소창 URL이 그대로일 수 있다. 서버 로그나 view 이름은 바뀌는데 네트워크에 `302`가 안 보이면 forward일 가능성이 높다.

### 3. SPA router navigation은 HTTP 상태 코드보다 JS 이벤트가 더 중요하다

SPA에서는 로그인 API가 `200 OK` JSON만 돌려주고, 그다음 이동은 프론트엔드가 결정할 수 있다.

```http
POST /api/login HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/json

{"result":"ok"}
```

그 뒤 브라우저 앱 코드가 `router.push('/home')`나 `navigate('/home')`를 호출하면 URL과 화면이 바뀐다. 이때 페이지 이동 자체는 `302`가 아니라 자바스크립트 상태 변화다. 대신 화면 진입에 필요한 API 요청이 뒤따라 나갈 수 있다.

## 흔한 오해와 함정

- URL이 바뀌면 무조건 redirect는 아니다. SPA router도 URL을 바꿀 수 있다.
- 화면이 바뀌었다고 항상 새 HTTP 문서 요청이 생기지는 않는다. SPA는 기존 HTML 안에서 컴포넌트만 바꿀 수 있다.
- `200 OK`가 보인다고 이동이 없는 것은 아니다. API 성공 뒤 JS가 navigation을 실행할 수 있다.
- forward는 브라우저 주소창이 그대로일 수 있어서 "왜 `/login`인데 홈 화면이 보이지?" 같은 혼란을 만든다.
- redirect와 forward를 섞어 생각하면 "로그인 후 요청이 두 번 간다"와 "컨트롤러에서 뷰만 바뀐다"를 같은 현상처럼 설명하게 된다.

초보자 체크 질문은 세 개면 충분하다.

1. 네트워크에 `3xx`와 `Location`이 보이는가
2. 주소창 URL이 언제 바뀌는가
3. 이동 직후 화면 변경을 브라우저가 했는가, 서버가 했는가, JS 라우터가 했는가

## 실무에서 쓰는 모습

로그인 뒤 `/orders`로 가는 세 가지 흐름을 나란히 놓으면 차이가 선명해진다.

| 시나리오 | HTTP/브라우저에서 보이는 것 | 초보자 메모 |
|---|---|---|
| SSR 로그인 redirect | `POST /login -> 302/303 Location: /orders -> GET /orders` | 브라우저가 새 요청을 만든다 |
| 서버 forward | `POST /login -> 200` 한 줄만 보이고 서버가 내부 view를 바꾼다 | 주소창이 그대로일 수 있다 |
| SPA 로그인 후 라우터 이동 | `POST /api/login -> 200` 뒤 JS가 `/orders`로 이동, 필요한 API를 추가 호출 | 이동 주체는 라우터다 |

초보자용 첫 확인 순서는 아래처럼 고정하면 된다.

1. `Status`가 `302`/`303`인지 본다.
2. `Location`이 있으면 redirect로 읽는다.
3. `3xx`가 없고 주소창이 그대로면 forward 가능성을 본다.
4. login API가 `200`인데 화면이 넘어가면 프론트엔드 router 코드를 본다.

로그인 후 혼란이 생길 때는 이렇게 읽으면 된다.

- `SavedRequest`, `Location`, `302`가 보이면 redirect 흐름부터 본다
- Spring controller/view 이름은 바뀌는데 네트워크 `3xx`가 없으면 forward를 의심한다
- React/Vue 앱에서 login API는 `200`인데 화면이 넘어가면 router navigation을 본다

## 더 깊이 가려면

- redirect 응답의 `302`/`303`/`307`, `SavedRequest`, `Set-Cookie`를 더 보고 싶다면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- 브라우저가 쿠키를 저장하고 다음 요청에 보내는 흐름을 먼저 고정하려면 [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- HTTP 응답과 브라우저 후속 동작의 큰 그림이 아직 흐리면 [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- page 렌더링 성공과 JSON API 성공 처리 자체를 먼저 분리하고 싶다면 [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- Spring MVC에서 controller, view, dispatch가 어떻게 이어지는지 보려면 [Spring MVC Controller 기초](../spring/spring-mvc-controller-basics.md), [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
- browser login loop를 `401` vs `302`로 먼저 분기하려면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)

## 면접/시니어 질문 미리보기

**Q. redirect와 forward의 가장 큰 차이는 무엇인가요?**
redirect는 브라우저가 새 요청을 보내는 것이고, forward는 서버 내부에서 같은 요청을 다른 대상으로 넘기는 것이다.

**Q. SPA에서 URL이 바뀌면 왜 네트워크에 `302`가 안 보일 수 있나요?**
URL 변경을 서버 응답이 아니라 자바스크립트 라우터가 수행하기 때문이다.

**Q. 로그인 후 `/home`으로 이동했는데 이것이 redirect인지 router navigation인지 어떻게 구분하나요?**
네트워크에 `3xx`와 `Location`이 있는지, login 응답이 `200`인지, 페이지 전체 새로고침이 있었는지를 같이 보면 된다.

## 한 줄 정리

redirect는 서버가 브라우저에게 새 요청을 시키는 것이고, forward는 서버 안에서 같은 요청의 목적지만 바꾸는 것이며, SPA router navigation은 브라우저 자바스크립트가 화면과 URL을 바꾸는 것이다.

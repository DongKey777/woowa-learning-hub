# 세션·쿠키·JWT 기초

> 한 줄 요약: HTTP는 기본적으로 상태가 없어서, 로그인 상태를 유지하려면 쿠키·서버 세션 또는 JWT 중 하나로 "이전에 인증된 사람이 다시 왔다"는 사실을 서버에게 알려야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- `[primer]` [네트워크 HTTP 상태·세션·캐시](../network/http-state-session-cache.md)
- `[primer]` [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md)
- `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
- `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
- `[follow-up]` [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md)
- `[follow-up]` [Beginner Guide to Auth Failure Responses: 401 / 403 / 404](./auth-failure-response-401-403-404.md)
- `[deep dive]` [JWT 깊이 파기](./jwt-deep-dive.md)
- `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: session cookie jwt basics, 세션 쿠키 jwt 차이, 로그인 상태 유지, http stateless, 쿠키가 뭔가요, 세션이 뭔가요, jwt 입문, jsessionid, 서버 세션 vs jwt, 토큰 기반 인증, stateless auth, cookie session beginner, 왜 로그인이 유지되나요, security readme session primer, security beginner session route, login loop beginner bridge, browser session troubleshooting path, browser session troubleshooting safe next step, cookie exists but login loops, saved request beginner, browser session troubleshooting beginner, auth basics route, auth beginner route, security beginner route, security basics route, first-step session primer, security primer next step, return to security README, browser session primer ladder, primer bridge next step, primer bridge safe next step, browser session deep dive handoff, primer follow-up deep dive ladder, safe next step auth primer, safe next step browser session, auth session primer bridge

## 핵심 개념

HTTP는 요청과 응답이 독립적이라, 같은 사용자가 두 번 요청해도 서버는 기본적으로 "처음 보는 요청"처럼 처리한다. 이걸 **무상태(stateless)**라고 한다.

로그인 상태를 유지하려면 서버가 "이 요청이 아까 로그인한 그 사람이다"라는 사실을 알 방법이 필요하다. 쿠키·세션과 JWT는 이 문제를 해결하는 서로 다른 방법이다.

## 한눈에 보기

| 방식 | 서버에 상태 저장? | 클라이언트가 보내는 것 | 장점 | 단점 |
|---|---|---|---|---|
| 서버 세션 | 저장 (세션 스토어) | 세션 ID 쿠키 | 즉시 무효화 가능 | 서버 메모리/스토어 필요 |
| JWT | 저장 안 함 | JWT 토큰 (헤더나 쿠키) | 서버 확장이 쉬움 | 만료 전 강제 무효화 어려움 |

## 상세 분해

### 쿠키란 무엇인가

쿠키는 서버가 응답에 넣어 주는 작은 키-값 데이터다. 브라우저는 이것을 저장해 뒀다가 같은 도메인 요청마다 자동으로 함께 전송한다.

서버는 응답 헤더로 쿠키를 설정한다.
```
Set-Cookie: JSESSIONID=abc123; HttpOnly; Secure
```

브라우저는 다음 요청부터 자동으로 보낸다.
```
Cookie: JSESSIONID=abc123
```

### 서버 세션 방식

1. 로그인 성공 시 서버가 세션을 만들고 세션 ID를 쿠키로 내려보낸다.
2. 브라우저가 다음 요청에 세션 ID 쿠키를 자동 첨부한다.
3. 서버가 세션 스토어에서 그 ID로 사용자 정보를 조회한다.

Spring Boot에서는 기본적으로 `JSESSIONID` 쿠키와 서버 메모리 세션을 사용한다.

### JWT 방식

JWT(JSON Web Token)는 서버가 사용자 정보를 서명해 토큰으로 만들고 클라이언트에 넘긴다. 서버는 세션을 따로 저장하지 않고, 토큰의 서명만 검증한다.

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMSJ9.SflKxwRJSMeK...
  (헤더)                (페이로드)              (서명)
```

토큰 안에 사용자 ID, 만료 시간, role 등을 담는다. 서버가 서명을 검증하면 DB를 안 봐도 사용자를 알 수 있다.

## 흔한 오해와 함정

### "JWT가 쿠키를 대체한다"

JWT는 로그인 상태 표현 방식이고, 쿠키는 토큰을 전달하는 수단이다. JWT를 쿠키에 담아 전달하는 것도 흔한 패턴이다. 둘은 층위가 다르다.

### "JWT를 쓰면 완전히 stateless다"

refresh token을 서버에서 관리하거나, 강제 로그아웃을 지원하려면 서버에 일부 상태가 필요하다. "완전 stateless"는 이상적인 목표에 가깝다.

### "쿠키는 안전하지 않다"

쿠키 자체가 위험한 게 아니라, 설정이 잘못됐을 때 위험하다. `HttpOnly`(JS에서 읽기 차단), `Secure`(HTTPS만 전송), `SameSite`(CSRF 방어) 속성을 올바르게 설정하면 쿠키도 안전하게 쓸 수 있다.

## 실무에서 쓰는 모습

Spring Security에서 세션 기반 인증을 쓰는 서비스는 로그인 후 `JSESSIONID` 쿠키를 주고, 이후 요청마다 그 쿠키로 세션을 조회한다.

JWT 기반 REST API는 로그인 후 access token을 응답하고, 클라이언트가 `Authorization: Bearer <token>` 헤더로 보낸다. Spring Security는 필터에서 토큰을 검증해 SecurityContext에 principal을 세팅한다.

어느 방식이든 "다음 요청에 인증 증거를 어떻게 보내는가"를 이해하면 흐름이 보인다.

## 로그인 루프를 보면 어디로 갈까

먼저 이렇게 자르면 덜 헷갈린다. login loop는 대개 "브라우저가 인증 증거를 다시 보내지 못했다"거나 "서버가 받은 증거로 로그인 상태를 다시 찾지 못했다"는 뜻이다.

| 지금 보이는 증상 | 다음 단계 |
|---|---|
| `/login`으로 다시 튀고 `SavedRequest`가 낯설다 | [Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)에서 redirect / navigation memory 가지부터 따라간다. |
| `Application > Cookies`에는 값이 있는데 request `Cookie` header가 비어 보인다 | 같은 entrypoint에서 cookie scope 분기를 따라가고, 필요하면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 내려간다. |
| cross-origin `fetch`에서 `credentials: "include"`와 CORS, cookie scope가 같이 헷갈린다 | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)에서 request 옵션, CORS 응답 정책, cookie scope를 먼저 나눈다. |
| request에는 cookie가 실리는데 서버가 다시 로그인시킨다 | 같은 entrypoint에서 server session / BFF translation 분기로 들어가 원인을 좁힌다. |

깊은 Spring 문서로 바로 점프하기보다, 먼저 [Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)에서 증상을 갈라 놓고 내려가면 beginner 기준으로 읽는 순서가 훨씬 안정적이다.

## 더 깊이 가려면

- 보안 입문 문서 묶음으로 돌아가기: [Security README 기본 primer 묶음](./README.md#기본-primer)
- JWT 내부 구조와 검증 방법: [JWT 깊이 파기](./jwt-deep-dive.md)
- 401/403 응답과의 연결: [Beginner Guide to Auth Failure Responses: 401 / 403 / 404](./auth-failure-response-401-403-404.md)

## 면접/시니어 질문 미리보기

> Q: 서버 세션 방식과 JWT 방식의 차이는 무엇인가요?
> 의도: 상태 저장 위치와 확장성 트레이드오프를 이해하는지 확인
> 핵심: 서버 세션은 서버에 상태를 저장하고 즉시 무효화가 쉽다. JWT는 서버 확장이 쉽지만 만료 전 강제 무효화가 어렵다.

> Q: 쿠키의 HttpOnly와 Secure 속성은 왜 쓰나요?
> 의도: 쿠키 보안 속성의 의미를 아는지 확인
> 핵심: HttpOnly는 JS에서 쿠키 접근 차단(XSS 방어), Secure는 HTTPS에서만 전송.

## 한 줄 정리

HTTP의 무상태성 때문에 로그인 상태를 유지하려면 세션 ID 쿠키 또는 JWT 토큰을 매 요청에 함께 보내야 하며, 쿠키는 HttpOnly·Secure·SameSite 속성을 챙겨야 안전하다.

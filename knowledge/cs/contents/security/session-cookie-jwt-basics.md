---
schema_version: 3
title: 세션·쿠키·JWT 기초
concept_id: security/session-cookie-jwt-basics
canonical: true
category: security
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
aliases:
- session cookie jwt
- cookie session jwt
- 세션 쿠키 JWT
- 로그인 상태 유지
- HTTP stateless
- JSESSIONID
- server session vs JWT
intents:
- definition
linked_paths:
- contents/security/authentication-authorization-session-foundations.md
- contents/network/cookie-session-jwt-browser-flow-primer.md
- contents/security/signed-cookies-server-sessions-jwt-tradeoffs.md
- contents/security/browser-401-vs-302-login-redirect-guide.md
- contents/network/http-state-session-cache.md
- contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md
forbidden_neighbors:
- contents/security/xss-csrf-basics.md
expected_queries:
- 쿠키 세션 JWT가 뭐가 달라?
- 왜 로그인 상태가 유지돼?
- JSESSIONID는 뭐고 JWT랑은 뭐가 달라?
- cookie는 있는데 왜 다시 로그인되는지 보려면 어디서 시작해?
---

# 세션·쿠키·JWT 기초

> 한 줄 요약: HTTP는 기본적으로 상태가 없어서, 로그인 상태를 유지하려면 쿠키·서버 세션 또는 JWT 중 하나로 "이전에 인증된 사람이 다시 왔다"는 사실을 서버에게 알려야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- `[primer]` [네트워크 HTTP 상태·세션·캐시](../network/http-state-session-cache.md)
- `[primer]` [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md)
- `[follow-up primer]` [인증·인가·세션 기초 흐름](./authentication-authorization-session-foundations.md)
- `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
- `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
- `[follow-up]` [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md)
- `[follow-up]` [Beginner Guide to Auth Failure Responses: 401 / 403 / 404](./auth-failure-response-401-403-404.md)
- `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: session cookie jwt basics, 세션 쿠키 jwt 차이, 로그인 상태 유지, http stateless, 쿠키가 뭔가요, 세션이 뭔가요, jwt 뭐예요, 왜 로그인이 유지되나요, 쿠키 세션 jwt 헷갈림, jsessionid, 서버 세션 vs jwt, 토큰 기반 인증, spring security 들어가기 전, 쿠키는 있는데 왜 다시 로그인, 토큰 valid인데 왜 403

## 10초 선택표

이 문서는 `cookie`, `session`, `JWT`를 같은 층위로 섞지 않게 만드는 beginner primer다. 아래 질문이 더 직접적이면 그 문서로 먼저 가도 된다.

| 지금 더 궁금한 것 | 먼저 볼 문서 | 이 문서를 먼저 볼 필요가 없는 경우 |
|---|---|---|
| `로그인됐는데 왜 403이지?` | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) | 세션 continuity보다 authz 판단이 먼저 궁금할 때 |
| `브라우저에서 왜 다시 /login으로 가요?` | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) | 이미 redirect / cookie / session mapping 디버깅을 시작한 상태일 때 |
| `cookie, session, JWT가 각각 뭐예요?` | 이 문서 | 전달 수단과 로그인 상태 복원 방식을 한 장으로 먼저 잡고 싶을 때 |
| `server session과 JWT 중 뭘 고르죠?` | [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md) | 이미 기본 정의는 알고 있고 선택 기준이 궁금할 때 |

## 먼저 한 문장씩만 분리하기

처음 읽을 때 가장 많이 섞이는 것은 `cookie`, `session`, `JWT`가 같은 층위처럼 보인다는 점이다. 먼저 이렇게 끊어 읽으면 된다.

| 용어 | 한 문장 mental model | 초보자 오해 |
|---|---|---|
| cookie | 브라우저가 다음 요청에 다시 들고 가는 작은 표 | cookie 자체가 곧 로그인 방식이라고 생각함 |
| session | 서버가 "그 표 번호의 로그인 기록"을 다시 찾는 방식 | session이 브라우저 안 객체라고 생각함 |
| JWT | 로그인 정보를 서명해서 직접 들고 다니는 토큰 | JWT를 쓰면 cookie가 아예 사라진다고 생각함 |

즉 `cookie는 전달 수단`, `session과 JWT는 로그인 상태를 이어 가는 대표 방식`으로 먼저 보면 덜 헷갈린다.

## 10초 비교표: 무엇을 보내고, 어디서 복원하나

`cookie`, `header`, `session`, `JWT`를 한 표에 올려두면 층위가 다르다는 점이 더 빨리 보인다.

| 비교 대상 | 주로 답하는 질문 | 보통 어디에 있나 | beginner 한 줄 메모 |
|---|---|---|---|
| cookie | 브라우저가 다음 요청에 뭘 자동으로 보내나 | 브라우저 저장소 + request `Cookie` header | 전달 수단이다 |
| `Authorization` header | API client가 토큰을 어떻게 붙이나 | request header | 전달 수단이다 |
| server session | 서버가 로그인 상태를 어디서 다시 찾나 | 서버 메모리 / 세션 스토어 | 서버가 상태를 들고 있다 |
| JWT | 서버가 로그인 정보를 어떤 형태로 검증하나 | 토큰 자체의 서명된 payload | 토큰이 상태 힌트를 들고 다닌다 |

처음에는 `무엇을 보내는가`와 `어떻게 복원하는가`만 분리해도 충분하다.

## 핵심 개념

HTTP는 요청과 응답이 독립적이라, 같은 사용자가 두 번 요청해도 서버는 기본적으로 "처음 보는 요청"처럼 처리한다. 이걸 **무상태(stateless)**라고 한다.

로그인 상태를 유지하려면 서버가 "이 요청이 아까 로그인한 그 사람이다"라는 사실을 알 방법이 필요하다. 쿠키·세션과 JWT는 이 문제를 해결하는 서로 다른 방법이다.

처음에는 아래 한 줄만 정확히 잡아도 충분하다.

`cookie/header = 어떻게 보내나` / `session/JWT = 무엇을 근거로 다시 로그인 상태를 복원하나`

## 한눈에 보기

| 방식 | 서버에 상태 저장? | 클라이언트가 보내는 것 | 장점 | 단점 |
|---|---|---|---|---|
| 서버 세션 | 저장 (세션 스토어) | 세션 ID 쿠키 | 즉시 무효화 가능 | 서버 메모리/스토어 필요 |
| JWT | 저장 안 함 | JWT 토큰 (헤더나 쿠키) | 서버 확장이 쉬움 | 만료 전 강제 무효화 어려움 |

처음 읽는다면 이렇게만 잡아도 충분하다.

- "브라우저가 자동으로 붙여 보내는 표"가 쿠키다.
- "서버가 그 표 번호를 보고 로그인 기록을 찾는 방식"이 서버 세션이다.
- "표 자체에 로그인 정보를 서명해서 담아 보내는 방식"이 JWT다.

## beginner safe ladder

처음엔 이 문서 하나로 끝내려 하기보다 `network primer -> security primer -> 증상 guide` 순서만 고정하면 된다.

| 지금 막힌 질문 | 여기서 맡는 역할 | 다음 안전한 한 걸음 |
|---|---|---|
| `쿠키, 세션, JWT가 뭐가 다른지부터 헷갈려요` | 전달 수단과 복원 방식을 분리한다 | [인증·인가·세션 기초 흐름](./authentication-authorization-session-foundations.md) |
| `왜 로그인 후 상태가 유지되나요`, `JSESSIONID가 왜 보여요` | browser 전송과 server 복원을 나눈다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| `cookie 있는데 왜 다시 로그인돼요`, `API가 login HTML을 받아요` | redirect, cookie 전송, server 복원 중 어디가 깨졌는지 자른다 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| `token valid인데 왜 403`, `로그인됐는데 이 API만 403` | authz gate를 먼저 분리한다 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) |
| `Spring Security 문서에서 SavedRequest, SessionCreationPolicy가 갑자기 나와요` | deep dive 전에 symptom branch를 고른다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

한 줄 route: [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md) -> 이 문서 -> [인증·인가·세션 기초 흐름](./authentication-authorization-session-foundations.md) -> `401/403/404` 또는 login redirect guide

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

작게 다시 말하면 이렇다.

- `cookie vs header`는 "어떻게 보낼까" 문제다.
- `server session vs jwt`는 "무엇을 근거로 로그인 상태를 복원할까" 문제다.

### "session을 쓰면 JWT는 절대 안 쓴다"

실서비스에서는 둘이 함께 등장할 수 있다. 예를 들어 browser에는 session cookie만 보이고, BFF나 gateway 뒤에서는 서버가 downstream API 호출용 JWT를 따로 들고 있을 수 있다.

즉 "브라우저와 서버 사이"의 증거와 "서버와 다른 서비스 사이"의 증거가 다를 수 있다. 이 문서에서는 그 둘을 같은 층위로 섞지 않는 것이 핵심이다.

### "JWT를 쓰면 완전히 stateless다"

refresh token을 서버에서 관리하거나, 강제 로그아웃을 지원하려면 서버에 일부 상태가 필요하다. "완전 stateless"는 이상적인 목표에 가깝다.

### "쿠키는 안전하지 않다"

쿠키 자체가 위험한 게 아니라, 설정이 잘못됐을 때 위험하다. `HttpOnly`(JS에서 읽기 차단), `Secure`(HTTPS만 전송), `SameSite`(CSRF 방어) 속성을 올바르게 설정하면 쿠키도 안전하게 쓸 수 있다.

## 바로 떠올릴 예시

로그인 후 마이페이지를 다시 여는 장면으로 보면 흐름이 단순해진다.

| 방식 | 로그인 직후 | 다음 요청에서 서버가 보는 것 |
|---|---|---|
| 서버 세션 | 서버가 세션을 만들고 `JSESSIONID`를 내려준다 | `Cookie: JSESSIONID=...`를 보고 서버가 세션 저장소를 다시 조회한다 |
| JWT | 서버가 access token을 내려준다 | `Authorization: Bearer ...` 또는 쿠키 안 토큰을 보고 서명을 검증한다 |

여기서는 "다음 요청에 인증 증거를 어떻게 다시 보내는가"까지만 이해하면 충분하다. `SecurityContext`, refresh token rotation, 강제 로그아웃 설계 같은 운영 이슈는 follow-up 문서로 넘기는 편이 안전하다.

## 가장 흔한 장면 3개

아래 세 장면만 떠올려도 `cookie`, `session`, `JWT`가 언제 같이 나오고 언제 따로 나오는지 감이 잡힌다.

| 장면 | 브라우저/클라이언트가 주로 보내는 것 | 서버가 복원하거나 검증하는 것 | 초보자 포인트 |
|---|---|---|---|
| 전통적인 웹 로그인 | `Cookie: JSESSIONID=...` | 서버 세션 | cookie는 표, session은 서버 기록이다 |
| SPA + BFF | browser cookie, 필요 시 CSRF token | BFF session + 서버 쪽 downstream token | browser가 JWT를 꼭 직접 들고 있지는 않다 |
| 모바일/외부 API 호출 | `Authorization: Bearer ...` | JWT 서명, 만료, audience | header로 보내도 결국 핵심은 토큰 검증이다 |

## 문제가 생기면 여기서 깊게 파지 말고 분기한다

beginner 단계에서 login loop나 cookie incident를 이 문서 안에서 끝까지 파고들 필요는 없다. 먼저 "어디 층에서 막혔는가"만 고르고, 원인 수사는 다음 문서로 넘기는 편이 덜 헷갈린다.

| 지금 보이는 증상 | 여기서 먼저 고정할 질문 | 다음 단계 |
|---|---|---|
| `/login`으로 다시 튀고 `SavedRequest`가 낯설다 | redirect/login 흐름 문제인가 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| `Application > Cookies`에는 값이 있는데 request `Cookie` header가 비어 보인다 | 저장은 됐는데 전송이 안 되는가 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| request에는 cookie나 token이 보이는데도 거절된다 | 전달보다 auth/authz 해석이 문제인가 | [Beginner Guide to Auth Failure Responses: 401 / 403 / 404](./auth-failure-response-401-403-404.md) |

duplicate cookie, proxy mismatch, cross-origin `fetch`, BFF translation 같은 세부 branch는 위 문서들에서 한 단계씩만 더 내려가면 된다. 이 문서의 역할은 원인 수사보다 `세션/쿠키/JWT가 각각 어떤 인증 증거인지`를 구분해 주는 데 있다.

## 더 깊이 가려면

- 보안 입문 문서 묶음으로 돌아가기: [Security README 기본 primer 묶음](./README.md#기본-primer)
- 저장 위치, 무효화, 서버 상태 trade-off를 한 번 더 비교하기: [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md)
- JWT 내부 구조와 검증 방법은 beginner primer 다음 단계에서만: [JWT 깊이 파기](./jwt-deep-dive.md)
- 401/403 응답과의 연결: [Beginner Guide to Auth Failure Responses: 401 / 403 / 404](./auth-failure-response-401-403-404.md)

## 한 줄 정리

HTTP는 기본적으로 무상태라서 로그인 상태를 이어 주는 별도 증거가 필요하고, 보통 browser cookie나 `Authorization` header 같은 전달 수단 위에 server session 또는 JWT 같은 복원 방식을 얹어 사용한다.

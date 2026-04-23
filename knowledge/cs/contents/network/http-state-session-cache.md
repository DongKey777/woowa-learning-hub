# HTTP의 무상태성과 쿠키, 세션, 캐시

**난이도: 🟡 Intermediate**

> 신입 백엔드 개발자가 웹 요청의 상태 관리와 캐싱을 설명하기 위한 핵심 정리

> 관련 문서:
> - [Cache-Control 실전](./cache-control-practical.md)
> - [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
> - [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md)
> - [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
> - [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
> - [API Gateway Auth Rate Limit Chain](./api-gateway-auth-rate-limit-chain.md)
> - [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)
> - [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)
> - [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - [BFF Session Store Outage / Degradation Recovery](../security/bff-session-store-outage-degradation-recovery.md)
> - [Spring OAuth2 + JWT 통합](../spring/spring-oauth2-jwt-integration.md)

retrieval-anchor-keywords: HTTP stateless, cookie, session, JWT, HTTP cache, Set-Cookie, Cookie header, session id, browser state, browser cookie storage flow, JWT header vs cookie, personalization cache, login state, cookie session spring security route, beginner auth bridge, why login state is kept, hidden JSESSIONID, SessionCreationPolicy basics, browser auth primer route, session basics to SavedRequest, login loop starter, 401 302 bounce starter, login redirect primer, post-login original URL, cookie 있는데 다시 로그인, cookie는 있는데 session missing

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [다음 단계 브리지](#다음-단계-브리지)
- [HTTP는 왜 Stateless인가](#http는-왜-stateless인가)
- [쿠키](#쿠키)
- [세션](#세션)
- [JWT와의 차이](#jwt와의-차이)
- [HTTP 캐시](#http-캐시)
- [추천 공식 자료](#추천-공식-자료)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 중요한가

백엔드 개발자는 로그인 상태를 유지해야 하고, 응답 속도도 신경 써야 한다.  
이때 자주 나오는 개념이

- HTTP의 무상태성
- 쿠키
- 세션
- 캐시

다.

### Retrieval Anchors

- `HTTP stateless`
- `cookie`
- `session`
- `JWT`
- `HTTP cache`
- `Set-Cookie`
- `session id`
- `login state`

---

## 다음 단계 브리지

기초 개념을 읽고 바로 Spring/security deep dive로 점프하면 `cookie`, `session`, `JWT`, `stateless`, `hidden JSESSIONID`가 같은 말처럼 섞이기 쉽다.
아래 순서로 올라가면 안전하다.

1. 브라우저가 `Set-Cookie`를 저장하고 `Cookie`나 `Authorization`으로 다시 보내는 장면부터 보기: [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
2. 상태를 누가 보관하는지 비교: [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)
3. Spring Security가 요청 앞단에서 인증 상태를 어떻게 다루는지 보기: [Spring Security 아키텍처](../spring/spring-security-architecture.md)
4. browser login redirect, `302`, 숨은 `JSESSIONID`, 원래 URL 복귀가 한꺼번에 헷갈리면: [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
5. 로그인 후 원래 URL 복귀나 `302` bounce가 꼬이면: [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)
6. `STATELESS`인데 `JSESSIONID`가 생기거나 다음 요청에서 다시 익명이 되면: [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
7. 브라우저는 로그인돼 보이는데 API만 loop를 돌거나 `cookie는 있는데 session missing`처럼 보이면: [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md) -> [BFF Session Store Outage / Degradation Recovery](../security/bff-session-store-outage-degradation-recovery.md)

증상별로 다시 고르면 더 빠르다.

- `로그인 후 다시 /login으로 간다`, `SavedRequest 때문에 loop가 난다`: `RequestCache` / `SavedRequest`
- `redirect 응답에도 cookie가 저장되나`, `왜 login 전에도 JSESSIONID가 보이지`: [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- `왜 숨은 JSESSIONID가 생기지`, `세션 안 쓰려는데 왜 stateful처럼 보이지`: `SecurityContextRepository` / `SessionCreationPolicy`
- `cookie는 보이는데 서버는 세션을 못 찾는다`, `브라우저는 로그인돼 보이는데 API만 돈다`: browser/BFF translation -> BFF session store

---

## HTTP는 왜 Stateless인가

HTTP는 기본적으로 **이전 요청을 기억하지 않는 프로토콜**이다.

즉 같은 사용자가 연속해서 요청을 보내도,

- 서버는 기본적으로 이전 요청과 현재 요청을 자동으로 연결하지 않는다.

이 성질을 Stateless라고 부른다.

### 장점

- 서버 구조가 단순하다
- 확장하기 쉽다

### 단점

- 로그인 상태 같은 걸 따로 관리해야 한다

---

## 쿠키

쿠키는 **서버가 브라우저에 저장하라고 내려주는 작은 데이터**다.

서버는 응답 헤더에 `Set-Cookie`를 넣고,
브라우저는 이후 요청에 `Cookie` 헤더로 다시 보낸다.

### 주로 쓰는 목적

- 로그인 상태 유지
- 사용자 설정 유지
- 간단한 식별 정보 저장

### 주의

- 쿠키는 브라우저에 저장된다
- 민감한 정보를 그대로 넣는 것은 위험하다

---

## 세션

세션은 **서버 쪽에 사용자 상태를 저장하는 방식**이다.

보통 흐름은:

1. 서버가 세션 저장소에 사용자 상태를 만든다
2. 세션 ID를 쿠키로 브라우저에 보낸다
3. 이후 요청마다 브라우저가 세션 ID를 보낸다
4. 서버가 세션 저장소에서 상태를 찾는다

즉 보통

- 쿠키 = 세션 ID 전달 수단
- 세션 = 서버 측 상태 저장

으로 같이 쓰인다.

---

## JWT와의 차이

세션과 JWT는 로그인 상태를 유지한다는 점에서 비슷하지만 다르다.

### 세션

- 상태를 서버에 저장
- 브라우저에는 세션 ID만 둠

### JWT

- 토큰 자체에 정보를 담음
- 서버가 세션 저장소를 꼭 갖지 않아도 됨

즉 세션은 **서버 저장 중심**, JWT는 **토큰 자체 중심**이라고 보면 된다.

---

## HTTP 캐시

캐시는 **이전에 받은 응답을 다시 재사용해서 응답 속도를 높이는 방식**이다.

대표 헤더:

- `Cache-Control`
- `Expires`
- `ETag`
- `Last-Modified`

### 왜 중요한가

- 서버 부하를 줄인다
- 응답 속도를 높인다
- 네트워크 비용을 줄인다

### 주의

개인화된 응답은 캐시 전략을 조심해야 한다.  
로그인 사용자별 응답을 잘못 캐시하면 정보가 섞일 수 있다.

---

## 추천 공식 자료

- MDN HTTP Cookies:
  - https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies
- MDN HTTP Caching:
  - https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching
- HTTP Semantics RFC:
  - https://httpwg.org/specs/rfc9110.html

---

## 면접에서 자주 나오는 질문

### Q. HTTP가 Stateless라는 것은 무슨 뜻인가요?

- 서버가 기본적으로 이전 요청 상태를 기억하지 않는다는 뜻이다.

### Q. 쿠키와 세션의 차이는 무엇인가요?

- 쿠키는 브라우저에 저장되는 데이터다.
- 세션은 서버 쪽 상태 저장 방식이다.
- 보통 세션 ID를 쿠키로 전달한다.

### Q. 세션과 JWT 차이는 무엇인가요?

- 세션은 상태를 서버에 저장하고, JWT는 토큰 자체에 정보를 담는다.

### Q. 캐시를 왜 사용하나요?

- 응답 속도를 높이고 서버 부하를 줄이기 위해 사용한다.

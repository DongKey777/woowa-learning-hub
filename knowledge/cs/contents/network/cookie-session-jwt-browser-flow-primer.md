# Cookie / Session / JWT 브라우저 흐름 입문

> 한 줄 요약: 브라우저는 응답의 `Set-Cookie`를 보고 쿠키를 저장하고, 조건이 맞는 다음 HTTP 요청에 `Cookie` 헤더로 자동 전송한다. 세션 인증은 그 쿠키 안의 session id로 서버 상태를 찾고, JWT 인증은 토큰을 `Authorization` 헤더나 cookie에 실어 검증한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)
> - [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
> - [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)
> - [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)
> - [API Gateway Auth Rate Limit Chain](./api-gateway-auth-rate-limit-chain.md)
> - [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)
> - [CSRF in SPA + BFF Architecture](../security/csrf-in-spa-bff-architecture.md)
> - [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)

retrieval-anchor-keywords: cookie session jwt browser flow, browser cookie flow, Set-Cookie to Cookie, browser cookie storage rules, browser automatic cookie sending, session cookie vs persistent cookie, cookie domain path secure samesite, HttpOnly Secure SameSite basics, SameSite HttpOnly Secure matrix, cookie attribute matrix, Domain Path cookie scope, host-only cookie, JSESSIONID browser flow, hidden JSESSIONID route, login request response auth primer, login redirect primer, 302 login flow, SavedRequest beginner bridge, JWT Authorization header, Bearer token browser flow, JWT in cookie, authorization bearer vs cookie, cookie-based auth primer, beginner auth bridge, why login state is kept, fetch credentials cookie, same-origin vs same-site, cross-origin cookie fetch, why cookie not sent on fetch

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [한 번에 보는 전체 흐름](#한-번에-보는-전체-흐름)
- [쿠키는 브라우저가 저장하는 운반 수단이다](#쿠키는-브라우저가-저장하는-운반-수단이다)
- [브라우저는 언제 쿠키를 전송하나](#브라우저는-언제-쿠키를-전송하나)
- [세션 인증은 요청에서 어떻게 보이나](#세션-인증은-요청에서-어떻게-보이나)
- [JWT 인증은 요청에서 어떻게 보이나](#jwt-인증은-요청에서-어떻게-보이나)
- [세 가지 방식을 한 표로 비교](#세-가지-방식을-한-표로-비교)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 이 문서가 필요한가

입문 단계에서 가장 많이 섞이는 단어가 `cookie`, `session`, `JWT`다.

- `cookie`: 브라우저가 저장하고 전송하는 데이터
- `session`: 서버가 사용자 상태를 저장하는 방식
- `JWT`: 토큰 내용을 표현하는 형식

즉 셋은 같은 층위의 개념이 아니다.

- cookie는 **브라우저 쪽 전달 수단**
- session은 **서버 쪽 상태 저장 방식**
- JWT는 **토큰 형식과 검증 방식**

이 구분이 서면 "브라우저가 무엇을 저장하고", "HTTP 요청에 무엇이 실리고", "서버가 무엇을 확인하는가"가 한 번에 정리된다.

### Retrieval Anchors

- `cookie session jwt browser flow`
- `Set-Cookie to Cookie`
- `browser cookie storage rules`
- `browser automatic cookie sending`
- `JWT Authorization header`
- `JWT in cookie`
- `authorization bearer vs cookie`
- `hidden JSESSIONID route`

---

## 한 번에 보는 전체 흐름

로그인 이후 브라우저 요청 흐름을 아주 단순화하면 아래 셋 중 하나다.

```text
1. Session cookie
   login 응답: Set-Cookie: JSESSIONID=abc...
   다음 요청: Cookie: JSESSIONID=abc...
   서버 동작: session id로 서버 저장소를 조회

2. JWT in Authorization header
   login 응답: access token 반환
   다음 요청: Authorization: Bearer eyJ...
   서버 동작: JWT 서명/만료/claim 검증

3. JWT in cookie
   login 응답: Set-Cookie: access_token=eyJ...
   다음 요청: Cookie: access_token=eyJ...
   서버 동작: cookie에서 JWT를 꺼내 서명/만료/claim 검증
```

핵심 차이는 이렇다.

- session cookie는 **브라우저가 자동 전송**하고, 서버는 **추가로 session store를 조회**한다
- `Authorization: Bearer` JWT는 **브라우저가 자동 전송하지 않고**, 앱 코드가 헤더를 넣는다
- JWT를 cookie에 넣으면 **브라우저 자동 전송은 session과 비슷해지지만**, 서버 검증 방식은 session lookup이 아니라 token validation이 된다

---

## 쿠키는 브라우저가 저장하는 운반 수단이다

서버는 응답 헤더의 `Set-Cookie`로 브라우저에 값을 저장하라고 알려준다.

예:

```http
HTTP/1.1 200 OK
Set-Cookie: JSESSIONID=abc123; Path=/; HttpOnly; Secure; SameSite=Lax
Content-Type: application/json

{"message":"login success"}
```

브라우저는 보통 아래 정보를 기준으로 쿠키를 관리한다.

- 이름과 값
- 어느 호스트에 보낼지 (`Domain`)
- 어느 경로에 보낼지 (`Path`)
- HTTPS에서만 보낼지 (`Secure`)
- 자바스크립트에서 읽을 수 있는지 (`HttpOnly`)
- cross-site 상황에서 보낼지 (`SameSite`)
- 언제까지 유지할지 (`Max-Age`, `Expires`)

여기서 중요한 점:

- 쿠키는 **브라우저 저장소에 있다**
- 쿠키는 **HTTP 요청에 실리는 운반 수단**이다
- 쿠키 값이 꼭 세션 ID일 필요는 없다
- 쿠키 안에 JWT가 들어갈 수도 있고, 테마 설정값이 들어갈 수도 있다

또한 쿠키는 크게 두 종류로 많이 나눈다.

- session cookie: `Max-Age`나 `Expires` 없이 브라우저 세션 동안 유지
- persistent cookie: 만료 시각을 가진 쿠키

즉 "session cookie"라는 표현은 **세션 인증 방식**이 아니라 **브라우저 저장 수명**을 가리킬 때도 있어 문맥을 구분해야 한다.

---

## 브라우저는 언제 쿠키를 전송하나

브라우저는 저장된 모든 쿠키를 아무 요청에나 붙이지 않는다.
대략 아래 조건을 보고 맞는 쿠키만 `Cookie` 헤더에 넣는다.

- 요청 host가 `Domain` 규칙에 맞는가
- 요청 path가 `Path` 규칙에 맞는가
- HTTPS 요청인데 `Secure` 조건을 만족하는가
- same-site / cross-site 상황에서 `SameSite` 규칙을 만족하는가

조건이 맞으면 브라우저가 자동으로 이런 요청을 만든다.

```http
GET /me HTTP/1.1
Host: app.example.com
Cookie: JSESSIONID=abc123; theme=dark
Accept: application/json
```

이때 보통 브라우저 자바스크립트가 직접 `Cookie` 헤더를 조립하는 것은 아니다.
브라우저가 저장된 쿠키를 보고 자동으로 붙인다.

입문 단계에서 같이 알아두면 좋은 점:

- 같은 출처 요청에서는 cookie 자동 전송을 쉽게 체감한다
- 다른 출처로 `fetch`할 때는 `credentials` 설정과 CORS 정책이 함께 영향을 준다
- `HttpOnly`는 "JS가 읽지 못하게" 하는 옵션이지 "브라우저가 보내지 않게" 하는 옵션은 아니다

`SameSite`, `HttpOnly`, `Secure`, `Domain`, `Path`를 속성별로 따로 떼어 보고 싶다면 [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)를 같이 보면 된다.

`app.example.com -> api.example.com`처럼 same-site이지만 cross-origin인 경우의 cookie 전송 규칙은 [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)에서 따로 정리한다.

즉 `HttpOnly` cookie는 자바스크립트에서는 안 보여도, 요청에는 여전히 실릴 수 있다.

---

## 세션 인증은 요청에서 어떻게 보이나

세션 방식에서는 보통 서버가 로그인 성공 시 **서버 저장소에 사용자 상태를 만들고**, 브라우저에는 **그 상태를 찾을 수 있는 session id만** 보낸다.

흐름은 대개 이렇다.

1. 브라우저가 `POST /login` 요청을 보낸다
2. 서버가 인증 성공 후 session store에 사용자 상태를 저장한다
3. 서버가 `Set-Cookie: JSESSIONID=...`를 응답한다
4. 브라우저가 이후 요청마다 `Cookie: JSESSIONID=...`를 자동 전송한다
5. 서버가 session id로 사용자 상태를 다시 찾는다

요청/응답 모양을 보면:

```http
POST /login HTTP/1.1
Host: app.example.com
Content-Type: application/json

{"username":"neo","password":"secret"}
```

```http
HTTP/1.1 200 OK
Set-Cookie: JSESSIONID=s%3Aabc123; Path=/; HttpOnly; Secure; SameSite=Lax
Content-Type: application/json

{"message":"ok"}
```

```http
GET /me HTTP/1.1
Host: app.example.com
Cookie: JSESSIONID=s%3Aabc123
Accept: application/json
```

이 요청을 받은 서버는 보통 이렇게 생각한다.

- cookie에서 `JSESSIONID`를 꺼낸다
- 그 값으로 session store를 조회한다
- 해당 세션에 연결된 사용자 정보를 가져온다

즉 session 방식의 핵심은:

- 브라우저에는 **식별자**
- 서버에는 **실제 로그인 상태**

가 있다는 점이다.

---

## JWT 인증은 요청에서 어떻게 보이나

JWT는 "브라우저가 자동 전송하는가"보다 먼저 **토큰의 내용과 검증 형식**을 설명하는 말이다.

JWT를 요청에 싣는 대표 방식은 두 가지다.

### 1. `Authorization` 헤더에 넣는 방식

이 방식에서는 login 응답 뒤에 브라우저 앱 코드가 토큰을 보관하고, 다음 요청마다 직접 헤더를 넣는다.

```http
GET /me HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOi...
Accept: application/json
```

이 경우:

- 브라우저가 자동으로 `Authorization` 헤더를 붙여주지 않는다
- 프론트엔드 코드나 클라이언트 코드가 직접 넣는다
- 서버는 session store 조회 대신 JWT를 검증한다

즉 session cookie와 가장 큰 차이는 **자동 전송이 아니라 앱 코드 전송**이라는 점이다.

### 2. JWT를 cookie에 넣는 방식

JWT도 cookie에 담을 수 있다.

```http
HTTP/1.1 200 OK
Set-Cookie: access_token=eyJhbGciOi...; Path=/; HttpOnly; Secure; SameSite=Lax
```

그러면 다음 요청은 이렇게 보일 수 있다.

```http
GET /me HTTP/1.1
Host: app.example.com
Cookie: access_token=eyJhbGciOi...
Accept: application/json
```

이 방식은 겉보기에는 session cookie와 비슷하다.
둘 다 browser가 cookie를 자동 전송하기 때문이다.

하지만 서버 쪽 해석은 다르다.

- session cookie: session id로 **서버 상태 조회**
- JWT cookie: token을 직접 **서명/만료/claim 검증**

그래서 "JWT니까 무조건 header"도 아니고, "cookie에 있으면 곧 session"도 아니다.

---

## 세 가지 방식을 한 표로 비교

| 방식 | 브라우저가 자동 전송하나 | 서버가 요청에서 읽는 값 | 서버가 주로 하는 일 | beginner 주의점 |
|---|---|---|---|---|
| session cookie | 그렇다 | session id | session store 조회 | cookie와 session을 같은 개념으로 보면 안 된다 |
| JWT in `Authorization` | 아니다 | bearer token | JWT 검증 | 브라우저가 자동으로 붙여준다고 생각하면 안 된다 |
| JWT in cookie | 그렇다 | JWT token | JWT 검증 | cookie 기반이라 CSRF 경계가 다시 중요해진다 |

이 표를 보면 구분이 쉬워진다.

- cookie는 전송 방식에 가깝다
- session은 서버 상태 조회 전략이다
- JWT는 토큰 검증 전략이다

---

## 자주 헷갈리는 포인트

### 1. cookie와 session은 동의어가 아니다

많이 같이 쓰일 뿐이다.

- cookie: 브라우저 저장/전송
- session: 서버 저장/조회

session id를 cookie로 전달하는 경우가 흔해서 같이 묶여 보일 뿐이다.

### 2. JWT도 cookie에 담을 수 있다

그래서 "JWT vs cookie"는 비교가 어색하다.

- 더 정확한 비교는 `session vs JWT`
- 또는 `cookie transport vs Authorization header transport`

이다.

### 3. `HttpOnly`가 붙어도 브라우저는 cookie를 전송한다

`HttpOnly`는 자바스크립트 접근 제한용이다.
브라우저 자동 전송 자체를 막는 옵션이 아니다.

### 4. cookie를 쓴다고 무조건 stateful은 아니다

JWT를 cookie에 담고 서버가 매 요청 token만 검증하면, transport는 cookie여도 서버 상태 조회는 없을 수 있다.
반대로 opaque token을 `Authorization` 헤더로 보내도 서버가 매번 DB나 session store를 보면 stateful한 면이 생긴다.

즉 stateless/stateful은 **서버 검증 전략**까지 봐야 한다.

### 5. JWT를 cookie에 넣으면 CSRF를 다시 봐야 한다

브라우저가 cookie를 자동 전송하기 때문이다.
그래서 JWT 자체는 token 형식이지만, cookie transport를 선택하는 순간 `SameSite`, CSRF token, Origin 검증 같은 주제가 다시 중요해진다.

이 지점은 [CSRF in SPA + BFF Architecture](../security/csrf-in-spa-bff-architecture.md)로 이어진다.

### 6. 실무에서는 섞어서 쓰는 경우가 많다

예:

- 브라우저에는 session cookie만 노출
- 서버 BFF는 내부적으로 downstream JWT를 관리
- access token은 짧게, refresh token은 별도 cookie나 서버 저장소로 관리

그래서 단순히 "우리 서비스는 JWT를 쓴다"만으로는 실제 browser flow를 설명하기 부족할 수 있다.

---

## 면접에서 자주 나오는 질문

### Q. 브라우저는 cookie를 언제 요청에 붙이나요?

- `Domain`, `Path`, `Secure`, `SameSite` 같은 규칙이 맞을 때 붙인다.
- 같은 출처 요청에서는 자동 전송을 쉽게 볼 수 있고, cross-origin fetch는 `credentials`와 CORS 조건도 본다.

### Q. session과 cookie의 차이는 무엇인가요?

- cookie는 브라우저 저장/전송 수단이다.
- session은 서버가 사용자 상태를 저장하는 방식이다.
- 흔히 session id를 cookie로 전달한다.

### Q. JWT는 왜 `Authorization` 헤더에 넣기도 하고 cookie에 넣기도 하나요?

- JWT는 토큰 형식이라 transport가 하나로 고정되지 않는다.
- 헤더에 넣으면 앱 코드가 직접 붙이고, cookie에 넣으면 브라우저가 자동 전송한다.

### Q. JWT를 cookie에 넣으면 session과 완전히 같아지나요?

- 아니다.
- 브라우저 동작은 비슷해져도 서버는 session store를 조회할 수도 있고, JWT를 직접 검증할 수도 있다.

### Q. `HttpOnly` cookie면 CSRF를 신경 쓰지 않아도 되나요?

- 아니다.
- `HttpOnly`는 JS 읽기를 막는 옵션이고, 브라우저 자동 전송은 계속 일어날 수 있다.

## 한 줄 정리

cookie는 브라우저의 저장/전송 수단이고, session은 서버 상태 저장 방식이며, JWT는 토큰 형식이다. 브라우저 요청에서 이 셋이 만나는 지점은 결국 "`Set-Cookie`로 저장되고 `Cookie`나 `Authorization`으로 어떻게 다시 실리느냐"다.

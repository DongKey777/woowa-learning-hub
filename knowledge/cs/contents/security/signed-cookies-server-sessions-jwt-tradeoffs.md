# Signed Cookies / Server Sessions / JWT Tradeoffs

> 한 줄 요약: signed cookie, server session, JWT는 모두 인증 상태를 담지만, 누가 상태를 들고 누가 검증하는지에 따라 CSRF, revocation, 확장성의 균형이 달라진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - `[primer]` [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - `[primer]` [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md)
> - `[primer]` [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
> - `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
> - `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
> - `[primer bridge]` [Browser BFF Session Boundary Primer](../system-design/browser-bff-session-boundary-primer.md)
> - `[follow-up]` [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - `[follow-up]` [Session Fixation / Clickjacking / CSP](./session-fixation-clickjacking-csp.md)
> - `[deep dive]` [JWT 깊이 파기](./jwt-deep-dive.md)
> - `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
> - `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md)
> - `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: signed cookie, server session, JWT, HttpOnly cookie, session store, CSRF, revocation, stateless auth, browser auth, session fixation, cookie auth, session regeneration, federated login fixation, browser session coherence, login hardening path, browser auth primer, cookie session spring security route, beginner auth bridge, hidden JSESSIONID, why login state is kept, primer follow-up deep dive ladder, beginner ladder auth session, browser session route alignment, safe next step before deep dive

## 먼저 멈출 beginner 사다리

이 문서는 beginner primer가 아니라 `comparison deep dive`다.
처음 배우는 독자는 `무엇이 저장되고 누가 검증하는가`만 먼저 고정한 뒤에만 이 문서로 내려오는 편이 안전하다.

| 지금 막힌 질문 | 먼저 멈출 문서 | 여기까지 오기 전에 고정할 것 | 이 문서를 여는 시점 |
|---|---|---|---|
| `cookie`, `session`, `JWT`가 아직 같은 말처럼 들려요 | [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md) -> [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md) | `운반 수단`과 `서버 복원 방식`을 분리한다 | 기본 정의를 한 문장으로 말할 수 있을 때 |
| `cookie 있는데 왜 다시 로그인돼요`, `SavedRequest`가 보여요 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) | `redirect`, `cookie-missing`, `server-anonymous` 중 어느 branch인지 자른다 | login loop 원인이 비교 자체가 아니라는 점을 확인한 뒤 |
| `브라우저는 cookie를 보내는데 서버는 왜 token을 들고 있죠?` | [Browser BFF Session Boundary Primer](../system-design/browser-bff-session-boundary-primer.md) | browser session과 server-side token translation을 같은 층위로 섞지 않는다 | browser + BFF와 mobile/API bearer 경계를 비교하고 싶을 때 |

## 이 문서 다음에 보면 좋은 문서

- `cookie`, `session`, `JWT` 기본 정의가 아직 헷갈리면 한 단계 뒤로 가서 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md) -> [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md) -> [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md) 순서로 먼저 고정하는 편이 안전하다.
- 로그인 루프나 `SavedRequest` 증상으로 이어지면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) 순서로 먼저 분기한 다음 deep dive로 내려간다.
- browser cookie와 server-side token translation을 함께 보고 싶지만 Spring deep dive까지는 아직 이르다면 [Browser BFF Session Boundary Primer](../system-design/browser-bff-session-boundary-primer.md)에서 browser/session과 downstream token의 경계를 먼저 고정한다.
- browser auth 선택지 비교를 Spring 요청 처리 흐름으로 연결하려면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 이어 가면 된다.
- cookie/session hardening 관점의 fixation과 clickjacking 묶음은 [Session Fixation / Clickjacking / CSP](./session-fixation-clickjacking-csp.md)로 이어진다.
- OAuth/OIDC callback 이후 session regeneration이 왜 필요한지는 [Session Fixation in Federated Login](./session-fixation-in-federated-login.md)에서 더 구체적으로 볼 수 있다.
- browser login hardening 문서를 cluster 형태로 다시 고르려면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아가 redirect, fixation, storage 축을 한 번에 다시 잡으면 된다.

---

## 핵심 개념

세 가지는 모두 "로그인 상태"를 전달하지만 상태의 위치가 다르다.

- `signed cookie`: 브라우저가 값을 들고 있고, 서버는 서명으로 위변조를 막는다
- `server session`: 서버가 상태를 저장하고, 브라우저는 session id만 들고 있다
- `JWT`: 브라우저나 클라이언트가 서명된 토큰을 들고 다닌다

각 선택은 다음 질문에 답해야 한다.

- 상태를 누가 저장하는가
- 누가 revocation을 담당하는가
- 브라우저가 자동 전송하는가
- 서버를 얼마나 stateless하게 만들 것인가

즉 "쿠키 vs 세션 vs JWT"가 아니라 "상태와 신뢰 경계를 어디에 둘 것인가"가 핵심이다.

---

## 깊이 들어가기

### 1. signed cookie는 서버 상태를 줄일 수 있다

signed cookie는 cookie 값이 변조되지 않았음을 서버가 확인할 수 있게 한다.

장점:

- 서버 저장소 의존이 적다
- 구현이 단순해 보인다
- 서버가 cookie 내용 일부를 직접 읽을 수 있다

단점:

- cookie 자체가 자동 전송되므로 CSRF를 다시 봐야 한다
- revocation이 어렵다
- cookie 크기 제한이 있다

### 2. server session은 revocation이 쉽다

server session은 전통적으로 브라우저 웹앱에 강하다.

장점:

- logout, forced logout, account disable이 쉽다
- session fixation 방어와 결합하기 좋다
- 세션 상태를 서버가 통제한다

단점:

- shared session store가 필요하다
- 수평 확장이 복잡해진다
- store 장애가 로그인 경로를 흔든다

### 3. JWT는 확장성이 좋지만 폐기가 어렵다

JWT는 stateless에 가깝고, API와 모바일에 잘 맞는다.

장점:

- 검증이 로컬에서 가능하다
- distributed environment에 유리하다
- gateway와 잘 맞는다

단점:

- revoke가 늦다
- browser storage 전략이 중요하다
- 너무 많은 claim을 넣으면 stale policy가 된다

### 4. signed cookie와 JWT는 브라우저에서 비슷해 보이지만 다르다

둘 다 cookie에 넣을 수 있지만 의미는 다르다.

- signed cookie는 cookie가 곧 세션 상태일 수 있다
- JWT cookie는 서명된 bearer token이다

둘 다 CSRF 관점이 필요하다.
즉 "쿠키에 넣었으니 안전"도, "JWT니까 CSRF가 없다"도 아니다.

### 5. 선택은 클라이언트 유형에 따라 달라진다

- 브라우저 중심 웹앱: server session 또는 signed cookie가 단순할 수 있다
- SPA + API: JWT 또는 BFF + cookie 전략이 흔하다
- mobile / service: JWT가 잘 맞는다

---

## 실전 시나리오

### 시나리오 1: 브라우저 웹앱에서 logout가 꼭 즉시 반영돼야 함

대응:

- server session을 고려한다
- session store를 공유한다
- session version / revoke를 함께 쓴다

### 시나리오 2: API와 모바일이 같은 auth를 쓰고 싶음

대응:

- JWT를 짧게 운용한다
- refresh 회전과 revoke를 별도로 둔다
- 민감 경로는 session-like 상태를 추가한다

### 시나리오 3: signed cookie를 썼더니 CSRF가 터짐

대응:

- CSRF token과 SameSite를 적용한다
- Origin 검증을 추가한다
- state-changing endpoint를 분리한다

---

## 코드로 보기

### 1. server session 개념

```java
public void login(HttpServletRequest request, User user) {
    request.getSession(true).setAttribute("userId", user.id());
}
```

### 2. signed cookie 개념

```java
public ResponseCookie issueCookie(String payload, String signature) {
    return ResponseCookie.from("auth", payload + "." + signature)
        .httpOnly(true)
        .secure(true)
        .sameSite("Lax")
        .build();
}
```

### 3. JWT 개념

```java
public String issueJwt(User user) {
    return JWT.create()
        .withSubject(user.id().toString())
        .withExpiresAt(Date.from(Instant.now().plusSeconds(900)))
        .sign(algorithm);
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| signed cookie | 단순하고 가볍다 | CSRF와 revoke가 어렵다 | 제한된 상태 전달 |
| server session | revoke가 쉽다 | shared store가 필요하다 | 브라우저 중심 웹 |
| JWT | 분산 환경에 강하다 | 폐기와 storage 전략이 어렵다 | API, mobile, SPA |

판단 기준은 이렇다.

- logout 즉시성이 중요한가
- 브라우저 자동 전송이 허용되는가
- shared session store를 운영할 수 있는가
- 클라이언트가 stateful 상태를 유지할 수 있는가

---

## 꼬리질문

> Q: signed cookie와 JWT 쿠키의 차이는 무엇인가요?
> 의도: 쿠키라는 전달 수단과 내용 의미를 구분하는지 확인
> 핵심: 둘 다 쿠키를 쓰지만, signed cookie는 상태 자체가 다를 수 있다.

> Q: server session이 왜 revoke에 유리한가요?
> 의도: 중앙 상태 관리의 장점을 이해하는지 확인
> 핵심: 서버 저장소에서 즉시 삭제하면 되기 때문이다.

> Q: JWT가 왜 revocation에 불리한가요?
> 의도: stateless의 대가를 아는지 확인
> 핵심: 이미 발급된 토큰은 만료 전까지 살아남기 쉽기 때문이다.

> Q: cookie 기반 인증에서 왜 CSRF를 다시 봐야 하나요?
> 의도: 자동 전송 경계를 이해하는지 확인
> 핵심: 브라우저가 자동으로 요청에 쿠키를 붙이기 때문이다.

## 한 줄 정리

signed cookie, server session, JWT는 모두 인증 상태를 전달하지만, revocation과 CSRF와 확장성의 균형이 다르다.

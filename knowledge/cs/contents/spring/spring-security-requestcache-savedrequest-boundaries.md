# Spring Security `RequestCache` / `SavedRequest` Boundaries

> 한 줄 요약: Spring Security의 로그인 후 원래 URL 복귀는 `RequestCache`와 `SavedRequest`가 만드는 별도 흐름이므로, 브라우저 UX와 API/stateless 경계를 분리하지 않으면 302 redirect, hidden session 생성, login loop가 쉽게 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)
> - [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - [Spring OAuth2 + JWT 통합](./spring-oauth2-jwt-integration.md)
> - [OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)
> - [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
> - [BFF Session Store Outage / Degradation Recovery](../security/bff-session-store-outage-degradation-recovery.md)
> - [CSRF in SPA + BFF Architecture](../security/csrf-in-spa-bff-architecture.md)
> - [Session Revocation at Scale](../security/session-revocation-at-scale.md)
> - [Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md)
> - [Security README: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)
> - [Security README: Session / Boundary / Replay](../security/README.md#session--boundary--replay)
> - [Session Store Design at Scale](../system-design/session-store-design-at-scale.md)

retrieval-anchor-keywords: RequestCache, SavedRequest, DefaultSavedRequest, HttpSessionRequestCache, login redirect, saved request redirect, original URL after login, post-login redirect original URL, request cache stateless api, request cache beginner route, 302 login loop, auth session troubleshooting, BFF login redirect, hidden session, hidden JSESSIONID, hidden session beginner bridge, hidden session creation, cookie exists but session missing, logout redirect confusion, saved request debugging, API returns login HTML, OAuth2 login success redirect, SavedRequestAwareAuthenticationSuccessHandler, sid mapping, back-channel logout, post-login redirect vs logout mapping, post-login session persistence, security readme session bridge, security session boundary bridge, session boundary replay bundle, session basics to SavedRequest, session basics to Spring Security, SavedRequest beginner bridge, login loop beginner bridge, cookie 있는데 다시 로그인, browser 401 302 /login bounce, 401 302 bounce starter, hidden JSESSIONID next step, next request anonymous after login, browser session troubleshooting return path, security browser session troubleshooting path, login loop return path, spring security primer ladder return, spring readme security route, beginner return path to spring readme, /admin 302 login final 403, admin 302 -> login -> final 403, 로그인 후 원래 admin 복귀 403, 왜 login 갔다가 마지막 403, savedrequest final 403 beginner, beginner-safe handoff, safe next doc before requestcache, redirect navigation memory deep dive, spring deep dive after browser guide

## 입문 브리지

이 문서는 beginner ladder의 `follow-up deep dive`다. beginner-safe handoff는 먼저 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)에서 branch를 고정하고, 그다음에만 이 문서를 여는 것이다.
즉 이 문서는 `safe next doc` 자체가 아니라, `SavedRequest`, `saved request bounce`, `원래 URL 복귀`가 **`redirect / navigation memory`**로 확정된 뒤에 읽는 고정 deep dive다.
검색에서 바로 들어와 "관리자 URL이 `302 /login`인데 이게 왜 `403`이랑 다른가요?", "로그인 후 원래 `/admin`으로 복귀했는데 왜 마지막엔 `403`인가요?"를 먼저 묻는 독자라면 deep dive보다 초급 분기 문서로 먼저 내려보내는 편이 이탈을 줄인다.
반대로 `cookie 있는데 다시 로그인`, `hidden session`, `next request anonymous after login`처럼 **`server persistence / session mapping`** 쪽이 먼저 보이면 이 문서를 오래 붙잡지 말고 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 바로 갈아탄다.

### `/admin 302 -> login -> final 403` 먼저 끊어 읽기

beginner가 advanced 문서에 너무 빨리 들어오는 대표 장면이 이것이다.

```text
/admin 요청
-> 302 /login
-> 로그인 성공
-> 원래 /admin 으로 복귀
-> final 403
```

이 한 줄 증상을 통째로 보면 "`SavedRequest`가 문제인가?", "`권한이 없나?", "`세션이 날아갔나?"가 한꺼번에 섞인다. 먼저 아래 분기표로 **어느 단계까지는 정상인지**부터 고정한다.

| 지금 보인 장면 | 먼저 붙일 해석 라벨 | 바로 갈 next step |
|---|---|---|
| `/admin`에서 곧바로 `302 /login` | `인증 전 redirect` | [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)에서 `302`와 `403`를 먼저 분리 |
| 로그인 성공 후 원래 `/admin`으로 돌아옴 | `SavedRequest 복귀는 일단 성공` | 이 문서에서 `redirect / navigation memory` 축을 본다 |
| 복귀 직후 최종 `403` | `복귀와 인가 실패를 분리해야 함` | [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md)에서 role mapping을 먼저 확인 |
| 로그인 후 다시 `/login`으로 튐 | `복귀 후 인증 유지 실패 또는 loop` | [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 이동해 persistence를 본다 |

- 핵심 mental model은 이것이다: `302 /login`은 **인증 전 이동**, `원래 /admin 복귀`는 **주소 메모 재생**, `final 403`은 **복귀 후 인가 실패**일 수 있다.
- 그래서 "`/admin 302 -> login -> final 403`" 검색으로 들어온 독자는 이 문서를 처음부터 끝까지 읽기보다, 먼저 "복귀는 성공했는가, 마지막 막힘은 권한인가"를 분리해야 advanced 오진입이 줄어든다.

| 증상 alias | 고정 next-step label | 이 문서에서 보는 축 |
|---|---|---|
| `SavedRequest`, `saved request bounce`, `원래 URL 복귀` | `redirect / navigation memory` | `RequestCache` / `SavedRequest`가 만든 redirect 복귀 |
| `API가 login HTML을 받음`, `browser 401 -> 302 /login bounce` | `browser redirect / API contract` | browser용 redirect 정책이 API 계약에 섞였는지 |
| `cookie 있는데 다시 로그인`, `cookie exists but session missing`, `next request anonymous after login` | `server persistence / session mapping` | 이 문서보다 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)가 우선이다 |

- `cookie`, `session`, `JWT` 차이 자체가 아직 흐리면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md) -> [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md) -> [Spring Security 아키텍처](./spring-security-architecture.md) 순으로 먼저 올라온다.
- 검색 질문이 아직 "`302 /login`이랑 `403` 차이가 뭐예요", "`SavedRequest`가 왜 나오죠" 수준이라면 먼저 [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)로 내려가 `인증 전 redirect`와 `인증 후 권한 실패`를 분리하고 다시 올라온다.
- primer에서 `SavedRequest`, `saved request bounce`, `browser 401 -> 302 /login bounce`, `원래 URL 복귀` 같은 handoff alias로 올라왔다면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)에서 `safe next doc`을 먼저 고른 뒤 [Security README: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)로 돌아와 redirect/navigation memory branch를 확정하고 이 문서에서 **navigation memory / redirect 복귀** 축만 깊게 본다.
- `로그인 성공 후 원래 /admin URL 복귀`, `복귀 직후 403`, `SavedRequest는 되는데 admin 권한이 막힘`처럼 redirect 복귀와 role mapping이 한 장면에 같이 보이면, deep dive 전에 [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md)에서 `복귀`와 `인가 실패`를 두 단계로 먼저 분리한다.
- 너무 일찍 올라왔다고 느껴지면 먼저 [Spring README의 Spring + Security primer ladder](./README.md#spring--security)로 돌아가 entrypoint를 다시 고른다. 그다음 이 문서로 복귀할 때는 "로그인 후 원래 URL 복귀가 이상한가?" 질문 하나만 들고 온다.
- 그 다음 `로그인 후 다시 /login으로 튄다`, `보호 페이지로 돌아가자마자 또 인증하라고 한다`, `API가 401 대신 HTML login page를 준다`면 이 문서에서 `SavedRequest` / `RequestCache`를 먼저 분리한다.
- 같은 primer handoff라도 `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login`처럼 **다음 요청 인증 유지** 쪽이 핵심이면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 이어 간다.
- 브라우저 cookie는 남아 있는데 서버가 session/token translation을 못 찾아 `hidden session mismatch`처럼 보이면 [BFF Session Store Outage / Degradation Recovery](../security/bff-session-store-outage-degradation-recovery.md)까지 내려가 browser/BFF 경계를 확인한다.
- route가 아직 흐리면 이 문서를 붙잡고 있지 말고 [Security README: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)로 돌아가 request `Cookie` header, redirect `Location`, server anonymous 세 갈래부터 다시 고른다.
- 이 문서를 읽고 나면 다음 단계는 둘 중 하나로 고정한다: `redirect / navigation memory`면 여기서 계속, `server persistence / session mapping`이면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 이동한다. 경로가 다시 섞이면 [Spring README의 Spring + Security primer ladder](./README.md#spring--security)로 즉시 되돌아간다.

## 핵심 개념

브라우저 로그인 흐름에서는 사용자가 보호된 URL로 갔다가 인증 후 원래 URL로 돌아오는 UX가 중요하다.

Spring Security는 이를 위해:

- `RequestCache`
- `SavedRequest`

를 쓴다.

즉 인증 실패 시 단순히 401/302를 주는 것이 아니라, **원래 요청을 잠시 저장하고 인증 후 복귀시키는 흐름**이 하나 더 생긴다.

이걸 모르면 다음이 헷갈린다.

- 왜 세션을 안 쓰려는데 `JSESSIONID`가 생기지
- 왜 API가 401 대신 로그인 페이지 302로 가지
- 왜 로그인 후 어떤 경로는 원래 페이지로 돌아가고 어떤 경로는 기본 홈으로 가지

## 깊이 들어가기

### 1. request cache는 인증 전 요청을 임시 저장한다

전형적인 브라우저 흐름은 이렇다.

- 보호된 URL 요청
- Security가 인증 필요 판단
- 요청 정보를 cache에 저장
- 로그인 페이지로 redirect
- 인증 성공
- saved request가 있으면 원래 URL로 redirect

즉 `RequestCache`는 인증 자체보다, **인증 전후 사용자 이동 흐름을 이어주는 장치**다.

### 2. 기본 구현은 세션 기반과 잘 맞는다

대표 구현 감각:

- `HttpSessionRequestCache`
- `DefaultSavedRequest`

브라우저 웹 앱에는 자연스럽지만, API 서버에는 쉽게 문제를 만든다.

- 세션이 생길 수 있다
- 302 redirect가 튀어나온다
- stateless 기대와 어긋난다

### 3. entry point와 request cache를 같이 봐야 한다

보호된 리소스에 익명 사용자가 접근하면 Security는 보통 entry point로 보낸다.

이때 request cache가 켜져 있으면:

- 그냥 막는 것이 아니라
- 원래 요청을 저장하고
- 로그인 뒤 복귀 흐름까지 만든다

즉 302 문제는 entry point만의 문제가 아니라, **entry point + request cache 조합** 문제다.

### 4. API와 브라우저는 거의 항상 다른 정책이 낫다

브라우저 UI:

- 로그인 redirect 자연스러움
- saved request 유용함

API:

- 401/403 JSON 필요
- saved request 불필요하거나 해롭다
- 세션 생성 최소화 필요

그래서 API 체인에서는 대개 request cache를 끈다.

```java
http.requestCache(request -> request.disable());
```

### 5. 로그인 성공 후 어디로 갈지는 success handler와도 엮인다

request cache만 보는 것으로 끝나지 않는다.

- form login success handler
- OAuth2 login success handler
- default target URL
- saved request 우선순위

즉 로그인 후 redirect 이상은 saved request와 success handler 정책을 같이 봐야 한다.

### 6. saved request는 revoke lookup이 아니라 navigation memory다

OAuth2 login에서는 더 쉽게 헷갈린다. 로그인 성공 직후 같은 타이밍에

- saved request 소비
- local session/security context persistence
- `(issuer, sid/sub)` logout mapping 저장

이 함께 일어날 수 있기 때문이다.

하지만 역할은 다르다.

- saved request: 원래 URL 복귀용
- security context/session persistence: 다음 요청 인증 유지용
- OIDC session mapping: 나중에 back-channel logout이 왔을 때 revoke lookup용

즉 saved request가 남아 있다고 해서 logout propagation 근거가 생기는 것은 아니다. 반대로 back-channel logout이 잘 들어와도 saved request loop나 redirect 이상은 별도로 남을 수 있다.

### 7. 운영에서는 redirect loop와 숨은 session 생성으로 자주 드러난다

대표 징후:

- 로그인 후 다시 같은 보호 페이지에서 loop
- API client가 302를 따라가다가 HTML을 받음
- stateless라 생각했는데 세션 쿠키가 생김

이 경우 request cache가 숨어들었는지 먼저 보는 편이 빠르다.

## 실전 시나리오

### 시나리오 1: SPA/API 서버인데 401 대신 로그인 페이지 302가 온다

브라우저용 entry point와 request cache가 API 체인에 섞였을 수 있다.

### 시나리오 2: 로그인 후 어떤 경우만 원래 URL이 아니라 홈으로 간다

saved request 유무 또는 success handler/default target URL 우선순위가 달랐을 수 있다.

### 시나리오 3: `STATELESS`인데 세션 쿠키가 생긴다

security context 저장소뿐 아니라 request cache가 세션을 만들었을 가능성이 있다.

### 시나리오 4: 로그인 redirect loop가 생긴다

보호 URL 정책, 로그인 페이지 허용, saved request 재사용 흐름이 꼬였을 수 있다.

## Auth Session Troubleshooting Flow

### 0. 개념이 먼저 흔들리면 기초 브리지로 한 번 올라간다

- `SavedRequest`, `hidden JSESSIONID`, `SessionCreationPolicy`가 왜 한 질문에 같이 나오는지 모르겠다면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md) -> [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md) -> [Spring Security 아키텍처](./spring-security-architecture.md) 순으로 용어 축을 먼저 맞춘다.

### 1. `302`와 login loop는 먼저 saved request 문제인지 확인한다

- 보호 URL 접근 직후 login page로 튀고, 로그인 후 같은 URL로 되돌아간다면 request cache가 살아 있는 것이다.
- API나 BFF endpoint가 JSON 대신 HTML login page를 받는다면 [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)와 함께 봐서 브라우저용 redirect chain이 API chain에 섞였는지 확인한다.

### 2. logout 이상은 request cache만으로 끝내지 않는다

logout 후 다시 보호 URL로 bounce되거나 이전 URL로 되돌아가면 두 층을 나눠 봐야 한다.

- redirect 자체가 이상하면 이 문서와 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)부터 본다.
- cookie는 비웠는데 server-side token이나 session mapping이 남아 있으면 [Session Revocation at Scale](../security/session-revocation-at-scale.md), [Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md), [Session Store Design at Scale](../system-design/session-store-design-at-scale.md)로 내려가야 한다.
- OIDC provider logout와 함께 봐야 한다면, redirect 복귀는 이 문서에서 보고 `sid`/`sub` 기반 revoke lookup은 [OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md)로 분리해 본다.

### 3. BFF에서는 request 복귀와 token 번역을 따로 추적한다

saved request는 원래 URL 복귀 UX일 뿐이고, provider refresh token이나 downstream audience token cache까지 정리하지는 않는다. 브라우저 logout는 끝났는데 일부 API만 계속 통과하면 request cache보다 BFF/session-store/revocation 경계를 먼저 의심하는 편이 맞다.

### 4. OAuth2 login 이후에는 redirect와 persistence를 순서대로 좁힌다

- 로그인 후 landing URL만 이상하면 success handler와 saved request 정책부터 본다.
- 로그인은 성공했는데 다음 요청에서 다시 익명이라면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 넘어가 post-login persistence를 본다.
- logout token은 들어오는데 revoke가 안 먹는다면 [Spring OAuth2 + JWT 통합](./spring-oauth2-jwt-integration.md), [OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md) 순서로 `sid` mapping 저장 위치를 확인한다.

## 코드로 보기

### API 체인에서 request cache 비활성화

```java
@Bean
SecurityFilterChain apiChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/api/**")
        .requestCache(request -> request.disable())
        .build();
}
```

### 브라우저 체인에서 기본 흐름 유지

```java
@Bean
SecurityFilterChain webChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/app/**", "/login/**")
        .formLogin(Customizer.withDefaults())
        .build();
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 기본 request cache 사용 | 브라우저 로그인 UX가 자연스럽다 | 세션/redirect가 숨어들 수 있다 | 서버 렌더링 웹 앱 |
| API에서 request cache 비활성화 | stateless/API 계약이 선명하다 | 로그인 후 복귀 UX는 없다 | REST API, SPA 백엔드 |
| 체인 분리 | 경계가 명확하다 | 설정이 조금 더 복잡하다 | API + web 혼합 서비스 |
| 전역 기본값 유지 | 구현은 단순해 보인다 | 브라우저 UX와 API 계약이 서로 망가진다 | 가급적 피함 |

핵심은 request cache를 인증 필수 기능으로 보지 않고, **브라우저 로그인 복귀 UX를 위한 선택적 기능**으로 보는 것이다.

## 꼬리질문

> Q: `RequestCache`는 무엇을 해결하는가?
> 의도: saved request 흐름 이해 확인
> 핵심: 인증 전 요청을 저장했다가 인증 후 원래 URL로 복귀하게 돕는다.

> Q: API에서 request cache를 끄는 이유는 무엇인가?
> 의도: browser/API 경계 구분 확인
> 핵심: 302 redirect와 세션 생성이 API 계약을 흐릴 수 있기 때문이다.

> Q: `STATELESS`인데 세션이 생길 수 있는 이유는 무엇인가?
> 의도: 숨은 세션 생성 지점 이해 확인
> 핵심: request cache 같은 보안 기능이 세션을 만들 수 있기 때문이다.

> Q: 로그인 후 redirect가 이상할 때 무엇을 같이 봐야 하는가?
> 의도: success handler와 saved request 관계 확인
> 핵심: entry point만이 아니라 request cache와 success handler 우선순위를 함께 봐야 한다.

## 한 줄 정리

`RequestCache`와 `SavedRequest`는 브라우저 로그인 복귀 UX를 위한 기능이지, API 경계에 그대로 두어도 되는 기본값은 아니다.

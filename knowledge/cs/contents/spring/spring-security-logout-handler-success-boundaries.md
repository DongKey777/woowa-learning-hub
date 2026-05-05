# Spring Security `LogoutHandler` / `LogoutSuccessHandler` Boundaries

> 한 줄 요약: Spring Security의 logout 체인은 현재 요청에서 local session과 응답 흐름을 정리하는 경계일 뿐이며, cookie 삭제나 logout success redirect만으로 BFF token cache 정리, distributed revoke, federated logout 완료까지 보장되지는 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Logout Scope Primer](../security/logout-scope-primer.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - [Spring Security `RequestCache` / `SavedRequest` Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
> - [Spring OAuth2 + JWT 통합](./spring-oauth2-jwt-integration.md)
> - [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
> - [Session Revocation at Scale](../security/session-revocation-at-scale.md)
> - [OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md)
> - [BFF Session Store Outage / Degradation Recovery](../security/bff-session-store-outage-degradation-recovery.md)
> - [Session Inventory UX / Revocation Scope Design](../security/session-inventory-ux-revocation-scope-design.md)
> - [Session Store Design at Scale](../system-design/session-store-design-at-scale.md)

retrieval-anchor-keywords: LogoutFilter, LogoutHandler, LogoutSuccessHandler, SecurityContextLogoutHandler, CookieClearingLogoutHandler, logout success redirect, logoutSuccessUrl, local logout, cookie deletion, session invalidation, BFF token cache cleanup, provider refresh token revoke, downstream audience token cache, RP-initiated logout, OIDC logout success handler, back-channel logout, federated logout, sid mapping, logout propagation, security readme session bridge, security session boundary bridge, session boundary replay bundle

## 먼저 자를 질문

logout 문서는 "`지금 브라우저 한 탭을 정리하는 문제인가`", "`이 기기 전체나 모든 기기를 끊는 문제인가`", "`IdP까지 같이 끊는 문제인가`"를 먼저 가르는 것이 핵심이다.

| 지금 먼저 묻는 질문 | 먼저 갈 문서 | 이 문서를 여는 시점 |
|---|---|---|
| "`현재 세션`과 `모든 기기 로그아웃`이 같은 말인가요?" | [Logout Scope Primer](../security/logout-scope-primer.md) | revoke scope 용어를 이미 고정했고, 이제 Spring logout 체인의 local 경계를 보고 싶을 때 |
| "cookie는 지웠는데 BFF나 서버 세션이 왜 남죠?" | [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md) | browser pointer와 server credential을 분리한 뒤 local cleanup 누락을 보고 싶을 때 |
| "IdP logout redirect도 했는데 다른 기기 세션은 왜 남죠?" | [OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md) | federated logout과 local revoke가 별개라는 전제를 잡은 뒤 |

## 핵심 개념

Spring Security logout는 보통 두 층으로 나뉜다.

1. `LogoutHandler`: 현재 요청 기준 local cleanup을 수행한다.
2. `LogoutSuccessHandler`: cleanup 이후 어떤 응답을 보낼지 정한다.

여기서 중요한 오해가 있다.

- cookie를 지웠다
- `HttpSession`을 invalidate했다
- `/logout`가 `200`/`204`/redirect로 끝났다

이 셋은 어디까지나 **현재 브라우저 요청의 local completion signal**이다.  
여기에는 보통 다음이 자동으로 포함되지 않는다.

- BFF 서버측 token cache 정리
- refresh token family revoke
- 다른 device/session invalidate
- cluster 전역 revoke propagation
- 외부 IdP까지 포함한 federated logout 완료

즉 Spring logout 성공과 distributed revoke 완료는 다른 단계다.

---

## 깊이 들어가기

### 1. `LogoutHandler`와 `LogoutSuccessHandler`는 책임이 다르다

`LogoutHandler`는 side effect를 만든다.

- `SecurityContext` clear
- `HttpSession` invalidate
- cookie/header 제거
- local mapping cleanup

반면 `LogoutSuccessHandler`는 response contract를 만든다.

- `204 No Content`
- 로그인 페이지나 홈으로 redirect
- RP-initiated logout redirect 시작
- JSON body 반환

즉 success handler가 "성공 응답"을 만들었다고 해서 revoke plane 전체가 닫혔다고 보면 안 된다.

### 2. cookie 삭제는 session pointer 제거일 뿐이다

브라우저 cookie를 지우면 사용자는 대개 "로그아웃됐다"고 느낀다.  
하지만 실제로 끊어야 할 상태는 더 많을 수 있다.

- server-side session store row
- provider refresh/access token set
- BFF가 보관한 audience token cache
- remember-me token
- 다른 탭이나 다른 device의 session graph

특히 BFF 구조에서는 cookie가 **pointer**이고, 실제 credential은 서버에 있다.  
pointer만 지우고 서버 credential을 남겨 두면 반쯤만 로그아웃한 것이다.

### 3. BFF logout는 최소 세 개의 저장 경계를 같이 봐야 한다

BFF 구조에서는 보통 아래 매핑이 있다.

- browser session cookie
- local session store / security context
- provider token store + downstream audience cache

그래서 logout scope를 먼저 구분해야 한다.

- 현재 브라우저만 종료
- 이 앱의 모든 device/session 종료
- IdP 세션까지 포함한 federated logout

첫 번째는 Spring logout 체인만으로 닫히는 경우가 있다.  
두 번째와 세 번째는 보통 별도 revoke event, session graph cleanup, provider-side logout 설계가 필요하다.

### 4. RP-initiated logout과 back-channel logout은 방향이 다르다

Spring의 `LogoutSuccessHandler`는 outbound 흐름을 시작하기 좋다.

- 사용자가 `/logout` 호출
- local cleanup 수행
- IdP end-session endpoint로 redirect

이건 RP-initiated logout에 가깝다.

반면 back-channel logout은 inbound 흐름이다.

- IdP가 RP의 logout endpoint에 server-to-server 호출
- `logout_token` 검증
- `sid`/`sub` 기준 local session 및 refresh family revoke

즉 `OidcClientInitiatedLogoutSuccessHandler`를 붙였다고 해서 back-channel logout을 구현한 것은 아니다.

### 5. "logout success"와 "full revoke complete"는 metric을 분리해야 한다

운영 지표를 하나로 합치면 헷갈린다.

- `logout_http_success_total`
- `browser_cookie_cleared_total`
- `local_session_invalidated_total`
- `bff_token_cache_evicted_total`
- `refresh_family_revoked_total`
- `backchannel_logout_processed_total`
- `revocation_fanout_lag_seconds`

첫 줄은 프레임워크 success고, 마지막 줄들은 coherence 지표다.

---

## 실전 시나리오

### 시나리오 1: `/logout`는 204인데 어떤 API는 계속 통과한다

문제:

- cookie와 `SecurityContext`는 정리됐지만
- BFF audience token cache나 refresh token family가 남아 있다
- 이미 발급된 self-contained access token TTL도 살아 있다

대응:

- logout handler에서 local session id와 token cache mapping을 함께 지운다
- access token TTL과 revoke 반영 지표를 따로 본다
- 필요한 경우 [Session Revocation at Scale](../security/session-revocation-at-scale.md), [Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md)로 내려간다

### 시나리오 2: OIDC logout redirect는 되는데 다른 기기 세션은 남아 있다

문제:

- RP-initiated logout만 있고 local session graph revoke가 부족하다
- `sid`/`sub`와 local session mapping이 약하다

대응:

- logout success redirect와 back-channel revoke를 별도 단계로 설계한다
- `(issuer, sid)` 또는 `(issuer, sub)` lookup을 둔다
- [OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md)로 이어서 본다

### 시나리오 3: "logout all devices"를 `/logout` 하나로 해결하려 한다

문제:

- 현재 요청의 local logout semantics와 전역 revoke semantics가 섞였다

대응:

- 현재 세션 종료와 전체 세션 revoke endpoint를 분리한다
- UI copy도 "현재 기기 로그아웃"과 "모든 기기 로그아웃"을 나눈다
- scope naming은 [Session Inventory UX / Revocation Scope Design](../security/session-inventory-ux-revocation-scope-design.md)에서 같이 정리한다

---

## Auth Session Troubleshooting Flow

### 1. 먼저 local browser cleanup 문제인지 본다

- cookie가 안 지워지거나 logout 이후 redirect가 이상하면 `LogoutHandler`, `LogoutSuccessHandler`, `RequestCache` 설정부터 본다
- saved request bounce가 섞이면 [Spring Security `RequestCache` / `SavedRequest` Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)를 먼저 본다

### 2. 그 다음 BFF/session store cleanup을 본다

- cookie는 사라졌는데 BFF가 provider token이나 audience token을 계속 재사용하면 [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md), [BFF Session Store Outage / Degradation Recovery](../security/bff-session-store-outage-degradation-recovery.md)로 내려간다

### 3. 마지막으로 federated logout / global revoke tail을 본다

- 다른 device가 남거나 IdP logout 이후에도 local API가 살아 있으면 [OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md), [Session Revocation at Scale](../security/session-revocation-at-scale.md), [Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md)까지 같이 본다

---

## 코드로 보기

### 1. local cleanup과 응답 흐름을 분리한 logout 설정

```java
@Bean
SecurityFilterChain webChain(HttpSecurity http,
                             LogoutHandler bffCleanupLogoutHandler,
                             LogoutSuccessHandler logoutSuccessHandler) throws Exception {
    return http
        .securityMatcher("/app/**", "/logout")
        .logout(logout -> logout
            .logoutUrl("/logout")
            .addLogoutHandler(bffCleanupLogoutHandler)
            .deleteCookies("SESSION")
            .invalidateHttpSession(true)
            .clearAuthentication(true)
            .logoutSuccessHandler(logoutSuccessHandler)
        )
        .build();
}
```

핵심은 cookie 삭제와 success response를 넣더라도, 필요한 server-side cleanup은 별도 handler로 붙여야 한다는 점이다.

### 2. BFF token cache cleanup 예시

```java
@Component
public class BffTokenCacheCleanupLogoutHandler implements LogoutHandler {
    private final BrowserSessionLinkRepository sessionLinks;
    private final ProviderTokenStore providerTokenStore;
    private final AudienceTokenCache audienceTokenCache;

    @Override
    public void logout(HttpServletRequest request,
                       HttpServletResponse response,
                       Authentication authentication) {
        HttpSession session = request.getSession(false);
        if (session == null) {
            return;
        }

        BrowserSessionLink link = sessionLinks.findByLocalSessionId(session.getId());
        if (link == null) {
            return;
        }

        providerTokenStore.deleteBySessionId(link.localSessionId());
        audienceTokenCache.evictByBrowserSession(link.browserSessionId());
    }
}
```

이 handler는 local cleanup 예시일 뿐이다.  
모든 device revoke나 refresh family global revoke는 별도 domain service/event로 올려야 한다.

### 3. RP-initiated logout success handler 예시

```java
@Bean
LogoutSuccessHandler oidcLogoutSuccessHandler(ClientRegistrationRepository registrations) {
    OidcClientInitiatedLogoutSuccessHandler handler =
            new OidcClientInitiatedLogoutSuccessHandler(registrations);
    handler.setPostLogoutRedirectUri("{baseUrl}/logged-out");
    return handler;
}
```

이 설정은 IdP end-session redirect를 시작하는 outbound flow다.  
IdP가 보내는 back-channel `logout_token` 처리 endpoint는 별도로 구현해야 한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| cookie 삭제 + 기본 success redirect | 구현이 단순하다 | local browser cleanup만 끝나기 쉽다 | 단순 웹앱, 전역 revoke 요구가 약함 |
| custom `LogoutHandler` + BFF cache cleanup | local server state까지 같이 닫는다 | session/token mapping이 필요하다 | BFF, server-side token storage |
| RP-initiated logout success handler | IdP logout UX를 연결하기 쉽다 | 다른 device/local cache revoke는 별개다 | 외부 SSO 웹앱 |
| back-channel + revoke bus + 짧은 token TTL | coherence가 가장 좋다 | 운영 복잡도가 높다 | enterprise SSO, admin, 민감 기능 |

판단 기준은 이렇다.

- logout의 의미가 현재 브라우저 종료인지, 전체 세션 revoke인지
- BFF가 provider/downstream token을 서버에 보관하는지
- IdP 세션 종료가 실제 요구사항인지
- revoke tail과 multi-device coherence를 운영할 수 있는지

---

## 꼬리질문

> Q: `LogoutHandler`와 `LogoutSuccessHandler`의 차이는 무엇인가요?
> 의도: side effect와 response contract 구분 확인
> 핵심: 전자는 local cleanup, 후자는 cleanup 이후 응답 흐름이다.

> Q: cookie를 지웠는데 왜 완전 로그아웃이 아닐 수 있나요?
> 의도: browser pointer와 server credential 구분 확인
> 핵심: BFF token cache, refresh token, 다른 device session이 남을 수 있기 때문이다.

> Q: `OidcClientInitiatedLogoutSuccessHandler`를 붙이면 back-channel logout까지 끝난 건가요?
> 의도: RP-initiated와 back-channel 차이 확인
> 핵심: 아니다. redirect 기반 outbound flow와 inbound logout token 처리는 별도다.

> Q: "logout success" metric 하나만 보면 왜 위험한가요?
> 의도: framework success와 revoke completion 구분 확인
> 핵심: HTTP 응답 성공이 distributed revoke 완료를 뜻하지 않기 때문이다.

## 한 줄 정리

Spring logout 체인은 현재 요청의 local cleanup과 응답 계약을 다룰 뿐이고, BFF token cache 정리와 federated/global revoke는 그 바깥의 별도 coherence 설계다.

# BFF Session Store Outage / Degradation Recovery

> 한 줄 요약: BFF 구조에서 session store나 server-side token cache가 죽으면 브라우저는 로그인된 것처럼 보여도 실제 번역 계층이 사라질 수 있으므로, cookie 존재와 세션 유효성을 분리해서 보고 route별 degraded mode와 복구 순서를 준비해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
> - [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)
> - [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)
> - [Session Store Design at Scale](../system-design/session-store-design-at-scale.md)
> - [Security README: Browser / Server Boundary deep dive catalog](./README.md#browser--server-boundary-deep-dive-catalog)
> - [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: BFF session store outage, session cache outage, browser cookie but session missing, token cache outage, BFF degradation, session translation outage, browser server auth outage, BFF auth recovery, session store failover, login loop, 302 login loop, 401 302 bounce, hidden session mismatch, cookie still there but session missing, browser looks logged in but api loops, browser server boundary catalog, security readme browser server boundary

## 이 문서 다음에 보면 좋은 문서

- `login loop`, `401 -> 302` bounce, saved-request bounce처럼 redirect 복귀 자체가 꼬이면 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)에서 먼저 분리한다.
- `hidden session mismatch`, `cookie는 있는데 session missing`, `브라우저는 로그인돼 보이는데 API만 돈다` 같은 질의는 [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md), [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)와 같이 보면 translation 계층과 server session ownership을 같이 좁힐 수 있다.
- `logout still works`, `logout tail`, `revocation tail`처럼 실제 revoke propagation이 남는 증상이라면 [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md), [Session Revocation at Scale](./session-revocation-at-scale.md)로 바로 이어진다.

---

## 핵심 개념

BFF 기반 인증에서 브라우저가 가진 것은 보통 cookie reference뿐이다.  
실제 인증 상태는 서버 쪽 session store와 token cache에 있다.

그래서 이 구조의 장애는 독특하다.

- 브라우저에는 session cookie가 남아 있다
- 사용자는 로그인된 줄 안다
- 하지만 BFF는 session row나 provider token set을 찾지 못한다

즉 BFF auth outage의 핵심은 "cookie가 있나"가 아니라 "session translation 계층이 살아 있나"다.

---

## 깊이 들어가기

### 1. cookie 존재와 session 유효성은 별개다

브라우저는 opaque cookie를 계속 보낼 수 있다.  
하지만 다음 중 하나라도 깨지면 실제 인증은 무너진다.

- session store lookup 실패
- token cache lookup 실패
- refresh token decrypt 실패
- region failover 후 stale session routing

그래서 "쿠키 있으니 인증 유지"로 보면 안 된다.

### 2. 장애 유형을 나눠야 recovery가 달라진다

유형 예:

- session store 전체 outage
- 특정 region session replica lag
- token cache corruption
- cookie signing key rotation mismatch
- refresh path만 실패하고 existing short-lived access translation은 되는 상태

이 유형에 따라 완화가 달라진다.

- refresh only failure면 일부 cached token으로 짧게 버틸 수 있다
- session store miss면 민감 route는 바로 fail-closed가 맞다
- key mismatch면 재로그인 유도가 더 빠를 수 있다

### 3. route class별 degraded mode를 정해야 한다

예:

- public read route: anonymous fallback 가능
- low-risk personalized read: 짧은 stale session cache 허용 검토
- profile/settings/payment/admin: fail-closed

중요한 건 BFF가 죽었다고 모든 라우트를 같은 정책으로 다루지 않는 것이다.

### 4. refresh path와 session validation path를 분리해서 봐야 한다

많은 BFF가 다음을 한 번에 수행한다.

- cookie validate
- session load
- token load
- refresh if needed
- downstream call

그러면 어떤 단계가 깨졌는지 안 보인다.

운영상 최소한 구분이 필요하다.

- session lookup success rate
- token cache lookup success rate
- refresh success rate
- downstream exchange success rate

### 5. stale local cache는 매우 제한적으로만 써야 한다

가능한 상황:

- 최근에 검증된 server-side session snapshot이 있음
- low-risk read route
- 짧은 emergency window

안 되는 상황:

- logout/revoke 민감 route
- admin 기능
- step-up/elevated session 필요한 기능

즉 local stale cache는 "로그인 유지"가 아니라 "낮은 위험 read continuity" 정도로만 생각하는 편이 안전하다.

### 6. re-login storm도 사고다

session store outage 후 모두에게 재로그인을 요구하면:

- IdP 부하가 급증
- support 문의 폭증
- 일부 사용자만 계속 루프에 빠짐

그래서 recovery는 다음을 같이 본다.

- fail-closed route
- temporary holding page
- controlled re-login rollout
- region별 복구 순서

### 7. logout/revoke와 장애 복구가 충돌할 수 있다

예:

- stale session cache로 read continuity를 허용
- 그런데 이미 logout 요청이 들어온 세션일 수 있음

그래서 emergency cache는 반드시:

- revocation timestamp보다 오래된 snapshot 거부
- high-risk route 금지
- 매우 짧은 TTL

같은 안전장치를 가져야 한다.

### 8. observability는 cookie presence보다 state resolution을 봐야 한다

유용한 지표:

- cookie received but session not found
- session found but token set unavailable
- refresh path timeout rate
- forced re-login count
- degraded read fallback count

---

## 실전 시나리오

### 시나리오 1: 브라우저는 로그인돼 보이는데 모든 API가 302/401 루프에 빠진다

문제:

- cookie는 살아 있지만 session store lookup이 실패해 `hidden session mismatch`처럼 보인다

대응:

- session_not_found_after_cookie metric을 본다
- refresh path가 아니라 session path 문제인지 분리한다
- 일부 route는 holding page로 보내고, 복구 후 controlled re-login을 유도한다

### 시나리오 2: refresh token cache만 깨져 짧은 시간 뒤부터 순차적으로 사용자 세션이 죽는다

문제:

- 현재 번역된 access token은 살아 있으나 연장이 안 된다

대응:

- refresh failure와 session lookup failure를 분리해서 본다
- low-risk read route는 짧은 grace를 검토한다
- 결제/설정/관리자 route는 즉시 fail-closed 한다

### 시나리오 3: stale local session cache가 logout된 세션을 잠깐 살린다

문제:

- continuity 최적화가 revocation을 이긴다

대응:

- revocation-aware cache만 허용한다
- stale cache는 low-risk read에만 제한한다
- emergency window를 매우 짧게 둔다

---

## 코드로 보기

### 1. session resolution 단계 분리 예시

```java
public SessionResolution resolve(SessionCookie cookie) {
    BrowserSession session = sessionStore.find(cookie.value());
    if (session == null) {
        return SessionResolution.sessionMissing();
    }

    TokenSet tokens = tokenCache.find(session.id());
    if (tokens == null) {
        return SessionResolution.tokenSetMissing(session.id());
    }

    return SessionResolution.ok(session, tokens);
}
```

### 2. 운영 체크리스트

```text
1. cookie 존재와 session state resolution을 별도 단계로 본다
2. session store outage와 refresh outage를 분리해서 관측한다
3. degraded mode가 low-risk read에만 제한되는가
4. stale cache가 logout/revoke를 우회하지 않는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 전면 재로그인 | 구현이 단순하다 | re-login storm와 UX 피해가 크다 | 복구가 빠르고 범위가 작을 때 |
| low-risk read degraded mode | 사용자 체감을 줄인다 | stale session acceptance 위험이 있다 | read-heavy consumer app |
| stale local session cache | 짧은 continuity를 줄 수 있다 | revocation과 coherence가 약해질 수 있다 | 매우 제한적 emergency window |
| hard fail-closed | integrity가 강하다 | 가용성이 크게 떨어진다 | admin, payment, settings route |

판단 기준은 이렇다.

- 깨진 것이 session store인지 refresh path인지
- route가 personalized read인지 민감 write인지
- revocation-aware stale 정책을 구현할 수 있는지
- re-login storm를 감당할 수 있는지

---

## 꼬리질문

> Q: cookie가 남아 있는데 왜 로그인 상태가 아니라고 볼 수 있나요?
> 의도: browser reference와 server state를 구분하는지 확인
> 핵심: cookie는 참조값일 뿐이고, 실제 인증 상태는 server-side session resolution에 있기 때문이다.

> Q: BFF outage 때 stale cache를 아무 route에나 써도 되나요?
> 의도: degraded mode 범위를 이해하는지 확인
> 핵심: 아니다. logout/revoke 민감 route와 admin/payment 기능에는 매우 위험하다.

> Q: re-login storm가 왜 보안/운영 문제인가요?
> 의도: 복구 UX와 control plane 부하를 보는지 확인
> 핵심: IdP와 support에 2차 장애를 만들고 사용자를 루프에 빠뜨릴 수 있기 때문이다.

> Q: refresh failure와 session lookup failure를 왜 분리해서 봐야 하나요?
> 의도: 장애 유형별 복구가 다른 점을 이해하는지 확인
> 핵심: 하나는 세션 해석 문제고 다른 하나는 연장 문제라 완화 가능한 범위가 다르기 때문이다.

## 한 줄 정리

BFF 인증 장애를 운영 가능하게 만드는 핵심은 브라우저 cookie와 서버 state resolution을 분리해 보고, session store/refresh path별로 route-scoped degraded mode를 준비하는 것이다.

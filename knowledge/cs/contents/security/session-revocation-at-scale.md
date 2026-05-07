---
schema_version: 3
title: Session Revocation at Scale
concept_id: security/session-revocation-at-scale
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- session revocation
- logout
- token invalidation
- blacklist
aliases:
- session revocation
- logout
- token invalidation
- blacklist
- revocation store
- session version
- authz version
- claim version
- token version
- fan-out invalidation
- logout all devices
- distributed session
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/logout-scope-primer.md
- contents/security/role-change-session-freshness-basics.md
- contents/security/authz-session-versioning-patterns.md
- contents/security/jwt-deep-dive.md
- contents/security/refresh-token-rotation-reuse-detection.md
- contents/security/token-introspection-vs-self-contained-jwt.md
- contents/security/session-quarantine-partial-lockdown-patterns.md
- contents/security/revocation-propagation-lag-debugging.md
- contents/security/session-inventory-ux-revocation-scope-design.md
- contents/security/background-job-auth-context-revalidation.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Session Revocation at Scale 핵심 개념을 설명해줘
- session revocation가 왜 필요한지 알려줘
- Session Revocation at Scale 실무 설계 포인트는 뭐야?
- session revocation에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Session Revocation at Scale를 다루는 deep_dive 문서다. 세션 폐기는 단순 로그아웃 버튼이 아니라, 다수 인스턴스와 여러 토큰 종류에 걸쳐 일관되게 반영되어야 하는 분산 무효화 문제다. 검색 질의가 session revocation, logout, token invalidation, blacklist처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Session Revocation at Scale

> 한 줄 요약: 세션 폐기는 단순 로그아웃 버튼이 아니라, 다수 인스턴스와 여러 토큰 종류에 걸쳐 일관되게 반영되어야 하는 분산 무효화 문제다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **세션 무효화 모델과 revocation 전략**을 설명하는 deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Logout Scope Primer](./logout-scope-primer.md)
> - [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)
> - [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [Refresh Token Rotation / Reuse Detection](./refresh-token-rotation-reuse-detection.md)
> - [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md)
> - [Session Quarantine / Partial Lockdown Patterns](./session-quarantine-partial-lockdown-patterns.md)
> - [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
> - [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
> - [Background Job Auth Context / Revalidation](./background-job-auth-context-revalidation.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - [Spring Security `LogoutHandler` / `LogoutSuccessHandler` Boundaries](../spring/spring-security-logout-handler-success-boundaries.md)
> - [Session Store Design at Scale](../system-design/session-store-design-at-scale.md)
> - [Security README: Browser / Session Coherence](./README.md#browser--session-coherence)
> - [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)
> - [Security README: Session / Boundary / Replay](./README.md#session--boundary--replay)

retrieval-anchor-keywords: session revocation, logout, token invalidation, blacklist, revocation store, session version, authz version, claim version, token version, fan-out invalidation, logout all devices, distributed session, stale token, revocation lag, session quarantine, security session bridge, session boundary replay bundle, security readme session bridge, logout still works, logout tail, revocation tail, old session still works after logout, role revoked but session still works, permission change session revoke, session freshness

## 이 문서 다음에 보면 좋은 문서

- session이 살아 있을 때 role, permission, tenant membership 변경을 초보자 눈높이로 먼저 정리하고 싶으면 [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)부터 보고 내려오면 된다.
- `현재 세션`, `이 기기`, `모든 기기`, `refresh revoke`, `BFF cleanup`이 아직 한 덩어리로 들리면 [Logout Scope Primer](./logout-scope-primer.md)에서 범위를 먼저 자르고 내려오는 편이 안전하다.
- `logout still works`, `logout tail`, `revocation tail`처럼 실제 tail symptom을 바로 해석해야 하면 [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)로 이어진다.
- federated logout coherence는 [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)와 같이 보는 편이 좋다.
- `login loop`, `hidden session mismatch`, `cookie는 있는데 session missing`처럼 browser/BFF translation 계층이 먼저 의심되면 [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)로 이어진다.
- Spring logout local cleanup과 revoke plane 구분은 [Spring Security `LogoutHandler` / `LogoutSuccessHandler` Boundaries](../spring/spring-security-logout-handler-success-boundaries.md)에서 바로 연결된다.
- 사용자-facing 세션 목록과 revoke 범위 naming은 [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)으로 이어진다.
- 요청 이후 비동기 worker가 오래된 권한을 계속 써도 되는지는 [Background Job Auth Context / Revalidation](./background-job-auth-context-revalidation.md)에서 이어 볼 수 있다.

---

## 핵심 개념

세션 revocation은 "로그아웃 처리"를 넘어선다.

- access token을 더 이상 받아들이지 않아야 한다
- refresh token을 더 이상 재발급하면 안 된다
- 이미 배포된 여러 인스턴스가 같은 결정을 해야 한다
- 모든 device/session을 끊을지 선택해야 한다

즉 session revocation은 사용자 행동 이벤트가 아니라 분산 시스템의 무효화 일관성 문제다.

---

## 깊이 들어가기

### 1. revocation 대상이 하나가 아니다

폐기할 수 있는 것들:

- access token
- refresh token
- remember-me token
- device session
- API session
- browser session cookie

각각 수명이 다르고, 저장 위치도 다르다.

### 2. blacklist만으로는 비싸다

access token을 즉시 무효화하려고 blacklist를 두는 경우가 많다.

문제:

- 모든 요청마다 revocation store를 조회해야 한다
- store 장애가 인증 경로를 망칠 수 있다
- 토큰 TTL이 길면 black list가 커진다

그래서 짧은 access token + refresh revoke 조합이 더 현실적인 경우가 많다.

### 3. session version이 유용하다

사용자마다 session version을 두면 revoke가 쉬워진다.

- logout all devices 시 version을 올린다
- 비밀번호 변경 시 version을 올린다
- 권한 회수 시 version을 올린다

토큰에 version을 넣고 요청 시 비교하면, 오래된 세션을 자연스럽게 끊을 수 있다.

다만 실무에서는 `session_version` 하나만으로는 role revoke, tenant move, policy/cache stale을 세밀하게 가르기 어려워 `authz_version`, `tenant_version`, `refresh_family_version`까지 분리하는 경우가 많다.
이 분해 기준은 [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)에서 따로 본다.

### 4. 여러 인스턴스에서 같은 결정을 해야 한다

분산 환경에서는 다음이 필요하다.

- shared revocation store
- pub/sub invalidation
- 짧은 TTL
- cache busting

즉 단일 서버에서는 간단한 `revoked = true`가, 클러스터에서는 전파와 일관성 문제로 바뀐다.

### 5. logout UX와 security는 서로 trade-off다

강하게 끊을수록 UX는 나빠진다.

- 현재 탭
- 다른 탭
- 모바일 앱
- 백그라운드 refresh

그래서 "로그아웃" 버튼의 의미를 사용자에게 명확히 보여줘야 한다.

---

## 실전 시나리오

### 시나리오 1: 비밀번호 변경 후에도 기존 세션이 살아 있음

대응:

- password change 이벤트에서 session version을 올린다
- refresh token family를 revoke한다
- 중요 세션에는 재로그인을 요구한다

### 시나리오 2: 관리자 계정을 즉시 끊어야 함

대응:

- token introspection 또는 revocation store를 사용한다
- user disable 이벤트를 전체 세션에 fan-out한다
- cache TTL을 짧게 유지한다

### 시나리오 3: "모든 기기에서 로그아웃" 기능이 필요함

대응:

- device별 session 목록을 저장한다
- family revoke와 global revoke를 분리한다
- UI에서 revoke 범위를 명확히 보여준다

---

## 코드로 보기

### 1. session version 비교

```java
public void verifySession(UserPrincipal user, String tokenSessionVersion) {
    if (!Objects.equals(user.sessionVersion(), tokenSessionVersion)) {
        throw new SecurityException("session revoked");
    }
}
```

### 2. logout all devices

```java
public void logoutAllDevices(Long userId) {
    userRepository.bumpSessionVersion(userId);
    refreshTokenRepository.revokeAllByUserId(userId);
    sessionEventPublisher.publish(new UserLoggedOutAllEvent(userId));
}
```

### 3. revocation store 개념

```text
1. revoke event를 기록한다
2. access token은 짧게 유지한다
3. refresh token은 즉시 revoke한다
4. 여러 인스턴스가 같은 revocation source를 보게 한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| blacklist access tokens | 즉시 끊을 수 있다 | 조회 비용이 크다 | 매우 민감한 환경 |
| short-lived access + refresh revoke | 현실적이고 확장성 좋다 | 즉시성은 조금 떨어진다 | 대부분의 서비스 |
| session version | 구현이 명확하다 | 토큰 설계에 version이 필요하다 | 브라우저/모바일 세션 |
| introspection | revoke 반영이 빠르다 | auth server 의존이 생긴다 | 중앙 통제 환경 |

판단 기준은 이렇다.

- 로그아웃이 즉시 반영돼야 하는가
- token store 조회 비용을 감당할 수 있는가
- 모든 device를 함께 끊어야 하는가
- 세션 재사용 징후를 빨리 감지해야 하는가

---

## 꼬리질문

> Q: 세션 revocation이 왜 분산 문제인가요?
> 의도: 여러 인스턴스와 토큰 종류의 일관성을 아는지 확인
> 핵심: 모든 서버가 같은 폐기 상태를 봐야 하기 때문이다.

> Q: blacklist만 두면 왜 부담이 커질 수 있나요?
> 의도: 조회 비용과 장애 전파를 이해하는지 확인
> 핵심: 매 요청마다 revocation lookup이 필요하기 때문이다.

> Q: session version은 왜 유용한가요?
> 의도: 버전 기반 무효화를 아는지 확인
> 핵심: 오래된 세션을 한 번에 끊기 쉽다.

> Q: logout all devices는 무엇을 끊어야 하나요?
> 의도: 범위 설계를 이해하는지 확인
> 핵심: refresh family, browser session, device session을 모두 정리해야 한다.

## 한 줄 정리

세션 폐기는 사용자 로그아웃 버튼이 아니라, 여러 토큰과 인스턴스에 걸친 무효화 일관성을 맞추는 운영 문제다.

# Session Revocation at Scale

> 한 줄 요약: 세션 폐기는 단순 로그아웃 버튼이 아니라, 다수 인스턴스와 여러 토큰 종류에 걸쳐 일관되게 반영되어야 하는 분산 무효화 문제다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [Refresh Token Rotation / Reuse Detection](./refresh-token-rotation-reuse-detection.md)
> - [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [인증과 인가의 차이](./authentication-vs-authorization.md)

retrieval-anchor-keywords: session revocation, logout, token invalidation, blacklist, revocation store, session version, fan-out invalidation, logout all devices, distributed session, stale token

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

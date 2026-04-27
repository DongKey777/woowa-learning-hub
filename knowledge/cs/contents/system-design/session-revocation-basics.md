# Session Revocation Basics

> 한 줄 요약: logout, revoke propagation, short-lived token은 "토큰을 어떻게 검증하나"보다 "이미 발급된 자격을 언제부터 어떻게 못 쓰게 만드나"의 문제를 다루며, token-based auth도 lifecycle control을 위해 결국 서버 상태를 필요로 한다.

retrieval-anchor-keywords: session revocation basics, logout 뭐예요, logout propagation basics, forced logout basics, short-lived access token basics, short-lived token why, jwt logout basics, logout all devices basics, session version basics, refresh token basics, browser logout tail, mobile logout tail, beginner auth lifecycle, beginner system design auth, session revocation basics basics

**난이도: 🟢 Beginner**

관련 문서:

- [Stateless Sessions Primer](./stateless-sessions-primer.md)
- [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md)
- [Session Store Design at Scale](./session-store-design-at-scale.md)
- [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md)
- [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md)
- [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)
- [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md)
- [Security: Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md)
- [Security: Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)

---

## 핵심 개념

초보자가 가장 많이 헷갈리는 지점은 이것이다.

- token-based auth를 쓰면 서버가 세션을 안 들고 있을 것 같다
- 그래서 logout도 "클라이언트에서 token만 지우면 끝"처럼 느껴진다

하지만 실전에서 중요한 질문은 "토큰이 self-contained인가"보다 아래에 가깝다.

- 이 사용자를 지금부터 막아야 하는가
- 특정 기기만 끊을 것인가, 모든 기기를 끊을 것인가
- 비밀번호 변경이나 계정 정지 후에 언제부터 deny되어야 하는가
- 이미 발급된 access token이 edge/cache/BFF에 남아 있으면 어떻게 할 것인가

즉, session revocation은 **인증 정보를 발급하는 문제**보다 **이미 발급된 인증 정보를 수명 주기 동안 통제하는 문제**다.

아주 단순하게 그리면 아래처럼 본다.

```text
login
  -> access token issued
  -> refresh/session state issued

logout / password reset / admin disable
  -> revocation state written somewhere
  -> gateways, verifiers, caches, BFFs learn that state
  -> old token eventually stops working
```

여기서 핵심은 마지막 줄이다.
old token이 "즉시" 멈출 수도 있지만, 많은 시스템에서는 **전파 시간과 TTL만큼 tail**이 남는다.

---

## 깊이 들어가기: Logout, Token TTL, Lifecycle State

### 1. logout와 revocation은 비슷하지만 같은 단어는 아니다

`logout`은 "이 세션을 끝내라"라는 이벤트다.
`revocation`은 그 의도가 실제 검증 경로에 반영되어 더 이상 통과시키지 않는 상태다.

사용자 눈에는 "로그아웃했는데 왜 아직 한두 번은 통과하지?"처럼 보일 수 있다.

| 동작 | 서버가 해야 하는 일 |
|---|---|
| 현재 브라우저 로그아웃 | cookie/session 종료 + BFF mapping 정리 |
| 모든 기기 로그아웃 | subject 기준 전역 revoke 또는 version bump |
| 비밀번호 변경 후 강제 로그아웃 | subject/session epoch 상승 + refresh/session family 정리 |

### 2. short-lived access token은 revoke tail을 줄일 뿐이다

짧은 TTL이 주는 효과:

- 오래된 access token을 들고 있어도 오래 못 쓴다
- revoke event가 일부 verifier에 늦게 도착해도 최대 피해 시간을 줄인다

하지만 사용자는 계속 로그인 상태를 원한다. 그래서 refresh token이나 server session이 남고,
이 경로는 여전히 서버 상태를 봐야 한다.

```text
short-lived access token = fast read path
longer-lived refresh/session state = lifecycle control path
```

### 3. token auth도 lifecycle control 때문에 결국 상태가 필요하다

상태가 필요한 대표 요구:

- logout, logout all devices
- 비밀번호 변경 후 기존 세션 무효화
- 계정 정지나 직원 퇴사 후 즉시 차단
- refresh token rotation과 재사용 탐지

| 상태 모델 | 예시 |
|---|---|
| session inventory | `user -> active sessions` |
| revoke list / revoke-before time | `revoke_before = 10:30` |
| session version / subject epoch | `token.version < current_version`면 deny |
| refresh family store | refresh rotation, reuse detection |

---

## 깊이 들어가기: Revocation 전파와 브라우저/모바일 차이

### 4. revoke propagation이 어려운 이유는 검증 지점이 여러 층이기 때문이다

revocation은 보통 한 DB row만 바꾸고 끝나지 않는다.

검증 레이어: API gateway, edge verifier, regional cache, BFF의 downstream token cache, refresh/session store

이 과정 중 일부가 늦으면 `logout tail`이 보인다.

```text
user clicks logout
  -> origin says revoked
  -> region A gateway denies
  -> region B edge cache still allows for 20s
```

실무에서는 경로별로 강도를 나눈다.

- 저위험 경로: short TTL + eventual revoke propagation
- 고위험 경로: direct introspection, version check, shorter cache TTL

### 5. 브라우저 logout와 모바일/API logout는 같은 그림이 아니다

브라우저 + BFF에서 자주 보는 일:

- browser cookie 삭제
- server-side session 종료
- downstream token cache 정리

모바일/API bearer flow에서는:

- 새 refresh는 막는다
- 기존 access token은 TTL 또는 revoke propagation이 끝나야 완전히 죽는다

### 6. 초보자가 자주 하는 오해

`로그아웃은 클라이언트에서 token만 지우면 된다`
— 다른 기기, refresh token, BFF cache가 남아 있을 수 있다.

`JWT면 revoke를 못 하니까 그냥 만료만 기다려야 한다`
— version check, revoke-before, introspection, short TTL 같은 설계를 함께 쓴다.

`short-lived access token이면 보안 문제가 거의 끝난다`
— 탈취 대응, refresh rotation, device scope revoke는 여전히 남는다.

---

## 면접 답변 골격

짧게 답하면 이렇게 정리할 수 있다.

> token-based auth를 쓰더라도 logout이나 권한 변경 같은 lifecycle control 때문에 서버 상태가 필요합니다. access token은 짧게 두어 revoke tail을 줄이고, refresh token이나 session/version store를 통해 실제 무효화를 통제하는 식이 흔합니다. 또 브라우저+BFF와 모바일 bearer flow는 검증 지점이 달라서 logout propagation 방식도 다르게 설계해야 합니다.

---

## 꼬리질문

> Q: short-lived access token이면 왜 revoke store가 또 필요한가요?
> 의도: TTL과 lifecycle control을 구분하는지 확인
> 핵심: TTL은 피해 시간을 줄일 뿐이고, logout all devices나 refresh 차단은 서버 상태가 필요하다.

> Q: JWT는 self-contained인데 왜 버전 체크를 붙이나요?
> 의도: 서명 검증과 최신 계정 상태 반영을 구분하는지 확인
> 핵심: 권한 변경, 계정 정지, 비밀번호 변경을 즉시 반영하려면 현재 서버 상태와 비교해야 한다.

> Q: 브라우저 logout와 모바일 logout가 왜 다르게 느껴지나요?
> 의도: cookie/BFF 경계와 bearer token 경계를 구분하는지 확인
> 핵심: 브라우저는 session mapping과 downstream token translation이 있고, 모바일/API는 access token TTL과 refresh revoke가 더 직접적인 문제다.

> Q: revoke propagation이 느린데 왜 모든 요청을 introspection하지 않나요?
> 의도: 즉시성, 비용, 가용성 trade-off를 이해하는지 확인
> 핵심: 고위험 경로만 direct check를 강화하고, 나머지는 short TTL과 eventual propagation으로 비용을 낮추는 경우가 많다.

## 한 줄 정리

token-based auth도 logout, revoke, refresh, 권한 변경 같은 lifecycle control을 위해 결국 state plane이 필요하며, short-lived token은 그 state를 없애는 것이 아니라 revoke tail을 줄이는 도구다.

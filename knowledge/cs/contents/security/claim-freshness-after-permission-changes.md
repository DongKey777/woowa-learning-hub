# Claim Freshness After Permission Changes

> 한 줄 요약: role, permission, tenant membership이 바뀌면 source of truth만 바뀌는 것이 아니라 JWT claim, server session principal, authorization cache, revoke plane이 각자 수렴해야 하므로 old authority는 여러 층에서 따로 stale하게 남을 수 있다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **permission change가 JWT / session / cache / revocation으로 전파되는 경로**를 한 장의 mental model로 묶어 주는 bridge다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)
> - [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)
> - [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)
> - [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md)
> - [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
> - [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md)
> - [Security README: Session Coherence / Assurance deep dive catalog](./README.md#session-coherence--assurance-deep-dive-catalog)
> - [Security README: AuthZ / Tenant / Response Contracts deep dive catalog](./README.md#authz--tenant--response-contracts-deep-dive-catalog)

retrieval-anchor-keywords: claim freshness after permission changes, permission change propagation, role change jwt session cache revocation, permission changed but jwt still old, role revoked but old authorities remain, old authorities remain stale, stale authorities after role change, stale authority propagation, permission revoke propagation, role grant propagation, authz freshness propagation, jwt session cache revoke timeline, stale allow after revoke, stale deny after grant, session claim stale after permission change, refresh after role change, re-login after permission change, authz version revoke, claim snapshot stale

## 이 문서 다음에 보면 좋은 문서

- role, permission, session freshness 자체가 아직 낯설면 [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)부터 보면 된다.
- 방금 권한을 줬는데 `403`이 남는 쪽이 더 가깝다면 [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)로 바로 이어 가면 된다.
- `authz_version`, `session_version`, `tenant_version`, `refresh_family_version`을 실제로 어떻게 나눠 설계하는지 궁금하면 [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)로 내려가면 된다.
- stale allow/deny를 cache key와 invalidation 관점에서 더 깊게 보고 싶으면 [Authorization Caching / Staleness](./authorization-caching-staleness.md)를 붙이면 된다.
- revoke tail, regional lag, `last accepted after revoke`를 운영 관점에서 보고 싶으면 [Session Revocation at Scale](./session-revocation-at-scale.md), [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)로 이어진다.
- self-contained JWT와 introspection이 freshness에 어떤 차이를 만드는지 비교하려면 [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md)를 같이 보면 된다.

---

## 먼저 20초 그림

| 레이어 | 보통 무엇을 들고 있나 | 왜 stale이 남나 | 흔한 증상 | 안전한 기본 동작 |
|---|---|---|---|---|
| JWT / access token | role, scope, coarse permission, tenant context snapshot | 이미 발급된 토큰은 스스로 업데이트되지 않는다 | role을 회수했는데 old allow가 잠시 남음 | 짧은 TTL, `authz_version` 비교, 필요 시 refresh 또는 introspection |
| server session | `Principal`, `GrantedAuthority`, active tenant, login state | 세션 안 principal snapshot을 다시 만들지 않으면 old authority를 계속 쓴다 | re-login 전까지 old role이 유지되거나 반대로 old deny가 남음 | version mismatch 시 principal 재구성 또는 session terminate |
| authz cache | principal cache, membership cache, decision cache, graph/path cache | cache key에 relevant version이 없거나 invalidation fan-out이 늦다 | 일부 pod, 일부 tenant, 일부 route만 old allow/deny | scoped invalidation, versioned cache key, provenance 기록 |
| revoke plane | session version, refresh family revoke, regional fan-out state | revoke 요청과 마지막 accept 종료 사이에 tail이 남을 수 있다 | `logout still works`, disabled user가 특정 route에서 계속 통과 | `last_accepted_after_revoke` 추적, high-risk route direct check, quarantine |

핵심은 이것이다.

- permission change는 DB 한 줄 업데이트로 끝나지 않는다.
- 요청 경로가 믿는 모든 snapshot이 최신으로 수렴해야 freshness가 맞는다.
- 네 층 중 한 곳만 stale해도 사용자는 "왜 old authority가 아직 남지?"를 경험한다.

---

## permission change는 한 번의 쓰기가 아니라 여러 상태의 수렴이다

권한 변경을 안전하게 이해하려면 아래 흐름으로 봐야 한다.

```text
role / permission / membership change
-> source of truth update
-> authz/session/tenant version bump 또는 change event 발행
-> existing JWT/session을 refresh 또는 revoke 대상으로 표시
-> principal / membership / decision cache invalidation
-> 다음 요청이 최신 상태로 재평가
-> old allow 제거 또는 old deny 해소
```

여기서 중요한 점은 `권한이 바뀌었다`와 `요청이 그 사실을 안다`가 같은 순간이 아니라는 것이다.

- source of truth는 이미 최신일 수 있다.
- 그러나 현재 브라우저, API gateway, service cache는 여전히 예전 snapshot을 볼 수 있다.

그래서 freshness 문제는 "DB에는 반영됐는데 왜 안 바뀌죠?"라는 질문으로 자주 나타난다.

---

## 왜 JWT, session, cache, revocation을 따로 봐야 하나

### 1. JWT는 self-contained snapshot이라서 스스로 갱신되지 않는다

JWT를 쓰면 resource server는 서명과 claim을 로컬에서 빠르게 검증할 수 있다.  
대신 이미 발급된 토큰은 아래 사실을 모른다.

- 방금 admin role이 회수됐는가
- tenant membership이 삭제됐는가
- support grant가 종료됐는가

즉 `exp`가 남아 있으면 시간상 유효할 수는 있어도 freshness는 이미 깨졌을 수 있다.

그래서 JWT 경로에서는 보통 아래 중 하나가 필요하다.

- access token TTL을 짧게 둔다
- `authz_version` 같은 low-churn version claim을 넣는다
- high-risk route에서는 introspection이나 fresh check를 추가한다

JWT를 쓴다고 해서 revoke나 authority refresh 문제가 사라지는 것은 아니다.

### 2. server session도 principal snapshot을 캐시한다

초보자는 "server-side session이면 매 요청마다 최신 DB를 보겠지"라고 생각하기 쉽다.  
실제로는 세션 안에 아래 snapshot이 이미 들어 있는 경우가 많다.

- 로그인된 사용자 principal
- `GrantedAuthority` 목록
- selected tenant나 workspace context

이 snapshot을 다시 만들지 않으면 server session도 JWT와 비슷하게 stale해진다.

즉 server session은 수정 가능하다는 장점이 있지만,
`수정 로직이 있지 않으면` 자동으로 최신이 되지는 않는다.

### 3. cache는 credential보다 더 오래 stale할 수 있다

권한 변경 뒤에도 old authority가 남는 가장 흔한 이유는 cache다.

대표적인 예:

- principal cache
- tenant membership cache
- authorization decision cache
- relationship graph / path cache
- negative deny cache

예를 들어 role을 회수해 JWT를 새로 받아도,
decision cache가 `subject + action`만 key로 쓰고 `authz_version`을 안 보면 old allow가 남을 수 있다.

반대로 권한을 부여한 경우에는 old deny cache 때문에 계속 `403`이 남을 수 있다.

즉 cache invalidation은 성능 최적화가 아니라 auth correctness의 일부다.

### 4. revocation은 "요청했다"가 아니라 "마지막 accept가 끝났다"까지 봐야 한다

role 회수, user disable, logout-all, refresh family revoke 같은 이벤트는 revoke plane을 탄다.
여기서 자주 생기는 오해는 이것이다.

- revoke API가 성공했다
- 그러니 old authority는 끝났다

실제로는 그 뒤에 남는 tail을 봐야 한다.

- 어떤 region은 이미 막았는가
- 어떤 pod는 아직 old token을 받아 주는가
- refresh token은 끊겼지만 현재 access token TTL이 남아 있는가

그래서 revoke plane은 "버튼을 눌렀다"가 아니라 "언제 완전히 안 받아 주게 됐는가"를 설명해야 한다.

---

## revoke path와 grant path는 stale 종류가 다르다

| 변화 방향 | 가장 위험한 stale 상태 | 사용자에게 보이는 현상 | 기본 대응 |
|---|---|---|---|
| revoke / downgrade | stale allow | admin을 뺐는데 아직 admin API가 된다 | `authz_version` bump, allow cache purge, high-risk session/family revoke |
| grant / upgrade | stale deny | 권한을 줬는데 계속 `403`이다 | claim/session refresh, deny cache purge, 필요 시 step-up |

같은 version/event 체계를 써도 방향이 다르면 위험이 다르다.

- revoke는 `예전 allow를 얼마나 빨리 없애느냐`가 핵심이다.
- grant는 `예전 deny를 얼마나 안전하게 걷어 내느냐`가 핵심이다.

그래서 "권한 변경 전파"를 이해할 때 revoke와 grant를 같은 UX로 처리하면 안 된다.

---

## 타임라인 예시: admin role을 회수했는데 old authority가 남는 경우

```text
13:00  admin role 삭제, source of truth에서 user.authz_version 42 -> 43
13:00  change event 발행, refresh family revoke 요청
13:01  service A는 current authz_version=43을 보고 다음 요청부터 deny
13:01  browser access JWT는 여전히 authz_version=42라 old claim을 들고 있음
13:02  service B decision cache key에 authz_version이 없어 old allow hit
13:03  일부 region은 revoke fan-out이 늦어 old token을 잠깐 더 accept
13:05  access token TTL 종료 또는 refresh 후 finally old authority 사라짐
```

이 시나리오에서 stale authority가 남는 이유는 하나가 아니다.

- JWT가 아직 old snapshot이다
- cache가 old allow를 재사용한다
- revoke fan-out이 완전히 끝나지 않았다

즉 "권한 회수 후에도 old authority가 남는다"는 현상은
대부분 여러 레이어의 지연이 겹쳐서 생긴다.

---

## 반대 시나리오: 권한을 줬는데도 계속 `403`인 이유

grant path에서는 같은 구조가 반대로 나타난다.

- source of truth에는 새 role이 저장됐다
- 그러나 현재 session/JWT는 여전히 old claim이다
- negative cache는 여전히 old deny를 들고 있다
- 민감 작업은 recent-auth나 step-up이 별도로 필요할 수 있다

그래서 learner가 보게 되는 문장은 보통 이렇다.

- "재로그인하면 되긴 하는데 왜 처음에는 안 되죠?"
- "어떤 pod에서는 되는데 어떤 pod에서는 안 됩니다"
- "목록은 보이는데 POST만 계속 `403`입니다"

이건 authorize 우회를 해야 한다는 뜻이 아니라,
grant path convergence를 더 짧고 관측 가능하게 만들어야 한다는 뜻이다.

---

## 운영에서 기억할 기본값

- source of truth update와 request-path convergence를 별도 단계로 설계한다.
- `session_version`, `authz_version`, `tenant_version`, `refresh_family_version`처럼 stale 원인을 분리할 수 있는 축을 둔다.
- JWT에는 low-churn version만 넣고, high-risk route는 중앙 fresh check나 introspection으로 보강한다.
- principal cache, membership cache, decision cache, graph cache key에 relevant version을 포함한다.
- revoke 경로는 `requested_at`만이 아니라 `last_accepted_after_revoke`와 longest-tail region/pod를 추적한다.
- learner-facing UX에서는 "권한이 바뀌면 refresh/re-login이 필요할 수 있다"는 점을 숨기지 않는다.

---

## 한 줄 정리

permission change 뒤 old authority가 남는 이유는 권한 모델이 틀려서가 아니라, JWT와 session은 snapshot을 들고 있고 cache는 그 snapshot을 증폭시키며 revoke plane은 그 snapshot을 각 인스턴스에서 retire시키는 속도가 서로 다르기 때문이다.

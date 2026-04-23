# Role Change and Session Freshness Basics

> 한 줄 요약: 로그인 세션이 아직 살아 있어도 role, permission, tenant membership이 바뀌면 그 세션이 들고 있던 권한 정보는 낡을 수 있으므로, 시스템은 권한 변경을 session refresh, revoke, 재평가 중 하나로 바로 연결해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [인증과 인가의 차이](./authentication-vs-authorization.md)
- [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md)
- [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md)
- [Session Revocation at Scale](./session-revocation-at-scale.md)
- [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)
- [HTTP와 HTTPS 기초](../network/http-https-basics.md)
- [Spring Security 기초](../spring/spring-security-basics.md)

retrieval-anchor-keywords: role change session freshness, session freshness basics, role revoked but session still works, admin removed but still access, permission granted but still 403, stale claims, authz freshness basics, re-login after role change, authz version, session version, version bump pattern, role downgrade active session, 세션 권한 변경 뭐예요, beginner session freshness, 처음 배우는 세션 갱신

## 이 문서 다음에 보면 좋은 문서

- `인증`, `principal`, `session` 자체가 아직 섞이면 [인증과 인가의 차이](./authentication-vs-authorization.md)로 먼저 돌아가면 된다.
- 세션 상태를 어디에 두는지부터 다시 잡아야 하면 [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md)를 이어 보면 된다.
- role, permission 변경이 JWT, server session, cache, revoke plane을 따라 어떻게 퍼지며 왜 old authority가 남는지 한 장 timeline으로 보고 싶으면 [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md)로 이어 가면 된다.
- `session_version`, `authz_version`, `tenant_version`을 실제로 어떻게 나눠 들고 갈지 궁금하면 [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)로 바로 이어 보면 된다.
- role change보다 `org/team/tenant move 뒤 active tenant가 왜 refresh되어야 하는가`가 더 궁금하면 [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)로 바로 내려가면 된다.
- `로그아웃했는데 계속 된다`, revoke tail, distributed invalidation 자체가 궁금하면 [Session Revocation at Scale](./session-revocation-at-scale.md)로 내려가면 된다.
- 권한을 방금 줬는데도 `403`이 남거나, role을 회수했는데 old allow가 남는 운영 문제는 [Authorization Caching / Staleness](./authorization-caching-staleness.md)에서 더 직접적으로 다룬다.
- deprovisioning, group removal, tenant membership 삭제까지 같이 묶어 보려면 [SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md)로 이어진다.

---

## 먼저 15초 그림

| 지금 바뀐 것 | old session에 기대하면 안 되는 것 | 안전한 기본 동작 |
|---|---|---|
| role이나 permission이 회수됨 | 예전 admin claim, 예전 allow 판단 | 다음 요청부터 deny하거나 session/token을 refresh 또는 revoke |
| role이나 permission이 추가됨 | 기존 session이 자동으로 새 권한을 안다 | 새 권한은 session/claim refresh 또는 재로그인 후 반영 |
| tenant/team/ownership 문맥이 바뀜 | 예전 tenant scope, 예전 resource ownership | 다음 요청에서 최신 문맥으로 다시 인가 판단 |
| 민감 작업 정책이 강화됨 | 예전 로그인만으로 여전히 충분하다 | step-up 또는 재인증 후 처리 |

이 문서의 핵심은 한 줄이다.

- session은 보통 `누구인지`를 이어 준다.
- authorization은 `지금 무엇을 할 수 있는지`를 판단한다.
- freshness는 `지금 들고 있는 session/claim이 최신 권한 상태를 반영하는가`를 묻는다.

---

## freshness는 만료(expiration)와 다르다

초보자가 가장 자주 섞는 두 단어가 `만료`와 `freshness`다.

| 질문 | 만료(expiration) | freshness |
|---|---|---|
| 이 세션을 아직 써도 되나? | 맞다 | 일부만 맞다 |
| 권한 변경을 반영했나? | 직접 답하지 못한다 | 바로 다루는 질문이다 |
| 예시 | `8시간 세션이 아직 안 끝남` | `1분 전에 admin role이 회수됐는데 old claim을 계속 씀` |

즉 세션이 `안 끝났다고 해서` 권한 정보까지 최신이라는 뜻은 아니다.

---

## 왜 이 문제가 생기나

로그인 순간에는 보통 아래 중 일부가 session, cookie, JWT claim 안에 들어간다.

- user id
- tenant id
- coarse role
- 인증 시각
- 일부 permission snapshot

문제는 로그인 이후에도 시스템 바깥의 진실은 계속 바뀐다는 점이다.

- 관리자가 admin role을 회수할 수 있다
- 조직 이동으로 tenant membership이 바뀔 수 있다
- support grant가 종료될 수 있다
- 정책 배포로 특정 action이 더 엄격해질 수 있다

그래서 `오전에 로그인한 세션`과 `오후의 실제 권한`이 어긋날 수 있다.

---

## role이나 permission이 바뀌면 무엇이 일어나야 하나

가장 단순한 안전 모델은 아래 순서다.

1. source of truth에서 role, permission, membership, policy가 바뀐다.
2. 시스템이 `권한이 바뀌었다`는 사실을 event, version bump, cache invalidation으로 기록한다.
3. 기존 session이나 token이 예전 권한을 들고 있으면 refresh하거나 revoke한다.
4. 다음 요청은 최신 권한 모델로 다시 판단한다.

실무에서는 여기서 보통 `session_version`, `authz_version`, `tenant_version`을 분리해 올린다.  
이 분해 패턴은 [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)에서 따로 정리한다.

이 결과로 사용자가 보게 되는 동작은 보통 셋 중 하나다.

- 로그인은 유지되지만 더 이상 높은 권한 action은 못 한다.
- session 자체가 강제로 끊겨 다시 로그인해야 한다.
- 새 권한을 쓰려면 claim refresh, 재로그인, step-up이 먼저 필요하다.

중요한 점은 `권한이 바뀌었는데도 아무 일도 안 일어나는 것`이 가장 위험하다는 것이다.

---

## 권한이 줄어들 때의 기본 동작

권한 회수, role downgrade, tenant membership 제거는 보통 더 엄격하고 더 빨라야 한다.

### 안전한 기본값

- 다음 요청부터 old allow가 남지 않게 한다.
- session version이나 authz version을 올려 old claim을 무효화한다.
- authz cache와 negative/positive decision cache를 같이 정리한다.
- 민감 계정이면 refresh token family나 전체 session을 revoke한다.

### 사용자 입장에서 보이는 모습

- 기본 로그인 자체는 유지될 수 있다.
- 하지만 admin page, 승인 API, 다른 tenant 데이터 접근은 바로 막혀야 한다.

여기서 응답은 둘로 갈릴 수 있다.

- 로그인 상태는 유지되고 권한만 내려가면 보통 `403`에 가깝다.
- session 자체를 더 이상 신뢰하지 않으면 `401`이나 재로그인 흐름으로 간다.

즉 `role 회수 = 무조건 전원 로그아웃`은 아니다.  
하지만 `role 회수 후에도 old admin allow가 계속 남는다`는 더 나쁘다.

---

## 권한이 늘어날 때의 기본 동작

권한 추가는 회수와 반대 방향이지만, 여기서도 old session을 그대로 믿으면 안 된다.

### 안전한 기본값

- 새 권한은 session/claim refresh 뒤에 반영한다.
- stale deny cache가 남지 않게 invalidation을 같이 한다.
- 민감 권한은 재로그인이나 step-up 뒤에만 활성화한다.

### 왜 바로 열어 주면 안 되나

예를 들어 support role을 방금 부여했는데:

- session 안에는 예전 role만 들어 있을 수 있다
- gateway나 service cache에는 예전 deny가 남아 있을 수 있다
- 높은 위험 작업은 `방금 role이 생겼다`와 `최근에 다시 본인 확인을 했다`가 다른 질문이다

그래서 `권한이 생겼는데 바로 안 된다`는 현상은 보통 버그를 고칠 신호지, 보안 검사를 건너뛸 이유는 아니다.

---

## 문맥 변경도 사실상 같은 문제다

role 문자열이 안 바뀌어도 아래 변화는 session freshness 문제를 만든다.

- tenant 이동
- 팀 변경
- resource ownership 변경
- delegated support session 종료

예를 들어 `ROLE_USER`는 그대로여도 tenant A에서 tenant B로 이동했다면,
이전 tenant 기준 allow를 그대로 쓰면 안 된다.

즉 `권한 문자열`만 보는 것이 아니라,
`현재 요청이 기대하는 문맥이 최신인가`까지 같이 봐야 한다.

---

## 초보자용 예시 3개

### 1. 오전에 로그인한 admin이 오후에 admin role을 잃었다

안전한 동작:

- 다음 admin 요청부터는 old admin allow가 사라져야 한다
- 필요하면 admin 관련 session/refresh token을 바로 끊는다
- 일반 사용자 권한만 남는 서비스라면 로그인은 유지될 수도 있다

위험한 동작:

- `아까 로그인했으니 오늘은 계속 admin`

### 2. support role을 방금 받았는데 계속 `403`이 나온다

가능한 원인:

- session claim이 아직 갱신되지 않았다
- authz deny cache가 남아 있다
- 해당 작업은 step-up이나 재로그인을 요구한다

안전한 대응:

- session/claim을 refresh한다
- 관련 cache를 무효화한다
- 민감 작업이면 최근 인증을 다시 요구한다

### 3. 사용자 조직이 바뀌었는데 예전 tenant 데이터가 보인다

이건 단순 UI 버그가 아니라 authz freshness 문제다.

안전한 동작:

- 다음 요청에서 최신 tenant membership으로 다시 판단한다
- tenant-scoped cache key가 바뀌어야 한다
- old tenant session tail이 남지 않게 한다

---

## 자주 하는 오해

### 1. 세션이 살아 있으면 권한도 살아 있다

아니다. session은 로그인 지속 장치이고, authorization은 현재 권한 판단이다.

### 2. JWT에 role을 넣었으니 DB나 policy를 다시 볼 필요가 없다

아니다. 긴 수명의 claim은 role 회수, tenant 이동, policy change를 늦게 반영할 수 있다.

### 3. 권한 추가는 즉시 반영하고, 권한 회수는 조금 늦어도 된다

보안 관점에서는 보통 반대다. 회수 경로가 더 엄격하고 더 빨라야 한다.

### 4. 문제를 피하려면 무조건 전체 로그아웃만 시키면 된다

항상 그렇지는 않다.  
낮은 권한의 base session은 유지하되, 높은 권한만 제거하는 설계도 가능하다. 핵심은 old high-privilege allow가 남지 않는 것이다.

---

## 기억할 기본 원칙 5개

1. authentication은 살아 있어도 현재 authorization은 달라질 수 있다.
2. revocation path는 grant path보다 더 빠르고 엄격해야 한다.
3. session, cookie, JWT claim에는 refresh plan이나 version 전략이 필요하다.
4. cache invalidation은 성능 최적화가 아니라 auth correctness의 일부다.
5. 민감 권한은 `role이 생김`과 `최근 본인 확인`을 분리해서 봐야 한다.

---

## 한 줄 정리

role이나 permission이 session 중간에 바뀌면, 안전한 시스템은 `예전 로그인 순간의 권한 스냅샷`을 믿지 않고 다음 요청부터 최신 권한 기준으로 refresh, revoke, 재평가를 수행한다.

# Session Store Design at Scale

> 한 줄 요약: session store at scale은 세션 생성, 조회, 폐기, 핀닝, 복제 지연을 관리해 사용자 흐름의 상태 일관성을 제공하는 분산 저장소 설계다.

retrieval-anchor-keywords: session store, sticky session, external session store, token-based auth, stateless sessions primer, session pinning, monotonic reads, read-your-writes, revocation, TTL, distributed session, cache, token session, leader placement, failover policy, staleness budget, read quorum, session coherence, logout propagation, session revocation lag, regional revoke lag, cache invalidation replay, revoke redrive, device session graph, session store migration, claim version cutover, claim schema rollout, auth session troubleshooting, BFF session troubleshooting, hidden session creation, saved request login loop, JSESSIONID stateless api, logout all devices, security readme session bridge, security session boundary bridge, browser cookie session, BFF token translation, browser auth vs mobile auth, session revocation basics, short-lived access token basics, session boundary replay bundle

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Session Revocation at Scale](../security/session-revocation-at-scale.md)
> - [Stateless Sessions Primer](./stateless-sessions-primer.md)
> - [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md)
> - [Session Revocation Basics](./session-revocation-basics.md)
> - [Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md)
> - [OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md)
> - [Auth Incident Triage / Blast-Radius Recovery Matrix](../security/auth-incident-triage-blast-radius-recovery-matrix.md)
> - [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
> - [Session Inventory UX / Revocation Scope Design](../security/session-inventory-ux-revocation-scope-design.md)
> - [Security README: Session / Boundary / Replay](../security/README.md#session--boundary--replay)
> - [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)
> - [Revocation Bus Regional Lag Recovery 설계](./revocation-bus-regional-lag-recovery-design.md)
> - [Read-Your-Writes와 Session Pinning 전략](../database/read-your-writes-session-pinning.md)
> - [Replica Lag and Read-after-write Strategies](../database/replica-lag-read-after-write-strategies.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)
> - [Stateful Workload Placement / Failover Control Plane 설계](./stateful-workload-placement-failover-control-plane-design.md)
> - [Read / Write Quorum & Staleness Budget 설계](./read-write-quorum-staleness-budget-design.md)

## 핵심 개념

sticky session, external session store, token-based auth의 기본 비교부터 잡고 싶다면 먼저 [Stateless Sessions Primer](./stateless-sessions-primer.md)를 보고 오는 편이 좋다.
browser cookie session과 BFF가 downstream token 호출로 어떻게 이어지는지부터 분리하고 싶다면 [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md)를 먼저 읽고 오면 이 문서의 store 설계가 더 잘 들어온다.
logout, revoke propagation, short-lived token이 왜 같이 등장하는지부터 가볍게 잡고 싶다면 [Session Revocation Basics](./session-revocation-basics.md)를 먼저 보면 좋다.
session store는 "로그인 상태를 저장하는 DB"보다 훨씬 넓다.  
실전에서는 아래를 함께 관리해야 한다.

- session creation
- lookup and refresh
- revocation
- device/session inventory
- read-your-writes
- replica lag tolerance

즉, session store는 사용자 흐름의 상태를 안정적으로 유지하는 분산 무효화 저장소다.

## 깊이 들어가기

### 1. 세션 종류를 분리한다

보통 다음을 구분한다.

- browser session
- mobile session
- API session
- refresh session
- ephemeral login challenge

세션마다 TTL과 revocation 정책이 다르다.

### 2. Capacity Estimation

예:

- 동시 로그인 1,000만
- 세션 lookup 초당 20만
- revoke 이벤트 초당 수천

lookup이 훨씬 많고, revoke fan-out이 어렵다.

봐야 할 숫자:

- session lookup QPS
- cache hit ratio
- revoke propagation delay
- refresh churn
- miss rate

### 3. 저장 모델

대표 선택지:

- centralized session DB
- distributed cache + durable store
- token introspection store
- hybrid session version store

### 4. read-your-writes와 pinning

세션은 최근 변경이 바로 보여야 한다.

- 로그인 직후 읽기
- 비밀번호 변경 직후 revoke
- 권한 변경 직후 반영

이 부분은 [Read-Your-Writes와 Session Pinning 전략](../database/read-your-writes-session-pinning.md)과 연결된다.

### 5. revocation and versioning

세션 폐기는 가장 중요한 경계다.

- session version
- device revoke
- global revoke
- refresh family revoke

이 부분은 [Session Revocation at Scale](../security/session-revocation-at-scale.md)와 연결된다.
session store migration과 claim semantic 변경이 동시에 일어나는 경우는 [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)를 이어서 보면 좋다.

### 6. TTL and renewal

세션은 영구 상태가 아니다.

- idle timeout
- absolute timeout
- sliding renewal
- remember-me override

### 7. multi-region behavior

멀티 리전에서는 세션 복제가 늦을 수 있다.

- region-local session store
- global revocation plane
- sticky read routing
- fallback introspection

이 부분은 [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)와 연결된다.
특정 region 또는 cache tier만 revoke fan-out에서 뒤처졌을 때 redrive, dedupe, synthetic verification을 어떻게 설계할지는 [Revocation Bus Regional Lag Recovery 설계](./revocation-bus-regional-lag-recovery-design.md)로 이어서 보면 좋다.

### 8. framework symptom과 store incident를 분리해 triage한다

세션 문제는 application edge에서 먼저 보이지만, 모든 `JSESSIONID`, login redirect, logout bounce가 store 문제는 아니다.

- `STATELESS`인데 `JSESSIONID`가 생기거나 API가 `302`를 받으면 먼저 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)를 본다. 이건 replication lag보다 framework/session creation path 문제일 가능성이 크다.
- 브라우저 logout는 끝났는데 BFF가 downstream API를 계속 호출한다면 [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)로 가서 browser session, provider refresh token, downstream token cache mapping을 분리한다.
- `현재 세션 종료`, `이 기기 로그아웃`, `모든 기기 로그아웃`이 서로 다른 저장소 키를 자르면 [Session Inventory UX / Revocation Scope Design](../security/session-inventory-ux-revocation-scope-design.md)까지 같이 봐야 한다.
- 그 다음 단계에서야 [Session Revocation at Scale](../security/session-revocation-at-scale.md), [Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md)로 fan-out, TTL, cache tail을 분석하는 편이 빠르다.

## 실전 시나리오

### 시나리오 1: 비밀번호 변경 직후

문제:

- 오래된 세션이 살아 있으면 안 된다

해결:

- session version bump
- refresh revoke
- stale token reject

### 시나리오 2: 모바일 앱 재로그인

문제:

- 네트워크가 나빠 세션 갱신이 실패한다

해결:

- short-lived access + refresh
- retry with pinning

### 시나리오 3: 모든 기기 로그아웃

문제:

- 사용자 요청으로 전체 세션을 끊어야 한다

해결:

- revoke family
- device inventory update
- audit log 기록

### 시나리오 4: 브라우저에서는 로그아웃됐는데 일부 BFF/downstream 호출은 계속 통과한다

문제:

- 브라우저 cookie 삭제와 서버측 token cache revoke가 분리돼 있다

해결:

- browser session id, refresh family, audience token cache를 같은 subject/session mapping으로 본다
- request cache redirect 문제와 revocation tail을 분리한다
- 고위험 route는 direct check나 shorter TTL을 둔다

## 코드로 보기

```pseudo
function validateSession(token):
  session = sessionStore.get(token.sessionId)
  if session.version != token.version:
    reject()
  if session.expired():
    reject()
  return allow()
```

```java
public Session load(SessionId id) {
    return sessionRepository.findActive(id);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| sticky session | 단순하다 | 분산 효율이 낮다 | 세션 중심 앱 |
| centralized store | revoke가 쉽다 | 병목 가능 | 대부분의 웹앱 |
| cache + durable hybrid | 빠르고 안정적이다 | 복잡도 증가 | 대규모 서비스 |
| token introspection | 즉시 revoke 가능 | auth 의존성이 크다 | 민감 경로 |
| versioned sessions | clear semantics | 토큰 설계 필요 | 브라우저/모바일 |

핵심은 session store가 단순 로그인 저장소가 아니라 **읽기 일관성과 폐기 전파를 함께 제공하는 분산 상태 저장소**라는 점이다.

## 꼬리질문

> Q: session store와 JWT는 어떻게 다른가요?
> 의도: 상태 저장과 self-contained token 차이 이해 확인
> 핵심: 세션은 서버가 상태를 들고, JWT는 토큰 자체에 상태가 있다.

> Q: read-your-writes가 왜 중요한가요?
> 의도: 사용자 흐름 일관성 이해 확인
> 핵심: 로그인이나 권한 변경 직후 오래된 상태가 보이면 UX와 보안이 깨진다.

> Q: revoke fan-out은 왜 어렵나요?
> 의도: 분산 무효화 이해 확인
> 핵심: 여러 인스턴스와 캐시에 동시에 반영해야 하기 때문이다.

> Q: multi-region에서 session이 흔들리면 어떻게 하나요?
> 의도: 지역별 일관성 이해 확인
> 핵심: local store와 global revocation plane을 같이 둔다.

## 한 줄 정리

Session store at scale은 세션 생성과 갱신, 폐기, 핀닝, 복제를 함께 관리해 사용자 상태의 일관성을 유지하는 분산 저장 시스템이다.

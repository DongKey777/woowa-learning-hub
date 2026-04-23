# SCIM Deprovisioning / Session / AuthZ Consistency

> 한 줄 요약: SCIM deprovisioning은 계정 상태만 바꾸는 이벤트가 아니라, 세션 revoke, tenant membership 제거, authz cache invalidation까지 이어져야 의미가 있으며, 이 연결이 끊기면 퇴사자/탈퇴자 access tail이 남는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [SCIM Provisioning Security](./scim-provisioning-security.md)
> - [SCIM Drift / Reconciliation](./scim-drift-reconciliation.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md)
> - [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)
> - [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md)
> - [System Design: Database / Security Identity Bridge Cutover 설계](../system-design/database-security-identity-bridge-cutover-design.md)
> - [System Design: Session Store / Claim-Version Cutover 설계](../system-design/session-store-claim-version-cutover-design.md)

retrieval-anchor-keywords: SCIM deprovisioning, deprovision session revoke, SCIM authz consistency, identity lifecycle consistency, deprovisioning lag, orphan session, directory drift authz, SCIM membership revoke, access shutdown, deprovision tail, directory backfill, auth shadow evaluation, authority transfer

---

## 핵심 개념

SCIM deprovisioning이 성공했다고 해서 보안이 끝난 것은 아니다.

실제 질문:

- 기존 세션은 끊겼는가
- refresh family는 회수됐는가
- tenant membership cache는 갱신됐는가
- authz deny가 모든 route에 반영됐는가

즉 deprovisioning은 user row 업데이트가 아니라, identity lifecycle을 세션과 인가까지 일관되게 정리하는 문제다.

---

## 깊이 들어가기

### 1. deprovisioning tail은 세 곳에 남기 쉽다

- active session / refresh family
- stale authz cache
- orphan delegated/admin grant

그래서 account disabled와 access denied 사이에 긴 tail이 생긴다.

### 2. group removal도 사실상 deprovisioning일 수 있다

특히 group-to-role 매핑이 강한 시스템에서는:

- 특정 group 제거
- tenant membership 제거

가 곧 권한 철회다.

### 3. SCIM event와 local revoke는 같은 파이프라인에 묶는 편이 낫다

좋은 패턴:

- deprovision event 수신
- local account state 갱신
- session/family revoke
- authz cache invalidation
- propagation lag 추적

### 4. drift reconciliation도 session tail을 같이 봐야 한다

과거 drift를 정리할 때:

- 계정 상태만 맞추고
- 남아 있는 session을 안 끊으면

복구가 반쪽이다.

### 5. directory backfill 완료와 access shutdown 검증은 다른 질문이다

SCIM event replay나 reconciliation backfill이 끝났다고 access shutdown이 끝난 것은 아니다.

- source/local row diff는 0인데 refresh family가 아직 살아 있다
- membership row는 제거됐는데 authz cache와 shadow decision은 old allow를 낸다
- support override나 delegated grant cleanup이 늦어 DB 상태와 실제 권한이 어긋난다

그래서 identity lifecycle authority transfer에서는
[Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md)의 data parity gate와
[Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)의 decision parity gate를 함께 봐야 한다.

### 6. observability는 lifecycle-to-access lag를 봐야 한다

유용한 지표:

- deprovision requested at
- last accepted after deprovision
- stale membership cache hit
- orphan session count

---

## 실전 시나리오

### 시나리오 1: 퇴사자 계정은 disabled인데 모바일 앱은 계속 동작한다

문제:

- session/family revoke가 분리돼 있다

대응:

- SCIM deprovision event에서 revoke fan-out을 같이 실행한다
- last accepted after deprovision을 측정한다

### 시나리오 2: tenant membership이 제거됐는데 일부 화면만 계속 보인다

문제:

- authz cache/negative cache tail

대응:

- tenant membership invalidate를 authz cache invalidation과 연결한다
- route class별 stale hit를 본다

### 시나리오 3: drift reconciliation 후에도 support grant가 남아 있다

문제:

- delegated/admin override cleanup이 lifecycle과 연결되지 않았다

대응:

- deprovision flow에 override/grant cleanup을 포함한다

## 한 줄 정리

SCIM deprovisioning을 운영 가능하게 만드는 핵심은 계정 상태 변경을 세션 revoke, authz cache invalidation, override cleanup까지 이어지는 일관된 access shutdown 파이프라인으로 보는 것이다.

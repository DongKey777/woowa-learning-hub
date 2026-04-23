# Database / Security Identity Bridge Cutover 설계

> 한 줄 요약: database / security identity bridge cutover 설계는 데이터 저장소 authority 이전과 identity capability rollout을 한 묶음의 승격 절차로 다뤄, backfill mismatch는 없지만 토큰/세션/정책이 뒤처지는 식의 반쪽 cutover를 막는 운영 설계다.

> 문서 역할: 이 문서는 system-design 관점에서 database migration/repair gate와 security identity capability gate를 하나의 cutover matrix로 묶는 bridge 문서다.

retrieval-anchor-keywords: database security bridge, identity capability cutover, auth claim migration, workload identity rollout, backfill verification, auth shadow evaluation, cutover gate matrix, jwks overlap window, session revoke propagation, tenant routing cutover, authority transfer, bridge retirement, repair before cleanup, session store migration, claim version cleanup timing, legacy claim retirement, dedicated cell migration, service identity allowlist, post cutover auth drift, identity authority transfer, online backfill shadow compare, dual read verification, traffic shadowing, mirrored request validation, authorization decision parity, SCIM deprovision, deprovision tail, trust bundle rollback, SPIFFE trust bundle overlap, mesh trust root rotation

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Dual-Write Avoidance / Migration Bridge 설계](./dual-write-avoidance-migration-bridge-design.md)
> - [Zero-Downtime Schema Migration Platform 설계](./zero-downtime-schema-migration-platform-design.md)
> - [Capability Negotiation / Feature Gating 설계](./capability-negotiation-feature-gating-design.md)
> - [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
> - [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)
> - [Edge Authorization Service 설계](./edge-authorization-service-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md)
> - [Tenant Split-Out with Service Identity Rollout 설계](./tenant-split-out-service-identity-rollout-design.md)
> - [Trust-Bundle Rollback During Cell Cutover 설계](./trust-bundle-rollback-during-cell-cutover-design.md)
> - [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md)
> - [Database: CDC Gap Repair, Reconciliation, and Rebuild Boundaries](../database/cdc-gap-repair-reconciliation-playbook.md)
> - [Database: Hot Tenant Split-Out, Routing, and Cutover Playbook](../database/tenant-split-out-routing-cutover-playbook.md)
> - [Security: Service-to-Service Auth: mTLS, JWT, SPIFFE](../security/service-to-service-auth-mtls-jwt-spiffe.md)
> - [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)
> - [Security: SCIM Deprovisioning / Session / AuthZ Consistency](../security/scim-deprovisioning-session-authz-consistency.md)
> - [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)
> - [Security: Workload Identity / Long-Lived Service Account Keys](../security/workload-identity-vs-long-lived-service-account-keys.md)

## 핵심 개념

database cutover와 security identity rollout은 서로 다른 팀의 일처럼 보이지만, 실제로는 둘 다 "누가 authoritative truth인가"를 바꾸는 작업이다.

- database 쪽은 writer, read model, routing registry, repair boundary가 바뀐다
- security 쪽은 issuer, verifier, workload identity, authz decision, session shutdown 경계가 바뀐다

문제는 둘 중 하나만 먼저 바뀌면 시스템이 "부분적으로만 새 세상"에 들어간다는 점이다.

- backfill은 끝났는데 old claim semantic이 남아 cross-tenant allow가 열린다
- workload identity는 새로 바뀌었는데 tenant routing은 old shard를 본다
- SCIM deprovision은 반영됐는데 새 DB cutover 뒤 session revoke fan-out이 늦어 access tail이 남는다

즉 이 주제의 핵심은 migration과 identity가 별개라는 착각을 버리고, **data plane authority transfer와 identity capability transfer를 같은 cutover unit으로 다루는 것**이다.

## 깊이 들어가기

### 1. database plane과 identity plane은 다른 형태의 authority graph다

둘은 저장 구조는 다르지만 비슷한 질문에 답한다.

| 축 | database plane | identity plane | cutover에서 확인할 것 |
|---|---|---|---|
| authoritative source | primary writer, source table | issuer, session authority, policy source | 지금 누가 진실을 결정하는가 |
| compatibility bridge | CDC, projection bridge, dual-read compare | claim translation, capability downgrade, token exchange | old/new를 누가 이어 주는가 |
| repair primitive | replay, backfill, recompute | revoke fan-out, cache invalidation, shadow evaluation | 어긋났을 때 무엇으로 수리하는가 |
| rollback boundary | write fence, rollback window, cleanup gate | JWKS overlap, trust-bundle rollback, capability hard reject 전환점 | 얼마나 빨리 되돌릴 수 있는가 |
| retirement signal | drift zero, replay backlog zero | deprecated capability last-seen zero, shadow divergence zero | bridge를 언제 없앨 수 있는가 |

정리하면 database migration에서 보는 `authority transfer`와 security rollout에서 보는 `trust transfer`는 다른 말이지만 운영적으로는 거의 같은 구조다.

### 2. 잘못된 순서가 만드는 대표 장애

대표적인 반쪽 cutover는 아래와 같다.

1. read/write cutover는 끝났는데 auth context가 old tenant mapping을 쓴다.
2. 새 capability claim은 발급되는데 일부 verifier는 old JWKS/trust bundle만 본다.
3. SCIM membership 제거는 끝났는데 split-out된 tenant의 background worker가 old cache로 allow를 낸다.
4. database repair는 replay로 복구했는데 authz shadow divergence를 안 봐서 새 policy가 조용히 allow bug를 만든다.

이런 장애는 한 평면의 관측만으로는 잘 안 보인다.
row count와 checksum이 모두 맞아도 security plane이 틀어지면 사용자 영향은 그대로 난다.

### 3. 안전한 cutover는 phase를 공유해야 한다

권장 phase는 보통 다음과 같다.

#### Phase A. compatibility window

- database는 single writer + projection bridge를 유지한다
- security는 optional capability advertise, claim versioning, JWKS overlap을 유지한다
- 중요한 것은 old/new가 동시에 존재해도 **진실원은 하나**만 두는 것이다

이 구간에서 필요한 문서 연결은
[Zero-Downtime Schema Migration Platform](./zero-downtime-schema-migration-platform-design.md),
[Capability Negotiation / Feature Gating](./capability-negotiation-feature-gating-design.md),
[Workload Identity / Long-Lived Service Account Keys](../security/workload-identity-vs-long-lived-service-account-keys.md)다.

#### Phase B. shadow verification

- database는 shadow read, bucket checksum, late write gate를 본다
- security는 shadow policy evaluation, allow/deny divergence, `kid_miss`, revocation lag를 본다

즉 "새 경로가 동작한다"보다 **old와 new가 얼마나 다르게 판단하는가**를 먼저 본다.

이 구간은
[Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md)와
[Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)를 같이 봐야 감이 잡힌다.

여기서 database shadow read는 "같은 row인가"를,
security shadow evaluation은 "같은 allow/deny인가"를 묻는다.
둘 중 하나만 green이면 authority transfer는 아직 닫히지 않은 것이다.

Phase B는 shadow read 하나로 끝내기보다 세 층으로 나누는 편이 안전하다.

- [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)는 production request mix를 재현해 route, gateway, auth plugin 압력을 확인한다
- [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md)는 같은 요청의 row/projection/response invariant parity를 축적한다
- [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)는 같은 request context의 allow/deny parity와 divergence severity를 축적한다

즉 database/security bridge의 shadow verification은 "요청 재현", "data parity", "decision parity"를 하나의 cutover path로 묶는 단계다.

#### Phase C. fenced cutover

- database는 짧은 write fence나 freeze로 final delta를 닫는다
- security는 verifier overlap, trust bundle propagation, session/refresh revoke propagation을 닫는다
- tenant routing이나 route policy를 뒤집는 시점은 둘의 fence가 동시에 healthy할 때만 연다

단순 traffic shift가 아니라, "old authority가 더는 새 write/new identity를 승인하지 않는다"는 경계를 명시해야 한다.

#### Phase D. repair-first soak

- database는 CDC gap, drift bucket, replay backlog를 줄인다
- security는 shadow critical divergence, deprovision tail, deprecated capability hit를 줄인다

이 시점에는 feature를 더 켜기보다 repair를 먼저 끝내야 한다.
[Database: CDC Gap Repair, Reconciliation, and Rebuild Boundaries](../database/cdc-gap-repair-reconciliation-playbook.md)와
[Security: SCIM Deprovisioning / Session / AuthZ Consistency](../security/scim-deprovisioning-session-authz-consistency.md)가 바로 이 구간의 운영 문서다.

### 4. joint cutover gate가 있어야 "DB는 됐는데 auth가 안 됨"을 막는다

실전에서는 둘을 하나의 표로 묶어야 한다.

| gate | database evidence | security evidence | 승격 조건 |
|---|---|---|---|
| pre-cutover readiness | backfill lag, checksum mismatch, late write lag | `kid_miss`, trust bundle sync lag, capability advertise coverage | 둘 다 SLO 안 |
| shadow safety | shadow read mismatch, compare error budget | old/new authz divergence, high-risk allow delta | critical mismatch 0 |
| fence health | final delta applied, write fence active | verifier overlap healthy, revoke propagation healthy | rollback path 재현 가능 |
| post-cutover soak | replay backlog, repair queue, drift bucket | deprecated capability hit, session tail, auth cache stale hit | tail이 감소 추세 |
| bridge retirement | cleanup candidate 0, repair backlog 0 | capability last-seen 0, shadow divergence 0 | 둘 다 0일 때만 bridge 제거 |

한쪽만 green이라고 승격하면 안 된다.
특히 database cleanup을 먼저 하면 security side rollback 근거가 사라지고,
security hard reject를 먼저 열면 database bridge가 아직 live인데 client만 끊기는 일이 생긴다.
실제로 승인 패킷을 어떤 필드와 decision 문장으로 남겨야 하는지는 [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)에서 template 형태로 이어진다.

### 5. tenant 이동과 identity rollout은 같이 보는 편이 낫다

hot tenant split-out이나 dedicated cell 승격은 좋은 예다.

- database는 tenant routing registry와 shard cutover를 바꾼다
- security는 tenant-scoped authz, session membership, service identity allowlist를 바꾼다

그래서 tenant 이동 작업은
[Database: Hot Tenant Split-Out, Routing, and Cutover Playbook](../database/tenant-split-out-routing-cutover-playbook.md)과
[Security: Service-to-Service Auth: mTLS, JWT, SPIFFE](../security/service-to-service-auth-mtls-jwt-spiffe.md)를 한 세트로 보는 편이 안전하다.

DB만 옮기고 mTLS/SPIFFE allowlist를 안 바꾸면 새 cell로의 호출이 막히고,
반대로 identity만 먼저 열면 old shard에 남아야 할 traffic이 새 trust 경로로 새어 나간다.
이 조합을 tenant-scoped cutover 객체, allowlist overlap, post-cutover auth drift soak까지 포함해 더 구체적으로 좁혀 보면 [Tenant Split-Out with Service Identity Rollout 설계](./tenant-split-out-service-identity-rollout-design.md)로 바로 이어진다.
여기에 issuer나 mesh trust root까지 같이 바뀌면 verifier overlap과 bundle rollback window가 route flip보다 오래 살아야 하므로 [Trust-Bundle Rollback During Cell Cutover 설계](./trust-bundle-rollback-during-cell-cutover-design.md)를 함께 보는 편이 안전하다.

## 실전 시나리오

### 시나리오 1: tenant split-out과 workload identity 전환을 같이 진행

문제:

- tenant 42를 dedicated cluster로 옮기며 새 service account/SPIFFE identity도 같이 도입한다

해결:

- tenant routing cutover 전에 shadow read와 authz shadow divergence를 같이 본다
- DB write fence와 service identity allowlist 전환을 같은 change set으로 묶는다
- post-cutover에는 drift bucket과 denied-by-new-identity 비율을 함께 본다

### 시나리오 2: session store migration과 claim semantic 변경이 같이 발생

문제:

- 새 세션 저장소는 `tenant_scope_version`을 요구하지만 일부 verifier는 old claim만 이해한다

해결:

- claim translation bridge를 유지한 상태에서 new store를 shadow 검증한다
- deprecated capability hit가 0이 되기 전에는 old claim parser를 지우지 않는다
- revocation lag가 길면 DB cutover가 맞아도 access tail이 남으므로 cleanup을 미룬다

이 시나리오를 session authority, claim semantic, revoke propagation, cleanup clock 관점으로 확장해서 보면 [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)와 바로 이어진다.

### 시나리오 3: 권한 모델 변경 후 database repair가 필요해짐

문제:

- migration 도중 CDC gap repair는 끝났지만 새 authz policy가 old deny를 new allow로 뒤집는다

해결:

- database repair 완료를 승격 완료로 간주하지 않는다
- authz shadow critical divergence가 0이 될 때까지 enforce 비율을 올리지 않는다
- bridge retirement는 repair backlog와 capability last-seen이 모두 0일 때만 실행한다

## 코드로 보기

```pseudo
function canPromote(scope):
  dataReady =
    scope.backfillLagSec < 5 and
    scope.shadowReadMismatch == 0 and
    scope.cdcRepairBacklog == 0

  identityReady =
    scope.authShadowCriticalDivergence == 0 and
    scope.jwksKidMiss == 0 and
    scope.revocationLagSec < 30 and
    scope.deprecatedCapabilitySilentMinutes > 60

  rollbackReady =
    scope.writeFenceHealthy and
    scope.verifierOverlapHealthy and
    scope.cleanupStillDisabled

  return dataReady and identityReady and rollbackReady
```

```yaml
cutover_gate:
  scope: tenant-42
  database:
    backfill_verification: pass
    cdc_gap_repair: pass
    write_fence: ready
  security:
    auth_shadow_eval: pass
    jwks_overlap: ready
    session_revoke_tail: pass
  cleanup:
    enabled: false
    reason: "deprecated capability still observed"
```

핵심은 metric이 많은 것이 아니라, **database evidence와 security evidence를 같은 release gate에서 읽는 것**이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| DB cutover와 security rollout을 분리 | 조직별 진행이 쉽다 | 반쪽 성공이 늘고 fault isolation이 어려워진다 | 영향 범위가 정말 독립적일 때만 |
| joint cutover gate | 운영 판단이 명확하다 | 준비해야 할 지표와 절차가 늘어난다 | tenant 이동, claim 변경, issuer 전환 |
| 긴 compatibility window | rollback이 쉽다 | bridge 비용과 혼선이 오래 남는다 | long-tail client가 많을 때 |
| aggressive capability hard-reject | cleanup이 빠르다 | verifier skew와 session tail에 취약하다 | 내부 caller만 있고 관측이 충분할 때 |
| repair-first soak | silent drift를 줄인다 | 완료까지 시간이 더 걸린다 | 금융, tenant isolation, auth boundary처럼 고위험일 때 |

핵심은 database / security bridge cutover가 문서 두 개를 나란히 읽는 수준이 아니라, **authority transfer, repair, retirement를 두 평면에서 동시에 닫는 운영 설계**라는 점이다.

## 꼬리질문

> Q: database shadow read가 모두 통과했는데 왜 auth shadow evaluation도 봐야 하나요?
> 의도: 데이터 정합성과 권한 정합성을 분리해서 이해하는지 확인
> 핵심: 같은 row를 읽더라도 claim, tenant mapping, policy version이 다르면 다른 결정을 내릴 수 있기 때문이다.

> Q: JWKS overlap이나 workload identity rollout이 database migration과 왜 연결되나요?
> 의도: trust transfer와 data transfer를 함께 보는지 확인
> 핵심: 새 경로로 가는 요청이 누구로 인정되는지가 바뀌면, 저장소 cutover 성공 여부와 별개로 실제 트래픽은 실패하거나 과허용될 수 있다.

> Q: bridge retirement는 언제 시작해야 하나요?
> 의도: cleanup 시점의 보수성을 이해하는지 확인
> 핵심: repair backlog가 0이고 deprecated capability last-seen도 0일 때처럼 data와 identity tail이 모두 닫힌 뒤에만 시작하는 편이 안전하다.

## 한 줄 정리

Database / security identity bridge cutover 설계는 backfill, replay, shadow read 같은 data plane 증거와 JWKS, session revoke, capability divergence 같은 identity plane 증거를 하나의 승격 기준으로 묶어 반쪽 migration을 막는 운영 설계다.

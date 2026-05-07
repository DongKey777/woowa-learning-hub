---
schema_version: 3
title: Tenant Split-Out with Service Identity Rollout 설계
concept_id: system-design/tenant-split-out-service-identity-rollout-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- tenant split out service identity rollout
- tenant routing cutover
- dedicated cell migration
- hot tenant dedicated cell
aliases:
- tenant split out service identity rollout
- tenant routing cutover
- dedicated cell migration
- hot tenant dedicated cell
- premium tenant cell promotion
- dedicated cell promotion verification ladder
- mirrored traffic dual read auth drift
- mirrored traffic gate
- dual read gate
- auth drift soak
- workload identity allowlist
- SPIFFE allowlist
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/tenant-partition-strategy-reassignment-design.md
- contents/system-design/cell-based-architecture-blast-radius-isolation-design.md
- contents/system-design/database-security-identity-bridge-cutover-design.md
- contents/system-design/traffic-shadowing-progressive-cutover-design.md
- contents/system-design/dual-read-comparison-verification-platform-design.md
- contents/system-design/write-freeze-rollback-window-design.md
- contents/system-design/trust-bundle-rollback-during-cell-cutover-design.md
- contents/system-design/dedicated-cell-drain-retirement-design.md
- contents/system-design/bridge-retirement-evidence-packet-design.md
- contents/system-design/service-mesh-control-plane-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Tenant Split-Out with Service Identity Rollout 설계 설계 핵심을 설명해줘
- tenant split out service identity rollout가 왜 필요한지 알려줘
- Tenant Split-Out with Service Identity Rollout 설계 실무 트레이드오프는 뭐야?
- tenant split out service identity rollout 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Tenant Split-Out with Service Identity Rollout 설계를 다루는 deep_dive 문서다. tenant split-out with service identity rollout 설계는 특정 tenant를 shared pool에서 dedicated cell로 옮길 때 tenant routing cutover, write ownership 전환, SPIFFE/workload identity allowlist, post-cutover auth drift check를 하나의 tenant-scoped 승격 절차로 묶는 운영 설계다. 검색 질의가 tenant split out service identity rollout, tenant routing cutover, dedicated cell migration, hot tenant dedicated cell처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Tenant Split-Out with Service Identity Rollout 설계

> 한 줄 요약: tenant split-out with service identity rollout 설계는 특정 tenant를 shared pool에서 dedicated cell로 옮길 때 tenant routing cutover, write ownership 전환, SPIFFE/workload identity allowlist, post-cutover auth drift check를 하나의 tenant-scoped 승격 절차로 묶는 운영 설계다.
>
> 문서 역할: 이 문서는 tenant mobility, cell migration, database/security authority transfer가 한 번에 겹치는 상황을 system-design 관점에서 좁혀 설명하는 시나리오 deep dive다.

retrieval-anchor-keywords: tenant split out service identity rollout, tenant routing cutover, dedicated cell migration, hot tenant dedicated cell, premium tenant cell promotion, dedicated cell promotion verification ladder, mirrored traffic dual read auth drift, mirrored traffic gate, dual read gate, auth drift soak, workload identity allowlist, SPIFFE allowlist, SPIRE SVID rollout, service identity drain window, post cutover auth drift check, tenant scoped authz divergence, background worker principal drift, stale route cache drain, legacy principal drain, replay worker route cache, support tooling route hygiene, search indexer cutover hygiene, webhook sender principal rollover, tenant move background path hygiene, tenant caller class rollout matrix, foreground background caller checklist, principal issuance checklist, caller class allowlist checklist, caller class drift soak, foreground api principal issuance, background worker principal issuance, support tooling delegated principal, identity routing joint gate, trust bundle rollback, verifier overlap window, mesh trust root rotation, shared cell exit proof, rollback closure after tenant split out, dedicated cell retirement

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Tenant Partition Strategy / Reassignment 설계](./tenant-partition-strategy-reassignment-design.md)
> - [Cell-Based Architecture / Blast Radius Isolation 설계](./cell-based-architecture-blast-radius-isolation-design.md)
> - [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md)
> - [Write-Freeze Rollback Window 설계](./write-freeze-rollback-window-design.md)
> - [Trust-Bundle Rollback During Cell Cutover 설계](./trust-bundle-rollback-during-cell-cutover-design.md)
> - [Dedicated Cell Drain and Retirement 설계](./dedicated-cell-drain-retirement-design.md)
> - [Bridge Retirement Evidence Packet 설계](./bridge-retirement-evidence-packet-design.md)
> - [Service Mesh Control Plane 설계](./service-mesh-control-plane-design.md)
> - [Service Discovery / Health Routing 설계](./service-discovery-health-routing-design.md)
> - [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)
> - [Search Indexing Pipeline 설계](./search-indexing-pipeline-design.md)
> - [Webhook Delivery Platform 설계](./webhook-delivery-platform-design.md)
> - [Edge Verifier Claim-Skew Fallback 설계](./edge-verifier-claim-skew-fallback-design.md)
> - [Database: Hot Tenant Split-Out, Routing, and Cutover Playbook](../database/tenant-split-out-routing-cutover-playbook.md)
> - [Security: Service-to-Service Auth: mTLS, JWT, SPIFFE](../security/service-to-service-auth-mtls-jwt-spiffe.md)
> - [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)
> - [Security: Workload Identity / Long-Lived Service Account Keys](../security/workload-identity-vs-long-lived-service-account-keys.md)

## 이 문서 다음에 보면 좋은 설계

- dedicated-cell 승격 검증을 mirrored traffic -> dual-read -> auth drift soak 순서로 따라가려면 [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md), [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md), [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)을 먼저 묶어 보는 편이 좋다.
- foreground edge/API caller가 새 claim이나 verifier overlap을 어떻게 흡수하는지까지 보려면 [Edge Verifier Claim-Skew Fallback 설계](./edge-verifier-claim-skew-fallback-design.md)를 같이 보면 caller-class별 principal issuance 조건이 더 선명해진다.
- tenant가 shared cell을 실제로 언제 완전히 떠났는지, legacy principal과 rollback handle을 어떤 순서로 닫는지는 [Dedicated Cell Drain and Retirement 설계](./dedicated-cell-drain-retirement-design.md)로 이어 보면 post-cutover phase가 정리된다.
- caller class별 `last-seen`, quarantine, rollback closure 승인 필드를 어떤 packet으로 남길지는 [Bridge Retirement Evidence Packet 설계](./bridge-retirement-evidence-packet-design.md)를 이어 보면 좋다.
- trust bundle overlap과 old root retirement clock이 길게 남는 이유는 [Trust-Bundle Rollback During Cell Cutover 설계](./trust-bundle-rollback-during-cell-cutover-design.md)의 `bundle rollback window`를 같이 보면 더 선명하다.
- shared path cleanup이 irreversible boundary를 넘는 시점은 [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)와 연결해서 보는 편이 안전하다.

## 핵심 개념

hot tenant나 premium tenant를 dedicated cell로 승격할 때 많이 빠지는 착각이 있다.
"DB와 routing만 옮기면 된다"는 생각이다.

실전에서는 아래 네 가지 truth가 동시에 맞아야 한다.

- tenant directory가 새 cell을 가리켜야 한다
- write ownership과 background job ownership이 새 cell로 닫혀야 한다
- 새 cell에서 호출하는 workload identity가 SPIFFE/workload identity allowlist에 올라와 있어야 한다
- cutover 직후 old/new auth 결정이 어긋나는지 drift check를 계속 봐야 한다

즉 이 시나리오의 본질은 tenant 이동 자체보다, **routing truth와 trust truth를 같은 tenant-scoped release gate에서 같이 뒤집는 것**이다.

## 깊이 들어가기

### 1. 왜 tenant split-out과 identity rollout이 같이 깨지는가

둘은 다른 팀의 작업처럼 보이지만 같은 질문에 답한다.

- routing은 "이 tenant 요청을 어느 cell로 보낼 것인가"를 결정한다
- identity policy는 "어떤 workload가 그 cell에 들어올 수 있는가"를 결정한다

둘의 순서가 어긋나면 대표적으로 이런 장애가 난다.

1. tenant route는 새 dedicated cell로 넘어갔는데 worker principal allowlist가 안 열려 async job이 전부 deny된다
2. SPIFFE principal은 미리 열렸는데 tenant route는 old cell을 봐서 cross-cell 호출이 조용히 생긴다
3. foreground API는 새 cell을 보지만 support tool이나 replay worker는 old identity로 old cell을 계속 친다
4. data verification은 통과했는데 auth shadow divergence를 안 봐서 tenant boundary allow bug가 숨어 남는다

그래서 split-out cutover는 routing flip 하나가 아니라 **route registry, principal allowlist, background path inventory, auth drift telemetry**를 묶은 joint rollout이어야 한다.

### 2. 운영 평면을 먼저 분리해서 봐야 한다

| 평면 | authoritative source | cutover 때 같이 볼 것 | 대표 장애 |
|---|---|---|---|
| tenant routing plane | tenant directory, cell assignment registry | tenant -> cell mapping freshness, stale route cache | 일부 경로만 old cell로 감 |
| data plane | source writer, replicated snapshot, delta catch-up | final delta, write fence, background drain | old/new 양쪽 write |
| identity plane | SPIFFE issuer, trust bundle, allowlist policy | principal coverage, bundle propagation, legacy principal overlap | 새 cell 호출 deny 혹은 broad allow |
| auth drift plane | shadow decision log, deny bucket, cross-tenant allow counter | old/new divergence, `principal_missing`, `tenant_mismatch` | cutover 직후 조용한 권한 오류 |

중요한 것은 한 평면만 green이어도 cutover를 열면 안 된다는 점이다.
특히 tenant split-out은 cell 이동 자체가 blast radius 축소 목적이므로, identity plane이 틀어져 새 cell이 무방비가 되면 설계 의도가 바로 무너진다.

### 3. preflight에서는 traffic inventory가 routing table보다 더 넓어야 한다

cutover 전에 tenant 42가 어느 경로로 시스템에 들어오는지 전부 세야 한다.

- user-facing API
- internal sync RPC
- batch / replay / reconciliation worker
- support / admin tooling
- search indexer, webhook sender, outbox relay

이 inventory가 없으면 route flip 뒤에도 old principal이나 old endpoint hit가 남는다.
그래서 preflight에서는 다음을 함께 준비한다.

- tenant-specific routing entry와 rollback window
- dedicated cell warmup 상태
- 새 cell용 SPIFFE/workload identity principal 발급
- principal별 allowlist shadow mode
- route class별 auth drift dashboard

### 4. background path hygiene는 route epoch와 principal epoch를 같이 확인해야 한다

foreground API가 green이라고 tenant move가 끝난 것은 아니다.
오래 사는 background caller는 cutover 시점의 truth를 캡처한 채 계속 살 수 있기 때문이다.

대표 hidden caller:

- replay / reconciliation worker: long-lived lease나 cursor에 old cell target을 붙든다
- support / admin tooling: operator 세션이나 jumpbox cache에 tenant -> cell mapping이 남는다
- search indexer / outbox relay: target index alias나 queue namespace를 old assignment 기준으로 유지한다
- webhook sender: delivery worker가 legacy principal이나 old endpoint partition을 계속 사용한다

이 클래스들은 route cache와 principal cache를 따로 들고 있기 때문에, directory flip만으로는 정리가 안 된다.
그래서 tenant cutover object에는 caller inventory뿐 아니라 `routing_epoch`와 `principal_epoch`도 같이 넣는 편이 안전하다.

실전 제어 포인트:

- worker lease renew 시마다 tenant directory epoch를 재검증한다
- replay job, indexing task, webhook delivery payload에 target cell 또는 route version을 명시한다
- support tooling은 짧은 TTL cache와 tenant-scoped token exchange를 강제한다
- `legacy_principal_last_seen`과 `old_cell_hit_after_cutover`를 caller class별로 분리 집계한다
- background caller가 새 epoch를 ack하기 전에는 cleanup과 old principal 제거를 열지 않는다

### 5. cutover 전에 allowlist를 먼저 "관찰 가능한 상태"로 열어 두는 편이 안전하다

workload identity rollout을 route flip과 동시에 처음 적용하면 원인 분리가 어려워진다.
권장 방식은 보통 다음과 같다.

1. 새 dedicated cell principal을 미리 발급한다
2. allowlist에는 등록하되 `observe-only` 또는 shadow logging 상태로 둔다
3. mirrored call이나 sampled health probe로 `principal_missing`, `trust_bundle_stale`, `unexpected_allow`를 본다
4. old principal은 아직 authoritative path에서만 쓰게 두고, 새 principal이 실제로 어떤 경로를 건드리는지 먼저 계측한다

핵심은 "allowlist를 미리 열어 두라"가 아니라, **enforce 전에 telemetry를 확보하라**는 것이다.
그래야 route flip 이후 deny가 났을 때 routing 문제인지 principal 문제인지 바로 분리할 수 있다.

#### tenant caller-class rollout matrix를 별도 artifact로 둬야 한다

tenant cutover에서 `required_principals`를 한 줄 리스트로만 적어 두면 foreground green을 background readiness로 오해하기 쉽다.
실전에서는 caller class마다 principal 발급 타이밍, allowlist mode, drift soak exit evidence가 다르기 때문이다.

| caller class | 분류 | principal issuance checklist | allowlist / cutover checklist | drift soak exit evidence | 왜 분리해야 하나 |
|---|---|---|---|---|---|
| edge / API / synchronous ingress | foreground | target-cell pod principal, probe principal, verifier overlap, token exchange audience가 모두 준비됨 | pre-cutover는 `observe-only`, cutover 시점에는 route flip과 `enforce`를 같은 change set으로 묶고 old principal은 `legacy-observe`로 짧게 둠 | `auth.principal_missing=0`, `routing.old_cell_hit_after_cutover=0`, `auth.shadow.old_allow_new_deny=0` | 사용자 트래픽은 즉시 보이지만 cache skew가 있으면 p99 incident처럼 터진다 |
| internal sync RPC / fan-out hop | foreground | caller 서비스별 target-cell principal, downstream SAN/audience, connection pool 재기동 경로가 준비됨 | sampled mirrored RPC로 `tenant_mismatch`를 확인하고 cutover 때 client-side route cache를 같이 무효화 | `routing.tenant_mismatch=0`, `auth.shadow.old_deny_new_allow=0`, old target retry 0 | ingress green이어도 내부 fan-out hop이 old cell을 붙잡을 수 있다 |
| replay / reconciliation / billing worker | background | lease owner principal, queue consumer principal, `required_route_epoch`, `required_principal_set`가 job payload에 포함됨 | shadow consume 또는 dry-run 뒤 cutover 때 old lease revoke, queue binding 전환, old principal `quarantine-after-ack` | `auth.legacy_principal_last_seen=0`, `routing.old_cell_hit_after_cutover=0`, old queue backlog 0 | long-lived lease와 cursor가 cutover 직전 truth를 오래 붙잡는다 |
| search indexer / outbox relay / webhook sender | background | sender principal, retry worker principal, target alias/partition namespace가 새 cell 기준으로 발급됨 | dark canary send, sampled reindex, retry partition rebind를 마친 뒤에만 `enforce` | stale index write 0, old retry partition hit 0, `auth.principal_missing=0` | ingress shadow에는 보이지 않는 egress 경로가 남기 쉽다 |
| support / admin tooling | background-manual | delegated operator principal, break-glass TTL, tenant-scoped token exchange, audit tag가 준비됨 | audit-only narrow allowlist, cutover 직전 강제 re-auth와 route cache bust, old principal은 `deny-with-alert` | support probe 0, `legacy_principal_last_seen=0`, shared-cell admin action 0 | 저빈도지만 blast radius가 커서 hidden broad allow의 원인이 된다 |

foreground/background checklist를 실제 운영 artifact로 만들 때는 최소 아래를 caller class별 열로 남기는 편이 안전하다.

1. principal issuance: `target_principal`, `probe_principal`, `issuer_or_bundle_ready`, `required_route_epoch`
2. allowlist phase: `pre_cutover_mode`, `cutover_mode`, `legacy_mode`, `quarantine_ready`
3. drift soak: `old_cell_hit_after_cutover`, `legacy_principal_last_seen`, `shadow_divergence`, `old_queue_backlog`
4. ownership: 누가 principal을 발급하고, 누가 allowlist를 올리고, 누가 drift soak 종료를 승인하는지

특히 foreground green은 soak 시작 조건일 뿐 종료 조건이 아니다.
cleanup과 old principal 제거는 background caller가 새 `route_epoch`와 `principal_epoch`를 모두 ack한 뒤에만 여는 편이 안전하다.

### 6. dedicated-cell promotion은 mirrored traffic -> dual-read -> auth drift 순서로 닫아야 한다

tenant split-out에서는 검증 신호가 많다고 순서를 바꿔도 되는 것이 아니다.
dedicated-cell 승격은 보통 아래 사다리로 닫는 편이 안전하다.

| 단계 | 이 단계가 답하는 질문 | 주로 보는 증거 | 다음 단계로 넘어가는 기준 |
|---|---|---|---|
| mirrored traffic | 새 dedicated cell route와 auth plugin wiring이 실제 요청 mix를 받아도 안전한가 | `routing.shadow.route_mismatch`, mirrored request latency, `auth.principal_missing`, background caller mirror hit | shadow path가 side effect 없이 production mix를 소화하고 route/principal wiring 오류가 설명 가능한 수준으로 줄어듦 |
| dual-read | 같은 tenant 요청이 old/new cell에서 같은 row, projection, response invariant를 내는가 | `verification.invariant_mismatch`, projection freshness diff, tenant claim projection mismatch, sampled compare evidence | unexplained diff가 0이거나 allowlisted skew로만 설명되고 compare budget이 SLO 안에 남음 |
| auth drift soak | authoritative route flip 뒤에도 모든 caller가 같은 trust truth를 보는가 | `auth.shadow.old_deny_new_allow`, `auth.shadow.old_allow_new_deny`, `auth.legacy_principal_last_seen`, `routing.old_cell_hit_after_cutover` | critical divergence가 soak window 동안 0이고 legacy principal과 old cell hit가 operational silence 상태로 들어감 |

이 셋은 서로 대체재가 아니다.

- mirrored traffic은 gateway, router, auth plugin, principal wiring이 live input을 받았을 때 어떻게 흔들리는지 본다
- dual-read는 데이터와 read-model의 parity를 본다
- auth drift soak은 route flip 뒤에도 policy와 identity truth가 caller 전체에 같은지 본다

순서를 바꾸면 해석이 흐려진다.
mirrored traffic 없이 dual-read부터 보면 route/plugin wiring 문제를 data diff로 오해하기 쉽고, dual-read 없이 auth drift만 보면 read parity가 깨진 상태를 identity 문제로만 몰아갈 수 있다.
그래서 dedicated-cell 승격은 **mirrored traffic으로 입력을 확보하고, dual-read로 read parity를 증명한 뒤, auth drift soak으로 trust parity를 닫는 사다리**로 보는 편이 안전하다.

### 7. fenced cutover는 route flip과 principal mode 전환을 같은 change set으로 묶어야 한다

안전한 절차는 보통 아래 순서를 따른다.

1. tenant-specific write fence 또는 short freeze 시작
2. snapshot + delta catch-up 종료 확인
3. tenant route를 dedicated cell로 flip
4. 새 cell principal allowlist를 `enforce`로 올림
5. old principal을 `drain-read-only` 또는 `legacy-observe`로 낮춤
6. background worker와 support tooling route cache를 즉시 무효화

여기서 중요한 것은 route flip과 allowlist enforce 사이에 의미 있는 공백을 두지 않는 것이다.
둘 사이 공백이 길면 다음 둘 중 하나가 생긴다.

- route는 새 cell인데 principal이 막혀 요청이 연쇄 실패
- principal은 열렸는데 route가 아직 old cell이라 broad path가 생김

다만 새 cell이 새 SPIRE issuer나 mesh trust root를 같이 도입한다면 allowlist overlap만으로는 부족하다.
그 경우에는 verifier가 old/new root를 모두 받아들이는 기간과 bundle rollback window를 별도로 관리해야 하며, 이는 [Trust-Bundle Rollback During Cell Cutover 설계](./trust-bundle-rollback-during-cell-cutover-design.md)에서 따로 다룬다.

### 8. post-cutover에서는 data drift보다 auth drift가 더 오래 남을 수 있다

데이터 delta는 몇 초 안에 닫혀도 auth drift는 더 오래 tail을 끈다.
대표 이유:

- 일부 pod의 trust bundle 캐시가 늦게 갱신됨
- support tool이나 replay worker가 old principal을 계속 사용함
- cell-local policy cache가 old tenant mapping을 봄
- background path만 old deny / new allow 또는 old allow / new deny가 남음

그래서 soak 구간에서는 최소 아래 신호를 tenant, cell, principal 단위로 본다.

- `auth.shadow.old_deny_new_allow`
- `auth.shadow.old_allow_new_deny`
- `auth.principal_missing`
- `auth.cross_tenant_allow`
- `auth.legacy_principal_last_seen`
- `routing.old_cell_hit_after_cutover`
- `routing.tenant_mismatch`

이 구간의 핵심 질문은 "새 cell이 살아 있는가"가 아니라,
**모든 caller가 새 routing truth와 새 trust truth를 같은 방식으로 보고 있는가**다.

### 9. rollback보다 forward-fix가 더 안전한 순간이 많다

cutover 직후 문제가 나도 무조건 old cell로 되돌리는 것이 정답은 아니다.

- 새 cell이 이미 authoritative write를 받기 시작했을 수 있다
- old cell allowlist를 다시 열면 broad access가 생길 수 있다
- 문제 원인이 routing이 아니라 identity cache propagation일 수 있다

그래서 rollback 선택은 보통 세 갈래로 나뉜다.

| 상황 | 우선 조치 | 이유 |
|---|---|---|
| route만 틀렸고 write fence 안 | route rollback | authority가 아직 old 쪽에 있음 |
| data는 맞고 principal deny만 남음 | identity forward-fix | storage rollback보다 scope가 좁음 |
| broad allow가 감지됨 | old/new 모두 stricter policy로 quarantine | 먼저 blast radius를 줄여야 함 |

핵심은 rollback을 습관처럼 누르지 않고, **지금 write truth와 trust truth가 어디 있는지 보고 되돌릴지 고칠지 결정하는 것**이다.

### 10. 승격 종료 조건은 "deprecated principal이 조용해질 때"다

bridge 제거 시점을 너무 빨리 잡으면 hidden caller가 나중에 터진다.
보통 아래 조건이 같이 만족돼야 cleanup으로 들어간다.

- old principal last-seen이 충분히 길게 0
- post-cutover auth divergence critical bucket 0
- old cell hit after cutover 0
- tenant-specific support tooling까지 새 route/principal로 확인
- rollback window 종료 기준 충족

즉 cleanup은 data copy 종료 시점이 아니라, **legacy caller가 operationally silence 상태에 들어간 뒤** 시작하는 편이 안전하다.

## 실전 시나리오

### 시나리오 1: enterprise tenant를 dedicated cell로 승격

문제:

- tenant 42가 shared pool p99를 흔들어 dedicated cell로 분리해야 한다
- API, search indexer, billing worker가 모두 이 tenant를 건드린다

해결:

- tenant routing registry에 dedicated cell entry를 준비한다
- 새 cell용 SPIFFE principal과 allowlist를 shadow 모드로 먼저 배포하고 mirrored traffic으로 route/plugin wiring을 검증한다
- sampled dual-read로 tenant 42의 row, projection, response invariant parity를 먼저 축적한다
- write fence와 route flip, principal enforce를 하나의 change set으로 묶는다
- post-cutover에는 auth drift soak으로 old cell hit, legacy principal last-seen, shadow divergence를 함께 닫는다

### 시나리오 2: background path가 stale route cache와 legacy principal을 붙잡는다

문제:

- 사용자 API는 이미 dedicated cell을 보지만 replay worker, support tooling, search indexer, webhook sender는 old route cache나 old principal로 old cell을 계속 친다
- 일부 경로는 `principal_missing`, 일부 경로는 old queue drain이나 stale index write로 보여 장애가 조용히 분산된다

해결:

- foreground success를 cutover 종료 신호로 쓰지 않는다
- replay job, indexing task, delivery worker에 `tenant_route_epoch`와 `required_principal_set`을 태워 stale caller를 즉시 재시작하거나 quarantine한다
- support tooling, indexer, webhook sender까지 caller class별 `legacy_principal_last_seen`과 `old_cell_hit_after_cutover`를 분리 집계한다
- replay drain, reindex backlog, webhook retry backlog가 모두 새 route/principal로 닫히기 전까지 cleanup과 old allowlist 제거를 막는다

### 시나리오 3: allowlist가 너무 넓어 cross-cell allow가 생긴다

문제:

- cutover를 쉽게 하려고 `spiffe://prod.example.com/ns/*/sa/orders-api`처럼 broad principal을 허용했다

해결:

- tenant-specific target cell과 caller class에 맞춘 최소 allowlist로 줄인다
- `old deny -> new allow` divergence를 critical bucket으로 올린다
- broad allow를 제거하기 전까지 cleanup을 금지한다

## 코드로 보기

```pseudo
function canCutover(scope):
  ladderReady =
    scope.mirroredTrafficRouteMismatch == 0 and
    scope.mirroredTrafficPrincipalMissing == 0 and
    scope.dualReadInvariantMismatch == 0 and
    scope.dualReadExplainableSkewOnly and
    scope.authShadowCriticalDivergence == 0

  routingReady =
    scope.directoryFresh and
    scope.routeShadowMismatch == 0 and
    scope.backgroundOldCellHit == 0 and
    scope.backgroundRouteEpochLag == 0

  dataReady =
    scope.snapshotComplete and
    scope.deltaLagSec < 3 and
    scope.writeFenceHealthy

  identityReady =
    scope.requiredPrincipalsIssued and
    scope.principalMissingRate == 0 and
    scope.legacyBackgroundPrincipalLastSeen == 0 and
    scope.trustBundleLagSec < 30

  callerClassReady =
    all(scope.callerClasses, class =>
      class.targetPrincipalIssued and
      class.allowlistReady and
      class.routeEpochAcked and
      class.driftSilent)

  return ladderReady and routingReady and dataReady and identityReady and callerClassReady
```

```yaml
tenant_cutover:
  tenant_id: tenant-42
  source_cell: shared-apac-3
  target_cell: dedicated-enterprise-a
  verification_ladder:
    mirrored_traffic:
      mode: read-only-shadow
      exit:
        route_mismatch: 0
        principal_missing: 0
        unexpected_side_effect: 0
    dual_read:
      sample_rate: 0.2
      exit:
        invariant_mismatch: 0
        explainable_skew_only: true
    auth_drift:
      soak_minutes: 60
      exit:
        old_deny_new_allow: 0
        old_allow_new_deny: 0
        legacy_principal_last_seen_minutes: 60
        old_cell_hit_after_cutover: 0
  routing:
    mode: fenced_flip
    epoch: 1842
    cache_invalidation: immediate
  identity:
    required_principals:
      - spiffe://prod.example.com/ns/enterprise/sa/orders-api
      - spiffe://prod.example.com/ns/enterprise/sa/replay-worker
      - spiffe://prod.example.com/ns/enterprise/sa/search-indexer
      - spiffe://prod.example.com/ns/enterprise/sa/support-tool
      - spiffe://prod.example.com/ns/enterprise/sa/webhook-sender
      - spiffe://prod.example.com/ns/enterprise/sa/billing-worker
    legacy_principals:
      - spiffe://prod.example.com/ns/shared/sa/orders-api
    overlap_mode: legacy-observe
  caller_class_matrix:
    foreground_api:
      plane: foreground
      issuance:
        target_principal: spiffe://prod.example.com/ns/enterprise/sa/orders-api
        probe_principal: spiffe://prod.example.com/ns/enterprise/sa/orders-api-probe
        verifier_overlap: ready
      allowlist:
        pre_cutover_mode: observe-only
        cutover_mode: enforce-with-route-flip
        legacy_mode: legacy-observe
      soak_exit:
        principal_missing: 0
        old_cell_hit_after_cutover: 0
        old_allow_new_deny: 0
    background_replay:
      plane: background
      issuance:
        target_principal: spiffe://prod.example.com/ns/enterprise/sa/replay-worker
        queue_consumer_principal: spiffe://prod.example.com/ns/enterprise/sa/billing-worker
        required_route_epoch: 1842
      allowlist:
        pre_cutover_mode: shadow-consume
        cutover_mode: enforce-after-lease-rebind
        legacy_mode: quarantine-after-ack
      soak_exit:
        legacy_principal_last_seen_minutes: 60
        old_cell_hit_after_cutover: 0
        old_queue_backlog: 0
    background_egress:
      plane: background
      issuance:
        target_principal: spiffe://prod.example.com/ns/enterprise/sa/webhook-sender
        retry_principal: spiffe://prod.example.com/ns/enterprise/sa/search-indexer
        target_namespace_bound: true
      allowlist:
        pre_cutover_mode: dark-canary
        cutover_mode: enforce-after-partition-rebind
        legacy_mode: deny-with-alert
      soak_exit:
        old_retry_partition_hit: 0
        stale_index_write: 0
        principal_missing: 0
    support_tooling:
      plane: background-manual
      issuance:
        delegated_principal: spiffe://prod.example.com/ns/enterprise/sa/support-tool
        break_glass_ttl_minutes: 15
        audit_tagging: enabled
      allowlist:
        pre_cutover_mode: audit-only
        cutover_mode: enforce-after-reauth
        legacy_mode: deny-with-alert
      soak_exit:
        support_probe_old_cell_hit: 0
        legacy_principal_last_seen_minutes: 60
        shared_cell_admin_action: 0
  post_cutover_auth_drift_exit:
    old_deny_new_allow: 0
    old_allow_new_deny: 0
    legacy_principal_last_seen_minutes: 60
    stale_route_cache_hit: 0
    old_cell_hit_after_cutover: 0
```

핵심은 policy syntax가 아니라, route와 principal 상태를 같은 tenant cutover object에서 읽는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| route cutover와 identity rollout을 분리 | 팀별 진행이 쉽다 | 원인 분리가 어려운 반쪽 성공이 생긴다 | 영향 범위가 정말 독립적일 때만 |
| joint route + principal cutover | blast radius 설명이 명확하다 | 준비할 gate와 telemetry가 늘어난다 | dedicated cell migration, hot tenant split-out |
| 긴 legacy principal overlap | rollback과 디버깅이 쉽다 | broad trust가 오래 남는다 | hidden caller가 많을 때 |
| 빠른 strict allowlist 전환 | trust surface를 빨리 줄인다 | background path deny에 취약하다 | caller inventory가 충분할 때 |
| post-cutover auth drift soak | silent auth bug를 줄인다 | cleanup이 느려진다 | tenant isolation, premium tenant, 규제 workload |

핵심은 tenant split-out with service identity rollout이 단순 migration이 아니라, **tenant routing cutover와 workload identity trust cutover를 같은 승격 절차로 닫는 설계**라는 점이다.

## 꼬리질문

> Q: tenant route만 바꿨는데 왜 service identity allowlist까지 같이 봐야 하나요?
> 의도: routing과 trust boundary를 함께 보는지 확인
> 핵심: 새 cell에 도착한 호출이 누구인지 검증하지 못하면 dedicated cell 분리 효과가 바로 깨지기 때문이다.

> Q: SPIFFE principal을 미리 allowlist에 올리면 위험하지 않나요?
> 의도: observe-only/shadow 단계의 의미 이해 확인
> 핵심: enforce 전에 telemetry를 확보하려는 것이고, broad allow가 아니라 제한된 shadow 관측 상태로 두는 편이 안전하다.

> Q: data verification이 끝났는데 왜 auth drift soak이 더 필요하죠?
> 의도: data drift와 auth drift의 tail 차이 이해 확인
> 핵심: trust bundle cache, legacy worker, policy cache는 data delta보다 더 오래 어긋날 수 있기 때문이다.

> Q: 문제 나면 old cell로 바로 rollback하면 안 되나요?
> 의도: write truth와 trust truth의 위치를 함께 판단하는지 확인
> 핵심: 새 cell이 이미 authoritative write를 받았으면 identity forward-fix가 더 안전할 수 있다.

## 한 줄 정리

Tenant split-out with service identity rollout 설계는 tenant를 dedicated cell로 옮길 때 route flip, write fence, SPIFFE/workload identity allowlist, post-cutover auth drift soak을 같은 tenant-scoped gate로 묶어 blast radius와 trust drift를 함께 제어하는 운영 설계다.

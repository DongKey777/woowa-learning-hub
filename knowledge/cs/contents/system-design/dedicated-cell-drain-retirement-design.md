# Dedicated Cell Drain and Retirement 설계

> 한 줄 요약: dedicated cell drain and retirement 설계는 tenant가 shared cell에서 dedicated cell로 완전히 이동한 뒤 residual route hit, legacy principal, rollback handle, donor cleanup을 순서 있게 닫아 post-migration drain과 cleanup point-of-no-return을 안전하게 통과하는 운영 설계다.
>
> 문서 역할: 이 문서는 [Tenant Split-Out with Service Identity Rollout 설계](./tenant-split-out-service-identity-rollout-design.md) 이후 shared cell exit 증거, rollback closure, legacy principal retirement를 어떤 순서와 신호로 닫아야 하는지 설명하는 post-cutover drain deep dive다.

retrieval-anchor-keywords: dedicated cell drain and retirement, shared cell exit proof, shared cell retirement, post migration drain, dedicated cell cleanup gate, legacy principal retirement, rollback closure after tenant split out, old cell hit after cutover, legacy principal last seen, shared cell donor tombstone, dedicated cell point of no return, replay backlog closure, support tooling route hygiene, webhook sender principal drain, search indexer drain, tenant move cleanup, shared cell route silence, shared cell principal silence, tenant egress verification, drain to cleanup handoff

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Tenant Partition Strategy / Reassignment 설계](./tenant-partition-strategy-reassignment-design.md)
> - [Tenant Split-Out with Service Identity Rollout 설계](./tenant-split-out-service-identity-rollout-design.md)
> - [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)
> - [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
> - [Trust-Bundle Rollback During Cell Cutover 설계](./trust-bundle-rollback-during-cell-cutover-design.md)
> - [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)
> - [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)
> - [Write-Freeze Rollback Window 설계](./write-freeze-rollback-window-design.md)
> - [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)
> - [Search Indexing Pipeline 설계](./search-indexing-pipeline-design.md)
> - [Webhook Delivery Platform 설계](./webhook-delivery-platform-design.md)
> - [Database: Hot Tenant Split-Out, Routing, and Cutover Playbook](../database/tenant-split-out-routing-cutover-playbook.md)
> - [Security: Service-to-Service Auth: mTLS, JWT, SPIFFE](../security/service-to-service-auth-mtls-jwt-spiffe.md)
> - [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)

## 이 문서 다음에 보면 좋은 설계

- tenant 이동과 identity rollout 자체를 먼저 다시 맞추려면 [Tenant Split-Out with Service Identity Rollout 설계](./tenant-split-out-service-identity-rollout-design.md)의 `background path hygiene`와 `승격 종료 조건`을 함께 본다.
- trust bundle overlap을 얼마나 오래 남겨야 하는지는 [Trust-Bundle Rollback During Cell Cutover 설계](./trust-bundle-rollback-during-cell-cutover-design.md)의 `bundle rollback window`가 직접 연결된다.
- shared cell cleanup이 irreversible boundary를 언제 넘는지는 [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)로 이어 보면 정리가 된다.

## 핵심 개념

tenant를 dedicated cell로 옮긴 뒤 진짜 어려운 부분은 cutover 자체보다 "shared cell이 정말 비었는가"를 증명하는 일이다.

- foreground route가 dedicated cell을 보는가
- background worker가 old cell과 old queue를 놓았는가
- legacy principal이 shared allowlist와 trust path에서 사라졌는가
- rollback을 닫아도 correction-only로 운영 가능한가

즉 dedicated cell migration의 종료 조건은 단순 route flip 성공이 아니라, **shared cell silence와 rollback closure를 같은 증거 묶음으로 닫는 것**이다.

## 깊이 들어가기

### 1. 왜 post-migration drain이 별도 단계인가

tenant split-out은 흔히 cutover 순간만 크게 보이지만, shared cell exit는 그 뒤에 남은 잔존 경로를 정리해야 끝난다.

- user-facing API는 이미 dedicated cell로 감
- replay worker는 오래 잡은 lease 때문에 shared cell namespace를 계속 봄
- support tooling은 old tenant directory cache를 붙잡음
- webhook sender나 search indexer는 old principal 또는 old queue binding을 유지함

즉 foreground green만으로는 shared cell이 비었다고 말할 수 없다.
실전에서는 dedicated cell cutover 다음에 **drain window, legacy-principal quarantine, rollback closure, destructive cleanup**을 따로 운영한다.

### 2. exit evidence는 route, principal, repair, cleanup 축으로 나눠 본다

| 축 | authoritative question | exit 증거 | 빨리 닫으면 생기는 문제 |
|---|---|---|---|
| routing silence | 모든 caller가 dedicated cell만 보는가 | `old_cell_hit_after_cutover=0`, stale route cache 0, support/admin route probe green | hidden caller가 shared cell로 write/read를 재개 |
| principal silence | shared principal과 old trust가 더 이상 쓰이지 않는가 | `legacy_principal_last_seen=0`, old allowlist hit 0, old root last-seen 0 | cleanup 후 auth deny 또는 broad trust 복구 |
| repair silence | replay, reindex, webhook retry, reconciliation이 새 cell에서 닫혔는가 | backlog 0, retry destination=new cell, old queue lag 0 | shared cell queue를 purge했다가 late task 손실 |
| rollback closure | fast rollback을 닫아도 되는가 | write truth 확정, donor read-only 종료, rollback packet 승인 | cleanup 후 되돌릴 근거와 손잡이가 동시에 사라짐 |

핵심은 "traffic가 적다"가 아니라, 어떤 축의 silence가 증명됐는지 분리해서 보는 것이다.

### 3. 권장 상태 전이는 reversible soak에서 shared-cell tombstone까지다

좋은 운영은 보통 아래처럼 상태를 분리한다.

```text
CUTOVER_COMPLETE
 -> REVERSIBLE_SOAK
 -> SHARED_CELL_DRAIN
 -> LEGACY_PRINCIPAL_QUARANTINE
 -> ROLLBACK_CLOSED
 -> SHARED_CELL_TOMBSTONE
 -> IRREVERSIBLE_CLEANUP
```

각 단계의 의미는 다르다.

1. `REVERSIBLE_SOAK`: route flip과 write authority는 dedicated cell로 갔지만 donor/shared cell을 즉시 지우지 않는다.
2. `SHARED_CELL_DRAIN`: replay worker, search indexer, webhook sender, support tooling이 old route/queue/principal을 버리는지 본다.
3. `LEGACY_PRINCIPAL_QUARANTINE`: old principal을 `observe`에서 `deny-with-alert`로 낮춰 hidden caller를 잡는다.
4. `ROLLBACK_CLOSED`: route rollback, issuer rollback, donor reactivation을 policy상 닫는다.
5. `SHARED_CELL_TOMBSTONE`: shared cell tenant slot, old queue namespace, emergency route를 복구 가능하지만 비활성 상태로 둔다.
6. `IRREVERSIBLE_CLEANUP`: tombstone, old allowlist, bridge, donor data를 제거해 point-of-no-return을 넘는다.

이 순서가 섞이면 rollback closure와 destructive cleanup이 한 번에 일어나 사고 원인 분리가 어려워진다.

### 4. background drain inventory는 foreground보다 넓어야 한다

shared cell exit 증거는 API 요청량보다 background residue에서 더 자주 깨진다.

대표 drain inventory:

- replay / reconciliation worker
- search indexer / outbox relay
- webhook sender / retry worker
- support / admin tooling
- audit export, billing close, archive restore

각 클래스는 서로 다른 cache와 principal을 가진다.
그래서 tenant-retirement packet에는 최소 아래 필드를 caller class별로 남기는 편이 좋다.

- `required_route_epoch`
- `required_principal_set`
- `last_shared_cell_hit_at`
- `last_legacy_principal_seen_at`
- `old_queue_backlog`
- `quarantine_result`

이 inventory가 없으면 shared cell exit는 문장으로는 끝났지만, 실제로는 hidden worker가 old namespace를 계속 두드리는 상태가 된다.

### 5. legacy principal retirement는 route silence 뒤에 와야 한다

old principal을 빨리 끄면 security surface는 줄지만, 아직 route silence가 안 닫힌 caller가 전부 `principal_missing`으로 바뀌어 원인이 흐려진다.
반대로 너무 늦게 남기면 dedicated cell isolation이 약해진다.

권장 순서는 보통 이렇다.

1. dedicated cell route가 모든 caller class에서 관측상 green인지 확인한다.
2. shared principal을 `legacy-observe`로 낮춰 unexpected caller provenance를 수집한다.
3. hidden caller를 모두 dedicated principal로 올린다.
4. shared principal을 `quarantine` 또는 `deny-with-alert`로 바꾼다.
5. 충분한 silence window 뒤 allowlist, trust bundle overlap, token exchange rule을 제거한다.

즉 principal retirement는 policy cleanup이 아니라, **caller inventory를 증명으로 바꾸는 마지막 quarantine 단계**다.

### 6. rollback closure는 cleanup과 다르고 더 먼저 승인돼야 한다

많이 하는 실수는 donor purge나 old allowlist 제거를 rollback closure와 같은 뜻으로 보는 것이다.
하지만 rollback closure는 "지울 수 있는가"가 아니라 "더는 빠른 rollback을 운영 절차로 약속하지 않는가"를 뜻한다.

보통 아래가 같이 닫혀야 한다.

- dedicated cell이 authoritative write truth를 충분히 오래 유지
- shared cell donor가 read-only 또는 tombstone 상태로 안정화
- replay/reindex/webhook retry가 새 cell 기준으로 닫힘
- auth shadow divergence critical bucket 0
- trust bundle overlap이 rollback-only가 아니라 drain-tail 흡수용으로만 남음
- 도메인 owner가 forward-fix only로 전환 승인

여기서 중요한 점은 rollback closure 후에도 soft tombstone과 delayed cleanup이 잠시 남을 수 있다는 것이다.
즉 rollback을 닫았다고 바로 point-of-no-return을 넘어서는 안 된다.

### 7. cleanup point-of-no-return은 shared-cell truth를 지우는 순간이다

tenant가 shared cell에서 완전히 나갔다고 해도, 아래 중 하나를 지우는 순간부터는 rollback보다 correction이 더 현실적이 된다.

- tenant -> shared cell emergency route 삭제
- shared-cell queue namespace purge
- shared principal allowlist / token exchange rule 삭제
- donor state purge 또는 old index alias 삭제
- shared-cell verifier에서 old root 제거

그래서 destructive cleanup은 보통 세 단계로 나눈다.

| 단계 | 하는 일 | 아직 가능한 것 |
|---|---|---|
| soft tombstone | route disable, old principal hard deny, old queue freeze | provenance 확인, limited reactivation |
| delayed purge | donor data, old queue, alias, config key 제거 | forward-fix only, correction 가능 |
| full retirement | shared tenant slot와 rollback metadata 제거 | 재승격 대신 재bootstrap 필요 |

즉 point-of-no-return은 "shared cell이 비었다"가 아니라, **shared cell로 돌아갈 operational handle까지 없어진 순간**이다.

### 8. retirement evidence packet이 있어야 cleanup이 반복 가능해진다

tenant fully exited shared cell이라는 판단은 기억이 아니라 packet으로 남겨야 한다.

권장 packet:

- caller class별 `old_cell_hit_after_cutover` 추이
- caller class별 `legacy_principal_last_seen`와 quarantine 결과
- replay backlog, reindex backlog, webhook retry backlog 종료 증거
- rollback closure 승인 시각과 승인자
- tombstone start/end 시각
- point-of-no-return 직전 probe와 unexpected hit 결과

이 패킷이 있으면 후속 tenant split-out에서도 drain 조건을 재사용할 수 있다.
database repair signal과 security tail signal을 같은 승인 packet으로 어떻게 합칠지는 [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)에서 바로 이어서 볼 수 있다.

### 9. 관측성은 last-seen provenance가 핵심이다

운영자는 단순 카운터보다 "누가 아직 shared cell을 붙잡는가"를 알아야 한다.

권장 신호:

- `routing.old_cell_hit_after_cutover{tenant,caller_class}`
- `auth.legacy_principal_last_seen{tenant,caller_class}`
- `drain.old_queue_backlog{tenant,queue}`
- `drain.shared_cell_probe_fail_total{probe_class}`
- `retirement.rollback_closure_ready`
- `retirement.point_of_no_return_ready`
- `trust.old_root_last_seen{tenant,verifier_class}`

숫자가 0이라는 사실만으로는 부족하고, 마지막 provenance와 timestamp가 함께 남아야 숨은 caller를 잡을 수 있다.

## 실전 시나리오

### 시나리오 1: billing worker만 shared principal을 계속 사용한다

문제:

- user API, replay worker, search indexer는 모두 dedicated cell로 옮겼다
- 그런데 billing close worker가 하루 한 번 shared principal로 shared cell queue를 계속 친다

해결:

- `legacy_principal_last_seen{caller_class=billing-worker}`를 별도로 집계한다
- billing close batch에 `required_route_epoch`와 `required_principal_set`을 강제한다
- old principal을 `deny-with-alert`로 낮춰 hidden dependency를 surface한다
- billing close provenance가 사라지기 전에는 rollback closure와 queue purge를 막는다

### 시나리오 2: rollback window는 끝났지만 replay backlog가 shared cell에 남아 있다

문제:

- foreground는 안정적이어서 fast rollback은 닫으려 한다
- 하지만 일부 reconciliation replay가 old queue namespace를 아직 비우지 못했다

해결:

- rollback closure와 queue purge를 분리한다
- fast rollback은 닫되 shared queue는 soft tombstone으로 남긴다
- replay backlog가 dedicated cell destination으로 완전히 닫힌 뒤에만 destructive cleanup을 연다

### 시나리오 3: support tooling route cache가 늦게 비워진다

문제:

- 운영 콘솔과 admin script만 tenant 42를 여전히 shared cell로 보낸다
- 평소엔 트래픽이 적어 대시보드에서 잘 안 보인다

해결:

- support/admin caller class를 별도 probe와 last-seen bucket으로 분리한다
- manual operation 전에 tenant-scoped route probe를 강제한다
- support tooling `old_cell_hit_after_cutover`가 0이 되기 전까지 old emergency route 삭제를 금지한다

## 코드로 보기

```pseudo
function canCloseRollback(scope):
  return scope.writeTruth == "dedicated-cell" &&
         scope.replayBacklogAtSharedCell == 0 &&
         scope.authShadowCriticalDivergence == 0 &&
         scope.backgroundOldCellHit == 0 &&
         scope.rollbackApprovalGranted

function canReachPointOfNoReturn(scope):
  return canCloseRollback(scope) &&
         scope.legacyPrincipalLastSeenMinutes >= 120 &&
         scope.sharedQueueBacklog == 0 &&
         scope.oldRootLastSeenMinutes >= 120 &&
         scope.unexpectedSharedCellProbeFailures == 0
```

```yaml
tenant_retirement:
  tenant_id: tenant-42
  source_cell: shared-apac-3
  target_cell: dedicated-enterprise-a
  phase: LEGACY_PRINCIPAL_QUARANTINE
  route_silence:
    old_cell_hit_after_cutover: 0
    support_tool_probe_green: true
    required_route_epoch: 1842
  principal_silence:
    legacy_principal_last_seen_minutes: 135
    old_root_last_seen_minutes: 144
    quarantine_mode: deny_with_alert
  repair_silence:
    replay_backlog_shared_cell: 0
    reindex_backlog_shared_cell: 0
    webhook_retry_backlog_shared_cell: 0
  rollback:
    closure_ready: true
    closed_at: "2026-04-14T11:30:00+09:00"
  cleanup:
    tombstone_ready: true
    point_of_no_return_ready: true
```

핵심은 shared cell exit를 route, principal, backlog, rollback clock이 함께 들어 있는 retirement object로 다루는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 빠른 shared-cell retirement | 복잡도를 빨리 줄인다 | hidden caller와 rollback 손잡이를 놓치기 쉽다 | 작은 tenant, caller inventory가 완전할 때 |
| 긴 drain window | 숨은 background caller를 잡기 쉽다 | shared trust와 tombstone 비용이 오래 남는다 | enterprise tenant, background path가 많을 때 |
| tenant-scoped principal quarantine | provenance가 선명하다 | 정책/대시보드 준비가 더 필요하다 | shared principal 사용처가 다양한 플랫폼 |
| rollback closure와 purge 분리 | forward-fix 전환이 명확하다 | 단계가 늘어나 운영 문서가 복잡해진다 | 권한/데이터 authority가 함께 움직일 때 |
| full manual retirement packet | auditability가 높다 | 느리다 | 규제, 고가치 tenant, dedicated cell 승격 |

핵심은 dedicated cell drain and retirement 설계가 단순 cleanup이 아니라, **tenant가 shared cell을 완전히 떠났다는 증거를 route silence, principal silence, rollback closure로 순서 있게 닫는 운영 설계**라는 점이다.

## 꼬리질문

> Q: user-facing API가 모두 dedicated cell을 보면 migration은 끝난 것 아닌가요?
> 의도: foreground success와 shared-cell exit를 구분하는지 확인
> 핵심: 아니다. replay worker, support tooling, webhook sender 같은 background caller가 old cell과 old principal을 더 오래 붙잡을 수 있다.

> Q: legacy principal을 빨리 지우는 것이 항상 더 안전한가요?
> 의도: isolation 강화와 root-cause 분리의 균형 확인
> 핵심: route silence가 먼저 증명되지 않으면 hidden caller가 모두 auth 오류로만 보여 원인 분리가 더 어려워진다.

> Q: rollback closure와 point-of-no-return은 왜 다른가요?
> 의도: policy closure와 destructive cleanup의 차이 확인
> 핵심: rollback closure는 빠른 되돌림 약속을 닫는 것이고, point-of-no-return은 그 되돌림 손잡이 자체를 삭제하는 단계다.

> Q: shared cell tombstone을 남기는 이유는 무엇인가요?
> 의도: soft deletion과 delayed purge의 의미 확인
> 핵심: hidden caller provenance를 더 관찰하고, purge 전에 제한된 재활성화 가능성을 잠깐 남기기 위해서다.

## 한 줄 정리

Dedicated cell drain and retirement 설계는 tenant가 dedicated cell로 넘어간 뒤 shared cell residual traffic, legacy principal, replay tail, rollback handle을 순서 있게 닫아 cleanup point-of-no-return을 안전하게 통과하게 만드는 post-cutover 운영 설계다.

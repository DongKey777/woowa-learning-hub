# Bridge Retirement Evidence Packet

> 한 줄 요약: bridge retirement evidence packet은 database repair closure와 security tail closure를 한 장의 승인 패킷으로 묶어, replay backlog는 0인데 revoke tail이나 legacy trust가 남아 있는 반쪽 cleanup을 막는 운영 템플릿이다.
>
> 문서 역할: 이 문서는 [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md), [Dedicated Cell Drain and Retirement 설계](./dedicated-cell-drain-retirement-design.md), [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)에서 반복해서 등장하는 `retirement evidence packet`을 실제 approval packet 형태로 구체화한 template deep dive다.

retrieval-anchor-keywords: bridge retirement evidence packet, retirement approval packet, database repair signals, security tail signals, verification evidence handoff, shadow exit signal, parity exit signal, read parity exit, decision parity exit, joint bridge retirement, repair before cleanup, cutover cleanup evidence, cdc repair closure, replay backlog zero, drift bucket zero, auth shadow divergence zero, deprecated capability last seen, session revoke tail, deprovision access tail, old root last seen, legacy principal last seen, retirement soak approval, rollback closure evidence, decision log join key, audit hold evidence, donor silence proof, bridge decommission template

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)
> - [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)
> - [Dedicated Cell Drain and Retirement 설계](./dedicated-cell-drain-retirement-design.md)
> - [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)
> - [Trust-Bundle Rollback During Cell Cutover 설계](./trust-bundle-rollback-during-cell-cutover-design.md)
> - [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md)
> - [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md)
> - [Database: CDC Gap Repair, Reconciliation, and Rebuild Boundaries](../database/cdc-gap-repair-reconciliation-playbook.md)
> - [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)
> - [Security: SCIM Deprovisioning / Session / AuthZ Consistency](../security/scim-deprovisioning-session-authz-consistency.md)
> - [Security: AuthZ Decision Logging Design](../security/authz-decision-logging-design.md)
> - [Security: Audit Logging for Auth / AuthZ Traceability](../security/audit-logging-auth-authz-traceability.md)

## 이 문서 다음에 보면 좋은 설계

- cutover gate 전체 맥락부터 다시 잡으려면 [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)의 `joint cutover gate`와 함께 읽는다.
- bridge removal 직전의 shadow/parity 근거를 다시 모으려면 [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md), [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md), [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)를 같은 cohort 기준으로 이어서 본다.
- tenant/shared-cell exit 증거까지 내려가려면 [Dedicated Cell Drain and Retirement 설계](./dedicated-cell-drain-retirement-design.md)의 `retirement evidence packet`과 이어서 본다.
- claim/session translator cleanup까지 포함해 security tail을 더 자세히 보고 싶다면 [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)의 `cleanup / retirement evidence`와 연결해 읽는다.

## 핵심 개념

bridge retirement 승인에서 자주 생기는 오판은 둘 중 하나다.

- database 팀은 `replay backlog = 0`, `drift bucket = 0`을 보고 cleanup-safe라고 말한다.
- security 팀은 `deprecated capability last-seen`, `revoke tail`, `old root last-seen`이 아직 남았다고 말한다.

둘 다 맞을 수 있다.
문제는 bridge retirement가 어느 한 팀의 green으로 닫히는 사건이 아니라는 점이다.

bridge는 old/new 경계를 메우는 임시 구조이므로, retirement approval도 두 질문에 동시에 답해야 한다.

1. data plane repair가 정말 끝났는가
2. trust/session/policy tail이 더 이상 old bridge를 필요로 하지 않는가

즉 evidence packet의 목적은 지표를 모으는 것이 아니라, **database repair signals와 security tail signals를 하나의 승인 문장으로 합치는 것**이다.

## 깊이 들어가기

### 1. 승인 패킷은 "0 값 나열"이 아니라 두 개의 잔존 시계를 묶는 문서다

retirement 판단에서 실제로 닫아야 하는 시계는 둘이다.

| 시계 | 대표 질문 | 닫히지 않았을 때 |
|---|---|---|
| repair clock | replay/backfill/reconcile이 더 이상 old bridge를 필요로 하지 않는가 | cleanup 후 late repair, donor 재활성화, hidden data divergence |
| security tail clock | revoke/deprovision/trust overlap tail이 더 이상 old bridge를 필요로 하지 않는가 | cleanup 후 access tail, hidden allow path, rollback trust 불능 |

이 둘은 동시에 0이 되지 않을 수 있다.

- replay backlog는 먼저 0이 되지만 deprecated capability hit가 오래 남을 수 있다
- auth shadow divergence는 먼저 사라졌지만 donor reindex backlog가 늦게 닫힐 수 있다

그래서 packet은 `repair plane`, `security plane`, `overall decision`을 분리해 써야 한다.

### 2. 패킷 헤더에는 observation window와 join key를 먼저 적는다

좋은 packet은 수치보다 먼저 범위를 고정한다.

필수 헤더:

- bridge scope: tenant, region, route epoch, claim/version generation, trust bundle generation
- observation window: `started_at`, `ended_at`, `required_silence_window`
- rollback boundary: 아직 reversible인지, rollback-only handle이 남아 있는지
- join keys: `request_id`, `session_id`, `reconciliation_run_id`, `directory_event_id`, `decision_log_key`

이 헤더가 없으면 `deprecated capability last-seen` 하나와 `replay backlog 0` 하나가 같은 승인 윈도우를 가리키는지조차 설명하기 어렵다.

### 3. database repair signals는 "정합성 수리 필요 여부"를 대답해야 한다

권장 database plane 항목은 아래 정도가 최소 단위다.

| 필드 | 의미 | 승인에 쓰는 방식 |
|---|---|---|
| `backfill_mismatch_rows` | 아직 남은 canonical row mismatch | 0이 아니면 즉시 hold/reject |
| `cdc_gap_backlog` | CDC gap repair 대기량 | 0이 아니면 repair-first |
| `replay_backlog` | replay/reindex/reconcile 잔량 | 0이 아니면 old bridge cleanup 금지 |
| `drift_bucket_critical` | high-severity drift bucket 수 | 0이어야 함 |
| `final_delta_applied` | cutover 직전 final delta closure 여부 | `false`면 승인 불가 |
| `donor_probe_unexpected_hit` | donor/shared path unexpected hit 수 | 0이 아니면 아직 drain 미완료 |

핵심은 row count가 아니라, **cleanup 후에도 correction-only로 운영 가능한가**를 판단하는 수치만 남기는 것이다.

### 4. security tail signals는 "old trust를 지워도 tail incident를 설명할 수 있는가"를 대답해야 한다

권장 security plane 항목은 아래가 핵심이다.

| 필드 | 의미 | 승인에 쓰는 방식 |
|---|---|---|
| `auth_shadow_critical_divergence` | old/new decision critical mismatch | 0이 아니면 즉시 reject |
| `old_deny_new_allow` | 위험한 과허용 tail | 0이 아니면 hard stop |
| `deprecated_capability_last_seen_at` | legacy capability 마지막 관측 시각 | silence window 미충족이면 hold |
| `session_revoke_tail_p99_sec` | revoke tail의 장꼬리 | SLO 밖이면 hold |
| `last_access_after_deprovision_sec_p99` | deprovision 후 access tail | 0 또는 허용 범위 안이어야 함 |
| `old_root_last_seen_at` | old root/trust bundle 마지막 사용 시각 | verifier overlap tail이 남아 있으면 hold |
| `legacy_principal_last_seen_at` | legacy principal 마지막 관측 시각 | hidden caller 정리 전 cleanup 금지 |

이 축은 "보안 지표"를 모으는 용도가 아니다.
**bridge를 지운 뒤 incident tail을 다시 설명할 수 있는가**를 묻는 승인 축이다.

### 5. verification exit signals는 downstream 문서가 그대로 인용할 수 있게 packet 안에 남긴다

adapter retirement와 cleanup 문서는 raw dashboard를 다시 계산하는 문서가 아니라,
이 packet이 이미 닫아 둔 증거를 그대로 받아 쓰는 문서여야 한다.
그래서 packet에는 최소한 아래 두 개의 exit signal을 별도 블록으로 남기는 편이 안전하다.

| signal | 무엇을 닫았다는 뜻인가 | packet에 같이 남길 근거 |
|---|---|---|
| `shadow_exit_signal` | 같은 cohort에서 mirrored request mix, route/plugin wiring, auth shadow decision이 critical divergence 없이 수렴했다 | `traffic_shadow_ref`, `shadow_decision_ref`, 마지막 critical divergence 시각 |
| `parity_exit_signal` | 같은 cohort에서 read parity와 revoke/decision parity가 함께 닫혀 old bridge 없이도 같은 state/decision을 재현한다 | `dual_read_ref`, `revoke_probe_ref`, parity mismatch 요약 |

핵심은 `auth_shadow_critical_divergence = 0` 같은 raw metric을 downstream 문서가 다시 해석하지 않게 하는 것이다.
packet 안에 "shadow exit는 pass", "parity exit는 hold" 같은 명시적 신호가 있어야
[Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)와
[Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)가 같은 승인 근거를 재사용할 수 있다.

### 6. concrete packet template은 repair plane, security plane, verification exit, approval plane을 분리해서 쓴다

아래 템플릿은 bridge retirement 승인 회의나 runbook에 바로 붙여 넣을 수 있는 최소 형태다.

```yaml
bridge_retirement_packet:
  packet_id: brp-tenant42-2026-04-14T09:30:00Z
  scope:
    bridge_type: database-security-identity
    tenant: tenant-42
    region: ap-northeast-2
    route_epoch: 1842
    claim_schema_version: v3
    trust_bundle_generation: tb-2026-04-12-07
    change_window_id: chg-8821
  observation_window:
    started_at: 2026-04-13T00:00:00Z
    ended_at: 2026-04-14T09:30:00Z
    required_repair_silence_window_minutes: 180
    required_security_silence_window_minutes: 1440
  rollback_boundary:
    rollback_policy: rollback-closed
    cleanup_still_disabled: true
    point_of_no_return_ready: false
  join_keys:
    request_id_key: request_id
    session_key: session_id
    repair_run_key: reconciliation_run_id
    directory_event_key: directory_event_id
    decision_log_key: authz_decision_id
  database_repair:
    backfill_mismatch_rows: 0
    cdc_gap_backlog: 0
    replay_backlog: 0
    drift_bucket_critical: 0
    final_delta_applied: true
    donor_probe_unexpected_hit: 0
    evidence_refs:
      - dual-read-report-553
      - repair-run-221
      - donor-probe-17
    status: pass
  security_tail:
    auth_shadow_critical_divergence: 0
    old_deny_new_allow: 0
    deprecated_capability_last_seen_at: 2026-04-13T22:55:00Z
    session_revoke_tail_p99_sec: 12
    last_access_after_deprovision_sec_p99: 15
    old_root_last_seen_at: 2026-04-13T21:58:00Z
    legacy_principal_last_seen_at: 2026-04-13T22:10:00Z
    evidence_refs:
      - shadow-eval-window-84
      - scim-close-118
      - trust-bundle-probe-17
    status: hold
  verification_exit:
    cohort_id: tenant-42-route-1842-claim-v3
    shadow_exit_signal: pass
    traffic_shadow_ref: traffic-shadow-window-41
    shadow_decision_ref: shadow-eval-window-84
    shadow_critical_last_seen_at: 2026-04-13T18:10:00Z
    parity_exit_signal: hold
    dual_read_ref: dual-read-report-553
    revoke_probe_ref: revoke-probe-29
    read_parity_critical_mismatch: 0
    revoke_parity_tail_gt_slo: 1
    same_cohort_joined: true
    handoff_ready_for_bridge_removal: false
    status: hold
  approval:
    repair_plane: pass
    security_plane: hold
    verification_plane: hold
    overall_decision: hold
    hold_reason: parity exit signal not yet satisfied in same cohort
    next_recheck_at: 2026-04-14T22:55:00Z
    approvers_required:
      - data_owner
      - identity_owner
      - runtime_oncall
```

이 템플릿의 핵심은 `database_repair.status`와 `security_tail.status`를 따로 적고,
`verification_exit.status`로 downstream handoff를 별도 표시한 뒤,
맨 아래 `overall_decision`에서 셋을 다시 합친다는 점이다.

### 7. 승인 결정은 교집합 논리로 내려야 한다

가장 안전한 rule은 아래와 같다.

| repair plane | security plane | verification exit | overall decision | 의미 |
|---|---|---|---|---|
| fail | any | any | reject | data repair가 아직 열려 있음 |
| hold | pass | pass | hold | data plane silence window가 아직 부족 |
| pass | fail | any | reject | 보안 tail이 아직 위험하게 열려 있음 |
| pass | pass | fail | reject | shadow/parity exit 증거가 아직 bridge removal을 못 열어 줌 |
| pass | pass | hold | hold | verification evidence handoff가 아직 incomplete |
| pass | pass | pass | approve-candidate | 아직 point-of-no-return 전 최종 검증 필요 |

즉 `pass + pass = approve`가 아니라, 실제로는 아래 두 줄이 더 필요하다.

- evidence join이 가능해야 한다
- rollback closure와 cleanup enable이 분리돼 있어야 한다

그래서 최종 approval rule은 보통 이렇게 쓴다.

```pseudo
function decideRetirement(packet):
  if packet.database_repair.status != "pass":
    return "reject_repair_open"

  if packet.security_tail.status == "fail":
    return "reject_security_tail_open"

  if packet.security_tail.status == "hold":
    return "hold_extend_soak"

  if packet.verification_exit.status == "fail":
    return "reject_verification_exit_open"

  if packet.verification_exit.status == "hold":
    return "hold_exit_signal_open"

  if !packet.rollback_boundary.point_of_no_return_ready:
    return "hold_pre_cleanup"

  if !joinableEvidence(packet.join_keys):
    return "hold_missing_forensics"

  return "approve_retirement"
```

여기서 중요한 것은 `overall_decision`을 평균 점수나 단일 burn-rate로 만들지 않는 것이다.
bridge retirement는 보통 **최악 축 기준 승인**이 더 안전하다.

### 8. security tail이나 verification exit가 hold면 database가 완전히 green이어도 bridge는 남긴다

실전에서 가장 자주 보는 오판은 이 경우다.

- `replay_backlog = 0`
- `drift_bucket_critical = 0`
- `donor_probe_unexpected_hit = 0`
- 그런데 `deprecated_capability_last_seen_at`이 6시간 전이거나 `parity_exit_signal = hold`이고 required silence window는 24시간

이 경우 결론은 `approve`가 아니라 `hold`다.
이유는 bridge를 지운 뒤 legacy capability caller가 다시 튀면 원인이 data repair 문제가 아니라 security compatibility tail이라는 사실을 이미 알고 있기 때문이다.

반대 경우도 같다.

- auth shadow divergence는 0
- revoke tail도 SLO 안
- 하지만 `cdc_gap_backlog > 0`

이 경우는 security가 green이어도 `reject_repair_open`이다.
즉 packet은 둘 중 하나를 설득하는 문서가 아니라, **둘 중 더 느린 tail에 cleanup clock을 맞추는 문서**다.

### 9. packet에는 승인 문장 자체를 남겨야 한다

숫자와 run id만 남기고 결론 문장을 안 남기면 다음 wave에서 다시 해석 싸움이 시작된다.

권장 approval narrative:

- `repair plane`: 어떤 repair primitive가 모두 닫혔는가
- `security plane`: 어떤 tail이 아직 남았거나 모두 닫혔는가
- `verification exit`: shadow/parity exit signal이 어느 cohort에서 닫혔는가
- `why not now`: hold/reject면 어떤 residual horizon을 더 기다리는가
- `why safe now`: approve면 어떤 rollback/forensic handle을 확인했는가

예:

```text
repair plane is pass because replay, backfill mismatch, and donor probe residual are all zero across the full repair silence window.
security plane is pass because deprecated capability, revoke tail, and old-root signals all converged inside the required residual horizon.
verification exit remains hold because read/revoke parity is not yet closed for the same cohort that passed shadow evaluation.
overall decision is hold_exit_signal_open; bridge removal remains disabled until the parity exit signal closes.
```

이 narrative가 있어야 operator가 표를 다시 계산하지 않고도 왜 승인/보류가 났는지 이해할 수 있다.

### 10. packet 마지막에는 cleanup 직전 검증과 audit hold를 분리한다

approve 후보가 나와도 바로 destructive cleanup으로 넘어가면 위험하다.
마지막 두 블록을 분리해 두는 편이 안전하다.

| 블록 | 확인할 것 | 이유 |
|---|---|---|
| pre-cleanup verification | dark deny probe, donor route probe, legacy principal probe, trust acceptance matrix, `shadow_exit_signal=pass`, `parity_exit_signal=pass` 재확인 | point-of-no-return 직전 hidden caller와 열린 verification rung를 다시 잡기 위해 |
| audit / forensic hold | decision log join 가능 여부, audit retention, packet archive location | cleanup 뒤 incident 원인 재구성을 위해 |

즉 evidence packet의 끝은 `approve`가 아니라, **approve 이후 무엇을 아직 지우면 안 되는지까지 써 두는 것**이다.

## 실전 시나리오

### 시나리오 1: database repair는 닫혔지만 deprovision access tail이 남는다

문제:

- replay, drift, donor probe는 모두 0이다
- 하지만 `last_access_after_deprovision_sec_p99`가 여전히 SLO 밖이다

해결:

- `database_repair.status=pass`, `security_tail.status=fail`로 분리 기재한다
- overall decision은 `reject_security_tail_open`으로 둔다
- old bridge는 남기되 SCIM close, revoke fan-out, decision-log join을 먼저 수리한다

### 시나리오 2: trust bundle old root last-seen만 늦게 닫힌다

문제:

- session revoke와 capability tail은 거의 다 닫혔다
- 일부 admin/replay tool만 old root를 계속 사용한다

해결:

- `old_root_last_seen_at`, `legacy_principal_last_seen_at`를 packet에 caller provenance와 함께 남긴다
- `security_tail.status=hold`로 두고 cleanup enable을 막는다
- hidden admin path가 새 trust로 전환된 뒤에만 approve candidate로 승격한다

### 시나리오 3: evidence는 충분하지만 join key가 빠졌다

문제:

- repair와 security 숫자는 모두 green이다
- 그런데 `request_id -> authz_decision_id -> reconciliation_run_id`를 다시 잇는 키가 없다

해결:

- overall decision을 `hold_missing_forensics`로 둔다
- audit/decision evidence archive를 먼저 보강한다
- join key 없이 bridge를 지우면 나중에 tail incident가 stale data인지 stale policy인지 설명할 수 없기 때문이다

## 한 줄 정리

Bridge retirement evidence packet은 database repair closure와 security tail closure를 따로 기록한 뒤, 그 교집합만 overall approval로 승격하는 템플릿이며, `repair green`이나 `security green` 하나만으로 cleanup을 열지 않게 만드는 운영 문서다.

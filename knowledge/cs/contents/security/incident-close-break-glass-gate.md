# Incident-Close Break-Glass Gate

> 한 줄 요약: incident는 사용자 영향이 잦아들었다고 바로 닫는 것이 아니라, break-glass grant와 policy override가 control plane, evaluator, cleanup surface에서 모두 비활성화됐음을 증명한 뒤에만 close-eligible로 넘어가야 한다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **incident close gate, break-glass hard blocker, override cleanup evidence, close-eligibility control-plane check**를 설명하는 focused deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
> - [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md)
> - [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md)
> - [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)
> - [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)
> - [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md)
> - [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md)

retrieval-anchor-keywords: incident close break glass gate, incident close gate, break glass closure blocker, incident closure override gate, incident closed with active break glass, incident cannot close active override, close eligible emergency access, control plane closure check, break glass close criteria, active break glass grant count zero, active policy override count zero, fully blocked confirmed incident close, cleanup confirmed incident gate, orphan override blocker, incident review break glass, incident commander close gate, emergency override closure evidence, close blocked active grant, close blocked active override, security incident close control plane, delegated session tail cleanup, false closure

## 이 문서 다음에 보면 좋은 문서

- break-glass grant와 policy override 자체의 actor/scope/duration 제약은 [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)에서 먼저 고정하는 편이 좋다.
- leftover grant metric, `incident_closed_with_active_break_glass_count`, `grant_used_after_expiry_count` 같은 운영 신호는 [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md)에서 이어서 본다.
- revoke accepted 이후 `fully_blocked_confirmed`, `cleanup_confirmed`를 어떤 상태 의미로 써야 하는지는 [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)에서 따로 본다.
- preview, confirm, cleanup event를 `incident_id`, `access_group_id`, `revocation_request_id`로 잇는 correlation spine은 [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)에서 이어진다.
- stale cache, delegated refresh family, downstream token tail을 close blocker로 계산하는 기준은 [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md)에서 이어진다.
- timeline end event와 `cleanup_confirmed`를 같은 `closed`로 뭉개면 안 되는 이유는 [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md)에서 함께 보는 편이 좋다.

---

## 핵심 개념

incident close에서 흔한 착각은 "사용자 영향이 줄었으니 사건도 끝났다"는 판단이다.

break-glass가 끼어 있으면 이 판단은 불충분하다.

- operator에게 부여된 emergency grant가 아직 살아 있을 수 있다
- policy evaluator가 old/new override snapshot을 아직 들고 있을 수 있다
- revoke는 눌렀지만 downstream cache, delegated session, projector tail cleanup은 덜 끝났을 수 있다
- incident ticket은 닫혔는데 control plane에는 orphan override row가 남아 있을 수 있다

즉 incident close는 회고 문서 작성이 아니라, **emergency privilege가 실제로 더 이상 효력이 없음을 증명하는 control-plane gate**여야 한다.

---

## 깊이 들어가기

### 1. `resolved`와 `close-eligible`은 같은 상태가 아니다

권장 분리:

- `mitigated`: 사용자 영향이나 오류율은 안정화됨
- `recovery_in_progress`: revoke, rollback, cache convergence가 진행 중임
- `close_blocked`: 영향은 줄었지만 break-glass gate가 아직 닫히지 않음
- `close_eligible`: hard blocker가 모두 0이 됨

중요한 점:

- incident commander가 "상황은 진정됐다"고 느껴도 close gate는 별도 계산이어야 한다
- break-glass incident에서는 `mitigated`에서 `close_eligible`까지의 tail이 종종 더 길다
- close gate를 안 두면 "복구는 끝났는데 emergency 권한만 조용히 남는" 실패가 반복된다

### 2. close gate는 grant와 override 두 객체를 따로 본다

같은 break-glass라도 닫아야 하는 대상이 두 종류다.

- grant: 특정 operator, subject, tenant, action에 붙은 emergency lease
- override: policy evaluator, gateway, control plane rollout에 걸린 예외 규칙

둘을 같은 active count로만 뭉개면 안 된다.

- grant는 operator session, delegated token, approval TTL과 연결된다
- override는 policy snapshot version, rollout state, evaluator cache와 연결된다

즉 close gate는 "grant 0개"만 보는 것이 아니라 **grant registry와 override registry를 둘 다 0으로 만드는 일**이다.

### 3. authoritative source는 티켓 코멘트가 아니라 control plane이다

incident close를 막아야 하는 authoritative surface 예:

| surface | 확인 질문 | close blocked 조건 |
|---|---|---|
| break-glass grant registry | incident에 연결된 emergency lease가 남아 있는가 | `requested`, `approved`, `active`, `renewal_pending` grant 존재 |
| policy override registry | kill switch / allow override / scoped bypass가 아직 걸려 있는가 | `effective_now=true`인 override 존재 |
| revoke status surface | revoke request가 실제 차단까지 갔는가 | `status != fully_blocked_confirmed` |
| cleanup surface | cache, delegated session, projector tail이 닫혔는가 | `cleanup_confirmed_at` 누락 |
| timeline / audit projection | end event와 cleanup evidence가 모두 이어지는가 | `coverage=partial`, missing end event, orphan evidence |
| observability | 만료 후 사용이 있었는가 | `grant_used_after_expiry_count > 0` |

반대로 close gate의 근거로 부족한 것:

- incident channel에서 누가 "이제 닫아도 될 듯"이라고 남긴 댓글
- UI banner가 사라졌다는 정성적 확인
- ticket 상태만 `Resolved`로 바뀐 것

### 4. hard blocker는 "active 여부" 하나보다 조금 더 넓게 잡아야 한다

실무적으로 close를 막아야 하는 최소 조건은 아래처럼 보는 편이 안전하다.

| blocker class | 예시 조건 | 왜 block하는가 |
|---|---|---|
| live grant | `active_break_glass_grant_count > 0` | operator가 지금도 emergency 권한을 쓸 수 있다 |
| live override | `active_policy_override_count > 0` | evaluator/gateway가 지금도 완화 규칙을 적용한다 |
| revocation not converged | `requested`, `in_progress` 상태의 revoke request 존재 | registry는 닫혔어도 data plane은 아직 허용할 수 있다 |
| cleanup tail open | `cleanup_confirmed_at` 없음, `expired_but_still_active_count > 0` | stale cache, delegated token, projector tail이 남아 있다 |
| orphan privilege | `incident_id`, `approval_id`, `access_group_id` 없이 남은 override row | 남아 있는 권한이 이번 incident 소유인지조차 증명할 수 없다 |
| wide-scope exception | tenant-wide/global override가 terminal evidence 없이 남음 | blast radius가 커서 manual close를 허용하면 위험하다 |

핵심은 close gate가 "현재 active count 0" 한 줄로 끝나면 안 된다는 점이다.  
**revoked-but-not-converged, expired-but-still-active, orphan override**도 close blocker로 봐야 한다.

### 5. `fully_blocked_confirmed`와 `cleanup_confirmed`는 둘 다 필요하다

close gate에서 자주 생기는 오해:

- revoke가 accepted됐으니 close 가능하다
- timeline이 `revoked`로 보이니 cleanup도 끝난 것이다

하지만 의미는 다르다.

- `fully_blocked_confirmed`: 계산된 범위 전체에서 더 이상 효력이 없다는 enforcement evidence
- `cleanup_confirmed`: cache sweeper, delegated session, customer/security projector tail까지 닫혔다는 후속 evidence

incident close gate는 보통 이렇게 해석하는 편이 좋다.

1. live privilege는 `fully_blocked_confirmed` 전까지 hard block
2. 사용된 grant 또는 wide-scope override는 `cleanup_confirmed` 전까지도 hard block
3. low-scope, never-used grant는 정책에 따라 `fully_blocked_confirmed`까지만 hard block으로 둘 수 있다

즉 close gate는 revoke button click이 아니라 **terminal enforcement + cleanup evidence**를 본다.

### 6. operator mode와 evaluator snapshot도 함께 닫혀야 한다

break-glass incident에서는 권한 row만 지우면 끝나지 않는다.

추가 확인이 필요한 면:

- operator session이 아직 `BREAK_GLASS` mode인가
- tenant-wide/global evaluator snapshot이 old override version을 아직 캐시에 들고 있는가
- gateway나 sidecar가 replacement snapshot으로 수렴했는가
- step-up TTL, approval TTL, grant TTL 중 가장 짧은 효력 시간이 실제로 적용됐는가

즉 control plane close gate는 registry row만 보지 않고 **operator surface와 evaluator surface가 같은 terminal state를 보고 있는가**도 같이 확인해야 한다.

### 7. close gate 결과는 기계가 읽을 수 있어야 한다

incident commander가 dashboard를 보며 수동 판단해도 되지만, close 조건은 machine-readable contract로 남기는 편이 훨씬 안전하다.

예:

```json
{
  "incident_id": "INC-421",
  "close_eligible": false,
  "computed_at": "2026-04-14T12:11:00Z",
  "hard_blockers": [
    {
      "type": "active_policy_override",
      "override_id": "ovr_77",
      "scope_class": "tenant_wide",
      "reason": "effective_now"
    },
    {
      "type": "cleanup_pending",
      "revocation_request_id": "rr_981",
      "reason": "cleanup_confirmed_missing"
    }
  ],
  "summary": {
    "active_break_glass_grant_count": 0,
    "active_policy_override_count": 1,
    "fully_blocked_confirmed_pending_count": 0,
    "cleanup_confirmed_pending_count": 1,
    "grant_used_after_expiry_count": 0
  }
}
```

이런 contract가 있으면:

- close 버튼이 hard-block을 자동으로 걸 수 있고
- post-incident review가 same payload를 증거로 재사용할 수 있고
- "왜 안 닫히는가"를 사람과 시스템이 같은 언어로 설명할 수 있다

### 8. incident review는 close gate 통과 뒤에 시작된다

review에서 남겨야 하는 질문은 따로 있다.

- 왜 break-glass가 필요했는가
- scope와 TTL은 과도하지 않았는가
- renewal이 반복됐는가
- 다음 incident에서는 어떤 control plane을 더 잘 준비해야 하는가

하지만 이 질문들은 close gate를 대체하지 못한다.

좋은 순서:

1. grant / override active count를 0으로 만든다
2. `fully_blocked_confirmed`, `cleanup_confirmed`를 수집한다
3. orphan override와 missing timeline evidence를 없앤다
4. 그 뒤 incident를 close하고 review를 연다

즉 review는 학습 단계이고, close gate는 **권한이 정말 닫혔는지 검증하는 실행 단계**다.

---

## 실전 시나리오

### 시나리오 1: break-glass grant는 만료됐는데 한 리전 evaluator가 아직 허용한다

문제:

- registry row는 `expired`지만 regional cache가 stale하다

대응:

- `active_break_glass_grant_count`만 보지 말고 `fully_blocked_confirmed`를 필수로 본다
- `expired_but_still_active_count`가 0이 될 때까지 incident close를 막는다
- 마지막 region convergence 뒤에만 `close_eligible=true`로 바꾼다

### 시나리오 2: kill switch는 껐는데 tenant-wide allow override row가 orphan으로 남는다

문제:

- rollback은 끝났지만 control plane registry에는 incident-linked override가 남아 있다

대응:

- `incident_id`, `approval_id`, `override_id`가 있는 row를 close gate에서 직접 조회한다
- orphan override를 cleanup하지 못하면 close를 거부한다
- manual ticket note로 예외 승인하지 말고 explicit revoke/retire event를 남긴다

### 시나리오 3: timeline은 `revoked`로 보이지만 cleanup sweeper가 delegated token을 아직 정리 중이다

문제:

- lifecycle projection과 tail cleanup evidence를 같은 `closed`로 오해했다

대응:

- timeline `to_status=revoked`와 `cleanup_confirmed_at`를 분리해 본다
- `cleanup_confirmed_pending_count > 0`이면 close gate는 계속 막는다
- end event는 유지하되, incident status는 `close_blocked`로 둔다

### 시나리오 4: operator session이 아직 break-glass mode인데 티켓만 닫으려 한다

문제:

- grant registry는 비워졌지만 operator mode exit이 누락됐다

대응:

- active operator emergency mode count를 hard blocker에 포함한다
- mode banner 종료, approval TTL 만료, operator session step-down을 함께 확인한다
- operator surface와 backend registry가 같은 terminal state를 볼 때만 close를 허용한다

---

## 코드로 보기

### 1. close gate 계산 예시

```java
public IncidentCloseGateResult evaluate(Incident incident) {
    var grants = grantRegistry.findByIncidentId(incident.id());
    var overrides = overrideRegistry.findByIncidentId(incident.id());
    var blockers = new ArrayList<CloseBlocker>();

    blockers.addAll(findLiveGrantBlockers(grants));
    blockers.addAll(findLiveOverrideBlockers(overrides));
    blockers.addAll(findPropagationBlockers(incident.id()));
    blockers.addAll(findCleanupBlockers(incident.id()));
    blockers.addAll(findOrphanPrivilegeBlockers(incident.id()));

    return new IncidentCloseGateResult(
            incident.id(),
            blockers.isEmpty(),
            blockers,
            clock.instant()
    );
}
```

### 2. close blocker type 예시

```java
public enum CloseBlockerType {
    ACTIVE_BREAK_GLASS_GRANT,
    ACTIVE_POLICY_OVERRIDE,
    REVOCATION_NOT_CONVERGED,
    CLEANUP_PENDING,
    ORPHAN_OVERRIDE,
    ACTIVE_OPERATOR_BREAK_GLASS_MODE
}
```

### 3. incident close 전 최소 질문

```text
1. incident-linked break-glass grant와 policy override가 모두 0인가
2. revoke request가 모두 fully_blocked_confirmed까지 갔는가
3. used grant와 wide-scope override는 cleanup_confirmed까지 닫혔는가
4. orphan override, missing approval ref, partial coverage가 남아 있지 않은가
5. operator surface와 evaluator surface가 같은 terminal state를 보고 있는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 사람 판단 위주 close | 빠르다 | leftover privilege를 놓치기 쉽다 | 피하는 편이 좋다 |
| active count만 보는 gate | 구현이 단순하다 | converged cleanup과 orphan override를 놓친다 | 작은 단일 서비스에서만 제한적으로 |
| control-plane multi-surface gate | 실제 효력 종료를 더 정확히 보장한다 | schema, status, metric join이 필요하다 | break-glass와 policy override를 함께 쓰는 운영 환경 |
| wide-scope override에 manual second close | blast radius가 큰 예외를 더 보수적으로 닫는다 | close가 늦어질 수 있다 | tenant-wide/global override incident |

판단 기준은 이렇다.

- incident 완화와 privilege 종료를 같은 상태로 뭉개고 있지 않은가
- registry, evaluator, cleanup surface가 모두 terminal evidence를 내는가
- orphan override나 partial coverage를 "나중에 보자"로 넘기고 있지 않은가
- close gate 출력이 기계가 읽을 수 있는 contract인가

---

## 꼬리질문

> Q: 왜 사용자 영향이 사라졌는데도 incident를 바로 닫으면 안 되나요?
> 의도: mitigated와 close-eligible을 구분하는지 확인
> 핵심: break-glass grant, policy override, cleanup tail은 사용자 영향이 줄어도 control plane에 남아 있을 수 있기 때문이다.

> Q: `fully_blocked_confirmed`와 `cleanup_confirmed`는 왜 둘 다 필요한가요?
> 의도: enforcement evidence와 tail cleanup evidence를 구분하는지 확인
> 핵심: 전자는 더 이상 효력이 없다는 뜻이고, 후자는 cache/session/projector tail까지 닫혔다는 뜻이다.

> Q: orphan override는 왜 hard blocker인가요?
> 의도: attribution이 없는 예외 권한의 위험을 이해하는지 확인
> 핵심: incident 소유와 종료 근거를 증명할 수 없어서, 실제로 남아 있는 권한을 안전하게 닫았는지 판단할 수 없기 때문이다.

> Q: break-glass close gate에서 가장 흔한 오해는 무엇인가요?
> 의도: timeline `revoked`와 실제 cleanup 완료를 혼동하는지 확인
> 핵심: revoke button click이나 timeline 종료 badge를 곧바로 privilege cleanup 완료로 해석하는 것이다.

incident-close break-glass gate의 핵심은 "incident를 닫을 수 있는가"를 사람이 감으로 정하는 것이 아니라, grant registry, override registry, revoke status, cleanup evidence를 함께 묶어 **emergency privilege가 더 이상 효력이 없다는 증거**로 계산하는 데 있다.

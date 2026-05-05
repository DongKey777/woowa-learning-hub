# Delegated Session Tail Cleanup

> 한 줄 요약: AOBO와 break-glass cleanup은 grant row를 닫는 것으로 끝나지 않고, delegated session graph의 downstream session, refresh family, exchanged token, stale cache가 더 이상 효력을 갖지 않음을 확인한 뒤에만 `cleanup_confirmed`로 닫아야 false closure를 피할 수 있다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **AOBO / break-glass cleanup target graph, downstream session invalidation, refresh-family retirement, stale-cache convergence, false-closure prevention**을 설명하는 focused deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md)
> - [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
> - [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md)
> - [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)
> - [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md)
> - [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)
> - [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md)
> - [Device / Session Graph Revocation Design](./device-session-graph-revocation-design.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md)
> - [Security README: Service / Delegation Boundaries](./README.md#service-delegation-boundaries-deep-dive-catalog)

retrieval-anchor-keywords: delegated session tail cleanup, session tail cleanup, session-tail cleanup, aobo cleanup tail, break glass cleanup tail, delegated access cleanup, false closure, false done revoke, cleanup confirmed criteria, downstream session invalidation, delegated refresh family cleanup, support access tail cleanup, operator session tail, downstream audience token cleanup, stale cache convergence, cache invalidation after revoke, break glass stale cache, aobo session family revoke, cleanup evidence matrix, revoke tail closure, cleanup without false closure

## 이 문서 다음에 보면 좋은 문서

- delegated access의 actor/scope/TTL 제약은 [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md), [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)에서 먼저 고정하는 편이 좋다.
- lifecycle close event와 tail cleanup event를 같은 `closed`로 뭉개면 안 되는 이유는 [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md)에서 바로 이어진다.
- preview, confirm, `revocation_request_id`, `cleanup_confirmed_at` spine은 [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)에서 연결한다.
- leftover grant alert, sweeper lag, post-incident review metric은 [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md)와 같이 봐야 한다.
- refresh lineage 전체를 어떤 단위로 끊을지는 [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md), [Device / Session Graph Revocation Design](./device-session-graph-revocation-design.md)로 이어진다.
- stale allow cache, evaluator snapshot convergence는 [Authorization Caching / Staleness](./authorization-caching-staleness.md), [Session Revocation at Scale](./session-revocation-at-scale.md)에서 더 넓게 볼 수 있다.

---

## 핵심 개념

delegated access cleanup에서 흔한 실패는 grant registry나 customer timeline row만 닫고 "이제 끝났다"고 선언하는 것이다.

하지만 AOBO와 break-glass는 둘 다 head보다 tail이 더 길다.

- grant row는 `revoked` 또는 `expired`가 됐다
- timeline은 `support_access_ended`로 닫혔다
- status endpoint는 `fully_blocked_confirmed`까지 갔다

그래도 아래 tail이 남을 수 있다.

- delegated browser/BFF session
- subject 또는 operator 쪽 refresh family
- token exchange로 파생된 downstream audience token
- regional authz cache, evaluator snapshot, gateway allow cache
- projector / notification tail과 cleanup evidence 누락

즉 cleanup의 핵심은 "revoke를 눌렀는가"가 아니라, **계산된 delegated session tail 전체가 더 이상 통과되지 않음을 positive evidence로 닫는 것**이다.

---

## 깊이 들어가기

### 1. cleanup 대상은 grant row가 아니라 tail graph다

AOBO와 break-glass cleanup은 공통으로 여러 종류의 tail object를 함께 본다.

| target class | AOBO에서 흔한 대상 | break-glass에서 흔한 대상 | terminal evidence |
|---|---|---|---|
| root grant / lifecycle | `access_group_id`, `grant_id`, operator delegated mode | `grant_id`, `override_id`, `incident_id` | revoke/expiry가 durable하게 기록됨 |
| interactive session | support console의 subject-bound browser/BFF session | operator의 emergency admin session, privileged tool session | session store delete, session version mismatch, local deny 확인 |
| refresh lineage | subject 작업 중 발급된 delegated refresh family, BFF refresh chain | operator emergency session에 매달린 refresh family | family exchange deny, child issuance 중단, lineage coverage=full |
| downstream token tail | exchanged token, service-to-service delegated token, cached access token | override 하에서 발급된 admin token, exchanged audience token | audience별 `blocked_confirmed` 또는 TTL tail 종료 확인 |
| cache / policy plane | BFF token cache, subject policy cache, per-tenant authz cache | evaluator snapshot cache, gateway allow override cache, regional registry cache | version convergence, stale region 0, revoke 이후 allow 없음 |
| projection / evidence tail | `support_access_cleanup_confirmed`, missing end repair | cleanup audit, incident close blocker 해제 evidence | join key 보존, `cleanup_confirmed_at` 기록, coverage=full |

핵심은 row delete가 아니라, **tail class마다 어떤 evidence를 모아야 terminal로 볼지 미리 고정하는 것**이다.

### 2. AOBO와 break-glass는 같은 상태 vocabulary를 쓰되 invalidate 축이 다르다

둘 다 delegated access지만 cleanup 질문은 다르다.

| 축 | AOBO | break-glass | 공통 규칙 |
|---|---|---|---|
| 직접 차단해야 하는 root | subject에 대한 delegated action lease | operator에게 부여된 emergency privilege / policy override | `revocation_request_id` 또는 동등한 revoke spine이 있어야 한다 |
| 우선 끊어야 하는 세션 | subject-bound browser/BFF session, delegated write flow | operator emergency session, privileged admin UI session | high-risk route는 tail보다 먼저 direct deny로 막는다 |
| 오래 남기 쉬운 tail | delegated refresh family, exchanged token, customer timeline repair | regional evaluator cache, gateway allow cache, override snapshot | `fully_blocked_confirmed`와 `cleanup_confirmed`를 분리한다 |
| 흔한 false closure | end event가 떴으니 subject 쪽 세션도 다 닫혔다고 오해 | registry revoke가 됐으니 모든 리전의 override도 내려갔다고 오해 | 사람용 lifecycle close와 enforcement evidence를 같은 의미로 쓰지 않는다 |
| incident close blocker | delegated refresh family active, missing cleanup evidence | active override cache, stale region, orphan override | close gate는 tail evidence가 모일 때까지 열린다 |

즉 vocabulary는 공유하되, AOBO는 subject/session 축, break-glass는 operator/override/cache 축을 더 강하게 확인해야 한다.

### 3. `ended`, `fully_blocked_confirmed`, `cleanup_confirmed`를 섞으면 false closure가 생긴다

| surface | 말해 주는 것 | 절대 의미하지 않는 것 |
|---|---|---|
| `support_access_ended` / `to_status=revoked` | delegated lifecycle이 사람에게는 종료로 보인다 | 모든 session family와 cache tail이 정리됐다는 뜻 |
| `fully_blocked_confirmed` | 계산된 revoke scope 전체가 더 이상 받아들여지지 않음이 확인됐다 | projector repair, cache sweeper, timeline cleanup까지 끝났다는 뜻 |
| `cleanup_confirmed` | tail cleanup evidence까지 모였다 | end event를 생략해도 된다는 뜻 |

권장 규칙:

- end event는 lifecycle close를 위해 즉시 기록한다
- `fully_blocked_confirmed`는 enforcement guarantee가 모였을 때만 기록한다
- `cleanup_confirmed`는 refresh family, downstream token, stale cache, projector tail이 닫힌 뒤에만 기록한다

즉 `revoked`는 사람용 종료고, `cleanup_confirmed`는 **숨은 tail까지 닫혔다는 운영 증거**다.

### 4. cleanup plan은 preview summary보다 한 단계 더 구체적이어야 한다

preview payload가 `refresh family 2개 영향` 정도만 보여 줬다면, accepted revoke 뒤에는 실제 cleanup target matrix가 필요하다.

최소한 아래는 계산하는 편이 안전하다.

- 어떤 browser/BFF session을 닫을 것인가
- 어떤 refresh family를 revoke할 것인가
- 어떤 downstream audience token을 즉시 deny하고, 어떤 것은 TTL tail을 기다릴 것인가
- 어떤 cache class를 invalidate하고 어떤 region의 convergence를 기다릴 것인가
- 어떤 evidence가 모이면 `fully_blocked_confirmed`, 어떤 evidence가 모이면 `cleanup_confirmed`인가

좋은 accepted context 예:

```json
{
  "revocation_request_id": "rr_01JVC9D7M4Q2P4X9",
  "access_group_id": "ag_01JVC9CGY7K3M9DT",
  "cleanup_targets": [
    {
      "target_class": "browser_bff_session",
      "scope_key": "sess_77",
      "terminal_rule": "deleted_or_version_mismatch"
    },
    {
      "target_class": "refresh_family",
      "scope_key": "fam_22",
      "terminal_rule": "exchange_denied"
    },
    {
      "target_class": "downstream_audience:billing-api",
      "scope_key": "aud_billing",
      "terminal_rule": "ttl_tail_or_deny_confirmed"
    },
    {
      "target_class": "authz_cache",
      "scope_key": "tenant_9:region-apne2",
      "terminal_rule": "snapshot_version_converged"
    }
  ]
}
```

핵심은 cleanup이 "나중에 sweeper가 알아서"가 아니라, **accepted 시점부터 어떤 tail을 닫아야 하는지 구조화돼 있어야 한다**는 점이다.

### 5. stale cache invalidation은 `invalidate` 호출이 아니라 convergence evidence로 닫는다

cache cleanup에서 가장 흔한 실수는 fan-out publish만 성공하면 끝났다고 보는 것이다.

하지만 false closure를 막으려면 아래가 더 필요하다.

- cache key 또는 snapshot version이 실제로 올라갔는가
- covered region / pod / gateway가 새 version을 봤는가
- revoke 이후 old cache로 allow된 요청이 더 있었는가
- self-contained token tail은 TTL 종료 또는 deny observation으로 닫혔는가

권장 evidence 축:

- positive evidence: deny log, version ack, evaluator snapshot convergence
- negative evidence: 선언된 tail window 이후 allow log 부재
- coverage evidence: `coverage=full`, `pending_region_count=0`, `pending_audience_count=0`

반대로 아래만으로는 부족하다.

- pub/sub publish 성공
- cache delete API 200 응답
- dashboard에서 active grant count가 0으로 보임

즉 stale cache cleanup은 invalidate command가 아니라 **convergence verification**이다.

### 6. positive evidence와 negative evidence를 같이 써야 한다

cleanup confirmed를 너무 보수적으로 잡으면 영원히 안 닫히고, 너무 느슨하게 잡으면 false closure가 된다.

실무적으로는 두 종류의 evidence를 같이 쓰는 편이 좋다.

- positive evidence
  - refresh family exchange가 실제로 deny됨
  - high-risk route에서 session version mismatch가 확인됨
  - evaluator cache가 새 snapshot version으로 수렴함
- negative evidence
  - 선언된 TTL tail window 이후 allow log가 없음
  - projector repair backlog가 0이고 missing end pair가 없음

중요한 점은 negative evidence만으로 닫지 않는 것이다.  
특히 break-glass처럼 wide-scope override가 있었던 경우에는 positive deny 또는 convergence ack가 반드시 들어가는 편이 안전하다.

### 7. cleanup 이후 accept가 다시 보이면 조용히 덮지 말고 reopen해야 한다

tail cleanup은 잘못 닫히기 쉬우므로 reopen rule을 미리 정의해야 한다.

권장 규칙:

- `cleanup_confirmed_at` 이후 accept evidence가 새로 발견되면 contract violation으로 기록한다
- 기존 `cleanup_confirmed_at`을 조용히 수정하지 않는다
- 새 repair trace 또는 새 revoke request로 다시 연다
- incident close gate가 이미 통과했다면 close decision도 함께 재검토한다

즉 false closure의 핵심 방어선은 처음부터 완벽하게 닫는 것만이 아니라, **잘못 닫힌 사실을 다시 열 수 있는 운영 규칙**을 두는 것이다.

---

## 실전 시나리오

### 시나리오 1: support AOBO는 종료됐는데 모바일 앱 refresh가 계속 된다

문제:

- `support_access_ended`는 기록됐지만 delegated refresh family가 아직 token endpoint에서 재발급된다

대응:

- subject 쪽 family revoke와 session version bump를 같이 건다
- `fully_blocked_confirmed`는 high-risk write deny가 모였을 때 먼저 기록할 수 있다
- `cleanup_confirmed`는 family exchange deny까지 확인한 뒤에만 기록한다

### 시나리오 2: break-glass revoke는 accepted됐는데 한 리전 gateway가 old allow snapshot을 본다

문제:

- control-plane registry revoke는 됐지만 regional authz cache가 stale하다

대응:

- cache version convergence를 cleanup target에 포함한다
- `pending_region_count > 0`이면 `cleanup_confirmed`를 내리지 않는다
- revoke 이후 allow log가 보이면 close gate를 계속 막는다

### 시나리오 3: timeline은 종료됐는데 downstream exchanged token이 잠깐 더 통과한다

문제:

- lifecycle close와 downstream audience tail을 같은 의미로 취급했다

대응:

- audience별 `blocked_confirmed` 또는 TTL tail 종료 evidence를 따로 둔다
- customer-facing timeline은 종료로 닫되, 내부 cleanup 상태는 `pending`으로 유지한다
- tail window 이후 accept가 남으면 reopen trace를 남긴다

---

## 코드로 보기

### 1. cleanup terminal guard 예시

```java
boolean cleanupConfirmed(DelegatedCleanupState state) {
    return state.lifecycleEnded()
            && state.fullyBlockedConfirmed()
            && state.refreshFamilies().allMatch(TargetState::terminal)
            && state.downstreamAudiences().allMatch(TargetState::terminal)
            && state.cachePlanes().allMatch(TargetState::terminal)
            && !state.observedAcceptAfterTerminal();
}
```

### 2. cleanup target state 예시

```java
public record TargetState(
        String targetClass,
        String scopeKey,
        String state,
        Instant confirmedAt,
        String evidenceSource
) {
    boolean terminal() {
        return "blocked_confirmed".equals(state)
                || "ttl_tail_expired".equals(state)
                || "snapshot_converged".equals(state);
    }
}
```

### 3. 운영 체크리스트

```text
1. revoke accepted 시점에 cleanup target matrix를 고정하는가
2. AOBO는 subject/session/family 축, break-glass는 operator/override/cache 축을 따로 보는가
3. fully_blocked_confirmed와 cleanup_confirmed를 같은 뜻으로 쓰지 않는가
4. cache invalidation을 publish 성공이 아니라 convergence evidence로 닫는가
5. cleanup 후 accept 발견 시 reopen 규칙이 있는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| grant revoke만 terminal로 본다 | 구현이 가장 단순하다 | false closure가 거의 필연적이다 | 권장하지 않음 |
| `fully_blocked_confirmed`까지만 terminal로 본다 | enforcement guarantee는 명확하다 | stale cache, projector tail, refresh family cleanup을 놓치기 쉽다 | low-scope, never-used revoke에서 제한적으로 가능 |
| cleanup target matrix + reopen rule을 둔다 | AOBO / break-glass tail을 가장 정확히 닫는다 | 상태와 evidence 설계가 더 필요하다 | support tooling, break-glass, regulated environment |

판단 기준은 이렇다.

- subject-bound session family가 실제로 생기는가
- regional cache / override snapshot tail이 긴가
- incident close를 machine-readable gate로 막아야 하는가
- post-incident review에서 false closure를 감사 추적으로 설명해야 하는가

---

## 꼬리질문

> Q: `support_access_ended`가 떴으면 cleanup도 끝난 것 아닌가요?
> 의도: lifecycle close와 tail cleanup을 구분하는지 확인
> 핵심: 아니다. end event는 사람용 종료이고, refresh family와 stale cache tail은 별도 evidence가 필요하다.

> Q: `fully_blocked_confirmed`와 `cleanup_confirmed`는 왜 둘 다 필요한가요?
> 의도: enforcement guarantee와 후속 정리를 분리하는지 확인
> 핵심: 전자는 access 차단 증거이고, 후자는 session family, downstream token, cache tail까지 닫혔다는 증거다.

> Q: cache invalidation은 publish 성공이면 충분하지 않나요?
> 의도: invalidate command와 convergence verification을 구분하는지 확인
> 핵심: 아니다. 모든 covered region이 새 snapshot을 보고 old allow가 사라졌다는 evidence가 있어야 한다.

> Q: cleanup 뒤에 accept가 다시 보이면 어떻게 해야 하나요?
> 의도: false closure 이후 운영 규칙을 이해하는지 확인
> 핵심: 조용히 덮지 말고 contract violation으로 기록하고 reopen해야 한다.

## 한 줄 정리

delegated session tail cleanup의 핵심은 AOBO와 break-glass revoke를 grant 종료로 착각하지 않고, session family, downstream token, stale cache가 실제로 더 이상 통과되지 않음을 확인한 뒤에만 `cleanup_confirmed`로 닫는 것이다.

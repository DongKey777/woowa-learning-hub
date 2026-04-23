# Revocation Propagation Status Contract

> 한 줄 요약: operator-triggered revocation은 confirm이 수락됐다는 사실과 실제 차단이 확인됐다는 사실을 분리해야 하며, backend status payload는 `requested`, `in_progress`, `fully_blocked_confirmed`를 서로 다른 보장으로 내려야 한다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **operator-triggered revocation status endpoint, propagation evidence, blocked-confirmation semantics**를 설명하는 focused deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md)
> - [Revocation Preview Drift Response Contract](./revocation-preview-drift-response-contract.md)
> - [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
> - [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
> - [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md)
> - [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)

retrieval-anchor-keywords: revocation propagation status contract, revocation status payload, revoke status api, operator revocation status, revocation request status endpoint, requested in progress fully blocked confirmed, execution requested vs requested, revoke polling contract, propagation state machine, fully blocked confirmed meaning, block confirmation evidence, last accepted after revoke, revocation progress payload, revocation request id, preview id graph snapshot id join, cleanup confirmed vs fully blocked confirmed, operator revoke progress, aobo revoke timeline join, break glass revoke status evidence, propagation lag status copy

## 이 문서 다음에 보면 좋은 문서

- confirm 이전 preview binding과 join key는 [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md)에서 먼저 고정한다.
- confirm 시점의 `accepted`/`stale`/`rejected` 응답은 [Revocation Preview Drift Response Contract](./revocation-preview-drift-response-contract.md)에서 다룬다.
- propagation tail 자체를 디버깅하는 기준은 [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)으로 이어진다.
- inventory와 operator UI copy에서 `requested`, `in_progress`, `fully_blocked_confirmed`를 어떻게 보여 줄지는 [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)과 같이 보는 편이 좋다.
- `cleanup_confirmed` 같은 후속 cleanup 상태와 구분하는 lifecycle 모델은 [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md)에서 이어진다.
- AOBO / break-glass revoke에서 `revocation_request_id`를 preview, confirm, timeline evidence까지 어떻게 잇는지는 [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)로 이어진다.

---

## 핵심 개념

operator가 revoke confirm을 눌렀을 때 backend가 실제로 말해야 하는 것은 세 가지다.

- 요청이 수락되어 `revocation_request_id`가 생성됐는가
- 고위험 경로나 일부 token family 차단이 실제로 시작됐는가
- 계산된 범위 전체에서 더 이상 access가 받아들여지지 않음이 확인됐는가

이 셋을 모두 `done`으로 뭉개면 바로 문제가 생긴다.

- `requested`를 완료로 번역해 operator가 "이미 모두 끊겼다"고 오해한다
- `in_progress`를 숨겨 high-risk write는 막혔지만 일반 read tail이 남은 상황을 설명하지 못한다
- queue drain이나 pub/sub ack만 보고 `fully_blocked_confirmed`를 찍어 실제 acceptance evidence가 없는 허위 완료 상태를 만든다

즉 revocation status contract의 본질은 job progress bar가 아니라, **현재 revoke request가 어떤 security guarantee까지 도달했는가를 구조화해서 표현하는 것**이다.

---

## 깊이 들어가기

### 1. 상태는 worker queue 상태가 아니라 security guarantee를 말해야 한다

권장 상태 집합은 아래 셋이다.

| 상태 | backend가 보장하는 것 | 절대 의미하지 않는 것 |
|---|---|---|
| `requested` | confirm이 수락되어 revoke request가 durable하게 생성됐다 | 어떤 route나 token이 이미 막혔다는 뜻 |
| `in_progress` | 적어도 하나 이상의 차단/전파 단계가 시작됐고, 일부 또는 high-risk 경로는 막혔을 수 있다 | 계산된 범위 전체가 이미 차단됐다는 뜻 |
| `fully_blocked_confirmed` | 계산된 범위 전체에 대해 더 이상 access가 받아들여지지 않음이 positive evidence로 확인됐다 | cleanup sweeper, projector repair, 후속 forensic cleanup까지 모두 끝났다는 뜻 |

핵심은 `completed` 같은 generic state를 피하는 것이다.  
revocation은 "비동기 작업이 끝났는가"보다 "차단 보장이 어느 수준까지 올라왔는가"가 더 중요하다.

### 2. 최소 payload envelope는 request, propagation, evidence를 함께 가져야 한다

상태 endpoint는 최소한 아래 영역을 항상 내려주는 편이 안전하다.

| 영역 | 필드 | 왜 필요한가 |
|---|---|---|
| 식별자 | `schema_version`, `revocation_request_id`, `status`, `status_reason`, `status_changed_at` | 어떤 계약 버전의 어떤 request가 지금 어느 상태인지 명확히 하기 위해 필요하다 |
| accept context | `accepted_at`, `preview_id`, `graph_snapshot_id`, `operator_session_id` | "무엇을 보고 누가 언제 confirm했는가"를 preview/confirm과 연결하기 위해 필요하다 |
| actor/subject | `operator_id`, `operator_mode`, `approval_id` 또는 `ticket_id`, `tenant_id`, `subject_user_id` | AOBO / break-glass / multi-tenant revoke를 잘못 섞지 않기 위해 필요하다 |
| 요청/범위 | `request`, `summary` | requested scope와 effective impact를 status page에서도 다시 설명하려면 필요하다 |
| 전파 상태 | `confirmation_coverage`, `high_risk_route_state`, `covered_*_count`, `blocked_confirmed_*_count`, `pending_route_class_count`, `tail_token_risk_count`, `pending_reasons[]` | 지금 무엇이 이미 막혔고 무엇이 아직 기다리는지 설명하려면 필요하다 |
| 증거 | `first_progress_at`, `last_progress_at`, `last_accept_after_request_at`, `fully_blocked_confirmed_at` | propagation lag와 blocked confirmation을 evidence로 재구성하려면 필요하다 |
| 후속 상태 | `cleanup.state`, `cleanup.cleanup_confirmed_at`, `next_poll_after_ms` | fully blocked 뒤에도 cleanup이 남을 수 있음을 분리해 보여 주기 위해 필요하다 |

여기서 중요한 규칙 두 가지:

- status payload는 preview summary를 다시 계산해도 되지만, 최소한 `preview_id`, `graph_snapshot_id`, `revocation_request_id`는 계속 이어져야 한다
- `cleanup.state`는 보조 축이다. `fully_blocked_confirmed`를 `cleanup_confirmed`의 동의어로 쓰면 안 된다

### 3. `requested`는 "수락됨"이지 "막힘"이 아니다

`requested`는 confirm 성공 직후 가장 먼저 보이는 정상 상태다.

들어가는 조건:

- confirm request가 정책 검증을 통과했다
- `revocation_request_id`가 durable하게 저장됐다
- 적어도 재시도 가능한 handoff가 만들어졌다

이 상태에서 아직 말할 수 없는 것:

- session store invalidation이 실제로 반영됐는지
- high-risk route가 이미 direct deny로 바뀌었는지
- self-contained access token tail이 끝났는지

권장 필드 패턴:

- `status_reason=awaiting_worker_claim|awaiting_fanout`
- `first_progress_at=null`
- `blocked_confirmed_*_count=0`
- `high_risk_route_state=pending|unknown`

즉 `requested`는 operator에게 "요청은 안전하게 접수됐다"를 알려 주는 상태지, "이미 모두 로그아웃됐다"를 뜻하는 상태가 아니다.

### 4. `in_progress`는 partial blocking과 tail waiting을 숨기지 않아야 한다

`in_progress`는 revoke가 실제로 움직이기 시작했지만 아직 전 scope 차단 확인이 안 된 상태다.

대표적인 진입 조건:

- session/version/family store 갱신이 끝났다
- high-risk route에 quarantine 또는 direct check deny가 적용됐다
- 일부 region/pod는 invalidation ack를 보냈지만 전부는 아니다
- refresh revoke는 끝났지만 access token TTL tail이 남아 있다

이 상태에서 payload가 꼭 알려줘야 하는 것:

- high-risk write/admin route는 이미 막혔는가
- 몇 개 session/family가 blocked-confirmed 되었는가
- 어떤 route class가 아직 pending인가
- pending 이유가 TTL인지, fan-out인지, evidence gap인지

권장 필드 패턴:

- `status_reason=high_risk_blocked_tail_remaining|regional_fanout_pending|ttl_tail_waiting`
- `first_progress_at`과 `last_progress_at`이 존재
- `pending_route_class_count > 0`
- `pending_reasons[]`에 `SELF_CONTAINED_ACCESS_TOKEN_TTL`, `REGIONAL_INVALIDATION_PENDING`, `CONFIRMATION_COVERAGE_PARTIAL` 같은 코드를 남김

중요한 점은 `in_progress`가 실패 상태가 아니라는 점이다.  
특히 security/admin route는 이미 막혔고 low-risk read path만 tail이 남은 경우에도, overall contract는 여전히 `in_progress`가 맞다.

### 5. `fully_blocked_confirmed`는 queue completion이 아니라 positive blocking evidence다

`fully_blocked_confirmed`는 가장 강한 상태다.

들어가는 조건:

- `confirmation_coverage=full`
- 계산된 범위 안의 모든 applicable route class가 `blocked_confirmed` 또는 `not_applicable`
- `pending_route_class_count=0`
- `fully_blocked_confirmed_at`이 기록됨

이 상태를 만들 때 필요한 증거 예시:

- session/version direct check가 모든 covered verifier에서 revoke를 보장한다
- refresh family 재발급이 전부 deny됨이 확인됐다
- self-contained access token tail은 TTL 만료 또는 deny observation으로 닫혔다
- downstream exchanged token도 covered audience 기준으로 더 이상 수용되지 않는다

반대로 아래만으로는 부족하다.

- worker queue 비움
- pub/sub 발행 성공
- revoke row status를 내부적으로 `done`으로 바꾼 것

즉 `fully_blocked_confirmed`는 "작업이 끝났을 것 같다"가 아니라, **계산된 범위 전체가 더 이상 통과되지 않음을 실제 enforcement evidence로 확인했다**는 뜻이어야 한다.

### 6. `fully_blocked_confirmed`와 `cleanup_confirmed`는 다른 질문에 답한다

둘을 섞으면 status contract가 바로 무너진다.

| 상태 | 답하는 질문 |
|---|---|
| `fully_blocked_confirmed` | 계산된 revoke scope 전체에서 access 차단이 확인됐는가 |
| `cleanup_confirmed` | cache sweeper, delegated session cleanup, projector tail 같은 후속 cleanup까지 닫혔는가 |

따라서 `fully_blocked_confirmed` payload에서도 아래는 가능하다.

- `cleanup.state=pending`
- `cleanup.cleanup_confirmed_at=null`

즉 operator status page는 이미 "차단 완료"를 말할 수 있어도, 내부 cleanup metric이나 security timeline은 아직 별도 후속 상태를 기다릴 수 있다.

### 7. route class와 evidence source를 분리해야 상태 의미가 안 흔들린다

단일 카운트만으로는 상태를 설명하기 어렵다.  
최소한 route class별 상태를 따로 두는 편이 안전하다.

권장 축:

- `admin_write`
- `security_settings`
- `general_read`
- `refresh_exchange`
- `downstream_audience:<name>`

각 route class row에 유용한 필드:

- `state`: `pending | blocked_confirmed | not_applicable`
- `reason_code`
- `confirmed_at`
- `expected_blocked_by`
- `evidence_source`

왜 필요한가:

- high-risk route는 이미 막혔는데 low-risk read만 tail이 남은 상태를 숨기지 않기 위해
- self-contained JWT TTL tail과 cache invalidation tail을 구분하기 위해
- "왜 아직 `in_progress`인가"를 support가 직접 설명할 수 있게 하기 위해

### 8. 상태 전이 규칙과 invariant를 고정해야 한다

권장 전이:

- `requested -> in_progress -> fully_blocked_confirmed`
- 매우 빠른 구조에서는 poller가 `requested`를 못 보고 바로 `fully_blocked_confirmed`를 볼 수 있다

추가 invariant:

- `accepted_at <= status_changed_at`
- `status=fully_blocked_confirmed`면 `fully_blocked_confirmed_at != null`
- `status=fully_blocked_confirmed`면 `pending_route_class_count=0`
- `confirmation_coverage != full`이면 `fully_blocked_confirmed`를 찍지 않는다

만약 `fully_blocked_confirmed_at` 이후 accept evidence가 새로 발견되면:

- 조용히 `in_progress`로 되돌리지 말고 contract violation으로 기록한다
- 새 incident 또는 repair trace를 남긴다
- 왜 잘못 confirmed됐는지 evidence gap을 postmortem 대상으로 올린다

즉 terminal confirmation이 뒤집히는 상황은 정상 진행이 아니라 관측/설계 실패다.

---

## 실전 시나리오

### 시나리오 1: confirm은 수락됐지만 worker가 아직 request를 잡지 않았다

올바른 상태:

- `status=requested`
- `status_reason=awaiting_worker_claim`
- `first_progress_at=null`

피해야 할 상태:

- `done`
- `completed`
- `fully_blocked_confirmed`

### 시나리오 2: admin/security route는 즉시 막혔지만 일반 read API의 access token TTL tail이 남았다

올바른 상태:

- `status=in_progress`
- `high_risk_route_state=blocked_confirmed`
- `pending_reasons=["SELF_CONTAINED_ACCESS_TOKEN_TTL"]`

피해야 할 상태:

- 전체를 `requested`로 뭉개 support가 "아직 아무것도 안 됐다"고 오해하게 만드는 것
- 전체를 `fully_blocked_confirmed`로 올려 tail risk를 숨기는 것

### 시나리오 3: pub/sub fan-out은 끝났지만 한 region에서 old token accept가 계속 관측된다

올바른 상태:

- `status=in_progress`
- `status_reason=regional_fanout_pending`
- `last_accept_after_request_at`이 계속 갱신됨

피해야 할 상태:

- worker queue가 비었다는 이유로 terminal state를 찍는 것

### 시나리오 4: 전 scope 차단은 확인됐지만 cleanup sweeper가 아직 AOBO delegated session을 정리 중이다

올바른 상태:

- `status=fully_blocked_confirmed`
- `cleanup.state=pending`

피해야 할 상태:

- cleanup이 늦다는 이유로 차단 완료까지 늦게 말하는 것
- 반대로 `cleanup_confirmed`를 status field에 그대로 재사용하는 것

### 시나리오 5: 일부 verifier의 confirmation evidence를 아직 수집하지 못한다

올바른 상태:

- `status=in_progress`
- `confirmation_coverage=partial`
- `pending_reasons=["CONFIRMATION_COVERAGE_PARTIAL"]`

피해야 할 상태:

- 모르는 verifier를 0개로 치고 `fully_blocked_confirmed`를 찍는 것

---

## 코드로 보기

### 1. `requested` payload 예시

```json
{
  "schema_version": "2026-04-14",
  "revocation_request_id": "revreq_01JV9Q96D65J8Y8X9W",
  "status": "requested",
  "status_reason": "awaiting_worker_claim",
  "accepted_at": "2026-04-14T11:04:10Z",
  "status_changed_at": "2026-04-14T11:04:10Z",
  "fully_blocked_confirmed_at": null,
  "source": {
    "trigger_kind": "operator_confirmed_preview",
    "preview_id": "prev_01JV9Q8SV0M29KYCZZ",
    "graph_snapshot_id": "graph_01JV9Q8S0V8J81R5GQ",
    "operator_id": "op_42",
    "operator_session_id": "opsess_991",
    "operator_mode": "ACTING_ON_BEHALF",
    "approval_id": "apr_77",
    "ticket_id": "INC-441"
  },
  "subject": {
    "tenant_id": "tenant_9",
    "subject_user_id": "user_123"
  },
  "request": {
    "action": "revoke_device_sessions",
    "scope_kind": "device",
    "selector": {
      "device_id": "dev_7"
    }
  },
  "summary": {
    "covered_session_count": 2,
    "covered_refresh_family_count": 1,
    "tail_token_risk_count": 1
  },
  "propagation": {
    "confirmation_coverage": "unknown",
    "high_risk_route_state": "pending",
    "blocked_confirmed_session_count": 0,
    "blocked_confirmed_refresh_family_count": 0,
    "pending_route_class_count": 3,
    "pending_reasons": ["AWAITING_WORKER_CLAIM"]
  },
  "evidence": {
    "first_progress_at": null,
    "last_progress_at": null,
    "last_accept_after_request_at": null
  },
  "cleanup": {
    "state": "not_started",
    "cleanup_confirmed_at": null
  },
  "next_poll_after_ms": 1500
}
```

### 2. `in_progress` payload 예시

```json
{
  "schema_version": "2026-04-14",
  "revocation_request_id": "revreq_01JV9Q96D65J8Y8X9W",
  "status": "in_progress",
  "status_reason": "high_risk_blocked_tail_remaining",
  "accepted_at": "2026-04-14T11:04:10Z",
  "status_changed_at": "2026-04-14T11:04:13Z",
  "fully_blocked_confirmed_at": null,
  "source": {
    "trigger_kind": "operator_confirmed_preview",
    "preview_id": "prev_01JV9Q8SV0M29KYCZZ",
    "graph_snapshot_id": "graph_01JV9Q8S0V8J81R5GQ",
    "operator_id": "op_42",
    "operator_session_id": "opsess_991",
    "operator_mode": "ACTING_ON_BEHALF"
  },
  "subject": {
    "tenant_id": "tenant_9",
    "subject_user_id": "user_123"
  },
  "summary": {
    "covered_session_count": 2,
    "covered_refresh_family_count": 1,
    "tail_token_risk_count": 1
  },
  "propagation": {
    "confirmation_coverage": "partial",
    "high_risk_route_state": "blocked_confirmed",
    "blocked_confirmed_session_count": 2,
    "blocked_confirmed_refresh_family_count": 1,
    "pending_route_class_count": 1,
    "pending_reasons": [
      "SELF_CONTAINED_ACCESS_TOKEN_TTL"
    ]
  },
  "route_classes": [
    {
      "route_class": "admin_write",
      "state": "blocked_confirmed",
      "confirmed_at": "2026-04-14T11:04:12Z",
      "evidence_source": "direct_revoke_check"
    },
    {
      "route_class": "general_read",
      "state": "pending",
      "reason_code": "SELF_CONTAINED_ACCESS_TOKEN_TTL",
      "expected_blocked_by": "2026-04-14T11:09:10Z",
      "evidence_source": "access_token_ttl_window"
    }
  ],
  "evidence": {
    "first_progress_at": "2026-04-14T11:04:11Z",
    "last_progress_at": "2026-04-14T11:04:13Z",
    "last_accept_after_request_at": "2026-04-14T11:04:12Z"
  },
  "cleanup": {
    "state": "pending",
    "cleanup_confirmed_at": null
  },
  "next_poll_after_ms": 3000
}
```

### 3. `fully_blocked_confirmed` payload 예시

```json
{
  "schema_version": "2026-04-14",
  "revocation_request_id": "revreq_01JV9Q96D65J8Y8X9W",
  "status": "fully_blocked_confirmed",
  "status_reason": "all_covered_paths_blocked",
  "accepted_at": "2026-04-14T11:04:10Z",
  "status_changed_at": "2026-04-14T11:09:12Z",
  "fully_blocked_confirmed_at": "2026-04-14T11:09:12Z",
  "source": {
    "trigger_kind": "operator_confirmed_preview",
    "preview_id": "prev_01JV9Q8SV0M29KYCZZ",
    "graph_snapshot_id": "graph_01JV9Q8S0V8J81R5GQ",
    "operator_id": "op_42",
    "operator_session_id": "opsess_991",
    "operator_mode": "ACTING_ON_BEHALF"
  },
  "subject": {
    "tenant_id": "tenant_9",
    "subject_user_id": "user_123"
  },
  "summary": {
    "covered_session_count": 2,
    "covered_refresh_family_count": 1,
    "tail_token_risk_count": 0
  },
  "propagation": {
    "confirmation_coverage": "full",
    "high_risk_route_state": "blocked_confirmed",
    "blocked_confirmed_session_count": 2,
    "blocked_confirmed_refresh_family_count": 1,
    "pending_route_class_count": 0,
    "pending_reasons": []
  },
  "route_classes": [
    {
      "route_class": "admin_write",
      "state": "blocked_confirmed",
      "confirmed_at": "2026-04-14T11:04:12Z",
      "evidence_source": "direct_revoke_check"
    },
    {
      "route_class": "general_read",
      "state": "blocked_confirmed",
      "confirmed_at": "2026-04-14T11:09:12Z",
      "evidence_source": "ttl_expired_plus_acceptance_window_closed"
    }
  ],
  "evidence": {
    "first_progress_at": "2026-04-14T11:04:11Z",
    "last_progress_at": "2026-04-14T11:09:12Z",
    "last_accept_after_request_at": "2026-04-14T11:04:12Z"
  },
  "cleanup": {
    "state": "pending",
    "cleanup_confirmed_at": null
  },
  "next_poll_after_ms": 30000
}
```

### 4. 운영 체크리스트

```text
1. requested가 "수락됨"만 뜻하고 blocked guarantee를 암시하지 않는가
2. in_progress가 high-risk route 차단 여부와 pending reason을 같이 내려주는가
3. fully_blocked_confirmed가 queue drain이 아니라 acceptance evidence로만 생성되는가
4. confirmation_coverage가 full이 아닐 때 terminal state를 금지하는가
5. fully_blocked_confirmed와 cleanup_confirmed를 별도 필드로 분리하는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `requested/in_progress/fully_blocked_confirmed` 3단계 계약 | operator 설명과 security guarantee가 선명하다 | payload와 evidence 설계가 더 필요하다 | operator-triggered revoke, support tooling |
| generic `pending/done` 상태 | 구현이 단순하다 | propagation tail과 blocked confirmation을 숨긴다 | low-risk internal batch only |
| route class별 상태 포함 | 왜 아직 진행 중인지 설명이 가능하다 | payload가 길어진다 | multi-route, mixed token 환경 |
| cleanup를 별도 축으로 분리 | terminal 차단과 forensic cleanup을 혼동하지 않는다 | 상태 모델이 두 축이 된다 | AOBO, break-glass, distributed revoke |

판단 기준은 이렇다.

- confirm accepted와 실제 차단 확인 사이에 의미 있는 시간이 존재하는가
- high-risk route와 low-risk route의 revoke 즉시성이 다른가
- tail token과 regional fan-out을 operator가 설명해야 하는가
- cleanup lag와 access block을 별도 운영 지표로 봐야 하는가

---

## 꼬리질문

> Q: `requested`인데 이미 일부 route는 막혔을 수도 있지 않나요?
> 의도: 상태 명칭과 보장 수준을 구분하는지 확인
> 핵심: 그럴 수 있어도 `requested`가 약속하는 보장은 "접수 완료"뿐이다. 실제 차단을 말하려면 `in_progress` 이상의 evidence가 필요하다.

> Q: `in_progress`는 실패 상태인가요?
> 의도: 진행 중 상태를 오류로 오해하지 않는지 확인
> 핵심: 아니다. partial blocking, TTL tail, regional fan-out처럼 정상 전파 중인 상황을 뜻할 수 있다.

> Q: `fully_blocked_confirmed`면 cleanup도 끝난 건가요?
> 의도: terminal block과 cleanup을 분리하는지 확인
> 핵심: 아니다. 차단 확인과 cleanup confirmation은 다른 질문이다.

> Q: 왜 queue completion만으로 terminal state를 찍으면 안 되나요?
> 의도: enforcement evidence의 필요성을 이해하는지 확인
> 핵심: queue가 비어도 실제 verifier나 downstream audience가 old token을 계속 받아들일 수 있기 때문이다.

## 한 줄 정리

Revocation status contract의 핵심은 "작업이 돌고 있다"가 아니라, operator가 요청한 revoke가 지금 `requested`, `in_progress`, `fully_blocked_confirmed` 중 어느 security guarantee까지 도달했는지를 evidence와 함께 고정하는 것이다.

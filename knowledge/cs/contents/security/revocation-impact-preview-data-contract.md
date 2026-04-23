# Revocation Impact Preview Data Contract

> 한 줄 요약: operator tooling의 revocation preview는 버튼 label이 아니라, device/session/refresh family 그래프를 서버가 직접 확장한 snapshot payload와 stable join key를 함께 내려줘야 blast radius를 안전하게 설명할 수 있다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **operator revocation preview payload, join key, preview-to-execution handoff**를 설명하는 deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)
> - [Device / Session Graph Revocation Design](./device-session-graph-revocation-design.md)
> - [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
> - [Revocation Preview Drift Response Contract](./revocation-preview-drift-response-contract.md)
> - [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)
> - [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md)
> - [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
> - [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [Security README: Browser / Session Coherence](./README.md#browser--session-coherence)

retrieval-anchor-keywords: revocation impact preview, revoke preview payload, blast radius preview contract, operator revoke preview, device session family preview, session graph preview, preview join keys, graph snapshot id, revocation request id, operator session id, device id session id refresh family id, preview coverage partial, requested scope vs effective impact, tail token warning, operator revocation audit join, preview to execution handoff, preview drift response contract, preview expired confirm, forced re-confirmation, replacement preview, revocation status contract, requested in progress fully blocked confirmed, aobo revocation audit event schema, break glass revoke trace, preview confirm timeline join key, browser session coherence, session boundary bridge, session inventory branch

## 이 문서 다음에 보면 좋은 문서

- revoke 대상 그래프 모델 자체는 [Device / Session Graph Revocation Design](./device-session-graph-revocation-design.md)으로 이어진다.
- operator mode, friction, confirm flow는 [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)와 같이 봐야 한다.
- confirm 시점의 `graph_snapshot_id` drift, preview expiry, 강제 재확인 응답은 [Revocation Preview Drift Response Contract](./revocation-preview-drift-response-contract.md)에서 따로 다룬다.
- confirm 이후 status page가 `requested`, `in_progress`, `fully_blocked_confirmed`를 어떤 payload로 보여 줄지는 [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)에서 이어진다.
- AOBO / break-glass revoke의 `preview_id`, `graph_snapshot_id`, `revocation_request_id`, `access_group_id`를 audit timeline까지 어떻게 잇는지는 [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)로 이어진다.
- 사용자가 실제로 보게 되는 scope naming과 inventory row는 [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)로 이어진다.
- revoke 이후 tail과 propagation 상태 표현은 [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)을 같이 봐야 한다.
- preview, confirm, audit timeline을 한 trace로 묶는 방법은 [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)에서 이어 볼 수 있다.

---

## 핵심 개념

revocation preview에서 자주 하는 실수는 다음 셋을 하나로 뭉개는 것이다.

- operator가 **무엇을 요청했는가**
- 현재 session graph가 **실제로 무엇을 끊게 되는가**
- confirm 이후 **어떤 request/audit/event id로 이어지는가**

이 셋이 분리되지 않으면 문제가 생긴다.

- UI label은 `이 기기 종료`인데 실제로는 browser session 2개와 refresh family 1개가 끊긴다
- frontend가 display label 기준으로 dedupe해서 영향 수를 잘못 보여 준다
- confirm 이후 audit에는 `user_id`만 남고 어떤 preview를 보고 눌렀는지 복원할 수 없다

즉 preview payload의 본질은 "카운트 하나 더 내려주는 API"가 아니라, **destructive action 전에 graph expansion 결과와 추적용 식별자를 묶어 주는 읽기 모델**이다.

---

## 깊이 들어가기

### 1. payload는 `request`, `resolution`, `handoff` 세 덩어리로 나뉘어야 한다

최소 구조는 이렇다.

- `request`: operator가 선택한 scope와 현재 mode
- `resolution`: 서버가 현재 graph snapshot에서 계산한 실제 영향 범위
- `handoff`: confirm 시 그대로 넘겨야 하는 preview binding 정보

왜 분리해야 하는가.

- `request.scope_kind=device`여도 `resolution`에는 session/family/step-up grant가 여러 개 나올 수 있다
- operator가 AOBO인지 break-glass인지에 따라 같은 revoke라도 허용 조건이 다르다
- confirm 시점에는 preview 당시 기준과 현재 graph가 달라졌는지 비교해야 한다

즉 frontend는 scope를 "계산"하는 쪽이 아니라, **서버가 계산한 scope를 설명하고 재확인하는 쪽**이어야 한다.

### 2. requested scope와 effective impact를 동시에 내려야 한다

preview는 "무엇을 눌렀는가"와 "무엇이 실제로 영향을 받는가"를 같은 payload에 실어야 한다.

예를 들어:

- 요청은 `revoke_device_sessions`
- 선택된 대상은 `device_id=dev_7`
- 실제 영향은 `session 2`, `refresh family 1`, `step-up grant 1`
- 추가 warning은 `tail token may survive until TTL expiry`

이때 `summary`에는 최소한 아래 count가 필요하다.

- `impacted_device_count`
- `impacted_session_count`
- `impacted_refresh_family_count`
- `impacted_step_up_grant_count`
- `tail_token_risk_count`

중요한 점은 `tail_token_risk_count`가 revoke 대상 개수와 같은 의미가 아니라는 점이다.  
이 값은 "추가 설명이 필요한 잔여 tail이 몇 군데 남는가"를 뜻한다. 영향을 받는 session 수에 합쳐 버리면 operator가 실제 blast radius를 오해한다.

### 3. join key는 row id나 display label이 아니라 stable id여야 한다

preview에서 꼭 필요한 join key는 다음과 같다.

| 레이어 | 필수 키 | 왜 필요한가 |
|---|---|---|
| preview envelope | `preview_id`, `graph_snapshot_id`, `computed_at`, `expires_at` | 어떤 preview를 보고 confirm했는지와 snapshot drift를 추적하기 위해 필요하다 |
| operator context | `operator_id`, `operator_session_id`, `operator_mode`, `approval_id` 또는 `ticket_id` | AOBO / break-glass / 일반 지원 작업을 audit timeline과 연결하려면 필요하다 |
| subject scope | `tenant_id`, `subject_user_id` | multi-tenant operator tool에서 잘못된 cross-tenant join을 막기 위해 필요하다 |
| device row | `device_id` | 같은 device label이 여러 번 바뀌어도 session 묶음을 안정적으로 설명하기 위해 필요하다 |
| session row | `session_id`, `device_id`, `refresh_family_id`(nullable) | device 단위와 family 단위를 동시에 보여 주려면 각 session에 부모 key가 있어야 한다 |
| family row | `refresh_family_id` | family revoke, reuse 대응, audit join을 한 키로 묶기 위해 필요하다 |
| elevated/tail row | `step_up_grant_id`, `downstream_grant_id`(nullable) + 부모 session/family key | revoke 대상은 아니어도 operator에게 추가 영향과 cleanup 대상을 설명하려면 필요하다 |
| execution/audit | `revocation_request_id`, `preview_id`, `graph_snapshot_id` | confirm 이후 request status, propagation, audit를 하나의 trace로 묶기 위해 필요하다 |

반대로 join key로 쓰면 안 되는 것:

- `row_id`
- `display_label`
- `device_nickname`
- `Chrome / Seoul` 같은 사람용 copy

이 값들은 projection이 바뀌면 쉽게 흔들린다.

### 4. count semantics와 상태 semantics를 고정해야 한다

preview contract에는 숫자뿐 아니라 숫자의 의미도 있어야 한다.

권장 필드:

- `coverage`: `full | partial | stale`
- `partial_reasons[]`
- `propagation_expectation`: `immediate | lag_expected | unknown`
- `requires_step_up`: `true | false`
- `reconfirm_required`: `true | false`

해석 규칙도 고정하는 편이 좋다.

- `impacted_*_count`는 snapshot 시점의 **unique active id 수**다
- 이미 만료되었거나 이미 revoked인 row는 기본 count에서 제외하고, 필요하면 `already_inactive_count`로 분리한다
- 모르는 대상을 0으로 넣지 말고 `coverage=partial`과 `partial_reasons[]`로 드러낸다
- `propagation_expectation=lag_expected`는 "revoke 불가"가 아니라 "tail 설명 필요"라는 뜻이다

즉 preview API는 숫자만 주면 끝나는 것이 아니라, **숫자를 믿어도 되는 조건**까지 같이 설명해야 한다.

### 5. preview와 execution 사이 drift를 계약으로 다뤄야 한다

preview를 본 뒤 confirm하기 전에는 graph가 바뀔 수 있다.

예:

- session 하나가 이미 만료됨
- refresh family가 rotation으로 바뀜
- operator mode TTL이 끝남
- break-glass approval이 취소됨

그래서 confirm request에는 최소한 아래 값이 다시 들어가야 한다.

- `preview_id`
- `graph_snapshot_id`
- `confirm_token`
- `idempotency_key`
- `operator_session_id`

서버는 confirm 시점에 graph를 재검증하고, 차이가 크면 `drift_detected`로 되돌려 새 preview를 강제하는 편이 안전하다.

### 6. audit와 observability도 같은 key를 써야 한다

preview API만 join key를 잘 설계해도, confirm/audit/propagation event가 다른 key를 쓰면 trace가 끊긴다.

최소한 이어져야 하는 이벤트:

- `operator.revocation_previewed`
- `operator.revocation_confirmed`
- `session.revocation_requested`
- `session.revocation_propagation_completed`

이벤트 공통 필드로 유용한 것:

- `preview_id`
- `graph_snapshot_id`
- `revocation_request_id`
- `operator_session_id`
- `tenant_id`
- `subject_user_id`
- `device_id` / `session_id` / `refresh_family_id`

이렇게 해야 support가 "왜 이 family가 끊겼나"를 물었을 때 preview 화면, confirm 요청, propagation lag를 한 흐름으로 재구성할 수 있다.

---

## 실전 시나리오

### 시나리오 1: `이 기기 종료` preview가 실제보다 작게 보인다

문제:

- frontend가 `device_label` 기준으로만 dedupe했다
- 같은 device 아래 browser session 2개와 refresh family 1개가 숨었다

대응:

- count는 항상 stable id 기준으로 계산한다
- device row 아래 session/family key를 함께 내려 operator가 cut-set을 볼 수 있게 한다

### 시나리오 2: preview는 맞았는데 confirm 후 audit에서 연결이 끊긴다

문제:

- preview API에는 `preview_id`가 있었지만 revocation event에는 없다

대응:

- confirm request와 downstream event에 `preview_id`, `graph_snapshot_id`, `revocation_request_id`를 같이 실어 trace를 닫는다

### 시나리오 3: propagation lag가 있는데 UI는 즉시 완료로 보인다

문제:

- `tail_token_risk_count`와 `propagation_expectation`이 payload에 없다

대응:

- preview 단계에서 tail warning을 분리 노출한다
- confirm 이후에는 `requested`, `in_progress`, `fully_blocked_confirmed` 상태를 분리하고, 그 의미는 [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)에 맞춰 고정한다

### 시나리오 4: AOBO preview를 보고 눌렀는데 operator TTL이 이미 끝났다

문제:

- preview와 execution이 operator mode context를 공유하지 않는다

대응:

- preview payload에 `operator_session_id`, `operator_mode`, `expires_at`, `approval_id`를 포함한다
- confirm 시 같은 값을 재검증해 drift를 막는다

---

## 코드로 보기

### 1. preview payload 예시

```json
{
  "preview_id": "prev_01HR7J9YB3M8JY4A7Q",
  "graph_snapshot_id": "graph_01HR7J9ZZ4K5D4CX2D",
  "computed_at": "2026-04-14T11:02:03Z",
  "expires_at": "2026-04-14T11:03:03Z",
  "coverage": "full",
  "propagation_expectation": "lag_expected",
  "requires_step_up": true,
  "actor": {
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
    "impacted_device_count": 1,
    "impacted_session_count": 2,
    "impacted_refresh_family_count": 1,
    "impacted_step_up_grant_count": 1,
    "tail_token_risk_count": 1
  },
  "devices": [
    {
      "device_id": "dev_7",
      "display_label": "MacBook Pro / Chrome",
      "session_ids": ["sess_web_1", "sess_web_2"],
      "refresh_family_ids": ["fam_99"]
    }
  ],
  "sessions": [
    {
      "session_id": "sess_web_1",
      "device_id": "dev_7",
      "refresh_family_id": "fam_99",
      "step_up_grant_ids": ["sug_5"],
      "downstream_tail_risk": true
    },
    {
      "session_id": "sess_web_2",
      "device_id": "dev_7",
      "refresh_family_id": "fam_99",
      "step_up_grant_ids": [],
      "downstream_tail_risk": false
    }
  ],
  "refresh_families": [
    {
      "refresh_family_id": "fam_99",
      "session_ids": ["sess_web_1", "sess_web_2"]
    }
  ],
  "warnings": [
    {
      "code": "TAIL_TOKEN_MAY_SURVIVE",
      "refresh_family_id": "fam_99",
      "message": "short-lived downstream token may survive until TTL expiry"
    }
  ],
  "handoff": {
    "confirm_token": "cnf_4ddf10a2",
    "reconfirm_required": false
  }
}
```

### 2. confirm request 예시

```json
{
  "preview_id": "prev_01HR7J9YB3M8JY4A7Q",
  "graph_snapshot_id": "graph_01HR7J9ZZ4K5D4CX2D",
  "confirm_token": "cnf_4ddf10a2",
  "idempotency_key": "revreq_01HR7JA7RXCMR5Q5F4",
  "operator_session_id": "opsess_991"
}
```

### 3. 운영 체크리스트

```text
1. preview가 requested scope와 effective impact를 분리해 내려주는가
2. 모든 session row가 device_id와 refresh_family_id를 함께 가지는가
3. partial/unknown을 0으로 뭉개지 않고 coverage로 드러내는가
4. preview_id, graph_snapshot_id, revocation_request_id가 preview/confirm/audit 전 구간에서 이어지는가
5. propagation lag와 tail token warning을 summary count와 분리해 설명하는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| summary count만 주는 preview | 구현이 가볍다 | 왜 그 숫자가 나왔는지 설명이 약하다 | low-risk internal tool |
| graph projection + stable join key | blast radius 설명과 audit이 강하다 | 계산 비용이 늘어난다 | operator의 destructive revoke |
| frontend에서 entity join 계산 | UI 유연성이 크다 | stale cache와 잘못된 dedupe 위험이 크다 | 피하는 편이 낫다 |
| preview-bound confirm | drift와 재확인 누락을 줄인다 | confirm 흐름이 한 단계 늘어난다 | AOBO / break-glass / high-risk revoke |

판단 기준은 이렇다.

- operator가 실제 영향 row를 설명해야 하는가
- 같은 device 아래 여러 session/family가 공존하는가
- audit에서 preview와 confirm을 한 trace로 묶어야 하는가
- propagation lag를 사용자/운영자에게 분리해 설명해야 하는가

---

## 꼬리질문

> Q: `preview_id`와 `graph_snapshot_id`를 왜 둘 다 두나요?
> 의도: 읽은 preview와 계산 기준 snapshot을 구분하는지 확인
> 핵심: preview 자체의 식별자와 graph 버전 식별자는 역할이 다르기 때문이다.

> Q: display label로 join하면 왜 안 되나요?
> 의도: 사람용 copy와 시스템용 식별자를 구분하는지 확인
> 핵심: label은 projection이나 locale에 따라 쉽게 바뀌지만, revoke/audit join은 안정적인 id가 필요하기 때문이다.

> Q: `coverage=partial`을 0으로 처리하면 왜 위험한가요?
> 의도: unknown과 zero를 구분하는지 확인
> 핵심: 실제 blast radius를 과소평가해 operator가 과도하게 좁은 영향으로 오판할 수 있기 때문이다.

> Q: 왜 propagation warning을 revoke count와 분리하나요?
> 의도: 영향 범위와 tail 설명을 구분하는지 확인
> 핵심: 끊을 대상의 수와, 끊긴 뒤 잠깐 남을 수 있는 tail risk는 다른 의미의 정보이기 때문이다.

## 한 줄 정리

revocation impact preview의 핵심은 "이 버튼이 무엇을 끊는가"를 stable id 기반 graph snapshot으로 보여 주고, 그 snapshot을 confirm과 audit까지 같은 key로 이어 붙이는 것이다.

# Revocation Preview Drift Response Contract

> 한 줄 요약: revocation confirm API는 stale preview를 단순 오류로 끝내면 안 되고, `graph_snapshot_id` drift, preview 만료, 강제 재확인을 구분한 구조화 응답과 replacement preview를 내려 operator가 같은 흐름 안에서 안전하게 다시 확인할 수 있어야 한다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **revocation confirm-time response schema, drift taxonomy, operator UX state contract**를 설명하는 deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md)
> - [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)
> - [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
> - [Device / Session Graph Revocation Design](./device-session-graph-revocation-design.md)
> - [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)
> - [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [Security README: Browser / Session Coherence](./README.md#browser--session-coherence)

retrieval-anchor-keywords: preview drift response contract, revocation confirm response, graph snapshot drift, graph_snapshot_id drift, preview expired, forced re-confirmation, reconfirm required, replacement preview, stale preview response, confirm-time schema, operator revoke reconfirm, session graph drift, preview 409 conflict, preview 410 gone, blast radius diff, operator safety state, execution requested vs requested, revocation request status, requested in progress fully blocked confirmed, browser session coherence, session boundary bridge, session inventory branch

## 이 문서 다음에 보면 좋은 문서

- preview payload와 join key 정의는 [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md)에서 먼저 고정한다.
- operator mode, TTL, AOBO / break-glass friction은 [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)와 같이 봐야 한다.
- inventory row와 revoke scope naming은 [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)에서 이어진다.
- confirm이 `accepted`된 뒤 status endpoint가 어떤 payload로 전파 상태를 내려야 하는지는 [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)에서 이어진다.
- confirm 이후 propagation status와 tail 설명은 [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)으로 이어진다.
- preview, confirm, request lifecycle audit key는 [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)에서 묶는다.

---

## 핵심 개념

confirm 시점의 revocation은 단순한 yes/no endpoint가 아니다.  
이미 계산해 둔 preview가 현재 세션 그래프와 아직 같은지, TTL 안에 있는지, 그리고 high-risk action이라 다시 한 번 operator 의사를 받아야 하는지를 함께 다뤄야 한다.

여기서 자주 생기는 실패는 셋이다.

- stale preview를 `409 preview stale` 같은 문자열 하나로 뭉개 버린다
- `graph_snapshot_id`가 달라졌는데 old confirm token으로 그냥 실행한다
- 만료된 preview를 background refresh로 바꿔치기해 operator가 무엇을 다시 승인했는지 흐리게 만든다

즉 confirm-time contract의 핵심은 "실행 성공 여부"보다 **지금 보고 있는 preview가 아직 유효한가, 아니라면 어떤 UX state로 다시 확인시킬 것인가**를 고정하는 것이다.

---

## 깊이 들어가기

### 1. confirm 응답은 transport error보다 business state가 먼저여야 한다

권장 분리는 이렇다.

| confirm state | 권장 HTTP | 의미 | UX 기본 상태 |
|---|---|---|---|
| `accepted` | `202 Accepted` | confirm이 수락되어 revoke request가 생성됐다 | `execution_requested` |
| `stale` + `reason_code=graph_snapshot_drifted` | `409 Conflict` | 제출한 preview binding이 현재 graph와 충돌한다 | `drift_detected` 또는 `reconfirm_required` |
| `stale` + `reason_code=preview_expired` | `410 Gone` | preview TTL이 끝나 더 이상 old confirm을 받을 수 없다 | `preview_expired` 또는 `reconfirm_required` |
| `rejected` | `403` / `422` | operator context나 정책이 현재 실행을 허용하지 않는다 | `reauth_required` 또는 `blocked` |

핵심은 `409`나 `410` 자체가 최종 계약이 아니라는 점이다.  
operator tooling은 body 안에서 **왜 stale한지**, **새 preview가 이미 준비됐는지**, **즉시 재확인이 가능한지**까지 받아야 한다.

### 2. 최소 응답 envelope를 고정해야 한다

confirm-time body는 아래 필드를 공통으로 가지는 편이 안전하다.

| 필드 | 의미 | 왜 필요한가 |
|---|---|---|
| `confirm_state` | `accepted \| stale \| rejected` | 성공/재확인/차단을 transport와 분리해 표현한다 |
| `reason_code` | `none`, `graph_snapshot_drifted`, `preview_expired` 등 | stale/reject 원인을 operator copy와 audit에 같이 쓴다 |
| `forced_reconfirm` | `true \| false` | replacement preview가 있어도 old confirm을 재사용하지 않음을 명시한다 |
| `checked_at` | 서버가 재검증한 시각 | confirm 당시 판정 기준 시각을 남긴다 |
| `submitted_preview` | operator가 실제로 제출한 `preview_id`, `graph_snapshot_id`, `expires_at` | "무엇을 보고 눌렀는가"를 보존한다 |
| `current_evaluation` | 현재 graph 기준 판정 결과 | drift/coverage/impact delta를 담는다 |
| `replacement_preview` | 새로 발급한 preview envelope와 `confirm_token` | 같은 modal 안에서 재확인을 이어 가려면 필요하다 |
| `ux` | client가 바로 렌더링할 state와 action 힌트 | frontend마다 stale 처리 방식이 갈라지는 것을 막는다 |
| `audit` | trace용 join key | preview, confirm, revocation request를 한 흐름으로 묶는다 |

특히 중요한 규칙은 둘이다.

- `submitted_preview`는 절대 덮어쓰지 않는다
- 새 preview를 내릴 때는 항상 **새 `preview_id`, 새 `graph_snapshot_id`, 새 `confirm_token`, 새 `expires_at`**를 발급한다

즉 stale 응답은 "기존 preview를 고쳐서 다시 주는 것"이 아니라, **기존 preview를 보존한 채 superseding preview를 별도 발급하는 것**이어야 한다.

### 3. `graph_snapshot_id` drift는 diff와 replacement preview를 같이 내려야 한다

`graph_snapshot_id`가 달라졌다면 서버는 최소한 아래 질문에 답해야 한다.

- 영향 범위가 넓어졌는가 (`expanded`)
- 영향 범위가 줄었는가 (`reduced`)
- count는 비슷하지만 membership가 바뀌었는가 (`rotated`)
- partial coverage라 정확한 비교가 불가능한가 (`ambiguous`)

권장 필드는 이렇다.

- `current_evaluation.graph_snapshot_id`
- `current_evaluation.drift_class`
- `current_evaluation.summary_before`
- `current_evaluation.summary_after`
- `current_evaluation.changed_entities`
- `replacement_preview`

여기서 중요한 보안 기본값은 이것이다.

- AOBO / break-glass / tenant-wide revoke처럼 high-risk action은 `drift_class=same_effect`여도 기본적으로 `forced_reconfirm=true`
- low-risk internal tooling만 예외적으로 semantic equivalence를 증명했을 때 auto-continue를 허용할 수 있다

즉 snapshot id가 바뀌었는데 "count가 같으니 그냥 실행"은 기본값이 되면 안 된다.

### 4. preview 만료는 "자동 새로고침"보다 "기존 confirm 무효"로 보여야 한다

preview TTL이 끝났다면 old confirm button은 이미 의미를 잃었다.

그래서 만료 응답은 아래 규칙을 지키는 편이 좋다.

- `reason_code=preview_expired`
- old confirm CTA는 즉시 disabled
- old preview card/modal은 `expired` badge와 함께 visual mute 처리
- replacement preview가 없으면 primary action은 `recompute_preview`
- replacement preview가 있더라도 old confirm을 바로 재사용하지 않고 `forced_reconfirm=true`로 새 click을 요구

즉 preview expiry는 background refresh UX 문제가 아니라, **operator가 어떤 snapshot에 동의했는지의 증거를 새로 만드는 과정**이다.

### 5. UX state는 `drift_detected`, `preview_expired`, `reconfirm_required`를 분리한다

client는 서버 body를 해석해 아래 상태 중 하나로 들어가면 된다.

| `ux.state` | 언제 쓰는가 | UI 동작 |
|---|---|---|
| `drift_detected` | `graph_snapshot_id`가 달라졌고 replacement preview가 아직 없다 | old confirm 비활성화, diff summary 노출, `새 미리보기 계산` CTA 제공 |
| `preview_expired` | preview TTL이 끝났고 replacement preview가 없다 | 만료 배지, 남은 TTL 제거, `다시 계산` CTA 제공 |
| `reconfirm_required` | replacement preview가 이미 내려왔고 새 확인이 필요하다 | old preview를 접거나 muted 처리, 새 preview를 기준으로 diff와 confirm label을 갱신 |
| `execution_requested` | confirm이 수락됐다 | progress/state page로 이동하거나 in-progress badge 노출 |

권장 copy는 이렇게 고정할 수 있다.

- drift: `영향 범위가 변경되어 다시 확인이 필요합니다.`
- expiry: `미리보기 유효 시간이 지나 최신 상태로 다시 계산해야 합니다.`
- forced reconfirm: `새 미리보기 기준으로 다시 확인`

old confirm label을 그대로 두면 operator가 "방금 눌렀던 것의 재시도"로 오해하기 쉽다.  
따라서 `reconfirm_required`에서는 confirm button 자체를 새 의미로 rename하는 편이 안전하다.

또한 `ux.state=execution_requested`는 confirm-time 상태일 뿐, revoke propagation이 실제로 어디까지 갔는지는 아직 말해 주지 않는다.  
confirm이 수락된 뒤 polling/status surface에서는 `requested`, `in_progress`, `fully_blocked_confirmed`를 별도 계약으로 내려야 하고, 이는 [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)에서 따로 고정한다.

---

## 실전 시나리오

### 시나리오 1: device revoke preview를 보는 사이 refresh family가 rotation되어 영향 범위가 넓어졌다

문제:

- 제출한 `graph_snapshot_id`와 현재 graph가 다르다
- session count는 같지만 family membership가 바뀌었다

대응:

- `confirm_state=stale`
- `reason_code=graph_snapshot_drifted`
- `current_evaluation.drift_class=rotated`
- `replacement_preview`를 함께 내려 `ux.state=reconfirm_required`로 전환한다

### 시나리오 2: support가 통화 중 설명하다가 preview TTL이 끝났다

문제:

- preview는 더 이상 증거로 쓸 수 없지만, UI는 여전히 old confirm button을 보여 준다

대응:

- `410 Gone` + `reason_code=preview_expired`
- old confirm을 비활성화하고 `다시 계산` CTA만 남긴다
- 자동 새로고침으로 버튼 위치만 바꾸는 방식은 피한다

### 시나리오 3: snapshot id는 바뀌었지만 count는 같아서 엔지니어가 무시하고 싶다

문제:

- count equality를 semantic equality로 오해했다
- AOBO revoke라면 대상 membership 변화만으로도 의미가 달라질 수 있다

대응:

- `summary_after`만 보지 말고 `changed_entities`를 같이 본다
- high-risk action은 `same_effect` 판정이어도 기본적으로 강제 재확인을 유지한다

---

## 코드로 보기

### 1. confirm이 수락된 경우

```json
{
  "confirm_state": "accepted",
  "reason_code": "none",
  "forced_reconfirm": false,
  "checked_at": "2026-04-14T11:04:10Z",
  "submitted_preview": {
    "preview_id": "prev_01HR7J9YB3M8JY4A7Q",
    "graph_snapshot_id": "graph_01HR7J9ZZ4K5D4CX2D",
    "expires_at": "2026-04-14T11:05:03Z"
  },
  "current_evaluation": {
    "graph_snapshot_id": "graph_01HR7J9ZZ4K5D4CX2D",
    "drift_class": "none"
  },
  "replacement_preview": null,
  "ux": {
    "state": "execution_requested",
    "primary_action": "open_request_status"
  },
  "audit": {
    "preview_id": "prev_01HR7J9YB3M8JY4A7Q",
    "submitted_graph_snapshot_id": "graph_01HR7J9ZZ4K5D4CX2D",
    "current_graph_snapshot_id": "graph_01HR7J9ZZ4K5D4CX2D",
    "revocation_request_id": "revreq_01HR7JBFW3K3T8YB1Q"
  }
}
```

### 2. `graph_snapshot_id` drift로 새 preview 기준 재확인이 필요한 경우

```json
{
  "confirm_state": "stale",
  "reason_code": "graph_snapshot_drifted",
  "forced_reconfirm": true,
  "checked_at": "2026-04-14T11:04:10Z",
  "submitted_preview": {
    "preview_id": "prev_01HR7J9YB3M8JY4A7Q",
    "graph_snapshot_id": "graph_01HR7J9ZZ4K5D4CX2D",
    "expires_at": "2026-04-14T11:05:03Z"
  },
  "current_evaluation": {
    "graph_snapshot_id": "graph_01HR7JCG7VQ0D11S9F",
    "drift_class": "expanded",
    "summary_before": {
      "impacted_session_count": 2,
      "impacted_refresh_family_count": 1
    },
    "summary_after": {
      "impacted_session_count": 3,
      "impacted_refresh_family_count": 2
    },
    "changed_entities": {
      "added_session_count": 1,
      "added_refresh_family_count": 1
    }
  },
  "replacement_preview": {
    "preview_id": "prev_01HR7JCHD8MNQ3BBYV",
    "graph_snapshot_id": "graph_01HR7JCG7VQ0D11S9F",
    "expires_at": "2026-04-14T11:05:10Z",
    "confirm_token": "ct_01HR7JCK4N0H4N6QSN"
  },
  "ux": {
    "state": "reconfirm_required",
    "severity": "warning",
    "title": "영향 범위가 변경되어 다시 확인이 필요합니다.",
    "primary_action": "review_updated_preview",
    "confirm_label": "새 미리보기 기준으로 다시 확인",
    "disable_original_confirm": true
  },
  "audit": {
    "submitted_preview_id": "prev_01HR7J9YB3M8JY4A7Q",
    "submitted_graph_snapshot_id": "graph_01HR7J9ZZ4K5D4CX2D",
    "current_graph_snapshot_id": "graph_01HR7JCG7VQ0D11S9F"
  }
}
```

### 3. preview가 만료되어 다시 계산부터 해야 하는 경우

```json
{
  "confirm_state": "stale",
  "reason_code": "preview_expired",
  "forced_reconfirm": false,
  "checked_at": "2026-04-14T11:06:14Z",
  "submitted_preview": {
    "preview_id": "prev_01HR7J9YB3M8JY4A7Q",
    "graph_snapshot_id": "graph_01HR7J9ZZ4K5D4CX2D",
    "expires_at": "2026-04-14T11:05:03Z"
  },
  "current_evaluation": {
    "graph_snapshot_id": null,
    "drift_class": "unknown"
  },
  "replacement_preview": null,
  "ux": {
    "state": "preview_expired",
    "severity": "warning",
    "title": "미리보기 유효 시간이 지났습니다.",
    "primary_action": "recompute_preview",
    "disable_original_confirm": true
  },
  "audit": {
    "submitted_preview_id": "prev_01HR7J9YB3M8JY4A7Q",
    "submitted_graph_snapshot_id": "graph_01HR7J9ZZ4K5D4CX2D"
  }
}
```

---

## 체크리스트

1. confirm body가 `graph_snapshot_drifted`와 `preview_expired`를 구분하는가
2. stale 응답에서도 `submitted_preview`가 그대로 남는가
3. replacement preview를 낼 때 새 `preview_id`, 새 `graph_snapshot_id`, 새 `confirm_token`, 새 `expires_at`를 발급하는가
4. `ux.state`가 `drift_detected`, `preview_expired`, `reconfirm_required`로 고정돼 있는가
5. high-risk revoke에서 snapshot drift를 silent auto-accept하지 않는가
6. audit가 submitted/current snapshot id를 둘 다 남기는가

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 고르는가 |
|---|---|---|---|
| stale 시 separate preview API로만 재조회 | 구현이 단순하다 | client round-trip이 늘고 modal continuity가 떨어진다 | low-risk internal tooling |
| stale 응답에 replacement preview를 inline 포함 | operator 흐름이 덜 끊긴다 | confirm endpoint 책임이 커진다 | AOBO, support revoke, high-value account tooling |
| snapshot drift가 `same_effect`면 자동 진행 | 클릭 수를 줄인다 | membership 변화를 놓칠 수 있다 | low-risk, single-session revoke |
| 어떤 drift든 강제 재확인 | 보수적이고 audit 해석이 쉽다 | operator friction이 증가한다 | AOBO, break-glass, tenant-wide revoke |

## 꼬리질문

> Q: `graph_snapshot_id`만 바뀌고 count가 같으면 그냥 실행해도 되지 않나요?
> 의도: count equality와 semantic equality를 구분하는지 확인
> 핵심: 아니다. membership가 바뀌었을 수 있고, high-risk revoke는 같은 count라도 강제 재확인이 기본값이어야 한다.

> Q: preview 만료 시 자동으로 새 preview를 끼워 넣으면 UX가 더 부드럽지 않나요?
> 의도: operator 동의의 증거를 보존하는지 확인
> 핵심: 새 preview를 inline 제공할 수는 있지만, old confirm을 재사용하면 안 된다. 새 preview 기준의 명시적 재확인이 필요하다.

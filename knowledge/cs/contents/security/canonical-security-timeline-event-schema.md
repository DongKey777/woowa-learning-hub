---
schema_version: 3
title: Canonical Security Timeline Event Schema
concept_id: security/canonical-security-timeline-event-schema
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- canonical security timeline event schema
- support access event schema
- security timeline schema
- support timeline contract
aliases:
- canonical security timeline event schema
- support access event schema
- security timeline schema
- support timeline contract
- access group id
- case ref
- case reference
- support case reference
- break glass timeline schema
- support access lifecycle event
- timeline status transition
- timeline retention class
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/support-operator-acting-on-behalf-of-controls.md
- contents/security/customer-facing-support-access-notifications.md
- contents/security/audience-matrix-for-support-access-events.md
- contents/security/tenant-policy-schema-for-privileged-support-alerts.md
- contents/security/aobo-start-end-event-contract.md
- contents/security/operator-tooling-state-semantics-safety-rails.md
- contents/security/emergency-grant-cleanup-metrics.md
- contents/security/aobo-revocation-audit-event-schema.md
- contents/security/authz-kill-switch-break-glass-governance.md
- contents/security/audit-logging-auth-authz-traceability.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Canonical Security Timeline Event Schema 핵심 개념을 설명해줘
- canonical security timeline event schema가 왜 필요한지 알려줘
- Canonical Security Timeline Event Schema 실무 설계 포인트는 뭐야?
- canonical security timeline event schema에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Canonical Security Timeline Event Schema를 다루는 deep_dive 문서다. support AOBO와 break-glass 보안 타임라인은 surface마다 제각각 payload를 만들면 안 되며, `case_ref`, `access_group_id`, append-only status transition, `retention_class`를 공유하는 canonical event schema 위에서 customer/admin/security projection이 갈라져야 한다. 검색 질의가 canonical security timeline event schema, support access event schema, security timeline schema, support timeline contract처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Canonical Security Timeline Event Schema

> 한 줄 요약: support AOBO와 break-glass 보안 타임라인은 surface마다 제각각 payload를 만들면 안 되며, `case_ref`, `access_group_id`, append-only status transition, `retention_class`를 공유하는 canonical event schema 위에서 customer/admin/security projection이 갈라져야 한다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **support access timeline용 shared event schema, traceability key, status transition, retention class contract**를 설명하는 focused deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md)
> - [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)
> - [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md)
> - [Tenant Policy Schema for Privileged Support Alerts](./tenant-policy-schema-for-privileged-support-alerts.md)
> - [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md)
> - [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)
> - [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md)
> - [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)
> - [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)

retrieval-anchor-keywords: canonical security timeline event schema, support access event schema, security timeline schema, support timeline contract, access group id, case ref, case reference, support case reference, break glass timeline schema, support access lifecycle event, timeline status transition, timeline retention class, customer traceability schema, delegated access timeline schema, support access start end schema, aobo start end event contract, delegated support access end event schema, customer timeline projection rules, access group id vs grant id, timeline projector contract, emergency access timeline event, preview id revocation request id timeline evidence ref, aobo revocation audit event schema, break glass revoke timeline join, tenant policy schema for privileged support alerts, policy snapshot id, audience policy key, managed identity escalation, compliance-sensitive support event

## 이 문서 다음에 보면 좋은 문서

- customer-facing copy, privacy-safe field projection, inbox/email/timeline 역할 분리는 [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)로 이어진다.
- affected user, tenant admin, security contact routing은 [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md)에서 이어진다.
- `audience_policy_key`, `policy_snapshot_id`, compliance-sensitive retention override를 tenant 설정에서 어떻게 계산할지는 [Tenant Policy Schema for Privileged Support Alerts](./tenant-policy-schema-for-privileged-support-alerts.md)로 이어진다.
- canonical `support_access_started` / `support_access_ended` pair와 customer timeline close semantics는 [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md)에서 더 집중해서 본다.
- operator mode, AOBO grant, break-glass lease 제약은 [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md), [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)를 같이 보면 된다.
- preview, confirm, propagation status가 timeline evidence ref로 어떻게 이어지는지는 [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)로 이어진다.
- cleanup lag, `cleanup_confirmed`, end-event 누락 탐지는 [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md)에서 이어서 본다.

---

## 핵심 개념

support access timeline에서 흔한 실패는 "알림 copy", "타임라인 row", "내부 audit join key"를 한 번에 뭉개는 것이다.

좋은 설계는 세 층을 분리한다.

- 내부 raw audit/event: operator id, approval id, grant id, policy evidence를 충분히 담는 내부 증거
- canonical timeline event: customer/admin/security projection이 공통으로 쓰는 shared schema
- audience projection: 같은 canonical event를 audience별 redaction과 delivery 규칙으로 표현한 surface row

이때 canonical schema의 핵심 축은 네 가지다.

- `case_ref`: 사람과 support가 대화할 때 쓰는 stable reference
- `access_group_id`: 하나의 support access lifecycle을 묶는 machine-stable key
- `status_transition`: `started`, `ended`, `expired` 같은 상태 전이를 append-only로 남기는 계약
- `retention_class`: 이 row를 timeline에서 얼마나 오래 보관하고 export해야 하는지 정하는 정책 키

즉 타임라인 설계의 핵심은 "한 줄 copy"가 아니라, **같은 사건을 여러 surface와 review 흐름에서 일관되게 재구성할 수 있는 공통 식별자와 lifecycle contract**를 고정하는 데 있다.

---

## 깊이 들어가기

### 1. event row와 access group summary를 분리해야 한다

timeline은 보통 한 줄 row처럼 보이지만, 저장 모델은 append-only event가 더 안전하다.

- event row: 실제로 발생한 전이 하나를 기록한다
- access group summary: 같은 `access_group_id`의 최신 event를 모아 현재 상태를 계산한다

이렇게 나누면 좋은 점:

- 시작/종료/만료/강제 종료를 덮어쓰지 않고 모두 남길 수 있다
- customer timeline은 최신 상태 badge만 보여 주고, dispute 시에는 전체 history를 재구성할 수 있다
- projector bug가 나도 원본 event를 기준으로 다시 materialize할 수 있다

반대로 안 좋은 패턴:

- 시작 row를 나중에 in-place update해서 종료 사실만 덮는다
- `closed=true` 하나만 두고 ended/expired/revoked를 구분하지 않는다
- email copy와 timeline row id를 같은 키로 쓴다

### 2. `case_ref`, `access_group_id`, `grant_id`는 서로 다른 질문에 답해야 한다

이 셋을 섞으면 traceability가 바로 깨진다.

| 키 | 의미 | 재사용 규칙 | 왜 필요한가 |
|---|---|---|---|
| `case_ref` | support case, ticket, incident처럼 사람이 말하는 reference | 여러 access group이 같은 `case_ref`를 공유할 수 있다 | support conversation, customer dispute, admin review를 같은 사건으로 묶기 위해 필요하다 |
| `access_group_id` | 하나의 delegated access lifecycle을 묶는 canonical group key | 같은 lifecycle의 start/end/cleanup event가 모두 공유한다 | timeline row, start/end pair, current badge를 안정적으로 묶기 위해 필요하다 |
| `grant_id` | 내부 allow path나 lease registry에서 쓰는 execution key | renewal이나 reissue 때 바뀔 수 있다 | backend revoke, cache invalidation, audit forensic join에 필요하다 |

권장 규칙:

- read-only inspection 하나가 시작되고 끝날 때는 같은 `access_group_id`를 쓴다
- 같은 `case_ref`라도 read-only AOBO에서 write-capable AOBO로 승격되면 새 `access_group_id`를 발급한다
- `grant_id`는 projector 바깥으로 새지 않게 두고, 필요한 경우 `evidence_ref`로만 간접 노출한다

즉 `case_ref`는 사람용 사건 키, `access_group_id`는 timeline lifecycle 키, `grant_id`는 내부 실행 키다.

### 3. schema minimum set은 "누가, 무엇을, 어떤 lifecycle로, 얼마나 오래 남길 것인가"를 모두 담아야 한다

support access timeline의 canonical event는 최소한 아래 영역을 가져야 한다.

| 영역 | 필드 | 설명 |
|---|---|---|
| envelope | `schema_version`, `event_id`, `event_type`, `occurred_at`, `producer` | 어떤 버전의 projector/producer가 어떤 종류의 전이를 언제 기록했는지 설명한다 |
| access kind | `access_kind`, `reason_category`, `scope_class`, `scope_summary` | read-only AOBO인지, write AOBO인지, break-glass인지와 어떤 surface를 건드렸는지 구분한다 |
| traceability | `case_ref`, `access_group_id`, `tenant_id`, `subject_user_id` | support case와 timeline row를 사람/시스템 모두가 다시 찾을 수 있게 한다 |
| lifecycle | `from_status`, `to_status`, `expires_at`, `ended_at`, `cleanup_confirmed_at` | 현재 row가 왜 active인지, 왜 닫혔는지, cleanup까지 끝났는지 설명한다 |
| policy | `audience_policy_key`, `delivery_class`, `retention_class` | 어떤 audience와 surface로 가야 하고 얼마나 오래 남겨야 하는지 결정한다 |
| evidence join | `approval_id`, `ticket_id`, `incident_id`, `grant_id`, `audit_event_id` | raw audit와 cleanup metric, post-incident review를 같은 흐름으로 묶는다 |

주의할 점:

- `scope_summary`는 privacy-safe surface text에 가까운 축약 설명이어야 한다
- operator 개인 이메일, source IP, internal console path는 canonical timeline event에 직접 넣지 않는 편이 안전하다
- customer-visible copy는 `scope_summary`, `reason_category`, `case_ref`를 조합해 만들고, 내부 evidence는 `evidence join` 필드로 이어 붙인다

### 4. status transition은 generic `closed`가 아니라 명시적 terminal state를 가져야 한다

support access timeline은 `is_active` 하나로 운영하면 안 된다.  
종료 이유 자체가 security meaning을 가지기 때문이다.

권장 상태 집합:

- `requested`: 내부 준비 상태. customer/admin timeline에는 보통 안 보인다
- `approved`: approval은 끝났지만 아직 operator lease가 active는 아닌 상태
- `active`: 실제 delegated access가 열려 있는 상태
- `ended`: 정상 종료
- `expired`: hard TTL 만료로 종료
- `revoked`: operator 또는 system이 강제 종료
- `cleanup_confirmed`: cache, delegated session, projector tail까지 닫혔음이 확인된 상태

권장 전이 규칙:

- `requested -> approved -> active`
- `active -> ended`
- `active -> expired`
- `active -> revoked`
- `ended|expired|revoked -> cleanup_confirmed`

추가 rule:

- `active -> active`는 허용하되, 이 경우 `transition_reason=scope_changed|ttl_extended|audience_repaired` 같은 이유 코드를 같이 남긴다
- `closed` 같은 뭉뚱그린 상태는 쓰지 않는다
- `cleanup_confirmed`는 새로운 access 종료 이유가 아니라, 종료 이후 forensic tail까지 닫혔다는 별도 확인 상태다

즉 timeline badge는 `to_status`를 따라가고, dispute/review는 전체 전이 chain을 따라간다.

### 5. retention class는 delivery와 분리한 policy key여야 한다

즉시 email을 보냈다고 해서 timeline retention이 길어지는 것은 아니다.  
반대로 timeline에 오래 남겨도 push/email는 짧게 끝날 수 있다.

권장 baseline retention class:

| `retention_class` | 대상 | 기본 의미 |
|---|---|---|
| `timeline_standard_90d` | read-only AOBO, low-risk account inspection | 종료 시점 기준 최소 90일 timeline 보관 |
| `timeline_extended_180d` | write-capable AOBO, account security state change | 종료 시점 기준 최소 180일 보관, admin review/export를 고려 |
| `timeline_regulated_365d_exportable` | break-glass, tenant-wide privileged action, compliance-sensitive support access | 최소 365일 또는 규제 기준, export/audit handoff 가능 |

추가 원칙:

- `retention_class`는 event마다 찍되, access group summary는 가장 긴 class를 승계한다
- 같은 `access_group_id` 안에서 read-only가 write-capable로 승격되면 더 긴 class로 재분류한다
- internal audit retention은 이보다 더 길 수 있지만, canonical timeline schema의 `retention_class`는 customer/admin/security timeline obligation을 뜻한다

즉 retention은 "메시지를 얼마나 오래 unread로 둘 것인가"가 아니라, **timeline evidence를 언제까지 self-serve 또는 export 가능하게 유지할 것인가**를 뜻한다.

### 6. audience routing은 schema 밖에서 결정하되, schema는 그 결정을 설명할 수 있어야 한다

event schema가 audience routing을 직접 하지는 않지만, routing에 필요한 policy key는 들고 있어야 한다.

유용한 최소 필드:

- `audience_policy_key`: `b2c_user_only`, `b2b_user_admin`, `b2b_admin_security` 같은 분기 키
- `delivery_class`: `timeline_only`, `immediate_plus_timeline`
- `visibility_scope`: `affected_user`, `tenant_admin`, `security_contact`, `internal_only`

이렇게 두면:

- [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md)의 routing 규칙을 projector에서 재사용할 수 있고
- customer timeline, tenant admin inbox, security export가 같은 사건을 다른 visibility로 보여 줄 수 있고
- projection bug가 나도 canonical row에서 의도한 audience class를 검증할 수 있다

### 7. projector repair와 cleanup verification도 event schema에 포함돼야 한다

support access timeline은 나중에 고쳐질 일이 많다.

예:

- end event는 들어왔는데 customer projector가 밀렸다
- break-glass revoke는 됐지만 cleanup confirmation이 늦다
- tenant admin routing policy가 뒤늦게 수정됐다

그래서 event schema는 "시작/종료"만이 아니라 repair 가능한 trace도 남겨야 한다.

유용한 필드:

- `source_event_id`
- `repair_reason`
- `projector_version`
- `coverage`: `full|partial`

중요한 점:

- projector repair는 기존 event를 조용히 수정하지 말고, 새 event 또는 repair audit를 남기는 편이 안전하다
- `cleanup_confirmed_at`이 비어 있으면 terminal state여도 후속 cleanup metric에서 미완료로 볼 수 있다
- `coverage=partial`이면 UI count나 export completeness를 과신하지 말아야 한다

---

## 실전 시나리오

### 시나리오 1: 같은 support case 안에서 read-only 확인 후 MFA reset까지 이어진다

좋은 모델:

- `case_ref=CASE-1842`는 유지한다
- read-only inspection은 `access_group_id=ag_01_read`
- MFA reset용 write AOBO는 `access_group_id=ag_02_write`
- 두 group 모두 같은 case에 묶이지만, timeline row와 retention class는 별도로 계산한다

피해야 할 모델:

- 같은 case라는 이유로 read/write를 하나의 group에 섞는다
- retention을 짧은 read-only class에 맞춰 버린다

### 시나리오 2: break-glass가 시작됐는데 종료는 hard expiry로 닫혔다

좋은 모델:

- 시작 event는 `to_status=active`
- TTL 만료 event는 `to_status=expired`
- regional cache와 delegated session 정리가 끝난 뒤 `to_status=cleanup_confirmed`를 추가한다

피해야 할 모델:

- 만료와 cleanup confirmation을 같은 `closed` row로 뭉갠다
- customer timeline에는 종료됨으로 보이지만 cleanup metric은 아직 active인 상태를 만들고도 join key가 없다

### 시나리오 3: support end event가 customer timeline에 누락됐다

좋은 모델:

- canonical schema에는 이미 `access_group_id`와 terminal transition이 남아 있다
- projector는 같은 group id를 기준으로 missing end row를 복구한다
- repair 후에도 `source_event_id`와 `projector_version`을 남겨 postmortem에서 원인을 재구성한다

피해야 할 모델:

- email 발송 성공 여부만 보고 timeline row도 끝났다고 가정한다
- access group 없이 free-form case note로만 종료 사실을 남긴다

---

## 코드로 보기

### 1. canonical event payload 예시

```json
{
  "schema_version": "2026-04-14",
  "event_id": "stev_01JRQ2M0NB4R8CZ8A6",
  "event_type": "support_access_ended",
  "occurred_at": "2026-04-14T10:58:22Z",
  "producer": "support-access-projector",
  "access_kind": "AOBO_WRITE",
  "reason_category": "ACCOUNT_RECOVERY",
  "scope_class": "USER_SECURITY_STATE",
  "scope_summary": "MFA setting reset for account access recovery",
  "case_ref": "CASE-1842",
  "access_group_id": "ag_01JRQ2KQY3M1CY0C0M",
  "tenant_id": "tenant_9",
  "subject_user_id": "user_123",
  "from_status": "active",
  "to_status": "ended",
  "ended_at": "2026-04-14T10:58:22Z",
  "expires_at": "2026-04-14T11:05:00Z",
  "retention_class": "timeline_extended_180d",
  "audience_policy_key": "b2b_user_admin",
  "delivery_class": "immediate_plus_timeline",
  "approval_id": "apr_77",
  "ticket_id": "SUP-991",
  "grant_id": "grant_44",
  "audit_event_id": "audit_8121"
}
```

`access_kind`와 `event_type`을 같이 두면 "무슨 종류의 access였는가"와 "이번 row가 어떤 전이였는가"를 분리할 수 있다.

### 2. access group 상태 계산 예시

```java
public enum TimelineStatus {
    REQUESTED,
    APPROVED,
    ACTIVE,
    ENDED,
    EXPIRED,
    REVOKED,
    CLEANUP_CONFIRMED
}

public record TimelineEvent(
        String eventId,
        String caseRef,
        String accessGroupId,
        TimelineStatus fromStatus,
        TimelineStatus toStatus,
        String retentionClass,
        Instant occurredAt
) {
}

public TimelineStatus currentStatus(List<TimelineEvent> events) {
    return events.stream()
            .max(Comparator.comparing(TimelineEvent::occurredAt))
            .orElseThrow()
            .toStatus();
}
```

### 3. group rotation rule 예시

```text
1. 같은 case라도 scope class가 user -> tenant-wide로 넓어지면 새 access_group_id를 발급한다
2. 같은 case라도 read-only -> write-capable로 승격되면 새 access_group_id를 발급한다
3. 같은 access_group_id 안에서는 retention class를 더 짧게 내리지 않는다
4. cleanup_confirmed는 terminal transition 뒤에만 허용한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| surface별 bespoke timeline payload | 구현이 빠르다 | case ref, group id, retention semantics가 금방 어긋난다 | 임시 프로토타입 |
| canonical event + audience projector | traceability와 재처리가 강하다 | schema 설계와 projector 비용이 든다 | support access가 잦거나 규제/신뢰 요구가 큰 서비스 |
| `case_ref`만 공유하고 group id는 없음 | support conversation은 쉽다 | start/end pair, multi-grant lifecycle 복원이 약하다 | 단일 read-only support action만 있는 아주 단순한 서비스 |
| `grant_id`를 UI key로 그대로 사용 | backend join은 쉽다 | renewal/reissue 때 timeline 의미가 흔들린다 | 권장하지 않음 |

판단 기준은 이렇다.

- 같은 support case 안에서 여러 delegated access가 생길 수 있는가
- start/end/expiry/cleanup을 서로 다른 시스템이 기록하는가
- customer/admin/security contact가 같은 사건을 다른 surface에서 보게 되는가
- retention과 export 정책이 risk level에 따라 달라지는가

---

## 꼬리질문

> Q: `case_ref`와 `access_group_id`를 왜 둘 다 두나요?
> 의도: 사람용 사건 reference와 machine lifecycle key를 구분하는지 확인
> 핵심: case는 support conversation용, access group은 start/end/cleanup lifecycle용이다.

> Q: 종료 상태를 왜 `closed` 하나로 두면 안 되나요?
> 의도: ended/expired/revoked가 다른 security 의미를 가진다는 점을 이해하는지 확인
> 핵심: dispute, cleanup metric, forensic에서 종료 이유 자체가 중요하기 때문이다.

> Q: retention class는 inbox TTL과 같은가요?
> 의도: delivery retention과 timeline evidence retention을 구분하는지 확인
> 핵심: 아니다. retention class는 timeline evidence와 export obligation을 뜻한다.

> Q: 같은 support case에서 read-only 후 write가 이어지면 group을 재사용하나요?
> 의도: lifecycle scope와 risk escalation을 구분하는지 확인
> 핵심: 아니다. risk와 scope가 달라지면 새 `access_group_id`를 발급하는 편이 안전하다.

## 한 줄 정리

support access 보안 타임라인은 `case_ref`, `access_group_id`, 명시적 상태 전이, `retention_class`를 공유하는 canonical event schema가 먼저 있어야 audience routing과 customer copy, cleanup review가 서로 어긋나지 않는다.

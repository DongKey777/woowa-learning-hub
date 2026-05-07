---
schema_version: 3
title: Support Operator / Acting-on-Behalf-Of Controls
concept_id: security/support-operator-acting-on-behalf-of-controls
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- support impersonation
- acting on behalf of
- operator controls
- customer support access
aliases:
- support impersonation
- acting on behalf of
- operator controls
- customer support access
- assisted support session
- delegated operator action
- actor subject audit
- step-up operator action
- support admin governance
- operator tooling semantics
- session inventory support access
- delegated access timeline
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/delegated-admin-tenant-rbac.md
- contents/security/workload-identity-user-context-propagation-boundaries.md
- contents/security/step-up-session-coherence-auth-assurance.md
- contents/security/session-quarantine-partial-lockdown-patterns.md
- contents/security/session-inventory-ux-revocation-scope-design.md
- contents/security/customer-facing-support-access-notifications.md
- contents/security/audience-matrix-for-support-access-events.md
- contents/security/operator-tooling-state-semantics-safety-rails.md
- contents/security/emergency-grant-cleanup-metrics.md
- contents/security/audit-logging-auth-authz-traceability.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Support Operator / Acting-on-Behalf-Of Controls 핵심 개념을 설명해줘
- support impersonation가 왜 필요한지 알려줘
- Support Operator / Acting-on-Behalf-Of Controls 실무 설계 포인트는 뭐야?
- support impersonation에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Support Operator / Acting-on-Behalf-Of Controls를 다루는 deep_dive 문서다. 고객 지원이나 운영 도구에서 acting-on-behalf-of를 허용할 때는 단순 impersonation이 아니라 operator identity, subject identity, step-up, scope, recording을 함께 묶어야 안전하게 운영할 수 있다. 검색 질의가 support impersonation, acting on behalf of, operator controls, customer support access처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Support Operator / Acting-on-Behalf-Of Controls

> 한 줄 요약: 고객 지원이나 운영 도구에서 acting-on-behalf-of를 허용할 때는 단순 impersonation이 아니라 operator identity, subject identity, step-up, scope, recording을 함께 묶어야 안전하게 운영할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [Workload Identity / User Context Propagation Boundaries](./workload-identity-user-context-propagation-boundaries.md)
> - [Step-Up Session Coherence / Auth Assurance](./step-up-session-coherence-auth-assurance.md)
> - [Session Quarantine / Partial Lockdown Patterns](./session-quarantine-partial-lockdown-patterns.md)
> - [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
> - [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)
> - [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md)
> - [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)
> - [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
> - [Security README: Browser / Session Coherence](./README.md#browser--session-coherence)

retrieval-anchor-keywords: support impersonation, acting on behalf of, operator controls, customer support access, assisted support session, delegated operator action, actor subject audit, step-up operator action, support admin governance, operator tooling semantics, session inventory support access, delegated access timeline, support access notification, customer traceability support event, browser session coherence, session boundary bridge, ordinary session inventory vs support timeline

---

## 핵심 개념

support operator가 고객 문제를 재현하거나 대신 작업해야 하는 경우가 있다.  
이때 흔한 실수는 이것을 단순 impersonation 기능으로 만드는 것이다.

실제로는 더 많은 경계가 필요하다.

- operator는 누구인가
- 어떤 customer/tenant만 볼 수 있는가
- read만 가능한가, write도 가능한가
- step-up이 필요한가
- acting-on-behalf-of 사실이 모든 로그와 audit에 남는가

즉 이 기능의 본질은 "다른 사용자처럼 보이기"가 아니라, operator와 subject를 분리해 대리 행위를 통제하는 것이다.

---

## 깊이 들어가기

### 1. operator identity와 subject identity를 섞으면 안 된다

필요한 최소 구분:

- actor/operator: 실제로 버튼을 누른 사람
- subject/customer: 대신 작업 대상인 계정
- workload/tool: 어떤 내부 도구를 통해 실행됐는가

이 셋이 분리되지 않으면:

- 고객이 직접 한 일처럼 보인다
- support 남용을 탐지하기 어렵다
- postmortem과 법적 추적이 힘들다

### 2. read-only와 write-capable acting-on-behalf-of는 분리해야 한다

많은 지원 작업은 read-only로 충분하다.

- 계정 상태 확인
- 설정 조회
- 에러 재현

반면 write는 훨씬 위험하다.

- 정보 수정
- 환불/취소
- 보안 설정 초기화

그래서 보통:

- read-on-behalf-of
- write-on-behalf-of

를 다른 grant로 나누는 편이 안전하다.

### 3. operator action에는 별도의 step-up이 자연스럽다

고객 대신 행동하는 것은 평소보다 위험하다.

그래서 자주 쓰는 패턴:

- operator 기본 세션과 별도 elevated grant
- strong auth 재확인
- ticket id / approval id 요구
- 짧은 TTL

즉 support 도구는 일반 admin보다도 더 강한 assurance가 필요할 수 있다.

### 4. scope는 tenant, action, duration 세 축으로 제한한다

안전한 AOBO(acting on behalf of) grant 예:

- tenant `t-123`만
- `billing.read`만
- 15분 동안만

위험한 패턴:

- any user, any tenant, any action
- 만료 없음

이는 사실상 숨겨진 슈퍼관리자다.

### 5. UI/UX도 대리 상태를 강하게 드러내야 한다

운영자 스스로도 현재 상태를 잊기 쉽다.

필요한 것:

- 화면 상단 banner
- 현재 subject 표시
- 남은 TTL 표시
- 종료 버튼

보안 기능은 서버 정책만 아니라 사람의 실수 방지까지 포함한다.

### 6. session inventory와 support access timeline도 의미를 분리해야 한다

support AOBO를 고객 세션과 같은 줄에 섞으면 안 된다.

예를 들어 고객 보안 화면에서:

- ordinary device session
- support read-only inspection
- support write AOBO

가 모두 `Chrome / Seoul`처럼만 보이면 사용자는 무엇이 자기 로그인이고 무엇이 지원 개입인지 알 수 없다.

그래서 좋은 projection은 아래 둘 중 하나다.

- 일반 session inventory와 별도 support access timeline
- 같은 inventory를 쓰더라도 `support access`, `delegated action` 같은 badge와 operator/ticket 정보를 함께 노출

즉 AOBO는 권한 제어뿐 아니라 "사람이 어떻게 보게 할 것인가"까지 포함해야 한다.

### 7. 민감 작업은 dual-control 또는 explicit confirmation이 유용하다

예:

- 계정 비활성화
- MFA reset
- 환불/출금 취소
- 권한 부여

이런 작업은:

- second approver
- explicit reason code
- screen recording or command recording

같은 추가 통제가 자연스럽다.

### 8. session quarantine와 연결하면 오탐 대응이 쉬워진다

operator 세션 자체가 이상 신호를 띠면:

- 즉시 전부 종료 대신
- write-on-behalf-of만 막고
- read-only로 quarantine
- 새 step-up 후 복구

같은 단계적 통제가 가능하다.

### 9. audit와 customer-facing traceability를 함께 봐야 한다

내부에는 필요하다.

- operator id
- subject id
- tool id
- reason code
- scope
- before/after 상태

경우에 따라 고객에게도 "support access occurred" 이벤트를 보여 줄 수 있다.

이때 고객-facing copy, timeline retention, privacy-safe projection 원칙은 [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)에서 별도로 다루고, affected user / tenant admin / security contact 분기 기준은 [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md)로 분리하는 편이 좋다.

---

## 실전 시나리오

### 시나리오 1: support가 고객 대신 settings를 변경했는데 audit에는 고객 id만 남는다

문제:

- actor와 subject가 섞였다

대응:

- operator, subject, tool 세 필드를 분리한다
- 모든 side effect log에 acting-on-behalf-of를 명시한다

### 시나리오 2: support 도구가 영구적인 write 권한을 가진다

문제:

- 예외 권한이 상시 권한이 됐다

대응:

- time-boxed grant로 바꾼다
- write-on-behalf-of는 strong auth와 approval을 요구한다
- read-only와 write grant를 분리한다

### 시나리오 3: operator 세션에서 이상 신호가 발생하지만 업무 중단이 너무 크다

문제:

- revoke와 계속 허용 사이 선택지가 없다

대응:

- read-only quarantine을 도입한다
- write-on-behalf-of만 차단한다
- step-up과 approval 후에만 다시 풀어 준다

---

## 코드로 보기

### 1. acting-on-behalf-of grant 예시

```java
public record ActingOnBehalfGrant(
        String operatorId,
        String subjectUserId,
        String tenantId,
        String scope,
        Instant expiresAt,
        String approvalId
) {
}
```

### 2. audit 필드 예시

```text
actor_operator_id
subject_user_id
tool_id
scope
reason_code
approval_id
```

### 3. 운영 체크리스트

```text
1. actor/operator, subject/customer, tool/workload가 구분되는가
2. read-on-behalf-of와 write-on-behalf-of가 분리되는가
3. write capability에 strong auth와 approval이 필요한가
4. banner, TTL, 종료 버튼처럼 UI에서 대리 상태가 강하게 드러나는가
5. support access가 ordinary user session과 분리돼 보이는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| full impersonation | 구현이 단순하다 | audit와 오남용 통제가 약하다 | 가능하면 피한다 |
| read-only AOBO | 리스크가 낮다 | 일부 문제 해결에는 부족하다 | 일반 support 진단 |
| scoped write AOBO | 운영 복구에 유용하다 | 승인과 통제가 필요하다 | 환불, 설정 복구, 보안 지원 |
| break-glass support override | 긴급 대응이 가능하다 | 남용 위험이 높다 | 매우 제한된 incident 대응 |

판단 기준은 이렇다.

- operator가 실제로 write가 필요한가
- 고객/tenant 범위를 좁힐 수 있는가
- strong auth와 approval을 결합할 수 있는가
- acting-on-behalf-of 사실을 end-to-end audit에 남길 수 있는가

---

## 꼬리질문

> Q: support impersonation과 acting-on-behalf-of의 차이는 무엇인가요?
> 의도: 단순 변장과 명시적 대리 행위를 구분하는지 확인
> 핵심: AOBO는 operator identity를 숨기지 않고, subject를 대신한다는 사실을 명시적으로 남긴다.

> Q: 왜 read와 write를 분리해야 하나요?
> 의도: 대리 행위의 리스크 차이를 이해하는지 확인
> 핵심: 많은 지원 작업은 읽기로 충분하고, write는 훨씬 큰 위험과 승인 요구를 가진다.

> Q: acting-on-behalf-of에도 step-up이 필요한가요?
> 의도: 운영자 권한도 민감 작업이면 assurance가 필요함을 이해하는지 확인
> 핵심: 그렇다. 특히 고객 설정 변경, 보안 초기화, 환불 같은 작업은 강한 재확인이 자연스럽다.

> Q: 왜 UI banner 같은 사람 중심 장치가 중요한가요?
> 의도: 인간 오퍼레이터 실수까지 보안 범위로 보는지 확인
> 핵심: 운영자 자신이 현재 대리 상태를 잊지 않게 만들어 오작동을 줄여 주기 때문이다.

## 한 줄 정리

Support acting-on-behalf-of의 핵심은 고객처럼 위장하는 것이 아니라, operator와 subject를 끝까지 분리한 채 시간과 범위가 제한된 대리 권한을 강한 audit와 step-up 위에서 운영하는 것이다.

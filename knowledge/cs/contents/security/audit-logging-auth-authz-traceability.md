# Audit Logging for Auth / AuthZ Traceability

> 한 줄 요약: auth/authz audit log는 장애 진단 로그가 아니라 "누가 어떤 권한으로 무엇을 시도했는가"를 재구성하는 증거 레이어다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [로그 마스킹 기초: Authorization 헤더와 에러 로그는 어디까지 가려야 하나](./log-masking-basics.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
> - [Secret Scanning / Credential Leak Response](./secret-scanning-credential-leak-response.md)
> - [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [AuthZ Decision Logging Design](./authz-decision-logging-design.md)
> - [SCIM Drift / Reconciliation](./scim-drift-reconciliation.md)
> - [System Design: Session Store / Claim-Version Cutover 설계](../system-design/session-store-claim-version-cutover-design.md)

retrieval-anchor-keywords: audit log, auth log, authz traceability, actor action resource, denied access, security event, immutable log, forensics, principal, correlation id, compliance, security telemetry, claim schema version, store generation, reconciliation run id, directory event id, cleanup evidence, retirement evidence, deprovision proof, log masking, authorization header masking, token redaction, secret redaction

---

## 핵심 개념

auth/authz audit log는 누가 로그인했고, 어떤 권한으로, 어떤 자원에, 어떤 결과를 냈는지 추적하는 기록이다.
애플리케이션 debug log와 달리, audit log는 보안과 규제 대응을 위한 증거로 설계해야 한다.

핵심 질문:

- 누가 시도했는가
- 어떤 principal이었는가
- 어떤 resource를 향했는가
- 허용/거부 이유는 무엇이었는가
- 어떤 session / token / policy version이었는가

즉 audit log는 "나중에 기억하려는 로그"가 아니라 "사고 때 증명하려는 데이터"다.

---

## 깊이 들어가기

### 1. auth log와 authz log는 다르다

- `auth log`: login, logout, MFA, token issuance, token refresh 같은 인증 이벤트
- `authz log`: permission check, deny, allow, policy decision 같은 인가 이벤트

둘을 섞으면 원인 추적이 어려워진다.

### 2. deny를 꼭 기록해야 한다

권한이 있는 요청보다 없는 요청이 더 중요할 때가 많다.

- IDOR 시도
- brute force
- 계정 탈취 후 lateral movement
- admin endpoint probing

deny 로그는 공격 신호다.

### 3. 민감 정보는 남기면 안 된다

audit log는 길게 보관하지만, credential을 포함하면 안 된다.

- token 전체
- password
- secret
- full PII

필요한 경우 식별자만 남기고 마스킹한다.

### 4. correlation id와 principal id가 필요하다

장애와 사고를 엮으려면 다음이 필요하다.

- `request_id`
- `session_id`
- `user_id`
- `tenant_id`
- `policy_version`
- `resource_id`

이렇게 해야 허용/거부 경로를 재구성할 수 있다.

### 5. cleanup proof를 위해 lifecycle/decision join key를 남겨야 한다

SCIM reconciliation 이후 old claim/store를 retire하려면
"누가 아직 접근했는가"뿐 아니라
"그 접근이 어느 directory change, 어느 session generation, 어느 policy decision과 연결됐는가"를 다시 조인할 수 있어야 한다.

특히 authority transfer cleanup에서는 아래 키가 자주 필요하다.

- `directory_event_id`, `reconciliation_run_id`
- `session_id`, `refresh_family_id`
- `claim_schema_version`, `store_generation`
- `policy_version`, `authz_epoch`
- `request_id`, `trace_id`

이 필드는 하나의 거대한 audit row에 몰아넣으라는 뜻이 아니다.
auth/authz event stream, reconciliation artifact, cutover gate artifact를 분리해도 되지만,
적어도 [AuthZ Decision Logging Design](./authz-decision-logging-design.md)과
[Session Store / Claim-Version Cutover 설계](../system-design/session-store-claim-version-cutover-design.md)가 요구하는 join key는 유지돼야 한다.

### 6. immutable이 중요하다

audit log는 삭제/수정이 쉬우면 의미가 없다.

- append-only
- tamper-evident
- retention policy
- access control

이런 성질이 있어야 forensic 용도로 쓸 수 있다.

---

## 실전 시나리오

### 시나리오 1: 관리자 권한이 남용된 흔적을 찾아야 함

대응:

- admin login / logout / action events를 묶는다
- resource와 actor를 같이 본다
- policy version을 확인한다

### 시나리오 2: 유출된 token으로 어떤 자원이 접근됐는지 봐야 함

대응:

- token hash 또는 jti를 기록한다
- authz deny/allow 이벤트를 대조한다
- revocation 시점을 기준으로 탐색한다

### 시나리오 3: 허용된 접근과 거부된 접근을 모두 관찰해야 함

대응:

- security event stream을 별도 집계한다
- SIEM 또는 alert pipeline에 보낸다
- 정상/비정상 패턴을 분리한다

---

## 코드로 보기

### 1. authz event 기록

```java
public void authorize(UserPrincipal user, String resourceId, String action) {
    AuthorizationDecision decision = policyEngine.decide(user, resourceId, action);
    auditLogger.logAuthz(user.id(), user.tenantId(), resourceId, action, decision.allowed(), user.policyVersion());
    if (!decision.allowed()) {
        throw new AccessDeniedException("forbidden");
    }
}
```

### 2. auth event 기록

```java
public void onLoginSuccess(User user, String sessionId) {
    auditLogger.logAuth(user.id(), sessionId, "LOGIN_SUCCESS", "password+mfa");
}
```

### 3. 마스킹 규칙

```text
1. token 원문은 기록하지 않는다
2. password와 secret은 저장하지 않는다
3. 필요한 경우 prefix와 hash만 남긴다
4. time, actor, action, resource, outcome은 남긴다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| application debug log | 만들기 쉽다 | 증거성/보안성이 약하다 | 일반 디버깅 |
| auth/authz audit log | 추적과 증거에 강하다 | 설계와 저장이 필요하다 | 보안 필수 |
| deny-only logging | 소음이 적다 | allow 경로 재구성이 약하다 | 제한된 경우 |
| full decision logging | 분석이 강하다 | 비용과 민감정보 관리가 필요하다 | 고보안/규제 환경 |

판단 기준은 이렇다.

- 사고 후 누가 무엇을 했는지 재구성해야 하는가
- deny 이벤트를 봐야 하는가
- retention과 tamper resistance가 필요한가
- 로그에 남길 최소 필드는 정의했는가

---

## 꼬리질문

> Q: auth log와 authz log는 왜 분리하나요?
> 의도: 인증 이벤트와 권한 결정을 구분하는지 확인
> 핵심: 문제의 층이 다르기 때문이다.

> Q: deny 로그가 왜 중요한가요?
> 의도: 공격 시도를 추적하는 관점을 이해하는지 확인
> 핵심: 공격 탐지와 forensic에 매우 유용하기 때문이다.

> Q: audit log에 무엇을 남기면 안 되나요?
> 의도: 민감 정보 마스킹을 아는지 확인
> 핵심: token, password, secret, 과도한 PII는 남기면 안 된다.

> Q: 왜 immutable이어야 하나요?
> 의도: 증거성/감사성을 이해하는지 확인
> 핵심: 나중에 조작되면 증거가 되지 않기 때문이다.

## 한 줄 정리

auth/authz audit logging은 보안 이벤트를 증거로 남기는 설계이며, deny 이벤트와 policy version을 같이 기록해야 힘이 있다.

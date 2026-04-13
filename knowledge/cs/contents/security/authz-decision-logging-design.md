# AuthZ Decision Logging Design

> 한 줄 요약: authz decision log는 허용/거부 결과만 남기는 것이 아니라, 정책 버전과 평가 근거까지 기록해야 나중에 재현 가능한 증거가 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md)
> - [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)

retrieval-anchor-keywords: authz decision logging, decision reason, policy version, allow deny, PDP, PEP, traceability, resource owner, policy engine, security telemetry

---

## 핵심 개념

authz decision logging은 누가 어떤 자원에 어떤 동작을 하려 했고, 그 결과가 왜 allow 또는 deny였는지를 기록하는 설계다.

단순 access log와 다른 점:

- 요청이 왔다는 사실만 기록하지 않는다
- 권한 판단 결과를 기록한다
- 어떤 정책 버전과 어떤 근거로 결정했는지 남긴다

즉 authz decision log는 "무슨 일이 일어났는가"가 아니라 "왜 그렇게 판단했는가"까지 담아야 한다.

---

## 깊이 들어가기

### 1. 무엇을 기록해야 하나

기본 필드:

- actor id
- tenant id
- resource id
- action
- decision allow/deny
- policy version
- evaluation timestamp
- request id / correlation id

가능하면 추가:

- resource owner
- rule id
- reason code
- risk score
- cache hit 여부

### 2. reason code가 중요하다

단순히 deny만 남기면 나중에 분석이 어렵다.

예:

- `DENY_NOT_OWNER`
- `DENY_TENANT_MISMATCH`
- `DENY_POLICY_VERSION_STALE`
- `DENY_ROLE_MISSING`

reason code가 있어야 공격 탐지와 정책 개선이 쉬워진다.

### 3. log와 policy engine을 분리해야 한다

권한 결정을 내리는 엔진과 기록하는 레이어는 분리한다.

- PDP가 결정을 만든다
- PEP가 실행한다
- logger가 독립적으로 남긴다

한 함수에서 전부 하면 테스트와 운영이 어려워진다.

### 4. sensitive data는 기록하지 않는다

decision log는 강력하지만 위험할 수 있다.

- token 원문
- password
- secret
- 과도한 PII

필요한 식별자만 남긴다.

### 5. deny와 allow 모두 기록할지 결정해야 한다

모두 남기면 분석은 좋지만 비용이 든다.

- allow는 샘플링할 수 있다
- deny는 대부분 full capture가 필요하다

정책과 규모에 맞게 분리한다.

---

## 실전 시나리오

### 시나리오 1: 관리자 권한 남용 경로를 추적해야 함

대응:

- allow/deny와 policy version을 함께 본다
- admin action만 별도 스트림으로 묶는다
- correlation id로 앞뒤 요청을 연결한다

### 시나리오 2: 권한 회수 후에도 allow가 발생함

대응:

- stale policy version이 남았는지 본다
- cache hit 여부를 기록한다
- session revocation 로그와 대조한다

### 시나리오 3: audit와 decision log가 뒤섞여 분석이 어려움

대응:

- audit log는 사건 중심
- decision log는 정책 평가 중심
- 둘을 별도 sink로 보낸다

---

## 코드로 보기

### 1. decision log 기록

```java
public AuthorizationDecision decide(UserPrincipal user, String resourceId, String action) {
    AuthorizationDecision decision = policyEngine.evaluate(user, resourceId, action);
    decisionLogger.log(
        user.id(),
        user.tenantId(),
        resourceId,
        action,
        decision.allowed(),
        decision.reasonCode(),
        user.policyVersion()
    );
    return decision;
}
```

### 2. reason code enum

```java
public enum DecisionReason {
    ALLOW_OWNER,
    ALLOW_ADMIN,
    DENY_NOT_OWNER,
    DENY_TENANT_MISMATCH,
    DENY_ROLE_MISSING,
    DENY_STALE_POLICY
}
```

### 3. log sink 분리

```text
1. authz decision은 별도 sink로 보낸다
2. audit log와 포맷을 다르게 둔다
3. policy version과 reason code를 항상 포함한다
4. 민감 값은 마스킹한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| allow/deny only | 단순하다 | 재현성이 약하다 | 아주 작은 시스템 |
| reason code 포함 | 분석과 forensic에 좋다 | 설계가 필요하다 | 대부분의 서비스 |
| full policy trace | 재현성이 높다 | 비용과 민감정보 관리가 필요하다 | 고보안/규제 환경 |

판단 기준은 이렇다.

- deny 원인을 얼마나 빨리 알아야 하는가
- 정책 버전 차이를 추적해야 하는가
- 어떤 resource에 대한 결정을 재현해야 하는가
- 로그 보관과 개인정보 제약을 만족할 수 있는가

---

## 꼬리질문

> Q: authz decision log에는 무엇을 남겨야 하나요?
> 의도: 근거와 버전의 중요성을 아는지 확인
> 핵심: actor, resource, action, decision, reason code, policy version이다.

> Q: reason code가 왜 필요한가요?
> 의도: 단순 결과와 분석 가능성의 차이를 아는지 확인
> 핵심: 왜 deny/allow가 났는지 재현할 수 있기 때문이다.

> Q: audit log와 어떻게 다른가요?
> 의도: 사건 기록과 결정 기록을 구분하는지 확인
> 핵심: audit는 사건 중심, decision log는 정책 평가 중심이다.

> Q: policy version을 왜 기록하나요?
> 의도: drift와 stale policy 분석을 아는지 확인
> 핵심: 어떤 정책 기준으로 판단했는지 재현하기 위해서다.

## 한 줄 정리

authz decision logging은 결과만이 아니라 정책 버전과 reason code를 남겨야 나중에 재현 가능한 보안 증거가 된다.

# AuthZ Kill Switch / Break-Glass Governance

> 한 줄 요약: 인가 장애에서 필요한 것은 무조건적인 우회가 아니라, 어떤 정책을 어떤 범위에서 얼마 동안 완화할지 통제하는 break-glass 제어면이며, audit, expiry, approval, rollback이 없으면 emergency override 자체가 새로운 취약점이 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)
> - [AuthZ Decision Logging Design](./authz-decision-logging-design.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)
> - [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md)
> - [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md)
> - [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)
> - [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md)

retrieval-anchor-keywords: authz kill switch, break glass, emergency override, authorization override governance, policy bypass control, emergency access, scoped override, expiry override, audited override, rollback switch, break glass notification, emergency access timeline, incident close gate, break glass closure blocker, incident closed with active override

---

## 핵심 개념

인가 장애가 나면 흔히 두 가지 극단으로 흐른다.

- 아무것도 못 하게 막는다
- 급해서 다 열어 버린다

둘 다 위험하다.  
그래서 필요한 것이 authz kill switch와 break-glass governance다.

핵심 질문:

- 어떤 route 또는 capability만 완화할 것인가
- 어떤 actor만 쓸 수 있는가
- 언제 자동 만료되는가
- 누가 승인했고 누가 해제했는가

즉 break-glass는 "우회"가 아니라, 시간과 범위가 제한된 emergency control plane이다.

---

## 깊이 들어가기

### 1. kill switch와 break-glass는 다르다

- kill switch: 특정 policy path나 feature를 빠르게 끄는 운영 레버
- break-glass: 제한된 actor에게 예외 접근을 허용하는 긴급 절차

예:

- 새 policy rollout을 즉시 old policy로 되돌리는 것은 kill switch
- on-call admin에게 tenant 복구 권한을 30분 주는 것은 break-glass

둘을 섞으면 rollback과 예외 권한 부여가 동시에 엉켜 버린다.

### 2. 우회는 actor, scope, duration 세 축으로 제한해야 한다

안전한 break-glass는 최소한 이 셋이 있어야 한다.

- actor: 누가 사용할 수 있는가
- scope: 어떤 tenant/resource/action에만 적용되는가
- duration: 언제 만료되는가

없으면 생기는 문제:

- 모든 운영자가 영구적인 슈퍼권한을 갖는다
- incident 종료 후에도 예외가 남는다
- 누가 어떤 범위에 접근했는지 재구성할 수 없다

### 3. global allow override는 마지막 수단이어야 한다

가장 위험한 안티패턴:

- "403 많이 나오니 전부 allow"

더 나은 순서:

1. rollout kill switch로 old policy 복귀
2. 일부 route만 old evaluator 사용
3. 특정 tenant/actor에만 break-glass grant
4. global override는 정말 마지막 수단으로만, 매우 짧게

즉 policy bug와 운영 복구를 구분해야 한다.

### 4. break-glass 권한도 평소 권한 모델 안에서 표현하는 편이 낫다

좋은 패턴:

- 별도 break-glass role or grant
- explicit approval id
- strong step-up 요구
- time-boxed expiry

나쁜 패턴:

- DB에서 admin=true로 직접 수정
- 설정 파일로 몰래 allowlist 추가

후자는 빠를 수 있어 보여도 audit와 회수가 너무 어렵다.

### 5. step-up과 approval이 같이 가야 한다

긴급 권한은 계정 기본 세션만으로 주면 안 된다.

권장:

- 최근 strong auth 필수
- two-person approval 또는 ticket id 요구
- reason code 입력
- 민감 action은 recording/audit 강화

긴급 권한은 평소보다 더 강한 assurance를 요구하는 것이 자연스럽다.

### 6. override는 데이터 plane보다 control plane에 남겨야 한다

즉 실행 중 request path마다 임의 분기가 생기기보다:

- central override registry
- explicit evaluation layer
- structured audit event

처럼 control plane에서 관리하는 편이 낫다.

그래야 어느 서비스가 어떤 예외를 보고 있는지 추적할 수 있다.

### 7. incident 종료 후 cleanup이 반쯤이다

자주 잊는 단계:

- override 제거
- 영향받은 요청 재검토
- approve/used/revoked event 검토
- 장기 권한 drift 확인

break-glass는 "켜는 것"보다 "안 남기고 끄는 것"이 더 중요할 때가 많다.

### 8. observability가 없으면 override가 정상 운영처럼 섞인다

필요한 신호:

- active override count
- override by actor / scope
- override-mediated allow count
- expired-but-still-active anomaly
- incident timeline correlation

즉 break-glass는 로그 한 줄이 아니라 관측 가능한 운영 상태여야 한다.

그리고 customer-facing 또는 tenant-admin-facing surface가 있다면 ordinary admin login과 섞이지 않는 별도 emergency access event로 투영하는 편이 좋고, affected user / tenant admin / security contact matrix는 [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md)처럼 명시적으로 두는 편이 안전하다.
incident를 닫기 전에 active override와 leftover grant를 어떤 hard blocker로 계산할지는 [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md)에서 이어진다.

---

## 실전 시나리오

### 시나리오 1: policy rollout bug로 관리자 기능이 전부 막힌다

문제:

- support 복구가 필요한데 global allow는 위험하다

대응:

- old policy evaluator로 되돌리는 kill switch를 먼저 사용한다
- 일부 tenant 복구가 필요하면 scoped break-glass grant를 발급한다
- incident 종료 후 grant를 모두 회수한다

### 시나리오 2: 데이터 복구를 위해 특정 운영자에게 일시적 슈퍼권한이 필요하다

문제:

- 평소 role로는 접근 불가

대응:

- approval id와 강한 step-up을 요구한다
- tenant/action 범위와 TTL을 명시한다
- actor, subject, override reason을 모두 audit에 남긴다

### 시나리오 3: override가 종료 후에도 남아 조용한 권한 확대가 된다

문제:

- expiry와 cleanup이 자동화되지 않았다

대응:

- 모든 override에 hard expiry를 둔다
- active override count를 alert한다
- incident review에서 leftover override를 확인한다

---

## 코드로 보기

### 1. break-glass grant 예시

```java
public record BreakGlassGrant(
        String actorId,
        String scope,
        String reasonCode,
        String approvalId,
        Instant expiresAt
) {
}
```

### 2. evaluation 순서 예시

```java
public Decision decide(RequestContext context) {
    if (overrideRegistry.hasScopedGrant(context.actorId(), context.scope())) {
        return Decision.allow("BREAK_GLASS_OVERRIDE");
    }

    return policyEngine.evaluate(context);
}
```

### 3. 운영 체크리스트

```text
1. kill switch와 break-glass 권한 부여를 구분하는가
2. override가 actor, scope, duration으로 제한되는가
3. strong auth와 approval id가 필요한가
4. incident 종료 후 cleanup과 audit review가 자동화돼 있는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| global allow override | 빠르다 | blast radius가 너무 크다 | 거의 피해야 한다 |
| scoped kill switch | 빠른 rollback이 가능하다 | 정책 구조를 미리 준비해야 한다 | rollout bug 복구 |
| break-glass grant | 범위를 좁혀 emergency access를 줄 수 있다 | 운영 절차가 필요하다 | 복구/운영 작업 |
| DB 직접 수정 | 즉흥적으로 빠르다 | audit와 회수가 거의 안 된다 | 피해야 한다 |

판단 기준은 이렇다.

- 문제의 원인이 policy bug인지 실제 운영 복구인지
- override가 필요한 actor와 scope를 좁힐 수 있는지
- step-up과 approval을 함께 강제할 수 있는지
- 종료 후 leftover privilege를 검출할 수 있는지

---

## 꼬리질문

> Q: kill switch와 break-glass의 차이는 무엇인가요?
> 의도: rollback과 emergency access를 구분하는지 확인
> 핵심: kill switch는 정책 경로를 끄는 것이고, break-glass는 제한된 예외 권한을 부여하는 것이다.

> Q: 왜 global allow override가 위험한가요?
> 의도: 범위 제한의 중요성을 이해하는지 확인
> 핵심: 문제 범위를 넘어서 전체 권한 경계를 열어 blast radius가 커지기 때문이다.

> Q: break-glass에도 step-up이 필요한가요?
> 의도: 긴급 권한일수록 강한 assurance가 필요함을 이해하는지 확인
> 핵심: 그렇다. 평소보다 더 강한 인증과 승인 절차가 자연스럽다.

> Q: incident가 끝난 뒤 무엇을 꼭 해야 하나요?
> 의도: cleanup과 review를 운영 일부로 보는지 확인
> 핵심: override 회수, audit 검토, leftover privilege 확인이 필수다.

## 한 줄 정리

AuthZ break-glass의 핵심은 빨리 우회하는 것이 아니라, kill switch와 emergency grant를 분리하고 actor/scope/duration이 제한된 override를 감사 가능하게 운영하는 것이다.

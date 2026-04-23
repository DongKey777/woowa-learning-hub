# Authorization Runtime Signals / Shadow Evaluation

> 한 줄 요약: 인가 시스템은 설계 문서보다 런타임에서 더 많이 실패하므로, deny spike, owner mismatch, tenant mismatch, cache staleness, shadow decision divergence를 실시간으로 보고 정책 변경을 shadow evaluation과 canary로 배포해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [AuthZ Decision Logging Design](./authz-decision-logging-design.md)
> - [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [Authorization Graph Caching](./authorization-graph-caching.md)
> - [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md)
> - [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
> - [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)
> - [SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md)
> - [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md)
> - [System Design: Database / Security Identity Bridge Cutover 설계](../system-design/database-security-identity-bridge-cutover-design.md)

retrieval-anchor-keywords: authorization runtime signals, shadow evaluation, policy canary, deny spike, shadow decision divergence, graph snapshot drift, graph snapshot version mismatch, authorization graph lag, authz runtime telemetry, policy rollout safety, owner mismatch spike, tenant mismatch signal, authorization kill switch, break glass, auth shadow compare, decision parity, authority transfer, deprovision tail, data shadow compare

---

## 핵심 개념

인가 장애는 보통 "시스템이 죽었다"보다 "갑자기 deny가 늘었거나, 반대로 의도치 않은 allow가 늘었다"는 식으로 나타난다.

즉 authz 운영에서 중요한 질문은 다음이다.

- 지금 deny가 정상적인 공격 차단인가, policy bug인가
- policy cache가 stale해서 과거 권한을 보는가
- 새 policy version이 기존과 얼마나 다른 결과를 내는가
- rollout 중 어디서 divergence가 시작됐는가

이 문서는 policy modeling이 아니라, authz를 production에서 안전하게 바꾸고 감시하는 runtime signal에 초점을 둔다.

---

## 깊이 들어가기

### 1. authz incident는 allow bug와 deny bug 두 방향이 있다

deny bug는 눈에 잘 띈다.

- 사용자 불만
- 403/404 급증
- support ticket 증가

allow bug는 더 위험하지만 조용할 수 있다.

- 원래 막아야 할 호출이 허용됨
- 특정 tenant 경계가 조용히 무너짐
- audit를 보기 전엔 모름

그래서 deny rate만 보면 안 되고, allow semantics 변화도 봐야 한다.

### 2. runtime signal은 reason code 단위여야 한다

의미 있는 signal 예:

- `DENY_NOT_OWNER` 급증
- `DENY_TENANT_MISMATCH` 급증
- `ALLOW_VIA_ADMIN_OVERRIDE` 비율 증가
- `DECISION_CACHE_STALE` 증가
- `POLICY_VERSION_MISMATCH` 증가
- `GRAPH_SNAPSHOT_VERSION_MISMATCH` 증가

이런 bucket이 없으면 "403이 늘었다"까지만 알게 된다.

### 3. shadow evaluation은 production 트래픽으로 새 policy를 조용히 비교하는 방식이다

핵심 아이디어:

- 실제 enforce는 old policy로 한다
- 같은 입력으로 new policy도 같이 평가한다
- 결과가 다르면 divergence event를 남긴다

장점:

- 사용자 영향 없이 policy 차이를 본다
- 특정 route, tenant, actor class에서만 다른지 찾기 쉽다
- rollout 전에 위험한 deny/allow 변화를 발견할 수 있다

### 4. divergence는 "다르다"만으론 부족하고 의미를 분류해야 한다

예를 들어 다음은 다 다르지만 의미가 다르다.

- old allow / new deny
- old deny / new allow
- reason code만 바뀜
- latency만 크게 증가

특히 위험한 건:

- old deny / new allow on tenant boundary
- old deny / new allow on admin action
- old allow / new deny on hot path

따라서 divergence severity taxonomy가 필요하다.

### 5. data shadow read와 auth shadow evaluation은 서로 다른 실패를 잡는다

database migration이나 directory backfill이 함께 움직일 때 이 둘을 자주 혼동한다.

- data shadow read는 source/target row나 projection이 같은지 본다
- auth shadow evaluation은 같은 입력에 같은 allow/deny가 나오는지 본다

즉 다음 상태는 충분히 가능하다.

- backfill checksum과 shadow read는 green인데 tenant claim/policy version이 달라 decision divergence가 남는다
- SCIM deprovision row는 반영됐는데 session/authz cache tail 때문에 old allow가 계속 나온다
- local DB state는 수렴했지만 delegated override cleanup이 늦어 runtime allow가 남는다

authority transfer가 database와 security plane을 같이 건드리면
[Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md)와
[SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md)를 함께 보고,
승격 판단은 [System Design: Database / Security Identity Bridge Cutover 설계](../system-design/database-security-identity-bridge-cutover-design.md)처럼 joint gate로 묶는 편이 안전하다.

### 6. policy rollout은 code rollout보다 더 보수적이어야 한다

정책은 작아 보여도 blast radius가 넓다.

안전한 순서:

1. shadow-only
2. low-risk route canary
3. single-tenant or internal cohort
4. progressive percentage rollout
5. full enforce

그리고 각 단계마다 rollback kill switch가 있어야 한다.

### 7. cache와 policy version drift는 별도 signal로 봐야 한다

새 policy가 맞게 배포돼도 다음이 있으면 runtime 결과가 다르게 나온다.

- 일부 PEP만 old policy를 봄
- decision cache가 old version을 재사용
- authorization graph가 덜 동기화됨

즉 policy git SHA 하나만 같다고 runtime decision이 같은 것은 아니다.
relationship-based authz라면 policy version과 graph snapshot/version token을 따로 metric tag와 divergence log에 남겨야 한다.
이 축은 [Authorization Graph Caching](./authorization-graph-caching.md)의 snapshot invalidation 문제를 runtime signal로 끌어오는 최소 단위다.

### 8. deny spike는 공격과 버그를 함께 고려해야 한다

예를 들어 `DENY_TENANT_MISMATCH` 급증은:

- 실제 enumeration 공격일 수도 있고
- tenant resolver bug일 수도 있다
- cache pollution일 수도 있다

그래서 runtime signal에는 release version, region, route class, actor type도 같이 붙어야 한다.

### 9. allow-side guardrail이 있어야 조용한 권한 확장을 잡는다

유용한 guardrail:

- admin override allow ratio
- cross-tenant allow count
- owner-missing allow count
- shadow old deny / new allow count

인가는 deny만 보는 시스템이 아니라, 위험한 allow를 빨리 찾는 시스템이어야 한다.

---

## 실전 시나리오

### 시나리오 1: 새 policy rollout 뒤 404가 급증한다

문제:

- concealment policy와 owner check가 달라졌을 수 있다

대응:

- shadow divergence에서 old allow / new deny 비율을 본다
- `DENY_NOT_OWNER`, `DENY_TENANT_MISMATCH` reason code를 분리해 본다
- hot route canary를 rollback 한다

### 시나리오 2: 사용자 문제는 없는데 나중에 보니 cross-tenant allow가 생겼다

문제:

- deny 지표만 보고 allow-side guardrail이 없었다

대응:

- shadow old deny / new allow를 high-severity로 승격한다
- tenant boundary route에 별도 alert를 둔다
- audit와 decision log를 대조한다

### 시나리오 3: denial spike가 공격처럼 보였는데 실제로는 release bug다

문제:

- authz signal에 release/version 태그가 없다

대응:

- release version, region, route class를 metric에 포함한다
- 공격형 분포인지 rollout형 분포인지 먼저 구분한다

---

## 코드로 보기

### 1. shadow evaluation 개념

```java
public AuthorizationDecision decide(RequestContext context) {
    AuthorizationDecision enforced = oldPolicy.evaluate(context);
    AuthorizationDecision shadow = newPolicy.evaluate(context);

    if (!enforced.equalsSemantically(shadow)) {
        divergenceLogger.log(context, enforced, shadow);
    }

    return enforced;
}
```

### 2. divergence severity 예시

```text
old deny -> new allow on tenant/admin boundary = critical
old allow -> new deny on hot route = high
reason code changed only = medium
same decision but latency regression = medium
```

### 3. 운영 체크리스트

```text
1. deny/allow를 reason code와 route class 단위로 본다
2. policy rollout 전에 shadow evaluation을 거치는가
3. old deny -> new allow divergence를 별도 고위험 신호로 보는가
4. authz signal에 release version, region, policy/graph snapshot version이 붙는가
5. authority transfer 중이면 data shadow mismatch와 auth shadow divergence를 분리해 보는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| immediate enforce rollout | 빠르다 | silent allow bug와 deny spike 위험이 크다 | 아주 단순한 정책 |
| shadow evaluation | 사용자 영향 없이 차이를 본다 | 비용과 로그량이 늘어난다 | 대부분의 중대형 authz 시스템 |
| deny-only alerting | 구현이 쉽다 | 위험한 allow를 놓친다 | 초기 수준 |
| allow+deny guardrail | 보안 coverage가 좋다 | taxonomy와 tuning이 필요하다 | tenant/admin boundary가 중요한 시스템 |

판단 기준은 이렇다.

- 정책 변경이 tenant/admin/ownership 경계를 건드리는가
- PEP/PDP/cache가 분산되어 있는가
- silent allow bug를 얼마나 빨리 잡아야 하는가
- divergence 로그량을 감당할 수 있는가

---

## 꼬리질문

> Q: authz runtime signal은 왜 403 수치만으로 부족한가요?
> 의도: deny taxonomy의 필요를 이해하는지 확인
> 핵심: owner mismatch, tenant mismatch, stale cache, rollout bug가 모두 같은 403처럼 보일 수 있기 때문이다.

> Q: shadow evaluation의 가장 큰 가치는 무엇인가요?
> 의도: production-safe policy 변경 방법을 아는지 확인
> 핵심: 사용자 영향 없이 새 policy가 기존과 어떻게 다른지 production 입력으로 확인할 수 있다는 점이다.

> Q: 왜 old deny -> new allow가 특히 위험한가요?
> 의도: silent allow bug의 심각성을 아는지 확인
> 핵심: 고객 불만 없이 조용히 권한 경계가 무너질 수 있기 때문이다.

> Q: deny spike가 항상 공격 신호인가요?
> 의도: 보안 이벤트와 rollout 버그를 구분하는지 확인
> 핵심: 아니다. release bug, resolver bug, cache drift도 같은 현상을 만들 수 있다.

## 한 줄 정리

인가 운영의 핵심은 정책을 정적으로 설계하는 것이 아니라, reason-coded runtime signal과 shadow evaluation으로 deny spike와 silent allow drift를 production에서 안전하게 잡는 것이다.

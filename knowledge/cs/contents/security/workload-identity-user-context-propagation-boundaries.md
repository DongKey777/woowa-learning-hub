---
schema_version: 3
title: Workload Identity / User Context Propagation Boundaries
concept_id: security/workload-identity-user-context-propagation-boundaries
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- workload identity
- user context propagation
- end-user context
- service identity
aliases:
- workload identity
- user context propagation
- end-user context
- service identity
- caller identity
- on-behalf-of
- actor subject separation
- delegated user context
- zero trust service boundary
- confused deputy
- support operator
- Workload Identity / User Context Propagation Boundaries
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/service-to-service-auth-mtls-jwt-spiffe.md
- contents/security/gateway-auth-context-header-trust-boundary.md
- contents/security/token-exchange-impersonation-risks.md
- contents/security/workload-identity-vs-long-lived-service-account-keys.md
- contents/security/support-operator-acting-on-behalf-of-controls.md
- contents/security/audit-logging-auth-authz-traceability.md
- contents/security/background-job-auth-context-revalidation.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Workload Identity / User Context Propagation Boundaries 핵심 개념을 설명해줘
- workload identity가 왜 필요한지 알려줘
- Workload Identity / User Context Propagation Boundaries 실무 설계 포인트는 뭐야?
- workload identity에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Workload Identity / User Context Propagation Boundaries를 다루는 deep_dive 문서다. 서비스 간 신뢰에서 가장 중요한 분리는 "누가 호출한 workload인가"와 "그 요청이 어떤 사용자 맥락을 대리하는가"를 섞지 않는 것이며, 둘을 분리해야 on-behalf-of, audit, downscoping, confused deputy 방어가 가능해진다. 검색 질의가 workload identity, user context propagation, end-user context, service identity처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Workload Identity / User Context Propagation Boundaries

> 한 줄 요약: 서비스 간 신뢰에서 가장 중요한 분리는 "누가 호출한 workload인가"와 "그 요청이 어떤 사용자 맥락을 대리하는가"를 섞지 않는 것이며, 둘을 분리해야 on-behalf-of, audit, downscoping, confused deputy 방어가 가능해진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)
> - [Gateway Auth Context Headers / Trust Boundary](./gateway-auth-context-header-trust-boundary.md)
> - [Token Exchange / Impersonation Risks](./token-exchange-impersonation-risks.md)
> - [Workload Identity / Long-Lived Service Account Keys](./workload-identity-vs-long-lived-service-account-keys.md)
> - [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [Background Job Auth Context / Revalidation](./background-job-auth-context-revalidation.md)

retrieval-anchor-keywords: workload identity, user context propagation, end-user context, service identity, caller identity, on-behalf-of, actor subject separation, delegated user context, zero trust service boundary, confused deputy, support operator

---

## 핵심 개념

마이크로서비스에서 흔히 일어나는 혼선은 이 두 질문을 하나로 취급하는 것이다.

- 이 요청을 보낸 네트워크 주체는 누구인가
- 이 요청이 대신하고 있는 최종 사용자는 누구인가

첫 번째는 workload identity 문제다.  
두 번째는 user context propagation 문제다.

둘을 섞으면 다음 사고가 난다.

- 서비스가 자기 권한과 사용자 권한을 구분하지 못한다
- downstream이 caller service를 안 보고 user claim만 믿는다
- acting-on-behalf-of audit가 사라진다
- token exchange가 권한 확대 통로가 된다

즉 service-to-service trust boundary의 핵심은 workload identity와 user context를 동시에 보되, 같은 것으로 취급하지 않는 것이다.

---

## 깊이 들어가기

### 1. workload identity는 "어떤 서비스인가"를 말한다

보통 다음으로 표현된다.

- mTLS client certificate
- SPIFFE ID
- workload token
- service account federation

이 정보는 caller service 자체를 증명한다.

예:

- `payments-api`
- `report-worker`
- `admin-bff`

### 2. user context는 "누구를 대신해 무엇을 하려는가"를 말한다

이건 별도 축이다.

- user id
- tenant id
- delegated scope
- actor / subject 관계
- session or assurance context

즉 같은 `admin-bff`라도:

- 자기 시스템 작업인지
- 특정 사용자를 대신한 호출인지
- support operator가 acting-on-behalf-of인지

가 다를 수 있다.

### 3. downstream은 user context보다 caller workload identity를 먼저 확인해야 한다

많이 하는 실수:

- user claim만 있으면 downstream이 호출을 받아 준다

안전한 순서:

1. trusted workload인가 확인
2. 이 workload가 user context를 대리할 자격이 있는가 확인
3. user context의 audience와 scope가 좁혀졌는가 확인
4. actor와 subject를 audit에 남긴다

즉 "이 사용자라서 허용" 전에 "이 서비스를 통해 와도 되는가"를 먼저 봐야 한다.

### 4. raw end-user token pass-through는 경계를 흐리기 쉽다

edge에서 받은 user JWT를 내부 서비스 hop마다 그대로 넘기면 편해 보인다.  
하지만 장기적으로는 다음 문제가 쌓인다.

- audience가 내부 서비스 전체로 넓어진다
- 한 서비스가 받은 user token으로 다른 서비스까지 호출한다
- caller workload identity와 end-user context가 로그에서 구분되지 않는다
- 내부 hop에서 최소 권한이 어려워진다

그래서 보통은 token exchange나 internal auth context translation이 필요하다.

### 5. token exchange의 핵심은 actor/subject 분리다

internal exchanged token에는 최소한 이런 관점이 있어야 한다.

- subject: 최종 사용자는 누구인가
- actor: 지금 이 호출을 대리 수행하는 서비스는 누구인가
- audience: 어디까지 쓸 수 있는가
- scope: 무엇까지 할 수 있는가

이렇게 해야 downstream이:

- user id만 보지 않고
- caller service와 delegated scope를 같이 판단할 수 있다

### 6. background job와 scheduled task는 user context 전파보다 service-owned identity가 나은 경우가 많다

모든 비동기 작업이 사용자를 직접 대리할 필요는 없다.

오히려 더 안전한 패턴:

- 요청 당시 사용자와 승인 사실은 기록
- 실제 worker 실행은 service-owned identity로 수행
- tenant, report, object scope만 명시적으로 제한

이렇게 하면 stale user token을 queue로 옮기는 문제를 줄일 수 있다.

### 7. audit는 caller와 subject를 둘 다 남겨야 한다

필요한 필드:

- authenticated workload identity
- actor service id
- end-user subject
- tenant
- delegated scope
- route/action

이게 없으면 나중에 "사용자가 직접 한 행동인지, BFF가 대신한 건지, support operator가 acting-on-behalf-of 한 건지"를 구분하지 못한다.

### 8. trust boundary는 경로별로 다를 수 있다

예를 들어:

- edge -> BFF: user login context가 강함
- BFF -> domain API: workload identity + delegated user context
- scheduler -> batch worker: service identity 우선
- admin tool -> internal API: operator identity + acting-on-behalf-of

모든 경로에 같은 propagation 규칙을 강제하면 오히려 혼란이 생긴다.  
route class별 contract가 필요하다.

---

## 실전 시나리오

### 시나리오 1: 내부 서비스가 user JWT만 믿고 caller service 검증을 안 한다

문제:

- 어느 서비스든 그 token만 들고 호출하면 같은 권한처럼 보인다

대응:

- workload identity 검증을 먼저 둔다
- internal audience token 또는 exchanged token을 사용한다
- raw user token pass-through 범위를 줄인다

### 시나리오 2: support tool이 고객 대신 작업했는데 audit에는 user id만 남는다

문제:

- actor와 subject가 구분되지 않는다

대응:

- `actor=support-operator`, `subject=end-user`, `workload=admin-tool`를 모두 남긴다
- acting-on-behalf-of를 명시적 필드로 둔다

### 시나리오 3: batch worker가 오래된 사용자 권한으로 계속 실행된다

문제:

- queue에 user token을 그대로 실었다

대응:

- worker는 service-owned identity로 실행한다
- user context는 audit와 explicit scope 입력으로만 유지한다
- 실행 시 tenant/object scope를 재검증한다

---

## 코드로 보기

### 1. caller identity와 user context를 분리한 예시

```java
public record InternalCallContext(
        String workloadIdentity,
        String actorService,
        String subjectUserId,
        String tenantId,
        String delegatedScope,
        String audience
) {
}
```

### 2. downstream 검사 개념

```java
public void verify(CallContext context) {
    workloadPolicy.requireTrustedCaller(context.workloadIdentity());
    delegationPolicy.requireAllowedActor(context.actorService(), context.delegatedScope());
    audiencePolicy.requireAllowedAudience(context.audience());
}
```

### 3. 운영 체크리스트

```text
1. caller workload identity와 end-user subject를 별도 필드로 다루는가
2. raw user token pass-through 대신 downscoped internal token을 쓰는가
3. actor, subject, workload를 audit에 함께 남기는가
4. async job는 user token보다 service-owned identity를 우선 검토하는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| raw user token pass-through | 단순하다 | audience 확장과 confused deputy 위험이 크다 | 짧은 과도기 |
| workload identity만 사용 | 경계가 단순하다 | end-user delegated context 표현이 약하다 | pure internal system tasks |
| workload identity + exchanged user context | 가장 명확하다 | token exchange와 audit 설계가 필요하다 | 대부분의 사용자 대리 호출 |
| service-owned async identity | stale user credential 위험이 줄어든다 | 요청자 의미를 별도 기록해야 한다 | batch, export, scheduled jobs |

판단 기준은 이렇다.

- downstream이 최종 사용자를 알아야 하는가
- caller workload를 신뢰 기준으로 먼저 검증할 수 있는가
- actor/subject 분리를 audit에 남길 수 있는가
- queue나 long-running path에서 stale user context가 문제되는가

---

## 꼬리질문

> Q: workload identity와 user context propagation의 차이는 무엇인가요?
> 의도: caller service와 end-user를 구분하는지 확인
> 핵심: workload identity는 어떤 서비스가 호출했는지, user context는 누구를 대신한 호출인지 나타낸다.

> Q: 왜 downstream은 user context보다 caller workload를 먼저 봐야 하나요?
> 의도: trust ordering을 이해하는지 확인
> 핵심: trusted service를 통하지 않은 user claim은 쉽게 confused deputy나 권한 확대 문제로 이어질 수 있기 때문이다.

> Q: raw user token pass-through가 왜 위험한가요?
> 의도: audience와 최소 권한 문제를 아는지 확인
> 핵심: 내부 hop 전체로 bearer 범위를 넓혀 caller/service 경계가 흐려지기 때문이다.

> Q: async job에서도 user context를 그대로 들고 가야 하나요?
> 의도: service-owned identity 패턴을 이해하는지 확인
> 핵심: 아니다. 많은 경우 service identity + explicit scope 입력이 더 안전하다.

## 한 줄 정리

서비스 간 신뢰를 운영 가능하게 만드는 핵심은 workload identity로 "누가 호출했는가"를 먼저 고정하고, end-user context는 별도의 delegated 정보로 downscope해서 전달하는 것이다.

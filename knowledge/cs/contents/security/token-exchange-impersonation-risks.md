---
schema_version: 3
title: Token Exchange / Impersonation Risks
concept_id: security/token-exchange-impersonation-risks
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- token exchange
- impersonation
- subject token
- actor token
aliases:
- token exchange
- impersonation
- subject token
- actor token
- audience
- scope downscoping
- delegated authority
- OBO
- confused deputy
- JWT exchange
- service token
- user context propagation
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/service-to-service-auth-mtls-jwt-spiffe.md
- contents/security/oidc-id-token-userinfo-boundaries.md
- contents/security/jwt-deep-dive.md
- contents/security/workload-identity-user-context-propagation-boundaries.md
- contents/security/delegated-admin-tenant-rbac.md
- contents/security/audit-logging-auth-authz-traceability.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Token Exchange / Impersonation Risks 핵심 개념을 설명해줘
- token exchange가 왜 필요한지 알려줘
- Token Exchange / Impersonation Risks 실무 설계 포인트는 뭐야?
- token exchange에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Token Exchange / Impersonation Risks를 다루는 deep_dive 문서다. token exchange는 한 주체의 토큰을 다른 audience나 subject용 토큰으로 바꾸는 강력한 기능이지만, impersonation과 confused deputy를 막지 않으면 권한 상승 통로가 된다. 검색 질의가 token exchange, impersonation, subject token, actor token처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Token Exchange / Impersonation Risks

> 한 줄 요약: token exchange는 한 주체의 토큰을 다른 audience나 subject용 토큰으로 바꾸는 강력한 기능이지만, impersonation과 confused deputy를 막지 않으면 권한 상승 통로가 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)
> - [OIDC, ID Token, UserInfo](./oidc-id-token-userinfo-boundaries.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [Workload Identity / User Context Propagation Boundaries](./workload-identity-user-context-propagation-boundaries.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)

retrieval-anchor-keywords: token exchange, impersonation, subject token, actor token, audience, scope downscoping, delegated authority, OBO, confused deputy, JWT exchange, service token, user context propagation

---

## 핵심 개념

token exchange는 어떤 토큰을 받아 다른 용도의 토큰으로 바꾸는 메커니즘이다.  
대표적으로 on-behalf-of(OBO)나 delegated access, service token exchange에 쓰인다.

핵심 개념:

- `subject token`: 원래 사용자나 workload를 나타내는 토큰
- `actor token`: 대리하는 주체의 토큰
- `exchanged token`: 특정 audience/scope로 다시 발급된 토큰

이 기능은 매우 유용하지만, 잘못 설계하면:

- 사용자가 직접 허용하지 않은 범위까지 대리할 수 있다
- 서비스가 필요 이상 권한을 얻을 수 있다
- impersonation과 delegation 경계가 흐려진다

즉 token exchange는 delegation을 안전하게 표현하는 수단이지, 권한 확대용 지름길이 아니다.

---

## 깊이 들어가기

### 1. 왜 token exchange를 쓰나

주요 목적:

- audience를 좁힌다
- scope를 줄인다
- service-to-service hop에서 필요한 claim만 남긴다
- 사용자 토큰을 그대로 downstream에 넘기지 않는다

### 2. impersonation과 delegation은 다르다

- `delegation`: 사용자가 특정 서비스에게 대리 권한을 준다
- `impersonation`: 어떤 주체가 다른 주체인 척 행동한다

둘은 audit와 policy에서 다르게 다뤄야 한다.

### 3. confused deputy를 조심해야 한다

service A가 service B의 권한으로 호출할 수 있으면, B가 너무 많은 권한을 대리해 줄 수 있다.

방어:

- audience를 엄격히 좁힌다
- exchange 가능한 subject를 제한한다
- actor와 subject를 같이 기록한다
- downstream에서 original user context를 맹신하지 않는다

### 4. tenant와 role 경계가 중요하다

token exchange가 tenant를 넘어가면 위험하다.

- cross-tenant subject token exchange 금지
- admin impersonation은 명시적 승인 필요
- support access는 audit가 필수

### 5. downstream token은 원본 토큰보다 작아야 한다

좋은 교환 토큰은:

- 짧은 TTL
- 최소 scope
- 명시적 audience
- actor/subject 구분

---

## 실전 시나리오

### 시나리오 1: user token을 downstream 서비스에 그대로 전달함

대응:

- token exchange로 downstream audience 전용 토큰을 발급한다
- 필요한 claim만 남긴다
- 원본 토큰은 hop-by-hop으로 내려보내지 않는다

### 시나리오 2: support impersonation이 필요함

대응:

- impersonation을 별도 권한으로 분리한다
- audit log에 actor와 subject를 모두 남긴다
- step-up auth를 요구한다

### 시나리오 3: exchange된 토큰이 너무 넓은 scope를 가짐

대응:

- scope downscoping을 강제한다
- audience를 서비스 단위로 제한한다
- exchange policy를 centralize한다

---

## 코드로 보기

### 1. token exchange 개념

```java
public String exchange(String subjectToken, String audience) {
    return tokenService.exchange(subjectToken, audience, "minimal-scope");
}
```

### 2. impersonation audit 개념

```java
public void logExchange(UserPrincipal actor, String subjectUserId, String audience) {
    auditLogger.logAuthz(actor.id(), subjectUserId, audience, "TOKEN_EXCHANGE", true, actor.policyVersion());
}
```

### 3. scope downscoping

```text
1. 원본 토큰을 그대로 전달하지 않는다
2. audience를 한 서비스로 좁힌다
3. scope는 최소로 줄인다
4. actor와 subject를 모두 기록한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| pass-through token | 단순하다 | 권한이 넓고 추적이 어렵다 | 피해야 할 경우가 많다 |
| token exchange | audience/scope를 좁힐 수 있다 | 정책과 구현이 복잡하다 | MSA, OBO |
| impersonation token | support/ops에 유용하다 | abuse 위험이 크다 | 엄격한 승인 하 |
| mTLS only | transport 신원이 강하다 | user context 표현이 약하다 | service identity 중심 |

판단 기준은 이렇다.

- downstream이 원본 사용자 토큰을 직접 봐야 하는가
- impersonation이 필요한가
- actor/subject를 분리해 기록할 수 있는가
- audience와 scope를 서비스 단위로 줄일 수 있는가

---

## 꼬리질문

> Q: token exchange는 무엇을 위한 기능인가요?
> 의도: delegation과 downscoping 목적을 이해하는지 확인
> 핵심: 토큰을 다른 audience/scope로 바꿔 전달하기 위해서다.

> Q: impersonation과 delegation의 차이는 무엇인가요?
> 의도: 대리와 가장의 차이를 이해하는지 확인
> 핵심: delegation은 허용된 대리, impersonation은 다른 주체인 척 행동하는 것이다.

> Q: confused deputy는 왜 위험한가요?
> 의도: 토큰 교환과 대리 권한의 남용을 아는지 확인
> 핵심: 중간 서비스가 과도한 권한을 대신 행사할 수 있기 때문이다.

> Q: downstream token이 원본보다 작아야 하는 이유는 무엇인가요?
> 의도: 최소 권한 원칙을 아는지 확인
> 핵심: hop마다 필요한 권한만 남겨야 피해를 줄일 수 있기 때문이다.

## 한 줄 정리

token exchange는 delegation을 안전하게 좁히는 도구지만, impersonation과 confused deputy를 막는 정책이 없으면 위험해진다.

---
schema_version: 3
title: API Key Management Platform 설계
concept_id: system-design/api-key-management-platform-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- api key management
- key issuance
- secret rotation
- key revocation
aliases:
- api key management
- key issuance
- secret rotation
- key revocation
- scope
- usage analytics
- client credentials
- hmac
- key inventory
- developer portal
- API Key Management Platform 설계
- api key management platform design
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/api-key-hmac-signature-replay-protection.md
- contents/system-design/secrets-distribution-system-design.md
- contents/system-design/rate-limit-config-service-design.md
- contents/security/audit-logging-auth-authz-traceability.md
- contents/system-design/edge-authorization-service-design.md
- contents/security/workload-identity-vs-long-lived-service-account-keys.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- API Key Management Platform 설계 설계 핵심을 설명해줘
- api key management가 왜 필요한지 알려줘
- API Key Management Platform 설계 실무 트레이드오프는 뭐야?
- api key management 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 API Key Management Platform 설계를 다루는 deep_dive 문서다. API key management platform은 키 발급, 권한, 회전, 폐기, 사용량 추적을 중앙에서 관리하는 개발자 보안 인프라다. 검색 질의가 api key management, key issuance, secret rotation, key revocation처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# API Key Management Platform 설계

> 한 줄 요약: API key management platform은 키 발급, 권한, 회전, 폐기, 사용량 추적을 중앙에서 관리하는 개발자 보안 인프라다.

retrieval-anchor-keywords: api key management, key issuance, secret rotation, key revocation, scope, usage analytics, client credentials, hmac, key inventory, developer portal

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Key, HMAC Signed Request, Replay Protection](../security/api-key-hmac-signature-replay-protection.md)
> - [Secrets Distribution System 설계](./secrets-distribution-system-design.md)
> - [Rate Limit Config Service 설계](./rate-limit-config-service-design.md)
> - [Audit Logging for Auth / AuthZ Traceability](../security/audit-logging-auth-authz-traceability.md)
> - [Edge Authorization Service 설계](./edge-authorization-service-design.md)
> - [Workload Identity / Long-Lived Service Account Keys](../security/workload-identity-vs-long-lived-service-account-keys.md)

## 핵심 개념

API key는 단순 문자열이 아니다.  
실전에서는 아래를 함께 관리해야 한다.

- key issuance
- scopes and roles
- secret material
- rotation and revocation
- usage telemetry
- abuse detection

즉, API key management는 개발자 인증 수단을 운영하는 보안 플랫폼이다.

## 깊이 들어가기

### 1. key와 secret을 분리한다

- API key: 식별자
- API secret: 서명용 비밀
- scope: 허용 범위

이 구조가 있어야 rotation과 revoke가 가능하다.

### 2. Capacity Estimation

예:

- 10만 개발자 계정
- 수십만 active key
- 초당 수만 auth check

조회는 많고 발급은 적다.  
그래서 key lookup과 usage telemetry가 핵심이다.

봐야 할 숫자:

- key lookup QPS
- issuance rate
- revoke propagation delay
- usage report lag
- invalid request rate

### 3. portal and lifecycle

```text
Developer Portal
  -> Create Key
  -> Assign Scope
  -> Show Secret Once
  -> Rotate
  -> Revoke
  -> Audit
```

### 4. secret handling

secret은 평문으로 다시 보여주면 안 된다.

- 생성 시 1회 표시
- 이후에는 hash only
- rotation window
- emergency revoke

이 부분은 [Secrets Distribution System 설계](./secrets-distribution-system-design.md)와 연결된다.

### 5. usage and abuse

API key는 사용량과 abuse를 추적해야 한다.

- per key rate
- per tenant quota
- anomaly detection
- geo / ASN signal

이 부분은 [Rate Limit Config Service 설계](./rate-limit-config-service-design.md)와 [Edge Authorization Service 설계](./edge-authorization-service-design.md)와 연결된다.

### 6. scope model

Scope는 너무 넓으면 안 되고 너무 좁아도 불편하다.

- read/write/admin
- resource specific
- environment specific
- webhook send / receive

### 7. key rotation and revocation

키는 언젠가 교체해야 한다.

- scheduled rotation
- dual key overlap
- grace period
- forced revoke

이력은 [Audit Logging for Auth / AuthZ Traceability](../security/audit-logging-auth-authz-traceability.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: 고객이 키를 유출함

문제:

- GitHub에 실수로 노출됐다

해결:

- 즉시 revoke
- usage anomaly 확인
- 새 key 발급

### 시나리오 2: 키를 무중단 회전해야 함

문제:

- 외부 파트너가 새 키로 전환해야 한다

해결:

- old/new overlap
- dual validation

### 시나리오 3: 특정 key가 악용됨

문제:

- 과도한 호출과 실패가 보인다

해결:

- rate limit 강화
- scope 축소
- alert 발송

## 코드로 보기

```pseudo
function issueKey(app, scopes):
  secret = generateSecret()
  key = generatePublicKey()
  store(key, hash(secret), scopes)
  return {key, secretOnce}

function authenticate(key, signature):
  record = keyStore.get(key)
  verifySignature(record.secretHash, signature)
```

```java
public ApiCredential create(CredentialRequest req) {
    return keyService.issue(req.owner(), req.scopes());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Long-lived API key | 단순하다 | 유출 위험이 크다 | 레거시 |
| Rotating key + secret | 실무적이다 | 운영 절차 필요 | 일반적인 B2B API |
| Short-lived client credential | 안전하다 | 구현이 복잡 | 민감한 플랫폼 |
| Scope-per-key | 제어가 세밀하다 | 관리가 늘어난다 | 대규모 플랫폼 |
| Portal-driven lifecycle | 사용자 경험이 좋다 | backend 복잡도 | developer platform |

핵심은 API key management가 단순 식별자가 아니라 **발급, 회전, 사용량, 폐기를 함께 다루는 개발자 보안 플랫폼**이라는 점이다.

## 꼬리질문

> Q: API key와 API secret의 차이는 무엇인가요?
> 의도: 식별과 서명의 차이를 아는지 확인
> 핵심: key는 식별자, secret은 증명 수단이다.

> Q: secret을 다시 보여주면 안 되는 이유는?
> 의도: 민감정보 안전성 이해 확인
> 핵심: 재노출은 유출과 같다.

> Q: rotation을 무중단으로 하려면?
> 의도: dual validation과 grace window 이해 확인
> 핵심: 새/옛 키가 함께 유효한 기간이 필요하다.

> Q: abuse 탐지는 어디서 하나요?
> 의도: key telemetry와 policy 연결 이해 확인
> 핵심: 사용량, 실패율, geo, ASN 신호를 함께 본다.

## 한 줄 정리

API key management platform은 개발자용 키의 발급, scope, 회전, 폐기, 사용량 추적을 중앙에서 운영하는 보안 인프라다.


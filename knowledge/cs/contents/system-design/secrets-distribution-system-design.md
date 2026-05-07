---
schema_version: 3
title: Secrets Distribution System 설계
concept_id: system-design/secrets-distribution-system-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- secrets distribution
- secret manager
- vault
- kms
aliases:
- secrets distribution
- secret manager
- vault
- kms
- workload identity
- short-lived credential
- rotation
- lease
- envelope encryption
- federation
- audit trail
- Secrets Distribution System 설계
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/workload-identity-vs-long-lived-service-account-keys.md
- contents/security/envelope-encryption-kms-basics.md
- contents/security/key-rotation-runbook.md
- contents/security/secret-management-rotation-leak-patterns.md
- contents/system-design/config-distribution-system-design.md
- contents/system-design/api-gateway-control-plane-design.md
- contents/system-design/audit-log-pipeline-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Secrets Distribution System 설계 설계 핵심을 설명해줘
- secrets distribution가 왜 필요한지 알려줘
- Secrets Distribution System 설계 실무 트레이드오프는 뭐야?
- secrets distribution 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Secrets Distribution System 설계를 다루는 deep_dive 문서다. secrets distribution system은 짧은 수명의 자격 증명과 암호화된 비밀을 안전하게 배포하고 회전하는 중앙 신뢰 인프라다. 검색 질의가 secrets distribution, secret manager, vault, kms처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Secrets Distribution System 설계

> 한 줄 요약: secrets distribution system은 짧은 수명의 자격 증명과 암호화된 비밀을 안전하게 배포하고 회전하는 중앙 신뢰 인프라다.

retrieval-anchor-keywords: secrets distribution, secret manager, vault, kms, workload identity, short-lived credential, rotation, lease, envelope encryption, federation, audit trail

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Workload Identity / Long-Lived Service Account Keys](../security/workload-identity-vs-long-lived-service-account-keys.md)
> - [Envelope Encryption / KMS Basics](../security/envelope-encryption-kms-basics.md)
> - [Key Rotation Runbook](../security/key-rotation-runbook.md)
> - [Secret Management, Rotation, Leak Patterns](../security/secret-management-rotation-leak-patterns.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)

## 핵심 개념

비밀 배포는 "환경변수에 넣기"가 아니다.  
실전에서는 다음을 함께 해결해야 한다.

- 앱과 인프라가 secret을 안전하게 받는가
- 회전과 폐기를 자동화할 수 있는가
- 짧은 수명의 credential로 대체할 수 있는가
- 감사와 접근 통제가 남는가
- blast radius를 좁힐 수 있는가

즉, secrets distribution은 암호화와 identity, rotation의 중앙 제어 평면이다.

## 깊이 들어가기

### 1. secrets와 config는 다르다

config는 시스템 동작 파라미터이고, secrets는 인증과 암호화에 쓰이는 민감 정보다.

- config: timeout, feature toggle, routing
- secret: API key, DB password, signing key, private cert

둘을 같은 저장소에 넣으면 접근 제어와 회전 정책이 꼬인다.

### 2. Capacity Estimation

예:

- 5,000 workloads
- workload당 10개 secret
- 재시작/재배포로 분당 수천 번 fetch

핵심은 저장량보다 fetch latency와 rotation fan-out이다.  
특히 fleet이 크면 secret refresh가 장애 원인이 된다.

봐야 할 숫자:

- secret fetch QPS
- rotation fan-out
- lease renewal rate
- failed unwrap rate
- cache hit ratio

### 3. 배포 모델

| 방식 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| file mount | 단순하다 | 노출면이 넓다 | 레거시 |
| env var injection | 쉽다 | 프로세스 재시작이 필요 | 초기 형태 |
| sidecar fetch | 회전이 쉽다 | 런타임 복잡도 | 실서비스 |
| workload identity pull | 정적 key를 줄인다 | federation이 필요 | 현대 클라우드 |
| on-demand lease | blast radius가 작다 | 구현이 어렵다 | 민감 시스템 |

### 4. Rotation과 lease

secrets는 고정값이 아니라 lease가 있는 자원처럼 다루면 좋다.

- TTL
- grace period
- staged rotation
- dual validation

rotation이 실패하면 앱이 전부 죽을 수 있으므로 last-known-good와 fallback이 필요하다.

### 5. 접근 제어와 감사

중앙 비밀 저장소는 강력하지만 위험하다.

- 누가 읽었는가
- 누가 회전했는가
- 어떤 workload가 접근했는가
- 어떤 버전이 사용 중이었는가

이 감사를 [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)와 연결해야 한다.

### 6. workload identity와 federation

장기 키 대신 짧은 credential을 발급하는 편이 좋다.

- pod/workload attestation
- OIDC federation
- STS exchange
- short-lived token cache

이 부분은 [Workload Identity / Long-Lived Service Account Keys](../security/workload-identity-vs-long-lived-service-account-keys.md)와 직접 연결된다.

### 7. Failure mode

secrets backend가 죽었을 때 앱이 완전히 멈추면 안 된다.

- cached secret
- degraded startup
- read-only fallback
- emergency revocation path

## 실전 시나리오

### 시나리오 1: DB password rotation

문제:

- 무중단으로 DB 비밀번호를 바꿔야 한다

해결:

- dual password window
- connection pool 재시작
- old secret revoke

### 시나리오 2: CI 로그 유출

문제:

- build log에 secret이 찍혔다

해결:

- 즉시 revoke
- affected workload audit
- keyless federation 전환

### 시나리오 3: 서비스별 접근 분리

문제:

- 같은 secret을 여러 서비스가 공유한다

해결:

- workload별 secret scope 분리
- least privilege 적용

## 코드로 보기

```pseudo
function fetchSecret(workload, name):
  identity = attest(workload)
  token = sts.exchange(identity, name)
  return secretStore.read(name, token)
```

```java
public Secret load(String name) {
    return secretClient.get(name, workloadIdentity.token());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| static file secret | 단순하다 | 유출 위험이 크다 | 레거시 |
| secret manager | 중앙 통제가 쉽다 | 런타임 의존 증가 | 대부분의 서비스 |
| workload identity | 정적 key를 줄인다 | 인프라 연동 필요 | 현대 클라우드 |
| sidecar agent | 회전이 편하다 | 운영 복잡도 | 대규모 fleet |
| lease-based secret | blast radius가 작다 | 설계가 복잡하다 | 민감 시스템 |

핵심은 secrets distribution이 단순 저장소가 아니라 **identity, rotation, audit을 묶는 신뢰 인프라**라는 점이다.

## 꼬리질문

> Q: secrets와 config를 왜 분리해야 하나요?
> 의도: 민감정보와 운영설정 경계 이해 확인
> 핵심: 접근 제어와 회전 정책이 다르기 때문이다.

> Q: workload identity가 왜 중요한가요?
> 의도: 정적 키 제거의 의미 이해 확인
> 핵심: 장기 유출 위험을 줄이고 자동 회전을 쉽게 만든다.

> Q: rotation이 실패하면 어떻게 하나요?
> 의도: fallback과 blast radius 이해 확인
> 핵심: last-known-good와 staged rotation, emergency revoke가 필요하다.

> Q: 감사 로그가 왜 필요한가요?
> 의도: 비밀 접근 추적 이해 확인
> 핵심: 누가 언제 어떤 비밀을 썼는지 남겨야 사고를 복구할 수 있다.

## 한 줄 정리

Secrets distribution system은 짧은 수명의 credential과 암호화된 비밀을 안전하게 전달하고 회전하는 중앙 신뢰 계층이다.


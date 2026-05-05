---
schema_version: 3
title: Workload Identity / Long-Lived Service Account Keys
concept_id: security/workload-identity-vs-long-lived-service-account-keys
canonical: false
category: security
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- workload-identity-over-static-keys
- service-account-key-rotation-risk
- sts-vs-key-file
aliases:
- workload identity
- service account key
- long-lived key
- identity federation
- short-lived credential
- token exchange
- metadata service
- cloud auth
- pod identity
- keyless auth
- attestation
symptoms:
- 서비스 계정 키 파일을 배포에 넣어도 되는지 불안해요
- CI나 쿠버네티스에서 long-lived key 대신 뭘 써야 할지 모르겠어요
- key rotation이 자꾸 깨져서 정적 키를 계속 들고 가고 있어요
intents:
- comparison
- design
prerequisites:
- security/service-to-service-auth-mtls-jwt-spiffe
- security/secret-management-rotation-leak-patterns
next_docs:
- security/mtls-certificate-rotation-trust-bundle-rollout
- security/workload-identity-user-context-propagation-boundaries
- security/key-rotation-runbook
linked_paths:
- contents/security/service-to-service-auth-mtls-jwt-spiffe.md
- contents/security/mtls-certificate-rotation-trust-bundle-rollout.md
- contents/security/secret-management-rotation-leak-patterns.md
- contents/security/key-rotation-runbook.md
- contents/security/envelope-encryption-kms-basics.md
- contents/security/hardware-backed-keys-attestation.md
confusable_with:
- security/service-to-service-auth-mtls-jwt-spiffe
- security/secret-management-rotation-leak-patterns
- security/hardware-backed-keys-attestation
forbidden_neighbors: []
expected_queries:
- 쿠버네티스에서 service account key 파일 없이 인증하는 방법이 뭐야?
- workload identity가 static key보다 안전한 이유를 운영 관점에서 설명해줘
- CI 로그에 클라우드 키가 노출됐을 때 다음 구조를 어떻게 바꿔야 해?
- short-lived credential과 long-lived key를 언제 갈라서 봐야 하나요
- STS나 federation으로 키 없는 서버 인증을 한다는 게 무슨 뜻이야
- pod identity를 쓰면 key rotation 부담이 왜 줄어드는지 궁금해
contextual_chunk_prefix: |
  이 문서는 운영자가 쿠버네티스나 CI에서 정적 서비스 계정 키를 계속 둘지,
  workload identity와 federation으로 짧은 credential로 바꿀지 안전성과
  운영 부담 기준으로 결정하게 돕는 chooser다. 키 파일 유출 위험, pod가
  클라우드 권한을 받는 방식, STS로 잠깐 쓰는 토큰, 회전이 자꾸 깨지는 배포,
  keyless 인증 전환 같은 자연어 paraphrase가 본 문서의 선택 기준에 매핑된다.
---
# Workload Identity / Long-Lived Service Account Keys

> 한 줄 요약: workload identity는 실행 환경 자체가 신원 증명이 되게 만들고, long-lived service account key는 파일 하나만 유출돼도 장기 침해로 이어질 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)
> - [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)
> - [Secret Management, Rotation, Leak Patterns](./secret-management-rotation-leak-patterns.md)
> - [Key Rotation Runbook](./key-rotation-runbook.md)
> - [Envelope Encryption / KMS Basics](./envelope-encryption-kms-basics.md)

retrieval-anchor-keywords: workload identity, service account key, long-lived key, identity federation, short-lived credential, token exchange, metadata service, cloud auth, pod identity, keyless auth, attestation

---

## 핵심 개념

workload identity는 서비스나 pod 같은 실행 주체에 identity를 부여하는 방식이다.  
반대로 long-lived service account key는 다운로드 가능한 비밀 키 파일을 들고 다니며 인증하는 방식이다.

차이는 단순하다.

- workload identity: 환경이 바뀌어도 짧은 수명의 credential을 다시 받는다
- long-lived key: 한 번 새면 오래 재사용된다

그래서 현대 클라우드와 k8s 환경에서는 keyless 또는 short-lived 방식이 더 선호된다.

---

## 깊이 들어가기

### 1. long-lived key의 문제

서비스 계정 키 파일은 편해 보이지만 다음 위험이 있다.

- 저장소나 이미지에 들어간다
- 개발자 노트북에 남는다
- 로그나 backup에 섞인다
- rotation이 늦어진다

즉 파일 하나가 장기 bearer credential이 된다.

### 2. workload identity의 장점

workload identity는 보통 다음을 이용한다.

- kubelet / node attestation
- metadata service
- OIDC federation
- service mesh identity
- cloud IAM role assumption

장점:

- credential이 짧게 살아난다
- 정적 key 배포가 줄어든다
- 폐기와 회전이 쉬워진다

### 3. identity federation이 핵심이다

실제 현대 구조는 종종 외부 IdP나 cloud IAM과 연동한다.

- workload가 OIDC token을 받는다
- cloud provider가 이를 검증한다
- 짧은 수명 access token을 발급한다

이렇게 하면 정적 key를 복사하지 않아도 된다.

### 4. attestation과 최소 권한이 필요하다

identity를 부여한다고 끝이 아니다.

- 어떤 node/pod가 workload인지 확인해야 한다
- 어떤 role만 허용할지 제한해야 한다
- 어떤 namespace나 account만 신뢰할지 정의해야 한다

즉 identity와 authorization은 같이 설계해야 한다.

### 5. keyless가 무조건 가능한 것은 아니다

레거시 환경이나 일부 외부 API는 아직 long-lived key를 요구한다.

그럴 때는:

- key를 환경변수나 repo에 두지 않는다
- secret manager와 vault를 쓴다
- rotation runbook을 준비한다
- 사용 범위를 아주 좁힌다

---

## 실전 시나리오

### 시나리오 1: 서비스 계정 키가 CI 로그에 유출됨

대응:

- 즉시 폐기한다
- affected workloads를 식별한다
- workload identity로 전환 계획을 세운다

### 시나리오 2: k8s pod가 외부 API를 호출해야 함

대응:

- pod identity 또는 federation을 쓴다
- short-lived token을 받는다
- long-lived secret을 컨테이너에 넣지 않는다

### 시나리오 3: key rotation이 자주 실패함

대응:

- keyless federation을 우선 검토한다
- key rotation runbook을 붙인다
- KMS나 secret manager로 통합한다

---

## 코드로 보기

### 1. short-lived credential 요청 개념

```java
public AccessToken getWorkloadToken() {
    return stsClient.exchange(subjectToken, "storage.read");
}
```

### 2. long-lived key 사용 예시

```java
public Client initWithKey(Path keyFile) {
    return Client.builder()
        .serviceAccountKey(keyFile)
        .build();
}
```

### 3. 권장 흐름

```text
1. workload가 실행 환경으로부터 identity를 증명한다
2. federation 또는 STS로 짧은 credential을 받는다
3. 작업이 끝나면 credential은 자연스럽게 만료된다
4. long-lived key는 예외적으로만 남긴다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| workload identity | key 유출 위험이 낮다 | 환경 연동이 필요하다 | 현대 클라우드/k8s |
| long-lived service account key | 단순하다 | 유출 시 장기 침해로 이어진다 | 레거시, 예외 |
| federation + STS | 운영이 강하다 | 설정이 복잡하다 | 대규모 플랫폼 |
| vault-managed secret | 중앙 통제가 쉽다 | 런타임 의존이 늘어난다 | 민감한 시스템 |

판단 기준은 이렇다.

- 정적 키를 정말 써야 하는가
- workload를 attestation할 수 있는가
- 회전과 폐기를 자동화할 수 있는가
- 유출 시 blast radius를 제한할 수 있는가

---

## 꼬리질문

> Q: workload identity가 좋은 이유는 무엇인가요?
> 의도: 정적 key 대신 동적 credential의 장점을 이해하는지 확인
> 핵심: 짧은 수명의 credential로 장기 유출 위험을 줄이기 때문이다.

> Q: long-lived service account key가 위험한 이유는 무엇인가요?
> 의도: 파일형 비밀의 장기 재사용 문제를 아는지 확인
> 핵심: 한 번 유출되면 오래 재사용될 수 있기 때문이다.

> Q: federation은 무엇을 해결하나요?
> 의도: 외부 신원과 cloud auth를 연결하는 방식을 아는지 확인
> 핵심: 정적 키 배포 없이 짧은 credential을 교환하게 해준다.

> Q: keyless가 안 되는 환경에서는 어떻게 하나요?
> 의도: 현실적인 예외 처리를 아는지 확인
> 핵심: secret manager, rotation runbook, 최소 권한으로 좁힌다.

## 한 줄 정리

workload identity는 실행 환경을 신원으로 바꾸는 방식이고, long-lived service account key는 가능한 한 빨리 줄여야 할 레거시 위험이다.

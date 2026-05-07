---
schema_version: 3
title: Envelope Encryption / KMS Basics
concept_id: security/envelope-encryption-kms-basics
canonical: true
category: security
difficulty: advanced
doc_role: primer
level: advanced
language: mixed
source_priority: 70
mission_ids: []
review_feedback_tags:
- envelope encryption
- KMS
- data key
- master key
aliases:
- envelope encryption
- KMS
- data key
- master key
- CMK
- DEK
- key wrapping
- unwrap
- envelope
- rotation
- ciphertext
- key hierarchy
symptoms: []
intents:
- definition
- deep_dive
prerequisites: []
next_docs: []
linked_paths:
- contents/security/secret-management-rotation-leak-patterns.md
- contents/security/key-rotation-runbook.md
- contents/security/secret-scanning-credential-leak-response.md
- contents/security/https-hsts-mitm.md
- contents/security/mtls-certificate-rotation-trust-bundle-rollout.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Envelope Encryption / KMS Basics 핵심 개념을 설명해줘
- envelope encryption가 왜 필요한지 알려줘
- Envelope Encryption / KMS Basics 실무 설계 포인트는 뭐야?
- envelope encryption에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Envelope Encryption / KMS Basics를 다루는 primer 문서다. envelope encryption은 데이터 키와 마스터 키를 분리해 대량 데이터는 빠르게 암호화하고, 상위 키는 KMS로 더 강하게 보호하는 방식이다. 검색 질의가 envelope encryption, KMS, data key, master key처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Envelope Encryption / KMS Basics

> 한 줄 요약: envelope encryption은 데이터 키와 마스터 키를 분리해 대량 데이터는 빠르게 암호화하고, 상위 키는 KMS로 더 강하게 보호하는 방식이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Secret Management, Rotation, Leak Patterns](./secret-management-rotation-leak-patterns.md)
> - [Key Rotation Runbook](./key-rotation-runbook.md)
> - [Secret Scanning / Credential Leak Response](./secret-scanning-credential-leak-response.md)
> - [HTTPS / HSTS / MITM](./https-hsts-mitm.md)
> - [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)

retrieval-anchor-keywords: envelope encryption, KMS, data key, master key, CMK, DEK, key wrapping, unwrap, envelope, rotation, ciphertext, key hierarchy

---

## 핵심 개념

envelope encryption은 큰 데이터를 직접 마스터 키로 암호화하지 않고, 데이터 키(DEK)로 암호화한 뒤 그 DEK를 KMS가 보호하는 상위 키로 감싸는 방식이다.

왜 이렇게 하냐면:

- 대량 데이터 암호화는 빠르게 해야 한다
- 상위 키는 자주 노출되면 안 된다
- 키 회전은 데이터 전체를 다시 암호화하지 않게 하고 싶다

즉 envelope encryption은 성능과 보안을 동시에 맞추기 위한 키 계층화다.

---

## 깊이 들어가기

### 1. key hierarchy

보통 이렇게 나눈다.

- `root/master key`: 가장 상위 신뢰 키
- `KMS key/CMK`: 관리 가능한 상위 키
- `data key/DEK`: 실제 데이터 암호화에 쓰는 키

DEK는 데이터와 함께 사용되지만, 직접 평문으로 오래 남기지 않는다.

### 2. KMS가 하는 일

KMS는 대개 다음을 제공한다.

- key 생성
- key wrapping/unwrapping
- 접근 제어
- audit log
- rotation

중요한 건 KMS가 "모든 암호화를 대신 해주는 서비스"가 아니라는 점이다.  
대용량 데이터는 앱이 DEK로 직접 암호화하고, KMS는 DEK를 보호한다.

### 3. 왜 rotation이 쉬워지나

데이터 전체를 다시 암호화하는 건 비싸다.  
하지만 envelope 구조에서는 상위 키만 바꾸고 DEK를 다시 감쌀 수 있다.

- 대용량 ciphertext는 그대로 둔다
- DEK를 새 CMK로 re-wrap 한다
- 상위 키 교체 비용을 줄인다

### 4. access control이 암호화만큼 중요하다

KMS가 있어도 권한이 느슨하면 끝이다.

- 누가 decrypt를 요청할 수 있는가
- 어떤 서비스 역할만 unwrap 가능한가
- audit trail이 남는가

즉 envelope encryption은 암호화 설계이면서 접근 제어 설계다.

### 5. envelope encryption이 필요한 대표 경로

- DB column level encryption
- object metadata encryption
- secret at rest
- client-specific token wrapping
- backup encryption

---

## 실전 시나리오

### 시나리오 1: DB에 민감 값이 남아 있음

대응:

- 필드 단위 DEK를 둔다
- KMS로 DEK를 보호한다
- decrypt 권한을 최소화한다

### 시나리오 2: KMS 키 rotation이 필요함

대응:

- 기존 ciphertext는 유지한다
- DEK만 re-wrap한다
- decrypt 성공/실패 로그를 확인한다

### 시나리오 3: 운영자가 평문 키를 서버에 두려 함

대응:

- 평문 master key를 앱에 두지 않는다
- KMS IAM 정책과 audit log를 사용한다
- 로컬 파일 대신 managed key를 쓴다

---

## 코드로 보기

### 1. envelope 개념

```java
public EncryptedBlob encrypt(byte[] plaintext) {
    DataKey dataKey = kms.generateDataKey();
    byte[] ciphertext = symmetricEncrypt(dataKey.plaintextKey(), plaintext);
    return new EncryptedBlob(dataKey.encryptedKey(), ciphertext);
}
```

### 2. decrypt 개념

```java
public byte[] decrypt(EncryptedBlob blob) {
    byte[] plaintextDataKey = kms.decrypt(blob.encryptedKey());
    return symmetricDecrypt(plaintextDataKey, blob.ciphertext());
}
```

### 3. re-wrap 개념

```text
1. 새 CMK를 만든다
2. 기존 DEK를 새 CMK로 다시 감싼다
3. ciphertext는 그대로 둔다
4. decrypt 경로가 새 CMK를 보게 한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| direct master-key encryption | 단순하다 | 회전과 노출 위험이 크다 | 거의 비권장 |
| envelope encryption | 확장성과 회전에 유리하다 | 구현이 복잡하다 | 대부분의 실서비스 |
| per-record DEK | 격리가 좋다 | 메타데이터 관리가 늘어난다 | 고보안 데이터 |
| KMS only | 운영이 편하다 | 성능/비용을 고려해야 한다 | 소규모 시스템 |

판단 기준은 이렇다.

- 데이터 양이 많은가
- key rotation이 자주 필요한가
- decrypt 권한을 세밀하게 나눠야 하는가
- audit log가 필요한가

---

## 꼬리질문

> Q: envelope encryption의 핵심 이점은 무엇인가요?
> 의도: 데이터 키와 상위 키 분리를 아는지 확인
> 핵심: 대용량 데이터는 빠르게 암호화하고 상위 키는 강하게 보호할 수 있다.

> Q: KMS는 무엇을 해주나요?
> 의도: KMS의 역할 경계를 아는지 확인
> 핵심: key 관리, wrapping, 권한, audit, rotation을 돕는다.

> Q: 왜 전체 데이터를 다시 암호화하지 않아도 되나요?
> 의도: re-wrap의 의미를 이해하는지 확인
> 핵심: 데이터 자체는 유지하고 DEK만 다시 감싸면 되기 때문이다.

> Q: 접근 제어가 왜 중요한가요?
> 의도: 암호화만으로는 부족하다는 점을 아는지 확인
> 핵심: decrypt 권한이 넓으면 암호화가 있어도 안전하지 않다.

## 한 줄 정리

envelope encryption은 데이터와 키를 분리해 성능과 보안을 모두 챙기는 키 계층 설계다.

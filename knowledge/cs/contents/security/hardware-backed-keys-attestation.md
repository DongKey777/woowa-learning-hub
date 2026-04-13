# Hardware-Backed Keys / Attestation

> 한 줄 요약: hardware-backed key는 키를 소프트웨어 저장소가 아니라 TPM, Secure Enclave, HSM 같은 하드웨어 경계에 묶어 유출 위험을 줄인다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [WebAuthn / Passkeys / Phishing-Resistant Login](./webauthn-passkeys-phishing-resistant-login.md)
> - [Workload Identity / Long-Lived Service Account Keys](./workload-identity-vs-long-lived-service-account-keys.md)
> - [Envelope Encryption / KMS Basics](./envelope-encryption-kms-basics.md)
> - [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)
> - [Key Rotation Runbook](./key-rotation-runbook.md)

retrieval-anchor-keywords: hardware-backed keys, attestation, TPM, Secure Enclave, HSM, key protection, non-exportable key, device attestation, platform attestation, hardware root of trust

---

## 핵심 개념

hardware-backed key는 개인키를 메모리나 파일이 아니라 하드웨어 보안 경계에 저장하는 방식이다.  
핵심은 key를 "보관"하는 것보다 "반출 불가"하게 만드는 데 있다.

대표 경계:

- TPM
- Secure Enclave
- Android Keystore
- HSM

이런 구조는 키 탈취와 복제를 어렵게 한다.

---

## 깊이 들어가기

### 1. 왜 non-exportable이 중요한가

일반 소프트웨어 키는 파일이나 메모리에서 추출될 수 있다.

- 디스크 유출
- memory dump
- malware
- accidental logging

hardware-backed key는 이런 추출을 어렵게 만든다.

### 2. attestation은 무엇을 증명하나

attestation은 이 키가 믿을 수 있는 하드웨어 환경에서 생성되었음을 증명하는 메커니즘이다.

- device attestation
- platform attestation
- key attestation

하지만 attestation을 무조건 믿으면 안 된다.

- 정책상 어떤 attestation을 허용할지 정해야 한다
- privacy tradeoff가 있다
- 공급자와 플랫폼 차이를 고려해야 한다

### 3. 어디에 쓰나

- passkey
- device-bound service credential
- mTLS private key
- signing key protection
- code signing

### 4. HSM과 client hardware-backed key는 다르다

- HSM: 서버/인프라 쪽에서 키를 보호
- Secure Enclave/TPM: 클라이언트나 device 쪽에서 키를 보호

둘은 역할이 다르지만 "키를 밖으로 꺼내지 않는다"는 점은 같다.

### 5. 운영의 핵심은 회전과 복구다

hardware-backed라고 해서 운영이 쉬워지지는 않는다.

- 기기 분실
- attestation 실패
- platform change
- key rollover

복구 경로와 key lifecycle을 같이 설계해야 한다.

---

## 실전 시나리오

### 시나리오 1: passkey나 device credential을 hardware-backed로 유지하고 싶다

대응:

- platform attestation을 검토한다
- fallback과 recovery를 준비한다
- attestation 정책을 너무 강하게 고정하지 않는다

### 시나리오 2: 서비스 signing key를 소프트웨어에 두기 싫다

대응:

- HSM 또는 KMS-backed signing을 쓴다
- key export를 금지한다
- rotation runbook을 준비한다

### 시나리오 3: attestation이 환경마다 다르게 실패함

대응:

- allowlist 정책을 세분화한다
- 운영 환경과 사용자 환경을 분리한다
- attestation failure를 곧바로 fatal로 보지 않는다

---

## 코드로 보기

### 1. non-exportable key 개념

```java
public KeyPair generateHardwareBackedKey() {
    return keyStore.generateNonExportableKey("signing-key");
}
```

### 2. attestation check 개념

```java
public void verifyAttestation(AttestationReport report) {
    if (!attestationPolicy.isTrusted(report)) {
        throw new SecurityException("untrusted hardware attestation");
    }
}
```

### 3. rotation with hardware keys

```text
1. 새 hardware-backed key를 생성한다
2. attestation을 확인한다
3. signer와 verifier를 점진적으로 전환한다
4. old key를 폐기한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| software key | 단순하다 | 추출이 쉽다 | 낮은 위험 |
| hardware-backed key | 추출이 어렵다 | 운영과 호환성이 복잡하다 | 민감한 키 |
| HSM | 서버 키 보호가 강하다 | 비용과 운영 부담이 있다 | signing, encryption |
| device attestation | 신뢰도를 높인다 | privacy와 호환성 이슈가 있다 | 고보안 device flows |

판단 기준은 이렇다.

- 키가 유출되면 피해가 큰가
- 키를 외부로 내보내면 안 되는가
- attestation 정책을 운영할 수 있는가
- 회전과 복구 경로가 준비돼 있는가

---

## 꼬리질문

> Q: hardware-backed key가 왜 중요한가요?
> 의도: 키 추출 방지의 의미를 아는지 확인
> 핵심: 소프트웨어 저장소보다 반출과 복제가 어렵기 때문이다.

> Q: attestation은 무엇을 증명하나요?
> 의도: 하드웨어 신뢰 근거를 이해하는지 확인
> 핵심: key가 신뢰 가능한 하드웨어에서 만들어졌다는 점이다.

> Q: HSM과 Secure Enclave의 차이는 무엇인가요?
> 의도: 서버와 디바이스 경계를 구분하는지 확인
> 핵심: HSM은 서버측, Secure Enclave는 디바이스측 보호다.

> Q: hardware-backed라고 운영이 쉬워지나요?
> 의도: lifecycle과 recovery의 중요성을 아는지 확인
> 핵심: 아니요. 회전과 복구가 여전히 필요하다.

## 한 줄 정리

hardware-backed key와 attestation은 키 추출과 복제를 줄이지만, 회전과 복구와 정책 운영이 같이 있어야 완성된다.

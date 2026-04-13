# Device Binding Caveats

> 한 줄 요약: device binding은 세션이나 토큰을 특정 기기와 묶어 재사용을 줄이지만, 기기 변경, 복구, 공유 기기, 프라이버시, 위조 가능성을 함께 고려해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DPoP / Token Binding Basics](./dpop-token-binding-basics.md)
> - [Hardware-Backed Keys / Attestation](./hardware-backed-keys-attestation.md)
> - [Anti-Automation / Device Fingerprint Caveats](./anti-automation-device-fingerprint-caveats.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)

retrieval-anchor-keywords: device binding, device-bound session, token binding, device key, device identity, cloned device, shared device, recovery, privacy, mobile device migration, key rotation

---

## 핵심 개념

device binding은 인증 세션이나 refresh token을 어떤 device key나 device identity에 묶어 다른 환경에서 재사용하기 어렵게 만드는 설계다.

장점:

- 탈취된 토큰의 재사용을 줄인다
- 계정 탈취 후 다른 기기에서의 악용을 막는다
- high-risk action에 device continuity를 쓸 수 있다

하지만 caveat가 많다.

- 새 기기로 옮길 때 불편하다
- 기기 분실 시 복구가 어렵다
- shared device에서는 오탐이 생긴다
- binding proof가 위조되거나 복제될 수 있다

즉 device binding은 강한 부가 신호이지, 절대적인 신원 보증이 아니다.

---

## 깊이 들어가기

### 1. 무엇에 바인딩하나

가능한 대상:

- hardware-backed key
- platform attestation
- secure enclave identity
- device registration record

주의:

- device fingerprint와 혼동하면 안 된다
- 단순 mutable device id는 약하다

### 2. 이동성과 안전성의 tradeoff

binding이 강할수록:

- 새 폰 로그인
- 앱 재설치
- OS migration
- 백업 복원

이 어려워질 수 있다.

### 3. shared device 문제

가족 공용 기기, 회사 태블릿, 키오스크는 device binding과 충돌할 수 있다.

- 사용자별 분리
- short-lived session
- step-up auth
- recovery path

를 같이 고려해야 한다.

### 4. 복구 경로가 가장 취약할 수 있다

device binding을 우회하는 가장 쉬운 길은 복구다.

- 이메일 reset
- support override
- recovery code

이 경로가 느슨하면 binding이 무력해진다.

### 5. 민감 작업에만 부분 적용할 수도 있다

모든 요청에 강한 binding을 걸기보다:

- 로그인 유지
- 새 기기 등록
- 출금/비밀번호 변경

같은 작업에만 추가 검증으로 쓰는 것이 현실적이다.

---

## 실전 시나리오

### 시나리오 1: 새 기기 로그인에서 차단이 너무 많음

대응:

- device binding을 step-up 신호로 낮춘다
- 복구 경로를 분리한다
- 기기 등록 정책을 UX와 맞춘다

### 시나리오 2: 공격자가 토큰을 복사했지만 다른 기기에서 못 씀

대응:

- device-bound session이나 key binding을 유지한다
- replay detection과 함께 쓴다
- refresh token family revoke와 연결한다

### 시나리오 3: shared device에서 가족이 번갈아 로그인함

대응:

- device binding 강도를 낮춘다
- user-specific profile 분리를 둔다
- step-up auth를 더 자주 쓴다

---

## 코드로 보기

### 1. device registration 개념

```java
public DeviceRecord registerDevice(User user, PublicKey deviceKey) {
    return deviceRepository.save(new DeviceRecord(user.id(), deviceKey, Instant.now()));
}
```

### 2. binding check 개념

```java
public void verifyDeviceBinding(UserPrincipal user, DeviceProof proof) {
    if (!deviceRegistry.matches(user.id(), proof.deviceKey())) {
        throw new SecurityException("device binding mismatch");
    }
}
```

### 3. fallback 정책

```text
1. device binding은 보조 신호로 쓴다
2. 기기 이동과 복구 경로를 별도 설계한다
3. shared device는 예외 정책을 둔다
4. 민감 작업에만 강하게 적용한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| strong device binding | 재사용을 줄인다 | 이동/복구가 어렵다 | 고위험 |
| soft device binding | UX가 낫다 | 방어가 약하다 | 일반 서비스 |
| device binding + step-up | 현실적이다 | 설계가 복잡하다 | 대부분 |
| no binding | 단순하다 | 토큰 재사용이 쉽다 | 낮은 위험 |

판단 기준은 이렇다.

- 기기 변경이 얼마나 잦은가
- shared device가 있는가
- 복구 경로를 얼마나 강하게 만들 수 있는가
- binding proof를 신뢰할 수 있는가

---

## 꼬리질문

> Q: device binding은 무엇을 막나요?
> 의도: 토큰 재사용 감소 목적을 아는지 확인
> 핵심: 다른 기기에서의 재사용을 줄인다.

> Q: 왜 만능이 아닌가요?
> 의도: 이동성, 복구, shared device 문제를 아는지 확인
> 핵심: 기기 변경과 복구 경로가 어렵고 우회도 가능하기 때문이다.

> Q: fingerprint와 device binding은 같은가요?
> 의도: 추적 신호와 cryptographic binding을 구분하는지 확인
> 핵심: 아니다. binding은 더 강한 기기 결합이다.

> Q: 어디에 부분 적용하는 게 좋나요?
> 의도: 민감 작업 중심 설계를 아는지 확인
> 핵심: 새 기기 등록, 비밀번호 변경, 출금 같은 고위험 작업이다.

## 한 줄 정리

device binding은 강력한 보조 방어지만, 기기 이동성과 복구 경로를 함께 설계하지 않으면 운영에서 쉽게 깨진다.

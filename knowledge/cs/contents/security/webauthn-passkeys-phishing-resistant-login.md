---
schema_version: 3
title: WebAuthn / Passkeys / Phishing-Resistant Login
concept_id: security/webauthn-passkeys-phishing-resistant-login
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- WebAuthn
- passkey
- phishing-resistant login
- public key credential
aliases:
- WebAuthn
- passkey
- phishing-resistant login
- public key credential
- authenticator
- origin binding
- RP ID
- attestation
- assertion
- user verification
- discoverable credential
- WebAuthn / Passkeys / Phishing-Resistant Login
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/authentication-vs-authorization.md
- contents/security/xss-csrf-spring-security.md
- contents/security/password-storage-bcrypt-scrypt-argon2.md
- contents/security/oauth2-authorization-code-grant.md
- contents/security/jwt-deep-dive.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- WebAuthn / Passkeys / Phishing-Resistant Login 핵심 개념을 설명해줘
- WebAuthn가 왜 필요한지 알려줘
- WebAuthn / Passkeys / Phishing-Resistant Login 실무 설계 포인트는 뭐야?
- WebAuthn에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 WebAuthn / Passkeys / Phishing-Resistant Login를 다루는 deep_dive 문서다. passkey는 "비밀번호를 대신하는 로그인 수단"이 아니라, origin에 묶인 공개키 인증으로 피싱과 재사용 공격을 구조적으로 줄이는 방법이다. 검색 질의가 WebAuthn, passkey, phishing-resistant login, public key credential처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# WebAuthn / Passkeys / Phishing-Resistant Login

> 한 줄 요약: passkey는 "비밀번호를 대신하는 로그인 수단"이 아니라, origin에 묶인 공개키 인증으로 피싱과 재사용 공격을 구조적으로 줄이는 방법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - [Password Storage: bcrypt / scrypt / Argon2](./password-storage-bcrypt-scrypt-argon2.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)

retrieval-anchor-keywords: WebAuthn, passkey, phishing-resistant login, public key credential, authenticator, origin binding, RP ID, attestation, assertion, user verification, discoverable credential

---

## 핵심 개념

WebAuthn은 브라우저와 인증기(authenticator)가 협력해서 공개키 기반 인증을 수행하는 표준이다.  
passkey는 WebAuthn을 사용자가 쉽게 쓰도록 만든 경험 중심 이름에 가깝다.

핵심은 비밀번호와 다르게 다음 성질을 갖는다는 점이다.

- 서버가 비밀을 저장하지 않는다
- 브라우저 origin에 묶인다
- 피싱 사이트로는 같은 credential을 재사용할 수 없다
- 생체인식이나 디바이스 잠금과 결합할 수 있다

즉 passkey는 "기억해야 할 비밀"을 없애는 게 아니라, "서명 가능한 신원"으로 바꾸는 방식이다.

---

## 깊이 들어가기

### 1. WebAuthn은 무엇을 보장하나

WebAuthn 흐름은 크게 registration과 authentication으로 나뉜다.

- registration: 새 공개키를 서버에 등록한다
- authentication: challenge에 대해 개인키로 서명한 assertion을 보낸다

중요한 보장은 다음과 같다.

- 개인키는 기기 밖으로 나오지 않는다
- 서명은 특정 `origin`과 `RP ID`에 묶인다
- 공격자가 비슷한 UI를 보여줘도 다른 origin이면 재사용이 어렵다

### 2. passkey가 피싱에 강한 이유

피싱 사이트의 핵심은 사용자를 속여 자격 증명을 입력하게 만드는 것이다.  
passkey는 credential이 웹사이트 origin에 묶이므로, 가짜 사이트가 같은 credential을 받아쓰지 못한다.

이건 비밀번호와 본질적으로 다르다.

- 비밀번호는 입력하면 끝이다
- passkey는 서명 대상이 origin과 challenge에 묶인다

그래서 "문자열 탈취"보다 "정당한 origin에서만 서명 가능"이 핵심 방어가 된다.

### 3. attestation과 assertion은 다르다

- `attestation`: 어떤 종류의 인증기가 등록되었는지에 대한 증명
- `assertion`: 실제 로그인 시 챌린지에 대한 응답

실무에서는 attestation을 너무 강하게 믿지 않는다.

- 기기 모델 식별이 민감할 수 있다
- 정책상 attestation을 최소화할 수 있다
- 로그인 성공의 본질은 assertion 검증이다

### 4. discoverable credential과 usernameless login

passkey는 사용자를 username 입력 없이 로그인시키는 흐름도 지원한다.

- 브라우저나 플랫폼이 저장된 credential을 찾는다
- 사용자는 기기 잠금이나 생체인식만 통과하면 된다

하지만 이 편의성은 다음과 함께 봐야 한다.

- 계정 복구 경로
- 다중 디바이스 동기화
- 분실 기기 처리
- fallback login 정책

### 5. fallback이 없으면 운영이 어려워진다

passkey가 좋아도 현실에서는 늘 예외가 있다.

- 플랫폼이 WebAuthn을 완전히 지원하지 않는다
- 사용자가 새 기기로 옮겼다
- 기업 환경에서 생체인식이 제한된다

그래서 보통 다음과 같이 설계한다.

- passkey를 primary로 둔다
- 복구 코드를 별도로 둔다
- 기존 비밀번호 또는 OTP를 제한적 fallback으로 둔다
- 계정 복구는 더 엄격하게 검증한다

---

## 실전 시나리오

### 시나리오 1: 피싱 사이트가 사용자의 passkey를 훔치려 함

문제:

- 공격자가 로그인 페이지를 복제한다
- 사용자는 비슷한 화면에서 로그인한다고 착각한다

대응:

- credential은 origin-bound이므로 다른 origin에서 재사용되지 않는다
- 사용자가 실제 origin을 확인하도록 UX를 설계한다
- 이메일 링크 로그인보다 passkey를 우선한다

### 시나리오 2: 기기 분실 후 계정이 잠길까 걱정됨

문제:

- passkey만 쓰면 새 기기 로그인 경로가 막힐 수 있다

대응:

- 계정 복구 경로를 따로 둔다
- 복구 시에는 stronger verification을 요구한다
- 등록된 passkey 목록과 revoke 기능을 제공한다

### 시나리오 3: 여러 기기 간 동기화가 불안함

문제:

- platform passkey sync 정책이 사용자 기대와 다르다

대응:

- 동기화 가능 credential과 device-bound credential의 차이를 설명한다
- 지원 기기 기준을 문서화한다
- passkey 외 fallback을 정리한다

---

## 코드로 보기

### 1. registration challenge 발급 개념

```java
public PublicKeyCredentialCreationOptions beginRegistration(User user) {
    String challenge = challengeService.issue(user.id());

    return PublicKeyCredentialCreationOptions.builder()
        .rp(RelyingPartyEntity.builder()
            .id("example.com")
            .name("Example")
            .build())
        .user(UserEntity.builder()
            .id(user.id().toString().getBytes(StandardCharsets.UTF_8))
            .name(user.email())
            .displayName(user.displayName())
            .build())
        .challenge(challenge.getBytes(StandardCharsets.UTF_8))
        .build();
}
```

### 2. assertion 검증 개념

```java
public void verifyAssertion(String credentialId, byte[] clientDataJSON, byte[] authenticatorData, byte[] signature) {
    Challenge challenge = challengeService.consume();
    PublicKey publicKey = credentialRepository.findPublicKeyByCredentialId(credentialId);

    webauthnVerifier.verify(
        publicKey,
        challenge.value(),
        clientDataJSON,
        authenticatorData,
        signature,
        "example.com"
    );
}
```

### 3. 계정 복구 정책

```text
1. passkey를 기본 인증 수단으로 둔다
2. fallback은 제한적으로만 제공한다
3. recovery path는 더 높은 검증 강도를 요구한다
4. 등록/삭제/새 디바이스 추가는 별도 감사 로그를 남긴다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| passkey only | 피싱에 강하고 UX가 좋다 | 복구와 호환성 설계가 어렵다 | 소비자 대상, modern browser 중심 |
| passkey + fallback | 운영이 현실적이다 | fallback이 약점이 될 수 있다 | 대부분의 서비스 |
| password only | 구현이 쉽다 | 피싱과 재사용에 취약하다 | 점진적 전환 전 |
| passkey + device binding | 더 강하다 | 기기 이동성이 떨어진다 | 높은 보안 요구 |

판단 기준은 이렇다.

- 피싱이 주된 위협인가
- 계정 복구 UX를 얼마나 허용할 수 있는가
- 플랫폼 호환성을 얼마나 넓게 가져가야 하는가
- fallback 경로가 다시 취약점이 되지 않는가

---

## 꼬리질문

> Q: passkey가 비밀번호보다 안전한 이유는 무엇인가요?
> 의도: origin-bound 공개키 인증의 핵심을 이해하는지 확인
> 핵심: 비밀을 입력하지 않고, 같은 credential을 피싱 origin에서 재사용할 수 없기 때문이다.

> Q: attestation과 assertion의 차이는 무엇인가요?
> 의도: 등록 단계와 로그인 단계의 역할을 구분하는지 확인
> 핵심: attestation은 등록 장치의 증명, assertion은 로그인 시 챌린지 응답이다.

> Q: passkey만 쓰면 계정 복구는 끝나나요?
> 의도: 운영 현실을 이해하는지 확인
> 핵심: 아니다. 분실 기기와 fallback을 고려한 복구 경로가 필요하다.

> Q: 사용자에게 origin 확인이 왜 중요한가요?
> 의도: 피싱 방어가 UX와 연결되는지 확인
> 핵심: passkey는 origin-bound이므로 진짜 사이트에서만 써야 한다.

## 한 줄 정리

WebAuthn/passkey는 비밀번호를 더 복잡하게 만드는 기술이 아니라, 피싱에 강한 origin-bound 로그인 체계로 바꾸는 기술이다.

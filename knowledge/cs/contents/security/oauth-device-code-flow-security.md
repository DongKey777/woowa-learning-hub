# OAuth Device Code Flow / Security Model

> 한 줄 요약: Device Code Flow는 브라우저가 없는 기기를 위한 OAuth 흐름이지만, 코드 노출, phishing, polling, user verification을 같이 설계해야 안전하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [OIDC, ID Token, UserInfo](./oidc-id-token-userinfo-boundaries.md)

retrieval-anchor-keywords: device code flow, device authorization, user code, verification URI, polling, OAuth, limited input device, phishing, one-time code, cross-device login

---

## 핵심 개념

Device Code Flow는 TV, CLI, 콘솔, IoT처럼 브라우저 입력이 어려운 기기에서 사용자를 인증할 때 쓰는 OAuth 흐름이다.  
기기는 짧은 `device_code`와 사람이 입력할 `user_code`를 얻고, 사용자는 다른 브라우저에서 verification URI에 들어가 승인한다.

이 흐름의 핵심은 편의가 아니라 제약된 입력 환경을 안전하게 다루는 것이다.

- 기기는 비밀번호를 직접 받지 않는다
- 사용자는 별도 브라우저에서 승인한다
- 기기는 토큰 endpoint를 polling한다

즉 device code flow는 "브라우저 없는 기기용 authorization code"에 가깝지만, 공격면이 다르다.

---

## 깊이 들어가기

### 1. device code flow의 본질

흐름:

1. 기기가 device authorization request를 보낸다
2. 서버가 `device_code`, `user_code`, `verification_uri`를 돌려준다
3. 사용자가 다른 기기에서 `user_code`를 입력한다
4. 승인되면 기기가 token endpoint를 polling해서 토큰을 얻는다

장점:

- 제한된 입력 기기에서 로그인 가능
- 비밀번호를 기기에 입력하지 않아도 된다
- cross-device UX가 좋다

### 2. 가장 큰 위험은 user_code phishing이다

공격자가 가짜 verification page를 만들 수 있다.

- 사용자가 다른 사이트에 user_code를 입력한다
- 공격자가 그 code를 자기 device와 연결할 수 있다

그래서 verification URI는 매우 신뢰 가능한 출처여야 한다.

### 3. polling은 rate limit과 결합해야 한다

기기는 승인될 때까지 polling한다.

- 너무 자주 polling하면 auth server 부하가 커진다
- 너무 느리면 UX가 나빠진다
- 잘못하면 brute force나 enumeration에 악용된다

그래서 polling interval과 backoff, rate limit이 필요하다.

### 4. device code와 user code는 다르다

- `device_code`: 기기가 쓰는 비밀성 높은 코드
- `user_code`: 사용자가 입력하는 짧은 코드

user_code는 기억하기 쉽지만 추측되기 쉬우므로 짧은 유효 시간과 공간 제한이 필요하다.

### 5. 승인 후에도 token 보관 전략이 필요하다

CLI나 device는 토큰 저장 위치가 브라우저와 다르다.

- local file
- OS credential store
- secure enclave
- hardware-backed storage

토큰이 오래 남지 않도록 refresh 정책도 같이 설계해야 한다.

---

## 실전 시나리오

### 시나리오 1: TV 앱에서 로그인해야 함

대응:

- device code flow를 쓴다
- verification URI를 휴대폰/PC에서 열도록 안내한다
- user_code는 짧은 TTL로 둔다

### 시나리오 2: CLI가 polling 폭주를 일으킴

대응:

- polling interval을 강제한다
- exponential backoff를 적용한다
- auth server에서 per-device rate limit을 둔다

### 시나리오 3: 피싱 사이트가 user_code를 가로챔

대응:

- verification page를 정확한 origin으로 한정한다
- 승인 화면에 device name, client name, scope를 크게 표시한다
- user에게 device 일치 확인을 요구한다

---

## 코드로 보기

### 1. device authorization request 개념

```java
public DeviceAuthResponse startDeviceFlow(String clientId) {
    return oauthClient.requestDeviceCode(clientId);
}
```

### 2. polling 개념

```java
public TokenPair pollToken(String deviceCode) {
    while (!clock.expired(deviceCode)) {
        try {
            return tokenEndpoint.exchangeDeviceCode(deviceCode);
        } catch (AuthorizationPendingException e) {
            sleep(pollInterval);
        }
    }
    throw new IllegalStateException("device code expired");
}
```

### 3. verification UI 개념

```text
1. user_code를 정확한 origin에서만 입력받는다
2. device name, scope, issuer를 보여준다
3. 승인 전에는 토큰이 발급되지 않는다
4. 승인 후 기기는 토큰을 안전하게 저장한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| device code flow | 입력 제한 기기에 잘 맞는다 | phishing과 polling 관리가 필요하다 | CLI, TV, 콘솔 |
| auth code + PKCE | 일반 브라우저에서 강하다 | browser가 필요하다 | SPA, mobile |
| password on device | 단순하다 | 피싱과 재사용에 약하다 | 지양 |
| cross-device approve | UX가 좋다 | verification origin 관리가 필요하다 | consumer devices |

판단 기준은 이렇다.

- 브라우저가 있는가
- 사용자가 다른 기기에서 승인할 수 있는가
- polling 부하를 감당할 수 있는가
- code 입력이 피싱에 악용되지 않게 할 수 있는가

---

## 꼬리질문

> Q: device code flow는 어떤 기기에 적합한가요?
> 의도: 제한 입력 환경을 이해하는지 확인
> 핵심: TV, CLI, 콘솔처럼 브라우저 입력이 어려운 기기다.

> Q: user_code가 왜 위험할 수 있나요?
> 의도: 피싱과 code 재사용을 아는지 확인
> 핵심: 가짜 verification page에 입력되면 탈취될 수 있다.

> Q: polling은 왜 조절해야 하나요?
> 의도: auth server 부하와 abuse를 이해하는지 확인
> 핵심: 너무 자주 하면 부하와 남용이 생기기 때문이다.

> Q: device_code와 user_code의 차이는 무엇인가요?
> 의도: 흐름 내 역할 분리를 이해하는지 확인
> 핵심: 하나는 기기용, 다른 하나는 사람이 입력하는 코드다.

## 한 줄 정리

Device Code Flow는 제한된 기기용 로그인 흐름이지만, user_code 피싱과 polling 남용을 같이 막아야 한다.

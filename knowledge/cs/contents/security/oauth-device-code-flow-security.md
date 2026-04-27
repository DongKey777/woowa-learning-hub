# OAuth Device Code Flow / Security Model

> 한 줄 요약: Device Code Flow는 브라우저가 없는 기기를 위한 OAuth 흐름이다. 로그인 창 redirect를 붙이는 대신, 다른 기기에서 승인하고 현재 기기는 polling으로 기다린다.

**난이도: 🔴 Advanced**

관련 문서:
- [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
- [Auth, Session, Token Master Note](../../master-notes/auth-session-token-master-note.md)
- [Browser Auth Frontend Backend Master Note](../../master-notes/browser-auth-frontend-backend-master-note.md)
- [Browser Session Security Master Note](../../master-notes/browser-session-security-master-note.md)
- [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md)
- [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
- [JWT 깊이 파기](./jwt-deep-dive.md)
- [OIDC, ID Token, UserInfo](./oidc-id-token-userinfo-boundaries.md)
- [Spring Security 아키텍처](../spring/spring-security-architecture.md)
- [System Design: Auth Session Troubleshooting Bridge](../system-design/README.md#system-design-auth-session-troubleshooting-bridge)

retrieval-anchor-keywords: device code flow, cli login oauth, tv login oauth, user code phishing, verification uri, wrong verification url, expired user code, slow_down error, authorization_pending, over aggressive polling, browserless login basics, device authorization, cross-device login, device code flow 뭐예요

---

## 이 문서를 어디에 붙여 읽나

- 질문이 `CLI 로그인`, `터미널 로그인`, `TV에서 코드 입력`, `브라우저 없는 기기 로그인`이면 이 문서가 첫 출발점이다. 이 경우 [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)나 [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)을 먼저 읽지 않는다.
- [Auth, Session, Token Master Note](../../master-notes/auth-session-token-master-note.md)나 [Browser Auth Frontend Backend Master Note](../../master-notes/browser-auth-frontend-backend-master-note.md)에서 "브라우저 callback이 없다"가 명확해질 때 내려오는 branch다.
- 브라우저 세션 hardening 자체가 목적이면 [Browser Session Security Master Note](../../master-notes/browser-session-security-master-note.md)로 돌아가고, security 카테고리에서 다른 OAuth branch를 다시 고르려면 [Security README: OAuth / Browser / BFF](./README.md#2-oauth--browser--bff)로 복귀한다.
- 승인 뒤 토큰 보관/회수 전략은 [Auth, Session, Token Master Note](../../master-notes/auth-session-token-master-note.md)에서 다시 정리한다.

---

## 30초 분기: 이 문서가 맞는 질문인가

먼저 이 한 문장으로 갈라 보면 된다.

> "지금 로그인하려는 주체가 자기 브라우저 callback을 직접 받을 수 있는가?"

| 질문 모습 | 먼저 읽을 문서 | 이유 |
|---|---|---|
| `CLI에서 로그인해야 해요`, `TV 화면에 코드가 뜨고 휴대폰으로 승인해요`, `브라우저가 없는 장비예요` | 이 문서 | 현재 기기는 브라우저 redirect를 끝까지 처리하지 못하고, 다른 기기 승인 + polling이 핵심이기 때문이다. |
| `구글 로그인 callback이 왜 이 URL로 와요`, `redirect_uri`, `PKCE`, `BFF`, `session cookie`가 문제예요 | [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md) | 브라우저 redirect와 callback hardening이 중심이기 때문이다. |

브라우저가 없는 장면에서 browser redirect 문서를 먼저 읽으면 `redirect_uri`, `SavedRequest`, `BFF cookie` 쪽으로 사고가 끌려간다. Device Code Flow는 출발점부터 다르다.

---

## 핵심 개념

Device Code Flow는 TV, CLI, 콘솔, IoT처럼 브라우저 입력이 어려운 기기에서 사용자를 인증할 때 쓰는 OAuth 흐름이다.

가장 쉬운 mental model은 이렇다.

- 지금 로그인하려는 기기는 "로그인 창을 끝까지 처리하는 곳"이 아니다
- 사용자는 휴대폰이나 PC 브라우저에서 승인한다
- 원래 기기는 "승인이 끝났는지 물어보며 기다리는 쪽"이다

즉 기기는 짧은 `device_code`와 사람이 입력할 `user_code`를 얻고, 사용자는 다른 브라우저에서 verification URI에 들어가 승인한다.

이 흐름의 핵심은 편의가 아니라 제약된 입력 환경을 안전하게 다루는 것이다.

- 기기는 비밀번호를 직접 받지 않는다
- 사용자는 별도 브라우저에서 승인한다
- 기기는 토큰 endpoint를 polling한다

즉 device code flow는 "브라우저 없는 기기용 authorization code"에 가깝지만, 공격면이 다르다.

### Authorization Code Grant와 무엇이 다른가

| 항목 | Authorization Code Grant | Device Code Flow |
|---|---|---|
| 로그인 UI가 열리는 곳 | 같은 브라우저 세션 안 | 다른 기기 브라우저 |
| 핵심 연결 방식 | `redirect_uri` callback | `user_code` + verification page |
| 현재 기기의 역할 | callback을 받고 세션을 이어감 | 승인 완료를 polling으로 기다림 |
| 초보자가 먼저 보는 문제 | redirect URI, PKCE, session fixation | phishing, verification origin, polling interval |

다음 한 걸음:

- polling/backoff와 code 남용 방어가 궁금하면 이 문서의 아래 `polling은 rate limit과 결합해야 한다`부터 이어 읽는다.
- 브라우저 callback hardening이 실제 문제였던 경우 [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)로 이동한다.
- 다른 security branch를 다시 고르려면 [Security README: Browserless / Cross-Device Login](./README.md#2-c-branch-point-browserless--cross-device-login)으로 돌아간다.

---

## CLI 로그인 증상 빠른 표

처음 배우는데 CLI login이 막히면 에러 이름보다 "지금 눈앞에서 무슨 일이 보이냐"로 고르는 편이 빠르다.

| 보이는 증상 | 보통 뜻 | 먼저 할 일 | 다음 step |
|---|---|---|---|
| `Code expired`, `expired_token`, `만료된 코드`가 뜬다 | `user_code`나 `device_code`의 TTL이 끝났다. 승인 화면을 오래 열어 두었거나 CLI가 너무 늦게 poll했다. | 새 device flow를 다시 시작하고, 화면에 새 `user_code`가 떴는지 확인한다. 예전 코드를 재사용하지 않는다. | polling 만료 동작은 이 문서의 [`polling은 rate limit과 결합해야 한다`](#3-polling은-rate-limit과-결합해야-한다)로 이어 읽고, category 분기로 돌아가려면 [Security README: Browserless / Cross-Device Login](./README.md#2-c-branch-point-browserless--cross-device-login)으로 복귀한다. |
| 브라우저에서 코드를 넣었는데 "없는 페이지", 다른 회사 로그인 화면, 철자가 다른 URL이 나온다 | verification URI를 잘못 열었거나 피싱 페이지일 수 있다. Device Code Flow의 핵심 위험이 여기다. | CLI가 보여준 `verification_uri`와 브라우저 주소창 origin이 정확히 같은지 다시 본다. 북마크나 검색 결과로 들어가지 않는다. | verification origin 확인 포인트는 이 문서의 [`가장 큰 위험은 user_code phishing이다`](#2-가장-큰-위험은-user_code-phishing이다)로 이어 읽는다. |
| CLI가 곧바로 반복 에러를 뿜거나 `slow_down`이 나온다 | polling 간격이 너무 짧다. 서버가 아직 승인 대기 중인데 과하게 재시도하고 있다. | CLI가 서버가 준 interval을 따르는지 보고, `slow_down`을 받으면 대기 시간을 늘린다. 승인 전에는 busy loop를 돌리지 않는다. | poll/backoff 설계는 이 문서의 [`polling은 rate limit과 결합해야 한다`](#3-polling은-rate-limit과-결합해야-한다)와 [Rate Limiting vs Brute Force Defense](./rate-limiting-vs-brute-force-defense.md)로 이어진다. |

이 표는 "증상으로 branch 고르기"용이다.

---

## 승인했는데도 CLI가 계속 기다리면

`authorization_pending`이 반복되면 이것부터 확인한다.

- 같은 로그인 시도에서 받은 최신 `device_code`를 poll하고 있는지 본다.
- 승인 직후 한두 번의 pending은 정상일 수 있다.
- CLI를 재시작했다면 예전 flow를 버리고 새 flow 하나만 남긴다.

다음 step:

- token 저장/후속 세션 연결이 궁금하면 [Auth, Session, Token Master Note](../../master-notes/auth-session-token-master-note.md)로 넘어간다.
- browser callback 문제가 실제 원인이면 [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)로 분기한다.
- 원리 자체를 잡고 싶으면 바로 아래 `깊이 들어가기`부터 읽는다.

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

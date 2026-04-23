# PKCE Failure Modes / Recovery

> 한 줄 요약: PKCE는 code 탈취를 줄이지만, challenge 저장 실패, verifier 분실, redirect/state 오류, 잘못된 client 분류가 있으면 여전히 깨질 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [OIDC, ID Token, UserInfo](./oidc-id-token-userinfo-boundaries.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - [Security README: Browser / Server Boundary deep dive catalog](./README.md#browser--server-boundary-deep-dive-catalog)

retrieval-anchor-keywords: PKCE, code_verifier, code_challenge, S256, authorization code, public client, verifier loss, replay, redirect_uri, state, OAuth2, authorization server, callback hardening, login completion hardening, verifier consume, post-login csrf token reset, BFF login completion, social login first post 403, state vs csrf token, browser server boundary catalog, security readme browser server boundary

## 이 문서 다음에 보면 좋은 문서

- PKCE가 Authorization Code 전체에서 정확히 어느 단계인지 다시 잡으려면 [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)로 돌아가 flow 전체를 본다.
- verifier consume 이후 cookie 기반 login completion과 후속 POST hardening으로 이어가려면 [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)로 이어진다.
- 브라우저 hardening 문서를 cluster로 다시 고르려면 [Security README: Browser / Server Boundary deep dive catalog](./README.md#browser--server-boundary-deep-dive-catalog)에서 redirect, session regeneration, browser-visible credential 축을 함께 고르면 된다.

---

## 핵심 개념

PKCE(Proof Key for Code Exchange)는 authorization code를 훔쳐도 토큰 교환을 못 하게 만드는 장치다.  
핵심은 code를 요청할 때 만든 `code_verifier`의 해시인 `code_challenge`를 같이 보내고, 토큰 교환 시 원본 verifier를 다시 제시하는 구조다.

이 문서의 초점은 "왜 PKCE가 필요한가"가 아니라 "PKCE가 실제로 어디서 깨지는가"다.

- verifier가 유실되면 사용자는 로그인 흐름을 다시 해야 한다
- challenge 저장이 잘못되면 코드 교환이 실패한다
- `plain` challenge를 허용하면 보안 강도가 약해진다
- `redirect_uri`와 `state` 검증이 느슨하면 code가 다른 세션으로 연결될 수 있다
- public client와 confidential client를 혼동하면 보안 모델이 무너진다

즉 PKCE는 단순 옵션이 아니라, 브라우저/모바일 환경에서 authorization code flow를 안전하게 쓰기 위한 상태 관리 프로토콜이다.

---

## 깊이 들어가기

### 1. PKCE가 막는 것과 못 막는 것

PKCE가 잘 막는 것:

- authorization code 탈취
- 중간자 또는 악성 앱의 code 재사용
- 브라우저 외부에서 code만 훔쳐가는 시도

PKCE가 못 막는 것:

- client가 verifier를 안전하게 저장하지 못하는 문제
- redirect_uri 오염
- state 생략
- token endpoint에서의 정책 오류

### 2. S256을 써야 하는 이유

PKCE는 `plain`과 `S256` 두 방식이 알려져 있지만, 실무에서는 `S256`이 기본이다.

- `plain`: challenge가 verifier와 사실상 같아 강도가 약함
- `S256`: verifier를 해시해서 노출 면적을 줄임

즉 challenge 자체가 노출되더라도 verifier를 바로 알 수 없게 해야 한다.

### 3. verifier 저장 실패가 매우 흔하다

클라이언트가 로그인 탭을 닫아버리거나, 앱이 재시작되면 verifier가 사라질 수 있다.

문제 패턴:

- 로그인 요청만 저장하고 verifier를 메모리에 둔다
- redirect 후 callback 시점에 verifier가 없다
- 사용자는 "로그인 실패"만 본다

대응:

- flow별 correlation id를 둔다
- browser session storage 또는 서버 세션에 verifier를 잠시 저장한다
- 실패 시 재시도 UX를 명확히 만든다

### 4. state와 PKCE는 대체재가 아니다

PKCE는 code 교환의 정당성을 높이고, state는 요청 연동과 CSRF를 돕는다.

- PKCE만 있으면 로그인 시작 세션과 callback 세션이 정확히 연결된다고 보장하지 않는다
- state만 있으면 code 탈취를 막지 못한다

둘은 서로 다른 문제를 푼다.

### 5. public client로 분류해야 할 때와 아닐 때

브라우저 SPA, 모바일 앱은 보통 public client다.

- client secret을 안전하게 지킬 수 없다
- PKCE가 사실상 필수다

반면 서버가 있는 confidential client는 더 많은 보호 수단을 가질 수 있다.

- redirect endpoint 제어
- server-side verifier 저장
- client secret 추가 검증

### 6. verifier 검증이 끝나도 login completion hardening은 남는다

PKCE exchange 성공은 "code를 훔쳐도 token endpoint를 못 통과한다"는 뜻이지, 브라우저 login completion 전체가 끝났다는 뜻은 아니다.

- `state`는 어떤 login 요청의 callback인지 묶는 값이다
- PKCE는 callback에 들어온 code가 원래 verifier를 가진 흐름인지 확인한다
- anti-CSRF token은 로그인 후 BFF/session cookie로 보내는 상태 변경 요청을 보호한다

즉 social login callback success와 첫 번째 POST `/api/...` success는 다른 gate다.

- callback 직후 session id를 재발급하지 않으면 익명 세션 continuation이 남는다
- authenticated session 기준 CSRF secret을 다시 만들지 않으면 첫 mutation이 `403`으로 깨지거나, 반대로 검증이 느슨해질 수 있다
- verifier는 1회성으로 consume하고, 실패는 안전한 restart UX로 돌려야 한다

flow 전체 그림은 [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md), post-login cookie/BFF hardening은 [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)로 이어 본다.

---

## 실전 시나리오

### 시나리오 1: callback에서 verifier를 못 찾아 로그인 실패

문제:

- 사용자가 다른 탭으로 이동했고 verifier가 사라졌다

대응:

- flow 시작 시점에 short-lived storage를 쓴다
- callback 실패를 재시도 가능한 오류로 분리한다
- 로그인 시작과 callback이 같은 browser context인지 확인한다

### 시나리오 2: redirect_uri가 느슨해서 code가 다른 엔드포인트로 감

문제:

- wildcard redirect 또는 prefix match를 쓴다

대응:

- exact match만 허용한다
- registered redirect uri를 고정한다
- `state`와 origin을 함께 본다

### 시나리오 3: 앱이 plain PKCE를 허용함

문제:

- 구현은 쉬워 보이지만 code challenge가 너무 약하다

대응:

- `S256`만 허용한다
- provider 설정과 클라이언트 설정을 모두 점검한다
- legacy client는 별도 migration 경로를 둔다

### 시나리오 4: social login callback은 성공했는데 첫 POST가 `403`이거나 반대로 너무 느슨함

문제:

- verifier consume까지만 성공 처리하고 authenticated session 기준 CSRF secret을 다시 안 만들었다
- 익명 단계 session/token을 그대로 재사용했다

대응:

- callback 성공 후 session id를 재발급한다
- authenticated session 기준으로 CSRF token을 새로 발급한다
- SPA는 새 token을 다시 bootstrap한 뒤 상태 변경 요청을 보낸다

---

## 코드로 보기

### 1. PKCE 생성 개념

```javascript
const verifier = base64url(randomBytes(32));
const challenge = base64url(sha256(verifier));

sessionStorage.setItem("pkce_verifier", verifier);
startOAuthLogin({ code_challenge: challenge, code_challenge_method: "S256" });
```

### 2. callback 처리 개념

```java
public TokenPair exchange(String code, String state, String flowId) {
    verifyState(state, flowId);
    String verifier = pkceStore.consume(flowId)
        .orElseThrow(() -> new IllegalStateException("missing code verifier"));

    return authServerClient.exchange(code, verifier);
}
```

### 3. exact redirect 검증

```text
1. redirect_uri는 사전 등록된 exact value만 허용한다
2. state는 흐름 연동용으로 사용한다
3. code_verifier는 짧게 저장하고 callback 후 즉시 제거한다
4. callback 성공 후 session id와 CSRF secret을 재발급한다
5. 실패 시 재인증 흐름을 명시적으로 제공한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| PKCE only | code 탈취 방어가 된다 | state/redirect 정책은 별도다 | public client 기본값 |
| PKCE + state | code 탈취와 세션 혼선을 함께 막는다 | 구현 포인트가 늘어난다 | SPA, mobile, 브라우저 |
| PKCE + exact redirect | open redirect 위험을 줄인다 | 관리가 엄격해진다 | 대부분의 실서비스 |
| plain challenge | 구현이 쉽다 | 강도가 약하다 | 거의 권장되지 않음 |

판단 기준은 이렇다.

- client가 비밀을 안전하게 보관할 수 있는가
- verifier를 어떤 저장소에 둘 것인가
- redirect_uri를 exact match로 묶을 수 있는가
- callback 실패를 재시도 가능하게 처리할 수 있는가

---

## 꼬리질문

> Q: PKCE가 막는 핵심 위협은 무엇인가요?
> 의도: code 탈취와 재사용 문제를 이해하는지 확인
> 핵심: authorization code 탈취 후 토큰 교환을 막는 것이다.

> Q: PKCE와 state는 왜 둘 다 필요한가요?
> 의도: 역할 분리를 이해하는지 확인
> 핵심: PKCE는 code 교환 보호, state는 요청 연동과 CSRF 대응이다.

> Q: S256을 왜 선호하나요?
> 의도: challenge 노출 강도를 아는지 확인
> 핵심: plain보다 verifier 노출 가능성을 줄이기 때문이다.

> Q: verifier가 사라지면 어떻게 해야 하나요?
> 의도: 실패 복구와 UX를 이해하는지 확인
> 핵심: 안전하게 재시작하고 다시 인증 흐름을 시작해야 한다.

## 한 줄 정리

PKCE는 "code를 훔쳐도 못 쓰게 하는 장치"지만, state, redirect_uri, verifier 저장까지 같이 설계하지 않으면 실전에서 쉽게 흔들린다.

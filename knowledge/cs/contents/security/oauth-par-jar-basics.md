# OAuth PAR / JAR Basics

> 한 줄 요약: PAR와 JAR는 OAuth 요청을 더 단단하게 만드는 장치다. 요청을 front-channel에 그대로 두지 않고, authorization request 자체를 서버가 미리 받거나 서명된 형태로 보호한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)
> - [Auth, Session, Token Master Note](../../master-notes/auth-session-token-master-note.md)
> - [Browser Auth Frontend Backend Master Note](../../master-notes/browser-auth-frontend-backend-master-note.md)
> - [Browser Session Security Master Note](../../master-notes/browser-session-security-master-note.md)
> - [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md)
> - [Open Redirect Hardening](./open-redirect-hardening.md)
> - [OIDC, ID Token, UserInfo](./oidc-id-token-userinfo-boundaries.md)
> - [Token Exchange / Impersonation Risks](./token-exchange-impersonation-risks.md)

retrieval-anchor-keywords: PAR, pushed authorization request, JAR, JWT secured authorization request, OAuth, front-channel, back-channel, authorization request, request object, signed request, exact redirect, oauth branch point, authorization request hardening branch, auth session token master note, browser auth master note, browser session master note, confidential client, token endpoint client auth, request hardening vs client auth, private_key_jwt, mTLS client auth

---

## 이 문서를 어디에 붙여 읽나

- [Auth, Session, Token Master Note](../../master-notes/auth-session-token-master-note.md), [Browser Auth Frontend Backend Master Note](../../master-notes/browser-auth-frontend-backend-master-note.md), [Browser Session Security Master Note](../../master-notes/browser-session-security-master-note.md)에서 redirect 흐름은 맞지만 authorization request hardening이 필요할 때 내려오는 branch다.
- 이후 browser hardening mainline으로 다시 합류하려면 [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md) 다음 [Open Redirect Hardening](./open-redirect-hardening.md)과 browser/session hardening 묶음으로 이어 가면 된다.
- PAR/JAR를 골라도 token endpoint에서 confidential client를 어떻게 증명할지는 남는다. back-channel client proof 분기는 [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)로 이어진다.

---

## 핵심 개념

OAuth authorization request는 기본적으로 브라우저를 통해 이동한다.  
이 경로는 편리하지만, 파라미터 조작과 노출 면적이 넓다.

PAR(Pushed Authorization Request):

- 클라이언트가 authorization request를 먼저 authorization server에 보낸다
- 서버는 request_uri 같은 참조값을 돌려준다
- 브라우저에는 짧은 참조만 보낸다

JAR(JWT Secured Authorization Request):

- authorization request 전체를 서명된 JWT로 포장한다
- 파라미터 변조를 어렵게 만든다
- 요청의 무결성을 높인다

즉 PAR는 "요청 내용을 front-channel에 덜 싣는 것"이고, JAR는 "요청 자체를 서명해 보호하는 것"이다.

---

## 깊이 들어가기

### 1. 왜 필요하나

일반 authorization request는 여러 파라미터를 가진다.

- client_id
- redirect_uri
- scope
- state
- code_challenge
- response_type

문제는 이 값들이 브라우저를 통과하면서 노출되거나 조작될 수 있다는 점이다.

### 2. PAR의 장점

PAR는 request를 back-channel로 먼저 보내기 때문에 다음을 줄인다.

- URL 길이 문제
- 파라미터 노출
- 공격자에 의한 일부 파라미터 주입

특히 rich scope, claims, extra request parameter가 많을 때 유용하다.

### 3. JAR의 장점

JAR는 authorization request를 JWT로 서명한다.

- request tampering을 어렵게 한다
- request 내용의 출처를 증명한다
- 일부 파라미터 변조를 막는다

하지만 서명만 있다고 완전해지는 건 아니다.

- redirect_uri exact match는 여전히 필요하다
- state와 PKCE도 여전히 필요하다
- request object 유효 기간도 짧게 유지해야 한다

### 4. PAR와 JAR는 함께 쓰일 수 있다

실무에서는 다음 조합이 가능하다.

- JAR로 request 전체 무결성을 높인다
- PAR로 front-channel 노출을 줄인다

둘 다 쓰면 복잡해지지만, 고보안 환경에서는 값어치가 있다.

다만 PAR/JAR는 authorization request hardening이지 token endpoint client authentication의 대체가 아니다. confidential client라면 PAR submitter나 code exchanger가 `client_secret_basic`, `private_key_jwt`, mTLS 중 무엇으로 자신을 증명할지도 별도로 정해야 하며, 그 선택지는 [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)에서 정리한다.

### 5. client 유형을 구분해야 한다

- public client는 요청 위변조와 노출에 더 약하다
- confidential client는 back-channel 활용이 쉽다
- 모바일/SPA는 PAR/JAR보다 PKCE와 exact redirect가 더 실용적인 경우가 많다

---

## 실전 시나리오

### 시나리오 1: scope가 많은 enterprise login

대응:

- PAR를 써서 request를 back-channel로 먼저 보낸다
- JAR로 request 무결성을 보강한다
- redirect_uri는 exact match로 제한한다

### 시나리오 2: authorization request 파라미터가 브라우저에서 노출됨

대응:

- front-channel에 넣는 파라미터를 줄인다
- request object를 사용한다
- state와 PKCE를 같이 유지한다

### 시나리오 3: request object가 오래 살아남음

대응:

- request_uri TTL을 짧게 둔다
- 한 번 사용한 request는 재사용하지 않는다
- 로깅에 request JWT 원문을 남기지 않는다

---

## 코드로 보기

### 1. PAR 개념

```java
public String pushAuthorizationRequest(AuthRequest request) {
    return authorizationServer.push(request);
}
```

### 2. JAR 개념

```java
public String buildRequestObject(AuthRequest request) {
    return jwtSigner.sign(request);
}
```

### 3. front-channel 최소화

```text
1. authorization request를 먼저 서버로 보낸다
2. 브라우저에는 짧은 참조만 보낸다
3. request object는 서명과 TTL을 가진다
4. redirect_uri, state, PKCE는 그대로 점검한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| PAR | front-channel 노출을 줄인다 | 구현이 늘어난다 | 보안 우선 |
| JAR | 요청 변조를 어렵게 한다 | 서명/검증이 추가된다 | 고보안 client |
| PAR + JAR | 둘의 장점을 합친다 | 운영 복잡도가 높다 | enterprise, regulated |
| plain OAuth request | 단순하다 | 노출과 변조에 약하다 | 일반적인 기본값 |

판단 기준은 이렇다.

- request 파라미터가 많은가
- front-channel 노출을 줄여야 하는가
- confidential client인가
- request 무결성을 서명으로 보장해야 하는가

---

## 꼬리질문

> Q: PAR와 JAR의 차이는 무엇인가요?
> 의도: 요청 전달 방식과 무결성 보호의 차이를 이해하는지 확인
> 핵심: PAR는 back-channel 선전송, JAR는 signed request object다.

> Q: PKCE가 있는데도 왜 PAR/JAR가 필요할 수 있나요?
> 의도: 서로 다른 공격면을 구분하는지 확인
> 핵심: PKCE는 code 교환 보호, PAR/JAR는 request 노출과 변조를 줄인다.

> Q: request object에 TTL이 왜 필요한가요?
> 의도: 재사용과 replay를 아는지 확인
> 핵심: 오래 살아 있으면 재사용될 수 있기 때문이다.

> Q: PAR를 쓰면 redirect_uri 검증이 사라지나요?
> 의도: 안전 장치가 대체가 아니라 보완임을 아는지 확인
> 핵심: 아니다. exact match는 여전히 필요하다.

> Q: PAR/JAR를 쓰면 client authentication 문제도 끝나나요?
> 의도: request hardening과 back-channel client proof를 구분하는지 확인
> 핵심: 아니다. PAR/JAR는 authorization request를 보호하고, token endpoint에서의 client auth 선택은 [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)로 따로 이어진다.

## 한 줄 정리

PAR는 OAuth 요청을 back-channel로 밀어내고, JAR는 그 요청 자체를 서명해 변조를 줄인다.

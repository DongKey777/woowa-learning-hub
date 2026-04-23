# OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS

> 한 줄 요약: OAuth의 어려운 지점은 사용자 로그인만이 아니라 token endpoint에서 "어떤 client가 토큰을 요청하는가"를 안전하게 증명하는 일이며, 공유 secret보다 비대칭 키와 채널 바인딩이 운영 사고를 줄이는 경우가 많다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [OAuth PAR / JAR Basics](./oauth-par-jar-basics.md)
> - [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md)
> - [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)
> - [mTLS Client Auth vs Certificate-Bound Access Token](./mtls-client-auth-vs-certificate-bound-access-token.md)
> - [JWK Rotation / Cache Invalidation / `kid` Rollover](./jwk-rotation-cache-invalidation-kid-rollover.md)
> - [Key Rotation Runbook](./key-rotation-runbook.md)
> - [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)
> - [Secret Management / Rotation / Leak Patterns](./secret-management-rotation-leak-patterns.md)

retrieval-anchor-keywords: OAuth client authentication, token endpoint auth, client_secret_basic, client_secret_post, private_key_jwt, client assertion, mutual TLS, confidential client, OAuth client credential proof, sender constrained token, client secret rotation, token endpoint security, certificate-bound token, authorization code backend client auth, PAR JAR follow-up, BFF confidential client, browser token boundary follow-up

---

## 핵심 개념

OAuth에서 자주 섞이는 질문이 있다.

- 사용자가 누구인가
- 어떤 앱이 이 토큰을 요청하는가
- 이 토큰이 어떤 리소스를 향하는가

첫 번째는 user authentication이고, 두 번째는 client authentication이다.  
Authorization Code Grant를 쓴다고 해서 client authentication이 자동으로 끝나는 것은 아니다.

특히 confidential client는 token endpoint에서 자기 정체를 따로 증명해야 한다.

- `client_secret_basic`
- `client_secret_post`
- `private_key_jwt`
- mTLS client authentication

어떤 방식을 고르느냐에 따라 leak surface, rotation 난이도, replay 방어, 프록시/로드밸런서 구성까지 달라진다.

즉 Authorization Code Grant, PAR/JAR, BFF가 "어디서 요청과 토큰을 다룰지"를 정한다면, 이 문서는 그 다음 질문인 "그 server-side client가 무엇으로 자신을 증명할지"를 다룬다.

---

## 깊이 들어가기

### 1. client authentication은 user authentication의 부속이 아니다

브라우저에서 사용자가 로그인에 성공했다고 해서, token endpoint를 호출하는 백엔드 client도 자동으로 신뢰되는 것은 아니다.

token endpoint 입장에서는 별도 질문이 있다.

- 이 code를 교환하러 온 주체가 등록된 client가 맞는가
- 탈취된 code를 다른 client가 들고 온 것은 아닌가
- client 자격 증명이 staging/prod 간에 섞이지 않았는가

즉 client authentication은 authorization code 탈취, 잘못된 app registration, 운영 환경 혼선에 대한 방어선이다.

### 2. `client_secret_basic`은 단순하지만 공유 비밀의 비용을 안고 간다

가장 흔한 방식은 `client_id`와 `client_secret`을 token endpoint에 보내는 것이다.

이 방식의 장점:

- 구현이 단순하다
- 대부분의 라이브러리가 기본 지원한다
- confidential web app에는 빠르게 붙일 수 있다

하지만 운영 비용도 분명하다.

- secret이 여러 서버와 배포 파이프라인에 복제된다
- secret이 한번 새면 asymmetric key보다 회수가 번거롭다
- 사람이 값을 복사해 쓰는 문화가 남기 쉽다
- `client_secret_post`는 request body, access log, APM payload에 남을 표면적이 더 넓다

그래서 `client_secret_basic`은 "쉬운 기본값"이지 "장기적으로 가장 안전한 선택"은 아닐 수 있다.

### 3. `private_key_jwt`는 client가 비대칭 키로 자신을 증명한다

`private_key_jwt`에서는 client가 짧게 사는 signed assertion을 만들어 token endpoint에 보낸다.

핵심 포인트:

- `iss`와 `sub`는 보통 `client_id`와 맞춘다
- `aud`는 authorization server가 기대하는 token endpoint 식별자와 정확히 맞아야 한다
- `exp`는 짧게 잡는다
- `jti`는 replay 방어에 쓸 수 있다
- `kid` 또는 등록된 JWKS로 어떤 public key인지 식별한다

이 방식의 장점:

- private key는 client 쪽에만 있고 서버는 public key만 가진다
- shared secret 복제보다 blast radius를 줄이기 쉽다
- key rotation을 등록된 JWKS 기반으로 운영하기 좋다

실패 패턴도 분명하다.

- `aud`를 issuer와 token endpoint URL 중 무엇으로 맞출지 profile이 어긋난다
- clock skew 때문에 `exp`와 `iat`가 튕긴다
- `jti` replay store를 안 둬서 재사용 탐지가 약하다
- client key rotation 후 authorization server 쪽 key cache가 stale하다

### 4. mTLS client authentication은 전송 채널에서 client를 묶는다

mTLS는 애플리케이션 레벨이 아니라 TLS handshake 레벨에서 client certificate로 주체를 증명한다.

이 방식이 강한 이유:

- token endpoint까지의 채널 자체가 client identity와 결합된다
- proxy나 debug 경로에서 secret을 복사해 재사용하기 어렵다
- B2B integration, internal machine client에 특히 잘 맞는다

하지만 다음을 같이 봐야 한다.

- TLS termination 지점이 어디인가
- authorization server가 실제 client certificate identity를 어떻게 받는가
- load balancer가 인증서를 검증한 뒤 upstream에 어떤 형태로 전달하는가

즉 "mTLS를 쓴다"보다 "누가 cert를 보고 최종 client binding을 판단하는가"가 더 중요하다.

### 5. mTLS와 sender-constrained token은 같은 말이 아니다

mTLS는 client authentication에 쓸 수 있고, access token을 certificate-bound로 만들 수도 있다.

이 둘은 연결되지만 동일하지 않다.

- token endpoint에서만 mTLS로 client를 인증할 수 있다
- access token 자체를 cert thumbprint와 묶어 resource server에서도 확인하게 만들 수도 있다

전자는 "누가 토큰을 받아 갔는가"의 문제이고,  
후자는 "받아 간 토큰을 누가 실제로 사용 중인가"의 문제다.

### 6. public client는 client authentication보다 다른 방어선이 중요하다

SPA, mobile app, desktop app 같은 public client는 secret을 안전하게 숨기기 어렵다.

그래서 보통:

- PKCE
- redirect URI 엄격 검증
- 짧은 code lifetime
- token storage hardening

에 더 무게를 둔다.

public client에 secret을 억지로 심는다고 confidential client가 되지는 않는다.

### 7. 환경 분리와 등록 체계가 보안의 절반이다

실전에서 많이 깨지는 지점은 암호학보다 등록 정보다.

- staging client key가 prod authorization server에 등록돼 있음
- 여러 app이 같은 `client_secret`을 공유함
- `client_id` 하나에 너무 많은 redirect URI와 credential type을 몰아넣음
- cert subject와 client registry mapping이 느슨함

권장되는 운영 원칙:

- environment마다 client registration을 분리한다
- app마다 credential을 분리한다
- rotation 주기와 등록 owner를 명시한다
- 어떤 client가 어떤 auth method를 쓰는지 inventory를 남긴다

### 8. 관측 가능성이 없으면 `invalid_client`를 못 고친다

token endpoint 실패는 종종 다 `invalid_client` 한 줄로 뭉개진다.  
하지만 운영에는 아래 구분이 필요하다.

- method mismatch
- unknown client
- bad secret
- assertion audience mismatch
- assertion expired
- replayed `jti`
- client cert mismatch
- client key lookup failure

민감 정보는 남기지 않되, 어느 failure bucket인지와 client registration id 정도는 남겨야 한다.

---

## 실전 시나리오

### 시나리오 1: staging 유출이 prod까지 번진다

문제:

- staging, prod가 같은 `client_secret`을 쓴다
- staging 로그에서 secret이 노출된다

대응:

- environment마다 client registration을 분리한다
- secret 공유 대신 `private_key_jwt` 또는 client별 cert를 쓴다
- rotation blast radius를 app 단위로 줄인다

### 시나리오 2: `private_key_jwt` 전환 후 간헐적 `invalid_client`

문제:

- 새 key로 서명했지만 authorization server 또는 gateway가 옛 JWKS cache를 본다
- 어떤 pod는 새 key를 알고, 어떤 pod는 모른다

대응:

- client key rollover도 server-side signer key rollover처럼 overlap window를 둔다
- `kid_not_found`, `aud_mismatch`, `assertion_expired`를 따로 본다
- JWKS refresh를 single-flight로 묶는다

### 시나리오 3: mTLS가 load balancer 뒤에서만 깨진다

문제:

- edge는 cert를 확인하지만 upstream auth server는 client cert identity를 직접 못 본다
- `X-Client-Cert` 같은 헤더를 아무 서비스나 넣을 수 있다

대응:

- TLS termination과 identity assertion ownership을 명확히 한다
- trusted proxy chain이 아니면 forwarded cert header를 무시한다
- 내부 hop을 다시 mTLS로 보호하거나 signed metadata로 전달한다

---

## 코드로 보기

### 1. `private_key_jwt` token request 개념

```text
POST /oauth/token
grant_type=authorization_code
code=...
client_id=orders-web
client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer
client_assertion=eyJ...
```

### 2. client assertion 생성 개념

```java
public String buildClientAssertion(PrivateKey privateKey, String clientId, String audience, String kid) {
    Instant now = Instant.now();
    return JwtBuilder.create()
            .header("kid", kid)
            .claim("iss", clientId)
            .claim("sub", clientId)
            .claim("aud", audience)
            .claim("jti", UUID.randomUUID().toString())
            .claim("iat", now.getEpochSecond())
            .claim("exp", now.plusSeconds(60).getEpochSecond())
            .sign(privateKey);
}
```

핵심은 assertion을 길게 살려 두지 않는 것이다.

### 3. auth method 선택 체크리스트

```text
1. secret을 안전하게 보관할 수 있는 server-side confidential client인가
2. key rotation과 app registration을 자동화할 수 있는가
3. token endpoint가 mTLS termination ownership을 명확히 갖는가
4. client credential failure bucket을 관측할 수 있는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| `client_secret_basic` | 단순하고 호환성이 좋다 | secret 복제와 rotation 비용이 크다 | 소수의 서버사이드 confidential client |
| `private_key_jwt` | shared secret보다 blast radius가 작다 | key registration과 clock 관리가 필요하다 | B2B, enterprise, 장기 운영 서비스 |
| mTLS client auth | 채널 단위 binding이 강하다 | TLS termination과 cert 운영이 복잡하다 | internal client, regulated B2B, machine identity |
| `private_key_jwt` + mTLS | app identity와 채널 identity를 함께 강화한다 | 운영 복잡도가 높다 | 매우 민감한 token endpoint, partner integration |

판단 기준은 이렇다.

- credential 유출 시 blast radius를 얼마나 줄여야 하는가
- load balancer, gateway, auth server ownership이 명확한가
- key/cert rotation 자동화를 감당할 수 있는가
- public client인지 confidential client인지 경계가 분명한가

---

## 꼬리질문

> Q: `client_secret_basic`보다 `private_key_jwt`가 왜 더 나은가요?
> 의도: shared secret과 asymmetric proof의 차이를 아는지 확인
> 핵심: private key를 서버가 공유하지 않아도 되어 leak blast radius를 줄이기 쉽다.

> Q: public client도 client authentication을 해야 하나요?
> 의도: public/confidential 구분을 아는지 확인
> 핵심: 보통 아니다. PKCE와 redirect URI 검증이 더 중요하다.

> Q: mTLS와 certificate-bound access token은 같은가요?
> 의도: token issuance와 token use를 구분하는지 확인
> 핵심: 아니다. 하나는 client auth이고, 다른 하나는 토큰 재사용 방어까지 확장한 개념이다.

> Q: `private_key_jwt`에서 가장 흔한 운영 실수는 무엇인가요?
> 의도: 스펙보다 운영 포인트를 아는지 확인
> 핵심: `aud` mismatch, clock skew, stale client key cache가 흔하다.

## 한 줄 정리

OAuth client authentication의 핵심은 "user가 로그인했는가"가 아니라 "토큰을 요구하는 app이 등록된 그 client가 맞는가"를 증명하는 것이며, 장기 운영에서는 shared secret보다 비대칭 키와 채널 바인딩이 더 안전한 경우가 많다.

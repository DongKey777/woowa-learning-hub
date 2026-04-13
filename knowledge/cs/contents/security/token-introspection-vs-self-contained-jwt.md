# Token Introspection vs Self-Contained JWT

> 한 줄 요약: introspection은 중앙 제어와 즉시성에 강하고, self-contained JWT는 지연과 결합도를 줄인다. 선택은 revocation과 latency 중 무엇을 더 중시하느냐에 달려 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)
> - [API Gateway auth / rate limit chain](../network/api-gateway-auth-rate-limit-chain.md)
> - [인증과 인가의 차이](./authentication-vs-authorization.md)

retrieval-anchor-keywords: token introspection, self-contained JWT, opaque token, JWKS, revocation, audience, auth server, gateway, latency, offline validation, circuit breaker, token cache

---

## 핵심 개념

토큰 검증에는 크게 두 방식이 있다.

- `self-contained JWT`: 토큰 안에 필요한 클레임과 서명이 들어 있어서 로컬에서 검증 가능
- `token introspection`: 리소스 서버가 auth server에 토큰 상태를 물어보는 방식

두 방식은 같은 문제를 다르게 푼다.

- JWT는 "토큰 자체를 믿을 수 있게 만든다"
- introspection은 "토큰 상태를 중앙에서 판단한다"

이 차이는 운영에서 매우 크다.

- JWT는 빠르고 독립적이다
- introspection은 revocation과 실시간 정책에 강하다
- JWT는 탈취된 후 만료까지 살아남기 쉽다
- introspection은 auth server가 죽으면 전체 경로가 영향을 받는다

즉 이 선택은 단순 구현 방식이 아니라 장애 모드와 보안 모델의 선택이다.

---

## 깊이 들어가기

### 1. self-contained JWT의 장단점

JWT는 서명 검증만으로 로컬에서 처리할 수 있다.

장점:

- 네트워크 hop이 줄어든다
- auth server 의존이 낮다
- 대규모 트래픽에 잘 맞는다
- 캐시와 오프라인 검증이 쉽다

단점:

- revoke가 어렵다
- 권한 변경 반영이 늦다
- 토큰 수명이 길면 탈취 피해가 커진다

그래서 JWT는 보통 짧은 access token과 같이 쓰인다.

### 2. introspection의 장단점

introspection은 토큰이 지금도 active한지 서버에 묻는다.

장점:

- revoke가 즉시 반영된다
- 사용자 상태, 정책 상태를 함께 볼 수 있다
- opaque token과 잘 맞는다

단점:

- auth server가 병목이 될 수 있다
- 네트워크 지연이 늘어난다
- auth server 장애가 곧 인증 장애가 된다

### 3. hybrid가 현실적이다

실무에서는 둘 중 하나만 고집하지 않는다.

흔한 조합:

- access token은 짧은 JWT
- refresh token은 opaque 또는 server-side state
- 고위험 endpoint는 introspection 또는 fresh check
- gateway는 JWT 검증, service는 policy check

이렇게 하면 latency와 revocation 사이를 어느 정도 타협할 수 있다.

### 4. JWKS와 introspection cache

JWT 검증은 보통 JWKS를 통해 public key를 가져온다.

- `kid`로 키를 선택한다
- public key는 캐시할 수 있다
- key rotation이 가능하다

introspection도 cache할 수는 있지만 조심해야 한다.

- 캐시 TTL이 길면 revoke가 늦어진다
- TTL이 짧으면 auth server 부하가 커진다
- cache miss가 장애 증폭으로 이어질 수 있다

그래서 introspection cache는 짧게, 그리고 위험 경로 중심으로만 쓰는 편이 좋다.

### 5. fail-open과 fail-closed

auth server가 죽었을 때 어떻게 할지도 정해야 한다.

- `fail-closed`: 안전하지만 가용성이 떨어진다
- `fail-open`: 가용성은 좋지만 보안이 약해진다

보통 민감한 API는 fail-closed가 맞고, 읽기 전용이나 낮은 위험 경로는 조건부 완화가 가능하다.

---

## 실전 시나리오

### 시나리오 1: logout 직후에도 토큰이 살아 있음

문제:

- JWT는 로컬 검증만 하므로 logout 이벤트가 바로 반영되지 않는다

대응:

- access token TTL을 짧게 둔다
- refresh token을 revoke한다
- 민감 경로는 introspection이나 version check를 추가한다

### 시나리오 2: auth server 장애로 전체 API가 막힘

문제:

- introspection을 매 요청마다 한다

대응:

- 응답 캐시를 짧게 둔다
- circuit breaker를 넣는다
- 일부 경로는 JWT local validation으로 우회한다

### 시나리오 3: 권한이 자주 바뀌는 관리자 API

문제:

- JWT에 넣은 role이 오래 남는다

대응:

- 관리자 경로는 fresh lookup 또는 introspection을 쓴다
- permission version을 함께 검증한다

---

## 코드로 보기

### 1. JWT local validation 예시

```java
public Claims validateJwt(String token) {
    DecodedJWT decoded = JWT.require(algorithm)
        .withIssuer("auth.example.com")
        .withAudience("api.example.com")
        .build()
        .verify(token);

    return decoded.getClaims();
}
```

### 2. introspection client 예시

```java
public TokenStatus introspect(String token) {
    return introspectionCache.computeIfAbsent(hash(token), ignored -> {
        TokenStatus status = authServerClient.introspect(token);
        if (!status.active()) {
            return status;
        }
        return status.withCachedAt(Instant.now());
    });
}
```

### 3. gateway에서의 선택 개념

```text
1. 일반 API는 JWT를 로컬 검증한다
2. revoke 민감 경로는 introspection을 한다
3. auth server 장애 시 circuit breaker 정책을 적용한다
4. 사용자/권한 변경 이벤트는 cache invalidation으로 반영한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| self-contained JWT | 빠르고 독립적이다 | revoke가 느리다 | 고트래픽 API, 짧은 수명 토큰 |
| introspection | 중앙 통제와 즉시성이 좋다 | 지연과 의존성이 생긴다 | 강한 revoke 요구, 민감 경로 |
| opaque token + introspection | 상태 중심 운영이 쉽다 | 모든 요청이 auth server를 탄다 | 중앙 정책이 중요한 시스템 |
| JWT + targeted introspection | 현실적인 균형이다 | 설계가 복잡하다 | 대부분의 실서비스 |

판단 기준은 이렇다.

- revoke가 몇 초 안에 반영돼야 하는가
- auth server가 병목이 되어도 되는가
- 서비스가 오프라인에서도 토큰을 검증해야 하는가
- 정책 변경이 잦은가

---

## 꼬리질문

> Q: self-contained JWT와 introspection의 가장 큰 차이는 무엇인가요?
> 의도: 로컬 검증과 중앙 상태 확인의 차이를 아는지 확인
> 핵심: JWT는 자체 서명 검증, introspection은 서버 상태 조회다.

> Q: introspection이 왜 운영상 부담이 될 수 있나요?
> 의도: 지연과 의존성, 병목을 이해하는지 확인
> 핵심: 매 요청 auth server 왕복이 생기기 때문이다.

> Q: revoke가 중요하면 JWT를 아예 쓰면 안 되나요?
> 의도: 실무형 절충을 이해하는지 확인
> 핵심: 아니요. 짧은 JWT와 targeted introspection을 같이 쓸 수 있다.

> Q: fail-open과 fail-closed 중 무엇이 더 안전한가요?
> 의도: 장애 모드에서 보안과 가용성의 균형 이해 확인
> 핵심: 보통 fail-closed가 더 안전하지만, 가용성 요구를 같이 봐야 한다.

## 한 줄 정리

JWT는 로컬 검증의 속도를 주고, introspection은 중앙 revoke와 최신 상태를 준다. 둘 중 무엇을 택할지는 장애와 보안 중 어디에 더 무게를 두는지에 달려 있다.

# JWT 깊이 파기

> 한 줄 요약: JWT는 "로그인 상태를 담은 문자열"이 아니라, 서명된 클레임 집합이다. 구조, 검증, 갱신, 탈취 대응을 같이 봐야 운영할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)
> - [Refresh Token Rotation / Reuse Detection](./refresh-token-rotation-reuse-detection.md)
> - [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md)
> - [Signed Cookies / Server Sessions / JWT Tradeoffs](./signed-cookies-server-sessions-jwt-tradeoffs.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [JWK Rotation / Cache Invalidation / `kid` Rollover](./jwk-rotation-cache-invalidation-kid-rollover.md)
> - [JWKS Rotation Cutover Failure / Recovery](./jwks-rotation-cutover-failure-recovery.md)
> - [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md)
> - [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md)
> - [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md)
> - [DPoP / Token Binding Basics](./dpop-token-binding-basics.md)
> - [Proof-of-Possession vs Bearer Token Trade-offs](./proof-of-possession-vs-bearer-token-tradeoffs.md)
> - [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
> - [시스템 설계 면접 프레임워크](../system-design/system-design-framework.md)

retrieval-anchor-keywords: JWT, JWT 처음 배우는데, JWT 입문자, JWT validation 입문 순서, beginner JWT primer, JWT intro kid issuer audience signature, JWT 기초 입문자, claim set, signature validation, signature verification failure, JWKS, key rotation, refresh token, revocation, token family, replay, cookie storage, localStorage, audience, issuer, kid, kid miss, authorization context, stale JWKS cache, token misuse, browser BFF boundary, proof of possession, key compromise

---

## 핵심 개념

JWT(JSON Web Token)는 보통 `Header.Payload.Signature` 형태의 문자열이다.

- `Header`: 알고리즘과 토큰 타입
- `Payload`: 사용자 식별자, 권한, 만료 시간 같은 클레임
- `Signature`: payload가 위조되지 않았음을 증명하는 서명

중요한 점은 JWT가 기본적으로 "암호화된 토큰"이 아니라는 것이다.  
대부분의 경우 내용은 누구나 디코딩해서 볼 수 있고, 위조만 막는다.

JWT를 쓰는 이유는 주로 다음이다.

- 서버 세션 저장소 의존도를 줄이기 위해
- 모바일/SPA/API 서버 간 인증 전달을 단순화하기 위해
- 분산 환경에서 인증 정보를 수평 확장 가능한 형태로 전달하기 위해

이 장점은 곧 단점이기도 하다.

- 서버가 상태를 적게 가지는 대신
- 토큰 폐기와 강제 로그아웃이 어려워진다
- 탈취되면 만료 전까지 악용될 수 있다

---

## 깊이 들어가기

### 1. JWT 구조

JWT는 보통 base64url로 인코딩된 세 조각으로 구성된다.

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiJ1c2VyLTEyMyIsInJvbGVzIjpbIlJPTEVfVVNFUiJdLCJleHAiOjE3MDAwMDAwMDB9.
signature
```

자주 보는 클레임:

- `sub`: 주체 식별자
- `exp`: 만료 시각
- `iat`: 발급 시각
- `iss`: 발급자
- `aud`: 대상 서비스
- `jti`: 토큰 고유 ID

### 2. 서명 검증이 핵심이다

서명은 payload가 변조되지 않았는지 확인하는 장치다.

- HMAC 계열은 shared secret으로 서명한다
- RSA/ECDSA 계열은 private key로 서명하고 public key로 검증한다

실무에서는 키 회전과 검증 분리를 고려한다.

- `kid` 헤더로 어떤 키를 쓸지 구분한다
- 검증 서버는 키셋(JWKS)을 갱신한다
- 만료 시간은 짧게 가져간다

### 3. 탈취 시나리오

JWT는 "서명만 검증하면 끝"이 아니다. 탈취 경로를 같이 막아야 한다.

대표 경로:

- XSS로 `localStorage`의 토큰을 읽음
- 프론트 로그나 디버그 로그에 토큰이 남음
- reverse proxy/애플리케이션 access log에 Authorization 헤더가 남음
- 브라우저 리퍼러/외부 공유 링크에 민감 값이 섞임

운영상 방어:

- access token은 짧게 유지한다
- refresh token은 HttpOnly cookie 또는 서버 저장소와 함께 관리한다
- 로그 마스킹을 강제한다
- 민감 API는 추가 검증을 둔다

### 4. refresh 전략

가장 흔한 패턴은 access token + refresh token 이다.

- access token: 짧게, API 호출용
- refresh token: 길게, 재발급용

실무에서 중요한 것은 회전(rotation)이다.

```text
1. access token이 만료됨
2. refresh token으로 새 access token을 받음
3. refresh token도 새 값으로 교체
4. 이전 refresh token은 폐기
```

이렇게 하면 재사용(replay)을 일부 잡아낼 수 있다.  
`jti` 또는 토큰 family ID를 저장해 중복 사용을 탐지하는 방식이 자주 쓰인다.

### 5. 왜 JWT만으로 끝나지 않는가

JWT는 인증 전달 수단이지, 인가 정책 저장소가 아니다.

- role은 토큰에 넣을 수 있지만, 자주 바뀌는 권한까지 토큰에 묶으면 늦게 반영된다
- 계정 정지, 강제 로그아웃, 세션 무효화는 별도 상태가 필요하다
- 사용자 삭제나 비밀번호 변경 이후 기존 토큰 폐기가 필요할 수 있다

즉 JWT는 "무상태"가 아니라 "덜 상태적인" 선택이다.

### 6. 운영에서 자주 터지는 보안/운영 trade-off

JWT의 문제는 스펙보다 운영에서 더 많이 터진다.

- TTL을 길게 잡으면 탈취 피해가 커진다
- TTL을 너무 짧게 잡으면 refresh 폭주가 생긴다
- claim을 많이 넣으면 stale authorization이 늦게 반영된다
- `kid` rotation이 늦으면 JWKS cache mismatch가 난다
- cookie에 넣으면 CSRF가 다시 중요해진다
- browser storage에 넣으면 XSS가 다시 중요해진다

그래서 JWT는 단독 솔루션이 아니라 주변 통제와 함께 본다.

- 짧은 access token
- refresh token rotation
- revocation store 또는 session version
- JWKS cache invalidation
- server-side authorization recheck
- browser 저장/전송 전략

### 7. 공격자가 노리는 경로

실무에서 자주 보는 경로는 다음이다.

- access token을 로그/telemetry에서 수집한다
- 오래 사는 토큰을 재사용한다
- `aud`가 넓은 토큰을 다른 서비스에 넣는다
- refresh token family reuse를 숨긴다
- `kid` 미스와 cache stale을 이용한다

이 때문에 JWT를 "서명됐으니 안전"으로 보는 건 너무 단순하다.

### 8. JWT와 token binding 계열의 관계

JWT 자체는 bearer token으로 쓰이는 경우가 많다.  
하지만 DPoP 같은 proof-of-possession 계열을 붙이면 재사용 위험을 더 줄일 수 있다.

- bearer JWT: 복사되면 끝
- sender-constrained token: key가 있어야 쓸 수 있음

이 차이는 [DPoP / Token Binding Basics](./dpop-token-binding-basics.md)와 같이 보면 더 분명해진다.

---

## 실전 시나리오

### 시나리오 1: 토큰이 탈취됐는데 막을 수 없음

원인:

- access token 만료 시간이 너무 길다
- refresh token 재사용 방지가 없다
- 로그아웃 시 서버가 아무 것도 지우지 않는다

대응:

- access token을 5~15분 수준으로 짧게 잡는다
- refresh token은 회전시킨다
- 토큰 폐기 저장소를 둔다

### 시나리오 2: 권한 변경이 바로 반영되지 않음

원인:

- role을 JWT에 넣고 그대로 신뢰한다
- 사용자가 관리자 권한을 회수당해도 예전 토큰이 살아 있다

대응:

- 민감 권한은 토큰뿐 아니라 서버 조회를 같이 본다
- 토큰 `iat`와 사용자 권한 버전을 비교한다
- 강제 로그아웃 이벤트를 운영한다

### 시나리오 3: 브라우저에서 JWT 저장 방식이 사고를 만듦

원인:

- `localStorage`에 넣고 XSS에 노출된다
- 쿠키에 넣었지만 CSRF 방어를 안 했다

대응:

- 브라우저 앱은 HttpOnly cookie + CSRF 전략을 검토한다
- API-only 앱은 짧은 access token + refresh cookie 조합을 자주 쓴다

### 시나리오 4: JWKS 캐시가 낡아 새 토큰만 검증 실패함

원인:

- signer는 새 `kid`로 전환했는데 verifier cache가 예전 key를 본다
- rotation window를 토큰 TTL보다 짧게 잡았다

대응:

- JWKS cache invalidation을 운영 이벤트로 둔다
- old/new key를 overlap시키고 제거 시점을 늦춘다
- `kid` 미스 시 force refresh를 한다

### 시나리오 5: JWT를 그대로 downstream에 전달하다가 audience가 커짐

원인:

- 사용자 토큰을 hop-by-hop으로 재사용했다
- downstream이 필요 이상 권한을 얻게 됐다

대응:

- token exchange로 audience/scope를 줄인다
- 서비스별 downstream 토큰을 다시 발급한다
- actor/subject를 분리해 기록한다

---

## 코드로 보기

### 1. 클레임 검증의 핵심

```java
public JwtClaims validateAndParse(String token) {
    DecodedJWT decoded = JWT.require(algorithm)
        .withIssuer("auth.example.com")
        .withAudience("api.example.com")
        .build()
        .verify(token);

    if (decoded.getExpiresAt().before(new Date())) {
        throw new IllegalArgumentException("token expired");
    }

    return new JwtClaims(
        decoded.getSubject(),
        decoded.getClaim("roles").asList(String.class),
        decoded.getId()
    );
}
```

서명 검증만으로 끝내지 말고, `iss`, `aud`, `exp`를 같이 본다.

### 2. refresh token 회전 개념

```java
public TokenPair refresh(String refreshToken) {
    RefreshToken stored = refreshTokenRepository.findActive(refreshToken)
        .orElseThrow(() -> new IllegalStateException("invalid refresh token"));

    stored.revoke();
    refreshTokenRepository.save(stored);

    String newAccessToken = jwtIssuer.issueAccessToken(stored.userId());
    String newRefreshToken = jwtIssuer.issueRefreshToken(stored.userId());

    refreshTokenRepository.save(new RefreshToken(stored.userId(), newRefreshToken));
    return new TokenPair(newAccessToken, newRefreshToken);
}
```

### 3. Spring Security 필터에서 사용 예시

```java
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String token = resolveToken(request);
        if (token != null) {
            JwtClaims claims = jwtService.validateAndParse(token);
            Authentication auth = new UsernamePasswordAuthenticationToken(
                claims.subject(),
                null,
                claims.roles().stream()
                    .map(SimpleGrantedAuthority::new)
                    .toList()
            );
            SecurityContextHolder.getContext().setAuthentication(auth);
        }
        filterChain.doFilter(request, response);
    }
}
```

### 4. logout / revoke / version check 개념

```java
public void verifyActiveSession(JwtClaims claims, UserState state) {
    if (!state.sessionVersion().equals(claims.sessionVersion())) {
        throw new IllegalStateException("session revoked");
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 짧은 access token + refresh token | 탈취 피해를 줄이고 운영 통제가 쉽다 | refresh 저장소와 회전 로직이 필요하다 | 대부분의 실서비스 |
| 긴 access token만 사용 | 구현이 단순하다 | 폐기와 강제 로그아웃이 어렵다 | 내부 도구, 단순 시스템 |
| 토큰에 권한을 많이 넣는다 | API가 단순해진다 | 권한 변경 반영이 느려진다 | 권한이 거의 안 바뀌는 도메인 |
| 서버 조회 기반 인가 | 최신 상태를 반영한다 | 요청당 추가 조회 비용이 든다 | 민감 기능, 관리자 기능 |

핵심 판단 기준은 이렇다.

- 토큰이 탈취됐을 때 피해를 얼마나 줄여야 하는가
- 권한 변경이 얼마나 자주 일어나는가
- 강제 로그아웃이 필요한가
- 브라우저, 모바일, 서버 중 어디가 주 클라이언트인가
- JWKS cache와 key rotation 운영을 감당할 수 있는가
- token exchange나 DPoP가 필요한 수준인가

---

## 꼬리질문

> Q: JWT는 왜 항상 안전하다고 말할 수 없는가?
> 의도: 서명 검증과 탈취 대응을 분리해서 이해하는지 확인
> 핵심: 위조는 막아도 탈취는 못 막는다.

> Q: refresh token을 왜 회전시키는가?
> 의도: replay attack과 토큰 재사용 탐지 이해 여부 확인
> 핵심: 이전 토큰 재사용을 발견하고 피해를 줄이기 위해서다.

> Q: localStorage와 HttpOnly cookie의 차이를 단순 저장 위치가 아니라 공격면 관점으로 설명할 수 있는가?
> 의도: 브라우저 저장 전략의 보안 trade-off 이해 여부 확인
> 핵심: localStorage는 XSS에 취약하고, cookie는 CSRF 전략을 같이 봐야 한다.

> Q: JWT에 role을 넣는 것이 왜 항상 좋은가?
> 의도: 인가 정책과 토큰의 수명 차이를 이해하는지 확인
> 핵심: 권한 변경 반영이 느려질 수 있다.

## 한 줄 정리

JWT는 서명된 클레임 묶음이고, 안전하게 쓰려면 구조를 이해하는 것보다 만료, 회전, 폐기, 탈취 대응까지 같이 설계해야 한다.

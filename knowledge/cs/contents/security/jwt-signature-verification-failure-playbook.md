# JWT Signature Verification Failure Playbook

> 한 줄 요약: JWT 검증 장애는 "서명이 틀렸다" 한 문장으로 뭉개면 못 고친다. 파싱, issuer 바인딩, JWKS 조회, `kid` 선택, 알고리즘 검증, claim 검증을 단계별로 분리해야 안전하게 복구할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [JWK Rotation / Cache Invalidation / `kid` Rollover](./jwk-rotation-cache-invalidation-kid-rollover.md)
> - [Key Rotation Runbook](./key-rotation-runbook.md)
> - [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md)
> - [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md)
> - [OIDC, ID Token, UserInfo 경계](./oidc-id-token-userinfo-boundaries.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [Secret Scanning / Credential Leak Response](./secret-scanning-credential-leak-response.md)

retrieval-anchor-keywords: JWT signature verification, JWT validation failure, JWKS outage, kid miss, kid rollover, stale JWKS cache, algorithm allowlist, issuer binding, signature invalid, verification playbook, duplicate kid, fail closed, stale-if-error, recovery ladder, verifier outage

---

## 핵심 개념

JWT 검증 실패를 다룰 때 가장 흔한 실수는 모든 401을 같은 종류의 실패로 보는 것이다.

실제로는 층위가 다르다.

1. 토큰 형식이 깨졌는가
2. 어떤 issuer의 어떤 키로 검증해야 하는가
3. `kid`에 맞는 key를 찾았는가
4. 허용된 알고리즘으로 실제 서명 검증이 성공했는가
5. `iss`, `aud`, `exp`, `nbf`, `typ` 같은 claim 검증이 통과했는가

이 다섯 단계를 분리하지 않으면 원인을 잘못 잡는다.

- `kid` miss인데 "서명 위조"로 오판할 수 있다
- issuer 설정 drift인데 JWKS 캐시만 계속 비울 수 있다
- claim mismatch인데 crypto incident처럼 과대 대응할 수 있다
- JWKS endpoint 장애인데 모든 토큰을 tampering으로 착각할 수 있다

이 문서는 steady-state 설계보다, 이미 검증 실패가 발생했을 때 무엇부터 확인하고 어디서 fail-closed 해야 하는지에 초점을 둔다.

---

## 깊이 들어가기

### 1. 먼저 실패 단계를 분류해야 한다

실무에서 "JWT validation failed"는 너무 넓은 로그다.  
적어도 아래 bucket으로 나눠야 한다.

- malformed token: segment 수가 틀리거나 base64url decode가 깨짐
- issuer resolution failure: 어떤 trust domain인지 결정 불가
- key lookup failure: `kid`에 맞는 key가 없음
- crypto failure: key는 찾았지만 signature가 맞지 않음
- claim validation failure: `iss`, `aud`, `exp`, `nbf`, `typ` 등이 안 맞음
- dependency failure: JWKS fetch timeout, metadata fetch error, cache store 장애

이 분류가 있어야 대응 순서가 생긴다.

### 2. JOSE 헤더는 라우팅 힌트이지 신뢰 기준이 아니다

헤더의 `kid`와 `alg`는 검증 경로를 고르는 데 도움을 준다.  
하지만 둘 다 "받은 입력"이다.

- `kid`는 이미 신뢰하기로 한 key set 안에서 후보를 좁히는 용도다
- `alg`는 allowlist와 key metadata가 허용할 때만 써야 한다
- `jku`, `x5u` 같은 URL 기반 힌트는 임의로 따라가면 안 된다

즉 검증자는 이렇게 동작해야 한다.

- 애플리케이션이 미리 허용한 issuer와 `jwks_uri`를 갖는다
- 그 issuer에서 허용한 알고리즘만 받는다
- `kid`는 그 issuer의 JWKS 내부에서만 매칭한다

장애 대응 중에도 이 원칙을 깨면 안 된다.  
"일단 통과시키기 위해 다른 issuer의 key도 대입해 본다" 같은 fallback은 사고를 만든다.

### 3. issuer 바인딩이 먼저고, key 선택은 그 다음이다

multi-issuer 환경에서는 특히 이 순서가 중요하다.

- issuer A의 토큰은 issuer A의 metadata와 JWKS로만 검증한다
- issuer B의 public key를 issuer A 토큰 검증에 재사용하면 안 된다
- cache key도 `(issuer, jwks_uri, tenant, environment)` 수준으로 분리한다

주의할 점은 `iss` claim 자체도 서명 전에는 신뢰할 수 없다는 것이다.  
그래서 실무에서는 보통 아래 둘 중 하나를 쓴다.

- endpoint나 route 별로 허용 issuer를 고정한다
- unverified `iss`를 candidate selection 힌트로만 쓰고, 검증 성공 후 exact match를 다시 확인한다

즉 `iss`는 "수락 조건"이지 "무조건 믿는 라벨"이 아니다.

### 4. `kid` miss는 흔하지만, 처리 순서가 중요하다

`kid` miss가 났다고 바로 공격으로 단정할 필요는 없다.  
rotation 직후라면 가장 흔한 원인은 stale JWKS cache다.

안전한 순서는 대체로 이렇다.

1. issuer별 캐시에서 `kid`를 찾는다
2. miss면 issuer 단위로 JWKS refresh를 한 번 시도한다
3. concurrent miss는 single-flight로 collapse 한다
4. refresh 후에도 없으면 reject 한다
5. 지표에 `kid_not_found_after_refresh`를 별도 bucket으로 남긴다

여기서 중요한 것은 "한 번 refresh"와 "issuer 단위 collapse"다.

- 매 요청마다 JWKS를 다시 가져오면 refresh storm이 난다
- refresh 실패 후 모든 key를 brute-force 하듯 대입하면 잘못된 수락이 생긴다
- 다른 issuer cache까지 뒤지면 trust boundary가 무너진다

### 5. `kid` rollover 장애는 새 key 추가보다 제거 타이밍에서 더 많이 난다

새 `kid`가 보이지 않아 새 토큰만 깨지는 경우가 흔하지만, old key를 너무 빨리 지워서 아직 유효한 토큰이 깨지는 경우도 많다.

운영 체크 포인트:

- 새 key는 signer cutover 전에 JWKS에 먼저 노출했는가
- verifier fleet가 새 JWKS를 받을 시간을 줬는가
- old key 제거 시점을 `max token lifetime + clock skew + rollout lag`로 계산했는가
- mobile client, edge cache, CDN cache 같은 느린 경로를 반영했는가

즉 rollover incident는 "새 토큰 실패"와 "기존 토큰 실패"를 따로 봐야 한다.

- 새 토큰만 실패: stale cache, new `kid` 전파 지연 가능성
- 기존 토큰도 갑자기 실패: old key 조기 제거, issuer drift, 잘못된 JWKS publish 가능성

### 6. `signature invalid`와 `claim invalid`를 섞으면 안 된다

운영 로그에서 두 오류가 같은 bucket으로 합쳐지면 대응이 어긋난다.

예를 들어:

- `aud` mismatch는 key rotation으로는 해결되지 않는다
- `exp` 초과는 시계 오차, token TTL, queue delay를 봐야 한다
- `typ` mismatch는 cross-JWT confusion 방어 규칙을 점검해야 한다
- `signature invalid`는 잘못된 key, 잘못된 알고리즘, token tampering 중 하나일 가능성이 크다

즉 crypto 검증이 성공한 뒤의 claim 오류와, crypto 자체 실패는 runbook이 달라야 한다.

### 7. 알고리즘 mismatch는 구성 drift일 때가 많다

실패 메시지가 "signature invalid"처럼 보여도 실제로는 알고리즘 정책 문제일 수 있다.

대표 사례:

- issuer는 `RS256`인데 verifier가 `HS256`도 허용해 둠
- library upgrade 후 허용 알고리즘 기본값이 바뀜
- JWK의 `kty`, `use`, `alg`가 verifier 기대와 안 맞음
- 같은 `kid`를 서로 다른 알고리즘 key에 재사용함

운영 원칙:

- 허용 알고리즘은 issuer별 allowlist로 고정한다
- key 하나는 정확히 한 알고리즘과만 연결한다
- `alg`는 header에서 읽더라도 policy와 key metadata가 재확인해야 한다

### 8. JWKS fetch 실패와 crypto 실패는 다르게 다뤄야 한다

이 둘은 보안 의미가 다르다.

- JWKS fetch timeout: dependency outage 가능성
- `kid` miss after refresh: rollout 또는 config drift 가능성
- signature mismatch with resolved key: tampering, wrong issuer binding, wrong key publish 가능성

그래서 fallback도 다르게 해야 한다.

`stale-while-revalidate`를 쓰더라도 범위를 좁혀야 한다.

- 네트워크 실패 시 최근에 검증 성공 이력이 있는 issuer에 한해 짧은 stale cache를 허용할 수 있다
- 하지만 refresh 후에도 `kid`가 없는 토큰을 stale cache로 억지 통과시키면 안 된다
- duplicate `kid`, unexpected `kty`, unexpected `alg`는 availability보다 integrity incident로 본다

### 9. duplicate `kid`는 "애매하면 시도"가 아니라 설정 사고다

같은 JWKS 안에서 같은 `kid`가 여러 key를 가리키면 verifier가 추측하기 시작한다.

- 어떤 key를 먼저 시도할지 implementation마다 다르다
- key type이 다르면 더 위험하다
- 장애 시 재현성이 낮아진다

이 경우 안전한 대응은 추측이 아니라 reject와 incident 승격이다.

### 10. 관측 가능성이 없으면 플레이북이 돌아가지 않는다

최소한 아래 필드는 남겨야 한다.

- issuer candidate
- verified issuer
- `kid`
- header `alg`
- selected key fingerprint or thumbprint
- JWKS cache age
- refresh reason: ttl_expired, kid_miss, manual_evict
- failure bucket
- verifier version / region / pod

민감 정보 때문에 JWT 전체를 로그로 남기면 안 된다.  
토큰 원문 대신 thumbprint, `jti`, issuer, `kid`, failure bucket 정도로 좁혀야 한다.

---

## 실전 시나리오

### 시나리오 1: 배포 직후 새 로그인만 실패하고 기존 세션은 정상

가능성 높은 원인:

- signer가 새 `kid`로 전환했지만 verifier cache가 stale하다
- 일부 region만 JWKS refresh가 늦다
- CDN이 JWKS를 오래 캐시한다

대응:

- `kid_not_found`가 특정 issuer와 region에 몰리는지 본다
- issuer 단위 강제 refresh를 실행한다
- old/new key가 JWKS에 같이 보이는지 확인한다
- old key 제거는 보류한다

### 시나리오 2: 모든 토큰이 동시에 "signature invalid"로 바뀜

가능성 높은 원인:

- verifier 설정이 잘못된 issuer metadata를 가리킨다
- 허용 알고리즘 설정이 바뀌었다
- 잘못된 JWKS가 publish 됐다
- library upgrade가 기본 검증 동작을 바꿨다

대응:

- 최근 config deploy와 library 변경부터 본다
- 현재 JWKS와 직전 JWKS fingerprint를 비교한다
- 특정 `kid`만 실패하는지, 전부 실패하는지 분리한다
- claim validator가 아니라 crypto verifier 단계에서 실패하는지 확인한다

### 시나리오 3: JWKS endpoint 장애로 인증이 간헐적으로 무너짐

가능성 높은 원인:

- metadata/JWKS fetch 경로의 DNS, TLS, egress 장애
- cache TTL이 너무 짧아 외부 의존성이 과도하다
- refresh collapse가 없어 thundering herd가 발생한다

대응:

- stale cache 허용 정책이 있는지 확인한다
- single-flight refresh와 backoff를 적용한다
- 최근 검증 성공 issuer에 한해 제한적 stale 사용 여부를 판단한다
- 근본적으로는 TTL, prefetch, issuer별 warm-up 전략을 재설계한다

### 시나리오 4: 특정 tenant만 계속 실패한다

가능성 높은 원인:

- multi-tenant cache key가 issuer 대신 host만 쓰고 있다
- tenant별 issuer mapping이 꼬였다
- tenant 전용 key set에 duplicate `kid`가 있다

대응:

- cache namespace를 tenant와 issuer까지 포함해 점검한다
- failing tenant의 metadata와 JWKS를 별도 diff 한다
- cross-tenant key reuse 여부를 확인한다

---

## 코드로 보기

### 1. 검증 파이프라인 분리 개념

```java
public VerificationResult verify(String token, VerificationContext context) {
    ParsedJwt parsed = jwtParser.parse(token); // syntax only, still untrusted

    IssuerPolicy policy = issuerRouter.resolveCandidate(parsed, context);
    if (!policy.allowedAlgorithms().contains(parsed.header().alg())) {
        return VerificationResult.reject("alg_not_allowed");
    }

    ResolvedKey resolvedKey = keyResolver.resolve(policy, parsed.header().kid(), parsed.header().alg());
    if (resolvedKey.status() == KeyStatus.NOT_FOUND) {
        return VerificationResult.reject("kid_not_found");
    }

    if (!cryptoVerifier.verify(parsed, resolvedKey.publicKey(), policy.expectedAlgorithm())) {
        return VerificationResult.reject("signature_invalid");
    }

    return claimValidator.validate(parsed.claims(), policy);
}
```

핵심은 parse, routing, key lookup, crypto verify, claim validate를 한 덩어리로 두지 않는 것이다.

### 2. `kid` miss 시 refresh collapse 개념

```java
public ResolvedKey resolve(IssuerPolicy policy, String kid, String alg) {
    JwksSnapshot snapshot = jwksCache.get(policy.issuer());
    Jwk key = snapshot.find(kid, alg);
    if (key != null) {
        return ResolvedKey.found(key.toPublicKey());
    }

    JwksSnapshot refreshed = refreshCoordinator.refreshOnce(policy.issuer(), policy.jwksUri());
    Jwk afterRefresh = refreshed.find(kid, alg);
    if (afterRefresh != null) {
        return ResolvedKey.found(afterRefresh.toPublicKey());
    }
    return ResolvedKey.notFound();
}
```

여기서 `refreshOnce`는 issuer 단위 single-flight여야 한다.

### 3. 운영 체크리스트

```text
1. failure bucket을 malformed / key lookup / crypto / claims / dependency로 나눈다
2. failing issuer와 region, verifier version을 묶어 본다
3. kid miss인지 signature invalid인지 먼저 구분한다
4. JWKS 현재값과 직전값, cache age를 확인한다
5. 새 key 추가 / old key 제거 / alg 설정 변경 시점을 대조한다
6. refresh storm, duplicate kid, wrong issuer binding 여부를 본다
7. 임시 완화가 integrity를 깨는지 먼저 확인한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 짧은 JWKS TTL | rollover 반영이 빠르다 | 외부 의존성 부하가 커진다 | key rotation이 잦고 issuer 수가 적을 때 |
| 긴 JWKS TTL | 안정적이고 부하가 낮다 | `kid` 반영 지연이 커진다 | issuer 변경이 드문 내부 환경 |
| `kid` miss 시 즉시 refresh | self-healing이 쉽다 | miss storm에 취약하다 | single-flight와 backoff가 있을 때 |
| 네트워크 오류 시 bounded stale 허용 | auth outage를 줄인다 | stale acceptance 위험이 있다 | issuer가 고정되고 최근 검증 이력이 충분할 때 |
| refresh 후에도 없는 `kid`를 거부 | integrity를 지킨다 | rollout 실수 시 가용성이 떨어진다 | 외부 신뢰 경계를 엄격히 지켜야 할 때 |

판단 기준은 이렇다.

- availability보다 integrity를 어디까지 우선하는가
- issuer 수와 tenant 수가 얼마나 많은가
- rotation 주기가 얼마나 잦은가
- verifier fleet의 rollout 편차가 얼마나 큰가

---

## 꼬리질문

> Q: `kid`를 받았으면 왜 그 값만으로 key를 믿으면 안 되나요?
> 의도: 헤더를 trust anchor로 오해하지 않는지 확인
> 핵심: `kid`는 이미 신뢰한 issuer의 key set 안에서 후보를 좁히는 힌트일 뿐이다.

> Q: `kid` miss가 났을 때 가장 먼저 해야 할 일은 무엇인가요?
> 의도: rollout과 공격을 구분하는지 확인
> 핵심: issuer 단위 JWKS refresh를 한 번 시도하고, 여전히 없으면 reject 하며 관측 지표를 남긴다.

> Q: JWKS fetch 실패와 signature mismatch를 왜 다르게 봐야 하나요?
> 의도: dependency outage와 integrity failure를 분리하는지 확인
> 핵심: 전자는 가용성 문제일 수 있지만, 후자는 잘못된 key publish나 tampering 가능성이 더 크다.

> Q: multi-issuer 환경에서 가장 위험한 구현 실수는 무엇인가요?
> 의도: trust boundary를 이해하는지 확인
> 핵심: issuer별 key set과 cache namespace를 분리하지 않고 다른 issuer key까지 fallback하는 것이다.

## 한 줄 정리

JWT 검증 장애 대응의 핵심은 `kid` miss, JWKS stale, 알고리즘 drift, signature mismatch, claim mismatch를 같은 오류로 보지 않고 trust boundary를 지키는 순서대로 분리하는 것이다.

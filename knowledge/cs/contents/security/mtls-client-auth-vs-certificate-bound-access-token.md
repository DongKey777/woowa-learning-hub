# mTLS Client Auth vs Certificate-Bound Access Token

> 한 줄 요약: mTLS client authentication은 "누가 토큰을 받아 가는가"를 강하게 만들고, certificate-bound access token은 "받아 간 토큰을 누가 실제로 쓰는가"까지 묶으므로, 둘은 비슷해 보여도 보호하는 경계가 다르다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)
> - [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)
> - [Proof-of-Possession vs Bearer Token Trade-offs](./proof-of-possession-vs-bearer-token-tradeoffs.md)
> - [DPoP / Token Binding Basics](./dpop-token-binding-basics.md)
> - [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)
> - [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)

retrieval-anchor-keywords: mTLS client auth, certificate-bound token, sender-constrained access token, cert bound access token, mutual TLS token binding, OAuth mTLS, PoP token, client certificate binding, token replay resistance, mixed rollout, tls termination metadata, cert rotation tail, AS RS support mismatch, sender-constrained rollout

---

## 핵심 개념

mTLS와 certificate-bound token은 자주 한 덩어리로 설명되지만, 실제로는 다른 질문에 답한다.

- mTLS client auth: token endpoint나 API가 "지금 연결한 client가 누구인가"를 확인
- certificate-bound access token: "이 access token은 어떤 client certificate와 함께 써야 하는가"를 확인

즉 전자는 인증, 후자는 토큰 재사용 방어까지 확장된 바인딩이다.

---

## 깊이 들어가기

### 1. mTLS client auth만으로는 토큰 재사용까지 막지 못할 수 있다

예:

- token endpoint에서 mTLS로 client를 인증
- access token은 일반 bearer로 발급

이 경우:

- 토큰을 누가 받아 갔는지는 강하게 확인
- 하지만 받아 간 토큰이 다른 경로에서 재사용되는지는 별도 문제

### 2. certificate-bound token은 token use 시점까지 바인딩을 유지한다

resource server는:

- access token의 binding 정보
- 현재 TLS client certificate

를 함께 봐서 일치하는지 확인한다.

즉 토큰 탈취 후 다른 certificate로의 재사용을 줄인다.

### 3. load balancer와 TLS termination ownership이 중요하다

이 구조에서 가장 중요한 운영 질문:

- 누가 client certificate를 실제로 검증하는가
- upstream에 어떤 증거를 전달하는가
- 그 전달 자체는 또 어떻게 신뢰하는가

termination ownership이 흐리면 cert-bound token도 약해진다.

### 4. 브라우저에는 보통 맞지 않는다

certificate-bound token은 대개:

- B2B client
- native client
- service-to-service

에 더 잘 맞는다.

브라우저에서는 certificate lifecycle과 UX가 너무 무겁다.

### 5. DPoP와 비교하면 채널 바인딩 vs 앱 레벨 proof 차이가 있다

- cert-bound token: TLS channel과 certificate에 강하게 묶임
- DPoP: 애플리케이션 레벨 proof와 key에 묶임

둘 다 sender-constrained이지만 운영 층이 다르다.

### 6. rollout 순서를 잘못 잡으면 부분적으로만 안전해진다

가장 흔한 잘못된 전개:

1. authorization server가 cert-bound token 발급을 먼저 켠다
2. 일부 resource server는 아직 binding 검증을 지원하지 않는다
3. gateway는 검증하지만 backend는 전달된 토큰을 bearer처럼 다시 쓴다

이 경우 생기는 문제:

- 어떤 경로는 sender-constrained, 어떤 경로는 사실상 bearer
- 장애 시 운영자가 "일단 검증 끄자"며 fallback regression을 넣기 쉬움
- 로그에는 mTLS가 보이므로 안전하다고 착각하기 쉬움

그래서 rollout 단위는 보통 "전체 플랫폼"이 아니라 `audience`, `resource server class`, `gateway path` 단위로 쪼개야 한다.

### 7. rotation과 recovery도 다르다

- mTLS client auth: cert rotation, trust bundle rollout
- cert-bound token: cert rotation + 기존 token binding tail 처리

즉 certificate-bound token은 token lifecycle까지 포함해 더 복잡하다.

특히 cert rotation 시에는 다음을 같이 봐야 한다.

- old cert에 묶인 token TTL이 얼마나 남았는가
- old/new cert overlap 동안 어느 thumbprint를 허용할 것인가
- client가 새 cert를 받자마자 token도 재발급받는가
- resource server가 rotated cert metadata를 일관되게 보는가

### 8. failure policy를 미리 정하지 않으면 rollback이 bearer downgrade가 된다

sender-constrained route에서 실패했을 때 선택지는 보통 세 가지다.

- fail closed: high-risk API는 즉시 거부
- limited degrade: 읽기 전용이나 낮은 위험 audience만 임시 우회
- hard rollback: bound token 발급 자체를 중단하고 새 bearer 정책으로 명시 전환

여기서 가장 나쁜 선택은 "검증기가 에러 나면 그냥 bearer처럼 통과"다.  
이렇게 되면 장애 복구가 아니라 보안 경계 제거가 된다.

---

## 실전 시나리오

### 시나리오 1: token endpoint는 mTLS인데 resource server는 bearer처럼 받는다

문제:

- issuance는 보호되지만 token replay는 열려 있다

대응:

- certificate-bound token 도입 여부를 검토한다
- 최소한 high-risk audience만 sender-constrained로 좁힌다

### 시나리오 2: load balancer 뒤에서 client cert identity가 누락된다

문제:

- binding check 근거가 흔들린다

대응:

- TLS termination ownership을 명확히 한다
- trusted metadata 전달 경로를 점검한다

### 시나리오 3: authorization server는 cert-bound token을 발급하지만 일부 API는 아직 bearer만 안다

문제:

- client는 같은 access token을 들고 다니는데
- API별로 검증 수준이 다르다

대응:

- audience별로 발급 정책을 나눈다
- bound token을 받는 API와 bearer API를 분리한다
- mixed support 기간에는 acceptance 로그를 따로 본다

### 시나리오 4: certificate rotation 직후 기존 access token이 대량 실패한다

문제:

- 새 cert로 mTLS는 붙지만 old cert thumbprint에 묶인 token이 남아 있다

대응:

- cert rotation 직후 token re-issue를 강제한다
- token TTL을 cert overlap 창보다 길게 두지 않는다
- rotation 전후 thumbprint mismatch 지표를 별도 경보로 둔다

### 시나리오 5: browser에도 동일 패턴을 억지로 적용하려 한다

문제:

- certificate UX와 lifecycle이 과도하다

대응:

- 브라우저는 BFF + server-side token이나 DPoP 적합성을 다시 본다

---

## 코드로 보기

### 1. 개념 비교

```text
mTLS client auth = issuance/auth path 강화
cert-bound access token = token use path까지 바인딩 강화
```

### 2. 운영 체크리스트

```text
1. client certificate를 누가 검증하는가
2. resource server가 binding check를 어디서 하는가
3. authorization server와 resource server가 같은 binding semantics를 공유하는가
4. TLS termination metadata를 upstream이 신뢰 가능한가
5. cert rotation과 token tail을 함께 운영할 수 있는가
6. 장애 시 fail-closed / limited-degrade / rollback 기준이 있는가
7. 브라우저가 아닌 환경에만 제한하는가
```

### 3. rollout 순서 개념

```text
1. mTLS client auth 경로를 안정화한다
2. resource server가 certificate binding 검증을 이해하는지 확인한다
3. 특정 audience에만 cert-bound token 발급을 켠다
4. cert rotation과 token re-issue 경로를 함께 검증한다
5. acceptance mismatch가 없을 때 범위를 넓힌다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| mTLS client auth only | issuance 신원이 강하다 | token replay까지는 못 막을 수 있다 | token endpoint 보호 |
| certificate-bound token | replay 저항성이 더 강하다 | TLS/control plane, cert rotation tail, partial rollout 복잡도 높다 | B2B, service-to-service |
| DPoP | 앱 레벨에서 유연하다 | proof store/key lifecycle이 필요하다 | public/native client |
| bearer token | 단순하다 | 탈취 후 재사용이 쉽다 | 저위험/단순 환경 |

### 4. rollout failure 매트릭스

| 실패 유형 | 실제로 깨지는 지점 | 위험 |
|-----------|--------------------|------|
| AS/RS 지원 불일치 | AS는 bound token 발급, RS는 bearer처럼 수용 | sender-constrained 공백 |
| TLS metadata 손실 | LB/ingress 뒤에서 cert thumbprint 전달 실패 | 정상 요청 거부 또는 잘못된 우회 |
| cert rotation tail | old cert bound token이 새 cert와 충돌 | 대량 401/403 |
| emergency fallback | 검증 실패 시 bearer 허용 | 보안 경계 붕괴 |

## 한 줄 정리

mTLS client auth는 client identity를 강하게 만들고, certificate-bound token은 token 재사용까지 줄이는 장치다. 둘의 차이는 개념 설명보다 mixed rollout, TLS metadata, cert rotation tail에서 더 선명하게 드러난다.

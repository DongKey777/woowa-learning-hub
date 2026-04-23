# Proof-of-Possession vs Bearer Token Trade-offs

> 한 줄 요약: bearer token은 단순성과 호환성이 강하고, proof-of-possession 계열은 재사용 저항성이 강하지만 키 관리와 클라이언트 복잡도가 커지므로, 토큰 탈취 위협 모델과 클라이언트 환경을 기준으로 선택해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DPoP / Token Binding Basics](./dpop-token-binding-basics.md)
> - [mTLS Client Auth vs Certificate-Bound Access Token](./mtls-client-auth-vs-certificate-bound-access-token.md)
> - [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)
> - [Device Binding Caveats](./device-binding-caveats.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
> - [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)

retrieval-anchor-keywords: proof of possession vs bearer, bearer token tradeoffs, PoP token, sender-constrained token, DPoP vs bearer, token binding, stolen token replay, key-bound token, token replay resistance, certificate-bound access token, mTLS-bound token, partial rollout, bearer fallback, sender-constrained rollout failure

---

## 핵심 개념

토큰 전달 방식은 크게 두 부류로 볼 수 있다.

- bearer token: 토큰만 있으면 사용 가능
- proof-of-possession(PoP) token: 토큰 외에 키 소유 증명이 필요

이 차이는 단순 구현 디테일이 아니라 탈취 후 재사용 위험을 바꾼다.

---

## 깊이 들어가기

### 1. bearer token의 장점은 단순성이다

- 대부분의 클라이언트가 쉽게 지원
- 프록시/게이트웨이/SDK 호환성이 좋음
- 디버깅과 운영이 단순

하지만 단점도 명확하다.

- 복사되는 순간 재사용 가능
- 로그/브라우저 storage/debug output 노출에 취약
- 탈취 후 소유 증명이 없음

### 2. PoP 계열은 하나가 아니라 여러 층으로 나뉜다

대표 예:

- DPoP: 애플리케이션 레벨 proof를 매 요청에 붙인다
- certificate-bound token: access token을 특정 client certificate와 묶는다
- mTLS client auth only: client를 강하게 인증하지만, 토큰 자체가 sender-constrained는 아닐 수 있다
- device-bound session: 디바이스 또는 하드웨어 키와 세션을 묶는다

장점:

- 토큰만 유출돼서는 재사용이 어렵다
- replay 저항성이 커진다

대신 비용:

- 클라이언트 키 생성/보관 필요
- proof 검증과 replay store 필요
- 브라우저 환경에서는 key 보관이 애매할 수 있음

즉 `PoP = DPoP`가 아니라, 어느 계층에서 sender를 묶는지 먼저 구분해야 한다.

### 3. 위협 모델이 선택을 바꾼다

bearer가 충분한 경우:

- 낮은 위험 read API
- short-lived token + BFF 구조
- 내부망의 단순 service token

PoP가 유리한 경우:

- 고위험 API
- 토큰 탈취 표면이 큰 public client
- mobile/native app에서 key 보관이 상대적으로 가능한 경우

### 4. 브라우저에서는 PoP가 항상 답이 아니다

브라우저에서 key를 안전하게 다루기 어렵다면:

- BFF + cookie + server-side token storage

가 더 현실적일 수 있다.

즉 브라우저의 PoP는 토큰 이론보다 실제 key lifecycle이 더 중요하다.

### 5. mTLS client auth와 certificate-bound token은 같은 말이 아니다

- mTLS client auth only: token endpoint나 API가 "지금 접속한 client가 누구인지"를 확인
- certificate-bound token: 발급된 token을 "같은 certificate를 든 caller만 쓰게" 제한

따라서 다음 조합이 모두 가능하다.

- mTLS client auth + bearer access token
- mTLS client auth + certificate-bound access token
- bearer access token + 별도 DPoP

실무에서 헷갈리는 이유는 둘 다 client certificate를 쓰기 때문이다. 하지만 보호 경계는 다르다.

### 6. service-to-service에서는 mTLS와 PoP를 같이 볼 수 있다

서비스 간에는:

- mTLS로 채널/호출 주체 인증
- JWT bearer로 user/delegated context 전달
- 필요 시 sender-constrained token 추가

즉 bearer vs PoP는 이분법이라기보다 계층 조합일 때가 많다.

### 7. rollout은 토큰 종류보다 더 자주 실패한다

sender-constrained 전환은 보통 한 번에 끝나지 않는다.

- authorization server는 이미 bound token을 발급하기 시작했다
- 일부 resource server는 아직 binding 검증을 모른다
- gateway는 검사하지만 내부 서비스는 bearer처럼 통과시킨다
- TLS termination 계층이 cert identity를 upstream에 안정적으로 전달하지 못한다

이 상태에서 생기는 대표 실패:

- mixed fleet acceptance: 어떤 노드는 PoP를 검사하고 어떤 노드는 bearer처럼 받음
- fallback regression: 장애 대응 중 `if proof missing then accept bearer`가 들어감
- cert metadata loss: LB/ingress 재설정 후 certificate thumbprint가 backend까지 안 감
- stale token tail: cert rotation 뒤에도 old certificate에 묶인 token이 살아 있음

즉 sender-constrained는 발급만 켜면 끝나는 기능이 아니라, 검증 경로 전체를 동시에 맞춰야 하는 rollout 기능이다.

### 8. misuse detection과 recovery도 달라진다

bearer 사고:

- token reuse detection
- session quarantine
- revoke 속도 중요

PoP 사고:

- proof replay detection
- key mismatch
- key rotation/registration 문제
- partial rollout mismatch 추적

즉 stronger token type을 선택해도 운영 신호는 새로 생긴다.

### 9. PoP는 fallback 설계가 어렵다

가장 위험한 순간:

- PoP 검증 실패 시 bearer처럼 받아 주는 fallback

이건 경계를 바로 무너뜨린다.  
PoP를 도입했다면 failure mode도 명확히 분리해야 한다.

특히 rollout 중에는 다음처럼 정책을 쪼개는 편이 낫다.

- sender-constrained가 필수인 audience는 fail-closed
- 아직 migration 전인 audience만 명시적으로 bearer 허용
- fallback 여부를 코드 분기 대신 route/audience 정책으로 관리

### 10. 선택 기준은 "이론상 더 안전한가"보다 "우리 환경에서 운영 가능한가"다

필요한 질문:

- 키를 어디에 저장하는가
- key loss/recovery를 어떻게 처리하는가
- replay store 장애 시 어떻게 할 것인가
- 브라우저/모바일/서버별 지원 수준은 어떤가
- mixed rollout 기간 동안 어떤 resource만 sender-constrained로 강제할 것인가
- cert rotation과 bound token tail을 누가 정리할 것인가

---

## 실전 시나리오

### 시나리오 1: browser SPA가 localStorage bearer token을 직접 든다

문제:

- XSS 후 바로 재사용된다

대응:

- BFF 구조로 전환을 검토한다
- 브라우저 PoP보다 server-side translation이 더 현실적인지 본다

### 시나리오 2: mobile app은 secure enclave key를 쓸 수 있다

문제:

- 고위험 API에 bearer만 쓰기엔 아쉽다

대응:

- DPoP 또는 device-bound token을 검토한다
- key loss/recovery UX를 같이 설계한다

### 시나리오 3: PoP 검증이 일부 route에서 깨진다고 bearer fallback을 연다

문제:

- 보안 목적 자체가 사라진다

대응:

- route class별로 fail policy를 분리한다
- PoP failure를 별도 incident로 다룬다

### 시나리오 4: B2B API에 cert-bound token을 켰는데 일부 resource server가 아직 모른다

문제:

- 어떤 서버는 certificate binding을 검사하고
- 어떤 서버는 bearer처럼 통과시킨다

대응:

- audience 단위로 rollout한다
- 지원하지 않는 resource server에는 bound token을 보내지 않는다
- mixed fleet 기간 동안 acceptance matrix를 로그로 확인한다

### 시나리오 5: client certificate rotation 뒤 기존 bound token이 연속 실패한다

문제:

- 새 certificate는 정상인데 old cert에 묶인 access token이 아직 남아 있다

대응:

- cert rotation과 token TTL을 함께 설계한다
- old/new cert overlap과 token 재발급 창을 같이 둔다
- emergency 시에는 cert rollback이 아니라 token re-issue 경로를 먼저 연다

---

## 코드로 보기

### 1. 단순 비교표

| 방식 | sender를 어디에 묶는가 | 장점 | 주된 실패 지점 |
|------|--------------------------|------|------------------|
| bearer | 묶지 않음 | 가장 단순하고 호환성 높음 | 탈취 즉시 재사용 |
| DPoP | 앱 레벨 key + proof | public/native client에 유연 | proof replay, key storage, proxy/path mismatch |
| certificate-bound token | TLS client certificate + token | B2B/service에서 강한 재사용 저항성 | cert rotation tail, TLS termination metadata loss |
| mTLS client auth only | 연결 시 client 인증 | issuance/client identity 강화 | token 자체는 bearer일 수 있음 |
| BFF + server-side token | 브라우저 밖 서버 세션에 보관 | 브라우저 token 노출 감소 | session store/translation 계층 운영 필요 |

### 2. rollout 체크리스트

```text
1. 현재 위협 모델이 token theft/replay에 얼마나 민감한가
2. 클라이언트가 key를 안전하게 보관할 수 있는가
3. authorization server와 resource server가 같은 sender-constrained 방식을 이해하는가
4. TLS termination 또는 gateway가 binding evidence를 손상 없이 넘기는가
5. cert rotation / key rotation / token TTL이 충돌하지 않는가
6. PoP 검증 실패 시 fallback 정책이 명확한가
7. BFF 구조가 더 현실적인 대안은 아닌가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| bearer token | 단순하고 호환성이 좋다 | 탈취 후 재사용이 쉽다 | 저위험 API, 단순 통합 |
| DPoP | replay 저항성이 높고 public client에 비교적 유연하다 | proof/key 관리, replay store, route 정합성 필요 | public API, native/mobile |
| cert-bound token | mTLS 경로에서 강한 재사용 저항성을 준다 | TLS/control plane, cert rotation, partial rollout 복잡도 높음 | B2B, service-to-service |
| mTLS client auth only | client identity를 강하게 만든다 | 토큰 재사용 방어는 별도 | token endpoint 보호, B2B client 식별 |
| BFF + server-side token | 브라우저 노출을 줄인다 | session store/CSRF 운영 필요 | 웹앱, browser-heavy 환경 |

판단 기준은 이렇다.

- 브라우저인지 모바일인지 서버인지
- token theft가 주된 위협인지
- key lifecycle을 운영할 수 있는지
- sender-constrained failure mode를 감당할 수 있는지
- mixed rollout과 rollback을 audience 단위로 설계할 수 있는지

---

## 꼬리질문

> Q: bearer token과 PoP의 가장 큰 차이는 무엇인가요?
> 의도: possession 증명 여부를 구분하는지 확인
> 핵심: bearer는 토큰만 있으면 되고, PoP는 키 소유 증명이 추가로 필요하다.

> Q: PoP가 있으면 토큰 탈취가 완전히 해결되나요?
> 의도: key theft와 replay store 문제를 아는지 확인
> 핵심: 아니다. 키 탈취, proof replay, key lifecycle 문제가 여전히 남는다.

> Q: 브라우저에서도 PoP가 항상 bearer보다 낫나요?
> 의도: 환경 제약을 고려하는지 확인
> 핵심: 아니다. key 보관이 애매하면 BFF 구조가 더 현실적일 수 있다.

> Q: PoP 실패 시 bearer fallback을 열어도 되나요?
> 의도: failure mode의 위험을 이해하는지 확인
> 핵심: 보통 안 된다. sender-constrained 보안 경계를 스스로 무너뜨리기 때문이다.

> Q: mTLS client auth를 쓰면 자동으로 cert-bound token이 되나요?
> 의도: issuance 인증과 token use 바인딩을 구분하는지 확인
> 핵심: 아니다. mTLS client auth만으로는 access token이 여전히 bearer일 수 있다.

> Q: sender-constrained rollout에서 가장 흔한 장애는 무엇인가요?
> 의도: mixed-fleet와 rotation tail을 이해하는지 확인
> 핵심: 일부 서버만 검증하거나, cert/key rotation과 token TTL이 어긋나서 정상 요청이 실패하는 경우가 흔하다.

## 한 줄 정리

PoP와 bearer의 선택은 더 안전한 토큰 이론을 고르는 문제가 아니라, sender를 어느 계층에 묶을지와 그 rollout 실패를 어떤 운영 복잡도로 감당할지 정하는 문제다.

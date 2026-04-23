# Gateway Auth Context Headers / Trust Boundary

> 한 줄 요약: gateway가 인증을 끝냈다고 해서 upstream 서비스가 아무 auth header나 믿어도 되는 것은 아니며, strip/overwrite, hop identity, canonical context가 함께 있어야 header spoofing과 confused deputy를 막을 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)
> - [Workload Identity / User Context Propagation Boundaries](./workload-identity-user-context-propagation-boundaries.md)
> - [Trust Boundary Bypass / Detection Signals](./trust-boundary-bypass-detection-signals.md)
> - [Token Exchange / Impersonation Risks](./token-exchange-impersonation-risks.md)
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [API Gateway auth / rate limit chain](../network/api-gateway-auth-rate-limit-chain.md)
> - [Forwarded / X-Forwarded-For / X-Real-IP 신뢰 경계](../network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
> - [Proxy Header Normalization Chain / Trust Boundary](../network/proxy-header-normalization-chain-trust-boundary.md)

retrieval-anchor-keywords: gateway auth header, trusted auth context, X-Authenticated-User, X-User-Id spoofing, edge authentication, header stripping, auth context propagation, confused deputy, gateway trust boundary, internal auth header, forwarded identity, caller identity, boundary bypass

---

## 핵심 개념

API gateway나 auth proxy가 access token을 검증한 뒤 upstream 서비스에 이런 정보를 넘기는 경우가 많다.

- user id
- tenant id
- scope
- actor type
- auth time

문제는 여기서부터 시작된다.

- 클라이언트가 같은 이름의 header를 직접 넣을 수 있다
- 일부 경로는 gateway를 우회해 서비스에 직접 들어올 수 있다
- 서비스가 bearer token과 propagated header를 동시에 받아 일관성이 깨질 수 있다

즉 gateway auth context는 "편한 최적화"가 아니라 별도의 신뢰 경계 설계다.

---

## 깊이 들어가기

### 1. 한 hop에서는 하나의 권위 있는 인증 소스만 둬야 한다

다음 두 가지를 동시에 허용하면 사고가 난다.

- gateway가 검증한 `X-Authenticated-User`
- 서비스가 직접 읽는 `Authorization: Bearer ...`

둘이 불일치할 때 어느 쪽이 진짜인지 모호해진다.

그래서 hop별 규칙이 필요하다.

- edge에서만 외부 bearer token을 받는다
- 내부 hop에서는 canonical header만 받는다
- 또는 내부용 exchanged token만 받는다

중요한 것은 "복수의 진실 소스"를 만들지 않는 것이다.

### 2. strip/overwrite가 없으면 header spoofing이 된다

가장 흔한 실수는 gateway가 header를 추가하기만 하고, 클라이언트가 보낸 동명 header를 먼저 제거하지 않는 것이다.

안전한 edge 동작:

1. 외부에서 들어온 trusted auth header를 모두 제거한다
2. gateway가 검증을 마친 뒤 canonical header를 다시 쓴다
3. upstream은 gateway를 거친 hop에서 온 것만 믿는다

즉 `X-User-Id`를 쓴다는 사실보다, 누가 그 header를 overwrite할 권한을 가지는지가 더 중요하다.

### 3. direct exposure가 남아 있으면 내부 header는 외부 입력이 된다

서비스가 원래 internal only라고 생각해도 실제 배포에서는 이런 구멍이 생긴다.

- 잘못된 ingress rule
- debug용 node port
- sidecar bypass 경로
- 내부 ALB가 인터넷에서 reachable

이 상태에서 앱이 `X-Authenticated-User`를 그대로 믿으면, 공격자는 토큰 검증 없이 임의 사용자가 된다.

그래서 header trust는 네트워크 토폴로지와 분리해서 생각하면 안 된다.

### 4. canonical auth context는 작고 명시적이어야 한다

gateway가 모든 claim과 role 목록을 덤프하듯 넘기면 downstream drift가 커진다.

보통은 아래처럼 최소 필드만 남기는 편이 낫다.

- subject or actor id
- tenant id
- authentication strength or auth time
- token id or trace id
- coarse scope summary
- client id
- issuer

그리고 schema version을 둬야 한다.

header 예시:

```text
X-Auth-Subject: user-123
X-Auth-Tenant: tenant-a
X-Auth-Client: web-bff
X-Auth-Context-Version: 3
```

### 5. header trust는 gateway identity와 내부 채널 보호에 묶어야 한다

upstream 서비스는 "header가 존재한다"가 아니라 "trusted gateway가 붙인 header다"를 확인해야 한다.

현실적인 방어선:

- gateway와 service 사이 mTLS
- mesh identity allowlist
- internal network segmentation
- signed internal token exchange

즉 header는 payload일 뿐이고, hop identity는 별도로 보장해야 한다.

### 6. exchanged token이 header보다 더 안전한 경우가 많다

단순 header 전달은 구현이 쉽지만, hop 수가 늘수록 약점이 커진다.

대안:

- gateway가 외부 bearer token을 검증한다
- 내부 전용 audience의 짧은-lived token을 재발급한다
- downstream은 그 내부 token만 검증한다

이 방식의 장점:

- trust source가 다시 명확해진다
- claim set을 최소화할 수 있다
- replay 범위를 internal audience로 좁힌다

### 7. cache, queue, log에 auth header를 영속 권한처럼 남기면 안 된다

auth header는 요청 순간의 전달 정보다.  
이를 그대로 queue message, cache key, batch input에 남기면 시간이 흐른 뒤 stale authorization 문제가 생긴다.

예를 들어:

- export job가 2시간 뒤 실행된다
- 그 사이 사용자가 tenant에서 제거됐다
- worker가 예전 `X-Auth-Tenant`를 근거로 작업을 계속한다

따라서 async 경계에서는 header 재사용이 아니라 재평가 모델이 필요하다.

### 8. 로그에는 외부 응답과 내부 결정을 분리해 남겨야 한다

외부에는 404를 주더라도 내부 로그에는 아래가 필요하다.

- gateway verified subject
- propagated context version
- trusted hop identity
- upstream decision reason
- route that bypassed gateway인지 여부

이 정보가 없으면 "header spoofing인지, policy deny인지, gateway bypass인지"를 분리하기 어렵다.

---

## 실전 시나리오

### 시나리오 1: direct service endpoint가 열려 있어 임의 header로 로그인 우회

문제:

- 서비스는 internal route라고 가정하고 `X-User-Id`를 신뢰한다
- 하지만 특정 ingress가 서비스를 직접 노출한다

대응:

- 외부 reachable path를 inventory로 관리한다
- trusted header를 읽기 전에 gateway identity를 확인한다
- 서비스가 직접 노출될 수 있으면 internal exchanged token으로 바꾼다

### 시나리오 2: 어떤 경로는 gateway header를, 어떤 경로는 bearer token을 읽는다

문제:

- 같은 API라도 route마다 인증 소스가 달라진다
- 401/403 분기와 audit log가 일관되지 않다

대응:

- route class별 canonical auth source를 문서화한다
- service 진입점에서 둘 중 하나만 허용한다
- gateway와 app의 책임 경계를 테스트로 고정한다

### 시나리오 3: auth header를 queue에 넣어 delayed job가 stale 권한으로 실행된다

문제:

- 요청 시점 권한과 실행 시점 권한이 다르다

대응:

- queue에는 actor/tenant/policy version만 싣고 실행 시 재검증한다
- 고정 snapshot이 필요한 경우 approval artifact와 만료 시간을 둔다

---

## 코드로 보기

### 1. trusted header를 읽기 전 gateway identity를 확인하는 개념

```java
public AuthContext resolve(Request request) {
    if (request.hasHeader("X-Auth-Subject") && !request.isFromTrustedGateway()) {
        throw new SecurityException("untrusted auth header source");
    }

    if (request.hasHeader("X-Auth-Subject")) {
        return AuthContext.fromGatewayHeaders(request.headers());
    }

    throw new SecurityException("missing canonical auth context");
}
```

핵심은 header 파싱보다 source verification이 먼저라는 점이다.

### 2. canonical auth context 예시

```java
public record AuthContext(
        String subject,
        String tenantId,
        String clientId,
        String issuer,
        String contextVersion,
        Instant authenticatedAt
) {
}
```

### 3. 운영 체크리스트

```text
1. edge가 외부 입력의 trusted auth header를 strip/overwrite 하는가
2. upstream이 trusted gateway hop identity를 별도로 확인하는가
3. 내부 경로에서 bearer token과 header를 동시에 허용하지 않는가
4. queue/cache/log에 auth header를 장기 권한처럼 재사용하지 않는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| raw bearer token pass-through | 단순하다 | 모든 서비스가 외부 토큰 검증 책임을 진다 | 서비스 수가 적고 일관된 검증 라이브러리가 있을 때 |
| normalized gateway headers | 구현이 가볍다 | spoofing과 bypass 설계가 약하면 위험하다 | internal only 경로가 강하게 보장될 때 |
| internal exchanged token | trust source가 명확하다 | token exchange 운영이 필요하다 | 다수 서비스, 다중 hop, zero-trust 경계 |
| signed auth context envelope | header보다 무결성이 강하다 | 검증 로직과 키 운영이 추가된다 | gateway와 앱이 분리되고 hop가 여러 개인 경우 |

판단 기준은 이렇다.

- direct service exposure 가능성이 있는가
- internal hop identity를 mTLS나 mesh로 보장할 수 있는가
- gateway와 app이 같은 팀/배포 경계 안에 있는가
- async와 cache 경계에서 auth context를 어떻게 다룰 것인가

---

## 꼬리질문

> Q: gateway가 토큰 검증을 끝냈으면 서비스는 header만 믿어도 되나요?
> 의도: payload와 source trust를 분리하는지 확인
> 핵심: 아니다. 그 header를 누가 붙였는지와 direct bypass 가능성까지 확인해야 한다.

> Q: 왜 bearer token과 propagated header를 동시에 허용하면 안 되나요?
> 의도: single source of truth를 이해하는지 확인
> 핵심: 불일치 시 어떤 인증 결과가 진짜인지 모호해져 confused deputy를 만든다.

> Q: 모든 claim을 header로 넘기면 편하지 않나요?
> 의도: canonical context 최소화의 필요를 아는지 확인
> 핵심: stale policy와 downstream drift가 커지므로 최소 필드만 넘기는 편이 낫다.

> Q: auth header를 queue에 넣으면 왜 위험한가요?
> 의도: 시간 경계의 stale authorization를 이해하는지 확인
> 핵심: 요청 시점 권한을 실행 시점에도 그대로 믿게 되어 회수된 권한이 반영되지 않을 수 있다.

## 한 줄 정리

Gateway auth header 패턴의 핵심은 "무슨 header를 쓰는가"가 아니라 "누가 그 header를 overwrite할 수 있고 upstream은 어떤 hop identity를 근거로 그것을 신뢰하는가"를 명확히 하는 것이다.

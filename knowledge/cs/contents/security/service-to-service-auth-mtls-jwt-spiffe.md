---
schema_version: 3
title: 'Service-to-Service Auth: mTLS, JWT, SPIFFE'
concept_id: security/service-to-service-auth-mtls-jwt-spiffe
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- service-to-service auth
- mTLS
- SPIFFE
- SPIRE
aliases:
- service-to-service auth
- mTLS
- SPIFFE
- SPIRE
- workload identity
- JWT
- service mesh
- certificate rotation
- caller identity
- user context propagation
- certificate-bound token
- 'Service-to-Service Auth: mTLS, JWT, SPIFFE'
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/network/service-mesh-sidecar-proxy.md
- contents/network/tls-loadbalancing-proxy.md
- contents/security/oauth2-authorization-code-grant.md
- contents/security/jwt-deep-dive.md
- contents/security/mtls-client-auth-vs-certificate-bound-access-token.md
- contents/security/workload-identity-user-context-propagation-boundaries.md
- contents/spring/spring-security-architecture.md
- contents/spring/spring-oauth2-jwt-integration.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- 'Service-to-Service Auth: mTLS, JWT, SPIFFE 핵심 개념을 설명해줘'
- service-to-service auth가 왜 필요한지 알려줘
- 'Service-to-Service Auth: mTLS, JWT, SPIFFE 실무 설계 포인트는 뭐야?'
- service-to-service auth에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: '이 문서는 security 카테고리에서 Service-to-Service Auth: mTLS, JWT, SPIFFE를 다루는 deep_dive 문서다. 서비스 간 인증은 "누가 호출했는가"를 증명하는 문제이고, mTLS는 네트워크 경계에서, JWT는 메시지/클레임 경계에서 그 증명을 맡는다. 검색 질의가 service-to-service auth, mTLS, SPIFFE, SPIRE처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.'
---
# Service-to-Service Auth: mTLS, JWT, SPIFFE

> 한 줄 요약: 서비스 간 인증은 "누가 호출했는가"를 증명하는 문제이고, mTLS는 네트워크 경계에서, JWT는 메시지/클레임 경계에서 그 증명을 맡는다.

**난이도: 🔴 Advanced**

> related-docs:
> - [Service Mesh, Sidecar Proxy](../network/service-mesh-sidecar-proxy.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [mTLS Client Auth vs Certificate-Bound Access Token](./mtls-client-auth-vs-certificate-bound-access-token.md)
> - [Workload Identity / User Context Propagation Boundaries](./workload-identity-user-context-propagation-boundaries.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)
> - [Spring OAuth2 + JWT 통합](../spring/spring-oauth2-jwt-integration.md)

retrieval-anchor-keywords: service-to-service auth, mTLS, SPIFFE, SPIRE, workload identity, JWT, service mesh, certificate rotation, caller identity, user context propagation, certificate-bound token

---

## 핵심 개념

서비스 간 인증은 사용자 로그인과 다르다.

- 사용자는 "브라우저 밖의 사람"을 확인한다
- 서비스 간 인증은 "어떤 workload가 다른 workload를 호출했는가"를 확인한다

여기서 자주 섞이는 개념이 있다.

- `mTLS`: 양쪽이 서로 인증서를 제시하고 통신 자체를 암호화한다
- `JWT`: 토큰 안의 클레임으로 호출 주체와 권한 범위를 전달한다
- `SPIFFE`: workload identity를 표준화한 아이디 체계다
- `SPIRE`: SPIFFE identity를 발급하고 회전시키는 구현체다

즉, 이 문서의 핵심은 "서비스 간 신뢰를 코드가 아니라 신원과 전송 계층으로 어떻게 나눌 것인가"다.

---

## 깊이 들어가기

### 1. 왜 서비스 간 인증이 어려운가

사람 로그인은 대체로 중앙 IdP 하나로 정리할 수 있지만, 서비스 간 통신은 훨씬 자주 바뀐다.

- pod가 계속 재시작된다
- IP가 고정되지 않는다
- 서비스가 수평 확장된다
- 팀별로 배포 주기가 다르다

그래서 "이 IP는 믿는다" 같은 네트워크 신뢰는 금방 무너진다.  
Zero-trust 스타일에서는 네트워크 내부라도 기본적으로 믿지 않고, 호출할 때마다 신원과 정책을 확인한다.

### 2. mTLS가 하는 일

mTLS는 TLS 위에 client authentication을 더한 것이다.

- 서버는 서버 인증서를 제시한다
- 클라이언트도 client certificate를 제시한다
- 서로가 trusted issuer 체인 안에 있는지 검증한다

이 방식의 장점은 명확하다.

- 전송 구간이 암호화된다
- 통신 주체의 신원이 강하게 보장된다
- 애플리케이션 코드가 "이 요청이 진짜 우리 서비스인가"를 직접 구현하지 않아도 된다

### 3. SPIFFE와 SPIRE

SPIFFE는 workload identity를 나타내는 표준 문자열을 정의한다.

예시:

```text
spiffe://prod.example.com/ns/payments/sa/orders-api
```

이 ID는 "어디서 실행되느냐"가 아니라 "무슨 workload냐"를 표현하려고 쓴다.  
SPIRE는 이 ID를 실제 인증서/SVID로 발급하고, workload가 안전하게 자기 identity를 증명하도록 돕는다.

보통 운영 흐름은 이렇다.

1. node attestation 또는 k8s attestation으로 workload를 확인한다
2. SPIRE server가 SVID를 발급한다
3. workload는 짧은 수명의 certificate를 받아 쓴다
4. 만료되면 자동 회전한다

이 구조가 중요한 이유는 certificate rotation을 사람이 수동으로 하지 않아도 되기 때문이다.

### 4. JWT가 하는 일

JWT는 주로 다음에 강하다.

- 사용자 권한 전달
- 서비스 간 호출의 세부 권한 범위 전달
- gateway 이후의 internal authorization

하지만 JWT는 전송 자체를 보호하지 않는다.

- 토큰이 가로채일 수 있다
- 서명 검증은 가능하지만 탈취 방지는 아니다
- 토큰을 어느 서비스까지 허용할지 정책이 필요하다

그래서 서비스 간 auth에서 JWT는 보통 mTLS의 대체재가 아니라 보완재다.

### 5. mTLS와 JWT의 역할 분리

실무에서 가장 안정적인 패턴은 다음 둘을 분리하는 것이다.

- mTLS로 "누가 연결했는가"를 확인한다
- JWT로 "이 호출이 무엇을 할 수 있는가"를 확인한다

예를 들어:

- sidecar proxy가 mTLS로 `orders` 서비스의 identity를 확인한다
- 앱은 JWT의 `scope=inventory.read` 같은 클레임을 보고 세부 인가를 한다

이렇게 하면 네트워크 수준 신원과 애플리케이션 수준 권한을 분리할 수 있다.

---

## 실전 시나리오

### 시나리오 1: 내부망이라서 인증을 안 했다가 침투당함

문제:

- VPC 안이니까 안전하다고 가정했다
- pod 탈취 후 평문 HTTP로 다른 서비스에 접근했다

대응:

- 서비스 간 통신을 전부 mTLS로 강제한다
- 서비스 mesh 또는 sidecar에서 plaintext를 금지한다
- identity 기반 allowlist를 둔다

### 시나리오 2: JWT만 믿고 서비스 간 호출을 허용함

문제:

- bearer token 하나만 있으면 누구나 호출 가능하다
- 토큰이 로그/프록시/디버그 경로로 새면 재사용된다

대응:

- mTLS로 caller identity를 먼저 확인한다
- JWT는 claim-based authorization에만 사용한다
- token audience를 서비스 단위로 좁힌다

### 시나리오 3: certificate rotation이 수동이라 운영이 깨짐

문제:

- 인증서 만료 전에 사람이 배포를 해야 한다
- 몇 개 서비스가 빠지면 장애가 난다

대응:

- SPIRE로 짧은 수명의 SVID를 발급한다
- 자동 회전 주기를 짧게 가져간다
- 만료 경보를 app에서가 아니라 control plane에서 잡는다

---

## 코드로 보기

### 1. SPIFFE ID 기반 정책 예시

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: orders-allow-inventory
  namespace: payments
spec:
  selector:
    matchLabels:
      app: orders
  rules:
    - from:
        - source:
            principals:
              - "spiffe://prod.example.com/ns/payments/sa/inventory-api"
```

이런 정책은 "어느 IP에서 왔는가"보다 "어떤 workload identity인가"에 더 가깝다.

### 2. mTLS 연결 확인 커맨드

```bash
kubectl exec deploy/orders-api -c app -- \
  openssl s_client -connect inventory-api:8443 -showcerts
```

운영에서는 proxy 로그와 함께 봐야 한다.

```bash
kubectl logs deploy/orders-api -c istio-proxy
kubectl describe peerauthentication -n payments
```

### 3. 서비스 간 JWT 검증 예시

```java
public void verifyDownstreamToken(String token) {
    JWT.require(algorithm)
        .withIssuer("orders-api")
        .withAudience("inventory-api")
        .withClaim("scope", "inventory.read")
        .build()
        .verify(token);
}
```

핵심은 `aud`를 넓게 두지 않는 것이다.  
한 번 발급된 토큰이 여러 서비스를 무제한으로 통과하면 zero-trust가 무너진다.

### 4. Spring에서 outbound JWT를 붙이는 개념 예시

```java
public class DownstreamAuthInterceptor implements ClientHttpRequestInterceptor {
    @Override
    public ClientHttpResponse intercept(HttpRequest request, byte[] body, ClientHttpRequestExecution execution)
            throws IOException {
        request.getHeaders().setBearerAuth(tokenService.issueServiceToken("inventory-api"));
        return execution.execute(request, body);
    }
}
```

이 패턴은 "서비스 인증"과 "사용자 인증"을 같이 실어 보내야 할 때 유용하다.  
다만 내부 hop마다 사용자 JWT를 그대로 전달하지 말고, 필요한 claim만 재발급하는 편이 더 안전하다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| mTLS만 사용 | 전송 구간 암호화와 caller identity가 강하다 | 세밀한 비즈니스 권한 표현은 약하다 | 서비스 내부 신원 확인이 우선일 때 |
| JWT만 사용 | 애플리케이션 권한 모델을 세밀하게 표현할 수 있다 | 토큰 탈취와 재사용에 취약하다 | mesh가 없고, API gateway 중심일 때 |
| mTLS + JWT | 신원과 권한을 분리할 수 있다 | 운영과 설계가 더 복잡하다 | zero-trust, MSA, 민감 데이터 서비스 |
| trust the network | 구현이 가장 쉽다 | 내부 침투에 취약하다 | 거의 쓰지 말아야 한다 |

판단 기준은 간단하다.

- 네트워크 경계가 믿을 수 없으면 mTLS가 먼저다
- 서비스마다 권한이 다르면 JWT가 필요하다
- 둘 중 하나만으로 충분하다고 느껴지면, 보통 요구사항을 덜 본 것이다

### zero-trust 결정을 어떻게 내릴까

아래 질문에 "예"가 많을수록 mTLS + SPIFFE/SPIRE 쪽으로 간다.

- pod 탈취를 가정해야 하는가?
- 서로 다른 팀이 같은 클러스터를 공유하는가?
- 내부망도 침투될 수 있다고 보는가?
- 인증서와 identity를 자동 회전해야 하는가?
- 호출 주체를 IP가 아니라 workload 단위로 식별해야 하는가?

JWT는 그 다음 질문에 답한다.

- 이 workload가 무엇을 읽고/쓸 수 있는가?
- 어떤 audience와 scope만 허용할 것인가?
- 사용자 맥락을 hop-by-hop으로 전달할 필요가 있는가?

---

## 꼬리질문

> Q: 서비스 간 인증에서 왜 JWT만으로 끝내면 안 되는가?
> 의도: bearer token의 탈취/재사용 문제를 아는지 확인
> 핵심: JWT는 권한을 담을 수 있지만, 전송 경로 신원 보장은 못 한다.

> Q: mTLS가 있는데 SPIFFE/SPIRE가 왜 필요한가?
> 의도: 인증서 발급 자동화와 workload identity 표준 이해 확인
> 핵심: mTLS는 메커니즘이고, SPIFFE/SPIRE는 identity와 회전을 운영 가능하게 만든다.

> Q: zero-trust에서 네트워크 내부를 왜 믿지 않는가?
> 의도: 경계 기반 보안에서 identity 기반 보안으로의 전환 이해 확인
> 핵심: 내부망도 침해될 수 있으니 호출마다 신원을 검증해야 한다.

> Q: 서비스 mesh가 있으면 애플리케이션에서 아무것도 안 해도 되는가?
> 의도: mesh와 앱 책임 경계 이해 확인
> 핵심: transport auth는 mesh가, business authorization은 앱이 맡는다.

---

## 한 줄 정리

서비스 간 인증은 mTLS로 workload identity를 믿고, JWT로 세부 권한을 나누는 방식이 가장 현실적인 zero-trust 선택이다.

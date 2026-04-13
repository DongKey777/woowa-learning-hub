# API Gateway Control Plane 설계

> 한 줄 요약: API gateway control plane은 라우팅, 인증, rate limit, observability, 정책 배포를 중앙에서 관리하는 엣지 제어 시스템이다.

retrieval-anchor-keywords: api gateway control plane, routing policy, authz, mTLS, rate limit, request transform, canary, api versioning, plugin policy, edge config

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Rate Limiter 설계](./rate-limiter-design.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)

## 핵심 개념

Gateway control plane은 API 요청을 직접 처리하는 게 아니라,  
gateway data plane이 따라야 할 정책을 배포한다.

- route 생성/수정
- auth policy
- rate limit policy
- request/response transform
- canary release
- observability tags

즉, control plane은 엣지에서 동작하는 네트워크 정책의 진원지다.

## 깊이 들어가기

### 1. Control plane과 data plane 분리

```text
Admin / CI
  -> Gateway Control Plane
  -> Policy Store
  -> Config Publisher
  -> Gateway Nodes
  -> Backend Services
```

control plane은 변경과 검증을 담당하고, gateway nodes는 요청을 빠르게 처리한다.

### 2. Capacity Estimation

예:

- 초당 50만 edge request
- route rule 수천 개
- tenant별 policy 수백 개

이 구조에서는 data plane latency가 매우 중요하고, control plane의 변경 fan-out도 무시할 수 없다.

봐야 할 숫자:

- policy propagation delay
- request latency overhead
- routing miss rate
- config refresh error rate
- canary failure rate

### 3. 정책 모델

Gateway가 수행하는 일:

- path / host routing
- header mutation
- JWT validation
- mTLS enforcement
- IP allow/deny
- rate limit
- request timeout

정책은 declarative하게 관리하는 편이 안전하다.

### 4. Canary와 traffic shifting

새 backend로 트래픽을 옮길 때는 순차적으로 해야 한다.

- 1%
- 10%
- 50%
- 100%

그리고 success criteria를 정해야 한다.

- 5xx rate
- latency
- upstream saturation
- business metric

### 5. Tenant-aware edge policy

멀티 테넌트 환경에서는 정책도 tenant-aware여야 한다.

- tenant별 rate limit
- tenant별 backend route
- tenant별 auth scope
- tenant별 logging tag

이 부분은 [멀티 테넌트 SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)와 직접 연결된다.

### 6. Extensibility

실무 gateway는 plugin-style policy가 많다.

- auth plugin
- transform plugin
- logging plugin
- custom header plugin

하지만 plugin이 많아질수록 요청 path가 느려질 수 있으므로 실행 순서를 엄격히 관리해야 한다.

### 7. Failure mode

gateway control plane이 죽어도 request path는 살아야 한다.

대응:

- last-known-good config
- local policy cache
- safe default routing
- emergency bypass rules

## 실전 시나리오

### 시나리오 1: 새 API 버전 출시

문제:

- `/v2`로 일부만 보내고 싶다

해결:

- route policy에 canary 비율 적용
- error budget이 넘으면 rollback

### 시나리오 2: rate limit 조정

문제:

- 특정 tenant가 API를 과하게 호출한다

해결:

- tenant-aware limit 변경
- control plane에서 즉시 배포

### 시나리오 3: 인증 정책 변경

문제:

- 특정 엔드포인트는 mTLS가 필요하다

해결:

- route 단위 auth policy 적용
- config checksum으로 배포 검증

## 코드로 보기

```pseudo
function route(request):
  policy = loadGatewayPolicy(request.host, request.path)
  if !policy.allowed(request):
    return deny()
  upstream = policy.upstream
  return proxy(upstream, request)
```

```java
public GatewayPolicy currentPolicy() {
    return policyCache.loadOrFallback();
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Central control plane | 관리가 쉽다 | 운영 병목 위험 | 중간 규모 |
| Distributed policy sync | 확장성이 좋다 | propagation 복잡 | 대규모 edge |
| Static route config | 단순하다 | 변경이 느리다 | 작은 API |
| Plugin-based gateway | 유연하다 | latency/complexity 증가 | enterprise gateway |
| Last-known-good fallback | 안전하다 | stale policy risk | 필수 안전장치 |

핵심은 gateway가 프록시가 아니라 **엣지 정책을 집행하는 분산 제어 시스템**이라는 점이다.

## 꼬리질문

> Q: gateway control plane과 data plane은 왜 나누나요?
> 의도: 정책 관리와 요청 처리 분리 이해 확인
> 핵심: 변경은 느려도 되지만 요청 처리는 매우 빨라야 하기 때문이다.

> Q: canary를 왜 gateway에서 하죠?
> 의도: 엣지에서 트래픽 조절하는 이유 확인
> 핵심: backend까지 갈 필요 없이 비율 기반 제어가 가능하기 때문이다.

> Q: tenant-aware routing이 왜 필요한가요?
> 의도: 멀티테넌트 정책 격리 이해 확인
> 핵심: tenant별 limit, backend, logging policy가 다를 수 있기 때문이다.

> Q: control plane이 죽으면 어떻게 되나요?
> 의도: fallback과 운영 연속성 확인
> 핵심: last-known-good policy로 request path를 계속 살려야 한다.

## 한 줄 정리

API gateway control plane은 라우팅과 인증, rate limit, canary, 관측성 정책을 중앙에서 배포하고 엣지에서 집행하는 시스템이다.


# Service Mesh Control Plane 설계

> 한 줄 요약: service mesh control plane은 서비스 간 통신 정책, mTLS, traffic shaping, retry/timeout, telemetry 구성을 중앙에서 배포해 sidecar나 node proxy가 일관된 네트워크 동작을 수행하게 만드는 운영 제어 시스템이다.

retrieval-anchor-keywords: service mesh control plane, xds, sidecar proxy, traffic policy, mTLS rollout, retry timeout policy, telemetry config, service identity, canary routing, mesh policy distribution, control plane data plane separation, protocol version skew, capability negotiation, mesh trust root rotation, trust bundle rollback, verifier overlap

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Discovery / Health Routing 설계](./service-discovery-health-routing-design.md)
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
> - [Control Plane / Data Plane Separation 설계](./control-plane-data-plane-separation-design.md)
> - [Distributed Tracing Pipeline 설계](./distributed-tracing-pipeline-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Trust-Bundle Rollback During Cell Cutover 설계](./trust-bundle-rollback-during-cell-cutover-design.md)
> - [Edge Authorization Service 설계](./edge-authorization-service-design.md)
> - [Automated Canary Analysis / Rollback Platform 설계](./automated-canary-analysis-rollback-platform-design.md)
> - [Protocol Version Skew / Compatibility 설계](./protocol-version-skew-compatibility-design.md)
> - [Config Rollback Safety 설계](./config-rollback-safety-design.md)
> - [Capability Negotiation / Feature Gating 설계](./capability-negotiation-feature-gating-design.md)

## 핵심 개념

서비스 수가 늘어나면 각 애플리케이션이 직접 다음을 다 구현하기 어렵다.

- service discovery
- retry / timeout 정책
- mTLS와 인증서 교체
- canary / shadow routing
- telemetry 표준화

service mesh는 이런 공통 네트워크 정책을 proxy data plane으로 모으고,
control plane은 그 proxy들이 따라야 할 정책과 identity를 배포한다.

즉, service mesh control plane은 "네트워크 SDK"가 아니라 **서비스 간 통신을 운영 정책으로 다루는 중앙 제어 시스템**이다.

## 깊이 들어가기

### 1. 왜 mesh control plane이 필요한가

sidecar나 node proxy만 있어서는 부족하다.
누군가는 다음을 계산해 배포해야 한다.

- endpoint set
- route / retry / timeout policy
- mTLS cert and trust bundle
- telemetry sampling / tags
- fault injection rules

정책이 각 서비스에 흩어지면 일관성도 떨어지고 롤백도 어렵다.

### 2. Capacity Estimation

예:

- 서비스 1,000개
- proxy instance 3만 개
- 정책 변경 분당 수백 건
- endpoint update 초당 수천 건

이때 봐야 할 숫자:

- config fan-out latency
- rejected / stale proxy ratio
- control push QPS
- proxy convergence time
- xDS snapshot size

mesh control plane은 QPS 자체보다 fan-out과 convergence가 병목이 되기 쉽다.

### 3. Control plane과 proxy data plane

```text
Policy API / Admin
  -> Mesh Control Plane
  -> Identity / Cert Manager
  -> Config Snapshot / xDS Publisher
  -> Sidecar / Node Proxy
  -> Service-to-Service Traffic
```

data plane proxy는 request path에서 빠르게 동작하고,
control plane은 정책 계산, 배포, 인증서 수명주기를 담당한다.

### 4. Traffic policy lifecycle

대표 정책:

- retry / timeout
- circuit breaking
- request hedging
- canary / weighted route
- shadow traffic
- failover route

중요한 것은 정책 정의보다도 **버전 관리와 rollback**이다.
잘못된 retry policy 하나가 mesh 전체의 retry storm을 만들 수 있다.

### 5. Identity and mTLS rollout

mesh의 큰 장점 중 하나는 service identity 표준화다.
하지만 운영은 쉽지 않다.

- cert issuance
- rotation
- trust bundle distribution
- gradual strict mTLS rollout
- mixed-mode 지원

특히 dedicated cell migration과 issuer/root 전환이 같이 오면 bundle propagation과 rollback window가 route change보다 오래 살아야 한다.
이 좁은 문제를 따로 파고들면 [Trust-Bundle Rollback During Cell Cutover 설계](./trust-bundle-rollback-during-cell-cutover-design.md)로 바로 이어진다.

즉, 보안 정책도 결국 progressive delivery 문제다.

### 6. Observability-rich mesh

mesh는 telemetry를 많이 만들어 낼 수 있지만, 아무렇게나 다 켜면 비용이 폭발한다.

고민할 것:

- default metrics와 labels
- trace propagation
- sampling policy
- route / version / service identity 태그
- log enrichment

관측성은 기본 제공이 아니라 budget과 cardinality 관리가 필요한 제품이다.

### 7. Failure mode

mesh control plane이 죽어도 proxy data plane은 계속 살아야 한다.

대응:

- last-known-good xDS snapshot
- cert cache
- bounded config staleness
- safe default deny/allow rules

mesh가 운영 편의성을 주더라도 control plane dependency를 runtime hard dependency로 만들면 안 된다.

## 실전 시나리오

### 시나리오 1: 서비스 간 strict mTLS 전환

문제:

- 일부 레거시 서비스가 아직 plaintext를 사용한다

해결:

- permissive mode에서 시작한다
- cert rotation과 trust bundle 배포를 안정화한다
- 서비스 그룹별로 strict mode를 점진 전환한다

### 시나리오 2: 내부 API canary routing

문제:

- `payments-v2`를 일부 caller만 사용하게 하고 싶다

해결:

- mesh route policy로 weighted split을 둔다
- trace / metrics에서 caller, route version을 함께 본다
- automated canary analysis와 연계해 승격/롤백한다

### 시나리오 3: control plane partial outage

문제:

- xDS push가 멈췄다

해결:

- proxy는 last-known-good 정책으로 계속 동작한다
- 긴급 정책만 수동 snapshot 경로로 배포한다
- stale window를 넘긴 경우만 경고/점진 축소한다

## 코드로 보기

```pseudo
function publishMeshConfig(change):
  validated = validator.check(change)
  snapshot = compiler.buildSnapshot(validated, serviceRegistry.current())
  xds.publish(snapshot)

function handleTraffic(req):
  policy = proxy.localSnapshot()
  route = policy.match(req)
  return proxy.forward(req, route)
```

```java
public ProxySnapshot currentSnapshot(NodeId nodeId) {
    return snapshotStore.forNode(nodeId).orElse(lastKnownGood(nodeId));
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| App library per service | 단순하다 | 일관성과 운영성이 약하다 | 작은 조직 |
| Service mesh with sidecars | 정책 통일이 쉽다 | 리소스/운영 비용이 높다 | 대규모 플랫폼 |
| Node proxy mesh | sidecar 비용이 낮다 | isolation과 디버깅이 더 어렵다 | 노드 단위 최적화 |
| Rich mesh policy | 강력하다 | 잘못 설정하면 blast radius가 크다 | mature platform |

핵심은 service mesh control plane이 proxy 설정 배포기가 아니라 **서비스 간 통신 정책과 identity, observability를 중앙에서 운영하는 제어 시스템**이라는 점이다.

## 꼬리질문

> Q: service discovery만 있으면 mesh control plane은 필요 없지 않나요?
> 의도: discovery와 policy control 차이 이해 확인
> 핵심: discovery는 endpoint를 알려 주지만, retry/timeout/mTLS/telemetry/traffic shaping 같은 정책 배포는 별도 문제다.

> Q: mesh를 쓰면 앱 코드에서 resilience 로직을 다 지워도 되나요?
> 의도: 책임 경계 이해 확인
> 핵심: 일부 공통 정책은 mesh로 옮길 수 있지만, 비즈니스 의미가 있는 fallback과 idempotency는 앱 레벨 설계가 여전히 필요하다.

> Q: control plane 장애 시 가장 중요한 원칙은?
> 의도: runtime independence 이해 확인
> 핵심: proxy data plane이 last-known-good 정책으로 계속 요청을 처리할 수 있어야 한다.

> Q: mTLS rollout이 왜 progressive delivery 문제인가요?
> 의도: mixed-mode migration 이해 확인
> 핵심: 모든 서비스가 한 번에 strict mode로 갈 수 없으므로 compatibility window와 점진 전환이 필요하기 때문이다.

## 한 줄 정리

Service mesh control plane은 서비스 간 통신 정책, identity, telemetry 구성을 중앙 배포해 proxy data plane이 일관된 네트워크 동작을 하게 만드는 운영 제어 시스템이다.

---
schema_version: 3
title: Service Discovery / Health Routing 설계
concept_id: system-design/service-discovery-health-routing-design
canonical: true
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- dns-vs-discovery
- readiness-vs-outlier-ejection
- warmup-drain-routing-policy
aliases:
- service discovery
- endpoint registry
- health check
- client side load balancing
- dns discovery
- xds
- zone aware routing
- outlier detection
- connection draining
- service mesh control plane
- traffic shifting
- endpoint warmup
- failover routing
- global traffic control
- auth dependency failover
symptoms:
- 서비스 이름만 알면 호출되는 줄 알았는데 실제 endpoint 선택이 어떻게 되는지 모르겠어
- readiness는 붙어 있는데 부분 장애 인스턴스를 왜 더 빨리 빼야 하는지 헷갈려
- warm-up, drain, zone failover를 누가 한 정책으로 묶는지 감이 안 와
intents:
- definition
- design
- troubleshooting
prerequisites:
- system-design/load-balancer-basics
- system-design/load-balancer-drain-and-affinity-primer
- system-design/control-plane-data-plane-separation-design
next_docs:
- system-design/global-traffic-failover-control-plane-design
- system-design/service-mesh-control-plane-design
- system-design/stateful-workload-placement-failover-control-plane-design
linked_paths:
- contents/system-design/load-balancer-drain-and-affinity-primer.md
- contents/system-design/api-gateway-control-plane-design.md
- contents/system-design/config-distribution-system-design.md
- contents/system-design/backpressure-and-load-shedding-design.md
- contents/system-design/multi-region-active-active-design.md
- contents/system-design/edge-authorization-service-design.md
- contents/system-design/distributed-tracing-pipeline-design.md
- contents/system-design/traffic-shadowing-progressive-cutover-design.md
- contents/system-design/shard-rebalancing-partition-relocation-design.md
- contents/system-design/stateful-workload-placement-failover-control-plane-design.md
- contents/system-design/service-mesh-control-plane-design.md
- contents/system-design/control-plane-data-plane-separation-design.md
- contents/system-design/global-traffic-failover-control-plane-design.md
- contents/security/jwt-jwks-outage-recovery-failover-drills.md
- contents/security/auth-incident-triage-blast-radius-recovery-matrix.md
confusable_with:
- system-design/global-traffic-failover-control-plane-design
- system-design/load-balancer-drain-and-affinity-primer
- system-design/service-mesh-control-plane-design
forbidden_neighbors: []
expected_queries:
- service discovery는 DNS랑 뭐가 다르고 health routing까지 왜 같이 봐야 해?
- readiness 말고 outlier detection이나 passive health가 필요한 이유가 뭐야?
- 새 인스턴스 warm-up과 drain 정책을 discovery 쪽에서 왜 같이 다뤄?
- zone 장애가 나면 local 우선 라우팅을 언제 풀어야 해?
- control plane이 죽어도 data plane이 계속 라우팅해야 하는 이유를 설명해줘
contextual_chunk_prefix: |
  이 문서는 학습자가 service discovery를 주소록이 아니라 endpoint 상태와
  routing policy를 결합한 제어 평면으로 이해하게 돕는 advanced deep dive다.
  DNS만으로 충분한가, readiness 외에 passive health가 왜 필요한가, 새
  인스턴스 warm-up과 draining을 누가 묶어 보나, zone 장애 때 local 우선
  정책을 언제 푸나 같은 자연어 질문이 본 문서의 discovery/routing 모델에
  매핑된다.
---
# Service Discovery / Health Routing 설계

> 한 줄 요약: service discovery와 health routing은 서비스 이름을 실제 endpoint 집합으로 해석하고, 건강한 인스턴스로만 트래픽을 보내도록 제어하는 런타임 네트워크 제어 시스템이다.

retrieval-anchor-keywords: service discovery, endpoint registry, health check, client side load balancing, dns discovery, xds, zone aware routing, outlier detection, connection draining, service mesh control plane, traffic shifting, endpoint warmup, failover routing, global traffic control, auth dependency failover, issuer endpoint routing, auth control plane

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Load Balancer Drain and Affinity Primer](./load-balancer-drain-and-affinity-primer.md)
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Edge Authorization Service 설계](./edge-authorization-service-design.md)
> - [Distributed Tracing Pipeline 설계](./distributed-tracing-pipeline-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Shard Rebalancing / Partition Relocation 설계](./shard-rebalancing-partition-relocation-design.md)
> - [Stateful Workload Placement / Failover Control Plane 설계](./stateful-workload-placement-failover-control-plane-design.md)
> - [Service Mesh Control Plane 설계](./service-mesh-control-plane-design.md)
> - [Control Plane / Data Plane Separation 설계](./control-plane-data-plane-separation-design.md)
> - [Global Traffic Failover Control Plane 설계](./global-traffic-failover-control-plane-design.md)
> - [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)
> - [Security: Auth Incident Triage / Blast-Radius Recovery Matrix](../security/auth-incident-triage-blast-radius-recovery-matrix.md)

## 핵심 개념

`user-service`라는 이름만 안다고 요청을 보낼 수 있는 것은 아니다.
실전에서는 다음을 같이 알아야 한다.

- 현재 살아 있는 endpoint는 무엇인가
- 어느 zone이나 region이 더 가까운가
- 새 인스턴스는 warm-up이 끝났는가
- 느리지만 아직 살아 있는 인스턴스를 계속 쓸 것인가
- 장애가 난 endpoint를 언제 다시 복귀시킬 것인가

즉, service discovery는 주소록이 아니라 **이름, 상태, 라우팅 정책을 결합한 제어 평면**이다.
health check, drain, sticky affinity 자체를 먼저 입문 난도로 잡고 싶다면 [Load Balancer Drain and Affinity Primer](./load-balancer-drain-and-affinity-primer.md)부터 읽고 오는 편이 좋다.

## 깊이 들어가기

### 1. discovery와 load balancing은 분리해서 생각한다

보통 두 문제가 섞인다.

- discovery: `payments`라는 논리 이름을 실제 endpoint 집합으로 해석
- routing/load balancing: 그 집합 중 누구에게 보낼지 결정

이 둘을 구분하지 않으면 DNS만 있으면 끝나는 것처럼 보이지만, 실제 운영에서는 health, locality, draining 같은 정책이 더 중요하다.

### 2. Capacity Estimation

예:

- 서비스 500개
- 인스턴스 총 3만 개
- endpoint 변경 이벤트 초당 1천 건
- 클라이언트 요청 QPS 20만

이때 control plane이 보는 숫자:

- registry update rate
- endpoint fan-out
- policy propagation delay
- stale endpoint ratio

data plane이 보는 숫자:

- pick latency
- connection reuse ratio
- retry amplification
- outlier eject 비율

### 3. Registry 모델

대표적인 등록 방식:

- instance self-registration
- orchestrator-driven registration
- sidecar / mesh 기반 자동 발견

중요한 것은 "누가 truth를 관리하는가"다.
컨테이너 오케스트레이터가 있으면 control plane이 lifecycle 정보를 가장 잘 안다.
반대로 VM 기반 환경에서는 agent heartbeat가 더 중요할 수 있다.

### 4. Health signal은 단일 비트가 아니다

헬스는 `UP` 또는 `DOWN`만으로 표현하면 부족하다.
실전에서는 다음 신호를 섞는다.

- readiness
- liveness
- passive failure rate
- timeout 비율
- queue depth
- warm-up 완료 여부

예를 들어 프로세스는 살아 있지만 DB pool이 고갈되면, liveness만 통과시켜서는 안 된다.

### 5. Zone-aware routing과 failover

가까운 곳으로 보내는 것이 기본이지만, 항상 local 우선만 하면 안 된다.

- 정상 시에는 same zone 우선
- zone 장애 시 cross-zone 허용
- region 장애 시 global reroute

즉, 라우팅 정책은 latency 최적화와 장애 흡수 사이의 균형이다.
이 부분은 [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)와 직접 연결된다.
새 경로 승격 전에는 weighted routing을 shadow/canary 절차와 함께 다루는 편이 안전하다.

### 6. Warm-up, draining, outlier detection

실전에서 가장 많이 놓치는 부분이다.

- 새 인스턴스는 캐시와 JIT warm-up 전까지 바로 100% 트래픽을 받으면 안 된다
- 종료 중인 인스턴스는 새 요청을 받지 않고 connection draining 해야 한다
- 부분 장애 인스턴스는 passive outlier detection으로 잠시 격리해야 한다

이 세 가지가 없으면 배포 때마다 p99가 흔들린다.
stateful endpoint나 shard owner가 바뀌는 상황에서는 relocation 완료 전까지 warm-up weight와 drain 규칙을 더 보수적으로 둬야 한다.

### 7. Control plane이 죽어도 data plane은 살아야 한다

가장 중요한 안정성 원칙:

- 마지막으로 받은 endpoint snapshot을 로컬에 유지한다
- health signal이 불확실하면 보수적으로 endpoint를 줄인다
- registry 장애가 즉시 전체 요청 실패로 번지지 않게 한다

즉, discovery 시스템도 결국 config distribution과 같은 last-known-good 모델이 필요하다.

## 실전 시나리오

### 시나리오 1: 롤링 배포 중 새 인스턴스 투입

문제:

- 새 pod가 뜨자마자 100% 트래픽을 받으면 캐시 미스와 연결 생성 폭주가 난다

해결:

- readiness 통과 후에도 warm-up weight를 낮게 둔다
- connection pool이 안정된 뒤 가중치를 올린다
- 구 인스턴스는 draining 상태에서만 종료한다

### 시나리오 2: 특정 zone 부분 장애

문제:

- zone 하나에서 timeout이 급증하지만 완전 다운은 아니다

해결:

- passive outlier detection으로 unhealthy endpoint를 격리한다
- same zone 우선 정책을 일시 완화한다
- retry는 cross-zone 한 번만 허용해 증폭을 막는다

### 시나리오 3: discovery control plane 장애

문제:

- registry 갱신이 멈췄다

해결:

- data plane은 local snapshot으로 계속 라우팅한다
- stale threshold를 넘는 endpoint만 점진적으로 제거한다
- 운영자는 control plane 복구와 별개로 data plane health를 관찰한다

## 코드로 보기

```pseudo
function pickEndpoint(service):
  endpoints = cache.get(service)
  healthy = filterReady(endpoints)
  localFirst = preferSameZone(healthy)
  return chooseWeighted(localFirst)

function onHealthSignal(endpoint, signal):
  registry.update(endpoint, signal)
  if signal.outlier():
    eject(endpoint, ttl=30s)
```

```java
public Endpoint pick(String serviceName) {
    List<Endpoint> endpoints = snapshotStore.current(serviceName);
    return balancer.choose(endpoints, locality.currentZone());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| DNS 기반 discovery | 단순하다 | health와 빠른 갱신이 약하다 | 초기 시스템 |
| Client-side discovery | 유연하다 | 클라이언트 라이브러리 복잡도 증가 | 내부 마이크로서비스 |
| Sidecar / mesh | 정책 일관성이 높다 | 운영 비용이 크다 | 대규모 플랫폼 |
| Active health check | 빠른 감지가 가능하다 | probe 비용이 든다 | 중요한 서비스 |
| Passive outlier detection | 실제 요청 품질을 반영한다 | false positive 가능성 | p99 안정성이 중요할 때 |

핵심은 service discovery가 주소 해석이 아니라 **장애와 배포, 지역성을 포함한 런타임 트래픽 제어**라는 점이다.

## 꼬리질문

> Q: DNS만으로 service discovery를 끝낼 수 없나요?
> 의도: discovery와 health routing 차이 이해 확인
> 핵심: 빠른 health 반영, locality, draining, outlier detection이 부족한 경우가 많다.

> Q: readiness와 liveness는 왜 분리하나요?
> 의도: health signal 설계 감각 확인
> 핵심: 프로세스 생존과 트래픽 수용 가능성은 다르기 때문이다.

> Q: retry를 많이 하면 더 안전한가요?
> 의도: 장애 증폭 이해 확인
> 핵심: unhealthy endpoint가 많을 때 retry는 오히려 부하를 증폭시킬 수 있다.

> Q: control plane 장애 시 가장 중요한 원칙은?
> 의도: data plane 독립성 이해 확인
> 핵심: 마지막으로 검증된 snapshot으로 계속 동작할 수 있어야 한다.

## 한 줄 정리

Service discovery와 health routing은 서비스 이름을 건강한 endpoint 집합으로 해석하고, 배포와 장애 중에도 안전한 경로로 트래픽을 보내게 하는 런타임 제어 시스템이다.

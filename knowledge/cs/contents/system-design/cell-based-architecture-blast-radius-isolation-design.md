# Cell-Based Architecture / Blast Radius Isolation 설계

> 한 줄 요약: cell-based architecture는 서비스를 여러 개의 독립된 운영 셀로 분할해 장애, noisy neighbor, 배포 실수, 데이터 문제의 blast radius를 제한하는 확장·격리 설계다.

retrieval-anchor-keywords: cell based architecture, blast radius isolation, cell routing, compartmentalization, noisy neighbor isolation, failure containment, tenant pinning, shard cell, regional cell, operational cell, tenant partition strategy

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Multi-tenant SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)
> - [Global Traffic Failover Control Plane 설계](./global-traffic-failover-control-plane-design.md)
> - [Stateful Workload Placement / Failover Control Plane 설계](./stateful-workload-placement-failover-control-plane-design.md)
> - [Shard Rebalancing / Partition Relocation 설계](./shard-rebalancing-partition-relocation-design.md)
> - [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md)
> - [Control Plane / Data Plane Separation 설계](./control-plane-data-plane-separation-design.md)
> - [Tenant Partition Strategy / Reassignment 설계](./tenant-partition-strategy-reassignment-design.md)

## 핵심 개념

시스템이 커질수록 "모두가 하나의 거대한 cluster를 공유"하는 구조는 운영 리스크가 커진다.
cell-based architecture는 이를 다음 방식으로 줄인다.

- 트래픽과 상태를 셀 단위로 나눈다
- 각 셀은 상대적으로 독립된 compute/data plane을 가진다
- control plane은 셀 배정과 정책만 중앙에서 관리한다

즉, 셀은 확장 단위이면서 **장애와 실수의 격리 단위**다.

## 깊이 들어가기

### 1. 왜 셀이 필요한가

대표적인 문제:

- 한 tenant가 과도한 부하를 만들어 전체 cluster를 흔듦
- 데이터 손상이나 잘못된 migration이 전체에 퍼짐
- 배포 실수 하나가 모든 고객에게 영향
- 상태 이동과 maintenance가 너무 큰 범위에 영향을 줌

cell 구조는 평균 효율은 약간 희생해도 blast radius를 줄인다.

### 2. Capacity Estimation

예:

- tenant 10만 개
- 셀 20개
- 셀당 정상 headroom 30%
- 한 셀 장애 시 인접 셀이 일부만 흡수

이때 봐야 할 숫자:

- cell utilization skew
- tenant distribution
- cross-cell failover headroom
- cell-local queue depth
- noisy tenant concentration

cell 구조에서는 전체 평균보다 "최악의 셀 하나"가 더 중요하다.

### 3. Cell assignment

셀 배정 기준은 도메인마다 다르다.

- tenant based
- region based
- shard based
- workload class based
- premium / standard tier based

핵심은 셀 경계를 나중에도 설명 가능해야 한다는 점이다.
무작위 배정만으로는 운영 상 의미 있는 isolation을 얻기 어렵다.

### 4. Shared control plane, isolated data plane

보통 셀 구조는 다음처럼 간다.

```text
Global Control Plane
  -> Cell Directory / Assignment
  -> Per-Cell Data Plane
      -> Compute
      -> Queue
      -> Cache
      -> Stateful Store
```

모든 것을 완전히 셀별로 분리하면 비용이 너무 크다.
그래서 보통은 control plane은 공유하고, 데이터 처리 경로는 셀 단위로 나누는 경우가 많다.

### 5. Routing and tenant pinning

cell 구조가 의미 있으려면 요청이 올바른 셀로 가야 한다.

필요한 것:

- tenant-to-cell directory
- sticky routing
- cell-local fallback
- migration during reassignment

cell 이동은 결국 shard relocation과 비슷한 문제를 일으키므로, assignment 변경 절차도 중요하다.

### 6. Noisy neighbor와 resource isolation

셀은 단순한 라벨이 아니라 자원 경계가 되어야 한다.

- per-cell worker pool
- per-cell queue
- per-cell rate limit
- cell-local cache

그렇지 않으면 control plane만 셀을 알고, 실제로는 모두가 같은 병목을 계속 공유하게 된다.

### 7. Operations and debugging

좋은 cell architecture는 운영 질문에 답하기 쉬워야 한다.

- 이 tenant는 어느 cell에 있는가
- 이 장애는 몇 개 cell에 영향을 주는가
- 셀 이동 중인 tenant는 누구인가
- 특정 cell만 degraded mode인가

즉, 셀은 아키텍처 개념이면서 운영 대시보드의 기본 차원이 된다.

## 실전 시나리오

### 시나리오 1: noisy enterprise tenant

문제:

- 한 대형 tenant가 대량 배치로 전체 search cluster를 흔든다

해결:

- 해당 tenant를 별도 high-capacity cell로 옮긴다
- queue, cache, worker pool을 cell-local로 격리한다
- 나머지 tenant는 기존 cell에서 안정성 유지

### 시나리오 2: risky migration rollout

문제:

- 새 read model migration을 전 고객에 바로 적용하기 위험하다

해결:

- 특정 cell에만 먼저 rollout한다
- dual-read와 canary analysis를 cell 차원으로 본다
- 안정화 후 다른 cell로 확산한다

### 시나리오 3: regional cell failure

문제:

- 한 cell이 장애지만 전체 region을 failover할 정도는 아니다

해결:

- 그 cell만 degraded mode로 전환한다
- global control plane은 새 tenant를 다른 cell로 배정한다
- 필요하면 일부 tenant만 cell reassignment한다

## 코드로 보기

```pseudo
function routeRequest(req):
  cell = cellDirectory.lookup(req.tenantId)
  return router.send(cell.endpoint, req)

function rebalanceCells():
  for cell in cells:
    if cell.overloaded():
      tenants = planner.selectMovableTenants(cell)
      startReassignment(tenants)
```

```java
public CellId assign(TenantId tenantId) {
    return assignmentPolicy.choose(tenantId, cellInventory.current());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Single large cluster | 효율이 좋다 | blast radius가 크다 | 초기 시스템 |
| Cell-based split | 격리가 좋다 | 운영과 capacity planning이 복잡하다 | 대형 multi-tenant 플랫폼 |
| Dedicated tenant silo | 격리가 매우 강하다 | 비용이 높다 | 아주 큰 고객, 규제 요구 |
| Shared control + per-cell data | 현실적 균형 | control plane이 중요해진다 | 대부분의 cell architectures |

핵심은 cell-based architecture가 단순 샤딩이 아니라 **배포, 장애, noisy neighbor, migration의 영향 범위를 줄이기 위한 운영 격리 구조**라는 점이다.

## 꼬리질문

> Q: cell architecture와 shard는 같은 개념인가요?
> 의도: 배치 단위와 운영 격리 단위 구분 확인
> 핵심: 겹칠 수는 있지만, shard는 데이터 분산 단위이고 cell은 보통 더 넓은 운영·격리 단위다.

> Q: cell을 나누면 무조건 더 안전한가요?
> 의도: isolation vs efficiency 균형 이해 확인
> 핵심: 아니다. control plane, routing, reassignment가 약하면 오히려 복잡도만 늘 수 있다.

> Q: noisy neighbor 문제를 왜 cell로 푸나요?
> 의도: blast radius 사고방식 확인
> 핵심: 전체 공유 cluster보다 일부 tenant나 workload만 별도 격리 단위로 두는 편이 전체 안정성에 유리하기 때문이다.

> Q: cell 이동은 왜 어려운가요?
> 의도: assignment 변경의 상태성 이해 확인
> 핵심: routing, cache, queue, state ownership이 함께 움직여야 하기 때문이다.

## 한 줄 정리

Cell-based architecture는 서비스를 운영 셀 단위로 분할해 장애와 noisy neighbor, 위험한 배포의 영향을 제한하는 blast-radius 중심 확장·격리 설계다.

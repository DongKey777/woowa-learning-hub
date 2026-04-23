# Tenant Partition Strategy / Reassignment 설계

> 한 줄 요약: tenant partition strategy와 reassignment 설계는 tenant를 어떤 기준으로 shard, cell, cluster에 배치하고, hot tenant나 premium tenant를 언제 어떻게 다른 격리 단위로 이동시킬지 정하는 multi-tenant 운영 설계다.

retrieval-anchor-keywords: tenant partition strategy, tenant reassignment, tenant sharding, tenant mobility, hot tenant isolation, dedicated tenant cell, tenant promotion, partition directory, noisy neighbor mitigation, tenant placement, tenant scoped recovery

**난이도: 🔴 Advanced**

> 관련 문서:
> - [멀티 테넌트 SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)
> - [Cell-Based Architecture / Blast Radius Isolation 설계](./cell-based-architecture-blast-radius-isolation-design.md)
> - [Shard Rebalancing / Partition Relocation 설계](./shard-rebalancing-partition-relocation-design.md)
> - [Stateful Workload Placement / Failover Control Plane 설계](./stateful-workload-placement-failover-control-plane-design.md)
> - [Global Traffic Failover Control Plane 설계](./global-traffic-failover-control-plane-design.md)
> - [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md)
> - [Tenant-Scoped Config Incident Recovery 설계](./tenant-scoped-config-incident-recovery-design.md)
> - [Tenant Split-Out with Service Identity Rollout 설계](./tenant-split-out-service-identity-rollout-design.md)

## 핵심 개념

멀티 테넌트 시스템에서 "tenant를 어디에 둘 것인가"는 단순 해시 문제가 아니다.
실전에서는 다음을 같이 결정해야 한다.

- 어떤 tenant를 같은 partition에 둘 것인가
- noisy tenant를 언제 분리할 것인가
- premium tenant는 전용 cell이 필요한가
- region / residency 요구는 어떻게 반영할 것인가
- tenant 이동 중 읽기/쓰기 정합성은 어떻게 지킬 것인가

즉, tenant partition strategy는 key 분산이 아니라 **고객 단위 격리, 수익성, blast radius를 함께 고려하는 운영 배치 전략**이다.

## 깊이 들어가기

### 1. 왜 tenant-aware partitioning이 필요한가

단순 key hash만 쓰면 평균 분산은 좋아질 수 있다.
하지만 실전에서는 tenant가 운영의 기본 단위가 된다.

- SLA와 요금제가 tenant마다 다름
- noisy neighbor도 tenant 단위로 보임
- migration / support / incident도 tenant 단위로 진행됨
- residency 규제도 tenant 계약과 연결됨

그래서 partition 전략은 종종 `entity_id`보다 `tenant_id`를 먼저 고려해야 한다.

### 2. Capacity Estimation

예:

- tenant 20만 개
- 상위 1% tenant가 전체 부하의 60%
- premium tenant 200개
- 월별 tenant growth 5%

이때 봐야 할 숫자:

- tenant size skew
- tenant growth rate
- top-tenant concentration
- reassignment frequency
- cross-partition move cost

평균 tenant보다 상위 tail tenant가 전략을 바꾼다.

### 3. 대표 전략

보통 조합은 아래와 같다.

- shared pool for long tail
- weighted partitioning for mid-size tenants
- dedicated cell / cluster for top tenants
- residency-specific partitions for regulated tenants

즉, "모든 tenant에 하나의 규칙"보다 **계층형 partition strategy**가 현실적이다.

### 4. Tenant directory와 placement metadata

tenant 이동과 라우팅을 안정적으로 하려면 directory가 필요하다.

- tenant -> partition
- tenant -> cell
- tenant -> region
- migration state
- placement class

이 metadata가 없으면 요청 라우팅과 운영 설명이 모두 어려워진다.

### 5. Reassignment trigger

tenant를 이동해야 하는 대표 이유:

- hot tenant
- capacity skew
- premium 계약 변경
- residency 요구
- risky migration cell 분리

중요한 것은 "언제 이동할지"를 수동 감으로만 결정하지 않는 것이다.
보통은 size, QPS, storage, cost, SLA breach를 기준으로 trigger를 둔다.

### 6. Tenant move safety

tenant reassignment는 shard relocation보다 더 tricky할 수 있다.
이유:

- 요청 라우팅이 tenant 중심으로 이뤄짐
- cache, queue, state store가 함께 이동해야 할 수 있음
- 일부 tenant는 외부 integration key까지 가짐

보통 절차:

1. tenant directory에 pending move 상태를 둔다
2. state snapshot + delta catch-up
3. read verification
4. write freeze or fenced cutover
5. old partition drain

### 7. Economic and operational balance

모든 큰 tenant를 전용 cell로 두면 안정성은 좋지만 비용이 커진다.
반대로 전부 shared면 효율은 좋지만 noisy neighbor와 support 비용이 증가한다.

즉, tenant partitioning은 기술 문제이면서 **수익성 최적화 문제**이기도 하다.

## 실전 시나리오

### 시나리오 1: hot enterprise tenant 분리

문제:

- 한 대형 tenant가 전체 shared cluster의 p99를 흔든다

해결:

- dedicated cell class로 승격한다
- tenant directory를 갱신한다
- cache, queue, search projection을 함께 재배치한다
- dedicated cell로 들어오는 workload identity allowlist와 post-cutover auth drift도 같이 본다

route만 바꾸고 service identity를 old shared principal에 묶어 두면 cell 승격 뒤에도 background path가 조용히 실패할 수 있다.
tenant 이동과 trust 이동이 같이 붙는 운영 절차는 [Tenant Split-Out with Service Identity Rollout 설계](./tenant-split-out-service-identity-rollout-design.md)에서 더 좁게 이어서 볼 수 있다.

### 시나리오 2: residency 요구가 생긴 tenant 이동

문제:

- 기존 APAC shared pool의 tenant가 EU-only 저장을 요구한다

해결:

- region-specific partition으로 reassignment한다
- cross-region move 동안 read/write cutover 경계를 명시한다
- global routing과 state placement를 함께 조정한다

### 시나리오 3: risky migration rollout

문제:

- 새 read model을 일부 고객에게만 적용하고 싶다

해결:

- 특정 tenant class 또는 cell에만 rollout한다
- dual-read verification과 canary를 tenant slice 단위로 본다
- 안정화 후 다른 tenant class로 확장한다

## 코드로 보기

```pseudo
function locateTenant(tenantId):
  assignment = tenantDirectory.lookup(tenantId)
  return assignment.partition

function maybePromoteTenant(tenant):
  if tenant.qps > hotTenantThreshold or tenant.plan == "ENTERPRISE":
    target = planner.dedicatedCell(tenant)
    startReassignment(tenant, target)
```

```java
public PartitionAssignment assignmentFor(TenantId tenantId) {
    return tenantDirectory.current(tenantId);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Pure hash partition | 단순하다 | tenant 의미가 약하다 | 작은 homogeneous SaaS |
| Tenant-aware shared partition | 운영성이 좋다 | skew 관리가 필요하다 | 대부분의 multi-tenant SaaS |
| Dedicated cell for top tenants | 격리가 강하다 | 비용이 높다 | 상위 enterprise, 규제 tenant |
| Dynamic reassignment | 유연하다 | 이동 절차가 복잡하다 | tenant skew가 큰 플랫폼 |

핵심은 tenant partition strategy가 샤딩 공식이 아니라 **tenant 단위 격리, 이동성, 수익성, residency를 함께 고려하는 multi-tenant 운영 설계**라는 점이다.

## 꼬리질문

> Q: tenant마다 dedicated DB를 주면 가장 안전하지 않나요?
> 의도: isolation vs cost 균형 이해 확인
> 핵심: 안전성은 높지만 long-tail tenant까지 그렇게 하면 비용과 운영 복잡도가 너무 커질 수 있다.

> Q: tenant-aware partitioning이 단순 hash보다 나은 이유는?
> 의도: 운영 단위 사고 확인
> 핵심: support, SLA, noisy neighbor, residency, migration이 tenant 단위로 일어나기 때문이다.

> Q: tenant move가 왜 어려운가요?
> 의도: state + routing 결합 이해 확인
> 핵심: 데이터만이 아니라 routing, cache, queue, 외부 integration state까지 함께 움직여야 할 수 있기 때문이다.

> Q: hot tenant를 언제 dedicated cell로 승격하나요?
> 의도: trigger 설계 감각 확인
> 핵심: QPS, storage, SLA breach, support burden, 계약 조건을 조합해 threshold를 정하는 편이 현실적이다.

## 한 줄 정리

Tenant partition strategy / reassignment 설계는 tenant를 어떤 격리 단위에 배치하고 언제 다른 shard나 cell로 이동시킬지 정해, multi-tenant 플랫폼의 noisy neighbor와 blast radius를 관리하는 운영 설계다.

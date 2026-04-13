# Entitlement / Quota 설계

> 한 줄 요약: entitlement와 quota는 사용자, tenant, plan별로 무엇을 허용할지와 얼마나 사용할지를 제어하는 정책 집행 시스템이다.

retrieval-anchor-keywords: entitlement, quota, plan limits, usage metering, feature flags, soft limit, hard limit, tenant limits, credit budget, policy enforcement, usage accounting

**난이도: 🔴 Advanced**

> 관련 문서:
> - [멀티 테넌트 SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)
> - [Rate Limiter 설계](./rate-limiter-design.md)
> - [분산 캐시 설계](./distributed-cache-design.md)
> - [Distributed Scheduler 설계](./distributed-scheduler-design.md)
> - [Webhook Delivery Platform 설계](./webhook-delivery-platform-design.md)
> - [Job Queue 설계](./job-queue-design.md)

## 핵심 개념

Entitlement는 "무엇을 쓸 수 있는가"이고, quota는 "얼마나 쓸 수 있는가"다.  
둘을 섞으면 정책이 망가진다.

- entitlement: 기능 접근 권한
- quota: 사용량 상한
- metering: 사용량 측정
- enforcement: 실제 차단

즉, 이 설계는 권한 시스템, 과금 시스템, 보호 장치를 동시에 만족해야 한다.

## 깊이 들어가기

### 1. 정책 모델을 분리한다

보통 아래 세 층으로 나눠 생각한다.

1. plan entitlement
2. usage quota
3. runtime enforcement

예:

- free plan: SSO 없음, API 1,000 req/day
- pro plan: SSO 있음, API 100,000 req/day
- enterprise: custom limits, dedicated support

### 2. Capacity Estimation

정책 시스템은 QPS보다 lookup 빈도가 높다.

예:

- 요청 50,000 req/sec
- 요청마다 3개의 policy check
- cache hit 99%

그래도 cache miss가 몰리면 policy store가 병목이 된다.  
따라서 읽기 path와 쓰기 path를 분리해야 한다.

봐야 할 숫자:

- entitlement lookup QPS
- quota update QPS
- metering lag
- cache invalidation rate
- policy evaluation latency

### 3. 데이터 모델

핵심 엔티티:

- plan
- entitlement
- usage_meter
- quota_bucket
- policy_override
- billing_period

정책은 대개 테넌트와 기간에 묶인다.

### 4. hard limit과 soft limit

제어 방식은 두 가지다.

- hard limit: 즉시 거부
- soft limit: 경고 후 허용, 또는 degraded mode

실무에서는 중요도에 따라 다르게 둔다.

- 보안/비용 방어: hard limit
- 리포트/보조 기능: soft limit

### 5. Metering과 enforcement를 분리한다

사용량 측정은 종종 지연된다.

- 실시간 카운트
- 비동기 집계
- 일별 정산
- 월별 청구

그래서 "현재 사용량"과 "최종 청구 사용량"이 다를 수 있다.  
이 차이를 정책에 명시해야 한다.

### 6. 캐시와 일관성

Entitlement는 읽기가 많다.

- plan config cache
- quota snapshot cache
- per-tenant usage cache

하지만 캐시만 믿으면 초과 사용을 늦게 막는다.  
따라서 critical path는 캐시 + 원장 + fallback의 조합이 필요하다.

### 7. 정책 변경과 versioning

정책은 자주 바뀐다.

- 플랜 업그레이드
- 기능 공개/비공개
- quota 증감
- trial 정책

필요한 것:

- effective_from
- policy version
- audit trail
- rollback path

이 부분은 [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: API quota 초과

문제:

- 한 tenant가 API를 과도하게 사용한다

해결:

- soft warning 이후 hard limit 적용
- quota snapshot을 캐시하고 원장과 동기화한다

### 시나리오 2: 플랜 업그레이드 직후

문제:

- 사용자가 결제 후 바로 더 높은 기능을 써야 한다

해결:

- entitlement cache를 invalidate한다
- billing event를 기준으로 policy version을 전환한다

### 시나리오 3: 월말 메터링 정산

문제:

- usage 집계와 실제 청구가 다를 수 있다

해결:

- daily metering job을 돌린다
- audit log와 usage ledger를 대사한다

## 코드로 보기

```pseudo
function authorize(tenant, action):
  policy = policyCache.get(tenant.plan)
  if !policy.allows(action):
    return DENY
  quota = usageCache.get(tenant.id)
  if quota.exceeded(action):
    return DENY
  return ALLOW
```

```java
public Decision decide(TenantId tenantId, Action action) {
    Plan plan = entitlementRepository.findPlan(tenantId);
    if (!plan.allows(action)) return Decision.deny();
    return quotaService.canConsume(tenantId, action) ? Decision.allow() : Decision.deny();
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Hard limit | 비용 방어가 확실하다 | 사용자 경험이 거칠다 | 보안/과금 경로 |
| Soft limit | 경험이 부드럽다 | 비용이 새기 쉽다 | 보조 기능 |
| Real-time metering | 정확하다 | 비용이 높다 | 고가 서비스 |
| Batch metering | 단순하다 | 지연이 있다 | 청구/리포트 |
| Cache-first policy check | 빠르다 | stale risk | high-QPS service |

핵심은 entitlement와 quota를 같은 "권한"으로 뭉개지 않고, **정책, 측정, 집행을 각각 설계**하는 것이다.

## 꼬리질문

> Q: entitlement와 quota는 왜 분리해야 하나요?
> 의도: 기능 접근과 사용량 제어의 차이 이해 확인
> 핵심: 하나는 허용 여부, 다른 하나는 사용량 상한이다.

> Q: usage는 실시간으로 꼭 맞아야 하나요?
> 의도: metering과 enforcement의 차이 이해 확인
> 핵심: 보통은 약간의 지연을 허용하지만 critical limit은 더 엄격해야 한다.

> Q: 캐시를 쓰면 quota 초과가 생기지 않나요?
> 의도: stale data risk 이해 확인
> 핵심: 그래서 cache, snapshot, fallback을 같이 둔다.

> Q: 정책 변경을 안전하게 하려면 무엇이 필요하나요?
> 의도: versioning과 audit 이해 확인
> 핵심: policy version, effective time, audit trail이 필요하다.

## 한 줄 정리

Entitlement / quota 설계는 기능 허용과 사용량 제한을 정책, metering, enforcement로 분리해 안전하게 집행하는 시스템이다.


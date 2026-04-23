# 멀티 테넌트 SaaS 격리 설계

> 한 줄 요약: 여러 고객이 같은 플랫폼을 쓰더라도, 한 tenant의 폭주와 실수가 다른 tenant의 성능, 보안, 데이터 경계를 무너뜨리지 않게 만드는 설계다.

**난이도: 🔴 Advanced**

> related-docs:
> - [Rate Limiter 설계](./rate-limiter-design.md)
> - [분산 캐시 설계](./distributed-cache-design.md)
> - [정규화와 반정규화 트레이드오프](../database/normalization-denormalization-tradeoffs.md)
> - [Partition Pruning and Hot/Cold Data](../database/partition-pruning-hot-cold-data.md)
> - [인증과 인가의 차이](../security/authentication-vs-authorization.md)
> - [Modular Monolith Boundary Enforcement](../software-engineering/modular-monolith-boundary-enforcement.md)
> - [Cell-Based Architecture / Blast Radius Isolation 설계](./cell-based-architecture-blast-radius-isolation-design.md)
> - [Tenant Partition Strategy / Reassignment 설계](./tenant-partition-strategy-reassignment-design.md)

> retrieval-anchor-keywords: multi-tenant, noisy neighbor, tenant isolation, shared schema, separate schema, separate database, rate limit, RBAC, data residency, cell architecture, blast radius, tenant partition strategy

---

## 핵심 개념

멀티 테넌트 SaaS에서 진짜 문제는 "같은 코드로 여러 고객을 서비스한다"가 아니다.  
진짜 문제는 **한 tenant의 부하, 권한, 데이터, 장애가 다른 tenant로 새지 않게 만드는 것**이다.

이 설계는 최소한 다음 5개 층을 함께 본다.

- 앱 계층: tenant 컨텍스트를 얼마나 강하게 강제할 것인가
- DB 계층: shared schema, separate schema, separate database 중 무엇을 택할 것인가
- cache 계층: key 충돌과 hot key를 어떻게 막을 것인가
- queue 계층: tenant별 backlog와 우선순위를 어떻게 나눌 것인가
- auth 계층: 인증은 공통화하되 인가와 RBAC는 tenant 경계 안에서 어떻게 유지할 것인가

핵심 질문은 단순하다.

- 같은 테이블을 공유해도 안전한가
- 캐시와 큐가 한 tenant 때문에 포화되지 않는가
- 관리자 권한이 tenant 경계를 넘지 않는가
- 데이터 위치와 보관 정책이 지역 규제를 만족하는가

이 문서는 [Rate Limiter 설계](./rate-limiter-design.md)에서 다룬 "누구를 얼마나 제한할 것인가"를 tenant 관점으로 확장하고, [분산 캐시 설계](./distributed-cache-design.md)의 key 분리 원칙을 tenant isolation으로 이어 읽는 문서다.

---

## 깊이 들어가기

### 1. 격리의 목표를 먼저 분리해야 한다

멀티 테넌트 격리는 하나의 문제가 아니다. 보통 아래 다섯 가지를 분리해서 본다.

| 격리 대상 | 질문 | 실패하면 생기는 일 |
|------|------|------|
| 성능 | 한 tenant가 다른 tenant를 느리게 만드는가 | noisy neighbor |
| 보안 | 다른 tenant 데이터에 접근 가능한가 | 데이터 유출 |
| 비용 | 특정 tenant가 자원을 과도하게 쓰는가 | 수익성 악화 |
| 운영 | 장애나 배포가 tenant 단위로 격리되는가 | 전면 장애 |
| 규제 | 데이터가 특정 지역 밖으로 나가지 않는가 | data residency 위반 |

이 다섯 개는 같은 방식으로 해결되지 않는다.  
예를 들어 DB를 separate database로 쪼개면 보안과 운영 격리는 좋아지지만, 비용과 운영 복잡도는 올라간다.

### 2. 아키텍처 층별 격리 포인트

```text
Client
  -> CDN / WAF
  -> API Gateway
  -> App Service
      -> Tenant Context Resolver
      -> AuthN / AuthZ / RBAC
      -> Rate Limit
      -> Cache
      -> Queue
      -> Database
```

이 그림에서 중요한 것은 "tenant_id를 어디까지 전달하고, 어디서 강제하느냐"다.

- gateway에서 IP/tenant 단위의 1차 차단을 한다
- app에서 tenant context를 만들고 요청마다 검증한다
- cache, queue, DB key와 row scope에 tenant prefix를 붙인다
- authz는 role만 보지 말고 tenant membership과 resource ownership을 함께 본다

### 3. DB 격리 모델의 선택

#### Shared schema

모든 tenant가 같은 테이블을 공유하고, `tenant_id` 컬럼으로 구분하는 방식이다.

장점:

- 운영이 가장 단순하다
- tenant 수가 많아도 스키마 수가 폭발하지 않는다
- 분석 쿼리와 배치 처리가 쉽다

단점:

- 쿼리 실수로 tenant 필터를 빼먹기 쉽다
- noisy neighbor가 가장 잘 드러난다
- data residency를 tenant별로 강하게 나누기 어렵다

#### Separate schema

tenant별로 같은 구조의 schema를 분리하는 방식이다.

장점:

- logical isolation이 더 강하다
- tenant별 migration과 백업이 비교적 쉽다
- 일부 규제 대응이 수월하다

단점:

- schema 수가 많아지면 운영이 번거롭다
- cross-tenant 분석이 어려워진다
- 애플리케이션이 schema routing을 알아야 한다

#### Separate database

tenant별로 DB 인스턴스 또는 클러스터를 분리하는 방식이다.

장점:

- 가장 강한 격리를 제공한다
- 대형 tenant의 noisy neighbor를 가장 잘 막는다
- data residency, encryption key 분리, 백업 분리가 쉽다

단점:

- 비용이 가장 높다
- 운영 자동화가 필수다
- tenant 수가 많으면 관리 복잡도가 급상승한다

실무에서는 보통 세 가지를 혼합한다.

- small tenant: shared schema
- medium tenant: separate schema
- enterprise tenant: separate database

이건 [정규화와 반정규화 트레이드오프](../database/normalization-denormalization-tradeoffs.md)처럼 "무조건 하나"를 고르는 문제가 아니라, tenant 크기와 위험도에 따라 층을 나누는 문제다.

### 4. Cache 격리는 key 설계에서 시작한다

캐시는 가장 빨리 새는 층이다. tenant prefix가 없으면 서로 다른 고객의 데이터를 같은 key로 덮어쓸 수 있다.

```text
bad:
profile:123

good:
tenant:acme:profile:123
tenant:beta:profile:123
```

tenant-aware key는 반드시 일관된 규칙을 가져야 한다.

```text
tenant:{tenantId}:user:{userId}:profile
tenant:{tenantId}:plan:{planId}:limits
tenant:{tenantId}:permission:{principalId}
tenant:{tenantId}:cache:v2:report:{reportId}
```

주의할 점:

- `tenantId`는 사람이 읽는 slug보다 불변 식별자가 낫다
- cache stampede는 tenant 단위로도 터질 수 있다
- hot tenant의 cache miss가 DB 전체를 때리지 않게 해야 한다

그래서 cache는 보통 다음처럼 계층화한다.

```text
local cache
  -> distributed cache
      -> database
```

### 5. Queue 격리는 backlog와 우선순위로 본다

큐는 "비동기니까 안전하다"가 아니다. tenant별 작업이 같은 큐에 쌓이면 한 고객의 대량 작업이 다른 고객의 SLA를 망친다.

문제 패턴:

- 한 tenant가 수만 건 배치를 넣는다
- 큐 소비자가 같은 pool을 공유한다
- 작은 tenant의 알림이나 웹훅이 계속 밀린다

대응책:

- tenant별 queue 또는 partition을 둔다
- worker concurrency를 tenant policy로 제한한다
- large tenant는 별도 work class로 분리한다
- dead letter queue도 tenant context를 유지한다

```text
producer
  -> queue[tenant:acme]
  -> queue[tenant:beta]
  -> queue[shared-low-priority]
```

여기서 핵심은 "완전 분리"보다 "공정한 스케줄링"이다.  
모든 tenant를 별도 큐로 분리하면 운영이 쉬워 보이지만, 작은 tenant가 많을수록 오히려 비효율이 생긴다.

### 6. Auth는 인증보다 인가 설계가 더 중요하다

멀티 테넌트에서 로그인 성공은 끝이 아니다.  
진짜 검증은 "이 사용자가 어느 tenant의 어떤 역할로, 무엇을 할 수 있는가"다.

- 인증: 이 사용자가 누구인가
- 인가: 이 사용자가 이 tenant에서 이 자원을 할 수 있는가
- RBAC: tenant 내부에서 어떤 role을 가졌는가
- cross-tenant admin: 플랫폼 운영자도 모든 데이터에 접근 가능한가

```text
user authenticated
  -> resolve tenant membership
  -> resolve role / permission
  -> check resource ownership
  -> enforce tenant scope
```

흔한 실수는 `ROLE_ADMIN` 하나로 모든 tenant를 뚫는 것이다.  
플랫폼 관리자와 tenant 관리자는 다른 권한 모델이어야 한다.

이 부분은 [인증과 인가의 차이](../security/authentication-vs-authorization.md)에서 설명한 경계를 tenant 모델에 그대로 적용하면 이해가 쉽다.

### 7. Data residency는 설계 초기에 넣어야 한다

데이터가 특정 국가나 리전 밖으로 나가면 안 되는 tenant가 있다. 이 요구는 나중에 붙이면 거의 항상 비싸진다.

고려할 것:

- tenant별 region pinning
- backup location
- cache locality
- log shipping
- async job 실행 지역

예를 들어 EU tenant는 EU DB, EU cache, EU queue를 쓰고, 운영 메타데이터만 글로벌 서비스가 들고 있을 수 있다.  
이때는 "어떤 데이터가 cross-region으로 이동하는가"를 문서화해야 한다.

### 8. 모듈 경계도 tenant 경계처럼 강제해야 한다

tenant isolation은 아키텍처 관점에서 모듈 경계와 닮았다.  
경계를 코드로 강제하지 않으면 결국 편의상 우회 경로가 생긴다.

즉:

- tenant context를 thread-local이나 request context에만 숨기지 말고 명시적으로 전달한다
- repository와 query service는 tenant predicate를 기본으로 강제한다
- internal admin endpoint는 일반 tenant API와 분리한다

이 관점은 [Modular Monolith Boundary Enforcement](../software-engineering/modular-monolith-boundary-enforcement.md)와 같은 원리다. 경계는 문서가 아니라 enforcement로 지켜야 한다.

---

## 실전 시나리오

### 시나리오 1: shared schema에서 tenant 필터를 빠뜨림

문제:

- 조회 쿼리에 `tenant_id` 조건이 빠졌다
- 테스트는 단일 tenant만 써서 통과했다
- 운영에서 다른 tenant의 데이터가 섞여 보였다

원인:

- repository 레벨에서 tenant scope를 강제하지 않았다
- query builder가 안전장치 없이 동작했다

대응:

- 모든 쿼리 진입점에 tenant scope를 주입한다
- integration test에 multi-tenant fixture를 넣는다
- SQL lint나 repository wrapper로 tenant predicate를 강제한다

### 시나리오 2: noisy neighbor가 cache와 DB를 동시에 압박

문제:

- 대형 tenant가 리포트 생성을 반복한다
- cache miss가 증가하고 DB read가 폭발한다
- 작은 tenant의 p99가 함께 나빠진다

대응:

- tenant별 rate limit을 둔다
- heavy job은 별도 queue와 worker pool로 보낸다
- report 결과를 tenant-aware cache key로 저장한다
- 필요하면 enterprise tenant만 separate schema나 separate database로 올린다

이 시나리오는 [Rate Limiter 설계](./rate-limiter-design.md)와 [분산 캐시 설계](./distributed-cache-design.md)를 같이 써야 해결된다.

### 시나리오 3: data residency 때문에 글로벌 캐시가 독이 됨

문제:

- 사용자 데이터는 EU에 저장해야 한다
- 그런데 캐시가 글로벌로 공유된다
- 로그와 배치가 다른 리전에서 읽는다

대응:

- region-aware cache cluster를 둔다
- async job은 tenant region에서만 실행한다
- backup과 export 경로를 별도로 관리한다

### 시나리오 4: platform admin이 너무 강한 권한을 가짐

문제:

- 운영자가 모든 tenant 데이터를 볼 수 있다
- 감사 로그가 부족하다
- 권한 위임 경로가 없어서 사고 추적이 어렵다

대응:

- platform admin과 tenant admin을 분리한다
- RBAC에 scope를 붙인다
- sensitive action은 audit log를 남긴다
- impersonation은 승인된 절차로만 허용한다

---

## 코드로 보기

### 1. tenant scope를 강제하는 서비스 예시

```java
public class OrderService {
    private final OrderRepository orderRepository;

    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public OrderSummary getOrderSummary(TenantId tenantId, long orderId) {
        return orderRepository.findByTenantIdAndOrderId(tenantId.value(), orderId)
            .orElseThrow(() -> new IllegalArgumentException("order not found"));
    }
}
```

tenant scope를 메서드 시그니처에서 드러내면, 실수로 scope를 놓칠 확률이 줄어든다.

### 2. tenant-aware cache key와 rate limit key

```java
public final class TenantKeys {
    public static String profile(long tenantId, long userId) {
        return "tenant:" + tenantId + ":user:" + userId + ":profile";
    }

    public static String rateLimit(long tenantId, long principalId, String route, String window) {
        return "rl:tenant:" + tenantId + ":principal:" + principalId + ":" + route + ":" + window;
    }

    public static String queuePartition(long tenantId, String jobType) {
        return "queue:tenant:" + tenantId + ":" + jobType;
    }
}
```

### 3. RBAC와 tenant membership 체크

```java
public void updatePlan(UserPrincipal principal, TenantId tenantId) {
    if (!principal.isMemberOf(tenantId)) {
        throw new AccessDeniedException("tenant scope mismatch");
    }

    if (!principal.hasRole(tenantId, "TENANT_ADMIN")) {
        throw new AccessDeniedException("missing role");
    }

    planService.update(tenantId, principal.userId());
}
```

이 코드는 인증만으로는 부족하고, tenant membership과 role scope를 같이 확인해야 한다는 점을 보여준다.

### 4. shared schema 테이블 예시

```sql
CREATE TABLE tenant_orders (
  tenant_id BIGINT NOT NULL,
  order_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  status VARCHAR(32) NOT NULL,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (tenant_id, order_id),
  INDEX idx_tenant_orders_user_created (tenant_id, user_id, created_at)
);
```

이 테이블은 `tenant_id`가 PK와 인덱스의 앞부분에 있어야 tenant-local lookup과 pruning이 잘 된다.  
이 관점은 [Partition Pruning and Hot/Cold Data](../database/partition-pruning-hot-cold-data.md)와도 맞닿아 있다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| shared schema | 운영이 단순하고 tenant 수가 많아도 감당하기 쉽다 | tenant 필터 누락과 noisy neighbor 위험이 크다 | 소규모/중소 tenant가 많을 때 |
| separate schema | 논리적 격리가 강하고 tenant별 관리가 쉬워진다 | 스키마와 마이그레이션 운영이 복잡해진다 | 중형 tenant, 일부 규제 대응 |
| separate database | 가장 강한 격리와 data residency 대응이 가능하다 | 비용과 운영 자동화 부담이 크다 | enterprise tenant, 고위험 데이터 |
| shared cache | 구현이 쉽고 자원 효율이 좋다 | key 충돌과 hot key 위험이 있다 | tenant key가 엄격히 분리될 때 |
| tenant-partitioned queue | 공정성과 backlog 통제가 좋다 | worker/partition 설계가 복잡하다 | 비동기 작업이 SLA에 중요할 때 |
| global RBAC | 구현이 단순하다 | tenant scope를 뚫기 쉽다 | tenant가 없는 플랫폼 |
| scoped RBAC | 권한 경계가 명확하다 | 정책 설계와 테스트가 더 필요하다 | 멀티 테넌트 SaaS 대부분 |

핵심 기준은 "가장 안전한 구조"가 아니라 **어떤 실패를 가장 싸게 막을 수 있는가**다.

---

## 꼬리질문

> Q: shared schema에서 tenant_id만 넣으면 충분한가요?
> 의도: 단순 구분과 실제 격리의 차이를 아는지 확인
> 핵심: tenant_id는 시작점일 뿐이고, 쿼리 강제, 캐시 key, queue, authz까지 같이 묶어야 한다

> Q: separate schema와 separate database는 언제 나누나요?
> 의도: 격리 수준과 운영 비용의 판단 기준 확인
> 핵심: 규제, noisy neighbor 위험, tenant 규모, 백업/복구 요구를 같이 본다

> Q: cache key에 tenant prefix를 붙이면 끝인가요?
> 의도: 캐시 격리의 깊이를 확인
> 핵심: prefix는 기본이고, TTL, eviction, stampede, region locality까지 봐야 한다

> Q: RBAC만으로 tenant 경계를 지킬 수 있나요?
> 의도: 인증/인가와 resource scope 이해 확인
> 핵심: role은 권한의 한 축이고, tenant membership과 resource ownership 검사가 별도로 필요하다

> Q: data residency가 있으면 아키텍처가 왜 더 어려워지나요?
> 의도: 규제가 설계에 미치는 영향 이해 확인
> 핵심: storage, cache, queue, backup, logs, async job까지 지역 제약을 따라야 하기 때문이다

---

## 한 줄 정리

멀티 테넌트 SaaS의 핵심은 tenant_id를 저장하는 것이 아니라, 앱과 DB, cache, queue, auth 전층에서 tenant 경계를 강제로 유지해 noisy neighbor와 데이터 유출을 막는 것이다.

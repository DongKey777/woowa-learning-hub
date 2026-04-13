# Tenant-aware Search Architecture 설계

> 한 줄 요약: tenant-aware search architecture는 테넌트별 데이터 경계, 권한 필터, 색인 분리, 랭킹 정책을 검색 계층에 반영하는 설계다.

retrieval-anchor-keywords: tenant-aware search, search isolation, permission filter, per-tenant index, ACL filtering, query routing, multi-tenant search, row-level security, ranking override, data residency

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Search 시스템 설계](./search-system-design.md)
> - [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)
> - [멀티 테넌트 SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)
> - [Consistent Hashing / Hot Key 전략](./consistent-hashing-hot-key-strategies.md)
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)

## 핵심 개념

테넌트 인식 검색은 단순한 `tenant_id` 필터가 아니다.  
실전에서는 아래를 함께 보아야 한다.

- tenant별 데이터 격리
- document ACL
- per-tenant index or shared index
- ranking override
- data residency
- query routing

즉, 검색은 조회 기능이 아니라 권한과 랭킹을 함께 집행하는 다층 시스템이다.

## 깊이 들어가기

### 1. 격리 모델

대표적 선택지:

| 방식 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Shared index + tenant filter | 운영이 쉽다 | 필터 실수 위험 | small tenants |
| Per-tenant index | 격리가 강하다 | 운영 비용 증가 | enterprise tenants |
| Hybrid | 균형이 좋다 | 라우팅 복잡 | 대규모 SaaS |

실무에서는 크고 민감한 tenant만 분리하는 하이브리드가 흔하다.

### 2. Capacity Estimation

예:

- tenant 10만 개
- 상위 100개 tenant가 트래픽 대부분
- 검색 QPS 5만

이때 hot tenant는 독립 index나 캐시가 필요할 수 있다.  
모든 tenant가 같은 shard를 쓰면 noisy neighbor가 생긴다.

봐야 할 숫자:

- tenant-specific QPS
- index size per tenant
- ACL filter latency
- cache hit ratio
- refresh lag

### 3. Query routing

검색 요청은 tenant context를 반드시 포함해야 한다.

- tenant_id
- user role
- resource scope
- region

router는 적절한 index와 filter pipeline을 선택한다.

### 4. Permission filtering

검색은 결과가 빨라도 안 되면 의미가 없다.

- doc-level ACL
- field-level redaction
- role-based visibility
- row-level security

권한 필터는 검색 후처리가 아니라 초기 후보 생성 단계에서도 고려해야 한다.

### 5. Ranking override

tenant별로 랭킹 정책이 다를 수 있다.

- enterprise docs 우선
- 최근성 우선
- 민감 문서 downrank
- pinned result

공통 랭킹과 tenant override를 분리하면 운영이 쉬워진다.

### 6. Indexing and deletion

tenant 삭제는 까다롭다.

- tenant purge
- legal hold
- soft delete
- reindex on policy change

이 부분은 [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)와 연결된다.

### 7. Data residency

tenant가 특정 리전에 묶이면 검색도 따라가야 한다.

- EU tenant -> EU index
- APAC tenant -> APAC index
- metadata만 global control plane

이 부분은 [멀티 테넌트 SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)와 같은 원리다.

## 실전 시나리오

### 시나리오 1: 고객사별 문서 검색

문제:

- 서로 다른 고객의 문서가 섞이면 안 된다

해결:

- tenant-aware routing
- ACL filter
- per-tenant override

### 시나리오 2: 대형 tenant 폭주

문제:

- 한 고객의 검색 트래픽이 전체를 압박한다

해결:

- 독립 shard/index
- tenant quota
- cache partition

### 시나리오 3: 문서 삭제 요청

문제:

- 고객사가 데이터 삭제를 요구한다

해결:

- tenant purge job
- delete tombstone
- index 재빌드

## 코드로 보기

```pseudo
function search(tenantId, user, query):
  index = router.pickIndex(tenantId)
  candidates = index.lookup(query)
  filtered = aclFilter(candidates, user)
  return rank(filtered, tenantPolicy(tenantId))
```

```java
public SearchResult search(SearchRequest req) {
    TenantSearchContext ctx = tenantResolver.resolve(req);
    return searchService.search(ctx, req.query());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Shared index | 단순하다 | 격리 위험 | 초기 SaaS |
| Per-tenant index | 강한 격리 | 비용 증가 | enterprise |
| ACL at query time | 유연하다 | latency 증가 | 문서 수준 권한 |
| ACL at index time | 빠르다 | 재인덱싱 필요 | 민감 데이터 |
| Hybrid routing | 균형이 좋다 | 운영 복잡 | 대부분의 실서비스 |

핵심은 tenant-aware search가 단순 필터가 아니라 **검색, 권한, 격리, 랭킹을 함께 묶는 다중 정책 시스템**이라는 점이다.

## 꼬리질문

> Q: tenant filter만 붙이면 충분한가요?
> 의도: 격리와 권한의 차이 이해 확인
> 핵심: 필터 실수, ACL, residency까지 고려해야 한다.

> Q: per-tenant index는 언제 필요한가요?
> 의도: 격리 수준 선택 이해 확인
> 핵심: 대형, 민감, 규제 tenant에 적합하다.

> Q: 검색 랭킹도 tenant마다 다를 수 있나요?
> 의도: 정책별 랭킹 이해 확인
> 핵심: 문서 우선순위와 정책이 tenant별로 다를 수 있다.

> Q: 데이터 residency는 검색에 왜 중요하나요?
> 의도: 지역 제약 이해 확인
> 핵심: index와 query path도 지역 경계를 따라야 하기 때문이다.

## 한 줄 정리

Tenant-aware search architecture는 검색 결과의 정확성, 권한, 격리, 지역 규제를 함께 만족시키는 멀티테넌트 검색 시스템이다.


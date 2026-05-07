---
schema_version: 3
title: Hot Tenant Split-Out, Routing, and Cutover Playbook
concept_id: database/tenant-split-out-routing-cutover
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- multi-tenant
- tenant-split
- routing-cutover
- backfill
- fencing
aliases:
- hot tenant split out
- tenant routing cutover
- tenant migration playbook
- shared table to dedicated shard
- dual write tenant move
- tenant-specific backfill
- noisy neighbor isolation
- tenant routing registry
- write fence cutover
- dedicated tenant shard
symptoms:
- shared-table에서 특정 tenant가 전체 p99나 buffer pool을 흔들어 dedicated shard로 분리해야 해
- tenant split-out 중 일부 API는 새 DB, 일부 job은 옛 DB를 보는 routing split brain을 막아야 해
- snapshot backfill 이후 catch-up, write fence, routing flip 순서를 설계해야 해
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- database/multi-tenant-tenant-id-index-topology
- database/online-backfill-consistency
next_docs:
- database/schema-migration-partitioning-cdc-cqrs
- database/read-your-writes-session-pinning
- database/application-level-fencing-token-propagation
linked_paths:
- contents/database/multi-tenant-tenant-id-index-topology.md
- contents/database/online-backfill-consistency.md
- contents/database/schema-migration-partitioning-cdc-cqrs.md
- contents/database/read-your-writes-session-pinning.md
- contents/database/application-level-fencing-token-propagation.md
- contents/database/multi-tenant-stats-skew-plan-isolation.md
confusable_with:
- database/multi-tenant-tenant-id-index-topology
- database/online-backfill-consistency
- database/schema-migration-partitioning-cdc-cqrs
forbidden_neighbors: []
expected_queries:
- hot tenant를 shared table에서 dedicated shard로 split out할 때 routing cutover 순서를 알려줘
- tenant migration에서 데이터 복사보다 routing registry와 write fence가 더 어려운 이유가 뭐야?
- snapshot backfill, catch-up, final delta, routing flip, source tombstone 순서를 어떻게 설계해?
- 일부 API는 새 DB를 보고 background job은 옛 DB를 보는 tenant split brain을 어떻게 막아?
- dual write tenant move는 왜 위험하고 CDC catch-up과 짧은 transition으로 제한하는 편이 나아?
contextual_chunk_prefix: |
  이 문서는 hot tenant split-out을 shared table to dedicated shard, tenant routing registry, backfill catch-up, write fence, routing cutover 관점으로 다루는 advanced playbook이다.
  tenant migration, noisy neighbor isolation, dual write tenant move, routing split brain 질문이 본 문서에 매핑된다.
---
# Hot Tenant Split-Out, Routing, and Cutover Playbook

> 한 줄 요약: shared-table에서 hot tenant를 분리하는 일은 데이터 복사보다, 어떤 요청부터 어디로 보낼지와 dual-run 구간을 어떻게 안전하게 관리할지가 더 어렵다.

**난이도: 🔴 Advanced**

관련 문서:

- [Multi-Tenant Table Design, Tenant-First Indexing, and Hotspot Control](./multi-tenant-tenant-id-index-topology.md)
- [Online Backfill Consistency와 워터마크 전략](./online-backfill-consistency.md)
- [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md)
- [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)
- [Application-Level Fencing Token Propagation](./application-level-fencing-token-propagation.md)

retrieval-anchor-keywords: hot tenant split out, tenant routing cutover, tenant migration playbook, shared table to dedicated shard, dual write tenant move, tenant-specific backfill, noisy neighbor isolation

## 핵심 개념

멀티테넌트 시스템에서 특정 테넌트가 너무 커지면 보통 다음 선택지가 생긴다.

- 계속 shared-table에 둔다
- hot tenant만 별도 shard/DB로 승격한다
- 전체 모델을 schema-per-tenant 또는 database-per-tenant로 바꾼다

현실적으로는 "문제 테넌트만 먼저 분리"가 자주 선택된다.  
그런데 이 작업의 난점은 데이터 복사 자체보다 다음에 있다.

- 요청 라우팅을 언제 바꿀 것인가
- 복사 중 write를 어떻게 따라잡을 것인가
- split-out 직전/직후 read-your-writes를 어떻게 보장할 것인가
- 일부 경로만 새 DB를 보고 일부는 옛 DB를 보면 어떻게 막을 것인가

즉 tenant split-out은 storage migration이면서 동시에 **routing contract migration**이다.

## 깊이 들어가기

### 1. 먼저 "분리 이유"를 계량화해야 한다

hot tenant 분리는 비싸다.  
그래서 다음 신호가 있을 때 정당화된다.

- 한 테넌트가 buffer/cache를 과점한다
- tenant별 배치가 다른 테넌트 SLA를 흔든다
- 한 테넌트의 index skew 때문에 전체 plan이 흔들린다
- 지원 조직이 tenant별 export/replay를 자주 요구한다

핵심은 "큰 고객 하나"가 아니라, **shared path의 비용이 다른 테넌트에게 전이되는가**다.

### 2. 라우팅 테이블이 먼저 있어야 한다

split-out 전에 필요한 기본 구조는 tenant routing registry다.

- tenant 42 -> shared cluster
- tenant 999 -> dedicated cluster A

이 registry가 없으면:

- 애플리케이션마다 라우팅 기준이 달라지고
- 일부 job은 옛 DB를 보고
- 일부 API는 새 DB를 보는 split brain이 생긴다

즉 데이터 복사보다 먼저 **요청이 하나의 routing truth를 보도록** 만들어야 한다.

### 3. cutover는 snapshot copy가 아니라 catch-up + fence다

안전한 split-out은 보통 다음 순서를 따른다.

1. 대상 tenant의 snapshot/backfill
2. 변경분 catch-up
3. 짧은 freeze 또는 write fence
4. 최종 delta 적용
5. routing flip
6. 검증 후 source read-only 또는 tombstone화

여기서 중요한 것은 "마지막 write가 어느 쪽에 반영됐는지"를 모호하게 두지 않는 것이다.  
그래서 split-out에서는 짧은 write freeze나 fencing token이 자주 필요하다.

### 4. dual write는 강력하지만 가장 위험한 단계다

tenant split-out에서 dual write를 쓰고 싶어지는 이유는 명확하다.

- 두 DB를 동시에 맞춰 두면 cutover가 쉬워 보인다

하지만 실제 비용은 크다.

- 부분 실패 처리
- 순서 불일치
- 두 시스템의 constraint 차이
- idempotency/compensation 복잡도

그래서 가능하면:

- source of truth는 하나로 유지하고
- 다른 쪽은 backfill + CDC catch-up으로 따라가고
- dual write는 아주 짧은 transition에만 제한적으로 쓰는 편이 낫다

### 5. read-your-writes와 background job 경로를 특히 조심해야 한다

API routing만 바꾸면 끝나지 않는다.

- admin batch
- webhooks
- outbox relay
- search indexing worker
- support tooling

이런 경로가 옛 DB를 계속 보면 tenant 하나 안에서 데이터가 갈라진다.  
따라서 tenant split-out 체크리스트에는 "사용자 요청"뿐 아니라 **비동기/운영 경로 라우팅**이 반드시 포함돼야 한다.

### 6. rollback은 "source로 되돌림"이 아니라 "어느 지점까지 믿을지" 문제다

cutover 뒤 문제가 생겼다고 무조건 source DB로 돌아가면 더 위험할 수 있다.

- 새 DB에 이미 write가 들어왔을 수 있다
- 외부 side effect는 되돌릴 수 없다
- source 데이터는 stale할 수 있다

그래서 rollback 전략은 보통 두 가지 중 하나다.

- cutover 전까지 source만 write 허용, cutover 후 문제 시 route만 되돌림
- cutover 후 source를 read-only reference로 두고, forward-fix만 허용

즉 rollback은 기술적 스위치가 아니라 **write ownership을 어떻게 되돌릴지**에 관한 결정이다.

## 실전 시나리오

### 시나리오 1. VIP 테넌트가 전체 SaaS p99를 흔듦

shared-table에서 한 고객의 최근 주문 조회가 buffer pool을 과도하게 점유한다.

대응:

- tenant routing registry 도입
- snapshot + CDC catch-up
- 짧은 write fence 후 dedicated cluster로 cutover

### 시나리오 2. API는 새 DB를 보는데 배치는 옛 DB를 봄

분리 직후 관리자 재정산 job이 shared DB를 계속 읽으면 숫자가 엇갈린다.

교훈:

- background worker도 tenant-aware routing을 써야 한다
- 운영 도구 경로까지 점검해야 한다

### 시나리오 3. cutover 직후 rollback이 필요해 보임

새 DB latency가 높아 보여 route를 되돌리고 싶지만 이미 일부 write는 새 DB에만 있다.

이 경우는 원복보다:

- 새 DB write ownership 유지
- 읽기 경로만 임시 조정
- 성능 원인 forward-fix

가 더 안전할 수 있다.

## 코드로 보기

```sql
CREATE TABLE tenant_routing (
  tenant_id BIGINT PRIMARY KEY,
  target_cluster VARCHAR(50) NOT NULL,
  routing_version BIGINT NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

```java
class TenantRoutingResolver {
    DatabaseTarget resolve(long tenantId) {
        TenantRoute route = routingRepository.find(tenantId);
        return databaseRegistry.get(route.targetCluster());
    }
}
```

```sql
-- split-out 직전 source write fence 예시
UPDATE tenant_routing
SET target_cluster = 'dedicated-a',
    routing_version = routing_version + 1,
    updated_at = NOW()
WHERE tenant_id = 999;
```

핵심은 실제 SQL보다, 모든 경로가 같은 routing registry와 fencing 규칙을 보게 만드는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| shared-table 유지 | 구조가 단순하다 | noisy neighbor가 남는다 | 큰 테넌트가 아직 적을 때 |
| hot tenant split-out | 문제 테넌트만 분리 가능하다 | routing과 cutover 운영이 복잡하다 | 일부 테넌트만 유난히 클 때 |
| 전면 database-per-tenant | 격리와 이동성이 가장 좋다 | 운영비가 높다 | 규제/고객별 SLA가 강할 때 |
| dual write 중심 이전 | cutover가 부드러워 보인다 | 부분 실패와 정합성 위험이 크다 | 정말 짧은 전환 구간만 허용할 때 |

## 꼬리질문

> Q: hot tenant 분리에서 가장 먼저 필요한 구조는 무엇인가요?
> 의도: 데이터 복사보다 라우팅 통제를 우선하는지 확인
> 핵심: 모든 요청이 참조하는 tenant routing registry가 먼저 필요하다

> Q: tenant split-out에서 dual write를 왜 조심해야 하나요?
> 의도: transition 구간의 정합성 복잡도를 아는지 확인
> 핵심: 두 저장소의 부분 실패와 순서 불일치가 빠르게 커진다

> Q: rollback은 왜 단순히 route만 되돌리는 문제가 아닌가요?
> 의도: write ownership 관점을 이해하는지 확인
> 핵심: cutover 후 새 DB에만 존재하는 write와 side effect가 생길 수 있기 때문이다

## 한 줄 정리

hot tenant split-out의 본질은 데이터 이동보다, tenant별 write ownership과 read routing을 하나의 registry와 fence로 안전하게 전환하는 운영 절차다.

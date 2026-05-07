---
schema_version: 3
title: Multi-Tenant Table Design, Tenant-First Indexing, and Hotspot Control
concept_id: database/multi-tenant-tenant-id-index-topology
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 91
mission_ids: []
review_feedback_tags:
- multi-tenant
- tenant-first-index
- shared-table-design
- noisy-neighbor
aliases:
- multi tenant table design
- tenant_id index
- tenant-first composite key
- shared schema isolation
- tenant hotspot
- tenant scoped migration
- tenant routing registry
- hot tenant split out
- tenant_id를 인덱스 앞에 둬야 하나요
- 멀티테넌트 shared table 설계
symptoms:
- shared-table 멀티테넌시에서 tenant_id를 빠뜨린 access path 때문에 다른 tenant row까지 넓게 scan하고 있어
- 큰 tenant 하나가 buffer pool, batch, purge, query plan까지 흔드는 noisy neighbor가 되었어
- VIP tenant를 나중에 분리하려는데 PK, FK, backfill, routing registry가 tenant boundary로 정리되어 있지 않아
intents:
- design
- troubleshooting
prerequisites:
- database/index-basics
- database/clustered-index-locality
next_docs:
- database/multi-tenant-stats-skew-plan-isolation
- database/tenant-split-out-routing-cutover
- database/partition-pruning-hot-cold-data
linked_paths:
- contents/database/schema-migration-partitioning-cdc-cqrs.md
- contents/database/partition-pruning-hot-cold-data.md
- contents/database/insert-hotspot-page-contention.md
- contents/database/hot-row-contention-counter-sharding.md
- contents/database/read-your-writes-session-pinning.md
- contents/database/multi-tenant-stats-skew-plan-isolation.md
- contents/database/tenant-split-out-routing-cutover-playbook.md
- contents/database/clustered-index-locality.md
- contents/database/index-maintenance-window-rollout-playbook.md
confusable_with:
- database/multi-tenant-stats-skew-plan-isolation
- database/partition-pruning-hot-cold-data
- database/tenant-split-out-routing-cutover
forbidden_neighbors: []
expected_queries:
- shared table 멀티테넌시에서 tenant_id를 composite index 앞쪽에 둬야 하는 이유가 뭐야?
- tenant-first primary key와 global id plus secondary index의 장단점을 비교해줘
- noisy neighbor tenant가 생겼을 때 index, queue, shard 분리 순서로 어떻게 대응해?
- 나중에 VIP tenant를 별도 DB로 옮기려면 처음부터 어떤 tenant boundary를 남겨야 해?
- tenant 단위 backfill이나 purge가 전체 테이블을 흔들지 않게 설계하는 방법을 알려줘
contextual_chunk_prefix: |
  이 문서는 shared-table 멀티테넌시에서 tenant_id를 보안 필터이자 물리 locality, composite key, batch boundary로 설계하는 advanced playbook이다.
  tenant-first index, noisy neighbor, tenant scoped migration, hot tenant split out 준비 질문이 본 문서에 매핑된다.
---
# Multi-Tenant Table Design, Tenant-First Indexing, and Hotspot Control

> 한 줄 요약: shared-table 멀티테넌시는 `tenant_id`를 붙이는 것으로 끝나지 않고, primary key·secondary index·배치 범위를 tenant 경계에 맞춰야 오래 버틴다.

**난이도: 🔴 Advanced**

관련 문서:

- [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md)
- [Partition Pruning과 Hot/Cold 데이터 전략](./partition-pruning-hot-cold-data.md)
- [Insert Hotspot과 Page Contention](./insert-hotspot-page-contention.md)
- [Hot Row Contention과 Counter Sharding](./hot-row-contention-counter-sharding.md)
- [Read-after-write Session Pinning 전략](./read-your-writes-session-pinning.md)
- [Multi-Tenant Statistics Skew, Plan Drift, and Query Isolation](./multi-tenant-stats-skew-plan-isolation.md)
- [Hot Tenant Split-Out, Routing, and Cutover Playbook](./tenant-split-out-routing-cutover-playbook.md)

retrieval-anchor-keywords: multi tenant table design, tenant_id index, tenant-first composite key, noisy neighbor, shared schema isolation, tenant hotspot, tenant scoped migration, backend SaaS database, tenant routing registry, hot tenant split out

## 핵심 개념

shared-table 멀티테넌시는 여러 테넌트의 데이터를 같은 테이블에 넣고 `tenant_id`로 구분하는 방식이다.

장점:

- 운영이 단순하다
- schema drift가 적다
- 작은 테넌트가 많을 때 비용 효율이 좋다

하지만 시간이 지나면 다음 문제가 나타난다.

- 일부 테넌트가 noisy neighbor가 된다
- 쿼리에서 `tenant_id`를 빼먹으면 격리 사고가 난다
- 인덱스가 tenant 경계를 잘 반영하지 않으면 scan 범위가 커진다
- 배치, 백필, purge 작업이 전체 테이블을 흔든다

핵심은 shared-table의 본질이 "컬럼 하나 추가"가 아니라, **모든 access path를 tenant boundary 중심으로 재설계하는 것**이라는 점이다.

## 깊이 들어가기

### 1. `tenant_id`는 보안 필터이자 물리적 locality 힌트다

많은 팀이 `tenant_id`를 단순 권한 체크 컬럼으로 본다.  
하지만 DB 관점에서는 다음 역할도 한다.

- index prefix
- 파티셔닝 기준
- 배치/백필의 작업 단위
- 캐시 키와 CDC key의 범위 경계

즉 `tenant_id`를 access path 첫머리에 두지 않으면, 논리적 격리와 물리적 효율이 모두 무너질 수 있다.

### 2. shared-table에서 index는 tenant-first가 기본인 경우가 많다

예를 들어 대부분 쿼리가 "한 테넌트 안에서 주문 조회"라면:

- 좋은 후보
  - `(tenant_id, order_id)`
  - `(tenant_id, status, created_at)`
- 위험한 후보
  - `(status, created_at)`
  - `(created_at)`

tenant 조건이 뒤로 밀리면:

- 다른 테넌트 row까지 훑는다
- 캐시/버퍼 locality가 나빠진다
- tenant 단위 purge나 export가 비싸진다

물론 global admin query가 많다면 별도 global index나 read model이 필요할 수 있다.  
핵심은 "대부분의 요청 경로"를 기준으로 tenant-first를 기본값으로 두는 것이다.

### 3. primary key topology도 쓰기 hotspot과 연관된다

PK 선택은 격리뿐 아니라 page split과 hotspot에도 영향을 준다.

- `(tenant_id, local_id)` composite PK
  - 테넌트별 locality가 좋다
  - tenant 단위 export와 purge가 쉽다
  - 특정 tenant의 쓰기가 한 구간에 몰릴 수 있다
- global snowflake ID + `tenant_id` secondary index
  - 전역 uniqueness가 쉽다
  - tenant 조회 시 secondary lookup이 필요할 수 있다
- hash-sharded tenant key
  - 극단적 hotspot 분산에 유리하다
  - 운영 복잡도가 높다

즉 멀티테넌시에서 PK는 "식별자"만의 문제가 아니라 **트래픽 분포와 운영 단위**를 결정한다.

### 4. noisy neighbor를 쿼리와 인덱스만으로는 못 막을 때가 많다

큰 테넌트 하나가 다음을 유발할 수 있다.

- autovacuum/compaction 편중
- buffer pool 점유
- lag 증가
- tenant별 배치 경쟁

이때 대응은 계층적으로 올라간다.

- tenant rate limit
- tenant별 job queue 분리
- hot tenant 전용 파티션 또는 shard 분리
- schema-per-tenant / database-per-tenant 승격

shared-table이 영원한 종착지라고 가정하면, 결국 가장 큰 테넌트가 전체 시스템의 의사결정을 대신하게 된다.  
이 영향은 CPU와 IO뿐 아니라 global statistics와 query plan까지 번질 수 있다.

### 5. 운영 작업도 tenant 범위로 잘라야 안전하다

멀티테넌트 시스템의 backfill, delete, reindex, export는 전체 스캔보다 tenant 또는 tenant-bucket 단위로 나누는 편이 낫다.

이유:

- blast radius를 줄인다
- 특정 고객 이슈를 부분적으로 복구할 수 있다
- support 요청에 tenant 단위 재처리가 가능하다
- 큰 테넌트만 별도 스케줄링할 수 있다

즉 tenant boundary는 읽기 필터일 뿐 아니라 **운영 절차 단위**다.

### 6. shared-table에서 schema-per-tenant로 가는 탈출 경로를 미리 생각해야 한다

처음부터 database-per-tenant가 과한 경우가 많다.  
하지만 shared-table만 가정해도 위험하다.

미리 준비할 것:

- tenant_id가 모든 주요 테이블에 일관되게 존재하는가
- PK/FK에 tenant 경계가 드러나는가
- tenant 단위 export/import가 가능한가
- tenant 단위 shadow migration을 할 수 있는가

이 준비가 돼 있어야 특정 VIP tenant를 별도 cluster로 승격할 수 있다.
실제 승격 절차에서는 snapshot/backfill보다 routing registry와 write fence를 어떻게 거는지가 더 중요해진다.

## 실전 시나리오

### 시나리오 1. 관리자 화면이 특정 테넌트에서만 느림

해당 테넌트 데이터가 큰데 index가 `(status, created_at)` 위주라면, 한 테넌트 조회에도 다른 테넌트 row가 많이 섞인다.

대응:

- `(tenant_id, status, created_at)` 복합 인덱스 검토
- 대형 테넌트 전용 summary/read model
- heavy tenant 전용 read replica 또는 shard 분리

### 시나리오 2. tenant 단위 purge가 전체 시스템을 흔듦

탈퇴한 고객 데이터 삭제 배치를 전체 테이블 기준으로 돌리면 lock과 IO가 넓게 번진다.

대응:

- tenant_id prefix index 사용
- tenant bucket 단위 chunk delete
- archive 후 비동기 purge

### 시나리오 3. VIP 테넌트만 별도 DB로 옮기고 싶음

테이블 간 FK와 PK에 tenant 경계가 애매하면 export/import가 고통스럽다.

이 경우는 초기 설계 때부터 tenant-scoped key와 checkpoint, backfill tooling이 필요하다.

## 코드로 보기

```sql
CREATE TABLE orders (
  tenant_id BIGINT NOT NULL,
  order_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at TIMESTAMP NOT NULL,
  PRIMARY KEY (tenant_id, order_id),
  KEY idx_orders_tenant_status_created (tenant_id, status, created_at)
);
```

```sql
SELECT order_id, user_id, status, created_at
FROM orders
WHERE tenant_id = ?
  AND status = 'PAID'
ORDER BY created_at DESC
LIMIT 50;
```

```sql
-- tenant 단위 backfill 예시
INSERT INTO orders_summary (tenant_id, order_date, paid_count)
SELECT tenant_id, DATE(created_at), COUNT(*)
FROM orders
WHERE tenant_id = ?
GROUP BY tenant_id, DATE(created_at);
```

shared-table 멀티테넌시에서는 이런 식으로 대부분의 read/write/ops path가 tenant boundary로 잘려야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| shared table + tenant-first index | 비용 효율과 운영 단순성이 좋다 | noisy neighbor 위험이 있다 | 소형/중형 테넌트가 많은 SaaS |
| schema per tenant | 격리감이 좋다 | schema 운영비가 커진다 | 테넌트 수가 적고 커스터마이징이 많을 때 |
| database per tenant | 강한 격리와 이동성이 있다 | 인프라 비용이 높다 | VIP 고객, 규제 강한 환경 |
| hot tenant split-out | 점진 이행이 가능하다 | 이중 운영 복잡도가 생긴다 | 일부 테넌트만 과도하게 클 때 |

## 꼬리질문

> Q: shared-table에서 왜 `tenant_id`를 인덱스 앞쪽에 두나요?
> 의도: 논리 격리와 물리 locality를 함께 보는지 확인
> 핵심: 대부분의 쿼리가 tenant 범위 안에서 일어나므로 scan 범위와 cache locality를 줄일 수 있다

> Q: noisy neighbor 문제는 인덱스만 잘 잡으면 해결되나요?
> 의도: 구조적 한계를 아는지 확인
> 핵심: rate limit, queue 분리, shard 분리 같은 상위 계층 대응이 함께 필요할 수 있다

> Q: 멀티테넌트 설계에서 migration을 왜 미리 생각해야 하나요?
> 의도: 탈출 경로를 설계 관점에서 보는지 확인
> 핵심: 큰 테넌트를 나중에 분리하려면 tenant-scoped key와 export/backfill 경로가 필요하다

## 한 줄 정리

shared-table 멀티테넌시의 핵심은 `tenant_id` 존재 여부가 아니라, 인덱스와 운영 절차가 tenant 경계 중심으로 잘려 있어 noisy neighbor와 향후 분리를 감당할 수 있는가다.

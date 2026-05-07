---
schema_version: 3
title: Schema Migration, Partitioning, CDC, CQRS
concept_id: database/schema-migration-partitioning-cdc-cqrs
canonical: true
category: database
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- schema-migration
- partitioning
- cdc
- cqrs
- read-model
aliases:
- schema migration
- partitioning
- CDC
- CQRS
- multi-tenant database
- online schema change
- read model cutover
- projection rebuild
- dual read verification
- event schema evolution
symptoms:
- 운영 중 DDL 변경, backfill, CDC, read model cutover 주제가 한꺼번에 엮여 어디서 시작할지 모르겠어
- schema migration과 partitioning, CQRS를 각각 focused deep dive로 내려가야 해
- read/write splitting이나 read model freshness 문제를 CDC와 projection SLO까지 연결해야 해
intents:
- definition
- design
- deep_dive
prerequisites:
- database/online-schema-change-strategies
- database/cdc-debezium-outbox-binlog
next_docs:
- database/online-backfill-consistency
- database/cdc-schema-evolution-compatibility-playbook
- database/incremental-summary-table-refresh-watermark
- database/multi-tenant-tenant-id-index-topology
linked_paths:
- contents/database/online-schema-change-strategies.md
- contents/database/online-backfill-consistency.md
- contents/database/cdc-debezium-outbox-binlog.md
- contents/database/cdc-schema-evolution-compatibility-playbook.md
- contents/database/incremental-summary-table-refresh-watermark.md
- contents/database/multi-tenant-tenant-id-index-topology.md
- contents/database/multi-tenant-stats-skew-plan-isolation.md
- contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md
- contents/design-pattern/read-model-cutover-guardrails.md
- contents/design-pattern/event-upcaster-compatibility-patterns.md
- contents/system-design/change-data-capture-outbox-relay-design.md
- contents/system-design/historical-backfill-replay-platform-design.md
- contents/system-design/zero-downtime-schema-migration-platform-design.md
- contents/system-design/dual-read-comparison-verification-platform-design.md
confusable_with:
- database/online-schema-change-strategies
- database/cdc-debezium-outbox-binlog
- database/incremental-summary-table-refresh-watermark
forbidden_neighbors: []
expected_queries:
- schema migration, partitioning, CDC, CQRS를 한 번에 훑고 focused deep dive로 내려가는 순서를 알려줘
- 운영 중 스키마 변경은 DDL만이 아니라 backfill, dual read, cutover 전략이라는 뜻이 뭐야?
- CDC와 outbox, read model projection, freshness SLO가 어떻게 연결돼?
- tenant partitioning과 multi-tenant statistics skew를 schema migration 문맥에서 어떻게 봐야 해?
- CQRS read model을 만들면 동기화 지연, replay, rollback window까지 왜 설계해야 해?
contextual_chunk_prefix: |
  이 문서는 schema migration, partitioning, CDC, CQRS, read model cutover를 focused database/design/system 문서로 연결하는 advanced bridge다.
  online schema change, backfill, projection rebuild, dual read verification, event schema evolution 질문이 본 문서에 매핑된다.
---
# Schema Migration, Partitioning, CDC, CQRS

**난이도: 🔴 Advanced**

> 백엔드가 커질수록 등장하는 데이터 관리 주제를 정리한 문서
>
> 문서 역할: 이 문서는 schema migration, partitioning, CDC, CQRS를 한 번에 훑는 **survey 문서**다. 실행 절차나 장애 대응이 필요하면 아래의 focused deep dive를 먼저 보는 편이 낫다.

관련 문서: [온라인 스키마 변경 전략](./online-schema-change-strategies.md), [Online Backfill Consistency와 워터마크 전략](./online-backfill-consistency.md), [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md), [CDC Schema Evolution, Event Compatibility, and Expand-Contract Playbook](./cdc-schema-evolution-compatibility-playbook.md), [Incremental Summary Table Refresh and Watermark Discipline](./incremental-summary-table-refresh-watermark.md), [Multi-Tenant Table Design, Tenant-First Indexing, and Hotspot Control](./multi-tenant-tenant-id-index-topology.md), [Multi-Tenant Statistics Skew, Plan Drift, and Query Isolation](./multi-tenant-stats-skew-plan-isolation.md), [Projection Rebuild, Backfill, and Cutover Pattern](../design-pattern/projection-rebuild-backfill-cutover-pattern.md), [Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md), [Read Model Cutover Guardrails](../design-pattern/read-model-cutover-guardrails.md), [Projection Freshness SLO Pattern](../design-pattern/projection-freshness-slo-pattern.md), [Event Upcaster Compatibility Patterns](../design-pattern/event-upcaster-compatibility-patterns.md), [Change Data Capture / Outbox Relay 설계](../system-design/change-data-capture-outbox-relay-design.md), [Historical Backfill / Replay Platform](../system-design/historical-backfill-replay-platform-design.md), [Zero-Downtime Schema Migration Platform](../system-design/zero-downtime-schema-migration-platform-design.md), [Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)
retrieval-anchor-keywords: schema migration, partitioning, cdc, cqrs, multi-tenant database, summary table refresh, watermark, online schema change, read model, schema evolution compatibility, tenant stats skew, dual read verification, projection rebuild, read cutover, cdc outbox, session pinning, projection freshness slo, cutover guardrail

<details>
<summary>Table of Contents</summary>

- [이 문서를 어떻게 읽을까](#이-문서를-어떻게-읽을까)
- [왜 중요한가](#왜-중요한가)
- [Schema Migration](#schema-migration)
- [Partitioning](#partitioning)
- [CDC](#cdc)
- [CQRS](#cqrs)
- [Read/Write Splitting](#readwrite-splitting)
- [CQRS 실제 함정](#cqrs-실제-함정)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

## 이 문서를 어떻게 읽을까

- 운영 중 DDL 변경 전략이 궁금하면 [온라인 스키마 변경 전략](./online-schema-change-strategies.md)부터 본다.
- CDC 구현과 relay 경계가 궁금하면 [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md)로 내려간다.
- 이벤트/스키마 호환성까지 필요하면 [CDC Schema Evolution, Event Compatibility, and Expand-Contract Playbook](./cdc-schema-evolution-compatibility-playbook.md)을 본다.
- tenant 분리와 cutover는 [Multi-Tenant Table Design, Tenant-First Indexing, and Hotspot Control](./multi-tenant-tenant-id-index-topology.md), [Hot Tenant Split-Out, Routing, and Cutover Playbook](./tenant-split-out-routing-cutover-playbook.md)로 이어진다.
- read model cutover 검증이 궁금하면 [Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md), [Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)을 같이 본다.
- freshness budget, rollback window, fallback guardrail이 궁금하면 [Read Model Cutover Guardrails](../design-pattern/read-model-cutover-guardrails.md), [Projection Freshness SLO Pattern](../design-pattern/projection-freshness-slo-pattern.md), [Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)을 같이 본다.

## 왜 중요한가

작은 프로젝트에서는 테이블 생성만 잘해도 되지만,
서비스가 커지면

- 스키마를 안전하게 바꾸는 법
- 데이터를 나누는 법
- 변경 이벤트를 다른 시스템에 전달하는 법
- 읽기/쓰기 책임을 분리하는 법

까지 고민하게 된다.

---

## Schema Migration

Schema Migration은 **운영 중인 DB 스키마를 안전하게 변경하는 과정**이다.

예:

- 컬럼 추가
- 인덱스 추가
- nullable -> not null 전환

중요한 점:

- 운영 중 데이터가 이미 존재할 수 있다
- 한 번에 파괴적 변경을 하면 장애가 날 수 있다

즉 migration은 단순 DDL 실행이 아니라 **배포 전략** 문제와도 연결된다.
실행 순서, backfill, dual write/read, contract phase는 [온라인 스키마 변경 전략](./online-schema-change-strategies.md)에서 더 깊게 다룬다.

---

## Partitioning

Partitioning은 **큰 테이블을 특정 기준으로 논리/물리 분할하는 방식**이다.

예:

- 날짜 기준 분리
- 지역 기준 분리
- tenant 기준 분리

장점:

- 범위 조회 성능 개선 가능
- 관리 효율 향상

단점:

- 분할 키 설계가 중요
- 잘못하면 오히려 운영이 복잡해짐

---

## CDC

CDC(Change Data Capture)는 **DB의 변경 내용을 감지해서 다른 시스템으로 전달하는 방식**이다.

예:

- 주문 생성 이벤트를 검색 서버에 반영
- 결제 변경을 분석 시스템으로 전달

즉 “DB 변경을 이벤트처럼 흘려보내는 방식”이라고 보면 된다.
실제 relay, binlog, replay, backpressure는 [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md)과 [CDC Gap Repair, Reconciliation, and Rebuild Boundaries](./cdc-gap-repair-reconciliation-playbook.md)에서 이어서 본다.

---

## CQRS

CQRS(Command Query Responsibility Segregation)는
**쓰기 모델과 읽기 모델의 책임을 분리하는 방식**이다.

왜 쓰나:

- 읽기와 쓰기 요구사항이 다를 때
- 조회 최적화와 변경 정합성의 관심사가 다를 때

하지만 작은 서비스에 무조건 적용하면 과할 수 있다.

CQRS는 "조회 성능을 높이는 만능키"가 아니다.  
읽기 모델을 따로 만들면 결국 **동기화 지연, 중복 저장, 운영 복잡도**를 함께 떠안는다.

특히 summary table이나 read model은 watermark, replay, late event 정정 전략까지 있어야 오래 유지된다.
이 운영 비용은 [Incremental Summary Table Refresh and Watermark Discipline](./incremental-summary-table-refresh-watermark.md)와 연결해서 보면 이해가 빠르다.

---

## Read/Write Splitting

Read/Write Splitting은 **쓰기 요청은 primary로, 읽기 요청은 replica로 분리하는 방식**이다.

대표 목적:

- 읽기 부하 분산
- 쓰기와 읽기의 독립 확장

### 실전에서 중요한 점

- replica는 primary보다 늦을 수 있다
- 직전 write 직후 read가 들어오면 이전 값이 보일 수 있다
- 같은 사용자의 연속 요청에서 읽기 일관성이 깨질 수 있다

즉 읽기 분리는 성능을 위한 선택이지, 정합성을 자동으로 보장하는 선택은 아니다.

### 자주 생기는 문제

- 주문 생성 직후 조회했는데 주문이 안 보임
- 결제 완료 후 상태가 아직 pending으로 보임
- 관리자가 수정한 값이 잠시 반영되지 않음

### 대응 방식

- 중요한 읽기는 primary를 직접 보게 한다
- write 이후 일정 시간 동안 같은 사용자는 primary를 보게 한다
- 세션 단위 stickiness를 둔다
- replica lag가 허용 범위를 넘으면 읽기 라우팅을 바꾼다

읽기 분리는 "어디서 읽을지"를 정하는 문제이기도 하다.

---

## CQRS 실제 함정

CQRS를 도입할 때 가장 많이 놓치는 건 **모델 분리 자체보다 동기화 비용**이다.

### 1. 읽기 모델이 진실의 원천처럼 보인다

읽기 모델은 보통 조회 성능에 최적화된 별도 저장소다.  
하지만 실제 정답은 write model에 있고, read model은 지연될 수 있다.

### 2. write-after-read가 깨진다

예:

1. 사용자가 정보를 수정한다
2. 바로 목록 화면으로 이동한다
3. 목록은 replica/read model을 보고 있어서 옛값이 보인다

이건 버그처럼 보이지만, 설계상 예상 가능한 현상일 수 있다.

### 3. 이벤트 순서와 중복이 문제다

CQRS에서 read model을 갱신하는 방식은 보통 비동기다.

- 이벤트가 중복 전달될 수 있다
- 순서가 바뀔 수 있다
- 일부 이벤트는 늦게 도착할 수 있다

따라서 소비자는 멱등해야 하고, read model 갱신 로직도 순서를 감안해야 한다.

### 4. 운영 복잡도가 빠르게 커진다

CQRS는 보통 다음을 추가로 요구한다.

- 이벤트 발행
- 비동기 소비자
- 재처리 로직
- dead letter 처리
- 관측 지표

작은 서비스에서 이 비용은 편익보다 클 수 있다.

### 5. 조회가 단순하지 않다

읽기 모델을 따로 두면 조회는 빨라질 수 있지만,

- 데이터 중복
- 스키마 이중 관리
- 장애 시 정합성 확인

까지 생각해야 한다.

즉 CQRS는 단순한 아키텍처 스타일이 아니라 **운영 모델**이다.

---

## 시니어 관점 질문

- schema migration을 안전하게 하려면 어떤 배포 전략이 필요한가?
- partitioning과 sharding은 어떻게 다른가?
- CDC를 쓰면 결국 순서 보장과 중복 처리 문제를 왜 다시 마주치게 되는가?
- read/write splitting은 왜 성능 문제를 정합성 문제로 바꿀 수 있는가?
- CQRS에서 read model이 stale할 때 사용자 경험을 어떻게 설계할 것인가?
- CQRS는 왜 멋져 보여도 작은 서비스에는 과할 수 있는가?

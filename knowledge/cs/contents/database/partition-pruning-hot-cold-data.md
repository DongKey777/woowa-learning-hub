---
schema_version: 3
title: Partition Pruning and Hot/Cold Data
concept_id: database/partition-pruning-hot-cold-data
canonical: true
category: database
difficulty: intermediate
doc_role: playbook
level: intermediate
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- partition-pruning
- hot-cold-data
- archive
- query-tuning
aliases:
- partition pruning
- range partitioning
- hot cold data
- cold archive
- partition elimination
- time-series partition
- hot partition
- 핫콜드 데이터
- 파티션 pruning
- 오래된 데이터 archive
symptoms:
- 파티셔닝만 하면 자동으로 빨라진다고 보고 partition key와 WHERE 조건 정합성을 확인하지 않고 있어
- 최근 데이터와 오래된 audit/archive row가 섞여 hot query가 전체 table과 cold partition까지 훑고 있어
- DATE(created_at) 같은 함수 조건 때문에 partition pruning이나 index usage가 약해지고 있어
intents:
- troubleshooting
- design
prerequisites:
- database/schema-migration-partitioning-cdc-cqrs
- database/index-and-explain
next_docs:
- database/multi-tenant-tenant-id-index-topology
- database/online-backfill-consistency
- database/destructive-schema-cleanup-column-retirement
linked_paths:
- contents/database/schema-migration-partitioning-cdc-cqrs.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/index-and-explain.md
- contents/database/multi-tenant-tenant-id-index-topology.md
- contents/database/online-backfill-consistency.md
- contents/database/destructive-schema-cleanup-column-retirement.md
- contents/spring/spring-persistence-transaction-web-service-repository-primer.md
confusable_with:
- database/schema-migration-partitioning-cdc-cqrs
- database/multi-tenant-tenant-id-index-topology
- database/destructive-schema-cleanup-column-retirement
forbidden_neighbors: []
expected_queries:
- partition pruning은 파티셔닝하면 자동으로 되는 게 아니라 WHERE 조건과 왜 맞아야 해?
- hot data와 cold data를 분리하면 최근 주문 조회와 archive 운영에 어떤 이점이 있어?
- WHERE DATE(created_at) 조건이 pruning과 index 사용을 약하게 만드는 이유를 알려줘
- range partition과 hash partition을 hot/cold data 관점에서 비교해줘
- partition pruning이 index를 대체하지 않는 이유와 각 파티션 내부 인덱스 필요성을 설명해줘
contextual_chunk_prefix: |
  이 문서는 partition pruning, range partitioning, hot/cold data, cold archive를 query predicate와 partition key 정합성 기준으로 다루는 intermediate playbook이다.
  파티션 pruning, 핫콜드 데이터, 오래된 데이터 archive, DATE(created_at) pruning 실패 질문이 본 문서에 매핑된다.
---
# Partition Pruning and Hot/Cold Data


> 한 줄 요약: Partition Pruning and Hot/Cold Data는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-persistence-transaction-web-service-repository-primer.md)


retrieval-anchor-keywords: partition pruning hot cold data basics, partition pruning hot cold data beginner, partition pruning hot cold data intro, database basics, beginner database, 처음 배우는데 partition pruning hot cold data, partition pruning hot cold data 입문, partition pruning hot cold data 기초, what is partition pruning hot cold data, how to partition pruning hot cold data
> 파티셔닝은 데이터를 나누는 기술이고, partition pruning은 그중 읽을 것만 골라내는 최적화다. hot/cold 데이터를 같이 다루면 체감 효과가 커진다.

> 관련 문서: [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md), [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md), [인덱스와 실행 계획](./index-and-explain.md)

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [Partition Pruning](#partition-pruning)
- [Hot/Cold Data](#hotcold-data)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [SQL/운영 예제](#sql운영-예제)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)

</details>

> retrieval-anchor-keywords:
> - partition pruning
> - range partitioning
> - hot cold data
> - cold archive
> - partition elimination
> - time-series partition
> - 핫콜드 데이터

## 왜 중요한가

대용량 테이블에서 가장 비싼 비용은 "많은 행을 읽는 것"이다.
파티셔닝은 테이블을 나누어 관리 비용을 줄이지만, 진짜 이득은 **필요한 파티션만 읽게 만드는 것**에서 나온다.

- 최근 7일 데이터만 자주 본다
- 오래된 데이터는 거의 조회하지 않는다
- 삭제보다 보관/아카이빙이 더 중요하다

이런 경우 hot/cold 분리는 파티셔닝과 잘 맞는다.

---

## Partition Pruning

Partition pruning은 **쿼리 조건을 보고 DB가 불필요한 파티션을 건너뛰는 최적화**다.

예:

- `created_at` 범위 조건이 있으면 해당 월 파티션만 스캔
- `tenant_id` 기준이면 특정 tenant 파티션만 조회

중요한 점:

- 파티셔닝했다고 자동으로 빨라지지는 않는다
- 조건이 파티션 키와 맞아야 pruning이 잘 된다
- 함수로 감싸거나 조건이 애매하면 전체 파티션을 훑을 수 있다

---

## Hot/Cold Data

Hot data는 최근 조회/변경이 많은 데이터다.
Cold data는 오래되어 거의 읽지 않지만 보관은 필요한 데이터다.

예:

- hot: 최근 주문, 최근 결제, 최근 로그
- cold: 1년 전 주문, 감사 로그, 정산 이력

전략:

- hot 데이터는 빠른 인덱스와 짧은 보존 주기
- cold 데이터는 별도 파티션, 별도 스토리지, 아카이브 테이블

핵심은 "같은 테이블에 다 넣되, 모두를 같은 방식으로 대하지 않는 것"이다.

---

## 깊이 들어가기

### 1. pruning은 쿼리 형태에 민감하다

다음처럼 파티션 키를 직접 거는 조건이 유리하다.

```sql
SELECT *
FROM orders
WHERE created_at >= '2026-04-01'
  AND created_at <  '2026-05-01';
```

반대로 아래처럼 함수로 감싸면 최적화가 약해질 수 있다.

```sql
SELECT *
FROM orders
WHERE DATE(created_at) = '2026-04-08';
```

### 2. hot/cold는 운영 전략이다

Partitioning은 조회 최적화만이 아니다.

- 오래된 파티션 drop으로 purge 비용 감소
- cold 파티션을 별도 백업 정책으로 관리
- hot 파티션만 압축/튜닝 대상으로 유지

### 3. 잘못된 파티션 키는 역효과를 낸다

자주 쓰는 조건과 다르게 나누면 pruning이 안 되고,
파티션 메타데이터만 늘어날 수 있다.

### 4. 인덱스와 함께 봐야 한다

파티션을 잘 나눠도, 각 파티션 내부에서 인덱스가 부실하면 느리다.
즉 partition pruning은 인덱스를 대체하지 않는다.

---

## 실전 시나리오

### 시나리오 1: 최근 주문 조회가 느리다

원인:

- 전체 주문 테이블이 너무 큼
- 최근 데이터와 과거 데이터가 섞여 있음

대응:

- `created_at` 기준 range partition
- 최근 기간 조건을 명확히 넣는 API 설계
- cold 파티션은 조회 경로에서 분리

### 시나리오 2: 월말 정산용 데이터는 오래 보관해야 한다

원인:

- 삭제하면 안 됨
- 하지만 운영 쿼리와 섞이면 느려짐

대응:

- hot partition과 cold partition 분리
- 아카이브 테이블로 이동
- 조회 패턴에 따라 별도 경로 제공

---

## SQL/운영 예제

```sql
-- 파티션 키가 범위 조건과 맞을 때 pruning 기대
EXPLAIN
SELECT id, amount
FROM orders
WHERE created_at >= '2026-04-01'
  AND created_at <  '2026-04-02';
```

```sql
-- 비권장 예시: 함수로 감싸서 pruning 가능성을 낮춤
EXPLAIN
SELECT id, amount
FROM orders
WHERE DATE(created_at) = '2026-04-08';
```

```bash
# 운영 예시
# 1) 최근 30일은 hot partition 유지
# 2) 90일 지난 데이터는 cold partition으로 이동
# 3) 오래된 파티션은 백업 후 drop
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| range partition | pruning이 직관적 | 키 설계 중요 | 시간 축 데이터 |
| hash partition | 분산이 고름 | 범위 조회에 약함 | 균등 분산 필요 |
| hot/cold 분리 | 운영 효율 좋음 | 경로 복잡 | 보관 기간이 긴 서비스 |
| 단일 테이블 + 인덱스 | 단순 | 커지면 한계 | 규모가 작을 때 |

---

## 꼬리질문

- partition pruning은 왜 모든 파티셔닝에서 자동으로 잘 되지 않는가?
- hot/cold 데이터를 분리하면 어떤 운영 이점이 생기는가?
- 파티셔닝과 인덱스의 역할 차이는 무엇인가?
- `WHERE DATE(created_at) = ...` 같은 조건이 왜 불리한가?

---

## 한 줄 정리

파티셔닝의 핵심은 데이터를 나누는 것보다, 쿼리가 불필요한 데이터를 건너뛰게 만드는 것이다. hot/cold 분리는 그 효과를 운영 관점에서 키워준다.

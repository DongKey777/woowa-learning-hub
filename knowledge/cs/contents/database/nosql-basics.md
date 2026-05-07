---
schema_version: 3
title: NoSQL Basics
concept_id: database/nosql-basics
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- nosql
- data-modeling
- scale-out
- database-choice
aliases:
- nosql basics
- nosql 이란
- nosql vs rdb
- document store beginner
- key-value store beginner
- column-family beginner
- graph database beginner
- 수평 확장 DB
- NoSQL 언제 쓰나요
- MongoDB Redis Cassandra 차이
symptoms:
- RDB와 NoSQL을 속도나 유행 기준으로만 비교하고 데이터 모델과 조회 패턴 기준을 놓치고 있어
- document, key-value, column-family, graph store의 용도 차이를 입문 수준에서 구분해야 해
- NoSQL이면 schema와 transaction이 완전히 없다고 단정하고 있어
intents:
- definition
- comparison
prerequisites:
- database/database-first-step-bridge
next_docs:
- database/mvcc-replication-sharding
- database/schema-migration-partitioning-cdc-cqrs
- system-design/idempotency-key-store-dedup-window-replay-safe-retry-design
linked_paths:
- contents/database/mvcc-replication-sharding.md
- contents/database/schema-migration-partitioning-cdc-cqrs.md
- contents/spring/spring-data-jpa-basics.md
- contents/database/database-first-step-bridge.md
confusable_with:
- database/mvcc-replication-sharding
- database/schema-migration-partitioning-cdc-cqrs
- database/index-basics
forbidden_neighbors: []
expected_queries:
- NoSQL은 RDB와 무엇이 다르고 언제 선택해야 해?
- key-value, document, column-family, graph database를 초보자용으로 비교해줘
- NoSQL이면 schema나 transaction이 아예 없다고 보면 안 되는 이유가 뭐야?
- 수평 확장이 필요하면 무조건 NoSQL을 골라야 하는지 설명해줘
- MongoDB, Redis, Cassandra의 대표 사용 사례를 데이터 모델 기준으로 알려줘
contextual_chunk_prefix: |
  이 문서는 NoSQL을 key-value, document, column-family, graph 데이터 모델과 scale-out 관점에서 RDB와 비교하는 beginner primer다.
  NoSQL 이란, NoSQL vs RDB, 수평 확장 DB, MongoDB Redis Cassandra 차이 질문이 본 문서에 매핑된다.
---
# NoSQL 기초 (NoSQL Basics)

> 한 줄 요약: NoSQL은 관계형 DB의 고정 스키마와 조인 제약을 포기하는 대신 유연한 데이터 모델과 수평 확장을 선택한 DB 계열이다.

**난이도: 🟢 Beginner**

관련 문서:

- [MVCC, Replication, Sharding](./mvcc-replication-sharding.md)
- [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md)
- [database 카테고리 인덱스](./README.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

retrieval-anchor-keywords: nosql basics, nosql 이란, nosql vs rdb, document store beginner, key-value store beginner, 수평 확장 db, 스키마 유연성 db, nosql 언제 쓰나, mongodb redis cassandra beginner, nosql 뭐가 다른가요, nosql basics basics, nosql basics beginner, nosql basics intro, database basics, beginner database

## 핵심 개념

NoSQL(Not Only SQL)은 **관계형 DB(RDB)의 테이블·외래키·고정 스키마 대신, 다양한 데이터 모델을 선택할 수 있는 DB 유형의 총칭**이다.

왜 등장했는가? 2000년대 중반 이후 SNS와 검색 엔진처럼 수억 건의 데이터를 다루는 서비스가 늘면서, RDB의 수직 확장(더 좋은 서버) 방식이 한계에 부딪혔다. NoSQL은 서버를 여러 대로 늘리는 수평 확장(scale-out)을 기본 전제로 설계됐다.

입문자가 자주 헷갈리는 지점:

- "NoSQL이 항상 더 빠르다"는 아니다 — 단순 키 조회는 빠르지만, 복잡한 관계를 다루려면 애플리케이션에서 직접 조인 논리를 구현해야 해 오히려 복잡해질 수 있다.
- RDB를 대체하는 것이 아니라 **다른 문제를 위한 다른 도구**다.

## 한눈에 보기 — 주요 NoSQL 유형

| 유형 | 데이터 구조 | 대표 제품 | 주요 사용 사례 |
|---|---|---|---|
| Key-Value | 키 하나에 값 하나 | Redis, DynamoDB | 세션 저장, 캐시, 순위표 |
| Document | JSON/BSON 형태의 문서 | MongoDB, CouchDB | 유연한 속성의 콘텐츠, 카탈로그 |
| Column-family | 열 그룹 단위 저장 | Cassandra, HBase | 시계열 데이터, 이벤트 로그 |
| Graph | 노드와 엣지 | Neo4j, Amazon Neptune | 추천, 소셜 네트워크, 지식 그래프 |

## 상세 분해

**Key-Value 스토어**

가장 단순한 구조다. 임의의 키로 값을 저장하고 꺼낸다. 값은 문자열, JSON, 바이너리 등 무엇이든 가능하다. 구조가 단순한 만큼 조회 패턴도 단순해야 한다 — "이 키에 해당하는 값을 줘" 외에 복잡한 조건 검색은 지원이 약하다.

**Document DB**

JSON과 유사한 형태로 데이터를 저장한다. RDB에서 여러 테이블에 나뉘어 있던 데이터를 하나의 문서 안에 중첩해서 담을 수 있다. 스키마가 고정되지 않아 필드를 자유롭게 추가·변경할 수 있다. 단, 중첩 문서를 업데이트할 때 일관성 관리가 복잡해질 수 있다.

**Column-family DB**

행 키(row key) + 시간/이벤트 순으로 대량 쓰기가 발생하는 시계열·로그 데이터에 적합하다. 특정 열 그룹만 읽는 작업에서 I/O를 줄일 수 있다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "NoSQL은 트랜잭션이 없다" | MongoDB 4.x+는 멀티 도큐먼트 트랜잭션을 지원하고, RDB보다 제약이 강하지 않을 뿐 완전히 없는 것은 아니다 | 어떤 일관성 보장이 필요한지 먼저 파악하고 DB를 고른다 |
| "NoSQL이면 스키마가 아예 없어도 된다" | 스키마가 없어도 애플리케이션 코드가 암묵적 스키마 역할을 한다 | 필드 이름과 타입 규칙을 팀에서 관리하고 문서화한다 |
| "확장이 필요하면 무조건 NoSQL" | 수평 확장이 필요한 경우에도 RDB 샤딩·복제로 해결 가능한 경우가 많다 | 현재 데이터 구조와 조회 패턴이 RDB 모델에 맞으면 RDB를 유지하는 편이 낫다 |

## 실무에서 쓰는 모습

**(1) Redis로 세션 저장** — 웹 서버가 여러 대일 때 세션 정보를 각 서버 메모리가 아닌 Redis(Key-Value)에 두면 어떤 서버에 요청이 와도 같은 세션을 읽을 수 있다.

**(2) MongoDB로 동적 속성 상품 저장** — 의류, 가전, 식품처럼 속성이 서로 다른 상품을 하나의 Document에 담으면 RDB에서 불필요한 NULL 열이 수십 개 생기는 것을 피할 수 있다.

## 더 깊이 가려면

- 복제·샤딩 등 분산 DB 아키텍처 → [MVCC, Replication, Sharding](./mvcc-replication-sharding.md)

cross-category bridge:

- Spring Data Redis, Spring Data MongoDB 같은 추상화를 어떻게 사용하는지는 spring 카테고리 참고

## 면접/시니어 질문 미리보기

> Q: RDB와 NoSQL 중 어떤 기준으로 선택하나요?
> 의도: "유행을 따라" 선택하지 않고 트레이드오프를 따지는지 확인
> 핵심: 데이터 간 관계가 복잡하고 ACID 트랜잭션이 중요하다면 RDB, 단순한 조회 패턴에 수평 확장이 중요하거나 스키마가 자주 바뀐다면 NoSQL을 검토한다.

> Q: NoSQL은 왜 조인이 어려운가요?
> 의도: 분산 환경에서 관계 처리의 비용을 이해하는지 확인
> 핵심: NoSQL은 데이터를 여러 노드에 분산 저장하는 것을 전제로 하는데, 여러 노드에 흩어진 데이터를 조인하려면 네트워크 I/O가 크게 늘어 성능이 나빠진다.

## 한 줄 정리

NoSQL은 고정 스키마와 조인 대신 유연한 데이터 모델과 수평 확장을 선택한 DB 유형이고, RDB를 대체하는 것이 아니라 데이터 구조와 확장 요구에 따라 적합한 도구를 고르는 선택지다.

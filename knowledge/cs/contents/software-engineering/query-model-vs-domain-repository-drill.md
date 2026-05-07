---
schema_version: 3
title: Query Model vs Domain Repository Drill
concept_id: software-engineering/query-model-vs-domain-repository-drill
canonical: false
category: software-engineering
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
review_feedback_tags:
- query-model
- read-model
- domain-repository-boundary
- review-drill
aliases:
- query model vs domain repository drill
- read model repository drill
- 조회 모델 도메인 repository 구분
- 화면 조회 repository 분리 드릴
- CQRS beginner drill
symptoms:
- 화면 조회 요구 때문에 domain repository method가 계속 커진다
- aggregate 저장 계약과 목록 화면 join/query contract를 같은 interface에 둔다
- query repository를 쓰면 CQRS를 과하게 하는 것인지 헷갈린다
intents:
- drill
- comparison
- design
prerequisites:
- software-engineering/query-model-separation-read-heavy
- design-pattern/repository-boundary-aggregate-vs-read-model
next_docs:
- design-pattern/repository-boundary-aggregate-vs-read-model
- software-engineering/pageable-service-contract-vs-query-model-pagination-bridge
- database/sql-join-cardinality-mission-drill
linked_paths:
- contents/software-engineering/query-model-separation-read-heavy-apis.md
- contents/design-pattern/repository-boundary-aggregate-vs-read-model.md
- contents/software-engineering/pageable-service-contract-vs-query-model-pagination-bridge.md
- contents/database/sql-join-cardinality-mission-drill.md
- contents/software-engineering/repository-interface-return-type-drill.md
confusable_with:
- design-pattern/repository-boundary-aggregate-vs-read-model
- software-engineering/query-model-separation-read-heavy
- database/sql-join-cardinality-mission-drill
forbidden_neighbors:
- contents/database/index-basics.md
expected_queries:
- query model과 domain repository를 미션 코드로 구분하는 드릴을 줘
- 화면 조회 DTO 때문에 repository가 커지는 문제를 연습하고 싶어
- CQRS까지는 아니어도 read repository를 둘 수 있는지 문제로 판단해줘
- aggregate 저장 계약과 목록 조회 계약을 나누는 기준을 알려줘
contextual_chunk_prefix: |
  이 문서는 query model vs domain repository drill이다. 화면 목록 DTO,
  join 결과, pagination, aggregate 저장 계약, read model 분리, query
  repository를 둘지 고민하는 학습자 질문을 판별 문제로 매핑한다.
---
# Query Model vs Domain Repository Drill

> 한 줄 요약: domain repository는 "규칙을 이어서 판단할 aggregate를 복원한다"에 가깝고, query model은 "화면이나 API가 읽기 좋은 모양으로 조합한다"에 가깝다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "목록 화면 때문에 repository method가 너무 많아져요" | roomescape 관리자 예약 목록에서 member, theme, time 이름을 한 번에 보여주는 조회 | 저장 계약과 화면 조회 계약을 분리할 수 있는지 본다 |
| "같은 DB인데 query repository를 따로 두면 과한가요?" | shopping-cart 주문 상세 화면이 order, item, product를 조합해 DTO로 반환하는 흐름 | 물리 DB 분리보다 read contract 분리가 핵심이다 |
| "aggregate에 화면용 필드를 붙이면 편하지 않나요?" | domain object에 displayName, itemCountLabel 같은 응답 전용 값이 늘어나는 구조 | write model이 read shape에 끌려가는지 확인한다 |

**난이도: Beginner**

## 문제 1

상황:

```text
ReservationRepository.findAll()이 Reservation aggregate 대신 AdminReservationListItem을 반환한다.
```

답:

목록 화면 전용 조회라면 query repository로 이름과 위치를 분리하는 편이 낫다. domain repository처럼 두면 저장 계약과 화면 조합 계약이 섞인다.

## 문제 2

상황:

```text
OrderService.cancel(orderId)는 Order aggregate를 복원해 취소 가능 규칙을 검사한다.
```

답:

domain repository 쪽에 가깝다. 취소 규칙을 판단하려면 읽기 편한 DTO보다 domain state와 invariant가 중요하다.

## 문제 3

상황:

```text
GET /orders/{id}는 주문 기본 정보, item 이름, 총액, 배송 상태 label을 한 번에 반환한다.
```

답:

query model 후보가 강하다. 저장소가 aggregate를 완성해서 rule을 판단하는 흐름이 아니라 화면 응답을 조합하는 읽기 요구다.

## 빠른 체크

| 질문 | 가까운 쪽 |
|---|---|
| domain rule을 이어서 판단하는가 | domain repository |
| 화면 DTO shape가 먼저 보이는가 | query model |
| pagination/sort/join 최적화가 핵심인가 | query repository |
| invariant 보존이 핵심인가 | aggregate repository |

---
schema_version: 3
title: Repository Interface Return Type Drill
concept_id: software-engineering/repository-interface-return-type-drill
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
- repository-interface-contract
- return-type-boundary
- entity-leak
- review-drill
aliases:
- repository return type drill
- repository interface return type
- repository가 entity dto domain 중 뭘 반환해
- 저장소 반환 타입 경계 드릴
- domain repository return contract drill
symptoms:
- repository interface가 JPA Entity, DTO, domain model 중 무엇을 반환해야 하는지 헷갈린다
- domain service가 persistence entity를 받아 business rule을 검사한다
- 조회 화면 DTO와 domain 저장 계약을 같은 repository method로 섞는다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- software-engineering/repository-interface-contract
- software-engineering/repository-dao-entity
next_docs:
- spring/data-vs-domain-repository-bridge
- software-engineering/persistence-adapter-mapping-checklist
- software-engineering/repository-dao-boundary-review-drill
linked_paths:
- contents/software-engineering/repository-interface-contract-primer.md
- contents/software-engineering/repository-dao-entity.md
- contents/spring/spring-data-vs-domain-repository-bridge.md
- contents/software-engineering/persistence-adapter-mapping-checklist.md
- contents/software-engineering/repository-dao-boundary-review-drill.md
confusable_with:
- software-engineering/repository-dao-entity
- software-engineering/repository-interface-contract
- spring/data-vs-domain-repository-bridge
forbidden_neighbors:
- contents/software-engineering/repository-fake-design-guide.md
expected_queries:
- Repository interface가 Entity와 Domain 중 무엇을 반환해야 하는지 드릴로 풀어줘
- 저장소 반환 타입 때문에 service가 JPA Entity를 알게 되는 코드 리뷰 문제를 내줘
- query DTO 반환과 domain repository 반환을 어떻게 구분하는지 연습하고 싶어
- repository contract return type을 미션 코드 예제로 판단해줘
contextual_chunk_prefix: |
  이 문서는 repository interface return type drill이다. domain repository가
  JPA Entity를 반환함, response DTO를 저장소 계약에 섞음, query model과
  domain model을 구분하지 못함, adapter mapping 위치가 흐림 같은 리뷰
  문장을 반환 타입 경계 판별 문제로 매핑한다.
---
# Repository Interface Return Type Drill

> 한 줄 요약: repository 반환 타입은 "누가 이 값을 소비하는가"로 먼저 판단한다. domain service가 쓰는 저장 계약이면 domain model에 가까워야 하고, 화면 조회 전용이면 query model임을 이름과 위치로 드러내야 한다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "Repository가 Entity를 반환하면 안 되나요?" | roomescape service가 `ReservationJpaEntity`로 중복 예약 규칙을 검사하는 코드 | domain service가 persistence shape를 알아야 하는지 본다 |
| "목록 화면 DTO를 repository에서 바로 반환하고 싶어요" | 관리자 예약 목록이나 주문 목록 조회에서 join 결과를 response 모양으로 읽는 코드 | domain repository인지 query repository인지 역할을 분리한다 |
| "interface 계약과 adapter mapping 위치가 헷갈려요" | persistence adapter가 Entity를 domain으로 복원하지 않고 그대로 위로 올리는 구조 | mapping은 adapter 경계 안쪽에 둘 수 있는지 확인한다 |

**난이도: Beginner**

## 문제 1

상황:

```text
ReservationService.create()가 ReservationJpaEntity를 받아 예약 가능 여부를 검사한다.
```

답:

경계가 샌다. business rule 판단은 domain model이나 domain value로 하는 편이 좋고, JPA Entity는 persistence adapter 안에서 domain으로 복원하는 후보로 본다.

## 문제 2

상황:

```text
ReservationRepository.findAllForAdminPage()가 AdminReservationResponse를 반환한다.
```

답:

조회 전용 query model이라면 가능하지만 domain repository 계약처럼 이름 붙이면 혼란스럽다. 화면 조회 최적화라면 `ReservationQueryRepository` 같은 경계를 드러낸다.

## 문제 3

상황:

```text
OrderRepository.findById()가 Order와 OrderLine을 완성한 domain aggregate를 반환한다.
```

답:

domain service가 주문 규칙을 이어서 판단해야 한다면 자연스럽다. 이때 JPA fetch 전략은 adapter 내부 세부사항으로 숨기는 편이 좋다.

## 빠른 체크

| 반환 타입 | 먼저 의심할 경계 |
|---|---|
| JPA Entity | persistence 세부 누수 |
| Domain model | domain repository 계약 |
| Response DTO | query/read model |
| Raw row/map | DAO 또는 adapter 내부 |

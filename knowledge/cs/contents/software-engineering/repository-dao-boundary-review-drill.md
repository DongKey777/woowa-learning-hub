---
schema_version: 3
title: Repository / DAO Boundary Review Drill
concept_id: software-engineering/repository-dao-boundary-review-drill
canonical: false
category: software-engineering
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- repository-dao-boundary
- persistence-boundary
- review-drill
- adapter-mapping
aliases:
- repository dao boundary drill
- Repository DAO 구분 드릴
- 저장소 경계 리뷰 드릴
- repository adapter mapping drill
- DAO Repository 책임 구분
symptoms:
- Repository와 DAO를 이름만 다르게 붙이고 같은 책임으로 쓰고 있다
- 도메인 repository가 SQL shape나 JPA Entity shape를 그대로 노출한다
- 리뷰에서 "저장소 계약과 구현을 나눠 보라"는 말을 받았지만 수정 방향이 흐리다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- software-engineering/repository-dao-entity
- software-engineering/repository-interface-contract
next_docs:
- software-engineering/roomescape-dao-vs-repository-bridge
- spring/data-vs-domain-repository-bridge
- software-engineering/persistence-adapter-mapping-checklist
linked_paths:
- contents/software-engineering/repository-dao-entity.md
- contents/software-engineering/repository-interface-contract-primer.md
- contents/software-engineering/roomescape-dao-vs-repository-bridge.md
- contents/spring/spring-data-vs-domain-repository-bridge.md
- contents/software-engineering/persistence-adapter-mapping-checklist.md
- contents/software-engineering/repository-naming-smells-primer.md
confusable_with:
- software-engineering/repository-dao-entity
- software-engineering/repository-interface-contract
- spring/data-vs-domain-repository-bridge
forbidden_neighbors:
- contents/software-engineering/repository-fake-design-guide.md
expected_queries:
- Repository와 DAO 책임을 리뷰 문제로 짧게 연습하고 싶어
- 도메인 repository가 Entity나 SQL을 노출하면 왜 경계가 새는지 문제로 풀어줘
- roomescape DAO 피드백을 Repository 계약과 구현체 구분으로 다시 보고 싶어
- JpaRepository와 domain Repository interface를 헷갈리는 코드 리뷰 드릴을 줘
contextual_chunk_prefix: |
  이 문서는 Repository / DAO boundary review drill이다. Repository interface,
  DAO, JPA adapter, Entity leak, SQL shape 노출, roomescape DAO 피드백 같은
  자연어 질문을 저장소 계약과 persistence 구현 경계 구분 문제로 매핑한다.
---
# Repository / DAO Boundary Review Drill

> 한 줄 요약: Repository는 도메인이 기대하는 저장 계약이고, DAO/JPA adapter는 그 계약을 DB 기술로 수행하는 구현 쪽이다.

**난이도: Beginner**

## 문제 1

상황:

```text
OrderService가 OrderJpaEntity를 받아서 business rule을 검사한다.
```

답:

경계가 샌다. Service가 도메인 규칙을 판단한다면 `Order` 같은 도메인 모델을 받아야 하고, JPA Entity 변환은 persistence adapter 안에 두는 편이 안전하다.

## 문제 2

상황:

```text
ReservationRepository.findAllForListPage()가 SELECT 절과 join fetch 전략을 이름에 드러낸다.
```

답:

조회 모델 목적이 강하면 query repository나 DAO로 분리할 수 있다. 도메인 repository 계약처럼 보이게 두면 저장 계약과 화면 조회 최적화가 섞인다.

## 문제 3

상황:

```text
Roomescape 미션에서 "DAO 패턴을 써 보라"는 요구를 듣고 모든 Repository 이름을 DAO로 바꿨다.
```

답:

이름 치환이 아니라 책임 분리가 핵심이다. SQL/row mapping을 직접 다루는 접근 객체인지, 도메인 저장 계약인지 먼저 나눈다.

## 빠른 체크

| 질문 | 경계 판단 |
|---|---|
| 안쪽 코드가 SQL column 이름을 아는가 | DAO/adapter 누수 |
| domain이 `JpaRepository`를 직접 의존하는가 | framework 의존 누수 |
| 화면 전용 join 결과를 domain repository가 반환하는가 | query model 분리 후보 |
| fake로 계약을 재현하고 싶은가 | repository interface contract 질문 |

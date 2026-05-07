---
schema_version: 3
title: Domain / Entity / Response Mapping Review Drill
concept_id: software-engineering/domain-entity-response-mapping-review-drill
canonical: false
category: software-engineering
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/baseball
- missions/blackjack
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- mapping-boundary
- dto-vo-entity
- response-model
- persistence-leakage
aliases:
- domain entity response mapping drill
- DTO Entity Domain 매핑 드릴
- response mapping review drill
- Entity 그대로 반환 드릴
- 도메인 복원 매핑 리뷰
symptoms:
- Entity를 그대로 API response로 반환한다
- DTO, VO, Entity, Domain을 이름만 다르게 만들고 변환 기준이 없다
- 도메인 결과 의미와 출력 문구가 한 클래스에 섞인다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- software-engineering/dto-vo-entity-basics
- software-engineering/persistence-model-leakage
next_docs:
- software-engineering/baseball-turn-result-response-boundary-bridge
- software-engineering/blackjack-turn-result-response-boundary-bridge
- software-engineering/persistence-adapter-mapping-checklist
linked_paths:
- contents/software-engineering/dto-vo-entity-basics.md
- contents/software-engineering/persistence-model-leakage-anti-patterns.md
- contents/software-engineering/baseball-turn-result-response-boundary-bridge.md
- contents/software-engineering/blackjack-turn-result-response-boundary-bridge.md
- contents/software-engineering/persistence-adapter-mapping-checklist.md
- contents/spring/spring-controller-entity-return-vs-dto-return-primer.md
confusable_with:
- software-engineering/dto-vo-entity-basics
- software-engineering/persistence-model-leakage
- software-engineering/persistence-adapter-mapping-checklist
forbidden_neighbors:
- contents/software-engineering/repository-fake-design-guide.md
expected_queries:
- Entity를 그대로 response로 반환하는 문제를 드릴로 풀어줘
- Domain Entity DTO VO 매핑 책임을 리뷰 문제로 연습하고 싶어
- baseball 결과 문구와 도메인 결과를 어떻게 나눠야 하는지 문제로 보여줘
- 도메인 복원과 응답 매핑이 섞인 코드를 어떻게 판단해?
contextual_chunk_prefix: |
  이 문서는 Domain, Entity, Response DTO mapping boundary를 연습하는 review
  drill이다. Entity 그대로 반환, 도메인 복원, DTO/VO/Entity 혼동, 결과 문구와
  도메인 결과 의미 혼합 같은 미션 리뷰 피드백을 매핑 책임 분리 문제로 연결한다.
---
# Domain / Entity / Response Mapping Review Drill

> 한 줄 요약: Entity는 저장 모양, Domain은 규칙과 의미, Response는 바깥 표현을 맡으므로 변환은 귀찮은 의식이 아니라 변경 이유를 나누는 경계다.

**난이도: Beginner**

## 문제 1

```text
ReservationEntity를 controller가 그대로 JSON으로 반환한다.
```

답:

저장 구조가 API 계약으로 새는 신호다. response DTO를 두고, 필요한 필드와 표현만 선택한다.

## 문제 2

```text
BaseballGameResult가 "3볼 1스트라이크" 한국어 문장을 직접 만든다.
```

답:

도메인 결과 의미와 출력 표현이 섞인다. Domain은 strike/ball/nothing 의미를 닫고, view/response가 문장으로 바꾼다.

## 문제 3

```text
Repository가 Entity를 반환하고 Service가 Entity를 Domain으로 복원한다.
```

답:

구조에 따라 가능하지만, Service가 persistence mapping을 계속 알게 되면 adapter 책임이 새는지 점검해야 한다.

## 구분표

| 이름 | 주된 변경 이유 |
|---|---|
| Entity | table, ORM mapping, fetch strategy |
| Domain | business rule, invariant, state transition |
| Response DTO | API field, status, client contract |
| View model | 화면 표현, 문구, formatting |

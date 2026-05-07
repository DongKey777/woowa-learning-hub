---
schema_version: 3
title: Mission Review Vocabulary Primer
concept_id: software-engineering/mission-review-vocabulary-primer
canonical: true
category: software-engineering
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 91
mission_ids:
- missions/baseball
- missions/blackjack
- missions/lotto
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- mission-review-vocabulary
- responsibility-boundary-glossary
- dto-entity-service-transaction-validation
aliases:
- mission review vocabulary primer
- PR review glossary beginner
- domain rule DTO entity repository service validation transaction
- 리뷰 용어 입문
- 코드리뷰 용어 정리
- 우테코 리뷰 용어
- domain rule 뭐예요
- service repository 차이
- transaction 경계 입문
symptoms:
- 리뷰 용어를 사전식 정의로만 읽고 실제 코드 위치와 책임 경계로 번역하지 못한다
- DTO Entity Service Repository Validation Transaction 코멘트를 각각 별개로 외워 수정 순서가 흐려진다
- domain rule이 controller나 repository에 새어 있다는 말을 어떤 코드 이동으로 받아야 할지 모른다
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- software-engineering/woowacourse-backend-mission-prerequisite-primer
next_docs:
- software-engineering/refactoring-feedback-phrase-router
- software-engineering/layered-architecture-basics
- software-engineering/service-layer-basics
- software-engineering/dto-vo-entity-basics
linked_paths:
- contents/software-engineering/refactoring-feedback-phrase-router.md
- contents/software-engineering/woowacourse-backend-mission-prerequisite-primer.md
- contents/software-engineering/layered-architecture-basics.md
- contents/software-engineering/service-layer-basics.md
- contents/software-engineering/dto-vo-entity-basics.md
- contents/software-engineering/repository-dao-entity.md
confusable_with:
- software-engineering/refactoring-feedback-phrase-router
- software-engineering/layered-architecture-basics
- software-engineering/service-layer-basics
- software-engineering/dto-vo-entity-basics
- software-engineering/repository-dao-entity
forbidden_neighbors: []
expected_queries:
- PR 리뷰에서 domain rule DTO entity repository service validation transaction은 어떤 책임 경계를 말해?
- 리뷰 용어를 코드 위치로 번역하려면 Controller Service Repository 중 어디를 봐야 해?
- domain rule이 controller에 새어 있다는 코멘트는 어떤 수정 방향을 뜻해?
- DTO와 Entity 경계가 모호하다는 리뷰를 초보자가 어떻게 해석해야 해?
- transaction 범위와 validation 위치를 리뷰 피드백에서 어떻게 읽어야 해?
contextual_chunk_prefix: |
  이 문서는 mission review vocabulary beginner primer로, domain rule, DTO,
  entity, repository, service, validation, transaction 같은 PR 리뷰 용어를
  코드 책임 위치와 수정 방향으로 번역한다.
---
# Mission Review Vocabulary Primer

> 한 줄 요약: PR 리뷰에서 자주 나오는 `domain rule`, `DTO`, `entity`, `repository`, `service`, `validation`, `transaction`은 "코드를 어디에 두고 무엇을 지킬지"를 말하는 단어이며, 용어 뜻보다 책임 경계를 먼저 잡으면 훨씬 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [리팩토링 피드백 문장 라우터](./refactoring-feedback-phrase-router.md)
- [우테코 백엔드 미션 선행 개념 입문](./woowacourse-backend-mission-prerequisite-primer.md)
- [계층형 아키텍처 기초](./layered-architecture-basics.md)
- [Service 계층 기초](./service-layer-basics.md)
- [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)
- [Repository, DAO, Entity](./repository-dao-entity.md)
- [software-engineering 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: mission review vocabulary primer, pr review glossary beginner, domain rule dto entity repository service validation transaction, 리뷰 용어 입문, 코드리뷰 용어 정리, 우테코 리뷰 용어, domain rule 뭐예요, service repository 차이, transaction 경계 입문, validation 위치, dto entity 구분 초심자, mission review vocabulary primer basics, mission review vocabulary primer beginner, mission review vocabulary primer intro, software engineering basics

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "리뷰에서 도메인 규칙이 새어 있다고 하는데 무슨 뜻이에요?" | controller나 DTO 검증에 비즈니스 규칙이 섞인 코드 | 리뷰 용어를 사전식 뜻이 아니라 책임 위치 신호로 번역한다 |
| "DTO, entity, repository, service가 다 비슷하게 보여요" | roomescape, shopping-cart, lotto에서 값 이동과 저장 책임이 한 클래스에 몰린 구조 | 각 단어가 어느 계층 경계를 가리키는지 먼저 나눈다 |
| "transaction 경계를 보라는 리뷰가 왜 validation 얘기랑 같이 나와요?" | 저장 전 검증, 저장 후 후속 처리, 실패 rollback이 한 흐름에 섞인 유스케이스 | 입력 검증, 도메인 규칙, 저장 원자성을 다른 축으로 읽는다 |

## 먼저 잡는 한 줄 멘탈 모델

리뷰 용어는 어려운 이론 이름이 아니라, **"이 변경의 책임이 어느 계층에 있어야 하는지"를 빠르게 가리키는 좌표**다.

## 30초 번역표

| 용어 | 리뷰에서 보통 의미 | 초심자 번역 |
|---|---|---|
| domain rule | 비즈니스에서 반드시 지켜야 하는 규칙 | "서비스 정책/업무 규칙" |
| DTO | 계층 사이에서 주고받는 데이터 모양 | "전달용 봉투" |
| entity | 식별자로 추적되는 핵심 상태 객체 | "ID로 관리되는 핵심 객체" |
| repository | 저장/조회 접근을 감싸는 경계 | "저장소 창구" |
| service | 유스케이스 순서와 트랜잭션을 조립 | "업무 흐름 조립자" |
| validation | 입력/상태가 조건을 만족하는지 검사 | "조건 검사" |
| transaction | 여러 DB 변경을 한 덩어리로 처리 | "같이 성공/실패 묶음" |

## 용어를 코드 위치로 바꾸어 보기

| 용어 | 주로 놓는 위치 | 보통 리뷰 코멘트 |
|---|---|---|
| domain rule | domain 객체/도메인 서비스 | "규칙이 controller에 새어 있어요" |
| DTO | controller 경계, API 입출력 | "entity를 그대로 응답하지 말아 주세요" |
| entity | domain + persistence 경계 | "엔티티 책임이 너무 많아요" |
| repository | service 아래 저장 경계 | "서비스가 SQL/JPA 세부를 너무 알아요" |
| service | 유스케이스 조립 계층 | "서비스가 단순 위임만 하거나 반대로 god class예요" |
| validation | 입력 경계 + 도메인 불변식 | "검증 위치가 섞여 있어요" |
| transaction | service 유스케이스 단위 | "트랜잭션 경계가 너무 넓거나 좁아요" |

## before / after 한눈 비교

| 상태 | 리뷰 코멘트 읽는 방식 | 결과 |
|---|---|---|
| before: 용어를 사전처럼만 읽음 | `DTO`, `transaction`, `domain rule`을 각각 따로 외운다 | 코멘트는 이해한 것 같은데 실제 코드에서 어디를 고쳐야 하는지 흐려진다 |
| after: 책임 위치로 번역해서 읽음 | "이 용어가 Controller/Service/Repository 어디를 말하는가?"부터 확인한다 | 리뷰 코멘트를 수정 포인트로 바로 바꿀 수 있어 반영 속도가 빨라진다 |

## 작은 예시: 리뷰 코멘트 해석하기

리뷰 코멘트 원문:

`domain rule이 service 바깥으로 새어 있고 DTO/entity 경계가 모호합니다. validation 위치와 transaction 범위를 다시 보세요.`

초심자 해석:

1. 규칙 로직이 controller나 repository에 흩어져 있다.
2. 요청/응답 DTO와 entity를 섞어 써서 변경 영향이 커진다.
3. 입력 검증과 도메인 규칙 검증 위치가 섞여 있다.
4. `@Transactional`을 "한 유스케이스" 기준으로 다시 묶어야 한다.

## 흔한 오해와 빠른 교정

- "`service`에 모든 규칙을 넣으면 된다"
  - 교정: 서비스는 흐름 조립자다. 객체 스스로 지킬 수 있는 규칙은 도메인 안으로 넣는 편이 안전하다.
- "`DTO`가 귀찮으니 `entity`를 그대로 API로 내보내도 된다"
  - 교정: 처음엔 빠르지만 API 계약이 DB 구조에 묶여 이후 수정 비용이 커진다.
- "`validation`은 어딘가 한 번만 하면 된다"
  - 교정: 입력 형식 검증과 도메인 불변식 검증은 목적이 다르다. 보통 둘 다 필요하다.
- "`transaction`은 길수록 안전하다"
  - 교정: 길수록 락/대기 비용이 커진다. 유스케이스 완료에 필요한 최소 범위로 잡는 편이 낫다.

## 리뷰 코멘트가 왔을 때 4-step 체크

1. `입력`과 `규칙`이 섞였는지 본다. (`controller`에 정책 `if`가 많은가?)
2. `DTO`와 `entity`를 같은 타입으로 재사용하는지 본다.
3. `validation`이 입력 형식 검사인지, 도메인 불변식 검사인지 분리해서 본다.
4. `transaction` 범위가 한 유스케이스 완료 단위인지 확인한다.

## 안전한 다음 한 걸음

- 리뷰 문장이 `추상화가 어색해요`, `책임이 섞였어요`, `테스트가 너무 무거워요`처럼 바로 수정 방향으로 안 읽히면 [리팩토링 피드백 문장 라우터](./refactoring-feedback-phrase-router.md)에서 먼저 primer와 첫 행동을 고른다.
- service/repository 책임이 막히면 [Service 계층 기초](./service-layer-basics.md)
- DTO/entity 구분이 막히면 [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)
- repository 경계가 막히면 [Repository, DAO, Entity](./repository-dao-entity.md)
- 전체 그림을 다시 맞추려면 [계층형 아키텍처 기초](./layered-architecture-basics.md)

## 한 줄 정리

리뷰 용어를 외우려 하지 말고, 각 단어를 "코드 책임 위치"로 번역하면 PR 피드백을 훨씬 빠르게 반영할 수 있다.

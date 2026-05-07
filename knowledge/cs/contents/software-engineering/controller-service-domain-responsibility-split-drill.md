---
schema_version: 3
title: Controller / Service / Domain Responsibility Split Drill
concept_id: software-engineering/controller-service-domain-responsibility-split-drill
canonical: false
category: software-engineering
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/baseball
- missions/lotto
- missions/blackjack
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- responsibility-boundary
- service-layer
- domain-invariant
- controller-slimming
aliases:
- controller service domain split drill
- 계층 책임 분리 드릴
- controller service domain responsibility
- controller가 너무 많은 걸 알아요
- service domain boundary exercise
symptoms:
- Controller가 도메인 규칙을 조합하고 Service는 단순 전달자처럼 남아 있다
- Service가 모든 if를 품고 Domain 객체는 getter 묶음처럼 보인다
- 리뷰에서 "책임을 객체 쪽으로 보내라"는 말을 받았지만 어느 계층으로 옮길지 모른다
intents:
- drill
- troubleshooting
- design
prerequisites:
- software-engineering/service-layer-basics
- software-engineering/layered-architecture-basics
next_docs:
- software-engineering/readable-code-layering-test-feedback-loop-primer
- software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
- software-engineering/oop-design-basics
linked_paths:
- contents/software-engineering/service-layer-basics.md
- contents/software-engineering/layered-architecture-basics.md
- contents/software-engineering/readable-code-layering-test-feedback-loop-primer.md
- contents/software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md
- contents/software-engineering/oop-design-basics.md
- contents/software-engineering/mission-review-vocabulary-primer.md
confusable_with:
- software-engineering/service-layer-basics
- software-engineering/layered-architecture-basics
- software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
forbidden_neighbors:
- contents/design-pattern/god-object-spaghetti-golden-hammer.md
expected_queries:
- Controller Service Domain 책임 분리를 문제로 연습하고 싶어
- controller가 도메인 규칙을 알아버리는 리뷰 피드백을 드릴로 풀어줘
- Service가 너무 커졌을 때 어떤 책임을 domain으로 옮길지 연습하고 싶어
- 입력 검증과 도메인 불변식과 유스케이스 흐름을 어떻게 나눠?
contextual_chunk_prefix: |
  이 문서는 controller, service, domain responsibility split drill이다.
  controller가 너무 많은 걸 안다, service가 비대하다, domain invariant가
  밖으로 샌다, 계층 책임 분리 같은 리뷰 문장을 짧은 판별 문제로 연결한다.
---
# Controller / Service / Domain Responsibility Split Drill

> 한 줄 요약: Controller는 요청/응답 번역, Service는 유스케이스 순서, Domain은 규칙과 불변식을 책임지는 쪽으로 먼저 나눈다.

**난이도: Beginner**

## 문제 1

```text
Controller가 로또 번호 6개, 중복 없음, 1-45 범위를 모두 검사한다.
```

답:

형식 파싱은 Controller/DTO 근처에서 볼 수 있지만, "로또 번호의 유효한 상태"는 Domain 객체 생성 경계 안에 있어야 한다.

## 문제 2

```text
Service가 strike/ball 계산을 직접 하고 BaseballGame은 값만 들고 있다.
```

답:

게임 규칙이 Service로 올라왔다. Service는 한 턴 진행 순서를 조립하고, 판정 규칙은 Domain 객체나 policy로 내려야 한다.

## 문제 3

```text
Controller가 Entity를 그대로 응답으로 반환한다.
```

답:

요청/응답 표현과 persistence shape가 같이 새는 신호다. DTO 또는 response model로 표현 경계를 끊고, domain/entity 노출 이유를 다시 본다.

## 한눈 분기

| 책임 | 주로 둘 곳 |
|---|---|
| HTTP status, request binding, response DTO | Controller / adapter |
| 한 유스케이스의 순서, transaction boundary | Service / application layer |
| 값 규칙, 상태 전이, 불변식 | Domain |
| table, query, mapping strategy | Repository adapter / DAO |

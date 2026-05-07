---
schema_version: 3
title: Mission Test Slice Selection Drill
concept_id: software-engineering/mission-test-slice-selection-drill
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
- test-strategy
- slice-test
- integration-test
- mission-test-drill
aliases:
- mission test slice drill
- 테스트 슬라이스 선택 드릴
- unit integration acceptance test drill
- MockMvc DataJpaTest 선택
- 미션 테스트 전략 연습
symptoms:
- 모든 테스트를 통합 테스트로 만들거나 모든 테스트를 단위 테스트로만 만들려 한다
- Controller binding, Service rule, Repository query를 같은 테스트에서 한꺼번에 검증한다
- mock, fake, stub을 고르기 전에 어떤 경계를 테스트하는지 정하지 못한다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- software-engineering/test-strategy-basics
next_docs:
- software-engineering/inbound-adapter-test-slices-primer
- spring/spring-testing-basics
- software-engineering/hexagonal-testing-seams-primer
linked_paths:
- contents/software-engineering/test-strategy-basics.md
- contents/software-engineering/inbound-adapter-test-slices-primer.md
- contents/spring/spring-testing-basics.md
- contents/software-engineering/hexagonal-testing-seams-primer.md
- contents/software-engineering/testing-strategy-and-test-doubles.md
- contents/software-engineering/dummy-vs-stub-beginner-mini-card.md
confusable_with:
- software-engineering/test-strategy-basics
- software-engineering/inbound-adapter-test-slices-primer
- spring/spring-testing-basics
forbidden_neighbors:
- contents/software-engineering/repository-fake-design-guide.md
expected_queries:
- 미션 테스트를 unit slice integration 중 어디로 둘지 드릴로 풀어줘
- MockMvc DataJpaTest SpringBootTest 선택 기준을 문제로 연습하고 싶어
- controller binding과 service rule과 repository query를 어떤 테스트로 나눠?
- fake mock stub 고르기 전에 테스트 경계를 어떻게 정해?
contextual_chunk_prefix: |
  이 문서는 미션 테스트 전략을 unit, slice, integration 경계로 고르는 drill이다.
  MockMvc, DataJpaTest, SpringBootTest, service unit test, repository query,
  controller binding, test double 같은 표현을 테스트가 검증하려는 경계 기준으로
  매핑한다.
---
# Mission Test Slice Selection Drill

> 한 줄 요약: 테스트 종류는 도구 이름이 아니라 "지금 어느 경계의 계약을 검증하는가"로 먼저 고른다.

**난이도: Beginner**

## 문제 1

```text
Controller가 JSON body를 DTO로 받고 validation error를 400으로 바꾸는지 보고 싶다.
```

답:

Inbound adapter slice가 맞다. Spring MVC binding과 validation, exception handler를 보려면 MockMvc 계열 테스트가 자연스럽다.

## 문제 2

```text
Lotto 번호 6개, 중복 없음, 범위 규칙을 검증하고 싶다.
```

답:

Domain unit test가 먼저다. Spring context나 DB가 필요 없다.

## 문제 3

```text
Repository query가 실제 DB schema와 맞는지 보고 싶다.
```

답:

Repository slice나 integration 성격이 맞다. SQL, mapping, constraint를 보려면 in-memory fake보다 실제 DB와 가까운 환경을 고려한다.

## 문제 4

```text
예약 생성 API가 request부터 DB 저장까지 한 번에 이어지는지 보고 싶다.
```

답:

App integration test 후보지만, 이 테스트 하나로 모든 세부 규칙을 검증하려고 하면 무거워진다. 세부 규칙은 더 작은 테스트로 분리한다.

## 선택표

| 보고 싶은 것 | 먼저 고를 테스트 |
|---|---|
| 순수 도메인 규칙 | unit test |
| controller binding/status | inbound adapter slice |
| repository query/mapping | persistence slice |
| 여러 bean 협력과 transaction | app integration |

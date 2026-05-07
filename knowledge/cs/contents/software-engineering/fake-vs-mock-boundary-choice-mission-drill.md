---
schema_version: 3
title: Fake vs Mock Boundary Choice Mission Drill
concept_id: software-engineering/fake-vs-mock-boundary-choice-mission-drill
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
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- test-double
- fake-vs-mock
- repository-contract-test
- mission-drill
aliases:
- fake vs mock boundary drill
- fake mock stub mission drill
- 테스트 대역 선택 드릴
- repository fake contract drill
- mock interaction vs fake state drill
symptoms:
- mock, fake, stub을 도구 이름으로만 고르고 검증하려는 경계를 정하지 못한다
- repository fake가 실제 repository 계약과 다르게 동작해 service test가 거짓 안정감을 준다
- 외부 결제/메일 호출을 state fake로 둘지 interaction mock으로 볼지 헷갈린다
intents:
- drill
- comparison
- troubleshooting
prerequisites:
- software-engineering/fake-vs-mock-first-test-primer
- software-engineering/test-strategy-basics
next_docs:
- software-engineering/repository-fake-design-guide
- software-engineering/testing-strategy-and-test-doubles
- software-engineering/mission-test-slice-selection-drill
linked_paths:
- contents/software-engineering/fake-vs-mock-first-test-primer.md
- contents/software-engineering/repository-fake-design-guide.md
- contents/software-engineering/testing-strategy-and-test-doubles.md
- contents/software-engineering/mission-test-slice-selection-drill.md
- contents/software-engineering/api-contract-testing-consumer-driven.md
confusable_with:
- software-engineering/fake-vs-mock-first-test-primer
- software-engineering/repository-fake-design-guide
- software-engineering/mission-test-slice-selection-drill
forbidden_neighbors:
- contents/software-engineering/unit-testing-basics.md
expected_queries:
- fake와 mock을 미션 테스트 예제로 고르는 드릴을 줘
- repository fake가 실제 계약과 달라지는 문제를 어떻게 연습해?
- 외부 결제 client는 mock인지 fake인지 판단하는 문제를 내줘
- 테스트 대역을 도구가 아니라 boundary 기준으로 고르고 싶어
contextual_chunk_prefix: |
  이 문서는 fake vs mock boundary choice mission drill이다. repository fake,
  mock interaction verification, external payment client, state-based test,
  contract drift, stub response 같은 테스트 대역 질문을 검증 경계 기준으로
  매핑한다.
---
# Fake vs Mock Boundary Choice Mission Drill

> 한 줄 요약: fake와 mock은 취향이 아니라 "상태 계약을 재현할지, 호출 상호작용을 검증할지"로 고른다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "Repository는 fake로 만들면 되나요?" | roomescape service unit test에서 예약 저장/조회 상태를 메모리로 재현하는 상황 | 실제 repository contract와 같은 실패/조회 규칙을 fake가 지키는지 본다 |
| "결제 client는 mock으로 verify해야 하나요?" | shopping-cart checkout 뒤 외부 payment API가 한 번 호출됐는지 확인하는 테스트 | 상태보다 외부 port 호출 계약이 핵심인지 판단한다 |
| "stub 응답만 있으면 충분한가요?" | lotto 번호 generator를 고정값으로 바꿔 domain rule을 테스트하는 흐름 | 테스트가 필요한 것은 값 공급인지, 저장 상태인지, interaction인지 나눈다 |

**난이도: Beginner**

## 문제 1

상황:

```text
ReservationService 중복 예약 테스트에서 InMemoryReservationRepository를 쓴다.
```

답:

fake 후보가 맞다. 다만 실제 repository처럼 같은 date/time 중복 조회, id 부여, not found 동작을 맞춰야 service test가 의미 있다.

## 문제 2

상황:

```text
PaymentClient.approve()가 정확히 한 번 호출됐는지 보고 싶다.
```

답:

mock/spy 후보가 강하다. 외부 시스템에 전달했는지라는 interaction contract가 테스트 목적이면 호출 검증이 자연스럽다.

## 문제 3

상황:

```text
LottoNumberGenerator가 항상 [1,2,3,4,5,6]을 반환하게 한다.
```

답:

stub에 가깝다. 상태 저장이나 interaction보다 예측 가능한 입력값 공급이 목적이다.

## 빠른 체크

| 테스트 목적 | 먼저 볼 대역 |
|---|---|
| 저장/조회 상태 재현 | fake |
| 호출 여부/순서/횟수 검증 | mock/spy |
| 고정 응답 공급 | stub |
| 실제 DB 제약 확인 | fake보다 slice/integration |

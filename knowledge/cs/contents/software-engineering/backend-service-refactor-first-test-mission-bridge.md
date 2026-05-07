---
schema_version: 3
title: Backend Service Refactor First-Test Mission Bridge
concept_id: software-engineering/backend-service-refactor-first-test-mission-bridge
canonical: false
category: software-engineering
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: mixed
source_priority: 78
mission_ids:
- missions/backend
review_feedback_tags:
- backend
- service-refactor
- first-failing-test
- test-double
aliases:
- backend service refactor first test bridge
- backend service first failing test
- service 리팩터링 첫 테스트 미션 브리지
- fake repository service refactor bridge
- transaction boundary refactor first test
symptoms:
- service가 커졌다는 리뷰를 받았지만 첫 failing test를 어디에 둘지 고르지 못한다
- repository, payment client, notifier 협력이 섞여 unit test와 integration test 선택이 흔들린다
- mock 호출 순서부터 고정해서 리팩터링 자유도가 줄어든다
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- software-engineering/service-refactor-first-test-examples
- software-engineering/test-strategy-basics
next_docs:
- software-engineering/fake-vs-mock-first-test-primer
- software-engineering/testing-strategy-and-test-doubles
- software-engineering/service-layer-basics
linked_paths:
- contents/software-engineering/service-refactor-first-test-examples-pack.md
- contents/software-engineering/test-strategy-basics.md
- contents/software-engineering/fake-vs-mock-first-test-primer.md
- contents/software-engineering/testing-strategy-and-test-doubles.md
- contents/software-engineering/service-layer-basics.md
- contents/database/transaction-basics.md
confusable_with:
- software-engineering/service-refactor-first-test-examples
- software-engineering/fake-vs-mock-first-test-primer
- software-engineering/test-strategy-basics
forbidden_neighbors:
- contents/software-engineering/controller-service-domain-responsibility-split-drill.md
expected_queries:
- backend service refactor에서 첫 failing test를 어디에 둬야 해?
- service가 비대해졌다는 리뷰를 first failing test와 test double로 바꿔줘
- fake repository와 integration test 중 backend service 리팩터링 시작점은 어떻게 골라?
- 결제 승인 저장 알림 순서를 바꿀 때 어떤 테스트가 먼저 안전해?
- service refactor 미션 리뷰를 테스트 전략으로 연결해줘
contextual_chunk_prefix: |
  이 문서는 backend service refactor first-test mission_bridge다. service bloat,
  first failing test, fake repository, stub policy, spy notifier, transaction
  boundary, mock over-specification 같은 미션 리뷰 문장을 test strategy와
  service responsibility split로 매핑한다.
---
# Backend Service Refactor First-Test Mission Bridge

> 한 줄 요약: backend service 리팩터링은 "service를 쪼갠다"가 아니라, 바꾸려는 위험 1개를 먼저 실패시키는 테스트를 고르는 작업에서 시작한다.

**난이도: Intermediate**

## 미션 진입 증상

| backend 리뷰 장면 | 먼저 바꿀 질문 |
|---|---|
| service 메서드가 저장, 계산, 알림을 모두 한다 | 이번 변경에서 깨질 규칙은 무엇인가 |
| repository mock 호출 순서가 테스트 대부분을 차지한다 | 결과 규칙을 fake로 읽을 수 있는가 |
| 결제 승인 실패 후 저장 잔여가 걱정된다 | transaction boundary를 실제 repository로 확인해야 하는가 |
| notifier 호출 횟수가 문제다 | spy로 관찰할 협력 1개만 남길 수 있는가 |

## CS concept 매핑

backend service 리뷰를 CS 문서로 연결할 때는 아래 순서가 안전하다.

1. `service bloat`를 한 문장 위험으로 줄인다.
2. 위험이 값 결과인지, 저장 결과인지, 외부 협력 호출인지 나눈다.
3. 가장 싼 첫 failing test를 고른다.
4. test double은 질문에 필요한 최소 한 종류만 둔다.

| 위험 종류 | 먼저 붙일 테스트 | double 기본값 |
|---|---|---|
| 할인, 상태 전이, 검증 같은 순수 규칙 | unit test | stub 또는 직접 값 |
| repository 조회/저장 결과가 핵심 | service unit test | fake repository |
| DB rollback, unique constraint, transaction propagation | integration test | 실제 repository |
| 알림, 결제 client 호출 자체가 답 | unit 또는 slice test | spy/fake external client |

## 리뷰 신호 해석

- "service가 너무 많은 일을 해요"는 곧장 계층을 늘리라는 말이 아니라, 어떤 책임이 테스트 질문을 흐리는지 보라는 신호다.
- "mock이 너무 많아요"는 내부 호출 순서보다 결과 규칙을 읽을 수 있는 fake/stub 경계가 있는지 보라는 뜻이다.
- "트랜잭션은 어떻게 보장되나요?"는 unit test만으로는 저장 잔여 여부를 증명하기 어렵다는 신호다.
- "외부 호출 실패 시 어떻게 되나요?"는 fake client와 retry/idempotency 질문을 분리하라는 말이다.

## 빠른 판단 순서

```text
리뷰 문장 -> 위험 1개 -> 첫 failing test -> 필요한 double 1개 -> 리팩터링
```

예를 들어 `OrderService.confirm()`이 결제 승인, 주문 저장, 알림 전송을 모두 한다면 처음부터 세 collaborator를 mock으로 고정하지 않는다.
먼저 "승인 실패 시 주문이 저장되지 않는다"가 핵심이면 integration test를, "성공 시 알림이 한 번만 나간다"가 핵심이면 spy notifier를 둔다.
그 뒤 service 내부 구조를 나누면 테스트가 설계 변경을 방해하지 않는다.

## 한 줄 정리

backend service 리팩터링의 출발점은 새 클래스 이름이 아니라, 리뷰 문장을 가장 먼저 실패시킬 수 있는 테스트 질문 1개다.

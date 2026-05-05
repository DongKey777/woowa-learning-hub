---
schema_version: 3
title: Strategy vs State vs Policy Object 결정 가이드
concept_id: design-pattern/strategy-state-policy-object-decision-guide
canonical: false
category: design-pattern
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
  - state-vs-strategy-boundary
  - policy-object-vs-state
  - decision-object-naming
aliases:
  - strategy vs state vs policy object
  - 상태 패턴이냐 전략이냐 정책 객체냐
  - 실행 방법 vs 상태 전이 vs 도메인 규칙
  - if else를 객체로 나눴는데 이름이 안 잡힘
  - 결제 전략 상태 정책 객체 구분
  - 환불 규칙 객체와 상태 패턴 차이
symptoms:
  - 상태에 따라 달라지는데 strategy로 뺐더니 이름이 어색하다
  - 환불 규칙을 state로 만들었는데 전이가 없다
  - 결제 수단 선택과 주문 상태 전이를 같은 패턴으로 설명하고 있다
intents:
  - comparison
  - design
  - definition
prerequisites:
  - design-pattern/strategy-pattern-basics
  - design-pattern/state-pattern-workflow-payment
next_docs:
  - design-pattern/strategy-pattern-basics
  - design-pattern/state-pattern-workflow-payment
  - design-pattern/policy-object-pattern
linked_paths:
  - contents/design-pattern/strategy-vs-state-vs-policy-object.md
  - contents/design-pattern/strategy-pattern-basics.md
  - contents/design-pattern/state-pattern-workflow-payment.md
  - contents/design-pattern/policy-object-pattern.md
confusable_with:
  - design-pattern/strategy-pattern-basics
  - design-pattern/state-pattern-workflow-payment
  - design-pattern/policy-object-pattern
forbidden_neighbors:
  - contents/design-pattern/strategy-pattern-basics.md
  - contents/design-pattern/state-pattern-workflow-payment.md
expected_queries:
  - 결제 수단을 고르는 로직이랑 주문 상태 전이는 어떻게 다르게 봐야 해?
  - 환불 가능 여부를 판단하는 객체는 strategy보다 policy object가 더 맞아?
  - 지금 상태에서 가능한 행동이 달라질 때는 어떤 패턴으로 설명해?
  - 알고리즘 선택, 상태 변화, 규칙 판정을 한 번에 구분하는 기준이 뭐야?
  - if else를 객체로 쪼갰는데 strategy인지 state인지 이름을 못 정하겠어
contextual_chunk_prefix: |
  이 문서는 Strategy, State, Policy Object를 한 번에 헷갈리는 학습자에게
  세 선택지를 빠르게 가르게 돕는 chooser다. 실행 방법 교체, 현재 단계에
  따라 가능한 행동 변화, 허용 여부와 이유 판정, 결제 수단 선택, 주문 상태
  전이, 환불 가능 규칙 같은 자연어 paraphrase가 본 문서의 비교 기준에
  매핑된다.
---

# Strategy vs State vs Policy Object 결정 가이드

## 한 줄 요약

> 실행 방법을 갈아끼우면 Strategy, 현재 단계 때문에 가능한 행동이 달라지면 State, 허용 여부와 이유를 판정하면 Policy Object다.

## 결정 매트릭스

| 지금 코드가 답하는 질문 | 먼저 볼 패턴 | 왜 그쪽이 맞는가 |
|---|---|---|
| 이번 요청을 어떤 방식으로 처리할까? | Strategy | 같은 역할의 구현을 바꿔 끼우는 문제다. |
| 지금 상태에서 어떤 행동이 가능한가? | State | 전이 규칙과 허용 행동이 현재 단계에 묶여 있다. |
| 이 상황을 허용할지, 수수료나 이유를 어떻게 낼까? | Policy Object | 행동 수행보다 도메인 판정 결과가 중심이다. |
| 호출자가 구현을 골라 넣는가? | Strategy | 선택 주체가 외부에 있고 교체 가능성이 중요하다. |
| 객체가 스스로 다음 단계로 바뀌는가? | State | 상태 변화가 모델의 핵심 의미다. |

결제 예시로 보면 `카드냐 계좌이체냐`는 Strategy, `AUTHORIZED -> CAPTURED`는 State, `배송 후라 환불 불가`는 Policy Object에 가깝다.

## 흔한 오선택

`환불 가능 여부`를 State로 모델링하는 경우:
전이가 거의 없고 핵심이 허용/거절 이유라면 상태 패턴보다 Policy Object가 자연스럽다. `RefundDecision` 같은 결과를 바로 드러내는 편이 읽힌다.

`주문 상태 전이`를 Strategy로 빼는 경우:
호출자가 구현을 고르는 문제가 아니라 주문이 자기 단계에 따라 가능한 행동이 달라지는 문제다. 이때는 `OrderState`처럼 상태 전이를 모델링해야 한다.

`결제 수단 선택`을 Policy Object라고 부르는 경우:
규칙 판정보다 실제 실행 방법 교체가 핵심이면 Strategy가 더 정확하다. 학습자가 "카드 구현이랑 포인트 구현을 바꿔 끼운다"라고 말하면 Strategy 신호다.

## 다음 학습

- 실행 방법 교체 감각을 먼저 굳히려면 [전략 패턴 기초](./strategy-pattern-basics.md)
- 상태 전이와 워크플로 모델링으로 내려가려면 [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)
- 도메인 규칙 판정 객체를 더 또렷하게 보려면 [Policy Object Pattern: 도메인 결정을 객체로 만든다](./policy-object-pattern.md)
- 긴 비교 설명이 필요하면 [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)

---
schema_version: 3
title: Strategy vs State vs Policy Object
concept_id: design-pattern/strategy-vs-state-vs-policy-object
canonical: true
category: design-pattern
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
- strategy-state-policy-choice
- pattern-role-confusion
- payment-domain-patterns
aliases:
- strategy vs state
- strategy vs policy object
- state vs policy object
- strategy state policy comparison
- payment method vs payment status
- refund policy object
- workflow state transition
- policy decision object
- runtime algorithm selection vs domain rule
- 결제 수단 선택 vs 주문 상태
symptoms:
- 모든 if-else 제거를 strategy로만 부르면서 실행 방법, 현재 상태, 도메인 판정 책임이 섞인다
- 결제 수단 선택과 결제 진행 단계를 같은 패턴으로 모델링해 누가 구현을 선택하는지 불명확하다
- 환불 가능 여부 같은 policy decision을 상태 전이나 실행 strategy처럼 만들어 변경 이유가 섞인다
intents:
- comparison
- definition
- design
prerequisites:
- design-pattern/object-oriented-design-pattern-basics
- design-pattern/strategy-pattern
- design-pattern/policy-object-pattern
next_docs:
- design-pattern/state-pattern-workflow-payment
- design-pattern/pattern-selection
- design-pattern/command-handler-pattern
linked_paths:
- contents/design-pattern/strategy-pattern.md
- contents/design-pattern/state-pattern-workflow-payment.md
- contents/design-pattern/policy-object-pattern.md
- contents/design-pattern/template-method-vs-strategy.md
- contents/design-pattern/pattern-selection.md
- contents/software-engineering/oop-design-basics.md
- contents/design-pattern/command-handler-pattern.md
confusable_with:
- design-pattern/strategy-pattern
- design-pattern/state-pattern-workflow-payment
- design-pattern/policy-object-pattern
- design-pattern/template-method-vs-strategy
forbidden_neighbors: []
expected_queries:
- Strategy, State, Policy Object는 모두 if else를 객체로 빼는데 어떤 질문이 달라?
- 결제 수단 선택은 strategy이고 결제 상태 전이는 state인 이유를 예시로 설명해줘
- 환불 가능 여부나 수수료 판단은 왜 policy object로 이름 붙이는 편이 좋아?
- State는 객체가 현재 단계에 따라 스스로 바뀌고 Strategy는 호출자가 실행 방법을 고른다는 차이가 뭐야?
- 주문 취소 흐름에서 상태 전이, 환불 정책, 실제 환불 방식은 어떻게 역할을 나눠?
contextual_chunk_prefix: |
  이 문서는 Strategy vs State vs Policy Object chooser로, 실행 방법을 교체하는 Strategy,
  현재 단계에 따라 허용 행동이 바뀌는 State, 허용 여부와 이유를 판단하는 Policy Object를
  결제 수단, 결제 lifecycle, 환불 규정 예시로 구분한다.
---
# 실행 방법 선택, 상태 전이, 규칙 판정은 어떻게 다를까: Strategy vs State vs Policy Object

> 한 줄 요약: 세 패턴 모두 객체로 분리해 보이지만, Strategy는 실행 방법을 고르고, State는 현재 단계에 따라 행동이 달라지며, Policy Object는 허용 여부 같은 도메인 판정을 맡는다.

**난이도: 🟡 Intermediate**


관련 문서:

- [전략 패턴이란 무엇인가: 런타임에 구현을 바꾸는 방법](./strategy-pattern.md)
- [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)
- [Policy Object Pattern: 도메인 결정을 객체로 만든다](./policy-object-pattern.md)
- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
- [실전 패턴 선택 가이드](./pattern-selection.md)
- [객체지향 설계 기초: 합성, 책임, 협력](../software-engineering/oop-design-basics.md)

retrieval-anchor-keywords: strategy vs state, strategy vs policy object, state vs policy object, strategy state policy comparison, payment method vs payment status, refund policy object, workflow state transition, policy decision object, runtime algorithm selection vs domain rule, strategy vs state vs policy object basics, strategy vs state vs policy object beginner, 결제 수단 선택 vs 주문 상태, 상태 전이 뭐예요, policy object 뭐예요, pattern distinction 처음

---

## 핵심 개념

세 패턴은 모두 "if-else를 객체로 분리한다"는 점 때문에 처음 보면 비슷해 보인다.
하지만 객체가 맡는 질문이 다르다.

- Strategy: "어떤 방식으로 실행할까?"
- State: "지금 상태에서 무엇을 할 수 있지?"
- Policy Object: "이 상황에서 허용되는 규칙은 무엇이지?"

이 세 질문을 섞어 버리면, 결제 수단 선택을 상태처럼 모델링하거나, 주문 상태 전이를 단순 정책 객체로 눌러 담는 식의 혼란이 생긴다.

구조가 비슷할 때일수록 이름은 구현 모양보다 "객체가 대답하는 질문"을 드러내야 한다. 그래야 나중에 변경 이유가 달라져도 한 객체가 세 역할을 동시에 떠안지 않는다.

### 먼저 질문 하나로 구분하기

- 실행 방법을 갈아끼우는가: Strategy
- 현재 단계 때문에 가능한 행동이 달라지는가: State
- 허용 여부, 이유, 수수료 같은 판정을 내려야 하는가: Policy Object

---

## 한눈에 구분

| 구분 | Strategy | State | Policy Object |
|---|---|---|---|
| 핵심 질문 | 어떤 방법을 쓸까 | 지금 어떤 상태인가 | 어떤 규칙으로 판단할까 |
| 변화 이유 | 알고리즘/실행 방식 교체 | 상태 전이 | 비즈니스 규칙 변경 |
| 선택 주체 | 보통 호출자나 조립 코드 | 객체 자신 | 서비스나 도메인 흐름 |
| 대표 결과 | 동작 수행, 계산 결과 | 다음 상태, 허용된 행동 | 허용 여부, 이유, 금액, 등급 |
| 대표 예시 | 결제 수단, 정렬 방식, 할인 계산 | 주문 생성/승인/캡처/취소 | 환불 정책, 배송비 정책, 승인 규정 |

짧게 외우면 다음과 같다.

- Strategy는 "방법"이다.
- State는 "단계"다.
- Policy Object는 "판정 기준"이다.

---

## 같은 결제 도메인으로 비교하기

비슷한 결제 도메인에서도 셋은 전혀 다른 문제를 푼다.

### 1. Strategy: 결제 수단을 고른다

카드, 계좌이체, 간편결제 중 어떤 수단으로 결제를 실행할지 고르는 문제다.

```java
public interface PaymentStrategy {
    PaymentResult pay(Order order);
}
```

여기서 관심사는 "같은 결제"를 어떤 구현으로 처리하느냐다.

### 2. State: 결제 진행 단계를 모델링한다

`PENDING -> AUTHORIZED -> CAPTURED -> CANCELED`처럼 현재 단계에 따라 허용 행동이 달라지는 문제다.

```java
public interface PaymentState {
    PaymentState approve(Payment payment);
    PaymentState capture(Payment payment);
    PaymentState cancel(Payment payment);
}
```

여기서 관심사는 "지금 이 결제가 어디까지 왔는가"다.

### 3. Policy Object: 환불 가능 여부를 판정한다

배송 여부, 결제 후 경과 시간, 상품 유형에 따라 환불 가능 여부와 수수료를 결정하는 문제다.

```java
public interface RefundPolicy {
    RefundDecision evaluate(Order order);
}
```

여기서 관심사는 "허용되는가, 왜 그런가, 비용은 얼마인가"다.

같은 주문 시스템 안에서도 셋이 동시에 존재할 수 있다.

- 결제 시도 방식은 Strategy
- 결제 라이프사이클은 State
- 환불/취소 규정은 Policy Object

---

## 초보자가 자주 헷갈리는 지점

### 1. Strategy와 Policy Object는 모양이 비슷하다

둘 다 인터페이스 하나와 구현체 여러 개로 보일 수 있다.
차이는 구조가 아니라 **이름이 설명하는 도메인 의미**에 있다.

- `DiscountStrategy.calculate(price)`는 실행 방법을 바꾼다
- `RefundPolicy.evaluate(order)`는 규칙 판정을 드러낸다

즉 "행동을 바꾸는가"에 더 무게가 있으면 Strategy, "규칙을 말하는가"에 더 무게가 있으면 Policy Object다.

### 2. State도 겉모양은 Strategy처럼 보인다

State 역시 인터페이스와 구현 클래스로 나뉘기 때문에 Strategy와 비슷하게 보인다.
하지만 State는 호출자가 매번 고르는 객체라기보다, **객체가 자기 상태에 따라 스스로 바꾸는 객체**에 가깝다.

- `shippingService`에 `ExpressStrategy`를 넣는 것: Strategy
- `payment.capture()` 후 `AuthorizedState`가 `CapturedState`로 바뀌는 것: State

### 3. Policy Object가 상태 전이를 대신하지는 않는다

`RefundPolicy`가 "환불 가능"을 판단할 수는 있어도, 주문이 `REQUESTED -> APPROVED -> REFUNDED`로 어떻게 움직이는지까지 설명하진 않는다.
전이가 핵심이면 State나 워크플로 모델이 필요하다.

---

## 선택 기준

### Strategy를 먼저 볼 때

- 같은 목적을 여러 방식으로 실행한다
- 런타임에 구현을 교체할 수 있어야 한다
- 호출자가 어떤 구현을 쓸지 고를 수 있다

### State를 먼저 볼 때

- 현재 단계에 따라 가능한 행동이 달라진다
- 전이 규칙이 도메인 규칙 그 자체다
- 잘못된 순서의 호출을 막아야 한다

### Policy Object를 먼저 볼 때

- 허용/거절, 이유, 수수료, 레벨 같은 판정 결과가 중요하다
- 조건식이 도메인 언어로 드러나야 한다
- 규칙 변경 이유가 행동 흐름 변경과 다르다

---

## 함께 쓰는 구조도 많다

실무에서는 셋 중 하나만 고르는 경우보다, 역할을 나눠 함께 쓰는 경우가 더 많다.

예를 들어 주문 취소 흐름에서는:

1. 현재 주문 상태가 취소 가능한 단계인지 State가 본다.
2. 취소 수수료와 환불 가능 여부를 Policy Object가 판정한다.
3. 실제 환불을 카드 취소로 할지 포인트 복구로 할지는 Strategy가 고른다.

이렇게 분리하면 "상태 전이", "판정 규칙", "실행 방식"이 서로 다른 이유로 바뀔 수 있다는 점이 코드에 드러난다.

---

## 꼬리질문

> Q: `PaymentMethodPolicy`처럼 이름 붙이면 Strategy와 뭐가 다른가요?
> 의도: 구조보다 도메인 의미를 먼저 보는지 확인한다.
> 핵심: 실제로 실행 방식을 고르는 객체라면 Policy보다 Strategy가 더 정확한 이름이다.

> Q: 상태를 `enum`으로만 두면 안 되나요?
> 의도: 상태 식별과 상태별 규칙 응집을 구분하는지 확인한다.
> 핵심: 식별만 필요하면 enum으로 충분하지만, 상태별 허용 행동과 전이가 커지면 State 패턴이 낫다.

> Q: 환불 정책도 구현체가 여러 개면 결국 Strategy 아닌가요?
> 의도: 구조적 유사성과 의도 차이를 구분하는지 확인한다.
> 핵심: 구현 모양은 비슷할 수 있지만, 코드가 전달해야 할 도메인 의미가 판정 규칙이면 Policy Object라고 부르는 편이 더 명확하다.

---

## 한 줄 정리

Strategy는 "어떻게 실행할지", State는 "지금 어떤 단계인지", Policy Object는 "어떤 규칙으로 판단할지"를 객체로 드러낸다.

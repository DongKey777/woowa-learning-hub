---
schema_version: 3
title: "Policy, Strategy, Specification, Factory 이름은 언제 붙일까"
concept_id: design-pattern/policy-object-naming-primer
canonical: false
category: design-pattern
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 86
mission_ids:
- missions/blackjack
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- policy-naming
- strategy-vs-policy
- specification-boundary
- factory-misnaming
aliases:
- policy object naming primer
- policy vs strategy vs specification
- when to name policy
- when to name strategy
- when to name specification
- factory vs policy strategy specification
- rule object naming beginner
- decision object naming
- boolean rule naming
- policy strategy specification beginner
- policy naming guide
- policy strategy factory 차이
- policy object 이름 언제
symptoms:
- policy와 strategy 이름을 언제 갈라야 하는지 모르겠어
- boolean만 반환하는 규칙도 policy라고 불러야 하는지 헷갈려
- 생성도 안 하는데 factory라고 이름 붙여도 되는지 감이 안 와
intents:
- definition
- comparison
- design
prerequisites:
- design-pattern/factory-basics
- design-pattern/strategy-pattern-basics
next_docs:
- design-pattern/strategy-policy-selector-naming
- design-pattern/policy-object-vs-strategy-map-beginner-bridge
- design-pattern/specification-pattern
linked_paths:
- contents/design-pattern/factory-basics.md
- contents/design-pattern/strategy-policy-selector-naming.md
- contents/design-pattern/policy-object-vs-strategy-map-beginner-bridge.md
- contents/design-pattern/policy-object-pattern.md
- contents/design-pattern/specification-pattern.md
- contents/design-pattern/strategy-vs-state-vs-policy-object.md
confusable_with:
- design-pattern/strategy-policy-selector-naming
- design-pattern/policy-object-pattern
- design-pattern/specification-pattern
forbidden_neighbors:
- contents/design-pattern/factory-basics.md
expected_queries:
- policy랑 strategy랑 specification 이름을 언제 각각 써?
- boolean만 반환하면 specification인가 policy인가?
- 생성도 안 하는데 factory라고 부르면 왜 어색해?
- rule object 이름을 policy로 붙여야 할지 strategy로 붙여야 할지 모르겠어
contextual_chunk_prefix: |
  이 문서는 beginner가 policy, strategy, specification, factory 네 이름의
  경계를 처음 구분하도록 돕는 primer다. policy vs strategy naming,
  boolean rule naming, 생성도 안 하는데 factory라고 부르는 상황, rule
  object naming confusion 같은 자연어 질문이 이 문서의 질문 축과 예시에
  매핑된다.
---
# Policy Object Naming Primer: `Policy`, `Strategy`, `Specification`을 언제 붙일까

> 한 줄 요약: rule object가 실행 방식을 바꾸면 `Strategy`, 판정 결과를 내리면 `Policy`, 조건 통과 여부만 답하면 `Specification`이고, 아무것도 만들지 않으면 `Factory`가 아니다.

**난이도: 🟢 Beginner**

관련 문서:

- [팩토리 패턴 기초](./factory-basics.md)
- [Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들](./strategy-policy-selector-naming.md)
- [Policy Object vs Strategy Map: 커지는 전략 맵을 규칙 객체로 올릴 때](./policy-object-vs-strategy-map-beginner-bridge.md)
- [Policy Object Pattern: 도메인 결정을 객체로 만든다](./policy-object-pattern.md)
- [Specification Pattern: 조건식을 조합 가능한 도메인 규칙으로 만들기](./specification-pattern.md)
- [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: policy object naming primer, policy vs strategy vs specification, rule object naming beginner, when to name policy, when to name strategy, when to name specification, factory vs policy strategy specification, rule object not factory, decision object naming, boolean rule naming, algorithm object naming, policy object beginner naming, specification beginner naming, strategy beginner naming, beginner naming guide policy strategy specification

---

## Quick check

- 실행 방식을 바꾸면 `Strategy`
- 규칙을 평가해 결정을 만들면 `Policy`
- 조건 통과 여부만 답하면 `Specification`
- 새 객체를 조립해 반환하면 `Factory`

처음에는 메서드 이름보다 **이 객체가 어떤 질문에 답하나**를 먼저 보면 된다.

## 먼저 머릿속 그림

처음에는 네 이름이 다 비슷하게 들린다.
하지만 머릿속 그림을 다르게 잡으면 훨씬 덜 헷갈린다.

- `Strategy`: 같은 일을 **어떤 방식으로 실행할지** 고르는 카드
- `Policy`: 이 상황에서 **무슨 결정을 내려야 하는지** 적힌 규정표
- `Specification`: 어떤 대상을 **통과시킬지 말지** 보는 체크리스트
- `Factory`: 필요한 객체를 **새로 만들거나 조립하는** 작업대

짧게 외우면 이렇게 끝난다.

**방법이면 `Strategy`, 판정이면 `Policy`, 통과 조건이면 `Specification`, 생성이면 `Factory`다.**

---

## 먼저 10초 기준

짧게 외우면 아래 한 줄이면 된다.

**방법이면 `Strategy`, 판정이면 `Policy`, 통과 조건이면 `Specification`, 생성이면 `Factory`다.**

이 한 줄로 먼저 자르고, 그다음 메서드 모양과 반환값을 보면 이름이 훨씬 빨리 정리된다.

## 30초 비교표

| 이름 | 객체가 답하는 질문 | 흔한 메서드 모양 | 대표 반환값 | 보통 바뀌는 이유 |
|---|---|---|---|---|
| `Strategy` | "어떤 방식으로 실행할까?" | `pay()`, `send()`, `calculate()` | 실행 결과, 계산 결과 | 알고리즘/실행 방식 추가 |
| `Policy` | "이 상황에서 어떤 결정을 내려야 할까?" | `evaluate()`, `decide()` | `Decision`, reason, fee, level | 비즈니스 규칙 변경 |
| `Specification` | "이 조건을 만족하는가?" | `isSatisfiedBy()`, `test()` | `boolean` | 자격/검색/필터 조건 변경 |
| `Factory` | "무엇을 새로 만들까?" | `create()`, `of()`, `from()` | 새 객체, 조립 결과 | 생성/wiring 방법 변경 |

여기서 가장 중요한 기준은 클래스 모양이 아니라 **객체가 하는 질문**이다.
인터페이스 하나와 구현체 여러 개라는 모양만 보고 전부 같은 이름으로 부르면 초보자가 가장 먼저 길을 잃는다.

---

## 1분 예시: 환불 도메인에서 이름 붙이기

환불 도메인 하나만 잡아도 네 이름은 역할이 갈린다.

### `Specification`: 환불 대상인가

```java
public interface RefundSpecification {
    boolean isSatisfiedBy(Order order);
}
```

이 객체는 "`이 주문이 환불 조건을 만족하는가?`"만 답한다.
통과 여부만 중요하면 여기서 끝이다.

### `Policy`: 환불을 어떻게 판정할까

```java
public record RefundDecision(boolean allowed, int fee, String reasonCode) {}

public interface RefundPolicy {
    RefundDecision evaluate(Order order);
}
```

이 객체는 허용 여부뿐 아니라 수수료와 사유까지 함께 돌려준다.
즉 질문이 "`환불 가능한가?`"를 넘어서 "`그래서 어떤 결정을 내릴까?`"가 된다.

### `Strategy`: 실제 환불은 어떤 방식으로 실행할까

```java
public interface RefundStrategy {
    void refund(Payment payment);
}
```

카드 취소, 포인트 복구, 쿠폰 재발급처럼 **실행 방식**이 바뀌는 축이면 `Strategy`가 더 자연스럽다.

### `Factory`: 새 객체를 만들고 있나

```java
public final class RefundClientFactory {
    public RefundClient create(PaymentGateway gateway) {
        return new RefundClient(gateway.baseUrl(), gateway.apiKey());
    }
}
```

생성 책임이 실제로 보일 때만 `Factory`가 맞다.

---

## 초보자가 제일 많이 틀리는 지점

### 1. 구현체가 여러 개면 전부 `Strategy`라고 생각한다

아니다.
구현체가 여러 개라는 사실보다, **무엇이 바뀌는가**가 더 중요하다.

- 카드 환불 방식, 포인트 환불 방식: `Strategy`
- 국가별 환불 규정, 회원 등급별 할인 규정: `Policy`
- VIP 자격, 환불 가능 자격: `Specification`

### 2. 뭔가 고르면 일단 `Factory`라고 붙인다

이것도 아니다.
이미 있는 후보를 고르기만 하면 보통 `Selector`나 `Registry`에 더 가깝다.

```java
public final class RefundPolicySelector {
    private final Map<Region, RefundPolicy> policies;

    public RefundPolicy select(Region region) {
        return policies.get(region);
    }
}
```

이 코드는 policy를 **만들지 않는다**.
이미 등록된 policy를 고르기만 하므로 `RefundPolicyFactory`보다 `RefundPolicySelector`가 더 정확하다.

### 3. `Policy`와 `Specification`을 같은 말로 쓴다

둘 다 규칙 객체처럼 보여서 자주 섞인다.
하지만 질문이 다르다.

- `Specification`: 통과 여부를 고정한다
- `Policy`: 통과 여부를 포함한 최종 결정을 정리한다

즉 `boolean`이면 끝나는 질문인지, `Decision`까지 필요한 질문인지부터 보면 된다.

---

## 이름을 가장 빨리 고르는 3단계

새 클래스를 만들기 전에 아래 세 줄만 써 보면 된다.

1. 이 객체가 답해야 하는 질문을 한 문장으로 쓴다.
2. 메서드가 돌려줄 값을 적는다.
3. 다음 요구사항이 들어오면 무엇이 바뀔지 적는다.

판정은 이렇게 내리면 된다.

- 질문이 "어떻게 실행하지?"이고 반환이 실행 결과면 `Strategy`
- 질문이 "어떤 결정을 내리지?"이고 반환이 `Decision`이면 `Policy`
- 질문이 "조건을 만족하나?"이고 반환이 `boolean`이면 `Specification`
- 질문이 "무엇을 만들지?"이고 새 객체를 조립하면 `Factory`

---

## 잘못 붙인 이름을 바로 고치기

| 지금 이름 | 실제 메서드 모양 | 더 맞는 이름 |
|---|---|---|
| `DiscountFactory` | `evaluate(order)`로 할인 허용/사유를 돌려줌 | `DiscountPolicy` |
| `RefundStrategy` | `isSatisfiedBy(order)`만 있음 | `RefundSpecification` |
| `PaymentPolicy` | `pay(order)`로 실제 결제를 수행함 | `PaymentStrategy` |
| `ShippingPolicyFactory` | 등록된 `ShippingPolicy`를 key로 꺼냄 | `ShippingPolicySelector` 또는 `ShippingPolicyRegistry` |

이 표의 핵심은 "이름이 구조를 설명하지 말고 책임을 설명해야 한다"는 점이다.

---

## 같이 쓰는 구조도 흔하다

세 이름은 경쟁 관계가 아니라 역할 분담 관계인 경우가 많다.

예를 들어 환불 흐름은 이렇게 나눌 수 있다.

1. `RefundSpecification`이 최소 자격을 본다.
2. `RefundPolicy`가 reason code와 fee를 포함한 결정을 만든다.
3. `RefundStrategy`가 실제 취소/복구 방식을 실행한다.
4. `RefundPolicySelector`가 지역이나 상품군에 맞는 policy를 고른다.

이 구조에서 `Factory`는 없다.
정말 새 클라이언트나 조립 결과를 만드는 단계가 생길 때만 등장한다.

---

## 자주 하는 질문

### 구현체가 여러 개면 결국 다 전략 아닌가요

아니다.
여러 구현체라는 모양은 공통이고, `Strategy`인지 `Policy`인지는 **행동 실행 축인지, 규칙 판정 축인지**로 결정한다.

### `Policy` 안에서 `Specification`을 써도 되나요

된다.
오히려 자주 그렇게 쓴다.
조건 조합은 `Specification`이 맡고, 최종 decision 조립은 `Policy`가 맡으면 경계가 더 선명해진다.

### `Factory`를 쓰면 틀린 건가요

컴파일은 된다.
문제는 읽는 사람이 "새 객체를 만드는 복잡한 코드가 있겠구나"라고 오해한다는 점이다.
생성이 아니라 선택/판정/조건 확인이 중심이면 다른 이름이 더 낫다.

---

## 다음 읽기

- 이름이 아니라 "선택기 vs 생성기"를 더 보고 싶다면 [Strategy vs Policy Selector Naming](./strategy-policy-selector-naming.md)
- 커지는 전략 맵에서 rule만 policy object로 올리는 순간을 보고 싶다면 [Policy Object vs Strategy Map](./policy-object-vs-strategy-map-beginner-bridge.md)
- rich decision까지 담는 정책 객체를 더 깊게 보고 싶다면 [Policy Object Pattern](./policy-object-pattern.md)
- boolean 조합과 정책 객체 경계를 더 깊게 보고 싶다면 [Specification Pattern](./specification-pattern.md)

## 한 줄 정리

이름을 붙일 때는 구현체 개수보다 질문을 먼저 본다. 실행 방식을 바꾸면 `Strategy`, 판정 결과를 만들면 `Policy`, 조건 충족 여부만 보면 `Specification`, 새 객체를 만들면 `Factory`다.

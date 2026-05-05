---
schema_version: 3
title: 'Policy Object vs Strategy Map: 커지는 전략 맵을 규칙 객체로 올릴 때'
concept_id: design-pattern/policy-object-vs-strategy-map-beginner-bridge
canonical: false
category: design-pattern
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 85
mission_ids:
- missions/blackjack
- missions/shopping-cart
review_feedback_tags:
- strategy-map-smell
- policy-object-naming
- rich-decision-result
aliases:
- policy object vs strategy map
- strategy map to policy object
- growing strategy map smell
- map key strategy policy object
- strategy collection vs policy object
- behavior selector vs rule object
- policy selector beginner
- refund policy decision object
- discount strategy map smell
- strategy map rule explosion
- strategy map beginner bridge
- policy object beginner bridge
- rule deserves policy object
- rich decision result vs strategy result
- strategy selector with policy object
symptoms:
- Map에서 전략을 고르는 코드가 커지는데 어디서부터 policy로 봐야 할지 모르겠어요
- 금액 말고 거절 이유까지 내려야 하는데 strategy만 늘고 있어요
- selector인지 rule object인지 이름이 안 잡혀요
intents:
- comparison
prerequisites:
- design-pattern/strategy-pattern-basics
- design-pattern/strategy-map-vs-registry-primer
next_docs:
- design-pattern/policy-object-pattern
- design-pattern/strategy-vs-state-vs-policy-object
- design-pattern/policy-registry-pattern
linked_paths:
- contents/design-pattern/strategy-pattern-basics.md
- contents/design-pattern/strategy-map-vs-registry-primer.md
- contents/design-pattern/strategy-policy-selector-naming.md
- contents/design-pattern/strategy-vs-state-vs-policy-object.md
- contents/design-pattern/policy-object-pattern.md
- contents/design-pattern/policy-registry-pattern.md
- contents/design-pattern/strategy-registry-vs-service-locator-drift.md
confusable_with:
- design-pattern/strategy-map-vs-registry-primer
- design-pattern/policy-object-pattern
forbidden_neighbors:
- contents/design-pattern/strategy-map-vs-registry-primer.md
- contents/design-pattern/policy-object-pattern.md
expected_queries:
- 전략 맵이 커질 때 언제 policy object로 올려야 해?
- Map으로 구현 선택하는 코드가 규칙 객체로 바뀌어야 하는 신호가 뭐야?
- 허용 여부와 이유를 같이 내려야 하면 strategy보다 어떤 구조가 맞아?
- selector 클래스가 점점 판정 로직까지 먹고 있는데 어떻게 정리해?
- discount나 refund 규칙이 strategy map을 넘어서기 시작했다는 건 무슨 뜻이야?
contextual_chunk_prefix: |
  이 문서는 학습자가 Map으로 구현 선택을 모으던 코드가 언제 규칙 객체로
  올라가야 하는지, 키 선택과 도메인 판정을 어떻게 잇는지 연결한다. 메뉴판처럼
  하나 고르기, 판정 이유까지 함께 내려주기, 허용 여부와 사유 반환, selector가
  규칙을 먹기 시작함, 전략 맵 비대화 같은 자연어 paraphrase가 본 문서의 경계에
  매핑된다.
---
# Policy Object vs Strategy Map: 커지는 전략 맵을 규칙 객체로 올릴 때

> 한 줄 요약: `Map<Key, Strategy>`가 "키로 행동을 고르는 메뉴"라면 그대로 strategy map이고, 키보다 규칙 판정과 이유가 중요해지면 policy object로 올리는 편이 읽기 쉽다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> Beginner Route: `[entrypoint]` [전략 패턴 기초](./strategy-pattern-basics.md) -> `[bridge]` 이 문서 -> `[deep dive]` [Policy Object Pattern: 도메인 결정을 객체로 만든다](./policy-object-pattern.md)

> 관련 문서:
> - [전략 패턴 기초](./strategy-pattern-basics.md)
> - [Strategy Map vs Registry Primer](./strategy-map-vs-registry-primer.md)
> - [Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들](./strategy-policy-selector-naming.md)
> - [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)
> - [Policy Object Pattern: 도메인 결정을 객체로 만든다](./policy-object-pattern.md)
> - [Policy Registry Pattern: 정책 객체를 키로 찾아 조합하기](./policy-registry-pattern.md)
> - [Strategy Registry vs Service Locator Drift Note](./strategy-registry-vs-service-locator-drift.md)
> - [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: policy object vs strategy map, strategy map to policy object, growing strategy map smell, map key strategy policy object, strategy collection vs policy object, behavior selector vs rule object, policy selector beginner, refund policy decision object, discount strategy map smell, strategy map rule explosion, strategy map beginner bridge, policy object beginner bridge, rule deserves policy object, rich decision result vs strategy result, strategy selector with policy object

---

## 먼저 머릿속 그림

전략 맵과 정책 객체는 둘 다 `if-else`를 줄이는 데 쓰일 수 있다.
그래서 처음 보면 거의 같은 모양처럼 보인다.

하지만 머릿속 그림은 다르다.

- **Strategy map**: 메뉴판에서 하나를 고른다. "카드 결제면 카드 전략, 포인트 결제면 포인트 전략."
- **Policy object**: 판정표로 결정을 내린다. "이 주문은 환불 가능한가, 수수료는 얼마인가, 거절 사유는 무엇인가."

짧게 외우면 이렇게 된다.

**키로 행동을 고르면 strategy map, 규칙으로 결정을 내리면 policy object다.**

---

## 30초 구분표

| 질문 | Strategy map으로 남겨도 좋다 | Policy object로 올리는 게 좋다 |
|---|---|---|
| 중심 질문 | 어떤 행동을 실행할까 | 어떤 규칙으로 판단할까 |
| 선택 기준 | 결제수단, 배송타입처럼 단순한 key | 상태, 시간, 등급, 예외 조건이 함께 작동 |
| 꺼낸 뒤 하는 일 | 같은 메서드를 실행한다 | 허용/거절, 이유, 금액, 등급을 판정한다 |
| 새 코드가 생기는 이유 | 새 행동 방식이 추가된다 | 새 규칙 조항이나 예외가 추가된다 |
| 결과 모양 | 계산값, 실행 결과 | `Decision`, `Reason`, `Fee`, `Level` 같은 판정 결과 |
| 좋은 이름 | `PaymentStrategySelector`, `ShippingStrategyMap` | `RefundPolicy`, `CancellationPolicy`, `DiscountPolicy` |

핵심은 자료구조가 아니다.
`Map<Key, Something>`을 쓰더라도, 그 `Something`이 **단순 실행 방식**인지 **도메인 판정 규칙**인지가 더 중요하다.

---

## 먼저 이 4문장만 확인하면 된다

아직 헷갈리면 아래 네 문장을 순서대로 보면 된다.

1. key 하나로 누구를 고를지만 정하면 끝나는가
2. lookup 뒤에 모두 같은 행동을 바로 실행하는가
3. 호출자가 금액 말고도 이유, 허용 여부, 다음 액션까지 함께 필요로 하는가
4. 새 요구사항이 "새 방식 추가"보다 "예외 규칙 추가"에 더 가까운가

판단은 이렇게 하면 된다.

- 1, 2가 "그렇다"면 strategy map으로 남겨도 되는 경우가 많다.
- 3, 4가 "그렇다"면 rule 자체를 policy object로 올리는 편이 읽기 쉽다.

즉 "map을 버릴까?"부터 고민할 필요는 없다.
먼저 **지금 커지고 있는 것이 selector인지, rule인지**를 보면 된다.

---

## Strategy map으로 충분한 예

결제 수단별로 실제 결제 실행 방식만 바뀐다고 하자.

```java
public interface PaymentStrategy {
    PaymentResult pay(Order order);
}

public final class PaymentStrategySelector {
    private final Map<PaymentMethod, PaymentStrategy> strategies;

    public PaymentStrategySelector(Map<PaymentMethod, PaymentStrategy> strategies) {
        this.strategies = strategies;
    }

    public PaymentResult pay(PaymentMethod method, Order order) {
        PaymentStrategy strategy = strategies.get(method);
        if (strategy == null) {
            throw new IllegalArgumentException("unsupported method: " + method);
        }
        return strategy.pay(order);
    }
}
```

이 구조는 strategy map으로 충분하다.

- key가 `PaymentMethod` 하나로 단순하다.
- 후보들은 모두 `PaymentStrategy`라는 같은 역할이다.
- lookup 직후 `pay(...)`라는 같은 행동을 실행한다.
- 새 항목은 "새 결제 방식"을 추가한다는 뜻이다.

즉 이 코드는 "규칙을 판정한다"보다 "실행 방식을 고른다"에 가깝다.

---

## 맵이 커져도 그대로 selector로 남겨도 되는 경우

초보자가 가장 자주 오해하는 지점이 이것이다.
`Map<Key, Strategy>`가 커진다고 해서 무조건 policy object로 바꿔야 하는 것은 아니다.

예를 들어 지역별 환불 규정이 다를 수 있다.
그렇더라도 selector의 역할이 아래처럼 단순하면 map은 그대로 둬도 된다.

```java
public final class RefundPolicySelector {
    private final Map<Region, RefundPolicy> policies;

    public RefundPolicy select(Region region) {
        RefundPolicy policy = policies.get(region);
        if (policy == null) {
            throw new IllegalArgumentException("unsupported region: " + region);
        }
        return policy;
    }
}
```

여기서 map이 하는 일은 여전히 단순하다.

- `Region` key로 알맞은 후보를 고른다.
- selector 자신은 환불 가능 여부를 판정하지 않는다.
- 복잡한 규칙은 각 `RefundPolicy` 안으로 들어간다.

즉 map의 크기보다 더 중요한 것은 **map 안에 규칙 판정이 새어 들어오는가**다.
selector가 selector 역할에 머물면, 큰 map도 충분히 건강할 수 있다.

---

## Policy object가 필요해지는 예

처음에는 할인도 아래처럼 단순한 strategy map으로 시작할 수 있다.

```java
public interface DiscountStrategy {
    int discountAmount(Order order);
}

public final class DiscountService {
    private final Map<MemberGrade, DiscountStrategy> discounts;

    public int discount(Order order) {
        DiscountStrategy strategy = discounts.get(order.memberGrade());
        return strategy.discountAmount(order);
    }
}
```

그런데 시간이 지나면서 `VipDiscountStrategy` 안에 이런 조건이 늘어난다고 하자.

```java
public final class VipDiscountStrategy implements DiscountStrategy {
    @Override
    public int discountAmount(Order order) {
        if (order.hasCoupon()) {
            return 0;
        }
        if (order.isFirstOrder()) {
            return 5000;
        }
        if (order.totalPrice() < 30000) {
            return 1000;
        }
        return 3000;
    }
}
```

이제 이름은 `Strategy`지만 실제 관심사는 점점 "VIP 할인 실행 방식"이 아니다.
관심사는 이런 판정에 가까워진다.

- 쿠폰과 멤버십 할인은 함께 적용 가능한가
- 첫 주문이면 어떤 우선순위를 갖는가
- 최소 주문 금액 미달이면 왜 할인 금액이 줄어드는가
- 사용자에게 어떤 reason code를 보여 줄 것인가

이때는 정책 객체가 더 읽기 쉽다.

## Policy object가 필요해지는 예 (계속 2)

```java
public interface DiscountPolicy {
    DiscountDecision evaluate(Order order);
}

public record DiscountDecision(int amount, String reasonCode) {}

public final class VipDiscountPolicy implements DiscountPolicy {
    @Override
    public DiscountDecision evaluate(Order order) {
        if (order.hasCoupon()) {
            return new DiscountDecision(0, "COUPON_ALREADY_APPLIED");
        }
        if (order.isFirstOrder()) {
            return new DiscountDecision(5000, "VIP_FIRST_ORDER");
        }
        if (order.totalPrice() < 30000) {
            return new DiscountDecision(1000, "VIP_MINIMUM_AMOUNT_NOT_MET");
        }
        return new DiscountDecision(3000, "VIP_STANDARD");
    }
}
```

바뀐 점은 "객체를 더 만들었다"가 아니다.
규칙의 의미가 코드에 더 직접적으로 드러난다.

- `discountAmount(...)`보다 `evaluate(...)`가 판정 느낌을 준다.
- `int` 하나보다 `DiscountDecision`이 금액과 이유를 함께 전한다.
- 테스트 이름도 `coupon_already_applied_returns_zero_discount`처럼 규칙 문장에 가까워진다.

여기서 중요한 포인트는 "전략 맵이 커졌다"가 아니다.
더 정확히는 **전략 안쪽의 rule이 도메인 판정 언어를 요구하기 시작했다**는 것이다.

- `discountAmount(...)` 하나로는 의도가 부족하다.
- `0`이라는 숫자만으로는 왜 0인지 설명이 안 된다.
- 호출자는 계산 결과뿐 아니라 판정 이유도 함께 써야 한다.

이 순간이 "selector는 그대로 두고, rule을 policy object shape로 올릴 때"다.

---

## 전략 맵을 유지할지 묻는 체크리스트

아래에 많이 해당하면 strategy map으로 남겨도 괜찮다.

- key 하나로 후보를 고르는 설명이 충분하다.
- 후보들이 같은 인터페이스의 같은 메서드를 실행한다.
- 반환값이 단순 계산 결과나 실행 결과다.
- 새 항목을 추가할 때 "새 방식이 생겼다"고 말할 수 있다.
- 각 전략 안의 조건문이 작고, 도메인 예외 설명이 거의 없다.

예를 들면 `PaymentMethod -> PaymentStrategy`, `ShippingType -> ShippingStrategy`는 보통 이쪽이다.

---

## Policy object로 올릴지 묻는 체크리스트

아래에 많이 해당하면 policy object를 고려한다.

- key 하나로는 규칙을 설명하기 어렵다.
- 상태, 시간, 금액, 등급, 예외 조건이 함께 판정에 들어간다.
- 호출자가 `allowed`, `reasonCode`, `fee`, `discountAmount`, `nextAction` 같은 결과를 함께 필요로 한다.
- "새 결제 방식"이 아니라 "새 규칙 조항"이 자주 추가된다.
- 전략 클래스 안에 `if`, `else if`, `return 0`, `throw`가 계속 늘어난다.
- 테스트가 "어떤 구현을 썼나"보다 "어떤 조건에서 왜 허용/거절되나"를 묻는다.

예를 들면 `RefundPolicy`, `CancellationPolicy`, `DiscountPolicy`, `ApprovalPolicy`는 보통 이쪽이다.

---

## 가장 작은 리팩터링 순서

처음부터 큰 추상화를 다시 짤 필요는 없다.
보통은 아래 순서가 가장 안전하다.

| 단계 | 유지하는 것 | 바꾸는 것 |
|---|---|---|
| 1 | 기존 `Map<Key, Strategy>` selector | 전략 구현 안의 큰 규칙 묶음을 찾는다 |
| 2 | selector의 key lookup | `int`, `boolean` 같은 반환값을 `Decision` 객체로 바꾼다 |
| 3 | selector의 선택 책임 | `calculate(...)`보다 `evaluate(...)`처럼 판정 이름을 드러낸다 |
| 4 | 바깥 호출 흐름 | reason code, allowed, next action 같은 결과를 소비하게 만든다 |

짧게 말하면 이렇다.

- **selector는 남겨도 된다**
- **rule이 policy object shape로 바뀌면 된다**

즉 "strategy map vs policy object"를 완전 교체 관계로 보기보다,
"어느 층이 selector이고 어느 층이 rule인가"를 다시 나누는 쪽이 초보자에게 더 정확한 그림이다.

---

## 둘은 같이 쓸 수도 있다

초보자가 자주 놓치는 부분은 이것이다.
strategy map과 policy object는 반드시 둘 중 하나만 고르는 관계가 아니다.

예를 들어 위의 `RefundPolicySelector`처럼 지역 key로 policy를 고른 뒤, 실제 판정은 policy object가 맡게 할 수 있다.

```java
RefundPolicy policy = refundPolicySelector.select(order.region());
RefundDecision decision = policy.evaluate(order);
```

여기서 역할은 분리된다.

- `RefundPolicySelector`: 지역 key로 어떤 정책을 쓸지 고른다.
- `RefundPolicy`: 주문을 보고 환불 가능 여부와 이유를 판정한다.
- `RefundDecision`: 호출자가 써야 할 결과를 담는다.

즉 `Map<Region, RefundPolicy>`는 policy object를 고르는 selector일 수 있다.
그렇다고 policy object의 규칙까지 selector 안에 넣어야 하는 것은 아니다.

---

## 흔한 오해

- **"`Map<Key, Policy>`면 strategy map인가요?"**
  - map은 선택 도구다. 값이 정책 객체라면 전체 구조는 "정책 선택 + 정책 판정"으로 읽는 편이 더 정확하다.
- **"`Strategy` 이름을 `Policy`로 바꾸면 해결인가요?"**
  - 아니다. 반환값과 테스트가 여전히 단순 실행 방식이면 이름만 바꾼 것이다.
- **"조건문이 하나라도 있으면 무조건 policy object인가요?"**
  - 아니다. 작은 guard나 입력 검증은 전략 안에 있어도 된다. 규칙 설명, reason code, 예외 조항이 중심이 될 때 옮긴다.
- **"Policy object도 구현체가 여러 개면 결국 strategy 아닌가요?"**
  - 구조는 비슷할 수 있다. 하지만 독자가 읽어야 할 의미가 "실행 방식"인지 "규칙 판정"인지가 이름을 결정한다.

---

## 다음에 이어서 보면 좋은 문서

- `Map<Key, ...>`가 registry인지 strategy인지 먼저 가르고 싶다면 [Strategy Map vs Registry Primer](./strategy-map-vs-registry-primer.md)
- policy object 자체를 더 깊게 보고 싶다면 [Policy Object Pattern](./policy-object-pattern.md)
- strategy, state, policy object를 한 번에 비교하려면 [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)
- 선택기가 전역 조회소처럼 커지는 냄새는 [Strategy Registry vs Service Locator Drift Note](./strategy-registry-vs-service-locator-drift.md)

## 한 줄 정리

strategy map은 **이미 있는 후보 중 어떤 행동을 실행할지 고르는 구조**다.
규칙의 이유, 수수료, 허용 여부, 예외 조항이 코드의 중심이 되면 그 행동 후보 안쪽을 **policy object**로 올리는 편이 더 명확하다.

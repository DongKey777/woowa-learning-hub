# 전략 패턴 기초 (Strategy Pattern Basics)

> 한 줄 요약: 전략 패턴은 알고리즘(행동)을 별도 객체로 분리해 런타임에 교체할 수 있게 만드는 패턴으로, if-else 분기보다 변경 축을 명확하게 나누고 싶을 때 쓴다.

**난이도: 🟢 Beginner**

> Beginner Route: `[entrypoint]` [상속보다 조합 기초](./composition-over-inheritance-basics.md) -> `[entrypoint]` 이 문서 -> `[bridge]` [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) -> `[sibling primer]` [템플릿 메소드 패턴 기초](./template-method-basics.md)

관련 문서:

- [Language README - Java primer](../language/README.md#java-primer)
- [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md)
- [객체지향 디자인 패턴 기초](./object-oriented-design-pattern-basics.md)
- [Command vs Strategy: `execute()`가 비슷해 보여도 먼저 자르는 짧은 다리](./command-vs-strategy-quick-bridge.md)
- [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](./factory-selector-resolver-beginner-entrypoint.md)
- [Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들](./strategy-policy-selector-naming.md)
- [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](./registry-vs-factory-injected-handler-maps.md)
- [Strategy Map vs Registry Primer: 같은 `Map` 모양인데 질문이 다르다](./strategy-map-vs-registry-primer.md)
- [전략 (Strategy) — 심화](./strategy-pattern.md)
- [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)
- [Policy Object vs Strategy Map: 커지는 전략 맵을 규칙 객체로 올릴 때](./policy-object-vs-strategy-map-beginner-bridge.md)
- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) - 처음 배우는데 "호출자가 전략을 고른다 vs 부모가 흐름을 쥔다"를 빠르게 다시 자르는 비교 bridge
- [상속보다 조합 기초](./composition-over-inheritance-basics.md)
- [템플릿 메소드 패턴 기초](./template-method-basics.md) - 전략 다음에 상속 기반 고정 흐름 쪽 큰 그림으로 돌아가는 sibling primer
- [전략 폭발 냄새](./strategy-explosion-smell.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [IoC 컨테이너와 DI](../spring/ioc-di-container.md)

retrieval-anchor-keywords: strategy pattern basics, strategy pattern beginner, 전략 패턴 기초, 결제 전략, 할인 전략, if-else 대신 전략, caller chooses strategy, 호출자가 전략 선택, 처음 배우는데 전략 패턴, 전략 패턴 큰 그림, 전략 패턴 언제 쓰는지, 주입으로 구현 고르기, strategy vs factory vs registry, 전략 팩토리 레지스트리 차이, map strategy registry confusion

---

## 길을 잃었을 때: OOP 큰 그림으로 한 번 돌아가기

처음 배우는데 전략 패턴이 "if-else를 예쁘게 감싼 것"처럼만 보이면, 전략 자체를 더 깊게 보기보다 **객체지향 큰 그림 -> 조합 -> 전략** 순서로 다시 들어오는 편이 빠르다.

| 지금 막히는 지점 | 먼저 돌아갈 문서 | 왜 여기로 돌아가나 |
|---|---|---|
| 전략 패턴 전에 패턴 큰 그림부터 다시 보고 싶다 | [객체지향 디자인 패턴 기초](./object-oriented-design-pattern-basics.md) | 조합 -> 템플릿 메소드 -> 전략 route map을 먼저 보고 오면 전략이 "규칙 교체" 문제라는 위치가 더 또렷해진다 |
| 객체가 책임을 나눠 가진다는 감각이 아직 약하다 | [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md) | 캡슐화, 다형성, 추상화가 전략 객체 분리와 어떻게 이어지는지 큰 그림부터 맞춘다 |
| 부모 클래스와 객체 주입 차이가 아직 흐리다 | [상속보다 조합 기초](./composition-over-inheritance-basics.md) | 전략은 조합의 대표 예시라서 `extends` 대신 객체를 들고 오는 감각이 먼저다 |
| 추상 클래스와 인터페이스 선택이 헷갈린다 | [추상 클래스 vs 인터페이스 입문](../language/java/java-abstract-class-vs-interface-basics.md) | 전략 인터페이스가 "공통 흐름"이 아니라 "교체 규칙 계약"이라는 점을 먼저 자른다 |
| 템플릿 메소드와 전략이 자꾸 섞여 보인다 | [템플릿 메소드 패턴 기초](./template-method-basics.md) | 부모가 흐름을 쥐는 경우와 호출자가 규칙 객체를 고르는 경우를 나란히 비교한다 |

한 줄 route로 줄이면 이렇다.
**[객체지향 핵심 원리](../language/java/object-oriented-core-principles.md) -> [상속보다 조합 기초](./composition-over-inheritance-basics.md) -> 이 문서**

패턴 큰 그림에서 바로 이어 붙이면 이 route도 잘 맞는다.
**[객체지향 디자인 패턴 기초](./object-oriented-design-pattern-basics.md) -> [상속보다 조합 기초](./composition-over-inheritance-basics.md) -> 이 문서 -> [템플릿 메소드 패턴 기초](./template-method-basics.md)**

## 30초 길찾기: OOP primer -> 조합 -> 전략 -> 템플릿

처음 배우는데 전략 패턴만 먼저 잡으면 "조합의 대표 예시"라는 위치가 흐려질 수 있다. 이 문서는 아래 beginner route 가운데에서 읽으면 상속/조합/전략 이동 경로가 더 자연스럽다.

| 지금 필요한 큰 그림 | 먼저 볼 문서 | 이 문서를 읽은 뒤 다음 문서 |
|---|---|---|
| 객체지향 기초부터 다시 이어 붙이고 싶다 | [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md) | [상속보다 조합 기초](./composition-over-inheritance-basics.md) |
| `extends` 대신 객체를 들고 오는 감각이 약하다 | [상속보다 조합 기초](./composition-over-inheritance-basics.md) | 이 문서 |
| 전략이 맞는지, 부모가 흐름을 쥐는 게 맞는지 헷갈린다 | 이 문서 | [템플릿 메소드 패턴 기초](./template-method-basics.md) 또는 [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) |

짧게 외우면 이렇다.

- **큰 그림이 흐리면**: [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md)
- **조합 감각이 약하면**: [상속보다 조합 기초](./composition-over-inheritance-basics.md)
- **전략 다음 비교가 필요하면**: [템플릿 메소드 패턴 기초](./template-method-basics.md)

## 핵심 개념

처음 배우는데 큰 그림부터 잡으면, 전략 패턴은 **`Context`가 전략을 알아서 고르는 패턴**이라기보다 **호출자/설정/DI/selector가 이번 규칙 객체를 골라 넣고 `Context`는 실행만 맡는 패턴**에 가깝다. 즉 질문의 핵심은 "전략 패턴이 뭔가요?"보다 먼저 **"누가 전략을 고르나?"**다.

전략 패턴은 "무엇을 할지"는 `Context`가 결정하고, "어떻게 할지"는 `Strategy` 구현체가 결정하도록 역할을 나누는 패턴이다. `Context`는 구체 구현 대신 공통 인터페이스(`Strategy`)에만 의존하므로, 구현체를 교체해도 `Context`를 바꿀 필요가 없다.

입문자가 자주 막히는 지점은 "if-else와 결과가 같은데 왜 구조를 키우나?"라는 의문이다. 핵심은 **변경 축의 분리**다. 새 결제 수단이나 새 할인 정책이 추가될 때 기존 코드를 건드리지 않고 새 구현체만 추가하면 된다.

| 처음 고정할 질문 | 전략 패턴에서 보통 누가 맡나 |
|---|---|
| 누가 전략을 고르나 | 호출자, 설정, DI, selector |
| `Context`는 무엇을 하나 | 선택된 전략에 실행을 위임한다 |
| 언제 beginner가 헷갈리나 | `Context` 내부 `if-else`와 DI 주입을 같은 일로 볼 때 |

### 많이 섞이는 이름 20초 구분표

처음 배우는데 strategy가 `factory`, `registry`와 같이 보이면 아래처럼 질문을 먼저 자른다.

| 지금 코드가 답하는 질문 | 더 가까운 이름 | 10초 예시 |
|---|---|---|
| 어떤 규칙을 실행할까 | strategy | `discountStrategy.apply(price)` |
| 지금 새 객체를 만들까 | factory | `paymentClientFactory.create(provider)` |
| 이미 등록된 객체를 key로 찾을까 | registry | `paymentHandlerRegistry.get(method)` |

즉 **전략은 실행 규칙**, **팩토리는 생성**, **레지스트리는 등록 lookup**이다.

### 자주 생기는 오해: `Map<Key, Strategy>`면 strategy인가 registry인가

둘 다 일부는 맞다. `Map`은 strategy를 찾는 lookup 도구라서 registry 같은 모양을 가지지만, **꺼낸 뒤 같은 행동을 실행하는 것이 중심이면 설계 질문은 strategy selection**이다.

```java
PaymentStrategy strategy = strategies.get(order.getPaymentMethod());
strategy.pay(order);
```

- `strategies.get(...)`만 보면 lookup이라 registry-like하다
- `strategy.pay(order)`까지 보면 "어떤 행동을 실행할까"가 중심이라 strategy 쪽이다

같은 `Map` 모양이 자꾸 헷갈리면 [Strategy Map vs Registry Primer: 같은 `Map` 모양인데 질문이 다르다](./strategy-map-vs-registry-primer.md)로 바로 내려가면 된다.

## 빠른 진입: 10초/30초/1분

처음 읽을 때는 `10초 질문 -> 30초 비교표 -> 1분 예시` 순서로만 훑는다.

### 10초 질문

아래 3줄만 먼저 체크한다.

1. 주문/할인 흐름은 비슷한데 계산 규칙만 자주 바뀌는가?
2. 호출자나 DI가 "이번에는 이 구현"을 골라 넣을 수 있는가?
3. 새 규칙을 추가할 때 `Context` 본문 if-else를 크게 늘리지 않아도 되는가?

3줄 중 2개 이상이 "예"라면 전략 패턴 후보로 본다.

### 30초 비교표

아래 표에서 지금 문제에 더 가까운 쪽을 먼저 고른다.

| 비교 질문 | if-else 분기 중심 | 전략 패턴 중심 |
|---|---|---|
| 규칙이 놓이는 곳 | `Context` 내부 조건문 | `Strategy` 구현체 |
| 새 규칙 추가 방식 | 기존 분기문 수정 | 구현체 추가 + 선택 매핑 추가 |
| 선택 책임 | `Context`가 내부에서 고른다 | 호출자/설정/DI가 고른다 |
| 잘 맞는 크기 | 규칙이 1~2개이고 거의 안 바뀐다 | 규칙이 늘고 교체가 잦다 |

흐름 순서를 부모가 고정해야 하는 문제라면 전략보다 [템플릿 메소드 패턴 기초](./template-method-basics.md)를 먼저 본다.

### 1분 예시: 회원 등급 할인

아래처럼 흐름은 유지한 채, 계산 규칙만 교체되는지 보면 된다.

`OrderService`는 계산 규칙을 직접 분기하지 않고 `DiscountStrategy`에 위임한다.

`int discounted = discountStrategy.apply(price);`

| 등급 | 전략 객체 | 계산식 |
|---|---|---|
| `VIP` | `VipDiscountStrategy` | `price * 0.8` |
| `BASIC` | `BasicDiscountStrategy` | `price` |

새 등급 `FAMILY`가 생기면 `FamilyDiscountStrategy`를 추가하고 선택 매핑만 보강하면 된다.

## 호출자 선택 책임 미니 체크

### 자주 헷갈리는 포인트 3개

- 전략 패턴의 핵심은 "if-else 제거"가 아니라 "변경 축 분리"다. 조건문이 조금 남아도 괜찮다.
- `Context`가 구현 선택까지 다 하면 전략의 장점이 줄어든다. 가능하면 호출자/설정/DI/selector가 선택 책임을 가진다.
- 단순 의존성 주입과 전략 주입은 다르다. 주입 대상이 "교체 가능한 규칙"인지 먼저 확인한다.

### 20초 미니 체크: 호출자 선택 책임

아래 4칸만 보면 `selector`, DI, 호출자 책임이 한 번에 정리된다.

| 질문 | 예라면 |
|---|---|
| 누가 `VipDiscountStrategy`를 골라 `OrderService`에 넣는가? | 호출자, 설정, DI, selector가 선택 책임을 가진다 |
| `OrderService`는 받은 객체에 계산만 맡기는가? | `Context`가 전략 실행에만 집중하고 있다는 뜻이다 |
| 새 전략 추가 때 `OrderService` 본문보다 선택 매핑 쪽이 더 바뀌는가? | 전략 패턴답게 변경 축이 밖으로 빠져 있다 |
| `OrderService` 안에서 `if (vip) new VipDiscountStrategy()`를 직접 하나? | 이 경우 선택 책임이 다시 `Context`로 들어와 전략 장점이 약해진다 |

짧게 외우면 이렇다. **고르는 쪽은 호출자/DI/selector, 실행하는 쪽은 `Context`**다.

## 짧은 오해 점검

### 짧은 오해 점검: Strategy vs if-else vs Policy Object

처음 읽을 때는 아래 세 문장만 바로 판별해도 감이 많이 잡힌다.

| 문장 | 바로 판단 |
|---|---|
| "분기가 2개뿐이면 무조건 Strategy로 바꿔야 한다" | 아니다. 규칙이 거의 안 바뀌면 `if-else`가 더 읽기 쉬울 수 있다. |
| "호출자가 `CardStrategy`와 `CashStrategy` 중 하나를 골라 넣는다" | Strategy에 가깝다. 실행 방법을 갈아끼우는 문제다. |
| "`RefundPolicy.evaluate(order)`가 허용 여부와 이유를 돌려준다" | Policy Object에 가깝다. 규칙 판정이 중심이다. |

작게 외우면 이렇게 정리된다.

- **간단한 분기면**: 먼저 `if-else`로도 충분한지 본다.
- **실행 방법 교체가 핵심이면**: Strategy를 본다.
- **허용 여부, 이유, 금액 같은 판정이 핵심이면**: Policy Object를 본다.

### 오해 컷: 추상 클래스가 보여도 바로 Template Method는 아니다

`AbstractPaymentProcessor`가 `cardPay()`, `cashPay()` 같은 독립 메서드만 모아 두고, 호출자가 그중 하나를 골라 실행한다면 핵심은 여전히 **실행 방법 교체**라서 Strategy 쪽이다. 반대로 부모가 `validate -> charge -> record` 순서를 직접 고정하고 하위 클래스는 중간 단계만 채운다면 그때가 Template Method다. 즉 "추상 클래스가 있다"보다 "누가 흐름을 쥐는가"를 먼저 보면 비교 문서로 넘어가기 전에 혼동이 훨씬 줄어든다.

### 역방향 20초 브리지: `hook vs strategy`를 찾다가 여기로 왔다면

처음 배우는데 `hook vs strategy`를 검색했어도, 실제 첫 질문이 "언제 strategy를 쓰는지"라면 이 문서를 먼저 읽는 편이 빠르다.

| 지금 머릿속 질문 | 여기서 먼저 잡을 한 줄 | 다음 문서 |
|---|---|---|
| `hook 하나 더 열까, 전략으로 뺄까?` | 선택적 덧붙임이면 hook, 교체 규칙이면 strategy | [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) |
| `hook method가 왜 아니라 strategy죠?` | 부모가 흐름을 쥐지 않고 호출자가 구현을 고르면 strategy 쪽이다 | [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) |
| `처음 배우는데 strategy부터 큰 그림이 필요해요` | 큰 그림은 "호출자가 규칙 객체를 고른다"부터 고정한다 | 이 문서 계속 읽기 |

짧게 외우면 `hook`은 **고정 흐름 안의 선택적 빈칸**, `strategy`는 **호출자가 갈아끼우는 규칙 객체**다.

## Quick-Check 다음 갈림길

### Quick-Check 다음 갈림길

지금 감은 잡혔는데 beginner 기준으로 다음 문서가 헷갈리면 아래처럼 고른다.

| 지금 막힌 지점 | 바로 이어서 볼 문서 | 왜 여기로 가는가 |
|---|---|---|
| "객체지향 큰 그림부터 다시 깔고 오고 싶다" | [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md) | 전략이 다형성/추상화 위에서 서는 구조라는 점을 다시 한 장으로 맞춘다 |
| "`extends` 대신 객체를 들고 오는 감각이 아직 약하다" | [상속보다 조합 기초](./composition-over-inheritance-basics.md) | 전략을 조합의 대표 예시로 다시 붙인다 |
| "전략 말고 부모가 흐름을 쥐어야 하는 문제 같기도 하다" | [템플릿 메소드 패턴 기초](./template-method-basics.md) | **호출자가 규칙 객체를 고른다 vs 부모가 흐름을 쥔다**를 beginner 눈높이로 다시 자른다 |

## 처음 배우는데 큰 그림부터

처음 배우는데 가장 빨리 잡아야 할 큰 그림은 이것이다.

- 부모 클래스를 늘려서 공통 흐름을 잡고 싶다: 템플릿 메소드/상속 쪽 질문
- 호출자나 DI가 "이번에는 이 구현을 써"라고 객체를 넣어 준다: 전략/조합 쪽 질문

즉 전략 패턴은 "`Context`가 스스로 분기해서 고른다"보다 **호출자가 전략 객체를 골라 주입하고, `Context`는 그 객체에 위임한다**는 쪽에 가깝다.

짧게 외우면 다음 두 문장으로 충분하다.

- **상속은 부모가 뼈대를 쥔다**
- **전략은 호출자가 규칙 객체를 고른다**

## 한눈에 보기

```
Context (주문 처리)
    └─ Strategy 인터페이스 (pay)
            ├─ CardPayment
            ├─ CashPayment
            └─ VoucherPayment
```

| 역할 | 설명 |
|------|------|
| Context | 전략을 보유하고 실행 흐름을 가짐 |
| Strategy 인터페이스 | 공통 행동을 정의하는 추상화 |
| 구현체 (Concrete Strategy) | 실제 알고리즘/행동을 담은 클래스 |

## 상속 vs 조합으로 바로 자르기

전략 패턴은 "객체를 주입한다"는 말이 자주 같이 나온다. 이유는 단순하다.

| 질문 | 상속/템플릿 메소드 쪽 | 전략/조합 쪽 |
|------|----------------------|--------------|
| 누가 변화를 쥐는가 | 부모 클래스가 흐름을 쥔다 | 호출자, 설정, DI가 구현을 고른다 |
| 어떻게 연결되는가 | `extends`로 묶인다 | 필드/생성자로 전략 객체를 받는다 |
| 언제 잘 맞는가 | 순서를 꼭 고정해야 할 때 | 규칙을 바꿔 끼워야 할 때 |

그래서 "부모 클래스를 만들어야 하나, 객체를 주입해야 하나?"라는 질문이 나오면 전략 패턴 후보를 같이 봐야 한다.

## 구성 요소를 30초로만 보면

전략 패턴은 아래 세 역할만 기억해도 첫 읽기에는 충분하다.

- **Strategy 인터페이스** — 교체 가능한 행동의 공통 계약을 정의한다. 예: `PaymentStrategy.pay(int amount)`.
- **Concrete Strategy** — 인터페이스를 구현한 실제 알고리즘 클래스다. 예: `CardPaymentStrategy`, `CashPaymentStrategy`.
- **Context** — Strategy 인터페이스에 의존하며, 구체 구현은 모른다. 주입받거나 설정에서 받아 실행한다.

```java
public interface DiscountStrategy {
    int apply(int price);
}

public class VipDiscount implements DiscountStrategy {
    public int apply(int price) { return (int)(price * 0.8); }
}
```

## 흔한 오해와 함정

- **"if-else를 없애는 게 목적이다"** — 목적은 변경 축을 나누는 것이지 분기를 없애는 것이 아니다. 구현이 2개이고 단순하다면 if-else가 더 읽기 쉬울 수 있다.
- **"구현체 수가 많아야 전략이다"** — 구현체가 1개라도 교체 가능성이 있고 테스트에서 가짜를 넣어야 한다면 전략이 유용하다.
- **"전략 = 행동을 주입하는 모든 것"** — 람다나 함수도 넓게 보면 전략이지만, 이름 있는 역할·협력 객체·독립 테스트가 필요할 때 Strategy 타입으로 분리한다.
- **"전략은 `Context`가 알아서 고른다"** — 초보자가 자주 헷갈리지만, 전략 패턴의 핵심은 `Context`가 구현 선택 책임을 많이 갖지 않는다는 점이다. 보통 호출자, 설정, DI가 전략을 고른다.
- **"객체 주입이면 다 전략 패턴이다"** — 단순 서비스 의존성 주입과 교체 가능한 규칙 객체 주입은 다르다. 주입받는 대상이 "바뀌는 정책/알고리즘"일 때 전략에 가깝다.

### 미니 체크: selector/DI가 보일 때 먼저 물을 3문장

1. 이 클래스는 새 객체를 "만드나", 이미 있는 후보 중 하나를 "고르나"?
2. 고른 뒤 `Context`는 분기 대신 `strategy.apply()` 같은 공통 계약만 호출하나?
3. 새 규칙 추가 diff가 `Context` 본문보다 selector/설정/주입 wiring 쪽에 더 많이 생기나?

셋 중 2개 이상이 "예"면 초보자 관점에서는 "전략 + 선택 책임 분리"로 읽는 편이 안전하다.

## 실무에서 쓰는 모습

**결제 수단 선택**: `OrderService`는 `PaymentStrategy`에만 의존하고, 카드/현금/바우처 구현체는 런타임에 주입된다. 새 결제 수단이 추가돼도 `OrderService`는 그대로다.

**할인 정책 적용**: 회원 등급별로 다른 `DiscountStrategy`를 Map에 등록해두고 등급 키로 꺼내 실행한다. 등급이 늘어도 Map에 구현체만 추가한다.

생활 검색어로 바꾸면 같은 구조가 더 쉽게 보인다. `결제 전략`, `할인 전략`, `정책 교체`는 모두 "규칙 객체만 갈아끼우는가?"를 먼저 보면 된다.

| 생활 검색어 | 문서에서 먼저 볼 질문 | 보통 보는 구조 |
|---|---|---|
| 결제 전략 | 결제 방법만 갈아끼우는가? | `PaymentStrategy` 교체 |
| 할인 전략 | 할인 계산식만 바뀌는가? | `DiscountStrategy` 교체 |
| 정책 교체 | 상황별로 규칙 객체를 바꾸는가? | selector/DI가 전략 선택 |

## 다음 읽기

- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) — 상속으로 뼈대를 잡을지, 호출자가 전략 객체를 주입할지 바로 비교
- [상속보다 조합 기초](./composition-over-inheritance-basics.md) — 객체 주입과 조합이 왜 전략 패턴과 자주 같이 나오는지 큰 그림 정리
- [Strategy vs Policy Selector Naming](./strategy-policy-selector-naming.md) — strategy 자체와 strategy를 고르는 selector 경계를 더 짧게 자를 때
- [전략 (Strategy) — 심화](./strategy-pattern.md) — hook method, Context 결합 방식, 전략 선택 registry 구조처럼 심화 내용이 필요할 때만
- [Strategy vs Function: lambda로 충분한가](./strategy-vs-function-chooser.md) — lambda로 끝낼지, 이름 있는 Strategy 타입이 필요한지 볼 때

## Confusion Box

| 헷갈리는 쌍 | 먼저 던질 질문 | 빠른 기준 |
|---|---|---|
| Strategy vs if-else | "규칙이 자주 늘고 교체되는가?" | 반복 교체면 `Strategy`, 작고 고정된 분기면 `if-else`도 가능 |
| Strategy vs Policy Object | "실행 방법 교체인가, 판정 결과 계산인가?" | 행동 교체면 `Strategy`, 허용/이유/금액 판정이면 `Policy Object` |
| Strategy vs Template Method | "부모가 흐름을 쥐는가, 호출자가 구현을 고르는가?" | 호출자가 고르면 `Strategy`, 부모가 고정 흐름이면 `Template Method` |

## 한 줄 정리

전략 패턴은 "어떻게 할지"를 인터페이스 뒤로 숨겨 Context를 변경 없이 구현체를 교체할 수 있게 만드는 구조다.

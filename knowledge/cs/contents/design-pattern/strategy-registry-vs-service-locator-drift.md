---
schema_version: 2
title: "Strategy Registry vs Service Locator Drift Note"
concept_id: "design-pattern/strategy-registry-vs-service-locator-drift"
difficulty: beginner
doc_role: bridge
level: beginner
aliases:
  - strategy registry vs service locator
  - strategy lookup helper smell
  - strategy selector service locator
  - 전역 조회소 냄새
  - 숨은 의존성 조회
expected_queries:
  - strategy registry가 언제 service locator 냄새가 돼?
  - Map으로 전략을 찾는 helper가 숨은 의존성이 되는 기준은 뭐야?
  - payment strategy registry를 전역 조회소처럼 쓰면 왜 문제야?
  - strategy selector와 service locator를 리뷰에서 어떻게 구분해?
acceptable_neighbors:
  - contents/design-pattern/strategy-map-vs-registry-primer.md
  - contents/design-pattern/service-locator-antipattern.md
  - contents/design-pattern/injected-registry-vs-service-locator-checklist.md
companion_neighbors:
  - contents/software-engineering/dependency-injection-basics.md
---

# Strategy Registry vs Service Locator Drift Note

> 한 줄 요약: 전략을 key로 찾는 helper는 좁은 selector일 수 있지만, 아무 전략이나 전역에서 꺼내 주기 시작하면 service locator 냄새가 난다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [전략 패턴 기초](./strategy-pattern-basics.md)
> - [Strategy Map vs Registry Primer](./strategy-map-vs-registry-primer.md)
> - [Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들](./strategy-policy-selector-naming.md)
> - [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md)
> - [Registry Pattern: 객체를 찾는 이름표와 저장소](./registry-pattern.md)
> - [Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계](./service-locator-antipattern.md)

retrieval-anchor-keywords: strategy registry vs service locator drift, strategy lookup helper smell, strategy selector service locator, strategy registry service locator beginner, map<key strategy> service locator smell, strategy registry narrow selector, strategy lookup helper global locator, paymentstrategyregistry service locator drift, discountstrategyselector vs servicelocator, strategy collection hidden dependency lookup, global strategy registry smell, strategy registry drift note, 전략 레지스트리 서비스 로케이터, 전략 조회 helper 냄새, beginner strategy registry smell

---

## 먼저 머릿속 그림

전략 lookup helper는 원래 **작은 이름표 보관함**이다.

- `PaymentMethod.CARD`를 넣으면 `CardPaymentStrategy`를 돌려준다.
- `ShippingType.EXPRESS`를 넣으면 `ExpressShippingStrategy`를 돌려준다.

여기까지는 괜찮다.
문제는 이 helper가 점점 "결제 전략도, 알림 전략도, 외부 client도, repository도 이름만 주면 다 꺼내 주는 곳"이 될 때다.

짧게 외우면 된다.

**"한 종류의 전략만 고르면 selector, 아무 의존성이나 꺼내면 service locator."**

---

## 30초 비교표

| 질문 | 좁은 strategy registry / selector | Service locator drift |
|---|---|---|
| 값의 범위 | `PaymentStrategy`처럼 한 역할로 좁다 | 여러 종류의 service, client, repository까지 넓어진다 |
| key의 의미 | `PaymentMethod`, `ShippingType` 같은 domain key | bean name, class name, 임의 문자열 |
| 호출 위치 | 특정 use case가 생성자로 받아 쓴다 | 여러 곳에서 전역/static helper를 직접 부른다 |
| 반환 타입 | 보통 한 인터페이스로 고정된다 | `Object`, `<T> T get(Class<T>)`, `get(String)`처럼 넓다 |
| 테스트 | fake strategy map을 넣고 바로 테스트한다 | 전역 registry나 Spring context를 준비해야 한다 |

핵심은 helper 이름이 아니다.
`StrategyRegistry`라는 이름이어도 책임이 넓어지면 locator가 될 수 있다.

---

## 좋은 예: 좁은 전략 선택 helper

```java
public final class PaymentStrategySelector {
    private final Map<PaymentMethod, PaymentStrategy> strategies;

    public PaymentStrategySelector(Map<PaymentMethod, PaymentStrategy> strategies) {
        this.strategies = strategies;
    }

    public PaymentStrategy select(PaymentMethod method) {
        PaymentStrategy strategy = strategies.get(method);
        if (strategy == null) {
            throw new IllegalArgumentException("unsupported method: " + method);
        }
        return strategy;
    }
}
```

이 구조가 아직 안전한 이유는 단순하다.

- 다루는 값이 `PaymentStrategy` 한 종류다.
- key가 결제 도메인 값인 `PaymentMethod`다.
- 생성자에 필요한 lookup helper가 보인다.
- selector는 고르기만 하고, 전역 컨테이너를 뒤지지 않는다.

이때 `Map`은 strategy를 찾는 도구이고, 전체 흐름의 중심은 "어떤 결제 전략을 실행할까"다.
이 경계는 [Strategy Map vs Registry Primer](./strategy-map-vs-registry-primer.md)와 이어진다.

---

## 나쁜 예: 전역 전략 조회소로 미끄러진 경우

```java
public final class StrategyLocator {
    public static <T> T get(Class<T> type, String name) {
        return ApplicationContextProvider.getContext().getBean(name, type);
    }
}

public final class CheckoutService {
    public void pay(Order order) {
        String beanName = order.paymentMethod().name().toLowerCase() + "PaymentStrategy";
        PaymentStrategy strategy = StrategyLocator.get(PaymentStrategy.class, beanName);
        strategy.pay(order);
    }
}
```

겉으로는 "전략을 찾아 실행한다"처럼 보인다.
하지만 설계상 위험한 지점이 많다.

- `CheckoutService` 생성자만 봐서는 결제 전략 의존성이 보이지 않는다.
- 결제 도메인 key가 Spring bean name 규칙과 섞인다.
- `StrategyLocator`는 다른 타입도 꺼낼 수 있는 전역 통로가 된다.
- 단위 테스트가 plain object 생성이 아니라 context 준비에 묶인다.

이 경우는 strategy registry라기보다 [Service Locator Antipattern](./service-locator-antipattern.md)에 가까워진다.

---

## Drift 신호

아래 신호가 두세 개 이상 보이면 "strategy helper가 service locator로 변하고 있나?"를 묻는다.

- `PaymentStrategyRegistry`가 어느새 `NotificationStrategy`, `CouponPolicy`, `Repository`도 꺼낸다.
- public API가 `get(String)`, `get(Class<T>)`, `getAnything(...)`처럼 넓어진다.
- service 메서드 안에서 static helper나 `ApplicationContext.getBean(...)`을 직접 호출한다.
- key가 domain enum/value object가 아니라 bean name 문자열이다.
- 새 전략을 추가할 때 도메인 key 등록보다 component 이름 맞추기가 더 중요해진다.
- 테스트가 fake strategy 하나로 끝나지 않고 전역 registry 초기화 순서에 의존한다.

초보자용 판단 문장은 이것이다.

**"이 helper가 없어도 생성자만 보고 필요한 전략 후보를 말할 수 있는가?"**

말할 수 있으면 아직 좁은 selector일 가능성이 높다.
말하기 어렵다면 숨은 의존성 lookup을 의심한다.

---

## 어떻게 고치면 좋은가

처음부터 거창하게 바꾸지 말고 범위를 다시 좁힌다.

| 현재 모양 | 더 나은 방향 |
|---|---|
| `StrategyLocator.get(PaymentStrategy.class, beanName)` | `PaymentStrategySelector.select(PaymentMethod)` |
| `Map<String, Object>` | `Map<PaymentMethod, PaymentStrategy>` |
| 서비스 본문에서 `getBean` | 생성자로 selector나 strategy map 주입 |
| bean name 조합 | domain key를 registry 생성 시점에 검증 |
| 모든 전략 공용 locator | 결제, 배송, 할인처럼 use case별 selector 분리 |

Spring의 `Map<String, Bean>` 주입을 쓰는 것 자체가 나쁜 것은 아니다.
다만 그 `String`을 서비스 분기 기준으로 흘리기 전에 [Bean Name vs Domain Key Lookup](./bean-name-vs-domain-key-lookup.md)처럼 domain key registry로 감싸는 편이 안전하다.

---

## 흔한 오해

- **"`Map<Key, Strategy>`면 service locator인가요?"**
  아니다. 한 역할의 전략을 domain key로 찾고 생성자에 드러나면 좁은 registry/selector다.
- **"전략을 런타임에 고르면 전부 locator인가요?"**
  아니다. 런타임 선택은 전략 패턴의 정상 사용이다. 문제는 전역 조회로 의존성을 숨기는 것이다.
- **"`StrategyRegistry`라는 이름이면 괜찮나요?"**
  이름보다 public API와 사용 위치를 본다. `get(Class<T>)`처럼 넓어지면 이름과 달리 locator가 된다.
- **"selector와 registry 중 무엇이라 불러야 하나요?"**
  호출자의 입력으로 후보를 고르는 책임이 중심이면 selector, key로 등록된 후보를 찾는 저장소가 중심이면 registry가 더 자연스럽다.

## 한 줄 정리

Strategy lookup helper는 **한 역할의 전략 후보를 domain key로 고르는 동안에는 좁은 selector**다.
하지만 **전역에서 여러 의존성을 이름으로 꺼내 주는 통로**가 되면 service locator drift를 의심해야 한다.

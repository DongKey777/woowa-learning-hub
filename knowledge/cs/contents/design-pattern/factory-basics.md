# 팩토리 패턴 기초 (Factory Pattern Basics)

> 한 줄 요약: 팩토리 패턴은 객체를 어떻게 만들지를 호출자로부터 숨기고, 생성 책임을 한 곳에 모아 변경이 생겨도 호출 측 코드를 건드리지 않게 해준다.

**난이도: 🟢 Beginner**

관련 문서:

- [팩토리 (Factory) 심화](./factory.md)
- [Factory와 DI 컨테이너 Wiring: 프레임워크가 대신하는 생성, 남겨야 하는 생성](./factory-vs-di-container-wiring.md)
- [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [OOP 설계 원칙 기초](../software-engineering/oop-design-basics.md)

retrieval-anchor-keywords: factory pattern basics, 팩토리 패턴 기초, 객체 생성 패턴, 팩토리 메서드 입문, factory method beginner, when to use factory, 팩토리가 뭔가요, new 대신 팩토리, 생성 책임 분리, 팩토리 패턴 왜 쓰나요, beginner factory, 팩토리 패턴 예시, factory vs di container, spring bean factory method, handwritten factory vs @Bean

---

## 핵심 개념

팩토리 패턴은 **객체를 직접 `new`로 만드는 대신, 생성 책임을 별도 메서드나 클래스에 위임**하는 패턴이다. 호출자는 어떤 구현 클래스가 만들어지는지 알 필요 없이 원하는 타입의 객체를 받을 수 있다.

입문자가 자주 헷갈리는 것은 "그냥 `new` 쓰면 되는데 왜 팩토리를?"이다. 핵심은 **변경점 격리**다. 생성 로직이 여러 곳에 흩어지면, 구현 클래스 이름이나 생성자 시그니처가 바뀔 때 모든 호출 측을 수정해야 한다.

## 한눈에 보기

```
호출자
  │  createPayment("CARD")
  ▼
PaymentFactory ──→ CardPayment (implements Payment)
               ──→ CashPayment (implements Payment)
```

| 역할 | 설명 |
|------|------|
| 팩토리 메서드 | 객체를 만들어 반환하는 메서드 |
| 공통 인터페이스 | 호출자가 실제 구현을 몰라도 되게 해줌 |
| 구현 클래스 | 팩토리 안에서만 `new` 됨 |

## 상세 분해

팩토리 패턴은 세 가지 형태로 나뉜다.

- **정적 팩토리 메서드** — `Payment.of("CARD")` 처럼 같은 클래스 안의 정적 메서드로 생성. 가장 단순하며 Java의 `List.of()`, `Optional.of()`가 이 형태다.
- **팩토리 메서드 패턴** — 부모 클래스에 `createProduct()` 추상 메서드를 두고, 서브클래스가 어떤 객체를 만들지 결정한다.
- **추상 팩토리 패턴** — 연관된 객체 군(예: 버튼 + 다이얼로그)을 묶어 함께 생성하는 인터페이스. 팩토리 메서드보다 범위가 넓다.

입문 단계에서는 정적 팩토리 메서드와 기본 팩토리 메서드 패턴만 이해해도 충분하다.

## 흔한 오해와 함정

- **"팩토리 = 무조건 별도 클래스"** — 정적 팩토리 메서드처럼 같은 클래스 안에 둬도 팩토리 패턴이다. 복잡도에 맞게 형태를 선택한다.
- **"팩토리 쓰면 객체가 항상 새로 만들어진다"** — 팩토리는 캐싱이나 풀링된 객체를 반환할 수도 있다. 호출자는 신경 쓸 필요 없다.
- **"if/switch로 분기하면 팩토리가 아니다"** — 초기에는 if/switch도 충분하다. 분기가 폭증하면 레지스트리 기반으로 리팩터한다.

## 실무에서 쓰는 모습

결제 수단마다 다른 처리 객체가 필요할 때, 팩토리 메서드 하나로 수단 코드를 받아 알맞은 구현체를 반환한다. 호출 측은 `Payment payment = PaymentFactory.create(method)` 처럼 사용하고, 새 수단이 추가되면 팩토리만 수정한다.

Spring에서는 `@Bean` 메서드가 팩토리 메서드 역할을 한다. 설정 클래스에서 객체를 만들고, 컨테이너가 그 객체를 필요한 곳에 주입한다. 다만 애플리케이션 wiring이 핵심이면 손으로 `*ServiceFactory`를 늘리기보다 컨테이너에 맡기는 편이 자연스럽다. 이 경계는 [Factory와 DI 컨테이너 Wiring](./factory-vs-di-container-wiring.md)에서 예시로 이어서 볼 수 있다.

## 더 깊이 가려면

- [팩토리 (Factory) 심화](./factory.md) — 팩토리 메서드 vs 추상 팩토리 경계, 언제 정적 팩토리만으로 충분한지
- [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md) — 세 가지 생성 패턴의 선택 기준 비교

## 면접/시니어 질문 미리보기

> Q: 정적 팩토리 메서드와 생성자의 차이는?
> 의도: 팩토리의 장점을 이해하는지 확인한다.
> 핵심: 이름을 줄 수 있고, 반환 타입이 유연하며, 캐싱이 가능하다.

> Q: 팩토리 패턴이 필요한 시점은 언제인가?
> 의도: 무조건 적용이 아니라 트레이드오프를 아는지 확인한다.
> 핵심: 구현 클래스를 숨겨야 하거나, 생성 로직이 여러 곳에 흩어질 때다.

> Q: Spring `@Bean` 메서드가 팩토리 패턴과 어떤 관계인가?
> 의도: 패턴과 프레임워크를 연결하는지 확인한다.
> 핵심: `@Bean` 메서드가 팩토리 메서드이며, Spring 컨테이너가 그 반환 객체를 관리한다.

## 한 줄 정리

팩토리 패턴은 `new` 호출을 한 곳에 모아 호출자가 구현 클래스를 몰라도 되게 하며, 새 구현 추가 시 팩토리만 수정하면 되는 구조를 만든다.

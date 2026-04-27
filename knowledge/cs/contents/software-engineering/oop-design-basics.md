# 객체지향 설계 기초 (OOP Design Basics)

> 한 줄 요약: 객체지향 설계는 현실의 역할과 책임을 객체 단위로 나눠 협력하게 만드는 방식이며, 캡슐화·상속·다형성·추상화가 그 네 기둥이다.

**난이도: 🟢 Beginner**

관련 문서:

- [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md)
- [Java 상속과 오버라이딩 기초](../language/java/java-inheritance-overriding-basics.md) - 객체지향 큰 그림 뒤에 "상속 언제 쓰는지"를 더 좁게 읽어 갈 때 붙는 primer
- [추상 클래스 vs 인터페이스 입문](../language/java/java-abstract-class-vs-interface-basics.md) - 상속 primer 다음에 "부모가 흐름을 쥘지, 계약을 열지"를 beginner 관점으로 나누는 handoff primer
- [SOLID 원칙 기초](./solid-principles-basics.md)
- [Service 계층 기초](./service-layer-basics.md)
- [design-pattern 카테고리 인덱스](../design-pattern/README.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: oop design basics, 객체지향 설계 입문, 캡슐화 기초, 상속 기초, 다형성 기초, 추상화 기초, 객체지향 4원칙, 책임과 역할, 객체 협력 기초, encapsulation beginner, polymorphism beginner, 객체지향 뭐예요, beginner oop, 메시지 기반 협력, 객체지향 큰 그림

## 핵심 개념

객체지향 설계(OOP, Object-Oriented Programming)는 프로그램을 독립적인 객체들의 협력으로 구성한다. 각 객체는 데이터(상태)와 행동(메서드)을 함께 가지며, 서로 메시지를 주고받아 목적을 달성한다.

입문자가 가장 많이 헷갈리는 부분은 "클래스를 어떻게 나눌까"다. 핵심은 **역할과 책임**이다. 클래스는 현실의 명사가 아니라, 시스템 안에서 어떤 책임을 지고 어떤 메시지에 응답하는가로 설계한다.

## 한눈에 보기

| 원칙 | 한 줄 정의 | 위반 신호 |
|---|---|---|
| 캡슐화 | 내부 상태를 숨기고 메서드로만 접근 | 외부에서 필드 직접 수정 |
| 상속 | 공통 행동을 부모 클래스에서 물려받음 | 재사용 목적의 무분별한 상속 |
| 다형성 | 같은 메시지에 다른 객체가 다르게 응답 | `instanceof` 분기 남용 |
| 추상화 | 세부 구현을 숨기고 인터페이스만 노출 | 구현 클래스에 직접 의존 |

## 상세 분해

**캡슐화**

`Order` 객체가 주문 금액 계산 로직을 내부에 가지고 있으면, 외부는 `order.calculateTotal()`만 호출하면 된다. 금액 계산 방식이 바뀌어도 외부 코드를 수정할 필요가 없다. getter로 모든 필드를 노출하면 캡슐화가 깨진다.

**상속**

`Animal`을 상속한 `Dog`는 `makeSound()`를 오버라이드해 짖는 소리를 낸다. 단, 상속은 "is-a" 관계일 때만 써야 한다. 코드 재사용이 목적이라면 상속보다 조합(Composition)을 먼저 검토하는 것이 낫다.

**다형성**

`List<Shape>`에 `Circle`과 `Rectangle`을 넣고 `shape.draw()`를 호출하면, 각 구현 클래스가 자신의 방식으로 그린다. `if (shape instanceof Circle)` 분기 없이도 동작이 달라진다.

**추상화**

`PaymentProcessor` 인터페이스만 노출하면 카드 결제, 계좌이체, 포인트 결제 중 어느 구현이 들어오는지 몰라도 된다. 호출 코드가 구현 세부에 묶이지 않는다.

## 흔한 오해와 함정

- "상속이 항상 재사용의 답이다"라는 오해가 있다. 상속 계층이 깊어지면 부모 클래스 변경이 모든 자식에 파급된다. 조합(has-a)이 더 유연한 경우가 많다.
- getter/setter를 모두 노출하면 "객체지향을 썼다"고 오해하기도 한다. getter로 상태를 꺼내 외부에서 계산하면 캡슐화가 깨진다. 로직은 객체 안에 있어야 한다.
- "다형성은 인터페이스만 써야 한다"는 생각도 있다. 추상 클래스도 다형성을 제공한다. 차이는 공유 상태·기본 구현이 필요하면 추상 클래스, 계약만 표현하면 인터페이스다.

## 실무에서 쓰는 모습

`OrderService`가 `DiscountPolicy` 인터페이스에 의존하면, `FixedDiscountPolicy`와 `RateDiscountPolicy` 중 어느 구현이 주입되어도 서비스 코드는 바뀌지 않는다. 새 할인 정책 추가는 새 클래스 작성으로 끝난다.

`Order` 클래스가 상품 목록을 직접 가지고 `totalPrice()`를 계산하는 구조는 캡슐화와 응집도를 함께 보여 주는 교과서 예시다.

## 더 깊이 가려면

- [SOLID 원칙 기초](./solid-principles-basics.md) — OOP 원칙을 구체적인 설계 지침으로 발전시킨 SOLID
- [design-pattern 카테고리 인덱스](../design-pattern/README.md) — 다형성과 추상화를 코드 패턴으로 구체화한 GoF 패턴들

## 면접/시니어 질문 미리보기

- "상속 대신 조합을 써야 하는 기준은?" — 부모-자식이 진짜 is-a 관계가 아니거나 부모 클래스를 자유롭게 변경할 수 없는 상황이라면 조합이 낫다.
- "캡슐화를 잘 지킨다는 기준이 있나요?" — Tell, Don't Ask 원칙이 좋은 기준이다. 객체의 상태를 꺼내(Ask) 외부에서 판단하는 대신, 객체에게 무엇을 하라고 명령(Tell)하면 캡슐화가 유지된다.
- "다형성이 없다면 어떤 코드가 생기나요?" — 타입마다 `if-else` 또는 `switch` 분기가 생기고, 새 타입이 추가될 때마다 분기를 모두 찾아 수정해야 한다.

## 한 줄 정리

객체지향 설계는 캡슐화·상속·다형성·추상화라는 네 도구로 "변경이 퍼지지 않는" 경계를 만드는 일이다.

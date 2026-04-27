# 의존성 주입(DI) 기초 (Dependency Injection Basics)

> 한 줄 요약: 의존성 주입은 객체가 필요한 협력 객체를 스스로 생성하지 않고 외부에서 받는 설계 방식이며, 테스트와 교체를 쉽게 만든다.

**난이도: 🟢 Beginner**

관련 문서:

- [SOLID 원칙 기초](./solid-principles-basics.md)
- [Service 계층 기초](./service-layer-basics.md)
- [Spring IoC/DI 컨테이너](../spring/ioc-di-container.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: dependency injection basics, di 기초, 의존성 주입 입문, ioc 컨테이너 입문, new 직접 생성 문제, 객체 외부 주입, 생성자 주입 기초, 필드 주입 vs 생성자 주입, di 왜 쓰나요, 테스트 의존성 교체, spring di 입문, beginner di, dependency injection basics basics, dependency injection basics beginner, dependency injection basics intro

## 핵심 개념

의존성 주입(DI, Dependency Injection)은 클래스 안에서 `new`로 직접 생성하던 협력 객체를 외부에서 넘겨받는 방식이다.

직접 생성 코드:
```java
class OrderService {
    private OrderRepository repo = new JdbcOrderRepository(); // 구현에 직접 묶임
}
```

외부 주입 코드:
```java
class OrderService {
    private final OrderRepository repo;
    OrderService(OrderRepository repo) { this.repo = repo; } // 외부에서 받음
}
```

두 번째 방식이 DI다. 어떤 `OrderRepository`를 쓸지 결정권이 `OrderService` 밖으로 옮겨진다.

IoC(Inversion of Control, 제어의 역전)는 이 패턴의 상위 개념이다. 객체가 자신의 의존 객체를 관리하던 제어권을 외부 컨테이너(예: Spring)가 가져간다는 의미다.

## 한눈에 보기

| 방식 | 특징 | 주의점 |
|---|---|---|
| 생성자 주입 | 불변, 필수 의존성 강조, 테스트 용이 | 파라미터가 많아지면 설계 냄새 신호 |
| 세터 주입 | 선택적 의존성, 나중에 교체 가능 | 미주입 상태 실행 위험 |
| 필드 주입 (`@Autowired`) | 코드 짧음 | 테스트에서 주입 불가, final 불가 |

## 상세 분해

**왜 직접 생성이 문제인가**

`new JdbcOrderRepository()`를 서비스 안에 박으면 테스트할 때도 실제 DB가 필요해진다. DB를 가짜(Mock)로 교체하려면 서비스 코드를 수정해야 한다.

**생성자 주입이 권장되는 이유**

생성자 주입은 객체가 생성될 때 의존 객체가 반드시 있어야 한다는 계약을 명시한다. `final` 필드로 선언하면 불변성도 얻는다. 테스트 코드에서 `new OrderService(fakeRepo)`처럼 가짜 객체를 직접 넣을 수 있다.

**Spring의 역할**

Spring IoC 컨테이너는 `@Component`나 `@Bean`으로 등록된 객체를 관리하고, 의존 관계를 자동으로 연결(자동 와이어링)해 준다. 개발자는 `new`를 직접 쓰지 않아도 된다.

## 흔한 오해와 함정

- "DI와 IoC는 같은 말이다"는 오해가 많다. IoC는 넓은 패턴이고, DI는 IoC를 구현하는 한 가지 방법이다.
- 필드 주입(`@Autowired`)은 코드가 짧아 보이지만 테스트에서 의존성을 교체하기 어렵고, `final`을 사용할 수 없다. Spring 공식 문서도 생성자 주입을 권장한다.
- "DI를 쓰면 무조건 인터페이스가 필요하다"는 오해도 있다. 인터페이스 없이도 DI는 가능하다. 다만 교체 유연성을 얻으려면 인터페이스가 필요하다.

## 실무에서 쓰는 모습

Spring Boot 프로젝트에서 `@Service`가 붙은 `OrderService`가 `@Repository`가 붙은 `OrderRepository`를 생성자 주입으로 받는 구조가 가장 흔한 모습이다.

테스트에서는 `Mockito.mock(OrderRepository.class)`로 가짜 객체를 만들어 생성자에 넘긴다. DI 덕분에 DB 없이 서비스 로직만 단위 테스트할 수 있다.

## 더 깊이 가려면

- [Spring IoC/DI 컨테이너](../spring/ioc-di-container.md) — Spring이 DI를 어떻게 처리하는지 내부 구조
- [SOLID 원칙 기초](./solid-principles-basics.md) — DI가 DIP(의존 역전 원칙)와 어떻게 연결되는지

## 면접/시니어 질문 미리보기

- "생성자 주입과 필드 주입의 차이는?" — 생성자 주입은 불변, 테스트 용이, 순환 의존성을 컴파일 타임에 감지. 필드 주입은 리플렉션으로 주입해 테스트에서 직접 제어 불가.
- "DI가 없으면 어떤 문제가 생기나요?" — 협력 객체를 직접 생성하므로 구현에 강하게 묶이고, 테스트를 위해 프로덕션 코드를 수정해야 한다.
- "Spring 없이 DI를 구현할 수 있나요?" — 가능하다. 생성자에 의존 객체를 넘기면 DI다. Spring은 대규모 프로젝트에서 이 과정을 자동화하는 컨테이너다.

## 한 줄 정리

의존성 주입은 객체가 협력자를 스스로 만들지 않고 외부에서 받아 사용하는 방식이고, 이 단순한 변화가 테스트·교체·확장을 모두 쉽게 만든다.

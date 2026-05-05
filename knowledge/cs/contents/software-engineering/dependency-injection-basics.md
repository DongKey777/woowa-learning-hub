---
schema_version: 3
title: 의존성 주입(DI) 기초
concept_id: software-engineering/dependency-injection-basics
canonical: true
category: software-engineering
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
aliases:
- DI
- Dependency Injection
- 의존성 주입
- constructor injection
intents:
- definition
linked_paths:
- contents/spring/spring-ioc-di-basics.md
- contents/spring/ioc-di-container.md
expected_queries:
- DI가 뭐야?
- 왜 new 대신 주입받아?
- 생성자 주입은 왜 써?
- Spring 없이도 DI가 가능해?
contextual_chunk_prefix: |
  이 문서는 학습자가 필요한 도구(협력 객체)를 직접 만들지 않고 받아쓰면
  코드가 어떻게 더 시험하기 쉬워지는지, 객체가 자기 의존성을 외부에서
  받는 설계 원리를 처음 잡는 primer다. 필요한 도구 받아쓰기, 코드 시험
  쉬워지는 이유, new 대신 주입, 객체 조립을 외부에서 하기, 테스트 더블
  교체, 객체를 직접 만들지 않고 외부에서 받기 같은 자연어 paraphrase가 본
  문서의 큰 그림에 매핑된다.
---

# 의존성 주입(DI) 기초 (Dependency Injection Basics)

> 한 줄 요약: 의존성 주입은 객체가 필요한 협력 객체를 스스로 생성하지 않고 외부에서 받는 설계 방식이며, 테스트와 교체를 쉽게 만든다.

**난이도: 🟢 Beginner**

관련 문서:

- [SOLID 원칙 기초](./solid-principles-basics.md)
- [Service 계층 기초](./service-layer-basics.md)
- [Repository, DAO, Entity](./repository-dao-entity.md)
- [IoC와 DI 기초: 제어 역전과 의존성 주입이 왜 필요한가](../spring/spring-ioc-di-basics.md)
- [Spring IoC/DI 컨테이너](../spring/ioc-di-container.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: dependency injection basics, dependency injection what is, di 기초, di 처음, 의존성 주입 뭐예요, ioc랑 di 차이 헷갈림, di랑 bean 차이, spring 없이 di 가능한가, 왜 new 하면 안 돼요, 객체 외부 주입, 생성자 주입 기초, 생성자 주입 언제 쓰나요, 필드 주입 vs 생성자 주입, 테스트 의존성 교체, service repository 연결 누가 해요, 객체를 직접 만들지 않고 외부에서 받는 설계, 객체를 직접 만들지 않고 외부에서 받는 게 뭐야, wiring without new

## 먼저 잡는 멘탈 모델

DI를 처음 볼 때는 "어려운 프레임워크 기능"으로 외우기보다, 아래 한 장면으로 이해하는 편이 빠르다.

| 장면 | 지금 클래스가 하는 일 | 결과 |
|---|---|---|
| 직접 생성 | 필요한 협력 객체를 `new`로 직접 고른다 | 구현체가 바뀌면 내 코드도 같이 흔들린다 |
| DI | "나는 `OrderRepository`가 필요하다"만 말한다 | 실제 구현체 선택은 바깥에서 바꿀 수 있다 |

짧게 말하면 DI는 **객체가 협력자를 직접 고르는 책임을 바깥으로 미루는 설계**다.

## 지금 질문이라면 어디로 이어 읽나

| 지금 헷갈리는 질문 | 이 문서에서 먼저 잡을 것 | 다음 문서 |
|---|---|---|
| "왜 그냥 `new`하면 안 돼요?" | 결합도와 테스트 교체 비용 | 이 문서의 `핵심 개념` |
| "Service 안 `Repository`는 누가 넣어요?" | 주입과 컨테이너의 역할 분리 | [IoC와 DI 기초: 제어 역전과 의존성 주입이 왜 필요한가](../spring/spring-ioc-di-basics.md) |
| "Spring이 실제로 Bean을 어떻게 연결해요?" | DI와 컨테이너를 구분해서 보기 | [Spring IoC/DI 컨테이너](../spring/ioc-di-container.md) |
| "`DI`, `IoC`, `Bean`이 다 같은 말 같아요" | 용어가 가리키는 층위 구분 | 이 문서의 `DI / IoC / Bean 20초 구분표` |
| "Repository 인터페이스를 왜 두죠?" | 구현 교체와 책임 분리 | [Repository, DAO, Entity](./repository-dao-entity.md) |

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

두 번째 방식이 DI다. 어떤 `OrderRepository`를 쓸지 결정권이 `OrderService` 밖으로 옮겨진다. 처음에는 "객체를 받는 문법"보다 **구현체 선택 책임이 서비스 밖으로 빠진다**는 점이 더 중요하다.

IoC(Inversion of Control, 제어의 역전)는 이 패턴의 상위 개념이다. 객체가 자신의 의존 객체를 관리하던 제어권을 외부 컨테이너(예: Spring)가 가져간다는 의미다.

## DI / IoC / Bean 20초 구분표

처음에는 세 단어가 한 문장에 같이 나와서 같은 뜻처럼 들린다. 하지만 초급자 기준으로는 "설계 방식 / 더 큰 원리 / Spring 구현 단위"로만 자르면 충분하다.

| 단어 | 가장 짧은 뜻 | 주문 예시로 붙이면 |
|---|---|---|
| DI | 필요한 협력 객체를 외부에서 받는 방식 | `OrderService`가 `OrderRepository`를 생성자에서 받는다 |
| IoC | 객체 생성과 연결 제어권이 바깥으로 넘어간 상태 | `OrderService`가 직접 `new JdbcOrderRepository()`를 고르지 않는다 |
| Bean | Spring 컨테이너가 관리하는 객체 | `@Service OrderService`, `@Repository JdbcOrderRepository` |

- 짧게 외우면 `DI는 받는 방식`, `IoC는 제어권 이동`, `Bean은 Spring이 관리하는 객체`다.
- 그래서 Spring 없이도 생성자에 `OrderRepository`를 넘기면 DI이고, Spring은 그 연결을 자동화해 주는 도구다.

## 한눈에 보기

| 방식 | 특징 | 주의점 |
|---|---|---|
| 생성자 주입 | 불변, 필수 의존성 강조, 테스트 용이 | 파라미터가 많아지면 설계 냄새 신호 |
| 세터 주입 | 선택적 의존성, 나중에 교체 가능 | 미주입 상태 실행 위험 |
| 필드 주입 (`@Autowired`) | 코드 짧음 | 테스트에서 주입 불가, final 불가 |

초보자가 가장 자주 묻는 질문은 사실 "어떤 주입 방식을 외울까?"보다 "`new`를 지우면 뭐가 좋아지나?"다. 답은 아래 두 줄로 충분하다.

- 구현체를 바꿀 때 서비스 코드를 덜 건드린다.
- 테스트에서 가짜 객체를 넣어 서비스 로직만 따로 검증하기 쉬워진다.

## 상세 분해

**왜 직접 생성이 문제인가**

`new JdbcOrderRepository()`를 서비스 안에 박으면 테스트할 때도 실제 DB가 필요해진다. DB를 가짜(Mock)로 교체하려면 서비스 코드를 수정해야 한다.

**생성자 주입이 권장되는 이유**

생성자 주입은 객체가 생성될 때 의존 객체가 반드시 있어야 한다는 계약을 명시한다. `final` 필드로 선언하면 불변성도 얻는다. 테스트 코드에서 `new OrderService(fakeRepo)`처럼 가짜 객체를 직접 넣을 수 있다.

**Spring의 역할**

Spring IoC 컨테이너는 `@Component`나 `@Bean`으로 등록된 객체를 관리하고, 의존 관계를 자동으로 연결(자동 와이어링)해 준다. 개발자는 `new`를 직접 쓰지 않아도 된다.

## 같은 주문 예시로 보는 before / after

처음 읽을 때는 추상 용어보다 "주문 생성 서비스 하나"에 붙여 보는 편이 덜 헷갈린다.

| 코드 상태 | 서비스 코드에서 보이는 신호 | 초보자 기준 결과 |
|---|---|---|
| before | `new JdbcOrderRepository()`가 서비스 안에 박혀 있다 | 테스트에서 DB 없는 실행이 어렵다 |
| after | 생성자에서 `OrderRepository`를 받는다 | `FakeOrderRepository`나 mock으로 바꿔 끼우기 쉽다 |

예를 들어 주문 저장 방식을 메모리 저장소에서 JPA 저장소로 바꾸고 싶을 때, DI가 없으면 `OrderService`를 수정해야 한다. DI가 있으면 주입되는 구현체만 바꾸고 서비스 코드는 그대로 둘 수 있다.

## 테스트 더블로 바로 체감하는 작은 예시

초심자가 "`그래서 테스트가 왜 쉬워지는데요?`"에서 막히면, fake 하나 끼워 넣는 장면만 보면 된다.

```java
class FakeOrderRepository implements OrderRepository {
    private final List<Order> saved = new ArrayList<>();

    @Override
    public void save(Order order) {
        saved.add(order);
    }

    boolean contains(Order order) {
        return saved.contains(order);
    }
}

@Test
void 주문을_저장한다() {
    FakeOrderRepository fakeRepo = new FakeOrderRepository();
    OrderService service = new OrderService(fakeRepo);

    Order order = new Order("A-100", 2);
    service.place(order);

    assertThat(fakeRepo.contains(order)).isTrue();
}
```

- `OrderService`는 진짜 DB 대신 `FakeOrderRepository`를 받는다.
- 그래서 "저장 명령을 보냈는가"를 빠르게 확인할 수 있고, DB 연결 실패 같은 주변 변수 없이 서비스 규칙만 먼저 본다.
- 이 장면이 DI의 가장 실용적인 첫 이점이다.

## 흔한 오해와 함정

- "DI와 IoC는 같은 말이다"는 오해가 많다. IoC는 넓은 패턴이고, DI는 IoC를 구현하는 한 가지 방법이다.
- "DI는 Spring을 써야만 가능하다"는 오해도 많다. 생성자나 세터로 협력 객체를 외부에서 받으면 Spring 없이도 이미 DI다.
- 필드 주입(`@Autowired`)은 코드가 짧아 보이지만 테스트에서 의존성을 교체하기 어렵고, `final`을 사용할 수 없다. Spring 공식 문서도 생성자 주입을 권장한다.
- "DI를 쓰면 무조건 인터페이스가 필요하다"는 오해도 있다. 인터페이스 없이도 DI는 가능하다. 다만 교체 유연성을 얻으려면 인터페이스가 필요하다.
- "DI를 쓰면 Service가 아무 일도 안 하는 얇은 껍데기가 되어야 한다"는 뜻은 아니다. DI는 책임 분리 도구이지, 비즈니스 로직 금지 규칙이 아니다.

## 실무에서 쓰는 모습

Spring Boot 프로젝트에서 `@Service`가 붙은 `OrderService`가 `@Repository`가 붙은 `OrderRepository`를 생성자 주입으로 받는 구조가 가장 흔한 모습이다.

테스트에서는 `Mockito.mock(OrderRepository.class)`로 가짜 객체를 만들어 생성자에 넘긴다. DI 덕분에 DB 없이 서비스 로직만 단위 테스트할 수 있다.

## 더 깊이 가려면

- "왜 `new` 대신 주입받는가"를 Spring 맥락으로 다시 붙이고 싶다면 [IoC와 DI 기초: 제어 역전과 의존성 주입이 왜 필요한가](../spring/spring-ioc-di-basics.md)부터 읽는다.
- [Spring IoC/DI 컨테이너](../spring/ioc-di-container.md) — Spring이 DI를 어떻게 처리하는지 내부 구조
- [Repository, DAO, Entity](./repository-dao-entity.md) — 저장 책임과 인터페이스 경계를 같이 보기
- [SOLID 원칙 기초](./solid-principles-basics.md) — DI가 DIP(의존 역전 원칙)와 어떻게 연결되는지

## 면접/시니어 질문 미리보기

- "생성자 주입과 필드 주입의 차이는?" — 생성자 주입은 불변, 테스트 용이, 순환 의존성을 컴파일 타임에 감지. 필드 주입은 리플렉션으로 주입해 테스트에서 직접 제어 불가.
- "DI가 없으면 어떤 문제가 생기나요?" — 협력 객체를 직접 생성하므로 구현에 강하게 묶이고, 테스트를 위해 프로덕션 코드를 수정해야 한다.
- "Spring 없이 DI를 구현할 수 있나요?" — 가능하다. 생성자에 의존 객체를 넘기면 DI다. Spring은 대규모 프로젝트에서 이 과정을 자동화하는 컨테이너다.

## 한 줄 정리

의존성 주입은 객체가 협력자를 스스로 만들지 않고 외부에서 받아 사용하는 방식이고, 이 단순한 변화가 테스트·교체·확장을 모두 쉽게 만든다.

---
schema_version: 3
title: 'IoC와 DI 기초: 제어 역전과 의존성 주입이 왜 필요한가'
concept_id: spring/ioc-di-basics
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
aliases:
- IoC
- DI
- dependency injection
- 의존성 주입
- 제어 역전
intents:
- definition
linked_paths:
- contents/software-engineering/dependency-injection-basics.md
- contents/spring/ioc-di-container.md
- contents/design-pattern/factory-vs-di-container-wiring.md
- contents/design-pattern/service-locator-antipattern.md
expected_queries:
- DI가 뭐야?
- 의존성 주입이 뭐야?
- 왜 new 대신 DI를 써?
- IoC랑 DI 차이가 뭐야?
---

# IoC와 DI 기초: 제어 역전과 의존성 주입이 왜 필요한가

> 한 줄 요약: IoC는 객체 생성과 조립의 제어권을 개발자에서 컨테이너로 넘기는 원칙이고, DI는 그 구현 방법으로 컨테이너가 필요한 의존 객체를 주입해 결합도를 낮춘다.
>
> 문서 역할: 이 문서는 "IoC/DI가 왜 필요한가"를 먼저 잡는 입문 진입점이다. Bean 등록, component scan, 프록시 세부 동작은 다음 문서로 넘긴다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Bean과 DI 기초](./spring-bean-di-basics.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md)
- [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)
- [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: ioc di basics, 스프링 ioc di 가 뭐예요, 스프링 ioc di 처음 배우는데, spring ioc di beginner primer, ioc 제어 역전 입문, dependency injection 입문, spring di 왜 필요해요, 의존성 주입이 뭐예요, 왜 new 대신 di 를 써요, 결합도 낮추기 di, 테스트하기 좋은 코드 di, 구현체 교체 why di, spring 객체 조립 원리, ioc di what is, beginner spring di why

## 핵심 개념

처음에는 용어를 외우기보다 아래 한 줄 감각부터 잡으면 된다.

- IoC: "객체를 누가 만들고 연결할지"의 책임을 애플리케이션 코드 밖으로 넘긴다.
- DI: 그 책임을 넘긴 뒤, 필요한 객체를 실제로 "주입받는" 방식이다.

DI(Dependency Injection, 의존성 주입)를 처음 접하면 "왜 내가 `new`로 직접 만들면 안 되는가?"라는 질문이 자연스럽게 생긴다.

핵심은 **결합도**다. 내가 `new MemoryOrderRepository()`를 직접 쓰면 `OrderService`와 `MemoryOrderRepository`가 강하게 묶인다. 나중에 `JpaOrderRepository`로 바꾸고 싶을 때 `OrderService` 코드를 직접 수정해야 한다.

IoC(Inversion of Control, 제어 역전)는 이 조립 책임을 컨테이너에게 넘기는 원칙이다. DI는 그 방식으로 컨테이너가 의존 객체를 생성해서 주입한다.

## 한눈에 보기

```text
DI 없이:
  OrderService -> new MemoryOrderRepository()
  (OrderService가 구현체를 직접 선택)

DI 있음:
  OrderService <- (컨테이너가 OrderRepository를 주입)
  (OrderService는 인터페이스만 알면 됨)
```

| 비교 | `new` 직접 생성 | Spring DI |
|---|---|---|
| 구현체 결정 | 클래스가 직접 결정 | 컨테이너가 결정 |
| 테스트 | 구현체 교체 어려움 | mock으로 쉽게 교체 |
| 결합도 | 높음 | 낮음 |

| 용어 | 초급자용 질문 | 짧은 답 |
|---|---|---|
| IoC | "누가 객체를 만들고 연결해요?" | 컨테이너가 그 제어권을 가져간다 |
| DI | "그럼 필요한 객체는 어떻게 들어와요?" | 생성자나 setter 같은 통로로 주입된다 |

## 상세 분해

- **IoC**: "누가 객체를 만들고 연결할지"의 제어권을 애플리케이션 코드가 아니라 컨테이너가 갖는다는 원칙이다.
- **DI**: 그 제어권 역전을 실제 코드에 반영하는 방식이다. 객체가 필요한 의존성을 직접 만들지 않고 외부에서 받는다.
- **왜 필요한가**:
  - 구현체 교체가 쉬워진다
  - 테스트에서 mock 객체로 바꾸기 쉽다
  - 서비스가 "무엇이 필요한지"에만 집중할 수 있다
- **의존성 주입 방식 세 가지**:
  - 생성자 주입: 생성 시점에 의존성이 고정되어 불변 설계가 가능하다. Spring 권장 방식.
  - setter 주입: 선택적 의존성이나 나중에 변경할 가능성이 있을 때.
  - 필드 주입(`@Autowired`를 필드에 직접): 짧고 편하지만 테스트에서 주입이 어렵고 불변성도 없어 학습 예제 외에는 피한다.
- **인터페이스 기반 설계**: DI의 이점을 최대로 누리려면 구체 클래스 대신 인터페이스에 의존해야 한다. 컨테이너가 구현체를 바꿔 주입할 수 있다.

## 구체 예시로 한 번에 보기

처음에는 "repository 구현체를 바꾸는 순간 서비스 코드가 같이 바뀌는가?"만 봐도 감이 빨리 온다.

### 직접 `new`하는 경우

```java
public class OrderService {
    private final OrderRepository orderRepository = new MemoryOrderRepository();

    public Order findOrder(Long id) {
        return orderRepository.findById(id);
    }
}
```

이 코드는 지금은 단순하지만, `JpaOrderRepository`로 바꾸려면 `OrderService` 코드도 같이 고쳐야 한다.

### DI를 쓰는 경우

```java
public class OrderService {
    private final OrderRepository orderRepository;

    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public Order findOrder(Long id) {
        return orderRepository.findById(id);
    }
}
```

이제 `OrderService`는 "무엇이 필요하다"만 말하고, 실제 구현체 선택은 바깥으로 밀려난다. 초급자 기준으로는 이 차이가 가장 중요하다.

| 바꾸고 싶은 것 | 직접 `new` | DI |
|---|---|---|
| 저장소 구현체 교체 | 서비스 코드 수정 필요 | 주입 설정만 바꾸면 될 수 있다 |
| 테스트에서 가짜 객체 넣기 | 어렵다 | 생성자에 mock을 넣기 쉽다 |
| 서비스 관심사 | 구현체 선택까지 같이 떠안음 | 비즈니스 로직에 더 집중 |

## 같은 주문 요청에서 어디까지가 DI 질문인가

처음에는 `POST /orders` 같은 한 장면에서 MVC, Bean 등록, `@Transactional`이 전부 같이 보여서 "`DI가 요청도 처리하나요?`"처럼 섞여 묻기 쉽다. 이럴 때는 아래 표로 질문 축부터 다시 자르면 된다.

| 같은 주문 요청에서 보이는 장면 | 이걸 담당하는 축 | 지금 문서가 답하는가 |
|---|---|---|
| `/orders`가 어떤 컨트롤러로 가는가 | MVC 길찾기 | 아니오. [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md) |
| `OrderController` 안 `OrderService`는 누가 넣어 뒀나 | IoC/DI | 예. 이 문서 중심 질문이다 |
| `OrderService`와 `OrderRepository`를 Spring이 후보로 등록했나 | Bean 등록 / component scan | 일부만 다룬다. 다음은 [Spring Bean과 DI 기초](./spring-bean-di-basics.md) |
| `placeOrder()` 앞뒤에 commit/rollback이 왜 붙나 | 트랜잭션 프록시 | 아니오. [@Transactional 기초](./spring-transactional-basics.md) |

짧게 외우면 이렇다.

- MVC는 "`어디로 가나`"다.
- IoC/DI는 "`누가 연결했나`"다.
- Bean 문서는 "`그 후보를 어떻게 등록했나`"다.
- `@Transactional`은 "`어디까지 묶나`"다.

## 같은 `POST /orders`라도 먼저 보는 곳이 다르다

초급자에게 가장 흔한 혼동은 "`controller`, `service`, `transaction`이 한 요청에서 같이 보이니까 다 DI 이야기겠지"라고 묶어 버리는 것이다. 실제로는 같은 주문 요청도 질문 축이 다르면 먼저 보는 문서가 달라진다.

| 지금 먼저 튀어나온 말 | 먼저 보는 축 | 한 줄 판단 |
|---|---|---|
| "`/orders`가 왜 이 메서드로 안 가요?" | MVC | URL/HTTP 메서드 매핑과 바인딩 질문이다 |
| "`OrderService`는 누가 넣어 둔 거예요?" | IoC/DI | 객체 조립 책임이 컨테이너로 넘어간 장면이다 |
| "`bean missing`이 나요" | Bean 등록 | 후보를 scan하거나 `@Bean`으로 올렸는지 먼저 본다 |
| "`save()`는 됐는데 rollback이 이상해요" | 트랜잭션 | DI보다 service 경계와 프록시 호출을 먼저 본다 |

짧게 외우면 `요청은 MVC`, `연결은 DI`, `후보 등록은 Bean`, `작업 묶음은 @Transactional`이다. 그래서 같은 `POST /orders` 장면을 보더라도 "`누가 연결했나`"가 질문일 때만 이 문서가 정답에 가장 가깝다.

## 처음 막힐 때 4칸 비교

처음에는 "`왜 new 대신 주입해요?`", "`bean`이 뭐예요?", "`왜 `@Transactional`이 안 먹어요?`"가 전부 비슷한 Spring 자동화처럼 보인다. 아래 표처럼 "지금 묻는 문장이 무엇인가"만 나눠도 첫 문서를 훨씬 덜 헤맨다.

| 지금 입에서 먼저 나오는 말 | 이 질문의 중심 | 먼저 볼 문서 |
|---|---|---|
| "`왜 new 대신 주입해요?`" | 객체 조립 책임을 왜 밖으로 밀어내나 | 이 문서 |
| "`service bean`은 누가 등록해요?", "`bean missing`이에요" | Bean 후보를 어떻게 올리나 | [Spring Bean과 DI 기초](./spring-bean-di-basics.md) |
| "`/orders`가 왜 컨트롤러까지 안 가요?`" | 요청이 어디로 라우팅되나 | [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md) |
| "`save()`는 됐는데 rollback이 이상해요" | 어디까지 한 트랜잭션으로 묶나 | [@Transactional 기초](./spring-transactional-basics.md) |

같은 주문 예시를 한 줄씩만 붙이면 더 선명하다.

```text
앱 시작:
  OrderRepository Bean 등록 -> OrderService에 주입

요청 도착:
  /orders -> OrderController -> OrderService.placeOrder()

실행 중:
  필요하면 @Transactional 프록시가 placeOrder() 앞뒤를 감싼다
```

즉 IoC/DI 문서는 "왜 `OrderService`가 `OrderRepository`를 직접 `new`하지 않나"를 설명하는 자리다. 요청 라우팅이나 트랜잭션 경계까지 한 번에 해결하는 문서는 아니다.

## 흔한 오해와 함정

**오해 1: DI를 쓰면 코드가 복잡해진다**
처음에는 인터페이스, Bean 등록이 낯설어 복잡하게 느껴지지만, 프로젝트 규모가 커질수록 테스트가 쉬워지고 구현체 교체 비용이 줄어드는 효과가 명확해진다.

**오해 2: `@Autowired` 필드 주입이 제일 편하니 그냥 써도 된다**
필드 주입은 테스트에서 mock을 주입하려면 리플렉션을 써야 하고, 객체가 불완전한 상태로 만들어질 수 있다. 생성자 주입을 기본으로 쓰는 것이 Spring의 권장이다.

**오해 3: IoC와 DI는 같은 말이다**
IoC는 더 넓은 원칙(제어를 역전하라)이고, DI는 그 구현 방법 중 하나다. IoC는 DI 외에도 서비스 로케이터 패턴 등으로 구현할 수 있다.

## 처음 헷갈리는 질문 4개

| 헷갈리는 말 | 먼저 고정할 답 |
|---|---|
| "왜 그냥 `new`하면 안 돼요?" | 작은 예제에서는 가능하지만, 구현체 교체와 테스트가 어려워진다 |
| "IoC랑 DI가 같은 말 아닌가요?" | IoC는 원칙, DI는 그 원칙을 구현하는 대표 방법이다 |
| "DI면 무조건 인터페이스가 있어야 하나요?" | 항상 그런 것은 아니지만, 구현 교체 가능성을 열어 두려면 인터페이스가 유리하다 |
| "`@Autowired`만 붙이면 끝인가요?" | 주입 표시는 끝이 아니라 시작이다. 어떤 Bean이 등록됐는지와 후보가 하나인지도 같이 봐야 한다 |

## 실무에서 쓰는 모습

생성자 주입을 사용하는 가장 기본 패턴이다.

```java
@Service
public class OrderService {

    private final OrderRepository orderRepository;

    // Lombok @RequiredArgsConstructor 또는 직접 작성
    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public Order findOrder(Long id) {
        return orderRepository.findById(id);
    }
}
```

`OrderService`는 `OrderRepository`가 `MemoryOrderRepository`인지 `JpaOrderRepository`인지 알 필요가 없다. 컨테이너가 적절한 구현체를 결정해서 주입한다.

여기서 초반에는 두 가지만 기억하면 된다.

- 이 문서의 질문: "왜 직접 `new`하지 않고 주입받지?"
- 다음 문서의 질문: "그럼 Spring은 그 객체를 어디서 등록하고 어떻게 찾아오지?"

## 요청 흐름과 연결해서 이해하기

IoC/DI 문서를 따로 외우지 말고, 아래 한 장으로 붙여 읽으면 덜 헷갈린다.

```text
HTTP 요청 (예: GET /orders/1)
-> DispatcherServlet 이 OrderController 메서드로 라우팅
-> OrderController 가 OrderService 호출
-> OrderService 안의 orderRepository는 컨테이너가 이미 주입해 둔 Bean
```

핵심은 "요청은 MVC가 받고, 객체 연결은 DI가 맡는다"는 분리다.

처음 헷갈릴 때는 같은 장면을 아래처럼 다시 읽으면 된다.

| 먼저 떠오른 말 | 1차 판단 | 지금 바로 볼 문서 |
|---|---|---|
| "`왜 new 대신 주입해요?`" | 구현체 선택 책임을 밖으로 밀고 싶은가 | 이 문서 |
| "`bean`이 뭐예요?", "`component scan`은 뭐예요?" | 후보를 어떻게 등록하는지가 궁금한가 | [Spring Bean과 DI 기초](./spring-bean-di-basics.md) |
| "`@Transactional`이 왜 안 먹어요?" | 호출 경계와 프록시 문제인가 | [@Transactional 기초](./spring-transactional-basics.md) |
| "`404`, `400`이 먼저 보여요" | 요청 길찾기/바인딩 문제인가 | [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md) |

## 더 깊이 가려면

- Bean 등록, component scan, `@Configuration`, 프록시 감각은 [Spring Bean과 DI 기초](./spring-bean-di-basics.md)에서 이어서 본다.
- Bean 후보 선택, `@Primary`, `@Qualifier`, `BeanDefinition`, 생명주기 같은 컨테이너 내부 동작은 [IoC 컨테이너와 DI](./ioc-di-container.md)에서 이어서 본다.
- 저장소 레이어에서 DI가 어떻게 쓰이는지는 [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)를 같이 보면 연결이 명확해진다.
- HTTP 메서드와 컨트롤러 매핑부터 다시 올라오려면 [HTTP 메서드와 REST 멱등성 입문](../network/http-methods-rest-idempotency-basics.md) -> [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md) -> 이 문서 순서로 본다.

## 면접/시니어 질문 미리보기

> Q: IoC와 DI의 차이를 설명하면?
> 의도: 용어 구분 확인
> 핵심: IoC는 제어 역전 원칙, DI는 그 구현 방법으로 컨테이너가 의존 객체를 주입하는 것이다.

> Q: 생성자 주입을 권장하는 이유는?
> 의도: 주입 방식 트레이드오프 이해 확인
> 핵심: 불변 설계 가능, 테스트에서 mock 주입 용이, 필수 의존성을 생성 시점에 강제할 수 있다.

> Q: 인터페이스에 의존해야 DI가 효과적인 이유는?
> 의도: 결합도 개념 이해 확인
> 핵심: 구체 클래스에 의존하면 컨테이너가 구현체를 교체하는 이점이 없어진다.

## 한 줄 정리

IoC는 객체 조립 책임을 컨테이너에게 넘기는 원칙이고, DI는 그 원칙을 코드에 적용해 결합도를 낮추고 테스트를 쉽게 만드는 방법이다.

# Spring `404`/`405` vs Bean Wiring Error Confusion Card: 요청 매핑 실패와 DI 예외를 먼저 분리하기

> 한 줄 요약: `404`/`405`는 먼저 "요청이 어느 controller 매핑으로 가야 하는가"를 보는 문제이고, `NoSuchBeanDefinitionException`/`NoUniqueBeanDefinitionException`는 "Spring이 객체를 어떻게 등록하고 주입했는가"를 보는 문제다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 초급자가 `404`, `405`, bean wiring 예외를 한 덩어리로 오해하지 않도록 먼저 분리해 주는 **beginner troubleshooting card**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)
- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
- [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)
- [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: spring 404 vs bean error, spring 405 vs bean wiring, 404 405 vs nosuchbeandefinitionexception, 404 405 vs nouniquebeandefinitionexception, mapping error vs di error, request mapping vs bean wiring, controller mapping not found vs bean missing, request method not supported vs bean ambiguous, beginner spring troubleshooting order, spring first check order 404 bean, spring mvc mapping error before di, dispatcher servlet vs bean container confusion, no handler found vs no qualifying bean, 404 not found spring controller mapping, spring 404 405 vs bean wiring confusion card basics

## 먼저 mental model 한 줄

`404`/`405`는 **요청이 controller 매핑까지 잘 갔는지**를 묻는 신호이고,
bean wiring 예외는 **controller/service/repository 같은 객체가 앱 시작 때 잘 조립됐는지**를 묻는 신호다.

초급자 기준으로는 이 한 줄만 먼저 고정하면 된다.

- 요청 길찾기 문제: `404`, `405`
- 객체 조립 문제: `NoSuchBeanDefinitionException`, `NoUniqueBeanDefinitionException`

## 30초 비교표

| 보이는 증상 | 지금 먼저 갈라야 할 질문 | 보통 보는 위치 | 첫 체크 |
|---|---|---|---|
| `404 Not Found` | 이 URL에 맞는 handler/controller 매핑이 있나 | MVC 요청 매핑 | 경로, `@RequestMapping`, `@GetMapping`, context-path |
| `405 Method Not Allowed` | URL은 맞는데 HTTP method가 틀렸나 | MVC 요청 매핑 | `GET`/`POST`/`PUT` 등 method 선언 |
| `NoSuchBeanDefinitionException` | 주입하려는 bean 후보가 0개인가 | Bean 등록/DI | scan 범위, stereotype annotation, `@Bean`, profile/condition |
| `NoUniqueBeanDefinitionException` | 후보는 있는데 2개 이상이라 못 고르나 | Bean 등록/DI | 구현체 수, `@Primary`, `@Qualifier` |

핵심은 "에러 화면이 보였다"가 아니라 **어느 층에서 실패했는지**다.

## 첫 체크 순서

1. 먼저 에러 이름이나 HTTP status를 본다.
2. `404`나 `405`면 controller 매핑부터 본다.
3. `NoSuchBeanDefinitionException`나 `NoUniqueBeanDefinitionException`면 DI/bean 등록부터 본다.
4. 로그에 `UnsatisfiedDependencyException`만 보여도, 안쪽 cause에 bean 예외가 있는지 끝까지 본다.

초급자용으로 더 짧게 줄이면 아래 한 줄이다.

```text
404/405 = 요청 길찾기, NoSuch/NoUnique = 객체 조립
```

## 작은 예시 하나로 분리하기

### 경우 1. `404` 또는 `405`

```java
@RestController
@RequestMapping("/orders")
public class OrderController {

    @GetMapping("/{id}")
    public OrderResponse find(@PathVariable Long id) {
        return new OrderResponse(id);
    }
}
```

- `GET /orders/1`은 맞을 수 있다.
- `POST /orders/1`이면 같은 URL이라도 `405`가 날 수 있다.
- `GET /order/1`처럼 경로가 다르면 `404`가 날 수 있다.

이때 초급자 첫 질문은 "`OrderService` bean이 없나?"가 아니라
**"내 요청 URL과 HTTP method가 controller 매핑과 맞나?"**다.

### 경우 2. `NoSuchBeanDefinitionException`

```java
@Service
public class OrderService {

    private final DiscountPolicy discountPolicy;

    public OrderService(DiscountPolicy discountPolicy) {
        this.discountPolicy = discountPolicy;
    }
}
```

```java
public class FixedDiscountPolicy implements DiscountPolicy {
}
```

`FixedDiscountPolicy`가 Spring bean으로 등록되지 않았다면 앱 시작 중 주입 실패가 날 수 있다.

이때 초급자 첫 질문은 "`/orders` 경로가 틀렸나?"가 아니라
**"`DiscountPolicy` 구현체가 scan 또는 `@Bean` 등록에 들어왔나?"**다.

## 자주 헷갈리는 장면

| 헷갈리는 말 | 왜 헷갈리나 | 더 안전한 해석 |
|---|---|---|
| "컨트롤러가 안 떠서 404인가요?" | controller bean 생성 실패와 URL 매핑 실패를 한 문장으로 섞기 쉽다 | 먼저 로그에 bean 예외가 있는지, 아니면 단순 HTTP `404` 응답인지 분리한다 |
| "`No qualifying bean`이니까 URL을 못 찾은 건가요?" | "못 찾았다"는 표현이 둘 다 들어간다 | bean 예외의 "못 찾았다"는 URL이 아니라 **주입 후보**를 못 찾았다는 뜻이다 |
| "같은 URL인데 왜 405죠?" | 초급자는 URL mismatch만 떠올리기 쉽다 | `405`는 경로보다 **HTTP method mismatch**일 때 자주 나온다 |

## 어디로 이어서 보면 되나

- `404`/`405`가 핵심이면 [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)로 가서 `HandlerMapping`부터 본다.
- 요청 처리와 Bean 컨테이너를 큰 그림으로 같이 붙이고 싶으면 [Spring 요청 파이프라인과 Bean Container 기초](./spring-request-pipeline-bean-container-foundations-primer.md)로 간다.
- bean 후보 0개/2개 이상 분기가 핵심이면 [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)로 바로 내려간다.
- scan 누락이 의심되면 [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)을 먼저 본다.

## 한 줄 정리

초급자 기준 첫 분기는 이것 하나면 충분하다.
`404`/`405`는 **요청 매핑 문제**, `NoSuchBeanDefinitionException`/`NoUniqueBeanDefinitionException`는 **Bean 등록·주입 문제**다.

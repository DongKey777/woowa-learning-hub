# Spring Open Session In View Trade-offs

> 한 줄 요약: OSIV는 지연 로딩을 편하게 해주지만, 조회 경계와 웹 응답 경계를 섞어 트랜잭션과 커넥션 점유 시간을 늘릴 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Cache 추상화 함정](./spring-cache-abstraction-traps.md)
> - [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)

retrieval-anchor-keywords: open session in view, OSIV, persistence context, lazy loading, detached entity, N+1, transaction boundary, view rendering

## 핵심 개념

OSIV(Open Session In View)는 웹 요청이 끝날 때까지 영속성 컨텍스트를 열어 두는 방식이다.

이 방식의 의도는 단순하다.

- 서비스 계층에서 엔티티를 가져온 뒤
- 컨트롤러나 JSON 직렬화 단계에서
- 지연 로딩이 필요해도 예외 없이 접근하게 하려는 것

문제는 이 편의가 **조회 경계와 응답 경계**를 하나로 만들어 버린다는 점이다.

- 서비스에서는 끝났다고 생각한 쿼리가
- 컨트롤러 직렬화 중에 다시 나갈 수 있다
- 커넥션 점유 시간이 응답 렌더링까지 늘어난다
- 어떤 필드가 실제로 쿼리를 유발하는지 추적이 어려워진다

OSIV는 "lazy loading을 쓸 수 있느냐"보다 **어디까지 DB 접근을 허용할 것인가**의 문제다.

## 깊이 들어가기

### 1. OSIV가 열어 두는 것은 단순 세션이 아니다

JPA 관점에서 중요한 것은 영속성 컨텍스트와 커넥션 점유다.

흐름은 보통 이렇게 보인다.

```text
HTTP request
  -> controller
  -> service transaction
  -> repository
  -> commit
  -> view / JSON serialization
  -> lazy association access
  -> additional query
```

이때 서비스 트랜잭션은 끝났는데, 영속성 컨텍스트는 요청 끝까지 살아 있을 수 있다.

즉, 커밋은 끝났지만 엔티티 접근은 계속 가능하다.
이게 편리함의 원천이지만, 동시에 "응답 생성 중 쿼리"라는 숨은 비용을 만든다.

### 2. OSIV는 N+1을 더 늦게 드러나게 한다

서비스에서 리스트를 가져오고, 응답 직렬화 과정에서 연관 엔티티를 접근하면 N+1이 뒤늦게 터진다.

```java
@GetMapping("/orders")
public List<OrderResponse> orders() {
    return orderService.findAll().stream()
        .map(OrderResponse::from)
        .toList();
}
```

`OrderResponse::from`이 `order.getMember().getName()` 같은 lazy 필드를 읽는 순간 추가 쿼리가 발생할 수 있다.

문제는 이 쿼리가 서비스 로그가 아니라 직렬화 로그 근처에서 튀어나온다는 점이다.

### 3. 커넥션 점유 시간이 길어질 수 있다

OSIV가 켜져 있으면 요청 후반까지 persistence context가 살아 있어, 느린 렌더링이나 큰 JSON 응답이 커넥션과 함께 길어질 수 있다.

특히 다음 상황에서 더 위험하다.

- 응답 객체가 크다
- 직렬화가 복잡하다
- 템플릿 렌더링이 무겁다
- 응답 중 lazy association 접근이 많다

이건 단순히 "DB 쿼리가 한 번 더 돈다"가 아니라, **동시성 수용량이 줄어드는 문제**로 이어진다.

### 4. OSIV는 디버깅을 어렵게 만든다

트랜잭션 밖에서 엔티티를 건드려도 동작하므로, 개발 단계에서는 문제가 안 보일 수 있다.

하지만 운영에서는 다음과 같은 문제가 생긴다.

- 어떤 코드가 쿼리를 유발했는지 추적이 어렵다
- 특정 응답만 느린 이유를 찾기 어렵다
- 서비스 계층이 아닌 view 계층에서 DB가 터진다

즉, OSIV는 숨은 DB 접근을 허용하는 대신 **문제의 위치를 늦게 드러내는 구조**다.

## 실전 시나리오

### 시나리오 1: JSON 직렬화 중 lazy loading이 발생한다

```java
@RestController
public class OrderController {
    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @GetMapping("/orders/{id}")
    public Order order(@PathVariable Long id) {
        return orderService.findById(id);
    }
}
```

컨트롤러가 엔티티를 그대로 반환하면 Jackson 직렬화 단계에서 연관 필드를 접근할 수 있다.

OSIV가 켜져 있으면 예외는 안 날 수 있지만, 대신 뒤늦은 쿼리와 N+1이 숨어 버린다.

### 시나리오 2: read-only 조회처럼 보이는데 쓰기 플러시가 섞인다

조회 API라고 생각했는데, 영속성 컨텍스트가 살아 있어서 다른 객체의 변경이 우연히 flush될 수 있다.

이 문제는 [@Transactional 깊이 파기](./transactional-deep-dive.md)에서 보는 `readOnly`와 flush 전략 문제와 같이 봐야 한다.

### 시나리오 3: 커넥션 풀이 갑자기 부족해진다

응답 렌더링 시간이 늘어나면 DB 커넥션 반납도 늦어진다.

- 커넥션 풀 대기 증가
- p99 상승
- 트래픽이 늘지 않아도 DB가 더 바빠 보임

즉, OSIV는 코드 가독성의 문제가 아니라 **운영 용량**의 문제이기도 하다.

## 코드로 보기

### OSIV가 문제를 숨기는 전형적인 코드

```java
@Entity
public class Order {
    @Id
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    private Member member;

    public String memberName() {
        return member.getName();
    }
}
```

```java
@Transactional(readOnly = true)
public List<Order> findAll() {
    return orderRepository.findAll();
}
```

이후 controller나 serializer가 `memberName()`을 호출하면 추가 쿼리가 늦게 발생할 수 있다.

### DTO로 경계를 닫는 방식

```java
@Transactional(readOnly = true)
public List<OrderResponse> findAll() {
    return orderRepository.findAllWithMember().stream()
        .map(order -> new OrderResponse(
            order.getId(),
            order.getMember().getName()
        ))
        .toList();
}
```

```java
public record OrderResponse(Long id, String memberName) {
}
```

이 방식은 service 내부에서 필요한 데이터를 다 꺼내 응답 경계를 명확히 닫는다.

### OSIV 비활성화 예시

```yaml
spring:
  jpa:
    open-in-view: false
```

OSIV를 끄면 늦은 lazy loading이 더 빨리 드러난다.
처음에는 불편하지만, 경계를 정리하기에는 오히려 좋다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| OSIV on | 개발이 편하고 lazy loading 예외가 적다 | 숨은 쿼리와 커넥션 점유가 늘어난다 | 단순 CRUD와 전환기 |
| OSIV off | DB 접근 경계가 명확하다 | DTO 설계와 fetch 전략이 필요하다 | 서비스 경계를 명확히 관리할 때 |
| 엔티티 직접 반환 | 코드가 짧다 | 직렬화가 DB 접근을 유발할 수 있다 | 거의 권장하지 않음 |
| DTO projection | 응답이 안정적이다 | 조회별 매핑 코드가 늘어난다 | 운영 안정성이 중요할 때 |

핵심은 OSIV가 "좋다/나쁘다"가 아니라, **응답 계층에서 DB 접근을 허용할 것인지**다.

## 꼬리질문

> Q: OSIV를 끄면 왜 lazy loading 예외가 더 잘 드러나는가?
> 의도: 경계가 어디서 닫히는지 이해하는지 확인
> 핵심: 트랜잭션 종료 후 엔티티 접근이 불가능해지기 때문이다.

> Q: OSIV가 성능 문제를 만드는 이유는 무엇인가?
> 의도: 커넥션 점유와 응답 렌더링 비용 이해 확인
> 핵심: 커넥션과 영속성 컨텍스트가 더 오래 살아남을 수 있다.

> Q: 엔티티를 바로 반환하면 왜 위험한가?
> 의도: 직렬화와 DB 접근의 결합 이해 확인
> 핵심: JSON 변환 중 lazy association 접근이 일어날 수 있다.

> Q: OSIV 대신 무엇을 기본 전략으로 두는가?
> 의도: 실무적 대안 선택 기준 확인
> 핵심: 서비스에서 DTO로 필요한 데이터를 미리 완성하는 방식이다.

## 한 줄 정리

OSIV는 lazy loading 편의성을 주지만, 조회와 응답의 경계를 흐려 숨은 쿼리와 긴 커넥션 점유를 만들 수 있다.

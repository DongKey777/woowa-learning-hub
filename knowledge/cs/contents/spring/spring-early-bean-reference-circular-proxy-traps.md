# Spring Early Bean References and Circular Proxy Traps

> 한 줄 요약: 순환 의존성과 early bean reference는 단순 startup 에러가 아니라, 프록시가 붙기 전의 raw target이나 반쯤 초기화된 객체가 노출될 수 있는 지점이어서 `@Transactional`, `@Async`, `@Validated` 같은 프록시 기능이 조용히 어긋날 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
> - [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)
> - [Spring BeanFactoryPostProcessor vs BeanPostProcessor Lifecycle](./spring-beanfactorypostprocessor-vs-beanpostprocessor-lifecycle.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
> - [Spring Startup Bean Graph Debugging Playbook](./spring-startup-bean-graph-debugging-playbook.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)

retrieval-anchor-keywords: circular dependency, early bean reference, BeanCurrentlyInCreationException, getEarlyBeanReference, singletonObjects, earlySingletonObjects, singletonFactories, raw target injection, circular proxy trap

## 핵심 개념

Spring은 보통 Bean을 끝까지 만든 뒤 post processor를 거쳐 프록시를 붙인다.

그런데 순환 의존성이 있으면 일부 경우에는 Bean이 완전히 초기화되기 전에 "early reference"를 노출해야 할 수 있다.

여기서 문제가 생긴다.

- 누군가는 raw target을 받는다
- 컨테이너 최종 등록본은 proxy다
- 혹은 아예 `BeanCurrentlyInCreationException`으로 실패한다

즉 순환 의존성 문제는 단순히 "서로 참조해서 안 된다"가 아니라, **어느 시점의 어떤 객체가 누구에게 주입됐는가**의 문제다.

## 깊이 들어가기

### 1. constructor cycle과 setter/field cycle은 체감이 다르다

constructor injection 순환은 보통 즉시 실패한다.

```java
class A {
    A(B b) {}
}

class B {
    B(A a) {}
}
```

둘 다 완성 전의 상대가 필요하므로 Spring이 안전하게 풀기 어렵다.

반면 setter/field injection은 생성 자체는 먼저 하고, 나중에 의존성을 주입할 수 있어서 일부 경우 early reference로 이어질 수 있다.

이게 "setter 주입이면 순환이 해결된다"는 뜻은 아니다.

오히려 **반쯤 만든 객체를 노출하는 대가**가 생길 수 있다.

### 2. early singleton exposure는 세 단계 캐시로 이해하면 감이 온다

개념적으로 보면 Spring singleton 생성 과정은 아래 세 저장소 감각으로 이해할 수 있다.

- `singletonObjects`: 완전히 만들어진 최종 singleton
- `earlySingletonObjects`: 아직 완성 전이지만 조기 노출된 참조
- `singletonFactories`: 필요하면 early reference를 만들 수 있는 팩토리

이 구조 덕분에 일부 순환 참조는 풀 수 있다.

하지만 여기서 중요한 건 조기 노출된 참조가 **최종 프록시와 같으리라는 보장이 항상 자동으로 성립하는 것은 아니라는 점**이다.

### 3. 프록시 기능은 early reference 경로와 맞물려야 한다

`@Transactional`, `@Async`, `@Validated` 같은 기능은 보통 BeanPostProcessor가 프록시를 붙여 만든다.

따라서 순환 참조 상황에서는 다음이 중요하다.

- early reference도 proxy여야 하는가
- 아니면 raw target이 새어 나가는가

이 문제를 다루기 위해 일부 post processor는 `getEarlyBeanReference` 같은 경로를 사용한다.

만약 조기 노출 경로와 최종 post-processing 결과가 어긋나면, 한쪽 빈은 raw target을 보고 컨테이너는 나중에 proxy를 최종본으로 등록할 수 있다.

그 결과는 매우 헷갈린다.

- 어떤 호출은 `@Transactional`이 된다
- 어떤 호출은 같은 타입인데도 안 된다
- startup은 겨우 통과했지만 런타임 의미가 일관되지 않다

### 4. 증상은 startup 실패보다 "이상한 동작"으로 더 자주 보인다

대표 증상은 아래와 같다.

- `BeanCurrentlyInCreationException`
- "not eligible for getting processed by all BeanPostProcessors" 류의 로그
- self-invocation이 아닌데도 프록시 기능이 빠진 것처럼 보임
- 특정 Bean만 raw class로 주입되어 타입/동작이 이상함

즉 순환 의존성은 에러가 명확할 때보다, **프록시 의미가 조용히 무너질 때 더 위험하다**.

### 5. `@Lazy`와 `ObjectProvider`는 응급 처치일 뿐 설계 이유를 남겨야 한다

순환 의존을 끊기 위해 아래를 쓸 수는 있다.

- `@Lazy`
- `ObjectProvider`
- 이벤트 발행
- 오케스트레이션 서비스 분리

이 중 `@Lazy`와 `ObjectProvider`는 실용적이다.

하지만 왜 늦게 조회해도 되는지 설명되지 않으면, 문제를 미루기만 한 셈이 된다.

좋은 기준은 다음과 같다.

- 정말 순환 관계가 도메인적으로 필요한가
- 아니면 orchestration 책임이 빠진 것인가
- 읽기/쓰기 책임이 섞인 것인가

### 6. 디버깅은 생성 순서와 최종 주입 대상을 분리해서 본다

문제가 생기면 다음 순서가 유용하다.

1. constructor cycle인지부터 본다
2. 어떤 Bean이 어떤 시점에 주입됐는지 본다
3. 실제 주입된 객체가 proxy class인지 raw class인지 확인한다
4. startup 로그의 BeanPostProcessor 경고를 확인한다
5. `@Lazy`로 가릴지, 구조를 분리할지 결정한다

핵심은 순환 그래프만 보는 것이 아니라, **최종 호출 경계가 프록시를 타는지**를 확인하는 것이다.

## 실전 시나리오

### 시나리오 1: `BeanCurrentlyInCreationException`이 난다

대개 constructor cycle이거나, 안전하게 조기 노출할 수 없는 그래프다.

이 경우는 우회 주입보다 구조 분리가 먼저다.

### 시나리오 2: startup은 되는데 `@Transactional`이 기대와 다르게 안 먹는다

순환 참조 중 한쪽에 raw target이 들어갔을 가능성을 의심할 수 있다.

특히 AOP 경계가 중요한 서비스끼리 서로 직접 참조하면 이런 문제가 숨어들기 쉽다.

### 시나리오 3: `@Lazy`를 붙였더니 일단 되지만 코드가 더 이해하기 어려워졌다

실제론 순환을 푼 게 아니라 지연 조회로 미뤄 놓았을 수 있다.

이 경우는 orchestration service나 domain event로 책임을 다시 나누는 편이 장기적으로 낫다.

### 시나리오 4: custom post processor를 넣은 뒤 특정 Bean만 이상하게 동작한다

Bean 생성/조기 참조/post-processing 순서가 얽혔을 수 있다.

이때는 lifecycle 훅과 early reference 경로를 함께 봐야 한다.

## 코드로 보기

### 위험한 constructor cycle

```java
@Service
public class OrderService {
    public OrderService(PaymentService paymentService) {
    }
}

@Service
public class PaymentService {
    public PaymentService(OrderService orderService) {
    }
}
```

### 지연 조회로 순환을 느슨하게 푸는 예

```java
@Service
public class PaymentService {

    private final ObjectProvider<OrderService> orderServiceProvider;

    public PaymentService(ObjectProvider<OrderService> orderServiceProvider) {
        this.orderServiceProvider = orderServiceProvider;
    }

    public void pay() {
        orderServiceProvider.getObject().markPaid();
    }
}
```

### 더 나은 방향: orchestration 분리

```java
@Service
public class OrderPaymentFacade {

    private final OrderService orderService;
    private final PaymentService paymentService;

    public void placeAndPay(OrderCommand command) {
        Long orderId = orderService.create(command);
        paymentService.pay(orderId);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 순환 구조 유지 | 당장 코드 이동이 적다 | 프록시, lifecycle, 테스트가 불안정해진다 | 가급적 피한다 |
| `@Lazy` / `ObjectProvider` | 빠르게 결합을 느슨하게 할 수 있다 | 설계 문제를 숨길 수 있다 | 임시 완충 또는 진짜 지연 조회가 필요한 경우 |
| orchestration 분리 | 호출 방향과 책임이 명확해진다 | 클래스 수가 늘어난다 | 유스케이스 조합이 순환을 만들 때 |
| 이벤트 기반 분리 | 직접 참조를 끊기 쉽다 | 비동기/정합성 설계가 필요하다 | 후속 처리나 느슨한 결합이 적합할 때 |

핵심은 순환 의존성 해결을 "에러 없애기"가 아니라, **프록시와 lifecycle이 안정적으로 동작하는 호출 방향을 회복하는 일**로 보는 것이다.

## 꼬리질문

> Q: constructor cycle이 특히 위험한 이유는 무엇인가?
> 의도: 생성 순서 제약 이해 확인
> 핵심: 둘 다 완성 전 상대 객체가 필요해 안전한 조기 노출이 어렵기 때문이다.

> Q: early bean reference와 프록시가 충돌하면 어떤 일이 생길 수 있는가?
> 의도: raw target 누출 위험 이해 확인
> 핵심: 어떤 빈은 raw 객체를 보고, 컨테이너는 나중에 proxy를 최종본으로 등록할 수 있다.

> Q: `@Lazy`는 왜 만능 해결책이 아닌가?
> 의도: 임시 우회와 구조 개선 구분 확인
> 핵심: 순환을 본질적으로 푼 것이 아니라 접근 시점을 늦춘 것일 수 있기 때문이다.

> Q: 순환 참조 문제를 디버깅할 때 가장 먼저 무엇을 볼 것인가?
> 의도: 문제 분해 순서 확인
> 핵심: constructor cycle인지, 실제 주입 객체가 proxy인지 raw인지부터 본다.

## 한 줄 정리

early bean reference와 순환 의존성 문제의 본질은 startup 에러 자체보다, 프록시가 붙기 전 객체가 새어 나가 호출 의미가 조용히 무너질 수 있다는 데 있다.

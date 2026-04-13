# AOP와 프록시 메커니즘

> 한 줄 요약: Spring AOP는 "마법"이 아니라, 빈 앞뒤에 프록시를 끼워 넣어 호출을 가로채는 구조다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Cache 추상화 함정](./spring-cache-abstraction-traps.md)
> - [Spring Method Validation Proxy Pitfalls](./spring-method-validation-proxy-pitfalls.md)
> - [Spring Security Method Security Deep Dive](./spring-security-method-security-deep-dive.md)

retrieval-anchor-keywords: proxy, advisor, pointcut, advice, target source, JDK dynamic proxy, CGLIB, self-invocation, exposeProxy, AopContext, proxyBeanMethods

---

## 핵심 개념

Spring AOP의 핵심은 **실제 객체(target)** 를 직접 호출하는 대신, **프록시(proxy)** 를 통해 메서드 호출을 한 번 거쳐 가게 만드는 것이다.

즉, 호출 흐름은 대략 이렇게 바뀐다.

```text
Client -> Proxy -> Advice(부가기능) -> Target
```

여기서 프록시는 다음 역할을 한다.

- 메서드 호출 전후에 공통 기능을 끼워 넣는다
- 조건에 따라 다른 로직을 실행한다
- 실제 객체를 감싸서 책임을 분리한다

Spring AOP가 자주 쓰이는 대표 사례는 다음과 같다.

- `@Transactional`
- 로깅
- 성능 측정
- 보안 검사
- 예외 변환

이 문서는 [IoC 컨테이너와 DI](./ioc-di-container.md)에서 이어지는 내용이다.  
Bean이 어떻게 생성되고, 그 Bean이 왜 프록시로 바뀔 수 있는지 이해해야 AOP가 보인다.

---

## 깊이 들어가기

### 1. Spring AOP는 언제 프록시를 만들까

Spring은 Bean 생성 후 `BeanPostProcessor` 단계에서 프록시를 만들 수 있다.  
즉, 실제 객체가 완성된 뒤에 감싸는 방식이다.

대략적인 흐름은 다음과 같다.

```text
Bean 생성 -> 의존성 주입 -> 초기화 -> BeanPostProcessor -> 프록시 생성 -> 컨테이너 등록
```

이 말은 곧, AOP는 객체 생성 그 자체를 바꾸는 게 아니라 **객체를 꺼내주는 시점과 호출 시점**을 바꾸는 것이다.

Spring 내부에서는 이 과정에 `Advisor`와 `Pointcut`이 함께 엮인다.

- Pointcut: 어디에 적용할지
- Advice: 무엇을 할지
- Advisor: 둘을 묶은 실행 단위

즉, 프록시는 단순 래퍼가 아니라 "적용 대상과 부가기능을 연결하는 실행 껍질"이다.

### 2. JDK Dynamic Proxy와 CGLIB 차이

Spring은 상황에 따라 두 가지 방식 중 하나를 쓴다.

| 방식 | 대상 | 장점 | 단점 |
|------|------|------|------|
| JDK Dynamic Proxy | 인터페이스 기반 | 표준 JDK 기능, 가볍다 | 인터페이스가 없으면 못 쓴다 |
| CGLIB | 클래스 기반 | 인터페이스 없이도 가능 | final 클래스/메서드 제약, 생성 비용이 더 크다 |

정리하면:

- 인터페이스가 있으면 보통 JDK Dynamic Proxy를 먼저 고려한다
- 인터페이스가 없으면 CGLIB가 필요하다
- Spring Boot에서는 설정과 상황에 따라 둘 중 하나가 자동 선택된다

### 3. 왜 self-invocation이 문제인가

프록시는 **외부에서 프록시 객체를 통해 들어오는 호출**만 가로챈다.

그런데 같은 클래스 내부에서 `this.someMethod()`처럼 호출하면, 그건 프록시를 거치지 않고 **실제 target 내부 호출**이 된다.

그래서 다음과 같은 일이 발생한다.

- 외부 호출에서는 `@Transactional`이 적용된다
- 내부 자기 호출에서는 트랜잭션이 적용되지 않는다

이게 self-invocation 문제다.

같은 이유로 다음도 자주 헷갈린다.

- `@Transactional`
- `@Cacheable`
- `@Async`
- `@Validated`
- `@PreAuthorize`

이들 모두 프록시 경계 밖의 내부 호출에서는 기대와 다를 수 있다.

### 4. "마법"처럼 보이는 이유

마법처럼 보이지만 실제로는 단순하다.

- 컨테이너가 Bean을 만들고
- 프록시가 그 Bean을 감싸고
- 호출을 프록시가 먼저 받아
- 필요하면 부가기능을 실행한 뒤 target으로 넘긴다

즉, 핵심은 **호출을 가로채는 래퍼 객체**다.  
이 구조를 이해하지 못하면 `@Transactional`이나 `@Cacheable`이 왜 어떤 때는 되고 어떤 때는 안 되는지 설명할 수 없다.

### 5. `AopContext`와 `exposeProxy`는 최후의 수단이다

가끔 현재 프록시를 직접 가져와 내부 호출을 우회하려는 시도가 있다.

```java
((OrderService) AopContext.currentProxy()).saveOrder();
```

이 방식은 동작할 수 있지만, 설계를 숨기기 쉽다.

- 설정이 필요하다
- 테스트가 불편하다
- 구조가 프록시 의존적으로 굳을 수 있다

보통은 메서드를 분리하거나 책임을 나누는 편이 더 낫다.

---

## 실전 시나리오

### 시나리오 1: `@Transactional`이 내부 호출에서 안 먹는다

```java
@Service
public class OrderService {

    public void placeOrder() {
        validate();
        saveOrder(); // 같은 클래스 내부 호출
    }

    @Transactional
    public void saveOrder() {
        // DB insert
    }
}
```

`placeOrder()`에서 `saveOrder()`를 직접 부르면 프록시를 거치지 않는다.  
그래서 `saveOrder()`에 붙은 `@Transactional`은 기대대로 동작하지 않을 수 있다.

이 문제는 [@Transactional 깊이 파기](./transactional-deep-dive.md)에서 더 자세히 이어진다.

### 시나리오 2: 인터페이스 없이 AOP를 적용하려다 예상과 다르게 동작한다

인터페이스가 없는 클래스에 JDK Proxy를 기대하면 적용이 안 된다.  
이 경우 CGLIB가 필요하다.

### 시나리오 3: final 클래스/메서드 때문에 CGLIB가 실패한다

```java
public final class PaymentService {
    public final void pay() {
        // CGLIB가 오버라이드할 수 없음
    }
}
```

CGLIB는 상속과 오버라이드를 기반으로 동작하므로 final 제약에 걸린다.

### 시나리오 4: `@Configuration(proxyBeanMethods = true)`가 왜 같은 계열 문제를 푸는가

설정 클래스 내부의 `@Bean` 메서드 호출도 결국 프록시 경계를 활용한다.

이 문맥은 [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)와 같이 보면 자연스럽다.

---

## 코드로 보기

### 1. 프록시가 호출을 가로채는 최소 예시

```java
public interface Service {
    void work();
}

public class RealService implements Service {
    @Override
    public void work() {
        System.out.println("target work");
    }
}

public class LoggingHandler implements java.lang.reflect.InvocationHandler {
    private final Object target;

    public LoggingHandler(Object target) {
        this.target = target;
    }

    @Override
    public Object invoke(Object proxy, java.lang.reflect.Method method, Object[] args) throws Throwable {
        System.out.println("before");
        Object result = method.invoke(target, args);
        System.out.println("after");
        return result;
    }
}

Service proxy = (Service) java.lang.reflect.Proxy.newProxyInstance(
    Service.class.getClassLoader(),
    new Class<?>[] { Service.class },
    new LoggingHandler(new RealService())
);

proxy.work();
```

이 코드는 Spring AOP의 원리를 아주 작게 축약한 것이다.  
Spring은 여기에 포인트컷, 어드바이스, 인터셉터 체인을 더 얹는다.

### 2. self-invocation 우회 예시

```java
@Service
public class OrderService {
    private final OrderService self;

    public OrderService(@Lazy OrderService self) {
        this.self = self;
    }

    public void placeOrder() {
        self.saveOrder(); // 프록시를 통해 호출
    }

    @Transactional
    public void saveOrder() {
        // transactional boundary
    }
}
```

이 패턴은 동작은 하지만, 너무 쉽게 남용하면 구조가 지저분해진다.  
보통은 메서드를 분리하거나 책임을 나누는 편이 더 낫다.

### 3. advisor chain을 이해하기 위한 관점

프록시는 최종적으로 여러 어드바이스를 순서대로 태울 수 있다.

- transaction advisor
- cache advisor
- validation advisor
- security advisor

순서와 조합이 중요하므로, "프록시가 있다"보다 "어떤 advisor가 붙었는가"를 보는 게 더 실전적이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| JDK Dynamic Proxy | 표준, 단순, 인터페이스 기반 설계에 잘 맞음 | 인터페이스 필요 | 서비스 계약이 명확할 때 |
| CGLIB | 인터페이스 없이도 적용 가능 | final 제약, 상속 기반 한계 | 레거시 클래스에 AOP를 붙여야 할 때 |
| 프록시 기반 AOP | 비침투적, 기존 코드 수정이 적음 | self-invocation 같은 함정이 있음 | Spring의 일반적인 공통 관심사 처리 |
| 직접 호출/수동 래핑 | 구조가 명시적이고 이해하기 쉬움 | 반복 코드가 늘어남 | 아주 단순한 코드나 특수한 성능 요구가 있을 때 |

핵심 판단 기준은 이렇다.

- 공통 기능이 많고 반복되면 AOP가 유리하다
- 호출 경로를 엄밀하게 추적해야 하면 프록시 함정을 경계해야 한다
- 내부 호출이 많고 트랜잭션 경계가 복잡하면 설계를 먼저 나눠야 한다

---

## 꼬리질문

> Q: `@Transactional`이 붙었는데 왜 어떤 메서드는 트랜잭션이 안 걸리나요?  
> 의도: 프록시 기반 AOP와 self-invocation 이해 여부 확인  
> 핵심: 외부 호출은 프록시를 거치지만 내부 `this` 호출은 거치지 않는다

> Q: JDK Dynamic Proxy와 CGLIB의 차이를 단순히 "인터페이스 유무"로만 설명해도 되나요?  
> 의도: 구현 방식과 제약까지 아는지 확인  
> 핵심: JDK는 인터페이스 기반, CGLIB는 상속 기반이라 final 제약과 생성 비용 차이가 있다

> Q: 프록시 기반 AOP가 왜 마법이 아닌가요?  
> 의도: Spring 내부 메커니즘을 추상화가 아니라 호출 흐름으로 이해하는지 확인  
> 핵심: Bean을 감싼 프록시가 메서드 호출을 가로채서 부가기능을 넣는 구조다

> Q: `AopContext.currentProxy()`는 왜 최후의 수단인가?
> 의도: 프록시 노출에 대한 설계 감각 확인
> 핵심: 구조를 프록시 API에 묶어 버릴 수 있기 때문이다.

---

## 한 줄 정리

Spring AOP는 target 객체를 직접 바꾸는 게 아니라, 프록시를 통해 호출을 가로채 공통 기능을 끼워 넣는 구조이며, 내부 자기 호출은 이 경로를 우회하기 때문에 주의해야 한다.

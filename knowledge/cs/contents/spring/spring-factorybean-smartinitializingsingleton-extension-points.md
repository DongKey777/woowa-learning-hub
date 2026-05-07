---
schema_version: 3
title: Spring FactoryBean and SmartInitializingSingleton Extension Points
concept_id: spring/factorybean-smartinitializingsingleton-extension-points
canonical: true
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
review_feedback_tags:
- factorybean-smartinitializingsingleton-extension
- points
- factorybean
- smartinitializingsingleton
aliases:
- FactoryBean
- SmartInitializingSingleton
- &beanName
- FactoryBean product object
- singleton after initialization hook
- startup callback
- bean factory product vs factory
intents:
- deep_dive
- troubleshooting
linked_paths:
- contents/spring/ioc-di-container.md
- contents/spring/spring-beanfactorypostprocessor-vs-beanpostprocessor-lifecycle.md
- contents/spring/spring-application-context-refresh-phases.md
- contents/spring/spring-configuration-proxybeanmethods-beanpostprocessor-chain.md
- contents/spring/spring-startup-bean-graph-debugging-playbook.md
expected_queries:
- Spring FactoryBean은 일반 Bean과 어떻게 달라?
- FactoryBean 자체를 꺼내려면 왜 &beanName을 써야 해?
- SmartInitializingSingleton은 @PostConstruct와 어떤 시점이 달라?
- 모든 singleton 초기화 이후 registry를 스캔하려면 어떤 hook을 써?
contextual_chunk_prefix: |
  이 문서는 FactoryBean이 Bean을 만드는 Bean이고, 컨테이너 조회 시 보통
  getObject() product가 노출된다는 점을 설명한다. &beanName으로 factory 자체를
  보는 규칙, SmartInitializingSingleton afterSingletonsInstantiated hook,
  @PostConstruct보다 늦은 startup callback을 다루는 advanced deep dive다.
---
# Spring `FactoryBean` and `SmartInitializingSingleton` Extension Points

> 한 줄 요약: `FactoryBean`은 "Bean을 만드는 Bean"이고 `SmartInitializingSingleton`은 "모든 singleton 초기화 이후" 훅이므로, 둘을 모르면 컨테이너 확장 코드를 만들 때 생성 시점과 제품 객체를 자주 혼동하게 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [Spring BeanFactoryPostProcessor vs BeanPostProcessor Lifecycle](./spring-beanfactorypostprocessor-vs-beanpostprocessor-lifecycle.md)
> - [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
> - [Spring Startup Bean Graph Debugging Playbook](./spring-startup-bean-graph-debugging-playbook.md)

retrieval-anchor-keywords: FactoryBean, SmartInitializingSingleton, &beanName, object produced by FactoryBean, singleton after initialization hook, container extension point, startup callback, bean factory product vs factory

## 핵심 개념

Spring 컨테이너는 단순히 클래스를 new 해서 주입하는 수준을 넘어서, Bean 생성 자체를 커스터마이징할 수 있는 여러 확장 지점을 제공한다.

그중 실무에서 은근히 헷갈리는 둘이 있다.

- `FactoryBean`
- `SmartInitializingSingleton`

핵심 차이는 이렇다.

- `FactoryBean`: "무엇을 만들지"를 커스터마이징한다
- `SmartInitializingSingleton`: "singleton들이 다 올라온 뒤 무엇을 할지"를 정한다

즉 하나는 **제품 객체 생산**, 다른 하나는 **시작 후 후처리 타이밍**이다.

## 깊이 들어가기

### 1. `FactoryBean`은 자기 자신보다 "생산물"이 중요하다

일반 Bean은 컨테이너에서 꺼내면 그 Bean 자신이 나온다.

하지만 `FactoryBean`은 다르다.

컨테이너가 이 Bean을 보면 보통 다음처럼 동작한다.

- factory bean 자신을 직접 주기보다
- `getObject()`가 만든 제품 객체를 Bean으로 취급한다

즉 `FactoryBean<Foo>`를 등록하면, 주입 지점에서는 `Foo`를 받는 감각에 가깝다.

이 차이를 모르면 "왜 타입이 안 맞지?" 또는 "왜 내가 등록한 클래스가 아니라 다른 객체가 나오지?" 같은 혼란이 생긴다.

### 2. factory 자체가 필요할 땐 `&beanName`으로 본다

Spring은 보통 `FactoryBean`의 산출물을 노출한다.

factory 자체가 필요하면 이름 앞에 `&`를 붙여야 한다.

```java
Object factoryItself = applicationContext.getBean("&clientFactory");
```

이 규칙을 모르면 디버깅 시 실제로 보고 싶은 대상이

- 생산된 client 객체인지
- 그걸 만드는 factory 객체인지

계속 섞인다.

### 3. `FactoryBean`은 복잡한 객체 생성 캡슐화에 맞다

다음처럼 단순 생성자를 넘는 조립이 필요할 때 자주 쓴다.

- proxy client 생성
- 외부 메타데이터 기반 객체 생성
- 라이브러리 adapter 인스턴스 래핑

즉 `FactoryBean`의 포인트는 "생성 로직이 복잡하다"가 아니라, **제품 객체를 Spring Bean 생태계에 자연스럽게 얹고 싶다**는 데 있다.

### 4. `SmartInitializingSingleton`은 `@PostConstruct`보다 늦다

`@PostConstruct`는 개별 Bean 초기화 직후다.

반면 `SmartInitializingSingleton#afterSingletonsInstantiated()`는 일반 singleton들이 모두 올라온 뒤에 호출된다.

이 차이가 중요한 이유:

- 다른 singleton들이 다 준비된 뒤 registry 스캔을 하고 싶을 때
- 여러 bean을 모아 테이블/매핑/메타데이터를 완성하고 싶을 때
- startup 시점에 "전체 그림"이 필요한 작업을 하고 싶을 때

즉 `SmartInitializingSingleton`은 **개별 Bean 초기화 훅이 아니라, singleton 집합이 준비된 뒤의 훅**이다.

### 5. 하지만 시작 작업을 다 여기에 넣으면 startup을 망칠 수 있다

이 훅은 유용하지만, 아래를 넣으면 위험하다.

- 무거운 외부 네트워크 호출
- 긴 캐시 preload
- 실패해도 되는 비필수 warmup

이런 작업은 startup critical path에 들어가 버릴 수 있다.

즉 `SmartInitializingSingleton`은 "나중에 시작되는 훅"이지만, 여전히 **startup 경로의 일부**라는 점을 잊으면 안 된다.

### 6. 컨테이너 디버깅에서는 둘의 역할을 분리해서 봐야 한다

다음 증상은 `FactoryBean` 의심:

- 실제 주입 객체 타입이 예상과 다르다
- `&beanName`과 일반 bean 조회 결과가 다르다
- 생성 로직이 숨겨져 있다

다음 증상은 `SmartInitializingSingleton` 의심:

- startup 후반부에만 실패한다
- 모든 bean이 뜬 뒤 registry 스캔에서 터진다
- 개별 Bean 초기화는 됐는데 마지막 wiring 단계에서 깨진다

즉 둘 다 "확장 포인트"지만, **어느 단계에서 개입하는지**가 완전히 다르다.

## 실전 시나리오

### 시나리오 1: 라이브러리 client를 Spring Bean처럼 노출하고 싶다

단순 `@Bean` 메서드보다 생성 로직과 제품 타입을 더 깔끔하게 캡슐화하고 싶다면 `FactoryBean`이 맞을 수 있다.

### 시나리오 2: 모든 handler bean을 모아 registry를 구성해야 한다

개별 handler의 `@PostConstruct`보다, 전체 singleton들이 준비된 뒤 한 번에 스캔하는 `SmartInitializingSingleton`이 더 자연스럽다.

### 시나리오 3: startup 마지막쯤 mysterious failure가 난다

개별 Bean 생성이 아니라 `afterSingletonsInstantiated()` 단계에서 실패했을 수 있다.

### 시나리오 4: 디버깅 중 bean 조회 결과가 예상 타입이 아니다

`FactoryBean`의 제품을 보고 있는지, factory 자체를 보고 있는지부터 확인해야 한다.

## 코드로 보기

### `FactoryBean`

```java
public class PaymentClientFactoryBean implements FactoryBean<PaymentClient> {

    @Override
    public PaymentClient getObject() {
        return new PaymentClient("https://api.example.com");
    }

    @Override
    public Class<?> getObjectType() {
        return PaymentClient.class;
    }
}
```

### `SmartInitializingSingleton`

```java
@Component
public class HandlerRegistryInitializer implements SmartInitializingSingleton {

    private final List<CommandHandler> handlers;

    public HandlerRegistryInitializer(List<CommandHandler> handlers) {
        this.handlers = handlers;
    }

    @Override
    public void afterSingletonsInstantiated() {
        // 모든 singleton handler가 준비된 뒤 registry 구성
    }
}
```

### factory 자체 조회

```java
Object factory = applicationContext.getBean("&paymentClientFactoryBean");
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 일반 `@Bean` | 단순하고 읽기 쉽다 | 복잡한 생성 캡슐화에는 약하다 | 보통의 객체 생성 |
| `FactoryBean` | 제품 생성 로직을 Spring Bean 계약 안에 숨길 수 있다 | factory와 product 개념이 헷갈리기 쉽다 | proxy client, adapter, 복잡한 생성 |
| `@PostConstruct` | 개별 Bean 초기화가 단순하다 | 전체 singleton 집합이 준비됐다는 보장이 약하다 | 가벼운 per-bean 초기화 |
| `SmartInitializingSingleton` | singleton 전체가 준비된 뒤 후처리가 가능하다 | startup 경로를 무겁게 만들 수 있다 | registry 스캔, 전체 초기화 조립 |

핵심은 `FactoryBean`과 `SmartInitializingSingleton`을 둘 다 "초기화 관련 기능"으로 뭉뚱그리지 않고, **생산물 제어와 startup 시점 제어라는 서로 다른 축**으로 보는 것이다.

## 꼬리질문

> Q: `FactoryBean`을 등록했을 때 컨테이너가 보통 노출하는 것은 무엇인가?
> 의도: factory vs product 구분 확인
> 핵심: factory 자신보다 `getObject()`가 만든 제품 객체다.

> Q: `&beanName`은 언제 필요한가?
> 의도: factory 자체 조회 규칙 확인
> 핵심: `FactoryBean`의 산출물이 아니라 factory 객체 자체를 보고 싶을 때다.

> Q: `SmartInitializingSingleton`이 `@PostConstruct`와 다른 점은 무엇인가?
> 의도: startup 시점 차이 이해 확인
> 핵심: 개별 Bean 초기화 직후가 아니라, 일반 singleton들이 모두 준비된 뒤 호출된다는 점이다.

> Q: 왜 `SmartInitializingSingleton`에 무거운 로직을 넣으면 안 좋은가?
> 의도: startup critical path 인식 확인
> 핵심: 애플리케이션 startup 경로를 직접 무겁게 만들 수 있기 때문이다.

## 한 줄 정리

`FactoryBean`은 제품 객체 생성의 확장 포인트이고, `SmartInitializingSingleton`은 singleton 집합이 준비된 뒤 실행되는 startup 훅이다.

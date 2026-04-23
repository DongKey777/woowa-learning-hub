# Spring BeanFactoryPostProcessor vs BeanPostProcessor Lifecycle

> 한 줄 요약: `BeanFactoryPostProcessor`는 Bean 정의를 고치고, `BeanPostProcessor`는 실제 Bean 인스턴스를 감싸거나 바꾸는 단계라서 둘을 구분하지 않으면 컨테이너 확장 포인트를 잘못 쓴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
> - [Spring `FactoryBean` and `SmartInitializingSingleton` Extension Points](./spring-factorybean-smartinitializingsingleton-extension-points.md)
> - [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)
> - [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)

retrieval-anchor-keywords: BeanFactoryPostProcessor, BeanPostProcessor, BeanDefinition, postProcessBeanFactory, postProcessBeforeInitialization, postProcessAfterInitialization, lifecycle hook, container extension point, FactoryBean, SmartInitializingSingleton

## 핵심 개념

Spring 컨테이너는 Bean을 만들기 전에 정의를 먼저 다듬고, 만든 뒤에는 인스턴스를 다시 가공할 수 있다.

- `BeanFactoryPostProcessor`: BeanDefinition 수정
- `BeanPostProcessor`: Bean 인스턴스 수정

이 둘은 이름이 비슷하지만 책임이 다르다.

- 전자는 "무엇을 만들지"를 바꾼다
- 후자는 "만들어진 객체를 어떻게 사용할지"를 바꾼다

이 차이를 모르면 자동 구성, AOP, 주입, 커스텀 wrapper를 전부 같은 시점으로 착각한다.

## 깊이 들어가기

### 1. `BeanFactoryPostProcessor`는 인스턴스가 아니라 정의를 본다

```java
@Component
public class PropertyPlaceholderConfigurer implements BeanFactoryPostProcessor {

    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        // BeanDefinition의 property 값을 수정할 수 있다.
    }
}
```

이 단계에서는 아직 Bean이 생성되지 않았으므로, 인스턴스 메서드나 프록시를 기대하면 안 된다.

### 2. `BeanPostProcessor`는 생성된 객체를 본다

```java
@Component
public class TimingPostProcessor implements BeanPostProcessor {

    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) {
        return bean;
    }
}
```

이 단계에서는 객체를 감싸거나 바꾸는 것이 가능하다.

- AOP proxy
- validation wrapper
- custom initialization check

### 3. 생성 순서가 다르면 디버깅도 달라진다

정의 단계 문제가 있으면 bean creation 전에 터진다.

- 프로퍼티 누락
- 조건 실패
- scope 설정 오류

인스턴스 단계 문제가 있으면 이미 빈이 만들어진 뒤 흔적이 남는다.

- 프록시가 붙는다
- 잘못된 wrapper가 붙는다
- init 이후 상태가 바뀐다

### 4. `@Autowired`와 AOP는 같은 단계가 아니다

주입은 대체로 instantiation 이후, 프록시는 post-process 이후에 얹힌다.

이 문맥은 [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)와 같이 보면 더 선명하다.

### 5. 실무에서는 둘이 함께 움직인다

예를 들어 auto-configuration은 BeanDefinition 조건을 추가하고, AOP는 후처리 체인에서 프록시를 만든다.

즉, Spring 확장은 정의와 객체의 두 층에서 일어난다.

## 실전 시나리오

### 시나리오 1: 설정값을 Bean 생성 전에 바꿔야 한다

이때는 `BeanFactoryPostProcessor`가 맞다.

### 시나리오 2: 생성된 Bean을 감싸서 관측성을 넣고 싶다

이때는 `BeanPostProcessor`가 맞다.

### 시나리오 3: AOP 프록시와 custom wrapper가 겹친다

이 경우 wrapper 순서와 실제 target 타입을 구분해야 한다.

### 시나리오 4: BeanFactoryPostProcessor에서 Bean을 직접 꺼내려 했다

정의 단계와 인스턴스 단계를 혼동한 것이다. 이건 보통 설계 냄새다.

## 코드로 보기

### BeanFactoryPostProcessor

```java
@Component
public class CustomBeanDefinitionTweaker implements BeanFactoryPostProcessor {

    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        // BeanDefinition 조작
    }
}
```

### BeanPostProcessor

```java
@Component
public class CustomBeanWrapper implements BeanPostProcessor {

    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) {
        return bean;
    }
}
```

### 구분 예시

```java
// BeanFactoryPostProcessor: 정의 수정
// BeanPostProcessor: 생성된 인스턴스 수정
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `BeanFactoryPostProcessor` | 정의를 통제한다 | 인스턴스를 못 본다 | property, definition 조정 |
| `BeanPostProcessor` | 실제 객체를 바꿀 수 있다 | 디버깅이 어렵다 | proxy, wrapper, validation |
| 둘 다 사용 | 강력한 확장 가능 | 순서가 복잡하다 | 프레임워크 수준 확장 |

핵심은 "후처리"라는 단어가 같아도, **무엇을 후처리하는지**가 다르다는 점이다.

## 꼬리질문

> Q: `BeanFactoryPostProcessor`와 `BeanPostProcessor`의 차이는 무엇인가?
> 의도: 컨테이너 확장 포인트 이해 확인
> 핵심: 전자는 정의, 후자는 인스턴스를 다룬다.

> Q: AOP 프록시는 보통 어느 단계에서 만들어지는가?
> 의도: post-processing 시점 이해 확인
> 핵심: `BeanPostProcessor#postProcessAfterInitialization` 근처다.

> Q: 정의 단계에서 Bean 인스턴스를 기대하면 왜 안 되는가?
> 의도: refresh 순서 이해 확인
> 핵심: 아직 생성되지 않았기 때문이다.

> Q: 둘을 혼동하면 어떤 버그가 생기는가?
> 의도: 실전 디버깅 감각 확인
> 핵심: 조건, 주입, 프록시 시점이 꼬인다.

## 한 줄 정리

BeanFactoryPostProcessor는 설계도를 바꾸고, BeanPostProcessor는 완성된 객체를 바꾸므로 둘을 구분해야 Spring 확장 지점을 제대로 쓸 수 있다.

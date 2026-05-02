---
schema_version: 3
title: Spring ApplicationContext Refresh Phases
concept_id: spring/application-context-refresh-phases
canonical: false
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
aliases:
- ApplicationContext refresh
- refresh phases
- BeanFactoryPostProcessor
- BeanPostProcessor
intents:
- deep_dive
linked_paths:
- contents/spring/ioc-di-container.md
- contents/spring/spring-beanfactorypostprocessor-vs-beanpostprocessor-lifecycle.md
- contents/spring/spring-bean-lifecycle-basics.md
expected_queries:
- ApplicationContext refresh는 어떤 순서로 진행돼?
- BeanFactoryPostProcessor는 언제 실행돼?
- BeanPostProcessor는 언제 적용돼?
- ApplicationContext 시작 과정을 단계별로 설명해줘
---

# Spring ApplicationContext Refresh Phases

> 한 줄 요약: ApplicationContext refresh는 한 번의 "시작"이 아니라 Bean 정의, 후처리, 초기화, 이벤트 발행이 순서대로 맞물리는 부팅 파이프라인이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
> - [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)
> - [Spring `FactoryBean` and `SmartInitializingSingleton` Extension Points](./spring-factorybean-smartinitializingsingleton-extension-points.md)
> - [Spring Startup Hooks: `CommandLineRunner`, `ApplicationRunner`, `SmartLifecycle`, and Readiness Warmup](./spring-startup-runner-smartlifecycle-readiness-warmup.md)
> - [Spring Startup Bean Graph Debugging Playbook](./spring-startup-bean-graph-debugging-playbook.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)

retrieval-anchor-keywords: ApplicationContext refresh, refreshBeanFactory, invokeBeanFactoryPostProcessors, registerBeanPostProcessors, finishBeanFactoryInitialization, refresh lifecycle, context startup

## 핵심 개념

Spring ApplicationContext는 단순히 `new`로 생기는 객체가 아니다.

컨테이너는 refresh 과정에서 여러 단계를 거쳐 완성된다.

- BeanDefinition 준비
- BeanFactory 후처리
- BeanPostProcessor 등록
- 싱글톤 Bean 초기화
- 이벤트와 lifecycle callback 처리

이 흐름을 알아야 다음이 보인다.

- 왜 어떤 Bean은 아직 주입되지 않았는가
- 왜 `BeanFactoryPostProcessor`는 인스턴스보다 먼저인가
- 왜 `@PostConstruct`와 AOP 프록시 시점이 다를 수 있는가

## 깊이 들어가기

### 1. refresh는 컨테이너를 새로 여는 과정이다

```text
prepareRefresh
-> obtainFreshBeanFactory
-> prepareBeanFactory
-> postProcessBeanFactory
-> invokeBeanFactoryPostProcessors
-> registerBeanPostProcessors
-> finishBeanFactoryInitialization
-> finishRefresh
```

핵심은 Bean 생성 전에 정의를 다듬고, 그 다음 인스턴스를 만들고, 마지막에 초기화한다는 점이다.

### 2. BeanFactoryPostProcessor는 정의를 바꾼다

이 단계에서는 아직 Bean 인스턴스가 아니라 정의를 다룬다.

- BeanDefinition 수정
- property placeholder 처리
- 환경값 반영

즉, "무엇을 만들지"가 먼저 결정된다.

### 3. BeanPostProcessor는 인스턴스를 바꾼다

이 단계에서는 실제 객체를 감싸거나 대체할 수 있다.

- AOP proxy
- `@Autowired` 처리
- custom wrapper

그래서 Bean 생성 후에도 객체 모양이 달라질 수 있다.

### 4. 싱글톤 초기화가 끝나야 컨텍스트가 안정된다

`finishBeanFactoryInitialization` 단계에서 non-lazy singleton들이 만들어진다.

이 시점에 순환 의존성, 초기화 순서, 프록시 적용 문제가 드러난다.

### 5. refresh 완료 후에야 이벤트와 실행 준비가 끝난다

`finishRefresh`까지 가야 컨테이너가 운영 가능한 상태가 된다.

그 전에는 일부 이벤트, 리스너, actuator 상태가 기대와 다를 수 있다.

## 실전 시나리오

### 시나리오 1: 어떤 Bean은 주입 전인데 다른 Bean이 그걸 찾는다

대개 refresh 단계에서 아직 초기화되지 않았기 때문이다.

### 시나리오 2: `BeanFactoryPostProcessor`에서 Bean 인스턴스를 기대했다

이 단계는 정의 수정 단계다.

- 인스턴스를 찾는 시도가 실패할 수 있다
- 아직 생성 전이라 lifecycle이 다르다

### 시나리오 3: AOP 프록시가 초기화 이후에 나타난다

이는 BeanPostProcessor 체인 때문이며, [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)와 함께 봐야 한다.

### 시나리오 4: 테스트에서 컨텍스트가 느리다

refresh 단계 중 가장 무거운 부분이 Bean 초기화와 후처리다.

그래서 slice test와 context cache가 중요해진다.

## 코드로 보기

### lifecycle 확인

```java
@Component
public class RefreshLogger implements ApplicationListener<ApplicationReadyEvent> {

    @Override
    public void onApplicationEvent(ApplicationReadyEvent event) {
        System.out.println("ApplicationContext ready");
    }
}
```

### BeanFactoryPostProcessor

```java
@Component
public class DefinitionTweaker implements BeanFactoryPostProcessor {
    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        // BeanDefinition 단계
    }
}
```

### BeanPostProcessor

```java
@Component
public class BeanWrappingPostProcessor implements BeanPostProcessor {
    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) {
        return bean;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| refresh 전체 이해 | 문제 위치를 정확히 찾는다 | 처음엔 복잡하다 | 컨테이너 문제 디버깅 |
| lifecycle callback만 보기 | 단순하다 | 전체 순서를 놓치기 쉽다 | 개별 Bean 검토 |
| post processor 중심 접근 | 확장 포인트를 이해하기 쉽다 | 초기화 전후를 혼동하기 쉽다 | 프록시/자동구성 |

핵심은 컨테이너를 "실행되는 객체"가 아니라 **단계적으로 완성되는 파이프라인**으로 보는 것이다.

## 꼬리질문

> Q: ApplicationContext refresh가 왜 단계적으로 나뉘는가?
> 의도: 컨테이너 부팅 모델 이해 확인
> 핵심: 정의 수정, 후처리, 초기화, 완료를 분리하기 위해서다.

> Q: `BeanFactoryPostProcessor`와 `BeanPostProcessor`의 차이는 무엇인가?
> 의도: 정의/인스턴스 구분 확인
> 핵심: 전자는 정의를, 후자는 객체를 다룬다.

> Q: 왜 `@PostConstruct` 시점과 프록시 생성 시점이 다를 수 있는가?
> 의도: 초기화 순서 이해 확인
> 핵심: 프록시는 BeanPostProcessor 이후에 붙을 수 있다.

> Q: refresh 단계 이해가 테스트에도 왜 도움이 되는가?
> 의도: 컨텍스트 비용 이해 확인
> 핵심: 어떤 단계가 느린지 분해할 수 있다.

## 한 줄 정리

ApplicationContext refresh는 Bean 정의와 인스턴스화, 후처리, 초기화를 차례로 쌓아 컨테이너를 완성하는 부팅 파이프라인이다.

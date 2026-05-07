---
schema_version: 3
title: Spring BeanDefinitionRegistryPostProcessor and ImportBeanDefinitionRegistrar
concept_id: spring/bean-definition-registry-postprocessor-import-registrar
canonical: true
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 78
review_feedback_tags:
- bean-definition-registry
- postprocessor-import-registrar
- beandefinitionregistrypostprocessor
- importbeandefinitionregistrar
aliases:
- BeanDefinitionRegistryPostProcessor
- ImportBeanDefinitionRegistrar
- registry post processor
- bean definition registration
- ImportSelector
- metadata reader
- definition phase
intents:
- deep_dive
- design
linked_paths:
- contents/spring/ioc-di-container.md
- contents/spring/spring-beanfactorypostprocessor-vs-beanpostprocessor-lifecycle.md
- contents/spring/spring-boot-autoconfiguration.md
- contents/spring/spring-boot-condition-evaluation-report-debugging.md
- contents/spring/spring-bean-definition-overriding-semantics.md
expected_queries:
- BeanDefinitionRegistryPostProcessor는 BeanFactoryPostProcessor와 뭐가 달라?
- ImportBeanDefinitionRegistrar는 언제 써야 해?
- Spring에서 BeanDefinition을 직접 등록하는 확장 지점은 뭐야?
- ImportSelector와 ImportBeanDefinitionRegistrar 차이가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Spring 컨테이너의 Bean 인스턴스 생성 전 단계에서
  BeanDefinitionRegistryPostProcessor와 ImportBeanDefinitionRegistrar가
  bean definition을 등록하거나 조정하는 방식을 다룬다. BeanPostProcessor처럼
  만들어진 객체를 감싸는 단계가 아니라 definition phase 확장 지점이다.
---
# Spring BeanDefinitionRegistryPostProcessor and ImportBeanDefinitionRegistrar

> 한 줄 요약: `BeanDefinitionRegistryPostProcessor`와 `ImportBeanDefinitionRegistrar`는 Bean 인스턴스를 만드는 도구가 아니라, 컨테이너에 새 설계도를 등록하고 조정하는 가장 이른 확장 지점이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [Spring BeanFactoryPostProcessor vs BeanPostProcessor Lifecycle](./spring-beanfactorypostprocessor-vs-beanpostprocessor-lifecycle.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)
> - [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)

retrieval-anchor-keywords: BeanDefinitionRegistryPostProcessor, ImportBeanDefinitionRegistrar, registry post processor, bean definition registration, metadata reader, import selector, auto configuration import, definition phase

## 핵심 개념

Spring 확장의 시작은 종종 Bean 인스턴스가 아니라 BeanDefinition 등록이다.

- `BeanDefinitionRegistryPostProcessor`: registry에 새 정의를 추가하거나 수정한다
- `ImportBeanDefinitionRegistrar`: `@Configuration`/`@Import` 경로에서 정의를 등록한다

이 둘은 "만들어진 Bean을 후처리"하는 것이 아니라, **애초에 어떤 Bean이 존재할지 결정하는 단계**다.

## 깊이 들어가기

### 1. Registry post processor는 가장 이른 축이다

일반 `BeanFactoryPostProcessor`보다 앞서 정의 등록 자체를 건드릴 수 있다.

### 2. `ImportBeanDefinitionRegistrar`는 설정 클래스와 맞물린다

```java
@Configuration
@Import(MyRegistrar.class)
public class MyConfig {
}
```

이 패턴은 condition-based auto-config와 잘 맞는다.

### 3. `ImportSelector`와의 차이

- `ImportSelector`: 무엇을 import할지 이름 기반 선택
- `ImportBeanDefinitionRegistrar`: 정의를 직접 등록

### 4. metadata 기반 스캔과 함께 쓰인다

Boot auto-config는 classpath metadata와 조건 평가를 함께 사용한다.

이 문맥은 [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)과 [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)와 연결된다.

### 5. 남용하면 설정 클래스가 비대해진다

정의 등록을 너무 많이 커스터마이즈하면, 컨테이너가 아니라 작은 프레임워크를 다시 만들게 된다.

## 실전 시나리오

### 시나리오 1: 조건에 따라 Bean을 통째로 등록하고 싶다

이때 registry-level extension이 자연스럽다.

### 시나리오 2: 여러 bean definition을 한 번에 만들어야 한다

예를 들어 특정 starter가 여러 supporting bean을 함께 제공해야 할 때다.

### 시나리오 3: auto-config를 대체하고 싶다

기본 bean definition을 바꾸거나 새로 넣는 방식으로 대응할 수 있다.

### 시나리오 4: bean definition overriding과 헷갈린다

여기서는 override가 아니라, 애초에 등록 시점에 개입하는 것이다.

## 코드로 보기

### registrar

```java
public class MyRegistrar implements ImportBeanDefinitionRegistrar {

    @Override
    public void registerBeanDefinitions(AnnotationMetadata importingClassMetadata,
                                        BeanDefinitionRegistry registry) {
        GenericBeanDefinition definition = new GenericBeanDefinition();
        definition.setBeanClass(MyService.class);
        registry.registerBeanDefinition("myService", definition);
    }
}
```

### registry post processor

```java
public class MyRegistryPostProcessor implements BeanDefinitionRegistryPostProcessor {

    @Override
    public void postProcessBeanDefinitionRegistry(BeanDefinitionRegistry registry) {
    }

    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `ImportSelector` | 선택이 간단하다 | 정의 커스터마이즈는 약하다 | 조건부 모듈 선택 |
| `ImportBeanDefinitionRegistrar` | 직접 정의 등록 가능 | 복잡도가 높다 | starter/extention |
| `BeanDefinitionRegistryPostProcessor` | 최상위 등록 제어 가능 | 너무 강력해서 남용되기 쉽다 | 프레임워크 수준 |

핵심은 이 지점이 "생성"이 아니라 **등록**이라는 것이다.

## 꼬리질문

> Q: `BeanDefinitionRegistryPostProcessor`와 `BeanFactoryPostProcessor`의 차이는 무엇인가?
> 의도: 정의 등록과 정의 수정 구분 확인
> 핵심: 전자는 registry 단계, 후자는 factory 단계다.

> Q: `ImportBeanDefinitionRegistrar`는 언제 유용한가?
> 의도: 설정 기반 정의 등록 이해 확인
> 핵심: 조건에 따라 BeanDefinition을 직접 넣어야 할 때다.

> Q: `ImportSelector`와 registrar의 차이는 무엇인가?
> 의도: import 전략 구분 확인
> 핵심: selector는 선택, registrar는 등록이다.

> Q: 너무 강한 registry 후처리를 남용하면 왜 안 되는가?
> 의도: 컨테이너 설계 감각 확인
> 핵심: 설정이 숨겨지고 프레임워크가 복잡해진다.

## 한 줄 정리

BeanDefinitionRegistryPostProcessor와 ImportBeanDefinitionRegistrar는 Bean 생성 이전에 컨테이너 설계도를 바꾸는 가장 이른 확장 지점이다.

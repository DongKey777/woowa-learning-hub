---
schema_version: 3
title: Spring Bean Definition Overriding Semantics
concept_id: spring/bean-definition-overriding-semantics
canonical: true
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
review_feedback_tags:
- bean-definition-overriding
- semantics
- beandefinitionoverrideexception
- bean-name-collision
aliases:
- bean definition overriding
- BeanDefinitionOverrideException
- bean name collision
- @Primary vs override
- ConditionalOnMissingBean
- bean alias
- duplicate bean name
intents:
- deep_dive
- troubleshooting
linked_paths:
- contents/spring/spring-primary-vs-bean-override-primer.md
- contents/spring/ioc-di-container.md
- contents/spring/spring-boot-autoconfiguration.md
- contents/spring/spring-boot-condition-evaluation-report-debugging.md
- contents/spring/spring-configuration-proxybeanmethods-beanpostprocessor-chain.md
- contents/spring/spring-bean-lifecycle-scope-traps.md
expected_queries:
- Bean definition overriding은 @Primary와 뭐가 달라?
- 같은 이름 bean이 둘이면 Spring Boot는 어떻게 처리해?
- ConditionalOnMissingBean은 override와 어떤 점이 달라?
- bean name collision과 타입 후보 충돌을 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 Spring bean definition overriding, bean name collision,
  @Primary와 alias, @ConditionalOnMissingBean, Boot 자동 구성 back-off를 구분한다.
  이름 충돌과 타입 후보 선택 문제를 분리하고, 운영에서 우연한 override를 막는
  컨테이너 안전성 계약을 설명한다.
---
# Spring Bean Definition Overriding Semantics

> 한 줄 요약: Bean definition overriding은 이름이 같을 때 누가 이기는지의 규칙이 아니라, 어떤 설정이 안전하게 교체 가능한지에 대한 컨테이너 계약이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `@Primary` vs Bean Override Primer: 주입 우선순위와 bean 이름 충돌은 다른 문제다](./spring-primary-vs-bean-override-primer.md)
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
> - [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)

retrieval-anchor-keywords: bean definition overriding, bean name collision, alias, primary bean, conditional on missing bean, bean factory, configuration class, override semantics

## 핵심 개념

Spring은 같은 이름의 Bean definition이 생길 때 어떻게 할지 결정해야 한다.

- 허용할지
- 막을지
- 대체할지

이건 단순 충돌 해결이 아니라 **컨테이너의 안전성 정책**이다.

## 깊이 들어가기

### 1. 이름 충돌과 타입 충돌은 다르다

같은 타입이 여러 개인 것과 같은 이름이 여러 개인 것은 다르다.

- 이름 충돌: definition override 문제
- 타입 충돌: injection candidate 문제

초보자용 비교가 먼저 필요하면 [Spring `@Primary` vs Bean Override Primer: 주입 우선순위와 bean 이름 충돌은 다른 문제다](./spring-primary-vs-bean-override-primer.md)를 먼저 보고 다시 돌아오는 편이 읽기 쉽다.

### 2. Boot는 기본적으로 안전 쪽으로 간다

중복 Bean name을 무심코 덮어쓰는 대신, 상황에 따라 실패시키는 것이 더 안전하다.

자동 구성과 같이 보면 [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)와 연결된다.

### 3. override가 유용한 경우도 있다

- 테스트에서 fake bean 교체
- 라이브러리 기본 설정 덮어쓰기
- 커스텀 auto-config 대체

하지만 운영에서 우연히 덮이면 버그다.

### 4. alias와 primary는 override가 아니다

이름 alias와 `@Primary`는 충돌을 다른 방식으로 푸는 도구다.

- alias: 같은 bean을 다른 이름으로 부름
- primary: 타입 후보가 여러 개일 때 우선 선택

### 5. 조건부 등록이 더 안전한 대안이다

`@ConditionalOnMissingBean`은 충돌 후 덮어쓰기가 아니라, **처음부터 대체 가능하게 설계하는 방식**이다.

## 실전 시나리오

### 시나리오 1: 같은 이름의 Bean이 둘 생겼다

개발자는 "마지막 것이 이긴다"를 기대하지만, 실제로는 예외가 나거나 다른 정책이 적용될 수 있다.

### 시나리오 2: 테스트는 통과하는데 운영은 깨진다

테스트 프로필에서만 override가 허용되어 있을 수 있다.

### 시나리오 3: auto-config를 직접 bean으로 덮어버렸다

그렇게 하면 Boot가 제공하던 기본 계약이 깨질 수 있다.

### 시나리오 4: 이름은 같은데 타입은 다르다

이 경우는 injection과 override 문제를 분리해서 봐야 한다.

## 코드로 보기

### definition collision

```java
@Configuration
public class AConfig {
    @Bean
    public Foo foo() {
        return new Foo();
    }
}

@Configuration
public class BConfig {
    @Bean
    public Foo foo() {
        return new Foo();
    }
}
```

### safe replacement with condition

```java
@Bean
@ConditionalOnMissingBean
public Foo foo() {
    return new Foo();
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| override 허용 | 유연하다 | 우연한 교체 위험 | 테스트/특수 설정 |
| override 금지 | 안전하다 | 교체가 번거롭다 | 운영 기본값 |
| conditional bean | 계약이 명확하다 | 조건 이해가 필요하다 | auto-config |

핵심은 overriding을 "편의 기능"이 아니라, **의도된 대체가 가능한지**를 검증하는 정책으로 보는 것이다.

## 꼬리질문

> Q: bean definition overriding과 `@Primary`는 같은가?
> 의도: 이름 기반 교체와 타입 기반 선택 구분 확인
> 핵심: 다르다. overriding은 definition 충돌, primary는 타입 후보 선택이다.

> Q: 왜 Boot는 이름 충돌을 함부로 허용하지 않는가?
> 의도: 안전성 정책 이해 확인
> 핵심: 우연한 교체를 막기 위해서다.

> Q: 조건부 등록은 왜 override보다 안전한가?
> 의도: auto-config 계약 이해 확인
> 핵심: 처음부터 대체 가능한 구조이기 때문이다.

> Q: 테스트에서만 override를 허용하는 이유는 무엇인가?
> 의도: 환경별 정책 차이 이해 확인
> 핵심: 운영과 다른 실험용 대체를 허용하기 위해서다.

## 한 줄 정리

Bean definition overriding은 이름 충돌 해결이 아니라, 의도된 대체를 허용할지 정하는 컨테이너 정책이다.

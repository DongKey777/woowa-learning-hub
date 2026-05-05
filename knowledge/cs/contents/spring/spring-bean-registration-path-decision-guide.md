---
schema_version: 3
title: Spring Bean 등록 경로 결정 가이드
concept_id: spring/bean-registration-path-decision-guide
canonical: false
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids:
  - missions/lotto
review_feedback_tags:
  - component-scan-vs-bean-method-choice
  - external-object-bean-registration
  - autoconfiguration-vs-user-bean
aliases:
  - component scan vs @Bean
  - '@Bean vs auto-configuration'
  - spring bean 등록 방식
  - service는 자동 등록
  - ObjectMapper 직접 등록
  - starter 기본 bean
  - 우리 코드 scan 외부 객체 bean
  - bean registration path
symptoms:
  - service는 잘 뜨는데 ObjectMapper 같은 건 어디서 등록해야 할지 모르겠어요
  - starter가 만든 bean인지 제가 @Bean으로 만들어야 하는지 헷갈려요
  - 우리 코드 클래스도 @Bean으로 만들고 있는데 이게 맞는지 확신이 없어요
intents:
  - comparison
  - design
  - troubleshooting
prerequisites:
  - spring/ioc-di-basics
next_docs:
  - spring/bean-di-basics
  - spring/boot-autoconfiguration-basics
  - spring/component-scan-failure-patterns
linked_paths:
  - contents/spring/spring-bean-di-basics.md
  - contents/spring/spring-boot-autoconfiguration-basics.md
  - contents/spring/spring-configuration-vs-autoconfiguration-primer.md
  - contents/spring/spring-component-scan-failure-patterns.md
  - contents/spring/spring-starter-added-but-bean-missing-faq.md
confusable_with:
  - spring/bean-di-basics
  - spring/boot-autoconfiguration-basics
  - spring/component-scan-failure-patterns
forbidden_neighbors: []
expected_queries:
  - Spring에서 component scan이랑 @Bean은 언제 갈라서 써?
  - service 클래스도 @Bean으로 등록해야 해?
  - ObjectMapper나 Clock은 왜 component scan이 아니라 @Bean으로 만들어요?
  - starter가 bean을 만들어 주는 상황과 내가 직접 등록하는 상황은 어떻게 구분해?
  - 우리 코드 클래스, 외부 라이브러리 객체, Boot 기본 bean을 어떤 기준으로 나눠?
contextual_chunk_prefix: |
  이 문서는 Spring 초급 학습자가 bean을 어떤 경로로 등록해야 하는지
  component scan, `@Bean`, Boot auto-configuration 셋으로 나눠 결정하게
  돕는 chooser다. service는 자동 등록되는데 ObjectMapper는 어디서 만드나,
  starter가 bean을 이미 주는지 내가 직접 `@Bean`을 써야 하는지, 우리 코드
  클래스도 `@Bean`으로 만들어야 하나 같은 자연어 질문을 "우리 코드 역할
  클래스", "외부 객체 조립", "Boot 기본값" 세 갈래 판단으로 연결한다.
---

# Spring Bean 등록 경로 결정 가이드

> 한 줄 요약: 우리 코드 역할 클래스면 component scan, 외부 객체 조립이면 `@Bean`, starter가 채우는 공용 기본값이면 Boot auto-configuration부터 보는 것이 기본 분기다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Bean과 DI 기초](./spring-bean-di-basics.md)
- [Spring Boot 자동 구성 기초](./spring-boot-autoconfiguration-basics.md)
- [Spring Configuration vs Auto-configuration 입문](./spring-configuration-vs-autoconfiguration-primer.md)
- [Spring Component Scan 실패 패턴](./spring-component-scan-failure-patterns.md)
- [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ](./spring-starter-added-but-bean-missing-faq.md)
- [Dependency Injection Basics](../software-engineering/dependency-injection-basics.md)

retrieval-anchor-keywords: component scan vs bean, spring bean registration path, service 는 자동 등록, objectmapper bean 어디서, starter 기본 bean, bean registration basics, 언제 bean 메서드, auto configuration 처음, what is component scan, 왜 service 에 bean 안 붙임

## 핵심 개념

Bean 등록 경로를 고른다는 것은 "어떤 코드가 이 객체를 만들 책임을 지는가"를 정하는 일이다. 초급 단계에서는 우리 코드 역할 클래스인지, 외부 객체를 조립하는지, starter가 기본값을 제공하는지 세 갈래로 먼저 나누면 대부분 정리된다. 등록 실패 증상이 먼저라면 경로 선택보다 "왜 후보가 안 생겼나"를 우선 본다.

## 한눈에 보기

| 지금 등록하려는 대상 | 기본 경로 | 이유 |
| --- | --- | --- |
| `@Service`, `@Repository`, `@Controller` 같은 우리 코드 역할 클래스 | component scan | stereotype과 package 경계만 맞으면 Spring이 자동으로 찾는다 |
| `Clock`, `ObjectMapper`, 외부 SDK client | `@Configuration` + `@Bean` | 생성 규칙을 메서드로 드러내는 편이 명확하다 |
| starter를 넣으면 보통 같이 오는 공용 기본 bean | Boot auto-configuration | classpath, property, 기존 bean 유무를 보고 조건부로 채운다 |
| shared config 묶음 | `@Import` 또는 별도 설정 | bean 하나보다 모듈 연결 설계에 가깝다 |

## 빠른 분기

1. 역할이 클래스에 이미 드러난 우리 코드면 scan을 기본값으로 본다.
2. 내 소유 타입이 아니거나 생성 인자가 중요한 객체면 `@Bean` 쪽이 더 맞다.
3. starter 설명서에 "자동 구성"이 보이면 내 코드보다 Boot 기본 bean 경로를 먼저 의심한다.
4. bean이 있을 줄 알았는데 안 보이면 경로 선택 전에 back-off, 조건 탈락, scan boundary를 점검한다.

## 흔한 오해와 함정

- `OrderService` 같은 우리 코드를 전부 `@Bean` 메서드로 올기기 시작하면 역할 클래스와 조립 코드가 섞여 읽기 어려워진다.
- 외부 라이브러리 객체에 stereotype을 붙일 수 있다고 생각하면 `ObjectMapper` 같은 대상을 잘못된 경로로 다루기 쉽다.
- starter 기본 bean이 안 보일 때 auto-configuration 고장으로 단정하면, 실제로는 내가 먼저 만든 bean 때문에 back-off한 상황을 놓칠 수 있다.
- "scanBasePackages를 넓히거나 `@Bean`을 더 추가하면 언젠가 되겠지" 식으로 접근하면 왜 동작하는지 학습이 남지 않는다.

## 다음 행동

- 우리 코드 bean 등록과 DI 큰 그림을 다시 잡으려면 [Spring Bean과 DI 기초](./spring-bean-di-basics.md)를 본다.
- starter가 bean을 왜 바로 만드는지 궁금하면 [Spring Boot 자동 구성 기초](./spring-boot-autoconfiguration-basics.md)로 간다.
- `@Configuration`, `@Bean`, auto-configuration`의 연결을 보고 싶으면 [Spring Configuration vs Auto-configuration 입문](./spring-configuration-vs-autoconfiguration-primer.md)을 잇는다.
- 등록 실패 증상이 먼저라면 [Spring Component Scan 실패 패턴](./spring-component-scan-failure-patterns.md)이나 [Spring Bean을 못 찾아요 원인 라우터](./spring-bean-not-found-cause-router.md)로 분기한다.

## 한 줄 정리

Bean 등록 경로는 "우리 코드 역할 클래스, 외부 객체 조립, Boot 기본값" 중 어디에 속하는지 먼저 정하면 대부분의 선택이 자연스럽게 따라온다.

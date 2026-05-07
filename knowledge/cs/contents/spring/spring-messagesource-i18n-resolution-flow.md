---
schema_version: 3
title: Spring MessageSource and i18n Resolution Flow
concept_id: spring/messagesource-i18n-resolution-flow
canonical: true
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
review_feedback_tags:
- messagesource-i18n-resolution
- flow
- messagesource
- i18n
aliases:
- MessageSource
- i18n
- ResourceBundleMessageSource
- message codes
- fallback message
- locale context
- error code localization
intents:
- deep_dive
- troubleshooting
linked_paths:
- contents/spring/spring-mvc-request-lifecycle.md
- contents/spring/spring-mvc-exception-resolver-chain-contract.md
- contents/spring/spring-problemdetail-error-response-design.md
- contents/spring/spring-validation-binding-error-pipeline.md
- contents/spring/spring-conversion-service-formatter-binder-pipeline.md
expected_queries:
- Spring MessageSource는 locale code fallback formatting을 어떻게 처리해?
- validation error message를 locale별로 바꾸려면 어떤 message code를 봐야 해?
- ResourceBundleMessageSource 설정과 fallback 정책은 어떻게 잡아?
- ProblemDetail error response를 i18n 메시지로 바꾸려면 무엇을 연결해?
contextual_chunk_prefix: |
  이 문서는 Spring MessageSource가 단순 번역 사전이 아니라 code lookup,
  Locale, fallback, formatting, ResourceBundleMessageSource, validation error
  message code, ProblemDetail localization을 결합해 메시지를 해석하는 i18n
  resolution flow임을 설명한다.
---
# Spring `MessageSource` and i18n Resolution Flow

> 한 줄 요약: `MessageSource`는 단순 번역 사전이 아니라 locale, code, fallback, and formatting을 결합해 메시지를 해석하는 국제화 엔진이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
> - [Spring ProblemDetail Error Response Design](./spring-problemdetail-error-response-design.md)
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
> - [Spring ConversionService, Formatter, and Binder Pipeline](./spring-conversion-service-formatter-binder-pipeline.md)

retrieval-anchor-keywords: MessageSource, i18n, LocaleResolver, message codes, fallback message, ResourceBundleMessageSource, error code localization, locale context

## 핵심 개념

Spring의 i18n은 `MessageSource`와 `Locale`가 함께 움직인다.

- code를 찾는다
- locale을 정한다
- fallback을 적용한다
- 메시지를 포맷한다

즉, 번역 문자열이 아니라 **메시지 해석 흐름**이다.

## 깊이 들어가기

### 1. code lookup이 먼저다

```java
messageSource.getMessage("order.not.found", null, locale);
```

Spring은 코드에 매핑된 메시지를 찾아낸다.

### 2. locale은 request context와 연결된다

MVC에서는 LocaleResolver가 요청별 locale을 결정할 수 있다.

### 3. fallback rule이 중요하다

locale에 맞는 메시지가 없으면 기본 메시지나 다른 locale로 fallback할 수 있다.

### 4. validation error와 잘 맞는다

이 문맥은 [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)와 연결된다.

필드 에러 메시지를 locale별로 바꾸려면 message code 전략이 중요하다.

### 5. ProblemDetail과도 연결된다

이 문맥은 [Spring ProblemDetail Error Response Design](./spring-problemdetail-error-response-design.md)과 같이 봐야 한다.

에러 본문을 locale별로 바꾸면 사용자 경험이 좋아진다.

## 실전 시나리오

### 시나리오 1: 메시지가 영어로만 나온다

LocaleResolver나 message bundle 설정이 빠졌을 수 있다.

### 시나리오 2: validation error가 code 대신 raw text를 보여준다

message code mapping과 interpolation이 필요하다.

### 시나리오 3: 운영에서 locale이 섞인다

요청 단위 locale context가 제대로 분리되지 않았을 수 있다.

### 시나리오 4: fallback이 없어서 메시지가 비어 보인다

default message 정책을 정해야 한다.

## 코드로 보기

### MessageSource use

```java
@Bean
public MessageSource messageSource() {
    ResourceBundleMessageSource source = new ResourceBundleMessageSource();
    source.setBasename("messages");
    source.setDefaultEncoding("UTF-8");
    return source;
}
```

### localized error text

```java
String text = messageSource.getMessage("user.not.found", null, locale);
```

### message bundle example

```properties
# messages_ko.properties
user.not.found=사용자를 찾을 수 없습니다.
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 locale | 단순하다 | 글로벌 UX가 약하다 | 내부 도구 |
| 다국어 MessageSource | 사용자 경험이 좋다 | 관리 비용이 든다 | public API |
| default-only fallback | 안전하다 | 메시지가 덜 친절하다 | 빠른 시작 |

핵심은 `MessageSource`를 문자열 저장소가 아니라, **locale-aware message resolution flow**로 보는 것이다.

## 꼬리질문

> Q: `MessageSource`는 무엇을 하는가?
> 의도: i18n 해석 흐름 이해 확인
> 핵심: locale과 code를 기반으로 메시지를 찾는다.

> Q: validation 에러 localization은 어디서 연결되는가?
> 의도: 메시지 코드/에러 연계 이해 확인
> 핵심: binding/validation과 message code가 연결된다.

> Q: fallback 메시지는 왜 중요한가?
> 의도: 운영 안정성 이해 확인
> 핵심: 번역이 없을 때도 응답이 비지 않게 하기 위해서다.

> Q: LocaleResolver와 MessageSource의 관계는 무엇인가?
> 의도: locale 결정과 메시지 해석 분리 확인
> 핵심: LocaleResolver가 locale을 정하고 MessageSource가 메시지를 찾는다.

## 한 줄 정리

`MessageSource`는 locale, code, fallback을 조합해 메시지를 해석하는 국제화 엔진이다.

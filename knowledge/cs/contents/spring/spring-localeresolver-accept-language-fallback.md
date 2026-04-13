# Spring LocaleResolver and Accept-Language Fallback

> 한 줄 요약: `LocaleResolver`는 요청별 locale을 정하는 계층이고, `MessageSource`는 그 locale을 바탕으로 메시지를 찾는 계층이라 둘을 분리해 봐야 i18n이 안정적으로 동작한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `MessageSource` and i18n Resolution Flow](./spring-messagesource-i18n-resolution-flow.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring ProblemDetail Error Response Design](./spring-problemdetail-error-response-design.md)
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
> - [Spring SecurityContext Propagation Across Async and Reactive Boundaries](./spring-securitycontext-propagation-async-reactive-boundaries.md)

retrieval-anchor-keywords: LocaleResolver, Accept-Language, LocaleContextHolder, AcceptHeaderLocaleResolver, SessionLocaleResolver, locale fallback, i18n, request locale, language negotiation

## 핵심 개념

Locale은 메시지 번역과 에러 응답 포맷에 영향을 준다.

- 브라우저의 `Accept-Language`
- 세션 저장 locale
- 요청 컨텍스트 locale
- 기본 locale fallback

이 결정은 `MessageSource`보다 앞단이다.

## 깊이 들어가기

### 1. `LocaleResolver`가 먼저 locale을 정한다

```java
@Bean
public LocaleResolver localeResolver() {
    AcceptHeaderLocaleResolver resolver = new AcceptHeaderLocaleResolver();
    resolver.setDefaultLocale(Locale.KOREA);
    return resolver;
}
```

### 2. `Accept-Language`는 힌트다

브라우저가 보내는 언어 우선순위는 서버가 locale을 정할 때 참고된다.

### 3. `SessionLocaleResolver`는 사용자가 바꾼 locale을 기억할 수 있다

UI에서 언어 전환을 저장해야 할 때 유용하다.

### 4. `LocaleContextHolder`는 요청 컨텍스트에 붙는다

이 값은 thread boundary를 넘으면 사라질 수 있다.

이 문맥은 [Spring SecurityContext Propagation Across Async and Reactive Boundaries](./spring-securitycontext-propagation-async-reactive-boundaries.md)와도 비슷하다.

### 5. locale이 바뀌면 validation과 ProblemDetail도 바뀔 수 있다

이 문맥은 [Spring ProblemDetail Error Response Design](./spring-problemdetail-error-response-design.md)와 [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: 브라우저 언어는 한국어인데 영어 메시지가 나온다

LocaleResolver 설정이나 message bundle fallback을 확인해야 한다.

### 시나리오 2: 사용자가 언어를 바꿨는데 다음 요청에 반영되지 않는다

SessionLocaleResolver나 locale cookie 정책이 필요할 수 있다.

### 시나리오 3: async 작업에서 locale이 사라진다

thread-local 기반 locale context가 전달되지 않은 것이다.

### 시나리오 4: 메시지는 번역됐는데 에러 코드 설명이 부자연스럽다

ProblemDetail과 validation 메시지 매핑을 함께 봐야 한다.

## 코드로 보기

### accept-header locale resolver

```java
@Bean
public LocaleResolver localeResolver() {
    AcceptHeaderLocaleResolver resolver = new AcceptHeaderLocaleResolver();
    resolver.setDefaultLocale(Locale.ENGLISH);
    return resolver;
}
```

### locale-aware message lookup

```java
String message = messageSource.getMessage("user.not.found", null, LocaleContextHolder.getLocale());
```

### fallback locale

```java
resolver.setDefaultLocale(Locale.KOREA);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| AcceptHeaderLocaleResolver | 브라우저 친화적이다 | 사용자 선택 저장이 약하다 | API/브라우저 기본 |
| SessionLocaleResolver | 언어 선택을 기억한다 | 세션 의존성이 있다 | 웹 UI |
| 기본 locale 고정 | 단순하다 | 다국어 UX가 약하다 | 내부 도구 |

핵심은 locale을 "번역 문자열"이 아니라 **요청별 언어 컨텍스트**로 보는 것이다.

## 꼬리질문

> Q: `LocaleResolver`와 `MessageSource`의 차이는 무엇인가?
> 의도: locale 결정과 메시지 검색 구분 확인
> 핵심: 전자는 locale을 정하고, 후자는 메시지를 찾는다.

> Q: `Accept-Language`는 왜 힌트인가?
> 의도: 언어 협상 이해 확인
> 핵심: 서버가 최종 locale을 결정한다.

> Q: async 작업에서 locale이 사라지는 이유는 무엇인가?
> 의도: thread boundary 이해 확인
> 핵심: locale context가 thread-local일 수 있기 때문이다.

> Q: locale fallback을 왜 명시해야 하는가?
> 의도: 사용자 경험/운영 안정성 확인
> 핵심: 번역이 없을 때도 일관된 응답이 필요하다.

## 한 줄 정리

LocaleResolver는 요청의 언어 컨텍스트를 정하고, MessageSource는 그 컨텍스트를 바탕으로 문자열을 해석한다.

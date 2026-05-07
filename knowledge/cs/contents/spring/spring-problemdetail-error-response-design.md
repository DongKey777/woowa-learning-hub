---
schema_version: 3
title: Spring ProblemDetail Error Response Design
concept_id: spring/problemdetail-error-response-design
canonical: true
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- problemdetail-error-response
- problemdetail
- rfc-7807-error
- response
aliases:
- Spring ProblemDetail
- RFC 7807 error response
- Spring error response design
- @ExceptionHandler ProblemDetail
- validation error ProblemDetail
- BasicErrorController ProblemDetail
intents:
- deep_dive
- design
- troubleshooting
linked_paths:
- contents/spring/spring-custom-error-dto-to-problemdetail-handoff-primer.md
- contents/spring/spring-mvc-exception-resolver-chain-contract.md
- contents/spring/spring-problemdetail-before-after-commit-matrix.md
- contents/spring/spring-mvc-filter-interceptor-controlleradvice-boundaries.md
- contents/spring/spring-validation-binding-error-pipeline.md
- contents/spring/spring-basicerrorcontroller-errorattributes-whitelabel-boundaries.md
- contents/spring/spring-boot-condition-evaluation-report-debugging.md
- contents/spring/spring-actuator-exposure-security.md
expected_queries:
- Spring ProblemDetail로 에러 응답 계약을 어떻게 설계해?
- status title detail type instance는 각각 어떤 의미로 써야 해?
- validation error와 domain error를 ProblemDetail에 어떻게 담아?
- @ExceptionHandler와 BasicErrorController의 ProblemDetail 책임은 어떻게 나뉘어?
contextual_chunk_prefix: |
  이 문서는 Spring에서 ProblemDetail을 단순 오류 DTO가 아니라 HTTP status, type,
  title, detail, instance를 포함한 error response contract로 설계하는 deep dive다.
  validation, domain, auth, default error path, actuator 노출 경계를 함께 다룬다.
---
# Spring `ProblemDetail` Error Response Design

> 한 줄 요약: `ProblemDetail`은 예외를 표준 HTTP 오류 응답으로 모델링하는 방식이라, 상태 코드와 에러 본문 계약을 함께 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer](./spring-custom-error-dto-to-problemdetail-handoff-primer.md)
> - [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
> - [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
> - [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
> - [Spring `BasicErrorController`, `ErrorAttributes`, and Whitelabel Error Boundaries](./spring-basicerrorcontroller-errorattributes-whitelabel-boundaries.md)
> - [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)
> - [Spring Actuator Exposure and Security](./spring-actuator-exposure-security.md)

retrieval-anchor-keywords: ProblemDetail, error response design, RFC 9457, API error contract, status, title, detail, instance, type URI, exception mapping, BasicErrorController, ErrorAttributes

## 핵심 개념

`ProblemDetail`은 Spring이 제공하는 표준 오류 응답 모델이다.

- status
- title
- detail
- instance
- type

핵심은 "예쁜 에러 객체"가 아니라, **HTTP 오류를 구조화된 계약으로 만든다**는 점이다.

## 깊이 들어가기

### 1. `ProblemDetail`은 상태 코드와 함께 써야 한다

```java
ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.NOT_FOUND);
problem.setTitle("Order not found");
problem.setDetail("Order 123 not found");
```

상태 코드만으로는 충분하지 않고, 본문도 함께 있어야 클라이언트가 처리하기 쉽다.

### 2. `type`은 오류의 의미를 식별한다

오류 타입 URI는 같은 400이라도 다른 의미를 구분하는 데 유용하다.

### 3. validation error와 domain error는 다르게 설계할 수 있다

- validation: 요청이 잘못됨
- domain: 비즈니스 규칙 위반

이 둘을 같은 문제로 섞으면 클라이언트가 처리하기 어려워진다.

### 4. `@ExceptionHandler`와 결합하면 강력하다

이 문맥은 [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)와 같이 봐야 한다.

### 5. 확장 필드는 신중하게 넣는다

`ProblemDetail`은 표준 필드 외에 properties를 추가할 수 있지만, 너무 많은 정보를 넣으면 계약이 지저분해진다.

## 실전 시나리오

### 시나리오 1: 모든 예외를 400으로만 보낸다

클라이언트는 원인을 구분할 수 없다.

### 시나리오 2: 상태 코드는 맞는데 본문이 없다

디버깅과 사용자 경험이 모두 나빠진다.

### 시나리오 3: validation error와 auth error가 같은 포맷이다

의도적으로 통합할 수도 있지만, 서로 다른 처리 전략이 필요한 경우가 많다.

### 시나리오 4: 내부 예외 메시지를 그대로 노출한다

보안과 사용자 경험 측면에서 위험할 수 있다.

## 코드로 보기

### ProblemDetail 생성

```java
@ExceptionHandler(OrderNotFoundException.class)
public ResponseEntity<ProblemDetail> handle(OrderNotFoundException ex) {
    ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.NOT_FOUND);
    problem.setTitle("Order not found");
    problem.setDetail(ex.getMessage());
    problem.setType(URI.create("https://example.com/problems/order-not-found"));
    return ResponseEntity.status(HttpStatus.NOT_FOUND).body(problem);
}
```

### validation error mapping

```java
@ExceptionHandler(MethodArgumentNotValidException.class)
public ResponseEntity<ProblemDetail> handleValidation(MethodArgumentNotValidException ex) {
    ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
    problem.setTitle("Validation failed");
    problem.setDetail("Request body is invalid");
    return ResponseEntity.badRequest().body(problem);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `ProblemDetail` | 표준화가 쉽다 | 너무 일반적이면 의미가 흐려진다 | 공통 API error contract |
| 커스텀 error DTO | 유연하다 | 표준성과 호환성이 낮다 | 도메인 특화 응답 |
| 상태 코드만 반환 | 단순하다 | 클라이언트가 처리하기 어렵다 | 아주 단순한 API |

핵심은 오류를 "문자열"이 아니라 **상태가 있는 HTTP 문제 객체**로 설계하는 것이다.

## 꼬리질문

> Q: `ProblemDetail`이 해결하는 것은 무엇인가?
> 의도: 오류 표준화 이해 확인
> 핵심: HTTP 에러를 구조화된 계약으로 표현한다.

> Q: validation error와 domain error를 왜 구분해야 하는가?
> 의도: 오류 의미 분리 확인
> 핵심: 클라이언트 처리 방식이 다르기 때문이다.

> Q: `type` URI를 왜 넣는가?
> 의도: 오류 분류 이해 확인
> 핵심: 오류 의미를 안정적으로 식별하기 위해서다.

> Q: `ProblemDetail`을 쓸 때 주의할 점은 무엇인가?
> 의도: 보안/계약 이해 확인
> 핵심: 내부 예외 메시지를 그대로 노출하지 말아야 한다.

## 한 줄 정리

`ProblemDetail`은 HTTP 오류를 표준 구조로 표현하므로, 상태 코드와 본문 계약을 함께 설계해야 한다.

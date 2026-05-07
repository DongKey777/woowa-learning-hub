---
schema_version: 3
title: Spring Method Validation Proxy Pitfalls
concept_id: spring/method-validation-proxy-pitfalls
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 82
review_feedback_tags:
- method-validation-proxy
- pitfalls
- method-validation
- validated
aliases:
- method validation
- @Validated
- executable validation
- proxy validation
- self invocation validation
- ConstraintViolationException
- parameter validation
- return value validation
intents:
- troubleshooting
- deep_dive
symptoms:
- service method에 제약 annotation을 붙였는데 method validation이 실행되지 않는다.
- 같은 클래스 내부 호출이라 @Validated proxy를 통과하지 못한다.
- request body validation 예외와 method-level ConstraintViolationException의 에러 계약이 섞인다.
linked_paths:
- contents/spring/spring-validation-binding-error-pipeline.md
- contents/spring/aop-proxy-mechanism.md
- contents/spring/spring-self-invocation-proxy-annotation-matrix.md
- contents/spring/spring-bean-lifecycle-scope-traps.md
- contents/spring/transactional-deep-dive.md
- contents/spring/spring-security-method-security-deep-dive.md
expected_queries:
- Spring method validation은 @Valid와 뭐가 달라?
- @Validated를 붙였는데 service method parameter validation이 안 되는 이유는?
- method validation도 self-invocation이면 proxy를 우회해?
- ConstraintViolationException을 API error contract로 어떻게 번역해야 해?
contextual_chunk_prefix: |
  이 문서는 Spring method validation이 @Validated와 proxy interception으로 동작하는
  방식을 다룬다. parameter/return value validation, validation groups,
  self-invocation proxy bypass, ConstraintViolationException, @Valid request body
  validation과 method-level validation의 경계를 진단하는 playbook이다.
---
# Spring Method Validation Proxy Pitfalls

> 한 줄 요약: method validation은 `@Validated`와 proxy 기반 interception으로 동작하므로, self-invocation과 계층 경계를 잘못 잡으면 검증이 조용히 빠질 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
> - [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
> - [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
> - [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Security Method Security Deep Dive](./spring-security-method-security-deep-dive.md)

retrieval-anchor-keywords: method validation, @Validated, constraint groups, executable validation, proxy validation, self invocation, ConstraintViolationException, parameter validation, return value validation

## 핵심 개념

Spring의 method validation은 메서드 입력과 반환값에 제약을 거는 기능이다.

- 파라미터 validation
- return value validation
- group-based validation

중요한 건 이것도 proxy 기반이라는 점이다.

즉, 호출이 프록시를 지나야 검증이 적용된다.

## 깊이 들어가기

### 1. `@Valid`와 method validation은 다르다

- `@Valid`: 주로 객체 바인딩 이후의 validation
- `@Validated`: group과 method-level validation에 쓰임

```java
@Service
@Validated
public class AccountService {

    public void transfer(@Positive Long fromId, @Positive Long toId) {
        ...
    }
}
```

### 2. validation은 실행 전후로 걸릴 수 있다

파라미터는 실행 전에, 반환값은 실행 후에 검증할 수 있다.

```java
@NotNull
public UserDto findUser(@Positive Long id) {
    ...
}
```

### 3. proxy를 안 타면 검증도 안 탄다

같은 클래스 내부에서 직접 호출하면 method validation이 무시될 수 있다.

이건 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)과 같은 함정이다.

### 4. group validation은 요청 종류를 나눈다

예를 들어 생성과 수정은 다른 제약을 가질 수 있다.

```java
public interface CreateGroup {}
public interface UpdateGroup {}
```

```java
@Validated(CreateGroup.class)
public void create(@NotNull(groups = CreateGroup.class) String name) {
}
```

### 5. validation 실패는 보통 `ConstraintViolationException`으로 번역된다

이 예외를 어디서 잡는지 정해야 에러 계약이 일관된다.

## 실전 시나리오

### 시나리오 1: 서비스 메서드에 붙였는데 검증이 안 된다

원인 후보:

- `@Validated`를 안 붙였다
- proxy를 안 탔다
- 내부 self-invocation이었다

### 시나리오 2: 생성과 수정이 같은 validation rule을 쓴다

이 경우 불필요하게 느슨하거나 엄격해진다.

group으로 나누는 것이 낫다.

### 시나리오 3: 반환값 validation이 뒤늦게 터진다

실행 후 검증이므로, 비즈니스 로직이 끝난 뒤 예외가 난다.

이건 의도된 설계지만, 비용이 있다.

### 시나리오 4: controller validation과 service validation이 중복된다

입력 경계와 도메인 경계를 분리해서 봐야 한다.

- controller: 외부 입력 형식
- service: 핵심 제약

## 코드로 보기

### service method validation

```java
@Service
@Validated
public class PaymentService {

    public void pay(@Positive Long orderId, @Positive BigDecimal amount) {
        ...
    }
}
```

### group validation

```java
public interface Create {}

public interface Update {}
```

```java
@Validated(Create.class)
public void create(@NotBlank(groups = Create.class) String name) {
}
```

### exception handling

```java
@RestControllerAdvice
public class ValidationExceptionAdvice {

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ErrorResponse> handle(ConstraintViolationException ex) {
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("METHOD_VALIDATION_FAILED", ex.getMessage()));
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| controller validation | 입력 경계를 지킨다 | 서비스 내부 제약은 못 잡는다 | 외부 요청 검증 |
| method validation | 서비스 계약을 지킨다 | proxy/self-invocation 함정이 있다 | 핵심 도메인 메서드 |
| group validation | 상황별 규칙을 나눈다 | 복잡해질 수 있다 | create/update 구분 |
| manual checks | 제어가 명확하다 | 중복 코드가 늘어난다 | 특수한 규칙 |

핵심은 validation을 어디에 둘지보다, **어떤 계약을 강제하려는지**다.

## 꼬리질문

> Q: `@Valid`와 `@Validated`의 차이는 무엇인가?
> 의도: validation 계층 이해 확인
> 핵심: `@Validated`가 group과 method validation에 더 적합하다.

> Q: method validation이 proxy를 타야 하는 이유는 무엇인가?
> 의도: AOP 기반 동작 이해 확인
> 핵심: 호출 interception으로 검증이 들어가기 때문이다.

> Q: self-invocation에서 검증이 빠질 수 있는 이유는 무엇인가?
> 의도: 프록시 경계 이해 확인
> 핵심: 내부 호출은 프록시를 우회할 수 있다.

> Q: group validation은 언제 유용한가?
> 의도: 계약 분리 이해 확인
> 핵심: 생성/수정/상황별 규칙이 다를 때다.

## 한 줄 정리

Method validation은 서비스 계약을 강제하는 강력한 도구지만 proxy 기반이라 self-invocation과 group 설계를 같이 챙겨야 한다.

# Spring `HandlerMethodArgumentResolver` Pipeline

> 한 줄 요약: `HandlerMethodArgumentResolver`는 컨트롤러 메서드 인자를 만드는 체인이라서, 커스텀 인자를 넣을 때는 누가 어떤 순서로 값을 해석하는지 알아야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
> - [Spring ConversionService, Formatter, and Binder Pipeline](./spring-conversion-service-formatter-binder-pipeline.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)

retrieval-anchor-keywords: HandlerMethodArgumentResolver, argument resolution, MethodArgumentResolver, RequestParamMethodArgumentResolver, PathVariableMethodArgumentResolver, custom argument resolver, controller method parameter, resolver chain

## 핵심 개념

컨트롤러 메서드의 파라미터는 Spring이 리플렉션으로 해석해 채운다.

이때 사용하는 것이 `HandlerMethodArgumentResolver` 체인이다.

- 어떤 resolver가 이 파라미터를 맡을지 고른다
- 선택된 resolver가 실제 값을 만든다

즉, 요청 데이터가 메서드 인자로 들어오는 과정은 "자동 주입"처럼 보이지만 실제로는 **순서가 있는 해석 체인**이다.

## 깊이 들어가기

### 1. resolver는 지원 여부를 먼저 판단한다

각 resolver는 `supportsParameter`로 자기 역할인지 판단한다.

```java
public interface HandlerMethodArgumentResolver {
    boolean supportsParameter(MethodParameter parameter);
    Object resolveArgument(...);
}
```

### 2. 기본 resolver가 많다

Spring MVC는 파라미터 타입과 애노테이션에 따라 여러 resolver를 가진다.

- `@RequestParam`
- `@PathVariable`
- `@RequestBody`
- `@AuthenticationPrincipal`
- `HttpServletRequest`
- `Model`

이 resolver들이 순서대로 후보를 본다.

### 3. 커스텀 resolver는 강력하지만 책임이 크다

```java
@Target(ElementType.PARAMETER)
@Retention(RetentionPolicy.RUNTIME)
public @interface ClientIp {
}
```

```java
public class ClientIpArgumentResolver implements HandlerMethodArgumentResolver {

    @Override
    public boolean supportsParameter(MethodParameter parameter) {
        return parameter.hasParameterAnnotation(ClientIp.class)
            && parameter.getParameterType().equals(String.class);
    }

    @Override
    public Object resolveArgument(MethodParameter parameter,
                                  ModelAndViewContainer mavContainer,
                                  NativeWebRequest webRequest,
                                  WebDataBinderFactory binderFactory) {
        HttpServletRequest request = webRequest.getNativeRequest(HttpServletRequest.class);
        return request != null ? request.getRemoteAddr() : null;
    }
}
```

### 4. resolver와 binder는 연결돼 있다

어떤 resolver는 단순 값 반환이 아니라, binder를 통해 객체를 만든다.

이 문맥은 [Spring ConversionService, Formatter, and Binder Pipeline](./spring-conversion-service-formatter-binder-pipeline.md)와 같이 봐야 한다.

### 5. resolver 남용은 메서드 시그니처를 흐린다

파라미터가 많아질수록 "이 값이 어디서 왔지?"를 보기 어려워진다.

그래서 resolver는 편하지만, 도메인/요청 경계를 흐리지 않게 써야 한다.

## 실전 시나리오

### 시나리오 1: 커스텀 애노테이션을 만들었는데 안 먹는다

대개 resolver 등록을 안 했거나 `supportsParameter`가 틀렸다.

### 시나리오 2: `@RequestBody`와 커스텀 resolver가 충돌한다

resolver 순서와 애노테이션 조건을 확인해야 한다.

### 시나리오 3: Security 정보를 파라미터로 넣고 싶다

기본 resolver 또는 custom resolver를 통해 `SecurityContext` 기반 값을 받을 수 있다.

이건 [Spring Security 아키텍처](./spring-security-architecture.md)와 연결된다.

### 시나리오 4: 테스트에서는 되는데 운영에서는 null이다

요청 컨텍스트가 실제로 들어왔는지, body가 이미 소비되지 않았는지 확인해야 한다.

## 코드로 보기

### custom annotation

```java
@Target(ElementType.PARAMETER)
@Retention(RetentionPolicy.RUNTIME)
public @interface TenantId {
}
```

### resolver registration

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
        resolvers.add(new ClientIpArgumentResolver());
    }
}
```

### controller use

```java
@GetMapping("/me")
public String me(@ClientIp String clientIp) {
    return clientIp;
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 기본 resolver만 사용 | 단순하다 | 커스텀이 어렵다 | 일반 MVC |
| custom resolver | 선언적으로 편하다 | 디버깅이 어렵다 | 반복되는 요청 컨텍스트 |
| 파라미터 수동 파싱 | 명시적이다 | 보일러플레이트가 많다 | 특수한 요청 |

핵심은 resolver를 "편의 기능"이 아니라 **파라미터 해석 규칙**으로 보는 것이다.

## 꼬리질문

> Q: `HandlerMethodArgumentResolver`는 무엇을 하는가?
> 의도: MVC 인자 해석 이해 확인
> 핵심: 컨트롤러 메서드 인자를 만든다.

> Q: 커스텀 resolver가 동작하려면 무엇이 필요한가?
> 의도: 등록과 지원 여부 이해 확인
> 핵심: `supportsParameter`와 등록이 필요하다.

> Q: resolver와 binder의 차이는 무엇인가?
> 의도: 해석과 바인딩 구분 확인
> 핵심: resolver가 후보를 선택하고 binder가 값을 만든다.

> Q: resolver를 남용하면 왜 안 좋은가?
> 의도: API 계약 가독성 확인
> 핵심: 메서드 시그니처가 불투명해진다.

## 한 줄 정리

HandlerMethodArgumentResolver는 컨트롤러 인자 해석 체인이므로, 커스텀 파라미터를 만들 때는 지원 조건과 등록 순서를 같이 봐야 한다.

# Spring CORS: Security vs MVC Ownership

> 한 줄 요약: CORS는 Security와 MVC 어디서나 보일 수 있지만, 실제로는 필터 체인과 핸들러 레이어 중 어디가 정책의 주인이냐를 분리해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)
> - [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)

retrieval-anchor-keywords: CORS, preflight, Access-Control-Allow-Origin, Access-Control-Allow-Credentials, Security filter chain, MVC config, cross-origin request, preflight request

## 핵심 개념

CORS는 브라우저 정책이므로 서버는 그 요청에 맞는 헤더를 제공해야 한다.

문제는 이 정책이 Security와 MVC 둘 다에 연결될 수 있다는 점이다.

- Security에서 막힐 수 있다
- MVC CORS config에서 처리될 수 있다
- preflight 요청은 인증 전에 거를 수도 있다

그래서 ownership을 명확히 해야 한다.

## 깊이 들어가기

### 1. preflight는 OPTIONS 요청이다

브라우저는 실제 요청 전에 OPTIONS preflight를 보낼 수 있다.

### 2. Security가 먼저 막을 수 있다

이 문맥은 [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)와 같이 봐야 한다.

필터 체인이 OPTIONS를 차단하면 CORS 설정이 있어도 실패한다.

### 3. MVC CORS config는 핸들러 수준이다

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
}
```

이런 방식은 컨트롤러 매핑과 함께 CORS 정책을 관리한다.

### 4. allowCredentials와 wildcard는 주의해야 한다

credentials를 쓰면서 `*`를 쓰면 안 되는 경우가 있다.

### 5. 경계는 "누가 먼저 응답하느냐"로 보인다

필터가 먼저 응답하면 MVC는 도달하지 못한다.

## 실전 시나리오

### 시나리오 1: 브라우저에서만 CORS 에러가 난다

curl은 되는데 브라우저가 막는다면 preflight 문제일 수 있다.

### 시나리오 2: Security를 켜자 CORS가 깨진다

필터 순서나 Security CORS 설정을 봐야 한다.

### 시나리오 3: 특정 origin만 허용하고 싶다

정확한 origin 관리가 필요하다.

### 시나리오 4: 개발환경과 운영환경이 다르다

환경별 origin 차이를 분리해야 한다.

## 코드로 보기

### Security CORS

```java
@Bean
SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    return http
        .cors(cors -> {})
        .build();
}
```

### MVC CORS

```java
@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("https://example.com");
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Security ownership | 보안 정책과 통합된다 | 설정이 복잡해질 수 있다 | 인증이 필요한 API |
| MVC ownership | 라우트별 정책이 명확하다 | Security와 중복될 수 있다 | 단순 CORS |
| 둘 다 사용 | 세밀하게 조정된다 | 중복/충돌 위험 | 복잡한 서비스 |

핵심은 CORS를 "브라우저 에러"가 아니라 **보안 필터와 MVC 처리 책임의 경계**로 보는 것이다.

## 꼬리질문

> Q: preflight 요청은 왜 필요한가?
> 의도: 브라우저 교차 출처 정책 이해 확인
> 핵심: 실제 요청 전에 허용 여부를 확인하기 위해서다.

> Q: Security와 MVC 중 어디가 CORS의 주인이 되어야 하는가?
> 의도: ownership 판단 확인
> 핵심: 보안 정책은 보통 Security, 라우트 단 정책은 MVC다.

> Q: `allowCredentials`와 `*`가 왜 문제인가?
> 의도: CORS 헤더 제약 이해 확인
> 핵심: credentials를 허용할 때 wildcard가 제한될 수 있다.

> Q: 브라우저만 실패하고 curl은 성공하는 이유는 무엇인가?
> 의도: preflight 이해 확인
> 핵심: 브라우저가 CORS preflight를 추가로 수행하기 때문이다.

## 한 줄 정리

CORS는 Security와 MVC가 모두 관여할 수 있지만, 실제 책임 주체를 분리해야 preflight와 허용 헤더가 일관되게 동작한다.

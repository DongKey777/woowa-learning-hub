# Spring Security 아키텍처

> 한 줄 요약: Spring Security는 "요청을 막는 프레임워크"가 아니라, 필터 체인 위에서 인증 정보와 권한 판단을 일관되게 흘려보내는 보안 인프라다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
> - [Spring OAuth2 + JWT 통합](./spring-oauth2-jwt-integration.md)
> - [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)
> - [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - [Spring Security `LogoutHandler` / `LogoutSuccessHandler` Boundaries](./spring-security-logout-handler-success-boundaries.md)
> - [Spring Security `RequestCache` / `SavedRequest` Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)
> - [HTTP 메서드, REST, 멱등성](../network/http-methods-rest-idempotency.md)
> - [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
> - [BFF Session Store Outage / Degradation Recovery](../security/bff-session-store-outage-degradation-recovery.md)

retrieval-anchor-keywords: spring security, SecurityFilterChain, FilterChainProxy, SecurityContext, AuthenticationManager, AuthenticationProvider, AuthenticationEntryPoint, AccessDeniedHandler, SecurityContextRepository, SessionCreationPolicy, LogoutFilter, LogoutHandler, LogoutSuccessHandler, RequestCache, SavedRequest, cookie session spring security route, beginner auth bridge, hidden JSESSIONID, why login state is kept, session basics to spring security

---

## 입문 브리지

이 문서는 `Advanced`다. `cookie`, `session`, `JWT`, `stateless`가 아직 한 덩어리로 느껴지면 먼저 한 단계 물러나는 편이 안전하다.

1. 전달 수단과 상태 저장 위치를 먼저 분리한다: [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
2. browser auth 선택지를 비교한다: [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)
3. 그다음 현재 문서에서 `FilterChain`, `SecurityContext`, 인증/인가 흐름을 본다.
4. 숨은 세션 생성과 persistence 경계까지 이어서 보려면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 내려간다.

## 핵심 개념

Spring Security의 핵심은 세 가지다.

1. 요청이 들어오면 `FilterChain`에서 보안 처리를 먼저 수행한다.
2. 인증이 끝나면 `SecurityContext`에 인증 결과를 저장한다.
3. 이후 인가 단계에서 현재 사용자의 권한을 기준으로 접근을 허용하거나 거부한다.

즉, Spring Security는 컨트롤러보다 앞단에서 동작한다.  
`DispatcherServlet` 이전에 보안 필터가 요청을 가로채고, 인증이 성공하면 그 결과를 스레드 로컬 기반 컨텍스트에 보관한 뒤, 이후 로직이 그 정보를 참조한다.

### 주요 구성 요소

- `DelegatingFilterProxy`: 서블릿 컨테이너 필터를 Spring Bean으로 연결하는 다리
- `FilterChainProxy`: Spring Security가 실제로 관리하는 보안 필터 체인
- `SecurityFilterChain`: 요청 경로별로 적용할 필터 집합
- `Authentication`: "누구인가"를 표현하는 인증 결과
- `AuthenticationManager`: 인증 시도를 총괄하는 진입점
- `AuthenticationProvider`: 실제 인증 로직을 담당하는 구현체
- `SecurityContext`: 현재 요청의 인증 정보를 담는 저장소
- `SecurityContextHolder`: `SecurityContext`에 접근하는 정적 진입점

### 인증과 인가

- 인증(Authentication): 사용자가 누구인지 확인하는 과정
- 인가(Authorization): 확인된 사용자가 무엇을 할 수 있는지 판단하는 과정

이 둘을 섞으면 설계가 무너진다.  
예를 들어 "로그인했는가"와 "관리자 권한이 있는가"는 서로 다른 질문이다.

---

## 깊이 들어가기

### 1. 요청이 흘러가는 순서

전형적인 흐름은 아래와 같다.

```text
HTTP Request
  -> DelegatingFilterProxy
    -> FilterChainProxy
      -> SecurityFilterChain 선택
        -> 인증 필터 실행
        -> SecurityContext 저장
        -> 인가 필터 실행
        -> DispatcherServlet
          -> Controller
```

핵심은 "컨트롤러가 인증을 하는 게 아니라, 필터가 먼저 인증을 끝낸다"는 점이다.

### 2. `SecurityContext`의 의미

`SecurityContext`는 현재 요청에서 사용할 인증 정보를 담는다.

- 인증 성공 후 `Authentication` 객체를 저장한다.
- 이후 비즈니스 로직은 `SecurityContextHolder.getContext()`로 사용자 정보를 조회한다.
- 기본 구현은 스레드 로컬을 사용하므로, 요청 스레드와 인증 정보가 연결된다.

여기서 흔한 실수는 비동기 처리나 다른 스레드로 작업을 넘길 때 `SecurityContext`가 자연스럽게 따라간다고 착각하는 것이다.  
스레드가 바뀌면 컨텍스트도 달라질 수 있다.

### 3. `Authentication`과 `GrantedAuthority`

`Authentication`은 단순 문자열이 아니라, 보통 아래 정보를 포함한다.

- principal: 사용자 식별자 또는 사용자 객체
- credentials: 비밀번호나 토큰 같은 인증 증명
- authorities: 권한 목록
- authenticated: 인증 성공 여부

권한은 대개 `ROLE_USER`, `ROLE_ADMIN` 같은 형태로 표현된다.  
실무에서 `hasRole("ADMIN")`과 `hasAuthority("ROLE_ADMIN")`의 차이를 놓치면 접근 제어가 어긋난다.

### 4. 세션 기반 인증

세션 기반 인증은 로그인 성공 후 서버가 세션을 저장하고, 클라이언트는 세션 ID를 쿠키로 들고 다니는 방식이다.

장점:
- 구현이 단순하다
- 서버가 세션을 무효화하면 즉시 로그아웃시킬 수 있다
- 브라우저 기반 웹 앱과 잘 맞는다

단점:
- 서버가 상태를 가진다
- 다중 인스턴스에서는 세션 공유 저장소가 필요하다
- 로드밸런싱 환경에서 세션 스티키 전략이나 외부 세션 저장소가 필요할 수 있다

### 5. JWT 기반 인증

JWT는 서버 세션 없이도 인증 정보를 전달할 수 있어 분산 환경에서 편하다.

장점:
- 서버 상태를 줄이기 쉽다
- 인증 검증을 독립적으로 수행할 수 있다
- API 서버와 모바일/SPA 조합에 잘 맞는다

단점:
- 탈취되면 만료 전까지 악용될 수 있다
- 강제 로그아웃과 토큰 폐기가 까다롭다
- 토큰이 길어져 네트워크 비용이 늘 수 있다

즉 JWT는 "무조건 더 좋은 인증"이 아니라, **세션 저장 비용을 토큰 검증 비용으로 바꾼 선택**이다.

### 6. OAuth2와 JWT

OAuth2는 "인증 수단"이라기보다 **외부 자원 접근 위임 프로토콜**에 가깝다.  
실무에서는 OAuth2 로그인 결과를 바탕으로 애플리케이션 내부 사용자 계정을 매핑하고, 그 뒤 자체 JWT를 발급하는 구성이 많다.

이 경계 설계는 [Spring OAuth2 + JWT 통합](./spring-oauth2-jwt-integration.md)에서 더 자세히 다룬다.

흐름 예시:

1. 사용자가 구글 로그인 버튼을 누른다.
2. Authorization Code Grant로 외부 인증 서버에 위임한다.
3. 사용자 식별 정보를 받아 우리 서비스 사용자와 연결한다.
4. 우리 서비스가 내부 JWT나 세션을 발급한다.

이때 OAuth2의 access token과 우리 서비스의 JWT를 혼동하면 안 된다.  
역할과 발급 주체가 다르다.

---

## 실전 시나리오

### 시나리오 1: `@PermitAll`인데도 차단된다

원인 후보는 다음과 같다.

- 필터 체인에서 CORS나 CSRF 단계에서 먼저 막힘
- 정적 리소스 허용 경로와 실제 요청 경로가 다름
- `permitAll()`과 `web.ignoring()`의 차이를 잘못 이해함

`permitAll()`은 인가를 통과시키는 것이고, `ignoring()`은 보안 필터 자체를 아예 안 타게 하는 것이다.  
운영에서는 대체로 `permitAll()`이 더 안전하다.

### 시나리오 2: JWT 인증이 가끔만 성공한다

체크할 순서:

1. 토큰 포맷 확인
2. 서명 검증 키 확인
3. 만료 시간 확인
4. 필터 등록 순서 확인
5. `SecurityContextHolder`에 인증을 저장했는지 확인

실무에서는 토큰 검증보다 필터 순서 실수가 더 흔하다.

### 시나리오 3: 로그아웃했는데 계속 접근된다

JWT의 전형적인 문제다.  
토큰이 서버에 저장되지 않으면 서버는 보통 "이 토큰이 예전 토큰인지"를 즉시 알기 어렵다.

대응 방식:

- 짧은 access token 만료 시간
- refresh token 별도 저장 및 폐기
- 블랙리스트 저장소 운영
- 민감한 기능만 추가 검증 적용

### 시나리오 4: 관리자 권한인데 403이 난다

자주 있는 원인:

- `ROLE_` prefix 누락
- `hasRole`과 `hasAuthority` 혼동
- 사용자 객체에 권한이 제대로 매핑되지 않음
- `UserDetailsService` 반환값이 잘못 구성됨

---

## 코드로 보기

### 기본 보안 설정

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/public/**", "/login").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            .addFilterBefore(jwtAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class)
            .build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public JwtAuthenticationFilter jwtAuthenticationFilter() {
        return new JwtAuthenticationFilter();
    }
}
```

### JWT 필터 예시

```java
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String token = resolveToken(request);

        if (token != null && validate(token)) {
            Authentication authentication = buildAuthentication(token);
            SecurityContextHolder.getContext().setAuthentication(authentication);
        }

        filterChain.doFilter(request, response);
    }

    private String resolveToken(HttpServletRequest request) {
        String header = request.getHeader("Authorization");
        if (header == null || !header.startsWith("Bearer ")) {
            return null;
        }
        return header.substring(7);
    }
}
```

### 인증 객체 구성 예시

```java
public Authentication buildAuthentication(String token) {
    UserPrincipal principal = new UserPrincipal("donghun", List.of("ROLE_USER"));

    return new UsernamePasswordAuthenticationToken(
        principal,
        null,
        principal.authorities()
    );
}
```

### 메서드 보안 예시

```java
@Service
public class AdminService {

    @PreAuthorize("hasRole('ADMIN')")
    public void deleteUser(Long userId) {
        // 관리자만 허용
    }
}
```

이 방식은 URL 단위 제어보다 세밀한 정책을 적용할 때 유용하다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 적합한 상황 |
|---|---|---|---|
| 세션 인증 | 단순하고 즉시 폐기 가능 | 서버 상태 필요 | 전통적인 웹 서비스, 관리자 콘솔 |
| JWT 인증 | 분산 환경에 유리 | 강제 폐기 어려움 | API 서버, 모바일, SPA |
| OAuth2 로그인 | 외부 계정 연동이 쉬움 | 구조가 복잡해짐 | 소셜 로그인, 외부 IdP 연동 |
| URL 레벨 인가 | 구현이 쉽다 | 정책이 커지면 한계 | 단순한 권한 모델 |
| 메서드 레벨 인가 | 세밀한 제어 가능 | 설정 누락 위험 | 업무 규칙이 복잡한 서비스 |

### 선택 기준

- 서버가 세션을 들고 있어도 괜찮다면 세션이 단순하다.
- 여러 서비스/앱에서 공통 인증을 쓰려면 JWT가 편하다.
- 외부 계정 로그인까지 필요하면 OAuth2가 필요하다.
- 인가 규칙이 복잡하면 URL보다 메서드 보안이 더 정확하다.

---

## 꼬리질문

> Q: `permitAll()`과 `web.ignoring()`은 어떻게 다른가?
> 의도: 필터 체인의 존재를 이해하는지 확인
> 핵심: `permitAll()`은 필터는 타고 인가만 통과, `ignoring()`은 보안 필터 자체를 건너뜀

> Q: JWT를 쓰면 왜 완전한 stateless가 아닌가?
> 의도: 토큰 폐기, 블랙리스트, refresh token 저장 여부를 이해하는지 확인
> 핵심: 토큰 검증은 stateless에 가깝지만, 운영에서는 폐기와 회수를 위해 상태가 다시 생긴다

> Q: `SecurityContextHolder`는 왜 스레드 로컬을 쓰는가?
> 의도: 요청 단위 인증 정보 격리 개념 확인
> 핵심: 한 요청의 인증 정보를 다른 요청과 섞지 않기 위해서다

> Q: OAuth2와 JWT는 같은 건가?
> 의도: 인증 위임과 토큰 형식을 구분하는지 확인
> 핵심: OAuth2는 위임 프로토콜, JWT는 토큰 표현 방식이다

> Q: `hasRole("ADMIN")`이 안 먹을 때 가장 먼저 볼 것은?
> 의도: 권한 prefix와 매핑 실수 파악
> 핵심: `ROLE_` prefix, `GrantedAuthority` 값, `UserDetailsService` 반환값 순서로 확인한다

---

## 한 줄 정리

Spring Security는 필터 체인에서 인증을 끝내고 `SecurityContext`에 결과를 저장한 뒤, 그 정보를 바탕으로 인가를 수행하는 구조이며, 세션·JWT·OAuth2는 그 위에서 선택하는 서로 다른 운영 모델이다.

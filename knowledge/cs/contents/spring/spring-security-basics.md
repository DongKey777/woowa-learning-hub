# Spring Security 기초: 인증과 인가의 흐름 잡기

> 한 줄 요약: Spring Security는 필터 체인이 HTTP 요청을 가로채 인증(누구인지 확인)과 인가(뭘 할 수 있는지 판단)를 처리하고, 실패하면 적절한 응답을 반환한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Security 아키텍처](./spring-security-architecture.md)
- [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)
- [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
- [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring security basics, spring security 입문, spring security filter chain beginner, 처음 배우는데 security filter chain, security filter chain 큰 그림, security filter chain 기초, security filter chain 언제 쓰는지, spring security 401 403 차이, spring security 로그인 흐름, spring security 세션 기초, spring security 뭐예요, httpsecurity 기초, spring security basics basics, spring security basics beginner, spring security basics intro

## 핵심 개념

Spring Security는 인증(Authentication)과 인가(Authorization)를 담당하는 프레임워크다.

- **인증**: 요청한 사람이 누구인지 확인하는 것. 로그인, 토큰 검증 등.
- **인가**: 인증된 사람이 이 자원에 접근할 권한이 있는지 판단하는 것.

입문자가 자주 헷갈리는 이유는 필터 체인이 눈에 보이지 않고, 401과 403의 차이, 그리고 어디서 로그인을 처리하는지 흐름이 불명확하기 때문이다.

## 한눈에 보기

```text
HTTP 요청
  -> SecurityFilterChain (여러 필터가 순서대로 실행)
  -> 인증 필터 (UsernamePasswordAuthenticationFilter 등)
  -> SecurityContextHolder에 인증 정보 저장
  -> 인가 필터 (AuthorizationFilter)
  -> 컨트롤러 실행
```

처음 배우는데 `security filter chain`이 낯설다면, 큰 그림은 아래 3문장으로 잡으면 된다.

1. 요청이 컨트롤러에 닿기 전에 보안 필터 묶음이 먼저 돈다.
2. 앞쪽 필터는 "누구인지" 확인하고, 뒤쪽 필터는 "들어와도 되는지" 판단한다.
3. 순서가 바뀌면 인증 실패와 권한 실패가 섞여 보인다.

| 상황 | HTTP 상태 코드 | 의미 |
|---|---|---|
| 인증 안 됨 | 401 Unauthorized | 로그인이 필요하다 |
| 인증은 됐지만 권한 없음 | 403 Forbidden | 접근 권한이 없다 |

## 상세 분해

- **필터 체인**: Spring Security는 서블릿 필터 체인 위에서 동작한다. Spring의 Bean이 아닌 서블릿 레이어에서 먼저 요청을 가로챈다.
- **`SecurityContextHolder`**: 현재 인증된 사용자 정보를 스레드 로컬에 저장하는 곳이다. 컨트롤러에서 `SecurityContextHolder.getContext().getAuthentication()`으로 인증 정보를 꺼낼 수 있다.
- **`HttpSecurity` 설정**: 어떤 URL은 인증 없이 접근 가능하고(`permitAll`), 어떤 URL은 로그인이 필요한지(`authenticated`), 어떤 URL은 특정 역할이 필요한지(`hasRole`) 설정한다.
- **`UserDetailsService`**: 사용자 이름으로 사용자 정보를 불러오는 인터페이스. 로그인 시 DB에서 사용자를 조회할 때 이 인터페이스를 구현한다.
- **`PasswordEncoder`**: 비밀번호를 암호화하고 비교하는 컴포넌트. `BCryptPasswordEncoder`가 가장 많이 쓰인다.

## 흔한 오해와 함정

**오해 1: 401과 403은 같은 의미다**
401은 인증 자체가 안 된 것(로그인 필요), 403은 인증은 됐지만 권한이 없는 것이다. 구분하지 않으면 디버깅이 어려워진다.

**오해 2: `@PreAuthorize`는 컨트롤러에만 쓸 수 있다**
서비스 레이어 메서드에도 붙일 수 있다. 단 메서드 시큐리티를 활성화(`@EnableMethodSecurity`)해야 한다.

**오해 3: Spring Security를 추가하면 모든 엔드포인트가 자동으로 보호된다**
기본 설정에서는 그렇게 동작하지만, 명시적 `SecurityFilterChain` Bean을 정의하는 순간 기본 설정이 대체된다. `permitAll`을 빠뜨리면 공개해야 할 엔드포인트도 막힐 수 있다.

## 실무에서 쓰는 모습

가장 기본적인 `SecurityFilterChain` 설정 패턴이다.

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .anyRequest().authenticated()
            )
            .formLogin(Customizer.withDefaults());
        return http.build();
    }
}
```

`/api/public/**`은 누구나 접근 가능하고, 나머지는 로그인한 사용자만 접근 가능하다.

## 더 깊이 가려면

- `security filter chain`의 큰 그림은 이해했는데 "그래서 어느 필터가 먼저 도는가?"가 궁금해졌다면 [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)으로 넘어간다.
- 필터 체인 내부 구조, `AuthenticationManager`, `AuthenticationProvider` 흐름은 [Spring Security 아키텍처](./spring-security-architecture.md)에서 자세히 다룬다.
- HTTP 세션, 쿠키 기반 인증의 기초는 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)를 먼저 읽으면 더 명확해진다.
- 메서드 레벨 시큐리티(`@PreAuthorize`, `@PostAuthorize`)는 고급 주제에 해당한다.

## 면접/시니어 질문 미리보기

> Q: 401과 403의 차이는 무엇인가?
> 의도: 인증과 인가 구분 확인
> 핵심: 401은 인증 없음(로그인 필요), 403은 인증됐지만 권한 없음이다.

> Q: Spring Security는 어느 레이어에서 동작하는가?
> 의도: 필터 체인 위치 이해 확인
> 핵심: 서블릿 필터 레이어에서 동작하므로 컨트롤러보다 먼저 요청을 처리한다.

> Q: `SecurityContextHolder`에 저장된 정보는 언제 사라지는가?
> 의도: 스레드 로컬 생명주기 이해 확인
> 핵심: 기본 전략은 스레드 로컬이라 요청 처리 스레드가 반환될 때 자동으로 정리된다.

## 한 줄 정리

Spring Security는 필터 체인이 요청을 가로채 인증(401) → 인가(403) 순으로 판단하고, `HttpSecurity` 설정으로 URL별 접근 규칙을 정의한다.

# 인증과 인가의 차이

> 한 줄 요약: 인증은 `누구인가`를 확인하는 일이고, 인가는 `무엇을 할 수 있는가`를 판단하는 일이다. 둘을 섞으면 가장 먼저 관리자 권한과 데이터 접근 제어에서 사고가 난다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)
> - [시스템 설계 면접 프레임워크](../system-design/system-design-framework.md)

---

## 핵심 개념

인증(Authentication)은 사용자가 정말 그 사람인지 확인하는 과정이다.

- 아이디/비밀번호로 로그인한다
- 소셜 로그인으로 신원을 위임받는다
- 토큰 서명과 만료를 검증한다

인가(Authorization)는 인증된 사용자가 특정 자원이나 기능에 접근할 수 있는지 판단하는 과정이다.

- 게시글을 읽을 수 있는가
- 관리자 화면에 들어갈 수 있는가
- 다른 사용자의 주문을 수정할 수 있는가

둘은 순서도 다르다.

1. 먼저 인증으로 `누구인지` 확인한다.
2. 그 다음 인가로 `무엇을 할 수 있는지` 결정한다.

이 둘을 헷갈리면 보통 아래 식으로 터진다.

- 로그인만 하면 관리자 API도 열리는 버그
- 본인 글만 수정해야 하는데 남의 글도 수정되는 버그
- JWT 검증은 했지만 권한 체크를 빼먹은 버그

---

## 깊이 들어가기

### 1. 인증은 신원 확인, 인가는 권한 확인

인증은 입력된 증명 정보가 유효한지 보는 것이다.

- 비밀번호가 맞는가
- 토큰 서명이 유효한가
- 외부 IdP가 이 사용자를 정말 인증했는가

인가는 그 결과로 얻은 사용자 정보에 어떤 권한이 붙어 있는지 보는 것이다.

- `ROLE_ADMIN`인가
- `ORDER_WRITE` 권한이 있는가
- 이 리소스의 소유자인가

### 2. 세션, JWT, OAuth의 역할 경계

이 세 가지를 자주 섞는데, 역할이 다르다.

| 기술 | 주 역할 | 상태 | 흔한 오해 |
|------|--------|------|-----------|
| 세션 | 인증 결과를 서버에 저장 | 서버 상태 있음 | 인증 방식 그 자체라고만 생각함 |
| JWT | 인증 결과를 토큰으로 전달 | 서버 상태를 줄이기 쉬움 | 권한 부여까지 토큰만으로 끝난다고 착각함 |
| OAuth2 | 외부 신원/권한 위임 | 프로토콜 | 로그인 방식과 완전히 동일하다고 오해함 |

실무 판단은 대략 이렇다.

- 브라우저 중심이고 강제 로그아웃이 중요하면 세션이 단순하다
- API 서버, 모바일, 분산 환경이면 JWT가 자주 맞는다
- 구글/카카오 같은 외부 계정으로 로그인받고 싶으면 OAuth2를 쓴다

중요한 점은, OAuth2 로그인 결과를 받은 뒤에도 보통 우리 서비스의 인증 체계는 따로 둔다는 것이다.  
외부 계정 인증과 내부 권한 모델은 다른 문제다.

### 3. backend에서 많이 터지는 경계 실수

가장 흔한 실수는 인증 성공만 보고 권한 검사를 생략하는 것이다.

- `isAuthenticated()`만 확인하고 `isAdmin()`을 안 본다
- 토큰 유효성만 검증하고 리소스 소유자 검증을 안 한다
- `POST /users/{id}`에서 path parameter와 로그인 사용자를 비교하지 않는다

이건 보안 사고로 바로 이어진다.  
개발자 입장에서는 "로그인 상태니까 괜찮겠지"가 가장 위험한 가정이다.

### 4. Spring Security와 연결되는 지점

Spring Security에서는 인증이 끝나면 `SecurityContext`에 결과가 들어가고, 이후 인가 단계가 이 정보를 참조한다.  
즉 인증과 인가는 한 덩어리가 아니라 파이프라인의 다른 단계다.

이 구조는 [Spring Security 아키텍처](../spring/spring-security-architecture.md)에서 더 자세히 이어진다.

---

## 실전 시나리오

### 시나리오 1: 로그인만 하면 관리자 API가 열림

원인:

- 인증은 했지만 인가를 안 했다
- `authenticated()`만 확인하고 `hasRole("ADMIN")`을 안 걸었다

결과:

- 일반 사용자가 관리자 페이지를 볼 수 있다
- 설정 변경, 사용자 삭제 같은 기능이 노출된다

### 시나리오 2: 본인만 수정해야 하는데 남의 데이터가 수정됨

원인:

- 권한 체크를 `ROLE_USER` 수준에서만 한다
- 리소스 소유권을 확인하지 않는다

예:

```java
if (currentUserId.equals(targetUserId)) {
    userService.updateProfile(...);
}
```

이 로직이 빠지면 인증은 되어 있어도 인가가 깨진다.

### 시나리오 3: JWT는 검증했는데 여전히 취약함

원인:

- 서명만 검증하고 scope/role을 확인하지 않는다
- 만료 시간이 너무 길다
- refresh token 폐기 전략이 없다

JWT는 인증 전달 수단이지, 모든 권한 문제를 자동으로 해결하지 않는다.

### 시나리오 4: OAuth 로그인 후 내부 권한 모델이 꼬임

원인:

- 소셜 로그인 사용자와 내부 직원 계정을 같은 권한 체계로 뭉개버림
- 외부 IdP의 이메일 검증만 믿고 관리자 권한을 부여함

해결:

- 외부 로그인은 신원 확인까지만 담당하게 한다
- 내부 권한은 우리 서비스의 role/permission 테이블로 별도 관리한다

---

## 코드로 보기

### 1. 인증과 인가를 분리한 Spring Security 설정

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/login", "/public/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            .build();
    }
}
```

핵심은 `permitAll()`은 인증 없이 허용, `hasRole()`은 인가 판단이라는 점이다.

### 2. 소유자 검증 예시

```java
public void updatePost(Long currentUserId, Long postOwnerId, PostCommand command) {
    if (!currentUserId.equals(postOwnerId)) {
        throw new AccessDeniedException("not owner");
    }
    postRepository.update(command);
}
```

role 기반 권한만으로는 부족하고, 자원 소유권 검증이 별도로 필요하다.

### 3. JWT 검증 이후 인가 체크

```java
public void deleteUser(UserPrincipal principal, Long targetUserId) {
    boolean isAdmin = principal.roles().contains("ADMIN");
    boolean isOwner = principal.id().equals(targetUserId);

    if (!isAdmin && !isOwner) {
        throw new AccessDeniedException("forbidden");
    }
}
```

토큰이 유효하다고 해서 모든 작업이 허용되는 것은 아니다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 세션 | 강제 로그아웃이 쉽고 브라우저 기반 앱에 단순하다 | 서버 상태와 공유 저장소가 필요하다 | 전통적인 웹 서비스 |
| JWT | 서버 상태를 줄이기 쉽고 분산 환경에 맞는다 | 폐기와 강제 로그아웃이 어렵다 | API, 모바일, SPA |
| OAuth2 | 외부 계정 연동이 쉽다 | 내부 권한 체계와 분리해서 설계해야 한다 | 소셜 로그인 |
| role-only 인가 | 구현이 쉽다 | 리소스 소유권 같은 세밀한 제어가 약하다 | 단순한 관리자 기능 |
| role + ownership | 사고를 줄인다 | 구현과 테스트가 더 필요하다 | 대부분의 실서비스 |

핵심 판단 기준은 단순하다.

- 신원 확인이 필요한가
- 권한 판단이 필요한가
- 리소스 소유권이 중요한가
- 강제 로그아웃이 중요한가

이 질문에 답하면 기술 선택이 정리된다.

---

## 꼬리질문

> Q: 인증과 인가를 같은 함수에서 처리하면 왜 문제인가?
> 의도: 신원 확인과 권한 판단을 분리해서 설계하는지 확인
> 핵심: 인증 성공과 접근 허용은 다른 결정이다.

> Q: JWT가 있으면 세션이 완전히 필요 없나?
> 의도: 토큰 기반 설계의 장단점 이해 여부 확인
> 핵심: 강제 로그아웃, 폐기, 추적성 때문에 세션이 여전히 유효한 경우가 있다.

> Q: OAuth2 로그인과 우리 서비스 권한은 왜 분리해야 하나?
> 의도: 외부 신원 위임과 내부 인가 모델의 차이 이해 여부 확인
> 핵심: 외부 로그인은 신원 확인까지만 책임지고, 권한은 우리 도메인이 소유해야 한다.

> Q: `hasRole`과 `hasAuthority`는 왜 헷갈리면 안 되나?
> 의도: Spring Security 권한 문자열 규칙 이해 여부 확인
> 핵심: prefix 규칙이 어긋나면 기대한 보호가 동작하지 않을 수 있다.

---

## 한 줄 정리

인증은 `너 누구야`를 확인하는 일이고, 인가는 `그럼 이걸 해도 돼`를 판단하는 일이다. 둘을 분리해야 세션, JWT, OAuth, Spring Security를 제대로 설계할 수 있다.

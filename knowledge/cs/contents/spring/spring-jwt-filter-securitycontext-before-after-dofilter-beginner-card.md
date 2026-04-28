# Spring JWT 필터에서 `filterChain.doFilter(...)` 전후에 무슨 일이 일어날까

> 한 줄 요약: 초급자 기준으로 JWT 필터는 `filterChain.doFilter(...)` 전에 "이 요청이 누구인지"를 `SecurityContext`에 넣어 두고, 그 호출 뒤에는 "뒤쪽 필터와 컨트롤러가 처리한 결과"를 그대로 이어받는다고 보면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `OncePerRequestFilter` vs 일반 `Filter` 입문: 언제 상속부터 시작할까](./spring-onceperrequestfilter-vs-filter-beginner-primer.md)
- [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)
- [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)
- [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- [JWT 깊이 파기](../security/jwt-deep-dive.md)
- [세션·쿠키·JWT 기초](../security/session-cookie-jwt-basics.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring jwt filter beginner, filterchain dofilter before after, securitycontext before controller, jwt filter 뭐해요, dofilter 전후 차이, onceperrequestfilter jwt intro, bearer token securitycontext basics, authenticationprincipal before after, jwt filter 언제 securitycontext 넣나, controller 전에 인증, jwt filter flow beginner, spring security jwt primer

## 핵심 개념

처음에는 장면을 두 칸으로만 자르면 된다.

- `filterChain.doFilter(...)` 전: 토큰을 읽고, 유효하면 "`이 요청은 누구다`"를 `SecurityContext`에 넣는다.
- `filterChain.doFilter(...)` 후: 다음 필터, 컨트롤러, 응답 생성이 끝나고 다시 돌아온다.

즉 JWT 필터는 보통 **컨트롤러가 실행되기 전에 인증 정보를 준비하는 입구 작업**에 가깝다.  
초급자가 자주 헷갈리는 지점은 "`doFilter(...)` 뒤에 인증을 넣어도 되나?"인데, 그러면 이미 뒤쪽 로직이 끝난 뒤라 보통 늦다.

## 한눈에 보기

```text
요청 도착
-> JWT 필터
   1) Authorization 헤더 읽기
   2) 토큰 검증
   3) SecurityContext에 Authentication 저장
   4) filterChain.doFilter(...)
-> 뒤쪽 Security 필터 / 컨트롤러
-> 응답 생성
-> JWT 필터로 복귀
```

| 위치 | 보통 하는 일 | 왜 여기서 하나 |
|---|---|---|
| `doFilter(...)` 호출 전 | 헤더에서 JWT 추출, 검증, 사용자 정보 만들기, `SecurityContext` 저장 | 뒤쪽 필터와 컨트롤러가 현재 사용자를 알아야 하기 때문 |
| `doFilter(...)` 호출 중 | 다음 필터와 컨트롤러로 요청 전달 | JWT 필터 혼자 요청을 끝내지 않고 체인을 이어 가야 하기 때문 |
| `doFilter(...)` 호출 후 | 특별한 후처리가 없으면 그대로 반환 | 이미 뒤쪽에서 응답이 결정됐을 수 있기 때문 |

짧게 외우면 이렇다.  
`before doFilter = 사용자 식별 준비`, `after doFilter = 처리 결과를 들고 돌아오는 구간`.

## 상세 분해

### 1. `doFilter(...)` 전에 하는 일

JWT 필터는 보통 아래 순서로 움직인다.

1. `Authorization: Bearer ...` 헤더를 읽는다.
2. 토큰이 없으면 그냥 다음 단계로 넘긴다.
3. 토큰이 있으면 서명, 만료 시간 등을 검증한다.
4. 검증에 성공하면 `Authentication` 객체를 만든다.
5. 그 객체를 `SecurityContextHolder`에 넣는다.

핵심은 **컨트롤러보다 먼저 현재 사용자를 심어 두는 것**이다. 그래야 뒤쪽에서 `@AuthenticationPrincipal`, 권한 검사, `authenticated()` 판단이 가능하다.

### 2. `filterChain.doFilter(...)`가 의미하는 것

이 호출은 "내 일 끝났으니 다음 순서로 넘긴다"는 뜻이다.

- 뒤쪽 Spring Security 필터가 더 돌 수 있다
- `DispatcherServlet`이 컨트롤러를 찾을 수 있다
- 컨트롤러와 서비스가 실행될 수 있다
- 예외가 나면 뒤쪽 예외 번역 필터가 응답을 만들 수 있다

즉 `doFilter(...)`는 단순한 메서드 호출이 아니라 **요청 처리 바통을 다음 단계에 넘기는 지점**이다.

### 3. `doFilter(...)` 뒤에 다시 돌아오면

뒤쪽 필터와 컨트롤러가 다 끝나면 현재 메서드로 다시 복귀한다.

이때 초급자 기준으로는 보통 두 경우만 기억하면 된다.

- 특별한 후처리가 없으면 그대로 메서드가 끝난다
- 응답 헤더를 조금 만지거나 로그를 남길 수 있다

하지만 사용자 인증을 여기서 처음 넣는 것은 대개 늦다.  
컨트롤러, 권한 검사, `@AuthenticationPrincipal` 사용 시점은 이미 지나갔기 때문이다.

## 흔한 오해와 함정

- "`filterChain.doFilter(...)` 뒤가 더 나중이니 거기서 `SecurityContext`를 넣어야 정확하다"라고 생각하기 쉽다.  
  인증 정보는 뒤쪽 로직이 쓰기 전에 준비돼야 하므로 보통 호출 전에 넣는다.

- "토큰이 없으면 무조건 여기서 `401`을 내려야 한다"라고 생각하기 쉽다.  
  공개 API까지 모두 JWT 필터가 직접 막는 구조는 초급자에게 과하다. 많은 경우 토큰이 없으면 그냥 넘기고, 뒤쪽 인가 규칙이 보호 자원을 막는다.

- "`SecurityContextHolder`에 넣었으니 다음 요청도 자동 유지된다"라고 생각하기 쉽다.  
  현재 요청 안에서만 보이는 것과 다음 요청까지 저장되는 것은 다른 문제다. 다음 요청 복원은 `SecurityContextRepository`나 세션/무상태 전략이 결정한다.

## 실무에서 쓰는 모습

가장 흔한 형태는 아래와 비슷하다.

```java
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {
        String token = resolveToken(request);

        if (token != null && jwtTokenService.validate(token)) {
            Authentication authentication = jwtTokenService.toAuthentication(token);
            SecurityContextHolder.getContext().setAuthentication(authentication);
        }

        filterChain.doFilter(request, response);
    }
}
```

이 코드를 beginner 기준으로 읽으면 된다.

- `if` 블록: 컨트롤러 전에 "누구인지" 준비
- `filterChain.doFilter(...)`: 이제 뒤쪽이 이 사용자 정보를 믿고 처리
- 메서드 종료: 응답이 만들어진 뒤 돌아와 필터도 끝남

그래서 RoomEscape 같은 API에서 controller가 `@AuthenticationPrincipal`로 로그인 사용자를 받는다면, 그 준비는 대개 이 호출 **전**에 끝나 있어야 한다.

## 더 깊이 가려면

- JWT 필터 자체를 왜 `OncePerRequestFilter`로 많이 시작하는지부터 보고 싶다면 [Spring `OncePerRequestFilter` vs 일반 `Filter` 입문: 언제 상속부터 시작할까](./spring-onceperrequestfilter-vs-filter-beginner-primer.md)를 먼저 본다.
- JWT 필터가 security chain 안에서 어디쯤 놓이는지가 궁금하면 [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)으로 이어 간다.
- "`SecurityContextHolder`에 넣었는데 다음 요청에서 anonymous예요"가 핵심 증상이면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 바로 간다.
- JWT 자체의 구조, 서명, 만료, refresh token 설계까지 궁금하면 [JWT 깊이 파기](../security/jwt-deep-dive.md)를 본다.

## 면접/시니어 질문 미리보기

> Q: JWT 필터가 `filterChain.doFilter(...)` 전에 `SecurityContext`를 채우는 이유는 무엇인가?
> 의도: 인증 준비 시점 확인
> 핵심: 뒤쪽 필터와 컨트롤러가 현재 사용자를 알아야 하기 때문이다.

> Q: JWT 필터가 토큰이 없을 때 항상 직접 `401`을 내려야 하는가?
> 의도: 필터 책임과 인가 규칙 분리 확인
> 핵심: 공개 경로가 있으면 그냥 넘기고, 보호 자원은 뒤쪽 Security 규칙이 막는 구조도 흔하다.

> Q: `SecurityContextHolder`에 인증을 넣은 것과 다음 요청까지 로그인 상태가 유지되는 것은 왜 다른가?
> 의도: 현재 요청 컨텍스트와 저장 경계 분리 확인
> 핵심: 현재 요청의 context와 요청 간 persistence는 다른 책임이기 때문이다.

## 한 줄 정리

JWT 필터는 보통 `filterChain.doFilter(...)` 전에 현재 사용자를 `SecurityContext`에 준비해 두고, 그 뒤에는 다음 필터와 컨트롤러가 그 정보를 사용하도록 바통을 넘긴다.

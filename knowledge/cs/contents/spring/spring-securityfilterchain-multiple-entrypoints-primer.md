# Spring `SecurityFilterChain`을 둘로 나눠 `/admin/**`은 `302 /login`, `/api/**`는 `401` JSON으로 안전하게 다루는 입문 primer

> 한 줄 요약: 브라우저 화면과 JSON API가 같은 인증 실패를 읽는 방식이 다르면, `SecurityFilterChain`도 경로별로 나눠 각 요청이 자기 계약에 맞는 `AuthenticationEntryPoint`를 타게 하는 편이 안전하다.
>
> 문서 역할: 이 문서는 beginner primer로서 "`응답 계약 분리`를 실제 체인 분리 설정으로 옮기는 첫 구현 문서"를 맡는다. `SavedRequest`나 쿠키 복원보다 `경로별 entry point 분리`가 핵심일 때 읽는다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](./spring-api-401-vs-browser-302-beginner-bridge.md)
- [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
- [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)
- [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: multiple securityfilterchain primer, spring api 401 admin 302, securityfilterchain entrypoint split, authenticationentrypoint by path, /api 401 json /admin login redirect, spring security mixed app beginner, why api gets login html, securitymatcher order beginner, 두 개 체인 뭐예요, 처음 배우는데 securityfilterchain, admin api auth response split, form login and rest api separation

## 핵심 개념

처음에는 "`실패 원인`"보다 "`누가 이 응답을 읽는가`"를 먼저 보면 된다.

- `/admin/**` 브라우저 페이지는 로그인 화면으로 보내는 흐름이 자연스럽다.
- `/api/**` JSON API는 상태 코드와 JSON body를 직접 돌려주는 흐름이 자연스럽다.

그래서 같은 "아직 로그인 안 됨"이라도 한 체인에서 억지로 하나로 맞추기보다, **경로별 `SecurityFilterChain`이 각자의 entry point를 갖게 분리**하는 편이 초급자 기준 더 안전하다.

## 이 문서가 바로 맞는 질문

이 문서는 "`왜 302와 401이 다른가`"를 넘어서 "`그 차이를 Spring 설정에서 어떻게 분리하지?`"가 남았을 때 읽는다.

| 지금 막힌 질문 | 이 문서가 맞는가 | 이유 |
|---|---|---|
| "`/admin/**`은 login redirect, `/api/**`는 401 JSON으로 실제로 어떻게 나눠요?`" | 예 | `SecurityFilterChain`, `securityMatcher`, entry point 분리를 바로 다룬다 |
| "`api인데 login html 와요`" | 예 | API 요청이 웹 체인을 잘못 타는지 먼저 볼 수 있다 |
| "`cookie 있는데 다시 로그인`" | 아니오 | 체인 분리보다 세션 복원이 먼저 문제일 수 있다 |
| "`로그인 성공 후 원래 URL 복귀 403`" | 아니오 | 체인 선택보다 final `403` 권한 분기가 먼저다 |

즉 이 문서는 `entry point 분리 구현` 문서이고, 세션 persistence primer나 final `403` primer를 대체하지 않는다.

## 한눈에 보기

| 경로 | 주 클라이언트 | 인증 안 됨일 때 기대 응답 | 보통 연결할 것 |
|---|---|---|---|
| `/admin/**` | 브라우저 화면 이동 | `302 /login` | form login entry point |
| `/api/**` | fetch, 모바일, Postman | `401` JSON | JSON `AuthenticationEntryPoint` |
| `/admin/**` 로그인 후 권한 부족 | 브라우저 | `403` | `AccessDeniedHandler` 또는 기본 403 |
| `/api/**` 로그인 후 권한 부족 | API 클라이언트 | `403` JSON | JSON `AccessDeniedHandler` |

```text
request -> FilterChainProxy
        -> 먼저 맞는 SecurityFilterChain 하나 선택

/admin/** -> webChain -> login redirect 가능
/api/**   -> apiChain -> 401 json 가능
```

핵심은 "필터가 두 번 돈다"가 아니라, **요청마다 맞는 체인이 하나 선택된다**는 점이다.

## 상세 분해

### 1. 여러 `SecurityFilterChain`은 "정책을 나누는 스위치"다

하나의 Spring 앱 안에 브라우저 화면과 API가 같이 있으면, 인증 실패 응답도 서로 다른 계약을 가질 수 있다.

이때 다중 체인은 "인증 방식이 두 개"라기보다 "`/admin/**`은 웹 계약", "`/api/**`는 API 계약"처럼 **응답 전략을 경로 기준으로 분리**하는 도구에 가깝다.

### 2. `securityMatcher`가 어느 체인이 이 요청을 맡을지 정한다

`securityMatcher("/api/**")`는 "`/api/**` 요청은 이 체인이 맡아라"라는 뜻이다.

여기서 초급자가 기억할 포인트는 두 가지다.

- 더 구체적인 경로 체인이 먼저 와야 한다.
- 어떤 요청이든 기대한 체인 하나에만 걸려야 한다.

즉 `/api/**`를 위한 JSON 정책을 만들었더라도, 더 앞선 넓은 체인이 먼저 잡아 버리면 여전히 `/login` redirect가 나올 수 있다.

### 3. `AuthenticationEntryPoint`는 "인증 안 됨"의 말투를 정한다

같은 인증 실패라도 말투가 다르다.

- 웹 체인: "로그인 페이지로 이동하세요"
- API 체인: "`401` JSON을 읽으세요"

그래서 브라우저용 form login entry point를 API 체인에 섞으면 `fetch("/api/me")`가 JSON 대신 login HTML을 받는 혼란이 생긴다.

### 4. `403`은 체인 분리와 별개로 권한 단계에서 난다

체인을 잘 나눠도 로그인 후 권한이 부족하면 `403`은 여전히 날 수 있다.

즉 다중 체인이 해결하는 것은 주로 "`302 /login`이냐 `401` JSON이냐" 같은 **인증 실패의 표현 방식**이지, role 매핑 자체를 고쳐 주는 것은 아니다.

### 5. 안전한 기본 감각은 "웹 redirect는 웹에서만"이다

beginner가 가장 많이 줄여야 하는 사고는 이것이다.

- 페이지 UX용 redirect 정책이 API까지 새어 나간다.
- stateless API라고 생각했는데 `SavedRequest`나 login HTML이 보인다.

그래서 mixed app에서는 "`/api/**`는 JSON 실패를 유지한다"를 먼저 고정해 두는 편이 안전하다.

## 흔한 오해와 함정

- "`SecurityFilterChain`을 두 개 만들면 요청 하나가 두 체인을 순서대로 지난다"라고 생각하기 쉽다.  
  아니다. `FilterChainProxy`가 요청마다 맞는 체인 하나를 골라 탄다.

- "`/api/**`에 `permitAll()`만 주면 login redirect가 안 섞이겠지"라고 생각하기 쉽다.  
  공개 경로와 인증 실패 응답 계약은 다른 문제다. 보호된 API라면 JSON entry point를 가진 API 체인이 따로 있어야 한다.

- "`401`과 `302` 차이는 컨트롤러가 JSON을 주느냐 HTML을 주느냐 차이다"라고 생각하기 쉽다.  
  실제로는 컨트롤러 전에 Spring Security가 어떤 entry point를 태우는지가 먼저 갈린다.

- "`@Order`는 고급 옵션이니 나중에 봐도 된다"라고 생각하기 쉽다.  
  다중 체인에서는 어떤 체인이 먼저 매칭되는지가 결과를 바꾸므로 입문 단계에서도 순서를 가볍게라도 알아야 한다.

## 실무에서 쓰는 모습

가장 흔한 mixed app 장면은 이렇다.

1. 비로그인 사용자가 브라우저 주소창으로 `/admin/users`를 연다.
2. 웹 체인이 이 요청을 맡고 `/login` redirect를 만든다.
3. 같은 앱의 프론트엔드 코드가 `fetch("/api/me")`를 보낸다.
4. API 체인이 이 요청을 맡고 `401` JSON을 돌려준다.

코드는 아래처럼 읽으면 충분하다.

```java
@Bean
@Order(1)
SecurityFilterChain apiChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/api/**")
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .exceptionHandling(ex -> ex
            .authenticationEntryPoint(new ApiAuthenticationEntryPoint())
        )
        .build();
}

@Bean
@Order(2)
SecurityFilterChain webChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/admin/**", "/login", "/css/**")
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/login", "/css/**").permitAll()
            .anyRequest().authenticated()
        )
        .formLogin(Customizer.withDefaults())
        .build();
}
```

초급자는 구현 세부보다 아래 체크만 먼저 보면 된다.

- `/api/**` 체인에 JSON entry point가 있는가?
- `/admin/**` 체인에 form login이 있는가?
- 더 넓은 체인이 `/api/**`를 먼저 먹지 않는가?

## 더 깊이 가려면

- 왜 같은 앱에서 브라우저는 `302 /login`, API는 `401`이 자연스러운지부터 잡고 싶다면 [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](./spring-api-401-vs-browser-302-beginner-bridge.md)를 먼저 본다.
- `401`과 `403`을 실제로 누가 최종 결정하는지 보려면 [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)로 간다.
- 다중 체인에서 순서와 matcher 충돌을 더 깊게 보려면 [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)으로 내려간다.
- 브라우저 DevTools 기준으로 `302`와 `401` 증상을 먼저 나누고 싶다면 [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)를 먼저 읽는다.

## 면접/시니어 질문 미리보기

> Q: 왜 `/admin/**`와 `/api/**`를 같은 `AuthenticationEntryPoint`로 처리하면 불편해지는가?
> 의도: browser 계약과 api 계약 분리 확인
> 핵심: 브라우저는 redirect UX가 자연스럽지만 API는 `401` JSON을 직접 읽어야 해서 응답 계약이 다르다.

> Q: 다중 `SecurityFilterChain`에서 가장 먼저 체크할 안전 장치는 무엇인가?
> 의도: matcher와 order 감각 확인
> 핵심: 어떤 요청이 어느 체인에 매칭되는지, 더 넓은 체인이 먼저 잡지 않는지 확인한다.

> Q: 체인을 나눴는데도 `403`이 나는 이유는 무엇인가?
> 의도: authentication failure와 authorization failure 분리 확인
> 핵심: 체인 분리는 인증 실패 응답 계약을 나누는 것이고, 권한 부족은 별도의 인가 규칙 문제일 수 있다.

## 한 줄 정리

브라우저용 `/admin/**`과 JSON용 `/api/**`가 같은 앱에 있으면, 경로별 `SecurityFilterChain`으로 entry point를 분리해 각 요청이 자기 응답 계약을 타게 만드는 편이 가장 안전하다.

# Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지

> 한 줄 요약: 같은 Spring MVC 앱 안에서도 브라우저 페이지 요청은 로그인 화면으로 보내는 `302 /login` 흐름이 자연스럽고, JSON API 요청은 인증 실패를 `401`로 직접 말하는 흐름이 자연스러워서 둘을 같은 실패로 읽으면 금방 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `SecurityFilterChain`을 둘로 나눠 `/admin/**`은 `302 /login`, `/api/**`는 `401` JSON으로 안전하게 다루는 입문 primer](./spring-securityfilterchain-multiple-entrypoints-primer.md)
- [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)
- [Spring Security 기초: 인증과 인가의 흐름 잡기](./spring-security-basics.md)
- [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
- [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
- [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring api 401 vs browser 302, spring login redirect vs json api, api가 login html을 받아요, fetch 401 대신 302, browser page 302 login spring, spring mixed mvc app auth failure, api authentication entry point beginner, form login api separation spring, 처음 배우는데 401 302 차이, json api unauthorized beginner, spring browser redirect api json, login page redirect vs api error

## 핵심 개념

처음에는 "누가 이 응답을 읽는가"만 먼저 보면 된다.

- 브라우저 페이지 요청은 다음 화면으로 이동시켜 주는 것이 중요하다.
- JSON API 요청은 프론트엔드 코드나 다른 클라이언트가 상태 코드를 읽는 것이 중요하다.

그래서 같은 "아직 로그인 안 됨" 상황이어도 결과가 갈린다.

- 브라우저 페이지: `302 /login`
- JSON API: `401 Unauthorized`

입문자가 자주 헷갈리는 이유는 둘 다 결국 "인증 실패"인데, 하나는 이동이고 하나는 데이터 응답이라 모양이 완전히 다르게 보이기 때문이다.

## 한눈에 보기

```text
브라우저가 /admin 페이지 요청
-> 로그인 안 됨
-> login page로 이동시키는 쪽이 편함
-> 302 /login

브라우저 JS 또는 API client가 /api/me 요청
-> 로그인 안 됨
-> redirect보다 상태 코드가 더 중요함
-> 401 JSON
```

| 요청 종류 | 클라이언트가 기대하는 것 | 인증 실패 시 흔한 응답 | 초급자 질문 |
|---|---|---|---|
| 브라우저 페이지 이동 | 다음에 어디로 갈지 | `302 /login` | "로그인 화면으로 보내는 게 자연스러운가?" |
| JSON API 호출 | 상태 코드와 JSON body | `401` | "프론트 코드가 이 실패를 직접 읽어야 하나?" |
| 이미 로그인했지만 권한 부족 | 권한 거부 사실 | `403` | "이건 로그인 문제가 아니라 권한 문제인가?" |

핵심은 `302`와 `401`이 서로 경쟁하는 답이 아니라, **같은 인증 실패를 다른 계약으로 표현한 결과**일 수 있다는 점이다.

이 차이를 실제 설정에서 안전하게 유지하려면 `/admin/**`와 `/api/**`를 서로 다른 `SecurityFilterChain`으로 분리해 각 경로가 자기 `AuthenticationEntryPoint`를 타게 하는 구성이 흔하다.

## 상세 분해

### 1. 브라우저 페이지는 "다음 화면"이 중요하다

비로그인 사용자가 `/admin/reservations` 페이지를 열면, 브라우저는 보통 데이터를 직접 해석하기보다 화면 전환을 따른다.

그래서 Spring Security도 form login 중심 앱에서는 이런 흐름을 자주 만든다.

- 보호된 페이지 접근
- 로그인 안 됨
- `/login`으로 redirect
- 로그인 후 원래 페이지로 복귀할 수도 있음

즉 페이지 요청의 `302 /login`은 "실패를 숨긴다"기보다 "로그인 화면으로 안내한다"에 가깝다.

### 2. JSON API는 "화면 이동"보다 "실패 사실 전달"이 중요하다

반대로 `fetch("/api/me")`나 모바일 앱의 `/api/me` 호출은 redirect된 로그인 HTML보다 실패 정보를 직접 받는 편이 낫다.

이때 보통 기대하는 것은 다음이다.

- 상태 코드: `401`
- 응답 본문: JSON 에러 또는 `ProblemDetail`

그래서 API가 `302 /login`을 돌려주면 프론트엔드는 "로그인이 필요한 상태"를 깔끔하게 처리하기보다, login HTML을 받아 버리거나 redirect를 따라가다 더 헷갈리기 쉽다.

### 3. mixed Spring MVC 앱에서는 두 계약이 함께 존재할 수 있다

초급자가 흔히 보는 장면은 이것이다.

- `/admin/**`는 서버가 렌더링한 페이지 또는 브라우저 화면 흐름
- `/api/**`는 JSON 응답 중심 API

둘 다 같은 Spring 앱 안에 있어도, 인증 실패 응답은 같을 필요가 없다.

오히려 초반 설계 감각은 이렇게 잡는 편이 안전하다.

- 페이지 라우트: login redirect 허용
- API 라우트: `401` JSON 유지

즉 "`앱이 하나니까 인증 실패도 하나로 통일돼야지`"보다 "`클라이언트 계약이 다르니 응답도 갈릴 수 있구나`"가 beginner 기준 더 정확하다.

그리고 이 감각을 실제 Spring Security 설정으로 옮길 때는 `/admin/**`와 `/api/**`를 별도 `SecurityFilterChain`으로 나눠 각 경로가 자기 entry point를 타게 하는 구성이 가장 흔하다.

## redirect 기억과 권한 축 분리

### 4. `302`가 반복되면 redirect 기억과 API 계약이 섞였는지 먼저 본다

로그인 후 원래 URL로 복귀시키는 `RequestCache`와 `SavedRequest`는 브라우저 페이지 UX에는 유용하다.

하지만 API까지 같은 정책을 타면 이런 증상이 나온다.

- `fetch`가 `401` JSON 대신 login page HTML을 받는다
- Postman에서는 `401`을 기대했는데 브라우저에서는 `302 /login`으로 보인다
- stateless API라고 생각했는데 redirect와 세션이 함께 보인다

이때는 권한 규칙보다 먼저 "브라우저용 redirect 정책이 API에도 붙었나?"를 보는 편이 빠르다.

### 5. `403`은 이 문서의 주인공이 아니다

이 문서는 "인증 실패를 `302`로 보여 줄지 `401`로 보여 줄지"를 다룬다.

반면 `403`은 보통 이런 뜻이다.

- 로그인은 됨
- 하지만 권한이 없음

즉 `403`은 "`302`냐 `401`이냐"와 다른 축이다.  
초급자는 먼저 "`아직 인증 안 됨` vs `이미 로그인했지만 권한 없음`"을 분리한 뒤, 그다음 "`인증 안 됨`을 page 계약으로 보일지 API 계약으로 보일지"를 보면 된다.

## 흔한 오해와 함정

- "`302 /login`이면 무조건 브라우저 쪽 문제다"라고 생각하기 쉽다.  
  실제로는 API 경로에 form login용 entry point가 섞였다는 Spring 설정 문제일 수 있다.

- "`401`이 더 HTTP스럽으니 페이지도 전부 `401`로 통일해야 한다"라고 생각하기 쉽다.  
  브라우저 화면 흐름에서는 로그인 페이지 이동 UX가 더 자연스러울 수 있다.

- "`302`와 `401`은 전혀 다른 원인이다"라고 생각하기 쉽다.  
  같은 "인증 안 됨"을 서로 다른 클라이언트 계약으로 표현한 결과일 수 있다.

- "`fetch`가 login HTML을 받았으니 컨트롤러가 HTML을 반환했다"라고 생각하기 쉽다.  
  실제로는 컨트롤러 전에 Spring Security가 redirect를 만들고, 브라우저가 그 결과를 따라간 것일 수 있다.

## 실무에서 쓰는 모습

가장 흔한 mixed app 장면은 이렇다.

1. 사용자가 브라우저 주소창으로 `/admin` 페이지를 연다.
2. 비로그인 상태면 Spring Security가 `/login`으로 보낸다.
3. 같은 앱의 프론트엔드 코드가 `fetch("/api/me")`를 호출한다.
4. 이 요청은 login HTML이 아니라 `401` JSON을 받는 편이 프론트엔드 상태 처리에 맞다.

설정 감각도 두 갈래로 읽으면 된다.

```java
@Bean
SecurityFilterChain apiChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/api/**")
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .exceptionHandling(ex -> ex.authenticationEntryPoint(new Api401EntryPoint()))
        .build();
}

@Bean
SecurityFilterChain webChain(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/login", "/css/**").permitAll()
            .anyRequest().authenticated()
        )
        .formLogin(Customizer.withDefaults())
        .build();
}
```

이 코드를 외우기보다, 초급자는 아래 두 문장만 잡으면 충분하다.

- `/api/**`는 실패를 data 계약으로 돌려준다.
- 페이지 요청은 필요하면 login 화면으로 이동시킨다.

## 더 깊이 가려면

- `302 /login`과 `403`을 먼저 갈라야 한다면 [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)를 먼저 본다.
- `/admin/**`는 login redirect, `/api/**`는 `401` JSON으로 안전하게 분리하는 실제 설정 감각이 필요하면 [Spring `SecurityFilterChain`을 둘로 나눠 `/admin/**`은 `302 /login`, `/api/**`는 `401` JSON으로 안전하게 다루는 입문 primer](./spring-securityfilterchain-multiple-entrypoints-primer.md)로 이어 간다.
- "결국 누가 `302`와 `401`을 최종 결정하나?"가 궁금해지면 [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)로 내려간다.
- 로그인 후 원래 URL 복귀와 API redirect 충돌이 더 궁금하면 [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)를 이어 본다.
- 브라우저 DevTools 기준으로 `401`과 `302` 증상을 먼저 나누고 싶다면 [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)를 먼저 본다.
- 쿠키와 세션 자체가 아직 흐리면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)부터 다시 맞춘다.

## 면접/시니어 질문 미리보기

> Q: 같은 Spring 앱인데 어떤 요청은 `302 /login`, 어떤 요청은 `401`이 되는 이유는 무엇인가?
> 의도: browser page 계약과 JSON API 계약 분리 확인
> 핵심: 둘 다 인증 실패일 수 있지만, 페이지 요청은 redirect UX가 자연스럽고 API 요청은 상태 코드와 JSON 응답이 자연스럽다.

> Q: `fetch("/api/me")`가 `401` JSON 대신 login HTML을 받으면 무엇을 먼저 의심해야 하는가?
> 의도: browser redirect 정책과 API 경계 분리 확인
> 핵심: API 경로에 form login용 entry point나 request cache가 섞였는지 먼저 본다.

> Q: `403`은 왜 `302` vs `401` 이야기와 다른 축인가?
> 의도: authentication failure와 authorization failure 분리 확인
> 핵심: `403`은 로그인 후 권한 부족이고, `302`와 `401`은 보통 아직 인증 안 됐을 때의 표현 방식 차이다.

## 한 줄 정리

같은 Spring MVC 앱에서도 브라우저 페이지는 `302 /login`, JSON API는 `401`이 더 자연스러운 계약일 수 있으므로, mixed app 인증 실패는 "누가 이 응답을 읽는가"부터 나눠서 봐야 한다.

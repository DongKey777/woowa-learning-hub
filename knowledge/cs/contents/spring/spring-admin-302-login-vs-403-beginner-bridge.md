# Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지

> 한 줄 요약: 관리자 URL에서 `302 /login`은 대개 "아직 인증이 안 됐으니 로그인부터" 흐름이고, `403`은 "누군지는 확인됐지만 관리자 권한이 없음" 흐름이라서 redirect 기억과 권한 실패를 분리해서 봐야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)
- [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](./spring-api-401-vs-browser-302-beginner-bridge.md)
- [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)
- [Spring Security 기초: 인증과 인가의 흐름 잡기](./spring-security-basics.md)
- [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
- [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
- [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md)
- [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring admin 302 vs 403, admin request redirect vs forbidden, spring security admin login redirect, 302 /login 왜 가요, admin 403 왜 나요, savedrequest beginner, requestcache basics, authentication vs authorization spring, admin page not logged in, admin page role missing, 처음 배우는데 302 403 차이, spring security redirect memory, 로그인 페이지로 튀어요 spring, 권한 없어서 403 spring

## 핵심 개념

초급자 기준으로는 먼저 질문을 둘로 쪼개면 된다.

- `302 /login`: "이 요청을 보낸 사용자가 아직 로그인하지 않았다. 먼저 로그인시키고 원래 URL로 돌아오게 하자."
- `403`: "로그인은 했지만 이 URL에 들어올 권한은 없다."

헷갈리는 이유는 둘 다 "관리자 페이지 접근 실패"로 보이기 때문이다.  
하지만 실제로는 하나는 **인증 전 단계**, 다른 하나는 **인증 후 권한 단계**다.

## 한눈에 보기

| 먼저 확인할 것 | 보통 보이는 응답 | 의미 | 초급자용 다음 질문 |
|---|---|---|---|
| 로그인 자체가 안 됨 | `302 /login` 또는 API면 `401` | 인증부터 필요하다 | "지금 익명 사용자였나?" |
| 로그인은 됐음 | `403` | 관리자 권한이 부족하다 | "이 사용자가 `ADMIN`인가?" |
| 로그인 후 다시 원래 URL로 복귀 | `302`가 한 번 더 보일 수 있음 | `SavedRequest`가 로그인 전에 가려던 주소 메모를 다시 쓴다 | "주소 메모 흐름이 켜져 있나?" |

```text
/admin 요청
-> 아직 로그인 안 됨
-> AuthenticationEntryPoint
-> /login 으로 redirect (브라우저면 302 가능)

/admin 요청
-> 로그인은 됨
-> 권한 검사 실패
-> AccessDeniedHandler
-> 403
```

핵심은 `302`를 봤다고 바로 "권한이 없네"라고 결론 내리면 안 된다는 점이다.  
`302`는 권한 실패보다 먼저, "로그인 절차로 보내는 동작"일 가능성이 크다.

## 처음엔 이 세 사용자만 구분하면 된다

| 지금 사용자 상태 | `/admin/**`에서 자주 보이는 결과 | 초급자 해석 |
|---|---|---|
| 비로그인 사용자 | `302 /login` | "누군지 모르니 로그인부터" |
| 로그인한 일반 사용자 | `403` | "누군지는 알지만 관리자 아님" |
| 로그인한 관리자 사용자 | `200` 또는 정상 페이지 | "인증과 권한 둘 다 통과" |

이 표를 먼저 잡아 두면 "`302`도 접근 거부니까 `403`이랑 같은 것 아닌가?"라는 혼란이 많이 줄어든다.

## `SavedRequest`는 보통 어디서 끼어드나

beginner가 한 칸만 더 기억하면 연결이 쉬워진다.  
`SavedRequest`는 주로 `403` 자체보다 **비로그인 사용자를 `/login`으로 보내는 302 갈래**에서 같이 보인다.

```text
GET /admin/reservations
-> 아직 비로그인
-> RequestCache가 원래 URL을 잠깐 저장
   (SavedRequest: "/admin/reservations")
-> /login 으로 302 redirect
-> 로그인 성공
-> SavedRequest를 보고 원래 URL로 다시 이동
```

핵심은 "`SavedRequest` = 로그인 전에 가려던 주소 메모"라는 점이다.  
그래서 `SavedRequest`는 보통 `302 /login` 흐름을 설명할 때 먼저 등장하고, 마지막 `403`의 직접 원인으로 읽으면 안 된다.

같은 장면에서 자주 같이 나오는 초급 표현도 같이 맞춰 두면 좋다.

| 용어 | 초급 표현 | 이 문서에서 보는 순간 |
|---|---|---|
| `session` | 서버가 로그인 상태를 기억하는 보관함 | 로그인 성공 뒤 사용자를 다시 찾을 때 |
| `SecurityContext` | 이번 요청에서 바로 꺼내 쓰는 로그인 메모 | `/admin/**`에 들어갈 현재 사용자를 판단할 때 |
| `SavedRequest` | 로그인 전에 가려던 주소 메모 | `/login` 뒤 원래 URL로 다시 보낼 때 |

## 상세 분해

### 1. `302 /login`은 보통 브라우저 로그인 흐름이다

예를 들어 비로그인 상태로 `/admin/reservations`를 열면 Spring Security는 컨트롤러까지 보내지 않고 로그인 쪽으로 먼저 보낼 수 있다.

이때 브라우저 기반 form login이라면 흔히 이렇게 보인다.

- 보호된 URL 접근
- 인증 정보가 없음
- 로그인 페이지로 redirect
- 원래 요청 URL은 나중 복귀용으로 저장될 수 있음

즉 `302 /login`은 보통 "관리자 권한 없음"보다 "아직 누구인지 모름"에 가깝다.

### 2. `403`은 이미 누구인지 아는 상태에서 난다

반대로 일반 사용자로 로그인한 뒤 `/admin/**`에 접근하면 상황이 다르다.

- 세션이나 토큰으로 사용자는 확인됨
- 하지만 `ADMIN` 권한이 없음
- 그래서 로그인 페이지로 다시 보낼 필요가 없음
- 바로 `403 Forbidden`

즉 `403`은 "다시 로그인해도 해결되지 않을 수 있는 실패"다.  
문제의 중심이 인증이 아니라 권한 규칙이기 때문이다.

### 3. `RequestCache`는 권한 검사가 아니라 "원래 URL 기억" 역할이다

초급자가 자주 섞는 포인트가 여기다.

`RequestCache`와 `SavedRequest`는 "로그인 성공 후 어디로 돌려보낼까?"를 돕는 장치다.

- 비로그인 사용자가 `/admin/reservations` 요청
- Spring Security가 그 URL을 잠깐 기억
- 로그인 성공
- 원래 `/admin/reservations`로 다시 이동

이 흐름은 **redirect memory** 문제다. 보통 이 기억 장치가 `SavedRequest`로 보인다.  
`403`처럼 "권한이 없어서 막혔다"는 문제와는 축이 다르다.

### 4. 브라우저와 API는 같은 인증 실패라도 응답이 다를 수 있다

브라우저 웹 앱에서는 로그인 페이지로 보내는 것이 자연스럽다.  
그래서 인증 안 된 관리자 요청이 `302 /login`으로 보일 수 있다.

하지만 JSON API라면 보통 redirect보다 상태 코드 본문이 더 중요하다.

- 브라우저 UI: `302 /login`이 흔함
- API: 보통 `401` 또는 `403` JSON을 기대

그래서 관리자 API를 만들 때 "`302 /login`이 보인다"면 권한 규칙보다 먼저 "브라우저용 로그인 redirect 설정이 API에도 섞였나?"를 의심하는 편이 빠르다.

## 흔한 오해와 함정

- "`302 /login`도 결국 관리자 접근 거부니까 `403`이랑 같은 거다"라고 생각하기 쉽다.  
  아니다. `302`는 대개 인증하러 이동시키는 동작이고, `403`은 인증 후 권한 부족이다.

- "로그인 후 원래 `/admin`으로 돌아왔으니 권한도 통과한 것이다"라고 생각하기 쉽다.  
  아니다. 복귀는 `SavedRequest`가 도와줄 수 있지만, 돌아온 뒤에도 권한이 없으면 결국 `403`이 날 수 있다.

- "로그인 성공 후 원래 `/admin/**` URL로 복귀했다가 마지막에 `403`이 났으니 `SavedRequest`가 잘못됐다"라고 생각하기 쉽다.  
  실제로는 `SavedRequest`는 정상 동작했고, `hasRole("ADMIN")`와 실제 authority 이름이 어긋나 마지막 인가에서 실패한 경우가 많다. 이 경우는 [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md)로 바로 이어 간다.

- "`403`이 났으니 로그인 페이지로 보내면 해결된다"라고 생각하기 쉽다.  
  이미 로그인된 사용자의 권한 문제라면 재로그인보다 역할 매핑과 `hasRole("ADMIN")` 규칙을 먼저 봐야 한다.

- "API에서 `302 /login`이 보였으니 컨트롤러 redirect 코드 문제다"라고 생각하기 쉽다.  
  실제로는 Spring Security의 entry point와 request cache 조합일 수 있다.

## 실무에서 쓰는 모습

RoomEscape 관리자 기능을 떠올리면 이해가 쉽다.

1. 비로그인 브라우저가 `GET /admin/reservations`를 호출한다.
2. Security는 "아직 인증 안 됨"으로 판단하고 로그인 페이지로 보낸다.
3. 이때 원래 URL을 기억했다면 로그인 후 다시 `/admin/reservations`로 보낸다.
4. 반대로 일반 사용자 계정으로 이미 로그인한 상태라면, 다시 로그인 페이지로 보낼 이유가 없다.
5. 그 사용자가 `ADMIN`이 아니면 바로 `403`으로 끝난다.

설정 감각도 이 두 갈래와 연결된다.

```java
http.authorizeHttpRequests(auth -> auth
    .requestMatchers("/admin/**").hasRole("ADMIN")
    .anyRequest().permitAll()
);
```

이 설정에서 `/admin/**`는 "로그인만 하면 됨"이 아니라 "`ADMIN`이어야 함"을 뜻한다.  
그래서 익명 사용자는 먼저 인증 단계로 가고, 로그인 사용자는 권한 단계에서 `403`을 받을 수 있다.

## 초급자 체크 순서

1. 지금 사용자가 아예 비로그인인지, 이미 로그인한 일반 사용자인지 먼저 나눈다.
2. 비로그인이면 `302 /login`과 `SavedRequest` 흐름을 본다.
3. 로그인 사용자면 `hasRole("ADMIN")`, authority 이름, 역할 매핑을 본다.
4. 브라우저가 아니라 API 호출이라면 redirect보다 `401`/`403` 응답 계약이 맞는지도 함께 본다.

## 더 깊이 가려면

- 브라우저 쿠키와 서버 세션이 `/admin/**` 판단까지 어떻게 이어지는지 먼저 묶고 싶다면 [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)를 먼저 본다.
- 같은 앱 안에서 브라우저 페이지는 `302 /login`인데 JSON API는 `401`이어야 하는 이유를 먼저 떼어 보고 싶다면 [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](./spring-api-401-vs-browser-302-beginner-bridge.md)로 이어 간다.
- `302`와 `403`을 누가 최종 결정하는지 더 정확히 보고 싶다면 [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)로 간다.
- "이제 어느 필터가 이 `302 /login`과 `403` 분기를 실제로 만드는가?", "예외 번역 필터가 인증 실패와 권한 실패를 어느 순서에서 가르는가?"가 다음 질문이라면 [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)으로 이어 간다.
- 로그인 후 원래 관리자 URL로 돌아가는 과정이 이상하면 [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)로 이어 간다.
- 브라우저 redirect와 API `401` 계약이 왜 갈리는지부터 보고 싶다면 [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)를 먼저 읽는다.
- 세션과 쿠키가 아직 흐리면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)로 한 단계 내려가 개념을 맞춘다.

## 면접/시니어 질문 미리보기

> Q: 관리자 URL에서 `302 /login`과 `403`의 차이는 무엇인가?
> 의도: 인증 실패와 권한 실패 구분 확인
> 핵심: `302 /login`은 보통 인증 전 로그인 유도이고, `403`은 인증 후 권한 부족이다.

> Q: 로그인 후 원래 `/admin` URL로 복귀하는 것은 어느 개념과 관련 있는가?
> 의도: redirect memory와 authorization 분리 확인
> 핵심: `RequestCache`와 `SavedRequest`가 원래 요청을 기억하는 흐름이다.

> Q: 왜 API에서는 `302 /login`보다 `401` JSON이 더 자연스러운가?
> 의도: 브라우저와 API 응답 계약 차이 확인
> 핵심: API 클라이언트는 redirect된 로그인 HTML보다 명시적인 인증 실패 응답을 기대하기 때문이다.

## 한 줄 정리

관리자 요청에서 `302 /login`은 대개 "먼저 로그인" 흐름이고 `403`은 "이미 로그인했지만 관리자 권한이 없음" 흐름이므로, redirect 기억과 권한 실패를 같은 문제로 보면 안 된다.

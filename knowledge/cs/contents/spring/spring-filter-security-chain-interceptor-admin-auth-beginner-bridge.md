---
schema_version: 3
title: Spring Filter vs Spring Security Filter Chain vs HandlerInterceptor
concept_id: spring/spring-filter-security-chain-interceptor-admin-auth-beginner-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
aliases:
- Filter vs SecurityFilterChain vs HandlerInterceptor
- spring security filter chain beginner
- filter interceptor security 차이
- addFilterBefore 처음
- jwt filter 어디에 두나
intents:
- comparison
- design
linked_paths:
- contents/spring/spring-security-filter-chain.md
- contents/spring/spring-security-filter-chain-ordering.md
- contents/spring/spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card.md
- contents/security/browser-401-vs-302-login-redirect-guide.md
- contents/security/session-cookie-jwt-basics.md
confusable_with:
- spring/spring-security-filter-chain-ordering
- spring/spring-security-requestcache-savedrequest-boundaries
expected_queries:
- Spring Filter랑 SecurityFilterChain, HandlerInterceptor 차이가 뭐야?
- 관리자 인증에서 302 403 400이 섞이면 어디서 먼저 나눠?
- jwt filter를 어디에 두는지 처음 보기 전에 어떤 큰 그림을 봐?
- HandlerInterceptor에서 인증을 막아도 되는지 헷갈려
contextual_chunk_prefix: |
  이 문서는 *세 가지를 가르는 chooser bridge* — 일반 servlet Filter 체인
  vs Spring Security Filter Chain vs HandlerInterceptor — 가 처음 헷갈리는
  학습자에게 어디가 어떻게 다른지 가르는 entrypoint다. Spring Security
  filter chain만 깊이 다루는 deep_dive doc이 아니라 *세 갈래 중 어느 doc으로
  갈지 결정하는 chooser*다. 일반 Filter 체인 vs Spring Security Filter Chain,
  filter vs interceptor 차이, 관리자 페이지 접근 막는 코드를 컨트롤러
  들어가기 전에 둘지 직전에 둘지, 세 갈래 entrypoint, jwt filter 위치 같은
  자연어 paraphrase가 본 chooser bridge의 세 갈래 결정에 매핑된다.
---

# Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지

> 한 줄 요약: RoomEscape 관리자 인증 흐름을 처음 잡을 때는 "`Filter`는 웹 입구", "Spring Security filter chain은 인증/인가 묶음", "`HandlerInterceptor`는 컨트롤러 주변 보조 작업"으로 나누면 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)
- [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)
- [Spring Security 기초: 인증과 인가의 흐름 잡기](./spring-security-basics.md)
- [Spring Security `RequestCache` / `SavedRequest` Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)
- [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
- [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)
- [Spring `DispatcherServlet` / `HandlerInterceptor` 입문 브리지: 큰 그림부터 잡기](./spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md)
- [쿠키 속성 매트릭스: `SameSite`, `HttpOnly`, `Secure`, `Domain`, `Path`](../network/cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: filter vs security filter chain, spring security filter chain beginner, filter interceptor security 차이, savedrequest 어디서 생기나, 302 login 왜 뜨나, admin api 400 before controller, addfilterbefore 뭐예요, addfilterafter 뭐예요, usernamepasswordauthenticationfilter 앞, usernamepasswordauthenticationfilter 뒤, bearertokenauthenticationfilter 앞, bearertokenauthenticationfilter 뒤, jwt filter 어디에 두나, jwt filter 어디에 둬요, 필터 순서 처음

## 핵심 개념

처음에는 세 칸으로만 보면 충분하다.

- `Filter`: 서블릿 레벨의 입구다. Spring MVC보다 앞에서 요청을 본다.
- Spring Security filter chain: 여러 보안 필터가 묶여 있는 인증/인가 전용 파이프라인이다.
- `HandlerInterceptor`: 보안 검사를 통과한 뒤, 컨트롤러 전후에서 공통 작업을 붙이는 MVC 훅이다.

헷갈리는 이유는 셋 다 "요청 중간에서 뭔가 가로챈다"로 보이기 때문이다.  
하지만 beginner 기준 핵심은 "`누가 먼저 보는가`와 `무엇을 결정하는가`"다.

## 한눈에 보기

```text
브라우저 -> Filter -> Spring Security filter chain -> DispatcherServlet
        -> @RequestBody 변환 -> HandlerInterceptor -> @RestController -> 응답
```

RoomEscape 관리자 API를 예로 들면:

| 위치 | 관리자 요청에서 맡는 일 | 여기서 하면 좋은 일 |
|---|---|---|
| `Filter` | 요청이 웹 앱으로 들어왔음을 가장 먼저 본다 | trace id, 공통 로깅, request wrapping |
| Spring Security filter chain | 로그인 여부와 `ADMIN` 권한을 검사한다 | session/cookie 인증, `401`/`403` 결정 |
| `HttpMessageConverter` + `@RequestBody` binding | Security를 통과한 JSON body를 DTO로 바꾼다 | `400`/`415` 첫 분기, 날짜·시간·enum 파싱 |
| `HandlerInterceptor` | 이미 선택된 컨트롤러 주변에서 보조 작업을 한다 | 관리자 감사 로그, 메뉴 활성화 정보, 실행 시간 측정 |

한 문장으로 줄이면 이렇다.

- 관리자 인증을 "막는" 중심은 보통 Spring Security filter chain이다.
- 관리자 `POST` API의 JSON을 "DTO로 바꾸는" 중심은 `@RequestBody` binding 단계다.
- 인터셉터는 "누가 왔는지 이미 정해진 뒤" 덧붙이는 작업에 가깝다.

보안 체인 안쪽 순서를 초급자용으로 한 장만 더 펼치면 아래처럼 보면 된다.

```text
브라우저
  -> 바깥 Filter
     - 공통 로깅, trace id, request wrapping
  -> Spring Security filter chain
     - SecurityContext 읽기: 세션/쿠키에서 "로그인한 사람인가?" 복원
     - 인증 실패 분기:
       보호 URL + 비로그인
       -> SavedRequest 저장 가능
       -> 302 /login 또는 401
     - 인가 실패 분기:
       로그인은 됨 + ADMIN 아님
       -> 403
  -> DispatcherServlet
  -> @RequestBody 변환
  -> HandlerInterceptor
  -> Controller
  -> 응답
```

핵심은 "`302 /login`과 `SavedRequest`는 대개 Security filter chain 안에서 만들어지고, `HandlerInterceptor`는 그 뒤에야 온다"는 점이다.

## 이 문서에서 멈추고 다음 문서로 넘길 신호

이 문서는 "`누가 먼저 막는가`"까지만 설명한다. 아래 질문이 앞에 나오면 여기서 더 파고들지 말고 관련 문서로 넘기는 편이 초급자에게 안전하다.

| 지금 막힌 질문 | 여기서 길게 다루지 않는 이유 | 바로 갈 문서 |
|---|---|---|
| `addFilterBefore`, `addFilterAfter`, `jwt filter 어디에 둬요` | filter ordering은 개념 구분보다 한 단계 더 깊은 설정 질문이다 | [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md) |
| `SavedRequest`가 왜 생기고 로그인 후 어디로 돌아가요 | redirect 기억 장치는 security chain 안에서도 별도 축이다 | [Spring Security `RequestCache` / `SavedRequest` Boundaries](./spring-security-requestcache-savedrequest-boundaries.md) |
| `POST /admin/reservations`가 왜 controller 전에 `400`이에요 | 인증 통과 뒤에는 JSON 바인딩 축으로 넘어간다 | [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md) |

짧게 외우면 이렇다.

- 이 문서: `Filter`, security chain, `HandlerInterceptor` 역할 구분
- 다음 문서: filter ordering, redirect 기억, JSON 바인딩 같은 세부 원인

## 관리자 API 실패 지점 빠른 분기

관리자 API를 볼 때 초급자가 가장 자주 섞는 장면은 "`POST /admin/reservations`가 왜 컨트롤러에 안 들어갔지?`"다. 이때는 보안과 바인딩을 한 흐름으로 붙여 보는 편이 안전하다.

```text
브라우저 -> Filter -> Spring Security filter chain
        -> DispatcherServlet -> @RequestBody 변환
        -> HandlerInterceptor -> Controller
```

| 멈춘 위치 | 흔한 증상 | 먼저 볼 질문 |
|---|---|---|
| Spring Security filter chain | `302 /login`, `401`, `403` | 로그인 자체가 안 됐나, `ADMIN` 권한이 없나 |
| `@RequestBody` 변환 | 컨트롤러 로그 없이 `400` 또는 `415` | JSON 문법, `Content-Type`, `LocalDate`/`LocalTime` 형식이 맞나 |
| `HandlerInterceptor` 이후 controller | 컨트롤러 로그는 찍히는데 서비스/검증에서 실패 | 이제는 바인딩보다 비즈니스 규칙인가 |

즉 "`컨트롤러 로그가 안 찍힌다`"만으로는 아직 원인을 못 정한다.  
관리자 인증에서 먼저 막히면 Security 쪽 문제고, 인증을 통과한 뒤 JSON을 DTO로 못 만들면 `@RequestBody` 문제다.

### `302`, `403`, `400`을 한 줄로 먼저 자르기

```text
비로그인으로 /admin 접근
-> Security filter chain
-> SavedRequest 저장 가능
-> 302 /login

로그인은 됐지만 ADMIN 아님
-> Security filter chain
-> 403

ADMIN 로그인도 됐고 권한도 맞음
-> DispatcherServlet -> @RequestBody 변환
-> JSON/타입이 틀리면 400 또는 415
```

이 세 줄만 먼저 외우면 "`왜 컨트롤러 전에 끝났지?`"를 훨씬 빨리 분기할 수 있다.

## 상세 분해

### 1. `Filter`는 가장 바깥 입구다

예를 들어 `/admin/reservations` 요청이 들어오면 `Filter`는 아직 어떤 컨트롤러가 선택될지 모르는 상태에서도 요청을 볼 수 있다.

- 모든 경로에 공통인 헤더 검사
- 요청/응답 로깅
- `ContentCachingRequestWrapper` 같은 wrapping

즉 `Filter`는 "웹 요청 전체"에 관심이 있다.

### 2. Spring Security filter chain은 보안 전용 filter 묶음이다

여기서 중요한 점은 "Spring Security도 결국 filter를 쓰지만, 아무 filter 하나와 같지는 않다"는 것이다.

- 인증 정보를 복원한다
- 로그인 안 된 요청이면 `401` 또는 로그인 redirect를 결정한다
- 로그인은 됐지만 관리자 권한이 없으면 `403`을 만든다
- 필요하면 원래 가려던 URL을 `SavedRequest`로 기억해 로그인 후 다시 보내 준다

예를 들어 일반 사용자 세션으로 `/admin/reservations`에 접근하면, 컨트롤러보다 먼저 Security가 막는다.

### 3. `HandlerInterceptor`는 컨트롤러 주변 보조 작업에 맞다

관리자 페이지에서 이런 식의 요구가 들어오면 인터셉터가 잘 맞는다.

- "관리자 화면 진입 시간을 남기자"
- "컨트롤러 실행 전 audit context를 심자"
- "응답 후 관리자 액션 로그를 적재하자"

반대로 "비로그인 사용자를 막자"를 인터셉터 중심으로 풀기 시작하면 Security와 책임이 겹치기 쉽다.

## 흔한 오해와 함정

- `Spring Security filter chain`도 filter이니, 그냥 커스텀 `Filter` 하나로 관리자 인증을 대체해도 된다고 생각하기 쉽다.
  인증 정보 저장, 예외 번역, 권한 검사까지 다시 맞춰야 해서 초급자에게는 오히려 위험하다.

- 인터셉터에서 `admin` 권한을 검사하면 더 간단하다고 느끼기 쉽다.
  하지만 이 경우 `401`/`403` 규칙, 로그인 redirect, `SecurityContext` 활용이 따로 놀 수 있다.

- `Filter`와 Security filter chain을 완전히 별개라고 생각하기 쉽다.
  실제로는 Security filter chain도 servlet `Filter` 위에서 동작하는 "보안 특화 체인"이다.

- `@RestControllerAdvice`가 있으니 인증 실패 JSON도 거기서 통일된다고 기대하기 쉽다.
  보안 실패는 대개 컨트롤러 전에 발생하므로 Security 쪽 예외 번역이 먼저다.

## 실무에서 쓰는 모습

RoomEscape 관리자 기능을 단순화하면 이런 흐름이다.

1. 브라우저가 `/admin/reservations`를 호출한다.
2. 바깥 `Filter`가 trace id를 심고 요청 로그를 남긴다.
3. Spring Security filter chain이 세션 쿠키를 읽어 로그인 사용자인지 확인한다.
4. 비로그인이면 여기서 `302 /login` 또는 `401`, 일반 사용자면 `403`으로 끝날 수 있다.
5. 권한이 있으면 `DispatcherServlet`이 관리자 컨트롤러와 `@RequestBody` 파라미터 준비를 시작한다.
6. `POST /admin/reservations`라면 JSON body를 DTO로 바꾸는 단계에서 `400`/`415`가 날 수 있다.
7. 바인딩까지 통과하면 `HandlerInterceptor`가 "관리자 기능 접근" 감사 로그용 메타데이터를 심는다.
8. 그다음에야 컨트롤러가 실제 예약 관리 로직을 수행한다.

짧은 설정 감각도 이 순서와 맞닿아 있다.

```java
http.authorizeHttpRequests(auth -> auth
    .requestMatchers("/admin/**").hasRole("ADMIN")
    .anyRequest().permitAll()
);
```

이 설정이 말하는 것은 "`/admin/**`를 막는 주체는 Security filter chain"이라는 점이다.

## 더 깊이 가려면

- 브라우저 쿠키와 서버 세션이 security chain으로 어떻게 이어지는지부터 보고 싶다면 [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)를 먼저 읽는다.
- `/admin/**`에서 `302 /login`과 `403`을 먼저 갈라야 한다면 [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)를 이어 본다.
- 인증은 통과했는데 `POST /admin/reservations`가 컨트롤러 전에 `400`이면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)로 바로 내려간다.
- `filter`와 `interceptor`의 일반 경계를 더 보고 싶다면 [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)로 간다.
- "그래서 Security filter chain 안에서 어느 필터가 먼저 도는가?"가 궁금하면 [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)로 내려간다.
- 쿠키 기반 관리자 로그인 흐름이 낯설면 [쿠키 속성 매트릭스: `SameSite`, `HttpOnly`, `Secure`, `Domain`, `Path`](../network/cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)로 같이 보면 좋다.

## 한 줄 정리

관리자 API 흐름을 처음 배울 때는 `Filter`를 "입구", Spring Security filter chain을 "인증/인가 본체", `@RequestBody` binding을 "컨트롤러 전 JSON 변환", `HandlerInterceptor`를 "컨트롤러 주변 보조 작업"으로 나누면 된다.

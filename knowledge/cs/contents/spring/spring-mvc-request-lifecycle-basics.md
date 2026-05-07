---
schema_version: 3
title: Spring MVC 요청 생명주기 기초
concept_id: spring/spring-mvc-request-lifecycle-basics
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 93
mission_ids:
- missions/baseball
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- spring-mvc-request-lifecycle
- dispatcher-servlet-binding-basics
- filter-interceptor-controller-advice
aliases:
- spring mvc request lifecycle basics
- dispatcher servlet request flow
- spring mvc 큰 그림
- filter interceptor controller advice
- argument binding message conversion
- conversionservice formatter webdatabinder
- 요청이 컨트롤러까지 어떻게 가요
- query param localdate 변환
symptoms:
- Spring MVC의 Filter, DispatcherServlet, HandlerMapping, binding, controller, advice 단계를 모두 자동 처리로만 보고 위치를 구분하지 못한다
- ConversionService, Formatter, WebDataBinder 이름을 먼저 외우다가 요청 값 채우기 단계라는 큰 그림을 놓친다
- 400, 415, 404, 405, 302, 403을 모두 controller 내부 오류처럼 디버깅한다
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- network/http-request-response-basics-url-dns-tcp-tls-keepalive
- spring/mvc-controller-basics
next_docs:
- spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge
- spring/requestbody-400-before-controller-primer
- spring/modelattribute-vs-requestbody-binding-primer
- spring/spring-validation-binding-error-pipeline
linked_paths:
- contents/spring/spring-mvc-controller-basics.md
- contents/spring/spring-requestbody-400-before-controller-primer.md
- contents/spring/spring-requestbody-415-unsupported-media-type-primer.md
- contents/spring/spring-modelattribute-vs-requestbody-binding-primer.md
- contents/spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md
- contents/spring/spring-validation-binding-error-pipeline.md
- contents/spring/spring-mvc-request-lifecycle.md
- contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md
confusable_with:
- spring/mvc-request-lifecycle
- spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge
- spring/requestbody-400-before-controller-primer
- spring/spring-controller-not-hit-decision-guide
- network/http-request-response-basics-url-dns-tcp-tls-keepalive
forbidden_neighbors: []
expected_queries:
- Spring MVC 요청은 Filter부터 ControllerAdvice까지 어떤 순서로 흘러가?
- DispatcherServlet은 요청 생명주기에서 무슨 역할을 해?
- query param을 LocalDate로 바꾸는 ConversionService와 WebDataBinder는 어디 단계야?
- RequestBody 400이나 415가 컨트롤러 전에 나는 이유를 요청 흐름으로 설명해줘
- Filter와 Interceptor와 ControllerAdvice를 요청 생명주기에서 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 Spring MVC beginner primer로, HTTP 요청이 Filter,
  DispatcherServlet, HandlerMapping, binding, controller, exception resolver,
  ControllerAdvice를 지나 응답이 되는 흐름을 한 장으로 설명한다.
---
# Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기

> 한 줄 요약: Spring MVC를 처음 배울 때는 "요청이 어디서 들어와서, 누가 컨트롤러를 찾고, 값은 누가 채우고, 실패는 누가 HTTP 응답으로 바꾸는가"를 한 장의 흐름으로 먼저 잡으면 된다.

**난이도: 🟢 Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "요청이 controller까지 오는 순서가 전부 자동처럼 보여요" | 방탈출/장바구니 API 요청 디버깅 | Filter, DispatcherServlet, HandlerMapping, binding, controller 자리를 분리한다 |
| "`@RequestBody` 400이나 415가 왜 controller 전에 나는지 모르겠어요" | JSON 요청 DTO 바인딩 실패 | 값 채우기와 message conversion 단계가 controller 호출 전임을 확인한다 |
| "Filter, Interceptor, ControllerAdvice가 모두 중간 처리처럼 보여요" | 인증/로그/예외 처리 위치를 처음 나누는 단계 | 입구 차단, controller 전후 작업, 실패 응답 번역을 다른 축으로 본다 |

관련 문서:

- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md)
- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)
- [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md)
- [Spring `@ModelAttribute` vs `@RequestBody` 초급 비교 카드: 폼/query 바인딩과 JSON body를 한 장으로 분리하기](./spring-modelattribute-vs-requestbody-binding-primer.md)
- [Spring `DispatcherServlet` / `HandlerInterceptor` 입문 브리지: 큰 그림부터 잡기](./spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md)
- [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
- [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring mvc request lifecycle basics, spring mvc 큰 그림, spring mvc 처음 배우는데, 요청이 컨트롤러까지 어떻게 가요, spring mvc 파라미터 누가 채워요, conversionservice 뭐예요 처음, formatter 뭐예요 spring 처음, webdatabinder 뭐예요 처음, conversionservice formatter webdatabinder 차이 뭐예요, spring binding이 뭐예요, query param localdate 변환 누가 해요, webdatabinder 언제 나와요, filter interceptor 차이 basics, requestbody 400 왜 나요, @valid 전에 400 왜

## 먼저 여기까지만 잡는다

이 문서는 Spring MVC beginner가 "입구 -> 길찾기 -> 값 채우기 -> 컨트롤러 -> 실패 번역" 순서를 한 장으로 잡는 primer다. 특히 "`ConversionService`가 뭐예요?", "`WebDataBinder`는 언제 나와요?", "`query parameter`는 누가 `LocalDate`로 바꿔줘요?" 같은 첫 질문이 deep dive보다 먼저 여기로 오게 하는 entrypoint 역할도 맡는다.

- 먼저 잡을 것: `Filter`, `DispatcherServlet`, binding, controller, advice의 자리
- 지금 중심이 아닌 것: async dispatch, streaming, content negotiation 심화

| 먼저 보인 단어 | 이 primer에서 내릴 1차 판단 | 바로 넘길 문서 |
|---|---|---|
| `415`, `Accept`, `produces`, `consumes` | media type 계약 질문이 먼저다 | [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md), [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md) |
| `302 /login`, `401`, `403` | 바인딩보다 입구 security/filter 질문일 수 있다 | [Spring Filter vs Spring Security Filter Chain vs HandlerInterceptor: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md), [Security README](../security/README.md#browser--session-beginner-ladder) |
| `ConversionService`, `Formatter`, `WebDataBinder`, `query param -> LocalDate` | 내부 클래스 이름보다 "값 채우기" 큰 그림을 먼저 잡는다 | 아래 표를 보고, 다음 단계로 [Spring ConversionService, Formatter, and Binder Pipeline](./spring-conversion-service-formatter-binder-pipeline.md) |

## 핵심 개념

처음에는 Spring MVC를 "한 번의 요청이 지나가는 공항 동선"처럼 보면 된다.

- 입국장 입구에서는 `Filter`가 먼저 본다.
- 안내 데스크처럼 `DispatcherServlet`이 어느 컨트롤러로 보낼지 정한다.
- 탑승권 정보 맞추듯 `@PathVariable`, `@RequestParam`, `@RequestBody` 값을 Spring이 채운다.
- 실행 중 실패가 나면 `@ExceptionHandler`나 `@RestControllerAdvice`가 HTTP 응답으로 번역한다.

입문자가 자주 헷갈리는 이유는 이 단계들이 모두 "중간에서 뭔가 자동으로 해 준다"로 보이기 때문이다. 그래서 처음에는 구현체 이름보다 "입구 -> 길찾기 -> 값 채우기 -> 실행 -> 실패 번역" 순서만 고정하면 된다.

## 한눈에 보기

```text
HTTP 요청
  -> Filter
  -> DispatcherServlet
  -> HandlerMapping
  -> HandlerInterceptor preHandle
  -> argument binding / message conversion
  -> Controller 메서드 호출
  -> return value handling / HttpMessageConverter
  -> 예외면 ExceptionResolver -> @ExceptionHandler or @RestControllerAdvice
  -> HandlerInterceptor afterCompletion
  -> HTTP 응답
```

| 단계 | 지금 단계에서 이렇게 기억하면 된다 | 초급자가 자주 묻는 말 |
|---|---|---|
| `Filter` | Spring MVC 앞단에서 요청 자체를 본다 | "로그인 안 된 요청을 입구에서 막는 곳?" |
| `DispatcherServlet` | MVC의 관문이다 | "`DispatcherServlet`이 뭐예요?" |
| `HandlerMapping` | 어떤 컨트롤러 메서드로 갈지 찾는다 | "URL은 누가 매칭해요?" |
| 바인딩 | 문자열/JSON을 메서드 파라미터로 바꾼다 | "`@RequestBody` 400은 왜 나요?" |
| 컨트롤러 | 서비스 호출과 응답 반환에 집중한다 | "비즈니스 로직은 어디에 둬요?" |
| 예외 처리 | 실패를 HTTP 상태코드와 에러 바디로 바꾼다 | "`@ControllerAdvice`는 언제 써요?" |

## `ConversionService` / `Formatter` / `WebDataBinder`는 어디에 있나

`ConversionService`, `Formatter`, `WebDataBinder`라는 이름이 먼저 보이면 초급자는 deep dive 문서로 바로 내려가기보다 이 문서의 "값 채우기" 칸에 먼저 꽂아 두는 편이 안전하다.

| 용어 | beginner용 한 줄 역할 | 먼저 머리에 둘 자리 | 다음 문서 |
|---|---|---|---|
| `ConversionService` | 문자열을 `Long`, `Enum`, `LocalDate` 같은 타입으로 바꾸는 공용 변환기 | "값 채우기" 단계의 타입 변환 | [Spring ConversionService, Formatter, and Binder Pipeline](./spring-conversion-service-formatter-binder-pipeline.md) |
| `Formatter` | 사람 친화적 문자열 표기와 객체 표현을 연결하는 규칙 | "값 채우기" 단계의 문자열 표현 규칙 | [Spring ConversionService, Formatter, and Binder Pipeline](./spring-conversion-service-formatter-binder-pipeline.md) |
| `WebDataBinder` | query/form/path 값을 객체 필드에 묶는 웹 바인딩 도구 | 컨트롤러 호출 직전의 바인딩 조립 | [Spring ConversionService, Formatter, and Binder Pipeline](./spring-conversion-service-formatter-binder-pipeline.md) |

짧게 외우면 `ConversionService`는 "타입 바꾸기", `Formatter`는 "문자열 표현 규칙", `WebDataBinder`는 "웹 요청 값을 객체에 묶기"다.
처음 질문이 "`ConversionService`가 뭐예요?", "`WebDataBinder`가 왜 나와요?"라면 이 표까지만 잡고, 실제 `400` 증상은 아래 `@RequestBody` / `@ModelAttribute` 분기로 다시 내려가면 된다.

## 상세 분해

처음에는 `POST /admin/reservations` 한 요청만 붙잡아도 충분하다. 아래 여섯 칸으로 끊으면 "`지금 어디서 막혔는지`"가 빨리 보인다.

| 순서 | 누가 맡는가 | 여기서 하는 일 | 여기서 자주 막히는 증상 |
|---|---|---|---|
| 1 | `Filter` | 요청을 입구에서 먼저 검사한다 | 로그인 전 차단, CORS, 공통 로깅 |
| 2 | `DispatcherServlet` + `HandlerMapping` | 어느 컨트롤러 메서드로 갈지 찾는다 | `404`, `405` |
| 3 | `HandlerInterceptor` | 컨트롤러 전후 공통 작업을 붙인다 | 접근 로그, 처리 시간 측정 |
| 4 | argument binding / message conversion | `@PathVariable`, `@RequestParam`, `@RequestBody`를 채운다 | `415`=`Content-Type` 계약, `400`=`parse/type`, 객체가 만들어진 뒤 `@Valid`면 validation `400` |
| 5 | `Controller` | 서비스 호출과 응답 반환을 한다 | 도메인 규칙 위반, 조회 실패 |
| 6 | exception resolver / advice | 예외를 HTTP 응답으로 번역한다 | `400`/`404`/`409` 응답 모양 불일치 |

짧게 외우면 이렇다.

- 입구에서 막는 건 `Filter`
- 길을 정하는 건 `DispatcherServlet`
- 값을 채우는 건 binding
- 정책 응답으로 바꾸는 건 advice

## Filter, Interceptor, Controller는 어느 순서로 만나는가?

세 칸을 먼저 분리하면 lifecycle이 훨씬 덜 무겁다.

| 위치 | 담당 | 대표 질문 | RoomEscape 예시 |
|---|---|---|---|
| `Filter` | 요청 입구 공통 처리 | "아예 안으로 들여보낼까?" | 인증 쿠키 없음, 공통 로깅, CORS |
| `HandlerInterceptor` | 컨트롤러 전후 공통 처리 | "컨트롤러 주변에서 체크할까?" | 관리자 URL 접근 로그, 처리 시간 측정 |
| `Controller` | 요청을 서비스 호출로 연결 | "어떤 입력으로 어떤 작업을 시킬까?" | `AdminReservationController#create` |

많이 헷갈리는 지점은 "`Interceptor`도 요청 전에 실행되니 `Filter`와 같은 것 아닌가?"다. 초급자 기준 답은 간단하다.

- `Filter`는 Spring MVC 바깥 입구다.
- `HandlerInterceptor`는 이미 "어느 컨트롤러로 갈지" 감이 잡힌 뒤에 붙는다.
- `Controller`는 공통 처리 도구가 아니라 실제 업무 메서드다.

## `Filter` / `Interceptor` / `Controller` / `ControllerAdvice` 빠른 비교

beginner가 특히 많이 헷갈리는 지점은 "`요청 앞에서 무언가 한다`"는 말이 네 칸에 모두 보인다는 점이다. 처음에는 "`언제 끼어드는가`"와 "`실패를 막는가, 번역하는가`"만 나눠도 충분하다.

| 자리 | 언제 보나 | 주로 하는 일 | `POST /admin/reservations` 예시 |
|---|---|---|---|
| `Filter` | Spring MVC에 들어오기 전 | 요청 입구에서 공통 검사/차단 | 인증 쿠키가 없으면 컨트롤러 전에 막는다 |
| `HandlerInterceptor` | 컨트롤러를 찾은 뒤 전후 | 컨트롤러 주변 공통 처리 | 관리자 요청 시작/종료 로그를 남긴다 |
| `Controller` | 바인딩이 끝난 뒤 | 서비스 호출과 응답 반환 | `ReservationService.create(...)`를 호출한다 |
| `@RestControllerAdvice` | 예외가 밖으로 나올 때 | 실패를 HTTP 응답으로 번역 | `ReservationNotFoundException`을 `404` 바디로 바꾼다 |

짧게 외우면 `Filter`는 입구, `Interceptor`는 컨트롤러 주변, `Controller`는 업무 연결, `Advice`는 실패 번역이다.

## 컨트롤러 전에 끝나는 실패를 먼저 분리한다

입문자가 많이 꼬이는 이유는 `400`, `401/403`, `404`가 전부 "컨트롤러가 틀렸다"로 보이기 때문이다. 하지만 아래 셋은 **컨트롤러 본문에 들어가기 전** 끝날 수 있다.

| 먼저 보인 결과 | 보통 어디서 멈췄나 | 첫 질문 |
|---|---|---|
| `401`/`403` 또는 로그인 redirect | `Filter` / security filter chain | 입구에서 이미 막힌 것 아닌가 |
| `404`/`405` | `HandlerMapping` | URL과 HTTP 메서드가 맞나 |
| `400`/`415` | binding / message conversion | JSON, `Content-Type`, DTO 타입이 맞나 |

이 표는 "컨트롤러 로직 디버깅"으로 바로 들어가기 전에 쓰는 정지선이다. 컨트롤러 로그가 안 찍혔다면 controller/service보다 이 표를 먼저 다시 보면 된다.

### 자주 섞는 오해

- "`ControllerAdvice`가 요청을 먼저 가로채나요?"
  아니다. 보통은 컨트롤러나 그 아래에서 예외가 나온 뒤 응답을 정리하는 쪽이다.
- "`Interceptor`가 예외 응답 모양도 정하나요?"
  보통 아니다. 공통 전후 처리와 관찰에 가깝고, 에러 바디 번역은 `Advice` 축이 더 가깝다.
- "`Filter`에서 막히면 컨트롤러 로그가 찍혀야 하나요?"
  아니다. 입구에서 끊겼다면 컨트롤러까지 가지 않을 수 있다.

## `Filter`는 Spring MVC 바깥 입구다

`Filter`는 서블릿 컨테이너 레벨에서 요청을 먼저 본다. 그래서 인증 전처리, 공통 헤더, 요청 래핑처럼 "컨트롤러에 가기 전"에 해야 하는 일에 어울린다.

입문 기준으로는 이렇게 구분하면 충분하다.

- 요청 자체를 초입에서 막아야 하면 `Filter`
- 컨트롤러 주변에서 공통 작업을 붙이면 `HandlerInterceptor`

## `DispatcherServlet`은 길찾기 관문이다

`DispatcherServlet`은 직접 비즈니스 로직을 처리하지 않는다. 대신 "이번 요청을 누가 처리할까?"를 조율한다.

- `GET /admin/reservations` 요청이 들어온다.
- `HandlerMapping`이 맞는 컨트롤러 메서드를 찾는다.
- 필요하면 argument resolver, message converter, exception resolver 같은 도구를 붙여 handler를 Spring MVC 방식으로 실행한다.

즉 `DispatcherServlet`은 controller를 새로 만드는 존재가 아니라, 이미 준비된 Bean 중에서 맞는 handler를 찾아 연결하는 관문이다. 초급자가 헷갈리는 역할도 아래처럼 끊어 두면 덜 섞인다.

| 질문 | `DispatcherServlet`이 하는 일 | 하지 않는 일 |
|---|---|---|
| "URL은 누가 찾나요?" | 맞는 handler를 찾는 흐름을 조율한다 | 비즈니스 규칙을 직접 판단하지 않는다 |
| "파라미터 값은 누가 채우나요?" | 바인딩 도구들이 동작하도록 연결한다 | DTO 필드를 직접 수동 세팅하지 않는다 |
| "예외는 누가 응답으로 바꾸나요?" | resolver chain을 태워 응답 번역을 시도한다 | 팀의 도메인 정책을 스스로 결정하지 않는다 |

## 바인딩은 "값 채우기" 단계다

컨트롤러 파라미터는 그냥 비어 있는 상태로 들어오지 않는다. Spring이 요청에서 값을 꺼내 타입에 맞게 채운다.

| 파라미터 | 어디서 값이 오는가 | 흔한 실패 |
|---|---|---|
| `@PathVariable Long id` | URL 경로 `/rooms/1` | `abc`처럼 숫자로 못 바꾸는 값 |
| `@RequestParam String date` | 쿼리스트링 `?date=2026-04-28` | 이름 오타, 필수값 누락 |
| `@RequestBody ReservationRequest` | JSON body | [`415 Unsupported Media Type` first split](./spring-requestbody-415-unsupported-media-type-primer.md) 또는 [`400` before controller](./spring-requestbody-400-before-controller-primer.md) |

이 단계 실패는 아직 비즈니스 규칙 위반이 아닐 수 있다. 문자열을 숫자로 못 바꾸거나 JSON 모양이 DTO와 안 맞는 식의 **binding failure**일 수 있다.

README에서 내려왔다면 binding 칸은 이렇게 먼저 끊으면 된다: `415`는 `Content-Type` 계약, 컨트롤러 전 `400`은 JSON parse/type, 객체가 들어온 뒤 `@Valid` `400`은 validation.

`415`는 JSON 값 오류보다 `Content-Type` 계약 문제에 더 가깝다. 먼저 [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md)로 가고, `Accept`/`produces`/`consumes`까지 넓힐 때만 [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)로 내려가면 된다.

query/form은 `@ModelAttribute`, JSON body는 `@RequestBody`로 먼저만 나눠도 덜 헷갈린다. 표 비교가 필요하면 [Spring `@ModelAttribute` vs `@RequestBody` 초급 비교 카드](./spring-modelattribute-vs-requestbody-binding-primer.md)를 보면 된다.

짧게 끊어 기억하면 된다.

- `400`이 바로 났다고 해서 컨트롤러 로직이 실행된 것은 아닐 수 있다.
- `@RequestBody` 문제는 서비스 로직보다 JSON 모양, `Content-Type`, DTO 필드 타입을 먼저 본다.
- `@PathVariable Long id`에 `abc`가 들어오면 예약 조회 실패보다 숫자 변환 실패가 먼저 난다.

## 컨트롤러는 요청을 서비스 호출로 연결한다

초급자 기준 컨트롤러 역할은 단순하다.

- 요청에서 값을 받는다.
- 서비스를 호출한다.
- 결과를 응답으로 돌려준다.

예를 들어 RoomEscape 관리자 API라면 `POST /admin/reservations` 요청을 받아 `ReservationCreateRequest`로 바인딩하고, 컨트롤러는 그 객체를 서비스로 넘긴다. 검증, 저장, 도메인 규칙은 보통 서비스와 그 아래 계층이 맡는다.

## 예외 처리는 실패를 HTTP 응답으로 번역한다

컨트롤러에서 예외가 나면 그대로 브라우저에 Java 예외가 보이는 것이 아니다. Spring MVC가 예외를 잡아 HTTP 응답으로 바꾼다.

입문 기준으로는 이 두 가지만 먼저 구분하면 된다.

- binding/validation 실패: 대개 `400 Bad Request`
- 비즈니스 예외: 정책에 따라 `404`, `409`, `500` 등으로 번역

이 번역 정책을 공통화하는 대표 도구가 `@RestControllerAdvice`다.

여기서 중요한 감각은 "예외가 났다"와 "예외 응답이 나갔다"가 같은 문장이 아니라는 점이다.

- 예외는 controller/service 쪽에서 발생할 수 있다.
- 응답 상태코드와 에러 바디 모양은 exception resolver와 advice가 정리한다.
- 그래서 같은 `IllegalArgumentException`이어도 팀 정책에 따라 `400`으로 번역할 수도 있고, 별도 도메인 예외로 나눌 수도 있다.

초급자 첫 판단표도 같이 들고 가면 좋다.

| 실패 위치 | 처음 떠올릴 의미 | 흔한 상태 코드 |
|---|---|---|
| binding / validation | 요청 형식이나 입력값이 잘못됐다 | `400` |
| controller/service 조회 | 찾는 대상이 없다 | `404` |
| controller/service 비즈니스 규칙 | 현재 상태와 충돌한다 | `409` |
| 예상 밖 예외 | 아직 정책화되지 않았거나 서버 내부 문제다 | `500` |

## `@RequestBody` 400이 나면 어디서 실패한 건가?

입문자가 가장 자주 맞닥뜨리는 증상 중 하나라서 별도로 기억할 가치가 있다.

| 보이는 현상 | 먼저 볼 곳 | 흔한 원인 |
|---|---|---|
| 요청 보내자마자 `400 Bad Request` | binding / message conversion | JSON 필드명 불일치, 숫자/날짜 타입 변환 실패 |
| 요청 보내자마자 `415 Unsupported Media Type` | `@RequestBody`의 media type 계약 | `Content-Type: application/json` 누락, `consumes`와 불일치 |
| 필수값 누락 메시지 | validation | `@NotNull`, `@NotBlank` 같은 제약 위반 |
| 컨트롤러 로그가 안 찍힘 | binding 또는 filter 앞단 | 컨트롤러 전에 이미 실패했을 수 있음 |
| 응답 에러 모양이 프로젝트 표준과 다름 | `@RestControllerAdvice` | 예외 번역 정책이 빠졌거나 범위가 다를 수 있음 |

짧게 말하면:

- 요청 body를 객체로 못 바꾸면 binding 실패다.
- 객체로는 바꿨지만 규칙을 어기면 validation 실패다.
- 둘 다 최종적으로는 `400`처럼 비슷하게 보일 수 있어서, 초반에는 "컨트롤러에 들어오기 전 실패인지"를 먼저 따져야 한다.

`@RequestBody`가 왜 컨트롤러 전에 `400`으로 끝나는지 JSON 문법, DTO 타입, `Content-Type` 예시로 따로 보고 싶다면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)를 바로 이어서 보면 된다. 반대로 `415 Unsupported Media Type`이 먼저 보이면 [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md)에서 `Content-Type`과 `consumes`만 먼저 가르고, `Accept`까지 넓힐 때만 [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)로 내려가면 초급자 동선이 덜 무거워진다.

## 흔한 오해와 함정

- "`Filter`와 `Interceptor`는 같은 자리다"
  아니다. `Filter`가 더 앞단이고, `Interceptor`는 컨트롤러 실행 전후에 붙는다.

- "`@RequestBody` 400이면 컨트롤러 로직이 틀렸다"
  꼭 그렇지 않다. JSON 형식, `Content-Type`, DTO 구조가 안 맞아 바인딩 단계에서 먼저 실패했을 수 있다.

- "`@RestControllerAdvice`가 요청을 막는다"
  아니다. 이쪽 책임은 "실패를 어떤 HTTP 응답으로 보낼지"를 정하는 것이다.

- "`DispatcherServlet`이 서비스나 레포지토리를 만든다"
  아니다. 객체 생성과 주입은 Bean 컨테이너가 담당하고, `DispatcherServlet`은 요청 라우팅을 담당한다.

- "`HandlerInterceptor`의 `afterCompletion`이 항상 성공 흐름만 본다"
  아니다. 예외가 나도 정리 단계에서 호출될 수 있다. 그래서 로깅/정리에는 어울리지만, 예외를 응답으로 번역하는 주된 자리는 아니다.

## 실무에서 쓰는 모습

RoomEscape 스타일의 관리자 요청을 아주 단순화하면 이런 그림이다.

1. 클라이언트가 `POST /admin/reservations`와 JSON body를 보낸다.
2. 인증/로깅용 `Filter`가 먼저 요청을 통과시킨다.
3. `DispatcherServlet`이 `AdminReservationController#create` 같은 handler를 찾는다.
4. Spring이 JSON body를 `ReservationCreateRequest`로 바인딩한다.
5. 컨트롤러가 서비스를 호출한다.
6. 예약 시간 형식이 틀리면 binding/validation 예외가 난다.
7. `@RestControllerAdvice`가 `400` 에러 응답으로 바꾼다.
8. 성공이면 반환 객체를 JSON으로 직렬화해 응답한다.

이 흐름을 머리에 넣어 두면 "지금 내가 봐야 할 문제가 입구인가, 컨트롤러 매핑인가, 바인딩인가, 예외 번역인가"를 더 빨리 가를 수 있다.

반대로 같은 요청이 다른 결과로 끝나는 모습도 같이 보면 더 잘 남는다.

| 같은 `POST /admin/reservations`라도 | 어디서 끝나는가 | 초급자 첫 해석 |
|---|---|---|
| 인증 쿠키가 없다 | `Filter` 또는 security filter chain | 컨트롤러 전에 막혔다 |
| URL은 맞지만 `GET`으로 보냈다 | `HandlerMapping` 단계 | 매핑 규칙이 안 맞았다 |
| JSON 시간 형식이 깨졌다 | binding / message conversion | DTO로 못 바꿨다 |
| 예약 슬롯이 이미 찼다 | controller/service | 도메인 충돌이라 `409` 후보다 |

## 자주 보는 증상별 첫 분기

| 보이는 증상 | 첫 의심 지점 | 왜 그쪽을 먼저 보나 |
|---|---|---|
| `404 Not Found` | `HandlerMapping` | 맞는 URL/HTTP 메서드 매핑을 못 찾았을 수 있다 |
| `405 Method Not Allowed` | 매핑된 HTTP 메서드 | 경로는 맞지만 `GET`/`POST`가 다를 수 있다 |
| `@RequestBody` 요청에서 바로 `400` | binding / message conversion | JSON 형식이나 DTO 구조가 먼저 안 맞을 수 있다 |
| 로그인 전인데 컨트롤러까지 안 온다 | `Filter` 또는 Security filter chain | MVC보다 앞단에서 막혔을 수 있다 |
| 예외가 났는데 응답 모양이 제각각이다 | `@RestControllerAdvice` / exception resolver | 실패 번역 정책이 통일되지 않았을 수 있다 |

## RoomEscape 관리자 API로 한 번 더 묶기

RoomEscape 미션 기준으로는 아래처럼 생각하면 된다.

1. 관리자 요청 `POST /admin/reservations`가 들어온다.
2. 인증이나 공통 헤더 처리는 `Filter`에서 먼저 지나간다.
3. `DispatcherServlet`이 관리자 예약 생성 컨트롤러를 찾는다.
4. 요청 JSON을 `ReservationCreateRequest`로 바인딩한다.
5. 형식이 맞으면 컨트롤러가 서비스를 호출한다.
6. 예약 시간 형식이나 필수값이 틀리면 binding/validation에서 `400` 후보가 된다.
7. 이미 존재하는 예약 시간 같은 업무 예외면 서비스에서 예외를 던지고, advice가 `409` 같은 응답으로 번역할 수 있다.

이 한 장면만 떠올라도 초급자가 자주 섞는 네 가지를 분리할 수 있다.

- URL을 누가 찾는가: `DispatcherServlet`과 `HandlerMapping`
- 값을 누가 채우는가: binding / message conversion
- 업무를 누가 실행하는가: controller -> service
- 실패를 누가 HTTP 응답으로 바꾸는가: exception resolver / `@RestControllerAdvice`

## 더 깊이 가려면

- 전체 전략 객체와 resolver 체인까지 보고 싶다면 [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)로 내려간다.
- `Filter`, `HandlerInterceptor`, `@ControllerAdvice` 경계를 더 또렷하게 비교하려면 [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)를 본다.
- `@RequestBody` 400, `BindingResult`, validation 순서를 더 자세히 보려면 [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)로 이어간다.
- HTTP 요청이 서버까지 오는 더 바깥 그림이 필요하면 [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)으로 내려간다.

## 면접/시니어 질문 미리보기

> Q: `DispatcherServlet`의 역할은 무엇인가?
> 의도: Spring MVC 전체 요청 조율 이해 확인
> 핵심: 요청을 받아 handler 탐색, 실행, 예외/응답 처리까지 조율하는 관문이다.

> Q: `Filter`와 `HandlerInterceptor`는 어디가 다른가?
> 의도: 서블릿 경계와 MVC 경계 구분 확인
> 핵심: `Filter`는 서블릿 입구, `HandlerInterceptor`는 컨트롤러 전후다.

> Q: `@RequestBody`에서 `400`이 나는 대표 이유는 무엇인가?
> 의도: binding failure와 비즈니스 실패 구분 확인
> 핵심: JSON 형식, `Content-Type`, DTO 구조, 타입 변환 문제가 먼저 원인일 수 있다.

## 한 줄 정리

Spring MVC 요청 생명주기 기초는 "`Filter`가 입구를 보고, `DispatcherServlet`이 길을 정하고, Spring이 값을 바인딩해 컨트롤러를 실행하고, 예외 처리기가 실패를 HTTP 응답으로 바꾼다"는 한 문장으로 먼저 잡으면 된다.

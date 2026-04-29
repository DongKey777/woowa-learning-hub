# Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기

> 한 줄 요약: Spring 입문에서는 "요청은 `DispatcherServlet`이 길을 찾고, 일은 controller -> service -> repository로 흐르며, 그 객체들은 Bean 컨테이너가 미리 만들어 연결해 둔다"는 한 장의 그림만 먼저 잡으면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md)
- [Spring `404`/`405` vs Bean Wiring Error Confusion Card: 요청 매핑 실패와 DI 예외를 먼저 분리하기](./spring-404-405-vs-bean-wiring-confusion-card.md)
- [Spring `@Value` vs `@ConfigurationProperties` Env Guide](./spring-value-vs-configurationproperties-env-guide.md)
- [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [Database First-Step Bridge](../database/database-first-step-bridge.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring request pipeline beginner, dispatcherservlet basics, bean container basics, spring di basics, controller service repository basics, spring 요청 흐름 뭐예요, bean di 뭐예요, 처음 spring 구조 헷갈려요, 왜 404 bean missing 같이 보여요, controller 다음 save 어디서 봐요, spring basics what is, request pipeline what is

## 핵심 개념

이 문서의 목표는 초반 혼동을 두 줄로 자르는 것이다.

- 요청 처리 흐름: 들어온 HTTP 요청을 어디 컨트롤러로 보낼지 정한다.
- 객체 준비 흐름: controller, service, repository를 앱 시작 시점에 미리 만들고 연결한다.

초보자가 자주 헷갈리는 이유는 이 둘이 한 장면에 같이 보이기 때문이다. 하지만 보통은 순서가 다르다.

1. 애플리케이션 시작 시 Bean 컨테이너가 객체를 등록하고 주입한다.
2. 요청이 들어오면 `DispatcherServlet`이 이미 준비된 controller Bean으로 연결한다.
3. service 경계에서 필요하면 `@Transactional`이 DB 작업을 한 묶음으로 감싼다.

짧게 외우면 `컨테이너가 먼저 조립하고, MVC가 나중에 그 조립품을 사용한다`다.

## 한눈에 보기

| 지금 보이는 질문 | 먼저 봐야 할 축 | 한 줄 답 |
|---|---|---|
| "`/orders`가 왜 이 컨트롤러로 안 가요?" | MVC 길찾기 | URL과 HTTP 메서드 매핑 문제일 가능성이 크다 |
| "`OrderService`는 누가 넣어요?" | Bean 등록과 DI | 요청 때 만드는 게 아니라 시작할 때 주입해 둔다 |
| "`@Transactional`이 왜 안 먹어요?" | 트랜잭션 경계 | service 진입점과 프록시 호출 경계를 먼저 본다 |
| "`404`, `400`, bean missing이 같이 보여요" | 증상 분리 | 한 요청을 길찾기, 값 바인딩, 객체 조립으로 다시 나눈다 |

`404`는 보통 길찾기 문제이고, `bean missing`은 객체 조립 문제다. 같은 요청에서 보였다고 같은 원인이라고 보면 안 된다.

## 먼저 머리에 넣을 4문장

이 문서는 용어 설명을 늘리기보다 같은 주문 요청을 네 문장으로 다시 자르는 데 목적이 있다.

- 요청 입구는 MVC가 맡는다.
- `controller`와 `service` 연결은 Bean 컨테이너가 미리 끝낸다.
- DB 작업 묶음은 보통 service의 `@Transactional` 경계에서 정한다.
- `302`/`cookie`가 먼저면 network/security 쪽으로, `save()` 다음 SQL이 궁금하면 database 쪽으로 넘긴다.

| 지금 막힌 질문 | 이 문서에서 먼저 남길 한 줄 | 다음 한 걸음 |
|---|---|---|
| "`왜 404와 bean missing이 같이 보여요?`" | 길찾기와 객체 조립은 다른 타임라인이다 | MVC 또는 Bean/DI primer로 다시 나눈다 |
| "`controller` 다음 `save()`는 어디서 봐요?`" | Spring 안에서 repository 직전까지만 보고 멈춘다 | [Database First-Step Bridge](../database/database-first-step-bridge.md) |
| "`302 /login`이 먼저 떠요`", "`cookie`가 더 헷갈려요" | Spring 내부보다 요청 입구 바깥 축이 먼저일 수 있다 | [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md) |

## 자주 헷갈리는 첫 갈림길

처음에는 같은 주문 요청에서 `404`, `400`, `bean missing`, "`@Transactional`이 안 먹어요"가 한 화면에 같이 보여서 전부 Spring 한 문제처럼 느껴진다. 이럴 때는 증상을 먼저 아래처럼 쪼개면 된다.

| 먼저 튀어나온 증상 문장 | 1차로 자를 축 | 바로 갈 문서 |
|---|---|---|
| "`404`예요", "`왜 저 컨트롤러가 안 받아요?`" | MVC 길찾기 | [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md) |
| "`400`이 컨트롤러 전에 나요", "`JSON`이 안 들어가요" | 바인딩 / message conversion | [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md) |
| "`bean missing`이에요", "`service`를 못 찾는대요" | Bean 등록 / DI | [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md) |
| "`@Transactional`이 안 먹어요", "`commit`이 왜 안 묶여요?`" | service 경계 / 프록시 | [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md) |

짧게 외우면 `404`는 길찾기, `400`은 값 채우기, `bean missing`은 객체 조립, `@Transactional`은 작업 묶기다.

브라우저 `cookie`, `302`, `304`가 먼저 보이면 Spring 내부보다 [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)이나 network primer로 잠깐 되돌아가는 편이 빠르다. 반대로 controller 다음 `save()`와 SQL이 궁금하면 이 문서에서 멈추지 말고 [Database First-Step Bridge](../database/database-first-step-bridge.md)로 한 칸만 넘긴다.

## 한 요청, 두 타임라인으로 보면 덜 헷갈린다

초급자가 가장 자주 놓치는 부분은 "`요청이 들어오는 순서`"와 "`객체가 준비되는 순서`"를 같은 타임라인으로 읽는 점이다. 처음에는 아래 두 줄만 분리해도 mental model이 훨씬 또렷해진다.

| 타임라인 | 언제 일어나는가 | 지금 떠올릴 질문 |
|---|---|---|
| Bean 준비 타임라인 | 애플리케이션 시작 시점 | `controller`, `service`, `repository`를 누가 등록하고 연결했나 |
| 요청 처리 타임라인 | HTTP 요청이 들어온 뒤 | 어느 controller가 받고, 어떤 값이 채워지고, 어디서 예외가 응답으로 바뀌나 |

```text
앱 시작:
  component scan / @Bean 등록 -> DI 연결 -> 필요하면 프록시 준비

요청 도착:
  Filter -> DispatcherServlet -> Controller -> Service(@Transactional 경계) -> Repository
```

`bean missing`은 보통 위쪽 타임라인 문제이고, `404`/`400`은 아래쪽 타임라인 문제다. 같은 주문 요청 화면에 둘 다 보였더라도 "언제 준비된 문제인가"를 먼저 묻는 편이 빠르다.

## `POST /orders` 예시로 읽기

같은 주문 요청도 네 칸으로 보면 덜 헷갈린다.

| 장면 | 실제로 묻는 질문 | 먼저 떠올릴 것 |
|---|---|---|
| `POST /orders`가 컨트롤러에 안 들어간다 | 어느 메서드로 라우팅되는가 | `DispatcherServlet`과 `@PostMapping` |
| `OrderController` 안 `OrderService`가 이미 있다 | 누가 객체를 만들어 넣었는가 | Bean 컨테이너와 생성자 주입 |
| `orderRepository.save(...)`와 `paymentRepository.save(...)`가 같이 묶인다 | 어디까지 한 작업 단위인가 | service 경계와 `@Transactional` |
| controller 다음 SQL이 궁금하다 | DB 접근 기술이 어디서 시작되나 | repository 이후를 database bridge로 이어 보기 |

초급자 mental model은 "요청은 MVC가 받고, 객체는 DI가 준비하고, 저장 묶음은 service 트랜잭션이 정한다" 정도면 충분하다.

## 흔한 오해와 바로잡기

- `DispatcherServlet`이 controller를 새로 만드는 것은 아니다.
  이미 등록된 Bean 중에서 어떤 핸들러를 쓸지 고른다.
- `bean missing`은 HTTP 요청 실수와 같은 종류가 아니다.
  대개 component scan, `@Bean` 등록, 주입 후보 문제다.
- `@Transactional`은 요청 전체에 자동으로 붙는 마법이 아니다.
  보통 service 메서드를 프록시가 감싸서 적용한다.
- `application.yml`은 요청마다 다시 읽는 파일이 아니다.
  대개 시작 시점에 읽혀 Bean에 바인딩된다.

처음에는 모든 예외를 한 번에 풀려 하지 말고, `길찾기 문제인가`, `객체 조립 문제인가`, `트랜잭션 경계 문제인가`부터 나누는 편이 빠르다.

## 안전한 다음 단계

| 지금 막힌 지점 | 다음 문서 | 왜 이 순서가 안전한가 |
|---|---|---|
| 브라우저 요청이 controller까지 어떻게 오나 | [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md) | 요청 진입 흐름만 먼저 분리해서 본다 |
| `service`/`repository`를 누가 연결했나 | [Spring Bean과 DI 기초](./spring-bean-di-basics.md) | 등록 -> 주입 순서를 따로 복구한다 |
| rollback, proxy, self-invocation이 헷갈린다 | [@Transactional 기초](./spring-transactional-basics.md) | DB 작업 묶음의 경계만 따로 본다 |
| 설정값 주입이 왜 기대와 다르지 | [Spring `@Value` vs `@ConfigurationProperties` Env Guide](./spring-value-vs-configurationproperties-env-guide.md) | 요청 흐름과 설정 바인딩 문제를 분리한다 |
| controller 다음 `save()`와 SQL이 어디서 보이나 | [Database First-Step Bridge](../database/database-first-step-bridge.md) | spring 이후 DB 학습 루트로 안전하게 넘긴다 |

이 문서는 `spring 요청 흐름 뭐예요`, `bean di 뭐예요`, `왜 404 bean missing 같이 보여요`, `controller 다음 save 어디서 봐요` 같은 beginner 검색을 먼저 받는 엔트리다.

## 한 줄 정리

Spring 입문에서는 `DispatcherServlet`이 요청 길을 찾고, Bean 컨테이너가 미리 만든 controller/service/repository를 연결하며, service 경계의 `@Transactional`이 DB 작업 묶음을 정한다고 기억하면 첫 그림이 잡힌다.

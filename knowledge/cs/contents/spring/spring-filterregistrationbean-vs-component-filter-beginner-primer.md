# Spring `FilterRegistrationBean` vs `@Component` 필터 입문: "bean 등록"과 "서블릿 필터 등록"을 언제 나눌까

> 한 줄 요약: 초급자 기준으로는 "필터 객체를 Spring이 관리하게 하자"면 `@Component`/`@Bean`부터, "그 필터를 어느 경로와 순서로 실행할지까지 정하자"면 `FilterRegistrationBean`까지 같이 본다고 이해하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `OncePerRequestFilter` vs 일반 `Filter` 입문: 언제 상속부터 시작할까](./spring-onceperrequestfilter-vs-filter-beginner-primer.md)
- [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
- [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: filterregistrationbean vs component filter, spring filter bean registration, spring filter auto registration, filter url pattern order beginner, filterregistrationbean 언제 쓰나요, @component filter면 충분한가요, filter order 설정 어디서 해요, filter urlpatterns beginner, servlet filter registration basics, spring boot filter bean auto register, filter enabled false beginner, component filter vs registration bean, 처음 배우는데 filterregistrationbean, filter bean 등록이랑 servlet 등록 차이

## 핵심 개념

처음에는 질문을 둘로만 나누면 된다.

- `@Component` / `@Bean`: "이 필터 객체를 Spring bean으로 관리할까?"
- `FilterRegistrationBean`: "그 필터를 서블릿 컨테이너에 어떤 규칙으로 붙일까?"

Spring Boot에서는 `Filter`가 Spring bean이면 기본적으로 서블릿 필터로도 등록된다. 보통 `/*`에 연결된다고 생각하면 된다. 그래서 단순한 로깅 필터, trace id 필터처럼 "앱 전체에 그냥 걸면 되는 필터"는 `@Component`만으로도 출발할 수 있다.

반대로 URL 패턴, 순서, dispatcher type, 비활성화 여부까지 직접 잡아야 하면 `FilterRegistrationBean`이 더 맞다.

초급자용 선택 사다리는 이렇게 가져가면 된다.

1. 이 필터가 Spring 의존성 주입을 받아야 하나? 그러면 먼저 `@Component`나 `@Bean`으로 bean으로 만든다.
2. 전체 요청에 기본값으로 붙이면 충분한가? 그러면 거기서 멈춘다.
3. `/api/*`만 적용, 순서 조정, 등록 비활성화처럼 "어떻게 붙일지"가 중요해지면 `FilterRegistrationBean`을 추가한다.

## 한눈에 보기

| 지금 필요한 것 | 먼저 떠올릴 선택 | 이유 |
|---|---|---|
| 필터를 Spring이 관리하게 하고 전체 요청에 기본 적용 | `@Component` 또는 `@Bean` | Boot가 `Filter` bean을 기본 등록해 준다 |
| 필터가 다른 bean을 주입받아야 한다 | `@Component` 또는 `@Bean` | 먼저 bean으로 관리되어야 생성자 주입이 자연스럽다 |
| `/api/*`에만 걸고 싶다 | `FilterRegistrationBean` | URL 패턴을 직접 지정해야 한다 |
| 다른 필터보다 먼저/나중에 돌리고 싶다 | `FilterRegistrationBean` 또는 필터 자체 `@Order` | 기본 등록에 기대지 말고 순서를 드러내야 한다 |
| bean으로는 두되 지금은 서블릿 필터로 등록하지 않고 싶다 | `FilterRegistrationBean#setEnabled(false)` | 등록 자체를 끌 수 있다 |

```text
1) bean 등록
Spring container가 "이 필터 객체를 생성하고 주입한다"

2) filter 등록
Servlet container가 "이 요청 경로/순서에 이 필터를 실행한다"
```

초급자에게 헷갈리는 지점은 둘 다 "등록"이라고 부르기 쉽다는 점이다. 하지만 **bean 등록과 filter 매핑 등록은 같은 질문이 아니다.**

## 상세 분해

### 1. `@Component`는 "Spring이 이 객체를 관리한다"는 뜻이다

```java
@Component
public class TraceFilter extends OncePerRequestFilter {
    // ...
}
```

이렇게 두면 먼저 `TraceFilter`가 Spring bean이 된다. Spring Boot 환경에서는 이런 `Filter` bean이 embedded servlet container에 기본 등록되므로, 초급자 입장에서는 "일단 전체 요청에 공통 필터를 붙였다"까지는 쉽게 갈 수 있다.

즉 `@Component`는 선택의 초점이 "bean으로 올릴까?"에 있다.

초급자에게 중요한 포인트는 이것이다.

- `@Component`는 직접 URL 패턴을 적지 않는다
- 하지만 Spring Boot에서는 `Filter` bean이면 기본 필터 등록까지 이어진다
- 그래서 "bean 등록만 했다"고 느꼈는데 실제로는 전역 필터처럼 동작할 수 있다

이 감각이 없으면 "`@Component`만 붙였는데 왜 모든 요청에서 도나요?"라는 질문으로 이어지기 쉽다.

### 2. `FilterRegistrationBean`은 "어떻게 붙일까?"를 조정한다

```java
@Bean
FilterRegistrationBean<TraceFilter> traceFilterRegistration(TraceFilter traceFilter) {
    FilterRegistrationBean<TraceFilter> registration = new FilterRegistrationBean<>(traceFilter);
    registration.addUrlPatterns("/api/*");
    registration.setOrder(1);
    return registration;
}
```

여기서 중요한 건 필터 로직 자체보다 등록 메타데이터다.

- 어떤 URL 패턴에 붙일지
- 어느 순서로 돌릴지
- 어떤 dispatcher type에 반응할지
- 지금은 아예 비활성화할지

즉 `FilterRegistrationBean`의 초점은 "필터 객체 생성"보다 **서블릿 컨테이너 등록 옵션**이다.

예를 들어 아래처럼 "bean은 이미 따로 있고, 등록 규칙만 여기서 잡는다"는 모양으로 읽으면 beginner 기준 큰 그림이 빨리 잡힌다.

```java
@Bean
TraceFilter traceFilter() {
    return new TraceFilter();
}
```

```java
@Bean
FilterRegistrationBean<TraceFilter> traceFilterRegistration(TraceFilter traceFilter) {
    FilterRegistrationBean<TraceFilter> registration = new FilterRegistrationBean<>(traceFilter);
    registration.addUrlPatterns("/api/*");
    registration.setOrder(1);
    return registration;
}
```

## 등록 감각 잡기

### 3. 둘은 완전히 다른 세계가 아니라, 질문 층이 다르다

처음엔 "`@Component` 대신 `FilterRegistrationBean`"처럼 보이지만, 실제로는 다음처럼 보는 편이 덜 헷갈린다.

- bean 등록이 필요하다
- 그다음 filter 등록 규칙이 단순한가, 커스텀인가를 고른다

그래서 "필터 객체는 Spring bean으로 관리받되, 등록 옵션은 따로 조절"하는 형태가 자연스럽다.

## 흔한 오해와 함정

- "`@Component`를 붙였으니 URL 패턴도 알아서 `/api/*`로 붙겠지"라고 생각하기 쉽다.
  기본 등록과 세부 매핑 제어는 다른 문제다. 특정 경로에만 걸려야 하면 `FilterRegistrationBean` 쪽 질문이다.

- "`FilterRegistrationBean`을 쓰면 필터가 Spring bean이 아닌가?"라고 생각하기 쉽다.
  핵심은 bean 여부보다 등록 메타데이터를 어디서 잡느냐다. 예제처럼 기존 filter bean을 주입받아 감싸는 형태도 흔하다.

- "`@Component`로 등록하고 같은 필터를 또 `FilterRegistrationBean`으로 감싸면 무조건 더 안전하다"라고 생각하기 쉽다.
  초급자 단계에서는 한 필터의 **등록 의도**를 한곳에서 읽히게 두는 편이 안전하다. 기본 자동 등록으로 충분한지, 아니면 registration bean으로 경로/순서/활성화를 직접 말할지부터 정리한다.

- "`필터가 DI를 받으려면 무조건 `FilterRegistrationBean`이어야 한다"라고 생각하기 쉽다.
  아니다. DI 필요 여부는 보통 bean 등록 질문이고, `FilterRegistrationBean`은 그다음 등록 규칙 질문이다.

## 실무에서 쓰는 모습

RoomEscape 관리자 API를 떠올려 보자.

### 경우 1. 앱 전체 요청에 trace id를 넣고 싶다

관리자 페이지든 일반 API든 전부 같은 로깅 규칙을 쓰고 싶다면, 초급자 첫 구현은 `@Component` 기반 필터로도 충분한 경우가 많다.

### 경우 2. `/api/*` 요청에만 JWT 헤더 검사 필터를 붙이고 싶다

이때는 "필터 bean이 있느냐"보다 "어디에 걸리느냐"가 더 중요하다. 그래서 `FilterRegistrationBean`으로 URL 패턴과 순서를 같이 적는 편이 의도를 더 잘 보여 준다.

### 경우 3. 테스트나 특정 프로필에서만 잠시 끄고 싶다

필터 코드는 bean으로 두되, 등록 자체를 끄고 싶다면 `FilterRegistrationBean`의 `enabled` 같은 옵션이 더 직접적이다.

짧게 결정하면 이렇게 정리할 수 있다.

| 상황 | 출발점 |
|---|---|
| "필터를 만들고 DI만 받으면 된다" | `@Component` / `@Bean` |
| "전체 요청에 기본 적용이면 충분하다" | `@Component` / `@Bean` |
| "경로, 순서, on/off를 말해야 한다" | `FilterRegistrationBean` |

## 더 깊이 가려면

- 필터를 만들 때 왜 `OncePerRequestFilter`를 먼저 권하는지부터 보고 싶다면 [Spring `OncePerRequestFilter` vs 일반 `Filter` 입문: 언제 상속부터 시작할까](./spring-onceperrequestfilter-vs-filter-beginner-primer.md)를 먼저 본다.
- 필터와 인터셉터를 아직 섞고 있다면 [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)로 큰 그림을 먼저 분리한다.
- 순서 충돌이 핵심이면 [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)으로 내려간다.
- bean 등록과 component scan 쪽이 더 헷갈리면 [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)로 돌아간다.

## 면접/시니어 질문 미리보기

> Q: `@Component` 필터와 `FilterRegistrationBean`의 beginner 기준 첫 차이는 무엇인가?
> 의도: bean 등록과 servlet registration 구분
> 핵심: `@Component`는 bean 등록 쪽, `FilterRegistrationBean`은 URL 패턴/순서 같은 등록 규칙 제어 쪽이다.

> Q: `/api/*`에만 필터를 걸고 싶을 때 왜 `FilterRegistrationBean`이 더 직접적인가?
> 의도: 선택 기준 확인
> 핵심: 기본 bean 등록만으로는 경로 매핑 의도를 충분히 드러내기 어렵고, registration bean이 URL 패턴을 명시적으로 표현하기 때문이다.

> Q: 필터를 Spring bean으로 관리하면서도 등록 규칙을 따로 잡을 수 있는가?
> 의도: 둘의 관계 이해 확인
> 핵심: 가능하다. filter 객체는 bean으로 두고, registration bean이 서블릿 등록 메타데이터를 담당할 수 있다.

## 한 줄 정리

초급자 기준으로 `@Component`는 "필터를 Spring이 관리하게 하자"에 가깝고, `FilterRegistrationBean`은 "그 필터를 어떤 경로와 순서로 실행시킬지 직접 정하자"에 가깝다.

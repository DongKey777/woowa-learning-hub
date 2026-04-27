# Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄

> 한 줄 요약: `Filter`와 `HandlerInterceptor`는 요청을 다음 단계로 넘길지 말지 결정하는 **책임 연쇄** 쪽이고, `OncePerRequestFilter`는 그 안에서 필터 구현 순서를 고정하는 **템플릿 메소드** 래퍼다.

**난이도: 🟢 Beginner**

> 학습 순서 라벨: `basics -> framework examples -> deep dive` (`framework examples -> deep dive` 사이 bridge)

관련 문서:

- [템플릿 메소드 패턴 기초](./template-method-basics.md)
- [템플릿 메소드 패턴](./template-method.md)
- [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](./chain-of-responsibility-filters-interceptors.md)
- [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md)
- [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](../spring/spring-onceperrequestfilter-async-error-dispatch-traps.md)
- [Pipeline vs Chain of Responsibility](./pipeline-vs-chain-of-responsibility.md)
- [실전 패턴 선택 가이드](./pattern-selection.md)

retrieval-anchor-keywords: spring filter vs handlerinterceptor, onceperrequestfilter template method, filter vs onceperrequestfilter, filter chain vs template method, handlerinterceptor chain of responsibility, onceperrequestfilter is a filter base class, dofilterinternal shouldnotfilter, prehandle short circuit, onceperrequestfilter beginner route, filter interceptor onceperrequestfilter comparison, template basics before onceperrequestfilter, 처음 배우는데 onceperrequestfilter, template method vs filter interceptor chain basics, template method vs filter interceptor chain beginner, template method vs filter interceptor chain intro

---

## 먼저 어디서 시작할까

처음 배우는데 `OncePerRequestFilter`가 템플릿 메소드 예시로 먼저 보였다면 이 비교 문서부터 바로 들어오기보다 `basics -> framework examples -> deep dive` 순서로 읽는 편이 덜 헷갈린다.

- `basics`: [템플릿 메소드 패턴 기초](./template-method-basics.md)
- `framework examples`: [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md)
- 이 문서: `framework examples -> deep dive` 사이에서 `chain participant`와 `template wrapper`를 분리하는 bridge
- `deep dive`: [템플릿 메소드 패턴](./template-method.md)

이 문서는 `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`가 한 요청 경로에서 **어느 레벨에서 다른 개념인지**를 30초 안에 자르는 bridge다.

| 지금 막힌 질문 | 먼저 볼 문서 | 그다음 |
|---|---|---|
| `템플릿 메소드가 뭐지`, `hook method` / `abstract step`이 낯설다 | [템플릿 메소드 패턴 기초](./template-method-basics.md) | framework example을 보고 이 문서로 온다 |
| `HttpServlet`, `OncePerRequestFilter`가 왜 템플릿 메소드 예시인지 큰 그림이 궁금하다 | [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md) | 이 문서에서 chain과 wrapper를 분리한다 |
| `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`가 같은 레벨처럼 섞여 보인다 | 이 문서 | dispatch 함정까지 필요하면 [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](../spring/spring-onceperrequestfilter-async-error-dispatch-traps.md)로 내려간다 |

---

## 이 문서는 무엇만 빠르게 분리하는가

Spring 요청 경로를 읽다 보면 아래 셋이 자주 한 덩어리로 섞인다.

- `Filter`
- `HandlerInterceptor`
- `OncePerRequestFilter`

하지만 셋은 같은 레벨의 개념이 아니다.

- `Filter`: 서블릿 요청 체인의 처리자
- `HandlerInterceptor`: Spring MVC 핸들러 실행 체인의 처리자
- `OncePerRequestFilter`: `Filter`를 구현할 때 쓰는 Spring base class

즉 `Filter`와 `HandlerInterceptor`는 **체인에 서 있는 역할**이고,
`OncePerRequestFilter`는 **필터 하나 내부의 확장 방식**이다.

---

## 30초 구분표

| 대상 | 먼저 읽어야 하는 패턴 | 누가 순서를 쥐는가 | 다음 단계로 넘길지 누가 결정하는가 | 대표 확장 지점 |
|---|---|---|---|---|
| `Filter` | 책임 연쇄 | 서블릿 컨테이너 + 등록된 필터 체인 | 각 필터가 `chain.doFilter()` 호출 여부를 정함 | `doFilter()` |
| `HandlerInterceptor` | 책임 연쇄 | `DispatcherServlet` + 등록된 interceptor chain | 각 인터셉터가 `preHandle()` 반환값으로 계속/중단을 정함 | `preHandle()`, `postHandle()`, `afterCompletion()` |
| `OncePerRequestFilter` | 템플릿 메소드 | Spring base class가 필터 실행 골격을 고정 | subclass는 내부 단계만 채우고, 실제 체인 진행은 보통 `doFilterInternal()` 안에서 수행 | `doFilterInternal()`, `shouldNotFilter()` |

바로 외우면 다음 한 문장으로 충분하다.

**"체인 참가자는 `Filter`/`HandlerInterceptor`, 템플릿 래퍼는 `OncePerRequestFilter`."**

---

## 왜 헷갈리는가

헷갈리는 이유는 `OncePerRequestFilter`가 **필터 체인 안에 들어가는 필터이면서**,
동시에 자기 내부에서는 **템플릿 메소드 구조**를 쓰기 때문이다.

즉 한 요청 안에 패턴이 겹친다.

1. 바깥 구조: 여러 `Filter`와 `HandlerInterceptor`가 이어지는 **책임 연쇄**
2. 안쪽 구현: `OncePerRequestFilter`가 `doFilter()` 골격을 쥐고 subclass에 `doFilterInternal()`을 여는 **템플릿 메소드**

패턴 이름을 하나만 붙이려 하면 여기서 계속 꼬인다.

---

## `Filter`를 읽는 법: 요청을 넘길지 끊을지 보는 체인 노드

`Filter`를 볼 때 먼저 봐야 할 질문은 "이 필터가 다음 필터로 넘기나?"다.

- `chain.doFilter(request, response)`를 호출하면 계속 진행
- 호출하지 않으면 여기서 종료
- 인증 실패, rate limit, 헤더 검증 실패 같은 short-circuit 지점이 자주 생김

따라서 `Filter`의 핵심은 "정해진 슬롯 override"보다 **전파 제어**다.

```java
public class AuthFilter implements Filter {
    @Override
    public void doFilter(
        ServletRequest request,
        ServletResponse response,
        FilterChain chain
    ) throws IOException, ServletException {
        if (!authorized((HttpServletRequest) request)) {
            ((HttpServletResponse) response).sendError(401);
            return;
        }
        chain.doFilter(request, response);
    }
}
```

이 구조를 읽을 때의 주 패턴은 템플릿 메소드가 아니라 **책임 연쇄**다.

## `HandlerInterceptor`를 읽는 법: 컨트롤러 앞뒤의 책임 연쇄

`HandlerInterceptor`도 본질은 비슷하다.
다만 위치가 필터보다 안쪽이고, `DispatcherServlet` 주변에서 동작한다.

- `preHandle()`이 `false`를 반환하면 컨트롤러까지 가지 않고 중단
- `postHandle()`은 핸들러 실행 후
- `afterCompletion()`은 정리/관측 지점

```java
public class AdminInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(
        HttpServletRequest request,
        HttpServletResponse response,
        Object handler
    ) throws Exception {
        if (!request.isUserInRole("ADMIN")) {
            response.sendError(403);
            return false;
        }
        return true;
    }
}
```

여기서도 핵심은 `preHandle()`이 **다음 단계 진행 여부를 결정**한다는 점이다.
그래서 인터페이스 메서드가 여러 개 있어도 1차 분류는 여전히 책임 연쇄다.

## `OncePerRequestFilter`를 읽는 법: 체인 안의 필터를 만드는 템플릿 메소드

`OncePerRequestFilter`는 `Filter` 자체를 대체하는 새 체인이 아니다.
필터 구현자가 매번 반복하던 공통 골격을 Spring이 base class로 묶어 둔 것이다.

- 바깥에서는 filter chain의 **한 노드**
- 안에서는 `doFilter()`가 실행 순서를 고정하는 **템플릿 메소드**

보통 이렇게 읽는다.

- 고정 골격: 한 요청당 한 번 처리, dispatch 관련 분기, 이미 필터링 여부 확인
- 필수 단계: `doFilterInternal()`
- 선택적 hook: `shouldNotFilter()`, `shouldNotFilterAsyncDispatch()`, `shouldNotFilterErrorDispatch()`

```java
public class TraceIdFilter extends OncePerRequestFilter {
    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return request.getRequestURI().startsWith("/health");
    }

    @Override
    protected void doFilterInternal(
        HttpServletRequest request,
        HttpServletResponse response,
        FilterChain filterChain
    ) throws ServletException, IOException {
        request.setAttribute("traceId", UUID.randomUUID().toString());
        filterChain.doFilter(request, response);
    }
}
```

즉 `OncePerRequestFilter`를 보며 묻는 질문은 다르다.

- "다음 필터로 넘길까?"보다
- "Spring base class가 어떤 순서를 고정했고, 내가 어떤 슬롯만 채우는가?"

이 질문이면 템플릿 메소드로 읽는 게 맞다.

---

## 한 그림으로 겹쳐 읽기

```text
Client
  -> Filter A
  -> MyTraceFilter extends OncePerRequestFilter
       -> doFilter()            // template method skeleton
       -> shouldNotFilter()?    // optional hook
       -> doFilterInternal()    // subclass step
       -> filterChain.doFilter()
  -> DispatcherServlet
       -> Interceptor 1 preHandle()
       -> Interceptor 2 preHandle()
       -> Controller
       -> Interceptor 2 postHandle()
       -> Interceptor 1 postHandle()
```

이 그림에서 패턴 경계는 이렇게 읽으면 된다.

- `Filter A -> MyTraceFilter -> DispatcherServlet`: 책임 연쇄
- `OncePerRequestFilter#doFilter -> doFilterInternal`: 템플릿 메소드
- `Interceptor preHandle`들의 continue/stop 결정: 책임 연쇄

---

## 짧은 FAQ

### Q1. `Filter`와 `OncePerRequestFilter`는 같은 레벨인가?

아니다.

- `Filter`: 체인에 서는 역할/SPI
- `OncePerRequestFilter`: 그 `Filter`를 만들 때 자주 쓰는 Spring base class

즉 비교 축부터 다르다.

### Q2. `OncePerRequestFilter`는 결국 필터니까 책임 연쇄만 보면 되나?

아니다.

- 바깥 위치: filter chain의 한 노드라서 책임 연쇄
- 안쪽 구현: `doFilter()` 골격을 base class가 쥐어서 템플릿 메소드

한 요청 안에 두 패턴이 겹친다.

### Q3. `HandlerInterceptor`도 `pre/post`가 있으니 템플릿 메소드인가?

보통 그렇게 읽지 않는다.

`HandlerInterceptor`가 skeleton을 가진 게 아니라 `DispatcherServlet`이 chain을 실행하고, 인터셉터는 `preHandle()`로 계속 갈지 멈출지 정한다.

---

## 빠른 판별 질문

- 지금 보고 있는 코드가 `next` 호출 여부나 `true/false` 반환으로 흐름을 끊는가?
  그러면 책임 연쇄 쪽이다.
- base class가 `doFilter()` 같은 공통 골격을 쥐고 subclass에 `Internal` 메서드만 열어 두는가?
  그러면 템플릿 메소드 쪽이다.
- `OncePerRequestFilter` subclass가 `filterChain.doFilter()`를 언제 호출할지 직접 고르는가?
  바깥 구조는 chain, subclass 확장 방식은 template method가 동시에 성립한다.

---

## 한 줄 정리

Spring 요청 경로에서 `Filter`와 `HandlerInterceptor`는 **누가 다음 단계로 넘길지 결정하는 책임 연쇄**이고, `OncePerRequestFilter`는 **그중 한 필터를 구현할 때 순서를 고정해 주는 템플릿 메소드 base class**다.

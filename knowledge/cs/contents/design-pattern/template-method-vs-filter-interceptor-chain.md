# Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄

> 한 줄 요약: `Filter`와 `HandlerInterceptor`는 요청을 다음 단계로 넘길지 말지 결정하는 **책임 연쇄** 쪽이고, `OncePerRequestFilter`는 그 안에서 필터 구현 순서를 고정하는 **템플릿 메소드** 래퍼다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [템플릿 메소드 패턴](./template-method.md)
> - [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](./chain-of-responsibility-filters-interceptors.md)
> - [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md)
> - [Pipeline vs Chain of Responsibility](./pipeline-vs-chain-of-responsibility.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)

retrieval-anchor-keywords: spring filter vs handlerinterceptor, onceperrequestfilter template method, filter chain vs template method, handlerinterceptor chain of responsibility, spring mvc interceptor chain, doFilterInternal shouldNotFilter, preHandle short circuit, filterchain doFilter, template method vs chain of responsibility spring, onceperrequestfilter is a filter base class, filter interceptor onceperrequestfilter comparison

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

## API별로 읽는 법

### 1. `Filter`: 요청을 넘길지 끊을지 결정하는 체인 노드

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

### 2. `HandlerInterceptor`: 컨트롤러 주변의 책임 연쇄

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

### 3. `OncePerRequestFilter`: 체인 안에 서는 필터를 위한 템플릿 메소드

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

## 자주 하는 오해

### 오해 1: `OncePerRequestFilter`도 그냥 책임 연쇄다

반은 맞고 반은 틀리다.

- 맞는 부분: 바깥에서 보면 filter chain의 한 노드다
- 틀린 부분: 클래스를 설계하는 방식은 template method다

즉 **runtime 위치는 chain, class-level extension 방식은 template method**다.

### 오해 2: `HandlerInterceptor`는 `pre/post`가 있으니 템플릿 메소드다

그렇지 않다.  
`HandlerInterceptor` 인터페이스 자체가 상위 skeleton을 들고 있는 게 아니라,  
`DispatcherServlet`이 interceptor chain을 실행한다.

핵심 제어는 여전히 `preHandle()`의 진행/중단 결정에 있다.

### 오해 3: `Filter`와 `OncePerRequestFilter`는 같은 레벨 비교 대상이다

엄밀히는 아니다.

- `Filter`: SPI/역할
- `OncePerRequestFilter`: 그 SPI를 구현하는 base class

그래서 비교 질문도 "둘 중 어떤 패턴인가?"가 아니라  
"필터 체인이라는 바깥 구조 안에서, 이 구현이 템플릿 메소드 래퍼를 쓰는가?"가 더 정확하다.

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

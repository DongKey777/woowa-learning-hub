# 프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle

> 한 줄 요약: 프레임워크가 라이프사이클의 뼈대를 고정하고, 애플리케이션은 `doGet`, `doFilterInternal`, `setUp` 같은 슬롯만 채운다.

**난이도: 🟢 Beginner**

> 학습 순서 라벨: `basics -> framework examples -> deep dive` (`framework examples` 단계)

관련 문서:

- [템플릿 메소드 패턴 기초](./template-method-basics.md)
- [템플릿 메소드 패턴](./template-method.md)
- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
- [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](./chain-of-responsibility-filters-interceptors.md)
- [Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄](./template-method-vs-filter-interceptor-chain.md)
- [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](../spring/spring-onceperrequestfilter-async-error-dispatch-traps.md)
- [JUnit 5 Callback Model vs Classic xUnit Template Skeleton](./junit5-callback-model-vs-classic-xunit-template-skeleton.md)
- [Template Hook Smells](./template-hook-smells.md)
- [상속보다 조합 기초](./composition-over-inheritance-basics.md)

retrieval-anchor-keywords: template method framework example, servlet lifecycle template method, httpservlet service doget dopost, onceperrequestfilter dofilterinternal shouldnotfilter, junit testcase runbare setup teardown, framework callback skeleton, dofilterinternal abstract step, shouldnotfilter hook, 처음 배우는데 framework template method, framework template method basics bridge

---

## 이 문서는 무엇만 다루는가

처음 배우는데 `hook method`나 `abstract step` 정의부터 막히면 [템플릿 메소드 패턴 기초](./template-method-basics.md)를 먼저 본다.

여기서는 기본 정의를 다시 풀기보다 "프레임워크가 골격을 어디에 숨겨 두는가", "필수 단계와 hook이 무엇인가", "다른 패턴과 왜 헷갈리는가"만 짚는다.

질문이 "이 프레임워크 base class를 상속해야 하나, 별도 policy/component로 빼야 하나?"라면 예시를 읽기 전에 [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)이나 [상속보다 조합 기초](./composition-over-inheritance-basics.md)를 먼저 보는 편이 빠르다.
이 문서는 inheritance 선택 자체를 판정하기보다, **이미 base class를 읽고 있을 때 skeleton과 hook을 식별하는 보조 문서**다.

처음 배우는데 `HttpServlet`, `OncePerRequestFilter`가 템플릿 메소드 예시로 먼저 보였다면 여기서 큰 그림을 잡고, async/error redispatch처럼 운영 디버깅 질문이 생길 때만 [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](../spring/spring-onceperrequestfilter-async-error-dispatch-traps.md)로 내려간다.

## 빠른 라우팅

| 지금 막힌 질문 | 먼저 볼 문서 | 그다음 |
|---|---|---|
| `템플릿 메소드가 뭐지`, `hook method` / `abstract step`이 아직 낯설다 | [템플릿 메소드 패턴 기초](./template-method-basics.md) | 이 문서로 와서 framework 예시를 본다 |
| `HttpServlet`, `OncePerRequestFilter`가 왜 템플릿 메소드 예시인지 큰 그림이 궁금하다 | 이 문서 | [Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄](./template-method-vs-filter-interceptor-chain.md) |
| async/error dispatch에서 필터가 왜 두 번 돌거나 빠져 보이는지 궁금하다 | [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](../spring/spring-onceperrequestfilter-async-error-dispatch-traps.md) | 이 문서로 돌아와 pattern 큰 그림을 다시 정리한다 |

---

## 콜백을 `abstract step` vs `hook`으로 바로 읽는 30초 브리지

먼저 멘탈 모델부터 잡는다.

- `abstract step`: 여기에 내 로직을 넣지 않으면 기능이 성립하지 않는 필수 슬롯
- `hook`: 필요할 때만 끼워 넣는 선택 슬롯

프레임워크 문서에서 callback 이름이 많아 보여도, 처음에는 아래처럼 두 칸으로만 분류하면 된다.

| 프레임워크 콜백 | 초심자용 분류 | 왜 이렇게 읽으면 빠른가 |
|---|---|---|
| `HttpServlet#doGet` / `doPost` | `abstract step`에 가까운 필수 슬롯 | `service()`가 분기 골격을 잡고, 실제 요청 처리 로직은 보통 여기서 채운다 |
| `OncePerRequestFilter#doFilterInternal` | `abstract step` (필수) | `OncePerRequestFilter`의 고정 골격 안에서 반드시 구현해야 하는 핵심 처리 단계다 |
| `OncePerRequestFilter#shouldNotFilter` | `hook` (선택) | override하지 않아도 기본 동작으로 흐르고, 필요할 때만 제외 조건을 추가한다 |
| `TestCase#setUp` / `tearDown` | `hook` (선택) | fixture 준비/정리 타이밍을 끼워 넣는 슬롯이고, 비워 두어도 테스트 구조는 돈다 |
| `TestCase#testXxx` 본문 | `abstract step`에 가까운 핵심 슬롯 | 프레임워크가 실행 순서를 잡고, 테스트가 실제로 검증할 내용은 여기서 채운다 |

자주 생기는 1차 혼동:

- `abstract step`이 반드시 `abstract` 키워드여야 하는 것은 아니다. 실무에서는 "채우지 않으면 목적 기능이 비는 슬롯"이면 이렇게 읽는 편이 빠르다.
- `hook`은 있어도 되고 없어도 되는 옵션이어야 한다. `shouldNotFilter()`에 핵심 비즈니스 분기가 계속 붙으면 hook이 아니라 설계 경계 재검토 신호다.
- callback이라는 이름만으로 성격이 같지 않다. 먼저 "필수 슬롯인가, 선택 슬롯인가"를 가르면 템플릿 메소드 구조가 빨리 보인다.

---

## 1. Servlet: `HttpServlet`이 HTTP 메서드 분기 뼈대를 쥔다

서블릿 컨테이너는 보통 서블릿 인스턴스에 직접 `doGet()`을 호출하지 않는다.
먼저 `service()`를 호출하고, `HttpServlet`이 HTTP method를 보고 `doGet()`, `doPost()`, `doPut()` 같은 단계로 분기한다.

- skeleton owner: 서블릿 컨테이너 + `HttpServlet`
- app extension point: `doGet()`, `doPost()` 같은 메서드별 handler
- 실무 포인트: 전체 분기 규칙을 바꾸려면 `service()`까지 건드려야 하므로, 대부분은 `doXxx()`만 override한다

```java
public class OrderServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
        throws ServletException, IOException {
        resp.getWriter().write("orders");
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp)
        throws ServletException, IOException {
        resp.setStatus(HttpServletResponse.SC_CREATED);
    }
}
```

핵심은 내가 요청 처리 순서를 정의한 게 아니라,
프레임워크가 이미 정해 둔 순서 안에서 메서드별 빈칸만 채운다는 점이다.

---

## 2. Filter: 체인 자체는 책임 연쇄, `OncePerRequestFilter` 래퍼는 템플릿 메소드

여기가 가장 자주 헷갈린다.

서블릿 `Filter#doFilter()` 자체는 [책임 연쇄](./chain-of-responsibility-filters-interceptors.md)에 가깝다.
각 필터가 `chain.doFilter()`를 호출할지 말지 결정하면서 다음 단계로 넘기기 때문이다.

하지만 Spring의 `OncePerRequestFilter`는 그 위에 **템플릿 메소드 레이어**를 하나 더 얹는다.

- `doFilter()` 쪽에서 once-per-request 검사, dispatch 분기, 공통 방어 로직을 고정한다
- `doFilterInternal()`을 필수 확장 단계로 연다
- `shouldNotFilter()`는 선택적 hook처럼 쓴다

```java
@Component
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

즉 같은 필터 API 주변에서도 패턴이 겹친다.

- 바깥 파이프라인: 책임 연쇄
- base class wrapper: 템플릿 메소드

필터 문서를 읽다가 `doFilterInternal()` 같은 이름이 보이면
"체인 안에서 프레임워크가 한 번 더 skeleton을 잡고 있구나"라고 보면 된다.

단, `shouldNotFilter()`가 path 제외를 넘어서 tenant/role/dispatch policy를 빨아들이기 시작하면
이제는 framework example을 읽는 수준을 넘었다고 보면 된다. `hook`이 1~2개 설명을 넘어서 `beforeX/afterX/cleanup`처럼 계속 늘면 [Template Hook Smells](./template-hook-smells.md)로 넘어간다.

---

## 3. Test lifecycle: classic xUnit은 템플릿 메소드 냄새가 강하다

고전 xUnit/JUnit 3 계열에서는 `TestCase#runBare()`가 대략 아래 뼈대를 쥔다.

1. `setUp()`
2. 테스트 본문 실행
3. `tearDown()`

애플리케이션 코드는 fixture 준비와 정리를 override하고, 테스트 본문만 채운다.

```java
public class OrderServiceTest extends TestCase {
    private OrderService orderService;

    @Override
    protected void setUp() {
        orderService = new OrderService(new FakePaymentGateway());
    }

    public void testCreateOrder() {
        assertEquals(1L, orderService.create("cola").getId());
    }

    @Override
    protected void tearDown() {
        orderService = null;
    }
}
```

여기서는 다음처럼 읽으면 된다.

- `runBare()` 같은 framework-owned entrypoint: 템플릿 메소드
- `setUp()` / `tearDown()`: hook에 가까운 lifecycle slot
- `testCreateOrder()`: 실제로 바뀌는 핵심 단계

단, 현대 JUnit 5의 `@BeforeEach` / `@AfterEach`는 상속 기반 템플릿 메소드보다
callback registration 성격이 더 강하다.
그래도 테스트 인프라를 읽을 때 "프레임워크가 순서를 쥐고 있고, 나는 정해진 slot만 채운다"는 감각은 그대로 유효하다.

반대로 base test class의 `setUp()` / `tearDown()`이 fixture 준비를 넘어 DB seed, clock reset, event spy 등록까지 끌어안기 시작하면
그건 템플릿 예시가 아니라 hook smell 쪽 신호다. 현대 JUnit 5 쪽 분해 감각은 [JUnit 5 Callback Model vs Classic xUnit Template Skeleton](./junit5-callback-model-vs-classic-xunit-template-skeleton.md), 냄새 기준은 [Template Hook Smells](./template-hook-smells.md)에서 이어 볼 수 있다.

---

## 4. 빠른 구분 포인트

| 질문 | 템플릿 메소드로 읽기 쉬운 신호 | 다른 패턴에 더 가까운 신호 |
|---|---|---|
| 누가 순서를 정하는가 | framework/base class가 entrypoint를 쥔다 | 각 단계가 `next` 호출 여부를 결정한다 |
| 무엇을 override하는가 | `doGet`, `doFilterInternal`, `setUp` 같은 named slot | 구현체 전체 또는 runtime strategy |
| 어디서 자주 헷갈리는가 | framework callback, base test class, servlet subclass | filter chain, interceptor chain, event listener |

한 줄 판별식:

- `service -> doGet/doPost`처럼 dispatch skeleton이 먼저 있으면 템플릿 메소드
- `filter -> next filter`처럼 다음 단계로 넘길지 말지 각 처리자가 정하면 책임 연쇄
- annotation으로 callback만 등록하고 공통 상위 skeleton이 안 보이면 classic 템플릿 메소드보다는 callback/observer 쪽

---

## 한 줄 정리

서블릿의 `service -> doGet/doPost`, Spring filter의 `doFilter -> doFilterInternal`, classic xUnit의 `runBare -> setUp/test/tearDown`처럼
"framework owns the sequence, app fills the slots"일 때 템플릿 메소드로 읽으면 구조가 빨리 보인다.

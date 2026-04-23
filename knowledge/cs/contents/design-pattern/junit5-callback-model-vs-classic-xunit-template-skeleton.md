# JUnit 5 Callback Model vs Classic xUnit Template Skeleton

> 한 줄 요약: classic xUnit의 `runBare -> setUp/test/tearDown`는 템플릿 스켈레톤으로 읽기 쉽지만, JUnit 5의 `@BeforeEach` / `@AfterEach`와 extension API는 **상속 기반 skeleton 하나**보다 **annotation + callback composition**에 더 가깝다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md)
> - [템플릿 메소드 패턴](./template-method.md)
> - [Template Hook Smells](./template-hook-smells.md)
> - [Composition over Inheritance](./composition-over-inheritance-practical.md)

retrieval-anchor-keywords: junit 5 callback model, junit5 callback model, junit 5 beforeeach aftereach, junit5 beforeeach aftereach, BeforeEachCallback AfterEachCallback, BeforeTestExecutionCallback AfterTestExecutionCallback, ParameterResolver InvocationInterceptor, classic xUnit template skeleton, junit TestCase runBare setUp tearDown, junit extension not template method, annotation callback composition, test lifecycle callback model

---

## 이 문서는 언제 읽으면 좋은가

- `@BeforeEach` / `@AfterEach`를 classic `setUp()` / `tearDown()`와 완전히 같은 그림으로 봐도 되는지 헷갈릴 때
- base test class 상속과 `@ExtendWith` extension이 섞여 있어 템플릿 메소드와 callback 모델의 경계가 흐릴 때
- "프레임워크가 순서를 쥔다"는 감각은 유지하되, 왜 modern JUnit 5 extension 전체를 classic Template Method라고 부르면 과한지 정리하고 싶을 때

---

## 1. Classic xUnit: 템플릿 스켈레톤이 눈에 보인다

classic xUnit/JUnit 3 쪽은 보통 아래 그림으로 읽힌다.

```text
runBare()
  -> setUp()
  -> testMethod()
  -> tearDown()
```

여기서는 템플릿 메소드라고 부르기 쉽다.

- skeleton owner: `TestCase#runBare()`
- 확장 방식: 하위 클래스가 `setUp()` / `tearDown()`을 override
- 핵심 감각: framework가 entrypoint를 쥐고, test class는 정해진 slot만 채운다

즉 classic xUnit의 중심은 **상속된 base class가 가진 고정 skeleton**이다.

---

## 2. JUnit 5에서 `@BeforeEach` / `@AfterEach`는 어디에 들어가나

JUnit 5에서도 여전히 framework가 각 테스트의 실행 순서를 쥔다.  
다만 slot을 여는 방식이 `runBare()` override보다 더 분해되어 있다.

예외 처리 callback을 생략하고 단순화하면 per-test 흐름은 대략 이렇게 읽으면 된다.

```text
BeforeEachCallback
  -> @BeforeEach
    -> BeforeTestExecutionCallback
      -> @Test
    -> AfterTestExecutionCallback
  -> @AfterEach
AfterEachCallback
```

그래서 `@BeforeEach` / `@AfterEach`는 이렇게 이해하면 된다.

- `@BeforeEach`: 각 테스트 메서드 직전의 user lifecycle slot
- `@AfterEach`: 각 테스트 메서드 직후의 user lifecycle slot
- 둘 다 test body 바깥에서 실행되지만, JUnit 5 engine이 호출 순서를 결정한다

즉 "프레임워크가 순서를 쥐고 있고, 나는 정해진 lifecycle slot을 채운다"는 감각 자체는 여전히 유효하다.

---

## 3. 그런데 왜 modern JUnit 5 전체를 classic Template Method라고 부르면 과한가

### 1. 상속 override보다 callback registration이 중심이다

classic xUnit은 base class method override가 핵심이다.  
반면 JUnit 5는 `@BeforeEach`, `@AfterEach`, `@ExtendWith` 같은 등록 모델이 중심이다.

- test class를 반드시 특정 base class에 묶지 않아도 된다
- lifecycle method, extension callback, parameter injection을 조합해서 붙인다

즉 확장 방식의 중심축이 **inheritance**에서 **composition** 쪽으로 이동했다.

### 2. extension은 단일 hook slot보다 wrapper stack에 가깝다

`BeforeEachCallback` / `AfterEachCallback`는 여러 extension이 등록되면 wrapping 순서를 가진다.

- 먼저 등록된 extension의 `before`가 먼저 돈다
- 같은 extension의 `after`는 더 나중에 돈다
- 그래서 `Extension1`이 `Extension2`를 감싸는 wrapper처럼 동작할 수 있다

이 구조는 "base class 안의 hook 몇 개"보다 **callback wrapper chain**에 더 가깝다.

### 3. extension API는 단순 hook을 넘는다

JUnit 5 extension은 단순히 전후 slot만 여는 게 아니다.

- `ParameterResolver`: `@Test`, `@BeforeEach`, `@AfterEach` 파라미터를 런타임에 주입한다
- `InvocationInterceptor`: lifecycle method와 test method 호출 자체를 감싼다

이쯤 되면 "상위 클래스 skeleton의 빈칸을 채운다"보다  
"test engine의 callback/interception protocol에 참여한다"가 더 정확하다.

### 4. `@BeforeEach` 와 `@AfterEach`를 고전 `setUp` / `tearDown` 쌍처럼 생각하면 오해가 생긴다

JUnit 5는 같은 클래스 안에 여러 `@BeforeEach` / `@AfterEach`가 있을 때 순서를 보장하긴 하지만 intentionally non-obvious하게 정렬한다.  
그리고 여러 `@BeforeEach`와 여러 `@AfterEach` 사이에 classic xUnit식 짝맞춤 wrapping을 보장하지 않는다.

그래서 실무에서는 보통:

- 의존 관계가 있는 setup/cleanup이면 `@BeforeEach` 하나, `@AfterEach` 하나로 유지하고
- 공통 test fixture는 abstract base class보다 extension이나 helper object로 빼는 편이 읽기 쉽다

---

## 4. 어디까지는 템플릿 메소드 감각으로 읽어도 되는가

아래 수준까지는 템플릿 메소드 감각이 여전히 유효하다.

- framework가 테스트 실행 순서를 소유한다
- user code는 named lifecycle slot에 들어간다
- superclass의 `@BeforeEach`는 subclass보다 먼저, superclass의 `@AfterEach`는 subclass보다 나중에 실행된다

하지만 아래로 넘어가면 callback composition 쪽으로 읽는 편이 더 정확하다.

- `@ExtendWith`로 여러 extension을 감싼다
- parameter injection이 lifecycle method 시그니처에 들어온다
- invocation interception, conditional execution, exception handling extension이 개입한다

짧게 말하면:

- **classic xUnit**: template skeleton이 중심
- **JUnit 5**: lifecycle callback composition이 중심

---

## 5. 30초 판별표

| 질문 | classic xUnit 쪽 | JUnit 5 쪽 |
|---|---|---|
| 확장의 기본 수단은? | base class override | annotation + extension registration |
| `setUp` / `tearDown`의 대응물은? | override hook | `@BeforeEach` / `@AfterEach` lifecycle callback |
| 여러 확장이 겹치면? | 주로 상속 계층 문제 | extension wrapping, interceptor, resolver 조합 문제 |
| 핵심 메타포는? | 템플릿 스켈레톤 | callback composition / interception |

---

## 한 줄 정리

`@BeforeEach` / `@AfterEach`는 JUnit 5 안에서 분명 **framework-owned lifecycle slot**이다.  
하지만 modern JUnit 5 extension 모델 전체는 classic xUnit의 단일 Template Method skeleton보다 **callback registration, wrapper, interception을 조합하는 실행 프로토콜**로 읽는 편이 정확하다.

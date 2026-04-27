# Spring Test Context Cache Split Triage Guide: `@MockBean`, property override, `@DirtiesContext`, slice drift

> 한 줄 요약: Spring 테스트가 느릴 때는 "테스트 로직이 무겁다"보다 먼저 "거의 같은 컨텍스트를 여러 벌 다시 띄우고 있나"를 보고, 특히 `@MockBean`, property override, `@DirtiesContext`, slice drift 네 축부터 분리하면 원인이 빨리 보인다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 느린 테스트의 대표 원인인 context cache split을 `@MockBean`, 테스트 property, `@DirtiesContext`, slice drift 기준으로 분해하는 **beginner troubleshooting primer**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
> - [Spring Test Property Override Boundaries: `@SpringBootTest(properties)`, `@TestPropertySource`, `@DynamicPropertySource`, context cache](./spring-test-property-override-boundaries-primer.md)
> - [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)
> - [Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks](./spring-test-slice-import-testconfiguration-boundaries.md)
> - [테스트 전략과 테스트 더블](../software-engineering/testing-strategy-and-test-doubles.md)

retrieval-anchor-keywords: spring test slow context cache split, context cache split triage, mockbean cache split, springboottest slow startup repeated context, testpropertysource cache split, dynamicpropertysource cache split, dirtiescontext slow tests, webmvctest slice drift, datajpatest slice drift, slow spring test primer, context cache miss troubleshooting, test context reuse beginner, spring test startup repeated, mockbean property override dirtiescontext guide, spring test context cache split triage guide basics

---

## 핵심 개념

초보자 기준으로는 context cache를 이렇게 생각하면 된다.

```text
같은 레시피의 테스트 클래스들
-> Spring이 ApplicationContext를 한 번 띄움
-> 뒤 테스트들이 그 컨텍스트를 재사용

레시피가 조금이라도 달라짐
-> 새 컨텍스트를 다시 띄움
-> 전체 테스트 시간이 눈에 띄게 늘어남
```

즉 테스트가 느린 이유는 "assert가 무겁다"보다 먼저 **컨텍스트 재사용이 끊겼는지**를 봐야 한다.

특히 아래 네 가지가 자주 cache split을 만든다.

1. `@MockBean` 조합이 테스트마다 다르다
2. property override 방식이나 값이 테스트마다 다르다
3. `@DirtiesContext`가 캐시를 일부러 버린다
4. 원래 slice test여야 할 것이 점점 full context처럼 불어난다

이 문서는 이 네 가지를 가장 먼저 가르는 triage 안내서다.

---

## 먼저 이 표로 분류한다

| 증상 | 먼저 의심할 것 | 왜 느려지나 | 첫 대응 |
|---|---|---|---|
| 비슷한 `@WebMvcTest`가 많은데 전체 시간이 길다 | `@MockBean` 조합 차이 | mock 구성이 다르면 다른 컨텍스트로 취급될 수 있다 | 공통 mock 조합이 있는지 본다 |
| 테스트마다 property 한두 개만 다르다 | annotation property override | 값이나 선언 문자열이 다르면 레시피가 달라진다 | 공통 설정으로 묶을 수 있는지 본다 |
| 어떤 클래스 뒤부터 급격히 느려진다 | `@DirtiesContext` | 캐시를 재사용하지 않고 버린다 | 정말 컨텍스트를 오염시키는지 재검토한다 |
| `@WebMvcTest`인데 DB/security/service가 자꾸 따라온다 | slice drift | 작아야 할 slice가 커져 startup 비용이 커진다 | slice 유지가 맞는지, 아니면 통합 테스트로 올릴지 결정한다 |

핵심은 원인을 한 번에 다 잡으려 하지 말고, **무엇이 레시피를 갈랐는지**부터 찾는 것이다.

---

## 1. `@MockBean` split: mock이 많을수록 빠르지 않을 수 있다

초보자가 가장 자주 헷갈리는 지점이 여기다.

> "mock을 쓰면 가벼워지니까 테스트도 빨라지겠지?"

부분적으로만 맞다.
한 테스트 클래스 안에서는 실제 의존성을 대체해 편해질 수 있지만, **테스트 클래스마다 다른 `@MockBean` 세트**를 만들기 시작하면 context cache는 잘게 쪼개질 수 있다.

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @MockBean OrderService orderService;
}
```

```java
@WebMvcTest(OrderController.class)
class OrderControllerErrorTest {
    @MockBean OrderService orderService;
    @MockBean CouponService couponService;
}
```

겉보기에는 둘 다 비슷한 MVC 테스트지만, 컨텍스트 입장에서는 같은 레시피가 아닐 수 있다.

### 이럴 때 의심 신호

- 같은 controller를 테스트하는데 클래스마다 mock 목록이 다르다
- 공통으로 필요한 collaborator가 있는데 매번 제각각 선언한다
- `@SpringBootTest`에서 여러 bean을 `@MockBean`으로 부분 치환하고 있다

### 먼저 할 질문

1. 이 테스트들이 정말 서로 다른 협력자 조합이 필요한가?
2. 같은 대상 controller/service를 검증하는데 클래스만 쪼개진 것은 아닌가?
3. mock을 늘리는 대신 slice 경계를 다시 잡아야 하는 것은 아닌가?

### 초보자용 정리

- `@MockBean`은 "무조건 성능 최적화 버튼"이 아니다
- mock이 늘수록 context 설계가 흔들릴 수 있다
- 비슷한 테스트는 가능한 한 **비슷한 mock 레시피**를 유지하는 편이 cache 재사용에 유리하다

---

## 2. Property split: 값 하나 차이도 새 컨텍스트가 될 수 있다

테스트 property override도 cache split의 대표 원인이다.

```java
@SpringBootTest(properties = "feature.payment=false")
class PaymentOffTest {
}
```

```java
@SpringBootTest(properties = "feature.payment=true")
class PaymentOnTest {
}
```

둘은 테스트 의도는 비슷해 보여도, 컨텍스트 레시피는 다르다.
그래서 full context를 각각 새로 올릴 수 있다.

특히 아래가 흔한 원인이다.

- `@SpringBootTest(properties = ...)` 값을 클래스마다 조금씩 다르게 적는다
- `@TestPropertySource(properties = ...)`의 inline 문자열 스타일이 섞인다
- `@DynamicPropertySource`를 base class에 두고 하위 클래스마다 다른 값을 만든다

### 자주 헷갈리는 포인트

| 오해 | 실제로는 |
|---|---|
| 값이 한 개뿐이면 cache에 거의 영향이 없다 | 값 한 개 차이도 레시피 차이다 |
| inline property는 의미만 같으면 같은 취급이다 | 문자열 선언 차이도 cache 재사용에 영향을 줄 수 있다 |
| 동적 값은 어차피 테스트용이니 신경 안 써도 된다 | 동적 값도 컨텍스트 분리에 영향을 줄 수 있다 |

### 먼저 할 질문

1. 클래스마다 다른 property가 정말 필요하나?
2. 공통 테스트 설정 파일이나 공통 base 설정으로 묶을 수 있나?
3. 런타임 값이 필요한 상황인지, 그냥 고정값을 너무 많이 흩뿌린 것인지 구분했나?

property override 자체보다 더 중요한 질문은 이것이다.

> 이 값 차이가 정말 "다른 컨텍스트"를 만들 만큼 본질적인 차이인가?

그렇지 않다면 설정이 지나치게 분산된 것일 수 있다.

---

## 3. `@DirtiesContext` split: 느린 이유가 의도된 것일 수도 있다

`@DirtiesContext`는 이름 그대로 현재 컨텍스트를 "더럽혀졌다"고 표시하고 캐시에서 버리게 만든다.

즉 이 annotation은 버그가 아니라, **재사용을 포기하는 명시적 선언**이다.

```java
@SpringBootTest
@DirtiesContext
class ContextResetTest {
}
```

그래서 `@DirtiesContext`가 붙은 테스트 주변이 느리다면, 그건 이상 현상이 아니라 **설계상 그렇게 만든 결과**일 수 있다.

### 언제 정말 필요할까

- 테스트가 singleton bean의 내부 상태를 직접 바꾼다
- static/shared state가 컨텍스트와 강하게 엮여 있다
- dynamic property 상속 구조 때문에 하위 클래스마다 분리된 컨텍스트가 꼭 필요하다

### 자주 잘못 붙는 경우

- 데이터 정리가 귀찮아서 습관적으로 붙인다
- mock/stub reset 대신 컨텍스트 전체를 버린다
- 실제 문제는 DB 데이터 오염인데 컨텍스트 오염으로 오해한다

### 초보자 triage

| 질문 | `예`면 | `아니오`면 |
|---|---|---|
| bean 정의나 singleton 상태 자체를 테스트가 바꾸는가? | `@DirtiesContext`가 필요할 수 있다 | 다른 정리 방법을 먼저 본다 |
| 문제의 범위가 DB row/fixture 정리인가? | 트랜잭션 rollback, fixture reset을 먼저 검토한다 | 컨텍스트 문제일 가능성을 본다 |
| 하위 클래스마다 truly different dynamic property가 필요한가? | class 단위 분리가 맞을 수 있다 | 공통 컨텍스트 재사용 쪽이 낫다 |

핵심은 "`@DirtiesContext`를 지워라"가 아니라, **왜 캐시를 버려야 하는지 설명할 수 있어야 한다**는 점이다.

---

## 4. Slice drift: 원래 가벼워야 할 테스트가 점점 무거워진다

slice drift는 `@WebMvcTest`, `@DataJpaTest` 같은 테스트가 원래 경계를 잃고 점점 커지는 상황을 말한다.

대표적으로 이런 흐름이다.

1. 처음에는 `@WebMvcTest` 하나였다
2. 필요한 bean이 없어서 `@Import`를 추가했다
3. security/filter/config를 계속 더했다
4. 어느새 service, DB, 외부 설정까지 따라오기 시작했다

그러면 이름은 slice test인데 실제로는 **작지 않은 partial integration test**가 된다.

### 흔한 예

```java
@WebMvcTest(OrderController.class)
@Import(AppSecurityConfig.class)
class OrderControllerTest {
}
```

이 imported config가 다른 설정과 bean graph를 계속 끌어오면, 테스트는 더 이상 "controller 계약만 보는 빠른 slice"가 아니다.

### slice drift의 신호

- `@WebMvcTest`인데 mock 수가 계속 늘어난다
- DB bean, JPA bean, security bean을 계속 추가로 맞춰야 한다
- "그냥 `@SpringBootTest`로 바꾸자"는 말이 자주 나온다

### 이때 결정할 것

| 선택 | 언제 맞나 |
|---|---|
| slice를 다시 작게 줄인다 | controller/repository 같은 특정 레이어 계약만 보고 싶을 때 |
| 통합 테스트로 명시적으로 올린다 | 여러 레이어 wiring을 정말 같이 검증해야 할 때 |

중간 상태로 오래 두는 것이 가장 비싸다.
느리고, 이해하기 어렵고, cache도 잘 재사용되지 않기 때문이다.

---

## 5. 10분 triage 순서

느린 테스트를 처음 받았을 때는 아래 순서로 보면 된다.

1. 느린 클래스들이 `@SpringBootTest`인지 slice test인지 먼저 분류한다.
2. 비슷한 테스트들끼리 `@MockBean` 목록이 제각각인지 본다.
3. 클래스별 property override가 조금씩 다른지 본다.
4. `@DirtiesContext`가 붙은 클래스와 base class를 찾는다.
5. slice test인데 `@Import`, `@TestConfiguration`, security/filter 설정이 계속 붙었는지 본다.
6. 마지막에만 "테스트 로직 자체가 무거운가"를 본다.

이 순서를 추천하는 이유는, 실제로는 assertion보다 **컨텍스트 startup 반복 비용**이 더 큰 경우가 많기 때문이다.

---

## 6. 흔한 혼동 정리

| 혼동 | 바로잡기 |
|---|---|
| `@MockBean`은 실제 bean을 안 쓰니 무조건 빠르다 | 클래스마다 mock 조합이 달라지면 전체 스위트는 더 느려질 수 있다 |
| property override는 테스트 편의 기능일 뿐 성능과는 별개다 | override 차이도 cache split의 대표 원인이다 |
| `@DirtiesContext`는 안전한 기본값이다 | 안전할 수는 있어도, 재사용을 포기하는 비싼 선택이다 |
| slice test에 설정을 조금씩 더하는 것은 harmless하다 | 계속 쌓이면 slice drift가 생겨 작은 테스트의 장점이 사라진다 |

---

## 7. 한 장 결론

느린 Spring 테스트를 볼 때는 아래처럼 기억하면 된다.

```text
느리다
-> 컨텍스트를 매번 다시 띄우는가?
-> 왜 레시피가 달라졌는가?
   - @MockBean 조합 차이
   - property override 차이
   - @DirtiesContext 사용
   - slice drift
```

즉 triage의 핵심은 "무엇이 cache split을 만들었는가"를 찾는 것이다.
원인을 이 네 축으로 먼저 분리하면, 그다음에야 공통 설정 정리, test slice 재설계, `@DirtiesContext` 축소 같은 개선 방향이 명확해진다.

## 꼬리질문

> Q: `@MockBean`이 있는데도 테스트 스위트 전체는 왜 느려질 수 있나?
> 의도: 클래스별 mock 조합과 cache split 연결 확인
> 핵심: mock이 많아서가 아니라, 테스트마다 mock 레시피가 달라져 컨텍스트 재사용이 끊길 수 있기 때문이다.

> Q: property 값 하나만 다른데도 왜 느려질 수 있나?
> 의도: context cache가 "비슷함"이 아니라 "같은 레시피"를 본다는 점 확인
> 핵심: 값 하나 차이도 다른 컨텍스트로 이어질 수 있다.

> Q: `@DirtiesContext`는 언제 붙이는가?
> 의도: 캐시 포기와 실제 필요 구분 확인
> 핵심: bean 상태나 컨텍스트 자체를 바꾸는 테스트처럼 재사용이 위험할 때만 붙인다.

> Q: slice drift가 왜 문제인가?
> 의도: 느림과 테스트 계약 모호화 연결 확인
> 핵심: 원래 작고 빠른 slice가 애매한 준통합 테스트로 커지면 느리고 이해도 어려워진다.

## 한 줄 정리

Spring 테스트가 느릴 때는 "테스트 로직이 무겁다"보다 먼저 "거의 같은 컨텍스트를 여러 벌 다시 띄우고 있나"를 보고, 특히 `@MockBean`, property override, `@DirtiesContext`, slice drift 네 축부터 분리하면 원인이 빨리 보인다.

---
schema_version: 3
title: JUnit5 Callback Model vs Classic xUnit Template Skeleton
concept_id: design-pattern/junit5-callback-model-vs-classic-xunit-template-skeleton
canonical: true
category: design-pattern
difficulty: beginner
doc_role: bridge
level: beginner
language: ko
source_priority: 81
mission_ids: []
review_feedback_tags:
- junit5-callback
- template-method
- test-lifecycle
- fixture-design
aliases:
- junit5 callback model
- junit 5 callback model
- junit5 beforeeach aftereach
- junit 5 beforeeach aftereach
- classic xunit template skeleton
- beforeeach aftereach reading order
- junit5 callback order confusion
- junit5 extension callback
- JUnit5 콜백 모델
- BeforeEach AfterEach 순서
symptoms:
- JUnit 5의 @BeforeEach, @AfterEach, @ExtendWith를 classic xUnit setUp tearDown override와 완전히 같은 구조로 본다
- 여러 BeforeEach와 extension callback 순서를 읽지 못해 테스트 fixture가 어디서 준비되는지 헷갈린다
- hook에 assertion이나 핵심 의도가 숨어 테스트 본문만 읽어서는 무엇을 검증하는지 알기 어렵다
intents:
- comparison
- definition
- troubleshooting
prerequisites:
- design-pattern/template-method
- design-pattern/template-method-framework-lifecycle-examples
- design-pattern/composition-over-inheritance-practical
next_docs:
- design-pattern/template-hook-smells
- software-engineering/testing-strategy-and-test-doubles
- software-engineering/test-strategy-basics
linked_paths:
- contents/design-pattern/template-method-framework-lifecycle-examples.md
- contents/design-pattern/template-method.md
- contents/design-pattern/template-hook-smells.md
- contents/design-pattern/composition-over-inheritance-practical.md
- contents/software-engineering/testing-strategy-and-test-doubles.md
- contents/software-engineering/test-strategy-basics.md
confusable_with:
- design-pattern/template-method
- design-pattern/template-method-framework-lifecycle-examples
- design-pattern/template-hook-smells
- design-pattern/composition-over-inheritance-practical
forbidden_neighbors: []
expected_queries:
- JUnit 5 @BeforeEach @AfterEach와 classic xUnit setUp tearDown template skeleton은 어떻게 달라?
- JUnit5 extension callback model을 Template Method라고만 부르면 과한 이유가 뭐야?
- multiple BeforeEach AfterEach order가 헷갈릴 때 test body와 fixture hook을 어떻게 읽어야 해?
- 테스트 hook이 길어져 본문 assertion이 안 보이면 fixture helper로 어떻게 접어야 해?
- classic runBare setUp test tearDown skeleton과 JUnit5 annotation callback composition을 비교해줘
contextual_chunk_prefix: |
  이 문서는 JUnit5 Callback Model vs Classic xUnit Template Skeleton bridge로,
  classic xUnit runBare/setUp/test/tearDown inheritance skeleton과 JUnit 5 annotation,
  extension callback composition, fixture hook order를 비교해 Template Method와 callback 모델의 차이를 설명한다.
---
# JUnit 5 Callback Model vs Classic xUnit Template Skeleton

> 한 줄 요약: classic xUnit의 `runBare -> setUp/test/tearDown`는 템플릿 스켈레톤으로 읽기 쉽지만, JUnit 5의 `@BeforeEach` / `@AfterEach`와 extension API는 **상속 기반 skeleton 하나**보다 **annotation + callback composition**에 더 가깝다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md)
> - [템플릿 메소드 패턴](./template-method.md)
> - [Template Hook Smells](./template-hook-smells.md)
> - [Composition over Inheritance](./composition-over-inheritance-practical.md)

retrieval-anchor-keywords: junit 5 callback model, junit5 callback model, junit 5 beforeeach aftereach, junit5 beforeeach aftereach, multiple beforeeach order, multiple aftereach order, junit5 callback order confusion, beforeeach aftereach pairing misconception, junit 5 callback reading order card, junit5 callback reading order card, beforeeach aftereach 5 line card, beforeeach aftereach reading order, multiple beforeeach aftereach minimize, junit5 multiple beforeeach aftereach beginner, junit5 callback model vs classic xunit template skeleton basics

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

### 초미니 매핑표: hook 슬롯 vs 테스트 본문 슬롯

테스트 문맥에서 먼저 이 두 칸만 분리하면 읽기가 쉬워진다.

| 구분 | classic xUnit | JUnit 5 대응 | 한 줄 의미 |
|---|---|---|---|
| hook 슬롯 (준비/정리) | `setUp()` / `tearDown()` | `@BeforeEach` / `@AfterEach` | test 본문 바깥에서 fixture를 준비/정리 |
| 핵심 슬롯 (검증 본문) | `testMethod()` | `@Test` 메서드 본문 | 실제 행동 실행 + assertion이 들어가는 중심 |

자주 헷갈리는 지점:

- `@BeforeEach`가 있어도 그것이 test의 "핵심"은 아니다. 핵심은 `@Test` 본문이다.
- hook은 재사용 도구이고, 테스트의 의도(무엇을 검증하는지)는 본문 assertion에서 드러나야 한다.
- hook이 길어져 본문이 빈약해지면, fixture helper/object로 분리하는 편이 읽기 쉽다.

테스트 본문 중심 작성 3줄 체크리스트:

- `@Test` 본문 한 화면에서 `행동 1개 + 핵심 assertion 1~2개`가 바로 보이는가?
- `@BeforeEach`/`@AfterEach`가 없어도 "무엇을 검증하는 테스트인지"를 본문만 읽어 설명할 수 있는가?
- 본문 assertion 없이 hook 로그/상태 세팅만 길어졌다면, hook을 helper로 내리고 assertion을 본문으로 다시 올렸는가?

### 짧은 before/after: fixture가 길어질 때는 helper/object로 접는다

멘탈 모델은 단순하다.
`@BeforeEach`는 "준비를 다 적는 곳"보다 **준비를 한 줄로 호출하는 곳**에 가깝게 유지하면 읽기 쉽다.

## 2. JUnit 5에서 `@BeforeEach` / `@AfterEach`는 어디에 들어가나 (계속 2)

| 형태 | 읽는 사람이 먼저 보는 것 | 초보자에게 왜 쉬운가 |
|---|---|---|
| 긴 `@BeforeEach` | setup 절차 5~6줄 | 무엇을 검증하는 테스트인지 본문보다 setup를 먼저 해석하게 된다 |
| helper/object로 분리한 `@BeforeEach` | `fixture = PaymentFixture.readyOrder()` | "준비 완료된 상태"라는 이름이 먼저 보여 의도를 빨리 읽을 수 있다 |

Before:

```java
class PaymentServiceTest {
    private PaymentService service;
    private Order order;
    private FakeGateway gateway;

    @BeforeEach
    void setUp() {
        gateway = new FakeGateway();
        service = new PaymentService(gateway);
        order = new Order("order-1", 12000);
        gateway.willApprove(order.id());
    }

    @Test
    void approves_payment() {
        Receipt receipt = service.pay(order);

        assertThat(receipt.status()).isEqualTo(APPROVED);
    }
}
```

After:

## 2. JUnit 5에서 `@BeforeEach` / `@AfterEach`는 어디에 들어가나 (계속 3)

```java
class PaymentServiceTest {
    private PaymentFixture fixture;

    @BeforeEach
    void setUp() {
        fixture = PaymentFixture.readyOrder();
    }

    @Test
    void approves_payment() {
        Receipt receipt = fixture.service().pay(fixture.order());

        assertThat(receipt.status()).isEqualTo(APPROVED);
    }
}

final class PaymentFixture {
    private final FakeGateway gateway = new FakeGateway();
    private final PaymentService service = new PaymentService(gateway);
    private final Order order = new Order("order-1", 12000);

    static PaymentFixture readyOrder() {
        PaymentFixture fixture = new PaymentFixture();
        fixture.gateway.willApprove(fixture.order.id());
        return fixture;
    }

    PaymentService service() { return service; }
    Order order() { return order; }
}
```

여기서 핵심은 "새 패턴을 크게 도입했다"가 아니다.

- `@BeforeEach`가 fixture 조립 상세 대신 **의미 있는 이름 1개**만 남기게 했다
- 테스트 본문이 `approve` 검증으로 다시 앞으로 나왔다
- setup 절차가 더 길어지면 test class가 아니라 `PaymentFixture`를 먼저 정리하면 된다

### 예시 하나 더: helper로 접은 뒤에는 본문 assertion을 더 구체적으로 남긴다

초보자가 자주 놓치는 지점은 여기다.
hook-heavy 테스트를 helper로 줄였는데, 정작 `@Test` 본문은 여전히 `status == APPROVED` 한 줄만 남아 있을 수 있다.

그럴 때는 setup만 줄이는 데서 멈추지 말고, **테스트 이름이 말한 규칙**을 assertion으로 다시 올리면 읽기가 훨씬 좋아진다.

| 버전 | `@BeforeEach` 역할 | `@Test` 본문이 말해 주는 것 |
|---|---|---|
| refactor 전 | 객체 조립과 승인 준비를 자세히 나열 | "성공했다" 정도만 보임 |
| refactor 후 | `fixture = PaymentFixture.readyApprovedOrder()` 한 줄 | `승인 상태`와 `승인된 주문 id`까지 바로 보임 |

Before:

## 2. JUnit 5에서 `@BeforeEach` / `@AfterEach`는 어디에 들어가나 (계속 4)

```java
class PaymentServiceTest {
    private PaymentService service;
    private Order order;
    private FakeGateway gateway;

    @BeforeEach
    void setUp() {
        gateway = new FakeGateway();
        service = new PaymentService(gateway);
        order = new Order("order-1", 12000);
        gateway.willApprove(order.id());
    }

    @Test
    void approves_payment_for_ready_order() {
        Receipt receipt = service.pay(order);

        assertThat(receipt.status()).isEqualTo(APPROVED);
    }
}
```

After:

```java
class PaymentServiceTest {
    private PaymentFixture fixture;

    @BeforeEach
    void setUp() {
        fixture = PaymentFixture.readyApprovedOrder();
    }

    @Test
    void approves_payment_for_ready_order() {
        Receipt receipt = fixture.service().pay(fixture.order());

        assertThat(receipt.status()).isEqualTo(APPROVED);
        assertThat(receipt.orderId()).isEqualTo("order-1");
    }
}
```

읽는 포인트는 단순하다.

- helper는 "어떤 상태로 준비됐는가"를 이름으로 보여 준다
- assertion은 "그래서 무엇이 보장돼야 하는가"를 본문에서 바로 보여 준다
- 즉 `setup 상세는 helper로`, `검증 의도는 본문으로` 다시 분리한 것이다

자주 하는 오해:

- helper/object로 뺐다고 해서 무조건 복잡해지는 것은 아니다. setup가 4~5줄을 넘고 반복 의미가 있으면 오히려 더 빨리 읽힌다.
- fixture object는 "테스트용 조립기"이지, production pattern을 억지로 늘리는 작업이 아니다.
- helper로 옮긴 뒤에도 assertion까지 helper 안에 숨기면 다시 읽기 어려워진다. assertion은 여전히 `@Test` 본문에 남기는 편이 낫다.
- helper로 접었다고 끝이 아니다. 테스트 이름에 `approved`, `rejected`, `expired` 같은 규칙 단어가 있다면, 본문 assertion도 그 규칙을 최소 1개 더 직접 보여 주는 편이 좋다.

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

짧은 예시:

## 3. 그런데 왜 modern JUnit 5 전체를 classic Template Method라고 부르면 과한가 (계속 2)

```java
class PaymentServiceTest {
    @BeforeEach
    void createTempUser() { log("before:createTempUser"); }

    @BeforeEach
    void openTx() { log("before:openTx"); }

    @AfterEach
    void rollbackTx() { log("after:rollbackTx"); }

    @AfterEach
    void deleteTempUser() { log("after:deleteTempUser"); }

    @Test
    void approvePayment() { log("test:approvePayment"); }
}
```

실행 로그를 보면(요약):

```text
before:createTempUser
before:openTx
test:approvePayment
after:deleteTempUser
after:rollbackTx
```

읽는 순서 카드 5줄:

```text
1. 여러 `@BeforeEach`를 위에서 아래로 한 번 읽는다.
2. 가운데 `@Test` 본문을 핵심으로 읽는다.
3. 여러 `@AfterEach`를 따로 읽는다.
4. `before A -> after A`처럼 자동 짝을 짓지 않는다.
5. 헷갈리면 "before 목록 / test / after 목록" 세 덩어리로만 기억한다.
```

여기서 초보자가 자주 하는 오해:

- `openTx`와 `rollbackTx`가 한 쌍으로 "자동 매칭"된다고 가정한다
- `createTempUser`와 `deleteTempUser`도 별도 쌍이라고 가정한다
- 그런데 실제 순서는 "여러 before 목록 + 여러 after 목록"으로 실행되어 본문 의도(무엇을 검증하는 테스트인지)보다 lifecycle 퍼즐 해석에 시간이 든다

### 30초 규칙 카드: 여러 lifecycle method를 1쌍으로 줄여도 되는가

먼저 멘탈 모델부터 고정하면 쉽다.

- `@BeforeEach`는 "이번 테스트에 꼭 필요한 준비 1곳"
- `@AfterEach`는 "정말 남는 자원 정리 1곳"
- 나머지는 가능하면 helper/factory/fake 안으로 접는다

## 3. 그런데 왜 modern JUnit 5 전체를 classic Template Method라고 부르면 과한가 (계속 3)

| 보이면 | 먼저 의심할 점 | 초보자용 기본 선택 |
|---|---|---|
| `@BeforeEach`가 2개 이상 | 준비 순서를 독자가 퍼즐처럼 맞춰야 하나? | 가능하면 **하나로 합치고** 내부에서 helper 메서드를 호출 |
| `@AfterEach`가 2개 이상 | 어떤 정리가 어떤 준비와 묶이는지 헷갈리나? | 가능하면 **하나로 합치고** 정리 책임을 한곳에 모음 |
| before/after가 서로 "짝"처럼 보임 | JUnit이 pair를 보장한다고 착각하나? | pair 기대를 버리고 **before 1개 / after 1개**로 단순화 |
| 긴 fixture 조립 코드가 hook에 몰림 | 본문보다 setup 해석이 더 오래 걸리나? | fixture helper/object로 이동 |
| assertion이 약하고 hook만 길다 | 테스트 의도가 본문에 안 보이나? | hook은 줄이고 assertion을 본문에 다시 올림 |

짧은 규칙만 기억하면 된다.

```text
1. 기본값은 `@BeforeEach` 1개 + `@AfterEach` 1개다.
2. 둘 이상이면 "정말 분리해야 하나?"부터 의심한다.
3. 준비 상세는 helper/factory/fake로 숨기고 hook에는 이름만 남긴다.
4. 정리는 한 군데에서 끝내고 자동 pair 기대는 버린다.
5. 테스트 의도는 hook이 아니라 `@Test` 본문 assertion에서 보이게 한다.
```

비교를 한 번 보면 더 바로 읽힌다.

| 형태 | 처음 읽는 사람이 받는 인상 | beginner-friendly 판단 |
|---|---|---|
| `@BeforeEach` 2개 + `@AfterEach` 2개 | "어느 준비가 어느 정리와 연결되지?" | 줄일 수 있으면 줄이는 편이 낫다 |
| `@BeforeEach` 1개 + `@AfterEach` 1개 | "준비 한 덩어리, 정리 한 덩어리" | 기본 선택으로 가장 읽기 쉽다 |
| hook 1쌍 + helper/object | "준비 완료 상태 이름이 먼저 보인다" | 본문 의도까지 같이 살아남아 가장 안정적이다 |

예를 들어 아래 둘은 동작은 비슷해도 읽기 난이도가 다르다.

Before:

```java
class PaymentServiceTest {
    @BeforeEach
    void createTempUser() { ... }

    @BeforeEach
    void openTx() { ... }

    @AfterEach
    void rollbackTx() { ... }

    @AfterEach
    void deleteTempUser() { ... }
}
```

After:

## 3. 그런데 왜 modern JUnit 5 전체를 classic Template Method라고 부르면 과한가 (계속 4)

```java
class PaymentServiceTest {
    @BeforeEach
    void setUp() {
        fixture = PaymentFixture.readyUserInTransaction();
    }

    @AfterEach
    void tearDown() {
        fixture.cleanUp();
    }
}
```

핵심 차이는 이것이다.

- before/after 개수를 줄여 **읽는 순서를 단순화**했다
- 준비/정리 상세는 `fixture` 안으로 보내 **이름으로 상태를 읽게** 했다
- 테스트 본문은 다시 "무엇을 검증하는가"에 집중할 수 있게 됐다

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

### 왜 `@ExtendWith`가 들어오면 순서 추론이 더 어려워지나

멘탈 모델은 단순하다.
`@BeforeEach` / `@AfterEach`만 있을 때는 "내 테스트 클래스 안의 준비/정리 목록"을 읽으면 된다.
하지만 `@ExtendWith`가 붙으면 **클래스 바깥 extension도 같은 실행 구간에 끼어들 수 있어서**, 코드가 한 파일 안에 다 보이지 않는다.

| 상황 | 초보자가 머릿속에서 그리는 그림 | 실제로 순서 추론이 어려워지는 이유 |
|---|---|---|
| `@BeforeEach` / `@AfterEach`만 있음 | "이 클래스 안의 before 목록 -> test -> after 목록" | 같은 파일만 읽어도 대체 흐름을 거의 볼 수 있다 |
| `@ExtendWith` + callback extension 있음 | "before/after 앞뒤에 바깥 코드도 감쌀 수 있음" | `BeforeEachCallback`, `AfterEachCallback`, interceptor가 끼어들어 한 클래스만 보고는 전체 순서를 확정하기 어렵다 |
| extension이 여러 개 겹침 | "Extension A, B가 각각 전후 처리" | 등록 순서, wrapping 관계, 각 extension의 역할을 함께 읽어야 해서 `before A`와 `after A`를 직관적으로 짝짓기 더 어렵다 |
| `ParameterResolver` / `InvocationInterceptor`까지 있음 | "준비/정리만 추가"라고 생각하기 쉽다 | 단순 전후 hook이 아니라 파라미터 주입과 호출 감싸기까지 생겨서, 템플릿 빈칸보다 실행 프로토콜에 가깝게 바뀐다 |

한 줄로 줄이면:

- `@BeforeEach`만 보면 "내 클래스의 lifecycle slot"을 읽으면 되지만
- `@ExtendWith`가 붙는 순간 "엔진이 외부 callback들을 어떤 wrapper로 끼워 넣는가"까지 같이 봐야 한다

짧게 말하면:

- **classic xUnit**: template skeleton이 중심
- **JUnit 5**: lifecycle callback composition이 중심

## 4. 어디까지는 템플릿 메소드 감각으로 읽어도 되는가 (계속 2)

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

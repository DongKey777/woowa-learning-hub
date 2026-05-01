---
schema_version: 2
title: "@Transactional 기초: 트랜잭션 어노테이션이 하는 일"
concept_id: "spring/transactional-basics"
difficulty: beginner
doc_role: primer
level: beginner
aliases:
  - Transactional
  - @Transactional
  - Spring transaction
  - 트랜잭션 어노테이션
  - transactional proxy
expected_queries:
  - Transactional이 뭐야?
  - Spring에서 transaction이 뭐야?
  - 왜 Transactional이 안 먹어?
  - self invocation이면 왜 트랜잭션이 안 걸려?
acceptable_neighbors:
  - contents/spring/spring-self-invocation-transactional-only-misconception-primer.md
  - contents/spring/spring-transaction-debugging-playbook.md
  - contents/spring/aop-proxy-mechanism.md
  - contents/spring/transactional-deep-dive.md
companion_neighbors:
  - contents/spring/spring-persistence-transaction-web-service-repository-primer.md
---

# @Transactional 기초: 트랜잭션 어노테이션이 하는 일

> 한 줄 요약: `@Transactional`은 메서드 실행을 하나의 트랜잭션으로 묶어 주는 어노테이션이고, 실제 동작은 Spring이 생성한 프록시가 메서드 호출 전후로 begin/commit/rollback을 대신 처리하는 것이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md)
- [Spring 테스트 기초: @SpringBootTest부터 슬라이스 테스트까지](./spring-testing-basics.md)
- [AOP 기초: 관점 지향 프로그래밍이 왜 필요한가](./spring-aop-basics.md)
- [Spring Persistence / Transaction Mental Model Primer](./spring-persistence-transaction-web-service-repository-primer.md)
- [트랜잭션 기초](../database/transaction-basics.md)

retrieval-anchor-keywords: transactional basics, spring transaction beginner, spring 트랜잭션이 뭐예요, transactional 처음, 왜 @transactional이 안 먹어요, transactional 왜 안 먹어요, spring proxy transaction, begin commit rollback spring, transactional rollback default, transactional 내부 호출, transactional proxy bypass, 프록시 경로 먼저, bean public external call, transactional service method 어디에 붙여요, transactional self invocation beginner
retrieval-anchor-keywords: 스프링 transaction이 뭐야, spring transaction이 뭐야, spring transaction what is, spring transaction meaning beginner, transactional annotation beginner, spring transactional primer, transaction in spring beginner

## beginner 정지선

> `@Transactional` 옵션을 바꾸기 전에 먼저 확인할 것:
> 호출이 "프록시를 통과했는지"가 1순위다.

이 문서는 "`트랜잭션 옵션을 바꿔야 하나?`"로 들어가기 전에, 먼저 **트랜잭션이 어디서 시작되는지**를 잡는 beginner 입구다.

- 이 단계에서 먼저 잡을 것: "`요청 하나`와 `트랜잭션 하나`는 같은 말이 아니다", "`public` service 진입점을 프록시가 감싼다".
- 이 문서의 중심이 아닌 것: `propagation`, `isolation`, `rollback-only`, `REQUIRES_NEW`, 동시성 사례, test slice 세부 비교.
- 위 단어가 먼저 보이면 지금은 링크만 저장하고, 이 문서에서는 "`어디서 시작하나`"와 "`왜 안 먹나`" 두 질문까지만 끝내는 편이 낫다.
- `AOP`도 여기서는 새 축이 아니라 "`왜 프록시가 필요한가`"를 설명하는 보조 단어 정도로만 잡는다.

## 처음 30초 결론

- `@Transactional`은 service `public` 메서드 경계에 begin/commit/rollback을 붙이는 Spring 프록시 규칙이다.
- "`왜 안 먹어요?`"가 먼저 보이면 옵션보다 `this.method()`, `private`, 직접 `new`부터 확인한다.
- `REQUIRES_NEW`, `rollback-only`, `격리수준`, 테스트 rollback 착시는 이 문서의 끝이 아니라 다음 단계 링크다.

## `@Transactional`과 AOP를 한 문장으로 묶기

처음엔 `AOP`가 새 주제처럼 보여도, 이 문서에서는 "`@Transactional`을 메서드 앞뒤에 붙여 주는 전달 방식" 정도로만 이해하면 충분하다.

| 지금 들은 말 | 초급자용 번역 | 여기서 바로 안 파는 것 |
|---|---|---|
| "`AOP`" | 공통 코드를 메서드 앞뒤에 붙이는 방식 | `Advice`, `Pointcut` 세부 문법 |
| "`프록시`" | 진짜 service 앞에서 begin/commit/rollback을 대신 붙여 주는 문지기 | JDK/CGLIB 차이 |
| "`self-invocation`" | 같은 클래스 안에서 `this.method()`로 불러 문지기를 우회한 상태 | 우회 패턴 비교 |

짧게 외우면 "`@Transactional`은 트랜잭션 규칙이고, AOP/프록시는 그 규칙을 전달하는 방식"이다.

## 비유는 여기까지만 맞다

`문지기` 비유는 입문용으로는 유용하지만, "`메서드 몸체가 바뀌었다`"거나 "`annotation이 붙은 곳이면 어디서 불러도 항상 같은 효과가 난다`"까지 뜻하지는 않는다.

| 비유가 도와주는 지점 | 여기서 끊어야 하는 오해 |
|---|---|
| "`메서드 앞뒤에 공통 동작이 붙는다`" | 실제 메서드 코드가 직접 바뀌는 것은 아니다 |
| "`프록시를 지나면 begin/commit/rollback이 붙는다`" | 같은 클래스 내부 호출까지 자동으로 다 잡아 주는 것은 아니다 |
| "`service 앞에 한 겹이 더 있다`" | `private`, 직접 `new`, 내부 호출까지 모두 같은 방식으로 적용된다는 뜻은 아니다 |

그래서 beginner 기준 첫 확인 순서는 "`Bean인가?` -> `public` 진입 메서드인가? -> 다른 Bean에서 외부 호출로 들어왔는가?"다.

## 처음엔 여기까지만 끝내도 된다

| 지금 보이는 말 | 지금 문서에서 끝낼 답 | 더 깊게 볼 때만 여는 문서 |
|---|---|---|
| "`트랜잭션이 어디서 시작돼요?`" | service `public` 진입점에서 프록시가 begin/commit/rollback을 붙인다 | [Spring Persistence / Transaction Mental Model Primer](./spring-persistence-transaction-web-service-repository-primer.md) |
| "`왜 `@Transactional`이 안 먹어요?`" | `this.method()`, `private`, 직접 `new`를 먼저 본다 | [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md) |
| "`전파`, `격리수준`, `rollback-only`가 궁금해요" | beginner 범위를 넘는 follow-up이다 | [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md), [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md) |

## 처음엔 이 2문장만 기억한다

- `@Transactional`은 service 메서드 앞뒤에 begin/commit/rollback을 붙이는 프록시 규칙이다.
- "`왜 `@Transactional`이 안 먹어요?`"가 먼저 보이면 옵션보다 호출 경로부터 본다.

## 주문 예시로 10초만에 위치 잡기

초급자는 용어보다 "`한 요청에서 어디 장면을 보고 있나`"를 먼저 붙이면 덜 헷갈린다.

| 같은 `POST /orders` 장면 | 지금 붙일 이름 | 여기서 바로 할 질문 |
|---|---|---|
| controller가 `placeOrder()`를 부른다 | 요청 처리 | "`컨트롤러까지는 정상 진입했나?`" |
| service 진입 직전에 프록시가 선다 | 트랜잭션 시작 경계 | "`외부 호출로 프록시 정문을 지났나?`" |
| `orderRepository.save()`와 `paymentRepository.save()`가 묶인다 | DB 작업 묶기 | "`어디까지 같이 commit/rollback하나?`" |

즉 "`요청이 왔다`"와 "`트랜잭션이 열렸다`"는 보통 같은 문장이 아니라, 한 요청 안의 다른 장면이다.

## 요청, DI, 트랜잭션을 같은 말로 묶지 않는다

처음 막히는 지점은 보통 "`POST /orders` 요청이 왔다"와 "`트랜잭션이 열렸다`"를 같은 사건처럼 보는 데서 시작한다. beginner는 아래 세 칸만 분리해도 훨씬 덜 헷갈린다.

| 지금 보는 장면 | 먼저 붙일 이름 | 첫 질문 |
|---|---|---|
| URL이 controller까지 갔나 | MVC | "`요청이 어디서 끊겼지?`" |
| controller 안 `OrderService`가 왜 있나 | Bean + DI | "`누가 이 객체를 넣어 줬지?`" |
| `save()` 둘을 같이 commit/rollback하나 | 트랜잭션 경계 | "`어디까지 한 묶음이지?`" |

짧게 말하면 요청은 MVC가 받고, 객체 연결은 DI가 미리 끝내고, DB 작업 묶음은 `@Transactional`이 service 경계에서 정한다.

## 먼저 갈 문서부터 고른다

처음에는 `@Transactional`, test slice, 요청 바인딩, AOP가 한 화면에 같이 떠도 전부 한 문제로 묶지 않는 편이 빠르다. 이 문서는 "`Bean은 있고`, `요청도 들어왔고`, `service 경계에서 묶이는 규칙이 궁금하다`"일 때 여는 입구다.

| 지금 먼저 보인 말 | 먼저 자를 축 | 먼저 읽을 문서 |
|---|---|---|
| "`@WebMvcTest`인데 service bean not found예요" | 무엇을 띄웠나 | [Spring Test Slice Scan Boundary 오해](./spring-test-slice-scan-boundaries.md) |
| "`POST /orders`가 controller 전에 400 나요" | 요청 바인딩 / 파이프라인 | [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md) |
| "`왜 new 대신 주입해요?`", "`service`는 누가 넣어 줘요?`" | Bean + DI | [Spring Bean과 DI 기초](./spring-bean-di-basics.md) |
| "`service`는 보이는데 `@Transactional`이 안 먹어요" | 프록시 경계 | 이 문서 |

짧게 외우면 "`무엇을 띄웠나`"는 test slice, "`어떻게 호출했나`"는 트랜잭션 프록시다.

## AOP와 옵션은 여기서 링크만 건넨다

이 문서의 beginner 질문은 두 개뿐이다.

- "`트랜잭션이 어디서 시작돼요?`"
- "`왜 `@Transactional`이 안 먹어요?`"

그래서 아래 단어가 먼저 보여도 본문 중심으로 끌고 오지 않고 follow-up 링크만 건넨다.

| 먼저 보인 단어 | 여기서 내릴 1차 판단 | 다음 문서 |
|---|---|---|
| "`AOP`가 뭐예요?", "`프록시가 왜 나오죠?`" | 공통 코드를 메서드 앞뒤에 붙이는 방식부터 본다 | [AOP 기초](./spring-aop-basics.md) |
| "`this.method()`", "`private`", "`new Foo()`" | 프록시 정문을 우회했는지 먼저 본다 | [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md) |
| "`rollback-only`", `REQUIRES_NEW`, "`전파`" | beginner 옵션 범위를 넘는 follow-up이다 | [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md) |
| "`격리수준`", "`동시에 요청이 오면요?`" | Spring 프록시보다 DB 동시성 질문에 가깝다 | [트랜잭션 격리 수준 기초](../database/transaction-isolation-basics.md) |
| "`SQL`, `flush`, `JPA`는 어디서 봐요?`" | 트랜잭션 자체보다 persistence 흐름 질문이다 | [Database First-Step Bridge](../database/database-first-step-bridge.md) |

짧게 말하면 이 문서는 "service 메서드 경계를 Spring 프록시가 묶는다"까지만 잡고, 운영어와 심화 옵션은 링크 뒤로 미룬다.

## beginner-safe 다음 한 걸음

`@Transactional`이 처음인데 `rollback-only`, `REQUIRES_NEW`, `격리수준`, `self-invocation`까지 한 번에 섞이면 아래처럼 **한 장만 더** 내려가는 편이 안전하다.

| 지금 먼저 남은 질문 | 여기서 내릴 1차 판단 | 다음 문서 1장 |
|---|---|---|
| "`왜 같이 commit/rollback해요?`" | Spring 옵션보다 DB transaction 큰 그림이 먼저다 | [트랜잭션 기초](../database/transaction-basics.md) |
| "`service`는 있는데 `@Transactional`이 안 먹어요" | 옵션보다 프록시 경로 확인이 먼저다 | [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md) |
| "`전파`, `REQUIRES_NEW`, `rollback-only`가 왜 나와요?`" | beginner follow-up 한 장만 더 보면 된다 | [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md) |
| "`격리수준`, `동시에 요청이 오면요?`" | Spring 프록시보다 DB 동시성 질문에 가깝다 | [트랜잭션 격리 수준 기초](../database/transaction-isolation-basics.md) |

처음에는 "`실패 범위`는 DB primer, "`적용 경계`는 Spring proxy primer"라고만 분리해도 충분하다. 이 문서에서 멈췄는데 `save()` 뒤 SQL 위치가 더 궁금하면 [Database First-Step Bridge](../database/database-first-step-bridge.md)로, `동시에 마지막 재고가 두 번 팔려요`가 더 궁금하면 [트랜잭션 격리 수준 기초](../database/transaction-isolation-basics.md)로 한 칸만 옮긴다.

## 핵심 개념

`@Transactional`은 "이 메서드를 하나의 트랜잭션으로 실행하라"는 선언이다. 개발자가 직접 `begin`, `commit`, `rollback`을 적지 않아도 Spring이 프록시를 통해 알아서 처리한다.

입문자가 가장 자주 헷갈리는 지점은 어노테이션이 마법처럼 보인다는 것이다. 실제로는 Spring 컨테이너가 `@Transactional`이 붙은 Bean을 프록시 객체로 감싸고, 그 프록시가 메서드 호출 전에 트랜잭션을 시작하고 메서드 종료 후에 commit 또는 rollback을 호출한다.

## 한눈에 보기

```text
외부 -> 프록시(트랜잭션 시작) -> 실제 메서드 실행 -> 프록시(commit 또는 rollback)
```

| 결과 | 여기서 먼저 기억할 것 |
|---|---|
| 메서드 정상 종료 | commit |
| `RuntimeException` 발생 | rollback |
| checked exception, 전파 옵션 | 지금은 follow-up 링크로 넘긴다 |

## 주문 요청 한 장면으로 위치 잡기

`@Transactional`을 처음 볼 때는 옵션 이름보다 "`POST /orders` 한 장면에서 정확히 어디에 붙는가"를 먼저 보는 편이 빠르다.

| 같은 주문 요청에서 보이는 일 | 이걸 담당하는 축 | 초급자용 해석 |
|---|---|---|
| `POST /orders`가 컨트롤러로 들어온다 | MVC | 요청 길찾기다 |
| 컨트롤러가 `OrderService`를 들고 있다 | Bean + DI | 객체 조립은 요청 전에 끝나 있다 |
| `placeOrder()` 앞뒤로 commit/rollback 경계가 생긴다 | `@Transactional` 프록시 | DB 작업 묶기는 service 경계에서 본다 |

이 표를 먼저 잡아 두면 "`요청은 왔는데 rollback이 이상해요`" 같은 말을 볼 때도 MVC, DI, 트랜잭션을 한 덩어리로 섞지 않게 된다.

간단한 예시는 아래처럼 읽으면 된다.

```java
@RestController
class OrderController {
    private final OrderService orderService;

    @PostMapping("/orders")
    void create() {
        orderService.placeOrder();
    }
}

@Service
class OrderService {
    @Transactional
    public void placeOrder() {
        orderRepository.save(...);
        paymentRepository.save(...);
    }
}
```

- controller는 요청을 받는 입구다.
- `OrderService.placeOrder()`는 "주문 생성" 작업 묶음 경계다.
- `orderRepository.save(...)`, `paymentRepository.save(...)`는 같은 트랜잭션 안에서 같이 commit/rollback될 수 있다.

## 요청 하나와 트랜잭션 하나를 같은 말로 보면 꼬인다

입문자가 자주 하는 오해는 "`POST /orders` 요청 한 번 = 트랜잭션 한 번"으로 바로 생각하는 것이다. 실제로는 요청 처리와 트랜잭션 경계가 다른 층위다.

| 지금 보는 장면 | 누가 담당하나 | 초급자용 한 줄 |
|---|---|---|
| URL이 어느 메서드로 들어오나 | `DispatcherServlet` + controller | 요청 길찾기 |
| controller 안 `orderService`가 왜 있나 | Bean 컨테이너 + DI | 객체 연결 |
| DB 저장을 어디까지 같이 commit/rollback 하나 | `@Transactional` 프록시 | 작업 묶기 |

예를 들어 controller가 service를 호출해도, 그 service 메서드에 `@Transactional`이 없으면 요청은 정상 처리되지만 트랜잭션은 기대와 다르게 짧거나 아예 없을 수 있다. 반대로 요청은 하나여도 service 내부에서 여러 repository 작업을 한 트랜잭션으로 묶을 수 있다.

그래서 문제를 볼 때는 순서를 이렇게 잡는 편이 안전하다. "컨트롤러까지 왔나?" 다음에 "프록시를 타고 트랜잭션이 열렸나?"를 본다. 이 감각이 잡히면 `404`, DI 오류, rollback 문제를 한 덩어리로 섞지 않게 된다.

## 요청 1개가 트랜잭션도 꼭 1개라는 뜻은 아니다

beginner 오해를 가장 많이 줄이는 표 하나만 고르면 이 표다. HTTP 요청 횟수와 트랜잭션 개수는 보통 관련은 있지만, 같은 단위는 아니다.

| 장면 | 요청 수 | 트랜잭션 수 감각 | 왜 이렇게 되나 |
|---|---|---|---|
| 조회 controller가 단순 읽기만 하고 트랜잭션 경계를 따로 안 둠 | 1 | 0 또는 프레임워크 기본값에 의존 | 요청은 왔어도 service 경계에 `@Transactional`이 없을 수 있다 |
| `placeOrder()` 하나가 저장 2개를 함께 처리 | 1 | 1 | service `public` 메서드 하나를 작업 묶음 경계로 잡는다 |
| service가 다른 트랜잭션 정책 메서드를 추가로 호출 | 1 | 1 이상으로 달라질 수 있음 | 이때부터는 beginner 범위를 넘는 전파(follow-up) 질문이다 |

즉 "`요청이 하나니까 트랜잭션도 하나겠지`"보다 "`어느 service 경계를 한 묶음으로 봤지`"를 먼저 묻는 편이 안전하다.

## 처음엔 어디에 붙일지만 먼저 고른다

처음 `@Transactional`을 붙일 때는 옵션보다 "`어느 레이어를 작업 묶음 경계로 볼까`"를 먼저 정하는 편이 덜 헷갈린다.

| 붙이는 위치 | beginner 기본값 | 왜 이렇게 보나 |
|---|---|---|
| controller | 기본 시작점으로는 잘 안 쓴다 | 요청 길찾기와 DB 작업 묶음을 한 파일에서 같이 읽게 되어 질문 축이 섞이기 쉽다 |
| service `public` 진입 메서드 | 가장 흔한 시작점 | "주문 생성", "결제 취소" 같은 유스케이스 한 덩어리를 transaction으로 묶기 쉽다 |
| repository 메서드마다 | 입문 기본값으로는 너무 잘게 쪼개지기 쉽다 | 여러 저장 작업을 한 묶음으로 볼지 감각을 잡기 어렵다 |

안전한 첫 선택은 "controller는 요청 입구, service는 작업 묶음 경계"로 나누는 것이다. 그다음에 "`왜 service에서 프록시 이야기가 나오지?`"가 남으면 [AOP 기초](./spring-aop-basics.md)로 이어서 보면 된다.

## 30초 미니 체크: 프록시 정문 3문항

이 문서에서도 `this.method()` / `private` / 직접 `new Foo()`를 같은 이름으로 묶어 **프록시 정문 3문항**이라고 부른다.

먼저 용어보다 이 3문항으로 자가진단하면 된다.

| 질문 | 예 / 아니오 해석 | 지금 기억할 한 줄 |
|---|---|---|
| 같은 클래스 안에서 `this.method()`로 호출했나? | 예면 `@Transactional`이 빠질 수 있다 | 내부 호출은 프록시를 우회한다 |
| annotation을 `private` 메서드에 붙였나? | 예면 기대한 방식으로 적용되지 않는다 | 프록시가 잡는 `public` 진입 메서드로 올린다 |
| 객체를 `new`로 직접 생성했나? | 예면 Spring Bean이 아니라 프록시를 기대하기 어렵다 | 직접 생성 대신 DI 받은 Bean인지 먼저 본다 |

짧은 판단 예시는 아래처럼 보면 된다.

| 코드 한 줄 | 1차 판단 |
|---|---|
| `this.saveOrder();` | 내부 호출부터 의심 |
| `@Transactional private void save()` | `private` 메서드 적용 기대를 버리고 경계를 다시 잡기 |
| `new OrderService()` | Spring Bean이 맞는지부터 다시 보기 |

## 테스트로 확인할 때도 질문 축을 먼저 나눈다

`@Transactional`을 테스트로 확인할 때도, 처음에는 "테스트 종류"와 "프록시 경계"를 같은 말로 보면 금방 꼬인다.

| 지금 테스트에서 보이는 말 | 먼저 의심할 축 | 먼저 읽을 문서 |
|---|---|---|
| "`assertSame`인데 왜 프록시처럼 안 보여요?" | identity 테스트와 동작 테스트를 섞음 | [Spring `@Transactional` Self-invocation 검증 테스트 브리지](./spring-transactional-self-invocation-test-bridge-primer.md) |
| "`@WebMvcTest`에서 service bean이 없어요`" | slice 경계 문제 | [Spring 테스트 기초](./spring-testing-basics.md) |
| "`@DataJpaTest`인데 commit 뒤 동작이 안 보여요" | 기본 rollback slice에서 commit 이후를 기대함 | [Spring 테스트 기초](./spring-testing-basics.md) |
| "`트랜잭션이 안 먹는 것 같은데 this.method()`가 보여요" | 프록시 우회 문제 | [AOP 기초](./spring-aop-basics.md) |

짧게 외우면 이렇다.

- 테스트 어노테이션 선택은 "무엇을 띄울까" 문제다.
- `@Transactional` 적용 여부는 "프록시를 탔나" 문제다.
- 둘이 동시에 보여도 질문 축이 다르므로, 테스트를 바꾸기 전에 호출 경로를 먼저 분리한다.

초급자용 한 줄 복기:

- `service bean not found`면 보통 slice 경계 질문이다.
- "`트랜잭션이 안 먹는다`"면 보통 프록시 경계 질문이다.
- 같은 service 단어가 보여도, **무엇을 띄웠나**와 **어떻게 호출했나**는 다른 질문이다.

## `private`와 내부 호출은 구분만 하고, 원리 설명은 다른 문서로 넘긴다

이 문서에서 필요한 수준은 "둘이 다른 질문"이라는 구분까지다. 프록시가 왜 그렇게 동작하는지까지 깊게 풀면 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md), Bean으로 등록된 객체만 왜 감쌀 수 있는지는 [Spring Bean과 DI 기초](./spring-bean-di-basics.md)에서 이어 보는 편이 retrieval 경쟁을 덜 만든다.

| 보이는 코드 | 지금 여기서 내릴 1차 판단 | 바로 할 일 |
|---|---|---|
| `@Transactional private void save()` | 메서드 경계가 트랜잭션 진입점으로 부적절할 수 있다 | service 진입 메서드로 경계를 올린다 |
| `this.method()` | 호출 경로가 프록시를 우회했을 가능성이 크다 | 다른 Spring Bean 경유 호출로 바꾼다 |
| `new OrderService()` | Bean이 아니라 프록시 적용 자체를 기대하기 어렵다 | Bean 등록 경로부터 다시 본다 |

짧게만 외우면 된다.

- `private`: "어디에 경계를 둘까?" 문제다.
- 내부 호출: "어떻게 그 경계에 들어가나?" 문제다.
- 직접 `new`: "애초에 Spring이 관리하나?" 문제다.

예시는 하나만 보면 충분하다.

```java
@Service
public class OrderFacade {

    private final OrderTxService orderTxService;

    public OrderFacade(OrderTxService orderTxService) {
        this.orderTxService = orderTxService;
    }

    public void placeOrder() {
        orderTxService.saveOrder();
    }
}

@Service
public class OrderTxService {

    @Transactional
    public void saveOrder() {
    }
}
```

핵심은 코드 모양을 외우는 것이 아니라 "트랜잭션 경계는 보통 service의 공개 진입 메서드에 두고, 그 호출은 Spring Bean 바깥쪽 경로에서 들어오게 만든다"는 감각이다.

## 증상 라우팅 카드 (내부 호출/프록시 우회)

처음에는 용어보다 이 한 줄로 보면 된다.

이 문서에서 beginner 검색 spine은 본문 표현 `왜 @Transactional이 안 먹어요?`, retrieval alias `왜 @transactional이 안 먹어요`로 맞춘다.

`왜 @Transactional이 안 먹어요?`라는 질문이 먼저 나오면, 옵션(`rollbackFor`, `readOnly`)보다 먼저 "프록시를 통과했는가?"를 확인한다.

두 primer에서 공통으로 쓰는 라우팅 문구는 README와 같은 이 한 줄이고, 이 세 신호를 묶어 **프록시 정문 3문항**이라고 부른다.

`this.method()`, `private`, `new Foo()`가 보이면 옵션보다 먼저 `Bean + public + external call`이 깨졌는지 본다.

| 보이는 증상 | 1차 확인 | 바로 이동(입문) | 다음 확인(증상 고정 시) |
|---|---|---|---|
| `@Transactional`을 붙였는데 트랜잭션이 안 열린 것 같다 | 같은 클래스 내부에서 `this.method()`로 호출했는가 | [Service-Layer 2패턴](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴) | [Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md) |
| `private` 메서드에 `@Transactional`을 붙였는데 무시된다 | `Bean + public + external call` 중 `public` 경계가 맞는가 | [AOP 기초](./spring-aop-basics.md#checklist-private-method) | [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md) |
| 직접 `new`한 객체에 annotation을 붙였는데 아무 일도 안 일어난다 | 그 객체가 Spring Bean으로 등록되어 있는가 | [AOP 기초](./spring-aop-basics.md#checklist-direct-new) | [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md) |
| `@Transactional` 말고 `@Async`/`@Cacheable`도 내부 호출에서 이상하다 | 같은 "프록시 우회" 패턴이 반복되는가 | [AOP 기초](./spring-aop-basics.md) | [Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md) |

짧게 대응하면 이렇게 외우면 된다.

| 눈에 먼저 들어온 단서 | 먼저 고정할 질문 |
|---|---|
| `this.method()` | "다른 Bean을 거쳤나?" |
| `private` | "프록시가 설 `public` 경계인가?" |
| `new Foo()` | "애초에 Spring Bean인가?" |

헷갈릴 때는 "트랜잭션 옵션 문제"로 바로 들어가기보다, 위 표대로 호출 경로를 먼저 분리하는 쪽이 빠르다.

## 수정 패턴은 여기서 고르지 않고 링크만 건넨다

이 문서의 역할은 "`왜 안 먹지?`"를 프록시 경계 문제로 분리하는 데까지다. 실제 구조 수정은 [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)에서 `빈 분리`와 `Facade-Worker` 패턴을 비교해서 고른다.

## 지금 문서에서는 여기까지만 잡는다

초급자 첫 독해에서는 아래 세 줄이면 충분하다.

- `@Transactional`은 프록시가 메서드 앞뒤에서 begin/commit/rollback을 붙여 주는 장치다.
- `this.method()`, `private`, 직접 `new`는 옵션보다 먼저 호출 경로 문제를 의심한다.
- 예외 규칙, `readOnly`, 전파 옵션은 이 감각이 잡힌 뒤에 follow-up으로 넘긴다.

`readOnly`, `propagation`, rollback-only marker, nested/requires-new 같은 세부 옵션은 지금 문서의 중심에서 빼 두는 편이 안전하다. 이 단계에서는 "요청 처리"와 "트랜잭션 경계"를 헷갈리지 않고, "프록시를 탔는가"를 먼저 보는 습관이 더 중요하다. 세부 옵션은 [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md), [Spring TransactionTemplate과 Programmatic Transaction](./spring-transactiontemplate-programmatic-transaction-boundaries.md)로 이어서 보면 된다.

## 흔한 오해와 함정

**오해 1: 어노테이션만 붙이면 항상 트랜잭션이 걸린다**
같은 클래스 내부 호출은 프록시를 우회하므로 트랜잭션이 시작되지 않을 수 있다. beginner 기본값은 `Bean + public + external call`을 맞춘 외부 Bean 경로로 보는 편이 안전하다.

**오해 2: 안 되면 `rollbackFor`, `readOnly`, `propagation`부터 바꿔야 한다**
내부 호출/프록시 우회가 원인이면 옵션을 바꿔도 해결되지 않는다. 이 경우는 [Service-Layer 2패턴](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴)으로 바로 가서 구조를 먼저 고친다.

**오해 3: `private` 메서드에도 적용된다**
입문 단계에서는 트랜잭션 경계를 보통 service의 `public` 진입 메서드에 둔다고 생각하는 편이 안전하다. `private` 메서드에 붙여 두고 기대한 효과를 얻는 패턴은 beginner 기본값이 아니다.

**오해 3-1: `private`와 내부 호출은 같은 문제다**
아니다. `private`는 메서드 경계 문제이고, 내부 호출은 호출 경로 문제다. 그래서 `public`으로 바꿔도 `this.method()`면 여전히 안 될 수 있다.

**오해 4: 예외 규칙과 전파 옵션을 지금 다 외워야 한다**
처음 읽을 때는 "`@Transactional`이 어디서 시작되고 왜 안 먹는지"를 먼저 고정하면 충분하다. checked exception, `rollbackFor`, 전파 옵션 세부 규칙은 [Spring Mini Card: rollback-only 실패 vs checked exception인데 commit된 것처럼 보이는 놀람](./spring-rollbackonly-vs-checked-exception-commit-surprise-card.md), [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)로 넘긴다.

### 헷갈릴 때 바로 다시 보는 한 줄 구분

- 내부 호출: "어디서 호출했는가" 문제다.
- 예외 규칙: "무슨 예외가 났는가" 문제다.
- `private` 메서드: "프록시가 잡을 수 있는 메서드 경계인가" 문제다.

셋이 섞여 보여도 질문 축이 다르다. 그래서 30초 체크는 "호출 경로 -> 예외 종류 -> 메서드 경계" 순서로 보면 가장 덜 헷갈린다.

## 실무에서 쓰는 모습

서비스 레이어의 쓰기 메서드에 붙이는 것이 가장 기본 패턴이다. 초급자 첫 독해에서는 "서비스 메서드 하나를 작업 묶음 경계로 둔다" 정도만 받아들이면 충분하다.

```java
@Service
public class OrderService {

    @Transactional
    public void placeOrder(OrderRequest request) {
        // DB 저장, 재고 차감 등 여러 작업이 하나의 트랜잭션
    }

    public Order findOrder(Long id) {
        // 조회 메서드
    }
}
```

위 예시에서 `placeOrder` 메서드가 중간에 `RuntimeException`을 던지면 전체 작업이 rollback된다.

조회 메서드의 `readOnly = true`, 전파 옵션 조합처럼 세부 튜닝은 첫 이해가 끝난 뒤 붙여도 늦지 않다.

## 더 깊이 가려면

- 트랜잭션 전파(propagation), rollback-only 함정, 중첩 트랜잭션은 [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)와 [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)에서 이어서 본다.
- 내부 호출/프록시 우회 증상은 README가 약속한 표현대로 먼저 `프록시 경로 먼저`, `Bean + public + external call`을 다시 확인한 뒤 [Service-Layer 2패턴](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴)으로 바로 고쳐 본다. 원리 비교가 더 필요하면 [AOP 기초](./spring-aop-basics.md)와 [Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md)로 확장하면 빠르다.
- 프록시가 왜 내부 호출에서 한계가 생기는지는 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)을 보면 더 명확해진다.
- DB 격리수준과 `@Transactional(isolation=...)` 연결은 [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)에서 이어서 본다.

## 다음 질문은 다른 문서로 넘긴다

아래 질문이 먼저 떠오르면, 이 문서 안에서 더 파기보다 `프록시 경로 먼저`, `Bean + public + external call` 기준이 맞는지만 다시 확인하고 follow-up 문서로 바로 이동하는 편이 빠르다.

- "`왜 내부 호출이면 안 되죠?`" -> [AOP 기초](./spring-aop-basics.md), [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
- "`checked exception인데 rollback하려면요?`" -> [Spring Mini Card: rollback-only 실패 vs checked exception인데 commit된 것처럼 보이는 놀람](./spring-rollbackonly-vs-checked-exception-commit-surprise-card.md)
- "`동시에 요청이 오면요?`, `격리수준은 언제 봐요?`" -> [트랜잭션 격리 수준 기초](../database/transaction-isolation-basics.md), [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)
- "`readOnly`, `REQUIRES_NEW`는 언제 써요?`" -> [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)

## 한 줄 정리

`@Transactional`은 프록시가 메서드 전후에 begin/commit/rollback을 대신 처리하는 어노테이션이고, 입문 단계에서는 "service 경계"와 "프록시를 탔는가" 두 가지만 먼저 잡으면 대부분의 첫 혼란을 줄일 수 있다.

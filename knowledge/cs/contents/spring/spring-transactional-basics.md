# @Transactional 기초: 트랜잭션 어노테이션이 하는 일

> 한 줄 요약: `@Transactional`은 메서드 실행을 하나의 트랜잭션으로 묶어 주는 어노테이션이고, 실제 동작은 Spring이 생성한 프록시가 메서드 호출 전후로 begin/commit/rollback을 대신 처리하는 것이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)
- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
- [Spring Persistence / Transaction Mental Model Primer](./spring-persistence-transaction-web-service-repository-primer.md)
- [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
- [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)

retrieval-anchor-keywords: transactional basics, @transactional 입문, spring transaction beginner, spring 트랜잭션이 뭐예요, transactional 처음, transactional 왜 안 먹어요, transactional annotation how it works, spring proxy transaction, begin commit rollback spring, transactional method beginner, transactional rollback default, checked exception rollback, transactional 내부 호출, transactional proxy bypass

## 먼저 이 문서에서 멈출 범위

> `@Transactional` 옵션을 바꾸기 전에 먼저 확인할 것:
> 호출이 "프록시를 통과했는지"가 1순위다.

이 문서는 "`트랜잭션 옵션을 바꿔야 하나?`"로 들어가기 전에, 먼저 **트랜잭션이 어디서 시작되는지**를 잡는 beginner 입구다.

- 이 단계에서 먼저 잡을 것: "`요청 하나`와 `트랜잭션 하나`는 같은 말이 아니다", "`public` service 진입점을 프록시가 감싼다".
- 이 문서의 중심이 아닌 것: `propagation`, `isolation`, `rollback-only`, `REQUIRES_NEW`, 운영 장애 사례.
- 위 단어가 바로 궁금하면 이 문서를 끝까지 붙잡기보다 [Spring Persistence / Transaction Mental Model Primer](./spring-persistence-transaction-web-service-repository-primer.md), [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md), [@Transactional 깊이 파기](./transactional-deep-dive.md)로 넘어가는 편이 낫다.

## 프록시 경로 먼저 보는 기준

초급자용 공통 라우팅 한 줄:

`this.method()`, `private`, `new Foo()`가 보이면 옵션보다 먼저 `Bean + public + external call(proxy)`가 깨졌는지 본다.

짧게 구분하면:

| 지금 보이는 증상 | 먼저 볼 축 | 다음 문서 |
|---|---|---|
| "`@Transactional`이 아예 안 먹는 것 같다", "`this.method()`가 보인다", "`private`에 붙였다" | 프록시 경로 문제 | [AOP 기초](./spring-aop-basics.md) |
| "트랜잭션은 잡히는 것 같은데 rollback/readOnly/전파 결과가 기대와 다르다" | 트랜잭션 옵션 문제 | 이 문서 계속 읽기 |

## 핵심 개념

`@Transactional`은 "이 메서드를 하나의 트랜잭션으로 실행하라"는 선언이다. 개발자가 직접 `begin`, `commit`, `rollback`을 적지 않아도 Spring이 프록시를 통해 알아서 처리한다.

입문자가 가장 자주 헷갈리는 지점은 어노테이션이 마법처럼 보인다는 것이다. 실제로는 Spring 컨테이너가 `@Transactional`이 붙은 Bean을 프록시 객체로 감싸고, 그 프록시가 메서드 호출 전에 트랜잭션을 시작하고 메서드 종료 후에 commit 또는 rollback을 호출한다.

## 한눈에 보기

```text
외부 -> 프록시(트랜잭션 시작) -> 실제 메서드 실행 -> 프록시(commit 또는 rollback)
```

| 결과 | 기본 동작 |
|---|---|
| 메서드 정상 종료 | commit |
| RuntimeException (unchecked) 발생 | rollback |
| checked Exception 등 세부 규칙 | 이 문서 끝의 follow-up 링크로 미룬다 |

## 주문 요청 한 장면으로 위치 잡기

`@Transactional`을 처음 볼 때는 옵션 이름보다 "`POST /orders` 한 장면에서 정확히 어디에 붙는가"를 먼저 보는 편이 빠르다.

| 같은 주문 요청에서 보이는 일 | 이걸 담당하는 축 | 초급자용 해석 |
|---|---|---|
| `POST /orders`가 컨트롤러로 들어온다 | MVC | 요청 길찾기다 |
| 컨트롤러가 `OrderService`를 들고 있다 | Bean + DI | 객체 조립은 요청 전에 끝나 있다 |
| `placeOrder()` 앞뒤로 commit/rollback 경계가 생긴다 | `@Transactional` 프록시 | DB 작업 묶기는 service 경계에서 본다 |

이 표를 먼저 잡아 두면 "`요청은 왔는데 rollback이 이상해요`" 같은 말을 볼 때도 MVC, DI, 트랜잭션을 한 덩어리로 섞지 않게 된다.

## 요청 하나와 트랜잭션 하나를 같은 말로 보면 꼬인다

입문자가 자주 하는 오해는 "`POST /orders` 요청 한 번 = 트랜잭션 한 번"으로 바로 생각하는 것이다. 실제로는 요청 처리와 트랜잭션 경계가 다른 층위다.

| 지금 보는 장면 | 누가 담당하나 | 초급자용 한 줄 |
|---|---|---|
| URL이 어느 메서드로 들어오나 | `DispatcherServlet` + controller | 요청 길찾기 |
| controller 안 `orderService`가 왜 있나 | Bean 컨테이너 + DI | 객체 연결 |
| DB 저장을 어디까지 같이 commit/rollback 하나 | `@Transactional` 프록시 | 작업 묶기 |

예를 들어 controller가 service를 호출해도, 그 service 메서드에 `@Transactional`이 없으면 요청은 정상 처리되지만 트랜잭션은 기대와 다르게 짧거나 아예 없을 수 있다. 반대로 요청은 하나여도 service 내부에서 여러 repository 작업을 한 트랜잭션으로 묶을 수 있다.

그래서 문제를 볼 때는 순서를 이렇게 잡는 편이 안전하다. "컨트롤러까지 왔나?" 다음에 "프록시를 타고 트랜잭션이 열렸나?"를 본다. 이 감각이 잡히면 `404`, DI 오류, rollback 문제를 한 덩어리로 섞지 않게 된다.

## 30초 미니 체크: 이 3문항부터 답해 보기

먼저 용어보다 이 기준으로 자가진단하면 된다.

- 호출이 프록시 정문으로 들어갔는가
- 프록시가 가로챌 수 있는 메서드 형태인가
- 지금 문제를 옵션보다 구조로 먼저 볼 수 있는가

| 질문 | 예 / 아니오 해석 | 지금 기억할 한 줄 |
|---|---|---|
| 같은 클래스 안에서 `this.save()`처럼 불렀는가 | 예면 `@Transactional`이 빠질 수 있다 | 내부 호출은 프록시를 우회한다 |
| `@Transactional`을 `private` 메서드에 붙였는가 | 예면 기대한 방식으로 적용되지 않는다 | 프록시가 잡는 공개 진입 메서드로 올린다 |
| controller 요청은 왔는데 service 경계에서 묶이지 않는가 | 예면 옵션보다 service 진입 경계를 먼저 본다 | 요청 처리와 트랜잭션 경계를 같은 문제로 섞지 않는다 |

짧은 판단 예시는 아래처럼 보면 된다.

| 코드 한 줄 | 1차 판단 |
|---|---|
| `this.saveOrder();` | 내부 호출부터 의심 |
| `@Transactional private void save()` | `private` 메서드 적용 기대를 버리고 경계를 다시 잡기 |
| controller에서 service는 호출되는데 한 묶음 rollback이 안 보임 | service `public` 진입점과 호출 경로부터 확인 |

## 테스트로 확인할 때도 질문 축을 먼저 나눈다

`@Transactional`을 테스트로 확인할 때도, 처음에는 "테스트 종류"와 "프록시 경계"를 같은 말로 보면 금방 꼬인다.

| 지금 테스트에서 보이는 말 | 먼저 의심할 축 | 먼저 읽을 문서 |
|---|---|---|
| "`assertSame`인데 왜 프록시처럼 안 보여요?" | identity 테스트와 동작 테스트를 섞음 | [Spring `@Transactional` Self-invocation 검증 테스트 브리지](./spring-transactional-self-invocation-test-bridge-primer.md) |
| "`@WebMvcTest`에서 service bean이 없어요`" | slice 경계 문제 | [Spring 테스트 기초](./spring-testing-basics.md) |
| "`트랜잭션이 안 먹는 것 같은데 this.method()`가 보여요" | 프록시 우회 문제 | [AOP 기초](./spring-aop-basics.md) |

짧게 외우면 이렇다.

- 테스트 어노테이션 선택은 "무엇을 띄울까" 문제다.
- `@Transactional` 적용 여부는 "프록시를 탔나" 문제다.
- 둘이 동시에 보여도 질문 축이 다르므로, 테스트를 바꾸기 전에 호출 경로를 먼저 분리한다.

## `private`와 내부 호출은 구분만 하고, 원리 설명은 다른 문서로 넘긴다

이 문서에서 필요한 수준은 "둘이 다른 질문"이라는 구분까지다. 프록시가 왜 그렇게 동작하는지까지 깊게 풀면 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md), Bean으로 등록된 객체만 왜 감쌀 수 있는지는 [Spring Bean과 DI 기초](./spring-bean-di-basics.md)에서 이어 보는 편이 retrieval 경쟁을 덜 만든다.

| 보이는 코드 | 지금 여기서 내릴 1차 판단 | 바로 할 일 |
|---|---|---|
| `@Transactional private void save()` | 메서드 경계가 트랜잭션 진입점으로 부적절할 수 있다 | service 진입 메서드로 경계를 올린다 |
| `this.saveOrder()` | 호출 경로가 프록시를 우회했을 가능성이 크다 | 다른 Spring Bean 경유 호출로 바꾼다 |
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

`@Transactional`이 안 먹는 것처럼 보이면, 옵션(rollbackFor/readOnly)보다 먼저 "프록시를 통과했는가?"를 확인한다.

두 primer에서 공통으로 쓰는 라우팅 문구는 아래 한 줄이다.

`this.method()`, `private`, `new Foo()`가 보이면 옵션보다 먼저 `Bean + public + external call(proxy)`가 깨졌는지 본다.

| 보이는 증상 | 1차 확인 | 바로 이동(입문) | 다음 확인(증상 고정 시) |
|---|---|---|---|
| `@Transactional`을 붙였는데 트랜잭션이 안 열린 것 같다 | 같은 클래스 내부에서 `this.method()`로 호출했는가 | [Service-Layer 2패턴](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴) | [Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md) |
| `private` 메서드에 `@Transactional`을 붙였는데 무시된다 | 프록시가 가로채는 `public` 메서드 외부 호출인가 | [AOP 기초](./spring-aop-basics.md) | [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md) |
| 직접 `new`한 객체에 annotation을 붙였는데 아무 일도 안 일어난다 | 그 객체가 Spring Bean으로 등록되어 있는가 | [AOP 기초](./spring-aop-basics.md#checklist-direct-new) | [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md) |
| `@Transactional` 말고 `@Async`/`@Cacheable`도 내부 호출에서 이상하다 | 같은 "프록시 우회" 패턴이 반복되는가 | [AOP 기초](./spring-aop-basics.md) | [Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md) |

짧게 대응하면 이렇게 외우면 된다.

| 눈에 먼저 들어온 단서 | 먼저 고정할 질문 |
|---|---|
| `this.method()` | "다른 Bean을 거쳤나?" |
| `private` | "프록시가 설 `public` 경계인가?" |
| `new Foo()` | "애초에 Spring Bean인가?" |

헷갈릴 때는 "트랜잭션 옵션 문제"로 바로 들어가기보다, 위 표대로 호출 경로를 먼저 분리하는 쪽이 빠르다.

## 2패턴 선택 빠른 기준

`@Transactional 기초`에서 더 들어가야 할 때는, 원리 설명보다 수정 패턴 선택으로 바로 넘어가는 편이 빠르다.

| 질문 | `Yes`면 고를 패턴 | 이유 |
|---|---|---|
| 지금 문제는 사실상 `this.saveOrder()` 한 군데인가? | [빈 분리(Caller/Worker)](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴) | 가장 작은 변경으로 프록시 경로를 복구한다 |
| 주문 생성, 재고 차감처럼 여러 하위 작업을 한 유스케이스로 묶는 대표 메서드가 필요한가? | [Facade-Worker 분리](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴) | 커밋 경계 소유자를 대표 메서드 1곳으로 모은다 |

짧게 기억하면 이렇다.

- "메서드 하나가 self-invocation에 걸렸다"면 빈 분리부터 본다.
- "유스케이스 전체 경계가 흐리다"면 Facade-Worker부터 본다.

## 지금 문서에서는 여기까지만 잡는다

초급자 첫 독해에서는 아래 네 줄이면 충분하다.

- `@Transactional`은 프록시가 메서드 앞뒤에서 begin/commit/rollback을 붙여 주는 장치다.
- 기본 rollback 대상은 보통 `RuntimeException` 쪽이다.
- checked exception이면 `rollbackFor`를 따로 볼 수 있다.
- `this.method()`, `private`, 직접 `new`는 옵션보다 먼저 호출 경로 문제를 의심한다.

`readOnly`, `propagation`, rollback-only marker, nested/requires-new 같은 세부 옵션은 지금 문서의 중심에서 빼 두는 편이 안전하다. 이 단계에서는 "요청 처리"와 "트랜잭션 경계"를 헷갈리지 않고, "프록시를 탔는가"를 먼저 보는 습관이 더 중요하다. 세부 옵션은 [@Transactional 깊이 파기](./transactional-deep-dive.md), [Spring TransactionTemplate과 Programmatic Transaction](./spring-transactiontemplate-programmatic-transaction-boundaries.md)로 이어서 보면 된다.

## 흔한 오해와 함정

**오해 1: 어노테이션만 붙이면 항상 트랜잭션이 걸린다**
같은 클래스 내부 호출은 프록시를 우회하므로 트랜잭션이 시작되지 않는다. 반드시 외부 Bean에서 호출해야 한다.

**오해 2: checked exception도 무조건 rollback된다**
기본값은 아니다. `rollbackFor = Exception.class` 처럼 명시해야 checked exception에도 rollback이 걸린다.

**오해 3: `private` 메서드에도 적용된다**
입문 단계에서는 트랜잭션 경계를 보통 service의 `public` 진입 메서드에 둔다고 생각하는 편이 안전하다. `private` 메서드에 붙여 두고 기대한 효과를 얻는 패턴은 beginner 기본값이 아니다.

**오해 3-1: `private`와 내부 호출은 같은 문제다**
아니다. `private`는 메서드 경계 문제이고, 내부 호출은 호출 경로 문제다. 그래서 `public`으로 바꿔도 `this.save()`면 여전히 안 될 수 있다.

**오해 4: 안 되면 `rollbackFor`, `propagation`부터 바꿔야 한다**
내부 호출/프록시 우회가 원인이면 옵션을 바꿔도 해결되지 않는다. 이 경우는 [Service-Layer 2패턴](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴)으로 바로 가서 구조를 먼저 고치고, 패턴 비교가 더 필요하면 [Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md)로 넘어간다.

### 헷갈릴 때 바로 다시 보는 한 줄 구분

- 내부 호출: "어디서 호출했는가" 문제다.
- checked exception: "무슨 예외가 났는가" 문제다.
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

- 트랜잭션 전파(propagation), rollback-only 함정, 중첩 트랜잭션은 [@Transactional 깊이 파기](./transactional-deep-dive.md)에서 다룬다.
- 내부 호출/프록시 우회 증상은 [Service-Layer 2패턴](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴)으로 먼저 바로 고쳐 보고, 원리 비교가 더 필요하면 [AOP 기초](./spring-aop-basics.md)와 [Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md)로 확장하면 빠르다.
- 프록시가 왜 내부 호출에서 한계가 생기는지는 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)을 보면 더 명확해진다.
- DB 격리수준과 `@Transactional(isolation=...)` 연결은 [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)에서 이어서 본다.

## 다음 질문은 다른 문서로 넘긴다

아래 질문이 먼저 떠오르면, 이 문서 안에서 더 파기보다 follow-up 문서로 바로 이동하는 편이 빠르다.

- "`왜 내부 호출이면 안 되죠?`" -> [AOP 기초](./spring-aop-basics.md), [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
- "`checked exception인데 rollback하려면요?`" -> [@Transactional 깊이 파기](./transactional-deep-dive.md)
- "`readOnly`, `REQUIRES_NEW`, 격리수준은 언제 써요?`" -> [@Transactional 깊이 파기](./transactional-deep-dive.md), [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)

## 한 줄 정리

`@Transactional`은 프록시가 메서드 전후에 begin/commit/rollback을 대신 처리하는 어노테이션이고, 내부 호출과 checked exception 기본 동작을 알면 입문 시의 대부분 함정을 피할 수 있다.

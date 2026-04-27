# @Transactional 기초: 트랜잭션 어노테이션이 하는 일

> 한 줄 요약: `@Transactional`은 메서드 실행을 하나의 트랜잭션으로 묶어 주는 어노테이션이고, 실제 동작은 Spring이 생성한 프록시가 메서드 호출 전후로 begin/commit/rollback을 대신 처리하는 것이다.

**난이도: 🟢 Beginner**

## 다음 단계: 내부 호출 증상에서 어디로 갈까

> `@Transactional` 옵션을 바꾸기 전에 먼저 확인할 것:
> 호출이 "프록시를 통과했는지"가 1순위다.

| 지금 상태 | 바로 볼 문서 | 왜 지금 이 문서인가 |
|---|---|---|
| "`@Transactional`만 유독 문제인 줄 안다" | [Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md) | self-invocation을 트랜잭션 전용 문제가 아니라 프록시 기반 annotation 공통 규칙으로 먼저 다시 잡아 준다 |
| 내부 호출 증상을 봤고, 코드 구조를 바로 어떻게 바꿀지 보고 싶다 | [Service-Layer 2패턴으로 바로 이동](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴) | 같은 클래스 `this.method()` 우회를 가장 자주 고치는 두 가지 구조를 짧게 비교해 준다 |
| `@Transactional` 기본 개념은 알겠는데 내부 호출에서 자꾸 막힌다 | [Spring Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md) | `@Transactional`, `@Async`, `@Cacheable`을 같은 프록시 우회 패턴으로 한 번에 비교해 준다 |
| 매트릭스를 보다가 용어가 과하게 느껴진다 | [@Transactional 기초](./spring-transactional-basics.md) (이 문서) | begin/commit/rollback과 프록시 경계를 쉬운 언어로 다시 정리한 뒤 재진입하기 좋다 |

관련 문서:

- [Spring Persistence / Transaction Mental Model Primer: Web, Service, Repository를 한 장으로 묶기](./spring-persistence-transaction-web-service-repository-primer.md)
- [AOP 기초: 관점 지향 프로그래밍이 왜 필요한가](./spring-aop-basics.md)
- [Spring Mini Card: rollback-only 실패 vs checked exception인데 commit된 것처럼 보이는 놀람](./spring-rollbackonly-vs-checked-exception-commit-surprise-card.md)
- [Spring Self-Invocation 공통 오해 1페이지 카드: "`@Transactional`만 문제"가 아니다](./spring-self-invocation-transactional-only-misconception-primer.md)
- [@Transactional 깊이 파기](./transactional-deep-dive.md)
- [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
- [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
- [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: transactional basics, @transactional 입문, spring transaction beginner, spring 트랜잭션이 뭐예요, transactional annotation how it works, spring proxy transaction, begin commit rollback spring, transactional method beginner, transactional rollback default, unchecked exception rollback, checked exception rollback, @transactional readonly, spring transaction 기초, transactional 내부 호출, transactional proxy bypass, this method transactional 안됨, self invocation transactional beginner, 왜 transactional 안 먹지, aop proxy routing card, service layer 2 patterns, transactional internal call fix, caller worker pattern, facade worker pattern, 다음 단계 self invocation 매트릭스, transactional self invocation bridge, transactional beginner round trip, transactional 30초 체크, transactional self check, transactional checked exception mini check, transactional private method mini check, transactional internal call mini check, private method transactional 안됨, checked exception rollback 안됨, transactional beginner confusion, private vs internal call transactional, private vs self invocation transactional, 접근 제한자 vs 내부 호출 비교, transactional private internal difference, transactional before after example, private transactional before after, self invocation transactional before after, this method transactional example, rollback-only vs checked exception, checked exception commit surprise, 예외 났는데 commit 됨

초급자용 공통 라우팅 한 줄:

`this.method()`, `private`, `new Foo()`가 보이면 옵션보다 먼저 `Bean + public + external call(proxy)`가 깨졌는지 본다.

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
| checked Exception 발생 | 기본적으로 rollback 안 함 |
| `rollbackFor` 지정 시 | 지정된 예외에 rollback |

## 30초 미니 체크: 이 3문항부터 답해 보기

먼저 용어보다 이 기준으로 자가진단하면 된다.

- 호출이 프록시 정문으로 들어갔는가
- 기본 rollback 규칙을 벗어나는 예외인가
- 프록시가 가로챌 수 있는 메서드 형태인가

| 질문 | 예 / 아니오 해석 | 지금 기억할 한 줄 |
|---|---|---|
| 같은 클래스 안에서 `this.save()`처럼 불렀는가 | 예면 `@Transactional`이 빠질 수 있다 | 내부 호출은 프록시를 우회한다 |
| 터진 예외가 `IOException` 같은 checked exception인가 | 예면 기본값으로는 rollback이 안 될 수 있다 | checked exception은 `rollbackFor`를 따로 본다 |
| `@Transactional`을 `private` 메서드에 붙였는가 | 예면 기대한 방식으로 적용되지 않는다 | 프록시가 잡는 공개 진입 메서드로 올린다 |

짧은 판단 예시는 아래처럼 보면 된다.

| 코드 한 줄 | 1차 판단 |
|---|---|
| `this.saveOrder();` | 내부 호출부터 의심 |
| `throw new IOException();` | checked exception rollback 규칙부터 확인 |
| `@Transactional private void save()` | `private` 메서드 적용 기대를 버리고 경계를 다시 잡기 |

## `private` 문제와 내부 호출 문제를 한눈에 구분하기

처음 배울 때는 둘 다 "`@Transactional`이 안 먹는다"로 보여서 쉽게 섞인다.

- `private`는 "프록시가 메서드 경계에 설 수 있나?"를 묻는 질문이다.
- 내부 호출은 "그 메서드를 부를 때 프록시 정문을 지났나?"를 묻는 질문이다.

| 비교 항목 | `@Transactional private void save()` | `this.save()` 같은 내부 호출 |
|---|---|---|
| 먼저 보는 축 | 메서드 접근 제한자 | 호출 경로 |
| 초급자용 한 줄 | 문이 닫혀 있어서 프록시가 서기 어렵다 | 문이 있어도 정문을 안 지나갔다 |
| `public`으로 바꾸면 끝나나 | 메서드 경계 문제는 줄어든다 | 아니다. 여전히 `this.save()`면 우회한다 |
| 다른 Bean에서 호출하면 해결되나 | 메서드가 여전히 `private`면 어렵다 | 예. 외부 Bean 호출이면 프록시 경유를 기대할 수 있다 |
| 자주 하는 착각 | "`private`만 `public`으로 바꾸면 끝" | "`public`인데 왜 안 되지?" |
| 기본 수정 방향 | 트랜잭션 경계 메서드를 `public` 진입점으로 올린다 | 트랜잭션 메서드를 다른 Bean으로 분리한다 |

### 전후 코드로 바로 구분하기

아래 두 쌍은 겉보기 증상은 비슷하지만, 고치는 포인트가 다르다.

| 증상 | 바꾸기 전 | 바꾼 뒤 | 핵심 판단 |
|---|---|---|---|
| `private` 메서드에 `@Transactional`을 붙였다 | `@Transactional private void save()` | `@Transactional public void save()` | 먼저 메서드 경계를 프록시가 잡을 수 있게 올린다 |
| `public`인데 `this.save()`로 부른다 | `this.save()` | `orderTxService.save()` | 호출 경로를 외부 Bean 경유로 바꿔 프록시 정문을 통과시킨다 |

`private` 증상은 "메서드 선언"을 고치는 쪽이고, 내부 호출 증상은 "누가 어떻게 호출하나"를 고치는 쪽이다.

#### 1. `private` 문제: 선언을 먼저 바꾼다

```java
// before
@Service
public class OrderService {

    @Transactional
    private void saveOrder() {
    }
}
```

```java
// after
@Service
public class OrderService {

    @Transactional
    public void saveOrder() {
    }
}
```

이 경우 1차 수정 포인트는 `private -> public`이다. 다만 이것만으로 충분한지는 "누가 이 메서드를 호출하나"를 이어서 봐야 한다.

#### 2. 내부 호출 문제: 호출 경로를 바꾼다

```java
// before
@Service
public class OrderService {

    public void placeOrder() {
        this.saveOrder();
    }

    @Transactional
    public void saveOrder() {
    }
}
```

```java
// after
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

여기서는 이미 `public`이어도 `this.saveOrder()`면 안 된다. 핵심은 "다른 Spring Bean이 호출하느냐"다.

둘이 같이 나오는 코드도 많다.

```java
@Service
public class OrderService {

    public void placeOrder() {
        this.saveOrder(); // 내부 호출
    }

    @Transactional
    private void saveOrder() { // private 경계
    }
}
```

이 코드는 문제가 하나가 아니라 둘이다.

- `saveOrder()`가 `private`라 메서드 경계 자체가 프록시에 열려 있지 않다.
- `placeOrder()`가 `this.saveOrder()`로 불러서 호출 경로도 프록시를 우회한다.

그래서 고칠 때도 순서를 이렇게 잡으면 덜 헷갈린다.

1. 트랜잭션 경계를 `public` 메서드로 올린다.
2. 그 메서드를 다른 Spring Bean에서 호출하게 바꾼다.

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

### 2패턴 선택 빠른 기준

`@Transactional 기초`와 `Service-Layer` 문서는 아래 같은 질문으로 고른다.

| 질문 | `Yes`면 고를 패턴 | 이유 |
|---|---|---|
| 지금 문제는 사실상 `this.saveOrder()` 한 군데인가? | [빈 분리(Caller/Worker)](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴) | 가장 작은 변경으로 프록시 경로를 복구한다 |
| 주문 생성, 재고 차감처럼 여러 하위 작업을 한 유스케이스로 묶는 대표 메서드가 필요한가? | [Facade-Worker 분리](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴) | 커밋 경계 소유자를 대표 메서드 1곳으로 모은다 |

짧게 기억하면 이렇다.

- "메서드 하나가 self-invocation에 걸렸다"면 빈 분리부터 본다.
- "유스케이스 전체 경계가 흐리다"면 Facade-Worker부터 본다.

## 상세 분해

- **프록시 래핑**: `@Transactional` Bean은 컨테이너가 프록시로 감싼다. 외부에서 메서드를 호출해야 프록시를 타고 트랜잭션이 시작된다.
- **기본 롤백 규칙**: `RuntimeException`과 `Error`는 기본으로 rollback, checked exception은 기본으로 commit 방향이다.
- **`readOnly = true`**: 읽기 전용 힌트를 주어 불필요한 dirty checking을 줄이고 일부 DB 드라이버는 read replica로 라우팅할 수 있다. 쓰기가 없는 조회 메서드에 적용하면 좋다.
- **propagation**: 이미 트랜잭션이 있을 때 이 메서드가 그 트랜잭션에 참여할지, 새로 시작할지 결정하는 설정이다. 기본값은 `REQUIRED`(기존 트랜잭션에 참여, 없으면 새로 시작).
- **내부 호출 주의**: 같은 클래스 안에서 `this.메서드()`로 부르면 프록시를 타지 않아 `@Transactional`이 적용되지 않는다.

## 흔한 오해와 함정

**오해 1: 어노테이션만 붙이면 항상 트랜잭션이 걸린다**
같은 클래스 내부 호출은 프록시를 우회하므로 트랜잭션이 시작되지 않는다. 반드시 외부 Bean에서 호출해야 한다.

**오해 2: checked exception도 무조건 rollback된다**
기본값은 아니다. `rollbackFor = Exception.class` 처럼 명시해야 checked exception에도 rollback이 걸린다.

**오해 3: `private` 메서드에도 적용된다**
Spring AOP 프록시는 `public` 메서드에만 적용된다. `private` 메서드에 `@Transactional`을 붙여도 동작하지 않는다.

**오해 3-1: `private`와 내부 호출은 같은 문제다**
아니다. `private`는 메서드 경계 문제이고, 내부 호출은 호출 경로 문제다. 그래서 `public`으로 바꿔도 `this.save()`면 여전히 안 될 수 있다.

**오해 4: 안 되면 `rollbackFor`부터 바꿔야 한다**
내부 호출/프록시 우회가 원인이면 rollback 옵션을 바꿔도 해결되지 않는다. 이 경우는 [Service-Layer 2패턴](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴)으로 바로 가서 구조를 먼저 고치고, 패턴 비교가 더 필요하면 [Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md)로 넘어간다.

### 헷갈릴 때 바로 다시 보는 한 줄 구분

- 내부 호출: "어디서 호출했는가" 문제다.
- checked exception: "무슨 예외가 났는가" 문제다.
- `private` 메서드: "프록시가 잡을 수 있는 메서드 경계인가" 문제다.

셋이 섞여 보여도 질문 축이 다르다. 그래서 30초 체크는 "호출 경로 -> 예외 종류 -> 메서드 경계" 순서로 보면 가장 덜 헷갈린다.

## 실무에서 쓰는 모습

서비스 레이어의 쓰기 메서드에 붙이는 것이 가장 기본 패턴이다.

```java
@Service
public class OrderService {

    @Transactional
    public void placeOrder(OrderRequest request) {
        // DB 저장, 재고 차감 등 여러 작업이 하나의 트랜잭션
    }

    @Transactional(readOnly = true)
    public Order findOrder(Long id) {
        // 조회 전용 - dirty checking 비용 줄임
    }
}
```

위 예시에서 `placeOrder` 메서드가 중간에 `RuntimeException`을 던지면 전체 작업이 rollback된다.

## 더 깊이 가려면

- 트랜잭션 전파(propagation), rollback-only 함정, 중첩 트랜잭션은 [@Transactional 깊이 파기](./transactional-deep-dive.md)에서 다룬다.
- 내부 호출/프록시 우회 증상은 [Service-Layer 2패턴](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴)으로 먼저 바로 고쳐 보고, 원리 비교가 더 필요하면 [AOP 기초](./spring-aop-basics.md)와 [Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md)로 확장하면 빠르다.
- 프록시가 왜 내부 호출에서 한계가 생기는지는 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)을 보면 더 명확해진다.
- DB 격리수준과 `@Transactional(isolation=...)` 연결은 [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)에서 이어서 본다.

## 면접/시니어 질문 미리보기

> Q: `@Transactional`이 붙은 메서드를 같은 클래스 내부에서 호출하면 트랜잭션이 걸리는가?
> 의도: 프록시 메커니즘 이해 확인
> 핵심: 내부 호출은 프록시를 우회하므로 트랜잭션이 시작되지 않는다.

> Q: checked exception이 발생했는데 rollback이 안 됐다. 왜인가?
> 의도: 기본 rollback 규칙 이해 확인
> 핵심: 기본 rollback 대상은 `RuntimeException`과 `Error`이고 checked exception은 `rollbackFor`로 명시해야 한다.

> Q: `@Transactional(readOnly = true)`는 어떤 이점이 있는가?
> 의도: readOnly 의미 이해 확인
> 핵심: dirty checking 비용 절감, 일부 환경에서 read replica 라우팅 가능성.

## 한 줄 정리

`@Transactional`은 프록시가 메서드 전후에 begin/commit/rollback을 대신 처리하는 어노테이션이고, 내부 호출과 checked exception 기본 동작을 알면 입문 시의 대부분 함정을 피할 수 있다.

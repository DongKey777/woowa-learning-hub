# Spring Service-Layer Transaction Boundary Patterns

> 한 줄 요약: `@Transactional`은 "어디서 DB를 호출하느냐"가 아니라, 하나의 비즈니스 유스케이스를 어디까지 원자적으로 묶을지 선언하는 경계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Self-Invocation / Proxy Annotation Matrix](./spring-self-invocation-proxy-annotation-matrix.md)
> - [AOP 기초](./spring-aop-basics.md)
> - [Spring `@Transactional` 기초](./spring-transactional-basics.md)
> - [Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기](./spring-service-layer-external-io-after-commit-outbox-primer.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)
> - [Spring Transaction Propagation: `MANDATORY` / `SUPPORTS` / `NOT_SUPPORTED` Boundaries](./spring-transaction-propagation-mandatory-supports-not-supported-boundaries.md)
> - [Spring EventListener, TransactionalEventListener, and Outbox](./spring-eventlistener-transaction-phase-outbox.md)
> - [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
> - [Transaction Boundary, Isolation, and Locking Decision Framework](../database/transaction-boundary-isolation-locking-decision-framework.md)
> - [Aggregate Boundary vs Transaction Boundary](../design-pattern/aggregate-boundary-vs-transaction-boundary.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)

retrieval-anchor-keywords: service layer transaction boundary, application service, use case transaction, transactional placement, @transactional service layer 어디, @transactional 위치, controller service repository transactional 어디 둬야, transactional service layer remote call, controller transaction, repository transaction, self invocation, transactional self invocation fix, 프록시 우회 수정 패턴, 빈 분리 transactional, facade worker pattern, facade worker transactional, transactional internal call 2 patterns, same class transactional fix, caller worker pattern, this method transactional fix, beginner transaction boundary bridge, remote call in transaction, outbox, mandatory propagation, 프록시 우회 체크리스트, transactional 30초 진단 카드, 증상 원인 패턴 선택, this 호출 transactional 안됨

---

## 핵심 개념

트랜잭션 경계는 보통 "서비스 계층에 둔다"라고 배우지만, 정확히는 **유스케이스를 완결하는 application service 메서드**에 두는 것이 맞다.

핵심은 다음 네 가지다.

- 트랜잭션은 테이블이나 repository가 아니라 **비즈니스 상태 전이**를 기준으로 잡는다.
- 컨트롤러보다 안쪽, repository보다 바깥쪽에 두는 경우가 가장 많다.
- 같은 유스케이스의 상태 변경은 한 경계 안에 묶고, 외부 부작용은 가능하면 경계 밖으로 뺀다.
- 하위 서비스가 제각각 트랜잭션을 열기 시작하면 커밋 단위가 유스케이스가 아니라 구현 세부사항에 종속된다.

즉, `@Transactional`의 기본 위치는 "DB를 가장 많이 건드리는 클래스"가 아니라 **업무적으로 같이 성공하거나 같이 실패해야 하는 메서드**다.

### 초급자용 먼저 잡는 그림

처음에는 이렇게만 보면 된다.

- `@Transactional`이 안 먹는 증상: 호출 경로가 프록시 정문을 지났는지 본다.
- 어디에 붙여야 할지 헷갈림: "이 유스케이스를 대표하는 메서드가 무엇인가"를 먼저 찾는다.

## 초급자 왕복 링크

이 문서는 "패턴 선택" 문서다. 막히는 위치에 따라 아래처럼 왕복하면 된다.

| 지금 막히는 지점 | 먼저 돌아갈 문서 | 이 문서에서 다시 볼 위치 |
|---|---|---|
| AOP 용어가 아직 추상적이다 | [AOP 기초](./spring-aop-basics.md) | 아래 [`초급 빠른 수정: 내부 호출 프록시 우회 2패턴`](#초급-빠른-수정-내부-호출-프록시-우회-2패턴) |
| `@Transactional` begin/commit/rollback 그림이 먼저 필요하다 | [Spring `@Transactional` 기초](./spring-transactional-basics.md) | 아래 [`초급 빠른 수정: 내부 호출 프록시 우회 2패턴`](#초급-빠른-수정-내부-호출-프록시-우회-2패턴) |
| 패턴 이름은 알겠는데 왜 필요한지 다시 헷갈린다 | [AOP 기초의 `Bean + public + external call` 체크](./spring-aop-basics.md#초급자용-3단계-왕복-라우트) | 이 문서의 30초 진단 카드 |

| 지금 질문 | 먼저 보는 한 줄 답 |
|---|---|
| "`this.save()`가 왜 안 되지?" | 같은 Bean 내부 호출이라 프록시를 안 탔다 |
| "`@Transactional`은 어디에 두지?" | 유스케이스를 설명하는 서비스 메서드가 기본 자리다 |
| "두 문제를 같이 고치려면?" | 아래 2패턴에서 호출 구조와 경계 소유자를 같이 정리한다 |

## 30초 진단 카드: 프록시 우회 증상 -> 원인 -> 2패턴 선택

이 섹션은 "왜 안 되지?"를 30초 안에 자르기 위한 카드다.

`@Transactional 기초`에서 쓰는 용어와 여기서 쓰는 용어를 그대로 맞춘다.

- 증상이 `this.save()`/같은 클래스 내부 호출이면: 전파 옵션보다 먼저 프록시 우회 여부를 본다.
- 원인은 대부분 하나다: 트랜잭션이 틀린 게 아니라 호출이 프록시 정문을 안 지났다.
- 선택은 두 가지면 충분하다: 작은 구조 수정인지, 유스케이스 경계 재정리인지부터 고른다.

| 지금 보이는 증상 | 가장 먼저 의심할 원인 | 먼저 고를 패턴 |
|---|---|---|
| `@Transactional`을 붙였는데 트랜잭션 로그가 안 잡히는 것 같다 | 같은 클래스 내부 호출이라 프록시를 우회했다 | 빈 분리(Caller/Worker) |
| `public`으로 바꿨는데도 그대로다 | 접근 제한자보다 호출 경로가 여전히 `this`다 | 빈 분리(Caller/Worker) |
| 주문 생성, 재고 차감처럼 여러 작업이 섞여서 "누가 커밋 주인인지" 모호하다 | 트랜잭션 경계 소유자가 한 메서드로 모이지 않았다 | Facade-Worker 분리 |

### 2패턴 선택 빠른 기준

| 질문 | `Yes`면 고를 패턴 | 이유 |
|---|---|---|
| 지금 문제는 사실상 `this.write()` 한 군데인가? | 빈 분리(Caller/Worker) | 가장 작은 변경으로 프록시 경로를 복구한다 |
| 주문 생성, 재고 차감처럼 여러 하위 작업을 한 유스케이스로 묶는 대표 메서드가 필요한가? | Facade-Worker 분리 | 커밋 경계 소유자를 대표 메서드 1곳으로 모은다 |

자주 하는 오해:

- `REQUIRES_NEW`를 붙이면 프록시 우회가 해결되는 것이 아니다.
- `private`를 `public`으로만 바꾸고 같은 클래스에서 계속 부르면 증상은 그대로일 수 있다.
- 두 패턴 모두 핵심은 "애노테이션 추가"가 아니라 "프록시를 지나는 호출 구조 복구"다.

---

## 초급 빠른 수정: 내부 호출 프록시 우회 2패턴

> [`@Transactional 기초`](./spring-transactional-basics.md)에서 "내부 호출 증상"을 보고 넘어왔다면 이 섹션만 먼저 읽으면 된다.
> AOP 프록시 감각이 흐려졌다면 [`AOP 기초`](./spring-aop-basics.md#초급자용-3단계-왕복-라우트)로 한 칸 돌아가도 된다.

먼저 감각만 잡으면 간단하다.

- `@Transactional`은 "메서드에 글자 붙이기"가 아니라 "프록시를 거쳐 호출되어야 발동"하는 규칙이다.
- 같은 클래스 안에서 `this.method()`로 부르면 프록시를 우회하므로 트랜잭션이 안 걸릴 수 있다.
- 이때는 전파 옵션을 만지기 전에 호출 구조를 먼저 고친다.

| 패턴 | 언제 쓰나 | 바꾸는 방법 | 한 줄 체크 |
|---|---|---|---|
| 빈 분리(Caller/Worker) | 기존 서비스 내부에서 `this.write()`를 호출 중일 때 | 쓰기 메서드를 별도 `@Service`로 분리하고, 기존 서비스가 주입받아 호출 | 호출이 `this`가 아니라 `otherBean.write()`인가? |
| Facade-Worker 분리 | 한 유스케이스에서 여러 하위 작업을 묶고 싶을 때 | Facade가 `@Transactional` 경계를 소유하고 Worker들은 그 경계 안에서 동작 | 커밋 의미가 Facade 메서드 1개로 설명되는가? |

### 어떤 패턴부터 고를까

| 지금 보이는 코드 | 권장 시작점 | 이유 |
|---|---|---|
| 한 클래스 안에서 `this.write()`만 문제다 | 빈 분리(Caller/Worker) | 가장 작은 변경으로 프록시 경로를 복구한다 |
| 여러 서비스 호출이 섞여 있고 "누가 커밋 주인인지" 애매하다 | Facade-Worker 분리 | 트랜잭션 경계를 유스케이스 1곳으로 모은다 |

초급자에게는 이렇게 외우는 편이 빠르다.

- 빈 분리: "문제 메서드를 다른 집으로 옮겨 정문으로 다시 들어가게 한다"
- Facade-Worker: "유스케이스 대표 메서드 1개가 커밋 주인이다"

<a id="pattern-caller-worker"></a>
### 패턴 1) 빈 분리(Caller/Worker)

```java
@Service
public class OrderFacade {
    private final OrderWriter orderWriter;

    public OrderFacade(OrderWriter orderWriter) {
        this.orderWriter = orderWriter;
    }

    public void place() {
        orderWriter.write(); // Bean -> Proxy -> @Transactional
    }
}

@Service
public class OrderWriter {
    @Transactional
    public void write() {
        // DB write
    }
}
```

<a id="pattern-facade-worker"></a>
### 패턴 2) Facade-Worker 분리

```java
@Service
public class CheckoutFacade {
    private final OrderWorker orderWorker;
    private final InventoryWorker inventoryWorker;

    public CheckoutFacade(OrderWorker orderWorker, InventoryWorker inventoryWorker) {
        this.orderWorker = orderWorker;
        this.inventoryWorker = inventoryWorker;
    }

    @Transactional
    public void checkout() {
        orderWorker.create();
        inventoryWorker.decrease();
    }
}
```

자주 헷갈리는 포인트:

- Worker에도 `@Transactional`을 중복으로 붙이면 경계 소유자가 흐려진다. 기본은 Facade 한 곳부터 시작한다.
- `private @Transactional`로는 해결되지 않는다. 호출 경로가 프록시를 타지 않기 때문이다.
- `REQUIRES_NEW`는 "내부 호출 우회 수정" 도구가 아니라 "독립 커밋" 선택이다.

---

## 깊이 들어가기

### 1. 가장 기본 패턴은 application service 단일 write boundary다

가장 흔하고 안정적인 패턴은 "한 유스케이스를 orchestration하는 서비스 메서드"에 트랜잭션을 두는 것이다.

예를 들어 주문 생성은 보통 다음을 하나의 경계로 본다.

- 주문 생성
- 재고 차감
- 쿠폰 사용
- 결제 상태 기록

이 작업들이 함께 성공해야 한다면, 컨트롤러도 아니고 repository도 아니라 **주문 유스케이스를 조합하는 서비스 메서드**가 경계가 된다.

```text
controller
  -> application service (@Transactional)
    -> domain/repository calls
    -> commit
```

이 패턴의 장점은 명확하다.

- 커밋 단위가 비즈니스 언어와 일치한다
- 롤백 범위를 설명하기 쉽다
- 테스트에서 "이 유스케이스가 원자적인가"를 검증하기 쉽다

### 2. 조회와 변경은 경계를 다르게 가져간다

모든 서비스 메서드에 같은 방식으로 `@Transactional`을 붙이면 경계가 뭉개진다.

실무에서는 보통 이렇게 나누는 편이 안정적이다.

- command service: 상태 변경, `@Transactional`
- query service: 조회 전용, `@Transactional(readOnly = true)` 또는 비트랜잭션

이 분리는 CQRS처럼 거창한 아키텍처가 아니더라도 유용하다.

- 조회 메서드에 쓰기 플러시가 섞이는 일을 줄인다
- read-only 의도가 드러난다
- 락과 커넥션 점유 시간을 더 보수적으로 관리할 수 있다

### 3. 하위 서비스는 "경계를 소유하는지"를 명시해야 한다

서비스가 여러 개로 나뉘어 있어도, 모두가 각자 트랜잭션을 열 필요는 없다.

오히려 흔한 실수는 아래 둘이다.

- 상위 orchestrator에는 `@Transactional`이 없고, 하위 서비스마다 각각 붙어 있다
- 안쪽 서비스에 `REQUIRES_NEW`가 숨어 있어 부분 커밋이 생긴다

트랜잭션 소유권 관점에서 하위 서비스는 셋 중 하나로 설계하는 편이 낫다.

- 상위 경계에 조용히 참여한다: 기본 `REQUIRED`
- 반드시 상위 경계 안에서만 호출되게 강제한다: `MANDATORY`
- 정말 독립 커밋이 필요할 때만 분리한다: `REQUIRES_NEW`

특히 핵심 도메인 변경 로직인데도 바깥 트랜잭션 없이 호출되면 안 되는 경우, `MANDATORY`는 설계 실수를 빨리 드러내는 안전장치가 된다.

### 4. 원격 호출과 메시지 발행은 트랜잭션 안에 오래 두지 않는다

서비스 메서드가 유스케이스 경계를 소유하더라도, 그 안에 외부 HTTP 호출이나 느린 메시지 전송을 그대로 넣으면 다른 문제가 생긴다.

- DB 락 점유 시간이 길어진다
- 커넥션 점유 시간이 늘어난다
- 외부 시스템 지연이 로컬 트랜잭션 지연으로 번진다
- 재시도 시 중복 커밋/중복 호출 설계가 더 어려워진다

그래서 write boundary를 잡을 때는 "무엇을 같이 커밋할까"만이 아니라 "무엇을 트랜잭션 밖으로 밀어낼까"도 같이 봐야 한다.

대표 대안은 다음과 같다.

- DB 상태 변경까지만 트랜잭션으로 묶고, 외부 호출은 커밋 후 수행
- `@TransactionalEventListener(AFTER_COMMIT)` 사용
- 더 신뢰성이 필요하면 outbox 패턴 사용

초급자 예시부터 빠르게 보고 싶다면 [외부 I/O는 트랜잭션 밖으로, `AFTER_COMMIT` vs Outbox](./spring-service-layer-external-io-after-commit-outbox-primer.md)를 먼저 본 뒤 이 문서로 돌아오는 편이 덜 헷갈린다.

### 5. 프록시 기반 제약은 placement mistake를 만든다

`@Transactional`이 서비스 계층에 있어도, 메서드 배치가 잘못되면 경계가 성립하지 않는다.

대표 제약은 다음과 같다.

- 같은 클래스 내부 호출은 프록시를 안 탄다
- `private` 메서드는 프록시 기반 interception 대상이 되지 않는다
- Spring 빈이 아닌 객체에 붙여도 동작하지 않는다

즉, "서비스 계층에 두라"는 말만 기억하면 부족하고, **프록시가 실제로 그 경계를 가로챌 수 있는 구조인가**까지 봐야 한다.

---

## 흔한 `@Transactional` 배치 실수

### 1. 컨트롤러에 트랜잭션을 둔다

컨트롤러에 `@Transactional`을 붙이면 다음이 한 경계에 섞이기 쉽다.

- 요청 파싱
- 입력 검증
- 인증/인가 후처리
- 응답 직렬화
- 외부 API 호출

이렇게 되면 DB 작업보다 훨씬 넓은 시간이 트랜잭션으로 묶인다.

문제는 단순 성능 저하가 아니다.

- 락 유지 시간이 길어진다
- 예외 원인이 웹 계층과 DB 계층 사이에서 섞인다
- OSIV와 결합되면 경계가 더 흐려진다

컨트롤러는 HTTP 요청/응답 경계고, 트랜잭션은 유스케이스 경계다. 둘은 보통 일치하지 않는다.

### 2. repository마다 습관적으로 트랜잭션을 붙인다

repository 메서드마다 `@Transactional`을 붙이면, 상위 유스케이스가 경계를 소유하지 못한다.

예를 들어 주문 저장과 재고 차감이 서로 다른 repository/서비스의 개별 트랜잭션으로 커밋되면:

- 주문은 저장됐는데 재고 차감은 실패
- 재고는 줄었는데 쿠폰 사용은 실패

같은 문제가 나온다.

repository는 보통 **데이터 접근 단위**이지 **비즈니스 커밋 단위**가 아니다.

### 3. 상위 orchestrator를 비트랜잭션으로 두고 하위 서비스가 각각 커밋한다

이건 규모가 커질수록 자주 나오는 실수다.

```java
public void checkout() {
    orderService.createOrder();
    inventoryService.decrease();
    couponService.use();
}
```

겉보기엔 서비스 계층이지만, `checkout()`에 경계가 없고 각 하위 서비스만 `@Transactional`이면 사실상 세 번 커밋하는 구조가 된다.

이 패턴의 문제는 장애가 났을 때 "무엇이 이미 반영됐는가"가 유스케이스 기준으로 설명되지 않는다는 점이다.

### 4. `private` 메서드나 내부 호출에 붙여 놓고 믿는다

가장 유명하지만 여전히 반복되는 실수다.

```java
@Service
public class OrderService {

    public void placeOrder() {
        writeOrder();
    }

    @Transactional
    private void writeOrder() {
        // ...
    }
}
```

이 코드는 의도한 경계를 만들지 못한다.

- `private`이라 프록시 적용 대상이 아니다
- 내부 호출이라 프록시를 우회한다

즉, annotation의 위치가 아니라 **호출 경로**가 중요하다.

### 5. 원격 호출까지 같은 트랜잭션으로 묶는다

결제 승인 API, 배송 예약 API, 알림 전송 같은 외부 호출을 DB 쓰기와 한 트랜잭션처럼 취급하면 설계가 꼬이기 쉽다.

- DB 트랜잭션은 로컬 자원에 대한 원자성만 보장한다
- 외부 시스템은 같은 롤백 경계에 자연스럽게 들어오지 않는다
- 실패 시 보상 트랜잭션이나 outbox가 더 현실적인 선택이다

`@Transactional`을 붙였다고 시스템 전체가 분산 트랜잭션처럼 동작하는 것은 아니다.

### 6. `REQUIRES_NEW`를 "문제 해결용 분리 버튼"처럼 쓴다

실패 전파가 불편하다고 안쪽 서비스에 `REQUIRES_NEW`를 넣기 시작하면, 설계가 곧바로 부분 커밋 구조로 바뀐다.

의도된 감사 로그라면 괜찮지만, 핵심 상태 변경에 무심코 들어가면 다음이 생긴다.

- 롤백돼야 할 데이터가 일부 남는다
- 장애 분석이 어려워진다
- 커넥션 풀 압박이 커진다

`REQUIRES_NEW`는 배치 위치의 문제가 아니라 **커밋 의미를 바꾸는 선택**이다.

---

## 실전 시나리오

### 시나리오 1: 체크아웃 경계를 상위 서비스가 소유한다

좋은 기본형은 아래와 같다.

```java
@Service
public class CheckoutService {
    private final OrderService orderService;
    private final InventoryService inventoryService;
    private final CouponService couponService;

    @Transactional
    public Long checkout(CheckoutCommand command) {
        Order order = orderService.create(command);
        inventoryService.decrease(command.items());
        couponService.use(command.couponId());
        return order.getId();
    }
}
```

이 구조에서는 커밋 단위가 `checkout` 유스케이스와 일치한다.

하위 서비스는 트랜잭션을 "소유"하기보다 현재 경계 안에서 도메인 작업을 수행한다.

### 시나리오 2: 상위 서비스에 경계가 없어서 부분 커밋이 발생한다

```java
@Service
public class CheckoutFacade {
    private final OrderService orderService;
    private final InventoryService inventoryService;

    public void checkout() {
        orderService.createOrder();
        inventoryService.decrease();
    }
}
```

```java
@Service
public class OrderService {
    @Transactional
    public void createOrder() {
        // commit A
    }
}
```

```java
@Service
public class InventoryService {
    @Transactional
    public void decrease() {
        // commit B
    }
}
```

이 구조는 "서비스 계층에 `@Transactional`이 있다"는 말만 보면 맞아 보이지만, 실제로는 유스케이스가 원자적이지 않다.

### 시나리오 3: 외부 결제 승인 때문에 트랜잭션이 길어진다

```java
@Transactional
public void placeOrder(PlaceOrderCommand command) {
    Order order = orderRepository.save(Order.create(command));
    paymentGateway.approve(command.payment()); // 느린 외부 호출
    order.markPaid();
}
```

이 코드는 DB 락과 외부 네트워크 지연을 한 경계에 묶는다.

더 나은 방향은 보통 둘 중 하나다.

- 결제 승인을 먼저 받고 짧은 DB 트랜잭션으로 주문 반영
- 주문을 `PENDING`으로 저장하고 커밋 후 결제/이벤트 처리

어느 쪽이 맞는지는 비즈니스의 보상 가능성에 따라 다르다.

### 시나리오 4: 내부 서비스는 `MANDATORY`로 보호한다

```java
@Service
public class InventoryService {

    @Transactional(propagation = Propagation.MANDATORY)
    public void decrease(List<OrderItem> items) {
        // 재고 차감은 반드시 상위 유스케이스 경계 안에서만 수행
    }
}
```

이 방식은 재고 차감이 단독 호출되어도 된다는 잘못된 사용을 빨리 깨뜨린다.

모든 곳에 필요한 패턴은 아니지만, "반드시 상위 유스케이스에 소속돼야 하는 상태 변경"에는 효과적이다.

---

## 코드로 보기

### 나쁜 예: 컨트롤러가 경계를 소유한다

```java
@RestController
public class OrderController {

    @PostMapping("/orders")
    @Transactional
    public OrderResponse create(@RequestBody CreateOrderRequest request) {
        Order order = orderService.create(request);
        auditClient.send(order.getId());
        return OrderResponse.from(order);
    }
}
```

문제는 웹 요청 처리와 외부 호출이 모두 트랜잭션 범위에 들어간다는 점이다.

### 좋은 예: application service가 유스케이스 경계를 소유한다

```java
@Service
public class OrderApplicationService {
    private final OrderDomainService orderDomainService;
    private final OrderRepository orderRepository;

    @Transactional
    public Long createOrder(CreateOrderCommand command) {
        Order order = orderDomainService.create(command);
        orderRepository.save(order);
        return order.getId();
    }
}
```

이 구조에서는 컨트롤러는 요청을 번역하고, application service가 커밋 의미를 소유한다.

### 좋은 예: 외부 부작용을 after-commit 또는 outbox로 분리한다

```java
@Transactional
public Long createOrder(CreateOrderCommand command) {
    Order order = orderRepository.save(Order.create(command));
    eventPublisher.publishEvent(new OrderCreatedEvent(order.getId()));
    return order.getId();
}
```

이후 커밋 이후 phase에서 알림이나 외부 연동을 처리하면, 핵심 상태 변경과 느린 부작용을 같은 트랜잭션으로 묶지 않을 수 있다.

### 좋은 예: query service는 read-only 의도를 드러낸다

```java
@Service
public class OrderQueryService {

    @Transactional(readOnly = true)
    public OrderDetailResponse find(Long orderId) {
        Order order = orderRepository.findDetail(orderId).orElseThrow();
        return OrderDetailResponse.from(order);
    }
}
```

이렇게 하면 읽기 경계와 쓰기 경계가 자연스럽게 분리된다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| application service 단일 경계 | 유스케이스와 커밋이 일치한다 | 상위 서비스 책임이 커질 수 있다 | 일반적인 명령 유스케이스 |
| 하위 서비스 개별 경계 | 코드가 분리돼 보인다 | 부분 커밋과 추적 비용이 커진다 | 독립 작업일 때만 제한적으로 |
| controller 경계 | 구현이 단순해 보인다 | 웹 처리 시간까지 트랜잭션이 길어진다 | 보통 권장하지 않음 |
| `MANDATORY` 내부 보호 | 잘못된 호출을 빨리 드러낸다 | 설계 의도를 팀이 공유해야 한다 | 반드시 상위 경계에 종속된 쓰기 |
| outbox / after-commit 분리 | 외부 부작용을 짧은 DB 트랜잭션 밖으로 민다 | 즉시성과 운영 복잡도가 늘 수 있다 | 외부 연동 신뢰성이 중요할 때 |

핵심은 "어디에 붙이면 편한가"가 아니라, **어떤 실패를 함께 묶고 어떤 부작용은 분리할 것인가**다.

---

## 꼬리질문

> Q: `@Transactional`의 기본 위치를 왜 controller가 아니라 application service로 두는가?
> 의도: HTTP 경계와 유스케이스 경계의 차이 이해 확인
> 핵심: 컨트롤러는 요청/응답을 다루고, 트랜잭션은 비즈니스 상태 전이를 원자적으로 묶기 때문이다.

> Q: 하위 서비스마다 `@Transactional`이 있으면 왜 위험할 수 있는가?
> 의도: 부분 커밋과 유스케이스 원자성 이해 확인
> 핵심: 상위 유스케이스가 하나여도 실제 커밋은 여러 번 일어날 수 있다.

> Q: `REQUIRES_NEW`를 쉽게 도입하면 왜 설계가 급격히 바뀌는가?
> 의도: 전파 옵션이 커밋 의미를 바꾼다는 점 확인
> 핵심: 단순한 예외 회피가 아니라 독립 커밋과 추가 커넥션 사용을 만든다.

> Q: 내부 상태 변경 서비스에 `MANDATORY`를 검토하는 이유는 무엇인가?
> 의도: 트랜잭션 소유권 명시의 의미 확인
> 핵심: 반드시 상위 유스케이스 안에서만 실행돼야 하는 쓰기를 보호하기 위해서다.

---

## 한 줄 정리

`@Transactional`은 서비스 "레이어"에 두는 것이 아니라, 하나의 유스케이스를 책임지는 서비스 "경계"에 두고, 원격 호출과 독립 부작용은 그 밖으로 밀어내는 쪽이 실무적으로 안전하다.

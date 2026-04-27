# Spring Self-Invocation 공통 오해 1페이지 카드: "`@Transactional`만 문제"가 아니다

> 한 줄 요약: self-invocation(내부 호출)은 `@Transactional` 전용 버그가 아니라, "프록시를 안 지나면 annotation 기능이 빠질 수 있다"는 공통 규칙이다.

**난이도: 🟢 Beginner**

관련 문서:

- [AOP 기초: 관점 지향 프로그래밍이 왜 필요한가](./spring-aop-basics.md)
- [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md)
- [Spring `@Transactional` Self-invocation 검증 테스트 브리지: `@Bean` self-call identity 테스트와 무엇이 다른가](./spring-transactional-self-invocation-test-bridge-primer.md)
- [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
- [JDBC / JPA / MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: self invocation primer, transactional only misconception, transactional만 문제 오해, self invocation 공통 오해, proxy bypass beginner, internal call proxy bypass, this method transactional async cacheable, transactional async cacheable 공통 규칙, self invocation 1페이지 카드, why transactional not applied beginner, why async not async self invocation, 프록시 안 지나면 annotation 안 먹음, spring self invocation transactional only misconception primer basics, spring self invocation transactional only misconception primer beginner, spring self invocation transactional only misconception primer intro

## 먼저 mental model 한 줄

annotation이 일을 하는 게 아니라, **프록시가 그 annotation을 보고 중간에서 끼어든다.**

이 카드에서 `self-invocation`은 계속 **같은 클래스 안에서 `this.method()`로 다시 부르는 내부 호출**이라는 뜻으로 쓴다.

그래서 같은 클래스 안에서 `this.method()`로 바로 들어가면 "`@Transactional`이 안 먹는다"가 아니라, 더 정확히는 **프록시를 안 지나서 프록시 기반 기능이 빠질 수 있다**가 맞다.

## 30초 비교표

| 지금 붙인 annotation | 초급자가 기대하는 것 | self-invocation이면 어떻게 보이나 |
|---|---|---|
| `@Transactional` | 트랜잭션 시작/커밋/롤백 | 트랜잭션이 안 열리거나 rollback 기대가 깨짐 |
| `@Async` | 다른 스레드에서 비동기 실행 | 그냥 현재 스레드에서 바로 실행됨 |
| `@Cacheable` | 캐시 적중 후 원본 호출 생략 | 매번 실제 메서드가 다시 실행됨 |
| `@Validated` | 메서드 인자/리턴값 검증 | 검증이 조용히 빠질 수 있음 |
| `@PreAuthorize` | 메서드 호출 전 권한 검사 | 내부 호출 경로에서는 보안 검사가 안 걸릴 수 있음 |

핵심은 annotation 이름이 아니라 호출 경로다.

## 한 장으로 보는 구조

```text
외부 Bean 호출 -> 프록시 -> annotation 기능 적용 -> 실제 메서드
같은 클래스 내부 호출 -> 실제 메서드 직행 -> annotation 기능 누락 가능
```

이걸 초급자 언어로 바꾸면 아래처럼 기억하면 된다.

- 다른 Bean이 불러 주면 정문으로 들어간다.
- 같은 클래스 안에서 `this.method()`로 부르면 옆문으로 바로 들어간다.
- 문제는 "`@Transactional`이 예민해서"가 아니라 정문을 안 지났다는 점이다.

## 작은 예시 하나로 끝내기

```java
@Service
public class BillingService {

    public void issueBill() {
        this.writeBill();      // 프록시 우회
        this.sendReceipt();    // 프록시 우회
    }

    @Transactional
    public void writeBill() {
    }

    @Async
    public void sendReceipt() {
    }
}
```

위 코드는 annotation이 두 개라서 다른 문제처럼 보이지만, 초급자 기준 원인은 하나로 묶인다.

- `writeBill()`이 안 묶이면 "`@Transactional`이 왜 안 먹지?"라고 느낀다.
- `sendReceipt()`가 동기처럼 보이면 "`@Async`가 왜 안 먹지?"라고 느낀다.
- 하지만 둘 다 실제 원인은 `this.` 내부 호출로 프록시를 안 탔기 때문이다.

## `@Async`는 스레드 이름만 봐도 1차 확인이 된다

초급자에게 가장 빠른 확인법은 "정말 다른 스레드로 갔는가"를 로그 한 줄로 보는 것이다.

## 전: 같은 클래스 내부 호출이라 프록시를 우회한 경우

```java
@Service
public class BillingService {

    public void issueBill() {
        System.out.println("issueBill thread = " + Thread.currentThread().getName());
        this.sendReceipt();
    }

    @Async
    public void sendReceipt() {
        System.out.println("sendReceipt thread = " + Thread.currentThread().getName());
    }
}
```

예상 로그:

```text
issueBill thread = http-nio-8080-exec-1
sendReceipt thread = http-nio-8080-exec-1
```

둘 다 같은 이름이면 "`@Async`가 아예 안 붙었나?"보다 먼저 **프록시를 우회했나**를 의심하는 편이 맞다.

## 후: 다른 Bean으로 분리해 프록시를 타게 한 경우

```java
@Service
public class BillingFacade {

    private final ReceiptSender receiptSender;

    public BillingFacade(ReceiptSender receiptSender) {
        this.receiptSender = receiptSender;
    }

    public void issueBill() {
        System.out.println("issueBill thread = " + Thread.currentThread().getName());
        receiptSender.sendReceipt();
    }
}

@Service
public class ReceiptSender {

    @Async
    public void sendReceipt() {
        System.out.println("sendReceipt thread = " + Thread.currentThread().getName());
    }
}
```

예상 로그:

```text
issueBill thread = http-nio-8080-exec-1
sendReceipt thread = task-1
```

핵심은 로그 문자열 자체가 아니라 **호출 스레드와 실행 스레드가 갈라졌는가**다.

## 스레드 로그를 어떻게 읽나

| 로그 모양 | 초급자용 해석 | 다음 확인 |
|---|---|---|
| 두 줄이 같은 스레드 이름 | `@Async`가 동기처럼 실행됐다 | self-invocation, `private`, 직접 `new` 여부 |
| `sendReceipt`만 다른 스레드 이름 | 프록시를 타고 비동기로 넘어갔을 가능성이 높다 | executor 이름, 예외 관측 방식 |

주의:

- 같은 스레드 로그가 곧바로 "`@EnableAsync`가 없다"의 증거는 아니다.
- 초급 단계에서는 먼저 **프록시를 탔는지**부터 확인하는 편이 더 빠르다.
- `@Async`가 실제로 분리돼도, 이후 문제는 [`Spring Scheduler / Async Boundaries`](./spring-scheduler-async-boundaries.md)나 [`Spring `@Transactional` and `@Async` Composition Traps`](./spring-transactional-async-composition-traps.md)에서 이어서 본다.

## 흔한 오해 바로잡기

| 흔한 말 | 왜 반만 맞나 | 더 정확한 말 |
|---|---|---|
| "`@Transactional`만 원래 까다롭다" | 트랜잭션 증상이 가장 먼저 보여서 그렇다 | 프록시 기반 annotation 전반이 같은 구조 함정을 공유한다 |
| "`public`으로 바꾸면 해결된다" | 메서드 경계는 열리지만 호출 경로 문제는 남을 수 있다 | `public` + 프록시 경유 호출을 같이 봐야 한다 |
| "`self-injection`이 정답이다" | 우회는 가능하지만 구조 이해를 숨길 수 있다 | 기본 해법은 다른 Bean으로 경계를 분리하는 것이다 |

## 처음 수정할 때의 기본 답

가장 먼저 보는 선택지는 보통 이것 하나다.

| 지금 코드 모양 | 첫 수정 방향 |
|---|---|
| 한 서비스 안에서 `this.method()`로 다시 부른다 | 프록시 기능이 필요한 메서드를 다른 Bean으로 분리한다 |

```java
@Service
public class BillingFacade {
    private final BillingWorker billingWorker;

    public void issueBill() {
        billingWorker.writeBill();
        billingWorker.sendReceipt();
    }
}
```

이 구조가 초급자에게 좋은 이유는 "`왜 동작하나`"가 눈에 보이기 때문이다.

- 호출이 다른 Bean으로 나간다.
- 그 Bean 앞에 프록시가 설 수 있다.
- 그래서 `@Transactional`, `@Async` 같은 기능이 다시 적용된다.

## 여기서 어디로 가면 되나

| 지금 필요한 것 | 다음 문서 |
|---|---|
| self-invocation 자체를 가장 짧게 이해하고 싶다 | [AOP 기초](./spring-aop-basics.md) |
| `@Transactional` 증상부터 다시 잡고 싶다 | [@Transactional 기초](./spring-transactional-basics.md) |
| `@Bean` self-call identity 테스트와 왜 검증 방식이 다른지 먼저 분리하고 싶다 | [Spring `@Transactional` Self-invocation 검증 테스트 브리지](./spring-transactional-self-invocation-test-bridge-primer.md) |
| `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`까지 한 번에 비교하고 싶다 | [Spring Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md) |
| 코드를 바로 어떻게 나눌지 보고 싶다 | [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md) |

## 한 줄 정리

self-invocation은 "`@Transactional`만 문제"가 아니라, **프록시를 안 타면 프록시 기반 annotation 전체가 같은 방식으로 흔들릴 수 있다**는 입문 규칙이다.

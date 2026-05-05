# Spring `@Async` 내부 호출 증상 카드: 같은 스레드 로그를 async 설정 버그로 오해할 때

> 한 줄 요약: `@Async` 메서드 로그가 caller와 같은 스레드에서 찍히면 executor 설정부터 의심하기 전에, 먼저 그 호출이 프록시 정문을 탔는지 확인해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Self-Invocation 공통 오해 1페이지 카드: "`@Transactional`만 문제"가 아니다](./spring-self-invocation-transactional-only-misconception-primer.md)
- [AOP 기초: 관점 지향 프로그래밍이 왜 필요한가](./spring-aop-basics.md)
- [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
- [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)
- [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)
- [OS: 동기/비동기, blocking/non-blocking 기초](../operating-system/sync-async-blocking-nonblocking-basics.md)

retrieval-anchor-keywords: async same thread, async self invocation, async proxy bypass, same thread log async, @async not working, enableasync misconception, task executor misconception, this send async, bean split async, caller worker async, proxy rule symptom, async config bug, async 안 돼요 왜, 처음 배우는데 async, async 뭐예요

## 먼저 mental model 한 줄

`@Async`가 "스레드를 바꾸는 마법"처럼 보여도, 실제로는 **프록시가 메서드 호출을 가로채 worker thread로 넘겨 주는 구조**다.

그래서 같은 클래스 안에서 `this.sendMail()`처럼 부르면 `@Async`가 틀린 게 아니라, **프록시를 거치지 못해 동기 호출처럼 보일 수 있다.**

이 카드에서는 `this.method()` / `private` / 직접 `new`를 매번 따로 나열하지 않고, **프록시 정문 3문항**으로 묶어 읽는다.

| 정문 3문항 신호 | 초급자용 해석 | 첫 확인 |
|---|---|---|
| `this.method()` | 같은 집 안에서 바로 다시 불렀다 | 호출을 다른 Bean으로 뺐는지 |
| `private` 메서드 | 프록시가 설 문이 닫혀 있다 | `public` 경계로 올려야 하는지 |
| 직접 `new` | 스프링 밖 객체라 프록시를 못 건다 | DI 받은 Bean인지 |

## 이 증상은 이렇게 읽는다

| 보인 증상 | 초급자 오해 | 먼저 볼 것 |
|---|---|---|
| `caller`와 `@Async` 로그가 같은 스레드 이름 | `@EnableAsync`를 빼먹었다 | 같은 클래스 내부 호출인지 |
| `task-1`, `applicationTaskExecutor-1` 같은 이름이 안 보임 | executor bean 등록이 틀렸다 | 위 `프록시 정문 3문항`부터 본다 |
| 로컬에서는 동기처럼 보이는데 Bean 분리 후 갑자기 다른 스레드로 감 | 환경 차이 버그다 | 프록시 경유 여부가 달라졌는지 |

같은 스레드 로그는 "설정 버그 확정"이 아니라 **프록시 우회 신호일 수 있다**가 첫 판단이다.

처음 검색할 때는 아래처럼 문장을 바로 바꿔 읽으면 덜 헷갈린다.

| 학습자가 실제로 치는 질문 | 이 카드에서 먼저 답하는 것 |
|---|---|
| "`@Async` 안 돼요. 왜 같은 스레드예요?" | 설정 전 점검보다 호출 경로가 프록시를 탔는지 본다 |
| "`@EnableAsync` 붙였는데 왜 그대로예요?" | `@EnableAsync` 유무만으로는 내부 호출 우회를 못 막는다 |
| "Bean 분리하니까 갑자기 async가 되는데 왜죠?" | 기능이 바뀐 게 아니라 프록시가 끼어들 자리가 생긴 것이다 |

## 가장 흔한 오진 예시

```java
@Service
public class BillingService {

    public void issueBill() {
        System.out.println("issueBill = " + Thread.currentThread().getName());
        this.sendReceipt();
    }

    @Async
    public void sendReceipt() {
        System.out.println("sendReceipt = " + Thread.currentThread().getName());
    }
}
```

예상 로그:

```text
issueBill = http-nio-8080-exec-1
sendReceipt = http-nio-8080-exec-1
```

이때 초급자는 "`@EnableAsync`가 없나?"로 바로 뛰기 쉽다. 하지만 이 코드는 먼저 **`this.sendReceipt()`가 프록시를 우회했는지**를 봐야 한다.

## 첫 수정은 설정 추가보다 Bean 경계 분리다

```java
@Service
public class BillingFacade {
    private final ReceiptSender receiptSender;

    public BillingFacade(ReceiptSender receiptSender) {
        this.receiptSender = receiptSender;
    }

    public void issueBill() {
        receiptSender.sendReceipt();
    }
}

@Service
public class ReceiptSender {
    @Async
    public void sendReceipt() {
    }
}
```

이 구조가 초급자에게 좋은 이유는 단순하다.

- `BillingFacade`는 호출을 맡는다.
- `ReceiptSender`는 비동기 일을 맡는다.
- 다른 Bean 호출이 되면서 `@Async` 프록시가 끼어들 자리가 생긴다.

즉 첫 수리는 "executor 옵션 더 붙이기"보다 **호출 경로를 프록시가 탈 수 있게 만들기**다.

## 그래도 설정 문제는 언제 보나

프록시 우회가 아닌 게 확인된 뒤에 설정을 본다.

1. `@Async` 메서드가 Spring Bean의 `public` 메서드인가
2. 다른 Bean에서 호출했는가
3. 그래도 같은 스레드면 그때 `@EnableAsync`, executor bean 이름, 테스트 대역 설정을 본다

이 순서를 뒤집으면, "구조 문제를 설정 문제로 오진"하기 쉽다.

비유로는 "`@Async`는 옆문으로 새는 호출을 worker에게 태워 주는 정문 직원"처럼 이해하면 쉽다. 다만 이 비유는 **프록시가 개입하는 순간까지만** 맞고, 실제 스레드 생성과 큐잉 정책은 executor 설정이 따로 결정한다.

## 어디로 이어서 읽나

- self-invocation 자체를 1분 안에 다시 잡고 싶으면 [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md)
- `프록시 정문 3문항` 원리를 한 번에 다시 보고 싶으면 [AOP 기초](./spring-aop-basics.md)
- `@Async`와 `@Transactional`이 같이 있을 때 왜 더 헷갈리는지 보려면 [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)

## 한 줄 정리

`@Async` 로그가 같은 스레드에서 찍히면 "설정이 틀렸나?"보다 먼저 "프록시를 안 타고 내부 호출했나?"를 확인하는 편이 빠르다.

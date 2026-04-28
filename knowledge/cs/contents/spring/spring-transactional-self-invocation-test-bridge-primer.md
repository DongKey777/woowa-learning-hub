# Spring `@Transactional` Self-invocation 검증 테스트 브리지: `@Bean` self-call identity 테스트와 무엇이 다른가

> 한 줄 요약: `@Bean` self-call은 "같은 객체인가?"를 identity로 확인하지만, `@Transactional` self-invocation은 "트랜잭션 동작이 실제로 걸렸는가?"를 behavior로 확인해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Self-invocation(내부 호출) 검증 테스트 미니 가이드: `assertSame` / `assertNotSame`로 수정 전후를 바로 확인하기](./spring-self-call-verification-test-mini-guide.md)
- [Spring Self-Invocation 공통 오해 1페이지 카드: "`@Transactional`만 문제"가 아니다](./spring-self-invocation-transactional-only-misconception-primer.md)
- [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
- [JDBC / JPA / MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md)

retrieval-anchor-keywords: transactional self invocation test, transactional self invocation beginner, transactional proxy bypass test, assertsame not enough transactional, bean self call vs transactional, transaction active test, rollback behavior test, identity vs behavior test, spring transactional test bridge, transactional 안 먹어요 test, self invocation 헷갈려, behavior verification basics

## 먼저 mental model 한 줄

이 문서에서 `self-invocation`은 **같은 클래스 안에서 `this.method()`로 다시 부르는 내부 호출**이라고 읽으면 된다.

둘 다 "self-invocation"처럼 보이지만, 테스트 질문이 다르다.

- `@Bean` self-call: **컨테이너 Bean과 실제 주입 객체가 같은가**
- `@Transactional` self-invocation: **프록시가 끼어들어 트랜잭션 동작이 실제로 적용됐는가**

초급자 기준으로 기억할 문장은 이것 하나면 충분하다.

**`@Bean` self-call은 identity 테스트, `@Transactional` self-invocation은 behavior 테스트다.**

## 처음 헷갈릴 때 20초 분기

| 지금 머릿속 질문 | 먼저 보는 기준 | 추천 검증 |
|---|---|---|
| "`assertSame` 했는데 왜 아직도 `@Transactional`이 안 먹어요?" | 같은 객체인지와 트랜잭션 동작은 다른 질문이다 | transaction active, commit/rollback 결과 확인 |
| "처음인데 `self-call`이랑 self-invocation이 같은 말인가요?" | 둘 다 내부 호출 문맥이지만, 문서마다 검증 질문이 다를 수 있다 | 이 문서에서는 behavior 쪽만 본다 |
| "무엇을 수정해야 하나요?" | annotation 옵션보다 호출 경로가 먼저다 | 다른 Bean으로 경계 분리 후 다시 테스트 |

## 20초 비교표

| 상황 | 먼저 던질 질문 | 잘 맞는 검증 | 초급자가 자주 고르는 잘못된 검증 |
|---|---|---|---|
| `@Configuration`의 `@Bean` self-call | 같은 Bean을 재사용했나? | `assertSame` / `assertNotSame` | "`@Transactional`처럼 동작 로그를 보면 되겠지" |
| `@Transactional` 내부 호출 | 트랜잭션이 실제로 시작됐나? | transaction active, commit/rollback, DB side effect 확인 | `assertSame(service, bean)` 같은 identity 확인 |

핵심은 "`self-invocation`이라는 단어가 같아도, 검증 신호는 같지 않다"는 점이다.

## 왜 `@Transactional`은 identity 테스트로 안 풀리나

`@Transactional`에서 초급자가 보고 싶은 것은 보통 이것들이다.

- 트랜잭션이 열렸는가
- 예외가 나면 rollback 됐는가
- 읽기/쓰기 경계가 의도대로 적용됐는가

이 질문들은 객체가 같은지와 거의 직접 연결되지 않는다.

```java
var service = context.getBean(BillingService.class);
assertSame(service, context.getBean(BillingService.class));
```

위 테스트는 Bean 조회가 같은 인스턴스를 돌려준다는 사실만 보여 준다.
하지만 이걸로는 `this.writeBill()`가 프록시를 탔는지, 트랜잭션이 열렸는지 전혀 알 수 없다.

## 가장 작은 `@Transactional` 동작 검증 예제

아래처럼 "호출 경로만 바꿨을 때 transaction active가 달라지는가"만 보면 된다.

```java
@Service
class BillingService {
    boolean issueBill() {
        return writeBill();
    }

    @Transactional
    boolean writeBill() {
        return TransactionSynchronizationManager.isActualTransactionActive();
    }
}
```

```java
@Service
class BillingFacade {
    private final BillingWorker billingWorker;

    boolean issueBill() {
        return billingWorker.writeBill();
    }
}

@Service
class BillingWorker {
    @Transactional
    boolean writeBill() {
        return TransactionSynchronizationManager.isActualTransactionActive();
    }
}
```

```java
assertFalse(billingService.issueBill()); // 내부 호출
assertTrue(billingFacade.issueBill());   // 다른 Bean 호출
```

- `BillingService.issueBill()` 안의 `writeBill()`은 같은 객체 내부 호출이라 프록시를 우회한다.
- 그래서 `@Transactional`이 붙어 있어도 transaction active가 `false`일 수 있다.
- 다른 Bean인 `BillingWorker`로 경계를 나누면 프록시를 타기 쉬워지고, 그때는 `true`를 기대할 수 있다.

## 왜 이 예제가 초급자에게 안전한가

이 예제는 옵션을 많이 보지 않고도 핵심만 보여 준다.

- 같은 클래스 내부 호출이면 `false`
- 다른 Bean을 거치면 `true`

즉 처음에는 `propagation`, `rollbackFor`보다 "`정문인 프록시를 지났나`"만 확인해도 충분하다.

## 무엇을 assert해야 하나

`@Transactional` self-invocation에서는 아래처럼 **동작 신호**를 고른다.

| 보고 싶은 것 | 추천 신호 |
|---|---|
| 트랜잭션이 실제로 열렸는가 | `TransactionSynchronizationManager.isActualTransactionActive()` |
| rollback이 실제로 일어났는가 | 예외 후 DB 상태 재조회 |
| commit 경계가 분리됐는가 | 호출 전후 저장 결과, 로그, 이벤트 발행 시점 |

반대로 아래는 보조 정보일 뿐 핵심 검증이 아니다.

- service 객체 identity
- 프록시 클래스명 문자열
- `AopUtils.isAopProxy(...)`만 확인하고 끝내기

이런 체크는 "프록시가 있을 수도 있다"는 힌트는 주지만, **원하는 트랜잭션 동작이 진짜 발생했는지**까지 대신 증명해 주지는 않는다.

## 자주 헷갈리는 포인트

- `@Bean` self-call 문서에서 `assertSame`을 봤다고 해서, `@Transactional`도 같은 방식으로 검증하면 안 된다.
- `@Transactional` self-invocation은 "같은 인스턴스냐"보다 "`this.` 내부 호출이라 프록시를 안 지났나"를 봐야 한다.
- 초급 단계에서는 `AopContext.currentProxy()` 같은 우회보다, 다른 Bean으로 경계를 분리하고 동작을 다시 검증하는 쪽이 더 읽기 쉽다.

## 다음 한 걸음

- 테스트가 왜 필요한지부터 다시 묶고 싶으면 [`@Transactional 기초`](./spring-transactional-basics.md)로 돌아간다.
- "`@Transactional`만의 예외가 아니라 프록시 공통 규칙인가?"가 궁금하면 [`Spring Self-Invocation 공통 오해 1페이지 카드`](./spring-self-invocation-transactional-only-misconception-primer.md)로 이어간다.
- service 분리 패턴까지 보고 싶으면 [`Spring Service-Layer Transaction Boundary Patterns`](./spring-service-layer-transaction-boundary-patterns.md)를 본다.

## 어디로 이어서 보면 되나

1. `@Bean` self-call과 헷갈린다면 먼저 [Spring Self-invocation(내부 호출) 검증 테스트 미니 가이드](./spring-self-call-verification-test-mini-guide.md)에서 identity 테스트 질문을 분리한다.
2. "`@Transactional`만 문제인가?"가 헷갈리면 [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md)로 가서 프록시 규칙을 다시 잡는다.
3. 트랜잭션 경계를 실제 서비스 설계로 옮기려면 [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)로 이어서 본다.

## 한 줄 정리

`@Transactional` self-invocation은 `assertSame`보다 "내부 호출이 프록시를 탔는가, 그래서 트랜잭션 동작이 실제로 보였는가"를 검증해야 초급자가 덜 헷갈린다.

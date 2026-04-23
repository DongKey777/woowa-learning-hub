# @Transactional 기초: 트랜잭션 어노테이션이 하는 일

> 한 줄 요약: `@Transactional`은 메서드 실행을 하나의 트랜잭션으로 묶어 주는 어노테이션이고, 실제 동작은 Spring이 생성한 프록시가 메서드 호출 전후로 begin/commit/rollback을 대신 처리하는 것이다.

**난이도: 🟢 Beginner**

관련 문서:

- [@Transactional 깊이 파기](./transactional-deep-dive.md)
- [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
- [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: transactional basics, @transactional 입문, spring transaction beginner, spring 트랜잭션이 뭐예요, transactional annotation how it works, spring proxy transaction, begin commit rollback spring, transactional method beginner, transactional rollback default, unchecked exception rollback, checked exception rollback, @transactional readonly, spring transaction 기초

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

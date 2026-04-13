# Spring Transactional Test Rollback Misconceptions

> 한 줄 요약: `@Transactional` 테스트가 자동으로 모든 부작용을 되돌린다고 믿으면 안 되며, 트랜잭션 범위 밖의 작업은 그대로 남을 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
> - [Spring Testcontainers Boundary Strategy](./spring-testcontainers-boundary-strategy.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls](./spring-transaction-synchronization-aftercommit-pitfalls.md)

retrieval-anchor-keywords: transactional test, rollback misconception, test transaction, integration test rollback, test managed transaction, commit in tests, async side effects, database cleanup

## 핵심 개념

Spring 테스트에서 `@Transactional`을 붙이면 보통 테스트 메서드가 끝나고 롤백된다.

하지만 이것이 의미하는 것은 "DB 트랜잭션 안에 있는 변경"일 뿐이다.

- 비동기 작업
- 외부 API 호출
- 파일 생성
- 다른 transaction manager 커밋

이런 것들은 그대로 남을 수 있다.

## 깊이 들어가기

### 1. 테스트 트랜잭션은 테스트 경계에 묶인다

테스트 프레임워크가 관리하는 transaction과 실제 애플리케이션 로직의 경계는 다를 수 있다.

### 2. 커밋을 강제하는 코드가 있으면 롤백과 무관하다

`REQUIRES_NEW` 같은 별도 경계는 테스트 롤백과 분리될 수 있다.

이 문맥은 [@Transactional 깊이 파기](./transactional-deep-dive.md)와 [Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls](./spring-transaction-synchronization-aftercommit-pitfalls.md)와 같이 봐야 한다.

### 3. async side effect는 롤백되지 않는다

`@Async`로 보낸 작업은 테스트 트랜잭션과 별개로 실행될 수 있다.

### 4. DB rollback만으로는 충분하지 않다

테스트 후 데이터 정리는 DB, queue, cache, filesystem, external service를 모두 고려해야 한다.

### 5. commit을 검증하고 싶다면 별도 테스트가 필요하다

트랜잭션 롤백을 기대하는 테스트와 실제 commit 흐름을 검증하는 테스트는 다르게 설계해야 한다.

## 실전 시나리오

### 시나리오 1: 테스트가 끝났는데 outbox row가 남는다

별도 트랜잭션이나 비동기 relay 때문일 수 있다.

### 시나리오 2: DB는 깨끗한데 파일은 남는다

파일 시스템은 DB 롤백과 무관하다.

### 시나리오 3: 테스트는 롤백되는데 외부 API는 호출됐다

외부 side effect는 자동으로 되돌려지지 않는다.

### 시나리오 4: `@Commit` / `@Rollback(false)`를 남용한다

테스트가 서로에게 오염을 남길 수 있다.

## 코드로 보기

### transactional test

```java
@SpringBootTest
@Transactional
class OrderServiceTest {

    @Test
    void placeOrder() {
        orderService.placeOrder();
    }
}
```

### commit test

```java
@Commit
@Test
void shouldPersist() {
}
```

### async side effect

```java
@Async
public void sendMail() {
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| transactional test | DB cleanup이 쉽다 | commit 경로를 못 본다 | 일반 통합 테스트 |
| commit test | 실제 저장을 본다 | 오염 관리가 어렵다 | commit 검증 |
| manual cleanup | 명시적이다 | 번거롭다 | 외부 side effect |

핵심은 test rollback을 "만능 청소기"가 아니라, **DB 트랜잭션에만 적용되는 경계**로 이해하는 것이다.

## 꼬리질문

> Q: `@Transactional` 테스트가 모두 되돌리는 것은 무엇인가?
> 의도: 테스트 경계 이해 확인
> 핵심: 테스트 관리 트랜잭션 안의 DB 변경이다.

> Q: 왜 async side effect는 롤백되지 않는가?
> 의도: 트랜잭션과 스레드 경계 이해 확인
> 핵심: 다른 스레드/경계에서 실행되기 때문이다.

> Q: `@Commit`은 언제 쓰는가?
> 의도: commit path 검증 이해 확인
> 핵심: 실제 저장을 확인해야 할 때다.

> Q: DB rollback만으로 충분하지 않은 이유는 무엇인가?
> 의도: 외부 side effect 인식 확인
> 핵심: 파일, 메시지, 외부 호출은 따로 관리해야 한다.

## 한 줄 정리

Transactional test rollback은 DB 경계에만 적용되므로, async와 외부 side effect는 별도 정리와 검증이 필요하다.

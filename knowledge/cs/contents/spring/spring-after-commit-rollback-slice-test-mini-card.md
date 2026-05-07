---
schema_version: 3
title: Spring AFTER_COMMIT and Rollback Slice Test Mini Card
concept_id: spring/after-commit-rollback-slice-test-mini-card
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 84
review_feedback_tags:
- after-commit-rollback
- slice-test
- after-commit-test
- transactionaleventlistener-after-commit
aliases:
- AFTER_COMMIT test
- TransactionalEventListener after commit
- rollback slice test
- DataJpaTest after commit
- TestTransaction end
- flush is not commit
intents:
- definition
- troubleshooting
linked_paths:
- contents/spring/spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md
- contents/spring/spring-transactional-test-rollback-misconceptions.md
- contents/spring/spring-service-layer-external-io-after-commit-outbox-primer.md
- contents/spring/spring-eventlistener-transaction-phase-outbox.md
expected_queries:
- @TransactionalEventListener AFTER_COMMIT이 DataJpaTest에서 왜 안 돌아?
- flush를 했는데 after commit listener가 실행되지 않는 이유가 뭐야?
- rollback 기반 slice test로 commit 이후 동작을 검증해도 돼?
- TestTransaction.end를 언제 써야 해?
contextual_chunk_prefix: |
  이 문서는 @TransactionalEventListener(AFTER_COMMIT), flush와 commit 차이,
  @DataJpaTest rollback 기본값, TestTransaction.end와 @Commit을 beginner 관점에서
  분리한다. listener가 안 도는 이유가 로직 버그인지 commit이 없어서인지 먼저
  가르는 mini primer다.
---
# Spring Mini Card: 왜 rollback 기반 slice test만으로 `AFTER_COMMIT`를 끝까지 믿기 어려운가

> 한 줄 요약: `@TransactionalEventListener(AFTER_COMMIT)`는 **정말 commit이 끝났을 때만** 실행되므로, 기본이 rollback인 `@DataJpaTest` 같은 slice test는 "리스너 로직이 맞다"보다 "애초에 commit이 없었다"를 더 많이 검증한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `@DataJpaTest` Mental-Model Bridge: 런타임 트랜잭션 감각을 테스트에 그대로 옮기기](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)
- [Spring Transactional Test Rollback Misconceptions](./spring-transactional-test-rollback-misconceptions.md)
- [Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기](./spring-service-layer-external-io-after-commit-outbox-primer.md)
- [Spring EventListener / TransactionalEventListener / Outbox](./spring-eventlistener-transaction-phase-outbox.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: after commit test beginner, transactionaleventlistener after_commit test, datajpatest after commit, rollback based slice test, transactional event listener rollback test, commit visible test beginner, testtransaction after commit, slice test commit path, after commit listener not called test, beginner after commit primer, spring after commit rollback slice test mini card basics, spring after commit rollback slice test mini card beginner, spring after commit rollback slice test mini card intro, spring basics, beginner spring

## 먼저 mental model 한 줄

초급자는 이렇게 먼저 보면 된다.

- `flush()`는 SQL을 밀어내는 것
- commit은 트랜잭션을 끝내는 것
- `AFTER_COMMIT`은 이름 그대로 **commit 뒤**에만 돈다

즉 rollback 기반 테스트에서 보통 확인되는 것은 "`AFTER_COMMIT`이 안전하다"가 아니라, **"아직 commit 세계로 안 나갔다"**는 사실이다.

## 30초 비교표

| 테스트 상황 | 실제로 강하게 확인되는 것 | 놓치기 쉬운 것 |
|---|---|---|
| 기본 `@DataJpaTest` | repository, mapping, flush 시점, rollback 안쪽 동작 | commit 뒤에만 도는 listener 실행 |
| `flush()`까지 넣은 slice test | SQL/제약 조건이 중간에 드러나는지 | `AFTER_COMMIT` callback 실행 여부 |
| `@Commit` 또는 `TestTransaction.end()`를 쓴 테스트 | commit 뒤 후속 처리 경로 | test 오염 정리, 더 넓은 통합 경계 |

핵심은 이것이다.

**rollback 기반 slice test가 통과해도, 그것만으로 "`AFTER_COMMIT`이 운영처럼 잘 돈다"까지는 말할 수 없다.**

## 증상 문장으로 먼저 가르기

초급자는 아래처럼 **지금 막힌 말**로 먼저 분리하면 된다.

| 막힌 말 | 먼저 떠올릴 질문 |
|---|---|
| "`flush()`까지 했는데 listener가 안 돌아요" | commit이 실제로 있었나 |
| "`verify(..., never())`는 통과하는데 안심해도 되나요?" | rollback 때문에 원래 안 돈 것과 버그를 구분했나 |
| "`@DataJpaTest`에서 `AFTER_COMMIT`까지 보고 싶어요" | slice test 하나로 끝낼 문제인가, commit-visible 테스트를 따로 둘 문제인가 |

짧게 줄이면 아래 한 줄이다.

```text
안 도는 이유가 로직 버그인지, 아직 commit이 없어서인지 먼저 가른다
```

## 왜 이런 착시가 생기나

### 1. `flush`를 commit처럼 느끼기 쉽다

```java
testEntityManager.flush();
```

초급자 눈에는 "SQL도 나갔고 DB에도 들어갔으니 거의 끝난 것 아닌가?"처럼 보일 수 있다.
하지만 `AFTER_COMMIT` 기준에서는 아직 아니다.

- `flush`는 중간 동기화다
- rollback되면 그 SQL 결과도 최종 확정이 아니다
- listener phase는 `AFTER_FLUSH`가 아니라 `AFTER_COMMIT`이다

### 2. slice test의 기본값이 rollback이라 commit 자체가 없다

`@DataJpaTest`는 보통 테스트 메서드가 끝날 때 rollback된다.

그러면 아래 코드는 발행까지는 되더라도,

```java
@Transactional
public void placeOrder() {
    orderRepository.save(new Order());
    applicationEventPublisher.publishEvent(new OrderPlacedEvent());
}
```

이 listener는 테스트 기본 흐름에서는 끝까지 안 돌 수 있다.

```java
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void on(OrderPlacedEvent event) {
    notificationClient.send();
}
```

이때 초급자가 내려야 할 해석은 "`AFTER_COMMIT`이 고장났다"가 아니라 **"이 테스트는 commit을 만들지 않았다"**에 가깝다.

### 3. "호출 안 됨"이 안전성 증명이 되지는 않는다

rollback 기반 테스트에서 아래 검증은 종종 통과한다.

```java
verify(notificationClient, never()).send();
```

하지만 이 결과만으로는 두 가지를 분리하지 못한다.

- 롤백돼서 원래 안 돈 것인지
- commit이 일어나도 로직이 안 도는 버그가 있는지

즉 **부재 검증**만으로 commit 경로의 정답을 확정하기 어렵다.

## 초급자용 판단 카드

| 지금 확인하려는 것 | 기본 선택 |
|---|---|
| repository 저장/조회, flush, 제약 조건 | `@DataJpaTest` |
| `AFTER_COMMIT` listener가 실제 commit 뒤 실행되는지 | commit이 보이는 더 넓은 테스트 |
| commit 뒤 outbox row, 알림 호출, 후속 side effect가 이어지는지 | `@Commit`/`TestTransaction` 또는 더 넓은 통합 테스트 |

초급자 기준으로는 질문을 하나만 먼저 던지면 된다.

**"내가 지금 보고 싶은 결과는 같은 테스트 트랜잭션 안 결과인가, commit 뒤 세계의 결과인가?"**

뒤쪽이라면 rollback 기본 slice test만으로 끝내지 않는 편이 정확하다.

## 가장 작은 보강 예시

### 1. repository 감각은 slice test로 본다

```java
@DataJpaTest
class OrderRepositoryTest {
}
```

이건 여전히 유용하다.
JPA 매핑, query, flush 시점 검증에 잘 맞는다.

### 2. `AFTER_COMMIT` 경로는 commit이 보이는 테스트를 따로 둔다

```java
@SpringBootTest
class OrderAfterCommitTest {
}
```

또는 테스트 트랜잭션을 직접 끝내서 commit 경로를 드러낼 수도 있다.

```java
TestTransaction.flagForCommit();
TestTransaction.end();
```

다만 이 순간부터는 "기본 rollback slice test의 편한 실험실"이 아니라, **실제 commit 경로를 다루는 별도 검증**에 가까워진다.

## 자주 하는 오해 4개

- "`flush()`까지 했으니 `AFTER_COMMIT`도 거의 본 셈이다"가 아니다.
- "`@DataJpaTest`가 통과했으니 이벤트 후속 처리도 안전하다"가 아니다.
- "rollback 테스트에서 listener가 안 돌았으니 버그다"가 아니다.
- "`AFTER_COMMIT` 검증을 위해 무조건 모든 테스트를 `@SpringBootTest`로 바꿔야 한다"가 아니다.

보통은 **slice test로 JPA 감각을 먼저 고정**하고, **commit-visible 경로만 별도 테스트로 얇게 보강**하면 된다.

## 다음 테스트를 어디로 보낼까

| 지금 확인하려는 것 | 추천 출발점 |
|---|---|
| 엔티티 매핑, repository 저장/조회, flush 반응 | `@DataJpaTest` |
| `AFTER_COMMIT` listener 호출 여부 | commit이 실제로 보이는 테스트 |
| commit 뒤 알림/아웃박스 같은 후속 side effect | 더 넓은 통합 테스트 또는 명시적 commit 테스트 |

초급자 기준으로는 **"같은 트랜잭션 안 확인"과 "commit 뒤 확인"을 같은 테스트 책임으로 묶지 않는 것**이 핵심이다.

## 어디로 이어서 보면 좋나

| 지금 막히는 질문 | 다음 문서 |
|---|---|
| "`flush`와 commit 차이를 다시 짧게 잡고 싶다" | [Spring `@DataJpaTest` Mental-Model Bridge: 런타임 트랜잭션 감각을 테스트에 그대로 옮기기](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md) |
| "테스트 rollback이 왜 만능이 아닌가" | [Spring Transactional Test Rollback Misconceptions](./spring-transactional-test-rollback-misconceptions.md) |
| "`AFTER_COMMIT`과 outbox를 언제 나누나" | [Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기](./spring-service-layer-external-io-after-commit-outbox-primer.md) |
| listener phase 자체를 더 자세히 보고 싶다 | [Spring EventListener / TransactionalEventListener / Outbox](./spring-eventlistener-transaction-phase-outbox.md) |

## 한 줄 정리

`@TransactionalEventListener(AFTER_COMMIT)`는 commit이 있어야만 뜻이 살아나므로, rollback 기반 slice test는 좋은 출발점이지만 그 자체로 commit 뒤 동작까지 완전히 증명해 주지는 않는다.

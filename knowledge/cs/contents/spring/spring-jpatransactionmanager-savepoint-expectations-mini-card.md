---
schema_version: 3
title: Spring JpaTransactionManager Savepoint Expectations Mini Card
concept_id: spring/jpatransactionmanager-savepoint-expectations-mini-card
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 85
review_feedback_tags:
- jpatransactionmanager-savepoint-expectations
- jpatransactionmanager-nested
- jpa-nested-savepoint
- nestedtransactionallowed
aliases:
- JpaTransactionManager NESTED
- JPA nested savepoint
- nestedTransactionAllowed
- persistence context savepoint mismatch
- JPA nested rollback misconception
- JDBC savepoint
- NESTED propagation JPA caveat
intents:
- definition
- troubleshooting
linked_paths:
- contents/spring/spring-transaction-propagation-required-requires-new-rollbackonly-primer.md
- contents/spring/spring-transaction-propagation-nested-requires-new-case-studies.md
- contents/spring/spring-persistence-context-flush-clear-detach-boundaries.md
- contents/spring/spring-transactional-basics.md
- contents/database/savepoint-partial-rollback.md
- contents/database/jdbc-jpa-mybatis.md
expected_queries:
- JpaTransactionManager에서 NESTED propagation은 JPA 중첩 트랜잭션이야?
- JPA에서 savepoint rollback 후 persistence context 상태가 왜 그대로일 수 있어?
- nestedTransactionAllowed 기본값과 JDBC savepoint 기대를 어떻게 봐야 해?
- @Transactional NESTED와 REQUIRES_NEW를 beginner 관점으로 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 JpaTransactionManager에서 Propagation.NESTED를 JPA nested transaction이
  아니라 조건부 JDBC savepoint 기대에 가깝게 봐야 한다는 beginner mini card다.
  nestedTransactionAllowed, JDBC Connection savepoint, persistence context cached
  entity state, partial rollback misconception을 분리한다.
---
# Spring Mini Card: `JpaTransactionManager`에서 `NESTED` 기대가 자주 깨지는 이유

> 한 줄 요약: `JpaTransactionManager`에서 `NESTED`를 봤을 때 초급자가 먼저 기억할 문장은 "`JPA 중첩 트랜잭션`이 아니라, 조건부 JDBC savepoint일 뿐"이다.
>
> 문서 역할: 이 문서는 초급자가 `JpaTransactionManager`, `NESTED`, savepoint, persistence context를 한 장에서 연결해 "`안쪽만 롤백될 줄 알았는데 왜 JPA 상태가 그대로지?`" 같은 기대 mismatch를 빠르게 줄이는 **beginner mini card**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)
- [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)
- [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
- [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md)
- [Savepoint와 Partial Rollback](../database/savepoint-partial-rollback.md)
- [JDBC · JPA · MyBatis](../database/jdbc-jpa-mybatis.md)

retrieval-anchor-keywords: jpatransactionmanager nested beginner, jpa nested savepoint expectation, jpatransactionmanager savepoint caveat, nestedtransactionallowed false jpa, jpa does not support nested transactions, persistence context savepoint mismatch, nested jpa beginner card, jpa nested rollback misconception, jdbc oriented thinking safer, savepoint only jdbc connection, entity manager cached objects nested, jpa savepoint primer, transactional nested jpa not behaving, spring jpa nested caveat beginner, spring jpatransactionmanager savepoint expectations mini card basics

## 먼저 mental model 한 줄

초급자는 `JpaTransactionManager`의 `NESTED`를 이렇게 먼저 보면 된다.

- JDBC 감각: 같은 DB 연결에 savepoint를 찍고 일부만 되감기
- JPA 감각: `EntityManager`와 persistence context가 엔티티 상태를 계속 들고 있기

즉 `NESTED`를 붙였다고 해서 **JPA 객체 세계까지 자동으로 "안쪽만 되돌리기"가 되는 것은 아니다.**

## 30초 비교표

| 질문 | `DataSourceTransactionManager` 쪽 감각 | `JpaTransactionManager` 쪽 감각 |
|---|---|---|
| 기본 전제 | JDBC 연결이 중심이다 | `EntityManager`와 persistence context가 중심이다 |
| `NESTED`를 기대할 때 먼저 떠올릴 것 | savepoint가 되나? | savepoint가 되어도 JPA 상태가 같이 되감기진 않는다 |
| 기본 `nestedTransactionAllowed` | 보통 `true` | 기본 `false` |
| 초급자에게 더 안전한 사고방식 | "JDBC savepoint 기능" | "JPA 중첩 트랜잭션을 기대하지 말기" |

핵심은 이것이다.

**`JpaTransactionManager`의 `NESTED`는 "JPA가 중첩 트랜잭션을 이해한다"는 뜻이 아니라, 필요하면 JDBC savepoint를 쓸 수 있다는 쪽에 더 가깝다.**

## 왜 기대가 깨지나

Spring 공식 문서 기준으로 초급자가 꼭 기억할 사실은 네 가지다.

1. `JpaTransactionManager`의 `nestedTransactionAllowed` 기본값은 `false`다.
2. 켜더라도 savepoint는 **JDBC Connection**에 적용된다.
3. JPA 자체는 nested transaction을 지원하지 않으므로, JPA access code가 그 안쪽 경계에 "의미상 참여"할 것을 기대하면 안 된다.
4. 실제 savepoint 기대는 같은 `DataSource` 참여와 JDBC driver savepoint 지원까지 맞아야 한다.

즉 아래 기대가 자주 틀린다.

- "`@Transactional(propagation = NESTED)`면 안쪽 JPA `save()`만 되돌아가겠지"
- "savepoint로 롤백했으니 persistence context 안 객체 상태도 원래대로 돌아오겠지"
- "JPA에서도 JDBC 배치처럼 부분 롤백 감각이 그대로 보이겠지"

## 제일 작은 예시

```java
@Transactional
public void outer() {
    Order order = orderRepository.findById(id).orElseThrow();
    order.changeStatus("PAID");

    try {
        inner();
    } catch (RuntimeException ignored) {
    }

    // 초급자는 여기서 order 상태가 savepoint 이전으로 돌아갔다고 기대하기 쉽다.
}

@Transactional(propagation = Propagation.NESTED)
public void inner() {
    orderRepository.save(new AuditOrder(...));
    throw new RuntimeException("fail inner");
}
```

초급자 기대:

```text
inner만 rollback
바깥 JPA 상태는 savepoint 이전으로 자동 복구
```

실제 초급자 관찰 포인트:

```text
savepoint는 JDBC 쪽 이야기다
persistence context는 이미 들고 있는 엔티티 상태를 계속 볼 수 있다
즉 "DB 일부 롤백"과 "메모리 속 JPA 상태 복구"를 같은 일로 보면 틀리기 쉽다
```

## 언제 JDBC-oriented thinking이 더 안전한가

아래 질문에 `예`가 나오면 JPA nested 환상보다 JDBC savepoint 감각으로 보는 편이 안전하다.

| 상황 | 더 안전한 1차 사고방식 |
|---|---|
| "정말 savepoint가 핵심인가?" | JDBC 관점으로 본다 |
| "안쪽 실패 후 일부 SQL만 되감고 계속 가고 싶은가?" | JDBC/배치 스타일 사고가 더 맞다 |
| "엔티티 상태 복구보다 DB 체크포인트가 더 중요하나?" | JDBC 쪽이 더 직접적이다 |
| "JPA persistence context가 개입하면 더 헷갈리나?" | `NESTED`보다 설계 단순화 또는 JDBC 분리를 먼저 본다 |

짧게 말하면:

- **부분 SQL 롤백**이 핵심이면 JDBC 사고가 더 직접적이다.
- **엔티티 상태와 영속성 컨텍스트 일관성**이 핵심이면 `NESTED` 기대를 낮추는 편이 안전하다.

## 초급자용 선택 카드

| 내가 원하는 것 | 먼저 떠올릴 선택 |
|---|---|
| 안쪽 작업만 별도 커밋으로 남기기 | `REQUIRES_NEW` |
| 같은 물리 트랜잭션 안에서 savepoint 되돌리기 | JDBC 쪽 `NESTED` 감각 |
| JPA 엔티티 변경과 rollback 경계를 덜 헷갈리기 | `REQUIRED`/`REQUIRES_NEW`로 단순화 |
| JPA와 JDBC를 섞되 savepoint가 꼭 필요하기 | `JpaTransactionManager` + JDBC 참여 조건을 아주 조심해서 보기 |

특히 초급자는 "`NESTED`가 안쪽 성공/실패를 예쁘게 분리해 주겠지"라고 기대하기 쉽다.
하지만 JPA 문맥에서는 **부분 롤백보다 경계 단순화가 먼저**인 경우가 많다.

## 자주 하는 오해

- "`JpaTransactionManager`도 `NESTED`가 있으니 JPA nested transaction을 지원한다"가 아니다.
- "savepoint rollback이면 persistence context의 엔티티 상태도 자동 복구된다"가 아니다.
- "`REQUIRES_NEW`와 `NESTED`는 둘 다 안쪽 분리니까 거의 비슷하다"가 아니다.
- "JPA 코드가 중심인데도 JDBC 배치 partial rollback 감각을 그대로 적용해도 된다"가 아니다.

## 한 줄 정리

`JpaTransactionManager`에서 `NESTED` 기대가 깨지는 이유는 savepoint가 **JDBC 연결 수준**의 기능인데, 초급자는 이를 **JPA 영속성 컨텍스트까지 되감기는 기능**으로 오해하기 쉽기 때문이다.

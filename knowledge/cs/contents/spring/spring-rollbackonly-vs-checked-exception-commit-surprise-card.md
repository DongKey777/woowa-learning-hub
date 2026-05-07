---
schema_version: 3
title: Spring RollbackOnly vs Checked Exception Commit Surprise Card
concept_id: spring/rollbackonly-vs-checked-exception-commit-surprise-card
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 75
review_feedback_tags:
- rollbackonly-vs-checked
- exception-commit-surprise
- rollback-only-vs
- checked-exception-commit
aliases:
- rollback-only vs checked exception commit
- UnexpectedRollbackException beginner
- checked exception no rollback
- transaction marked rollback-only
- exception but commit surprise
intents:
- comparison
- troubleshooting
linked_paths:
- contents/spring/spring-transactional-basics.md
- contents/spring/spring-unexpectedrollbackexception-mini-debugging-card.md
- contents/spring/spring-unexpectedrollback-rollbackonly-marker-traps.md
- contents/spring/spring-transaction-propagation-required-requires-new-rollbackonly-primer.md
- contents/spring/spring-transactional-test-rollback-misconceptions.md
expected_queries:
- rollback-only와 checked exception인데 commit되는 문제는 어떻게 달라?
- UnexpectedRollbackException은 왜 마지막 commit 시점에 터져?
- checked exception을 던졌는데 @Transactional이 rollback하지 않는 이유는?
- 예외가 났는데 commit된 것처럼 보일 때 초급자는 무엇부터 봐야 해?
contextual_chunk_prefix: |
  이 문서는 초급자가 rollback-only로 이미 실패 예정인 transaction이 마지막에 터지는 문제와,
  checked exception 기본 규칙 때문에 rollback되지 않는 문제를 구분하도록 돕는 comparison card다.
  UnexpectedRollbackException과 rollbackFor 설정을 연결한다.
---
# Spring Mini Card: rollback-only 실패 vs checked exception인데 commit된 것처럼 보이는 놀람

> 한 줄 요약: 둘 다 "예외가 났는데 기대와 다른 결과"처럼 보이지만, rollback-only는 **이미 실패 예정인 트랜잭션이 마지막에 터지는 문제**이고, checked exception commit surprise는 **예외를 던지고도 기본 규칙상 commit 방향으로 끝나는 문제**다.
>
> 문서 역할: 이 문서는 초급자가 `UnexpectedRollbackException`, `rollback-only`, `checked exception인데 왜 롤백 안 됨`, `예외 났는데 commit됨`을 한 장에서 빠르게 분리하는 **beginner comparison card**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:

- [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md)
- [Mini Debugging Card for `UnexpectedRollbackException`](./spring-unexpectedrollbackexception-mini-debugging-card.md)
- [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)
- [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
- [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
- [트랜잭션 기초](../database/transaction-basics.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: rollback-only vs checked exception, checked exception commit surprise, 예외 났는데 commit 됨, checked exception인데 왜 롤백 안 됨, unexpectedrollbackexception vs checked exception, rollback-only 마지막에 터짐, catch 했는데 commit 실패, rollback 안 된 것 같아요, checked exception commit beginner, rollbackfor beginner card, transaction marked rollback-only vs checked exception, transactional rollback default confusion, runtime exception rollback checked commit, beginner transaction surprise card, spring rollbackonly checked exception basics

## 이 문서가 먼저 잡는 질문

이 문서는 아래처럼 **"예외가 났는데 왜 기대와 다르게 끝났지?"**라는 질문을 두 축으로 먼저 자르기 위해 만든 comparison card다.

| 학습자 질문 모양 | 이 문서에서 먼저 주는 답 |
|---|---|
| "예외가 났는데 왜 마지막에만 터져요?" | rollback-only 지연 폭발인지 먼저 보라고 답한다 |
| "checked exception인데 왜 commit돼요?" | 기본 rollback 규칙 밖의 예외인지 먼저 보라고 답한다 |
| "rollback이 안 된 건지, commit surprise인지 헷갈려요" | 트랜잭션 상태 문제와 예외 타입 규칙 문제를 분리하라고 답한다 |
| "`rollbackFor`를 볼 문제인가요, catch 코드를 볼 문제인가요?" | checked exception이면 규칙부터, 마지막 commit 폭발이면 rollback-only부터 보라고 안내한다 |

## 먼저 mental model 한 줄

초급자는 먼저 이렇게 나누면 된다.

- rollback-only: "이 트랜잭션은 이미 망했다"가 **나중에 commit 시점에 드러나는 경우**
- checked exception commit surprise: "예외는 났지만 기본 rollback 대상이 아니라서" **commit 쪽으로 끝나는 경우**

즉 둘은 둘 다 트랜잭션 놀람이지만, 놀람의 이유가 다르다.

## 30초 분리표

| 질문 | rollback-only 쪽 | checked exception commit surprise 쪽 |
|---|---|---|
| 언제 많이 보이나 | 메서드 끝, commit 시점 | 예외를 던진 직후 |
| 바깥에서 보이는 대표 증상 | `UnexpectedRollbackException` | `IOException` 같은 checked exception이 났는데 DB는 반영됨 |
| 핵심 원인 | 같은 tx 안 어딘가에서 이미 실패 판정 | 기본 rollback 규칙이 checked exception을 자동 rollback하지 않음 |
| 초급자 첫 질문 | "앞에서 누가 rollback-only를 찍었지?" | "던진 예외가 checked exception인가?" |
| 자주 같이 보이는 코드 | `try/catch` 후 계속 진행 | `throws Exception`, `throws IOException` |
| 첫 대응 방향 | 마지막 save보다 최초 실패 지점 추적 | `rollbackFor`가 필요한 상황인지 확인 |

## 한 문장으로 바로 구분

- `catch 했는데 마지막 commit에서 갑자기 터진다` -> rollback-only 쪽을 먼저 본다.
- `예외를 던졌는데도 일부 데이터가 남았다` -> checked exception 기본 commit 규칙을 먼저 본다.

## 경우 1. rollback-only 실패

```java
@Transactional
public void placeOrder() {
    try {
        paymentService.charge();
    } catch (Exception ex) {
        log.warn("일단 계속 진행", ex);
    }

    auditRepository.save(new AuditLog("done"));
}
```

초급자 눈에는 "예외를 처리했으니 뒤 save는 되겠지"처럼 보일 수 있다.
하지만 `paymentService.charge()`가 같은 트랜잭션에서 실패해 rollback-only를 찍었다면 흐름은 이렇게 읽어야 한다.

```text
1. placeOrder tx 시작
2. payment 실패
3. 현재 tx가 rollback-only 상태가 됨
4. catch가 예외 전달만 숨김
5. 바깥 코드는 계속 진행
6. commit 시점에 실패가 드러남
```

핵심:

- 문제는 "마지막 save"가 아니라 **이미 실패 예정인 트랜잭션**
- `catch`는 rollback-only를 정상 상태로 되돌리지 못함

## 경우 2. checked exception인데 commit surprise

```java
@Transactional
public void importMembers() throws IOException {
    memberRepository.save(new Member("a"));

    if (remoteFileBroken()) {
        throw new IOException("file read failed");
    }
}
```

초급자 눈에는 "예외가 났으니 save도 롤백되겠지"처럼 보일 수 있다.
하지만 `IOException`은 checked exception이라, 기본 규칙만 쓰면 트랜잭션은 rollback이 아니라 commit 방향으로 끝날 수 있다.

```text
1. importMembers tx 시작
2. member 저장
3. IOException 발생
4. 기본 rollback 대상 아님
5. commit 방향으로 종료될 수 있음
```

핵심:

- 문제는 "중간에 실패했는데도 커밋됐다"가 아니라 **그 예외가 기본 rollback 대상이 아니었다는 점**
- 이 경우는 rollback-only와 달리, "이미 실패 예정인 tx"가 아니라 **rollback 규칙 자체**를 먼저 봐야 한다

## 둘을 같은 표로 다시 비교

| 항목 | rollback-only 실패 | checked exception commit surprise |
|---|---|---|
| 트랜잭션 상태 | 이미 커밋 불가 상태 | 기본 설정상 커밋 가능 상태 |
| 예외를 catch 하면 | 화면상 예외는 숨겨질 수 있지만 tx는 복구 안 됨 | catch 여부보다 예외 타입이 더 핵심 |
| 마지막 commit에서 보이는가 | 자주 그렇다 | 꼭 그렇지 않다 |
| 대표 해결 방향 | 실패를 숨기지 말고 tx 경계를 다시 본다 | `rollbackFor` 또는 예외 설계를 본다 |
| 초급자 오해 | "마지막 repository 호출이 문제다" | "예외면 다 자동 rollback이다" |

## 가장 흔한 혼동 3개

### 1. "예외가 났다"는 공통점 때문에 같은 문제로 본다

아니다.

- rollback-only는 **트랜잭션 상태 문제**
- checked exception surprise는 **rollback 규칙 문제**

### 2. checked exception도 rollback-only를 만들 수 있다고 생각한다

기본값만 보면 바로 그렇게 단순화하면 안 된다.

- checked exception이 바깥으로 던져졌다고 해서 기본적으로 rollback-only가 되는 것은 아니다.
- 다만 `rollbackFor`를 지정했거나, 내부에서 다른 runtime 예외가 먼저 났다면 이야기가 달라질 수 있다.

즉 초급자 1차 판단은 항상 "예외 종류"와 "같은 tx 안에서 먼저 실패 판정이 있었는지"를 분리하는 것이다.

### 3. JPA flush 예외도 전부 checked exception처럼 본다

flush 시점에 많이 보이는 DB/JPA 예외는 초급자 체감상 "나중에 터진다"는 공통점이 있지만, 실제로는 대개 runtime 예외 경로라 rollback-only나 즉시 rollback 쪽 문맥으로 읽어야 한다.

그래서 "commit 근처에서 예외가 보였다"만으로 checked exception 문제라고 단정하면 안 된다.

## 바로 써먹는 4문장 체크

- "이 예외는 checked exception인가, runtime exception인가?"
- "앞에서 이미 같은 tx가 rollback-only가 되었나?"
- "지금 놀람은 commit 시점 지연 폭발인가, 예외 타입 기본 규칙인가?"
- "`rollbackFor`를 볼 문제인지, catch-and-continue를 볼 문제인지 분리했나?"

## 언제 어느 문서로 이어지나

- checked exception 기본 규칙부터 다시 잡으려면 [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md)로 간다.
- `catch 했는데 마지막에 터짐` 패턴을 짧게 디버깅하려면 [Mini Debugging Card for `UnexpectedRollbackException`](./spring-unexpectedrollbackexception-mini-debugging-card.md)로 간다.
- `REQUIRED`, `REQUIRES_NEW`, rollback-only를 서비스 이야기로 묶어 보려면 [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)로 간다.

## 한 줄 정리

rollback-only는 **이미 실패 예정인 트랜잭션이 commit 때 드러나는 문제**이고, checked exception commit surprise는 **예외가 rollback 규칙 밖에 있어서 commit 방향으로 끝나는 문제**다.

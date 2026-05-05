---
schema_version: 3
title: "Spring Transaction Propagation Deep Dive: `REQUIRED`, `REQUIRES_NEW`, rollback-only"
concept_id: "spring/transaction-propagation-deep-dive"
canonical: false
category: "spring"
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids:
  - missions/roomescape
  - missions/shopping-cart
review_feedback_tags:
  - transactional-propagation-boundary
  - requires-new-audit-log
  - unexpectedrollback-root-cause
aliases:
  - transaction propagation deep dive
  - spring transaction propagation
  - transactional propagation
  - REQUIRED REQUIRES_NEW
  - rollback-only transaction
  - propagation behavior
symptoms:
  - 안쪽 @Transactional 예외를 잡았는데 바깥 트랜잭션까지 같이 롤백돼요
  - 감사 로그만 따로 남기려고 REQUIRES_NEW를 쓰려는데 어디서 경계를 끊어야 할지 모르겠어요
  - catch 했는데 마지막 commit에서 UnexpectedRollbackException이 터져요
intents:
  - deep_dive
  - design
prerequisites:
  - spring/transactional-basics
next_docs:
  - spring/transaction-debugging-playbook
  - spring/transaction-synchronization-aftercommit-pitfalls
linked_paths:
  - contents/spring/spring-transactional-basics.md
  - contents/spring/transactional-deep-dive.md
  - contents/spring/spring-transaction-propagation-required-requires-new-rollbackonly-primer.md
  - contents/spring/spring-transaction-propagation-nested-requires-new-case-studies.md
  - contents/spring/spring-unexpectedrollback-rollbackonly-marker-traps.md
  - contents/spring/spring-transaction-debugging-playbook.md
confusable_with:
  - spring/transactional-basics
  - spring/transactional-deep-dive
  - spring/transactional-not-applied-cause-router
forbidden_neighbors:
  - contents/database/transaction-isolation-basics.md
  - contents/database/transaction-isolation-locking.md
expected_queries:
  - Spring transaction propagation이 어떻게 동작해?
  - REQUIRED와 REQUIRES_NEW를 언제 갈라야 해?
  - rollback-only가 왜 마지막 commit에서 터져?
  - propagation 때문에 바깥 트랜잭션까지 같이 실패하는 이유가 뭐야?
  - 감사 로그를 REQUIRES_NEW로 빼면 어떤 trade-off가 생겨?
contextual_chunk_prefix: |
  이 문서는 @Transactional 기초는 이미 봤지만 propagation과 rollback-only가
  왜 결과를 바꾸는지 이해되지 않는 학습자를 위한 Spring transaction deep dive다.
  REQUIRED vs REQUIRES_NEW, transaction propagation 동작, rollback-only가 마지막
  commit에서 터지는 이유, 감사 로그를 분리할 때 trade-off, propagation 때문에
  바깥 트랜잭션까지 왜 같이 실패하나 같은 자연어 질문을 service boundary
  관점의 의사결정 표와 failure narrative로 연결한다.
---

# Spring Transaction Propagation Deep Dive: `REQUIRED`, `REQUIRES_NEW`, rollback-only

> 한 줄 요약: propagation은 "안쪽 메서드가 바깥 트랜잭션에 합류할지, 잠깐 멈추고 새로 열지, 이미 실패 예정 상태를 그대로 끌고 갈지"를 정하는 규칙이라서, 옵션 이름보다 실패 범위와 commit 책임을 같이 봐야 한다.

**난이도: 🔴 Advanced**

관련 문서:

- [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md)
- [@Transactional 깊이 파기](./transactional-deep-dive.md)
- [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)
- [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
- [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
- [트랜잭션 기초](../database/transaction-basics.md)

retrieval-anchor-keywords: transaction propagation deep dive, spring transaction propagation, transactional propagation, required vs requires_new, rollback-only deep dive, why unexpectedrollbackexception, 감사 로그 requires new, propagation 때문에 같이 롤백, @transactional propagation 어떻게 동작해, transactional what does it mean next step, spring transaction meaning advanced, commit responsibility, service boundary tradeoff, transaction join suspend resume

## 먼저 구분할 것

이 문서는 "`@Transactional`이 뭐야?"를 처음 설명하는 primer가 아니다. 그 질문이면 [@Transactional 기초](./spring-transactional-basics.md)로 가는 편이 맞다. 여기서는 이미 프록시와 begin/commit/rollback은 안다는 전제로, **전파 규칙이 실패 범위를 어떻게 바꾸는지**를 본다.

초급 비유로 "`한 배를 같이 타는가`"라고 말할 수는 있지만, 그 비유가 "`트랜잭션이 실제로 중첩된다`"까지 뜻하는 것은 아니다. `REQUIRED`는 보통 같은 물리 트랜잭션에 합류하고, `REQUIRES_NEW`는 바깥 것을 잠시 suspend한 뒤 별도 commit 책임을 만든다.

## 결정표

| 질문 | `REQUIRED` | `REQUIRES_NEW` | rollback-only |
|---|---|---|---|
| 커밋 책임 | 바깥 경계가 최종 책임을 진다 | 안쪽 경계가 별도 책임을 진다 | 최종 commit 시점에 이미 실패 예정 |
| 실패 범위 | 보통 전체 묶음으로 번진다 | 안쪽 실패를 분리할 수 있다 | 예외를 catch해도 마지막에 터질 수 있다 |
| 대표 장면 | 주문 저장 + 재고 차감 | 감사 로그, 보조 기록, outbox 후보 | `UnexpectedRollbackException`, "분명 catch했는데 왜 실패?" |
| 먼저 볼 trade-off | 같이 망해야 하는가 | 정합성 추적이 더 어려워지지 않는가 | 어디서 rollback-only가 찍혔는가 |

짧게 말하면 propagation은 기술 옵션표가 아니라 **service boundary decision table**이다.

## 왜 `REQUIRES_NEW`가 만능이 아닌가

`REQUIRES_NEW`는 바깥 작업이 실패해도 안쪽 기록을 남길 수 있어서 매력적이다. 하지만 그만큼 "같은 요청에서 남은 것과 안 남은 것"이 갈라진다.

예를 들어 주문 저장은 실패했는데 감사 로그만 남으면, 운영 관찰성에는 도움이 되지만 비즈니스 정합성을 설명하는 비용이 올라간다. 그래서 "`남겨야 해서 REQUIRES_NEW`"보다 먼저 "`정말 독립 commit이어야 하나`"를 묻는 편이 안전하다.

## rollback-only가 마지막에 터지는 이유

가장 흔한 오해는 "`예외를 catch했으니 이제 괜찮다`"는 감각이다. 이미 참여 중인 트랜잭션이 rollback-only로 표시됐다면, 바깥 메서드가 정상 종료처럼 보여도 마지막 commit 단계에서 실패가 드러날 수 있다.

```text
outer REQUIRED 시작
  -> inner REQUIRED 예외 발생
  -> tx marked rollback-only
  -> inner 예외 catch
outer 정상 종료 시도
  -> commit 불가
  -> UnexpectedRollbackException
```

이 패턴은 "예외 처리" 문제가 아니라 **트랜잭션 상태 전파** 문제다. 그래서 catch 블록을 늘리기보다, 왜 rollback-only가 찍혔는지와 실패를 정말 분리해야 하는지를 먼저 본다.

## 어디까지를 다음 문서로 넘길지

- `@Transactional` 의미 자체가 아직 낯설면 [@Transactional 기초](./spring-transactional-basics.md)
- propagation 입문 비교만 더 필요하면 [Spring Transaction Propagation Beginner Primer](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)
- `UnexpectedRollbackException` 추적이 목적이면 [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
- suspend / resume, synchronization callback, savepoint까지 내려가면 [@Transactional 깊이 파기](./transactional-deep-dive.md)

## 한 줄 정리

propagation은 "안쪽 메서드를 어떤 트랜잭션 책임에 묶을지"를 정하는 규칙이므로, `REQUIRED`와 `REQUIRES_NEW`는 옵션 암기가 아니라 실패 범위와 독립 commit 필요성을 기준으로 고르는 편이 맞다.

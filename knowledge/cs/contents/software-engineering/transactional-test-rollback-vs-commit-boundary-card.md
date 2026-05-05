---
schema_version: 3
title: '`flush()` vs commit: `AFTER_COMMIT` 초심자 브리지 카드'
concept_id: software-engineering/transactional-test-rollback-vs-commit-boundary-card
canonical: false
category: software-engineering
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- flush-vs-commit
- after-commit-test-boundary
- commit-visible-verification
aliases:
- flush vs commit beginner
- flush is not commit
- after_commit listener not called
- outbox commit visible test
- transactional test rollback vs commit
- spring test rollback commit boundary
- testtransaction.end 뭐예요
- '@commit 테스트 언제 써요'
- 처음 flush commit 헷갈려요
- 왜 flush 했는데 after commit 안 돌아요
- what is commit path test
- outbox 왜 commit 뒤에 봐요
- slice test vs app integration test transaction
- rollback test app integration test
- datajpatest commit visible
symptoms:
- flush까지 했는데 AFTER_COMMIT 리스너가 안 돌아서 왜 그런지 모르겠어요
- rollback 테스트는 초록인데 커밋 뒤에 남아야 하는 데이터 검증이 불안해요
- TestTransaction.end()와 @Commit 중 뭘 써야 할지 감이 안 와요
intents:
- comparison
- design
prerequisites:
- software-engineering/test-strategy-basics
- software-engineering/inbound-adapter-test-slices-primer
- software-engineering/datajpatest-flush-clear-batch-checklist
next_docs:
- software-engineering/after-commit-listener-rollback-test-beginner-bridge
- software-engineering/testtransaction-vs-commit-choice-mini-card
- software-engineering/outbox-message-adapter-test-matrix
linked_paths:
- contents/software-engineering/after-commit-listener-rollback-test-beginner-bridge.md
- contents/software-engineering/test-strategy-basics.md
- contents/software-engineering/inbound-adapter-test-slices-primer.md
- contents/software-engineering/datajpatest-db-difference-checklist.md
- contents/software-engineering/datajpatest-flush-clear-batch-checklist.md
- contents/software-engineering/outbox-message-adapter-test-matrix.md
- contents/software-engineering/testtransaction-vs-commit-choice-mini-card.md
- contents/spring/spring-testing-basics.md
- contents/spring/spring-after-commit-rollback-slice-test-mini-card.md
- contents/spring/spring-transactional-test-rollback-misconceptions.md
confusable_with:
- software-engineering/after-commit-listener-rollback-test-beginner-bridge
- software-engineering/testtransaction-vs-commit-choice-mini-card
- software-engineering/datajpatest-flush-clear-batch-checklist
forbidden_neighbors:
- contents/software-engineering/datajpatest-flush-clear-batch-checklist.md
expected_queries:
- flush를 했는데도 다른 트랜잭션에서 안 보이는 이유를 초심자 기준으로 설명해 줄래?
- rollback 기반 테스트와 commit visible 테스트를 언제 분리해서 봐야 해?
- AFTER_COMMIT 리스너 검증은 왜 DataJpaTest 하나로 끝내기 어려워?
- TestTransaction.end()랑 @Commit은 어떤 질문일 때 각각 고르면 돼?
- outbox row가 정말 커밋 뒤에도 남는지 보려면 어떤 테스트 경계가 필요해?
contextual_chunk_prefix: |
  이 문서는 트랜잭션 테스트를 처음 다루는 학습자가 flush 시점 검증과
  commit 이후 검증을 나눠 보고, rollback 기반 테스트로 충분한지 아니면
  commit path를 따로 열어야 하는지 골라주는 chooser다. SQL은 나갔는데
  후속 동작이 왜 안 보이나, 커밋 뒤 리스너와 outbox는 언제 확인하나, 같은
  트랜잭션 초록이면 끝난 건가, 실제 반영 여부를 어떤 경계에서 보나,
  TestTransaction.end()와 @Commit을 어느 질문에 쓰나 같은 자연어
  paraphrase가 본 문서의 테스트 선택 기준에 매핑된다.
---
# `flush()` vs commit: `AFTER_COMMIT` 초심자 브리지 카드

> 한 줄 요약: `flush()`는 SQL을 보내는 중간 동기화일 뿐 commit이 아니고, `@TransactionalEventListener(AFTER_COMMIT)`나 outbox 검증은 이름 그대로 commit 뒤 세계를 따로 열어 봐야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [왜 rollback 테스트에서 `AFTER_COMMIT` listener가 안 보이나요](./after-commit-listener-rollback-test-beginner-bridge.md)
- [테스트 전략 기초](./test-strategy-basics.md)
- [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)
- [Service 계층 기초](./service-layer-basics.md)
- [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md)
- [DataJpaTest Flush/Clear Batch Checklist](./datajpatest-flush-clear-batch-checklist.md)
- [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md)
- [`TestTransaction.end()` vs `@Commit` 선택 미니 카드](./testtransaction-vs-commit-choice-mini-card.md)
- [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](../spring/spring-testing-basics.md)
- [Spring Mini Card: 왜 rollback 기반 slice test만으로 `AFTER_COMMIT`를 끝까지 믿기 어려운가](../spring/spring-after-commit-rollback-slice-test-mini-card.md)
- [Spring Transactional Test Rollback Misconceptions](../spring/spring-transactional-test-rollback-misconceptions.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: flush vs commit beginner, flush is not commit, after_commit listener not called, outbox commit visible test, transactional test rollback vs commit, spring test rollback commit boundary, testtransaction.end 뭐예요, @commit 테스트 언제 써요, 처음 flush commit 헷갈려요, 왜 flush 했는데 after commit 안 돌아요, what is commit path test, outbox 왜 commit 뒤에 봐요, slice test vs app integration test transaction, rollback test app integration test, datajpatest commit visible

## 핵심 개념

초심자가 가장 자주 헷갈리는 문장은 두 개다.

- "`flush()`까지 했는데 왜 다른 트랜잭션에서 안 보여요?"
- "`AFTER_COMMIT` listener가 왜 테스트에서 안 돌아요?"

이 둘은 사실 같은 뿌리다.
`flush()`는 **지금까지 쌓인 SQL을 DB로 보내는 것**이고, commit은 **트랜잭션을 최종 확정하는 것**이다.

둘 중 두 번째 질문만 따로 짧게 다시 보고 싶다면 [왜 rollback 테스트에서 `AFTER_COMMIT` listener가 안 보이나요](./after-commit-listener-rollback-test-beginner-bridge.md)를 먼저 열면 된다.

반대로 `@TransactionalEventListener(AFTER_COMMIT)`와 outbox 확인은 commit 뒤에만 의미가 생긴다.
즉 초심자는 먼저 "`지금 보는 결과가 같은 테스트 트랜잭션 안 결과인가, commit 뒤 결과인가`"를 갈라야 한다.

## 한눈에 보기

| 지금 보는 것 | 실제 의미 | 아직 아닌 것 |
|---|---|---|
| `save()`만 했다 | 영속성 컨텍스트에 올렸다 | SQL 실행, commit 확정 |
| `flush()`까지 했다 | SQL을 DB로 보내 봤다 | commit 확정, `AFTER_COMMIT` 실행 |
| commit까지 끝났다 | 다른 트랜잭션에서도 볼 수 있는 최종 확정 상태가 생겼다 | 외부 시스템까지 자동 검증된 것은 아님 |

| 지금 확인하는 질문 | rollback 기반 테스트가 잘 보는 것 | commit 경로 테스트가 더 맞는 것 |
|---|---|---|
| 저장/조회, 매핑, 제약 조건이 맞는가 | 예 | 경우에 따라 과하다 |
| 예외가 나면 같은 트랜잭션 안 작업이 취소되는가 | 예 | 굳이 먼저 갈 필요는 적다 |
| commit 뒤 다른 조회 지점에서도 결과가 보이는가 | 약함 | 예 |
| `AFTER_COMMIT`, outbox, 후속 알림이 실제로 이어지는가 | 약함 | 예 |

- 짧게 외우면 `flush = 중간 동기화`, `commit = 최종 확정`이다.
- 테스트 라벨로 바꾸면 `rollback 기반 slice test = 트랜잭션 안`, `app integration test의 commit-visible 경로 = 트랜잭션 밖까지`다.

## 같은 라벨로 다시 붙이기: slice test vs app integration test

이 카드에서는 다른 beginner 문서들과 같은 이름으로만 부른다.

| 지금 보는 테스트 | 이 문서에서 붙이는 라벨 | 주로 답하는 질문 |
|---|---|---|
| `@DataJpaTest`처럼 JPA 경계만 좁게 보는 테스트 | `slice test` | 저장/조회, 매핑, 제약 조건, rollback 안쪽 규칙 |
| `@SpringBootTest`에서 commit 순간이나 여러 빈 협력을 보는 테스트 | `app integration test` | 실제 transaction, commit 뒤 가시성, `AFTER_COMMIT`, outbox |

- 그래서 "`flush()`까지 봤다"는 말은 보통 `slice test` 안 관찰에 가깝다.
- 반대로 "`commit 뒤에도 남나`"는 질문은 보통 `app integration test` 질문이다.
- beginner-safe 순서는 `slice test로 안쪽 규칙 잠그기 -> 필요한 경우 app integration test로 commit-visible 경로 1장 보강`이다.

## 언제 rollback 테스트로 충분한가

아래처럼 질문이 아직 **같은 트랜잭션 안**에 머물러 있으면 rollback 기반 테스트가 좋은 첫 선택이다.

| 장면 | 먼저 쓰기 좋은 테스트 |
|---|---|
| Repository 쿼리, 매핑, 저장/조회 확인 | `slice test` (`@DataJpaTest`) |
| Service 규칙에서 예외가 나면 전체 저장이 취소되는지 확인 | rollback 기본값의 `app integration test` (`@SpringBootTest`) |
| `flush()` 시점에 unique/FK 제약이 터지는지 확인 | `slice test` (`@DataJpaTest` + `flush()`) |

핵심은 "`지금 검증하려는 결과가 테스트 메서드가 끝나기 전에 이미 판단 가능한가?`"다.
그렇다면 commit까지 일부러 만들지 않아도 되는 경우가 많다.

## 언제 commit 경로 테스트를 따로 두나

질문이 **commit 뒤 세계**를 가리키면 rollback 테스트 1개만으로는 부족할 수 있다.

| 이런 질문이면 | 왜 별도 테스트가 필요한가 |
|---|---|
| "`flush()`는 했는데 다른 트랜잭션에서 안 보여요" | `flush`와 `commit`은 다르다 |
| "`AFTER_COMMIT` listener가 안 돌아요" | 이름 그대로 commit이 있어야 뜻이 살아난다 |
| "outbox row가 실제로 남는지 보고 싶어요" | rollback이면 테스트 끝에 지워질 수 있다 |
| "`@Transactional` 테스트는 초록인데 운영에서는 커밋 후 알림이 안 가요" | 같은 트랜잭션 안 검증과 후속 부작용 검증이 섞여 있다 |

초심자 기준 안전한 규칙은 하나면 충분하다.

**commit 뒤 관찰해야 답이 나오는 질문이면, rollback 테스트와 별도 commit-visible 테스트를 나눈다.**

특히 "`왜 rollback 테스트에서 `AFTER_COMMIT` listener가 안 보이나요?`"처럼 증상 자체가 헷갈릴 때는, 이 문서 전체보다 [focused mini card](./after-commit-listener-rollback-test-beginner-bridge.md)로 먼저 증상 해석을 고정하는 편이 빠르다.

## outbox 질문으로 바로 이어 붙이는 30초 다리

많은 초심자는 여기서 바로 "`그러면 outbox는 어디까지 test로 봐야 하죠?`"로 넘어간다.
이때는 질문을 두 단계로 자르면 덜 헷갈린다.

| 지금 막힌 문장 | 먼저 붙일 해석 | 바로 다음 문서 |
|---|---|---|
| "`flush()`는 했는데 outbox row가 진짜 남는지 모르겠어요" | 지금 질문은 `트랜잭션 안`이 아니라 `commit 뒤 가시성`이다 | [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md) |
| "메시지가 두 번 오면 side effect도 두 번 생기나요?" | 이건 commit 여부보다 `consumer 중복 처리` 질문이다 | [Domain Events, Outbox, Inbox](./outbox-inbox-domain-events.md) |
| "`UnexpectedRollbackException`이랑 outbox 누락이 같은 문제예요?" | 먼저 rollback-only 놀람과 commit 뒤 관찰 질문을 분리해야 한다 | [Spring Mini Card: rollback-only 실패 vs checked exception인데 commit된 것처럼 보이는 놀람](../spring/spring-rollbackonly-vs-checked-exception-commit-surprise-card.md) |

짧게 외우면 이렇다.

- `commit 뒤에 남는가`를 묻기 시작하면 outbox 쪽으로 넘어간다.
- `중복 메시지에도 결과가 한 번만 남는가`를 묻기 시작하면 inbox/dedup 쪽으로 넘어간다.
- `왜 마지막에 터졌지`가 먼저면 rollback-only 카드로 되돌아간다.

## 가장 작은 commit-visible 보강법

여기서 많은 초심자가 바로 "`그럼 서버를 다 띄우는 큰 통합 테스트로 가야 하나?`"로 점프한다.
하지만 commit 경로를 딱 1개만 드러내고 싶다면 더 작은 선택지가 있다.

| 상황 | 가장 작은 안전한 선택 | 왜 이게 충분한가 |
|---|---|---|
| 같은 테스트 메서드 안에서 "지금 commit시키고, 그 다음 조회"를 보고 싶다 | `TestTransaction.end()` | 현재 테스트 트랜잭션을 끝내 실제 commit 시점을 만들 수 있다 |
| 테스트 전체를 commit 기준으로 1번 검증하고 싶다 | `@Commit` 또는 `@Rollback(false)` | 메서드 종료 시 rollback 대신 commit되게 바꾼다 |
| HTTP, security, 메시지 wiring까지 실제 경로를 같이 봐야 한다 | 더 넓은 `app integration test` | 질문 자체가 이미 commit 하나보다 넓다 |

- 짧게 외우면 `commit 순간만 열고 싶다 -> TestTransaction.end()`, `테스트 1개를 commit 기준으로 남기고 싶다 -> @Commit`이다.
- 둘 다 "모든 테스트를 큰 시나리오로 키우는 것"과는 다르다. commit 경로 질문 1개만 최소로 꺼내는 보강이다.
- 여기서 바로 "`둘 중 정확히 언제 무엇을 고르죠?`"가 다음 질문이라면, 이 문서보다 [별도 선택 카드](./testtransaction-vs-commit-choice-mini-card.md)로 좁혀 보는 편이 덜 헷갈린다.

## 왜 `flush()`가 `AFTER_COMMIT`를 대신하지 못하나

초심자 기준으로는 아래 순서만 머리에 넣으면 된다.

1. `save()`는 엔티티 상태를 작업 단위에 올린다.
2. `flush()`는 pending SQL을 DB로 밀어낸다.
3. commit은 그 작업 단위를 최종 확정한다.
4. `AFTER_COMMIT`은 3번이 끝난 뒤에만 실행된다.

즉 `flush()` 뒤에 insert SQL 로그가 보여도, 테스트 전체가 rollback되면 `AFTER_COMMIT` listener는 안 돌 수 있다.
outbox도 마찬가지다. row를 중간에 `flush()`로 볼 수는 있어도, "정말 commit 뒤에도 남는가"는 별도 질문이다.

## `TestTransaction.end()` vs `@Commit`는 어디서 갈라지나

이 문서의 역할은 "`rollback 테스트와 commit-visible 테스트를 왜 분리하나`"까지다.
그 다음 초심자 질문은 보통 "`둘 중 뭘 고르죠?`"로 좁아진다.

그 판단표는 [별도 선택 카드](./testtransaction-vs-commit-choice-mini-card.md)에 분리해 두었다.

- 한 테스트 안에서 commit 전/후를 이어 보고 싶다 -> `TestTransaction.end()`
- 테스트 메서드 전체를 commit 기준으로 한 번 끝내면 된다 -> `@Commit`
- 둘 다 필요 없을 수 있는 질문인지 먼저 보고 싶다 -> 이 문서의 `트랜잭션 안 vs commit 뒤` 표로 돌아간다

안전한 시작점은 그대로 같다.

1. 먼저 rollback 테스트로 트랜잭션 안 규칙을 잠근다.
2. 정말 commit 뒤 질문이 남을 때만 `TestTransaction.end()` 또는 `@Commit`으로 얇게 1장 더 붙인다.
3. 세부 선택이 헷갈리면 [별도 선택 카드](./testtransaction-vs-commit-choice-mini-card.md)에서 중간 commit 필요 여부만 먼저 본다.

## 흔한 오해와 함정

- "`flush()`까지 했으니 거의 commit을 본 셈이다"
  - 아니다. `flush`는 SQL 동기화이고, `AFTER_COMMIT`과 다른 트랜잭션 가시성은 commit 뒤에야 생긴다.
- "`@Transactional` 테스트가 초록이면 운영도 같다"
  - 아니다. 테스트가 본 범위가 트랜잭션 안인지 밖인지 먼저 봐야 한다.
- "그럼 모든 테스트를 `@Commit`으로 바꿔야 하나"
  - 아니다. 대부분은 rollback 테스트가 더 싸고, commit 경로만 얇게 보강하면 된다.
- "`TestTransaction.end()`를 쓰면 바로 풀 인티그레이션 테스트가 된다"
  - 아니다. transaction 경계를 한 번 끝내 보는 것이지, HTTP나 외부 시스템을 전부 붙인다는 뜻이 아니다.
- "rollback 테스트에서 후속 알림이 안 갔으니 버그다"
  - commit이 없어서 원래 안 간 것인지 먼저 가려야 한다.

## 실무에서 쓰는 모습

주문 생성 후 outbox 이벤트를 남기는 코드를 예로 들면, 초심자는 보통 테스트 1개에 아래 두 질문을 같이 넣으려 한다.

1. 주문 저장이 되는가
2. commit 뒤 outbox row가 남는가

이 둘을 한 테스트에 억지로 넣기보다 보통 이렇게 나누는 편이 읽기 쉽다.

| 테스트 역할 | 먼저 확인할 것 |
|---|---|
| rollback 기반 `app integration test` | 주문 저장, 예외 시 롤백, 트랜잭션 안 규칙 |
| commit-visible `app integration test` | commit 뒤 outbox row, `AFTER_COMMIT` 후속 처리 |

즉 초심자에게 필요한 감각은 "테스트를 크게 만드는 것"이 아니라 **질문 경계를 트랜잭션 안/밖으로 자르는 것**이다.

## 더 깊이 가려면

- [테스트 전략 기초](./test-strategy-basics.md): 첫 테스트를 unit/`@DataJpaTest`/`@SpringBootTest` 중 어디에 둘지 다시 고를 때
- [DataJpaTest Flush/Clear Batch Checklist](./datajpatest-flush-clear-batch-checklist.md): `flush()`와 `clear()`가 어디까지 보여 주는지 짧게 복습할 때
- [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md): outbox 검증을 unit/integration/contract로 어디서 나눌지 더 크게 보고 싶을 때
- [Domain Events, Outbox, Inbox](./outbox-inbox-domain-events.md): outbox/inbox 자체를 아직 "왜 필요한가" 수준에서 먼저 다시 잡고 싶을 때
- [`TestTransaction.end()` vs `@Commit` 선택 미니 카드](./testtransaction-vs-commit-choice-mini-card.md): commit-visible 테스트 안에서 두 선택지 중 무엇을 먼저 고를지 바로 정하고 싶을 때
- [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](../spring/spring-testing-basics.md): `@SpringBootTest`를 바로 E2E처럼 키우지 않고 어디까지 붙였는지부터 구분할 때
- [왜 rollback 테스트에서 `AFTER_COMMIT` listener가 안 보이나요](./after-commit-listener-rollback-test-beginner-bridge.md): rollback 기반 테스트에서 보이는 증상 문장을 먼저 분리하고 싶을 때
- [Spring Mini Card: 왜 rollback 기반 slice test만으로 `AFTER_COMMIT`를 끝까지 믿기 어려운가](../spring/spring-after-commit-rollback-slice-test-mini-card.md): `@DataJpaTest`나 slice test에서 `AFTER_COMMIT`이 왜 안 보이는지 한 장 더 짧게 확인할 때
- [Spring Transactional Test Rollback Misconceptions](../spring/spring-transactional-test-rollback-misconceptions.md): Spring 테스트 rollback의 고급 함정을 더 자세히 볼 때

## 한 줄 정리

`flush()`는 commit이 아니므로, `AFTER_COMMIT` listener나 outbox처럼 commit 뒤에만 뜻이 생기는 질문은 rollback 테스트와 별도 commit-visible 테스트로 나눠 봐야 덜 헷갈린다.

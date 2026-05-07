---
schema_version: 3
title: 락 기초
concept_id: database/lock-basics
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- lock
- database-lock
- row-lock
- shared-lock
aliases:
- database lock
- row lock
- shared lock
- exclusive lock
- optimistic lock
- pessimistic lock
- 락
- 잠금
symptoms: []
intents:
- definition
- comparison
- troubleshooting
prerequisites:
- database/transaction-basics
- database/transaction-isolation-basics
next_docs:
- database/lock-wait-deadlock-latch-triage-playbook
- spring/transactional-basics
linked_paths:
- contents/database/deadlock-vs-lock-wait-timeout-primer.md
- contents/database/lock-timeout-blocker-first-check-mini-card.md
- contents/database/unique-vs-version-cas-vs-for-update-decision-guide.md
- contents/database/transaction-basics.md
- contents/database/transaction-isolation-basics.md
- contents/database/transaction-isolation-locking.md
- contents/database/deadlock-case-study.md
- contents/database/lock-wait-deadlock-latch-triage-playbook.md
- contents/database/jdbc-jpa-mybatis-basics.md
- contents/spring/spring-transactional-basics.md
confusable_with:
- database/deadlock-vs-lock-wait-timeout-primer
- database/unique-vs-version-cas-vs-for-update-chooser
forbidden_neighbors: []
expected_queries:
- DB lock이 뭐야?
- 공유 락과 배타 락은 뭐가 달라?
- 낙관적 락과 비관적 락은 뭐가 달라?
- lock wait은 왜 생겨?
- FOR UPDATE랑 UNIQUE랑 같은 락 종류로 보면 왜 틀려?
- deadlock, lock timeout, lock 자체를 처음 볼 때 뭐부터 구분해?
contextual_chunk_prefix: |
  이 문서는 데이터베이스 학습자가 여러 사용자가 같은 데이터를 동시에 바꾸려
  할 때 충돌을 어떻게 막는지, 동시성 제어 메커니즘으로서 lock이 무엇이고
  왜 필요한지 처음 잡는 primer다. 동시 변경 충돌 방지, 동시성 충돌, 같은
  데이터 동시에 수정, 락이 뭐야, optimistic vs pessimistic, shared vs
  exclusive lock 같은 자연어 paraphrase가 본 문서의 핵심 개념에 매핑된다.
---
# 락 기초 (Database Lock Basics)

> 한 줄 요약: 데이터베이스 락은 동시에 실행되는 트랜잭션이 같은 데이터를 충돌 없이 변경할 수 있도록 순서를 강제하는 메커니즘이다.

**난이도: 🟢 Beginner**

관련 문서:

- [트랜잭션 기초](./transaction-basics.md)
- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- [database 카테고리 인덱스](./README.md)
- [Deadlock Case Study](./deadlock-case-study.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [Spring @Transactional 심화](../spring/transactional-deep-dive.md)

retrieval-anchor-keywords: database lock basics, 락 기초, shared lock exclusive lock 처음 배우는데, 낙관적 락 비관적 락 차이, optimistic pessimistic lock 입문, 락이 뭐예요, 데드락 기초, deadlock what is, deadlock 처음, deadlock이 뭐예요, lock wait 왜 생겨요, lock timeout 처음, row lock table lock 입문, 잠금 기초, lock basics beginner

## 핵심 개념

**락(lock)** 은 트랜잭션이 데이터를 읽거나 쓸 때 다른 트랜잭션이 동시에 간섭하지 못하도록 잠그는 장치다. 아무도 락을 걸지 않으면 두 트랜잭션이 같은 계좌 잔액을 동시에 읽어 각자 10원을 차감하고 commit하는 "갱신 손실(lost update)" 문제가 생긴다.

입문자가 자주 혼동하는 지점:

- 락은 DB 서버가 내부적으로 관리하는 것이지만, 개발자가 `SELECT ... FOR UPDATE`처럼 명시적으로 요청할 수도 있다
- 락이 길어지면 다른 트랜잭션이 대기한다. 여기서는 "왜 기다리나"까지만 잡고, `deadlock` 대응은 관련 문서로 넘긴다
- 격리 수준이 높아질수록 내부 동작이 더 복잡해질 수 있지만, 입문 1회차에서는 "락은 순서를 세운다"만 기억하면 충분하다

## 한눈에 보기 — 락 종류

| 종류 | 설명 | 언제 걸리나 |
|---|---|---|
| 공유 락 (S Lock, Shared) | 읽기용. 여러 트랜잭션이 동시에 가질 수 있다 | `SELECT ... LOCK IN SHARE MODE` 또는 SERIALIZABLE 읽기 |
| 배타 락 (X Lock, Exclusive) | 쓰기용. 하나의 트랜잭션만 가질 수 있다 | `UPDATE`, `DELETE`, `SELECT ... FOR UPDATE` |
| 행 락 (Row Lock) | 특정 행 하나를 잠금 | InnoDB 기본값 — 인덱스 기반 |
| 테이블 락 (Table Lock) | 테이블 전체를 잠금 | DDL, MyISAM 등 |

## 상세 분해

**비관적 락 vs 낙관적 락** — 입문에서 가장 많이 혼동하는 개념이다.

- **비관적 락(pessimistic lock)**: "충돌이 자주 난다"고 가정하고 데이터를 읽는 순간부터 락을 건다. `SELECT ... FOR UPDATE`가 대표적이다. 락을 잡고 있는 동안 다른 트랜잭션은 대기해야 한다.
- **낙관적 락(optimistic lock)**: "충돌이 드물다"고 가정하고 락 없이 읽은 뒤, 쓸 때 버전 번호(`version` 컬럼)를 비교한다. 버전이 다르면 충돌로 판단해 예외를 던지고 재시도한다. JPA `@Version`이 이 방식이다.

비관적 락은 대기가 발생하지만 충돌을 즉시 막는다. 낙관적 락은 대기가 없지만 충돌 시 재시도 비용이 든다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "락은 자동으로 걸리니 신경 안 써도 된다" | DB가 자동 락을 걸더라도 범위와 시간을 개발자가 제어하지 않으면 데드락·타임아웃이 발생한다 | 락이 어느 범위에 어떤 기간 동안 걸리는지 의식적으로 설계한다 |
| "낙관적 락이 항상 더 빠르다" | 충돌이 잦은 상황에서는 재시도 비용이 쌓여 오히려 더 느리다 | 충돌 빈도를 먼저 예측하고 방식을 고른다 |
| "테이블 락을 걸면 행 락보다 안전하다" | 테이블 전체가 잠기면 해당 테이블에 접근하는 모든 트랜잭션이 대기해 처리량이 급감한다 | InnoDB 행 락으로 최소 범위를 잡고, 테이블 락은 DDL 등 부득이한 경우로 제한한다 |

## 지금 이 문서에서 답하는 것과 넘기는 것

처음에는 `deadlock`, `lock wait timeout`, `FOR UPDATE` 같은 단어가 같이 보여도 전부 한 번에 해결하려 하지 않는 편이 낫다. 이 문서는 "락이 왜 필요하나"까지만 답하고, 실제 증상 대응은 링크로 넘긴다.

| 지금 보인 말 | 이 문서에서 먼저 잡을 것 | 자세한 대응 문서 |
|---|---|---|
| "`lock`이 뭐예요?" | 순서를 세워 같은 데이터를 동시에 망가뜨리지 않게 하는 장치 | 이 문서 |
| "`FOR UPDATE`가 왜 필요해요?" | 읽으면서 경쟁 자원을 잡는 locking read라는 감각 | [트랜잭션 격리수준과 락](./transaction-isolation-locking.md) |
| "`deadlock`이 왜 떴어요?" | 여기서는 "서로 반대 순서로 기다리는 순환 대기"까지만 기억 | [Deadlock Case Study](./deadlock-case-study.md) |
| "`lock wait timeout`이 떴어요" | 여기서는 "오래 기다렸다는 신호"까지만 기억 | [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md) |

증상 단어별 빠른 갈림길도 같이 기억하면 좋다.

| 먼저 보인 단어 | 1문장 번역 | 바로 열 문서 |
|---|---|---|
| `deadlock` | 서로가 가진 락을 반대 순서로 기다리는 순환 대기다 | [Deadlock Case Study](./deadlock-case-study.md) |
| `lock wait timeout` | 락 줄에서 너무 오래 기다렸다는 뜻이지, 이미 중복 성공했다는 뜻은 아니다 | [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md) |
| `FOR UPDATE` | 그냥 읽기와 달리 읽으면서 경쟁 자원을 잡는 locking read다 | [트랜잭션 격리수준과 락](./transaction-isolation-locking.md) |

## 코드에서 처음 읽을 때는 여기까지만

처음 코드에서 락을 찾을 때는 복잡한 운영 사고보다 아래 두 장면만 보면 된다.

| 보인 코드/단서 | 초보자용 첫 해석 | 다음 문서 |
|---|---|---|
| `SELECT ... FOR UPDATE` | 읽으면서 row를 먼저 잡아 다른 트랜잭션을 기다리게 할 수 있다 | [트랜잭션 격리수준과 락](./transaction-isolation-locking.md) |
| JPA `@Version` | 지금 바로 잠그기보다 "나중에 쓸 때 충돌을 확인"하는 낙관적 락일 수 있다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md), [Spring @Transactional 심화](../spring/transactional-deep-dive.md) |

짧은 예시도 이 정도면 충분하다.

- 재고 차감: `SELECT ... FOR UPDATE`로 해당 row를 먼저 잡고 확인한 뒤 차감한다.
- 프로필 수정: `@Version`으로 충돌을 뒤늦게 발견하고 재시도 여부를 판단한다.

## 여기서 멈추는 기준

입문 1회차에서는 아래만 분리되면 충분하다.

- plain `SELECT`와 locking read는 역할이 다르다.
- 비관적 락은 기다리게 하고, 낙관적 락은 충돌 시 실패시키고 다시 판단한다.
- deadlock, timeout, gap lock은 "락이 있다" 다음 단계의 심화 주제다. 이 문서에서는 용어 뜻만 붙이고 대응 절차는 관련 문서로 넘긴다.

## 더 깊이 가려면

- 격리 수준과 락의 관계, 갭 락·넥스트 키 락 → [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- 실제 데드락 발생 패턴과 해결책은 2단계 follow-up으로 → [Deadlock Case Study](./deadlock-case-study.md)
- deadlock/lock timeout incident에서 blocker 분류가 바로 필요하면 3단계 playbook으로 → [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)

cross-category bridge:

- JPA `@Version`과 `@Transactional`에서 낙관적 락이 어떻게 동작하는지 → [Spring @Transactional 심화](../spring/transactional-deep-dive.md)

## 한 줄 정리

락은 동시 트랜잭션의 충돌을 막는 순서 강제 메커니즘이며, 공유/배타 락과 비관적/낙관적 접근 중 충돌 빈도와 비용에 맞는 방식을 골라야 한다.

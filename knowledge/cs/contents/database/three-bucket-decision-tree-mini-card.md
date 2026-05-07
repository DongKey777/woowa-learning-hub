---
schema_version: 3
title: Three-bucket Exception Decision Tree Mini Card
concept_id: database/three-bucket-decision-tree
canonical: true
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 91
mission_ids: []
review_feedback_tags:
- exception-mapping
- duplicate-key
- lock-timeout
- retry
- beginner
aliases:
- three bucket decision tree
- 3버킷 결정 트리
- already exists busy retryable
- exception signal bucket
- duplicate busy retryable
- beginner retry classifier
- mysql 1062 1205 1213
- sqlstate bucket mapping
- deadlock root code
- service outcome bucket
symptoms:
- duplicate key, lock timeout, deadlock, serialization failure를 모두 같은 실패로 보고 있어
- Spring 예외 이름보다 root SQLSTATE나 vendor code로 service outcome을 먼저 분류해야 해
- lock timeout을 무조건 retryable로 보거나 duplicate key를 blind retry하려 해
intents:
- comparison
- troubleshooting
- definition
prerequisites:
- database/three-bucket-terms-common
- database/unique-vs-locking-read-duplicate-primer
next_docs:
- database/insert-if-absent-retry-outcome-guide
- database/spring-jpa-lock-timeout-deadlock-exception-mapping
- database/postgresql-serializable-retry-playbook
linked_paths:
- contents/database/three-bucket-terms-common-card.md
- contents/database/insert-if-absent-retry-outcome-guide.md
- contents/database/unique-vs-locking-read-duplicate-primer.md
- contents/database/spring-cannotacquirelockexception-root-sql-code-card.md
- contents/database/spring-jpa-lock-timeout-deadlock-exception-mapping.md
- contents/database/connection-timeout-vs-lock-timeout-card.md
- contents/database/postgresql-serializable-retry-playbook.md
confusable_with:
- database/three-bucket-terms-common
- database/insert-if-absent-retry-outcome-guide
- database/lock-duplicate-three-bucket-mini-bridge
forbidden_neighbors: []
expected_queries:
- duplicate key, lock timeout, deadlock, serialization failure를 already exists busy retryable로 어떻게 나눠?
- MySQL 1062, 1205, 1213과 PostgreSQL 23505, 55P03, 40P01, 40001을 어떤 버킷에 넣어?
- lock timeout은 왜 무조건 retryable이 아니라 busy로 먼저 보고 blocker를 확인해야 해?
- duplicate key는 왜 보통 재시도보다 winner fresh read로 이어져야 해?
- Spring 예외 이름이 같아 보여도 root SQLSTATE와 errno로 service action을 고정하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 DB 예외 신호를 already exists, busy, retryable 3버킷으로 빠르게 고르는 beginner chooser다.
  duplicate key, lock timeout, deadlock, serialization failure, MySQL 1062/1205/1213, SQLSTATE mapping 질문이 본 문서에 매핑된다.
---
# 3버킷 결정 트리 미니카드

> 한 줄 요약: 예외 이름을 길게 외우기보다, 먼저 `already exists` / `busy` / `retryable` 3버킷으로 번역하면 기본 동작이 빨라진다.

**난이도: 🟢 Beginner**

관련 문서:

- [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [Spring `CannotAcquireLockException`에서 root SQL 코드 먼저 읽는 초간단 카드](./spring-cannotacquirelockexception-root-sql-code-card.md)
- [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: 3버킷 결정 트리, three bucket decision tree, already exists busy retryable, exception signal to service action, duplicate key lock timeout deadlock serialization failure, connection timeout busy mapping, beginner retry classifier, insert-if-absent decision card, service outcome bucket card, duplicate busy retryable mini card, 예외 신호 버킷 기본 동작, duplicate key busy retryable 표, 락 타임아웃 데드락 재시도 분류, mysql 1062 1205 1213, deadlock root code beginner

## 먼저 멘탈모델

용어 자체가 헷갈리면 먼저 [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)를 보고 돌아오면 된다.

이 문서는 그 공통 용어를 기준으로 **예외 신호를 30초 안에 어디에 넣을지**만 빠르게 고르는 카드다.

> "이 신호는 이미 승패가 끝났다는 뜻인가, 지금 막혀 있다는 뜻인가, 이번 시도만 버리고 다시 하라는 뜻인가?"

처음 읽을 때는 아래 `입문` 표만 먼저 보고, 신호별 차이를 더 구분하고 싶을 때만 `확장` 표까지 내려가면 된다.

## 입문: 30초 결정 트리

| 예외 신호 | 대표 root SQL 코드 | 먼저 넣을 버킷 | 기본 동작 |
|---|---|---|---|
| `duplicate key` / unique violation | MySQL `1062`, PostgreSQL `23505` | `already exists` | 기존 row 또는 기존 결과 재조회 |
| `lock timeout` | MySQL `1205`, PostgreSQL `55P03` | `busy` | 즉시 무한 재시도 말고 blocker/혼잡 먼저 확인 |
| `connection timeout` | 풀/드라이버 설정 확인 | `busy` | 풀 고갈/긴 트랜잭션부터 확인 |
| `deadlock` | MySQL `1213`, PostgreSQL `40P01` | `retryable` | 전체 트랜잭션 bounded retry |
| `serialization failure` | PostgreSQL `40001` | `retryable` | 새 snapshot에서 전체 트랜잭션 bounded retry |

짧게 외우면:

- `duplicate key` = "이미 결론이 났다"
- `lock timeout` / `connection timeout` = "아직 결론을 못 봤다"
- `deadlock` / `serialization failure` = "이번 시도를 버리고 새로 시작한다"

root code까지 같이 외우는 가장 짧은 줄:

- `already exists` -> MySQL `1062`, PostgreSQL `23505`
- `busy` -> MySQL `1205`, PostgreSQL `55P03`
- `retryable` -> MySQL `1213`, PostgreSQL `40P01`, PostgreSQL `40001`

## 확장: 버킷별 한 장 비교표

| 버킷 | 대표 신호 | 초보자 해석 | 기본 응답 |
|---|---|---|---|
| `already exists` | `duplicate key`, unique violation | 같은 business key의 승자가 이미 있다 | 기존 결과를 돌려주거나 fresh read |
| `busy` | `lock timeout`, `connection timeout` | 지금 줄이 막혀 있어 결과를 단정 못 한다 | 짧은 실패 응답, 혼잡 원인 확인, 필요 시 제한적 retry |
| `retryable` | `deadlock`, `serialization failure` | 이번 attempt만 무효다 | 새 트랜잭션으로 2~3회 bounded retry |

## 작은 예시

쿠폰 발급 API에서 `(coupon_id, member_id)`가 유일해야 한다고 하자.

| 상황 | 어떤 버킷인가 | 기본 동작 |
|---|---|---|
| 다른 요청이 먼저 insert를 commit해서 `duplicate key` 발생 | `already exists` | 이미 발급된 쿠폰으로 응답 |
| 선행 트랜잭션이 row를 오래 잡아 `lock timeout` 발생 | `busy` | "지금 혼잡" 응답 또는 짧은 재시도 |
| 서로 다른 순서로 잠그다 `deadlock` victim이 됨 | `retryable` | 전체 발급 트랜잭션 다시 시도 |

핵심은 "실패했다"가 아니라 **왜 실패했는지에 따라 기본 동작이 달라진다**는 점이다.

## 자주 헷갈리는 지점

- `lock timeout`을 무조건 `retryable`로 두면 혼잡을 더 키울 수 있다.
- `duplicate key`는 보통 재시도 대상이 아니라 이미 존재하는 결과를 읽어야 하는 신호다.
- `connection timeout`은 DB deadlock이 아니라 앱 풀 대기 실패일 수 있다.
- `serialization failure`는 deadlock과 비슷하게 retry하지만, 의미는 "새 snapshot에서 다시 계산"이다.
- Spring 예외 이름이 같아 보여도 최종 분류는 root `SQLSTATE/errno`를 보고 고정하는 편이 안전하다.

## 실무 기본 규칙

1. 서비스 결과 언어를 먼저 `already exists` / `busy` / `retryable`로 고정한다.
2. retry는 SQL 한 줄이 아니라 **트랜잭션 전체**를 다시 시작한다.
3. `busy`가 반복되면 재시도 횟수보다 blocker, 긴 트랜잭션, 풀 고갈부터 본다.

## 다음에 이어서 볼 문서

- 신호별 설명을 더 보고 싶으면 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- Spring/JPA 예외 이름이 왜 섞여 보이는지 알고 싶으면 [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- `connection timeout`과 `lock timeout`을 먼저 분리하고 싶으면 [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)

## 한 줄 정리

예외 이름을 길게 외우기보다, 먼저 `already exists` / `busy` / `retryable` 3버킷으로 번역하면 기본 동작이 빨라진다.

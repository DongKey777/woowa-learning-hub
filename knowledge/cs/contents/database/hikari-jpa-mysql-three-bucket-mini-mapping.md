---
schema_version: 3
title: Hikari/JPA/MySQL 예외 3버킷 미니 매핑표
concept_id: database/hikari-jpa-mysql-three-bucket-mini-mapping
canonical: true
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 91
mission_ids: []
review_feedback_tags:
- hikari-jpa-mysql-three-bucket
- busy-retryable-already-exists
- mysql-1205-1213-1062-mapping
aliases:
- hikari jpa mysql three bucket mapping
- busy retryable already exists hikari jpa mysql
- connection is not available cannotacquirelockexception duplicate key
- mysql 1205 1213 1062 spring jpa
- beginner db exception translator
- hikari timeout busy
- cannotacquirelockexception retryable or busy
- DataIntegrityViolationException 1062
- Hikari JPA MySQL 예외 매핑표
- busy retryable already exists
symptoms:
- Hikari timeout, CannotAcquireLockException, DuplicateKeyException을 모두 같은 DB 장애로 보고 있어
- MySQL 1205, 1213, 1062을 busy, retryable, already exists로 번역하지 못하고 있어
- DataIntegrityViolationException 안쪽의 1062, 1452, 1048을 모두 already exists로 오분류하고 있어
intents:
- comparison
- troubleshooting
- definition
prerequisites:
- database/three-bucket-terms-common
- database/lock-duplicate-three-bucket-mini-bridge
next_docs:
- database/connection-timeout-vs-lock-timeout-card
- database/spring-jpa-lock-timeout-deadlock-exception-mapping
- database/mysql-duplicate-key-retry-handling-cheat-sheet
- database/db-signal-service-result-http-bridge
linked_paths:
- contents/database/three-bucket-terms-common-card.md
- contents/database/connection-timeout-vs-lock-timeout-card.md
- contents/database/timeout-errorcode-mapping-mini-card.md
- contents/database/spring-jpa-lock-timeout-deadlock-exception-mapping.md
- contents/database/mysql-duplicate-key-retry-handling-cheat-sheet.md
- contents/database/spring-jpa-sqlstate-23p01-bridge.md
- contents/database/lock-duplicate-three-bucket-mini-bridge.md
- contents/database/hikari-connection-pool-tuning.md
- contents/database/db-signal-service-result-http-bridge.md
confusable_with:
- database/three-bucket-terms-common
- database/lock-duplicate-three-bucket-mini-bridge
- database/connection-timeout-vs-lock-timeout-card
forbidden_neighbors: []
expected_queries:
- Hikari timeout, MySQL 1205, 1213, 1062을 busy retryable already exists로 어떻게 매핑해?
- CannotAcquireLockException은 항상 retryable이 아니라 MySQL errno에 따라 어떻게 나눠?
- DataIntegrityViolationException에서 1062는 already exists지만 1452와 1048은 왜 다른 문제야?
- Hikari Connection is not available은 deadlock이 아니라 pool busy로 먼저 봐야 하는 이유는 뭐야?
- Spring/JPA/MySQL 예외를 초보자용 3버킷으로 번역하는 표를 보여줘
contextual_chunk_prefix: |
  이 문서는 Hikari, Spring/JPA, MySQL 예외 표면을 busy, retryable, already exists 세 버킷으로 번역하는 beginner chooser다.
  Hikari timeout, CannotAcquireLockException, MySQL 1205 1213 1062, DataIntegrityViolationException 같은 자연어 질문이 본 문서에 매핑된다.
---
# Hikari/JPA/MySQL 예외 3버킷 미니 매핑표

> 한 줄 요약: 초보자는 예외 클래스 이름을 길게 외우기보다, Hikari/JPA/MySQL에서 보이는 대표 메시지를 먼저 `busy` / `retryable` / `already exists`로 번역하면 대응이 훨씬 덜 흔들린다.

**난이도: 🟢 Beginner**

관련 문서:

- [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)
- [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- [Timeout 에러코드 매핑 미니카드](./timeout-errorcode-mapping-mini-card.md)
- [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)
- [Spring/JPA 예외 래퍼에서 `SQLSTATE 23P01` 꺼내는 브리지](./spring-jpa-sqlstate-23p01-bridge.md)
- [Lock 예외와 Unique 예외 통합 미니 브리지](./lock-duplicate-three-bucket-mini-bridge.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: hikari jpa mysql three bucket mapping, hikari mysql exception busy retryable already exists, connection is not available cannotacquirelockexception duplicate key 1062, hikaricp jpa mysql beginner exception table, mysql 1205 1213 1062 spring jpa cheat sheet, busy retryable already exists hikari jpa mysql, hikaricp timeout busy, cannotacquirelockexception retryable or busy, dataintegrityviolationexception 1062 1452 1048, fk not null not already exists, 왜 already exists 아닌가, beginner db exception translator, 초보자 예외 번역표, hikari jpa mysql 예외 매핑표, busy retryable already exists 미니표

## 먼저 멘탈모델

초보자는 에러 문장을 보자마자 설정값부터 바꾸기 쉽다.
먼저 아래처럼 **DB 요청이 막히는 위치**를 3버킷으로 나누면 훨씬 쉽다.

- `busy`: 아직 결과를 확정하지 못했다. 지금은 줄이 막혔다.
- `retryable`: 이번 시도만 졌다. 새 트랜잭션으로 다시 하면 된다.
- `already exists`: 같은 key의 승자가 이미 있다.

짧게 외우면:

- Hikari 풀 입구에서 못 빌리면 `busy`
- deadlock처럼 이번 시도만 깨졌으면 `retryable`
- duplicate key처럼 winner가 이미 있으면 `already exists`

## 30초 미니 매핑표

| 어디서 보였나 | 대표 메시지/예외 | 먼저 둘 버킷 | 초보자 해석 | 첫 대응 |
|---|---|---|---|---|
| Hikari | `Connection is not available, request timed out after ...` | `busy` | 풀 좌석이 안 돌아온다 | 긴 트랜잭션, 외부 I/O, 풀 대기 지표 확인 |
| JPA/Spring | `CannotAcquireLockException` + MySQL `1205` | `busy` | 락 줄이 안 풀린다 | blocker/hot row 먼저 본다 |
| JPA/Spring | `CannotAcquireLockException` + MySQL `1213` | `retryable` | deadlock victim이 됐다 | 새 트랜잭션으로 bounded retry |
| JPA/Spring | `PessimisticLockingFailureException` + MySQL `1205` | `busy` | 비관적 락 대기 실패다 | blind retry보다 락 경합 확인 |
| JPA/Spring | `DataIntegrityViolationException` + MySQL `1062` | `already exists` | 같은 exact key 승자가 이미 있다 | 기존 row/result 재조회 |
| Hibernate/JPA | `ConstraintViolationException` + MySQL `1062` | `already exists` | ORM 바깥 이름이 달라도 뜻은 duplicate다 | same key winner 확인 |

## 한 장으로 보는 대표 신호

| 레이어 | 자주 보는 표면 이름 | 아래쪽 실제 힌트 | 3버킷 |
|---|---|---|---|
| Hikari | `SQLTransientConnectionException` | `Connection is not available...` | `busy` |
| Spring DAO | `CannotAcquireLockException` | MySQL `1205` `Lock wait timeout exceeded` | `busy` |
| Spring DAO | `CannotAcquireLockException` | MySQL `1213` deadlock victim | `retryable` |
| Spring DAO | `DeadlockLoserDataAccessException` | MySQL `1213` | `retryable` |
| Spring DAO / JPA | `DataIntegrityViolationException` | MySQL `1062` duplicate entry | `already exists` |
| Hibernate | `ConstraintViolationException` | MySQL `1062` duplicate entry | `already exists` |

핵심은 **Spring/JPA top-level 이름만 보지 말고 MySQL errno까지 같이 보는 것**이다.

- `1205`면 보통 `busy`
- `1213`면 보통 `retryable`
- `1062`면 보통 `already exists`

## `DataIntegrityViolationException` 갈림표

같은 `DataIntegrityViolationException`이라도 안쪽 DB 신호가 다르면 뜻도 갈린다. 초보자는 클래스 이름보다 아래 한 장 표를 먼저 붙들면 `already exists` 오분류가 줄어든다.

| 안쪽 MySQL 힌트 | 초보자 해석 | `already exists`로 보나 | 첫 대응 |
|---|---|---|---|
| `1062 duplicate entry` | 같은 exact key winner가 이미 있다 | 예 | 같은 `INSERT` 재시도보다 기존 row/result 재조회 |
| `1452 cannot add or update a child row` | 참조할 부모 row가 없거나 FK 값이 틀렸다 | 아니오 | parent row 존재, 저장 순서, FK 매핑 확인 |
| `1048 column ... cannot be null` | 필수 칼럼에 `null`이 들어갔다 | 아니오 | DTO -> entity 매핑, 기본값, `nullable=false` 경로 확인 |

한 줄 기억법:

- `1062`만 "이미 있다" 쪽이다.
- FK/`NOT NULL`은 "이미 있다"보다 "잘못 참조했거나 비어 있다" 쪽이다.

## 가장 흔한 오해 3개

- `CannotAcquireLockException` = 무조건 retryable -> 아니다. MySQL `1205`면 기본은 `busy`다.
- Hikari timeout = DB deadlock -> 아니다. 풀에서 커넥션을 못 빌린 것일 수 있다.
- `DataIntegrityViolationException` = 무조건 `already exists` -> 아니다. `1062`만 그쪽이고, FK/`NOT NULL`은 다른 무결성 실패다.

## 작은 예시

쿠폰 발급 API에서 같은 `(coupon_id, user_id)`를 한 번만 허용한다고 하자.

| 로그 조각 | 3버킷 | 어떻게 읽나 |
|---|---|---|
| `Connection is not available, request timed out after 30000ms` | `busy` | 발급 로직이 길어져 커넥션 반환이 늦다 |
| `CannotAcquireLockException` + MySQL `1205` | `busy` | 누군가 같은 row 또는 근처 락을 오래 잡고 있다 |
| `CannotAcquireLockException` + MySQL `1213` | `retryable` | 이번 발급 시도만 deadlock victim이 됐다 |
| `DataIntegrityViolationException` + MySQL `1062` | `already exists` | 같은 쿠폰 발급 winner가 이미 있다 |
| `DataIntegrityViolationException` + MySQL `1452` | 3버킷 밖 | 쿠폰을 연결할 사용자/주문 row 참조가 깨졌다 |
| `DataIntegrityViolationException` + MySQL `1048` | 3버킷 밖 | 필수 칼럼이 비어 저장 자체가 안 된다 |

이 예시에서 초보자용 안전 규칙은 단순하다.

1. Hikari timeout이면 pool 입구 문제부터 본다.
2. `1205`는 무한 retry보다 혼잡 원인을 먼저 본다.
3. `1213`만 transaction 전체 bounded retry 후보로 둔다.
4. `1062`는 같은 `INSERT`를 또 던지기보다 기존 winner read로 넘어간다.
5. `1452`/`1048`은 `already exists`로 닫지 말고 입력/매핑 문제부터 본다.

## 바로 써먹는 기억법

| 숫자/문장 | 바로 떠올릴 말 |
|---|---|
| `Connection is not available` | 지금은 `busy` |
| MySQL `1205` | 지금 락 줄이 막혀서 `busy` |
| MySQL `1213` | 이번 시도만 깨져서 `retryable` |
| MySQL `1062` | 이미 같은 key가 있어서 `already exists` |
| MySQL `1452` / `1048` | 참조/필수값 무결성 실패, `already exists` 아님 |

## 한 줄 정리

Hikari/JPA/MySQL 예외는 먼저 "`풀 입구가 막혔나`=`busy`, `이번 시도만 죽었나`=`retryable`, `같은 key winner가 있나`=`already exists`"로 번역하되, `DataIntegrityViolationException` 안쪽의 `1062`와 `1452`/`1048`을 따로 갈라 보면 초보자도 `already exists` 오분류를 크게 줄일 수 있다.

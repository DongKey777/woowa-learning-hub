---
schema_version: 3
title: Transaction Timeout vs Lock Timeout
concept_id: database/transaction-timeout-vs-lock-timeout
canonical: true
category: database
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- timeout
- transaction-timeout
- lock-timeout
- statement-timeout
- retry
aliases:
- transaction timeout
- lock wait timeout
- statement timeout
- query timeout
- Spring transactional timeout
- innodb_lock_wait_timeout
- JDBC query timeout
- timeout taxonomy
- 작업 시간 락 대기 문장 실행
- timeout 종류 구분
symptoms:
- transaction timeout, lock timeout, statement timeout, query timeout을 하나로 뭉쳐서 대응하고 있어
- 쿼리는 빨리 끝났는데 외부 호출 포함 transaction이 오래 열려 lock과 connection을 붙잡아
- lock wait timeout이 경쟁 신호인지, statement timeout이 느린 쿼리 신호인지 구분해야 해
intents:
- comparison
- troubleshooting
- definition
prerequisites:
- database/transaction-isolation-locking
- database/deadlock-case-study
next_docs:
- database/timeout-tuning-order-checklist
- database/transaction-retry-serialization-failure-patterns
- database/connection-timeout-vs-lock-timeout-card
linked_paths:
- contents/database/transaction-isolation-locking.md
- contents/database/deadlock-case-study.md
- contents/database/transaction-retry-serialization-failure-patterns.md
- contents/database/timeout-tuning-order-checklist-card.md
- contents/database/connection-timeout-vs-lock-timeout-card.md
confusable_with:
- database/timeout-tuning-order-checklist
- database/connection-timeout-vs-lock-timeout-card
- database/statement-timeout-vs-lock-timeout-card
forbidden_neighbors: []
expected_queries:
- transaction timeout, lock timeout, statement timeout, query timeout은 각각 어떤 시간을 재는 거야?
- query는 빨리 끝났는데 transaction이 오래 열려 있으면 어떤 timeout과 lock 문제가 생겨?
- lock wait timeout은 경쟁 때문에 retry 후보일 수 있지만 statement timeout은 쿼리 튜닝이 먼저라는 차이를 설명해줘
- Spring @Transactional timeout과 innodb_lock_wait_timeout, JDBC query timeout을 어떻게 구분해?
- timeout을 늘리기 전에 원인이 락 대기인지 느린 쿼리인지 전체 작업 시간인지 어떻게 나눠?
contextual_chunk_prefix: |
  이 문서는 transaction timeout, lock wait timeout, statement/query timeout을 작업 시간, 락 대기, SQL 문장 실행 레이어로 구분하는 advanced chooser다.
  timeout 종류 구분, innodb_lock_wait_timeout, Spring transactional timeout, query timeout 질문이 본 문서에 매핑된다.
---
# Transaction Timeout과 Lock Timeout

> 한 줄 요약: 오래 걸린다고 다 같은 실패가 아니고, “쿼리가 느린 것”과 “락을 못 얻는 것”은 다른 문제로 다뤄야 한다.

**난이도: 🔴 Advanced**

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Deadlock Case Study](./deadlock-case-study.md), [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
retrieval-anchor-keywords: transaction timeout, lock wait timeout, statement timeout, query timeout, spring transactional timeout

## 핵심 개념

Timeout은 하나가 아니다.  
애플리케이션, JDBC, DB, 락 대기 각각이 다르게 시간을 잰다.

왜 중요한가:

- 쿼리는 빨리 끝났는데 트랜잭션이 오래 열려 있을 수 있다
- 락을 기다리다 타임아웃이 나면 재시도가 필요하다
- 잘못 설정하면 실패가 늦게 발생해 더 큰 락 대기를 만든다

즉 timeout은 성능 설정이 아니라 **실패를 어디서 끊을지 정하는 정책**이다.

## 깊이 들어가기

### 1. transaction timeout이란

transaction timeout은 보통 전체 작업이 허용되는 최대 시간이다.

- Spring `@Transactional(timeout = ...)`
- 애플리케이션 레벨 작업 제한
- 요청-응답 SLA와 연결

이 시간이 지나면 트랜잭션 자체를 중단시키려 한다.

### 2. lock timeout이란

lock timeout은 특정 락을 기다릴 수 있는 최대 시간이다.

- `innodb_lock_wait_timeout`
- row lock 대기 한계
- 경합이 심한 자원에서 빠르게 실패하도록 함

락 타임아웃은 “DB가 바쁜지”를 감지하는 도구에 가깝다.

### 3. statement timeout과 query timeout

statement/query timeout은 한 SQL 문이 오래 걸리지 않도록 자르는 장치다.

- 느린 SELECT
- 대형 UPDATE
- 범위 스캔

이건 lock wait와 다르다.  
쿼리가 CPU/IO로 오래 걸리는지, 락을 못 얻어서 오래 기다리는지 구분해야 한다.

### 4. 왜 구분해야 하나

같은 “timeout”이라도 대응이 다르다.

- lock timeout: 경쟁이므로 retry가 유효할 수 있다
- statement timeout: 쿼리 자체를 다시 써야 할 수 있다
- transaction timeout: 작업 범위를 줄여야 할 수 있다

이걸 섞으면 운영에서 원인 파악이 어려워진다.

## 실전 시나리오

### 시나리오 1: 결제 API가 30초 후 실패

쿼리는 1초 만에 끝났지만 외부 호출 포함 트랜잭션이 30초 열려 있었다.  
이 경우 lock timeout보다 transaction timeout이 먼저 문제다.

### 시나리오 2: 재고 업데이트가 락 대기하다 실패

row를 잡지 못해 lock wait timeout이 발생했다.  
이건 재시도 가능한 실패일 수 있다.

### 시나리오 3: 느린 보고서가 요청 시간을 다 먹는다

쿼리 자체가 오래 걸리는 상황은 statement/query timeout으로 끊어야 한다.  
트랜잭션 타임아웃만 늘린다고 해결되지 않는다.

## 코드로 보기

```java
@Transactional(timeout = 5)
public void reserveStock() {
    // 5초 안에 끝나야 하는 작업
}
```

```sql
SET innodb_lock_wait_timeout = 5;

START TRANSACTION;
SELECT * FROM stock WHERE id = 1 FOR UPDATE;
UPDATE stock SET amount = amount - 1 WHERE id = 1;
COMMIT;
```

```java
// JDBC query timeout 예시
statement.setQueryTimeout(3);
```

timeout은 하나로 뭉치지 말고, **작업 시간 / 락 대기 / 문장 실행**으로 나눠서 봐야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 긴 transaction timeout | 작업 유연성 | 락과 커넥션을 오래 점유한다 | 배치성 작업 |
| 짧은 lock timeout | 빠르게 실패한다 | 재시도 폭이 늘 수 있다 | 경합이 잦은 경로 |
| 짧은 statement timeout | 느린 쿼리를 빨리 끊는다 | 대형 조회가 실패할 수 있다 | 사용자 요청 경로 |
| 애플리케이션 timeout | SLA 제어가 쉽다 | DB 상태와 분리될 수 있다 | 서비스 단위 정책 |

## 꼬리질문

> Q: transaction timeout과 lock timeout은 같은 건가요?
> 의도: timeout 종류를 분리해서 이해하는지 확인
> 핵심: 전체 작업 제한과 락 대기는 다른 레이어다

> Q: lock timeout이 났을 때 retry가 가능한가요?
> 의도: 재시도 가능 실패와 불가능 실패를 구분하는지 확인
> 핵심: 경쟁 때문에 실패한 경우는 retry 후보가 될 수 있다

> Q: timeout을 늘리면 문제가 해결되나요?
> 의도: 시간만 늘리는 방식의 한계를 아는지 확인
> 핵심: 원인이 락인지 느린 쿼리인지 먼저 분리해야 한다

## 한 줄 정리

Timeout은 하나가 아니며, transaction timeout은 전체 작업을, lock timeout은 락 대기를, statement timeout은 느린 쿼리를 각각 끊는다.

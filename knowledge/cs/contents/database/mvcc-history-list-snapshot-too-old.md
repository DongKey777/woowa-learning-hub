---
schema_version: 3
title: MVCC History List Growth and Snapshot Too Old
concept_id: database/mvcc-history-list-snapshot-too-old
canonical: true
category: database
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- mvcc
- undo-log
- purge-lag
- long-transaction
aliases:
- MVCC history list growth
- snapshot too old
- history list length
- undo log purge lag
- vacuum debt
- consistent snapshot too long
- long transaction undo bloat
- 오래 열린 트랜잭션 때문에 undo가 쌓여요
- history list가 계속 커져요
symptoms:
- 오래 열린 read transaction 때문에 InnoDB history list length와 undo tablespace가 계속 커지고 있어
- report query나 batch가 snapshot을 오래 붙잡아 purge lag, vacuum debt, replica lag가 같이 커져
- snapshot too old 오류나 조용한 성능 저하가 긴 consistent read 이후 발생해
intents:
- troubleshooting
- deep_dive
prerequisites:
- database/transaction-isolation-locking
- database/redo-undo-checkpoint-crash-recovery
next_docs:
- database/vacuum-purge-debt-forensics-symptom-map
- database/vacuum-purge-freeze-risk-runbook-routing
- database/autovacuum-freeze-debt-wraparound-playbook
linked_paths:
- contents/database/transaction-isolation-locking.md
- contents/database/redo-log-undo-log-checkpoint-crash-recovery.md
- contents/database/mvcc-replication-sharding.md
- contents/database/vacuum-purge-debt-forensics-symptom-map.md
- contents/database/vacuum-purge-freeze-risk-runbook-routing.md
- contents/database/autovacuum-freeze-debt-wraparound-playbook.md
confusable_with:
- database/vacuum-purge-debt-forensics-symptom-map
- database/autovacuum-freeze-debt-wraparound-playbook
- database/redo-undo-checkpoint-crash-recovery
forbidden_neighbors: []
expected_queries:
- 오래 열린 트랜잭션 하나가 undo log와 history list length를 왜 키우는지 설명해줘
- InnoDB에서 snapshot too old 대신 purge lag와 undo bloat로 보이는 증상을 어떻게 해석해?
- report query가 consistent snapshot을 오래 잡을 때 운영 DB에 어떤 압박이 생겨?
- MVCC history list growth를 줄이려면 batch read를 어떤 방식으로 나눠야 해?
- vacuum debt와 purge lag를 lock wait나 디스크 부족과 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 MVCC history list growth, undo log purge lag, snapshot too old, long transaction이 과거 row version 정리를 막는 증상을 라우팅하는 advanced 문서다.
  history list length 증가, undo tablespace 팽창, vacuum debt, 오래 열린 report query 질문이 본 문서에 매핑된다.
---
# MVCC History List Growth와 Snapshot Too Old

> 한 줄 요약: 오래 열린 트랜잭션은 과거를 읽게 해 주는 대신, undo를 쌓아 올려 전체 시스템의 숨통을 조인다.

**난이도: 🔴 Advanced**

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md), [MVCC, Replication, Sharding](./mvcc-replication-sharding.md), [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)
retrieval-anchor-keywords: history list length, undo log, purge lag, snapshot too old, consistent read, vacuum debt, cleanup backlog

## 핵심 개념

MVCC는 읽기와 쓰기를 격리하기 위해 과거 버전을 남긴다.  
문제는 그 과거 버전이 **언제까지 살아 있어야 하는지**다.

왜 중요한가:

- 긴 보고서 쿼리 하나가 undo 정리를 늦출 수 있다
- purge가 밀리면 디스크와 buffer pool 압력이 커진다
- 어떤 엔진은 직접적으로 `snapshot too old` 오류를 내고, 어떤 엔진은 조용히 느려진다

MySQL/InnoDB에서는 보통 “오래된 snapshot을 못 읽는다”기보다, **history list length 증가와 purge lag**로 나타난다.  
PostgreSQL이나 Oracle은 버전과 설정에 따라 더 노골적으로 오래된 snapshot 문제를 드러내기도 한다.

## 깊이 들어가기

### 1. consistent read는 무엇을 보나

Repeatable Read나 snapshot 기반 read는 트랜잭션 시작 시점의 view를 기준으로 과거 버전을 따라간다.

즉 다음이 동시에 성립한다.

- 현재 row는 계속 갱신된다
- 내 트랜잭션은 시작 시점의 일관된 그림을 본다
- 그 그림을 유지하려면 오래된 row version이 필요하다

### 2. history list가 왜 커지는가

UPDATE/DELETE는 새 버전을 만들고, 이전 버전은 undo chain에 남는다.  
purge thread는 더 이상 어떤 활성 snapshot도 그 버전을 필요로 하지 않을 때만 정리할 수 있다.

문제는 오래 열린 트랜잭션이다.

- `START TRANSACTION` 후 외부 API를 오래 기다리면 안 된다
- 배치가 읽기 트랜잭션을 몇 시간 열어두면 undo가 쌓인다
- replica apply가 밀리면 오래된 버전 정리도 더 늦어진다

### 3. snapshot too old는 어디서 보이나

엔진마다 증상이 다르다.

- InnoDB: `history list length` 증가, undo tablespace 팽창, purge 지연
- PostgreSQL/Oracle 계열: 일정 조건에서 오래된 snapshot을 직접 읽지 못해 오류가 날 수 있음

즉 “snapshot too old”라는 단어만 찾기보다, **긴 트랜잭션이 과거 버전 정리를 막는다**는 공통 원리를 이해해야 한다.

### 4. 운영에서 보는 신호

대표적인 신호는 다음과 같다.

- DML은 빠른데 디스크 사용량이 계속 증가한다
- `SHOW ENGINE INNODB STATUS`에서 history list가 커진다
- 긴 트랜잭션이 있는데도 누가 잡고 있는지 놓친다
- replica lag가 같이 커진다

## 실전 시나리오

### 시나리오 1: 보고서 하나가 undo를 다 먹는다

분석용 쿼리를 아침에 열어두고 점심까지 유지하면, 그 사이 발생한 UPDATE/DELETE의 이전 버전이 정리되지 못한다.  
결과적으로 DML 전체가 점점 무거워진다.

### 시나리오 2: 배치가 읽기 트랜잭션을 너무 오래 유지한다

배치가 pagination 도중 커넥션을 잡은 채 외부 API를 호출하면, 트랜잭션이 필요 이상으로 길어진다.  
이 패턴은 MVCC에 특히 치명적이다.

### 시나리오 3: 장애 후 디스크는 남는데 느려진다

디스크 여유가 있어도 undo/purge가 밀리면 성능은 떨어질 수 있다.  
“공간 문제”처럼 보이지만 실제 원인은 snapshot 유지다.

## 코드로 보기

```sql
-- 오래 열린 consistent snapshot
START TRANSACTION WITH CONSISTENT SNAPSHOT;

SELECT COUNT(*)
FROM orders
WHERE created_at >= '2026-04-01';

-- 이 트랜잭션을 오래 유지하면,
-- 뒤에서 UPDATE/DELETE가 생성한 이전 버전 정리가 지연된다.
```

```sql
-- 현재 잡고 있는 긴 트랜잭션 점검
SELECT trx_id, trx_started, trx_state, trx_query
FROM information_schema.innodb_trx
ORDER BY trx_started;

SHOW ENGINE INNODB STATUS\G
```

트랜잭션 안에서 외부 네트워크 호출이나 긴 계산을 하지 않는 것이 가장 중요하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 긴 snapshot read | 일관된 결과를 쉽게 얻는다 | undo와 purge를 압박한다 | 짧고 가벼운 읽기일 때만 |
| chunked read | 메모리와 undo 압박이 적다 | 구현이 복잡하다 | 대용량 배치/보고서 |
| report replica | 운영 DB 보호에 유리하다 | replica lag와 데이터 지연이 있다 | 분석성 조회 |
| materialized summary | 읽기가 빠르다 | 갱신 전략이 필요하다 | 반복 집계 쿼리 |

## 꼬리질문

> Q: 왜 오래 열린 트랜잭션이 문제가 되나요?
> 의도: MVCC가 과거 버전을 유지하는 비용을 이해하는지 확인
> 핵심: snapshot을 오래 유지할수록 undo 정리가 늦어진다

> Q: `snapshot too old`는 MySQL에서 항상 뜨나요?
> 의도: 엔진별 증상 차이를 아는지 확인
> 핵심: InnoDB는 보통 purge lag와 bloat로 나타난다

> Q: 오래된 읽기가 필요한데 트랜잭션을 길게 열지 않는 방법은?
> 의도: 운영 가능한 대안 설계 능력 확인
> 핵심: chunked read, summary table, snapshot export, report replica를 고려한다

## 한 줄 정리

MVCC는 과거를 읽게 해 주지만, 그 과거를 너무 오래 붙잡으면 undo와 purge가 밀려서 전체 DB가 느려진다.

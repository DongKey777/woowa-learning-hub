---
schema_version: 3
title: MVCC Read View and Consistent Read Internals
concept_id: database/mvcc-read-view-consistent-read-internals
canonical: false
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 80
aliases:
- MVCC read view
- consistent read
- snapshot read
- undo chain
- InnoDB read view
- m_low_limit_id
- m_up_limit_id
intents:
- deep_dive
linked_paths:
- contents/database/transaction-isolation-basics.md
- contents/database/transaction-isolation-locking.md
- contents/database/mvcc-history-list-snapshot-too-old.md
- contents/database/undo-record-version-chain-traversal.md
- contents/database/redo-log-undo-log-checkpoint-crash-recovery.md
- contents/database/change-buffer-purge-history-length.md
forbidden_neighbors:
- contents/spring/spring-transactional-basics.md
expected_queries:
- MVCC read view가 consistent read에서 무슨 역할을 해?
- InnoDB consistent read는 undo chain을 어떻게 따라가?
- repeatable read에서 snapshot read가 왜 같은 결과를 보여?
- m_low_limit_id랑 m_up_limit_id는 MVCC에서 어떤 경계야?
---

# MVCC Read View and Consistent Read Internals

> 한 줄 요약: MVCC의 핵심은 "과거 버전을 남긴다"가 아니라, read view가 어떤 버전을 볼 수 있는지 정확히 잘라내는 내부 규칙이다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: read view, consistent read, m_low_limit_id, m_up_limit_id, trx_id, undo chain, MVCC visibility, snapshot read

## 핵심 개념

- 관련 문서:
  - [MVCC History List Growth와 Snapshot Too Old](./mvcc-history-list-snapshot-too-old.md)
  - [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)
  - [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
  - [Change Buffer, Purge, History List Length](./change-buffer-purge-history-length.md)

MVCC에서 읽기는 "현재 row를 읽는다"가 아니라, **내 read view에 보이는 버전을 고른다**는 문제다.  
이걸 이해하지 못하면 Repeatable Read, Phantom, long transaction, purge lag가 전부 따로 놀아 보인다.

read view는 보통 다음 질문에 답한다.

- 이 트랜잭션 id는 내 시점에서 보이는가
- 더 최신 버전이라면 undo chain을 따라가야 하는가
- 지금 snapshot을 유지해야 하는가

## 깊이 들어가기

### 1. read view가 필요한 이유

동시에 쓰기와 읽기가 일어나면, 읽는 쪽은 "어느 시점의 세상"을 볼지 정해야 한다.  
그 기준점이 read view다.

read view는 대략 이런 역할을 한다.

- 활성 트랜잭션 목록을 기억한다
- 내가 볼 수 있는 trx_id 경계를 잡는다
- 현재 row 버전이 너무 최신이면 undo chain으로 되돌아가게 한다

### 2. m_low_limit_id와 m_up_limit_id 감각

구현 세부는 엔진마다 다르지만, MySQL/InnoDB read view는 보통 다음 경계 감각으로 이해하면 된다.

- 아직 시작되지 않은 트랜잭션은 볼 수 없다
- 이미 끝난 트랜잭션의 결과는 볼 수 있다
- 중간에 살아 있던 트랜잭션은 undo chain으로 확인해야 한다

즉 read view는 "보이는 trx 범위"를 잘라내는 필터다.

### 3. consistent read는 왜 빠르기만 한 게 아닌가

읽기 일관성은 공짜가 아니다.

- 최신 row가 아니면 undo chain을 따라가야 한다
- long transaction일수록 과거 버전이 많이 남는다
- purge가 지연되면 읽어야 할 과거 버전이 길어진다

이 때문에 consistent read는 겉으로는 단순 SELECT여도 내부적으로는 버전 추적을 수행한다.

### 4. read committed와 repeatable read의 차이가 read view에 드러난다

- Read Committed: statement마다 새 read view를 잡는 감각
- Repeatable Read: 트랜잭션 단위로 같은 snapshot을 오래 유지하는 감각

그래서 같은 SELECT라도 격리 수준에 따라 "보이는 세상"이 달라진다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `read view`
- `consistent read`
- `m_low_limit_id`
- `m_up_limit_id`
- `undo chain`
- `MVCC visibility`
- `snapshot read`

## 실전 시나리오

### 시나리오 1. 같은 SELECT인데 시간차가 나는 결과를 본다

트랜잭션을 오래 유지하면 같은 read view가 계속 유지될 수 있다.  
그 사이의 UPDATE는 보이거나 안 보이거나가 아니라, **내 snapshot 기준으로 판단**된다.

### 시나리오 2. 보고서 쿼리가 느린 이유가 인덱스가 아니다

인덱스는 좋아도 undo chain을 따라가야 하는 row가 많으면 consistent read가 느려질 수 있다.  
특히 purge가 밀린 상태면 읽기 비용이 더 커진다.

### 시나리오 3. "보이는 데이터"와 "현재 데이터"가 다르다

장기 트랜잭션과 빈번한 쓰기가 섞이면, 현재 테이블 상태와 snapshot 결과가 달라질 수 있다.  
이건 버그가 아니라 MVCC의 본질이다.

## 코드로 보기

### read view 감각 재현

```sql
-- session 1
START TRANSACTION;
SELECT status FROM orders WHERE id = 1;
-- 이 read view를 유지한 채 오래 둔다

-- session 2
UPDATE orders SET status = 'DONE' WHERE id = 1;
COMMIT;
```

session 1은 자신의 snapshot 기준으로 과거 버전을 계속 볼 수 있다.

### 긴 트랜잭션 확인

```sql
SELECT trx_id, trx_started, trx_state, trx_query
FROM information_schema.innodb_trx
ORDER BY trx_started;

SHOW ENGINE INNODB STATUS\G
```

### 상태 확인 포인트

```sql
SHOW STATUS LIKE 'Innodb_history_list_length';
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| Repeatable Read 유지 | 읽기 일관성이 강하다 | 오래된 버전과 purge 압박이 커질 수 있다 | 트랜잭션 단위 정합성이 중요할 때 |
| Read Committed 사용 | 최신 데이터 반영이 빠르다 | statement 간 결과가 달라질 수 있다 | 짧고 자주 읽는 OLTP |
| 짧은 트랜잭션 | undo chain 압박이 적다 | 코드가 더 세심해야 한다 | 운영 서비스 대부분 |

핵심은 MVCC를 "과거를 볼 수 있는 기능"이 아니라, **read view를 관리하는 시스템**으로 보는 것이다.

## 꼬리질문

> Q: read view는 왜 필요한가요?
> 의도: MVCC가 해결하는 문제를 이해하는지 확인
> 핵심: 읽기와 쓰기가 동시에 일어날 때 일관된 시점을 고르기 위해서다

> Q: Repeatable Read에서 왜 같은 트랜잭션 안의 결과가 일정한가요?
> 의도: 트랜잭션 단위 snapshot 유지 여부를 아는지 확인
> 핵심: 같은 read view를 계속 쓰기 때문이다

> Q: consistent read가 느려질 수 있는 이유는 무엇인가요?
> 의도: undo chain과 purge lag를 연결하는지 확인
> 핵심: 최신 버전이 아니면 과거 버전을 따라가야 한다

## 한 줄 정리

MVCC read view는 트랜잭션이 볼 수 있는 버전의 경계를 정하고, consistent read 성능은 그 경계와 undo chain 길이에 크게 좌우된다.

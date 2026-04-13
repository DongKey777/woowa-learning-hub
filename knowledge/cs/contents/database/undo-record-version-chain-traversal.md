# Undo Record Version Chain Traversal

> 한 줄 요약: MVCC 읽기는 현재 row를 보는 게 아니라, undo record chain을 따라가며 내 read view에 맞는 버전을 찾는 과정이다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: undo record, version chain traversal, read view, consistent read, undo chain, MVCC visibility, rollback segment

## 핵심 개념

- 관련 문서:
  - [MVCC Read View and Consistent Read Internals](./mvcc-read-view-consistent-read-internals.md)
  - [MVCC History List Growth와 Snapshot Too Old](./mvcc-history-list-snapshot-too-old.md)
  - [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)

undo record는 과거 row 버전을 담는다.  
consistent read는 이 undo record를 따라가며 내가 볼 수 있는 버전을 찾는다.

핵심은 다음이다.

- 최신 row가 내 snapshot에 보이지 않으면 undo를 따라간다
- chain이 길수록 읽기 비용이 늘어난다
- purge가 밀리면 traversal 비용이 커진다

## 깊이 들어가기

### 1. version chain은 어떻게 생기나

row가 UPDATE될 때마다 이전 버전은 undo 쪽에 남고, 새 버전이 앞으로 나온다.  
그러면 row는 단일 값이 아니라 "버전들의 연결 리스트"가 된다.

### 2. traversal은 언제 시작되나

현재 버전이 내 read view에 보이지 않으면 traversal이 시작된다.

- 트랜잭션 시작 시점 snapshot과 안 맞을 때
- repeatable read에서 같은 snapshot을 유지할 때
- 오래 열린 트랜잭션이 있을 때

### 3. traversal이 느려지는 이유

chain이 길수록 뒤로 더 많이 돌아가야 한다.

- 업데이트가 많았다
- purge가 밀렸다
- 오래된 snapshot이 살아 있다

이런 조건이 겹치면 읽기가 눈에 띄게 무거워질 수 있다.

### 4. rollback과 traversal은 다르다

rollback은 실패한 트랜잭션을 되돌리는 경로다.  
traversal은 읽기 시점에 보이는 버전을 찾는 경로다.

같은 undo를 쓰지만 목적이 다르다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `undo record`
- `version chain traversal`
- `undo chain`
- `consistent read`
- `rollback segment`
- `MVCC visibility`

## 실전 시나리오

### 시나리오 1. SELECT가 단순한데도 느리다

index는 좋아 보이는데 읽기가 느리면 undo chain traversal 비용이 있을 수 있다.  
특히 update가 많은 테이블에서 자주 보인다.

### 시나리오 2. 긴 트랜잭션이 있는 날만 느리다

오래 살아 있는 snapshot이 있으면 purge가 버전을 못 지운다.  
그 결과 traversal chain이 길어진다.

### 시나리오 3. 배치 이후 read latency가 늘었다

대량 update가 undo chain을 늘려서 이후 read path가 더 길어질 수 있다.  
따라서 쓰기 배치와 읽기 SLA를 함께 봐야 한다.

## 코드로 보기

### read view와 version chain 감각

```sql
-- session 1
START TRANSACTION;
SELECT status FROM orders WHERE id = 1;

-- session 2
UPDATE orders SET status = 'DONE' WHERE id = 1;
COMMIT;
```

### 긴 트랜잭션 확인

```sql
SELECT trx_id, trx_started, trx_state, trx_query
FROM information_schema.innodb_trx
ORDER BY trx_started;
```

### 상태 확인

```sql
SHOW ENGINE INNODB STATUS\G
SHOW STATUS LIKE 'Innodb_history_list_length';
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| chain traversal 허용 | snapshot read가 가능하다 | 길어지면 느려진다 | MVCC 기본 |
| purge lag 줄이기 | traversal 비용을 줄인다 | 운영 관리가 필요하다 | 읽기 SLA가 민감할 때 |
| 긴 트랜잭션 축소 | 근본 원인을 제거한다 | 배치/리포트 설계가 필요하다 | 대부분의 운영 DB |

핵심은 undo record traversal을 "숨겨진 세부 구현"이 아니라, **읽기 성능을 좌우하는 실제 경로**로 보는 것이다.

## 꼬리질문

> Q: undo record chain을 왜 따라가나요?
> 의도: consistent read의 본질을 아는지 확인
> 핵심: 내 read view에 맞는 과거 버전을 찾기 위해서다

> Q: chain이 길면 왜 느려지나요?
> 의도: traversal 비용과 purge lag를 이해하는지 확인
> 핵심: 더 많은 버전을 뒤로 추적해야 하기 때문이다

> Q: rollback과 traversal의 차이는 무엇인가요?
> 의도: 같은 undo를 쓰는 다른 목적을 구분하는지 확인
> 핵심: rollback은 되돌리기, traversal은 읽기 버전 찾기다

## 한 줄 정리

undo record version chain traversal은 consistent read가 최신 row 대신 read view에 맞는 과거 버전을 찾기 위해 undo를 뒤로 따라가는 과정이다.

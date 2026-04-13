# Undo Tablespace Truncation and Purge Debt

> 한 줄 요약: undo tablespace는 단순 저장소가 아니라, purge가 밀릴수록 커지고 truncate 조건이 맞아야 줄어드는 부채 장부다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: undo tablespace, undo truncation, purge debt, innodb_undo_log_truncate, purge lag, history list length, rollback segment, undo tablespace bloat

## 핵심 개념

- 관련 문서:
  - [MVCC History List Growth와 Snapshot Too Old](./mvcc-history-list-snapshot-too-old.md)
  - [Change Buffer, Purge, History List Length](./change-buffer-purge-history-length.md)
  - [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)

undo tablespace는 과거 버전과 rollback 정보를 저장하는 공간이다.  
이 공간이 계속 커진다고 해서 곧바로 장애는 아니지만, purge가 늦고 truncate가 안 되면 운영 부담이 커진다.

핵심은 다음이다.

- undo는 MVCC와 rollback에 필요하다
- purge는 더 이상 필요 없는 과거 버전을 치운다
- truncate는 purge가 치운 뒤 남은 공간을 되돌려 받는 단계다

## 깊이 들어가기

### 1. undo는 왜 쌓이는가

UPDATE/DELETE가 많고 오래된 snapshot이 남아 있으면, purge가 과거 버전을 바로 지울 수 없다.  
그 결과 undo tablespace가 커질 수 있다.

### 2. purge debt는 어떻게 보이는가

purge debt는 "언젠가 치워야 할 과거 버전의 양"으로 이해하면 쉽다.

- `history list length`가 증가한다
- undo tablespace가 두꺼워진다
- 오래된 트랜잭션이 purge를 막는다

### 3. truncate는 왜 바로 되지 않나

undo를 지웠다고 파일 크기가 바로 줄어드는 것은 아니다.  
DB는 안전한 시점에만 tablespace truncation을 진행할 수 있다.

즉:

- purge가 먼저
- 안전한 공간 정리가 그다음
- truncate는 마지막 단계

### 4. 운영에서 자주 생기는 오해

- 공간이 커졌으니 바로 장애라는 오해
- truncate만 하면 모든 게 해결된다는 오해
- 긴 트랜잭션을 무시해도 된다는 오해

실제로는 purge lag와 long transaction이 핵심 원인이다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `undo tablespace`
- `undo truncation`
- `purge debt`
- `innodb_undo_log_truncate`
- `history list length`
- `rollback segment`
- `undo tablespace bloat`

## 실전 시나리오

### 시나리오 1. 디스크가 줄지 않는다

트랜잭션이 길거나 purge가 늦으면 undo tablespace가 자주 shrink되지 않는다.  
이때는 truncate보다 먼저 긴 트랜잭션과 purge lag를 봐야 한다.

### 시나리오 2. 배치 이후 undo가 계속 커진다

대량 UPDATE/DELETE가 반복되면 undo가 쌓인다.  
snapshot이 빨리 끝나지 않으면 tablespace가 회수되지 않는다.

### 시나리오 3. purge thread를 늘렸는데도 효과가 약하다

오래 열린 트랜잭션이 계속 있으면 thread를 늘려도 치울 수 없는 버전이 남는다.  
이 경우 병목은 쓰레드 수가 아니라 snapshot 유지다.

## 코드로 보기

### 설정 확인

```sql
SHOW VARIABLES LIKE 'innodb_undo_log_truncate';
SHOW VARIABLES LIKE 'innodb_purge_threads';
SHOW VARIABLES LIKE 'innodb_purge_rseg_truncate_frequency';
```

### 상태 확인

```sql
SHOW STATUS LIKE 'Innodb_history_list_length';
SHOW ENGINE INNODB STATUS\G
```

### 긴 트랜잭션 점검

```sql
SELECT trx_id, trx_started, trx_state, trx_query
FROM information_schema.innodb_trx
ORDER BY trx_started;
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| undo truncation 활성 | 공간 회수가 가능하다 | truncate 타이밍이 제한된다 | purge가 정상적일 때 |
| purge thread 증가 | 정리 속도를 높일 수 있다 | 백그라운드 I/O가 늘 수 있다 | undo debt가 계속 커질 때 |
| 긴 snapshot 줄이기 | root cause를 제거한다 | 배치/리포트 설계가 필요하다 | 운영 안정성을 우선할 때 |

핵심은 undo tablespace를 "정리 대상 파일"로 보지 말고, **purge debt가 남긴 결과물**로 보는 것이다.

## 꼬리질문

> Q: undo tablespace는 왜 커지나요?
> 의도: MVCC와 purge 지연을 연결하는지 확인
> 핵심: 과거 버전이 아직 필요해서 지워지지 않기 때문이다

> Q: truncate가 바로 안 되는 이유는 무엇인가요?
> 의도: 안전한 공간 회수의 조건을 아는지 확인
> 핵심: purge 이후에야 안전하게 줄일 수 있다

> Q: history list length와 undo tablespace는 어떻게 연결되나요?
> 의도: purge debt의 외형을 이해하는지 확인
> 핵심: 정리 못 한 과거 버전이 쌓이면서 둘 다 커진다

## 한 줄 정리

undo tablespace truncation은 purge가 끝낸 부채를 안전하게 되돌려 받는 과정이고, 가장 먼저 고쳐야 하는 건 긴 트랜잭션과 purge lag다.

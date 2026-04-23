# Purge Thread Scheduling and Lag Control

> 한 줄 요약: purge thread는 "나중에 정리하는 백그라운드 작업"이 아니라, 오래된 버전을 얼마나 빨리 치우느냐를 결정하는 시스템 스케줄러다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: purge thread scheduling, purge lag, innodb_purge_threads, innodb_max_purge_lag, history list length, undo debt, MVCC cleanup, truncate frequency

## 핵심 개념

- 관련 문서:
  - [MVCC History List Growth와 Snapshot Too Old](./mvcc-history-list-snapshot-too-old.md)
  - [Undo Tablespace Truncation and Purge Debt](./undo-tablespace-truncation-purge-debt.md)
  - [Change Buffer, Purge, History List Length](./change-buffer-purge-history-length.md)
  - [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)
  - [Purge Backlog Remediation, Throttling, and Recovery Playbook](./purge-backlog-remediation-throttle-playbook.md)

purge thread는 undo chain에서 더 이상 필요한 과거 버전을 정리하는 백그라운드 작업자다.  
이 작업이 밀리면 history list length가 커지고, undo debt와 읽기 비용이 같이 증가한다.

이 문서의 핵심은 다음이다.

- purge는 MVCC의 뒷정리다
- purge thread 수와 batch 전략이 lag를 좌우한다
- 오래 열린 트랜잭션이 purge를 막는다
- lag가 커지면 DML 자체를 늦추는 throttling이 필요할 수 있다

## 깊이 들어가기

### 1. purge는 무엇을 정리하나

UPDATE/DELETE가 남긴 과거 버전은 당장 지울 수 없다.  
활성 snapshot이 그 버전을 볼 수도 있기 때문이다.

그래서 purge는 다음 조건이 맞을 때만 정리한다.

- 어떤 활성 트랜잭션도 그 버전을 참조하지 않는다
- undo chain에서 더 이상 필요한 연결이 아니다
- 안전하게 지워도 현재 읽기 결과에 영향이 없다

### 2. 스케줄링이 왜 중요한가

purge는 단순히 "있다/없다"가 아니라, 얼마나 자주 얼마나 많이 돌릴지가 중요하다.

- purge threads가 너무 적으면 lag가 쌓인다
- 너무 많으면 background I/O와 CPU를 잡아먹는다
- batch가 너무 크면 foreground와 경쟁한다

즉 purge는 스레드 수보다 스케줄링 균형이 더 중요하다.

### 3. lag control은 어떤 신호로 작동하나

MySQL/InnoDB는 특정 lag 임계치에 도달하면 DML을 늦추는 전략을 사용할 수 있다.

대표 변수:

- `innodb_purge_threads`
- `innodb_max_purge_lag`
- `innodb_max_purge_lag_delay`
- `innodb_purge_rseg_truncate_frequency`

이 변수들은 "정리 속도"와 "foreground 지연"의 균형을 바꾼다.

### 4. purge가 막히는 대표 원인

- 긴 보고서 트랜잭션
- 배치가 트랜잭션을 오래 유지함
- replica apply 지연으로 정리 지연이 늘어나는 상황
- snapshot을 너무 오래 잡고 있는 애플리케이션

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `purge thread scheduling`
- `purge lag`
- `innodb_purge_threads`
- `innodb_max_purge_lag`
- `history list length`
- `undo debt`

## 실전 시나리오

### 시나리오 1. DML은 되는데 DB가 점점 무거워진다

purge lag가 쌓이면 눈에 보이는 락이 없어도 디스크와 메모리 압박이 커진다.  
`history list length`가 계속 오르면 purge thread가 따라가지 못한다는 뜻이다.

### 시나리오 2. 오래된 SELECT 하나가 전체 정리를 막는다

장기 snapshot이 purge 대상 버전을 계속 보존하게 만들면, 정리 thread를 늘려도 효과가 제한적일 수 있다.  
이 경우 먼저 긴 트랜잭션을 찾아야 한다.

### 시나리오 3. purge를 너무 공격적으로 돌리면 평시가 흔들린다

background 정리를 세게 하면 foreground 쓰기와 I/O를 두고 경쟁한다.  
그래서 purge는 무조건 빠르게가 아니라, 시스템 전체를 덜 흔드는 방식이 중요하다.

## 코드로 보기

### 설정 확인

```sql
SHOW VARIABLES LIKE 'innodb_purge_threads';
SHOW VARIABLES LIKE 'innodb_max_purge_lag';
SHOW VARIABLES LIKE 'innodb_max_purge_lag_delay';
SHOW VARIABLES LIKE 'innodb_purge_rseg_truncate_frequency';
```

### 상태 확인

```sql
SHOW STATUS LIKE 'Innodb_history_list_length';
SHOW ENGINE INNODB STATUS\G
```

### 긴 트랜잭션 확인

```sql
SELECT trx_id, trx_started, trx_state, trx_query
FROM information_schema.innodb_trx
ORDER BY trx_started;
```

### lag를 유발하는 작업 예시

```sql
UPDATE orders
SET status = 'DONE'
WHERE created_at >= '2026-04-01'
  AND created_at <  '2026-04-08';
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| purge thread 증가 | 정리 속도를 높일 수 있다 | background I/O가 늘어난다 | lag가 계속 커질 때 |
| lag 기반 throttling | undo debt 폭증을 막는다 | 쓰기 latency가 늘 수 있다 | 운영 안정성이 우선일 때 |
| 긴 트랜잭션 줄이기 | 근본 원인을 제거한다 | 배치/리포트 설계가 필요하다 | 대부분의 서비스 |

핵심은 purge thread를 "정리 로봇"이 아니라 **lag control 시스템**으로 보는 것이다.

## 꼬리질문

> Q: purge thread는 왜 중요한가요?
> 의도: MVCC 뒷정리가 성능에 미치는 영향 이해 여부 확인
> 핵심: 오래된 버전을 치우지 못하면 undo debt가 쌓인다

> Q: purge lag가 커지면 무슨 일이 생기나요?
> 의도: 정리 지연이 읽기/쓰기 모두에 영향을 준다는 점 확인
> 핵심: history list length, 디스크 압박, 지연이 함께 증가한다

> Q: purge를 무조건 빠르게 하면 안 되는 이유는?
> 의도: foreground/background 경쟁을 아는지 확인
> 핵심: 다른 쿼리와 I/O를 두고 싸우기 때문이다

## 한 줄 정리

purge thread scheduling은 과거 버전 정리 속도와 foreground 지연을 함께 조절하는 문제이고, lag control은 긴 트랜잭션을 줄일 때 가장 잘 작동한다.

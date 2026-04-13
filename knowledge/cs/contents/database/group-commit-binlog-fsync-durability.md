# Group Commit, Binlog, Fsync Durability

> 한 줄 요약: 커밋이 느린 이유는 쿼리 자체보다 로그를 언제 누구와 같이 디스크에 확정하느냐에 달려 있다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: group commit, binlog, fsync, sync_binlog, innodb_flush_log_at_trx_commit, binlog_order_commits, durability, commit latency, 2PC, binary log

## 핵심 개념

- 관련 문서:
  - [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)
  - [Replication Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)
  - [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md)
  - [온라인 스키마 변경 전략](./online-schema-change-strategies.md)

MySQL에서 커밋은 단순히 "메모리에 반영"이 아니다.  
장애가 나도 다시 복구할 수 있으려면 redo log와 binlog를 어떤 순서로 얼마나 자주 디스크에 고정할지 결정해야 한다.

그 핵심 장치가 group commit이다.

- 여러 트랜잭션의 커밋을 묶어 fsync 비용을 나눈다
- binlog와 redo log의 durability 수준을 맞춘다
- commit latency와 crash safety를 맞교환한다

## 깊이 들어가기

### 1. 왜 fsync가 병목이 되는가

`fsync()`는 단순 write보다 훨씬 비싸다.  
메모리 쓰기가 아니라 디스크에 실제로 반영되었는지를 확인해야 하기 때문이다.

그래서 트랜잭션이 아주 잦은 시스템에서는, 각 커밋마다 fsync를 하면 tail latency가 튄다.

- 작은 트랜잭션이 많을수록 fsync 비중이 커진다
- 스토리지가 느릴수록 commit path가 지연된다
- 쓰기 부하가 몰리면 p95/p99가 흔들린다

### 2. group commit은 "같이 확정하기"다

group commit은 여러 커밋을 한 덩어리로 처리해 디스크 동기화 비용을 줄인다.  
핵심은 "빨리 끝낸다"가 아니라 "같이 끝내서 더 적은 fsync로 끝낸다"다.

개념적으로는 이런 단계로 이해하면 충분하다.

1. 트랜잭션이 변경을 준비한다.
2. binlog와 redo 관련 작업이 모인다.
3. sync 단계에서 디스크 확정을 묶는다.
4. 커밋 순서를 정리해 반영한다.

즉 커밋은 단일 요청의 문제가 아니라, **동시에 들어온 트랜잭션을 얼마나 잘 묶는가**의 문제다.

### 3. binlog와 redo log는 같은 목표를 다르게 지킨다

둘 다 장애 후 정합성을 위해 중요하지만 역할이 다르다.

- redo log는 InnoDB 페이지 복구에 필요하다
- binlog는 복제와 논리적 변경 추적에 필요하다

그래서 MySQL은 커밋 시점에 둘의 내구성을 함께 고려한다.  
한쪽만 안전하고 다른 쪽이 불안하면, 장애 후 상태와 replica 상태가 어긋날 수 있다.

### 4. 2PC 감각으로 보면 이해가 쉽다

실무에서는 복잡한 내부 구현보다 다음 감각이 더 중요하다.

- InnoDB는 커밋 전에 준비 상태를 만든다
- 서버는 binlog를 기록하고 필요하면 sync한다
- 마지막에 엔진 커밋을 확정한다

이 과정에서 장애가 나도 커밋 일관성을 유지하려고 여러 단계가 조정된다.  
group commit은 이 여러 단계를 여러 트랜잭션에 대해 묶어 비용을 줄이는 장치다.

### 5. 주요 설정값이 의미하는 것

자주 보는 변수는 아래다.

- `innodb_flush_log_at_trx_commit`
- `sync_binlog`
- `binlog_order_commits`
- `binlog_group_commit_sync_delay`
- `binlog_group_commit_sync_no_delay_count`

이 값들을 건드리는 건 "속도 조절"이 아니라 **장애 시 유실 허용치와 처리량을 정하는 결정**이다.

### 6. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `group commit`
- `binlog`
- `fsync`
- `sync_binlog`
- `innodb_flush_log_at_trx_commit`
- `binlog_order_commits`
- `binlog_group_commit_sync_delay`
- `durability`

## 실전 시나리오

### 시나리오 1. 잔잔한 트래픽인데도 커밋 p99가 튄다

조회는 빠른데 쓰기만 불안정하다면, 쿼리 자체보다 commit path를 먼저 봐야 한다.

원인 후보:

- 디스크 fsync가 느리다
- 트랜잭션이 너무 자주 커밋된다
- group commit이 충분히 묶이지 않는다

### 시나리오 2. 복제는 되는데 장애 후 복구가 찜찜하다

redo와 binlog의 durability 수준이 다르면, 재기동 후 상태와 replica 상태를 다시 검증해야 한다.  
특히 `sync_binlog=0` 같은 느슨한 설정은 성능은 좋아도 내구성 리스크를 키운다.

### 시나리오 3. 작은 write를 많이 넣는 배치가 전체 서비스에 영향을 준다

작은 insert/update를 짧게 끊어 보내면 fsync가 폭증할 수 있다.  
이때는 배치 묶음, 트랜잭션 크기, 커밋 빈도를 같이 다시 설계해야 한다.

## 코드로 보기

### durability 관련 설정 확인

```sql
SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit';
SHOW VARIABLES LIKE 'sync_binlog';
SHOW VARIABLES LIKE 'binlog_order_commits';
SHOW VARIABLES LIKE 'binlog_group_commit_sync_delay';
SHOW VARIABLES LIKE 'binlog_group_commit_sync_no_delay_count';
```

### commit path를 의식한 테스트

```sql
BEGIN;
INSERT INTO orders(id, user_id, status, created_at)
VALUES (900001, 1001, 'PAID', NOW());
COMMIT;
```

이 커밋 하나가 아니라, 동시에 여러 세션이 얼마나 함께 묶이는지가 중요하다.

### fsync 관찰

```bash
strace -fp "$(pidof mysqld)" -e fsync,fdatasync,pwrite64
```

`fsync` 호출이 짧은 간격으로 반복되면 commit latency의 후보 원인을 의심할 수 있다.

### binlog 관찰

```bash
mysql -e "SHOW BINARY LOGS;"
mysqlbinlog -vvv /var/lib/mysql/mysql-bin.000001 | head
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| `sync_binlog=1` | binlog durability가 강하다 | fsync 비용이 커진다 | 복구 정합성이 매우 중요할 때 |
| `innodb_flush_log_at_trx_commit=1` | redo durability가 강하다 | 커밋 latency가 올라간다 | 데이터 유실 허용이 거의 없을 때 |
| group commit 지연 허용 | 더 많은 트랜잭션을 묶을 수 있다 | 단일 커밋의 즉시성은 떨어진다 | 처리량이 중요할 때 |
| 느슨한 durability | 더 빠를 수 있다 | 장애 시 유실 위험이 있다 | 손실 허용 범위가 명확할 때 |

핵심은 더 빠른 설정을 찾는 게 아니라, **DB가 죽었을 때 어디까지 되돌릴 수 있는지**를 정하는 것이다.

## 꼬리질문

> Q: group commit은 왜 성능을 높이나요?
> 의도: fsync 비용의 본질 이해 여부 확인
> 핵심: 여러 트랜잭션의 디스크 동기화를 한 번에 묶기 때문이다

> Q: `sync_binlog=0`이면 무엇이 위험한가요?
> 의도: binlog 내구성과 복제 정합성 이해 여부 확인
> 핵심: 장애 시 binlog 유실 가능성이 커진다

> Q: redo log와 binlog는 왜 둘 다 필요한가요?
> 의도: InnoDB 복구와 replication 역할 분리 이해 확인
> 핵심: redo는 페이지 복구, binlog는 변경 전파와 복제에 쓰인다

## 한 줄 정리

커밋 성능은 SQL 실행이 아니라 redo/binlog를 fsync와 함께 어떻게 묶느냐에 달려 있고, 그 조합이 바로 group commit의 본질이다.

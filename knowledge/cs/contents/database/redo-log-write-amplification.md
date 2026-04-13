# Redo Log Write Amplification

> 한 줄 요약: redo log는 단순한 장애 복구 파일이 아니라, 모든 변경을 순차 기록으로 바꾸는 대신 쓰기 증폭과 fsync 비용을 함께 감수하는 장치다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: redo log write amplification, WAL, fsync, log buffer, dirty page, LSN, checkpoint, commit durability, sequential write

## 핵심 개념

- 관련 문서:
  - [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)
  - [Group Commit, Binlog, Fsync Durability](./group-commit-binlog-fsync-durability.md)
  - [Checkpoint Age and Flush Storms](./checkpoint-age-flush-storms.md)
  - [Doublewrite Buffer and Torn Page Protection](./doublewrite-buffer-torn-page-protection.md)

redo log는 변경 내용을 데이터 페이지에 즉시 반영하지 않고, 먼저 순차 로그로 안전하게 적는 장치다.  
그 결과 디스크 랜덤 쓰기를 줄이지만, 다른 종류의 비용이 생긴다.

- 로그를 한 번 더 쓰는 비용
- commit 시점의 fsync 비용
- checkpoint가 늦어질 때의 flush 압박

즉 redo log는 "쓰기를 줄이는" 것이 아니라 **쓰기 양상을 바꾸는 것**이다.

## 깊이 들어가기

### 1. 왜 redo log가 필요한가

데이터 페이지를 매번 직접 쓰면 랜덤 I/O가 너무 커진다.  
redo log는 변경 내용을 먼저 순차적으로 기록해, 나중에 페이지를 복구하는 방식으로 이를 완화한다.

이때 장점:

- 작은 변경을 순차 write로 바꾼다
- crash recovery가 가능해진다
- page flush와 commit을 분리할 수 있다

### 2. write amplification은 어디서 생기나

redo log 자체만 보면 순차 write라서 가벼워 보이지만, 실제로는 여러 번의 쓰기가 묶인다.

- 변경은 memory page와 redo log에 기록된다
- checkpoint를 위해 dirty page가 disk로 flush된다
- 장애 시 recovery에서 redo를 다시 적용한다

즉 하나의 row update가 여러 저장 계층에 남는다.

### 3. log buffer와 flush의 의미

커밋 시점에 redo가 메모리에만 있고 디스크에 없으면 durability가 약해진다.  
그래서 `fsync`나 flush 전략이 중요해진다.

### 4. redo가 커지면 좋은가 나쁜가

redo 로그 용량이 크다고 무조건 좋은 건 아니다.

- 너무 작으면 checkpoint pressure가 빨리 온다
- 너무 크면 recovery scan이 길어질 수 있다

따라서 redo size와 flush rate를 같이 본다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `redo log write amplification`
- `WAL`
- `log buffer`
- `LSN`
- `checkpoint`
- `commit durability`
- `sequential write`

## 실전 시나리오

### 시나리오 1. 업데이트는 빠른데 디스크는 바빠진다

작은 UPDATE가 많아질수록 redo log write와 checkpoint flush가 같이 늘어난다.  
이때는 쿼리 속도보다 저장소의 write path를 봐야 한다.

### 시나리오 2. commit latency가 갑자기 튄다

redo는 순차 write여도 commit에서는 durability 확인이 필요하다.  
여기에 fsync가 끼면 tail latency가 길어질 수 있다.

### 시나리오 3. 복구는 되는데 운영이 무겁다

redo는 crash recovery를 돕지만, 평소에는 write amplification과 flush pressure를 만든다.  
즉 장애 복구와 평시 성능은 하나의 트레이드오프다.

## 코드로 보기

### 로그 관련 설정 확인

```sql
SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit';
SHOW VARIABLES LIKE 'innodb_log_buffer_size';
SHOW VARIABLES LIKE 'innodb_redo_log_capacity';
SHOW VARIABLES LIKE 'sync_binlog';
```

### 상태 확인

```sql
SHOW ENGINE INNODB STATUS\G
```

### write pressure 재현

```sql
BEGIN;
UPDATE orders
SET status = 'DONE'
WHERE id BETWEEN 100000 AND 101000;
COMMIT;
```

### fsync 관찰

```bash
strace -fp "$(pidof mysqld)" -e fsync,fdatasync,pwrite64
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| redo log 강한 durability | 장애 후 정합성이 좋다 | commit latency가 늘 수 있다 | 유실 허용이 낮을 때 |
| redo log 완화 | 쓰기 성능이 좋아질 수 있다 | crash 시 손실 위험이 늘 수 있다 | 손실 허용 범위가 명확할 때 |
| redo capacity 확대 | checkpoint pressure를 늦춘다 | recovery가 길어질 수 있다 | 쓰기량이 많을 때 |

핵심은 redo를 줄이는 게 아니라, **redo가 만드는 쓰기 증폭과 fsync 비용을 어디까지 받아들일지** 정하는 것이다.

## 꼬리질문

> Q: redo log가 왜 write amplification을 일으키나요?
> 의도: 로그와 페이지 flush의 관계를 이해하는지 확인
> 핵심: 변경이 로그와 페이지 양쪽에 남기 때문이다

> Q: redo가 크면 무조건 좋은가요?
> 의도: 용량과 recovery 시간의 트레이드오프 이해 여부 확인
> 핵심: checkpoint pressure는 줄지만 복구 스캔이 길어질 수 있다

> Q: 왜 fsync와 같이 봐야 하나요?
> 의도: durability 비용의 위치를 아는지 확인
> 핵심: 커밋의 병목은 종종 fsync에 있다

## 한 줄 정리

redo log는 순차 쓰기로 랜덤 I/O를 줄이지만, 그 대신 write amplification, checkpoint pressure, fsync 비용을 함께 만든다.

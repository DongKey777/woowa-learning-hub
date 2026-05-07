---
schema_version: 3
title: Redo Log, Undo Log, Checkpoint, Crash Recovery
concept_id: database/redo-undo-checkpoint-crash-recovery
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- redo-log
- undo-log
- checkpoint
- crash-recovery
- durability
aliases:
- redo log
- undo log
- checkpoint
- crash recovery
- write ahead logging
- WAL
- LSN
- dirty page flush
- doublewrite buffer
- fsync durability
symptoms:
- 커밋 latency가 fsync나 redo flush 때문에 튀는 이유를 설명해야 해
- 장애 후 DB 재기동 시간이 checkpoint age와 redo 양에 좌우되는 이유를 묻고 있어
- undo log가 rollback뿐 아니라 MVCC consistent read에도 쓰인다는 점을 놓치고 있어
intents:
- deep_dive
- troubleshooting
- definition
prerequisites:
- database/transaction-isolation-locking
- database/innodb-buffer-pool-internals
next_docs:
- database/redo-log-write-amplification
- database/group-commit-binlog-fsync-durability
- database/checkpoint-age-flush-storms
- database/doublewrite-buffer-torn-page-protection
linked_paths:
- contents/database/transaction-isolation-locking.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/online-schema-change-strategies.md
- contents/database/redo-log-write-amplification.md
- contents/database/group-commit-binlog-fsync-durability.md
- contents/database/checkpoint-age-flush-storms.md
- contents/database/doublewrite-buffer-torn-page-protection.md
- contents/operating-system/page-cache-dirty-writeback-fsync.md
- contents/operating-system/mmap-sendfile-splice-zero-copy.md
confusable_with:
- database/redo-log-write-amplification
- database/group-commit-binlog-fsync-durability
- database/checkpoint-age-flush-storms
forbidden_neighbors: []
expected_queries:
- redo log, undo log, checkpoint, crash recovery 관계를 InnoDB 기준으로 설명해줘
- 커밋이 느려질 때 fsync와 redo flush, dirty page checkpoint를 같이 봐야 하는 이유가 뭐야?
- undo log는 rollback 말고 MVCC consistent read에서 어떻게 쓰여?
- checkpoint age가 커지면 장애 복구 시간과 운영 latency가 왜 동시에 문제가 돼?
- doublewrite buffer와 redo log는 crash recovery에서 각각 어떤 문제를 막아?
contextual_chunk_prefix: |
  이 문서는 InnoDB redo log, undo log, checkpoint, crash recovery를 WAL, fsync, dirty page flush, LSN, doublewrite buffer와 연결해 설명하는 advanced deep dive다.
  커밋 지연, 장애 복구 시간, checkpoint age, redo/undo 차이 질문이 본 문서에 매핑된다.
---
# Redo Log, Undo Log, Checkpoint, Crash Recovery

> 한 줄 요약: DB 장애 복구는 "죽은 뒤에 다시 살리는 기술"이 아니라, 평소의 쓰기 지연과 fsync 비용을 받아들이는 대신 장애 후 정합성을 되찾는 장치다.

**난이도: 🔴 Advanced**

관련 문서:

- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
- [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
- [Page Cache, Dirty Writeback, fsync](../operating-system/page-cache-dirty-writeback-fsync.md)
- [mmap, sendfile, splice, zero-copy](../operating-system/mmap-sendfile-splice-zero-copy.md)

retrieval-anchor-keywords: redo log, undo log, checkpoint, crash recovery, WAL, fsync, dirty page, doublewrite, checkpoint age, log sequence number, recovery time, durability

---

## 핵심 개념

백엔드 엔지니어가 이 주제를 알아야 하는 이유는 단순하다.

- 커밋이 느려지는 이유를 설명할 수 있어야 한다.
- 장애 후 재기동이 왜 오래 걸리는지 예측할 수 있어야 한다.
- `fsync`를 줄이면 무엇을 잃는지 판단할 수 있어야 한다.
- 대규모 배치, 대량 UPDATE, 온라인 스키마 변경이 왜 p95/p99를 흔드는지 이해해야 한다.

이 문서의 핵심은 다음 관계를 잡는 것이다.

- `redo log`는 "무슨 변경이 있었는지"를 남겨서 재실행한다.
- `undo log`는 "그 변경을 없던 일로 돌리거나, 과거 버전을 보여주기" 위해 쓴다.
- `checkpoint`는 "여기까지는 파일에 반영됐다"는 기준점이다.
- `crash recovery`는 재시작 시 redo를 다시 적용하고, 필요한 경우 undo로 미완료 작업을 정리하는 과정이다.

MySQL InnoDB 관점에서 보면 redo log는 WAL(Write-Ahead Logging)의 실전 구현이다.  
즉 데이터 페이지를 먼저 다 쓰는 게 아니라, 로그를 먼저 안전하게 남기고 나중에 dirty page를 반영한다.

---

## 깊이 들어가기

### 1. 왜 redo log가 먼저인가

DB는 매 update마다 데이터 파일 전체를 바로 고치지 않는다.  
그렇게 하면 랜덤 I/O가 너무 많아지고, 커밋이 너무 느려진다.

대신 다음 순서를 택한다.

1. 메모리의 버퍼풀에 페이지를 수정한다.
2. 변경 내용을 redo log에 기록한다.
3. 필요 시 `fsync()`로 로그를 디스크에 고정한다.
4. 데이터 페이지는 나중에 flush한다.

이 방식의 장점은 분명하다.

- 작은 변경을 순차 로그로 모아서 쓴다.
- 커밋 시점의 비용을 예측 가능하게 만든다.
- 장애가 나도 redo만 있으면 복구할 수 있다.

하지만 이 구조는 `fsync` 비용과 트레이드오프다.  
매 트랜잭션마다 디스크 동기화를 강하게 걸면 durability는 좋아지지만 TPS와 tail latency가 흔들린다.

### 2. undo log는 롤백뿐 아니라 MVCC에도 쓰인다

undo log를 "취소용 로그"로만 외우면 반쪽짜리다.

- 트랜잭션이 실패하면 되돌리기 위해 쓴다.
- 동시에 다른 트랜잭션이 과거 스냅샷을 읽을 수 있게 한다.

즉 undo는 단순 복구 도구가 아니라, 격리성과 읽기 일관성을 지탱하는 재료다.
그래서 [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)에서 다룬 읽기 일관성 문제와 직접 연결된다.

### 3. checkpoint는 왜 필요한가

redo log만 계속 쌓아 두면 언제까지나 복구할 수 있을 것 같지만, 실제로는 그렇지 않다.

checkpoint는 다음 목적을 가진다.

- 오래된 redo를 안전하게 버릴 수 있게 한다.
- 재시작 시 복구해야 할 redo 범위를 줄인다.
- dirty page flush의 기준점을 제공한다.

문제는 checkpoint를 너무 늦게 밀면 `checkpoint age`가 커지고, 커널과 DB 플러셔가 한꺼번에 몰린다는 점이다.
이때 흔히 보이는 현상이 바로 latency spike다.

- 짧은 시간에 많은 dirty page flush 발생
- I/O 대기열 포화
- commit path 지연
- 배치나 온라인 스키마 변경이 같이 있으면 더 악화

### 4. crash recovery는 어떤 순서로 일어나는가

장애 후 재기동할 때 DB는 대략 이런 흐름으로 복구한다.

1. 마지막 checkpoint 지점을 찾는다.
2. 그 이후 redo log를 다시 읽는다.
3. 커밋된 변경은 다시 적용한다.
4. 커밋되지 않은 트랜잭션은 undo를 이용해 정리한다.

이 과정에서 중요한 점은 "정상 종료가 아니었더라도 데이터 정합성을 회복한다"는 것이다.  
대신 복구 시간은 마지막 checkpoint 이후 누적된 redo 양과 dirty page 상태에 크게 좌우된다.

### 5. doublewrite buffer는 왜 등장했나

디스크에 페이지를 쓸 때는 torn page 문제가 생길 수 있다.  
예를 들어 16KB 페이지를 쓰는 도중 전원 장애가 나면 절반만 반영될 수 있다.

doublewrite는 이런 손상을 줄이기 위한 안전장치다.

- 페이지를 먼저 안전한 영역에 한 번 쓴다.
- 이후 실제 데이터 파일에 다시 쓴다.

성능은 조금 희생되지만, crash recovery 시 페이지 손상을 막아 준다.  
즉 durability는 `redo log`만의 문제가 아니라, 페이지 write의 원자성 문제까지 포함한다.

---

## 실전 시나리오

### 시나리오 1. 커밋은 빠른데 어느 순간부터 갑자기 느려진다

원인 후보는 보통 이쪽이다.

- dirty page가 너무 많이 쌓였다.
- checkpoint age가 커졌다.
- flush가 뒤늦게 몰렸다.
- `fsync`가 빈번해졌다.

운영에서 흔한 패턴은 이렇다.

```text
평소에는 5ms
대량 UPDATE 시작
몇 분 뒤 p95 200ms, p99 1s+
```

이때 "쿼리만" 보지 말고 redo와 flush 상태를 같이 봐야 한다.

### 시나리오 2. 온라인 스키마 변경 후 장애는 없는데 서버가 계속 버벅인다

`ALTER TABLE`, 대량 backfill, index rebuild, `pt-online-schema-change` 같은 작업은 dirty page와 redo 생성을 크게 늘린다.  
그 결과:

- redo log write pressure 증가
- flush thread 과부하
- checkpoint 밀림
- 일반 트래픽 commit 지연

이건 [온라인 스키마 변경 전략](./online-schema-change-strategies.md)에서 말하는 "작업은 성공했는데 운영은 느려지는" 전형적인 상황이다.

### 시나리오 3. 장애 복구 시간이 예상보다 길다

복구 시간은 보통 다음에 좌우된다.

- 마지막 checkpoint 이후 redo 양
- dirty page 비율
- 스토리지 성능
- redo log 파일 크기와 개수

redo log를 너무 작게 잡으면 checkpoint pressure가 빨리 온다.  
반대로 너무 크게 잡으면 장애 후 recovery scan이 길어질 수 있다.  
즉 "크면 무조건 좋다"가 아니다.

### 시나리오 4. `fsync` 설정이 바뀌고 나서 성능과 내구성의 체감이 달라진다

MySQL 계열에서는 이런 설정이 자주 논의된다.

```sql
SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit';
SHOW VARIABLES LIKE 'sync_binlog';
SHOW VARIABLES LIKE 'innodb_doublewrite';
```

대개 다음 질문으로 귀결된다.

- 커밋 시마다 로그를 동기화할 것인가
- binlog까지 매번 강하게 보장할 것인가
- 장애 시 몇 초의 데이터 손실을 허용할 것인가

이건 성능 튜닝이 아니라 비즈니스 정책 결정이다.

---

## 코드로 보기

### InnoDB 상태 확인

```sql
SHOW ENGINE INNODB STATUS\G
```

여기서 특히 볼 만한 항목은 다음이다.

- `Log sequence number`
- `Last checkpoint at`
- `Log flushed up to`
- `History list length`

`Log sequence number - Last checkpoint at` 값이 커지면, 복구해야 할 redo가 늘고 checkpoint 압력이 커졌다는 뜻으로 해석할 수 있다.

### durability 설정 확인

```sql
SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit';
SHOW VARIABLES LIKE 'sync_binlog';
SHOW VARIABLES LIKE 'innodb_doublewrite';
```

해석 예시:

- `innodb_flush_log_at_trx_commit=1`: 커밋마다 redo를 강하게 동기화
- `innodb_flush_log_at_trx_commit=2`: OS cache까지는 반영하고 디스크 flush는 덜 자주
- `sync_binlog=1`: binlog도 매번 안전하게 flush

### 쓰기 지연과 fsync 관찰

```bash
iostat -x 1
vmstat 1
strace -fp "$(pidof mysqld)" -e fsync,fdatasync,pwrite64
```

이 조합으로 보면 다음을 추적할 수 있다.

- `fsync` 호출이 폭증하는지
- 디스크 await가 튀는지
- writeback이 몰리는지

### 대량 쓰기 예시

```sql
START TRANSACTION;

UPDATE orders
SET status = 'SHIPPED'
WHERE status = 'READY'
  AND created_at < '2026-04-01';

COMMIT;
```

이런 쿼리는 row 수가 많으면 redo 생성량과 dirty page 수를 크게 늘릴 수 있다.  
실제로는 batch size를 쪼개거나, 운영 시간대를 피해 실행하거나, 온라인 스키마 변경 방식으로 우회하는 판단이 필요하다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| `innodb_flush_log_at_trx_commit=1` | 가장 강한 durability | 커밋 지연 증가 가능 | 결제, 주문, 원장처럼 손실이 거의 허용되지 않을 때 |
| `innodb_flush_log_at_trx_commit=2` | 커밋 성능 개선 | 장애 시 일부 손실 가능 | 손실 허용 범위가 명확할 때 |
| redo log 크게 설정 | checkpoint pressure 완화 | 복구 시간이 길어질 수 있음 | 쓰기 버스트가 큰 워크로드 |
| redo log 작게 설정 | 복구 범위가 작아질 수 있음 | checkpoint가 자주 몰림 | 쓰기량이 안정적이고 운영 단순성이 중요할 때 |
| `innodb_doublewrite=ON` | torn page 보호 | 추가 write 비용 | 일반적인 운영 DB 대부분 |
| `innodb_doublewrite=OFF` | 쓰기 비용 감소 가능 | 페이지 손상 리스크 증가 | 극단적 성능 최적화가 필요하고 위험을 감수할 때 |

핵심은 "성능 vs 안정성"이 아니라 "어떤 장애를 얼마만큼 감수할지"를 정하는 것이다.

---

## 꼬리질문

> Q: redo log가 있는데 왜 데이터 파일을 바로 안 쓰나요?
> 의도: WAL의 존재 이유와 순차 I/O 이점을 이해했는지 확인
> 핵심: redo를 먼저 안전하게 남기면 커밋을 빠르고 예측 가능하게 만들 수 있다.

> Q: checkpoint를 자주 하면 좋은 것 아닌가요?
> 의도: 복구 시간과 쓰기 성능의 균형 감각 확인
> 핵심: checkpoint를 너무 자주 밀면 flush 부담이 커지고, 너무 늦으면 recovery time과 latency spike가 커진다.

> Q: undo log는 롤백만 하나요?
> 의도: MVCC와 과거 버전 읽기 이해 확인
> 핵심: undo는 롤백뿐 아니라 일관된 읽기를 위한 버전 재료다.

> Q: `fsync()`를 줄이면 무조건 성능이 좋아지나요?
> 의도: durability tradeoff를 운영 관점에서 설명할 수 있는지 확인
> 핵심: 쓰기는 빨라질 수 있지만, 장애 시 손실 범위가 커진다.

> Q: doublewrite는 왜 필요한가요?
> 의도: torn page와 페이지 원자성 문제 이해 확인
> 핵심: 로그가 있어도 페이지 자체가 깨지면 복구가 어려우므로, 페이지 반쪽 쓰기를 막는 안전장치가 필요하다.

---

## 한 줄 정리

redo log, undo log, checkpoint, crash recovery는 "DB가 죽어도 다시 살아나는 이유"이자, 평소의 `fsync` 비용과 latency spike를 감수하는 대신 정합성과 durability를 지키는 핵심 장치다.

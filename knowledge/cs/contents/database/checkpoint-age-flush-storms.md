# Checkpoint Age and Flush Storms

> 한 줄 요약: checkpoint age가 커지면 InnoDB는 더 이상 천천히 flush하지 못하고, 갑작스러운 flush storm으로 지연을 터뜨린다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: checkpoint age, flush storm, dirty page, LSN, page cleaner, innodb_io_capacity, flush list, redo log capacity, latency spike

## 핵심 개념

- 관련 문서:
  - [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)
  - [InnoDB Buffer Pool Internals](./innodb-buffer-pool-internals.md)
  - [Doublewrite Buffer and Torn Page Protection](./doublewrite-buffer-torn-page-protection.md)

checkpoint age는 현재 LSN과 마지막 checkpoint LSN 사이의 거리로 이해하면 된다.  
이 값이 커질수록 redo가 많이 쌓였고, 아직 디스크에 반영되지 않은 더티 페이지가 많다는 뜻이다.

문제는 checkpoint age가 일정 수준을 넘어서면 시스템이 스스로 flush를 강하게 밀어붙인다는 점이다.  
그 결과 갑자기 I/O가 몰리고 p95/p99가 튄다.

## 깊이 들어가기

### 1. checkpoint age는 왜 중요한가

redo log는 무한정 쌓아 둘 수 없다.  
checkpoint는 "여기까지는 파일에 반영됐다"는 기준점이고, checkpoint age는 그 기준점부터 얼마나 멀어졌는지를 보여준다.

checkpoint age가 너무 커지면 다음 압력이 생긴다.

- redo 공간 압박
- dirty page flush 압박
- commit path 지연
- recovery time 증가 가능성

### 2. flush storm은 어떻게 생기는가

flush storm은 더티 페이지를 계속 미뤄 두다가 한 번에 몰아서 비우는 현상이다.  
원인은 다양하지만 패턴은 비슷하다.

- 대량 UPDATE/INSERT
- 인덱스 생성이나 backfill
- 오랫동안 낮게만 flush하다가 임계점 도달
- IO capacity 설정이 워크로드보다 너무 낮음

이때는 DB가 조용히 느려지는 게 아니라, 갑자기 시끄럽게 느려진다.

### 3. page cleaner와 adaptive flushing

InnoDB는 백그라운드에서 page cleaner를 돌려 dirty page를 조금씩 비우려 한다.  
이론적으로는 부드럽게 가야 하지만, 쓰기량이 너무 높거나 설정이 맞지 않으면 결국 flush pressure가 쌓인다.

중요한 감각은 이렇다.

- flush를 빨리 하면 latency spike를 줄일 수 있다
- flush를 너무 빨리 하면 foreground I/O와 경쟁한다
- flush를 너무 늦추면 checkpoint age가 커져서 결국 더 크게 터진다

### 4. redo capacity와 flush는 같이 봐야 한다

redo 로그 용량이 너무 작으면 checkpoint 압박이 더 빨리 온다.  
반대로 너무 크면 recovery 스캔이 길어질 수 있다.  
즉 redo와 flush는 함께 튜닝해야 한다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `checkpoint age`
- `flush storm`
- `dirty page`
- `LSN`
- `page cleaner`
- `innodb_io_capacity`
- `redo log capacity`
- `latency spike`

## 실전 시나리오

### 시나리오 1. 배치가 시작된 후 API latency가 갑자기 흔들린다

원인:

- 배치가 대량 쓰기를 발생시킴
- dirty page가 빠르게 증가
- checkpoint age가 커짐
- flush가 몰리면서 foreground query가 밀림

### 시나리오 2. 쿼리는 빠른데 commit만 느려진다

읽기 실행 계획은 나쁘지 않지만, flush pressure가 커지면 commit path가 길어진다.  
이 경우 `EXPLAIN`만 봐서는 원인을 못 찾는다.

### 시나리오 3. 재시작은 됐지만 recovery가 너무 길다

checkpoint age가 오래 커져 있었다면 recovery가 더 무거워질 수 있다.  
flush storm은 운영 중 latency 문제이면서, 동시에 장애 후 복구 부담의 전조다.

## 코드로 보기

### checkpoint 관련 상태 확인

```sql
SHOW ENGINE INNODB STATUS\G
```

확인 포인트:

- `Log sequence number`
- `Last checkpoint at`
- `dirty pages`

### flush 관련 설정 확인

```sql
SHOW VARIABLES LIKE 'innodb_io_capacity';
SHOW VARIABLES LIKE 'innodb_io_capacity_max';
SHOW VARIABLES LIKE 'innodb_redo_log_capacity';
```

### 운영 관찰

```bash
iostat -x 1
vmstat 1
```

I/O 대기열과 await가 튀는지 같이 본다.

### 쓰기 부하 재현 예시

```sql
BEGIN;
UPDATE orders
SET status = 'DONE'
WHERE created_at >= '2026-04-01'
  AND created_at <  '2026-04-08';
COMMIT;
```

이런 작업이 반복되면 flush pressure가 쌓이기 쉽다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| flush를 적극적으로 밀기 | checkpoint age를 낮출 수 있다 | foreground IO와 경쟁한다 | 쓰기 급증 직전/직후 |
| flush를 천천히 유지 | 평시 latency가 부드럽다 | 임계점에서 storm이 터질 수 있다 | 안정적인 OLTP |
| redo capacity 확대 | checkpoint pressure를 늦출 수 있다 | recovery 시간이 늘 수 있다 | 쓰기량이 크고 복구 창이 허용될 때 |
| IO capacity 상향 | flush 능력을 높일 수 있다 | 스토리지 여유가 필요하다 | 디스크가 버틸 수 있을 때 |

핵심은 flush를 빠르게 하느냐가 아니라, **checkpoint age가 임계점에 닿기 전에 얼마나 부드럽게 비우느냐**다.

## 꼬리질문

> Q: checkpoint age가 왜 latency spike와 연결되나요?
> 의도: redo와 flush 압박의 관계를 아는지 확인
> 핵심: age가 커지면 시스템이 강제 flush 모드로 들어가기 때문이다

> Q: flush storm은 왜 갑자기 보이나요?
> 의도: 배경 누적과 임계점 동작 이해 여부 확인
> 핵심: 미뤄 둔 dirty page를 한 번에 비워야 하기 때문이다

> Q: `innodb_io_capacity`를 높이면 항상 좋은가요?
> 의도: 스토리지 여력과 foreground 경쟁을 고려하는지 확인
> 핵심: 디스크와 워크로드 상황에 따라 부작용이 있다

## 한 줄 정리

checkpoint age는 InnoDB가 얼마나 flush 부채를 쌓았는지 보여주는 지표이고, 그 부채가 커지면 flush storm으로 p95/p99가 터진다.

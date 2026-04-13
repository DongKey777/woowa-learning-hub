# Flush Neighbors, Adaptive Flushing, and IO Capacity

> 한 줄 요약: InnoDB의 flush는 단순 쓰기가 아니라, 인접 페이지를 같이 밀지, 얼마나 빨리 밀지, 디스크 여력을 얼마나 쓸지 결정하는 제어 문제다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: flush neighbors, adaptive flushing, innodb_io_capacity, page cleaner, dirty page, flush list, writeback, neighbor flushing

## 핵심 개념

- 관련 문서:
  - [Checkpoint Age and Flush Storms](./checkpoint-age-flush-storms.md)
  - [InnoDB Buffer Pool Internals](./innodb-buffer-pool-internals.md)
  - [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)

flush는 "더티 페이지를 디스크에 적는다"로 끝나지 않는다.  
InnoDB는 백그라운드에서 다음을 같이 조절한다.

- 얼마나 빨리 flush할지
- 인접한 페이지를 같이 flush할지
- 현재 디스크가 감당할 수 있는 수준인지

이게 실패하면 평소엔 조용하다가, 어느 순간 flush storm이 터진다.

## 깊이 들어가기

### 1. adaptive flushing은 왜 필요한가

dirty page가 조금 쌓였다고 무작정 flush를 많이 하면 foreground query와 경쟁한다.  
반대로 너무 늦추면 checkpoint age가 커져 임계점에서 몰아서 flush해야 한다.

adaptive flushing은 이 중간점을 찾으려는 시도다.

- dirty page 추세를 본다
- redo 생성량을 본다
- flush rate를 조정한다

### 2. flush neighbors는 언제 도움이 되나

인접 페이지가 디스크 상에서도 가까울 때, 한 페이지를 flush하면서 옆 페이지도 같이 쓰면 순차성이 좋아질 수 있다.  
하지만 모든 장비에서 이득이 같지는 않다.

- HDD에서는 인접 flush가 더 의미 있을 수 있다
- SSD에서는 이득이 작거나 오히려 불필요할 수 있다

### 3. IO capacity는 실제 스토리지 여력과 맞아야 한다

`innodb_io_capacity`는 DB가 백그라운드로 얼마나 적극적으로 flush할지 정하는 신호다.  
너무 낮으면 더티 페이지가 밀리고, 너무 높으면 foreground와 경쟁한다.

### 4. dirty page 비율만 보면 안 되는 이유

중요한 건 dirty page 개수만이 아니라 그 생성 속도다.

- 빠르게 늘면 adaptive flushing이 따라가기 어렵다
- 천천히 늘면 평시 flush로 흡수할 수 있다

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `flush neighbors`
- `adaptive flushing`
- `innodb_io_capacity`
- `page cleaner`
- `dirty page`
- `neighbor flushing`

## 실전 시나리오

### 시나리오 1. 대량 UPDATE 후 CPU보다 I/O가 먼저 터진다

쿼리 자체는 단순한데 dirty page가 급격히 쌓이면 flush path가 병목이 된다.  
이때는 IO capacity와 flush behavior를 봐야 한다.

### 시나리오 2. HDD와 SSD에서 같은 튜닝이 다르게 보인다

인접 flush가 HDD에서는 도움이 될 수 있지만, SSD에서는 그렇지 않을 수 있다.  
스토리지 종류를 무시하고 같은 설정을 쓰면 결과가 엇갈린다.

### 시나리오 3. 평소엔 괜찮다가 가끔 latency가 튄다

adaptive flushing이 늦게 반응하면 checkpoint age가 커졌다가 한 번에 정리하는 식으로 보일 수 있다.  
그 순간 foreground latency가 같이 튄다.

## 코드로 보기

### flush 관련 설정 확인

```sql
SHOW VARIABLES LIKE 'innodb_io_capacity';
SHOW VARIABLES LIKE 'innodb_io_capacity_max';
SHOW VARIABLES LIKE 'innodb_flush_neighbors';
```

### 상태 관찰

```sql
SHOW ENGINE INNODB STATUS\G
SHOW STATUS LIKE 'Innodb_buffer_pool_pages_dirty';
```

### write pressure 재현

```sql
UPDATE orders
SET status = 'DONE'
WHERE created_at >= '2026-04-01'
  AND created_at <  '2026-04-08';
```

### 운영 관찰

```bash
iostat -x 1
vmstat 1
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| flush neighbors 활성 | 일부 장비에서 순차성을 높일 수 있다 | SSD에서 이득이 적을 수 있다 | HDD/순차 I/O |
| flush neighbors 비활성 | 불필요한 추가 flush를 줄인다 | 특정 장비에서 순차성 이득을 놓친다 | SSD 중심 |
| IO capacity 상향 | dirty page를 더 빨리 비운다 | foreground와 경쟁할 수 있다 | write-heavy OLTP |
| IO capacity 보수적 설정 | 평시가 부드럽다 | 임계점에서 몰릴 수 있다 | 낮은 변동성 워크로드 |

핵심은 flush를 많이 하느냐가 아니라, **스토리지 특성과 dirty page 생성 속도에 맞춰 흐름을 제어하느냐**다.

## 꼬리질문

> Q: adaptive flushing이 왜 필요한가요?
> 의도: flush를 정적 설정으로만 보지 않는지 확인
> 핵심: dirty page와 redo 생성 속도에 따라 flush 속도를 조정해야 하기 때문이다

> Q: flush neighbors는 항상 좋은가요?
> 의도: 스토리지 특성 차이를 이해하는지 확인
> 핵심: HDD와 SSD에서 효율이 다르다

> Q: IO capacity를 높이면 왜 위험할 수 있나요?
> 의도: 백그라운드와 foreground 경쟁을 아는지 확인
> 핵심: flush가 너무 공격적이면 일반 쿼리와 I/O를 두고 경쟁한다

## 한 줄 정리

flush neighbors와 adaptive flushing은 dirty page를 언제 어떻게 비울지 정하는 제어 장치이고, IO capacity는 그 제어의 상한선을 결정한다.

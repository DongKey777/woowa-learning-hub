# Adaptive Flushing Heuristics and Dirty Page Feedback

> 한 줄 요약: adaptive flushing은 dirty page가 얼마나 빨리 늘고 있는지를 보고 flush 속도를 조절하는 feedback loop다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: adaptive flushing heuristics, dirty page feedback, flush rate control, checkpoint age, innodb_io_capacity, page cleaner, writeback, feedback loop

## 핵심 개념

- 관련 문서:
  - [Checkpoint Age and Flush Storms](./checkpoint-age-flush-storms.md)
  - [Flush Neighbors, Adaptive Flushing, and IO Capacity](./flush-neighbors-adaptive-flushing-io-capacity.md)
  - [InnoDB Buffer Pool Internals](./innodb-buffer-pool-internals.md)
  - [Redo Log Write Amplification](./redo-log-write-amplification.md)

adaptive flushing은 "정해진 속도로만 flush"하지 않고, dirty page 생성 속도와 checkpoint 압박을 보고 flush를 조절하는 메커니즘이다.

핵심은 다음이다.

- dirty page가 빨리 늘면 flush를 더 세게 한다
- 평시에는 foreground와 경쟁하지 않게 조절한다
- 너무 늦으면 flush storm이 온다

## 깊이 들어가기

### 1. feedback loop의 감각

adaptive flushing은 간단히 말하면 제어 루프다.

1. dirty page 증가를 본다.
2. redo 생성량을 본다.
3. 현재 flush 속도를 조절한다.
4. checkpoint age가 너무 커지지 않게 유지한다.

### 2. 왜 heuristics가 필요한가

DB는 모든 순간 완벽한 미래를 알 수 없다.  
그래서 현재 관측치로 flush 속도를 추정한다.

이 추정치는:

- 쓰기 burst에 반응해야 하고
- 평시에는 과하게 flush하지 않아야 한다

즉 빠른 반응과 안정성 사이의 균형이다.

### 3. dirty page 비율만으로는 부족하다

중요한 것은 dirty page 비율뿐 아니라 **증가 속도**다.

- 천천히 증가하면 부드럽게 대처할 수 있다
- 급격히 증가하면 뒤늦게 밀어내기만 하게 된다

### 4. flush storm으로 이어지는 조건

- backfill이나 batch update
- 작은 log file capacity
- 낮은 IO capacity
- long-running transaction과 겹치는 상황

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `adaptive flushing heuristics`
- `dirty page feedback`
- `flush rate control`
- `checkpoint age`
- `page cleaner`
- `feedback loop`

## 실전 시나리오

### 시나리오 1. 배치 시작 후 조금 있다가 느려진다

flush가 dirty page 증가를 따라가다 임계점 근처에서 급하게 작동하면, latency가 뒤늦게 튈 수 있다.  
이건 쿼리 문제처럼 보이지만 실제로는 flush 제어 문제다.

### 시나리오 2. 평소엔 괜찮고 특정 시간대만 버벅인다

adaptive flushing이 burst 패턴에 완전히 따라가지 못하면, 특정 시간대에만 flush pressure가 쌓일 수 있다.

### 시나리오 3. IO capacity를 올렸는데도 여전히 흔들린다

IO capacity만이 전부는 아니다.  
dirty page 생성 속도, redo 압박, checkpoint age가 함께 봐야 한다.

## 코드로 보기

### 관련 설정

```sql
SHOW VARIABLES LIKE 'innodb_io_capacity';
SHOW VARIABLES LIKE 'innodb_io_capacity_max';
SHOW VARIABLES LIKE 'innodb_flush_neighbors';
SHOW VARIABLES LIKE 'innodb_redo_log_capacity';
```

### 상태 확인

```sql
SHOW ENGINE INNODB STATUS\G
SHOW STATUS LIKE 'Innodb_buffer_pool_pages_dirty';
```

### burst 예시

```sql
UPDATE orders
SET status = 'DONE'
WHERE created_at >= '2026-04-01'
  AND created_at <  '2026-04-08';
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| adaptive flushing 적극 | checkpoint age를 제어한다 | foreground 경쟁이 생길 수 있다 | write burst가 있을 때 |
| 보수적 flushing | 평시 latency가 안정적이다 | burst에서 밀릴 수 있다 | 안정적 OLTP |
| IO capacity 상향 | 더 많이 비울 수 있다 | 스토리지와 경쟁한다 | 디스크 여력이 있을 때 |

핵심은 adaptive flushing을 단일 설정이 아니라, **dirty page 증가를 보고 반응하는 feedback control**로 이해하는 것이다.

## 꼬리질문

> Q: adaptive flushing은 무엇을 보고 조절하나요?
> 의도: feedback input을 아는지 확인
> 핵심: dirty page 증가와 redo 압박이다

> Q: 왜 heuristics가 필요한가요?
> 의도: DB가 미래를 정확히 모른다는 점을 아는지 확인
> 핵심: 관측 기반으로 flush를 조절해야 하기 때문이다

> Q: flush storm은 왜 생기나요?
> 의도: 제어 루프가 뒤늦게 반응하는 상황을 아는지 확인
> 핵심: dirty page가 임계점까지 누적되기 때문이다

## 한 줄 정리

adaptive flushing heuristics는 dirty page와 redo 생성 속도를 보고 flush를 조절하는 제어 루프이며, burst를 놓치면 flush storm으로 이어진다.

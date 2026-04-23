# Queue Claim with `SKIP LOCKED`, Fairness, and Starvation Trade-offs

> 한 줄 요약: `SKIP LOCKED`는 queue claim throughput을 크게 올릴 수 있지만, 공정성과 오래 대기한 작업 보장까지 자동으로 해결해 주지는 않는다.

**난이도: 🔴 Advanced**

관련 문서:

- [Queue Consumer Transaction Boundaries](./queue-consumer-transaction-boundaries.md)
- [Transactional Claim-Check와 Job Leasing](./transactional-claim-check-job-leasing.md)
- [Advisory Locks와 Row Locks](./advisory-locks-vs-row-locks.md)
- [Compare-and-Swap과 Pessimistic Locks](./compare-and-swap-vs-pessimistic-locks.md)
- [Hot Row Contention과 Counter Sharding](./hot-row-contention-counter-sharding.md)
- [Hot Updates, Secondary Index Churn, and Write-Path Contention](./hot-update-secondary-index-churn.md)

retrieval-anchor-keywords: skip locked, queue claim, work stealing, job fairness, starvation, for update skip locked, queue throughput, claim ordering

## 핵심 개념

DB 기반 queue나 job table에서 흔히 쓰는 claim 패턴은 다음과 같다.

```sql
SELECT id
FROM job_queue
WHERE status = 'READY'
ORDER BY available_at
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

이 패턴의 장점은 명확하다.

- 이미 다른 worker가 잡은 row를 기다리지 않는다
- worker 수를 늘려도 throughput이 잘 나오는 편이다
- queue claim latency를 짧게 유지하기 쉽다

하지만 비용도 있다.

- 공정성이 약해질 수 있다
- 특정 row가 계속 건너뛰어져 starvation이 생길 수 있다
- hot prefix index에서 claim 경쟁이 지속될 수 있다

즉 `SKIP LOCKED`는 "기다리지 않는다"는 성질을 주지만, **올바른 순서와 균형 처리까지 보장하는 것은 아니다**.

## 깊이 들어가기

### 1. `SKIP LOCKED`의 본질은 대기를 포기하고 다른 일을 찾는 것이다

일반 `FOR UPDATE`는 잠긴 row를 만나면 기다린다.  
`SKIP LOCKED`는 그 row를 건너뛰고 다음 후보를 찾는다.

좋은 점:

- worker thread가 줄 서서 기다리지 않는다
- lock wait timeout이 줄어든다
- 높은 동시성에서 claim throughput이 좋아진다

하지만 이 선택은 곧 "지금 잡기 쉬운 일 먼저 처리"라는 정책을 뜻한다.

### 2. ordering과 fairness는 별도 문제다

`ORDER BY available_at`를 써도 실제 처리 순서는 완전히 보장되지 않을 수 있다.

왜냐하면:

- 가장 오래된 row가 이미 잠겨 있으면 건너뛴다
- 그다음 row가 먼저 처리된다
- 일부 오래된 row는 반복적으로 뒤로 밀릴 수 있다

즉 `SKIP LOCKED`는 strict FIFO보다 **높은 가용성과 throughput**을 우선하는 선택이다.

### 3. starvation은 장애가 아니라 설계 결과일 수 있다

다음 상황에서 starvation이 생기기 쉽다.

- 특정 row가 자주 실패해서 다시 READY로 돌아옴
- 일부 worker가 긴 처리 시간을 가짐
- 같은 prefix에서 claim 경쟁이 반복됨

이때 queue가 "멈춘 것"처럼 보이지는 않아도, 특정 작업은 계속 뒤로 밀린다.

그래서 `SKIP LOCKED` 기반 queue에는 보통 다음 중 하나가 필요하다.

- retry/backoff 조정
- priority bucket 분리
- 오래 대기한 작업 재스캔
- starvation watchdog

### 4. claim index가 잘못되면 기다림 대신 스캔 비용이 커진다

`SKIP LOCKED`가 만능처럼 보여도, claim 후보를 찾는 인덱스가 나쁘면:

- 잠긴 row를 많이 건너뛰기 위해 더 긴 스캔을 하고
- 같은 hot prefix를 여러 worker가 반복해서 훑고
- 결국 throughput 이점이 줄어든다

따라서 queue claim 설계는 SQL 문법보다:

- `status`, `available_at` 인덱스 구조
- partition/bucket 분산
- queue depth 분포

를 함께 봐야 한다.

### 5. lease/heartbeat와 섞일 때는 claim과 ownership을 분리하는 게 좋다

`SKIP LOCKED`는 "누가 지금 집을까"에는 좋지만, 긴 처리의 ownership까지 전부 맡기기는 불편할 수 있다.

특히 긴 job에서는:

- claim은 `SKIP LOCKED`로 빠르게
- ownership 유지와 takeover는 lease row로

분리하는 편이 안정적일 때가 많다.

즉 queue entry 선점과 장기 실행 보장은 같은 문제가 아니다.

### 6. `SKIP LOCKED`가 맞지 않는 경우도 있다

다음 요구가 강하면 다른 패턴이 더 맞을 수 있다.

- strict FIFO가 중요하다
- 같은 partition 안의 순서 보장이 필수다
- 일부 job starvation이 절대 허용되지 않는다

이 경우는:

- partitioned queue
- advisory lock gate
- lease coordinator
- broker-native ordering

같은 다른 구조를 검토해야 한다.

## 실전 시나리오

### 시나리오 1. queue worker 수를 늘렸더니 throughput은 좋아짐

원인:

- `SKIP LOCKED`가 lock wait를 줄여 worker가 놀지 않음

추가 점검:

- 오래된 job이 계속 뒤로 밀리는지
- READY range 스캔 비용이 커지는지

### 시나리오 2. 특정 재시도 job이 영원히 늦게 처리됨

재시도된 job이 같은 hot prefix에 다시 들어오고, 다른 쉬운 job이 계속 먼저 잡힌다.

대응:

- retry backoff 증가
- priority bucket 분리
- starving job reaper 추가

### 시나리오 3. 긴 job을 `SKIP LOCKED`만으로 처리

처리 시간이 길면 claim row만으로 ownership을 오래 표현하기 어렵다.

이 경우는:

- claim은 짧게
- 실행 ownership은 lease로

나누는 편이 더 낫다.

## 코드로 보기

```sql
SELECT id
FROM job_queue
WHERE status = 'READY'
  AND available_at <= NOW()
ORDER BY available_at, id
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

```sql
UPDATE job_queue
SET status = 'CLAIMED',
    claimed_by = ?,
    claimed_at = NOW()
WHERE id = ?;
```

```text
watch metrics
- claim success rate
- rows scanned per claim
- oldest READY age
- retry bucket backlog
```

핵심은 claim SQL 하나보다, claim fairness와 starvation을 관찰하는 메트릭을 함께 두는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| `FOR UPDATE` 대기 | 순서가 비교적 단순하다 | worker가 기다리며 throughput이 떨어진다 | 동시성이 낮을 때 |
| `SKIP LOCKED` | 높은 처리량과 낮은 wait를 준다 | fairness와 starvation 문제가 생길 수 있다 | high concurrency queue |
| claim + lease 분리 | 긴 job ownership이 안정적이다 | 구조가 복잡해진다 | 장기 실행 job |
| broker-native queue | ordering semantics가 강하다 | DB 일관성과 분리된다 | strict ordering 요구가 강할 때 |

## 꼬리질문

> Q: `SKIP LOCKED`를 쓰면 FIFO가 보장되나요?
> 의도: throughput과 fairness를 구분하는지 확인
> 핵심: 아니다. 잠긴 row를 건너뛰므로 실제 처리 순서는 어긋날 수 있다

> Q: starvation은 왜 생기나요?
> 의도: 오래된 row가 계속 밀리는 구조를 이해하는지 확인
> 핵심: 잡기 쉬운 row가 반복적으로 먼저 선택되고 특정 row는 계속 건너뛰어질 수 있기 때문이다

> Q: 긴 job에선 왜 lease를 같이 보나요?
> 의도: claim과 ownership을 분리하는지 확인
> 핵심: `SKIP LOCKED`는 빠른 선점에는 좋지만 장기 실행 ownership과 takeover 표현에는 부족할 수 있다

## 한 줄 정리

`SKIP LOCKED`는 queue claim의 wait를 줄여 throughput을 높이는 도구지만, fairness·starvation·ownership은 별도 설계와 메트릭으로 보완해야 한다.

# Hot Updates, Secondary Index Churn, and Write-Path Contention

> 한 줄 요약: 자주 바뀌는 컬럼을 secondary index에 얹으면 row lock보다 먼저 index leaf churn과 latch contention이 병목이 될 수 있다.

**난이도: 🔴 Advanced**

관련 문서:

- [Secondary Index Change Propagation Path](./secondary-index-change-propagation-path.md)
- [Insert Hotspot과 Page Contention](./insert-hotspot-page-contention.md)
- [Hot Row Contention과 Counter Sharding](./hot-row-contention-counter-sharding.md)
- [Compare-and-Swap과 Pessimistic Locks](./compare-and-swap-vs-pessimistic-locks.md)
- [Covering Index Width, Leaf Fanout, and Write Amplification](./covering-index-width-fanout-write-amplification.md)

retrieval-anchor-keywords: hot update, secondary index churn, index leaf contention, write path contention, status update hotspot, latch contention, update-heavy secondary index, queue table index

## 핵심 개념

write contention을 이야기할 때 보통 row lock부터 떠올린다.  
하지만 update-heavy workload에서는 row lock보다 먼저 secondary index churn이 병목이 될 수 있다.

대표 패턴:

- queue row의 `status`가 계속 바뀜
- 세션/heartbeat row의 `updated_at`이 자주 갱신됨
- retry counter나 priority가 빠르게 변함

이 컬럼들이 secondary index에 포함되어 있으면, 논리적으로는 "한 row update"라도 물리적으로는 **index entry delete/insert churn**이 반복된다.

## 깊이 들어가기

### 1. hot update는 row보다 index range를 뜨겁게 만든다

예를 들어 작업 큐에서 `status='READY'` -> `CLAIMED` -> `DONE`으로 상태가 바뀐다고 해보자.

`(status, available_at)` index가 있다면:

- READY range에서 entry 제거
- CLAIMED range에 entry 추가
- 같은 hot prefix page들에서 churn 반복

즉 병목은 "같은 row를 누가 잡느냐"뿐 아니라, **같은 index prefix 근처를 모두가 계속 고친다**는 데 있다.

### 2. 자주 바뀌는 컬럼은 읽기에는 좋아 보여도 쓰기에는 독이 된다

운영에서 자주 보는 유혹:

- queue polling을 빠르게 하려고 `status` 인덱스 추가
- 최근 접속 조회를 위해 `last_seen_at` 인덱스 추가
- 재시도 관리를 위해 `retry_count`를 복합 인덱스에 포함

하지만 이 컬럼들이 초당 수천 번 바뀌면:

- secondary leaf churn 증가
- page split/merge 가능성 증가
- redo/undo 증가
- latch contention과 cache pollution 증가

그래서 "조회가 빠르다"는 이유만으로 volatile column을 인덱싱하면 write path가 훨씬 더 비싸질 수 있다.

### 3. contention을 lock과 latch로 분리해서 봐야 한다

write path 병목은 크게 둘이다.

- lock contention
  - 같은 논리 row/범위를 두고 기다림
- latch/contention on hot pages
  - 같은 index/leaf page를 수정하려고 내부 구조에서 경쟁

애플리케이션 로그에는 둘 다 "DB가 느리다"로 보일 수 있다.  
하지만 해결책은 다르다.

- lock 문제 -> transaction boundary, isolation, claim protocol 조정
- latch 문제 -> index 구조, key 분산, volatile column 제거

### 4. queue/lease 테이블은 특히 volatile-index 설계를 조심해야 한다

queue, job, lease, heartbeat 테이블은 다음 성질이 강하다.

- status가 자주 바뀐다
- 작은 hot set에 요청이 몰린다
- 최신 timestamp를 기준으로 poll한다

이런 곳에서는 흔히:

- `status`, `available_at` 같은 최소 claim key만 두고
- 큰 payload나 자주 바뀌는 메타데이터는 별도 테이블로 분리하거나
- append-only event log + compacted view로 전환하는 편이 낫다

### 5. 단일 hot index를 피하는 구조적 방법이 있다

대표적인 완화책:

- status bucket sharding
- ready queue를 여러 partition으로 분산
- claim용 narrow index와 상세 row 분리
- volatile metadata를 별도 table 또는 cache로 이동

핵심은 contention이 row에 있는지, index prefix에 있는지 보고 **뜨거운 update path를 여러 물리 위치로 흩는 것**이다.

### 6. CAS가 항상 도움이 되는 것은 아니다

낙관적 락/CAS는 row-level 중복 성공을 줄이는 데 유용하다.  
하지만 indexed volatile column 자체가 계속 바뀌면:

- version check는 성공/실패를 조절할 뿐
- secondary index churn은 여전히 남는다

즉 CAS는 lock 전략이고, index churn은 storage path 문제다.  
둘을 같은 해결책으로 보면 안 된다.

## 실전 시나리오

### 시나리오 1. 작업 큐에서 claim TPS가 안 올라감

`WHERE status='READY' ORDER BY available_at LIMIT 1 FOR UPDATE SKIP LOCKED` 패턴이 있다.

문제:

- `status` 전이마다 index churn
- READY prefix page가 계속 뜨거워짐

대응:

- ready shard 분산
- claim용 narrow index 유지
- 상태 전이 메타데이터 최소화

### 시나리오 2. presence/heartbeat 갱신이 전체 DB를 흔듦

`last_seen_at` 인덱스를 둔 presence 테이블에서 수많은 heartbeat update가 발생한다.

이 경우:

- 최근 접속 조회를 위해 인덱스를 둔 것이
- 실제로는 update storm을 키울 수 있다

TTL cache나 append-only heartbeat log가 더 나을 수 있다.

### 시나리오 3. retry_count 인덱스를 둔 배치 테이블

재시도 우선순위 정렬을 위해 `retry_count`를 인덱스에 포함했는데, 실패가 몰리는 순간 update contention이 급격히 증가한다.

이때는 retry metadata를 분리하거나, priority bucket 자체를 coarse-grained 하게 단순화하는 편이 낫다.

## 코드로 보기

```sql
CREATE TABLE job_queue (
  id BIGINT PRIMARY KEY,
  status VARCHAR(20) NOT NULL,
  available_at TIMESTAMP NOT NULL,
  retry_count INT NOT NULL,
  payload JSON NOT NULL,
  INDEX idx_job_ready (status, available_at),
  INDEX idx_job_retry (status, retry_count, available_at)
);
```

```sql
UPDATE job_queue
SET status = 'CLAIMED',
    retry_count = retry_count + 1
WHERE id = ?;
```

위 update는 row 하나만 바꾸는 것처럼 보여도, `status`와 `retry_count`가 인덱스에 걸려 있으면 여러 leaf page를 흔든다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| volatile column까지 인덱싱 | 일부 조회/claim이 빨라진다 | update churn과 page contention이 커진다 | write 빈도가 낮을 때만 |
| narrow claim index | write path가 가볍다 | lookup이 남는다 | queue/lease처럼 상태 전이가 잦을 때 |
| shard/bucket 분산 | hot prefix 경쟁을 줄인다 | 운영 복잡도가 늘어난다 | high TPS queue, scheduler |
| metadata 분리 | hot update를 분산할 수 있다 | join/조회 경로가 늘어난다 | heartbeat/presence/retry 메타데이터 |

## 꼬리질문

> Q: update-heavy workload에서 왜 row lock 말고 index churn을 봐야 하나요?
> 의도: 논리 경합과 물리 경합을 구분하는지 확인
> 핵심: 자주 바뀌는 indexed column은 같은 index leaf/page를 계속 수정하게 만들기 때문이다

> Q: CAS를 쓰면 이런 병목이 해결되나요?
> 의도: lock 전략과 storage path를 구분하는지 확인
> 핵심: CAS는 충돌 제어일 뿐, volatile secondary index 유지 비용은 그대로 남을 수 있다

> Q: queue 테이블 인덱스는 무엇을 조심해야 하나요?
> 의도: claim path 설계 감각 확인
> 핵심: 자주 바뀌는 status/retry/timestamp를 과하게 인덱싱하면 write path가 먼저 무너질 수 있다

## 한 줄 정리

hot update 병목의 본질은 row 하나가 아니라, 자주 바뀌는 indexed column이 같은 secondary index range를 계속 흔들어 latch와 write amplification을 키우는 데 있다.

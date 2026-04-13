# Transaction Heartbeat와 Long-Running Job Locking

> 한 줄 요약: 오래 도는 작업은 살아 있음을 알리는 heartbeat가 필요하지만, 그 heartbeat가 락 점유를 대신해 주지는 않는다.

관련 문서: [Transaction Timeout과 Lock Timeout](./transaction-timeout-vs-lock-timeout.md), [Metadata Lock and DDL Blocking](./metadata-lock-ddl-blocking.md), [DB Lease와 Fencing Token](./db-lease-fencing-coordination.md)
Retrieval anchors: `transaction heartbeat`, `long-running job`, `lease renewal`, `heartbeat lock`, `job progress`

## 핵심 개념

Long-running job은 한 번에 끝나지 않기 때문에, 작업이 아직 살아 있는지와 작업이 정합성을 지키고 있는지를 따로 관리해야 한다.

왜 중요한가:

- 배치나 마이그레이션은 수분에서 수시간 걸릴 수 있다
- 작업이 멈춘 것인지, 오래 걸리는 것인지 구분이 필요하다
- heartbeat만 믿고 트랜잭션을 너무 오래 유지하면 락이 쌓인다

heartbeat는 주로 “죽지 않았다”는 신호이고, 락은 “아직 소유 중이다”라는 신호다.  
둘은 같은 것이 아니다.

## 깊이 들어가기

### 1. heartbeat가 필요한 이유

오래 도는 작업은 외부에서 보면 멈춘 것처럼 보일 수 있다.

- 배치가 chunk 단위로 처리된다
- 마이그레이션이 단계별로 진행된다
- 백필이 중간에 IO 병목을 만난다

이때 heartbeat를 남겨서 작업 관리자나 coordinator가 상태를 판단하게 한다.

### 2. heartbeat가 락을 대체하지 못하는 이유

heartbeat가 있다고 해서 락을 계속 잡아도 된다는 뜻은 아니다.

- 트랜잭션이 오래 열려 있으면 row lock과 MDL이 유지될 수 있다
- heartbeat는 상태 신호일 뿐 데이터 잠금이 아니다
- 살아 있다는 이유로 긴 락을 유지하면 전체 경합이 커진다

즉 heartbeat는 작업 상태 모니터링이고, 락 전략은 별도로 설계해야 한다.

### 3. chunked job과 heartbeat

좋은 패턴은 보통 이렇다.

- 작은 chunk마다 커밋한다
- chunk 완료 후 heartbeat를 갱신한다
- 다음 chunk는 새 트랜잭션으로 진행한다

이 방식은 락 점유 시간을 줄이고, 중간 실패 복구도 쉬워진다.

### 4. heartbeat가 너무 잦으면 생기는 문제

- DB write가 많아진다
- coordinator row가 핫스팟이 된다
- 상태 갱신 자체가 병목이 된다

heartbeat는 충분히 자주, 하지만 과하게 자주 보내지 않는 균형이 필요하다.

## 실전 시나리오

### 시나리오 1: 밤새 도는 백필이 멈춘 것처럼 보임

작업이 실제로는 chunk 30을 처리 중인데, 모니터링은 갱신이 없어서 실패로 오인한다.  
heartbeat가 있으면 이런 오판을 줄일 수 있다.

### 시나리오 2: heartbeat 때문에 오히려 DB가 느려짐

작업 상태 테이블을 초당 여러 번 갱신하면, 그 row 자체가 핫 row가 된다.  
이 경우 heartbeat 주기를 늘려야 한다.

### 시나리오 3: 오래 열린 트랜잭션이 배포를 막음

작업이 살아 있다고 판단되어 트랜잭션을 계속 유지하면 MDL과 row lock이 함께 오래 남을 수 있다.  
heartbeat와 락 수명은 분리해야 한다.

## 코드로 보기

```sql
CREATE TABLE job_heartbeat (
  job_name VARCHAR(100) PRIMARY KEY,
  worker_id VARCHAR(100) NOT NULL,
  last_seen_at DATETIME NOT NULL,
  progress_pct INT NOT NULL
);

UPDATE job_heartbeat
SET last_seen_at = NOW(),
    progress_pct = 60
WHERE job_name = 'daily-backfill';
```

```java
for (Chunk chunk : chunks) {
    processChunk(chunk);
    updateHeartbeat(jobName, workerId, chunk.progress());
    commitChunk();
}
```

heartbeat는 작업이 아직 살아 있음을 보여주지만, **트랜잭션과 락을 오래 붙잡아도 된다는 허가증은 아니다**.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 긴 단일 트랜잭션 + heartbeat | 단순하다 | 락과 MDL이 오래 간다 | 거의 없음 |
| chunked transaction + heartbeat | 복구가 쉽다 | 구현이 더 복잡하다 | 대부분의 장기 작업 |
| 외부 coordinator + heartbeat | 관측성이 좋다 | 운영 요소가 늘어난다 | 대규모 배치 |
| heartbeat 없는 작업 | 구현이 쉽다 | 중단 감지가 어렵다 | 매우 짧은 작업 |

## 꼬리질문

> Q: heartbeat가 있는데 왜 락이 오래 문제되나요?
> 의도: 상태 신호와 락 점유를 분리해서 아는지 확인
> 핵심: 살아 있음을 알리는 것과 자원을 오래 잡는 것은 별개다

> Q: 장기 작업은 왜 chunk로 나누나요?
> 의도: 롤백과 경합 비용을 이해하는지 확인
> 핵심: 락 점유를 줄이고 복구 지점을 만들기 위해서다

> Q: heartbeat를 너무 자주 갱신하면 무슨 일이 생기나요?
> 의도: coordinator row가 병목이 되는 점을 아는지 확인
> 핵심: 상태 테이블 자체가 핫스팟이 된다

## 한 줄 정리

Transaction heartbeat는 장기 작업의 생존 신호이고, 락은 chunk 단위로 짧게 유지해야 한다.

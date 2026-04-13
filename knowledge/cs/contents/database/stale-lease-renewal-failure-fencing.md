# Stale Lease Renewal Failure와 Fencing

> 한 줄 요약: lease 갱신이 실패하면 단순 만료보다 더 위험한데, 오래된 worker가 자신이 여전히 주인이라고 착각할 수 있기 때문이다.

관련 문서: [DB Lease와 Fencing Token](./db-lease-fencing-coordination.md), [Replication Failover and Split Brain](./replication-failover-split-brain.md), [Ghost Reads와 Mixed Routing Write Fence Tokens](./ghost-reads-mixed-routing-write-fence-tokens.md)
Retrieval anchors: `stale lease`, `lease renewal failure`, `fencing`, `clock skew`, `renewal drift`

## 핵심 개념

Lease renewal failure는 작업 주체가 자신의 lease를 갱신하지 못해 소유권이 끊기는 상황이다.  
문제는 그 뒤에 오래된 worker가 여전히 작업을 계속할 수 있다는 점이다.

왜 중요한가:

- 네트워크 순간 장애로 갱신이 실패할 수 있다
- GC pause나 스레드 정체로 heartbeat가 늦어질 수 있다
- 오래된 주체가 결과를 덮으면 정합성이 망가진다

fencing은 이 상황에서 “갱신 실패한 주체”를 실제 write 경로에서 차단하는 마지막 방어선이다.

## 깊이 들어가기

### 1. renewal failure가 왜 위험한가

lease 만료 자체보다 더 위험한 건, 갱신 실패 후에도 작업 코드가 계속 돌 수 있다는 점이다.

- worker는 자기 lease가 끊긴 줄 모른다
- coordinator는 새 주체를 발급했다
- 둘 다 write하려고 한다

이때 fencing token이 없으면 stale worker가 새 결과를 덮을 수 있다.

### 2. renewal drift

갱신 주기가 너무 빡빡하거나, 처리 시간이 들쭉날쭉하면 갱신이 늦어진다.

- 짧은 GC pause
- 네트워크 지연
- chunk 처리 편차

이런 drift는 lease 설계를 흔든다.  
그래서 renew 주기는 평균보다 충분히 길어야 한다.

### 3. fencing token의 역할

fencing token은 lease를 다시 얻을 때마다 증가하는 단조 값이다.

- 새 주체는 더 큰 token을 가진다
- 저장소는 더 작은 token의 write를 거절한다
- stale worker는 결과를 써도 반영되지 않는다

즉 fencing은 소유권이 아니라 **마지막 write 권리**를 제어한다.

### 4. renew 실패 후의 운영 대응

- 즉시 작업 중단
- 현재 step 기록
- 새 주체가 이어받을 수 있게 progress 저장
- stale worker의 후속 write 차단 확인

## 실전 시나리오

### 시나리오 1: 배치가 lease renewal 실패 후에도 계속 진행

worker는 refresh가 끊긴 걸 모르고 마지막 chunk를 끝까지 처리한다.  
이때 fencing이 없으면 stale write가 들어간다.

### 시나리오 2: 네트워크 흔들림으로 일시 갱신 실패

잠깐의 네트워크 단절이 lease 상실로 이어질 수 있다.  
재획득 후 새 token으로 이어받아야 한다.

### 시나리오 3: 오래된 worker가 마지막에 결과를 덮음

작업은 거의 끝났는데, 오래된 주체의 늦은 commit이 새 주체의 결과를 덮어 버린다.  
fencing이 없으면 회복이 어렵다.

## 코드로 보기

```sql
UPDATE distributed_lease
SET fencing_token = fencing_token + 1,
    owner_id = 'worker-b',
    expires_at = NOW() + INTERVAL 30 SECOND
WHERE name = 'reconciler'
  AND expires_at < NOW();

-- write side fencing
UPDATE job_result
SET status = 'DONE',
    fencing_token = 81
WHERE job_id = 'reconciler-1'
  AND fencing_token < 81;
```

```java
if (!leaseService.renew(jobName, token)) {
    throw new IllegalStateException("lease lost");
}
```

lease renewal 실패는 “잠깐 늦음”이 아니라, **소유권 상실 가능성**으로 다뤄야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| renewal only | 구현이 쉽다 | stale write를 못 막는다 | 매우 단순한 작업 |
| renewal + fencing | 안전하다 | token 관리가 필요하다 | 결과 덮어쓰기가 치명적일 때 |
| longer TTL | 오탐이 줄어든다 | 장애 감지가 늦어진다 | 작업 편차가 큰 경우 |
| external coordinator | 강하다 | 운영 복잡도 증가 | 분산 조정이 중요한 경우 |

## 꼬리질문

> Q: lease renewal failure가 왜 단순 만료보다 더 위험한가요?
> 의도: stale worker가 계속 write할 수 있음을 아는지 확인
> 핵심: 갱신 실패 후에도 오래된 주체가 작업을 계속할 수 있다

> Q: fencing token은 무엇을 막나요?
> 의도: stale write 차단을 이해하는지 확인
> 핵심: 더 낮은 token의 늦은 write를 거른다

> Q: renew 주기를 짧게 하면 더 안전한가요?
> 의도: 지나치게 짧은 주기의 부작용을 아는지 확인
> 핵심: 오히려 renewal drift와 오탐이 늘 수 있다

## 한 줄 정리

Lease renewal failure는 오래된 worker가 살아남아 write하는 상황을 만들 수 있으므로, fencing token으로 stale write를 차단해야 한다.

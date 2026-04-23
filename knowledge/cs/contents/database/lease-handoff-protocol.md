# Lease Handoff Protocol

> 한 줄 요약: lease handoff는 “주인이 바뀐다”를 안전하게 넘겨주는 절차이고, 겹침 구간과 fencing 없이는 사고가 난다.

**난이도: 🟡 Intermediate**

관련 문서: [DB Lease와 Fencing Token](./db-lease-fencing-coordination.md), [Stale Lease Renewal Failure와 Fencing](./stale-lease-renewal-failure-fencing.md), [Replication Failover and Split Brain](./replication-failover-split-brain.md)
retrieval-anchor-keywords: lease handoff, handoff protocol, ownership transfer, fencing token, grace period

## 핵심 개념

Lease handoff protocol은 현재 lease holder가 다음 holder에게 작업을 넘길 때의 안전 절차다.  
이 절차가 없으면 주인이 바뀌는 순간에 두 주체가 동시에 write할 수 있다.

왜 중요한가:

- 배치 worker, shard owner, leader 역할이 바뀌는 순간이 가장 위험하다
- 단순 만료는 넘김이 아니라 끊김이다
- handoff는 “새 주체에게 넘겨줌”과 “옛 주체를 확실히 멈춤”을 같이 해야 한다

즉 handoff는 소유권 이전이 아니라 **중복 실행 없이 권한을 이전하는 프로토콜**이다.

## 깊이 들어가기

### 1. 왜 handoff가 필요한가

lease 만료만 쓰면 다음 문제가 생긴다.

- 옛 주체가 아직 끝내지 못한 작업이 있다
- 새 주체가 바로 시작해서 중복 실행된다
- 결과가 덮이거나 순서가 틀어진다

handoff는 이 충돌 구간을 줄이기 위해 있다.

### 2. 안전한 handoff 단계

전형적인 절차는 다음과 같다.

1. 현재 holder가 drain 시작
2. 새로운 work intake 중지
3. progress 저장
4. fencing token 증가
5. 새 holder가 takeover
6. 옛 holder는 write 중단

핵심은 overlap이 생기더라도, write는 새 token만 통과해야 한다.

### 3. grace period의 의미

짧은 grace period는 in-flight 작업을 정리하는 데 유용하다.  
하지만 grace가 길어지면 두 주체가 동시에 살아 있는 시간이 늘어난다.

그래서 grace는 “충분히 짧고, 충분히 명시적이어야” 한다.

### 4. 손대면 안 되는 것

- 옛 holder가 새 token 없이 계속 write하는 것
- takeover 전에 새 holder가 무작정 실행하는 것
- progress 저장 없이 handoff만 하는 것

handoff는 제어되지 않은 추측이 아니라, 상태 전이의 합의다.

## 실전 시나리오

### 시나리오 1: 배치가 작업 중간에 리더를 넘김

옛 리더가 종료 직전이고 새 리더가 바로 시작하면 중복 처리 위험이 있다.  
handoff protocol이 필요하다.

### 시나리오 2: shard owner가 바뀌는 순간

partition owner가 바뀔 때 progress와 fencing 없이 넘기면 같은 chunk를 두 번 처리할 수 있다.

### 시나리오 3: 장애 후 강제 takeover

grace 없이 새 holder를 세우면 빠르지만, stale writer가 남을 수 있다.  
fencing이 필수다.

## 코드로 보기

```sql
-- handoff 시 epoch 증가
UPDATE lease_table
SET owner_id = 'worker-b',
    fencing_token = fencing_token + 1,
    expires_at = NOW() + INTERVAL 30 SECOND
WHERE name = 'daily-job';
```

```java
void handoff() {
    stopAcceptingNewChunks();
    saveProgress();
    leaseService.transferWithNewToken();
    stopWritesOnOldOwner();
}
```

handoff는 “바통 넘기기”처럼 보이지만, 실제로는 **새 바통과 옛 바통의 동시 유효 시간을 최소화하는 절차**다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| hard expire | 단순하다 | 중복 위험이 있다 | 비중요 작업 |
| grace handoff | 안전하다 | 구현이 복잡하다 | 중요한 배치/owner |
| fencing-only takeover | stale write를 막는다 | progress 정리가 필요하다 | 분산 coordination |
| manual handoff | 통제 가능 | 느리다 | 장애 복구 |

## 꼬리질문

> Q: lease handoff와 단순 만료의 차이는 무엇인가요?
> 의도: 권한 넘김과 끊김을 구분하는지 확인
> 핵심: handoff는 상태와 권한을 의도적으로 이전한다

> Q: grace period가 왜 필요한가요?
> 의도: in-flight 작업 정리를 아는지 확인
> 핵심: 처리 중이던 chunk를 안전하게 마치기 위해서다

> Q: handoff에서 fencing token이 왜 중요하나요?
> 의도: old owner의 stale write를 막는지 확인
> 핵심: 새 주체만 write를 통과시키는 최종 방어선이다

## 한 줄 정리

Lease handoff protocol은 주체 교체 순간의 겹침을 통제하는 절차이고, fencing token이 있어야 옛 주체의 늦은 write를 막을 수 있다.
